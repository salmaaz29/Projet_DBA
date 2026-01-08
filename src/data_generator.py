"""
MODULE 1 : Générateur de Données Synthétiques Oracle
Génère tous les CSV nécessaires pour simuler une instance Oracle
Conforme à l'énoncé : extraction depuis AUD$, V$SQL, DBA_USERS, etc.
"""

import pandas as pd
import random
from datetime import datetime, timedelta
import json
import os

def generate_audit_logs():
    """
    Génère 70 logs d'audit (50 normaux + 20 suspects)
    Simule : SELECT * FROM sys.aud$ WHERE timestamp > SYSDATE - 30
    """
    
    print("🔄 Génération des logs d'audit (simulation table AUD$)...")
    
    # Logs normaux (50) - Activité normale durant heures bureau
    normal_logs = []
    users = ["APP_USER", "ANALYST", "REPORT_USER", "ETL_USER", "READ_ONLY"]
    actions = ["SELECT", "INSERT", "UPDATE"]
    tables = ["CUSTOMERS", "ORDERS", "PRODUCTS", "INVOICES", "EMPLOYEES"]
    
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(50):
        log = {
            "log_id": f"LOG_{i+1:03d}",
            "timestamp": (base_time + timedelta(
                days=random.randint(0, 29),
                hours=random.randint(8, 18),
                minutes=random.randint(0, 59)
            )).strftime("%Y-%m-%d %H:%M:%S"),
            "username": random.choice(users),
            "action": random.choice(actions),
            "object_name": random.choice(tables),
            "status": "SUCCESS",
            "ip_address": f"192.168.1.{random.randint(10, 100)}",
            "session_id": random.randint(1000, 9999),
            "severity": "NORMAL"
        }
        normal_logs.append(log)
    
    # Logs suspects (20) - Activité anormale
    suspect_logs = []
    suspect_users = ["UNKNOWN_USER", "ADMIN", "SYS", "EXTERNAL_USER", "ROOT"]
    suspect_actions = ["DROP", "ALTER", "GRANT", "CREATE USER", "DELETE", "TRUNCATE"]
    sensitive_tables = ["USER_CREDENTIALS", "SALARY_INFO", "CREDIT_CARDS", "SYS.AUD$", "DBA_USERS"]
    
    for i in range(20):
        log = {
            "log_id": f"LOG_{i+51:03d}",
            "timestamp": (base_time + timedelta(
                days=random.randint(0, 29),
                hours=random.choice([0, 1, 2, 3, 22, 23]),  # Heures suspectes
                minutes=random.randint(0, 59)
            )).strftime("%Y-%m-%d %H:%M:%S"),
            "username": random.choice(suspect_users),
            "action": random.choice(suspect_actions),
            "object_name": random.choice(sensitive_tables),
            "status": random.choice(["SUCCESS", "FAILED", "BLOCKED"]),
            "ip_address": f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
            "session_id": random.randint(10000, 99999),
            "severity": random.choice(["SUSPECT", "CRITICAL", "HIGH"])
        }
        suspect_logs.append(log)
    
    # Combiner et mélanger
    all_logs = normal_logs + suspect_logs
    random.shuffle(all_logs)
    
    df = pd.DataFrame(all_logs)
    df.to_csv("data/audit_logs.csv", index=False)
    
    print(f"   ✅ {len(all_logs)} logs générés (50 normaux + 20 suspects)")
    return df


