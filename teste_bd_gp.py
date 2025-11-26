"""Script para verificar grupos/áreas no banco de dados"""
import sqlite3
import json
from pathlib import Path

# Caminhos dos bancos
base_path = Path(__file__).parent.parent.parent / 'databases'
client_db = base_path / 'synapselLog_client_name.db'

print("=" * 60)
print("🔍 VERIFICANDO GRUPOS/ÁREAS NO BANCO")
print("=" * 60)

# Conectar ao banco de polígonos
conn = sqlite3.connect(client_db)
cursor = conn.cursor()

# Verificar estrutura da tabela
print("\n📋 Estrutura da tabela polygon_data:")
cursor.execute("PRAGMA table_info(polygon_data)")
columns = cursor.fetchall()
for col in columns:
    print(f"   - {col[1]} ({col[2]})")

# Buscar todos os registros
print("\n📊 Registros na tabela polygon_data:")
cursor.execute("SELECT id, user_id, name, color, max_clients_per_day, created_at FROM polygon_data ORDER BY id")
rows = cursor.fetchall()

if not rows:
    print("   ⚠️ Nenhum registro encontrado!")
else:
    for row in rows:
        print(f"\n   ID: {row[0]}")
        print(f"   User ID: {row[1]}")
        print(f"   Nome: {row[2]}")
        print(f"   Cor: {row[3]}")
        print(f"   Max Clientes/Dia: {row[4]}")
        print(f"   Criado em: {row[5]}")

# Buscar por user_id específico
print("\n" + "=" * 60)
print("🔍 Buscando grupos por user_id:")
for user_id in [1, 2, 3]:
    cursor.execute("SELECT COUNT(*) FROM polygon_data WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"   User ID {user_id}: {count} grupos")
        cursor.execute("SELECT id, name FROM polygon_data WHERE user_id = ?", (user_id,))
        grupos = cursor.fetchall()
        for grupo in grupos:
            print(f"      → Grupo {grupo[0]}: {grupo[1]}")

conn.close()

print("\n" + "=" * 60)
print("✅ Verificação concluída")
print("=" * 60)