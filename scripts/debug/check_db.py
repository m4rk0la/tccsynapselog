"""Script para verificar dados no banco de dados"""
from app import create_app
from base.models import db, LatLong, Polygon, ClientName, User

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("🔍 VERIFICAÇÃO DO BANCO DE DADOS")
    print("="*80 + "\n")
    
    # Verifica usuários
    print("👤 USUÁRIOS:")
    users = User.query.all()
    if users:
        for user in users:
            print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}")
    else:
        print("  ⚠️ Nenhum usuário encontrado")
    
    print("\n" + "-"*80 + "\n")
    
    # Verifica clientes (ClientName)
    print("📋 CLIENTES (ClientName):")
    clients = ClientName.query.all()
    if clients:
        print(f"  Total: {len(clients)} clientes")
        user_counts = {}
        for c in clients:
            user_counts[c.user_id] = user_counts.get(c.user_id, 0) + 1
        
        for uid, count in user_counts.items():
            print(f"  - user_id {uid}: {count} clientes")
            
        # Mostra alguns exemplos
        print("\n  Exemplos (primeiros 5):")
        for c in clients[:5]:
            print(f"    - {c.name_client} (user_id: {c.user_id}, hash: {c.hash_client[:20]}...)")
    else:
        print("  ⚠️ Nenhum cliente encontrado")
    
    print("\n" + "-"*80 + "\n")
    
    # Verifica pontos (LatLong)
    print("📍 PONTOS DE LOCALIZAÇÃO (LatLong):")
    points = LatLong.query.all()
    if points:
        print(f"  Total: {len(points)} pontos")
        user_counts = {}
        for p in points:
            user_counts[p.id_user] = user_counts.get(p.id_user, 0) + 1
        
        for uid, count in user_counts.items():
            client_points = LatLong.query.filter_by(id_user=uid, user_point=False).count()
            base_points = LatLong.query.filter_by(id_user=uid, user_point=True).count()
            print(f"  - id_user {uid}: {count} pontos ({client_points} clientes, {base_points} pontos base)")
            
        # Mostra alguns exemplos
        print("\n  Exemplos (primeiros 5):")
        for p in points[:5]:
            tipo = "Base" if p.user_point else "Cliente"
            print(f"    - {tipo}: ({p.latitude}, {p.longitude}) - id_user: {p.id_user}")
    else:
        print("  ⚠️ Nenhum ponto encontrado")
    
    print("\n" + "-"*80 + "\n")
    
    # Verifica polígonos (áreas/grupos)
    print("🗺️ POLÍGONOS/GRUPOS (Polygon):")
    polygons = Polygon.query.all()
    if polygons:
        print(f"  Total: {len(polygons)} áreas")
        user_counts = {}
        for p in polygons:
            user_counts[p.user_id] = user_counts.get(p.user_id, 0) + 1
        
        for uid, count in user_counts.items():
            print(f"  - user_id {uid}: {count} áreas")
            
        # Mostra alguns exemplos
        print("\n  Exemplos:")
        for p in polygons:
            print(f"    - {p.group_name} (ID: {p.id}, user_id: {p.user_id})")
    else:
        print("  ⚠️ Nenhuma área encontrada")
    
    print("\n" + "="*80)
    print("✅ VERIFICAÇÃO CONCLUÍDA")
    print("="*80 + "\n")
    
    # Verifica especificamente user_id = 1
    print("\n" + "="*80)
    print("🔎 DADOS ESPECÍFICOS DO USER_ID = 1")
    print("="*80 + "\n")
    
    clients_user1 = ClientName.query.filter_by(user_id=1).all()
    print(f"📋 Clientes: {len(clients_user1)}")
    
    points_user1 = LatLong.query.filter_by(id_user=1).all()
    print(f"📍 Pontos: {len(points_user1)}")
    
    polygons_user1 = Polygon.query.filter_by(user_id=1).all()
    print(f"🗺️ Áreas: {len(polygons_user1)}")
    
    print("\n" + "="*80 + "\n")
