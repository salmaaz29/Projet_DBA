# pages/chatbot.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path

# Base de données Oracle non disponible dans cette version
ORACLE_AVAILABLE = False

def show():
    st.title("💬 Chatbot Oracle Expert")
    # Debug mode toggle
    st.sidebar.subheader("⚙️ Settings")
    debug_mode = st.sidebar.checkbox("Debug Mode (show intent classification)", value=False)
    st.session_state["debug_mode"] = debug_mode
    
    # Initialiser l'historique
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Bonjour! Je suis votre assistant Oracle IA connecté aux modules du projet. Comment puis-je vous aider?"}
        ]
    
    # Afficher l'historique
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Questions rapides MISES À JOUR
    st.sidebar.subheader("💡 Questions rapides")
    
    quick_questions = [
        "Pourquoi ma requête SELECT COUNT(*) FROM test_orders est lente?",
        "Y a-t-il des risques de sécurité détectés?",
        "Quelle stratégie de backup recommandez-vous?",
        "Comment récupérer une table supprimée?",
        "Y a-t-il des anomalies dans les logs?",
        "Quel est le score de sécurité actuel?",
        "Montre-moi les requêtes les plus lentes",
        "Guide pour récupérer ma base au 15 mars 14h"
    ]
    
    for q in quick_questions:
        if st.sidebar.button(q, key=f"quick_{q[:20]}"):
            st.session_state.messages.append({"role": "user", "content": q})
            st.rerun()
    
    # Input utilisateur
    if prompt := st.chat_input("Posez votre question sur Oracle..."):
        # Ajouter le message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Générer une réponse RÉELLE avec les modules
        with st.chat_message("assistant"):
            with st.spinner("🔄 Analyse en cours..."):
                response = generate_intelligent_response(prompt)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})


def generate_intelligent_response(prompt):
    """Generate response with classification reasoning"""
    
    try:
        from src.llm_engine import LLMEngine
        llm = LLMEngine()
        
        intent = llm.classify_intent_with_confidence(prompt)

        print(f"[Intent] {intent}")

        # Optional: Show classification to user in debug mode
        if st.session_state.get("debug_mode", False):
            st.info(f"🎯 **Classification:** {intent}")
        
        # Route to handler
        routing_map = {
            "DATABASE_QUERY": handle_database_query,
            "QUERY_OPTIMIZATION": handle_query_optimization,
            "SECURITY_AUDIT": handle_security_audit,
            "ANOMALY_DETECTION": handle_anomaly_detection,
            "BACKUP_STRATEGY": handle_backup_strategy,
            "RECOVERY_GUIDE": handle_recovery_guide,
            "GENERAL_HELP": lambda p: get_contextual_help(p.lower())
        }
        
        handler = routing_map.get(intent, lambda p: get_contextual_help(p.lower()))
        return handler(prompt)
        
    except Exception as e:
        return f"❌ Error: {str(e)}\n\n{get_contextual_help(prompt.lower())}"

# ============================================================
# FONCTIONS D'INTÉGRATION AVEC LES MODULES RÉELS - FIXED
# ============================================================

