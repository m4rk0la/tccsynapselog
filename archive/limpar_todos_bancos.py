"""
Script para limpar TODOS os bancos de dados
Use este script quando precisar resetar completamente o sistema
"""

from app import create_app
from base.models import (
    db, User, ClientName, LatLong, Products, 
    Routs, NDBFeatures, NDBOut, Polygon, OrderHistory
)

app = create_app()

def limpar_todos_bancos():
    """Limpa todas as tabelas de todos os bancos"""
    with app.app_context():
        print("=" * 80)
        print("🗑️  LIMPEZA COMPLETA DE TODOS OS BANCOS DE DADOS")
        print("=" * 80)
        
        # Contagem antes da limpeza
        print("\n📊 CONTAGEM ANTES DA LIMPEZA:")
        print("-" * 80)
        
        contagens = {
            'OrderHistory': OrderHistory.query.count(),
            'ClientName': ClientName.query.count(),
            'LatLong': LatLong.query.count(),
            'Products': Products.query.count(),
            'Routs': Routs.query.count(),
            'Polygon': Polygon.query.count(),
            'NDBFeatures': NDBFeatures.query.count(),
            'NDBOut': NDBOut.query.count(),
            'User': User.query.count(),
        }
        
        for tabela, count in contagens.items():
            print(f"  {tabela}: {count:,} registros")
        
        total_registros = sum(contagens.values())
        print(f"\n  TOTAL: {total_registros:,} registros")
        
        if total_registros == 0:
            print("\n✅ Todos os bancos já estão vazios!")
            return
        
        # Confirmação
        print("\n" + "=" * 80)
        print("⚠️  ATENÇÃO: Esta ação é IRREVERSÍVEL!")
        print("⚠️  Todos os dados serão PERMANENTEMENTE DELETADOS!")
        print("=" * 80)
        print("\nTabelas que serão limpas:")
        print("  1. OrderHistory (Histórico de Vendas)")
        print("  2. ClientName (Clientes)")
        print("  3. LatLong (Coordenadas)")
        print("  4. Products (Produtos)")
        print("  5. Routs (Rotas)")
        print("  6. Polygon (Polígonos/Áreas)")
        print("  7. NDBFeatures (Features)")
        print("  8. NDBOut (Saídas)")
        print("  9. User (Usuários - EXCETO admin)")
        
        print("\n" + "=" * 80)
        confirmacao1 = input("Digite 'LIMPAR TUDO' para confirmar: ").strip()
        
        if confirmacao1 != 'LIMPAR TUDO':
            print("\n❌ Operação cancelada pelo usuário.")
            return
        
        print("\n⚠️  ÚLTIMA CONFIRMAÇÃO!")
        confirmacao2 = input("Digite 'CONFIRMAR' para prosseguir: ").strip()
        
        if confirmacao2 != 'CONFIRMAR':
            print("\n❌ Operação cancelada pelo usuário.")
            return
        
        # Executa a limpeza
        print("\n🧹 Iniciando limpeza...")
        print("-" * 80)
        
        registros_deletados = {}
        
        try:
            # 1. OrderHistory
            print("  Limpando OrderHistory...")
            count = OrderHistory.query.delete()
            db.session.commit()
            registros_deletados['OrderHistory'] = count
            print(f"    ✅ {count:,} registros deletados")
            
            # 2. ClientName
            print("  Limpando ClientName...")
            count = ClientName.query.delete()
            db.session.commit()
            registros_deletados['ClientName'] = count
            print(f"    ✅ {count:,} registros deletados")
            
            # 3. LatLong
            print("  Limpando LatLong...")
            count = LatLong.query.delete()
            db.session.commit()
            registros_deletados['LatLong'] = count
            print(f"    ✅ {count:,} registros deletados")
            
            # 4. Products
            print("  Limpando Products...")
            count = Products.query.delete()
            db.session.commit()
            registros_deletados['Products'] = count
            print(f"    ✅ {count:,} registros deletados")
            
            # 5. Routs
            print("  Limpando Routs...")
            count = Routs.query.delete()
            db.session.commit()
            registros_deletados['Routs'] = count
            print(f"    ✅ {count:,} registros deletados")
            
            # 6. Polygon
            print("  Limpando Polygon...")
            count = Polygon.query.delete()
            db.session.commit()
            registros_deletados['Polygon'] = count
            print(f"    ✅ {count:,} registros deletados")
            
            # 7. NDBFeatures
            print("  Limpando NDBFeatures...")
            count = NDBFeatures.query.delete()
            db.session.commit()
            registros_deletados['NDBFeatures'] = count
            print(f"    ✅ {count:,} registros deletados")
            
            # 8. NDBOut
            print("  Limpando NDBOut...")
            count = NDBOut.query.delete()
            db.session.commit()
            registros_deletados['NDBOut'] = count
            print(f"    ✅ {count:,} registros deletados")
            
            # 9. User (mantém apenas o primeiro usuário que geralmente é admin)
            print("  Limpando User (mantendo primeiro usuário)...")
            first_user = User.query.first()
            if first_user:
                count = User.query.filter(User.id != first_user.id).delete()
                db.session.commit()
                registros_deletados['User'] = count
                print(f"    ✅ {count:,} registros deletados (mantido: {first_user.username})")
            else:
                registros_deletados['User'] = 0
                print(f"    ⚠️  Nenhum usuário encontrado")
            
            # Resumo
            print("\n" + "=" * 80)
            print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
            print("=" * 80)
            print("\n📊 RESUMO:")
            print("-" * 80)
            
            total_deletados = sum(registros_deletados.values())
            for tabela, count in registros_deletados.items():
                print(f"  {tabela}: {count:,} registros deletados")
            
            print(f"\n  TOTAL DELETADO: {total_deletados:,} registros")
            
            # Verifica se está tudo vazio
            print("\n📊 VERIFICAÇÃO PÓS-LIMPEZA:")
            print("-" * 80)
            
            contagens_pos = {
                'OrderHistory': OrderHistory.query.count(),
                'ClientName': ClientName.query.count(),
                'LatLong': LatLong.query.count(),
                'Products': Products.query.count(),
                'Routs': Routs.query.count(),
                'Polygon': Polygon.query.count(),
                'NDBFeatures': NDBFeatures.query.count(),
                'NDBOut': NDBOut.query.count(),
                'User': User.query.count(),
            }
            
            for tabela, count in contagens_pos.items():
                status = "✅" if count == 0 or (tabela == 'User' and count == 1) else "⚠️"
                print(f"  {status} {tabela}: {count:,} registros")
            
            print("\n" + "=" * 80)
            print("🎉 SISTEMA PRONTO PARA NOVA IMPORTAÇÃO!")
            print("=" * 80)
            print("\nPróximos passos:")
            print("  1. Importar base de clientes (usando função centralizada de hash)")
            print("  2. Importar histórico de vendas (usando mesma função de hash)")
            print("  3. Verificar que os hashes agora fazem match")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ ERRO durante a limpeza: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    limpar_todos_bancos()
