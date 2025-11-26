"""Script para testar contagem de clientes dentro de polígonos"""

from app import create_app
from base.models import db, Polygon, LatLong, ClientName
from ml.geo_utils import GeoUtils
import json

app = create_app()

with app.app_context():
    print('🧪 Testando Contagem de Clientes em Polígonos\n')
    
    # Busca o polígono
    polygons = Polygon.query.all()
    print(f'📊 Total de polígonos no banco: {len(polygons)}')
    
    if len(polygons) == 0:
        print('❌ Nenhum polígono encontrado!')
        exit(1)
    
    for poly in polygons:
        print(f'\n📍 Polígono: {poly.group_name} (ID: {poly.id})')
        print(f'   User ID: {poly.user_id}')
        
        # Parse GeoJSON
        geojson = json.loads(poly.geojson_data)
        coords = geojson['geometry']['coordinates'][0]
        print(f'   Coordenadas: {len(coords)} pontos')
        print(f'   Primeira coordenada: {coords[0]}')
        print(f'   Última coordenada: {coords[-1]}')
        
        # Converte para formato [lat, lng]
        polygon_coords = [[coord[1], coord[0]] for coord in coords]
        
        # Busca todos os clientes
        clients = LatLong.query.filter_by(user_point=False).all()
        print(f'\n👥 Total de clientes no banco: {len(clients)}')
        
        # Prepara dados para GeoUtils
        clients_data = [{
            'id': c.id,
            'latitude': c.latitude,
            'longitude': c.longitude,
            'hash_client': c.hash_client
        } for c in clients]
        
        polygons_data = [{
            'id': poly.id,
            'name': poly.group_name,
            'coordinates': polygon_coords
        }]
        
        # Usa GeoUtils para filtrar
        print(f'\n🔍 Usando GeoUtils para filtrar clientes...')
        result = GeoUtils.filter_clients_by_polygons_optimized(clients_data, polygons_data)
        
        # result é um dicionário {polygon_id: [clients]}
        clients_in_poly = result.get(poly.id, [])
        print(f'✅ Clientes dentro do polígono: {len(clients_in_poly)}')
        
        if len(clients_in_poly) > 0:
            print(f'\n📋 Primeiros 5 clientes:')
            for i, client in enumerate(clients_in_poly[:5]):
                print(f'   {i+1}. ID: {client["id"]}, Lat: {client["latitude"]:.6f}, Lng: {client["longitude"]:.6f}')
        
        # Teste manual com Ray Casting
        print(f'\n🧪 Teste manual com Ray Casting...')
        count_manual = 0
        for client in clients_data:
            lat, lng = client['latitude'], client['longitude']
            
            # Ray Casting Algorithm
            inside = False
            j = len(polygon_coords) - 1
            for i in range(len(polygon_coords)):
                xi, yi = polygon_coords[i]
                xj, yj = polygon_coords[j]
                
                intersect = ((yi > lng) != (yj > lng)) and (lat < (xj - xi) * (lng - yi) / (yj - yi) + xi)
                if intersect:
                    inside = not inside
                j = i
            
            if inside:
                count_manual += 1
        
        print(f'✅ Contagem manual (Ray Casting): {count_manual}')
        
        print(f'\n📊 Comparação:')
        print(f'   GeoUtils: {len(clients_in_poly)} clientes')
        print(f'   Ray Casting: {count_manual} clientes')
        
        if len(clients_in_poly) == count_manual:
            print('   ✅ Resultados consistentes!')
        else:
            print('   ⚠️ Diferença detectada!')
