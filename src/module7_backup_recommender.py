# -*- coding: utf-8 -*-
"""
MODULE 7 : Plans de Sauvegarde Intelligents Oracle - CSV + LLM
✅ Récupération métriques depuis CSV extracteur
✅ Interface utilisateur 3 questions (RPO, RTO, Budget)
✅ Recommandations IA avec prompts spécialisés
✅ Few-shot examples (4 stratégies types)
✅ Sortie JSON structurée
✅ Génération script RMAN réaliste
✅ Intégration LLM pour questions backup/sauvegarde
"""

import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from llm_engine import LLMEngine

class OracleBackupRecommender:
    """Recommandateur intelligent de stratégies de sauvegarde Oracle"""

    # Stratégies prédéfinies avec few-shot examples
    BACKUP_STRATEGIES = {
        "CRITICAL_24_7": {
            "name": "CRITIQUE 24/7 (Banque, Bourse)",
            "description": "Production critique avec RPO < 1h",
            "rpo_range": (0, 1),
            "rto_range": (0, 2),
            "backup_type": "complète",
            "frequency": "horaire",
            "retention_days": 30,
            "storage_location": "/backup/critical/",
            "cost_estimation": "Élevé (3x taille DB)",
            "script_type": "RMAN"
        },
        "PRODUCTION_STANDARD": {
            "name": "PRODUCTION STANDARD (E-commerce, ERP)",
            "description": "Production avec RPO 1-4h",
            "rpo_range": (1, 4),
            "rto_range": (2, 8),
            "backup_type": "incrémentale",
            "frequency": "quotidienne",
            "retention_days": 14,
            "storage_location": "/backup/production/",
            "cost_estimation": "Moyen (2x taille DB)",
            "script_type": "RMAN"
        },
        "BUSINESS_HOURS": {
            "name": "HEURES OUVRABLES (CRM, Reporting)",
            "description": "Production heures bureau avec RPO 4-8h",
            "rpo_range": (4, 8),
            "rto_range": (8, 24),
            "backup_type": "différentielle",
            "frequency": "hebdomadaire",
            "retention_days": 7,
            "storage_location": "/backup/business/",
            "cost_estimation": "Faible (1.5x taille DB)",
            "script_type": "Native Oracle"
        },
        "DEVELOPMENT": {
            "name": "DÉVELOPPEMENT / TEST",
            "description": "Environnement non-critique avec RPO > 24h",
            "rpo_range": (24, 168),
            "rto_range": (24, 72),
            "backup_type": "complète",
            "frequency": "hebdomadaire",
            "retention_days": 7,
            "storage_location": "/backup/dev/",
            "cost_estimation": "Minimal (1x taille DB)",
            "script_type": "Native Oracle"
        }
    }

    def __init__(self, llm_engine=None, rag_setup=None):
        self.llm = llm_engine
        self.rag = rag_setup
        self.db_metrics = None
    
    def load_metrics_from_csv(self) -> Dict:
        """Extraction métriques depuis CSV extracteur"""
        print("📊 Extraction métriques depuis CSV extracteur...")

        try:
            # Charger métriques DB
            if os.path.exists("data/db_metrics.csv"):
                df_metrics = pd.read_csv("data/db_metrics.csv")
                if not df_metrics.empty:
                    row = df_metrics.iloc[0]
                    db_size_gb = float(row.get('db_size_gb', 10.0))
                    active_sessions = int(row.get('active_sessions', 5))
                    log_mode = row.get('log_mode', 'ARCHIVELOG')

                    # Estimation volume transactions basé sur sessions actives
                    transactions_per_hour = max(active_sessions * 50, 100)

                    # Criticité basée sur mode log
                    criticality = "HIGH" if log_mode == "ARCHIVELOG" else "MEDIUM"

                    # Croissance estimée (0.5 GB/jour par défaut)
                    daily_growth_gb = 0.5

                    metrics = {
                        'size_gb': db_size_gb,
                        'transactions_per_hour': transactions_per_hour,
                        'criticality': criticality,
                        'daily_growth_gb': daily_growth_gb,
                        'workload_type': 'OLTP' if active_sessions > 10 else 'OLAP',
                        'log_mode': log_mode,
                        'active_sessions': active_sessions
                    }

                    print(f"   ✅ Métriques chargées depuis CSV:")
                    print(f"      • Taille: {db_size_gb} GB")
                    print(f"      • Transactions/h: {transactions_per_hour}")
                    print(f"      • Criticité: {criticality}")
                    print(f"      • Sessions actives: {active_sessions}")

                    self.db_metrics = metrics
                    return metrics

            print("   ⚠️  Fichier db_metrics.csv non trouvé → Métriques par défaut")
            return self._get_default_metrics()

        except Exception as e:
            print(f"   ❌ Erreur chargement CSV: {e}")
            return self._get_default_metrics()

    def _get_default_metrics(self) -> Dict:
        """Métriques par défaut"""
        return {
            'size_gb': 10.0,
            'transactions_per_hour': 1000,
            'criticality': 'MEDIUM',
            'daily_growth_gb': 0.5,
            'workload_type': 'OLTP',
            'log_mode': 'ARCHIVELOG',
            'active_sessions': 5
        }
    
    def ask_user_requirements(self) -> Dict:
        """Interface conversationnelle"""
        print("\n" + "="*70)
        print("📋 QUESTIONNAIRE - STRATÉGIE DE SAUVEGARDE")
        print("="*70)
        
        # RPO
        print("\n💬 Question 1/3 : RPO (Recovery Point Objective)")
        print("   Perte de données acceptable ?")
        print("   • 0.25 = 15 min (critique)")
        print("   • 1    = 1h (haute)")
        print("   • 4    = 4h (standard)")
        print("   • 24   = 1 jour (dev)")
        
        while True:
            try:
                rpo = input("   RPO en heures [4] : ").strip()
                rpo_hours = float(rpo) if rpo else 4.0
                if rpo_hours > 0:
                    break
            except:
                print("   ❌ Invalide")
        
        # RTO
        print("\n💬 Question 2/3 : RTO (Recovery Time Objective)")
        print("   Temps restauration acceptable ?")
        print("   • 1  = 1h")
        print("   • 8  = 8h")
        print("   • 24 = 1 jour")
        
        while True:
            try:
                rto = input("   RTO en heures [8] : ").strip()
                rto_hours = float(rto) if rto else 8.0
                if rto_hours > 0:
                    break
            except:
                print("   ❌ Invalide")
        
        # Budget
        print("\n💬 Question 3/3 : Budget")
        print("   1. LOW (économique)")
        print("   2. MEDIUM (équilibré)")
        print("   3. HIGH (performance)")
        
        while True:
            choice = input("   Choix [2] : ").strip()
            if choice == "" or choice == "2":
                budget = "MEDIUM"
                break
            elif choice == "1":
                budget = "LOW"
                break
            elif choice == "3":
                budget = "HIGH"
                break
        
        print(f"\n✅ RPO: {rpo_hours}h, RTO: {rto_hours}h, Budget: {budget}")
        
        return {
            'rpo_hours': rpo_hours,
            'rto_hours': rto_hours,
            'budget_category': budget
        }
    
    def select_strategy(self, rpo: float, rto: float, budget: str) -> str:
        """Sélectionne stratégie appropriée"""
        for key, strat in self.BACKUP_STRATEGIES.items():
            rpo_min, rpo_max = strat['rpo_range']
            rto_min, rto_max = strat['rto_range']
            
            if rpo_min <= rpo <= rpo_max and rto_min <= rto <= rto_max:
                return key
        
        if rpo < 1:
            return "CRITICAL_24_7"
        elif rpo <= 4:
            return "PRODUCTION_STANDARD"
        elif rpo <= 8:
            return "BUSINESS_HOURS"
        else:
            return "DEVELOPMENT"
    
    def calculate_costs(self, strategy_key: str, db_size: float, growth: float) -> Dict:
        """Calcule coûts stockage basé sur stratégie"""
        strategy = self.BACKUP_STRATEGIES[strategy_key]

        # Estimation stockage selon type de backup
        if strategy['backup_type'] == "complète":
            full_size = db_size
            daily_incr = 0
            arch_daily = growth * 0.5 if strategy['frequency'] == "horaire" else 0
        elif strategy['backup_type'] == "incrémentale":
            full_size = db_size * 0.7  # Backup complet hebdomadaire
            daily_incr = growth * 0.3  # Incrémental quotidien
            arch_daily = growth * 0.8
        elif strategy['backup_type'] == "différentielle":
            full_size = db_size * 0.8
            daily_incr = growth * 0.5
            arch_daily = growth * 0.6
        else:  # développement
            full_size = db_size
            daily_incr = 0
            arch_daily = 0

        # Calcul selon fréquence
        retention = strategy['retention_days']
        if strategy['frequency'] == "horaire":
            full_count = retention * 24  # Un backup complet par heure
        elif strategy['frequency'] == "quotidienne":
            full_count = retention
        elif strategy['frequency'] == "hebdomadaire":
            full_count = max(1, retention // 7)
        else:
            full_count = 1

        total_storage = (full_size * full_count +
                        daily_incr * retention +
                        arch_daily * retention)

        # Coût estimé (€/GB/mois)
        cost_per_gb_month = 0.10
        monthly_cost = total_storage * cost_per_gb_month

        return {
            'full_backup_size_gb': round(full_size, 2),
            'daily_incremental_gb': round(daily_incr, 2),
            'archive_logs_daily_gb': round(arch_daily, 2),
            'total_storage_gb': round(total_storage, 2),
            'monthly_cost_eur': round(monthly_cost, 2),
            'annual_cost_eur': round(monthly_cost * 12, 2)
        }
    
    def generate_backup_script(self, strategy_key: str, db_metrics: Dict) -> str:
        """Génère script backup réaliste selon stratégie"""
        strategy = self.BACKUP_STRATEGIES[strategy_key]

        if strategy['script_type'] == "RMAN":
            return self._generate_rman_script(strategy, db_metrics)
        else:
            return self._generate_native_script(strategy, db_metrics)

    def _generate_rman_script(self, strategy: Dict, db_metrics: Dict) -> str:
        """Génère script RMAN pour stratégies critiques/production"""
        script = f"""-- ============================================
-- STRATÉGIE RMAN: {strategy['name']}
-- Généré: {datetime.now().strftime('%Y-%m-%d %H:%M')}
-- Base: {db_metrics['size_gb']} GB - {db_metrics['criticality']} CRITICALITY
-- ============================================

-- Configuration RMAN
CONFIGURE COMPRESSION ALGORITHM 'BASIC';
CONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF {strategy['retention_days']} DAYS;
CONFIGURE CONTROLFILE AUTOBACKUP ON;
CONFIGURE DEVICE TYPE DISK PARALLELISM 4;

-- Script backup complet hebdomadaire
RUN {{
  ALLOCATE CHANNEL ch1 DEVICE TYPE DISK FORMAT '{strategy['storage_location']}full_%T_%U.bkp';
  ALLOCATE CHANNEL ch2 DEVICE TYPE DISK FORMAT '{strategy['storage_location']}full_%T_%U.bkp';
  ALLOCATE CHANNEL ch3 DEVICE TYPE DISK FORMAT '{strategy['storage_location']}full_%T_%U.bkp';
  ALLOCATE CHANNEL ch4 DEVICE TYPE DISK FORMAT '{strategy['storage_location']}full_%T_%U.bkp';

  BACKUP AS COMPRESSED BACKUPSET DATABASE PLUS ARCHIVELOG DELETE INPUT;
  BACKUP CURRENT CONTROLFILE FORMAT '{strategy['storage_location']}control_%T_%U.ctl';

  RELEASE CHANNEL ch1;
  RELEASE CHANNEL ch2;
  RELEASE CHANNEL ch3;
  RELEASE CHANNEL ch4;
}}

"""

        if strategy['backup_type'] == "incrémentale":
            script += """-- Backup incrémental quotidien
RUN {
  ALLOCATE CHANNEL ch1 DEVICE TYPE DISK FORMAT '{strategy['storage_location']}incr_%T_%U.bkp';
  BACKUP INCREMENTAL LEVEL 1 DATABASE PLUS ARCHIVELOG DELETE INPUT;
  RELEASE CHANNEL ch1;
}

"""

        script += """-- Validation et nettoyage
RESTORE DATABASE VALIDATE;
DELETE NOPROMPT OBSOLETE;

-- Rapport de backup
LIST BACKUP SUMMARY;
"""
        return script

    def _generate_native_script(self, strategy: Dict, db_metrics: Dict) -> str:
        """Génère script natif Oracle pour environnements moins critiques"""
        script = f"""-- ============================================
-- SCRIPT NATIVE ORACLE: {strategy['name']}
-- Généré: {datetime.now().strftime('%Y-%m-%d %H:%M')}
-- Base: {db_metrics['size_gb']} GB - {db_metrics['criticality']} CRITICALITY
-- ============================================

-- Création répertoire backup
CREATE OR REPLACE DIRECTORY BACKUP_DIR AS '{strategy['storage_location']}';

-- Grant permissions
GRANT READ, WRITE ON DIRECTORY BACKUP_DIR TO SYSTEM;

-- Script export Data Pump complet
expdp system/salmaoracle DIRECTORY=BACKUP_DIR \\
  DUMPFILE=full_backup_{datetime.now().strftime('%Y%m%d')}.dmp \\
  LOGFILE=full_backup_{datetime.now().strftime('%Y%m%d')}.log \\
  FULL=Y \\
  COMPRESSION=ALL

"""

        if strategy['frequency'] == "quotidienne":
            script += """-- Export incrémental quotidien (schemas modifiés)
expdp system/salmaoracle DIRECTORY=BACKUP_DIR \\
  DUMPFILE=incr_backup_%U.dmp \\
  LOGFILE=incr_backup.log \\
  SCHEMAS=HR,SALES,INVENTORY \\
  COMPRESSION=ALL

"""

        script += """-- Script de restauration d'urgence
-- ============================================
-- RESTAURATION EN CAS DE SINISTRE
-- ============================================

-- 1. Arrêter la base
SHUTDOWN IMMEDIATE;

-- 2. Démarrer en mode nomount
STARTUP NOMOUNT;

-- 3. Restaurer depuis export
impdp system/salmaoracle DIRECTORY=BACKUP_DIR \\
  DUMPFILE=full_backup_*.dmp \\
  LOGFILE=restore.log \\
  FULL=Y

-- 4. Ouvrir la base
ALTER DATABASE OPEN;
"""
        return script
    
    def generate_recommendation(self, rpo: float, rto: float, budget: str) -> Dict:
        """Génère recommandation complète avec LLM"""

        if self.db_metrics:
            db_size = self.db_metrics['size_gb']
            txn_hour = self.db_metrics['transactions_per_hour']
            criticality = self.db_metrics['criticality']
            growth = self.db_metrics['daily_growth_gb']
        else:
            db_size, txn_hour, criticality, growth = 10.0, 1000, 'MEDIUM', 0.5

        strategy_key = self.select_strategy(rpo, rto, budget)
        strategy = self.BACKUP_STRATEGIES[strategy_key]
        costs = self.calculate_costs(strategy_key, db_size, growth)
        backup_script = self.generate_backup_script(strategy_key, {
            'size_gb': db_size,
            'transactions_per_hour': txn_hour,
            'criticality': criticality
        })

        # Utilisation LLM pour recommandations backup
        llm_recommendation = self.llm.generate(prompt=f"En tant qu'expert DBA ...")
        llm_frequency = self.llm.generate(prompt=f"Quelle est la meilleure fréquence ...")

        return {
            'timestamp': datetime.now().isoformat(),
            'input': {
                'rpo_hours': rpo,
                'rto_hours': rto,
                'budget': budget,
                'db_size_gb': db_size,
                'transactions_per_hour': txn_hour,
                'criticality': criticality
            },
            'strategy': {
                'key': strategy_key,
                'name': strategy['name'],
                'description': strategy['description'],
                'backup_type': strategy['backup_type'],
                'frequency': strategy['frequency'],
                'retention_days': strategy['retention_days'],
                'storage_location': strategy['storage_location'],
                'script_type': strategy['script_type']
            },
            'costs': costs,
            'backup_script': backup_script,
            'llm_recommendation': llm_recommendation,
            'llm_frequency_analysis': llm_frequency,
            'implementation_steps': self._get_implementation_steps(strategy_key)
        }

    def _get_llm_backup_recommendation(self, rpo: float, rto: float, budget: str, db_size: float, strategy: Dict) -> str:
        """Obtient recommandation LLM pour stratégie backup"""
        if not self.llm:
            return "LLM non disponible - recommandation basée sur règles métier"

        prompt = f"""En tant qu'expert DBA Oracle, recommande une stratégie de sauvegarde.

Contexte:
- Base de données: {db_size} GB
- RPO requis: {rpo} heures (perte de données maximale acceptable)
- RTO requis: {rto} heures (temps de restauration maximal)
- Budget: {budget}
- Stratégie proposée: {strategy['name']}

Explique pourquoi cette stratégie est optimale pour ces exigences.
Décris les avantages et risques potentiels.
Recommande des ajustements si nécessaire.

Réponse concise en français."""

        try:
            return self.llm.generate(prompt, max_tokens=400)
        except Exception as e:
            return f"Erreur LLM: {e}"

    def _get_llm_backup_frequency(self, strategy: Dict, db_size: float, txn_hour: int) -> str:
        """Obtient analyse LLM de la fréquence de backup"""
        if not self.llm:
            return "LLM non disponible"

        prompt = f"""Quelle est la meilleure fréquence de sauvegarde pour cette configuration ?

Configuration:
- Taille DB: {db_size} GB
- Transactions/heure: {txn_hour}
- Stratégie: {strategy['name']}
- Type backup: {strategy['backup_type']}

Analyse la fréquence proposée et suggère des optimisations.
Considère le volume de données et la criticité métier.

Réponse en français."""

        try:
            return self.llm.generate(prompt, max_tokens=300)
        except Exception as e:
            return f"Erreur LLM: {e}"

    def _get_implementation_steps(self, strategy_key: str) -> List[str]:
        """Étapes d'implémentation pour la stratégie"""
        base_steps = [
            "1. Créer les répertoires de stockage",
            "2. Configurer les permissions Oracle",
            "3. Tester la connectivité au stockage",
            "4. Programmer les jobs de backup",
            "5. Configurer la surveillance",
            "6. Effectuer un test de restauration"
        ]

        if "CRITICAL" in strategy_key:
            base_steps.insert(0, "0. Mettre en place la réplication Data Guard")
            base_steps.append("7. Configurer les alertes temps réel")

        return base_steps
    
    def save_report(self, report: Dict):
        """Sauvegarde rapport JSON + script backup"""
        Path("reports").mkdir(exist_ok=True)

        # JSON complet
        json_path = f"reports/backup_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Script backup (RMAN ou natif)
        script_extension = "rman" if report['strategy']['script_type'] == "RMAN" else "sql"
        script_path = f"reports/backup_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{script_extension}"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(report['backup_script'])

        print(f"\n💾 Fichiers sauvegardés:")
        print(f"   • {json_path}")
        print(f"   • {script_path}")


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║   MODULE 7 : Plans Sauvegarde Intelligents (CSV + LLM)     ║
╚══════════════════════════════════════════════════════════════╝
""")

    # Initialiser LLM Engine
    try:
        print("🤖 Initialisation LLM Engine...")
        llm_engine = LLMEngine()
        print("   ✅ LLM Engine initialisé avec succès")
    except Exception as e:
        print(f"   ❌ Erreur LLM: {e}")
        print("   ⚠️  Continuation sans LLM (recommandations basées sur règles métier)")
        llm_engine = None

    # Initialiser le recommandeur avec LLM
    recommender = OracleBackupRecommender(llm_engine=llm_engine)

    # Charger métriques depuis CSV
    db_metrics = recommender.load_metrics_from_csv()
    recommender.db_metrics = db_metrics

    # Questionnaire utilisateur
    user_reqs = recommender.ask_user_requirements()

    # Générer recommandation complète
    print("\n⚙️  Génération stratégie avec IA...\n")
    report = recommender.generate_recommendation(
        rpo=user_reqs['rpo_hours'],
        rto=user_reqs['rto_hours'],
        budget=user_reqs['budget_category']
    )

    # Afficher résultats
    print("="*70)
    print("📊 STRATÉGIE RECOMMANDÉE")
    print("="*70)
    print(f"\n🎯 Stratégie: {report['strategy']['name']}")
    print(f"   📝 Description: {report['strategy']['description']}")
    print(f"   🔄 Type: {report['strategy']['backup_type']} ({report['strategy']['frequency']})")
    print(f"   📅 Rétention: {report['strategy']['retention_days']} jours")
    print(f"   💾 Script: {report['strategy']['script_type']}")

    print(f"\n💰 Coûts estimés:")
    print(f"   • Stockage total: {report['costs']['total_storage_gb']} GB")
    print(f"   • Coût mensuel: {report['costs']['monthly_cost_eur']}€")
    print(f"   • Coût annuel: {report['costs']['annual_cost_eur']}€")

    if report['llm_recommendation']:
        print(f"\n🤖 Analyse IA - Recommandation:")
        print(f"   {report['llm_recommendation'][:400]}...")

    if report['llm_frequency_analysis']:
        print(f"\n⏰ Analyse IA - Fréquence:")
        print(f"   {report['llm_frequency_analysis'][:300]}...")

    print(f"\n📋 Étapes d'implémentation:")
    for step in report['implementation_steps'][:6]:  # Afficher 6 premières étapes
        print(f"   {step}")

    # Sauvegarder rapport complet
    recommender.save_report(report)

    print("\n✅ MODULE 7 TERMINÉ - Rapport sauvegardé dans /reports")


if __name__ == "__main__":
    main()