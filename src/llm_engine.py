# src/llm_engine.py - VERSION FINALE COMPLÈTE AVEC SCORING CORRIGÉ
import ollama
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional, Dict, Any
import time
import re

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
        self.fallback_model = "tinyllama"

    def _load_prompts(self, file_path: str) -> Dict:
        """Charger tous les prompts depuis YAML."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  prompts.yaml non trouvé, utilisation des prompts par défaut: {e}")
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
        stop=stop_after_attempt(2),
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
                rag_results = self.rag.retrieve_context(prompt, n_results=3, min_score=0.4)
                context = "\n".join([doc['content'][:200] for doc in rag_results]) if rag_results else ""
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
                    'num_predict': 1500,
                    'temperature': 0.4,
                    'top_p': 0.95,
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
        """Extrait les recommandations de la réponse - VERSION AMÉLIORÉE."""
        recommendations = []
        lines = text.split('\n')
        
        # Mots-clés de recommandations
        rec_keywords = ['recommande', 'suggère', 'devrait', 'conseil', 'il faut', 
                        'restreindre', 'limiter', 'créer', 'ajouter', 'utiliser',
                        'configurer', 'activer', 'désactiver']
        
        for line in lines:
            line_clean = line.strip()
            line_lower = line_clean.lower()
            
            # Ignorer lignes trop courtes
            if len(line_clean) < 15:
                continue
            
            # Si ligne commence par bullet ou numéro
            if line_clean.startswith(('-', '•', '*')) or (line_clean and line_clean[0].isdigit()):
                clean = line_clean.lstrip('-•*0123456789. ').strip()
                if len(clean) > 15:
                    recommendations.append(clean)
            # Ou si contient mot-clé de recommandation
            elif any(keyword in line_lower for keyword in rec_keywords):
                # Ne pas ajouter si c'est un header
                if ':' not in line_clean[:30]:
                    recommendations.append(line_clean)
        
        return recommendations[:10]  # Max 10

    def assess_security(self, config: str) -> Dict[str, Any]:
        """Pour Module 4: Audit sécurité - VERSION FINALE AVEC SCORING PAR RÈGLES."""
        try:
            # Prompt optimisé avec instructions STRICTES sur le scoring
            prompt_optimise = f"""Tu es un expert en sécurité Oracle Database.

CONFIGURATION À ANALYSER :
{config}

INSTRUCTIONS IMPORTANTES :
- Un utilisateur avec DBA = TRÈS DANGEREUX → Score < 40
- CREATE ANY TABLE / SELECT ANY TABLE = DANGEREUX → Score < 60
- Mot de passe sans expiration = RISQUE → -20 points
- Chaque privilège excessif = -15 points

RÉPONSE REQUISE (suis ce format EXACTEMENT, une ligne par item) :

SCORE: [nombre entre 0 et 100]

RISQUES DÉTECTÉS:
- Privilège DBA accorde un accès administrateur complet
- CREATE ANY TABLE permet création dans tous les schémas
- SELECT ANY TABLE donne accès à toutes les données
- Mot de passe sans expiration facilite les attaques

RECOMMANDATIONS:
- Révoquer le privilège DBA immédiatement
- Limiter à CREATE TABLE dans le schéma propriétaire uniquement
- Configurer PASSWORD_LIFE_TIME à 90 jours
- Implémenter le principe du moindre privilège

