from query_optimizer import OracleQueryOptimizerLLM, initialize_llm  # Remplace 'ton_module' par le nom de ton fichier

if __name__ == "__main__":
    # Initialiser le LLM
    llm_engine = initialize_llm()
    if not llm_engine:
        print("❌ LLM non initialisé")
        exit(1)

    # Créer l'optimizer avec LLM
    optimizer = OracleQueryOptimizerLLM(llm_engine=llm_engine)

    # Charger les requêtes
    queries = optimizer.load_queries()
    if not queries:
        print("❌ Aucune requête à analyser")
        exit(1)

    # Analyser les requêtes avec LLM
    for query in queries:
        result = optimizer.analyze_query_conforme(query)
        print("\n===============================")
        print("SQL ID:", result['sql_id'])
        print("LLM utilisé:", result['llm_used'])
        print("Explication plan par LLM:\n", result['explication_plan'])
        print("Points coûteux par LLM:\n", result['points_couteux'])
        print("Recommandations LLM:")
        for rec in result['recommandations']:
            print("-", rec['description'])
        print("===============================\n")
