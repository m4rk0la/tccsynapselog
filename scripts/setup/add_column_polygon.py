"""
Script para adicionar coluna max_clients_per_day na tabela polygon_data
"""
import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'databases', 'synapselLog_polygon.db')
db_path = os.path.abspath(db_path)

print(f"📂 Banco de dados: {db_path}")
print(f"✓ Banco existe: {os.path.exists(db_path)}")

try:
    # Conecta ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifica tabelas existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n📊 Tabelas encontradas: {tables}")
    
    if 'polygon_data' not in tables:
        print("\n⚠️ Tabela polygon_data não existe! Criando...")
        
        # Cria a tabela
        cursor.execute("""
            CREATE TABLE polygon_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_name VARCHAR(100),
                geojson_data TEXT NOT NULL,
                max_clients_per_day INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ Tabela polygon_data criada com sucesso!")
    else:
        # Verifica se a coluna já existe
        cursor.execute("PRAGMA table_info(polygon_data)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"\n📋 Colunas existentes: {columns}")
        
        if 'max_clients_per_day' in columns:
            print("\n✓ Coluna max_clients_per_day já existe!")
        else:
            print("\n➕ Adicionando coluna max_clients_per_day...")
            cursor.execute("ALTER TABLE polygon_data ADD COLUMN max_clients_per_day INTEGER")
            conn.commit()
            print("✅ Coluna adicionada com sucesso!")
        
        # Verifica novamente
        cursor.execute("PRAGMA table_info(polygon_data)")
        columns_after = [row[1] for row in cursor.fetchall()]
        print(f"\n📋 Colunas após modificação: {columns_after}")
    
    # Conta registros
    cursor.execute("SELECT COUNT(*) FROM polygon_data")
    count = cursor.fetchone()[0]
    print(f"\n📊 Total de registros na tabela: {count}")
    
    conn.close()
    print("\n✅ Script executado com sucesso!")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
