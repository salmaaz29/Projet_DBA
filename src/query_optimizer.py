# -*- coding: utf-8 -*-
"""
MODULE 5 : Analyse d'Optimisation de Requêtes AVEC LLM - VERSION MODIFIÉE
✅ Analyse toutes les requêtes
✅ Utilise uniquement les prompts chargés dans le LLM
✅ Recommandations concrètes
✅ Gestion None pour object_name
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import re
import sys
import os

# Ajouter le chemin pour importer les autres modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.llm_engine import LLMEngine
    LLM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  LLMEngine non disponible: {e}")
    LLM_AVAILABLE = False

class OracleQueryOptimizerLLM:
    """Optimiseur Oracle avec intégration LLM"""
    
    def __init__(self, llm_engine: Optional[LLMEngine] = None):
        self.llm = llm_engine
        
        # Charger les prompts depuis le LLM (on ne fournit plus de prompts par défaut)
        if self.llm and hasattr(self.llm, 'prompts'):
            self.prompts = self.llm.prompts
        else:
            self.prompts = {}

    def load_queries(self) -> List[Dict]:
        """Charge les requêtes depuis JSON ou CSV"""
        json_path = Path("data/queries_for_optimization.json")
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                queries_data = json.load(f)
            queries = []
            for q in queries_data:
                queries.append({
                    'sql_id': q.get('sql_id', 'UNKNOWN'),
                    'sql_text': q.get('sql_text', ''),
                    'sql_fulltext': q.get('sql_fulltext', q.get('sql_text', '')),
                    'basic_metrics': q.get('basic_metrics', {}),
                    'execution_plan': q.get('execution_plan', []),
                    'objects_involved': q.get('objects_involved', []),
                    'existing_indexes': q.get('existing_indexes', [])
                })
            print(f"✅ {len(queries)} requêtes chargées depuis JSON")
            return queries
        
        csv_path = Path("data/slow_queries_detailed.csv")
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            queries = []
            for idx, row in df.iterrows():
                queries.append({
                    'sql_id': row.get('SQL_ID', f'Q{idx+1}'),
                    'sql_text': row.get('SQL_FULLTEXT_SHORT', ''),
                    'basic_metrics': {
                        'elapsed_sec': row.get('ELAPSED_SEC', 0),
                        'cpu_sec': row.get('CPU_SEC', 0),
                        'rows_processed': row.get('ROWS_PROCESSED', 0),
                        'executions': row.get('EXECUTIONS', 0),
                        'disk_reads': row.get('DISK_READS', 0),
                        'buffer_gets': row.get('BUFFER_GETS', 0),
                        'optimizer_cost': row.get('OPTIMIZER_COST', 0)
                    }
                })
            print(f"✅ {len(queries)} requêtes chargées depuis CSV")
            return queries

        print("❌ Aucun fichier de données trouvé")
        return []

    def convert_plan_to_text(self, plan_data: List[Dict]) -> str:
        """Convertit le plan en texte lisible"""
        if not plan_data:
            return "Aucun plan disponible"
        
        lines = ["📋 PLAN D'EXÉCUTION :"]
        lines.append("═" * 60)
        lines.append("| ID | OPÉRATION | OBJET | COÛT | LIGNES |")
        lines.append("|----|-----------|-------|------|--------|")
        for step in plan_data:
            id_val = step.get('id', 0)
            operation = step.get('operation', 'N/A')
            options = step.get('options', '')
            object_name = str(step.get('object_name') or '')
            cost = step.get('cost', 0)
            cardinality = step.get('cardinality', 0)
            op_text = f"{operation} {options}".strip()
            op_display = (op_text[:20] + '...') if len(op_text) > 20 else op_text.ljust(20)
            obj_display = (object_name[:15] + '...') if len(object_name) > 15 else object_name.ljust(15)
            cost_str = str(cost)
            cardinality_str = str(cardinality)
            lines.append(f"| {id_val:2} | {op_display:20} | {obj_display:15} | {cost_str:>4} | {cardinality_str:>6} |")
        lines.append("═" * 60)
        return "\n".join(lines)

    def analyze_query_conforme(self, query_data: Dict) -> Dict:
        """Analyse complète d'une requête utilisant les méthodes LLM"""
        sql_id = query_data.get('sql_id', 'UNKNOWN')
        sql_text = query_data.get('sql_text', '')
        sql_fulltext = query_data.get('sql_fulltext', sql_text)
        metrics = query_data.get('basic_metrics', {})
        plan_data = query_data.get('execution_plan', [])
        plan_text = self.convert_plan_to_text(plan_data)

        if self.llm:
            try:
                # Utiliser les méthodes spécialisées du LLM
                explication_plan = self.llm.explain_plan(plan_data)
                costly_operations = self.llm.identify_costly_operations(plan_data)
                suggestions_text = self.llm.suggest_optimizations(sql_text, plan_data)

                # Parser les suggestions en recommandations structurées
                recommandations = self._parse_suggestions_to_recommendations(suggestions_text)

                # Estimer les métriques avant/après
                current_cost = metrics.get('optimizer_cost', 100)
                current_time = metrics.get('elapsed_sec', 1.0)
                reduction_pct = len(recommandations) * 15  # Estimation basée sur le nombre de recommandations
                new_cost = max(1, int(current_cost * (1 - reduction_pct / 100)))
                new_time = max(0.1, current_time * (1 - reduction_pct / 100))

                return {
                    'sql_id': sql_id,
                    'sql_query': sql_text,
                    'timestamp': datetime.now().isoformat(),
                    'sql_full': sql_fulltext[:1000],
                    'explication_plan': explication_plan,
                    'points_couteux': costly_operations,
                    'recommandations': recommandations,
                    'metriques_avant_apres': {
                        'cout_avant': current_cost,
                        'cout_apres_estime': new_cost,
                        'temps_avant': current_time,
                        'temps_apres_estime': new_time,
                        'reduction_estimee': f"{reduction_pct}%"
                    },
                    'metrics': metrics,
                    'plan_text': plan_text,
                    'llm_used': True
                }
            except Exception as e:
                print(f"❌ LLM methods failed: {e} - fallback manuel")
                return self._analyze_classic_fallback(sql_id, sql_text, sql_fulltext, metrics, plan_data)
        else:
            return self._analyze_classic_fallback(sql_id, sql_text, sql_fulltext, metrics, plan_data)

    def _analyze_classic_fallback(self, sql_id, sql_text, sql_fulltext, metrics, plan_data):
        """Fallback manuel si LLM indisponible"""
        plan_text = self.convert_plan_to_text(plan_data)
        problems = self._identify_problems_auto(sql_text, plan_text, metrics)
        recommendations = self._generate_recommendations_auto(sql_text, problems)
        current_cost = metrics.get('optimizer_cost', 100)
        reduction = self._estimate_reduction(problems, recommendations)
        new_cost = max(1, int(current_cost * (1 - reduction / 100)))

        return {
            'sql_id': sql_id,
            'sql_query': sql_text,
            'timestamp': datetime.now().isoformat(),
            'sql_full': sql_fulltext[:1000],
            'explication_plan': "Analyse manuelle disponible",
            'points_couteux': "Analyse manuelle disponible",
            'recommandations': recommendations[:3],
            'metrique_avant_apres': {
                'avant_cout': current_cost,
                'apres_cout_estimee': new_cost,
                'reduction_estimee': f"{reduction:.1f}%"
            },
            'metrics': metrics,
            'problems': problems,
            'plan_text': plan_text,
            'llm_used': False
        }

    # Fonctions utilitaires
    def _identify_problems_auto(self, sql_text, plan_text, metrics):
        problems = []
        sql_upper = sql_text.upper()
        plan_upper = plan_text.upper()
        if 'SELECT *' in sql_upper:
            problems.append("SELECT * - récupère toutes les colonnes")
        if 'FULL' in plan_upper and 'SCAN' in plan_upper:
            problems.append("FULL TABLE SCAN détecté")
        cost = metrics.get('optimizer_cost', 0)
        if cost > 1000:
            problems.append(f"Coût optimiseur élevé ({cost})")
        return problems[:5]

    def _generate_recommendations_auto(self, sql_text, problems):
        recommendations = []
        tables = re.findall(r'FROM\s+(\w+)', sql_text.upper())
        for problem in problems:
            if 'SELECT *' in problem and tables:
                table = tables[0]
                recommendations.append({
                    'type': 'REECRITURE',
                    'description': f'Remplacer SELECT * par colonnes spécifiques sur {table}',
                    'sql': f"SELECT col1, col2 FROM {table}",
                    'gain': '30-50%'
                })
        if len(recommendations) < 2 and tables:
            table = tables[0]
            recommendations.append({
                'type': 'STATISTIQUES',
                'description': f'Mettre à jour les statistiques sur {table}',
                'sql': f"EXEC DBMS_STATS.GATHER_TABLE_STATS(USER, '{table}');",
                'gain': '10-20%'
            })
        return recommendations[:3]

    def _estimate_reduction(self, problems, recommendations):
        base = len(problems) * 15
        adj = len(recommendations) * 10
        return min(85, (base + adj) / 2)

    def _parse_suggestions_to_recommendations(self, suggestions_text: str) -> List[Dict]:
        """Parse les suggestions textuelles en recommandations structurées"""
        recommandations = []

        if not suggestions_text or suggestions_text.startswith("Error"):
            return recommandations

        # Diviser les suggestions en lignes
        lines = suggestions_text.split('\n')
        current_rec = None
        rec_id = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Détecter le début d'une nouvelle recommandation
            if any(keyword in line.upper() for keyword in ['INDEX', 'REECRITURE', 'HINT', 'STATISTIQUES', 'CREATE', 'ADD', 'MODIFY']):
                # Sauvegarder la précédente si elle existe
                if current_rec:
                    recommandations.append(current_rec)

                # Déterminer le type
                if 'INDEX' in line.upper() or 'CREATE INDEX' in line.upper():
                    rec_type = 'INDEX'
                elif 'REECRITURE' in line.upper() or 'REWRITE' in line.upper() or 'SELECT' in line.upper():
                    rec_type = 'REECRITURE'
                elif 'HINT' in line.upper():
                    rec_type = 'HINT'
                elif 'STATISTIQUES' in line.upper() or 'STATISTICS' in line.upper() or 'GATHER' in line.upper():
                    rec_type = 'STATISTIQUES'
                else:
                    rec_type = 'REECRITURE'

                # Extraire la commande SQL si présente
                sql_command = ""
                if 'CREATE' in line.upper() or 'EXEC' in line.upper() or 'ALTER' in line.upper():
                    sql_command = line
                elif 'SELECT' in line.upper():
                    sql_command = line

                current_rec = {
                    'id': rec_id,
                    'type': rec_type,
                    'description': line,
                    'sql_command': sql_command,
                    'gain_estime': '20-40%'  # Valeur par défaut
                }
                rec_id += 1

            elif current_rec:
                # Ajouter à la description ou commande existante
                if not current_rec['sql_command'] and ('CREATE' in line.upper() or 'EXEC' in line.upper()):
                    current_rec['sql_command'] = line
                else:
                    current_rec['description'] += f" {line}"

        # Ajouter la dernière recommandation
        if current_rec:
            recommandations.append(current_rec)

        # Limiter à 3 recommandations maximum
        return recommandations[:3]


