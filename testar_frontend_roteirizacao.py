"""
Teste completo do fluxo de carregamento de grupos na página de roteirização
"""
import requests
from requests.auth import HTTPBasicAuth

# Configuração
BASE_URL = 'http://127.0.0.1:5000'
USER_ID = 2

def test_grupos_endpoint():
    """Testa endpoint de grupos para roteirização"""
    print("\n" + "="*60)
    print("TESTE 1: Endpoint de grupos para roteirização")
    print("="*60)
    
    url = f"{BASE_URL}/autenticado/roteirizacao/grupos"
    
    try:
        # Criar sessão para manter cookies
        session = requests.Session()
        
        # Fazer request GET
        response = session.get(url)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success')}")
            print(f"✅ Total de grupos: {data.get('total')}")
            
            grupos = data.get('grupos', [])
            for i, grupo in enumerate(grupos, 1):
                print(f"\n📍 Grupo {i}:")
                print(f"   - ID: {grupo.get('id')}")
                print(f"   - Nome: {grupo.get('name')}")
                print(f"   - Coordenadas: {len(grupo.get('coordinates', []))} pontos")
                
                # Mostrar primeiras 2 coordenadas
                coords = grupo.get('coordinates', [])
                if coords:
                    print(f"   - Primeira coord: {coords[0]}")
                    if len(coords) > 1:
                        print(f"   - Segunda coord: {coords[1]}")
        else:
            print(f"❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_clientes_endpoint():
    """Testa endpoint de clientes"""
    print("\n" + "="*60)
    print("TESTE 2: Endpoint de clientes")
    print("="*60)
    
    url = f"{BASE_URL}/autenticado/grupos?action=get&user_id={USER_ID}"
    
    try:
        session = requests.Session()
        response = session.get(url)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success')}")
            
            clients = data.get('clients', [])
            print(f"✅ Total de clientes: {len(clients)}")
            
            # Contar pontos totais
            total_points = sum(len(c.get('points', [])) for c in clients)
            print(f"✅ Total de pontos: {total_points}")
            
            if clients:
                print(f"\n👤 Primeiro cliente:")
                print(f"   - Nome: {clients[0].get('name_client')}")
                print(f"   - Hash: {clients[0].get('hash_client')}")
                print(f"   - Pontos: {len(clients[0].get('points', []))}")
                
        else:
            print(f"❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_page_load():
    """Testa se a página carrega corretamente"""
    print("\n" + "="*60)
    print("TESTE 3: Carregamento da página")
    print("="*60)
    
    url = f"{BASE_URL}/autenticado/roteirizacao"
    
    try:
        session = requests.Session()
        response = session.get(url)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            html = response.text
            
            # Verificar elementos chave
            checks = [
                ('grupos-grid' in html, 'Elemento grupos-grid presente'),
                ('carregarGrupos' in html, 'Função carregarGrupos presente'),
                ('renderizarGrupos' in html, 'Função renderizarGrupos presente'),
                ('contarClientesPorGrupo' in html, 'Função contarClientesPorGrupo presente'),
                ('DOMContentLoaded' in html, 'Event listener DOMContentLoaded presente'),
            ]
            
            for check, msg in checks:
                status = "✅" if check else "❌"
                print(f"{status} {msg}")
                
        else:
            print(f"❌ Erro ao carregar página: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == '__main__':
    print("\n🧪 TESTANDO FLUXO COMPLETO DE ROTEIRIZAÇÃO")
    print("Certifique-se de que o servidor Flask está rodando!")
    print(f"Testando com USER_ID: {USER_ID}\n")
    
    test_grupos_endpoint()
    test_clientes_endpoint()
    test_page_load()
    
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    print("Se todos os testes passaram, o problema pode estar:")
    print("1. Na sessão do usuário (não está logado)")
    print("2. No JavaScript do navegador (verificar console)")
    print("3. Na renderização do HTML (verificar elementos no DevTools)")
    print("\nPróximos passos:")
    print("- Abrir http://127.0.0.1:5000/autenticado/roteirizacao")
    print("- Abrir DevTools (F12)")
    print("- Ver console.log para mensagens de erro")
    print("- Verificar Network tab para ver se APIs estão sendo chamadas")
