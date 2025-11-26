"""
Script de teste para verificar JOIN entre OrderHistory e ClientName
Valida se os hashes estão fazendo match corretamente
"""

from app import create_app
from base.models import db, OrderHistory, ClientName, LatLong
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("=" * 80)
    print("🔍 TESTE DE JOIN: OrderHistory ⟷ ClientName ⟷ LatLong")
    print("=" * 80)
    
    # 1. Contagem total de registros
    print("\n📊 CONTAGEM DE REGISTROS:")
    print("-" * 80)
    
    total_vendas = OrderHistory.query.count()
    total_clientes = ClientName.query.count()
    total_coordenadas = LatLong.query.count()
    
    print(f"Total de vendas (OrderHistory): {total_vendas:,}")
    print(f"Total de clientes (ClientName): {total_clientes:,}")
    print(f"Total de coordenadas (LatLong): {total_coordenadas:,}")
    
    # 2. Hashes únicos em cada tabela
    print("\n🔑 HASHES ÚNICOS:")
    print("-" * 80)
    
    hashes_vendas = db.session.query(
        func.count(func.distinct(OrderHistory.hash_cliente))
    ).scalar()
    
    hashes_clientes = db.session.query(
        func.count(func.distinct(ClientName.hash_client))
    ).scalar()
    
    hashes_latlong = db.session.query(
        func.count(func.distinct(LatLong.hash_client))
    ).scalar()
    
    print(f"Hashes únicos em OrderHistory: {hashes_vendas:,}")
    print(f"Hashes únicos em ClientName: {hashes_clientes:,}")
    print(f"Hashes únicos em LatLong: {hashes_latlong:,}")
    
    # 3. Verificar se há vendas
    if total_vendas == 0:
        print("\n⚠️  AVISO: Não há registros em OrderHistory!")
        print("    Execute o import de vendas primeiro.")
    else:
        # 4. Amostra de hashes de vendas
        print("\n📝 AMOSTRA DE HASHES EM OrderHistory (primeiros 10):")
        print("-" * 80)
        
        vendas_sample = OrderHistory.query.limit(10).all()
        for v in vendas_sample:
            print(f"  Hash: {v.hash_cliente[:16]}... | Cliente ID: {v.id_unico_cliente} | Pedido: {v.id_pedido}")
        
        # 5. Vendas e clientes: verificar correspondência manualmente
        print("\n✅ VERIFICAÇÃO DE CORRESPONDÊNCIA:")
        print("-" * 80)
        
        # Pega todos os hashes de vendas
        hashes_vendas_list = [v.hash_cliente for v in OrderHistory.query.limit(100).all()]
        hashes_vendas_set = set(hashes_vendas_list)
        
        # Pega todos os hashes de clientes
        hashes_clientes_list = [c.hash_client for c in ClientName.query.all()]
        hashes_clientes_set = set(hashes_clientes_list)
        
        # Encontra interseção
        hashes_match = hashes_vendas_set.intersection(hashes_clientes_set)
        
        print(f"  Hashes únicos em vendas (sample 100): {len(hashes_vendas_set)}")
        print(f"  Hashes únicos em clientes: {len(hashes_clientes_set)}")
        print(f"  Hashes que fazem MATCH: {len(hashes_match)}")
        
        if hashes_match:
            print(f"\n  ✅ EXEMPLO DE MATCHES (primeiros 5):")
            for i, h in enumerate(list(hashes_match)[:5], 1):
                # Busca cliente
                cliente = ClientName.query.filter_by(hash_client=h).first()
                # Conta vendas
                qtd_vendas = OrderHistory.query.filter_by(hash_cliente=h).count()
                print(f"    {i}. Hash: {h[:16]}...")
                print(f"       Cliente: {cliente.name_client if cliente else 'N/A'}")
                print(f"       Vendas: {qtd_vendas}")
        
        # Hashes que NÃO fazem match
        hashes_sem_match = hashes_vendas_set - hashes_clientes_set
        if hashes_sem_match:
            print(f"\n  ⚠️  Vendas SEM cliente correspondente: {len(hashes_sem_match)}")
            for i, h in enumerate(list(hashes_sem_match)[:3], 1):
                venda = OrderHistory.query.filter_by(hash_cliente=h).first()
                print(f"    {i}. Hash: {h[:16]}...")
                print(f"       ID Cliente: {venda.id_unico_cliente if venda else 'N/A'}")
        else:
            print(f"\n  ✅ TODAS as vendas têm cliente correspondente!")
        
        # 6. Vendas que NÃO TÊM cliente correspondente (já tratado acima)
        
        # 7. Clientes com coordenadas E vendas (processamento em memória)
        print("\n🗺️  CLIENTES COM COORDENADAS E VENDAS:")
        print("-" * 80)
        
        # Pega clientes com coordenadas
        clientes_com_coord = db.session.query(
            ClientName.name_client,
            ClientName.hash_client,
            LatLong.latitude,
            LatLong.longitude
        ).join(
            LatLong,
            ClientName.hash_client == LatLong.hash_client
        ).limit(20).all()
        
        clientes_completos_count = 0
        for cliente in clientes_com_coord:
            # Busca vendas deste cliente
            vendas_cliente = OrderHistory.query.filter_by(
                hash_cliente=cliente.hash_client
            ).all()
            
            if vendas_cliente:
                clientes_completos_count += 1
                if clientes_completos_count <= 5:  # Mostra só os 5 primeiros
                    total_pedidos = len(vendas_cliente)
                    valor_total = sum(v.valor_total_pagamento or 0 for v in vendas_cliente)
                    
                    print(f"\n  Cliente: {cliente.name_client}")
                    print(f"  Hash: {cliente.hash_client[:16]}...")
                    print(f"  Coordenadas: ({cliente.latitude}, {cliente.longitude})")
                    print(f"  Total de Pedidos: {total_pedidos}")
                    print(f"  Valor Total: R$ {valor_total:,.2f}")
        
        print(f"\n  Total de clientes com coordenadas e vendas: {clientes_completos_count}")
        
        # 8. Estatísticas agregadas (similar à rota)
        print("\n📈 ESTATÍSTICAS AGREGADAS (TODAS AS VENDAS):")
        print("-" * 80)
        
        stats = db.session.query(
            func.count(func.distinct(OrderHistory.hash_cliente)).label('total_clientes'),
            func.count(OrderHistory.id_pedido).label('total_pedidos'),
            func.sum(OrderHistory.valor_total_pagamento).label('valor_total'),
            func.avg(OrderHistory.valor_total_pagamento).label('ticket_medio'),
            func.max(OrderHistory.data_compra).label('ultima_compra')
        ).first()
        
        print(f"  Total de Clientes: {stats.total_clientes or 0:,}")
        print(f"  Total de Pedidos: {stats.total_pedidos or 0:,}")
        print(f"  Valor Total: R$ {stats.valor_total or 0:,.2f}")
        print(f"  Ticket Médio: R$ {stats.ticket_medio or 0:,.2f}")
        print(f"  Última Compra: {stats.ultima_compra}")
        
        # 9. Teste com hashes específicos de clientes no mapa
        print("\n🎯 TESTE COM HASHES DE CLIENTES (primeiros 5 do ClientName):")
        print("-" * 80)
        
        clientes_teste = ClientName.query.limit(5).all()
        hashes_teste = [c.hash_client for c in clientes_teste]
        
        for i, c in enumerate(clientes_teste, 1):
            print(f"\n  {i}. Cliente: {c.name_client}")
            print(f"     Hash: {c.hash_client}")
            
            # Busca vendas deste cliente
            vendas_cliente = OrderHistory.query.filter_by(
                hash_cliente=c.hash_client
            ).all()
            
            if vendas_cliente:
                total_valor = sum(v.valor_total_pagamento or 0 for v in vendas_cliente)
                print(f"     ✅ {len(vendas_cliente)} vendas encontradas")
                print(f"     Valor Total: R$ {total_valor:,.2f}")
            else:
                print(f"     ❌ Nenhuma venda encontrada")
        
        # 10. Teste da query usada na rota
        print("\n🔄 TESTE DA QUERY DA ROTA (simulando seleção de polígono):")
        print("-" * 80)
        
        if hashes_teste:
            stats_rota = db.session.query(
                func.count(func.distinct(OrderHistory.hash_cliente)).label('total_clientes'),
                func.count(OrderHistory.id_pedido).label('total_pedidos'),
                func.sum(OrderHistory.valor_total_pagamento).label('valor_total'),
                func.avg(OrderHistory.valor_total_pagamento).label('ticket_medio'),
                func.max(OrderHistory.data_compra).label('ultima_compra')
            ).filter(
                OrderHistory.hash_cliente.in_(hashes_teste)
            ).first()
            
            print(f"  Hashes testados: {len(hashes_teste)}")
            print(f"  Clientes com vendas: {stats_rota.total_clientes or 0}")
            print(f"  Total de Pedidos: {stats_rota.total_pedidos or 0}")
            print(f"  Valor Total: R$ {stats_rota.valor_total or 0:,.2f}")
            print(f"  Ticket Médio: R$ {stats_rota.ticket_medio or 0:,.2f}")
            print(f"  Última Compra: {stats_rota.ultima_compra}")
    
    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO")
    print("=" * 80)