def generate_slow_queries():
    """
    Génère 10 requêtes SQL lentes avec plans d'exécution
    Simule : SELECT * FROM v$sql WHERE elapsed_time > 1000000
    """
    
    print("🔄 Génération des requêtes lentes (simulation V$SQL)...")
    
    queries = [
        {
            "query_id": "Q001",
            "sql_text": "SELECT * FROM orders WHERE order_date > '2023-01-01'",
            "execution_time_sec": 45.2,
            "rows_processed": 1500000,
            "buffer_gets": 250000,
            "disk_reads": 12000,
            "executions": 156,
            "execution_plan": "TABLE ACCESS FULL | ORDERS | Cost: 5000 | Rows: 1.5M",
            "cost": 5000,
            "issue": "Full table scan sur 1.5M lignes - Index manquant sur ORDER_DATE",
            "recommendation": "CREATE INDEX idx_orders_date ON orders(order_date)"
        },
        {
            "query_id": "Q002",
            "sql_text": "SELECT c.name, COUNT(o.id) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name",
            "execution_time_sec": 32.8,
            "rows_processed": 800000,
            "buffer_gets": 180000,
            "disk_reads": 8500,
            "executions": 89,
            "execution_plan": "HASH JOIN | Cost: 3200 | Rows: 800K",
            "cost": 3200,
            "issue": "Pas d'index sur customer_id - HASH JOIN coûteux",
            "recommendation": "CREATE INDEX idx_orders_customer ON orders(customer_id)"
        },
        {
            "query_id": "Q003",
            "sql_text": "SELECT * FROM products WHERE UPPER(product_name) LIKE '%PHONE%'",
            "execution_time_sec": 28.5,
            "rows_processed": 500000,
            "buffer_gets": 120000,
            "disk_reads": 6000,
            "executions": 234,
            "execution_plan": "TABLE ACCESS FULL | PRODUCTS | Cost: 2800",
            "cost": 2800,
            "issue": "Fonction UPPER() empêche utilisation index - Leading wildcard",
            "recommendation": "Créer index fonction-based OU réécrire sans fonction"
        },
        {
            "query_id": "Q004",
            "sql_text": "SELECT e.name, d.dept_name FROM employees e, departments d WHERE e.dept_id = d.id",
            "execution_time_sec": 18.3,
            "rows_processed": 300000,
            "buffer_gets": 95000,
            "disk_reads": 4200,
            "executions": 67,
            "execution_plan": "NESTED LOOPS | Cost: 1500",
            "cost": 1500,
            "issue": "Syntaxe OLD JOIN (Oracle 8i) - Non optimal",
            "recommendation": "Réécrire avec JOIN explicite : FROM employees e JOIN departments d"
        },
        {
            "query_id": "Q005",
            "sql_text": "SELECT * FROM invoices WHERE invoice_date BETWEEN '2023-01-01' AND '2023-12-31'",
            "execution_time_sec": 55.7,
            "rows_processed": 2000000,
            "buffer_gets": 320000,
            "disk_reads": 15000,
            "executions": 412,
            "execution_plan": "INDEX RANGE SCAN | INVOICES_DATE_IDX | Cost: 6000",
            "cost": 6000,
            "issue": "Index existe mais sélectivité faible (trop de lignes retournées)",
            "recommendation": "Partitionner table par année OU ajouter colonnes au SELECT"
        },
        {
            "query_id": "Q006",
            "sql_text": "SELECT DISTINCT customer_id FROM orders",
            "execution_time_sec": 22.1,
            "rows_processed": 1200000,
            "buffer_gets": 210000,
            "disk_reads": 9800,
            "executions": 178,
            "execution_plan": "SORT UNIQUE | Cost: 2500",
            "cost": 2500,
            "issue": "DISTINCT coûteux sur gros volume - Tri en mémoire",
            "recommendation": "Utiliser GROUP BY customer_id (plus efficace avec index)"
        },
        {
            "query_id": "Q007",
            "sql_text": "SELECT * FROM transactions WHERE amount > (SELECT AVG(amount) FROM transactions)",
            "execution_time_sec": 65.4,
            "rows_processed": 3000000,
            "buffer_gets": 450000,
            "disk_reads": 18000,
            "executions": 23,
            "execution_plan": "SUBQUERY | TABLE ACCESS FULL | Cost: 8000",
            "cost": 8000,
            "issue": "Sous-requête scalaire exécutée pour chaque ligne",
            "recommendation": "Utiliser WITH clause (CTE) pour calculer AVG une seule fois"
        },
        {
            "query_id": "Q008",
            "sql_text": "SELECT p.*, c.category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE c.active = 1",
            "execution_time_sec": 15.2,
            "rows_processed": 250000,
            "buffer_gets": 85000,
            "disk_reads": 3500,
            "executions": 145,
            "execution_plan": "HASH JOIN OUTER | Cost: 1200",
            "cost": 1200,
            "issue": "Filtre WHERE sur table droite d'un LEFT JOIN - Convertit en INNER JOIN",
            "recommendation": "Utiliser INNER JOIN directement OU déplacer filtre dans ON"
        },
        {
            "query_id": "Q009",
            "sql_text": "SELECT * FROM sales WHERE sales_date IN (SELECT date FROM calendar WHERE is_holiday = 1)",
            "execution_time_sec": 38.9,
            "rows_processed": 900000,
            "buffer_gets": 165000,
            "disk_reads": 7200,
            "executions": 267,
            "execution_plan": "NESTED LOOPS | SUBQUERY | Cost: 4000",
            "cost": 4000,
            "issue": "IN avec sous-requête - Exécution répétée de la sous-requête",
            "recommendation": "Remplacer par JOIN : FROM sales s JOIN calendar c ON s.sales_date = c.date WHERE c.is_holiday = 1"
        },
        {
            "query_id": "Q010",
            "sql_text": "SELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id HAVING SUM(amount) > 10000 ORDER BY SUM(amount) DESC",
            "execution_time_sec": 42.6,
            "rows_processed": 1800000,
            "buffer_gets": 280000,
            "disk_reads": 11000,
            "executions": 98,
            "execution_plan": "SORT GROUP BY | SORT ORDER BY | Cost: 4500",
            "cost": 4500,
            "issue": "Double tri (GROUP BY + ORDER BY) - Consommation mémoire élevée",
            "recommendation": "Augmenter SORT_AREA_SIZE OU créer index sur (customer_id, amount)"
        }
    ]
    
    df = pd.DataFrame(queries)
    df.to_csv("data/slow_queries.csv", index=False)
    
    print(f"   ✅ {len(queries)} requêtes lentes générées avec plans d'exécution")
    return df


