"""
Script para investigar por que os hashes não estão fazendo match
"""

from app import create_app
from base.models import db, OrderHistory, ClientName
from base.utils import generate_client_hash
import hashlib

app = create_app()

with app.app_context():
    print("=" * 80)
    print("🔍 INVESTIGAÇÃO: Por que os hashes não fazem match?")
    print("=" * 80)
    
    # 1. Pega uma venda de exemplo
    print("\n📦 EXEMPLO DE VENDA:")
    print("-" * 80)
    venda = OrderHistory.query.first()
    
    if not venda:
        print("❌ Nenhuma venda encontrada!")
        exit()
    
    print(f"ID Pedido: {venda.id_pedido}")
    print(f"ID Único Cliente (usado para gerar hash): {venda.id_unico_cliente}")
    print(f"Hash armazenado no banco: {venda.hash_cliente}")
    
    # 2. Regenera o hash usando a função centralizada
    print("\n🔄 REGENERANDO HASH:")
    print("-" * 80)
    hash_regenerado = generate_client_hash(venda.id_unico_cliente)
    print(f"Hash regenerado: {hash_regenerado}")
    print(f"Match? {hash_regenerado == venda.hash_cliente}")
    
    # 3. Pega um cliente de exemplo
    print("\n👤 EXEMPLO DE CLIENTE:")
    print("-" * 80)
    cliente = ClientName.query.first()
    
    if not cliente:
        print("❌ Nenhum cliente encontrado!")
        exit()
    
    print(f"Nome do Cliente: {cliente.name_client}")
    print(f"Hash armazenado: {cliente.hash_client}")
    
    # 4. Tenta gerar hash do nome do cliente
    print("\n🔄 GERANDO HASH DO NOME DO CLIENTE:")
    print("-" * 80)
    hash_do_nome = generate_client_hash(cliente.name_client)
    print(f"Hash do nome: {hash_do_nome}")
    print(f"Match com hash do banco? {hash_do_nome == cliente.hash_client}")
    
    # 5. Análise do problema
    print("\n🧐 ANÁLISE:")
    print("-" * 80)
    print("VENDAS:")
    print(f"  - Hash é gerado de: id_unico_cliente (exemplo: '{venda.id_unico_cliente}')")
    print(f"  - Valor do hash: {venda.hash_cliente}")
    
    print("\nCLIENTES:")
    print(f"  - Hash é gerado de: Nome (exemplo: '{cliente.name_client}')")
    print(f"  - Valor do hash: {cliente.hash_client}")
    
    print("\n⚠️  PROBLEMA IDENTIFICADO:")
    print("  As vendas usam 'id_unico_cliente' para gerar hash")
    print("  Os clientes usam 'Nome' para gerar hash")
    print("  Esses valores são COMPLETAMENTE DIFERENTES!")
    print("  Por isso os hashes NUNCA vão fazer match!")
    
    # 6. Busca se existe algum campo em comum
    print("\n🔍 BUSCANDO CAMPO EM COMUM:")
    print("-" * 80)
    
    # Verifica se o id_unico_cliente da venda existe como nome em ClientName
    cliente_por_id = ClientName.query.filter_by(name_client=venda.id_unico_cliente).first()
    if cliente_por_id:
        print(f"✅ Encontrado cliente com nome = id_unico_cliente da venda!")
        print(f"   Nome: {cliente_por_id.name_client}")
        print(f"   Hash: {cliente_por_id.hash_client}")
    else:
        print(f"❌ NÃO existe cliente com nome = '{venda.id_unico_cliente}'")
    
    # 7. Mostra alguns id_cliente vs id_unico_cliente
    print("\n📊 AMOSTRA DE IDs NAS VENDAS:")
    print("-" * 80)
    vendas_sample = OrderHistory.query.limit(5).all()
    for i, v in enumerate(vendas_sample, 1):
        print(f"{i}. id_cliente: {v.id_cliente}")
        print(f"   id_unico_cliente: {v.id_unico_cliente}")
        print(f"   hash_cliente: {v.hash_cliente}")
        print()
    
    # 8. Verifica se algum desses IDs existe em ClientName
    print("🔍 VERIFICANDO SE ESSES IDs EXISTEM EM ClientName:")
    print("-" * 80)
    
    for v in vendas_sample:
        # Tenta com hash do id_cliente
        hash_id_cliente = generate_client_hash(v.id_cliente)
        cliente_match = ClientName.query.filter_by(hash_client=hash_id_cliente).first()
        
        if cliente_match:
            print(f"✅ MATCH ENCONTRADO!")
            print(f"   id_cliente da venda: {v.id_cliente}")
            print(f"   Nome do cliente: {cliente_match.name_client}")
            print(f"   Hash: {hash_id_cliente}")
            break
        
        # Tenta com hash do id_unico_cliente
        hash_id_unico = generate_client_hash(v.id_unico_cliente)
        cliente_match2 = ClientName.query.filter_by(hash_client=hash_id_unico).first()
        
        if cliente_match2:
            print(f"✅ MATCH ENCONTRADO!")
            print(f"   id_unico_cliente da venda: {v.id_unico_cliente}")
            print(f"   Nome do cliente: {cliente_match2.name_client}")
            print(f"   Hash: {hash_id_unico}")
            break
    else:
        print("❌ NENHUM MATCH ENCONTRADO com id_cliente ou id_unico_cliente")
    
    print("\n" + "=" * 80)
    print("💡 SOLUÇÃO SUGERIDA:")
    print("=" * 80)
    print("Os clientes foram importados usando o NOME como identificador.")
    print("As vendas foram importadas usando id_unico_cliente como identificador.")
    print()
    print("Para fazer match, precisamos:")
    print("1. Importar os clientes novamente usando id_unico_cliente OU")
    print("2. Ter uma tabela de mapeamento: id_unico_cliente → hash_cliente OU")
    print("3. Adicionar o campo id_unico_cliente na tabela ClientName")
    print("=" * 80)
