"""
Script para verificar dados de polígonos no banco
"""
import sqlite3
import os
import json

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'databases', 'synapselLog_polygon.db')
db_path = os.path.abspath(db_path)

print(f"📂 Banco de dados: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Busca todos os polígonos
    cursor.execute("SELECT * FROM polygon_data")
    rows = cursor.fetchall()
    
    # Pega nomes das colunas
    cursor.execute("PRAGMA table_info(polygon_data)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"\n📋 Colunas: {columns}")
    print(f"\n📊 Total de registros: {len(rows)}")
    
    if len(rows) > 0:
        print("\n" + "="*80)
        print("REGISTROS ENCONTRADOS:")
        print("="*80)
        
        for row in rows:
            print(f"\nID: {row[0]}")
            print(f"User ID: {row[1]}")
            print(f"Group Name: {row[2]}")
            
            # Parse geojson_data
            try:
                geojson = json.loads(row[3])
                coords = geojson.get('geometry', {}).get('coordinates', [])
                if coords and len(coords) > 0:
                    print(f"Coordenadas: {len(coords[0])} pontos")
                else:
                    print(f"Coordenadas: VAZIO ou inválido")
                print(f"GeoJSON (primeiros 100 chars): {row[3][:100]}...")
            except:
                print(f"GeoJSON: ERRO ao parsear - {row[3][:50]}...")
            
            print(f"Created At: {row[4]}")
            print(f"Max Clients Per Day: {row[5] if len(row) > 5 else 'N/A'}")
            print("-"*80)
    else:
        print("\n⚠️ Nenhum registro encontrado na tabela polygon_data!")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
