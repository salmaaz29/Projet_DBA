# 🗄️ Oracle AI Platform

Une plateforme intelligente de gestion et d'optimisation des bases de données Oracle utilisant l'IA et le Machine Learning.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Modules](#modules)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Structure des fichiers](#structure-des-fichiers)
- [API et Intégrations](#api-et-intégrations)
- [Tests](#tests)
- [Déploiement](#déploiement)
- [Contribuer](#contribuer)
- [Licence](#licence)

## 🎯 Vue d'ensemble

Oracle AI Platform est une application web moderne construite avec Streamlit qui offre une interface unifiée pour :

- **🤖 Intelligence Artificielle** : Intégration LLM (Groq API) pour l'analyse intelligente
- **📊 Optimisation des performances** : Analyse et optimisation automatique des requêtes SQL
- **🔒 Audit de sécurité** : Évaluation continue de la sécurité des bases de données
- **🚨 Détection d'anomalies** : Surveillance intelligente des logs d'audit
- **💾 Gestion des sauvegardes** : Recommandations stratégiques de sauvegarde
- **🔄 Récupération** : Guides automatisés de récupération après sinistre
- **📚 Recherche vectorielle** : RAG (Retrieval-Augmented Generation) avec Pinecone

## 🏗️ Architecture

### Architecture Technique

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │────│   Modules       │────│   LLM Engine    │
│   (Pages)       │    │   (Business     │    │   (Groq API)    │
└─────────────────┘    │   Logic)        │    └─────────────────┘
                       └─────────────────┘             │
                              │                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Data Layer    │────│   Vector DB     │
                       │   (Oracle DB)   │    │   (Pinecone)    │
                       └─────────────────┘    └─────────────────┘
```

### Technologies Principales

- **Frontend** : Streamlit
- **IA** : Groq API (Llama 4)
- **Base de données** : Oracle Database
- **Vector Database** : Pinecone
- **Langage** : Python 3.8+
- **ORM** : oracledb

## 🔧 Modules

### Module 1 : Extraction de Données (`data_extractor.py`)
- Connexion à Oracle Database
- Extraction de métriques de performance
- Collecte de plans d'exécution
- Génération de données synthétiques

### Module 2 : LLM Engine (`llm_engine.py`)
- Interface centralisée avec Groq API
- Gestion des prompts et templates
- Classification d'intention utilisateur
- Génération de réponses contextuelles

### Module 3 : RAG Setup (`rag_setup.py`)
- Configuration Pinecone
- Indexation vectorielle des documents
- Recherche sémantique
- Intégration avec LLM

### Module 4 : Security Audit (`security_audit.py`)
- Analyse des utilisateurs et rôles
- Évaluation des privilèges
- Génération de rapports de sécurité
- Recommandations de hardening

### Module 5 : Query Optimizer (`query_optimizer.py`)
- Analyse des plans d'exécution
- Détection des requêtes lentes
- Suggestions d'optimisation
- Métriques de performance

### Module 6 : Anomaly Detector (`module6_anomaly_detector.py`)
- Analyse des logs d'audit
- Détection d'anomalies comportementales
- Classification des menaces
- Alertes automatiques

### Module 7 : Backup Recommender (`module7_backup_recommender.py`)
- Analyse RTO/RPO
- Recommandations stratégiques
- Estimation des coûts
- Génération de scripts RMAN

### Module 8 : Recovery Guide (`recovery_guide.py`)
- Guides de récupération contextuels
- Playbooks automatisés
- Estimation des temps de récupération
- Support multi-scénarios

## 🚀 Installation

### Prérequis

```bash
# Python 3.8 ou supérieur
python --version

# Clés API
# - GROQ_API_KEY : https://console.groq.com/
# - PINECONE_API_KEY : https://www.pinecone.io/
```

### Installation Automatique

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

## ⚙️ Configuration

### Variables d'Environnement (`.env`)

```bash
# Oracle Database
ORACLE_HOST=localhost
ORACLE_PORT=1522
ORACLE_SERVICE=ORCLPDB1
ORACLE_USER=admin_user
ORACLE_PASSWORD=admin_password

# API Keys
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

## 🎮 Utilisation

### Démarrage de l'Application

```bash
# Depuis la racine du projet
streamlit run src/pages/dashboard.py

# Ou utiliser le launcher
python -m streamlit run src/pages/dashboard.py
```

### Navigation dans l'Interface

1. **🏠 Accueil** : Vue d'ensemble et métriques générales
2. **💬 Chatbot IA** : Assistant conversationnel intelligent
3. **⚡ Performance** : Analyse et optimisation des requêtes
4. **🔒 Sécurité** : Audit et recommandations de sécurité
5. **💾 Sauvegardes** : Gestion stratégique des sauvegardes
6. **📊 Dashboard** : Métriques et statut des modules

## 📁 Structure des Fichiers

```
Projet_DBA/
├── src/
│   ├── __init__.py
│   ├── llm_engine.py              # Moteur IA central
│   ├── rag_setup.py               # Configuration RAG
│   ├── data_extractor.py          # Extraction Oracle
│   ├── security_audit.py          # Module 4
│   ├── query_optimizer.py         # Module 5
│   ├── module6_anomaly_detector.py # Module 6
│   ├── module7_backup_recommender.py # Module 7
│   ├── recovery_guide.py          # Module 8
│   └── pages/
│       ├── dashboard.py           # Page principale
│       ├── chatbot.py             # Interface chatbot
│       ├── accueil.py             # Page d'accueil
│       ├── performance.py         # Page performance
│       ├── securite.py            # Page sécurité
│       └── sauvegardes.py         # Page sauvegardes
├── data/
│   ├── prompts.yaml               # Templates de prompts
│   ├── audit_logs_synthetic.csv   # Logs synthétiques
│   ├── security_*.csv            # Données sécurité
│   ├── slow_queries_*.csv        # Requêtes lentes
│   ├── docs/                     # Documentation Oracle
│   └── rapport_llm_*.json        # Rapports LLM
├── tests/
│   ├── test_*.py                 # Tests unitaires
│   └── creation_requetes.py      # Tests de génération
├── reports/
│   └── backup_strategy*.json     # Stratégies générées
├── requirements.txt              # Dépendances Python
├── README.md                     # Cette documentation
├── .env                          # Variables d'environnement
```

## 🔌 API et Intégrations

### Groq API
- **Modèle** : meta-llama/llama-4-scout-17b-16e-instruct
- **Usage** : Génération de texte, classification, analyse
- **Rate Limiting** : Gestion automatique des retries

### Pinecone Vector Database
- **Index** : oracle-ai
- **Namespace** : rag-docs
- **Dimensions** : 384 (embeddings)
- **Métrique** : Cosine similarity

### Oracle Database
- **Driver** : oracledb
- **Support** : Oracle 19c, 21c
- **Connexion** : Pooling automatique
- **Sécurité** : Chiffrement TLS

### Tests Disponibles

- `test_llm_engine.py` : Tests du moteur IA
- `test_module5.py` : Tests d'optimisation
- `test_module6.py` : Tests de détection d'anomalies
- `test_module7.py` : Tests de sauvegarde
- `test_module8.py` : Tests de récupération
- `test_connexion.py` : Tests de connexion Oracle
