"""
Script para limpar (truncar) todas as tabelas do banco de dados
ATENÇÃO: Este script apaga TODOS os dados! Use com cuidado!
"""

from app import create_app
from base.models import (
    db, User, SystemLog, ClientName, LatLong, Routs, KNN, 
    Polygon, Products, Consummer, NDBFeatures, NDBOut, OrderHistory
)

def limpar_banco_dados(confirmar=False, apenas_order_history=False):
    """
    Limpa todas as tabelas do banco de dados
    
    Parâmetros:
        confirmar (bool): True para executar, False para simular
        apenas_order_history (bool): True para limpar apenas OrderHistory
    """
    
    app = create_app()
    
    with app.app_context():
        print("="*80)
        print("🗑️  SCRIPT DE LIMPEZA DO BANCO DE DADOS")
        print("="*80)
        
        if apenas_order_history:
            tabelas_para_limpar = [
                ('OrderHistory', OrderHistory, 'order_history')
            ]
            print("\n⚠️  MODO: Limpar apenas OrderHistory")
        else:
            # Lista de todas as tabelas (ordem importa para FK)
            tabelas_para_limpar = [
                ('OrderHistory', OrderHistory, 'order_history'),
                ('NDBOut', NDBOut, 'neuraldatabaserout'),
                ('NDBFeatures', NDBFeatures, 'ml_features'),
                ('Consummer', Consummer, 'consummer'),
                ('KNN', KNN, 'KNN'),
                ('Routs', Routs, 'routs'),
                ('LatLong', LatLong, 'latlong'),
                ('Products', Products, 'products'),
                ('Polygon', Polygon, 'polygon'),
                ('ClientName', ClientName, 'client_name'),
                ('SystemLog', SystemLog, 'logs'),
                # User mantemos para não perder login
            ]
            print("\n⚠️  MODO: Limpar TODAS as tabelas (exceto Users)")
        
        if not confirmar:
            print("\n" + "="*80)
            print("🔍 MODO SIMULAÇÃO - Nenhum dado será apagado")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("⚠️  ATENÇÃO: DADOS SERÃO PERMANENTEMENTE APAGADOS!")
            print("="*80)
        
        print("\n📋 Tabelas que serão limpas:")
        print("-"*80)
        
        total_registros_antes = 0
        contadores = {}
        
        for nome_tabela, modelo, bind_key in tabelas_para_limpar:
            try:
                # Conta registros antes
                count = modelo.query.count()
                contadores[nome_tabela] = count
                total_registros_antes += count
                
                status = "🔴 SERÁ LIMPA" if confirmar else "⚪ SIMULAÇÃO"
                print(f"   {status} {nome_tabela:20s} - {count:,} registros no banco '{bind_key}'")
                
            except Exception as e:
                print(f"   ⚠️  ERRO ao contar {nome_tabela}: {str(e)}")
        
        print("-"*80)
        print(f"\n📊 Total de registros: {total_registros_antes:,}")
        
        if not confirmar:
            print("\n" + "="*80)
            print("💡 Para EXECUTAR a limpeza, rode:")
            print("   limpar_banco_dados(confirmar=True)")
            print("\n💡 Para limpar apenas OrderHistory:")
            print("   limpar_banco_dados(confirmar=True, apenas_order_history=True)")
            print("="*80)
            return
        
        # CONFIRMAÇÃO FINAL
        print("\n" + "="*80)
        print("⚠️  ÚLTIMA CONFIRMAÇÃO")
        print("="*80)
        print(f"Você está prestes a APAGAR {total_registros_antes:,} registros!")
        print("\nDigite 'CONFIRMAR' para prosseguir ou qualquer outra coisa para cancelar:")
        
        confirmacao = input("> ").strip().upper()
        
        if confirmacao != "CONFIRMAR":
            print("\n❌ Operação CANCELADA pelo usuário")
            print("="*80)
            return
        
        # EXECUÇÃO DA LIMPEZA
        print("\n" + "="*80)
        print("🔄 INICIANDO LIMPEZA...")
        print("="*80)
        
        registros_apagados = 0
        
        for nome_tabela, modelo, bind_key in tabelas_para_limpar:
            try:
                count_antes = contadores[nome_tabela]
                
                if count_antes > 0:
                    print(f"\n🗑️  Limpando {nome_tabela}...")
                    
                    # Deleta todos os registros
                    modelo.query.delete()
                    db.session.commit()
                    
                    # Verifica se limpou
                    count_depois = modelo.query.count()
                    
                    if count_depois == 0:
                        print(f"   ✅ {count_antes:,} registros apagados")
                        registros_apagados += count_antes
                    else:
                        print(f"   ⚠️  Ainda restam {count_depois:,} registros")
                else:
                    print(f"\n⚪ {nome_tabela} já estava vazio")
                    
            except Exception as e:
                print(f"\n❌ Erro ao limpar {nome_tabela}: {str(e)}")
                db.session.rollback()
        
        print("\n" + "="*80)
        print("✅ LIMPEZA CONCLUÍDA!")
        print("="*80)
        print(f"📊 Total de registros apagados: {registros_apagados:,}")
        print("\n💡 Agora você pode fazer uma importação limpa!")
        print("="*80)