def generate_security_config():
    """
    Génère configuration de sécurité
    Simule : SELECT * FROM dba_users JOIN dba_role_privs JOIN dba_sys_privs
    """
    
    print("🔄 Génération config sécurité (simulation DBA_USERS/ROLES/PRIVS)...")
    
    security_data = [
        {
            "username": "SYSTEM",
            "account_status": "OPEN",
            "profile": "DEFAULT",
            "created_date": "2020-01-15",
            "lock_date": None,
            "expiry_date": "2026-01-15",
            "roles": "DBA,CONNECT,RESOURCE",
            "system_privileges": "CREATE SESSION,CREATE TABLE,DROP ANY TABLE,ALTER SYSTEM",
            "password_life_days": 90,
            "failed_login_attempts": 0,
            "last_login": "2026-01-06 14:23:15",
            "risk_level": "CRITICAL",
            "risk_reasons": "Compte système avec DBA role - Privilèges excessifs"
        },
        {
            "username": "SYS",
            "account_status": "OPEN",
            "profile": "DEFAULT",
            "created_date": "2020-01-15",
            "lock_date": None,
            "expiry_date": "2026-06-15",
            "roles": "DBA,SYSDBA,SYSOPER",
            "system_privileges": "ALL PRIVILEGES",
            "password_life_days": 180,
            "failed_login_attempts": 0,
            "last_login": "2026-01-05 09:12:34",
            "risk_level": "CRITICAL",
            "risk_reasons": "Compte ultra-privilégié - Ne devrait pas être utilisé directement"
        },
        {
            "username": "ADMIN_USER",
            "account_status": "OPEN",
            "profile": "ADMIN_PROFILE",
            "created_date": "2023-03-10",
            "lock_date": None,
            "expiry_date": "2026-03-10",
            "roles": "DBA,CONNECT",
            "system_privileges": "CREATE SESSION,CREATE USER,DROP USER,GRANT ANY PRIVILEGE",
            "password_life_days": 60,
            "failed_login_attempts": 2,
            "last_login": "2026-01-07 08:45:22",
            "risk_level": "HIGH",
            "risk_reasons": "Peut créer/supprimer users - 2 tentatives login échouées récentes"
        },
        {
            "username": "APP_USER",
            "account_status": "OPEN",
            "profile": "APP_PROFILE",
            "created_date": "2023-06-20",
            "lock_date": None,
            "expiry_date": "2026-06-20",
            "roles": "CONNECT,RESOURCE",
            "system_privileges": "CREATE SESSION,CREATE TABLE,CREATE VIEW",
            "password_life_days": 90,
            "failed_login_attempts": 0,
            "last_login": "2026-01-07 10:15:43",
            "risk_level": "MEDIUM",
            "risk_reasons": "Compte applicatif standard - Privilèges appropriés"
        },
        {
            "username": "READ_ONLY",
            "account_status": "OPEN",
            "profile": "LIMITED_PROFILE",
            "created_date": "2024-01-05",
            "lock_date": None,
            "expiry_date": "2026-01-05",
            "roles": "CONNECT",
            "system_privileges": "CREATE SESSION",
            "password_life_days": 120,
            "failed_login_attempts": 0,
            "last_login": "2026-01-06 16:30:12",
            "risk_level": "LOW",
            "risk_reasons": "Compte lecture seule - Sécurisé"
        },
        {
            "username": "EXTERNAL_USER",
            "account_status": "OPEN",
            "profile": "DEFAULT",
            "created_date": "2025-11-20",
            "lock_date": None,
            "expiry_date": "2026-02-20",
            "roles": "CONNECT,RESOURCE,DBA",
            "system_privileges": "CREATE SESSION,DROP ANY TABLE,CREATE USER,ALTER SYSTEM",
            "password_life_days": 30,
            "failed_login_attempts": 5,
            "last_login": "2025-12-28 23:45:10",
            "risk_level": "CRITICAL",
            "risk_reasons": "Compte externe avec DBA - 5 tentatives échouées - Expiration courte - Login suspect (hors heures)"
        },
        {
            "username": "TEST_USER",
            "account_status": "EXPIRED",
            "profile": "DEFAULT",
            "created_date": "2024-06-10",
            "lock_date": "2025-12-10",
            "expiry_date": "2025-12-10",
            "roles": "CONNECT",
            "system_privileges": "CREATE SESSION",
            "password_life_days": 0,
            "failed_login_attempts": 10,
            "last_login": "2025-11-30 14:20:05",
            "risk_level": "HIGH",
            "risk_reasons": "Compte expiré non désactivé - 10 tentatives échouées - Doit être supprimé"
        },
        {
            "username": "ANALYST",
            "account_status": "OPEN",
            "profile": "ANALYST_PROFILE",
            "created_date": "2024-09-15",
            "lock_date": None,
            "expiry_date": "2026-09-15",
            "roles": "CONNECT,SELECT_CATALOG_ROLE",
            "system_privileges": "CREATE SESSION,SELECT ANY TABLE",
            "password_life_days": 90,
            "failed_login_attempts": 1,
            "last_login": "2026-01-07 09:30:45",
            "risk_level": "MEDIUM",
            "risk_reasons": "SELECT ANY TABLE privilège large - 1 tentative échouée"
        }
    ]
    
    df = pd.DataFrame(security_data)
    df.to_csv("data/security_config.csv", index=False)
    
    print(f"   ✅ {len(security_data)} configurations sécurité générées")
    return df


