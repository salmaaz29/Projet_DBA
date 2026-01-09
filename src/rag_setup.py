# -*- coding: utf-8 -*-
"""
MODULE 2 : RAG & Vector Database Setup avec PINECONE (VERSION ULTIME)
✅ Namespaces par module (isolation données)
✅ Déduplication fichier JSON (performance)
✅ Nettoyage texte avancé (qualité)
✅ Score minimum + validation tests (fiabilité)
✅ Paramètres optimisés (300 pages, 300 chars, 5000 metadata)
"""

import os
import time
import re
import json
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from pathlib import Path
import pypdf  # ← Changement ici : utilisation de pypdf au lieu de PyPDF2
import hashlib
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class OracleRAGSetup:
    """Configuration RAG pour documentation Oracle avec Pinecone"""
    
    # Namespaces pour chaque module du projet
    NAMESPACES = {
        "module2": "rag-docs",           # Documentation générale
        "module4": "security-audit",     # Audit sécurité
        "module5": "query-optimization", # Optimisation requêtes
        "module6": "anomaly-detection",  # Détection anomalies
        "module7": "backup-strategy",    # Stratégie backup
        "module8": "recovery-guide"      # Guide restauration
    }
    
    def __init__(self, index_name="oracle-docs-rag", namespace="module2"):
        """
        Args:
            index_name: Nom de l'index Pinecone
            namespace: Namespace à utiliser (module2, module4, etc.)
        """
        self.index_name = index_name
        
        # Valider namespace
        if namespace not in self.NAMESPACES and not namespace.startswith("module"):
            print(f"⚠️  Namespace '{namespace}' non standard")
            print(f"💡 Namespaces recommandés: {list(self.NAMESPACES.keys())}")
        
        self.namespace = self.NAMESPACES.get(namespace, namespace)
        
        # Vérifier clé API
        self.api_key = os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "\n❌ PINECONE_API_KEY manquant dans .env\n"
                "→ Créez un compte sur https://www.pinecone.io/\n"
                "→ Ajoutez PINECONE_API_KEY=votre_clé dans .env"
            )
        
        print(f"🔧 Initialisation Pinecone (namespace: '{self.namespace}')...")
        
        # Initialiser Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        
        # Modèle d'embedding
        print("🤖 Chargement modèle d'embedding...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        print(f"   ✅ Modèle 'all-MiniLM-L6-v2' chargé ({self.dimension} dimensions)")
        
        # Créer ou récupérer l'index
        self._setup_index()
        
        # Charger état déduplication (fichier JSON local)
        self._load_dedup_state()
        
        self.docs_dir = Path("data/docs/")
        self.docs_dir.mkdir(exist_ok=True)
        
        # Statistiques
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "failed_documents": 0,
            "skipped_duplicates": 0,
            "total_chars": 0
        }
    
    def _setup_index(self):
        """Créer ou récupérer l'index Pinecone"""
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"   📝 Création index '{self.index_name}'...")
            
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )
            
            print("   ⏳ Attente de l'index (30-60s)...")
            time.sleep(45)
            print(f"   ✅ Index '{self.index_name}' créé")
        else:
            print(f"   ✅ Index '{self.index_name}' existant chargé")
        
        # Connecter à l'index
        self.index = self.pc.Index(self.index_name)
        
        # Statistiques namespace
        time.sleep(2)
        stats = self.index.describe_index_stats()
        ns_stats = stats.get('namespaces', {}).get(self.namespace, {})
        vector_count = ns_stats.get('vector_count', 0)
        print(f"   📊 Vecteurs dans namespace '{self.namespace}': {vector_count}")
    
    def _load_dedup_state(self):
        """Charger état déduplication depuis fichier JSON local"""
        self.dedup_file = Path(f"./.pinecone_state_{self.namespace}.json")
        
        if self.dedup_file.exists():
            try:
                with open(self.dedup_file, 'r') as f:
                    state = json.load(f)
                    self.processed_docs = set(state.get('processed_docs', []))
                    print(f"   📋 État chargé: {len(self.processed_docs)} documents déjà traités")
            except Exception as e:
                print(f"   ⚠️  Erreur chargement état: {e}")
                self.processed_docs = set()
        else:
            self.processed_docs = set()
            print(f"   📋 Nouveau namespace (aucun document traité)")
    
    def _save_dedup_state(self):
        """Sauvegarder état déduplication"""
        try:
            state = {
                'namespace': self.namespace,
                'processed_docs': list(self.processed_docs),
                'last_update': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(self.dedup_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"   ⚠️  Erreur sauvegarde état: {e}")
    
    def _get_document_hash(self, file_path: Path) -> str:
        """Générer hash unique document (nom + taille + date modif)"""
        stat = file_path.stat()
        unique_str = f"{file_path.name}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.sha256(unique_str.encode()).hexdigest()
    
    def _is_document_processed(self, file_path: Path) -> bool:
        """Vérifier si document déjà traité"""
        doc_hash = self._get_document_hash(file_path)
        return doc_hash in self.processed_docs
    
    def _mark_document_processed(self, file_path: Path):
        """Marquer document comme traité"""
        doc_hash = self._get_document_hash(file_path)
        self.processed_docs.add(doc_hash)
        self._save_dedup_state()
    
    def _clean_text(self, text: str) -> str:
        """Nettoyage avancé du texte extrait"""
        text = re.sub(r'\n\d+\n', '\n', text)
        text = re.sub(r'\nPage \d+\n', '\n', text)
        
        lines = [line for line in text.split('\n') if len(line.strip()) > 20]
        text = '\n'.join(lines)
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'-\s+', '', text)
        
        return text.strip()
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Découper texte en chunks avec overlap"""
        text = self._clean_text(text)
        text = ' '.join(text.split())
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.strip()) > 300:
                chunks.append(chunk.strip())
        
        return chunks
    
    def _extract_text_from_pdf(self, pdf_path: Path, max_pages: int = 300) -> str:
        """
        Extraire texte d'un PDF avec pypdf (nouvelle version)
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)  # ← Utilisation de pypdf
                total_pages = len(reader.pages)
                
                print(f"      📄 {total_pages} pages détectées")
                
                pages_to_read = min(total_pages, max_pages)
                
                for i in range(pages_to_read):
                    page = reader.pages[i]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    if (i + 1) % 25 == 0 or i == pages_to_read - 1:
                        progress = (i + 1) / pages_to_read * 100
                        print(f"         → Page {i+1}/{pages_to_read} ({progress:.0f}%)")
                
                if total_pages > max_pages:
                    print(f"      ℹ️  Limité à {max_pages} premières pages (total: {total_pages})")
            
            return text.strip()
        
        except Exception as e:
            print(f"      ❌ Erreur lecture PDF: {e}")
            return ""
    
    def _load_text_file(self, file_path: Path) -> str:
        """Charger fichier texte avec multi-encoding"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read().strip()
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        print(f"      ⚠️  Impossible de décoder {file_path.name}")
        return ""
    
    def _generate_doc_id(self, text: str, doc_title: str, index: int) -> str:
        """Générer ID unique pour chunk"""
        unique_str = f"{self.namespace}_{doc_title}_{index}_{text[:50]}"
        hash_val = hashlib.md5(unique_str.encode()).hexdigest()[:16]
        return f"{self.namespace}_{hash_val}"
    
    def add_document(self, title: str, content: str, metadata: Dict = None, 
                     file_path: Optional[Path] = None):
        if file_path and self._is_document_processed(file_path):
            print(f"   ⏭️  '{title}' déjà traité (skip)")
            self.stats["skipped_duplicates"] += 1
            return
        
        if not content or len(content) < 200:
            print(f"   ⚠️  '{title}' trop court ({len(content)} chars), ignoré")
            self.stats["failed_documents"] += 1
            return
        
        print(f"\n   📄 Traitement: {title}")
        print(f"      📏 Taille: {len(content):,} caractères")
        self.stats["total_chars"] += len(content)
        
        chunks = self._chunk_text(content)
        
        if not chunks:
            print(f"   ⚠️  Aucun chunk généré")
            self.stats["failed_documents"] += 1
            return
        
        print(f"      ✂️  {len(chunks)} chunks générés")
        
        base_metadata = {
            "title": title,
            "source": metadata.get("source", "unknown") if metadata else "unknown",
            "type": metadata.get("type", "text") if metadata else "text",
            "namespace": self.namespace
        }
        
        print(f"      🔄 Vectorisation en cours...")
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
        
        vectors_to_upsert = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = self._generate_doc_id(chunk, title, i)
            
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_id": i,
                "total_chunks": len(chunks),
                "text": chunk[:5000]
            })
            
            vectors_to_upsert.append({
                "id": chunk_id,
                "values": embedding.tolist(),
                "metadata": chunk_metadata
            })
        
        batch_size = 100
        total_batches = (len(vectors_to_upsert) + batch_size - 1) // batch_size
        print(f"      ⬆️  Upload {total_batches} batch(s) vers namespace '{self.namespace}'...")
        
        for batch_num, i in enumerate(range(0, len(vectors_to_upsert), batch_size), 1):
            batch = vectors_to_upsert[i:i + batch_size]
            self.index.upsert(vectors=batch, namespace=self.namespace)
            if total_batches > 1:
                print(f"         → Batch {batch_num}/{total_batches}")
        
        print(f"   ✅ '{title}' ajouté ({len(chunks)} chunks)")
        
        if file_path:
            self._mark_document_processed(file_path)
        
        self.stats["total_documents"] += 1
        self.stats["total_chunks"] += len(chunks)
    
    def load_documents_from_directory(self, max_pages_pdf: int = 300):
        print(f"\n{'='*75}")
        print(f"📂 CHARGEMENT DOCUMENTS depuis {self.docs_dir.absolute()}")
        print(f"   Namespace: '{self.namespace}'")
        print(f"   Max pages PDF: {max_pages_pdf}")
        print(f"{'='*75}\n")
        
        files = list(self.docs_dir.iterdir())
        
        if not files:
            print("   ⚠️  Répertoire data/docs/ vide")
            return
        
        supported_files = [
            f for f in files 
            if f.is_file() and f.suffix.lower() in ['.pdf', '.txt', '.md']
        ]
        
        if not supported_files:
            print("   ⚠️  Aucun fichier supporté (.pdf, .txt, .md)")
            return
        
        print(f"📊 {len(supported_files)} fichiers détectés")
        print(f"{'─'*75}\n")
        
        for idx, file_path in enumerate(supported_files, 1):
            print(f"[{idx}/{len(supported_files)}] 📁 {file_path.name}")
            print(f"{'─'*75}")
            
            try:
                if file_path.suffix.lower() == '.pdf':
                    content = self._extract_text_from_pdf(file_path, max_pages_pdf)
                    if content:
                        self.add_document(
                            title=file_path.stem,
                            content=content,
                            metadata={"source": file_path.name, "type": "pdf"},
                            file_path=file_path
                        )
                    else:
                        print(f"   ⚠️  Contenu vide, ignoré")
                        self.stats["failed_documents"] += 1
                
                elif file_path.suffix.lower() in ['.txt', '.md']:
                    content = self._load_text_file(file_path)
                    if content:
                        self.add_document(
                            title=file_path.stem,
                            content=content,
                            metadata={"source": file_path.name, "type": "text"},
                            file_path=file_path
                        )
                    else:
                        print(f"   ⚠️  Contenu vide, ignoré")
                        self.stats["failed_documents"] += 1
            
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                self.stats["failed_documents"] += 1
        
        print(f"\n⏳ Synchronisation Pinecone (5s)...")
        time.sleep(5)
        
        self._print_final_stats()
    
    def _print_final_stats(self):
        print(f"\n{'='*75}")
        print("📊 STATISTIQUES FINALES")
        print(f"{'='*75}")
        print(f"✅ Documents traités:      {self.stats['total_documents']}")
        print(f"✅ Chunks générés:         {self.stats['total_chunks']}")
        print(f"✅ Caractères traités:     {self.stats['total_chars']:,}")
        print(f"⏭️  Doublons évités:       {self.stats['skipped_duplicates']}")
        print(f"❌ Échecs:                 {self.stats['failed_documents']}")
        
        stats = self.index.describe_index_stats()
        ns_stats = stats.get('namespaces', {}).get(self.namespace, {})
        vector_count = ns_stats.get('vector_count', 0)
        print(f"📦 Vecteurs namespace '{self.namespace}': {vector_count}")
        print(f"{'='*75}\n")
    
    def retrieve_context(self, query: str, n_results: int = 5, min_score: float = 0.3) -> List[Dict]:
        stats = self.index.describe_index_stats()
        ns_stats = stats.get('namespaces', {}).get(self.namespace, {})
        if ns_stats.get('vector_count', 0) == 0:
            print(f"⚠️  Namespace '{self.namespace}' vide")
            return []
        
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        results = self.index.query(
            vector=query_embedding,
            top_k=n_results,
            include_metadata=True,
            namespace=self.namespace
        )
        
        context_docs = []
        for match in results.get('matches', []):
            score = match['score']
            if score < min_score:
                continue
            
            context_docs.append({
                'id': match['id'],
                'score': score,
                'content': match['metadata'].get('text', ''),
                'metadata': {
                    'title': match['metadata'].get('title', 'N/A'),
                    'source': match['metadata'].get('source', 'N/A'),
                    'type': match['metadata'].get('type', 'N/A'),
                    'chunk_id': match['metadata'].get('chunk_id', 0),
                    'namespace': match['metadata'].get('namespace', self.namespace)
                }
            })
        
        return context_docs
    
    def clear_namespace(self):
        print(f"\n⚠️  Suppression namespace '{self.namespace}'...")
        try:
            self.index.delete(delete_all=True, namespace=self.namespace)
            print(f"✅ Namespace '{self.namespace}' vidé")
            
            if self.dedup_file.exists():
                self.dedup_file.unlink()
            self.processed_docs = set()
            print(f"✅ État déduplication réinitialisé")
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    def test_retrieval(self, test_queries: List[str]):
        print(f"\n{'='*75}")
        print(f"🧪 TEST DE RÉCUPÉRATION (namespace: '{self.namespace}')")
        print(f"{'='*75}\n")
        
        total_tests = len(test_queries)
        passed_tests = 0
        
        for idx, query in enumerate(test_queries, 1):
            print(f"[{idx}/{total_tests}] ❓ Requête: '{query}'")
            print(f"{'─'*75}")
            
            results = self.retrieve_context(query, n_results=3, min_score=0.3)
            
            if not results:
                print("   ❌ ÉCHEC: Aucun résultat pertinent (score < 0.3)\n")
                continue
            
            passed_tests += 1
            
            for i, doc in enumerate(results, 1):
                score_emoji = "🟢" if doc['score'] > 0.6 else "🟡" if doc['score'] > 0.4 else "🟠"
                print(f"\n   {score_emoji} Résultat {i} (Score: {doc['score']:.4f}):")
                print(f"      📌 Titre:  {doc['metadata']['title']}")
                print(f"      📁 Source: {doc['metadata']['source']}")
                print(f"      🏷️  Namespace: {doc['metadata']['namespace']}")
                print(f"      📝 Extrait: {doc['content'][:120]}...")
            
            print()
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"{'='*75}")
        print(f"📊 RÉSULTATS TESTS: {passed_tests}/{total_tests} réussis ({success_rate:.0f}%)")
        
        if success_rate >= 80:
            print("✅ MODULE 2 VALIDÉ (≥80% succès)")
        else:
            print("⚠️  MODULE 2 À AMÉLIORER (<80% succès)")
        
        print(f"{'='*75}\n")
    
    def get_stats(self):
        print(f"\n{'='*75}")
        print("📊 STATISTIQUES PINECONE")
        print(f"{'='*75}")
        
        stats = self.index.describe_index_stats()
        
        print(f"Index:              {self.index_name}")
        print(f"Namespace actuel:   {self.namespace}")
        print(f"Dimensions:         {self.dimension}")
        print(f"Métrique:           cosine")
        
        print(f"\n📦 Vecteurs par namespace:")
        namespaces = stats.get('namespaces', {})
        if namespaces:
            for ns_name, ns_stats in namespaces.items():
                count = ns_stats.get('vector_count', 0)
                print(f"   • {ns_name}: {count:,} vecteurs")
        else:
            print("   (aucun namespace)")
        
        total = stats.get('total_vector_count', 0)
        print(f"\n🔢 Total vecteurs:  {total:,}")
        print(f"{'='*75}\n")


# =========================================================
# ==================== POINT D'ENTRÉE =====================
# =========================================================

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║   MODULE 2 : RAG Setup ULTIME (Meilleurs des 2 versions)        ║
║   ✅ Namespaces • ✅ Dédup JSON • ✅ Clean avancé • ✅ Score    ║
╚═══════════════════════════════════════════════════════════════════╝
""")
    
    try:
        rag = OracleRAGSetup(namespace="module2")
    except ValueError as e:
        print(e)
        exit(1)
    
    # rag.clear_namespace()  # Décommenter pour réinitialiser
    
    rag.load_documents_from_directory(max_pages_pdf=300)
    
    rag.get_stats()
    
    test_queries = [
        "comment optimiser une requête lente avec des index",
        "best practices sécurité Oracle database",
        "stratégie de backup et recovery RMAN",
        "audit trail Oracle unified auditing",
        "full table scan problème de performance"
    ]
    
    rag.test_retrieval(test_queries)
    
    print(f"{'='*75}")
    print("✅ MODULE 2 TERMINÉ")
    print(f"{'='*75}")
    print("\n💡 Prochaines étapes:")
    print("   1. Vérifiez que tests ≥80% succès")
    print("   2. Relancez script → Aucun doublon créé")
    print("   3. Utilisez namespaces différents pour modules 4-8")
    print("   4. Passez au MODULE 3 (LLM Integration)\n")