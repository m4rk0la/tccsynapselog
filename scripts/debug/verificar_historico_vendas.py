"""
Script para visualizar dados do banco OrderHistory (histórico de vendas)

Mostra:
- Total de registros
- Amostra de dados
- Estatísticas por usuário
- Campos preenchidos vs vazios
"""

import sys
import os

# Adicionar root ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from base.models import db, OrderHistory
import pandas as pd

def verificar_historico_vendas():
    """
    Inspeciona o banco de dados de histórico de vendas
    """
    print("="*80)
    print("🔍 INSPEÇÃO DO BANCO DE DADOS - HISTÓRICO DE VENDAS")
    print("="*80)
    print()
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. CONTAGEM TOTAL
            print("📊 [1/6] CONTAGEM TOTAL")
            print("-"*80)
            
            total_registros = OrderHistory.query.count()
            print(f"   Total de registros: {total_registros}")
            
            if total_registros == 0:
                print("\n   ⚠️  Banco de dados vazio!")
                print("   💡 Importe dados via /autenticado/historicovendas")
                return
            
            print()
            
            # 2. ESTATÍSTICAS POR USUÁRIO
            print("📊 [2/6] ESTATÍSTICAS POR USUÁRIO")
            print("-"*80)
            
            vendas_todos = OrderHistory.query.all()
            
            # Agrupar por user_id
            users = {}
            for venda in vendas_todos:
                if venda.user_id not in users:
                    users[venda.user_id] = []
                users[venda.user_id].append(venda)
            
            for user_id, vendas in users.items():
                print(f"\n   👤 User ID: {user_id}")
                print(f"      Total de vendas: {len(vendas)}")
                print(f"      Clientes únicos: {len(set(v.hash_cliente for v in vendas))}")
                
                # Valores
                valores = [v.valor_total_pagamento for v in vendas if v.valor_total_pagamento]
                if valores:
                    print(f"      Valor total: R$ {sum(valores):,.2f}")
                    print(f"      Ticket médio: R$ {sum(valores)/len(valores):,.2f}")
                
                # Notas
                notas = [v.nota_avaliacao for v in vendas if v.nota_avaliacao]
                if notas:
                    print(f"      Avaliações: {len(notas)}/{len(vendas)} ({len(notas)/len(vendas)*100:.1f}%)")
                    print(f"      Nota média: {sum(notas)/len(notas):.2f}")
            
            print()
            
            # 3. AMOSTRA DE DADOS (Primeiros 5 registros)
            print("📋 [3/6] AMOSTRA DE DADOS (Primeiros 5 registros)")
            print("-"*80)
            
            amostra = OrderHistory.query.limit(5).all()
            
            for i, venda in enumerate(amostra, 1):
                print(f"\n   📦 Registro {i}:")
                print(f"      ID Pedido: {venda.id_pedido}")
                print(f"      Hash Cliente: {venda.hash_cliente[:30]}..." if len(venda.hash_cliente) > 30 else f"      Hash Cliente: {venda.hash_cliente}")
                print(f"      User ID: {venda.user_id}")
                print(f"      Data Compra: {venda.data_compra}")
                print(f"      Valor Total: R$ {venda.valor_total_pagamento:.2f}" if venda.valor_total_pagamento else "      Valor Total: N/A")
                print(f"      Nota Avaliação: {venda.nota_avaliacao}" if venda.nota_avaliacao else "      Nota Avaliação: N/A")
                print(f"      Status: {venda.status_pedido}" if venda.status_pedido else "      Status: N/A")
                print(f"      Método Pagamento: {venda.metodo_pagamento}" if venda.metodo_pagamento else "      Método Pagamento: N/A")
            
            print()
            
            # 4. ANÁLISE DE CAMPOS (Preenchidos vs Vazios)
            print("📊 [4/6] ANÁLISE DE CAMPOS")
            print("-"*80)
            
            campos_essenciais = {
                'id_pedido': 0,
                'hash_cliente': 0,
                'user_id': 0,
                'data_compra': 0,
                'valor_total_pagamento': 0,
                'nota_avaliacao': 0,
                'status_pedido': 0,
                'metodo_pagamento': 0
            }
            
            for venda in vendas_todos:
                if venda.id_pedido:
                    campos_essenciais['id_pedido'] += 1
                if venda.hash_cliente:
                    campos_essenciais['hash_cliente'] += 1
                if venda.user_id:
                    campos_essenciais['user_id'] += 1
                if venda.data_compra:
                    campos_essenciais['data_compra'] += 1
                if venda.valor_total_pagamento:
                    campos_essenciais['valor_total_pagamento'] += 1
                if venda.nota_avaliacao:
                    campos_essenciais['nota_avaliacao'] += 1
                if venda.status_pedido:
                    campos_essenciais['status_pedido'] += 1
                if venda.metodo_pagamento:
                    campos_essenciais['metodo_pagamento'] += 1
            
            print(f"\n   Campo                    | Preenchidos | Vazios | Taxa")
            print("   " + "-"*60)
            
            for campo, count in campos_essenciais.items():
                vazios = total_registros - count
                taxa = (count / total_registros * 100) if total_registros > 0 else 0
                print(f"   {campo:24s} | {count:11d} | {vazios:6d} | {taxa:5.1f}%")
            
            print()
            
            # 5. CLIENTES COM MAIS PEDIDOS
            print("🏆 [5/6] TOP 10 CLIENTES (Mais Pedidos)")
            print("-"*80)
            
            # Contar pedidos por hash_cliente
            clientes_pedidos = {}
            for venda in vendas_todos:
                if venda.hash_cliente not in clientes_pedidos:
                    clientes_pedidos[venda.hash_cliente] = {
                        'pedidos': 0,
                        'valor_total': 0,
                        'user_id': venda.user_id
                    }
                clientes_pedidos[venda.hash_cliente]['pedidos'] += 1
                if venda.valor_total_pagamento:
                    clientes_pedidos[venda.hash_cliente]['valor_total'] += venda.valor_total_pagamento
            
            # Ordenar por número de pedidos
            top_clientes = sorted(clientes_pedidos.items(), 
                                key=lambda x: x[1]['pedidos'], 
                                reverse=True)[:10]
            
            print(f"\n   Rank | Cliente (hash)           | Pedidos | Valor Total   | User ID")
            print("   " + "-"*75)
            
            for i, (hash_cliente, dados) in enumerate(top_clientes, 1):
                hash_display = hash_cliente[:20] + "..." if len(hash_cliente) > 20 else hash_cliente
                print(f"   {i:4d} | {hash_display:24s} | {dados['pedidos']:7d} | R$ {dados['valor_total']:9,.2f} | {dados['user_id']}")
            
            print()
            
            # 6. DISTRIBUIÇÃO TEMPORAL
            print("📅 [6/6] DISTRIBUIÇÃO TEMPORAL")
            print("-"*80)
            
            datas = [v.data_compra for v in vendas_todos if v.data_compra]
            
            if datas:
                datas_sorted = sorted(datas)
                data_min = datas_sorted[0]
                data_max = datas_sorted[-1]
                
                print(f"\n   Primeira venda: {data_min}")
                print(f"   Última venda: {data_max}")
                print(f"   Período: {(data_max - data_min).days} dias")
                
                # Vendas por ano
                vendas_por_ano = {}
                for data in datas:
                    ano = data.year
                    if ano not in vendas_por_ano:
                        vendas_por_ano[ano] = 0
                    vendas_por_ano[ano] += 1
                
                print(f"\n   Vendas por ano:")
                for ano in sorted(vendas_por_ano.keys()):
                    print(f"      {ano}: {vendas_por_ano[ano]} vendas")
            else:
                print("\n   ⚠️  Nenhuma data de compra registrada")
            
            print()
            print("="*80)
            print("✅ INSPEÇÃO CONCLUÍDA")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ ERRO durante inspeção: {str(e)}")
            import traceback
            traceback.print_exc()

