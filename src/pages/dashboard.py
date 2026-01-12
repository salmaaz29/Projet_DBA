# dashboard.py - VERSION SANS GRAPHIQUE NI MÉTRIQUES

import streamlit as st
import sys
from pathlib import Path
import os
import time

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
    Version corrigée pour compatibilité avec vos modifications
    """
    
    print("\n" + "="*60)
    print("🔧 INITIALISATION CENTRALISÉE DES MODULES (V2)")
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
        
        try:
            from llm_engine import LLMEngine
            from rag_setup import OracleRAGSetup

            print("      → Chargement RAG...")
            rag = OracleRAGSetup(namespace="rag-docs")
            print("      → RAG chargé")

            print("      → Chargement LLM Engine...")
            llm_engine = LLMEngine(model="meta-llama/llama-4-scout-17b-16e-instruct")
            print("      → LLM Engine chargé")

            modules_initialized['llm_engine'] = llm_engine
            modules_initialized['rag_setup'] = rag
            print("      ✅ LLM + RAG OK")

        except Exception as e:
            print(f"      ❌ LLM/RAG échec: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
            modules_initialized['llm_engine'] = None
            modules_initialized['rag_setup'] = None
        
        # ============================================================
        # MODULE 1 : Data Extractor (OPTIONNEL)
        # ============================================================
        print("\n[2/8] 📊 Data Extractor...")
        
        try:
            from data_extractor import OracleDataExtractor
            
            extractor = OracleDataExtractor(use_simulation=True)  # Simulation par défaut
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
        
        if not llm:
            print("⚠️  LLM non disponible - Modules 4-8 désactivés")
        else:
            # MODULE 4 : Security Audit
            print("\n[3/8] 🔒 Module 4 - Security Audit...")
            
            try:
                from security_audit import SecurityAudit
                modules_initialized['security_audit'] = SecurityAudit(llm_engine=llm)
                print("      ✅ Security Audit OK")
            except Exception as e:
                print(f"      ⚠️  Security Audit échec: {str(e)[:80]}")
            
            # MODULE 5 : Query Optimizer
            print("\n[4/8] ⚡ Module 5 - Query Optimizer...")
            
            try:
                from query_optimizer import OracleQueryOptimizerLLM
                modules_initialized['query_optimizer'] = OracleQueryOptimizerLLM(llm_engine=llm)
                print("      ✅ Query Optimizer OK")
            except Exception as e:
                print(f"      ⚠️  Query Optimizer échec: {str(e)[:80]}")
            
            # MODULE 6 : Anomaly Detector
            print("\n[5/8] 🚨 Module 6 - Anomaly Detector...")
            
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

            try:
                from recovery_guide import OracleRecoveryGuide
                modules_initialized['recovery_guide'] = OracleRecoveryGuide(rag_setup=rag)
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
# INTERFACE STREAMLIT - VERSION SIMPLIFIÉE
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
    
    /* Améliorations visuelles */
    .module-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        margin-bottom: 15px;
    }
    
    .status-success {
        color: #00C853;
        font-weight: bold;
    }
    
    .status-warning {
        color: #FF9800;
        font-weight: bold;
    }
    
    .status-error {
        color: #F44336;
        font-weight: bold;
    }
    
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    .chat-user {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    
    .chat-assistant {
        background-color: #F1F8E9;
        border-left: 4px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ============================================================
    # INITIALISATION AU DÉMARRAGE (CACHE)
    # ============================================================
    if 'modules' not in st.session_state:
        with st.spinner("🔧 Initialisation des modules..."):
            st.session_state.modules = initialize_all_modules()
    
    modules = st.session_state.modules
    
    # Vérifier le statut d'initialisation
    if modules.get('init_status') == 'error':
        st.error("❌ Erreur lors de l'initialisation. Consultez la console.")
    elif modules.get('init_status') == 'running':
        st.warning("⚠️ Initialisation en cours...")
    
    # ============================================================
    # NAVIGATION
    # ============================================================
    st.sidebar.title("🗄️ Oracle AI Platform")
    st.sidebar.markdown("---")
    
    # Statut des modules
    st.sidebar.subheader("📊 Statut Modules")
    
    # Vérification plus robuste des modules
    llm_status = "✅" if modules.get('llm_engine') else "❌"
    rag_status = "✅" if modules.get('rag_setup') else "❌"
    
    # Afficher avec couleurs
    st.sidebar.markdown(f"""
    <div style='margin-bottom: 10px;'>
    <span style='font-weight: bold;'>Core Modules:</span><br>
    {llm_status} <span style='color: {"green" if modules.get('llm_engine') else "red"};'>LLM Engine</span><br>
    {rag_status} <span style='color: {"green" if modules.get('rag_setup') else "red"};'>RAG Setup</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Onglets améliorés
    st.sidebar.subheader("📋 Navigation")
    
    # Utiliser des boutons radio avec icônes
    page_options = {
        "🏠 Accueil": "accueil",
        "💬 Chatbot IA": "chatbot",
        "⚡ Performance": "performance",
        "🔒 Sécurité": "securite",
        "💾 Sauvegardes": "sauvegardes",
        "📊 Dashboard": "dashboard"
    }
    
    selected_page = st.sidebar.radio(
        "Choisissez une page:",
        list(page_options.keys()),
        label_visibility="collapsed"
    )
    
    # Bouton pour recharger les modules
    if st.sidebar.button("🔄 Recharger les modules"):
        st.cache_resource.clear()
        if 'modules' in st.session_state:
            del st.session_state.modules
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Version 1.0 • {time.strftime('%d/%m/%Y %H:%M')}")
    
    # ============================================================
    # AFFICHAGE DES PAGES AVEC GESTION D'ERREURS
    # ============================================================
    try:
        page_file = page_options[selected_page]
        
        if selected_page == "🏠 Accueil":
            try:
                import accueil
                accueil.show()
            except Exception as e:
                st.error(f"❌ Erreur chargement page Accueil: {e}")
                st.info("Vérifiez que le fichier accueil.py existe dans le dossier pages/")
        
        elif selected_page == "💬 Chatbot IA":
            try:
                import chatbot
                chatbot.show()
            except Exception as e:
                st.error(f"❌ Erreur chargement page Chatbot: {e}")
                st.code(f"Erreur: {str(e)}", language="python")
        
        elif selected_page == "⚡ Performance":
            try:
                import performance
                performance.show()
            except Exception as e:
                st.error(f"❌ Erreur chargement page Performance: {e}")
        
        elif selected_page == "🔒 Sécurité":
            try:
                import securite
                securite.show()
            except Exception as e:
                st.error(f"❌ Erreur chargement page Sécurité: {e}")
        
        elif selected_page == "💾 Sauvegardes":
            try:
                import sauvegardes
                sauvegardes.show()
            except Exception as e:
                st.error(f"❌ Erreur chargement page Sauvegardes: {e}")
        
        elif selected_page == "📊 Dashboard":
            # Page dashboard intégrée (simplifiée)
            show_dashboard_page(modules)
    
    except Exception as e:
        st.error(f"❌ Erreur navigation: {e}")
        st.info("Vérifiez que tous les fichiers de pages existent dans le dossier pages/")

