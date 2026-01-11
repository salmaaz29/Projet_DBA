# dashboard.py - VERSION AVEC INITIALISATION CENTRALISÉE
import streamlit as st
import sys
from pathlib import Path
import os

# ============================================================
# CONFIGURATION DES CHEMINS - VERSION CORRIGÉE
# ============================================================
# Obtenir le répertoire du fichier actuel
CURRENT_FILE = Path(__file__).resolve()
CURRENT_DIR = CURRENT_FILE.parent  # src/pages/
SRC_DIR = CURRENT_DIR.parent       # src/
PROJECT_ROOT = SRC_DIR.parent      # Projet_DBA/

# Ajouter les chemins
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(CURRENT_DIR))  # Pour importer les autres pages

print(f"📁 Chemins configurés:")
print(f"   Project Root: {PROJECT_ROOT}")
print(f"   Src Dir: {SRC_DIR}")
print(f"   Current Dir: {CURRENT_DIR}")

# Changer le répertoire de travail vers la racine
os.chdir(PROJECT_ROOT)

# ============================================================
# INITIALISATION CENTRALISÉE (UNE SEULE FOIS)
# ============================================================

@st.cache_resource(show_spinner=False)
def initialize_all_modules():
    """
    Initialise TOUS les modules UNE SEULE FOIS au démarrage
    Utilisé par tous les onglets
    """
    import time
    
    print("\n" + "="*60)
    print("🔧 INITIALISATION CENTRALISÉE DES MODULES")
    print("="*60)
    
    modules_initialized = {
        'data_extractor': None,
        'llm_engine': None,
        'rag_setup': None,
        'security_audit': None,
        'query_optimizer': None,
        'anomaly_detector': None,
        'backup_recommender': None,
        'recovery_guide': None,
        'init_status': 'running'
    }
    
    try:
        # ============================================================
        # MODULE 3 : LLM Engine + RAG (BASE POUR TOUT)
        # ============================================================
        print("\n[1/8] 🤖 Initialisation LLM + RAG...")
        time.sleep(0.1)
        
        try:
            from llm_engine import LLMEngine
            from rag_setup import OracleRAGSetup

            print("      Chargement RAG...")
            rag = OracleRAGSetup(namespace="rag-docs")

            print("      Chargement LLM Engine...")
            llm_engine = LLMEngine(model="meta-llama/llama-4-scout-17b-16e-instruct")

            modules_initialized['llm_engine'] = llm_engine
            modules_initialized['rag_setup'] = rag
            print("      ✅ LLM + RAG OK")

        except Exception as e:
            print(f"      ⚠️  LLM/RAG échec: {str(e)[:80]}")
            modules_initialized['llm_engine'] = None
            modules_initialized['rag_setup'] = None
        
        # ============================================================
        # MODULE 1 : Data Extractor (OPTIONNEL)
        # ============================================================
        print("\n[2/8] 📊 Data Extractor...")
        time.sleep(0.1)
        
        try:
            from data_extractor import OracleDataExtractor
            
            # Mode simulation par défaut pour éviter les blocages
            extractor = OracleDataExtractor(use_simulation=False)
            modules_initialized['data_extractor'] = extractor
            print("      ✅ Data Extractor OK (mode simulation)")
            
        except Exception as e:
            print(f"      ⚠️  Data Extractor échec: {str(e)[:80]}")
            modules_initialized['data_extractor'] = None
        
        # ============================================================
        # MODULES 4-8 : Avec LLM
        # ============================================================
        llm = modules_initialized.get('llm_engine')
        rag = modules_initialized.get('rag_setup')
        
        # MODULE 4 : Security Audit
        print("\n[3/8] 🔒 Module 4 - Security Audit...")
        time.sleep(0.1)
        
        try:
            from security_audit import SecurityAudit

            if llm:
                modules_initialized['security_audit'] = SecurityAudit(llm_engine=llm)
                print("      ✅ Security Audit OK")
            else:
                print("      ⚠️  Security Audit nécessite LLM")
        except Exception as e:
            print(f"      ⚠️  Security Audit échec: {str(e)[:80]}")
        
        # MODULE 5 : Query Optimizer
        print("\n[4/8] ⚡ Module 5 - Query Optimizer...")
        time.sleep(0.1)
        
        try:
            from query_optimizer import OracleQueryOptimizerLLM
            
            if llm:
                modules_initialized['query_optimizer'] = OracleQueryOptimizerLLM(llm_engine=llm)
                print("      ✅ Query Optimizer OK")
            else:
                print("      ⚠️  Query Optimizer nécessite LLM")
        except Exception as e:
            print(f"      ⚠️  Query Optimizer échec: {str(e)[:80]}")
        
        # MODULE 6 : Anomaly Detector
        print("\n[5/8] 🚨 Module 6 - Anomaly Detector...")
        time.sleep(0.1)
        
        try:
            from module6_anomaly_detector import OracleAnomalyDetector
            
            modules_initialized['anomaly_detector'] = OracleAnomalyDetector(
                llm_engine=llm, 
                rag_setup=rag
            )
            print("      ✅ Anomaly Detector OK")
        except Exception as e:
            print(f"      ⚠️  Anomaly Detector échec: {str(e)[:80]}")
        
        # MODULE 7 : Backup Recommender
        print("\n[6/8] 💾 Module 7 - Backup Recommender...")
        time.sleep(0.1)

        try:
            from module7_backup_recommender import OracleBackupRecommender

            modules_initialized['backup_recommender'] = OracleBackupRecommender(
                llm_engine=llm,
                rag_setup=rag
            )
            print("      ✅ Backup Recommender OK")
        except Exception as e:
            print(f"      ⚠️  Backup Recommender échec: {str(e)[:80]}")
        
        # MODULE 8 : Recovery Guide
        print("\n[7/8] 🔄 Module 8 - Recovery Guide...")
        time.sleep(0.1)

        try:
            from recovery_guide import OracleRecoveryGuide

            modules_initialized['recovery_guide'] = OracleRecoveryGuide(
                rag_setup=rag
            )
            print("      ✅ Recovery Guide OK")
        except Exception as e:
            print(f"      ⚠️  Recovery Guide échec: {str(e)[:80]}")
        
        print("\n[8/8] ✅ Finalisation...")
        modules_initialized['init_status'] = 'completed'
        
        print("\n" + "="*60)
        print("🎉 INITIALISATION TERMINÉE")
        print("="*60)
        
    except Exception as global_error:
        print(f"\n❌ ERREUR GLOBALE: {global_error}")
        import traceback
        traceback.print_exc()
        modules_initialized['init_status'] = 'error'
    
    return modules_initialized


