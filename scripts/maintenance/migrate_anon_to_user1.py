"""Script para migrar dados de user_id='anon' para user_id=1"""
from app import create_app
from base.models import db, LatLong, Polygon, ClientName

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("🔄 MIGRAÇÃO: 'anon' → user_id=1")
    print("="*80 + "\n")
    
    # Conta registros antes
    clients_anon = ClientName.query.filter_by(user_id='anon').count()
    points_anon = LatLong.query.filter_by(id_user='anon').count()
    polygons_anon = Polygon.query.filter_by(user_id='anon').count()
    
    print(f"📊 ANTES DA MIGRAÇÃO:")
    print(f"  - Clientes com 'anon': {clients_anon}")
    print(f"  - Pontos com 'anon': {points_anon}")
    print(f"  - Áreas com 'anon': {polygons_anon}")
    
    if clients_anon == 0 and points_anon == 0 and polygons_anon == 0:
        print("\n⚠️ Nenhum dado com 'anon' encontrado. Nada a migrar.")
        print("="*80 + "\n")
        exit()
    
    print("\n🔄 Iniciando migração...\n")
    
    try:
        # Migra ClientName
        print("📋 Migrando clientes...")
        ClientName.query.filter_by(user_id='anon').update({'user_id': 1})
        clients_migrated = ClientName.query.filter_by(user_id=1).count()
        print(f"  ✅ {clients_migrated} clientes migrados")
        
        # Migra LatLong
        print("📍 Migrando pontos...")
        LatLong.query.filter_by(id_user='anon').update({'id_user': 1})
        points_migrated = LatLong.query.filter_by(id_user=1).count()
        print(f"  ✅ {points_migrated} pontos migrados")
        
        # Migra Polygon
        print("🗺️ Migrando áreas/grupos...")
        Polygon.query.filter_by(user_id='anon').update({'user_id': 1})
        polygons_migrated = Polygon.query.filter_by(user_id=1).count()
        print(f"  ✅ {polygons_migrated} áreas migradas")
        
        # Commit
        db.session.commit()
        print("\n💾 Alterações salvas no banco de dados")
        
        # Verifica depois
        print("\n" + "-"*80)
        print("📊 DEPOIS DA MIGRAÇÃO:")
        print(f"  - Clientes com user_id=1: {ClientName.query.filter_by(user_id=1).count()}")
        print(f"  - Pontos com id_user=1: {LatLong.query.filter_by(id_user=1).count()}")
        print(f"  - Áreas com user_id=1: {Polygon.query.filter_by(user_id=1).count()}")
        
        print("\n" + "="*80)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*80 + "\n")
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ ERRO na migração: {e}")
        print("🔙 Rollback executado - nenhuma alteração foi feita")
        print("="*80 + "\n")
