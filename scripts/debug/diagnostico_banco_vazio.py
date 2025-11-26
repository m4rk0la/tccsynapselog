"""
Script de diagnóstico completo para entender por que o banco está vazio
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from base.models import db, OrderHistory, ClientName, LatLong, User
from flask import current_app
import sqlite3

def diagnostico_completo():
    """
    Diagnóstico completo do sistema de banco de dados
    """
    print("="*80)
    print("🔍 DIAGNÓSTICO COMPLETO - BANCO DE DADOS")
    print("="*80)
    print()
    
    app = create_app()
    
    with app.app_context():
        # 1. VERIFICAR CONFIGURAÇÃO DOS BINDS
        print("📋 [1/7] CONFIGURAÇÃO DE BINDS")
        print("-"*80)
        
        binds = current_app.config.get('SQLALCHEMY_BINDS', {})
        
        if binds:
            print(f"   Total de binds configurados: {len(binds)}")
            for bind_name, bind_path in binds.items():
                print(f"   • {bind_name}: {bind_path}")
        else:
            print("   ⚠️  Nenhum bind configurado!")
        
        print()
        
        # 2. VERIFICAR SE ARQUIVOS .DB EXISTEM
        print("📂 [2/7] ARQUIVOS DE BANCO DE DADOS")
        print("-"*80)
        
        databases_dir = os.path.join(os.path.dirname(__file__), '../../databases')
        databases_dir = os.path.abspath(databases_dir)
        
        print(f"   Diretório: {databases_dir}")
        print(f"   Existe: {os.path.exists(databases_dir)}")
        print()
        
        if os.path.exists(databases_dir):
            db_files = [f for f in os.listdir(databases_dir) if f.endswith('.db')]
            print(f"   Arquivos .db encontrados: {len(db_files)}")
            for db_file in sorted(db_files):
                db_path = os.path.join(databases_dir, db_file)
                size = os.path.getsize(db_path)
                print(f"   • {db_file:35s} ({size:>10,} bytes)")
        else:
            print("   ⚠️  Diretório databases/ não existe!")
        
        print()
        
        # 3. VERIFICAR TABELAS NO BANCO order_history
        print("📊 [3/7] TABELAS NO BANCO order_history")
        print("-"*80)
        
        try:
            # Conectar diretamente ao SQLite para inspecionar
            order_history_path = None
            for bind_name, bind_path in binds.items():
                if 'order_history' in bind_name:
                    # Extrair caminho do SQLite URI
                    if 'sqlite:///' in bind_path:
                        order_history_path = bind_path.replace('sqlite:///', '')
                    break
            
            if order_history_path and os.path.exists(order_history_path):
                conn = sqlite3.connect(order_history_path)
                cursor = conn.cursor()
                
                # Listar tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                print(f"   Banco: {order_history_path}")
                print(f"   Tabelas encontradas: {len(tables)}")
                
                if tables:
                    for table in tables:
                        table_name = table[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        print(f"   • {table_name:30s}: {count:>6} registros")
                else:
                    print("   ⚠️  Nenhuma tabela encontrada no banco!")
                
                conn.close()
            else:
                print(f"   ⚠️  Banco order_history não encontrado!")
                print(f"   Caminho esperado: {order_history_path}")
        
        except Exception as e:
            print(f"   ❌ Erro ao inspecionar: {str(e)}")
        
        print()
        
        # 4. VERIFICAR USUÁRIOS NO SISTEMA
        print("👥 [4/7] USUÁRIOS NO SISTEMA")
        print("-"*80)
        
        try:
            users = User.query.all()
            print(f"   Total de usuários: {len(users)}")
            
            if users:
                for user in users:
                    print(f"   • ID: {user.id} | Email: {user.email}")
            else:
                print("   ⚠️  Nenhum usuário cadastrado!")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        print()
        
        # 5. VERIFICAR CLIENTES
        print("👤 [5/7] CLIENTES CADASTRADOS")
        print("-"*80)
        
        try:
            clientes = ClientName.query.all()
            print(f"   Total de clientes: {len(clientes)}")
            
            if clientes:
                # Agrupar por user_id
                por_usuario = {}
                for cliente in clientes:
                    if cliente.user_id not in por_usuario:
                        por_usuario[cliente.user_id] = 0
                    por_usuario[cliente.user_id] += 1
                
                for user_id, count in por_usuario.items():
                    print(f"   • User ID {user_id}: {count} clientes")
                
                # Mostrar amostra
                print("\n   Amostra (primeiros 3):")
                for cliente in clientes[:3]:
                    print(f"   • {cliente.name_client[:50]} (hash: {cliente.hash_client[:30]}...)")
            else:
                print("   ⚠️  Nenhum cliente cadastrado!")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        print()
        
        # 6. VERIFICAR COORDENADAS
        print("📍 [6/7] COORDENADAS (LatLong)")
        print("-"*80)
        
        try:
            coords = LatLong.query.all()
            print(f"   Total de coordenadas: {len(coords)}")
            
            if coords:
                por_usuario = {}
                for coord in coords:
                    if coord.id_user not in por_usuario:
                        por_usuario[coord.id_user] = 0
                    por_usuario[coord.id_user] += 1
                
                for user_id, count in por_usuario.items():
                    print(f"   • User ID {user_id}: {count} coordenadas")
            else:
                print("   ⚠️  Nenhuma coordenada cadastrada!")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        print()
        
        # 7. VERIFICAR HISTÓRICO DE VENDAS
        print("📦 [7/7] HISTÓRICO DE VENDAS")
        print("-"*80)
        
        try:
            vendas = OrderHistory.query.all()
            print(f"   Total de vendas: {len(vendas)}")
            
            if vendas:
                por_usuario = {}
                for venda in vendas:
                    if venda.user_id not in por_usuario:
                        por_usuario[venda.user_id] = 0
                    por_usuario[venda.user_id] += 1
                
                for user_id, count in por_usuario.items():
                    print(f"   • User ID {user_id}: {count} vendas")
            else:
                print("   ⚠️  Nenhuma venda cadastrada!")
                print()
                print("   💡 CAUSAS POSSÍVEIS:")
                print("      1. Arquivo Excel não foi importado via /autenticado/historicovendas")
                print("      2. Erro durante o upload (verificar logs)")
                print("      3. Validação de colunas falhou")
                print("      4. Exceção durante processamento")
        except Exception as e:
            if 'no such table' in str(e):
                print("   ⚠️  Tabela 'order_history_data' não existe!")
                print("   💡 Execute o script de inicialização dos bancos")
            else:
                print(f"   ❌ Erro: {str(e)}")
        
        print()
        
        # RESUMO FINAL
        print("="*80)
        print("📋 RESUMO DO DIAGNÓSTICO")
        print("="*80)
        
        try:
            total_users = User.query.count()
            total_clientes = ClientName.query.count()
            total_coords = LatLong.query.count()
            total_vendas = OrderHistory.query.count()
            
            print(f"   • Usuários: {total_users}")
            print(f"   • Clientes: {total_clientes}")
            print(f"   • Coordenadas: {total_coords}")
            print(f"   • Vendas: {total_vendas}")
            print()
            
            if total_vendas == 0:
                print("   🔍 PROBLEMA IDENTIFICADO:")
                print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print()
                print("   O banco de histórico de vendas está VAZIO porque:")
                print()
                
                if total_users == 0:
                    print("   ❌ Não há usuários cadastrados no sistema")
                    print("      Solução: Crie um usuário via /registro ou execute create_admin.py")
                    print()
                
                if total_clientes == 0:
                    print("   ⚠️  Não há clientes cadastrados")
                    print("      Nota: Clientes não são obrigatórios para vendas, mas recomendado")
                    print()
                
                print("   🎯 PRÓXIMOS PASSOS:")
                print()
                print("   1. Acesse http://localhost:5000 e faça login")
                print("   2. Vá em /autenticado/historicovendas")
                print("   3. Faça upload de um arquivo Excel com as colunas:")
                print("      - id_pedido (obrigatório)")
                print("      - id_cliente (obrigatório)")
                print("      - data_compra (obrigatório)")
                print("      - valor_total_pagamento (obrigatório)")
                print("      - nota_avaliacao (opcional)")
                print()
                print("   4. Após upload bem-sucedido, execute este script novamente")
                
        except Exception as e:
            print(f"   ❌ Erro ao gerar resumo: {str(e)}")
        
        print()
        print("="*80)

if __name__ == '__main__':
    diagnostico_completo()
