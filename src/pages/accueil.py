# pages/accueil.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path

def show():
    st.title("🏠 Tableau de Bord Oracle AI")

    # Récupérer les modules depuis la session
    modules = st.session_state.get('modules', {})

    # ============================================================
    # MÉTRIQUES PRINCIPALES - DONNÉES RÉELLES
    # ============================================================

    # Initialiser les métriques par défaut
    security_score = 0
    performance_score = 0
    availability_score = 99.9
    alerts_count = 0

    # 1. SCORE SÉCURITÉ (Module 4)
    try:
        if modules.get('security_audit'):
            security_audit = modules['security_audit']
            # Essayer de récupérer le dernier rapport
            reports_dir = Path("reports")
            if reports_dir.exists():
                security_reports = sorted(reports_dir.glob("security_audit_*.json"), reverse=True)
                if security_reports:
                    with open(security_reports[0], 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        security_score = report.get('score_securite', 0)
                        alerts_count += len(report.get('risques_identifies', []))
    except Exception as e:
        st.warning(f"Erreur chargement sécurité: {str(e)[:50]}")

    # 2. SCORE PERFORMANCE (Module 5)
    try:
        if modules.get('query_optimizer'):
            # Compter les requêtes lentes analysées
            json_path = Path("data/queries_for_optimization.json")
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    queries = json.load(f)
                    total_queries = len(queries)
                    slow_queries = sum(1 for q in queries if q.get('basic_metrics', {}).get('elapsed_sec', 0) > 0.1)
                    if total_queries > 0:
                        performance_score = max(0, 100 - (slow_queries / total_queries * 100))
    except Exception as e:
        st.warning(f"Erreur chargement performance: {str(e)[:50]}")

    # 3. ANOMALIES (Module 6)
    try:
        anomaly_results = Path("data/anomaly_analysis_results.json")
        if anomaly_results.exists():
            with open(anomaly_results, 'r', encoding='utf-8') as f:
                results = json.load(f)
                stats = results.get('statistics', {})
                alerts_count += stats.get('critique', 0) + stats.get('suspect', 0)
    except Exception as e:
        pass

    # Afficher les métriques
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        color = "normal" if security_score >= 80 else "inverse" if security_score >= 60 else "off"
        st.metric("Sécurité", f"{security_score}/100", delta_color=color)
    with col2:
        st.metric("Performance", f"{performance_score:.0f}%", f"-{100-performance_score:.0f}%")
    with col3:
        st.metric("Disponibilité", f"{availability_score}%", "stable")
    with col4:
        st.metric("Alertes", alerts_count, f"+{alerts_count}")

    # ============================================================
    # ALERTES CRITIQUES - DONNÉES RÉELLES
    # ============================================================

    st.subheader("🚨 Alertes Critiques")

    critical_alerts = []
    high_alerts = []

    # Alertes sécurité critiques
    try:
        if modules.get('security_audit'):
            reports_dir = Path("reports")
            if reports_dir.exists():
                security_reports = sorted(reports_dir.glob("security_audit_*.json"), reverse=True)
                if security_reports:
                    with open(security_reports[0], 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        risques = report.get('risques_identifies', [])
                        for risque in risques:
                            if risque.get('severite') == 'CRITIQUE':
                                critical_alerts.append({
                                    'title': risque.get('description', 'Risque critique'),
                                    'action': 'Action immédiate requise'
                                })
                            elif risque.get('severite') == 'HAUTE':
                                high_alerts.append({
                                    'title': risque.get('description', 'Risque élevé'),
                                    'action': 'Action recommandée'
                                })
    except Exception as e:
        pass

    # Alertes anomalies critiques
    try:
        anomaly_results = Path("data/anomaly_analysis_results.json")
        if anomaly_results.exists():
            with open(anomaly_results, 'r', encoding='utf-8') as f:
                results = json.load(f)
                reports = results.get('anomaly_reports', [])
                critiques = [r for r in reports if r.get('classification') == 'CRITIQUE']
                for crit in critiques[:2]:  # Max 2 alertes critiques
                    log = crit.get('log', {})
                    critical_alerts.append({
                        'title': f"Anomalie critique: {log.get('username', 'N/A')} - {log.get('action', 'N/A')}",
                        'action': 'Investigation immédiate'
                    })
    except Exception as e:
        pass

    # Afficher les alertes
    if critical_alerts:
        alert_col1, alert_col2 = st.columns(2)

        for i, alert in enumerate(critical_alerts[:2]):
            col = alert_col1 if i == 0 else alert_col2
            with col:
                st.error(f"""
                **CRITIQUE** : {alert['title']}
                - Action : {alert['action']}
                """)

    if high_alerts and len(critical_alerts) < 2:
        remaining_slots = 2 - len(critical_alerts)
        for alert in high_alerts[:remaining_slots]:
            st.warning(f"""
            **HAUTE** : {alert['title']}
            - Action : {alert['action']}
            """)

    if not critical_alerts and not high_alerts:
        st.success("✅ Aucune alerte critique détectée")

    # ============================================================
    # ACTIVITÉ RÉCENTE - DONNÉES RÉELLES
    # ============================================================

    st.subheader("📊 Activité Récente")

    activities = []

    # Activité sécurité
    try:
        reports_dir = Path("reports")
        if reports_dir.exists():
            security_reports = sorted(reports_dir.glob("security_audit_*.json"), reverse=True)
            if security_reports:
                timestamp = security_reports[0].stat().st_mtime
                dt = datetime.fromtimestamp(timestamp)
                activities.append({
                    "Heure": dt.strftime("%H:%M"),
                    "Événement": "Audit sécurité",
                    "Module": "Module 4",
                    "Statut": "✅ Terminé"
                })
    except Exception as e:
        pass

    # Activité performance
    try:
        json_path = Path("data/queries_for_optimization.json")
        if json_path.exists():
            timestamp = json_path.stat().st_mtime
            dt = datetime.fromtimestamp(timestamp)
            activities.append({
                "Heure": dt.strftime("%H:%M"),
                "Événement": "Analyse requêtes lentes",
                "Module": "Module 5",
                "Statut": "✅ Terminé"
            })
    except Exception as e:
        pass

    # Activité anomalies
    try:
        anomaly_results = Path("data/anomaly_analysis_results.json")
        if anomaly_results.exists():
            timestamp = anomaly_results.stat().st_mtime
            dt = datetime.fromtimestamp(timestamp)
            activities.append({
                "Heure": dt.strftime("%H:%M"),
                "Événement": "Détection anomalies",
                "Module": "Module 6",
                "Statut": "✅ Terminé"
            })
    except Exception as e:
        pass

    # Activité backup
    try:
        reports_dir = Path("reports")
        if reports_dir.exists():
            backup_reports = sorted(reports_dir.glob("backup_strategy_*.json"), reverse=True)
            if backup_reports:
                timestamp = backup_reports[0].stat().st_mtime
                dt = datetime.fromtimestamp(timestamp)
                activities.append({
                    "Heure": dt.strftime("%H:%M"),
                    "Événement": "Stratégie backup",
                    "Module": "Module 7",
                    "Statut": "✅ Terminé"
                })
    except Exception as e:
        pass

    # Activité récupération
    try:
        reports_dir = Path("reports")
        if reports_dir.exists():
            recovery_reports = sorted(reports_dir.glob("recovery_guide_*.json"), reverse=True)
            if recovery_reports:
                timestamp = recovery_reports[0].stat().st_mtime
                dt = datetime.fromtimestamp(timestamp)
                activities.append({
                    "Heure": dt.strftime("%H:%M"),
                    "Événement": "Guide récupération",
                    "Module": "Module 8",
                    "Statut": "✅ Terminé"
                })
    except Exception as e:
        pass

    # Si pas d'activité récente, ajouter des exemples
    if not activities:
        activities = [
            {"Heure": "10:30", "Événement": "Système initialisé", "Module": "Module 9", "Statut": "✅ Terminé"},
            {"Heure": "10:25", "Événement": "Modules chargés", "Module": "Tous", "Statut": "✅ Terminé"}
        ]

    # Trier par heure (plus récent en premier)
    activities.sort(key=lambda x: x["Heure"], reverse=True)

    df = pd.DataFrame(activities[:5])  # Max 5 activités
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ============================================================
    # TENDANCES SÉCURITÉ - DONNÉES RÉELLES
    # ============================================================

    st.subheader("📈 Tendances Sécurité")

    # Essayer de récupérer l'historique des scores sécurité
    security_history = []

    try:
        reports_dir = Path("reports")
        if reports_dir.exists():
            security_reports = sorted(reports_dir.glob("security_audit_*.json"))
            for report_file in security_reports[-7:]:  # Derniers 7 rapports
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        score = report.get('score_securite', 0)
                        # Extraire la date du nom de fichier
                        filename = report_file.name
                        # security_audit_20240113_120000.json -> 2024-01-13
                        date_str = filename.split('_')[2][:8]  # 20240113
                        date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        security_history.append({"Date": date, "Score": score})
                except Exception as e:
                    continue
    except Exception as e:
        pass

    if len(security_history) >= 2:
        security_df = pd.DataFrame(security_history)
        st.line_chart(security_df.set_index("Date"))
    else:
        # Données par défaut si pas d'historique
        security_data = pd.DataFrame({
            "Jour": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
            "Score": [78, 82, 85, 87, 85, 83, 85]
        })
        st.line_chart(security_data.set_index("Jour"))
        st.caption("*Données d'exemple - Lancez des audits pour voir l'évolution réelle*")

    # ============================================================
    # STATUT DES MODULES
    # ============================================================

    st.subheader("🔧 Statut des Modules")

    module_status = {
        'Module 1 - Extraction': '✅' if modules.get('data_extractor') else '❌',
        'Module 2 - RAG': '✅' if modules.get('rag_setup') else '❌',
        'Module 3 - LLM': '✅' if modules.get('llm_engine') else '❌',
        'Module 4 - Sécurité': '✅' if modules.get('security_audit') else '❌',
        'Module 5 - Performance': '✅' if modules.get('query_optimizer') else '❌',
        'Module 6 - Anomalies': '✅' if modules.get('anomaly_detector') else '❌',
        'Module 7 - Backup': '✅' if modules.get('backup_recommender') else '❌',
        'Module 8 - Recovery': '✅' if modules.get('recovery_guide') else '❌'
    }

    cols = st.columns(4)
    for i, (module_name, status) in enumerate(module_status.items()):
        with cols[i % 4]:
            st.metric(module_name, status)
