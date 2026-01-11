# src/recovery_guide.py - MODULE 8 COMPLET AVEC PLAYBOOK STRUCTURÉ
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime
from llm_engine import LLMEngine

class OracleRecoveryGuide:
    """
    Module 8: Restauration & Récupération Assistée
    Guide l'utilisateur à travers 4 scénarios de récupération Oracle
    """
    
    def __init__(self, rag_setup=None):
        self.llm = LLMEngine()
        self.rag = rag_setup
        self.scenarios = {
            'full_recovery': "Restauration complète après crash",
            'pitr': "Récupération point-in-time (PITR)",
            'table_recovery': "Récupération de table spécifique",
            'row_recovery': "Récupération de lignes (point-in-time au niveau data)"
        }

        # Few-shot examples pour améliorer les réponses LLM
        self.few_shot_examples = {
            'full_recovery': [
                {
                    'situation': 'Crash complet du serveur de base de données',
                    'solution': 'Restauration complète depuis backup RMAN + récupération des archive logs',
                    'commands': ['RMAN> STARTUP NOMOUNT;', 'RMAN> RESTORE CONTROLFILE;', 'RMAN> RESTORE DATABASE;', 'RMAN> RECOVER DATABASE;']
                },
                {
                    'situation': 'Panne de disque dur avec corruption de tous les fichiers de données',
                    'solution': 'Restauration complète de la base de données depuis backup',
                    'commands': ['RMAN> RESTORE DATABASE;', 'RMAN> RECOVER DATABASE;']
                }
            ],
            'pitr': [
                {
                    'situation': 'Suppression accidentelle de données importantes à 14h30',
                    'solution': 'Récupération PITR jusqu\'à 14h25 avant la suppression',
                    'commands': ['RMAN> RUN { SET UNTIL TIME "TO_DATE(\'...\')"; RESTORE DATABASE; RECOVER DATABASE; }']
                },
                {
                    'situation': 'Erreur humaine avec modification massive de données',
                    'solution': 'Point-in-time recovery au SCN juste avant l\'erreur',
                    'commands': ['RMAN> RUN { SET UNTIL SCN ...; RESTORE DATABASE; RECOVER DATABASE; }']
                }
            ],
            'table_recovery': [
                {
                    'situation': 'DROP TABLE accidentel d\'une table critique',
                    'solution': 'FLASHBACK TABLE TO BEFORE DROP si activé',
                    'commands': ['FLASHBACK TABLE table_name TO BEFORE DROP;']
                },
                {
                    'situation': 'Corruption logique d\'une table importante',
                    'solution': 'Tablespace Point-In-Time Recovery (TSPITR)',
                    'commands': ['RMAN> RECOVER TABLE table_name UNTIL TIME ...;']
                }
            ],
            'row_recovery': [
                {
                    'situation': 'Suppression accidentelle de lignes spécifiques',
                    'solution': 'FLASHBACK QUERY pour identifier et récupérer les données',
                    'commands': ['SELECT * FROM table AS OF TIMESTAMP ...;', 'INSERT INTO table SELECT * FROM table AS OF TIMESTAMP ...;']
                },
                {
                    'situation': 'Modification erronée de données sensibles',
                    'solution': 'Récupération des anciennes valeurs via flashback',
                    'commands': ['SELECT * FROM table AS OF SCN ... WHERE ...;']
                }
            ]
        }
    
    def classify_scenario(self, user_question: str) -> str:
        """
        Identifie le scénario de récupération demandé
        Retourne: 'full_recovery', 'pitr', 'table_recovery', 'row_recovery', ou 'unknown'
        """
        question_lower = user_question.lower()
        
        # Mots-clés pour chaque scénario (AMÉLIORÉS)
        scenario_keywords = {
            'full_recovery': [
                'crash', 'plantage', 'base perdue', 'base crashée',
                'rman restore', 'restauration complète', 'récupération complète',
                'base corrompue', 'media failure', 'perte totale', 'tout restaurer',
                'base entière', 'instance down', 'instance arrêtée'
            ],
            'pitr': [
                'point in time', 'point-in-time', 'p.i.t.r', 'pitr',
                'restaurer jusqu\'à', 'récupérer jusqu\'à', 'à une date',
                'heure spécifique', 'scn', 'restaurer au', 'récupérer au',
                'rollback time', 'mars', 'avril', 'mai', 'juin', 'juillet',  # Mois
                'janvier', 'février', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
                '14h', '15h', '16h', '17h', 'heure', 'h ', 'h:',  # Heures
                '2024', '2025', '2026',  # Années
                'date', 'moment précis', 'point précis'
            ],
            'table_recovery': [
                'table', 'table supprimée', 'table effacée', 'table perdue',
                'restaurer table', 'récupérer table', 'drop table', 'truncate table',
                'accidentellement supprimé', 'restore table', 'recover table',
                'employees', 'clients', 'produits',  # Noms de tables courants
                'objet supprimé', 'objet perdu'
            ],
            'row_recovery': [
                'ligne', 'lignes', 'données spécifiques', 'donnée particulière',
                'récupérer des lignes', 'restaurer des lignes', 'flashback query',
                'as of timestamp', 'anciennes données', 'valeur précédente',
                'annuler modification', 'rollback data', 'modification erronée',
                'données modifiées', 'données effacées'
            ]
        }
        
        # Compter les correspondances pour chaque scénario
        scores = {}
        for scenario, keywords in scenario_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in question_lower:
                    # Points supplémentaires pour les mots-clés forts
                    if keyword in ['pitr', 'point in time', 'scn']:
                        score += 3
                    elif keyword in ['table', 'ligne', 'crash']:
                        score += 2
                    else:
                        score += 1
            scores[scenario] = score
        
        # DEBUG: Afficher les scores
        debug = False  # Mettre à True pour debug
        if debug:
            print(f"\n🔍 DEBUG classification pour: '{user_question}'")
            for scenario, score in scores.items():
                print(f"  {scenario}: {score}")
        
        # Retourner le scénario avec le score le plus élevé
        best_scenario = max(scores.items(), key=lambda x: x[1])
        
        # Si score > 0, retourner le scénario, sinon 'unknown'
        if best_scenario[1] > 0:
            return best_scenario[0]
        return 'unknown'
    
    def get_clarification_questions(self, scenario: str) -> list:
        """
        Retourne les questions de clarification pour chaque scénario
        """
        questions_map = {
            'full_recovery': [
                "Avez-vous les backups RMAN récents ?",
                "Où sont stockés les fichiers de backup ? (disque, bande)",
                "L'instance Oracle est-elle encore en fonctionnement ?",
                "Avez-vous les fichiers de contrôle (controlfiles) ?",
                "Quelle est la version de la base de données ?"
            ],
            'pitr': [
                "Quelle est la date/heure exacte cible ? (format: JJ-MM-AAAA HH24:MI:SS)",
                "Connaissez-vous le SCN (System Change Number) cible ?",
                "Avez-vous tous les archive logs depuis le dernier backup ?",
                "Le backup a-t-il été fait avant la date cible ?",
                "Quelle est la raison de la récupération PITR ?"
            ],
            'table_recovery': [
                "Quel est le nom exact de la table à récupérer ?",
                "Quand a-t-elle été supprimée/modifiée ?",
                "Dans quel schéma se trouve cette table ?",
                "Avez-vous activé FLASHBACK TABLE ?",
                "Quelle est la taille approximative de la table ?"
            ],
            'row_recovery': [
                "Quelle table contient les données à récupérer ?",
                "Quand les données ont-elles été modifiées/supprimées ?",
                "Avez-vous besoin de récupérer toutes les lignes ou certaines spécifiques ?",
                "Connaissez-vous les anciennes valeurs ?",
                "Avez-vous activé UNDO_RETENTION avec une valeur suffisante ?"
            ]
        }
        
        return questions_map.get(scenario, [])
    
    def _format_llm_response(self, response: str, scenario: str) -> Dict[str, Any]:
        """
        Formate la réponse LLM en playbook structuré
        selon les exigences du projet
        """
        
        # Nettoyer la réponse
        cleaned = response.strip()
        
        # Extraire les éléments demandés
        steps = []
        commands = []
        validation_points = []
        estimated_time = None
        
        # Parser la réponse pour trouver les éléments
        lines = cleaned.split('\n')
        
        for line in lines:
            line_clean = line.strip()
            
            # Détecter les étapes numérotées
            if (re.match(r'^\d+[\.\)]', line_clean) or 
                'étape' in line_clean.lower() or
                'step' in line_clean.lower()):
                steps.append(line_clean)
            
            # Détecter les commandes RMAN
            if ('rman>' in line_clean.lower() or 
                'sql>' in line_clean.lower() or
                'flashback' in line_clean.lower() or
                'create ' in line_clean.lower() or
                'alter ' in line_clean.lower() or
                'recover' in line_clean.lower() or
                'restore' in line_clean.lower()):
                commands.append(line_clean)
            
            # Détecter les points de validation
            if ('vérifier' in line_clean.lower() or 
                'valider' in line_clean.lower() or
                'vérification' in line_clean.lower() or
                'validation' in line_clean.lower()):
                validation_points.append(line_clean)
            
            # Détecter le temps estimé
            if ('temps' in line_clean.lower() or 
                'durée' in line_clean.lower() or
                'time' in line_clean.lower() or
                'estimated' in line_clean.lower()):
                time_match = re.search(r'(\d+[-\s]*\d*\s*(heures?|minutes?|jours?|hours?|minutes?|days?))', 
                                      line_clean, re.IGNORECASE)
                if time_match:
                    estimated_time = time_match.group(1)
        
        # Si pas assez d'éléments, créer un playbook par défaut
        if len(steps) < 2:
            steps = self._get_default_steps(scenario)
        
        if len(commands) < 1:
            commands = self._get_default_commands(scenario)
        
        if not estimated_time:
            estimated_time = self._get_default_time(scenario)
        
        # Structurer le playbook
        playbook = {
            'steps': [],
            'commands': commands[:10],
            'validation_points': validation_points[:5],
            'estimated_time': estimated_time,
            'raw_response': cleaned[:500],  # Garder un extrait
            'structured': len(steps) > 1  # Indique si bien structuré
        }
        
        # Formater les étapes
        for i, step in enumerate(steps[:10], 1):
            if isinstance(step, dict):
                playbook['steps'].append(step)
            else:
                # Nettoyer le numéro si présent
                clean_step = re.sub(r'^\d+[\.\)]\s*', '', step)
                playbook['steps'].append({
                    'number': i,
                    'description': clean_step[:200]
                })
        
        return playbook
    
    def _get_default_steps(self, scenario: str) -> list:
        """Étapes par défaut selon le scénario"""
        defaults = {
            'full_recovery': [
                "Vérifier la disponibilité des backups RMAN",
                "Démarrer l'instance en mode NOMOUNT",
                "Restaurer le fichier de contrôle (controlfile)",
                "Monter la base de données",
                "Restaurer les fichiers de données",
                "Appliquer les archive logs",
                "Ouvrir la base avec RESETLOGS"
            ],
            'pitr': [
                "Déterminer le SCN ou timestamp cible",
                "Vérifier la disponibilité des archive logs",
                "Lancer la commande RMAN avec SET UNTIL",
                "Restaurer la base",
                "Appliquer les logs jusqu'au point cible",
                "Ouvrir avec RESETLOGS"
            ],
            'table_recovery': [
                "Vérifier si FLASHBACK TABLE est activé",
                "Essayer FLASHBACK TABLE TO BEFORE DROP",
                "Sinon, utiliser TSPITR via RMAN",
                "Récupérer la table depuis backup",
                "Valider l'intégrité des données"
            ]
        }
        return defaults.get(scenario, ["Analyser la situation", "Suivre procédure Oracle"])
    
    def _get_default_commands(self, scenario: str) -> list:
        """Commandes par défaut"""
        defaults = {
            'full_recovery': [
                "RMAN> STARTUP NOMOUNT;",
                "RMAN> RESTORE CONTROLFILE FROM AUTOBACKUP;",
                "RMAN> ALTER DATABASE MOUNT;",
                "RMAN> RESTORE DATABASE;",
                "RMAN> RECOVER DATABASE;",
                "RMAN> ALTER DATABASE OPEN RESETLOGS;"
            ],
            'pitr': [
                "RMAN> RUN {",
                "  SET UNTIL TIME \"TO_DATE('15-MAR-2024 14:30:00', 'DD-MON-YYYY HH24:MI:SS')\";",
                "  RESTORE DATABASE;",
                "  RECOVER DATABASE;",
                "  ALTER DATABASE OPEN RESETLOGS;",
                "}"
            ]
        }
        return defaults.get(scenario, ["-- Commandes spécifiques au scénario"])
    
    def _get_default_time(self, scenario: str) -> str:
        """Temps estimé par défaut"""
        times = {
            'full_recovery': "2-6 heures",
            'pitr': "1-4 heures",
            'table_recovery': "15-60 minutes",
            'row_recovery': "5-30 minutes"
        }
        return times.get(scenario, "Variable")
    
    def generate_recovery_guide(self, scenario: str, user_inputs: Dict[str, str]) -> Dict[str, Any]:
        """
        Génère un guide de récupération détaillé basé sur le scénario
        Utilise prompts.yaml avec fallback local et intégration LLM
        """

        print(f"🔧 Génération guide pour scénario: {scenario}")

        # Récupérer le prompt depuis prompts.yaml
        prompt_text = None

        try:
            # Chercher dans la hiérarchie prompts.yaml via llm_engine
            if self.llm and hasattr(self.llm, 'prompts'):
                if 'recovery_guidance' in self.llm.prompts:
                    # Mapping des scénarios aux clés prompts
                    scenario_mapping = {
                        'full_recovery': 'full_recovery',
                        'pitr': 'pitr',
                        'table_recovery': 'table_recovery',
                        'row_recovery': 'row_recovery'
                    }

                    prompt_key = scenario_mapping.get(scenario)
                    if prompt_key and prompt_key in self.llm.prompts['recovery_guidance']:
                        prompt_text = self.llm.prompts['recovery_guidance'][prompt_key]
        except Exception as e:
            print(f"⚠️  Erreur accès prompts.yaml: {e}")

        # Fallback local si prompt non trouvé
        if not prompt_text:
            prompt_text = self._get_local_prompt(scenario, user_inputs)

        # Formater le prompt avec les inputs utilisateur
        try:
            prompt_text = prompt_text.format(**user_inputs)
        except KeyError as e:
            print(f"⚠️  Variables manquantes dans prompt: {e}")

        # Ajouter les few-shot examples au prompt
        if scenario in self.few_shot_examples:
            examples_text = "\n\nEXEMPLES DE RÉFÉRENCE :\n"
            for i, example in enumerate(self.few_shot_examples[scenario][:2], 1):  # Max 2 examples
                examples_text += f"Exemple {i}: {example['situation']} → {example['solution']}\n"
                examples_text += f"Commandes: {', '.join(example['commands'])}\n\n"
            prompt_text += examples_text

        # Appeler LLM si disponible
        if self.llm:
            try:
                print(f"🤖 Génération avec LLM pour {scenario}...")

                # Contexte français obligatoire
                context = "Tu es un expert DBA Oracle français. Réponds exclusivement en français."

                # Ajouter contexte RAG si disponible
                if self.rag and hasattr(self.rag, 'retrieve_context'):
                    try:
                        rag_results = self.rag.retrieve_context(
                            f"Oracle recovery {scenario} français procédure",
                            n_results=2
                        )
                        if rag_results:
                            context += "\n" + "\n".join([doc['content'][:200] for doc in rag_results])
                    except Exception as rag_error:
                        print(f"⚠️  Erreur RAG: {rag_error}")

                # Générer avec LLM
                response = self.llm.generate(prompt_text, context=context)

                # Parser et formater la réponse
                playbook = self._format_llm_response(response, scenario)

                guide = {
                    'scenario': self.scenarios.get(scenario, scenario),
                    'playbook': playbook,
                    'model_used': getattr(self.llm, 'default_model', 'llm'),
                    'timestamp': datetime.now().isoformat(),
                    'language': 'french',
                    'llm_generated': True
                }

                return guide

            except Exception as e:
                print(f"⚠️  Erreur LLM: {e}")
                print("   🔄 Fallback vers génération locale")

        # Fallback: Génération locale structurée
        return self._generate_structured_guide(scenario, user_inputs)
    
    def _generate_structured_guide(self, scenario: str, user_inputs: Dict) -> Dict[str, Any]:
        """Génère un guide structuré local (fallback)"""
        
        playbook_data = {
            'steps': [],
            'commands': [],
            'validation_points': [],
            'estimated_time': self._get_default_time(scenario),
            'structured': True,
            'source': 'local_fallback'
        }
        
        if scenario == 'full_recovery':
            playbook_data['steps'] = [
                {'number': 1, 'description': 'Vérifier la disponibilité des backups RMAN'},
                {'number': 2, 'description': 'Démarrer l\'instance en mode NOMOUNT'},
                {'number': 3, 'description': 'Restaurer le fichier de contrôle (controlfile)'},
                {'number': 4, 'description': 'Monter la base de données'},
                {'number': 5, 'description': 'Restaurer les fichiers de données'},
                {'number': 6, 'description': 'Appliquer les archive logs'},
                {'number': 7, 'description': 'Ouvrir la base avec RESETLOGS'}
            ]
            playbook_data['commands'] = [
                'RMAN> STARTUP NOMOUNT;',
                'RMAN> RESTORE CONTROLFILE FROM AUTOBACKUP;',
                'RMAN> ALTER DATABASE MOUNT;',
                'RMAN> RESTORE DATABASE;',
                'RMAN> RECOVER DATABASE;',
                'RMAN> ALTER DATABASE OPEN RESETLOGS;'
            ]
            playbook_data['validation_points'] = [
                'Vérifier que tous les backups sont VALID',
                'Valider l\'intégrité des fichiers restaurés',
                'Tester l\'accès aux données après récupération'
            ]
            
        elif scenario == 'pitr':
            target_time = user_inputs.get('target_time', '15-MAR-2024 14:30:00')
            playbook_data['steps'] = [
                {'number': 1, 'description': f'Déterminer le point de récupération : {target_time}'},
                {'number': 2, 'description': 'Vérifier la disponibilité des archive logs'},
                {'number': 3, 'description': 'Lancer la récupération point-in-time'},
                {'number': 4, 'description': 'Restaurer la base jusqu\'au point spécifié'},
                {'number': 5, 'description': 'Appliquer les logs de restauration'},
                {'number': 6, 'description': 'Ouvrir la base avec RESETLOGS'}
            ]
            playbook_data['commands'] = [
                f"RMAN> RUN {{",
                f"  SET UNTIL TIME \"TO_DATE('{target_time}', 'DD-MON-YYYY HH24:MI:SS')\";",
                f"  RESTORE DATABASE;",
                f"  RECOVER DATABASE;",
                f"  ALTER DATABASE OPEN RESETLOGS;",
                f"}}"
            ]
            playbook_data['validation_points'] = [
                'Vérifier que les données correspondent au point dans le temps',
                'Confirmer l\'absence de données après le point cible',
                'Tester les applications métier'
            ]
            
        elif scenario == 'table_recovery':
            table_name = user_inputs.get('table_name', 'MA_TABLE')
            playbook_data['steps'] = [
                {'number': 1, 'description': 'Vérifier si FLASHBACK TABLE est activé'},
                {'number': 2, 'description': f'Tenter FLASHBACK TABLE {table_name} TO BEFORE DROP'},
                {'number': 3, 'description': 'Si échec, utiliser TSPITR via RMAN'},
                {'number': 4, 'description': f'Récupérer la table {table_name} depuis backup'},
                {'number': 5, 'description': 'Valider l\'intégrité des données'}
            ]
            playbook_data['commands'] = [
                f'FLASHBACK TABLE {table_name} TO BEFORE DROP;',
                f'SELECT COUNT(*) FROM {table_name}; -- Validation'
            ]
            playbook_data['validation_points'] = [
                'Vérifier le nombre de lignes récupérées',
                'Valider les contraintes d\'intégrité',
                'Tester les accès applicatifs'
            ]
        
        guide = {
            'scenario': self.scenarios.get(scenario, scenario),
            'playbook': playbook_data,
            'model_used': 'local_fallback',
            'timestamp': datetime.now().isoformat(),
            'language': 'french'
        }
        
        return guide
    
    def _get_local_prompt(self, scenario: str, user_inputs: Dict) -> str:
        """Prompts locaux de fallback"""
        
        prompts = {
            'full_recovery': f"""
            TU DOIS RÉPONDRE EN FRANÇAIS UNIQUEMENT !
            Tu es un expert DBA Oracle. Guide la restauration complète après crash.
            
            Situation : {user_inputs.get('situation', 'Crash complet de la base de données')}
            Backups disponibles : {user_inputs.get('backups', 'Backup RMAN complet sur disque')}
            
            FOURNIS UN PLAYBOOK DÉTAILLÉ EN FRANÇAIS AVEC :
            
            ÉTAPES NUMÉROTÉES :
            1. [Première étape avec détails]
            2. [Deuxième étape]
            3. [etc.]
            
            COMMANDES RMAN EXACTES :
            • RMAN> [commande complète]
            • RMAN> [commande suivante]
            
            POINTS DE VALIDATION :
            • [Ce qu'il faut vérifier après chaque étape]
            • [Autres points de contrôle]
            
            TEMPS ESTIMÉ : [X heures/minutes]
            """,
            
            'pitr': f"""
            TU DOIS RÉPONDRE EN FRANÇAIS UNIQUEMENT !
            Guide la récupération point-in-time (PITR) Oracle.
            
            Date/heure cible : {user_inputs.get('target_time', 'Non spécifiée')}
            Situation : {user_inputs.get('situation', 'Récupération à un point précis dans le temps')}
            
            FOURNIS UN PLAYBOOK PITR EN FRANÇAIS AVEC :
            
            ÉTAPES NUMÉROTÉES :
            1. [Déterminer SCN/timestamp]
            2. [Vérifier logs archive]
            3. [Lancer récupération]
            
            COMMANDES RMAN EXACTES :
            • RMAN> [commande SET UNTIL]
            • RMAN> [commande RESTORE]
            
            POINTS DE VALIDATION :
            • [Vérification données]
            • [Validation métier]
            
            TEMPS ESTIMÉ : [selon taille logs]
            
            LIMITATIONS : Indique ce qui sera perdu/récupéré
            """
        }
        
        return prompts.get(scenario, f"Guide de récupération pour scénario: {scenario}")
    
    def _parse_llm_response(self, response: str, scenario: str, user_inputs: Dict) -> Dict[str, Any]:
        """Tente de parser la réponse LLM en JSON structuré"""
        try:
            playbook = self._format_llm_response(response, scenario)
            return {
                'scenario': self.scenarios.get(scenario, scenario),
                'playbook': playbook,
                'timestamp': datetime.now().isoformat(),
                'user_inputs': user_inputs
            }
        except:
            pass
        
        # Format par défaut
        return {
            'scenario': self.scenarios.get(scenario, scenario),
            'response': response,
            'structured': False,
            'timestamp': datetime.now().isoformat(),
            'user_inputs': user_inputs
        }
    
    def handle_user_question(self, user_question: str, clarification_answers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Point d'entrée principal pour le Module 8
        """
        # 1. Identifier le scénario
        scenario = self.classify_scenario(user_question)
        
        if scenario == 'unknown':
            return {
                'error': 'Scénario non reconnu',
                'suggestion': 'Veuillez préciser votre besoin de récupération',
                'possible_scenarios': list(self.scenarios.values())
            }
        
        # 2. Préparer les inputs
        user_inputs = {
            'situation': user_question,
            'timestamp': datetime.now().isoformat()
        }
        
        # Ajouter les réponses de clarification si fournies
        if clarification_answers:
            user_inputs.update(clarification_answers)
        
        # 3. Générer le guide (avec VRAI LLM)
        guide = self.generate_recovery_guide(scenario, user_inputs)
        
        # 4. Ajouter des métadonnées
        result = {
            'module': 'Module 8 - Recovery Guide',
            'scenario': scenario,
            'scenario_name': self.scenarios.get(scenario),
            'guide': guide,
            'clarification_questions': self.get_clarification_questions(scenario),
            'needs_clarification': len(self.get_clarification_questions(scenario)) > 0 and not clarification_answers
        }
        
        return result


# Test simple
if __name__ == "__main__":
    print("🧪 Test simplifié du Module 8")

    # Test avec LLM
    guide = OracleRecoveryGuide()

    test_question = "Comment récupérer ma base au 15 mars 14h ?"
    result = guide.handle_user_question(test_question)

    print(f"Question: {test_question}")
    print(f"Scénario: {result.get('scenario_name')}")
    print(f"Besoin clarification: {result.get('needs_clarification')}")

    if result.get('guide', {}).get('playbook'):
        playbook = result['guide']['playbook']
        print(f"Étapes: {len(playbook.get('steps', []))}")
        print(f"Commandes: {len(playbook.get('commands', []))}")
        print(f"Temps estimé: {playbook.get('estimated_time')}")
