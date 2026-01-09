# src/llm_engine.py - VERSION COMPLÈTE SANS ERREUR DE SYNTAXE
import ollama
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional, Dict, Any
import time

# Importer le RAG du Module 2
from src.rag_setup import OracleRAGSetup

class LLMEngine:
    """
    Hub central pour intégration LLM avec Prompt Engineering et RAG.
    Optimisé pour gemma2:2b avec fallback tinyllama.
    """
    def __init__(self, rag_setup: OracleRAGSetup, prompts_file: str = "data/prompts.yaml", default_model: str = "gemma2:2b"):
        self.rag = rag_setup  # Instance RAG du Module 2
        self.default_model = default_model  # Maintenant gemma2:2b
        self.prompts = self._load_prompts(prompts_file)
        self.fallback_model = "tinyllama"  # ⚠️ CORRIGÉ : tinyllama au lieu de phi3:mini

    def _load_prompts(self, file_path: str) -> Dict:
        """Charger tous les prompts depuis YAML."""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  prompts.yaml non trouvé, utilisation des prompts par défaut: {e}")
            # Retourner des prompts par défaut si fichier manquant
            return self._get_default_prompts()

    def _get_default_prompts(self) -> Dict:
        """Retourne des prompts par défaut si le fichier YAML est manquant."""
        return {
            'module4': {
                'assess_security': """Analyse de sécurité Oracle :
Configuration : {config}
Identifie les risques de sécurité, donne un score sur 100 et des recommandations concrètes.
Format de réponse : 
- Score : /100
- Risques identifiés : liste
- Recommandations : liste"""
            },
            'module5': {
                'analyze_query': """Analyse de requête SQL Oracle :
Requête : {sql_query}
Plan d'exécution : {plan}
Analyse les problèmes de performance et propose des optimisations.
Format : Explication + recommandations d'index, restructuration, etc."""
            },
            'module6': {
                'detect_anomaly': """Détection d'anomalie dans logs Oracle :
Entrée de log : {log_entry}
Analyse si c'est normal ou suspect. Justifie la classification.
Format : Classification (NORMAL/SUSPECT/CRITIQUE) + Justification"""
            }
        }

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(2),  # Réduit à 2 tentatives
        wait=wait_exponential(multiplier=1, min=2, max=5)
    )
    def generate(self, prompt: str, context: Optional[str] = None, model: Optional[str] = None, max_tokens: int = 800) -> str:
        """
        Appel LLM optimisé pour gemma2:2b.
        Si context=None, utilise RAG pour le fetcher.
        """
        model = model or self.default_model
        
        if context is None:
            # Fetch context via RAG du Module 2
            try:
                rag_results = self.rag.retrieve_context(prompt, n_results=4, min_score=0.25)
                context = "\n".join([doc['content'][:500] for doc in rag_results]) if rag_results else ""
            except Exception as e:
                print(f"⚠️  Erreur RAG: {e}")
                context = ""

        # Prompt optimisé pour gemma2:2b
        if context:
            full_prompt = f"""Instruction : Réponds en français de manière concise et technique.
Contexte pertinent : {context}

Question : {prompt}

Réponse :"""
        else:
            full_prompt = f"""Instruction : Réponds en français de manière concise et technique.
Question : {prompt}

Réponse :"""

        try:
            # Appel Ollama avec paramètres optimisés
            start_time = time.time()
            response = ollama.generate(
                model=model,
                prompt=full_prompt,
                options={
                    'num_predict': max_tokens,
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'repeat_penalty': 1.1
                }
            )['response']
            
            elapsed = time.time() - start_time
            if elapsed > 25:
                print(f"⚠️  Réponse lente: {elapsed:.1f}s")
            
            return response.strip()
            
        except Exception as e:
            print(f"❌ Erreur LLM ({model}): {e} → Fallback à {self.fallback_model}")
            try:
                # Fallback avec tinyllama - prompt simplifié
                fallback_prompt = f"Q: {prompt[:500]}\nA (en français, court):"
                response = ollama.generate(
                    model=self.fallback_model,
                    prompt=fallback_prompt,
                    options={'num_predict': min(300, max_tokens), 'temperature': 0.4}
                )['response']
                return f"[tinyllama fallback] {response.strip()}"
            except Exception as fallback_error:
                print(f"❌ Fallback aussi en échec: {fallback_error}")
                # Dernier recours
                return f"[Erreur] Aucun modèle disponible. Installez au moins 'gemma2:2b' ou 'tinyllama'."

    def analyze_query(self, sql_query: str, plan: str) -> Dict[str, Any]:
        """Pour Module 5: Optimisation de requêtes."""
        try:
            prompt_template = self.prompts.get('module5', {}).get('analyze_query', 
                "Analyse cette requête SQL: {sql_query}\nPlan: {plan}\nSuggestions:")
            prompt = prompt_template.format(sql_query=sql_query, plan=plan)
            response = self.generate(prompt, max_tokens=600)
            
            return {
                "explanation": response,
                "recommendations": self._extract_recommendations(response),
                "model_used": self.default_model
            }
        except Exception as e:
            return {"error": str(e), "explanation": "Erreur d'analyse"}

    def _extract_recommendations(self, text: str) -> list:
        """Extrait les recommandations de la réponse."""
        recommendations = []
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in 
                   ['recommande', 'suggère', 'ajoute', 'crée', 'index', 'optimise', 'conseil']):
                recommendations.append(line.strip())
        return recommendations[:5]

    def assess_security(self, config: str) -> Dict[str, Any]:
        """Pour Module 4: Audit sécurité."""
        try:
            prompt_template = self.prompts.get('module4', {}).get('assess_security', 
                "Analyse sécurité Oracle: {config}\nRisques et recommandations:")
            prompt = prompt_template.format(config=config)
            response = self.generate(prompt, max_tokens=700)
            
            # Parsing amélioré
            score = 75
            try:
                import re
                score_match = re.search(r'(\d{1,3})/100', response.lower())
                if score_match:
                    score = min(100, max(0, int(score_match.group(1))))
            except:
                pass
            
            return {
                "score": score,
                "risks": self._extract_risks(response),
                "recommendations": self._extract_recommendations(response),
                "analysis": response[:500],
                "model_used": self.default_model
            }
        except Exception as e:
            return {"error": str(e), "score": 0, "risks": []}

    def _extract_risks(self, text: str) -> list:
        """Extrait les risques identifiés."""
        risks = []
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(risk_word in line_lower for risk_word in 
                   ['risque', 'vulnérabilité', 'danger', 'problème', 'faible', 'critique']):
                if 'score' not in line_lower:
                    risks.append(line.strip())
        return risks[:5]

    def detect_anomaly(self, log_entry: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Pour Module 6: Détection anomalies - VERSION CORRIGÉE SANS ERREUR SYNTAXE."""
        try:
            # 1. Récupération sécurisée du template
            prompt_template = None
            
            # Vérifie si prompts est un dict et a module6
            if isinstance(self.prompts, dict):
                module6 = self.prompts.get('module6')
                if isinstance(module6, dict):
                    prompt_template = module6.get('detect_anomaly')
            
            # 2. Template par défaut si nécessaire
            if not prompt_template or not isinstance(prompt_template, str):
                prompt_template = "Analyse de log Oracle:\nLog: {log_entry}\nCette entrée est-elle normale, suspecte ou critique? Justifie en français."
            
            # 3. Formatage sécurisé
            try:
                prompt = prompt_template.format(log_entry=log_entry)
            except:
                # Fallback simple
                prompt = f"Analyse ce log Oracle: {log_entry}\nClassification et justification:"
            
            # 4. Génération de la réponse
            response = self.generate(prompt, context=context, max_tokens=350)
            
            # 5. Analyse de la classification
            response_lower = response.lower()
            classification = "NORMAL"
            
            # Définir les mots-clés
            critical_keywords = ['critique', 'critical', 'urgence', 'emergency', 'fatal', 'grave', 'panne']
            suspect_keywords = ['suspect', 'anormal', 'anomal', 'warning', 'avertissement', 'problème', 'anomalie']
            
            # Vérifier d'abord les critères critiques
            if any(word in response_lower for word in critical_keywords):
                classification = "CRITIQUE"
            # Ensuite vérifier les suspects
            elif any(word in response_lower for word in suspect_keywords):
                classification = "SUSPECT"
            # Sinon reste "NORMAL" (valeur par défaut)
            
            # 6. Confiance
            confidence = "medium"
            if classification == "NORMAL" and len(response) < 30:
                confidence = "low"
            elif len(response) > 100 and ('car' in response_lower or 'parce que' in response_lower or 'caractéristique' in response_lower):
                confidence = "high"
            
            return {
                "classification": classification,
                "justification": response,
                "confidence": confidence,
                "model_used": self.default_model
            }
            
        except Exception as e:
            # Erreur détaillée pour debugging
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Erreur détection anomalie: {e}")
            
            return {
                "classification": "ERROR",
                "justification": f"Erreur d'analyse: {str(e)[:80]}",
                "confidence": "none",
                "error": str(e)[:100]
            }

# Test optimisé
if __name__ == "__main__":
    try:
        rag = OracleRAGSetup(namespace="module2")
        engine = LLMEngine(rag_setup=rag, default_model="gemma2:2b")
        
        print("🔧 Test LLM Engine avec gemma2:2b et fallback tinyllama")
        print("=" * 50)
        
        # Test 1
        test_response = engine.generate(
            "Explique ce plan d'exécution en termes simples", 
            context="Exemple plan: FULL TABLE SCAN sur table EMPLOYES avec 1M lignes",
            max_tokens=300
        )
        print(f"Test 1 - Réponse ({len(test_response)} chars):")
        print(test_response[:200] + "..." if len(test_response) > 200 else test_response)
        print()
        
        # Test 2
        security_test = engine.assess_security("Utilisateur TEST avec privilege DBA")
        print(f"Test 2 - Audit sécurité: Score {security_test.get('score', 'N/A')}")
        print(f"Risques: {security_test.get('risks', [])[:2]}")
        
        # Test 3 - Détection d'anomalie
        print("\nTest 3 - Détection d'anomalie:")
        anomaly_logs = [
            "ORA-01555: snapshot too old - rollback segment too small",
            "Completed: ALTER DATABASE OPEN",
            "TNS-12535: TNS:operation timed out"
        ]
        
        for log in anomaly_logs:
            result = engine.detect_anomaly(log)
            print(f"  Log: {log[:50]}...")
            print(f"    → Classification: {result.get('classification')}")
            print(f"    → Confiance: {result.get('confidence')}")
            print()
        
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        print("Test avec mock RAG...")
        class MockRAG:
            def retrieve_context(self, query, n_results=4, min_score=0.25):
                return [{'content': 'Oracle Database - Système de gestion de base de données relationnelle'}]
        
        engine = LLMEngine(rag_setup=MockRAG(), default_model="gemma2:2b")
        test = engine.generate("Qu'est-ce qu'Oracle?")
        print(f"Test mock: {test[:100]}...")