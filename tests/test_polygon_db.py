"""Script para testar o banco de dados de polígonos"""

from app import create_app
from base.models import db, Polygon

app = create_app()

with app.app_context():
    print('✅ Conexão com banco de dados OK')
    
    try:
        polygons = Polygon.query.all()
        print(f'\n📊 Total de polígonos no banco: {len(polygons)}')
        
        if len(polygons) > 0:
            print('\n📍 Polígonos encontrados:')
            for p in polygons:
                print(f'  - ID: {p.id}, Nome: {p.group_name}, User: {p.user_id}, Criado: {p.created_at}')
        else:
            print('\n⚠️ Nenhum polígono encontrado no banco de dados')
            
    except Exception as e:
        print(f'\n❌ Erro ao consultar banco: {e}')
        import traceback
        traceback.print_exc()