def initialize_llm() -> Optional[LLMEngine]:
    """Initialise LLMEngine correctement (sans rag_setup ni default_model)"""
    if not LLM_AVAILABLE:
        print("⚠️  LLMEngine non disponible")
        return None
    try:
        llm_engine = LLMEngine()  # utilisation par défaut avec api_key env et prompts.yaml
        return llm_engine
    except Exception as e:
        print(f"❌ Échec initialisation LLMEngine: {e}")
        return None


def main():
    print("\n🔧 Initialisation LLMEngine...")
    llm_engine = initialize_llm()
    optimizer = OracleQueryOptimizerLLM(llm_engine=llm_engine)

    print("\n📥 Chargement des requêtes...")
    queries = optimizer.load_queries()
    if not queries:
        print("❌ Aucune requête à analyser")
        return

    print(f"✅ {len(queries)} requêtes chargées")
    results = []

    for i, query in enumerate(queries, 1):
        print(f"\n📊 REQUÊTE {i}/{len(queries)}: {query.get('sql_id')}")
        try:
            result = optimizer.analyze_query_conforme(query)
            results.append(result)
            print(f"✓ Analyse terminée - LLM utilisé: {result['llm_used']}")
            # Sauvegarder rapport JSON
            report_file = f"data/rapport_llm_{result['sql_id']}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"💾 Rapport sauvegardé: {report_file}")
        except Exception as e:
            print(f"❌ Erreur analyse requête: {e}")


if __name__ == "__main__":
    main()
