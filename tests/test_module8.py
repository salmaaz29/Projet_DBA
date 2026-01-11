# cli_test.py
"""
Interface en ligne de commande pour tester le Module 8
"""

import sys
import json

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from colorama import init, Fore, Style
init(autoreset=True)

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ {text}{Style.RESET_ALL}")

def interactive_test():
    """Test interactif en CLI"""
    
    print_header("🧪 TEST INTERACTIF - MODULE 8 RECOVERY")
    
    try:
        # Importer
        from src.llm_engine import LLMEngine
        from src.recovery_guide import OracleRecoveryGuide
        
        print_info("Initialisation du LLMEngine...")
        
        # Mock RAG
        class MockRAG:
            def retrieve_context(self, *args, **kwargs):
                return []
        
        # Essayer gemma2:2b, fallback sur tinyllama
        try:
            llm = LLMEngine(rag_setup=MockRAG(), default_model="tinyllama")
            print_success(f"LLMEngine initialisé avec tinyllama")
        except:
            llm = LLMEngine(rag_setup=MockRAG(), default_model="tinyllama")
            print_info(f"Fallback sur tinyllama")
        
        guide = OracleRecoveryGuide(llm_engine=llm)
        print_success("OracleRecoveryGuide prêt")
        
        while True:
            print_header("POSER UNE QUESTION")
            print("Exemples:")
            print("  • 'Ma base a crashé, que faire ?'")
            print("  • 'Je veux récupérer à hier 14h'")
            print("  • 'Table EMPLOYEES supprimée'")
            print("  • 'Quit' pour quitter")
            print("-" * 40)
            
            question = input(f"{Fore.BLUE}❓ Votre question: {Style.RESET_ALL}").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if not question:
                continue
            
            print_info("Traitement en cours...")
            
            try:
                result = guide.handle_user_question(question)
                
                print(f"\n{Fore.GREEN}📊 RÉSULTAT:{Style.RESET_ALL}")
                print(f"  Scénario: {result['scenario_name']}")
                print(f"  ID: {result['scenario']}")
                
                if result['needs_clarification']:
                    print(f"\n{Fore.YELLOW}❓ QUESTIONS DE CLARIFICATION:{Style.RESET_ALL}")
                    for i, q in enumerate(result['clarification_questions'][:3], 1):
                        print(f"  {i}. {q}")
                    
                    # Simuler des réponses
                    clarifications = {}
                    if result['scenario'] == 'pitr':
                        clarifications['target_time'] = '15-MAR-2024 14:30:00'
                    elif result['scenario'] == 'table_recovery':
                        clarifications['table_name'] = 'EMPLOYEES'
                    
                    if clarifications:
                        print(f"\n{Fore.CYAN}📋 RÉPONSES SIMULÉES:{Style.RESET_ALL}")
                        for k, v in clarifications.items():
                            print(f"  • {k}: {v}")
                        
                        # Regénérer avec clarifications
                        print_info("Génération du guide final...")
                        final_result = guide.handle_user_question(question, clarifications)
                        result = final_result
                
                # Afficher le guide
                guide_data = result['guide']
                print(f"\n{Fore.GREEN}📋 GUIDE GÉNÉRÉ:{Style.RESET_ALL}")
                print(f"  Modèle: {guide_data.get('model_used', 'N/A')}")
                print(f"  Durée: {guide_data.get('estimated_duration', 'N/A')}")
                
                if 'response' in guide_data:
                    print(f"\n{Fore.WHITE}📄 CONTENU:{Style.RESET_ALL}")
                    print(guide_data['response'][:500])
                    if len(guide_data['response']) > 500:
                        print("...")
                elif 'steps' in guide_data:
                    print(f"\n{Fore.WHITE}📋 ÉTAPES ({len(guide_data['steps'])}):{Style.RESET_ALL}")
                    for step in guide_data['steps'][:3]:  # Afficher 3 premières
                        print(f"  {step['step']}. {step['title']}")
                    if len(guide_data['steps']) > 3:
                        print(f"  ... et {len(guide_data['steps']) - 3} étapes supplémentaires")
                
                print(f"\n{Fore.GREEN}✅ Test réussi!{Style.RESET_ALL}")
                
            except Exception as e:
                print_error(f"Erreur: {e}")
                
            input(f"\n{Fore.CYAN}↵ Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
    
    except ImportError as e:
        print_error(f"Import impossible: {e}")
        print_info("Assurez-vous que:")
        print("  1. Vous êtes dans le dossier du projet")
        print("  2. src/llm_engine.py existe")
        print("  3. Ollama est installé")

if __name__ == "__main__":
    interactive_test()