def exportar_para_csv(output_file='historico_vendas_export.csv'):
    """
    Exporta todos os dados do OrderHistory para CSV
    """
    print(f"\n📤 Exportando dados para {output_file}...")
    
    app = create_app()
    
    with app.app_context():
        try:
            vendas = OrderHistory.query.all()
            
            if not vendas:
                print("   ⚠️  Nenhum dado para exportar")
                return
            
            # Converter para lista de dicionários
            dados = []
            for venda in vendas:
                dados.append({
                    'id': venda.id,
                    'user_id': venda.user_id,
                    'id_pedido': venda.id_pedido,
                    'hash_cliente': venda.hash_cliente,
                    'data_compra': venda.data_compra,
                    'valor_total_pagamento': venda.valor_total_pagamento,
                    'nota_avaliacao': venda.nota_avaliacao,
                    'status_pedido': venda.status_pedido,
                    'metodo_pagamento': venda.metodo_pagamento
                })
            
            # Criar DataFrame e exportar
            df = pd.DataFrame(dados)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            print(f"   ✅ {len(dados)} registros exportados com sucesso!")
            print(f"   📁 Arquivo: {os.path.abspath(output_file)}")
            
        except Exception as e:
            print(f"   ❌ Erro ao exportar: {str(e)}")

if __name__ == '__main__':
    print()
    print("Escolha uma opção:")
    print("  1. Visualizar dados do banco")
    print("  2. Exportar para CSV")
    print("  3. Ambos")
    print()
    
    opcao = input("Digite a opção (1, 2 ou 3): ").strip()
    
    if opcao == '1':
        verificar_historico_vendas()
    elif opcao == '2':
        exportar_para_csv()
    elif opcao == '3':
        verificar_historico_vendas()
        exportar_para_csv()
    else:
        print("❌ Opção inválida!")
