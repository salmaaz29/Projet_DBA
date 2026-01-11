# create_real_slow_queries_simple.py
import oracledb
import os
import time
from dotenv import load_dotenv

print("="*60)
print("CRÉATION DE REQUÊTES LENTES SIMPLIFIÉE")
print("="*60)

load_dotenv()

try:
    # Connexion
    print("\n1. Connexion à Oracle...")
    dsn = f"{os.getenv('ORACLE_HOST')}:{os.getenv('ORACLE_PORT')}/{os.getenv('ORACLE_SERVICE')}"
    connection = oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=dsn
    )
    cursor = connection.cursor()
    print("   ✅ Connecté")
    
    # 2. Créer une simple table de test
    print("\n2. Création d'une table de test...")
    
    # Supprimer si existe
    try:
        cursor.execute("DROP TABLE test_slow_queries")
        print("   Table existante supprimée")
    except:
        pass
    
    # Créer une table avec 10,000 lignes
    cursor.execute("""
        CREATE TABLE test_slow_queries AS
        SELECT 
            level as id,
            'Data_' || level as description,
            SYSDATE - DBMS_RANDOM.VALUE(0, 365) as date_value,
            DBMS_RANDOM.VALUE(100, 10000) as amount,
            DBMS_RANDOM.STRING('A', 50) as comments
        FROM dual
        CONNECT BY level <= 10000
    """)
    print("   ✅ Table créée avec 10,000 lignes")
    
    # 3. Exécuter 5 requêtes lentes simples
    print("\n3. Exécution de 5 requêtes lentes...")
    
    queries = [
        # 1. Scan complet
        "SELECT * FROM test_slow_queries WHERE amount > 5000",
        
        # 2. Avec LIKE (lent)
        "SELECT * FROM test_slow_queries WHERE description LIKE '%Data_1%'",
        
        # 3. Agrégation
        "SELECT COUNT(*), AVG(amount) FROM test_slow_queries",
        
        # 4. Tri
        "SELECT * FROM test_slow_queries ORDER BY comments",
        
        # 5. Sous-requête
        "SELECT * FROM test_slow_queries WHERE amount > (SELECT AVG(amount) FROM test_slow_queries)"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n   Requête {i}:")
        print(f"   {query[:60]}...")
        
        start = time.time()
        cursor.execute(query)
        rows = cursor.fetchall()
        elapsed = time.time() - start
        
        print(f"   ⏱️  Temps: {elapsed:.3f}s")
        print(f"   📊 Lignes: {len(rows)}")
        
        # Exécuter 2 fois de plus pour le cache
        for _ in range(2):
            cursor.execute(query)
            cursor.fetchall()
    
    # 4. Vérifier dans V$SQL
    print("\n4. Vérification dans le cache Oracle...")
    cursor.execute("""
        SELECT sql_id, sql_text, elapsed_time/1000000 as elapsed_sec
        FROM v$sql 
        WHERE parsing_schema_name = USER
        AND sql_text LIKE '%test_slow_queries%'
        AND ROWNUM <= 5
    """)
    
    results = cursor.fetchall()
    print(f"   ✅ {len(results)} requêtes trouvées dans V$SQL:")
    for sql_id, sql_text, elapsed in results:
        print(f"   • {sql_id[:13]}... ({elapsed:.3f}s)")
    
    # 
    print("   ✅ Table TEST_SLOW_QUERIES conservée pour l'extraction")
    
    cursor.close()
    connection.close()
    
    print("\n" + "="*60)
    print("✅ REQUÊTES CRÉÉES AVEC SUCCÈS")
    print("="*60)
    print("\nMaintenant exécutez:")
    print("python src/data_extractor.py")
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()