Réponds en français. IMPORTANT : Sois SÉVÈRE dans ton scoring."""

            # Génération
            response = self.generate(prompt_optimise, max_tokens=700)
            
            # ÉTAPE 1 : Calcul du score par RÈGLES (plus fiable que LLM)
            config_lower = config.lower()
            score = 100  # Score de départ parfait
            
            # Pénalités automatiques basées sur mots-clés
            if 'dba' in config_lower:
                score -= 40  # TRÈS SÉVÈRE : accès complet
            if 'create any table' in config_lower:
                score -= 20  # Peut créer partout
            if 'select any table' in config_lower:
                score -= 20  # Peut lire partout
            if 'drop any' in config_lower:
                score -= 15  # Peut supprimer partout
            if "n'expire" in config_lower or 'never expire' in config_lower or 'jamais' in config_lower:
                score -= 15  # Mot de passe éternel
            if 'unlimited tablespace' in config_lower:
                score -= 10  # Peut remplir le disque
            if 'sysdba' in config_lower or 'sysoper' in config_lower:
                score -= 30  # Privilèges système
            
            # S'assurer que le score reste dans [0, 100]
            score = max(0, min(100, score))
            
            # ÉTAPE 2 : Extraction des RISQUES avec parsing amélioré
            risks = []
            
            # Chercher la section RISQUES DÉTECTÉS
            risk_section = re.search(r'RISQUES[^:]*:(.*?)(?=RECOMMANDATIONS|ANALYSE|$)', 
                                     response, re.IGNORECASE | re.DOTALL)
            
            if risk_section:
                risk_text = risk_section.group(1)
                for line in risk_text.split('\n'):
                    line = line.strip()
                    # Extraire les lignes avec bullets
                    if line.startswith(('-', '•', '*', '–')):
                        clean_risk = line.lstrip('-•*– ').strip()
                        # Retirer les "**" markdown
                        clean_risk = re.sub(r'\*\*', '', clean_risk)
                        # Retirer les deux-points et texte après si pattern "Titre: Description"
                        if ':' in clean_risk:
                            parts = clean_risk.split(':', 1)
                            if len(parts[0]) > 50:  # Si titre long, garder tout
                                clean_risk = clean_risk
                            else:  # Sinon prendre la description après ":"
                                clean_risk = parts[1].strip() if len(parts) > 1 else parts[0]
                        
                        if len(clean_risk) > 15:  # Ignorer trop court
                            risks.append(clean_risk)
            
            # Fallback : chercher dans tout le texte si section non trouvée
            if not risks:
                risk_keywords = ['dba', 'privilège', 'any table', 'expire', 'risque', 'vulnérabilité', 'danger']
                for line in response.split('\n'):
                    if any(kw in line.lower() for kw in risk_keywords):
                        clean = line.strip().lstrip('-•*– ')
                        clean = re.sub(r'\*\*', '', clean)
                        if 15 < len(clean) < 300:  # Longueur raisonnable
                            risks.append(clean)
            
            # ÉTAPE 3 : Extraction des RECOMMANDATIONS
            recommendations = []
            
            rec_section = re.search(r'RECOMMANDATIONS[^:]*:(.*?)(?=ANALYSE|$)', 
                                   response, re.IGNORECASE | re.DOTALL)
            
            if rec_section:
                rec_text = rec_section.group(1)
                for line in rec_text.split('\n'):
                    line = line.strip()
                    if line.startswith(('-', '•', '*', '–')) or (line and line[0].isdigit()):
                        clean_rec = line.lstrip('-•*–0123456789. ').strip()
                        clean_rec = re.sub(r'\*\*', '', clean_rec)
                        
                        # Retirer préfixes type "Exemple:", "Note:", etc.
                        if ':' in clean_rec[:30]:
                            parts = clean_rec.split(':', 1)
                            if parts[0].strip() in ['Exemple', 'Note', 'Important']:
                                clean_rec = parts[1].strip() if len(parts) > 1 else clean_rec
                        
                        if len(clean_rec) > 15:
                            recommendations.append(clean_rec)
            
            # Fallback pour recommandations
            if not recommendations:
                rec_keywords = ['recommande', 'devrait', 'révoquer', 'limiter', 'configurer', 
                               'implémenter', 'activer', 'désactiver', 'restreindre']
                for line in response.split('\n'):
                    if any(kw in line.lower() for kw in rec_keywords):
                        clean = line.strip().lstrip('-•*– ')
                        clean = re.sub(r'\*\*', '', clean)
                        if 15 < len(clean) < 300 and ':' not in clean[:20]:
                            recommendations.append(clean)
            
            # ÉTAPE 4 : Extraction de l'analyse générale
            analysis = response[:500]
            analysis_match = re.search(r'ANALYSE[^:]*:(.*)', response, re.IGNORECASE | re.DOTALL)
            if analysis_match:
                analysis = analysis_match.group(1).strip()[:500]
            
            return {
                "score": score,  # ⭐ Score calculé par RÈGLES (fiable)
                "risks": risks[:10],  # Max 10 risques
                "recommendations": recommendations[:10],  # Max 10 recommandations
                "analysis": analysis,
                "model_used": self.default_model,
                "scoring_method": "rule-based"  # Indiquer méthode de calcul
            }
            
        except Exception as e:
            print(f"❌ Erreur assess_security: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e), "score": 0, "risks": [], "recommendations": []}

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
        """Pour Module 6: Détection anomalies - VERSION AMÉLIORÉE avec règles."""
        
        # ÉTAPE 1 : Classification par RÈGLES (plus fiable que LLM)
        log_lower = log_entry.lower()
        classification = "NORMAL"
        severity = "BASSE"
        
        # Dictionnaire des erreurs critiques Oracle
        critical_errors = {
            'ora-00600': ('CRITIQUE', 'CRITIQUE', 'Erreur interne Oracle - Nécessite support Oracle'),
            'ora-00700': ('CRITIQUE', 'CRITIQUE', 'Soft internal error - Vérifier alertes'),
            'ora-01555': ('CRITIQUE', 'HAUTE', 'Snapshot too old - Augmenter UNDO_RETENTION'),
            'ora-01652': ('CRITIQUE', 'HAUTE', 'Tablespace temporaire plein - Augmenter TEMP'),
            'ora-00257': ('CRITIQUE', 'CRITIQUE', 'Archiver error - Espace disque insuffisant'),
            'ora-27037': ('CRITIQUE', 'HAUTE', 'Erreur I/O fichier - Vérifier disque'),
            'tns-12535': ('CRITIQUE', 'HAUTE', 'Timeout réseau - Vérifier connectivité'),
            'tns-12560': ('CRITIQUE', 'HAUTE', 'Erreur adaptateur protocole'),
        }
        
        suspect_errors = {
            'ora-00942': ('SUSPECT', 'MOYENNE', 'Table inexistante ou privilèges manquants'),
            'ora-01017': ('SUSPECT', 'MOYENNE', 'Login/password invalide - Possible attaque'),
            'ora-12154': ('SUSPECT', 'BASSE', 'TNS service name non résolu'),
            'ora-28000': ('SUSPECT', 'MOYENNE', 'Compte verrouillé - Tentatives login multiples'),
        }
        
        # Vérifier les erreurs
        justification_rule = None
        for error_code, (classif, sev, justif) in critical_errors.items():
            if error_code in log_lower:
                classification = classif
                severity = sev
                justification_rule = justif
                break
        
        if not justification_rule:
            for error_code, (classif, sev, justif) in suspect_errors.items():
                if error_code in log_lower:
                    classification = classif
                    severity = sev
                    justification_rule = justif
                    break
        
        # ÉTAPE 2 : Si règle trouvée, retourner directement (plus rapide et fiable)
        if justification_rule:
            return {
                "classification": classification,
                "justification": justification_rule,
                "severity": severity,
                "confidence": "high",  # Haute confiance car basé sur règles
                "model_used": "rule-based",
                "log_entry": log_entry[:100]
            }
        
        # ÉTAPE 3 : Si pas de règle, utiliser le LLM (pour cas complexes)
        try:
            prompt_detect = f"""Analyse ce log Oracle :

