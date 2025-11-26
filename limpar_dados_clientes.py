"""
Script para limpar todos os dados de clientes do sistema
Útil para fazer importação limpa após mudanças estruturais

ATENÇÃO: Este script apaga TODOS os dados de clientes de TODOS os usuários!
Use com EXTREMO cuidado em produção.

Tabelas afetadas:
- ClientName (client_name.db)
- LatLong (latlong.db)
- OrderHistory (order_history.db)
- ClientScore (client_scores.db)
- Polygon (polygon.db)
"""

import sys
import os

# Adicionar root ao path (script está no root do projeto)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from base.models import db, ClientName, LatLong, OrderHistory, ClientScore, Polygon

def limpar_dados_clientes():
    """
    Remove todos os dados de clientes do sistema
    """
    print("="*70)
    print("🗑️  LIMPEZA DE DADOS DE CLIENTES - SYNAPSELLOG")
    print("="*70)
    print()
    print("⚠️  ATENÇÃO: Este script vai apagar TODOS os dados de clientes!")
    print()
    print("Tabelas que serão limpas:")
    print("  1. ClientScore (client_scores.db) - Scores RFM")
    print("  2. OrderHistory (order_history.db) - Histórico de vendas")
    print("  3. LatLong (latlong.db) - Coordenadas geográficas")
    print("  4. ClientName (client_name.db) - Cadastro de clientes")
    print("  5. Polygon (polygon.db) - Áreas/grupos de clientes")
    print()
    
    # Confirmação de segurança
    confirmacao = input("Digite 'CONFIRMAR' para continuar: ")
    
    if confirmacao != 'CONFIRMAR':
        print("\n❌ Operação cancelada pelo usuário.")
        return False
    
    print("\n🔄 Iniciando limpeza...\n")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Contadores
            total_deletado = {
                'client_scores': 0,
                'order_history': 0,
                'latlong': 0,
                'client_name': 0,
                'polygon': 0
            }
            
            # 1. Limpar ClientScore (scores RFM)
            print("🗑️  [1/5] Limpando ClientScore...")
            try:
                count = ClientScore.query.count()
                if count > 0:
                    ClientScore.query.delete()
                    db.session.commit()
                    total_deletado['client_scores'] = count
                    print(f"   ✅ {count} registros de scores removidos")
                else:
                    print("   ℹ️  Nenhum registro encontrado")
            except Exception as e:
                if 'no such table' in str(e):
                    print("   ℹ️  Tabela client_scores_data ainda não existe (será criada no primeiro uso)")
                else:
                    raise
            
            # 2. Limpar OrderHistory (histórico de vendas)
            print("🗑️  [2/5] Limpando OrderHistory...")
            try:
                count = OrderHistory.query.count()
                if count > 0:
                    OrderHistory.query.delete()
                    db.session.commit()
                    total_deletado['order_history'] = count
                    print(f"   ✅ {count} registros de vendas removidos")
                else:
                    print("   ℹ️  Nenhum registro encontrado")
            except Exception as e:
                if 'no such table' in str(e):
                    print("   ℹ️  Tabela ainda não existe")
                else:
                    raise
            
            # 3. Limpar LatLong (coordenadas)
            print("🗑️  [3/5] Limpando LatLong...")
            try:
                count = LatLong.query.count()
                if count > 0:
                    LatLong.query.delete()
                    db.session.commit()
                    total_deletado['latlong'] = count
                    print(f"   ✅ {count} registros de coordenadas removidos")
                else:
                    print("   ℹ️  Nenhum registro encontrado")
            except Exception as e:
                if 'no such table' in str(e):
                    print("   ℹ️  Tabela ainda não existe")
                else:
                    raise
            
            # 4. Limpar ClientName (cadastro de clientes)
            print("🗑️  [4/5] Limpando ClientName...")
            try:
                count = ClientName.query.count()
                if count > 0:
                    ClientName.query.delete()
                    db.session.commit()
                    total_deletado['client_name'] = count
                    print(f"   ✅ {count} registros de clientes removidos")
                else:
                    print("   ℹ️  Nenhum registro encontrado")
            except Exception as e:
                if 'no such table' in str(e):
                    print("   ℹ️  Tabela ainda não existe")
                else:
                    raise
            
            # 5. Limpar Polygon (áreas/grupos)
            print("🗑️  [5/5] Limpando Polygon...")
            try:
                count = Polygon.query.count()
                if count > 0:
                    Polygon.query.delete()
                    db.session.commit()
                    total_deletado['polygon'] = count
                    print(f"   ✅ {count} registros de áreas removidos")
                else:
                    print("   ℹ️  Nenhum registro encontrado")
            except Exception as e:
                if 'no such table' in str(e):
                    print("   ℹ️  Tabela ainda não existe")
                else:
                    raise
            
            # Resumo
            print("\n" + "="*70)
            print("📊 RESUMO DA LIMPEZA")
            print("="*70)
            
            total_geral = sum(total_deletado.values())
            
            if total_geral > 0:
                for tabela, count in total_deletado.items():
                    if count > 0:
                        print(f"  • {tabela:20s}: {count:6d} registros removidos")
                print(f"\n  🎯 TOTAL GERAL: {total_geral} registros removidos")
                print("\n✅ Limpeza concluída com sucesso!")
                print("\n💡 Próximo passo: Importar dados limpos via interface web")
            else:
                print("  ℹ️  Nenhum dado foi encontrado para limpar")
                print("  ✅ Bancos de dados já estavam vazios")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO durante a limpeza: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def limpar_dados_usuario_especifico(user_id):
    """
    Remove dados de apenas um usuário específico
    """
    print("="*70)
    print(f"🗑️  LIMPEZA DE DADOS DO USUÁRIO {user_id} - SYNAPSELLOG")
    print("="*70)
    print()
    
    confirmacao = input(f"Digite 'CONFIRMAR' para limpar dados do user_id={user_id}: ")
    
    if confirmacao != 'CONFIRMAR':
        print("\n❌ Operação cancelada pelo usuário.")
        return False
    
    print("\n🔄 Iniciando limpeza...\n")
    
    app = create_app()
    
    with app.app_context():
        try:
            total_deletado = {
                'client_scores': 0,
                'order_history': 0,
                'latlong': 0,
                'client_name': 0,
                'polygon': 0
            }
            
            # 1. ClientScore
            print("🗑️  [1/5] Limpando ClientScore...")
            count = ClientScore.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            total_deletado['client_scores'] = count
            print(f"   ✅ {count} registros removidos")
            
            # 2. OrderHistory
            print("🗑️  [2/5] Limpando OrderHistory...")
            count = OrderHistory.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            total_deletado['order_history'] = count
            print(f"   ✅ {count} registros removidos")
            
            # 3. LatLong
            print("🗑️  [3/5] Limpando LatLong...")
            count = LatLong.query.filter_by(id_user=user_id).delete()
            db.session.commit()
            total_deletado['latlong'] = count
            print(f"   ✅ {count} registros removidos")
            
            # 4. ClientName
            print("🗑️  [4/5] Limpando ClientName...")
            count = ClientName.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            total_deletado['client_name'] = count
            print(f"   ✅ {count} registros removidos")
            
            # 5. Polygon
            print("🗑️  [5/5] Limpando Polygon...")
            count = Polygon.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            total_deletado['polygon'] = count
            print(f"   ✅ {count} registros removidos")
            
            # Resumo
            print("\n" + "="*70)
            print(f"📊 RESUMO DA LIMPEZA - USER_ID {user_id}")
            print("="*70)
            
            total_geral = sum(total_deletado.values())
            
            for tabela, count in total_deletado.items():
                if count > 0:
                    print(f"  • {tabela:20s}: {count:6d} registros removidos")
            
            print(f"\n  🎯 TOTAL: {total_geral} registros removidos")
            print("\n✅ Limpeza concluída com sucesso!")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print()
    print("Escolha o modo de limpeza:")
    print("  1. Limpar TODOS os dados de TODOS os usuários")
    print("  2. Limpar dados de um usuário específico")
    print("  3. Cancelar")
    print()
    
    opcao = input("Digite a opção (1, 2 ou 3): ").strip()
    
    if opcao == '1':
        limpar_dados_clientes()
    elif opcao == '2':
        try:
            user_id = int(input("Digite o user_id: ").strip())
            limpar_dados_usuario_especifico(user_id)
        except ValueError:
            print("❌ user_id inválido!")
    elif opcao == '3':
        print("❌ Operação cancelada.")
    else:
        print("❌ Opção inválida!")
