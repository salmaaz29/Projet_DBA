# pages/sauvegardes.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show():
    st.title("💾 Module Sauvegardes")
    
    # Métriques principales
    st.subheader("📊 État des Sauvegardes")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Dernier Backup", "2h", delta="-1h")
    with col2:
        st.metric("Taille totale", "250 GB", "+15 GB")
    with col3:
        st.metric("RPO actuel", "4h", delta="+0h")
    with col4:
        st.metric("RTO estimé", "2h", delta="-30m")
    
    # Historique backups
    st.subheader("📅 Historique des Sauvegardes")
    
    backup_history = pd.DataFrame({
        "Date": [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d %H:%M")
            for i in range(7, -1, -1)
        ],
        "Type": ["Full", "Incremental", "Incremental", "Full", "Incremental", "Incremental", "Full", "Incremental"],
        "Taille (GB)": [250, 12, 15, 255, 18, 14, 260, 16],
        "Statut": ["✅", "✅", "⚠️", "✅", "✅", "✅", "✅", "🔄"],
        "Durée": ["2h30", "25m", "30m", "2h45", "28m", "22m", "2h50", "En cours"]
    })
    
    st.dataframe(backup_history, use_container_width=True, hide_index=True)
    
    # Stratégie de sauvegarde
    st.subheader("🎯 Stratégie Recommandée")
    
    with st.expander("📋 Configuration actuelle", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**RPO requis:**")
            st.info("4 heures")
        
        with col2:
            st.write("**RTO requis:**")
            st.info("2 heures")
        
        with col3:
            st.write("**Criticité:**")
            st.warning("HAUTE")
    
    # Recommandations
    st.subheader("💡 Recommandations")
    
    recommendations = [
        "✅ Backup complet quotidien à 02:00",
        "✅ Backups incrémentaux toutes les 4 heures", 
        "⚠️  Archive logs à sauvegarder toutes les 30 minutes",
        "❌  Augmenter rétention de 7 à 14 jours",
        "✅  Tester la restauration chaque semaine"
    ]
    
    for rec in recommendations:
        if rec.startswith("✅"):
            st.success(rec)
        elif rec.startswith("⚠️"):
            st.warning(rec)
        elif rec.startswith("❌"):
            st.error(rec)
        else:
            st.info(rec)
    
    # Bouton pour générer une nouvelle stratégie
    st.subheader("⚙️ Générer une stratégie")
    
    if st.button("🔄 Générer une nouvelle stratégie de backup", type="primary"):
        with st.spinner("Analyse de votre base en cours..."):
            # Simulation d'appel au Module 7
            st.info("Exécution de: python src/backup_recommender.py")
            st.success("✅ Stratégie générée avec succès!")
            st.info("Consultez le fichier: reports/backup_strategy_*.json")
    
    # Lien vers le chatbot
    st.markdown("---")
    st.info("💬 **Besoin d'aide?** Demandez au chatbot: 'Quelle stratégie de backup pour RPO=2h?'")

if __name__ == "__main__":
    show()