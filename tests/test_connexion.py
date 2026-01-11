# test_connection.py
import oracledb
import os
import sys
from dotenv import load_dotenv

print("="*60)
print("DIAGNOSTIC CONNEXION ORACLE")
print("="*60)

# 1. Vérifier le fichier .env
load_dotenv()

print("\n📁 VARIABLES D'ENVIRONNEMENT:")
print(f"   ORACLE_USER: {os.getenv('ORACLE_USER')}")
print(f"   ORACLE_PASSWORD: {'*' * len(os.getenv('ORACLE_PASSWORD', ''))}")
print(f"   ORACLE_HOST: {os.getenv('ORACLE_HOST')}")
print(f"   ORACLE_PORT: {os.getenv('ORACLE_PORT')}")
print(f"   ORACLE_SERVICE: {os.getenv('ORACLE_SERVICE')}")

# 2. Vérifier si le module est installé
print("\n🔧 VÉRIFICATION MODULE ORACLEDB:")
try:
    print(f"   Version oracledb: {oracledb.__version__}")
    print("   ✅ Module oracledb OK")
except ImportError:
    print("   ❌ Module oracledb non installé")
    print("   Installez-le avec: pip install oracledb")
    sys.exit(1)

# 3. Tester la connexion
print("\n🔌 TEST DE CONNEXION...")
try:
    dsn = f"{os.getenv('ORACLE_HOST')}:{os.getenv('ORACLE_PORT')}/{os.getenv('ORACLE_SERVICE')}"
    print(f"   DSN: {dsn}")
    
    # Essayer avec thin mode
    print("   Mode Thin (par défaut)...")
    connection = oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=dsn
    )
    
    print("   ✅ Connexion réussie!")
    
    # Tester les requêtes simples
    cursor = connection.cursor()
    
    # Test 1: Version Oracle
    cursor.execute("SELECT * FROM v$version WHERE banner LIKE '%Oracle%'")
    version = cursor.fetchone()
    print(f"\n🗄️  VERSION ORACLE:")
    print(f"   {version[0]}")
    
    # Test 2: Utilisateur actuel
    cursor.execute("SELECT USER FROM dual")
    current_user = cursor.fetchone()
    print(f"\n👤 UTILISATEUR:")
    print(f"   {current_user[0]}")
    
    # Test 3: Tables existantes
    cursor.execute("""
        SELECT table_name, num_rows 
        FROM user_tables 
        WHERE table_name LIKE '%BIG%' 
        OR table_name LIKE '%CUSTOMER%'
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print(f"\n📊 TABLES EXISTANTES:")
    if tables:
        for table in tables:
            print(f"   • {table[0]} ({table[1] or 0} lignes)")
    else:
        print("   Aucune table de test trouvée")
    
    # Test 4: Privilèges
    cursor.execute("""
        SELECT privilege, admin_option 
        FROM user_sys_privs 
        WHERE privilege LIKE '%CREATE%'
        OR privilege LIKE '%DROP%'
    """)
    
    privileges = cursor.fetchall()
    print(f"\n🔐 PRIVILÈGES:")
    if privileges:
        for priv in privileges:
            print(f"   • {priv[0]} (admin: {priv[1]})")
    else:
        print("   Pas de privilèges CREATE/DROP")
    
    # Test 5: Vérifier si PROJET_DB a accès à V$SQL
    print(f"\n🔍 ACCÈS AUX VUES DE PERFORMANCE:")
    try:
        cursor.execute("SELECT COUNT(*) FROM v$sql WHERE parsing_schema_name = USER")
        count = cursor.fetchone()[0]
        print(f"   ✅ Accès à V$SQL: {count} requêtes dans le cache")
    except Exception as e:
        print(f"   ❌ Pas d'accès à V$SQL: {str(e)[:100]}")
        print("   Donnez les droits: GRANT SELECT ON v_$sql TO PROJET_DB;")
    
    cursor.close()
    connection.close()
    
    print("\n" + "="*60)
    print("✅ CONNEXION TESTÉE AVEC SUCCÈS")
    print("="*60)
    
except oracledb.DatabaseError as e:
    error, = e.args
    print(f"\n❌ ERREUR ORACLE:")
    print(f"   Code: {error.code}")
    print(f"   Message: {error.message}")
    print(f"   Contexte: {error.context}")
    
    # Suggestions de résolution
    print("\n💡 SOLUTIONS POSSIBLES:")
    
    if error.code == 12154:  # TNS
        print("   1. Vérifiez le nom du service (XEPDB1)")
        print("   2. Vérifiez que l'instance est en cours d'exécution")
        print("   3. Testez avec: tnsping XEPDB1")
        
    elif error.code == 12541:  # No listener
        print("   1. Démarrez le listener Oracle")
        print("   2. Vérifiez le port (1521)")
        
    elif error.code == 1017:  # Invalid credentials
        print("   1. Vérifiez le mot de passe")
        print("   2. L'utilisateur est-il verrouillé?")
        print("   3. Connectez-vous avec SYSTEM pour déverrouiller")
        
    elif error.code == 1031:  # Insufficient privileges
        print("   1. PROJET_DB n'a pas les droits nécessaires")
        print("   2. Connectez-vous en tant que SYSTEM et exécutez:")
        print("      GRANT CREATE SESSION TO PROJET_DB;")
        print("      GRANT CREATE TABLE TO PROJET_DB;")
        print("      GRANT UNLIMITED TABLESPACE TO PROJET_DB;")
        
except Exception as e:
    print(f"\n❌ ERREUR GÉNÉRALE: {e}")
    import traceback
    traceback.print_exc()

print("\nPour créer des requêtes lentes, exécutez:")
print("python src/creation_requetes.py")