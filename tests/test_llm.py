#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST MODULE 2 : Vérification RAG Setup avec recherche sémantique
Ce script teste la recherche vectorielle dans votre index Pinecone
"""

import sys
import time
from pathlib import Path

# Ajouter le chemin parent pour importer vos modules
sys.path.append(str(Path(__file__).parent.parent))

# Importer vos modules
from rag_setup import OracleRAGSetup
from llm_engine import LLMEngine

def test_basic_semantic_search():
    """Test basique de recherche sémantique"""
    print("\n" + "="*80)
    print("🧪 TEST 1: Recherche sémantique basique")
    print("="*80)
    
    try:
        # Initialiser RAG setup
        rag = OracleRAGSetup(namespace="module2")
        
        # Vérifier les stats de l'index
        print("\n📊 Statistiques de l'index:")
        rag.get_stats()
        
        # Requêtes de test
        test_queries = [
            "optimisation requête SQL",
            "index Oracle performance",
            "sécurité base de données",
            "backup RMAN stratégie",
            "analyse plan d'exécution"
        ]
        
        print("\n🔍 Test de recherche sémantique:")
        for query in test_queries:
            print(f"\n{'─'*40}")
            print(f"❓ Requête: '{query}'")
            results = rag.retrieve_context(query, n_results=3, min_score=0.1)
            
            if results:
                print(f"✅ {len(results)} résultat(s) trouvé(s):")
                for i, result in enumerate(results, 1):
                    print(f"\n  📌 Résultat {i}:")
                    print(f"     Score: {result['score']:.4f}")
                    print(f"     Titre: {result['metadata']['title']}")
                    print(f"     Source: {result['metadata']['source']}")
                    print(f"     Extrait: {result['content'][:100]}...")
            else:
                print(f"❌ Aucun résultat pour cette requête")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

def test_llm_integration():
    """Test d'intégration avec LLM"""
    print("\n" + "="*80)
    print("🧪 TEST 2: Intégration LLM avec RAG")
    print("="*80)
    
    try:
        # Initialiser LLM Engine
        llm = LLMEngine()
        
        # Initialiser RAG
        rag = OracleRAGSetup(namespace="module2")
        
        
        
        # Questions de test avec RAG
        test_questions = [
            "Comment optimiser une requête lente avec des index?",
            "Quelles sont les meilleures pratiques de sécurité Oracle?",
            "Comment fonctionne RMAN pour les backups?"
        ]
        
        for question in test_questions:
            print(f"\n{'─'*40}")
            print(f"🤖 Question: {question}")
            
            # Recherche vectorielle
            print("🔍 Recherche dans Pinecone...")
            context_results = rag.retrieve_context(question, n_results=3)
            
            if context_results:
                print(f"✅ {len(context_results)} contexte(s) trouvé(s)")
                
                # Afficher les résultats de recherche
                print("\n📊 Résultats de recherche vectorielle:")
                for i, result in enumerate(context_results, 1):
                    print(f"  {i}. [{result['score']:.4f}] {result['metadata']['title']}")
                
                # Générer réponse avec contexte
                print("\n💭 Génération de réponse avec contexte...")
                response = llm.query_with_vector_context(
                    user_prompt=question,
                    vector_results=context_results,
                    show_results=False  # On affichera manuellement
                )
                
                # Afficher la réponse
                print("\n💡 Réponse LLM:")
                print(f"  {response[:200]}...")
            else:
                print("❌ Aucun contexte trouvé pour cette question")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

def test_similarity_scores():
    """Test des scores de similarité"""
    print("\n" + "="*80)
    print("🧪 TEST 3: Analyse des scores de similarité")
    print("="*80)
    
    try:
        rag = OracleRAGSetup(namespace="module2")
        
        # Paire de requêtes avec similarité attendue
        query_pairs = [
            ("optimisation requête", "performance SQL"),
            ("sécurité Oracle", "audit base de données"),
            ("backup RMAN", "stratégie sauvegarde")
        ]
        
        for query1, query2 in query_pairs:
            print(f"\n{'─'*40}")
            print(f"Comparaison: '{query1}' vs '{query2}'")
            
            # Résultats pour query1
            results1 = rag.retrieve_context(query1, n_results=1, min_score=0)
            results2 = rag.retrieve_context(query2, n_results=1, min_score=0)
            
            if results1 and results2:
                doc1 = results1[0]
                doc2 = results2[0]
                
                print(f"📌 Document trouvé pour '{query1}':")
                print(f"   Titre: {doc1['metadata']['title']}")
                print(f"   Score: {doc1['score']:.4f}")
                
                print(f"\n📌 Document trouvé pour '{query2}':")
                print(f"   Titre: {doc2['metadata']['title']}")
                print(f"   Score: {doc2['score']:.4f}")
                
                # Vérifier si c'est le même document
                if doc1['id'] == doc2['id']:
                    print(f"\n✅ Même document retrouvé pour les deux requêtes")
                else:
                    print(f"\n⚠️  Documents différents trouvés")
            else:
                print("❌ Pas assez de résultats pour comparer")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

