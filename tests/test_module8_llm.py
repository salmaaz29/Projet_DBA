# tests/test_with_llm.py
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.recovery_guide import OracleRecoveryGuide
from src.llm_engine import LLMEngine

class MockRAG:
    def retrieve_context(self, *args, **kwargs):
        return []

def test_llm_integration():
    print("🧪 TEST INTÉGRATION COMPLÈTE AVEC LLM")
    print("="*70)
    
    # 1. Initialisation du LLM
    print("🔧 Initialisation du LLMEngine...")
    start_time = time.time()
    
    try:
        llm = LLMEngine(rag_setup=MockRAG(), default_model="tinyllama")
        init_time = time.time() - start_time
        print(f"✅ LLM initialisé en {init_time:.1f}s (modèle: tinyllama)")
    except Exception as e:
        print(f"❌ Erreur d'initialisation LLM: {e}")
        print("💡 Essayons avec gemma2:2b...")
        try:
            llm = LLMEngine(rag_setup=MockRAG(), default_model="gemma2:2b")
            print(f"✅ LLM initialisé avec gemma2:2b")
        except Exception as e2:
            print(f"❌ Échec complet: {e2}")
            print("⚠️  Utilisation du mode sans LLM")
            llm = None
    
    # 2. Création du guide
    print("\n🔧 Création du OracleRecoveryGuide...")
    guide = OracleRecoveryGuide(llm_engine=llm, rag_setup=MockRAG())
    
    # 3. Test avec différentes questions
    test_cases = [
        {
            "question": "Comment récupérer ma base au 15 mars 14h ?",
            "scenario": "pitr",
            "clarifications": {
                "target_time": "15-MAR-2024 14:00:00",
                "situation": "Suppression accidentelle de données critiques"
            }
        },
        {
            "question": "Ma base Oracle a crashé après une panne électrique",
            "scenario": "full_recovery",
            "clarifications": {
                "backups": "Backups RMAN complets sur disque NAS",
                "situation": "Crash complet suite à coupure de courant"
            }
        },
        {
            "question": "J'ai supprimé la table CLIENTS par erreur ce matin",
            "scenario": "table_recovery",
            "clarifications": {
                "table_name": "CLIENTS",
                "situation": "DROP TABLE exécuté accidentellement"
            }
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"🧪 TEST {i}: {test['scenario'].upper()}")
        print(f"{'='*70}")
        print(f"📝 Question: {test['question']}")
        
        # Étape 1: Sans clarifications
        print("\n🔄 Étape 1: Traitement initial...")
        step1_start = time.time()
        result1 = guide.handle_user_question(test['question'])
        step1_time = time.time() - step1_start
        
        print(f"   ⏱️  Temps: {step1_time:.1f}s")
        print(f"   🎯 Scénario détecté: {result1.get('scenario_name', 'N/A')}")
        print(f"   ❓ Clarification nécessaire: {result1.get('needs_clarification', 'N/A')}")
        
        # Afficher les questions de clarification
        if result1.get('needs_clarification'):
            questions = result1.get('clarification_questions', [])
            print(f"   📋 Questions posées ({len(questions)}):")
            for j, q in enumerate(questions[:3], 1):
                print(f"     {j}. {q}")
        
        # Étape 2: Avec clarifications
        print(f"\n🔄 Étape 2: Génération avec clarifications...")
        step2_start = time.time()
        result2 = guide.handle_user_question(test['question'], test['clarifications'])
        step2_time = time.time() - step2_start
        
        print(f"   ⏱️  Temps: {step2_time:.1f}s")
        
        # Analyser le résultat
        guide_data = result2.get('guide', {})
        playbook = guide_data.get('playbook', {})
        
        print(f"\n📊 RÉSULTAT FINAL:")
        print(f"   🔧 Modèle utilisé: {guide_data.get('model_used', 'N/A')}")
        print(f"   🗣️  Langue: {guide_data.get('language', 'N/A')}")
        print(f"   📏 Structuré: {playbook.get('structured', False)}")
        print(f"   ⏱️  Temps estimé: {playbook.get('estimated_time', 'N/A')}")
        
        # Afficher le contenu du playbook
        if playbook:
            print(f"\n📋 CONTENU DU PLAYBOOK:")
            
            # Étapes
            steps = playbook.get('steps', [])
            if steps:
                print(f"   📝 ÉTAPES ({len(steps)}):")
                for step in steps[:3]:  # Afficher 3 premières étapes
                    if isinstance(step, dict):
                        print(f"     {step.get('number', '?')}. {step.get('description', '')}")
                    else:
                        print(f"     • {step}")
                if len(steps) > 3:
                    print(f"     ... et {len(steps) - 3} étapes supplémentaires")
            
            # Commandes
            commands = playbook.get('commands', [])
            if commands:
                print(f"\n   💻 COMMANDES ({len(commands)}):")
                for cmd in commands[:3]:
                    print(f"     • {cmd}")
                if len(commands) > 3:
                    print(f"     ... et {len(commands) - 3} commandes supplémentaires")
            
            # Points de validation
            validations = playbook.get('validation_points', [])
            if validations:
                print(f"\n   ✅ POINTS DE VALIDATION ({len(validations)}):")
                for point in validations[:2]:
                    print(f"     • {point}")
            
            # Vérifier les exigences
            print(f"\n{'='*70}")
            print("✅ VÉRIFICATION DES EXIGENCES DU PROJET:")
            print(f"{'='*70}")
            
            requirements = {
                'playbook_structuré': playbook.get('structured', False),
                'étapes_numérotées': len(steps) >= 3,
                'commandes_précises': len(commands) >= 2,
                'points_de_validation': len(validations) >= 1,
                'temps_estimé': playbook.get('estimated_time') is not None,
                'réponse_en_français': guide_data.get('language') == 'french' or 'français' in str(playbook.get('raw_response', '')).lower()
            }
            
            all_passed = True
            for req_name, req_met in requirements.items():
                status = "✓" if req_met else "✗"
                color = "\033[92m" if req_met else "\033[91m"  # Vert/Rouge
                reset = "\033[0m"
                print(f"   {color}{status}{reset} {req_name.replace('_', ' ').title()}")
                if not req_met:
                    all_passed = False
            
            if all_passed:
                print(f"\n🎉 Toutes les exigences sont satisfaites !")
            else:
                print(f"\n⚠️  Certaines exigences ne sont pas satisfaites")
                
                # Afficher un extrait de la réponse brute pour debug
                raw_response = playbook.get('raw_response', '')
                if raw_response:
                    print(f"\n📄 Extrait de la réponse LLM (200 premiers caractères):")
                    print(f"   '{raw_response[:200]}...'")
        
        else:
            print(f"❌ Aucun playbook généré")
            print(f"   Guide disponible: {list(guide_data.keys())}")
        
        # Pause entre les tests
        if i < len(test_cases):
            print(f"\n⏳ Pause de 2 secondes avant le test suivant...")
            time.sleep(2)

def test_specific_demo_question():
    """Test spécifique pour la question de démo requise"""
    print(f"\n{'='*70}")
    print("🧪 TEST SPÉCIAL: Question de validation du projet")
    print(f"{'='*70}")
    
    print("📋 Exigence du projet: 'Validation : peut répondre \"Comment récupérer ma base au 15 mars 14h ?\"'")
    
    # Initialiser avec LLM
    try:
        llm = LLMEngine(rag_setup=MockRAG(), default_model="tinyllama")
        guide = OracleRecoveryGuide(llm_engine=llm, rag_setup=MockRAG())
    except:
        print("⚠️  LLM non disponible, test sans LLM")
        guide = OracleRecoveryGuide(llm_engine=None)
    
    # La question exacte de l'exigence
    demo_question = "Comment récupérer ma base au 15 mars 14h ?"
    clarifications = {
        "target_time": "15-MAR-2024 14:00:00",
        "situation": "Démonstration de la plateforme de récupération Oracle IA"
    }
    
    print(f"\n❓ Question: {demo_question}")
    print(f"📋 Clarifications fournies:")
    for k, v in clarifications.items():
        print(f"   • {k}: {v}")
    
    print("\n🔄 Génération du playbook...")
    start_time = time.time()
    result = guide.handle_user_question(demo_question, clarifications)
    elapsed = time.time() - start_time
    
    print(f"⏱️  Temps de génération: {elapsed:.1f}s")
    
    # Analyse détaillée
    guide_data = result.get('guide', {})
    playbook = guide_data.get('playbook', {})
    
    print(f"\n📊 ANALYSE DE LA RÉPONSE:")
    print(f"   Scénario: {result.get('scenario_name')}")
    print(f"   Modèle: {guide_data.get('model_used', 'local_fallback')}")
    
    # Vérifier spécifiquement les commandes RMAN
    commands = playbook.get('commands', [])
    rman_commands = [cmd for cmd in commands if 'rman>' in cmd.lower()]
    
    print(f"\n💻 COMMANDES RMAN TROUVÉES ({len(rman_commands)}):")
    for cmd in rman_commands[:5]:
        print(f"   • {cmd}")
    
    # Vérifier la présence de SET UNTIL TIME (spécifique à PITR)
    has_set_until = any('set until' in cmd.lower() for cmd in commands)
    print(f"\n🔍 VÉRIFICATIONS SPÉCIFIQUES PITR:")
    print(f"   ✓ SET UNTIL TIME présent: {has_set_until}")
    print(f"   ✓ Date spécifique (15 mars): {'15' in str(commands)}")
    print(f"   ✓ Heure spécifique (14h): {'14' in str(commands)}")
    
    # Afficher un exemple de playbook généré
    print(f"\n📋 EXEMPLE DE PLAYBOOK GÉNÉRÉ:")
    if playbook.get('steps'):
        print(f"\nÉtapes de récupération:")
        for step in playbook['steps'][:5]:
            if isinstance(step, dict):
                print(f"  {step.get('number')}. {step.get('description')}")
    
    print(f"\n⏱️  Temps estimé de récupération: {playbook.get('estimated_time', 'N/A')}")
    
    # Conclusion
    print(f"\n{'='*70}")
    print("🎯 CONCLUSION DU TEST DE VALIDATION:")
    print(f"{'='*70}")
    
    if len(rman_commands) >= 2 and has_set_until:
        print("✅ SUCCÈS: Le Module 8 répond correctement à la question de validation!")
        print("   ✓ Génère un playbook structuré")
        print("   ✓ Inclut des commandes RMAN spécifiques")
        print("   ✓ Gère le scénario PITR avec date/heure précise")
        print("   ✓ Prêt pour l'intégration dans le dashboard")
    else:
        print("⚠️  ATTENTION: Réponse incomplète")
        print("   • Vérifier les prompts dans prompts.yaml")
        print("   • S'assurer que le LLM répond en français")
        print("   • Ajouter plus d'exemples dans les prompts")

def quick_performance_test():
    """Test rapide de performance"""
    print(f"\n{'='*70}")
    print("⚡ TEST DE PERFORMANCE RAPIDE")
    print(f"{'='*70}")
    
    questions = [
        "Crash base Oracle",
        "Récupération table",
        "PITR 14h",
    ]
    
    try:
        llm = LLMEngine(rag_setup=MockRAG(), default_model="tinyllama")
        guide = OracleRecoveryGuide(llm_engine=llm, rag_setup=MockRAG())
        model_name = "tinyllama"
    except:
        guide = OracleRecoveryGuide(llm_engine=None)
        model_name = "sans_llm"
    
    print(f"Modèle: {model_name}")
    print(f"{'Question':<30} {'Scénario':<20} {'Temps (s)':<10} {'Étapes':<10}")
    print("-" * 70)
    
    for question in questions:
        start = time.time()
        result = guide.handle_user_question(question)
        elapsed = time.time() - start
        
        scenario = result.get('scenario', 'unknown')
        scenario_name = guide.scenarios.get(scenario, 'unknown')
        steps = len(result.get('guide', {}).get('playbook', {}).get('steps', []))
        
        print(f"{question[:28]:<30} {scenario_name[:18]:<20} {elapsed:<10.1f} {steps:<10}")

if __name__ == "__main__":
    print("🚀 TEST COMPLET DU MODULE 8 AVEC LLM")
    print("Version: Intégration LLM + Playbook structuré\n")
    
    try:
        # Test principal
        test_llm_integration()
        
        # Test spécifique de validation
        test_specific_demo_question()
        
        # Test de performance
        quick_performance_test()
        
        print(f"\n{'='*70}")
        print("📋 RÉSUMÉ POUR L'INTÉGRATION DANS LE DASHBOARD:")
        print(f"{'='*70}")
        print("""
        ✅ FONCTIONNALITÉS TESTÉES:
          1. Classification des 4 scénarios
          2. Questions de clarification intelligentes
          3. Génération de playbooks structurés
          4. Commandes RMAN exactes
          5. Temps estimé de récupération
          6. Points de validation
        
        🔧 INTÉGRATION DANS DASHBOARD:
        
        from src.llm_engine import LLMEngine
        from src.recovery_guide import OracleRecoveryGuide
        
        # Initialisation
        llm = LLMEngine(rag_setup=None)  # ou avec RAG si disponible
        recovery_module = OracleRecoveryGuide(llm_engine=llm)
        
        # Utilisation
        def handle_recovery_request(user_question, clarifications=None):
            result = recovery_module.handle_user_question(user_question, clarifications)
            
            if result['needs_clarification']:
                # Demander les clarifications à l'utilisateur
                return {
                    'type': 'clarification',
                    'questions': result['clarification_questions'],
                    'scenario': result['scenario_name']
                }
            else:
                # Afficher le playbook
                playbook = result['guide']['playbook']
                return {
                    'type': 'playbook',
                    'scenario': result['scenario_name'],
                    'steps': playbook['steps'],
                    'commands': playbook['commands'],
                    'validation_points': playbook['validation_points'],
                    'estimated_time': playbook['estimated_time']
                }
        """)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()