def generate_db_metrics():
    """
    Génère métriques de la base de données
    Simule : SELECT * FROM v$sysmetric, v$system_event, dba_data_files
    """
    
    print("🔄 Génération métriques DB (simulation V$SYSMETRIC, V$SYSTEM_EVENT)...")
    
    metrics = {
        "database_name": "ORCL_PROD",
        "instance_name": "ORCL",
        "host_name": "db-server-01",
        "db_version": "Oracle Database 19c Enterprise Edition Release 19.0.0.0.0",
        "startup_time": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d %H:%M:%S"),
        "db_size_gb": 2500,
        "tablespaces_count": 12,
        "datafiles_count": 48,
        "users_count": 45,
        "tables_count": 850,
        "indexes_count": 1200,
        "views_count": 320,
        "daily_transactions": 5000000,
        "peak_connections": 250,
        "current_connections": 187,
        "avg_response_time_ms": 120,
        "cpu_usage_percent": 65,
        "memory_total_gb": 256,
        "memory_usage_gb": 128,
        "sga_size_gb": 64,
        "pga_size_gb": 32,
        "disk_io_read_mbps": 450,
        "disk_io_write_mbps": 320,
        "network_traffic_mbps": 180,
        "buffer_cache_hit_ratio": 98.5,
        "library_cache_hit_ratio": 99.2,
        "backup_frequency": "DAILY",
        "last_full_backup": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "last_incremental_backup": datetime.now().strftime("%Y-%m-%d"),
        "backup_size_gb": 1800,
        "rto_hours": 4,
        "rpo_hours": 1,
        "archivelog_mode": "ENABLED",
        "flashback_enabled": "YES",
        "rac_enabled": "NO",
        "dataguard_enabled": "YES",
        "criticality": "HIGH",
        "environment": "PRODUCTION",
        "compliance_standards": "SOX,GDPR,PCI-DSS"
    }
    
    df = pd.DataFrame([metrics])
    df.to_csv("data/db_metrics.csv", index=False)
    
    print("   ✅ Métriques DB générées (simulation instance production)")
    return df


