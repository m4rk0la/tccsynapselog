"""
Teste das rotas de RFM integradas
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app

app = create_app()

with app.test_client() as client:
    # 1. Testar login
    response = client.post('/login', data={
        'email': 'admin@synapselLog.com',
        'password': 'admin123'
    }, follow_redirects=True)
    
    print(f"✅ Login: {response.status_code}")
    
    # 2. Testar API de estatísticas
    response = client.get('/autenticado/scores/estatisticas')
    print(f"✅ API Stats: {response.status_code}")
    if response.status_code == 200:
        print(f"   Dados: {response.get_json()}")
    
    # 3. Testar API de segmento
    response = client.get('/autenticado/scores/segmento/VIP')
    print(f"✅ API Segmento: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"   Clientes VIP: {data['total']}")
    
    print("\n🎉 Testes concluídos!")