def handle_query_optimization(prompt):
    """Intégration avec MODULE 5 - RÉEL avec LLM dynamique - FIXED"""

    try:
        from src.llm_engine import LLMEngine
        llm = LLMEngine()

        # Extraire la requête SQL du prompt si présente
        sql_query = extract_sql_from_prompt(prompt)

        if sql_query:
            # ✅ ALREADY CORRECT: Uses specific SQL query AND user question
            analysis_prompt = f"""
Analysez cette requête SQL Oracle et proposez des optimisations:

Question de l'utilisateur: "{prompt}"
Requête SQL: {sql_query}

Veuillez fournir:
1. Une explication du plan d'exécution potentiel
2. Les points coûteux identifiés
3. Des recommandations d'optimisation concrètes avec commandes SQL
4. L'impact estimé des optimisations

Répondez en français de manière claire et structurée.
"""
            llm_response = llm.generate(analysis_prompt)
            
            response = f"""
🚀 **Optimisation de Requête (Module 5 - Analyse LLM)**

{llm_response}

💡 *Analyse générée par l'IA en temps réel*
"""
            return response

        else:
            # ✅ FIXED: Now includes user question in all cases
            json_path = Path("data/queries_for_optimization.json")

            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        queries = json.load(f)
                except (json.JSONDecodeError, IOError):
                    queries = []

                if queries and len(queries) > 0:
                    query = queries[0]
                    sql_text = query.get('sql_text', 'SELECT COUNT(*) FROM test_orders')

                    # ✅ NOW INCLUDES USER QUESTION
                    analysis_prompt = f"""
Question de l'utilisateur: "{prompt}"

Analysez cette requête SQL lente et proposez des optimisations:

Requête: {sql_text}
Temps d'exécution: {query.get('basic_metrics', {}).get('elapsed_sec', 0.5)}s
Coût optimiseur: {query.get('basic_metrics', {}).get('optimizer_cost', 1500)}

Répondez spécifiquement à la question de l'utilisateur en fournissant:
1. Une analyse complète de la requête
2. Les goulots d'étranglement identifiés
3. Des recommandations d'optimisation concrètes
4. Des exemples de requêtes optimisées
5. L'impact estimé sur les performances

Répondez en français de manière claire et structurée.
"""
                    llm_response = llm.generate(analysis_prompt)
                    
                    response = f"""
🚀 **Optimisation de Requête (Module 5 - Analyse LLM)**

**Requête analysée:** `{sql_text[:100]}{'...' if len(sql_text) > 100 else ''}`

{llm_response}

💡 *Analyse générée par l'IA en temps réel*
"""
                    return response

            # ✅ FIXED: Includes user question in general prompt
            general_prompt = f"""
Question de l'utilisateur: "{prompt}"

Vous êtes un expert en optimisation de requêtes Oracle.
Répondez spécifiquement à la question ci-dessus en fournissant:
- Une réponse directe à leur question
- Des recommandations générales pour améliorer les performances des requêtes SQL Oracle
- Des exemples concrets adaptés à la question
- Des bonnes pratiques pertinentes (index, statistiques, hints, etc.)

Répondez en français de manière claire et structurée.
"""
            llm_response = llm.generate(general_prompt)
            
            response = f"""
🚀 **Optimisation de Requête (Module 5 - Analyse LLM)**

{llm_response}

💡 *Analyse générée par l'IA en temps réel*
"""
            return response

    except Exception as e:
        return f"❌ Erreur LLM: {str(e)}"


def extract_sql_from_prompt(prompt):
    """Extraire une requête SQL du prompt utilisateur"""
    import re

    # Patterns pour détecter du SQL
    sql_patterns = [
        r'SELECT\s+.*?\s+FROM\s+.*?;',
        r'SELECT\s+.*?\s+FROM\s+.*?(\s+WHERE\s+.*?)?(\s+ORDER\s+BY\s+.*?)?(\s+LIMIT\s+\d+)?;',
        r'INSERT\s+INTO\s+.*?\s+VALUES\s*\(.*?\);',
        r'UPDATE\s+.*?\s+SET\s+.*?(\s+WHERE\s+.*?)?;',
        r'DELETE\s+FROM\s+.*?(\s+WHERE\s+.*?)?;'
    ]

    prompt_lower = prompt.lower()

    for pattern in sql_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(0).strip()

    # Chercher des mots-clés SQL dans le prompt
    sql_keywords = ['select', 'from', 'where', 'join', 'group by', 'order by', 'having', 'insert', 'update', 'delete']

    if any(keyword in prompt_lower for keyword in sql_keywords):
        # Essayer d'extraire une requête simple
        # Chercher entre guillemets ou après "requête" ou "query"
        query_match = re.search(r'(?:requête|query|sql)\s*[:"]\s*(.+?)(?:[";]|$)', prompt, re.IGNORECASE)
        if query_match:
            return query_match.group(1).strip()

    return None


