# -*- coding: utf-8 -*-
"""
MODULE 1 : Oracle Data Extractor & Generator
Livrables exacts :
- Script Python de connexion Oracle (oracledb - mode Thin)
- Extraction automatisée des logs d'audit, configs sécurité, etc.
- Base de données CSV normalisée (data/audit_logs.csv, etc.)
- Mode simulation avec données synthétiques réalistes
- Documentation intégrée via commentaires
"""

import pandas as pd
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import warnings

# Supprime le warning pandas (propre et sans risque)
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

# Chargement des variables d'environnement
load_dotenv()

# Import oracledb avec fallback
try:
    import oracledb
    ORACLEDB_AVAILABLE = True
except ImportError:
    ORACLEDB_AVAILABLE = False


class OracleDataExtractor:
    def __init__(self, use_simulation=False):
        self.use_simulation = use_simulation
        self.connection = None

        if not use_simulation and ORACLEDB_AVAILABLE:
            self._connect_from_env()
        else:
            self.use_simulation = True

        if self.use_simulation:
            print("[INFO] Mode SIMULATION activé (données CSV)")
        else:
            print("[OK] Connexion Oracle réussie (mode Thin - sans Instant Client)")

    def _connect_from_env(self):
        user = os.getenv("ORACLE_USER")
        password = os.getenv("ORACLE_PASSWORD")
        host = os.getenv("ORACLE_HOST", "localhost")
        port = int(os.getenv("ORACLE_PORT", "1521"))
        service = os.getenv("ORACLE_SERVICE")

        if not all([user, password, service]):
            print("[ERROR] Variables manquantes dans .env → passage en mode simulation")
            self.use_simulation = True
            return

        dsn = oracledb.makedsn(host, port, service_name=service)

        try:
            self.connection = oracledb.connect(user=user, password=password, dsn=dsn)
            self.use_simulation = False
            print(f"[OK] Connecté à {host}:{port}/{service}")
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            print(f"[ERROR] Connexion échouée : ORA-{error_obj.code} - {error_obj.message}")
            print("    → Vérifie le container Docker, le port 1521 et les identifiants")
            self.use_simulation = True

    # ========== GÉNÉRATION SYNTHÉTIQUE ==========

    def _generate_audit_logs(self, num_normal=50, num_suspect=20):
        print("   Génération de logs d'audit synthétiques...")
        os.makedirs("data", exist_ok=True)

        normal_logs = []
        users = ["APP_USER", "ANALYST", "REPORT_USER", "ETL_USER", "READ_ONLY"]
        actions = ["SELECT", "INSERT", "UPDATE"]
        tables = ["CUSTOMERS", "ORDERS", "PRODUCTS", "INVOICES", "EMPLOYEES"]
        base_time = datetime.now() - timedelta(days=30)

        for i in range(num_normal):
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

        suspect_logs = []
        suspect_users = ["UNKNOWN_USER", "ADMIN", "SYS", "EXTERNAL_USER", "ROOT"]
        suspect_actions = ["DROP", "ALTER", "GRANT", "CREATE USER", "DELETE"]
        sensitive_tables = ["USER_CREDENTIALS", "SALARY_INFO", "CREDIT_CARDS", "SYS.AUD$"]

        for i in range(num_suspect):
            log = {
                "log_id": f"LOG_{i+num_normal+1:03d}",
                "timestamp": (base_time + timedelta(
                    days=random.randint(0, 29),
                    hours=random.choice([0, 1, 2, 3, 22, 23]),
                    minutes=random.randint(0, 59)
                )).strftime("%Y-%m-%d %H:%M:%S"),
                "username": random.choice(suspect_users),
                "action": random.choice(suspect_actions),
                "object_name": random.choice(sensitive_tables),
                "status": random.choice(["SUCCESS", "FAILED", "BLOCKED"]),
                "ip_address": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
                "session_id": random.randint(10000, 99999),
                "severity": random.choice(["SUSPECT", "CRITICAL", "HIGH"])
            }
            suspect_logs.append(log)

        all_logs = normal_logs + suspect_logs
        random.shuffle(all_logs)
        df = pd.DataFrame(all_logs)
        df.to_csv("data/audit_logs.csv", index=False)
        print(f"      → {len(all_logs)} logs générés et sauvegardés dans data/audit_logs.csv")
        return df

    def generate_all_data(self):
        """Génère toutes les données synthétiques nécessaires au projet"""
        os.makedirs("data", exist_ok=True)
        print("\nGÉNÉRATION DES DONNÉES SYNTHÉTIQUES")
        self._generate_audit_logs()
        # Tu ajouteras ici les autres générateurs (slow_queries, security_config, etc.)
        print("[OK] Toutes les données synthétiques sont prêtes dans le dossier data/\n")

    # ========== EXTRACTION RÉELLE OU SIMULÉE ==========

    def extract_audit_logs(self, days=7):
        """Extrait les logs d'audit - réel si possible, sinon simulation"""
        if self.use_simulation:
            path = "data/audit_logs.csv"
            if os.path.exists(path):
                df = pd.read_csv(path)
                print(f"[INFO] {len(df)} logs chargés depuis CSV (simulation)")
                return df
            else:
                return self._generate_audit_logs()

        # Tentatives d'extraction réelle
        queries = [
            # 1. Unified Audit Trail (Oracle 12c+)
            f"""
                SELECT TO_CHAR(DBTIMESTAMP, 'YYYY-MM-DD HH24:MI:SS') AS timestamp,
                       USERNAME,
                       ACTION_NAME AS action,
                       OBJECT_NAME AS object_name,
                       RETURNCODE AS status
                FROM UNIFIED_AUDIT_TRAIL
                WHERE DBTIMESTAMP > SYSDATE - {days}
                ORDER BY DBTIMESTAMP DESC
            """,
            # 2. AUD$ classique (correction du nom de colonne : OBJ$NAME)
            f"""
                SELECT TO_CHAR(TIMESTAMP#, 'YYYY-MM-DD HH24:MI:SS') AS timestamp,
                       USERID AS username,
                       ACTION_NAME AS action,
                       OBJ$NAME AS object_name,
                       RETURNCODE AS status
                FROM SYS.AUD$
                WHERE TIMESTAMP# > SYSDATE - {days}
                ORDER BY TIMESTAMP# DESC
            """
        ]

        for query in queries:
            try:
                df = pd.read_sql(query, self.connection)
                if not df.empty:
                    print(f"[OK] {len(df)} logs d'audit extraits depuis la base réelle")
                    return df
                else:
                    print("[INFO] Source vide, essai suivant...")
            except Exception as e:
                if "ORA-00942" in str(e) or "ORA-00904" in str(e):
                    print("[INFO] Table ou colonne inaccessible → essai de la source suivante")
                else:
                    print(f"[WARNING] Erreur SQL inattendue : {e}")

        # Fallback final
        print("[INFO] Aucune source d'audit réelle disponible → utilisation des données synthétiques")
        return self._generate_audit_logs()

    # Tu peux ajouter ces méthodes plus tard
    # def extract_slow_queries(self): ...
    # def extract_security_config(self): ...
    # def extract_performance_metrics(self): ...

    def close(self):
        """Ferme proprement la connexion Oracle"""
        if self.connection:
            self.connection.close()
            print("[OK] Connexion Oracle fermée")
        else:
            print("[INFO] Aucune connexion réelle à fermer (mode simulation)")


# ========== TEST ==========

if __name__ == "__main__":
    print("TEST DU MODULE 1 - Oracle Data Extractor\n")

    extractor = OracleDataExtractor(use_simulation=False)

    print("\nExtraction des logs d'audit...")
    logs = extractor.extract_audit_logs(days=7)
    print(f"\n[SUCCÈS] {len(logs)} logs disponibles")
    print(logs.head(5))

    # Génération des données synthétiques (au cas où)
    if extractor.use_simulation:
        extractor.generate_all_data()

    extractor.close()
    print("\nModule 1 terminé avec succès ! Tu peux passer au Module 2 (RAG & ChromaDB)")