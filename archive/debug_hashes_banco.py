"""
Script para debugar hashes entre ClientName e OrderHistory
"""

from app import create_app
from base.models import db, ClientName, OrderHistory

app = create_app()

with app.app_context():
    print("=" * 80)
    print("🔍 DEBUG: Comparando hashes entre ClientName e OrderHistory")
    print("=" * 80)
    
    # 1. Pega alguns clientes
    print("\n👥 CLIENTES NO BANCO:")
    print("-" * 80)
    clientes = ClientName.query.limit(10).all()
    
    for i, c in enumerate(clientes, 1):
        print(f"\n{i}. Nome: {c.name_client[:30]}...")
        print(f"   Hash: {c.hash_client}")
        print(f"   User ID: {c.user_id}")
        
        # Busca vendas com este hash
        vendas = OrderHistory.query.filter_by(
            hash_cliente=c.hash_client,
            user_id=c.user_id
        ).all()
        
        print(f"   ✅ Vendas encontradas: {len(vendas)}")
        
        if vendas:
            total_valor = sum(v.valor_total_pagamento or 0 for v in vendas)
            print(f"   💰 Valor total: R$ {total_valor:,.2f}")
    
    # 2. Pega algumas vendas
    print("\n\n📦 VENDAS NO BANCO:")
    print("-" * 80)
    vendas_sample = OrderHistory.query.limit(10).all()
    
    for i, v in enumerate(vendas_sample, 1):
        print(f"\n{i}. ID Único Cliente: {v.id_unico_cliente[:30]}...")
        print(f"   Hash Cliente: {v.hash_cliente}")
        print(f"   User ID: {v.user_id}")
        
        # Busca cliente com este hash
        cliente = ClientName.query.filter_by(
            hash_client=v.hash_cliente,
            user_id=v.user_id
        ).first()
        
        if cliente:
            print(f"   ✅ Cliente encontrado: {cliente.name_client[:30]}...")
        else:
            print(f"   ❌ CLIENTE NÃO ENCONTRADO!")
    
    # 3. Estatísticas gerais
    print("\n\n📊 ESTATÍSTICAS GERAIS:")
    print("-" * 80)
    
    total_clientes = ClientName.query.count()
    total_vendas = OrderHistory.query.count()
    
    print(f"Total de clientes: {total_clientes:,}")
    print(f"Total de vendas: {total_vendas:,}")
    
    # Hashes únicos
    hashes_clientes = set(c.hash_client for c in ClientName.query.all())
    hashes_vendas = set(v.hash_cliente for v in OrderHistory.query.all())
    
    print(f"\nHashes únicos em ClientName: {len(hashes_clientes):,}")
    print(f"Hashes únicos em OrderHistory: {len(hashes_vendas):,}")
    
    # Interseção
    matches = hashes_clientes.intersection(hashes_vendas)
    print(f"Hashes que fazem MATCH: {len(matches):,}")
    
    if len(matches) == 0:
        print("\n❌ PROBLEMA: Nenhum hash faz match!")
        print("\n🔍 COMPARAÇÃO DE VALORES:")
        print("-" * 80)
        
        # Mostra alguns valores originais
        print("\n📋 Valores em ClientName (name_client):")
        for c in ClientName.query.limit(5).all():
            print(f"  - {c.name_client} → {c.hash_client}")
        
        print("\n📋 Valores em OrderHistory (id_unico_cliente):")
        for v in OrderHistory.query.limit(5).all():
            print(f"  - {v.id_unico_cliente} → {v.hash_cliente}")
        
        # Verifica se os valores originais são iguais
        print("\n🧪 TESTE: Comparando valores ORIGINAIS:")
        cliente1 = ClientName.query.first()
        venda1 = OrderHistory.query.first()
        
        if cliente1 and venda1:
            print(f"ClientName.name_client: '{cliente1.name_client}'")
            print(f"OrderHistory.id_unico_cliente: '{venda1.id_unico_cliente}'")
            print(f"São iguais? {cliente1.name_client == venda1.id_unico_cliente}")
    else:
        print(f"\n✅ {len(matches):,} hashes fazem match!")
        percentual = (len(matches) / len(hashes_vendas)) * 100
        print(f"Cobertura: {percentual:.1f}% das vendas têm cliente correspondente")
    
    print("\n" + "=" * 80)