def handle_security_audit(prompt):
    """Intégration avec MODULE 4 - RÉEL avec LLM dynamique - ALREADY CORRECT"""

    try:
        from src.llm_engine import LLMEngine
        llm = LLMEngine()

        # Charger les données de sécurité existantes si disponibles
        reports_dir = Path("reports")
        security_context = ""

        if reports_dir.exists():
            security_reports = sorted(reports_dir.glob("security_audit_*.json"), reverse=True)
            if security_reports:
                try:
                    with open(security_reports[0], 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    security_context = f"""
Données de sécurité existantes:
- Score: {report.get('score_securite', 0)}/100
- Risques identifiés: {len(report.get('risques_identifies', []))}
- Recommandations: {len(report.get('recommandations', []))}
"""
                except:
                    pass

        # ✅ ALREADY CORRECT: Includes user's specific question
        security_prompt = f"""
Question de l'utilisateur: "{prompt}"

Vous êtes un expert en sécurité Oracle. Répondez spécifiquement à la question ci-dessus concernant la sécurité d'une base de données Oracle.

{security_context}

Basé sur la question de l'utilisateur, fournissez:
1. Une réponse directe à leur question spécifique
2. Une évaluation de sécurité pertinente
3. Les risques de sécurité identifiés en lien avec leur question
4. Des recommandations concrètes pour améliorer la sécurité
5. Des mesures de protection prioritaires

Répondez en français de manière structurée et professionnelle.
"""

        llm_response = llm.generate(security_prompt)

        response = f"""
🔒 **Audit de Sécurité (Module 4 - Analyse LLM)**

{llm_response}

💡 *Analyse de sécurité générée par l'IA en temps réel*
"""
        return response

    except Exception as e:
        return f"❌ Erreur LLM: {str(e)}"


def handle_anomaly_detection(prompt):
    """Intégration avec MODULE 6 - RÉEL avec LLM dynamique - ALREADY CORRECT"""

    try:
        from src.llm_engine import LLMEngine
        llm = LLMEngine()

        # Charger les données d'anomalies existantes
        anomaly_results = Path("data/anomaly_analysis_results.json")
        anomaly_context = ""

        if anomaly_results.exists():
            try:
                with open(anomaly_results, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                stats = results.get('statistics', {})
                total = stats.get('total_logs', 0)
                normal = stats.get('normal', 0)
                suspect = stats.get('suspect', 0)
                critique = stats.get('critique', 0)
                anomaly_context = f"""
Données d'anomalies existantes:
- Logs analysés: {total}
- Normaux: {normal}
- Suspects: {suspect}
- Critiques: {critique}
- Anomalies détectées: {len(results.get('anomaly_reports', []))}
"""
            except:
                pass

        # ✅ ALREADY CORRECT: Includes user's specific question
        anomaly_prompt = f"""
Question de l'utilisateur: "{prompt}"

Vous êtes un expert en cybersécurité Oracle. Répondez spécifiquement à la question ci-dessus concernant les logs d'audit et la détection d'anomalies.

{anomaly_context}

Basé sur la question de l'utilisateur, fournissez:
1. Une réponse directe à leur question spécifique
2. Une évaluation globale des anomalies détectées
3. Les types d'attaques ou comportements suspects identifiés
4. Des recommandations de sécurité immédiates
5. Des mesures de prévention à mettre en place

Répondez en français de manière structurée et professionnelle.
"""

        llm_response = llm.generate(anomaly_prompt)

        response = f"""
🚨 **Détection d'Anomalies (Module 6 - Analyse LLM)**

{llm_response}

💡 *Analyse d'anomalies générée par l'IA en temps réel*
"""
        return response

    except Exception as e:
        return f"❌ Erreur LLM: {str(e)}"

def handle_backup_strategy(prompt):
    """Intégration avec MODULE 7 - RÉEL avec LLM dynamique - ALREADY CORRECT"""

    try:
        from src.llm_engine import LLMEngine
        llm = LLMEngine()

        # Charger les données de sauvegarde existantes
        reports_dir = Path("reports")
        backup_context = ""

        if reports_dir.exists():
            backup_reports = sorted(reports_dir.glob("backup_strategy_*.json"), reverse=True)
            if backup_reports:
                try:
                    with open(backup_reports[0], 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    backup_context = f"""
Stratégie de sauvegarde existante:
- Type d'environnement: {report.get('environment_type', 'N/A')}
- Taille base: {report.get('database_size_gb', 0)}GB
- RPO recommandé: {report.get('recommended_rpo', 'N/A')}
- RTO recommandé: {report.get('recommended_rto', 'N/A')}
- Coûts estimés: {report.get('estimated_costs', {}).get('monthly_cost', 'N/A')}€
"""
                except:
                    pass

        # ✅ ALREADY CORRECT: Includes user's specific question
        backup_prompt = f"""
Question de l'utilisateur: "{prompt}"

Vous êtes un expert en sauvegarde Oracle. Répondez spécifiquement à la question ci-dessus concernant les stratégies de sauvegarde.

{backup_context}

Basé sur la question de l'utilisateur, fournissez:
1. Une réponse directe adaptée à leur demande spécifique
2. Une analyse des besoins de sauvegarde (RPO/RTO) si pertinent
3. Une stratégie recommandée adaptée au contexte de la question
4. Des procédures de sauvegarde avec commandes RMAN concrètes
5. Un plan de test et validation des sauvegardes
6. Des coûts estimés et optimisation budgétaire si demandé

Répondez en français de manière structurée et professionnelle.
"""

        llm_response = llm.generate(backup_prompt)

        response = f"""
💾 **Stratégie de Sauvegarde (Module 7 - Analyse LLM)**

{llm_response}

💡 *Stratégie de sauvegarde générée par l'IA en temps réel*
"""
        return response

    except Exception as e:
        return f"❌ Erreur LLM: {str(e)}"

def handle_recovery_guide(prompt):
    """Intégration avec MODULE 8 - RÉEL avec LLM dynamique - ALREADY CORRECT"""

    try:
        from src.llm_engine import LLMEngine
        llm = LLMEngine()

        # Charger les données de récupération existantes
        reports_dir = Path("reports")
        recovery_context = ""

        if reports_dir.exists():
            recovery_guides = sorted(reports_dir.glob("recovery_guide_*.json"), reverse=True)
            if recovery_guides:
                try:
                    with open(recovery_guides[0], 'r', encoding='utf-8') as f:
                        guide = json.load(f)
                    recovery_context = f"""
Scénario de récupération existant:
- Type: {guide.get('scenario_name', 'N/A')}
- Étapes: {len(guide.get('guide', {}).get('playbook', {}).get('steps', []))}
- Commandes: {len(guide.get('guide', {}).get('playbook', {}).get('commands', []))}
- Temps estimé: {guide.get('guide', {}).get('playbook', {}).get('estimated_time', 'N/A')}
"""
                except:
                    pass

        # ✅ ALREADY CORRECT: Includes user's specific question
        recovery_prompt = f"""
Question de l'utilisateur: "{prompt}"

Vous êtes un expert en récupération de données Oracle. Répondez spécifiquement à la question ci-dessus concernant la récupération de données.

{recovery_context}

Basé sur la question de l'utilisateur, fournissez:
1. Une réponse directe au scénario spécifique demandé
2. Une analyse du type d'incident et stratégie appropriée
3. Une procédure de récupération étape par étape adaptée à la question
4. Des commandes RMAN et SQL nécessaires concrètes
5. Le temps estimé et les prérequis
6. Des mesures de prévention pour éviter la récurrence

Répondez en français de manière structurée et professionnelle.
"""

        llm_response = llm.generate(recovery_prompt)

        response = f"""
🔄 **Guide de Récupération (Module 8 - Analyse LLM)**

{llm_response}

💡 *Guide de récupération généré par l'IA en temps réel*
"""
        return response

    except Exception as e:
        return f"❌ Erreur LLM: {str(e)}"


def is_database_specific_question(prompt_lower):
    """Détecte si la question porte sur des données spécifiques de la base"""

    # Mots-clés indiquant une question sur les données réelles
    data_keywords = [
        "combien", "nombre", "total", "liste", "montre-moi", "affiche",
        "quels sont", "quelle est", "qui sont", "donne-moi", "cherche",
        "trouve", "vérifie", "contrôle", "statut", "état actuel",
        "actuellement", "maintenant", "en ce moment", "réel", "vrai",
        "actif", "connecté", "session", "utilisateur connecté",
        "tablespace", "espace disque", "mémoire", "cpu", "performance actuelle"
    ]

    # Questions sur l'état actuel de la base
    status_keywords = [
        "statut", "état", "status", "actif", "running", "démarré",
        "arrêté", "stopped", "connecté", "disponible", "accessible"
    ]

    # Si contient des mots-clés de données ET pas de mots-clés d'analyse générale
    has_data_keywords = any(keyword in prompt_lower for keyword in data_keywords)
    has_status_keywords = any(keyword in prompt_lower for keyword in status_keywords)

    # Éviter les conflits avec les analyses générales
    analysis_keywords = ["pourquoi lent", "optimise", "audit", "sécurité", "backup", "récupération"]
    is_analysis_question = any(keyword in prompt_lower for keyword in analysis_keywords)

    return (has_data_keywords or has_status_keywords) and not is_analysis_question


def handle_database_query(prompt):
    """Gère les questions nécessitant une connexion à la base de données"""

    if not ORACLE_AVAILABLE:
        return """
❌ **Connexion Oracle non disponible**

Pour interroger votre base de données en temps réel, vous devez:

1. **Installer le driver Oracle:**
```bash
pip install oracledb
```

2. **Configurer la connexion** dans vos variables d'environnement:
- `ORACLE_HOST`
- `ORACLE_PORT`
- `ORACLE_SID` ou `ORACLE_SERVICE_NAME`
- `ORACLE_USER`
- `ORACLE_PASSWORD`

3. **Redémarrer l'application**

Une fois configuré, je pourrai interroger votre base Oracle directement!
"""

    try:
        # Tenter de se connecter à la base
        connection = get_oracle_connection()

        if not connection:
            return """
❌ **Impossible de se connecter à Oracle**

Vérifiez votre configuration:
- Variables d'environnement définies
- Base de données accessible
- Credentials corrects

Consultez les logs pour plus de détails.
"""

        # Analyser le type de question
        prompt_lower = prompt.lower()

        # Questions sur les sessions
        if any(word in prompt_lower for word in ["session", "connecté", "utilisateur actif", "qui est connecté"]):
            return handle_sessions_query(connection, prompt)

        # Questions sur les tables/tablespaces
        elif any(word in prompt_lower for word in ["table", "tablespace", "espace", "disque", "stockage"]):
            return handle_storage_query(connection, prompt)

        # Questions sur les performances actuelles
        elif any(word in prompt_lower for word in ["performance", "cpu", "mémoire", "actuellement", "maintenant"]):
            return handle_performance_query(connection, prompt)

        # Questions sur les utilisateurs
        elif any(word in prompt_lower for word in ["utilisateur", "user", "compte", "dba"]):
            return handle_users_query(connection, prompt)

        # Questions génériques sur l'état
        elif any(word in prompt_lower for word in ["statut", "état", "status", "base", "database"]):
            return handle_status_query(connection, prompt)

        # Par défaut, essayer d'extraire et exécuter une requête SQL
        else:
            sql_query = extract_sql_from_prompt(prompt)
            if sql_query:
                return execute_custom_query(connection, sql_query)
            else:
                return """
🤔 **Question non reconnue**

Pour interroger votre base, essayez:
• "Combien d'utilisateurs sont connectés?"
• "Quel est l'état des tablespaces?"
• "Montre-moi les sessions actives"
• "Quelle est la version d'Oracle?"
• Ou posez directement une requête SQL
"""

    except Exception as e:
        return f"""
❌ **Erreur lors de l'interrogation de la base**

**Erreur:** {str(e)}

Vérifiez:
- La configuration de connexion
- Les permissions de l'utilisateur
- La disponibilité de la base de données
"""


def get_oracle_connection():
    """Établit une connexion à Oracle"""
    try:
        # Charger les variables d'environnement depuis .env si disponible
        try:
            from dotenv import load_dotenv
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            ENV_PATH = BASE_DIR / ".env"
            if ENV_PATH.exists():
                load_dotenv(ENV_PATH)
                print("[OK] Variables d'environnement chargées")
        except ImportError:
            print("[WARNING] dotenv non installé")

        # Récupérer les paramètres de connexion
        host = os.getenv("ORACLE_HOST", "localhost")
        port = int(os.getenv("ORACLE_PORT", "1521"))
        service = os.getenv("ORACLE_SERVICE", "XEPDB1")
        user = os.getenv("ORACLE_USER", "system")
        password = os.getenv("ORACLE_PASSWORD", "")

        if not password:
            print("[WARNING] Mot de passe Oracle manquant")
            return None

        # Créer le DSN et se connecter
        dsn = f"{host}:{port}/{service}"
        connection = oracledb.connect(user=user, password=password, dsn=dsn)

        # Tester la connexion
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM dual")
        cursor.fetchone()
        cursor.close()

        print(f"[OK] Connexion Oracle établie: {service}")
        return connection

    except Exception as e:
        print(f"[ERROR] Connexion Oracle échouée: {e}")
        return None


def handle_sessions_query(connection, prompt):
    """Gère les questions sur les sessions"""
    try:
        cursor = connection.cursor()

        # Requête pour les sessions actives
        query = """
        SELECT s.sid, s.serial#, s.username, s.program, s.status,
               s.logon_time, s.machine, s.osuser
        FROM v$session s
        WHERE s.username IS NOT NULL
          AND s.status = 'ACTIVE'
        ORDER BY s.logon_time DESC
        """

        cursor.execute(query)
        sessions = cursor.fetchall()

        if not sessions:
            return "📊 **Sessions actives:** Aucune session utilisateur active trouvée."

        response = f"""
📊 **Sessions actives ({len(sessions)})**

| SID | Utilisateur | Programme | Statut | Machine | Connecté depuis |
|-----|-------------|-----------|--------|---------|----------------|
"""

        for session in sessions[:20]:  # Limiter à 20 résultats
            sid, serial, username, program, status, logon_time, machine, osuser = session
            program_short = (program or '')[:30] + '...' if program and len(program) > 30 else (program or '')
            machine_short = (machine or '')[:20] + '...' if machine and len(machine) > 20 else (machine or '')

            response += f"| {sid} | {username or 'N/A'} | {program_short} | {status} | {machine_short} | {logon_time.strftime('%d/%m %H:%M') if logon_time else 'N/A'} |\n"

        if len(sessions) > 20:
            response += f"\n*... et {len(sessions) - 20} autres sessions*"

        cursor.close()
        return response

    except Exception as e:
        return f"❌ Erreur lors de la récupération des sessions: {str(e)}"


def handle_storage_query(connection, prompt):
    """Gère les questions sur le stockage"""
    try:
        cursor = connection.cursor()

        # Requête pour les tablespaces
        query = """
        SELECT t.tablespace_name,
               ROUND(t.total_mb, 2) as total_mb,
               ROUND(t.used_mb, 2) as used_mb,
               ROUND(t.free_mb, 2) as free_mb,
               ROUND((t.used_mb / t.total_mb) * 100, 1) as pct_used
        FROM (
            SELECT tablespace_name,
                   SUM(bytes)/1024/1024 as total_mb,
                   SUM(CASE WHEN maxbytes = 0 THEN bytes ELSE GREATEST(bytes, maxbytes) END)/1024/1024 as max_mb
            FROM dba_data_files
            GROUP BY tablespace_name
        ) df,
        (
            SELECT tablespace_name,
                   SUM(bytes)/1024/1024 as used_mb
            FROM dba_segments
            GROUP BY tablespace_name
        ) s,
        (
            SELECT tablespace_name,
                   SUM(bytes)/1024/1024 as free_mb
            FROM dba_free_space
            GROUP BY tablespace_name
        ) f,
        (
            SELECT tablespace_name, total_mb, used_mb,
                   total_mb - used_mb as free_mb
            FROM (
                SELECT tablespace_name,
                       SUM(bytes)/1024/1024 as total_mb
                FROM dba_data_files
                GROUP BY tablespace_name
            ) t
            LEFT JOIN (
                SELECT tablespace_name,
                       SUM(bytes)/1024/1024 as used_mb
                FROM dba_segments
                GROUP BY tablespace_name
            ) u ON t.tablespace_name = u.tablespace_name
        ) t
        WHERE df.tablespace_name = s.tablespace_name(+)
          AND df.tablespace_name = f.tablespace_name(+)
          AND df.tablespace_name = t.tablespace_name
        ORDER BY t.pct_used DESC
        """

        cursor.execute(query)
        tablespaces = cursor.fetchall()

        if not tablespaces:
            return "📊 **Tablespaces:** Aucun tablespace trouvé."

        response = f"""
📊 **État des Tablespaces**

| Tablespace | Total (MB) | Utilisé (MB) | Libre (MB) | % Utilisé |
|------------|------------|--------------|------------|-----------|
"""

        for ts in tablespaces:
            name, total, used, free, pct = ts
            status_icon = "🟢" if pct < 80 else "🟡" if pct < 95 else "🔴"
            response += f"| {status_icon} {name} | {total:,.0f} | {used:,.0f} | {free:,.0f} | {pct:.1f}% |\n"

        cursor.close()
        return response

    except Exception as e:
        return f"❌ Erreur lors de la récupération des informations de stockage: {str(e)}"


def handle_performance_query(connection, prompt):
    """Gère les questions sur les performances actuelles"""
    try:
        cursor = connection.cursor()

        # Métriques de performance actuelles
        queries = {
            "CPU": """
            SELECT 'CPU Usage' as metric,
                   ROUND(100 - (avg_idle_time / 100), 1) as value,
                   '%' as unit
            FROM (
                SELECT AVG(value) as avg_idle_time
                FROM v$sysmetric
                WHERE metric_name = 'Database CPU Time Ratio'
                  AND intsize_csec > 0
            )
            """,
            "Mémoire": """
            SELECT 'Memory Usage' as metric,
                   ROUND((1 - (free_memory / total_memory)) * 100, 1) as value,
                   '%' as unit
            FROM (
                SELECT
                    (SELECT value FROM v$sga) as total_memory,
                    (SELECT bytes FROM v$sgastat WHERE name = 'free memory') as free_memory
                FROM dual
            )
            """,
            "Sessions actives": """
            SELECT 'Active Sessions' as metric,
                   COUNT(*) as value,
                   '' as unit
            FROM v$session
            WHERE status = 'ACTIVE' AND username IS NOT NULL
            """
        }

        response = "📊 **Métriques de Performance Actuelles**\n\n"

        for metric_name, query in queries.items():
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                if result:
                    name, value, unit = result
                    response += f"• **{name}:** {value}{unit}\n"
            except:
                continue

        # Top requêtes lentes actuelles
        try:
            cursor.execute("""
            SELECT sql_text, elapsed_time/1000000 as elapsed_sec,
                   cpu_time/1000000 as cpu_sec, executions
            FROM v$sql
            WHERE elapsed_time > 1000000  -- Plus d'1 seconde
              AND executions > 0
            ORDER BY elapsed_time DESC
            FETCH FIRST 5 ROWS ONLY
            """)

            slow_queries = cursor.fetchall()
            if slow_queries:
                response += f"\n🔍 **Top 5 Requêtes Lentes Actuelles**\n\n"
                for i, (sql, elapsed, cpu, execs) in enumerate(slow_queries, 1):
                    sql_short = sql[:100] + '...' if len(sql) > 100 else sql
                    response += f"{i}. **{elapsed:.2f}s** (CPU: {cpu:.2f}s, Exec: {execs})\n   `{sql_short}`\n\n"
        except:
            pass

        cursor.close()
        return response

    except Exception as e:
        return f"❌ Erreur lors de la récupération des métriques de performance: {str(e)}"


def handle_users_query(connection, prompt):
    """Gère les questions sur les utilisateurs"""
    try:
        cursor = connection.cursor()

        # Liste des utilisateurs DBA
        query = """
        SELECT username, account_status, default_tablespace,
               temporary_tablespace, created, lock_date
        FROM dba_users
        WHERE username NOT IN ('SYS', 'SYSTEM', 'SYSMAN', 'DBSNMP')
        ORDER BY created DESC
        """

        cursor.execute(query)
        users = cursor.fetchall()

        if not users:
            return "👥 **Utilisateurs:** Aucun utilisateur trouvé."

        response = f"""
👥 **Utilisateurs de la Base ({len(users)})**

| Utilisateur | Statut | Tablespace | Créé le | Verrouillé |
|-------------|--------|------------|---------|------------|
"""

        for user in users[:20]:  # Limiter à 20 résultats
            username, status, def_ts, temp_ts, created, lock_date = user
            status_icon = "✅" if status == 'OPEN' else "🔒"
            lock_info = lock_date.strftime('%d/%m/%y') if lock_date else '-'

            response += f"| {status_icon} {username} | {status} | {def_ts or 'N/A'} | {created.strftime('%d/%m/%y')} | {lock_info} |\n"

        if len(users) > 20:
            response += f"\n*... et {len(users) - 20} autres utilisateurs*"

        cursor.close()
        return response

    except Exception as e:
        return f"❌ Erreur lors de la récupération des utilisateurs: {str(e)}"


def handle_status_query(connection, prompt):
    """Gère les questions sur l'état général de la base"""
    try:
        cursor = connection.cursor()

        # Informations générales sur la base
        query = """
        SELECT instance_name, host_name, version, status, database_status
        FROM v$instance
        """

        cursor.execute(query)
        instance_info = cursor.fetchone()

        if instance_info:
            instance_name, host_name, version, status, db_status = instance_info

            response = f"""
🏛️ **État de la Base Oracle**

**Instance:** {instance_name}
**Hôte:** {host_name}
**Version:** {version}
**Statut:** {'🟢 ' + status if status == 'OPEN' else '🔴 ' + status}
**Base:** {'🟢 ' + db_status if db_status == 'ACTIVE' else '🔴 ' + db_status}

"""

            # Uptime
            try:
                cursor.execute("SELECT ROUND((SYSDATE - startup_time)*24, 1) as uptime_hours FROM v$instance")
                uptime = cursor.fetchone()
                if uptime:
                    response += f"**Uptime:** {uptime[0]} heures\n\n"
            except:
                pass

            # Informations supplémentaires
            response += "**Informations complémentaires:**\n"

            # Nombre de sessions
            try:
                cursor.execute("SELECT COUNT(*) FROM v$session WHERE username IS NOT NULL")
                session_count = cursor.fetchone()
                if session_count:
                    response += f"• Sessions utilisateur: {session_count[0]}\n"
            except:
                pass

            # Taille de la base
            try:
                cursor.execute("""
                SELECT ROUND(SUM(bytes)/1024/1024/1024, 2) as db_size_gb
                FROM dba_data_files
                """)
                db_size = cursor.fetchone()
                if db_size:
                    response += f"• Taille base: {db_size[0]} GB\n"
            except:
                pass

        else:
            response = "❌ Impossible de récupérer les informations d'instance."

        cursor.close()
        return response

    except Exception as e:
        return f"❌ Erreur lors de la récupération de l'état de la base: {str(e)}"


def execute_custom_query(connection, sql_query):
    """Exécute une requête SQL personnalisée"""
    try:
        cursor = connection.cursor()

        # Validation basique de sécurité
        sql_upper = sql_query.upper().strip()
        if sql_upper.startswith(('DROP', 'TRUNCATE', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER')):
            return "⚠️ **Requête non autorisée:** Les commandes DDL/DML sont interdites pour des raisons de sécurité."

        # Exécuter la requête
        cursor.execute(sql_query)

        # Pour les SELECT, récupérer les résultats
        if sql_upper.startswith('SELECT'):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            if not rows:
                return f"📊 **Résultat de la requête:**\n\nAucun résultat trouvé.\n\n```sql\n{sql_query}\n```"

            # Limiter les résultats
            max_rows = 50
            limited_rows = rows[:max_rows]

            response = f"📊 **Résultat de la requête ({len(rows)} lignes)**\n\n"

            # En-têtes
            response += "| " + " | ".join(columns) + " |\n"
            response += "|" + "|".join(["-" * (len(col) + 2) for col in columns]) + "|\n"

            # Données
            for row in limited_rows:
                formatted_row = []
                for value in row:
                    if value is None:
                        formatted_row.append("NULL")
                    elif isinstance(value, (int, float)):
                        formatted_row.append(str(value))
                    else:
                        # Tronquer les longues chaînes
                        str_val = str(value)
                        if len(str_val) > 50:
                            str_val = str_val[:47] + "..."
                        formatted_row.append(str_val)
                response += "| " + " | ".join(formatted_row) + " |\n"

            if len(rows) > max_rows:
                response += f"\n*... et {len(rows) - max_rows} autres lignes*"

            response += f"\n\n```sql\n{sql_query}\n```"

            cursor.close()
            return response

        else:
            # Pour les autres types de requêtes
            return f"✅ **Requête exécutée avec succès**\n\n```sql\n{sql_query}\n```"

    except Exception as e:
        return f"❌ **Erreur d'exécution SQL:** {str(e)}\n\n```sql\n{sql_query}\n```"


def get_contextual_help(prompt_text):
    """Aide contextuelle basée sur la question"""

    if "quoi" in prompt_text or "que" in prompt_text or "help" in prompt_text:
        return """
🤖 **Assistant Oracle IA - Ce que je peux faire**

Je suis spécialisé dans **l'administration Oracle automatisée**.

**🎯 DEMANDEZ-MOI DE:**
1. **Interroger votre base** en temps réel (sessions, stockage, performances)
2. **Analyser et optimiser** vos requêtes SQL lentes
3. **Auditer la sécurité** de votre base (utilisateurs, privilèges)
4. **Détecter des anomalies** et tentatives d'intrusion
5. **Recommander des stratégies** de sauvegarde
6. **Guider la récupération** après incidents

**💡 EXEMPLES CONCRETS:**
• "Combien d'utilisateurs sont connectés?"
• "Quel est l'état des tablespaces?"
• "Pourquoi `SELECT COUNT(*) FROM commandes` est lent?"
• "Y a-t-il des comptes DBA non autorisés?"
• "Quelle fréquence de backup pour 100GB de données?"
• "Comment restaurer la base au 15 mars 14h?"

**📝 PHRASES CLAIREMENT COMPRISES:**
• "sessions actives"
• "état stockage"
• "optimiser requête"
• "risques sécurité"
• "stratégie backup"
• "guide récupération"
• "détecter anomalies"
"""

    # Réponse par défaut plus utile
    return """
🔍 **Je n'ai pas bien compris votre question**

Essayez de formuler comme:

**Pour interroger la base:**
• "Combien de sessions sont actives?"
• "Montre-moi l'état des tablespaces"
• "Quelle est la version d'Oracle?"

**Pour l'optimisation:**
• "Optimise cette requête: SELECT * FROM produits"
• "Pourquoi ma requête COUNT est lente?"

**Pour la sécurité:**
• "Quels sont les risques détectés?"
• "Audite les utilisateurs"

**Pour la sauvegarde:**
• "Quelle stratégie de backup recommandez-vous?"
• "Comment sauvegarder avec RMAN?"

**Pour la récupération:**
• "Guide pour restaurer une table"
• "Comment récupérer au 15 mars 14h?"

Ou utilisez les **boutons questions rapides** à gauche →
"""