LOG: {log_entry}

Est-ce NORMAL, SUSPECT ou CRITIQUE ?

RÉPONSE REQUISE (format exact) :
CLASSIFICATION: [NORMAL ou SUSPECT ou CRITIQUE]
JUSTIFICATION: [Explique en 1-2 phrases]

Réponds en français."""

            response = self.generate(prompt_detect, context=context, max_tokens=300)
            
            # Parsing de la réponse LLM
            response_lower = response.lower()
            
            # Extraction classification
            class_match = re.search(r'CLASSIFICATION\s*:\s*(\w+)', response, re.IGNORECASE)
            if class_match:
                classification = class_match.group(1).upper()
            else:
                # Fallback : chercher mots-clés
                if 'critique' in response_lower or 'critical' in response_lower:
                    classification = "CRITIQUE"
                elif 'suspect' in response_lower or 'anormal' in response_lower:
                    classification = "SUSPECT"
                else:
                    classification = "NORMAL"
            
            # Extraction justification
            justif_match = re.search(r'JUSTIFICATION\s*:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
            justification = justif_match.group(1).strip()[:200] if justif_match else response[:200]
            
            # Inférer sévérité
            severity_map = {'CRITIQUE': 'CRITIQUE', 'SUSPECT': 'MOYENNE', 'NORMAL': 'BASSE'}
            severity = severity_map.get(classification, 'MOYENNE')
            
            return {
                "classification": classification,
                "justification": justification,
                "severity": severity,
                "confidence": "medium",  # Confiance moyenne car LLM
                "model_used": self.default_model
            }
        
        except Exception as e:
            print(f"❌ Erreur LLM detect_anomaly: {e}")
            # Fallback final
            return {
                "classification": "NORMAL",
                "justification": f"Impossible d'analyser ce log. Erreur: {str(e)[:50]}",
                "severity": "BASSE",
                "confidence": "low",
                "error": str(e)
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
            max_tokens=1500
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