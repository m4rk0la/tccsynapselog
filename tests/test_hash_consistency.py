"""
Script de teste para validar consistência de hashes entre ETLs

Este script testa se a função generate_client_hash() gera os mesmos hashes
para os mesmos identificadores, garantindo consistência entre:
- ETL de Clientes
- ETL de Histórico de Vendas
- Sistema de Roteirização
"""

from base.utils import generate_client_hash

def testar_consistencia_hash():
    """Testa se os hashes são gerados de forma consistente"""
    
    print("="*80)
    print("🔐 TESTE DE CONSISTÊNCIA DE HASH")
    print("="*80)
    
    # Casos de teste
    testes = [
        "Cliente ABC Ltda",
        "cliente abc ltda",  # Minúsculas (deve ser igual ao anterior)
        "  Cliente ABC Ltda  ",  # Com espaços (deve ser igual ao primeiro)
        "12345678900",
        "João da Silva",
        "MARIA SANTOS",
        "maria santos",  # Deve ser igual ao anterior
        "Empresa XYZ S.A.",
    ]
    
    print("\n📋 Testando geração de hash:")
    print("-" * 80)
    
    resultados = {}
    for identificador in testes:
        hash_gerado = generate_client_hash(identificador)
        resultados[identificador] = hash_gerado
        print(f"'{identificador}'")
        print(f"  → {hash_gerado}\n")
    
    # Validar normalização
    print("\n✅ VALIDAÇÃO DE NORMALIZAÇÃO:")
    print("-" * 80)
    
    # Teste 1: Case-insensitive
    hash1 = generate_client_hash("Cliente ABC Ltda")
    hash2 = generate_client_hash("cliente abc ltda")
    hash3 = generate_client_hash("CLIENTE ABC LTDA")
    
    if hash1 == hash2 == hash3:
        print("✅ Case-insensitive: OK")
        print(f"   'Cliente ABC Ltda' = 'cliente abc ltda' = 'CLIENTE ABC LTDA'")
        print(f"   Todos geraram: {hash1}")
    else:
        print("❌ Case-insensitive: FALHOU")
        print(f"   Hash 1: {hash1}")
        print(f"   Hash 2: {hash2}")
        print(f"   Hash 3: {hash3}")
    
    # Teste 2: Trim de espaços
    hash4 = generate_client_hash("Cliente ABC Ltda")
    hash5 = generate_client_hash("  Cliente ABC Ltda  ")
    hash6 = generate_client_hash("Cliente ABC Ltda   ")
    
    if hash4 == hash5 == hash6:
        print("\n✅ Trim de espaços: OK")
        print(f"   'Cliente ABC Ltda' = '  Cliente ABC Ltda  '")
        print(f"   Todos geraram: {hash4}")
    else:
        print("\n❌ Trim de espaços: FALHOU")
        print(f"   Hash sem espaços: {hash4}")
        print(f"   Hash com espaços: {hash5}")
    
    # Teste 3: Diferentes identificadores geram hashes diferentes
    hash7 = generate_client_hash("Cliente A")
    hash8 = generate_client_hash("Cliente B")
    
    if hash7 != hash8:
        print("\n✅ Unicidade: OK")
        print(f"   'Cliente A' ≠ 'Cliente B'")
        print(f"   {hash7} ≠ {hash8}")
    else:
        print("\n❌ Unicidade: FALHOU (colisão de hash!)")
    
    # Teste 4: Consistência em múltiplas execuções
    print("\n✅ TESTE DE CONSISTÊNCIA (10 execuções):")
    print("-" * 80)
    
    identificador_teste = "Empresa de Teste Ltda"
    hashes_gerados = [generate_client_hash(identificador_teste) for _ in range(10)]
    
    if len(set(hashes_gerados)) == 1:
        print(f"✅ 10 execuções geraram o mesmo hash:")
        print(f"   Identificador: '{identificador_teste}'")
        print(f"   Hash: {hashes_gerados[0]}")
    else:
        print("❌ Inconsistência detectada!")
        print(f"   Hashes únicos gerados: {len(set(hashes_gerados))}")
        for i, h in enumerate(set(hashes_gerados), 1):
            print(f"   Hash {i}: {h}")
    
    print("\n" + "="*80)
    print("✅ TESTE CONCLUÍDO")
    print("="*80)
    
    # Exemplo prático
    print("\n💡 EXEMPLO PRÁTICO:")
    print("-" * 80)
    print("Suponha que você tem:")
    print("  - ETL de Clientes: importa 'id_unico_cliente' = '12345'")
    print("  - ETL de Vendas: importa pedidos do cliente '12345'")
    print()
    print("Ambos usam: generate_client_hash('12345')")
    print(f"Resultado: {generate_client_hash('12345')}")
    print()
    print("✅ O hash será IDÊNTICO nos dois bancos!")
    print("✅ Você consegue fazer JOIN entre OrderHistory e ClientName pelo hash_cliente")
    print("="*80)


if __name__ == "__main__":
    testar_consistencia_hash()
