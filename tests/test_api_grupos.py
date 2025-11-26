"""Script para testar a API de grupos"""

import requests
import json

# URL base
BASE_URL = "http://127.0.0.1:5000"

print("🧪 Testando API de Grupos\n")

# Teste 1: GET sem user_id
print("📋 Teste 1: GET /autenticado/grupos?action=get")
response = requests.get(f"{BASE_URL}/autenticado/grupos?action=get")
print(f"Status: {response.status_code}")
data = response.json()
print(f"Success: {data.get('success')}")
print(f"Clientes: {len(data.get('clients', []))}")
print(f"Áreas: {len(data.get('areas', []))}")

if data.get('areas'):
    print("\n📍 Áreas retornadas:")
    for area in data['areas']:
        print(f"  - ID: {area['id']}, Nome: {area['group_name']}")
else:
    print("  ⚠️ Nenhuma área retornada")

# Teste 2: GET com user_id=anon
print("\n📋 Teste 2: GET /autenticado/grupos?action=get&user_id=anon")
response = requests.get(f"{BASE_URL}/autenticado/grupos?action=get&user_id=anon")
print(f"Status: {response.status_code}")
data = response.json()
print(f"Success: {data.get('success')}")
print(f"Clientes: {len(data.get('clients', []))}")
print(f"Áreas: {len(data.get('areas', []))}")

if data.get('areas'):
    print("\n📍 Áreas retornadas:")
    for area in data['areas']:
        print(f"  - ID: {area['id']}, Nome: {area['group_name']}")
        print(f"    GeoJSON: {json.dumps(area['geojson_data'], indent=2)[:200]}...")
else:
    print("  ⚠️ Nenhuma área retornada")

print("\n✅ Testes concluídos!")