def test_edge_cases():
    """Test des cas limites"""
    print("\n" + "="*80)
    print("🧪 TEST 4: Cas limites et erreurs")
    print("="*80)
    
    try:
        rag = OracleRAGSetup(namespace="module2")
        
        # Test avec requête vide
        print("\n❓ Test avec requête vide:")
        results = rag.retrieve_context("", n_results=3)
        print(f"Résultats: {len(results)}")
        
        # Test avec requête très longue
        print("\n❓ Test avec requête très longue:")
        long_query = " " + "optimisation " * 50 + " "
        results = rag.retrieve_context(long_query, n_results=3)
        print(f"Résultats: {len(results)}")
        
        # Test avec caractères spéciaux
        print("\n❓ Test avec caractères spéciaux:")
        special_query = "SQL injection ' OR '1'='1"
        results = rag.retrieve_context(special_query, n_results=3)
        print(f"Résultats: {len(results)}")
        
        # Test avec min_score élevé
        print("\n❓ Test avec min_score=0.8 (très restrictif):")
        results = rag.retrieve_context("Oracle", n_results=3, min_score=0.8)
        print(f"Résultats avec score >0.8: {len(results)}")
        
        # Test avec min_score bas
        print("\n❓ Test avec min_score=0.0 (peu restrictif):")
        results = rag.retrieve_context("Oracle", n_results=3, min_score=0.0)
        print(f"Résultats avec score >0.0: {len(results)}")
        
        if results:
            print("\n📊 Distribution des scores:")
            for result in results:
                print(f"  Score: {result['score']:.4f}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

def test_complete_workflow():
    """Test du workflow complet"""
    print("\n" + "="*80)
    print("🧪 TEST 5: Workflow complet RAG + LLM")
    print("="*80)
    
    try:
        # Initialiser les deux modules
        llm = LLMEngine()
        rag = OracleRAGSetup(namespace="module2")
        
        # Workflow complet
        user_question = "Comment créer un index pour améliorer les performances?"
        
        print(f"\n👤 Question utilisateur: {user_question}")
        
        # Étape 1: Recherche vectorielle
        print("\n1️⃣ Recherche vectorielle dans Pinecone...")
        context_results = rag.retrieve_context(user_question, n_results=3, min_score=0.3)
        
        if not context_results:
            print("❌ Aucun contexte trouvé. Utilisation de LLM seul.")
            response = llm.generate(user_question)
            print(f"\n🤖 Réponse (sans contexte):\n{response}")
            return True
        
        print(f"✅ {len(context_results)} contexte(s) trouvé(s)")
        
        # Étape 2: Affichage des résultats vectoriels
        print("\n2️⃣ Résultats de recherche vectorielle:")
        print("-"*60)
        
        for i, result in enumerate(context_results, 1):
            print(f"\n📌 Résultat {i}:")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Titre: {result['metadata']['title']}")
            print(f"   Source: {result['metadata']['source']}")
            print(f"   Extrait: {result['content'][:150]}...")
        
        print("-"*60)
        
        # Étape 3: Génération avec LLM
        print("\n3️⃣ Génération de réponse avec LLM...")
        
        # Préparer le contexte formaté
        formatted_context = ""
        for i, result in enumerate(context_results, 1):
            formatted_context += f"[Document {i}]\n"
            formatted_context += f"Titre: {result['metadata']['title']}\n"
            formatted_context += f"Contenu: {result['content'][:500]}\n"
            formatted_context += f"Score de pertinence: {result['score']:.4f}\n"
            formatted_context += "-"*40 + "\n"
        
        # Générer la réponse
        prompt = f"""En utilisant les documents contextuels ci-dessous, réponds à la question de l'utilisateur.

Documents contextuels:
{formatted_context}

Question: {user_question}

Réponse:"""
        
        response = llm.generate(prompt)
        
        print("\n4️⃣ Réponse finale:")
        print("="*60)
        print(response)
        print("="*60)
        
        # Étape 4: Évaluation de la qualité
        print("\n5️⃣ Évaluation de la réponse:")
        evaluation_prompt = f"""Évalue la qualité de cette réponse basée sur les critères suivants:
1. Pertinence par rapport à la question
2. Utilisation du contexte fourni
3. Précision technique
4. Clarté de l'explication

Question: {user_question}

Réponse: {response[:500]}...

Note sur 10 et commentaires:"""
        
        evaluation = llm.generate(evaluation_prompt)
        print(f"\n📈 Évaluation:\n{evaluation}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le workflow: {e}")
        return False

def run_all_tests():
    """Exécuter tous les tests"""
    print("\n" + "="*80)
    print("🚀 LANCEMENT DE TOUS LES TESTS RAG")
    print("="*80)
    
    tests = [
        ("Recherche sémantique basique", test_basic_semantic_search),
        ("Intégration LLM", test_llm_integration),
        ("Scores de similarité", test_similarity_scores),
        ("Cas limites", test_edge_cases),
        ("Workflow complet", test_complete_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n▶️  Début test: {test_name}")
        start_time = time.time()
        
        try:
            success = test_func()
            elapsed = time.time() - start_time
            
            if success:
                print(f"✅ {test_name}: RÉUSSI ({elapsed:.2f}s)")
                results.append((test_name, True, elapsed))
            else:
                print(f"❌ {test_name}: ÉCHEC ({elapsed:.2f}s)")
                results.append((test_name, False, elapsed))
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"💥 {test_name}: ERREUR - {e} ({elapsed:.2f}s)")
            results.append((test_name, False, elapsed))
    
    # Résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*80)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"\n📈 Résultats: {passed}/{total} tests réussis ({passed/total*100:.1f}%)")
    
    for test_name, success, elapsed in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name:<30} {elapsed:.2f}s")
    
    print("\n" + "="*80)
    if passed == total:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS ! Votre RAG setup fonctionne correctement.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez votre configuration.")
    print("="*80)

if __name__ == "__main__":
    # Exécuter soit tous les tests, soit un test spécifique
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "basic":
            test_basic_semantic_search()
        elif test_name == "llm":
            test_llm_integration()
        elif test_name == "scores":
            test_similarity_scores()
        elif test_name == "edge":
            test_edge_cases()
        elif test_name == "workflow":
            test_complete_workflow()
        else:
            print(f"Test '{test_name}' non reconnu. Utilisez: basic, llm, scores, edge, workflow")
    else:
        # Exécuter tous les tests par défaut
        run_all_tests()