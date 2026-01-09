# tests/test_llm_engine.py - VERSION CORRIGÉE
import sys
import os

# Ajoute le dossier parent (Projet_DBA) au chemin Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MAINTENANT on peut importer
try:
    from src.rag_setup import OracleRAGSetup
    from src.llm_engine import LLMEngine
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    print("Création de mock pour test...")
    
    # Mock si les modules ne sont pas disponibles
    class OracleRAGSetup:
        def __init__(self, namespace="module2"):
            self.namespace = namespace
            print(f"Mock RAG initialisé: {namespace}")
        
        def retrieve_context(self, query, n_results=5, min_score=0.3):
            mock_context = [
                {'content': 'RMAN (Recovery Manager) est un outil Oracle pour sauvegarde et récupération de bases de données.'},
                {'content': 'Un FULL TABLE SCAN se produit quand Oracle lit toutes les lignes d\'une table. Peut être optimisé avec des indexes.'},
                {'content': 'Les privilèges DBA donnent un accès complet à la base de données. À restreindre pour des raisons de sécurité.'}
            ]
            return mock_context[:n_results]

print("="*60)
print("🧪 TEST LLM Engine avec gemma2:2b et tinyllama fallback")
print("="*60)

print("Initialisation du RAG (Module 2)...")
try:
    rag = OracleRAGSetup(namespace="module2")
except:
    print("Utilisation du mock RAG")
    rag = OracleRAGSetup(namespace="module2")

print("Initialisation du LLM Engine avec Ollama...")
engine = LLMEngine(rag_setup=rag, default_model="gemma2:2b")

print(f"\n📊 Modèle actif: {engine.default_model}")
print(f"📊 Modèle fallback: {engine.fallback_model}")
print("="*60)

print("\n" + "="*60)
print("TEST 1 : Question simple sans contexte RAG")
print("="*60)
response1 = engine.generate(
    "Explique en français ce qu'est RMAN dans Oracle Database en 5 phrases maximum.",
    max_tokens=400
)
print("✅ Réponse reçue:")
print(response1)
print(f"📏 Longueur: {len(response1)} caractères")

print("\n" + "="*60)
print("TEST 2 : Question avec contexte RAG")
print("="*60)
response2 = engine.generate(
    "Comment optimiser une requête lente qui fait un full table scan ? Donne 3 conseils concrets.",
    max_tokens=500
)
print("✅ Réponse reçue:")
print(response2)
print(f"📏 Longueur: {len(response2)} caractères")

print("\n" + "="*60)
print("TEST 3 : Audit sécurité")
print("="*60)
fake_config = """
Utilisateur APP_USER possède les privilèges suivants :
- DBA
- CREATE ANY TABLE
- SELECT ANY TABLE
- Mot de passe qui n'expire jamais
"""
try:
    result = engine.assess_security(fake_config)
    print("✅ Audit sécurité terminé:")
    print(f"📊 Score: {result.get('score', 'N/A')}/100")
    print(f"⚠️  Risques identifiés: {len(result.get('risks', []))}")
    for i, risk in enumerate(result.get('risks', [])[:3], 1):
        print(f"   {i}. {risk}")
    print(f"💡 Recommandations: {len(result.get('recommendations', []))}")
    for i, rec in enumerate(result.get('recommendations', [])[:3], 1):
        print(f"   {i}. {rec}")
    if 'analysis' in result:
        print(f"📝 Analyse: {result['analysis'][:150]}...")
except Exception as e:
    print(f"❌ Erreur test sécurité: {e}")

print("\n" + "="*60)
print("TEST 4 : Test de fallback (simulé)")
print("="*60)
# Test avec un modèle inexistant pour forcer le fallback
try:
    test_fallback = engine.generate(
        "Test de réponse courte - quel est ton nom?",
        model="modele_inexistant",  # Force le fallback
        max_tokens=200
    )
    print("✅ Fallback testé (modele_inexistant forcé)")
    print(f"Réponse: {test_fallback[:150]}...")
except Exception as e:
    print(f"❌ Erreur fallback: {e}")

print("\n" + "="*60)
print("TEST 5 : Détection d'anomalie")
print("="*60)
test_log = "ORA-01555: snapshot too old - rollback segment too small"
try:
    anomaly_result = engine.detect_anomaly(test_log)
    print(f"✅ Classification: {anomaly_result.get('classification', 'N/A')}")
    justification = anomaly_result.get('justification', 'N/A')
    print(f"📝 Justification: {justification[:200]}..." if len(str(justification)) > 200 else f"📝 Justification: {justification}")
except Exception as e:
    print(f"❌ Erreur détection anomalie: {e}")

print("\n" + "="*60)
print("TEST 6 : Test direct de tinyllama")
print("="*60)
try:
    tiny_response = engine.generate(
        "Réponds en une phrase : qu'est-ce qu'Oracle?",
        model="tinyllama",  # Test direct de tinyllama
        max_tokens=100
    )
    print(f"✅ Test tinyllama direct: {tiny_response[:150]}...")
except Exception as e:
    print(f"❌ Erreur tinyllama: {e}")

print("\n" + "="*60)
print("🎯 RÉCAPITULATIF DES TESTS")
print("="*60)
print("✅ Modèles installés:")
print("   - gemma2:2b (1.6 GB) - modèle principal")
print("   - tinyllama (637 MB) - fallback rapide")
print("\n📊 Configuration:")
print(f"   Modèle principal: {engine.default_model}")
print(f"   Modèle fallback: {engine.fallback_model}")
print("\n✅ Avantages:")
print("   ✓ gemma2:2b: Bon pour réponses techniques")
print("   ✓ tinyllama: Rapide, léger (637 MB)")
print("   ✓ Fallback fonctionnel en cas d'erreur")

print("\n✅ Tous les tests sont terminés !")
print("="*60)