# ============================================================
# INTERFACE STREAMLIT
# ============================================================

def main():
    st.set_page_config(
        page_title="Oracle AI Platform",
        page_icon="🗄️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personnalisé
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ============================================================
    # INITIALISATION AU DÉMARRAGE (CACHE)
    # ============================================================
    if 'modules' not in st.session_state:
        # Afficher la progression
        progress_placeholder = st.empty()
        
        with progress_placeholder.container():
            st.info("🔧 Initialisation des modules en cours...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simuler la progression pendant l'init
            import time
            for i in range(0, 100, 12):
                progress_bar.progress(i)
                time.sleep(0.1)
            
            # Lancer l'initialisation
            st.session_state.modules = initialize_all_modules()
            
            progress_bar.progress(100)
            status_text.success("✅ Modules chargés!")
            time.sleep(1)
        
        progress_placeholder.empty()
    
    modules = st.session_state.modules
    
    # Vérifier le statut d'initialisation
    if modules.get('init_status') == 'error':
        st.error("❌ Erreur lors de l'initialisation. Consultez la console.")
    elif modules.get('init_status') == 'completed':
        pass  # OK
    else:
        st.warning("⚠️ Initialisation en cours...")
    
    # ============================================================
    # NAVIGATION
    # ============================================================
    st.sidebar.title("🗄️ Oracle AI Platform")
    st.sidebar.markdown("---")
    
    # Statut des modules
    st.sidebar.subheader("📊 Statut Modules")
    
    module_status = {
        'LLM Engine': '✅' if modules.get('llm_engine') else '❌',
        'RAG Setup': '✅' if modules.get('rag_setup') else '❌',
        'Oracle DB': '✅' if modules.get('data_extractor') and not modules['data_extractor'].use_simulation else '⚠️',
        'Security (M4)': '✅' if modules.get('security_audit') else '❌',
        'Performance (M5)': '✅' if modules.get('query_optimizer') else '❌',
        'Anomalies (M6)': '✅' if modules.get('anomaly_detector') else '❌',
        'Backup (M7)': '✅' if modules.get('backup_recommender') else '❌',
        'Recovery (M8)': '✅' if modules.get('recovery_guide') else '❌'
    }
    
    for module_name, status in module_status.items():
        st.sidebar.text(f"{status} {module_name}")
    
    st.sidebar.markdown("---")
    
    # Onglets
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Accueil", "💬 Chatbot", "⚡ Performance", "🔒 Sécurité", "💾 Sauvegardes"],
        label_visibility="collapsed"
    )
    
    # ============================================================
    # AFFICHAGE DES PAGES
    # ============================================================
    if page == "🏠 Accueil":
        import accueil
        accueil.show()
    
    elif page == "💬 Chatbot":
        import chatbot
        chatbot.show()
    
    elif page == "⚡ Performance":
        import performance
        performance.show()
    
    elif page == "🔒 Sécurité":
        import securite
        securite.show()
    
    elif page == "💾 Sauvegardes":
        import sauvegardes
        sauvegardes.show()


if __name__ == "__main__":
    main()