def generate_prompts_yaml():
    """
    Génère le fichier prompts.yaml avec tous les prompts du projet
    """
    
    print("🔄 Génération fichier prompts.yaml...")
    
    prompts = {
        "security_audit": {
            "analyze_users": """Tu es un expert DBA Oracle en sécurité.

Analyse cette configuration utilisateur Oracle et identifie les risques de sécurité :

{user_config}

Réponds en JSON avec :
- score_securite (0-100)
- risques (liste avec sévérité: CRITIQUE/HAUTE/MOYENNE/BASSE)
- recommandations (liste numérotée)

Exemples de risques :
- Compte SYSTEM/SYS utilisé directement
- Privilèges DBA accordés à comptes applicatifs
- Mots de passe expirés ou tentatives login multiples
- SELECT ANY TABLE, DROP ANY TABLE sur comptes non-admin
""",
            
            "analyze_privileges": """Analyse ces privilèges système Oracle :

{privileges}

Ces privilèges sont-ils excessifs pour un compte {role} ?

Réponds avec :
1. Privilèges appropriés (à garder)
2. Privilèges excessifs (à révoquer)
3. Justification pour chaque
"""
        },
        
        "query_optimization": {
            "explain_plan": """Tu es un expert Oracle Performance Tuning.

Explique ce plan d'exécution Oracle en termes simples :

SQL: {sql_text}
Plan: {execution_plan}
Temps: {execution_time}s
Lignes: {rows_processed}

Réponds en 3 parties :
1. Ce que fait la requête (langage simple)
2. Pourquoi c'est lent (goulots d'étranglement)
3. Solutions concrètes avec commandes SQL
""",
            
            "optimize_query": """Optimise cette requête Oracle lente :

{sql_text}

Plan actuel : {execution_plan}
Coût : {cost}
Problème identifié : {issue}

Propose :
1. Version réécrite de la requête
2. Index à créer (avec commande CREATE INDEX exacte)
3. Hints Oracle si nécessaires
4. Estimation gain performance (%)
"""
        },
        
        "anomaly_detection": {
            "analyze_log": """Tu es un expert cybersécurité Oracle.

Analyse ce log d'audit Oracle :

Timestamp: {timestamp}
User: {username}
Action: {action}
Object: {object_name}
Status: {status}
IP: {ip_address}

Ce log est-il normal ou suspect ?

Réponds en JSON :
- classification (NORMAL/SUSPECT/CRITIQUE)
- justification (pourquoi)
- severite (1-10 si anomalie)
- action_recommandee (que faire)

Exemples d'anomalies :
- Connexions hors heures bureau (22h-6h)
- DROP/ALTER/GRANT sur objets système
- Tentatives login échouées répétées
- Accès depuis IP externes
- Escalade privilèges
""",
            
            "detect_sql_injection": """Analyse cette séquence de logs pour détecter SQL injection :

{log_sequence}

Y a-t-il tentative d'injection SQL ?

Indique :
1. Type d'attaque (Union-based, Boolean-based, Time-based, etc.)
2. Payload détecté
3. Niveau de danger
4. Actions immédiates
"""
        },
        
        "backup_strategy": {
            "recommend_strategy": """Tu es un expert Oracle Backup & Recovery.

Recommande une stratégie de sauvegarde pour cette base :

Taille DB : {db_size_gb} GB
Transactions/jour : {daily_transactions}
RPO requis : {rpo_hours}h
RTO requis : {rto_hours}h
Criticité : {criticality}
Budget : {budget}

Réponds en JSON :
- type_backup (FULL, INCREMENTAL, DIFFERENTIAL)
- frequence (HORAIRE, QUOTIDIEN, HEBDOMADAIRE)
- retention_jours
- outil_recommande (RMAN, Data Pump, etc.)
- script_exemple (commande RMAN)
- cout_estime_mensuel
- justification
""",
            
            "recovery_steps": """Guide la récupération Oracle pour ce scénario :

Scénario : {scenario}
Backup disponible : {backup_type}
Date cible : {target_date}

Fournis un playbook détaillé :
1. Étapes numérotées (avec commandes RMAN exactes)
2. Points de validation après chaque étape
3. Temps estimé par étape
4. Plan B si échec
"""
        },
        
        "chatbot": {
            "general": """Tu es un assistant DBA Oracle intelligent et amical.

Question de l'utilisateur : {user_question}

Contexte de la base :
{db_context}

Réponds de manière :
- Claire et concise
- Avec exemples SQL si pertinent
- En proposant des actions concrètes
- En langage naturel (pas trop technique sauf si demandé)

Si la question concerne :
- Performance → Suggère d'analyser requêtes lentes
- Sécurité → Propose audit
- Backup → Recommande stratégie
- Erreurs → Demande logs précis
"""
        }
    }
    
    import yaml
    with open("data/prompts.yaml", "w", encoding="utf-8") as f:
        yaml.dump(prompts, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print("   ✅ Fichier prompts.yaml créé avec 10+ prompts")
    return prompts


def generate_all_data():
    """Génère tous les fichiers de données du projet"""
    
    print("\n" + "="*70)
    print("🚀 MODULE 1 : GÉNÉRATION DES DONNÉES SYNTHÉTIQUES ORACLE")
    print("="*70 + "\n")
    
    # Créer dossiers si nécessaires
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/oracle_docs", exist_ok=True)
    
    # Générer tous les fichiers
    df_audit = generate_audit_logs()
    df_queries = generate_slow_queries()
    df_security = generate_security_config()
    df_metrics = generate_db_metrics()
    prompts = generate_prompts_yaml()
    
    print("\n" + "="*70)
    print("✅ MODULE 1 TERMINÉ !")
    print("="*70)
    print("\n📁 Fichiers créés dans 'data/' :")
    print(f"   ✅ audit_logs.csv          - {len(df_audit)} logs (50 normaux + 20 suspects)")
    print(f"   ✅ slow_queries.csv        - {len(df_queries)} requêtes lentes avec plans")
    print(f"   ✅ security_config.csv     - {len(df_security)} configurations utilisateurs")
    print(f"   ✅ db_metrics.csv          - Métriques instance Oracle")
    print(f"   ✅ prompts.yaml            - 10+ prompts pour LLM")
    
    print("\n📊 Statistiques :")
    print(f"   • Logs normaux : {len(df_audit[df_audit['severity'] == 'NORMAL'])}")
    print(f"   • Logs suspects : {len(df_audit[df_audit['severity'] != 'NORMAL'])}")
    print(f"   • Requêtes analysées : {df_queries['executions'].sum()} exécutions totales")
    print(f"   • Risques sécurité CRITICAL : {len(df_security[df_security['risk_level'] == 'CRITICAL'])}")
    print(f"   • Taille DB simulée : {df_metrics['db_size_gb'].values[0]} GB")
    
    print("\n🎯 Prochaine étape : MODULE 2 (RAG Setup avec Pinecone)")
    print("="*70 + "\n")
    
    return {
        "audit_logs": df_audit,
        "slow_queries": df_queries,
        "security_config": df_security,
        "db_metrics": df_metrics,
        "prompts": prompts
    }


if __name__ == "__main__":
    generate_all_data()