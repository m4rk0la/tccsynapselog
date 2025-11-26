"""
Script para limpar áreas duplicadas do banco de dados
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from base.models import db, Polygon
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("🔍 Buscando áreas duplicadas...")
    
    # Busca todos os grupos do usuário
    user_id = 1  # Altere se necessário
    
    # Agrupa por user_id e group_name
    duplicates = db.session.query(
        Polygon.user_id,
        Polygon.group_name,
        func.count(Polygon.id).label('count')
    ).group_by(
        Polygon.user_id,
        Polygon.group_name
    ).having(
        func.count(Polygon.id) > 1
    ).all()
    
    if not duplicates:
        print("✅ Nenhuma área duplicada encontrada!")
    else:
        print(f"⚠️  Encontradas {len(duplicates)} áreas com duplicações:")
        
        for dup in duplicates:
            print(f"\n📍 user_id={dup.user_id}, group_name='{dup.group_name}' tem {dup.count} cópias")
            
            # Busca todas as áreas com esse nome
            areas = Polygon.query.filter_by(
                user_id=dup.user_id,
                group_name=dup.group_name
            ).order_by(Polygon.created_at.desc()).all()
            
            # Mantém apenas a mais recente
            if areas:
                keep = areas[0]
                print(f"   ✓ Mantendo: ID={keep.id} (criado em {keep.created_at})")
                
                for area in areas[1:]:
                    print(f"   ✗ Removendo: ID={area.id} (criado em {area.created_at})")
                    db.session.delete(area)
        
        # Confirma antes de deletar
        response = input("\n⚠️  Deseja REALMENTE excluir as áreas duplicadas? (digite 'SIM' para confirmar): ")
        
        if response.strip().upper() == 'SIM':
            db.session.commit()
            print("\n✅ Áreas duplicadas removidas com sucesso!")
        else:
            db.session.rollback()
            print("\n❌ Operação cancelada. Nenhuma alteração foi feita.")
    
    # Mostra estatísticas finais
    print("\n📊 Estatísticas finais:")
    all_areas = Polygon.query.all()
    users_with_areas = db.session.query(Polygon.user_id, func.count(Polygon.id)).group_by(Polygon.user_id).all()
    
    print(f"   Total de áreas: {len(all_areas)}")
    for user, count in users_with_areas:
        print(f"   user_id={user}: {count} área(s)")