def show_dashboard_page(modules):
    """Page dashboard simplifiée - SANS MÉTRIQUES NI GRAPHIQUE"""
    st.title("📊 Dashboard Oracle AI")
    
    # Section modules uniquement
    st.subheader("🔧 Modules")
    
    module_list = [
        ("LLM Engine", modules.get('llm_engine'), "🤖", "Core IA"),
        ("RAG Setup", modules.get('rag_setup'), "📚", "Recherche vectorielle"),
        ("Security Audit", modules.get('security_audit'), "🔒", "Module 4"),
        ("Query Optimizer", modules.get('query_optimizer'), "⚡", "Module 5"),
        ("Anomaly Detector", modules.get('anomaly_detector'), "🚨", "Module 6"),
        ("Backup Recommender", modules.get('backup_recommender'), "💾", "Module 7"),
        ("Recovery Guide", modules.get('recovery_guide'), "🔄", "Module 8"),
    ]
    
    cols = st.columns(3)
    for idx, (name, module, icon, desc) in enumerate(module_list):
        with cols[idx % 3]:
            status = "✅" if module else "❌"
            color = "green" if module else "red"
            st.markdown(f"""
            <div style='padding: 15px; border-radius: 10px; border: 2px solid {color}; margin-bottom: 10px;'>
                <div style='font-size: 24px;'>{icon}</div>
                <div style='font-weight: bold;'>{name}</div>
                <div style='color: gray; font-size: 12px;'>{desc}</div>
                <div style='color: {color}; font-weight: bold;'>{status}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Section tests rapides
    st.markdown("---")
    st.subheader("🧪 Tests rapides")
    
    if modules.get('llm_engine'):
        if st.button("Test LLM (hello)"):
            with st.spinner("Test en cours..."):
                try:
                    response = modules['llm_engine'].generate("Réponds 'OK' si tu fonctionnes")
                    st.success(f"✅ Réponse LLM: {response[:50]}...")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
    
    if modules.get('rag_setup'):
        if st.button("Test RAG (Oracle)"):
            with st.spinner("Recherche en cours..."):
                try:
                    results = modules['rag_setup'].retrieve_context("Oracle performance", n_results=2)
                    st.success(f"✅ {len(results)} résultat(s) trouvé(s)")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")

    # Test Pinecone integration if available
    if modules.get('llm_engine') and modules.get('rag_setup'):
        if st.button("Test Pinecone Integration"):
            with st.spinner("Test intégration Pinecone..."):
                try:
                    # Test the new Pinecone integration method
                    success = modules['llm_engine'].test_pinecone_integration(
                        pinecone_client=modules['rag_setup'].pinecone_client,
                        test_query="performance optimisation Oracle"
                    )
                    if success:
                        st.success("✅ Intégration Pinecone réussie")
                    else:
                        st.error("❌ Échec de l'intégration Pinecone")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")


if __name__ == "__main__":
    main()