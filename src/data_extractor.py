# -*- coding: utf-8 -*-
"""
MODULE 1 : Oracle Data Extractor & Generator COMPLET - VERSION CORRIGÉE POUR ORACLE 21c XE
✅ Extraction RÉELLE depuis vues Oracle 21c XE (UNIFIED_AUDIT_TRAIL, V$SQL, DBA_*)
✅ Connexion au PDB XEPDB1
✅ Fallback simulation automatique enrichi
✅ Données synthétiques réalistes et variées
✅ Compatible Oracle 21c XE Docker
"""

import pandas as pd
import random
from datetime import datetime, timedelta
import os
import warnings
import yaml
from pathlib import Path
from dotenv import load_dotenv

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

# =========================================================
# 🔐 CHARGEMENT .env
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    print(f"[OK] Fichier .env chargé : {ENV_PATH}")
else:
    print(f"[WARNING] Fichier .env introuvable : {ENV_PATH}")

# =========================================================
# Import oracledb
# =========================================================
try:
    import oracledb
    ORACLEDB_AVAILABLE = True
    print("[OK] Module oracledb disponible")
except ImportError:
    ORACLEDB_AVAILABLE = False
    print("[WARNING] Module oracledb non installé → simulation forcée")


class OracleDataExtractor:
    
    def __init__(self, use_simulation=False):
        """
        Args:
            use_simulation: True = forcer simulation, False = tenter connexion réelle
        """
        self.use_simulation = use_simulation
        self.connection = None
        self.cursor = None
        self.host = os.getenv("ORACLE_HOST", "localhost")
        self.port = int(os.getenv("ORACLE_PORT", "1521"))
        self.service = os.getenv("ORACLE_SERVICE", "XEPDB1")
        self.user = os.getenv("ORACLE_USER", "system")
        self.password = os.getenv("ORACLE_PASSWORD", "")

        if not use_simulation and ORACLEDB_AVAILABLE:
            self._connect_oracle_21c()
        else:
            self.use_simulation = True

        if self.use_simulation:
            print("[INFO] Mode SIMULATION activé")
        else:
            print(f"[OK] Connexion Oracle établie - Service: {self.service}")

    def _connect_oracle_21c(self):
        """Connexion Oracle 21c XE avec PDB XEPDB1"""
        print(f"   Tentative connexion à {self.host}:{self.port}/{self.service}...")
        
        if not self.password:
            print("[WARNING] Mot de passe Oracle manquant → simulation")
            self.use_simulation = True
            return

        try:
            # Connexion directe au PDB XEPDB1
            dsn = f"{self.host}:{self.port}/{self.service}"
            
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=dsn
            )
            self.cursor = self.connection.cursor()
            self.use_simulation = False
            
            # Vérifier la connexion
            self.cursor.execute("SELECT name FROM v$database")
            db_name = self.cursor.fetchone()[0]
            print(f"   ✅ Connecté à Oracle: {db_name}")
            
            # Vérifier le PDB
            try:
                self.cursor.execute("SELECT name, open_mode FROM v$pdbs WHERE open_mode = 'READ WRITE'")
                pdb_info = self.cursor.fetchone()
                if pdb_info:
                    print(f"   ✅ PDB actif: {pdb_info[0]} ({pdb_info[1]})")
            except:
                print("   ℹ️  Vue v$pdbs non disponible (peut être normal)")

        except Exception as e:
            print(f"   ❌ Connexion échouée: {e}")
            print("   [INFO] Basculement mode simulation")
            self.use_simulation = True

    # =========================================================
    # ========== EXTRACTION RÉELLE ORACLE 21c XE ===========
    # =========================================================
    
    def extract_audit_logs_real(self):
        """Extraction depuis UNIFIED_AUDIT_TRAIL (Oracle 21c)"""
        print("   Extraction logs d'audit depuis UNIFIED_AUDIT_TRAIL...")
        
        try:
            # Vérifier si l'audit unifié est activé
            check_query = """
                SELECT value FROM v$option WHERE parameter = 'Unified Auditing'
            """
            self.cursor.execute(check_query)
            unified_result = self.cursor.fetchone()
            is_unified = unified_result and unified_result[0] == 'TRUE'
            
            if is_unified:
                print("   ℹ️  Audit unifié détecté")
                query = """
                    SELECT 
                        ROWNUM as log_id,
                        TO_CHAR(EVENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS') as timestamp,
                        DBUSERNAME as username,
                        ACTION_NAME as action,
                        OBJECT_SCHEMA || '.' || OBJECT_NAME as object_name,
                        RETURN_CODE as status,
                        CLIENT_HOST as ip_address,
                        SESSIONID as session_id,
                        UNIFIED_AUDIT_POLICIES as policies
                    FROM UNIFIED_AUDIT_TRAIL 
                    WHERE EVENT_TIMESTAMP > SYSDATE - 30
                    AND ROWNUM <= 100
                    ORDER BY EVENT_TIMESTAMP DESC
                """
            else:
                print("   ℹ️  Audit standard (SYS.AUD$)")
                query = """
                    SELECT 
                        ROWNUM as log_id,
                        TO_CHAR(TIMESTAMP#, 'YYYY-MM-DD HH24:MI:SS') as timestamp,
                        USERID as username,
                        ACTION# as action_code,
                        OBJ$NAME as object_name,
                        RETURNCODE as status,
                        USERHOST as ip_address,
                        SESSIONID as session_id,
                        NULL as policies
                    FROM SYS.AUD$
                    WHERE TIMESTAMP# > SYSDATE - 30
                    AND ROWNUM <= 100
                    ORDER BY TIMESTAMP# DESC
                """
            
            df = pd.read_sql(query, self.connection)
            
            # Mapping actions Oracle pour audit standard
            if not is_unified and 'action_code' in df.columns:
                action_map = {
                    2: 'INSERT', 3: 'SELECT', 6: 'UPDATE', 7: 'DELETE',
                    9: 'CREATE', 12: 'DROP', 17: 'GRANT', 18: 'REVOKE',
                    26: 'ALTER', 28: 'AUDIT', 29: 'NOAUDIT'
                }
                df['action'] = df['action_code'].map(action_map).fillna('OTHER')
                df.drop('action_code', axis=1, inplace=True, errors='ignore')
            
            # Ajout de la sévérité
            if 'status' in df.columns:
                df['severity'] = df['status'].apply(
                    lambda x: 'CRITICAL' if x != 0 else 'NORMAL'
                )
            
            if 'policies' in df.columns:
                df['policies'] = df['policies'].fillna('N/A')
            
            print(f"      → {len(df)} logs extraits (Mode: {'Unifié' if is_unified else 'Standard'})")
            return df
            
        except Exception as e:
            print(f"      [ERROR] Extraction échouée: {e}")
            return None

    def extract_slow_queries_real(self):
        """Extraction depuis V$SQL (Oracle 21c)"""
        print("   Extraction requêtes lentes depuis V$SQL...")
        
        try:
            query = """
                SELECT 
                    s.SQL_ID as query_id,
                    SUBSTR(s.SQL_FULLTEXT, 1, 200) as sql_text,
                    ROUND(s.ELAPSED_TIME/1000000, 2) as execution_time_sec,
                    s.ROWS_PROCESSED as rows_processed,
                    s.OPTIMIZER_COST as cost,
                    s.DISK_READS,
                    s.BUFFER_GETS,
                    s.EXECUTIONS,
                    s.PARSE_CALLS,
                    s.FIRST_LOAD_TIME
                FROM V$SQL s
                WHERE s.ELAPSED_TIME > 1000000
                AND s.ROWS_PROCESSED > 0
                AND s.PARSING_SCHEMA_NAME NOT IN ('SYS', 'SYSTEM')
                AND ROWNUM <= 15
                ORDER BY s.ELAPSED_TIME DESC
            """
            
            df = pd.read_sql(query, self.connection)
            
            if len(df) > 0:
                # Analyse des problèmes
                def detect_issue(row):
                    if row['DISK_READS'] > 1000:
                        return 'Full table scan'
                    elif row['BUFFER_GETS'] > 10000:
                        return 'High buffer gets'
                    elif row['EXECUTIONS'] == 1 and row['ELAPSED_TIME'] > 1000000:
                        return 'First execution cost'
                    elif row['OPTIMIZER_COST'] > 1000:
                        return 'High optimizer cost'
                    else:
                        return 'Inefficient execution'
                
                df['issue'] = df.apply(detect_issue, axis=1)
                
                issue_recommendation = {
                    'Full table scan': 'Créer un index approprié ou vérifier les statistiques',
                    'High buffer gets': 'Optimiser les jointures ou réécrire la requête',
                    'First execution cost': 'Vérifier le plan d\'exécution initial',
                    'High optimizer cost': 'Analyser avec EXPLAIN PLAN',
                    'Inefficient execution': 'Considérer la réécriture ou l\'utilisation de hints'
                }
                df['recommendation'] = df['issue'].map(issue_recommendation)
            
            print(f"      → {len(df)} requêtes extraites")
            return df
            
        except Exception as e:
            print(f"      [ERROR] Extraction échouée: {e}")
            return None

    def extract_security_config_real(self):
        """Extraction depuis DBA_USERS, DBA_ROLES (Oracle 21c)"""
        print("   Extraction config sécurité depuis DBA_*...")
        
        try:
            # Requête améliorée pour Oracle 21c
            query = """
                SELECT 
                    u.USERNAME,
                    LISTAGG(r.GRANTED_ROLE, ', ') WITHIN GROUP (ORDER BY r.GRANTED_ROLE) as roles,
                    u.ACCOUNT_STATUS,
                    u.PROFILE,
                    u.DEFAULT_TABLESPACE,
                    u.TEMPORARY_TABLESPACE,
                    TO_CHAR(u.CREATED, 'YYYY-MM-DD HH24:MI:SS') as CREATED,
                    TO_CHAR(u.EXPIRY_DATE, 'YYYY-MM-DD HH24:MI:SS') as EXPIRY_DATE,
                    u.LOCK_DATE,
                    u.EXTERNAL_NAME
                FROM DBA_USERS u
                LEFT JOIN DBA_ROLE_PRIVS r ON u.USERNAME = r.GRANTEE
                WHERE u.USERNAME NOT IN ('SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'XS$NULL')
                AND u.ORACLE_MAINTAINED = 'N'
                GROUP BY u.USERNAME, u.ACCOUNT_STATUS, u.PROFILE, 
                         u.DEFAULT_TABLESPACE, u.TEMPORARY_TABLESPACE,
                         u.CREATED, u.EXPIRY_DATE, u.LOCK_DATE, u.EXTERNAL_NAME
                ORDER BY u.CREATED DESC
                FETCH FIRST 25 ROWS ONLY
            """
            
            df = pd.read_sql(query, self.connection)
            
            if len(df) > 0:
                # Évaluation risques avancée
                def assess_risk(row):
                    username = str(row['USERNAME']).upper()
                    roles = str(row['roles']).upper()
                    status = str(row['ACCOUNT_STATUS']).upper()
                    
                    # Critiques
                    if any(role in roles for role in ['DBA', 'SYSDBA', 'SYSOPER']):
                        return 'CRITICAL'
                    elif 'EXPIRED' in status or 'LOCKED' in status:
                        return 'HIGH'
                    elif 'RESOURCE' in roles or 'UNLIMITED TABLESPACE' in roles:
                        return 'MEDIUM-HIGH'
                    elif username in ['ADMIN', 'ROOT', 'SUPERUSER']:
                        return 'HIGH'
                    elif 'OPEN' in status and 'EXTERNAL_NAME' not in str(row['EXTERNAL_NAME']):
                        return 'MEDIUM'
                    else:
                        return 'LOW'
                
                df['risk_level'] = df.apply(assess_risk, axis=1)
                
                # Ajout de recommandations
                def generate_recommendation(row):
                    risk = row['risk_level']
                    if risk == 'CRITICAL':
                        return "Revoke DBA/SYSDBA privileges immediately"
                    elif risk == 'HIGH':
                        return "Review account status and privileges"
                    elif risk in ['MEDIUM', 'MEDIUM-HIGH']:
                        return "Implement least privilege principle"
                    else:
                        return "Regular monitoring recommended"
                
                df['recommendation'] = df.apply(generate_recommendation, axis=1)
            
            print(f"      → {len(df)} utilisateurs extraits")
            return df
            
        except Exception as e:
            print(f"      [ERROR] Extraction échouée: {e}")
            return None

    def extract_db_metrics_real(self):
        """Extraction métriques Oracle 21c XE"""
        print("   Extraction métriques DB Oracle 21c XE...")
        
        try:
            queries = [
                ("database_info", """
                    SELECT 
                        (SELECT name FROM v$database) as database_name,
                        (SELECT instance_name FROM v$instance) as instance_name,
                        (SELECT version FROM v$instance) as version,
                        (SELECT log_mode FROM v$database) as log_mode,
                        (SELECT platform_name FROM v$database) as platform,
                        (SELECT created FROM v$database) as db_created
                    FROM DUAL
                """),
                
                ("storage_metrics", """
                    SELECT 
                        ROUND(SUM(bytes)/1024/1024/1024, 2) as db_size_gb,
                        ROUND(SUM(CASE WHEN tablespace_name = 'SYSTEM' THEN bytes ELSE 0 END)/1024/1024, 2) as system_mb,
                        ROUND(SUM(CASE WHEN tablespace_name = 'SYSAUX' THEN bytes ELSE 0 END)/1024/1024, 2) as sysaux_mb,
                        COUNT(DISTINCT tablespace_name) as tablespace_count
                    FROM dba_segments
                """),
                
                ("performance_metrics", """
                    SELECT 
                        (SELECT COUNT(*) FROM v$session WHERE status='ACTIVE') as active_sessions,
                        (SELECT value/1024/1024 FROM v$parameter WHERE name='sga_target') as sga_size_mb,
                        (SELECT value/1024/1024 FROM v$parameter WHERE name='pga_aggregate_target') as pga_size_mb,
                        (SELECT ROUND(SUM(value)/1024/1024, 2) FROM v$sga) as total_sga_mb,
                        (SELECT COUNT(*) FROM v$process) as total_processes
                    FROM DUAL
                """),
                
                ("backup_status", """
                    SELECT 
                        (SELECT MAX(completion_time) FROM v$backup_set) as last_backup_time,
                        (SELECT COUNT(*) FROM v$backup_set WHERE completion_time > SYSDATE - 1) as backups_last_24h,
                        (SELECT backup_type FROM v$backup_set WHERE completion_time = (SELECT MAX(completion_time) FROM v$backup_set) AND ROWNUM = 1) as last_backup_type
                    FROM DUAL
                """)
            ]
            
            metrics = {}
            for name, query in queries:
                try:
                    df_temp = pd.read_sql(query, self.connection)
                    if not df_temp.empty:
                        metrics.update(df_temp.iloc[0].to_dict())
                except Exception as e:
                    print(f"      [WARN] Métrique {name} ignorée: {e}")
                    continue
            
            # Créer le DataFrame final
            if metrics:
                df = pd.DataFrame([metrics])
                
                # Déterminer criticité
                db_size = df.get('db_size_gb', [0])[0] if 'db_size_gb' in df.columns else 0
                if db_size > 100:
                    criticality = 'CRITICAL'
                elif db_size > 50:
                    criticality = 'HIGH'
                elif db_size > 10:
                    criticality = 'MEDIUM'
                else:
                    criticality = 'LOW'
                
                df['criticality'] = criticality
                
                print(f"      → {len(metrics)} métriques extraites")
                return df
            else:
                print("      [WARN] Aucune métrique extraite")
                return None
                
        except Exception as e:
            print(f"      [ERROR] Extraction échouée: {e}")
            return None

    # =========================================================
    # ========== GÉNÉRATION SYNTHÉTIQUE ENRICHIE ===========
    # =========================================================
    
    def _generate_audit_logs_sim(self):
        """Version enrichie : 50 normaux + 20 suspects"""
        print("   Génération logs d'audit (simulation)...")
        
        normal_logs = []
        users = ["APP_USER", "ANALYST", "REPORT_USER", "ETL_USER", "READ_ONLY", "DATA_SCIENTIST"]
        actions = ["SELECT", "INSERT", "UPDATE", "DELETE"]
        tables = ["CUSTOMERS", "ORDERS", "PRODUCTS", "INVOICES", "EMPLOYEES", "INVENTORY", "PAYMENTS"]
        base_time = datetime.now() - timedelta(days=30)
        
        # 50 logs normaux
        for i in range(50):
            normal_logs.append({
                "log_id": f"LOG_{i+1:04d}",
                "timestamp": (base_time + timedelta(
                    days=random.randint(0, 29),
                    hours=random.randint(8, 18),
                    minutes=random.randint(0, 59)
                )).strftime("%Y-%m-%d %H:%M:%S"),
                "username": random.choice(users),
                "action": random.choice(actions),
                "object_name": random.choice(tables),
                "status": 0,  # SUCCESS
                "ip_address": f"192.168.1.{random.randint(10, 100)}",
                "session_id": random.randint(1000, 9999),
                "severity": "NORMAL",
                "policies": "ORA_SECURECONFIG"
            })
        
        # 20 logs suspects variés
        suspect_scenarios = [
            {"action": "DROP TABLE", "object": "USER_CREDENTIALS", "severity": "CRITICAL", "status": 0},
            {"action": "ALTER TABLE", "object": "SALARY_INFO", "severity": "HIGH", "status": 3113},
            {"action": "GRANT DBA", "object": "TO BACKDOOR", "severity": "CRITICAL", "status": 0},
            {"action": "CREATE USER", "object": "HACKER_ACCOUNT", "severity": "CRITICAL", "status": 1920},
            {"action": "DELETE", "object": "AUDIT_LOGS", "severity": "CRITICAL", "status": 942},
            {"action": "SELECT", "object": "CREDIT_CARDS", "severity": "HIGH", "status": 0},
            {"action": "UPDATE", "object": "PASSWORD_HASH", "severity": "HIGH", "status": 0},
            {"action": "EXECUTE", "object": "UTL_FILE", "severity": "HIGH", "status": 4043},
        ]
        
        suspect_logs = []
        for i in range(20):
            scenario = random.choice(suspect_scenarios)
            suspect_logs.append({
                "log_id": f"LOG_{i+51:04d}",
                "timestamp": (base_time + timedelta(
                    days=random.randint(0, 29),
                    hours=random.choice([0, 1, 2, 3, 22, 23]),
                    minutes=random.randint(0, 59)
                )).strftime("%Y-%m-%d %H:%M:%S"),
                "username": random.choice(["UNKNOWN_USER", "ADMIN", "SYS", "ROOT", "TEMP_ADMIN", "EXTERNAL_SYS"]),
                "action": scenario["action"],
                "object_name": scenario["object"],
                "status": scenario["status"],
                "ip_address": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
                "session_id": random.randint(10000, 99999),
                "severity": scenario["severity"],
                "policies": "ORA_LOGON_FAILURES, ORA_DATABASE_PARAMETER"
            })
        
        df = pd.DataFrame(normal_logs + suspect_logs)
        print(f"      → {len(df)} logs générés (50 normaux + 20 suspects)")
        return df

    def _generate_slow_queries_sim(self):
        """Version enrichie : 10 requêtes lentes variées"""
        print("   Génération requêtes lentes (simulation)...")
        
        queries = [
            {
                "query_id": "Q001",
                "sql_text": "SELECT * FROM orders WHERE order_date > '2023-01-01' ORDER BY order_id",
                "execution_time_sec": 45.2,
                "rows_processed": 1500000,
                "cost": 5000,
                "disk_reads": 12000,
                "buffer_gets": 45000,
                "executions": 5,
                "parse_calls": 5,
                "first_load_time": "2024-12-01/10:30:00",
                "issue": "Full table scan",
                "recommendation": "Créer un index sur order_date et utiliser WHERE avec plage spécifique"
            },
            {
                "query_id": "Q002",
                "sql_text": "SELECT c.*, o.* FROM customers c JOIN orders o ON c.id = o.customer_id WHERE c.country = 'USA'",
                "execution_time_sec": 38.7,
                "rows_processed": 850000,
                "cost": 4200,
                "disk_reads": 8500,
                "buffer_gets": 52000,
                "executions": 12,
                "parse_calls": 12,
                "first_load_time": "2024-11-15/14:22:00",
                "issue": "Nested loops join inefficient",
                "recommendation": "Utiliser HASH JOIN avec hint /*+ USE_HASH(c o) */ et index sur customers.country"
            },
            {
                "query_id": "Q003",
                "sql_text": "SELECT DISTINCT product_name FROM products WHERE category LIKE '%elect%' AND price > 100",
                "execution_time_sec": 29.3,
                "rows_processed": 500000,
                "cost": 3500,
                "disk_reads": 4500,
                "buffer_gets": 38000,
                "executions": 8,
                "parse_calls": 8,
                "first_load_time": "2024-12-10/09:15:00",
                "issue": "LIKE avec wildcard initial",
                "recommendation": "Utiliser Oracle Text Search ou réécrire avec category LIKE 'elect%' si possible"
            },
            {
                "query_id": "Q004",
                "sql_text": "UPDATE employees SET salary = salary * 1.1 WHERE department_id IN (SELECT id FROM departments WHERE active = 'Y')",
                "execution_time_sec": 52.1,
                "rows_processed": 75000,
                "cost": 6800,
                "disk_reads": 9500,
                "buffer_gets": 67000,
                "executions": 1,
                "parse_calls": 1,
                "first_load_time": "2024-12-20/16:45:00",
                "issue": "Subquery non optimisée dans IN clause",
                "recommendation": "Remplacer par JOIN: UPDATE employees e SET salary = salary * 1.1 WHERE EXISTS (SELECT 1 FROM departments d WHERE d.id = e.department_id AND d.active = 'Y')"
            },
            {
                "query_id": "Q005",
                "sql_text": "SELECT * FROM invoices WHERE YEAR(invoice_date) = 2024 AND status = 'PAID'",
                "execution_time_sec": 41.8,
                "rows_processed": 1200000,
                "cost": 4900,
                "disk_reads": 11000,
                "buffer_gets": 42000,
                "executions": 25,
                "parse_calls": 25,
                "first_load_time": "2024-11-05/11:30:00",
                "issue": "Fonction sur colonne indexée",
                "recommendation": "Réécrire sans fonction: invoice_date >= '2024-01-01' AND invoice_date < '2025-01-01' AND status = 'PAID'"
            },
            {
                "query_id": "Q006",
                "sql_text": "SELECT p.*, (SELECT COUNT(*) FROM orders WHERE product_id = p.id) as order_count FROM products p",
                "execution_time_sec": 67.4,
                "rows_processed": 320000,
                "cost": 8200,
                "disk_reads": 15000,
                "buffer_gets": 89000,
                "executions": 3,
                "parse_calls": 3,
                "first_load_time": "2024-10-28/13:20:00",
                "issue": "Scalar subquery dans SELECT",
                "recommendation": "Remplacer par LEFT JOIN: SELECT p.*, COUNT(o.id) as order_count FROM products p LEFT JOIN orders o ON p.id = o.product_id GROUP BY p.id, p.name, ..."
            },
            {
                "query_id": "Q007",
                "sql_text": "SELECT * FROM audit_logs ORDER BY timestamp DESC FETCH FIRST 1000 ROWS ONLY",
                "execution_time_sec": 33.6,
                "rows_processed": 2000000,
                "cost": 5500,
                "disk_reads": 13000,
                "buffer_gets": 48000,
                "executions": 50,
                "parse_calls": 50,
                "first_load_time": "2024-12-12/08:45:00",
                "issue": "Tri sur table volumineuse non indexée",
                "recommendation": "Créer index sur timestamp, utiliser pagination avec OFFSET-FETCH, partitionner la table"
            },
            {
                "query_id": "Q008",
                "sql_text": "SELECT customer_id, SUM(amount) FROM payments WHERE status != 'CANCELLED' GROUP BY customer_id HAVING SUM(amount) > 10000",
                "execution_time_sec": 44.9,
                "rows_processed": 950000,
                "cost": 5800,
                "disk_reads": 8900,
                "buffer_gets": 51000,
                "executions": 15,
                "parse_calls": 15,
                "first_load_time": "2024-11-22/15:10:00",
                "issue": "Négation dans WHERE + aggregation",
                "recommendation": "Utiliser IN ('PAID', 'PENDING') et créer index couvrant (status, customer_id, amount)"
            },
            {
                "query_id": "Q009",
                "sql_text": "WITH cte AS (SELECT * FROM transactions WHERE trans_date > ADD_MONTHS(SYSDATE, -6)) SELECT * FROM cte WHERE amount > (SELECT AVG(amount) FROM cte)",
                "execution_time_sec": 58.3,
                "rows_processed": 1800000,
                "cost": 7200,
                "disk_reads": 14000,
                "buffer_gets": 75000,
                "executions": 7,
                "parse_calls": 7,
                "first_load_time": "2024-12-05/10:05:00",
                "issue": "CTE réutilisé avec agrégation",
                "recommendation": "Calculer la moyenne dans un sous-select séparé ou matérialiser la CTE"
            },
            {
                "query_id": "Q010",
                "sql_text": "SELECT d.dept_name, e.emp_name, e.salary FROM departments d CROSS JOIN employees e WHERE e.salary > 50000 AND d.location = 'HQ'",
                "execution_time_sec": 49.7,
                "rows_processed": 2500000,
                "cost": 6100,
                "disk_reads": 16500,
                "buffer_gets": 92000,
                "executions": 2,
                "parse_calls": 2,
                "first_load_time": "2024-11-30/17:25:00",
                "issue": "CROSS JOIN inutile",
                "recommendation": "Utiliser JOIN approprié avec condition, ou revoir la logique métier si CROSS JOIN est vraiment nécessaire"
            }
        ]
        
        df = pd.DataFrame(queries)
        print(f"      → {len(df)} requêtes générées")
        return df

    def _generate_security_config_sim(self):
        """Version enrichie : 15 utilisateurs avec rôles variés"""
        print("   Génération config sécurité (simulation)...")
        
        configs = [
            {"username": "SYSTEM", "roles": "DBA, SELECT_CATALOG_ROLE, EXECUTE_CATALOG_ROLE", 
             "account_status": "OPEN", "profile": "DEFAULT", "risk_level": "CRITICAL",
             "default_tablespace": "SYSTEM", "created": "2023-01-15 09:30:00"},
            
            {"username": "APP_USER", "roles": "CONNECT, RESOURCE", 
             "account_status": "OPEN", "profile": "APP_PROFILE", "risk_level": "MEDIUM",
             "default_tablespace": "USERS", "created": "2024-03-10 14:22:00"},
            
            {"username": "READ_ONLY", "roles": "CONNECT", 
             "account_status": "OPEN", "profile": "DEFAULT", "risk_level": "LOW",
             "default_tablespace": "USERS", "created": "2024-06-05 11:15:00"},
            
            {"username": "ETL_SERVICE", "roles": "CONNECT, RESOURCE, IMP_FULL_DATABASE", 
             "account_status": "OPEN", "profile": "ETL_PROFILE", "risk_level": "HIGH",
             "default_tablespace": "ETL_DATA", "created": "2024-02-20 08:45:00"},
            
            {"username": "ADMIN_BACKUP", "roles": "DBA, EXP_FULL_DATABASE", 
             "account_status": "LOCKED", "profile": "DEFAULT", "risk_level": "CRITICAL",
             "default_tablespace": "SYSTEM", "created": "2023-11-30 16:30:00"},
            
            {"username": "ANALYST_JOHN", "roles": "CONNECT, SELECT_ANY_TABLE", 
             "account_status": "OPEN", "profile": "ANALYST_PROFILE", "risk_level": "HIGH",
             "default_tablespace": "USERS", "created": "2024-04-12 10:20:00"},
            
            {"username": "TEMP_CONTRACTOR", "roles": "CONNECT, RESOURCE", 
             "account_status": "EXPIRED", "profile": "TEMPORARY", "risk_level": "MEDIUM-HIGH",
             "default_tablespace": "TEMP_TS", "created": "2024-09-01 13:40:00"},
            
            {"username": "REPORT_GEN", "roles": "CONNECT", 
             "account_status": "OPEN", "profile": "DEFAULT", "risk_level": "LOW",
             "default_tablespace": "USERS", "created": "2024-07-22 09:10:00"},
            
            {"username": "DEV_TEST", "roles": "CONNECT, RESOURCE, CREATE_SESSION", 
             "account_status": "OPEN", "profile": "DEVELOPER", "risk_level": "MEDIUM",
             "default_tablespace": "DEV_DATA", "created": "2024-05-18 15:25:00"},
            
            {"username": "AUDIT_USER", "roles": "CONNECT, AUDIT_ADMIN", 
             "account_status": "OPEN", "profile": "AUDIT_PROFILE", "risk_level": "HIGH",
             "default_tablespace": "AUDIT_DATA", "created": "2024-01-30 08:00:00"},
            
            {"username": "WEB_SERVICE", "roles": "CONNECT", 
             "account_status": "OPEN", "profile": "SERVICE_ACCOUNT", "risk_level": "MEDIUM",
             "default_tablespace": "USERS", "created": "2024-08-14 12:35:00"},
            
            {"username": "LEGACY_APP", "roles": "CONNECT, RESOURCE, UNLIMITED_TABLESPACE", 
             "account_status": "OPEN", "profile": "LEGACY", "risk_level": "HIGH",
             "default_tablespace": "LEGACY_TS", "created": "2023-08-05 10:50:00"},
            
            {"username": "DATA_SCIENTIST", "roles": "CONNECT, RESOURCE, CREATE ANY TABLE", 
             "account_status": "OPEN", "profile": "DATA_SCIENCE", "risk_level": "MEDIUM-HIGH",
             "default_tablespace": "DATA_SCIENCE", "created": "2024-10-08 11:45:00"},
            
            {"username": "MONITORING", "roles": "CONNECT, SELECT ANY DICTIONARY", 
             "account_status": "OPEN", "profile": "MONITOR_PROFILE", "risk_level": "HIGH",
             "default_tablespace": "USERS", "created": "2024-02-25 14:15:00"},
            
            {"username": "API_GATEWAY", "roles": "CONNECT", 
             "account_status": "OPEN", "profile": "SERVICE_ACCOUNT", "risk_level": "MEDIUM",
             "default_tablespace": "USERS", "created": "2024-11-12 16:40:00"}
        ]
        
        df = pd.DataFrame(configs)
        
        # Ajout de recommandations basées sur le risque
        risk_recommendations = {
            "CRITICAL": "Revoke unnecessary privileges immediately",
            "HIGH": "Review and reduce privileges, implement monitoring",
            "MEDIUM-HIGH": "Apply least privilege principle",
            "MEDIUM": "Regular review of access rights",
            "LOW": "Standard monitoring"
        }
        df['recommendation'] = df['risk_level'].map(risk_recommendations)
        
        print(f"      → {len(df)} configurations générées")
        return df

    def _generate_db_metrics_sim(self):
        """Version enrichie : métriques complètes pour Oracle 21c XE"""
        print("   Génération métriques DB (simulation)...")
        
        df = pd.DataFrame([{
            "database_name": "XEPDB1",
            "instance_name": "XE",
            "version": "21.3.0.0.0",
            "log_mode": "ARCHIVELOG",
            "platform": "Linux x86 64-bit",
            "db_created": "2026-01-08 14:07:20",
            "db_size_gb": 2.5,  # Taille typique XE
            "system_mb": 850.5,
            "sysaux_mb": 620.3,
            "tablespace_count": 8,
            "active_sessions": 12,
            "sga_size_mb": 1024,  # XE limit
            "pga_size_mb": 512,
            "total_sga_mb": 1536,
            "total_processes": 45,
            "last_backup_time": (datetime.now() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
            "backups_last_24h": 2,
            "last_backup_type": "FULL",
            "criticality": "MEDIUM",
            "backup_status": "OK",
            "uptime_days": 0.5
        }])
        
        print("      → Métriques générées (Oracle 21c XE simulé)")
        return df

    def _generate_prompts_yaml(self):
        """Fichier prompts.yaml enrichi avec tous les modules"""
        print("   Génération prompts.yaml...")
        
        prompts = {
            "security_audit": {
                "analyze_users": """Analyse cette configuration utilisateurs Oracle 21c.
Identifie les risques de sécurité selon ces critères :
- Privilèges excessifs (DBA, SYSDBA, SYSOPER)
- Comptes par défaut non sécurisés
- Rôles cumulés dangereux
- Comptes expirés mais actifs
- Profils non sécurisés
- Tablespace SYSTEM utilisé par des utilisateurs applicatifs

Configuration : {config}

Fournis : score/100, risques détectés (CRITIQUE/HAUTE/MOYENNE/FAIBLE), recommandations.""",
                
                "assess_privileges": """Évalue ces privilèges système Oracle 21c.
Vérifie : moindre privilège, séparation des responsabilités, accès sensibles.

Privilèges : {privileges}
Utilisateurs : {users}

Format : 
- Sévérité (CRITIQUE/HAUTE/MOYENNE/FAIBLE)
- Justification détaillée
- Correction immédiate
- Action à long terme""",
                
                "check_audit_policies": """Vérifie les politiques d'audit unifié Oracle 21c.
Politiques : {policies}

Évalue : couverture d'audit, événements critiques audités, lacunes."""
            },
            
            "query_optimization": {
                "explain_plan": """Explique ce plan d'exécution Oracle 21c en termes simples.
Identifie les 3 opérations les plus coûteuses et leurs impacts.

Plan : {plan}
Requête : {query}
Statistiques : {stats}

Format : 
1. Explication claire du flux
2. Points coûteux numérotés avec % d'impact
3. Suggestions de réduction de coût""",
                
                "suggest_optimization": """Propose 2-3 optimisations concrètes pour cette requête Oracle 21c.

Requête : {query}
Temps d'exécution : {time}s
Coût optimiseur : {cost}
Problème détecté : {issue}
Métriques : {metrics}

Fournis :
1. Recommandation 1 (prioritaire) avec code SQL
2. Recommandation 2 (alternative)
3. Recommandation 3 (architecturale si nécessaire)
4. Impact estimé sur performance""",
                
                "index_recommendation": """Recommande des index pour améliorer cette requête Oracle 21c.

Requête : {query}
Tables concernées : {tables}
Colonnes filtrées/jointees : {columns}
Volume de données : {volume}

Fournis :
- Index recommandés (colonne, type)
- Impact estimé
- Énoncé CREATE INDEX
- Considérations (maintien, espace)"""
            },
            
            "anomaly_detection": {
                "analyze_log": """Analyse ce log d'audit Oracle 21c. Est-il suspect ?

Log : {log}
Contexte : {context}
Heure : {time}
Utilisateur : {user}

Évalue selon :
1. Timing (heures normales de travail ?)
2. Utilisateur (habituel pour cette action ?)
3. Action (conforme aux rôles ?)
4. Objet cible (sensible ?)
5. IP (connue ?)

Classe en : NORMAL / SUSPECT / CRITIQUE
Justifie ta réponse avec des indicateurs.""",
                
                "detect_intrusion": """Détecte les patterns d'attaque dans cette séquence de logs Oracle 21c.
Recherche : injection SQL, escalade privilèges, exfiltration données, accès hors heure.

Logs : {logs}
Période : {period}
Utilisateurs concernés : {users}

Identifie :
1. Type d'attaque potentielle
2. Sévérité (CRITIQUE/HAUTE/MOYENNE)
3. Indicateurs de compromission
4. Recommandation immédiate
5. Investigation à mener""",
                
                "sequence_analysis": """Analyse cette séquence temporelle de logs Oracle.

Séquence : {sequence}
Fenêtre temporelle : {window}

Recherche :
- Activité anormale groupée
- Tentatives répétées
- Patterns d'attaque
- Comportements inhabituels

Fournis : timeline des événements, corrélations, risque global."""
            },
            
            "backup_strategy": {
                "recommend_plan": """Recommande une stratégie de sauvegarde Oracle 21c XE optimale.

Contexte Oracle 21c XE :
- Taille DB : {size} GB (limite XE: 12GB)
- RPO requis : {rpo}
- RTO requis : {rto}
- Criticité : {criticality}
- Espace disponible : {space}
- Archive mode : {archive_mode}

Fournis en JSON :
{
  "type_backup": ["complète", "incrémentielle", "archivelog"],
  "frequence": {"full": "X", "incremental": "Y", "archivelog": "Z"},
  "retention": {"days": N, "recovery_window": M},
  "emplacement": ["local", "cloud", "nfs"],
  "outil": ["RMAN", "Data Pump", "Cloud Backup"],
  "commande_exemple": "commande RMAN",
  "coût_estimé": "$",
  "limitations_XE": ["..."]
}""",
                
                "validate_rman_script": """Valide ce script RMAN Oracle 21c.

Script : {script}
Configuration : {config}

Vérifie :
1. Syntaxe correcte
2. Compatibilité Oracle 21c XE
3. Bonnes pratiques
4. Gestion des erreurs
5. Plan de restauration

Corrige si nécessaire."""
            },
            
            "recovery_guide": {
                "generate_playbook": """Génère un playbook RMAN détaillé pour Oracle 21c XE.

Scénario : {scenario}
Backup disponible : {backup_status}
Date cible : {target_date}
PDB/Non-CDB : {pdb_status}
Espace disponible : {space}

Fournis :
1. Étapes numérotées avec vérifications
2. Commandes RMAN exactes (Oracle 21c)
3. Points de validation à chaque étape
4. Durée estimée par étape
5. Rollback plan en cas d'échec
6. Post-recovery validation""",
                
                "point_in_time_recovery": """Guide de récupération point-in-time Oracle 21c.

Date/heure cible : {target_datetime}
Type de perte : {loss_type}
Objets affectés : {affected_objects}
Backups disponibles : {available_backups}

Fournis playbook avec :
1. Pré-requis et vérifications
2. Commandes RMAN exactes
3. Vérification des SCN/Time
4. Procédure de switchover
5. Validation post-récupération"""
            },
            
            "general_dba": {
                "troubleshoot_performance": """Diagnostique ce problème de performance Oracle 21c.

Symptômes : {symptoms}
Métriques : {metrics}
Alertes : {alerts}
Récent changements : {changes}

Fournis diagnostic par étapes :
1. Investigations immédiates
2. Commandes à exécuter
3. Interprétation des résultats
4. Correctifs possibles
5. Monitoring post-correction""",
                
                "capacity_planning": """Planification de capacité Oracle 21c XE.

Utilisation actuelle : {current_usage}
Croissance prévue : {growth}
Objectifs : {objectives}
Contraintes XE : {xe_constraints}

Fournis recommandations :
1. Projections 3/6/12 mois
2. Points de rupture
3. Actions préventives
4. Migration planning"""
            }
        }
        
        os.makedirs("data", exist_ok=True)
        with open("data/prompts.yaml", "w", encoding="utf-8") as f:
            yaml.dump(prompts, f, allow_unicode=True, default_flow_style=False)
        
        print("      → prompts.yaml créé (6 modules, 15 prompts)")
        return prompts

    # =========================================================
    # ========== ORCHESTRATION EXTRACTION ===========
    # =========================================================
    
    def extract_audit_logs(self):
        if not self.use_simulation:
            df = self.extract_audit_logs_real()
            if df is not None and len(df) > 0:
                df.to_csv("data/audit_logs.csv", index=False)
                return df
        
        df = self._generate_audit_logs_sim()
        df.to_csv("data/audit_logs.csv", index=False)
        return df

    def extract_slow_queries(self):
        if not self.use_simulation:
            df = self.extract_slow_queries_real()
            if df is not None and len(df) > 0:
                df.to_csv("data/slow_queries.csv", index=False)
                return df
        
        df = self._generate_slow_queries_sim()
        df.to_csv("data/slow_queries.csv", index=False)
        return df

    def extract_security_config(self):
        if not self.use_simulation:
            df = self.extract_security_config_real()
            if df is not None and len(df) > 0:
                df.to_csv("data/security_config.csv", index=False)
                return df
        
        df = self._generate_security_config_sim()
        df.to_csv("data/security_config.csv", index=False)
        return df

    def extract_db_metrics(self):
        if not self.use_simulation:
            df = self.extract_db_metrics_real()
            if df is not None and len(df) > 0:
                df.to_csv("data/db_metrics.csv", index=False)
                return df
        
        df = self._generate_db_metrics_sim()
        df.to_csv("data/db_metrics.csv", index=False)
        return df

    def generate_all_data(self):
        """Orchestre l'extraction complète"""
        print("\n" + "="*60)
        print("MODULE 1 : EXTRACTION DONNÉES ORACLE 21c XE")
        print("="*60 + "\n")

        os.makedirs("data", exist_ok=True)

        # Extraction des 4 sources principales
        print("📊 Extraction des données...")
        print("-" * 40)
        
        audit_df = self.extract_audit_logs()
        slow_df = self.extract_slow_queries()
        security_df = self.extract_security_config()
        metrics_df = self.extract_db_metrics()
        
        # Génération prompts.yaml
        print("\n📝 Génération des prompts...")
        print("-" * 40)
        self._generate_prompts_yaml()

        # Résumé
        print("\n" + "="*60)
        print("RÉSUMÉ EXTRACTION")
        print("="*60)
        
        files = [
            ("audit_logs.csv", audit_df),
            ("slow_queries.csv", slow_df),
            ("security_config.csv", security_df),
            ("db_metrics.csv", metrics_df)
        ]
        
        for filename, df in files:
            if df is not None:
                filepath = f"data/{filename}"
                try:
                    saved_df = pd.read_csv(filepath)
                    print(f"✅ {filename:20} : {len(saved_df):4} lignes")
                except:
                    print(f"⚠️  {filename:20} : FICHIER NON LU")
            else:
                print(f"❌ {filename:20} : ÉCHEC GÉNÉRATION")
        
        # Vérification prompts.yaml
        try:
            with open("data/prompts.yaml", "r", encoding="utf-8") as f:
                prompts_data = yaml.safe_load(f)
                prompt_count = sum(len(v) for v in prompts_data.values())
                print(f"✅ prompts.yaml         : {prompt_count} prompts ({len(prompts_data)} modules)")
        except:
            print("❌ prompts.yaml         : ERREUR")
        
        print("="*60)
        print(f"Mode: {'SIMULATION' if self.use_simulation else 'CONNEXION RÉELLE'}")
        print("="*60 + "\n")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("[OK] Connexion Oracle fermée")


# =========================================================
# ======================== TEST ============================
# =========================================================

if __name__ == "__main__":
    import sys

    print("""
╔══════════════════════════════════════════════════════════════╗
║   MODULE 1 : Oracle 21c XE Data Extractor & Generator      ║
║   Version : 3.0 (Optimisé pour Oracle 21c XE + XEPDB1)     ║
╚══════════════════════════════════════════════════════════════╝

Configuration détectée:
• Host: localhost:1521/XEPDB1
• User: system
• Mode: Connexion réelle tentée automatiquement

Usage:
  python data_extractor.py           → Tentative connexion réelle
  python data_extractor.py --sim     → Forcer mode simulation
""")

    force_sim = len(sys.argv) > 1 and sys.argv[1] == "--sim"
    
    extractor = OracleDataExtractor(use_simulation=force_sim)
    extractor.generate_all_data()
    extractor.close()

    print("\n✅ MODULE 1 TERMINÉ AVEC SUCCÈS")
    print("📂 Fichiers générés dans ./data/")
    print("📋 Prochaine étape : MODULE 2 (RAG Setup avec ChromaDB)\n")
    
    # Instructions supplémentaires
    if extractor.use_simulation:
        print("💡 Pour utiliser la connexion réelle à Oracle 21c XE :")
        print("   1. Assurez-vous que le conteneur Docker est en cours d'exécution")
        print("   2. Vérifiez votre fichier .env dans la racine du projet")
        print("   3. Installez oracledb: pip install oracledb")
        print("   4. Relancez sans --sim\n")