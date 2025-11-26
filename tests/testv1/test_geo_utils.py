"""
Testes para utilitários geográficos (ml/geo_utils.py)
"""
import unittest
from ml.geo_utils import GeoUtils


class TestPointInPolygon(unittest.TestCase):
    """Testes para verificação de ponto em polígono"""
    
    def setUp(self):
        """Define polígono retangular de teste"""
        # Retângulo em torno de Brasília
        self.square_polygon = [
            [-15.7, -47.9],  # Superior esquerdo
            [-15.7, -47.8],  # Superior direito
            [-15.8, -47.8],  # Inferior direito
            [-15.8, -47.9],  # Inferior esquerdo
            [-15.7, -47.9]   # Fecha o polígono
        ]
    
    def test_point_inside_polygon(self):
        """Testa ponto claramente dentro do polígono"""
        result = GeoUtils.point_in_polygon_fast(
            -15.75, -47.85, self.square_polygon
        )
        self.assertTrue(result)
    
    def test_point_outside_polygon(self):
        """Testa ponto claramente fora do polígono"""
        result = GeoUtils.point_in_polygon_fast(
            -15.6, -47.7, self.square_polygon
        )
        self.assertFalse(result)
    
    def test_point_on_edge(self):
        """Testa ponto na borda do polígono"""
        result = GeoUtils.point_in_polygon_fast(
            -15.7, -47.85, self.square_polygon
        )
        # Comportamento de borda pode variar, mas deve retornar bool
        self.assertIsInstance(result, bool)


class TestBoundingBox(unittest.TestCase):
    """Testes para cálculo de bounding box"""
    
    def test_calculate_bbox(self):
        """Testa cálculo de bbox simples"""
        coords = [
            [-15.7, -47.9],
            [-15.8, -47.8],
            [-15.75, -47.85]
        ]
        
        bbox = GeoUtils.calculate_bbox(coords)
        
        self.assertEqual(bbox['min_lat'], -15.8)
        self.assertEqual(bbox['max_lat'], -15.7)
        self.assertEqual(bbox['min_lon'], -47.9)
        self.assertEqual(bbox['max_lon'], -47.8)
    
    def test_bbox_empty_coords(self):
        """Testa bbox com coordenadas vazias"""
        bbox = GeoUtils.calculate_bbox([])
        self.assertIsNone(bbox)
    
    def test_point_in_bbox(self):
        """Testa se ponto está dentro do bbox"""
        bbox = {
            'min_lat': -15.8,
            'max_lat': -15.7,
            'min_lon': -47.9,
            'max_lon': -47.8
        }
        
        # Ponto dentro
        self.assertTrue(GeoUtils.point_in_bbox(-15.75, -47.85, bbox))
        
        # Ponto fora
        self.assertFalse(GeoUtils.point_in_bbox(-15.6, -47.7, bbox))


class TestFilterClientsByPolygons(unittest.TestCase):
    """Testes para filtragem de clientes por polígonos"""
    
    def setUp(self):
        """Define dados de teste"""
        self.clients = [
            {'id': 1, 'latitude': -15.75, 'longitude': -47.85, 'hash_client': 'cli1'},
            {'id': 2, 'latitude': -15.6, 'longitude': -47.7, 'hash_client': 'cli2'},
            {'id': 3, 'latitude': -15.77, 'longitude': -47.87, 'hash_client': 'cli3'}
        ]
        
        self.polygons = [
            {
                'id': 1,
                'name': 'Área 1',
                'coordinates': [
                    [-15.7, -47.9],
                    [-15.7, -47.8],
                    [-15.8, -47.8],
                    [-15.8, -47.9],
                    [-15.7, -47.9]
                ]
            }
        ]
    
    def test_filter_clients_basic(self):
        """Testa filtragem básica de clientes"""
        result = GeoUtils.filter_clients_by_polygons_optimized(
            self.clients, self.polygons
        )
        
        self.assertIn(1, result)
        self.assertIsInstance(result[1], list)
    
    def test_filter_returns_correct_clients(self):
        """Testa se retorna apenas clientes dentro do polígono"""
        result = GeoUtils.filter_clients_by_polygons_optimized(
            self.clients, self.polygons
        )
        
        # Cliente 1 e 3 devem estar dentro, cliente 2 fora
        polygon_clients = result[1]
        client_ids = [c['id'] for c in polygon_clients]
        
        self.assertIn(1, client_ids)
        self.assertIn(3, client_ids)
        self.assertNotIn(2, client_ids)
    
    def test_filter_empty_clients(self):
        """Testa com lista vazia de clientes"""
        result = GeoUtils.filter_clients_by_polygons_optimized(
            [], self.polygons
        )
        
        self.assertEqual(result[1], [])
    
    def test_filter_empty_polygons(self):
        """Testa com lista vazia de polígonos"""
        result = GeoUtils.filter_clients_by_polygons_optimized(
            self.clients, []
        )
        
        self.assertEqual(result, {})
    
    def test_filter_invalid_coordinates(self):
        """Testa com coordenadas inválidas"""
        invalid_clients = [
            {'id': 1, 'latitude': None, 'longitude': -47.85},
            {'id': 2, 'latitude': -15.75, 'longitude': None}
        ]
        
        result = GeoUtils.filter_clients_by_polygons_optimized(
            invalid_clients, self.polygons
        )
        
        # Não deve lançar exceção, apenas ignorar clientes inválidos
        self.assertEqual(result[1], [])


class TestBatchAssignClients(unittest.TestCase):
    """Testes para atribuição em lote de clientes a polígonos"""
    
    def test_batch_assign_format(self):
        """Testa formato de retorno da atribuição em lote"""
        from ml.geo_utils import batch_assign_clients_to_polygons
        
        clients = [
            {'id': 1, 'latitude': -15.75, 'longitude': -47.85, 'hash_client': 'cli1'}
        ]
        
        polygons = [
            {
                'id': 1,
                'coordinates': [
                    [-15.7, -47.9],
                    [-15.7, -47.8],
                    [-15.8, -47.8],
                    [-15.8, -47.9],
                    [-15.7, -47.9]
                ]
            }
        ]
        
        result = batch_assign_clients_to_polygons(clients, polygons)
        
        self.assertIsInstance(result, list)
        if len(result) > 0:
            self.assertIn('client_id', result[0])
            self.assertIn('polygon_id', result[0])
            self.assertIn('client_hash', result[0])


if __name__ == '__main__':
    unittest.main()
