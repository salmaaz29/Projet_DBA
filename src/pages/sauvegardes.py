# pages/sauvegardes.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# Exemple de contenu JSON généré (comme tu l'as montré)
generated_strategy_json = {
    "timestamp": "2026-01-11T17:45:14.832507",
    "input": {
        "rpo_hours": 1.0,
        "rto_hours": 1.0,
        "budget": "LOW",
        "db_size_gb": 2.5,
        "transactions_per_hour": 600,
        "criticality": "HIGH"
    },
    "strategy": {
        "key": "CRITICAL_24_7",
        "name": "CRITIQUE 24/7 (Banque, Bourse)",
        "description": "Production critique avec RPO < 1h",
        "backup_type": "complète",
        "frequency": "horaire",
        "retention_days": 30,
        "storage_location": "/backup/critical/",
        "script_type": "RMAN"
    },
    "costs": {
        "full_backup_size_gb": 2.5,
        "daily_incremental_gb": 0,
        "archive_logs_daily_gb": 0.25,
        "total_storage_gb": 1807.5,
        "monthly_cost_eur": 180.75,
        "annual_cost_eur": 2169.0
    },
    "backup_script": "-- ============================================\n-- STRATÉGIE RMAN: CRITIQUE 24/7 (Banque, Bourse)\n-- Généré: 2026-01-11 17:45\n-- Base: 2.5 GB - HIGH CRITICALITY\n-- ============================================\n\n-- Configuration RMAN\nCONFIGURE COMPRESSION ALGORITHM 'BASIC';\nCONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF 30 DAYS;\nCONFIGURE CONTROLFILE AUTOBACKUP ON;\nCONFIGURE DEVICE TYPE DISK PARALLELISM 4;\n\n-- Script backup complet hebdomadaire\nRUN {\n  ALLOCATE CHANNEL ch1 DEVICE TYPE DISK FORMAT '/backup/critical/full_%T_%U.bkp';\n  ALLOCATE CHANNEL ch2 DEVICE TYPE DISK FORMAT '/backup/critical/full_%T_%U.bkp';\n  ALLOCATE CHANNEL ch3 DEVICE TYPE DISK FORMAT '/backup/critical/full_%T_%U.bkp';\n  ALLOCATE CHANNEL ch4 DEVICE TYPE DISK FORMAT '/backup/critical/full_%T_%U.bkp';\n\n  BACKUP AS COMPRESSED BACKUPSET DATABASE PLUS ARCHIVELOG DELETE INPUT;\n  BACKUP CURRENT CONTROLFILE FORMAT '/backup/critical/control_%T_%U.ctl';\n\n  RELEASE CHANNEL ch1;\n  RELEASE CHANNEL ch2;\n  RELEASE CHANNEL ch3;\n  RELEASE CHANNEL ch4;\n}\n\n-- Validation et nettoyage\nRESTORE DATABASE VALIDATE;\nDELETE NOPROMPT OBSOLETE;\n\n-- Rapport de backup\nLIST BACKUP SUMMARY;\n",
    "implementation_steps": [
        "0. Mettre en place la réplication Data Guard",
        "1. Créer les répertoires de stockage",
        "2. Configurer les permissions Oracle",
        "3. Tester la connectivité au stockage",
        "4. Programmer les jobs de backup",
        "5. Configurer la surveillance",
        "6. Effectuer un test de restauration",
        "7. Configurer les alertes temps réel"
    ]
}

def show():
    st.title("💾 Module Sauvegardes")
    
    # --- Historique et métriques (comme avant) ---
    st.subheader("📊 État des Sauvegardes")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Dernier Backup", "2h", delta="-1h")
    with col2: st.metric("Taille totale", "250 GB", "+15 GB")
    with col3: st.metric("RPO actuel", "4h", delta="+0h")
    with col4: st.metric("RTO estimé", "2h", delta="-30m")
    
    st.subheader("📅 Historique des Sauvegardes")
    backup_history = pd.DataFrame({
        "Date": [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d %H:%M") for i in range(7, -1, -1)],
        "Type": ["Full", "Incremental", "Incremental", "Full", "Incremental", "Incremental", "Full", "Incremental"],
        "Taille (GB)": [250, 12, 15, 255, 18, 14, 260, 16],
        "Statut": ["✅", "✅", "⚠️", "✅", "✅", "✅", "✅", "🔄"],
        "Durée": ["2h30", "25m", "30m", "2h45", "28m", "22m", "2h50", "En cours"]
    })
    st.dataframe(backup_history, use_container_width=True, hide_index=True)
    
    # --- Bouton pour générer et afficher la stratégie ---
    st.subheader("⚙️ Générer et afficher une stratégie de backup")
    
    if st.button("🔄 Générer la stratégie de backup"):
        st.info("Analyse en cours...")
        
        # --- Affichage JSON complet ---
        st.subheader("📝 Stratégie JSON générée")
        st.json(generated_strategy_json)
        
        # --- Affichage du script RMAN ---
        st.subheader("💻 Script RMAN")
        st.code(generated_strategy_json["backup_script"], language="sql")
        
        # --- Étapes d'implémentation ---
        st.subheader("🛠 Étapes d'implémentation recommandées")
        for step in generated_strategy_json["implementation_steps"]:
            st.write(f"- {step}")
        
        st.success("✅ Stratégie affichée directement sur la page!")

if __name__ == "__main__":
    show()
