# pages/accueil.py - VERSION SIMPLIFIÉE
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
            security_reports = sorted(reports_dir.glob("security_audit*.json"), reverse=True)
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