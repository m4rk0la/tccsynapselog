"""
Script para testar a rota de grupos da roteirização
"""
import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app
import json

def testar_rota():
    app = create_app()
    
    with app.test_client() as client:
        # Simular login com user_id = 2
        with client.session_transaction() as sess:
            sess['user_id'] = 2
        
        print("=" * 60)
        print("🧪 TESTANDO: /autenticado/roteirizacao/grupos")
        print("=" * 60)
        print(f"User ID na sessão: 2\n")
        
        # Fazer requisição
        response = client.get('/autenticado/roteirizacao/grupos')
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 Content-Type: {response.content_type}\n")
        
        if response.status_code == 200:
            data = response.get_json()
            
            print("✅ RESPOSTA RECEBIDA:")
            print(f"   success: {data.get('success')}")
            print(f"   total: {data.get('total')}")
            print(f"   message: {data.get('message', 'N/A')}\n")
            
            grupos = data.get('grupos', [])
            print(f"📊 GRUPOS ENCONTRADOS: {len(grupos)}\n")
            
            if grupos:
                for i, grupo in enumerate(grupos, 1):
                    print(f"   {i}. ID: {grupo['id']}")
                    print(f"      Nome: {grupo['name']}")
                    print(f"      Coordenadas: {len(grupo['coordinates'])} pontos")
                    print(f"      Criado em: {grupo.get('created_at', 'N/A')}")
                    print()
            else:
                print("   ⚠️ Nenhum grupo retornado")
                
        else:
            print(f"❌ ERRO NA REQUISIÇÃO:")
            try:
                error_data = response.get_json()
                print(f"   {json.dumps(error_data, indent=2)}")
            except:
                print(f"   {response.get_data(as_text=True)}")
        
        print("=" * 60)

if __name__ == '__main__':
    testar_rota()