def limpar_apenas_order_history():
    """Atalho para limpar apenas OrderHistory"""
    return limpar_banco_dados(confirmar=True, apenas_order_history=True)


def verificar_banco():
    """Verifica o estado atual do banco sem fazer alterações"""
    
    app = create_app()
    
    with app.app_context():
        print("="*80)
        print("📊 ESTADO ATUAL DO BANCO DE DADOS")
        print("="*80)
        
        tabelas = [
            ('User', User, 'users_code'),
            ('SystemLog', SystemLog, 'logs'),
            ('ClientName', ClientName, 'client_name'),
            ('LatLong', LatLong, 'latlong'),
            ('Products', Products, 'products'),
            ('Consummer', Consummer, 'consummer'),
            ('Routs', Routs, 'routs'),
            ('KNN', KNN, 'KNN'),
            ('Polygon', Polygon, 'polygon'),
            ('NDBFeatures', NDBFeatures, 'ml_features'),
            ('NDBOut', NDBOut, 'neuraldatabaserout'),
            ('OrderHistory', OrderHistory, 'order_history'),
        ]
        
        print("\n📋 Registros por tabela:")
        print("-"*80)
        
        total = 0
        tem_dados = False
        
        for nome_tabela, modelo, bind_key in tabelas:
            try:
                count = modelo.query.count()
                total += count
                
                if count > 0:
                    tem_dados = True
                    status = "🔴"
                else:
                    status = "⚪"
                
                print(f"   {status} {nome_tabela:20s} {count:>8,} registros  [{bind_key}]")
                
            except Exception as e:
                print(f"   ⚠️  {nome_tabela:20s} ERRO: {str(e)}")
        
        print("-"*80)
        print(f"\n📊 Total geral: {total:,} registros")
        
        if tem_dados:
            print("\n💡 Para limpar o banco, execute:")
            print("   python limpar_banco.py")
        else:
            print("\n✅ Banco de dados está limpo!")
        
        print("="*80)


if __name__ == "__main__":
    import sys
    
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "🗑️  LIMPEZA DO HISTÓRICO DE VENDAS" + " "*27 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    # Primeiro verifica o estado
    verificar_banco()
    
    print("\n" + "="*80)
    print("⚠️  LIMPAR BANCO DE HISTÓRICO DE VENDAS (OrderHistory)")
    print("="*80)
    print()
    print("Esta operação irá APAGAR todos os registros da tabela OrderHistory.")
    print("Os dados de clientes, produtos e outras tabelas serão MANTIDOS.")
    print()
    
    try:
        confirma = input("Deseja continuar? Digite 'SIM' para confirmar: ").strip().upper()
        
        if confirma == 'SIM':
            limpar_banco_dados(confirmar=True, apenas_order_history=True)
        else:
            print("\n❌ Operação cancelada")
            print("💡 Nenhum dado foi alterado")
            
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
