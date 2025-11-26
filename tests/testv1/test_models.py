"""
Testes para os modelos do banco de dados (base/models.py)
"""
import unittest
from datetime import datetime
from unittest.mock import MagicMock

# Desabilita conexão real com banco para testes unitários
import sys
sys.modules['flask_sqlalchemy'] = MagicMock()

from base.models import User, ClientName, LatLong, Polygon, OrderHistory, ClientScore, SavedCalendar


class TestUserModel(unittest.TestCase):
    """Testes para o modelo User"""
    
    def test_user_creation(self):
        """Testa criação básica de usuário"""
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('senha123')
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertIsNotNone(user.password_hash)
    
    def test_password_hashing(self):
        """Testa se senha é hashada corretamente"""
        user = User(username='test', email='test@example.com')
        user.set_password('senha123')
        
        self.assertNotEqual(user.password_hash, 'senha123')
        self.assertTrue(user.check_password('senha123'))
        self.assertFalse(user.check_password('senha_errada'))
    
    def test_user_repr(self):
        """Testa representação string do usuário"""
        user = User(username='testuser', email='test@example.com')
        self.assertEqual(repr(user), '<User testuser>')


class TestClientNameModel(unittest.TestCase):
    """Testes para o modelo ClientName"""
    
    def test_client_creation(self):
        """Testa criação de cliente"""
        client = ClientName(
            name_client='Cliente Teste',
            hash_client='abc123',
            user_id=1,
            cidade='Brasília',
            estado='DF'
        )
        
        self.assertEqual(client.name_client, 'Cliente Teste')
        self.assertEqual(client.cidade, 'Brasília')
        self.assertEqual(client.estado, 'DF')
    
    def test_client_repr(self):
        """Testa representação do cliente"""
        client = ClientName(
            name_client='Cliente XYZ',
            hash_client='xyz789',
            user_id=1
        )
        self.assertEqual(repr(client), '<ClientName Cliente XYZ>')


class TestLatLongModel(unittest.TestCase):
    """Testes para o modelo LatLong"""
    
    def test_latlong_creation(self):
        """Testa criação de ponto geográfico"""
        point = LatLong(
            id_user=1,
            hash_client='abc123',
            latitude=-15.7942,
            longitude=-47.8822,
            user_point=False
        )
        
        self.assertEqual(point.latitude, -15.7942)
        self.assertEqual(point.longitude, -47.8822)
        self.assertFalse(point.user_point)
    
    def test_latlong_user_point(self):
        """Testa marcação de ponto base"""
        base_point = LatLong(
            id_user=1,
            latitude=-15.7942,
            longitude=-47.8822,
            user_point=True
        )
        
        self.assertTrue(base_point.user_point)


class TestPolygonModel(unittest.TestCase):
    """Testes para o modelo Polygon"""
    
    def test_polygon_creation(self):
        """Testa criação de polígono"""
        geojson_data = '{"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}'
        polygon = Polygon(
            user_id=1,
            group_name='Área Teste',
            geojson_data=geojson_data
        )
        
        self.assertEqual(polygon.group_name, 'Área Teste')
        self.assertIsNotNone(polygon.geojson_data)
    
    def test_polygon_max_clients(self):
        """Testa configuração de limite de clientes"""
        polygon = Polygon(
            user_id=1,
            group_name='Área Limitada',
            geojson_data='{}',
            max_clients_per_day=15
        )
        
        self.assertEqual(polygon.max_clients_per_day, 15)


class TestOrderHistoryModel(unittest.TestCase):
    """Testes para o modelo OrderHistory"""
    
    def test_order_creation(self):
        """Testa criação de pedido"""
        order = OrderHistory(
            user_id=1,
            id_pedido='PED001',
            hash_cliente='cli123',
            id_cliente='CLI001',
            id_unico_cliente='UNICO001',
            data_compra=datetime(2024, 1, 15),
            valor_total_pagamento=150.50,
            status_pedido='delivered'
        )
        
        self.assertEqual(order.id_pedido, 'PED001')
        self.assertEqual(order.valor_total_pagamento, 150.50)
        self.assertEqual(order.status_pedido, 'delivered')
    
    def test_order_with_review(self):
        """Testa pedido com avaliação"""
        order = OrderHistory(
            user_id=1,
            id_pedido='PED002',
            hash_cliente='cli456',
            id_cliente='CLI002',
            id_unico_cliente='UNICO002',
            nota_avaliacao=5,
            titulo_comentario='Excelente!',
            mensagem_comentario='Produto chegou rápido'
        )
        
        self.assertEqual(order.nota_avaliacao, 5)
        self.assertEqual(order.titulo_comentario, 'Excelente!')


class TestClientScoreModel(unittest.TestCase):
    """Testes para o modelo ClientScore"""
    
    def test_score_creation(self):
        """Testa criação de score RFM"""
        score = ClientScore(
            hash_cliente='cli123',
            user_id=1,
            score_total=85.5,
            score_recencia=90.0,
            score_frequencia=80.0,
            score_valor=85.0,
            score_satisfacao=87.0,
            total_pedidos=15,
            valor_total_vendas=5000.00,
            ticket_medio=333.33
        )
        
        self.assertEqual(score.score_total, 85.5)
        self.assertEqual(score.total_pedidos, 15)
    
    def test_get_segmento_vip(self):
        """Testa classificação de segmento VIP"""
        score = ClientScore(
            hash_cliente='vip001',
            user_id=1,
            score_total=85.0
        )
        
        self.assertEqual(score.get_segmento(), 'VIP')
    
    def test_get_segmento_alto_valor(self):
        """Testa classificação de segmento Alto Valor"""
        score = ClientScore(
            hash_cliente='alto001',
            user_id=1,
            score_total=70.0
        )
        
        self.assertEqual(score.get_segmento(), 'Alto Valor')
    
    def test_get_segmento_medio(self):
        """Testa classificação de segmento Médio"""
        score = ClientScore(
            hash_cliente='medio001',
            user_id=1,
            score_total=50.0
        )
        
        self.assertEqual(score.get_segmento(), 'Médio')
    
    def test_get_segmento_em_risco(self):
        """Testa classificação de segmento Em Risco"""
        score = ClientScore(
            hash_cliente='risco001',
            user_id=1,
            score_total=30.0
        )
        
        self.assertEqual(score.get_segmento(), 'Em Risco')
    
    def test_to_dict(self):
        """Testa serialização para JSON"""
        score = ClientScore(
            hash_cliente='cli123',
            user_id=1,
            score_total=75.0,
            score_recencia=80.0,
            total_pedidos=10
        )
        
        result = score.to_dict()
        
        self.assertIn('hash_cliente', result)
        self.assertIn('score_total', result)
        self.assertIn('segmento', result)
        self.assertEqual(result['segmento'], 'Alto Valor')


class TestSavedCalendarModel(unittest.TestCase):
    """Testes para o modelo SavedCalendar"""
    
    def test_calendar_creation(self):
        """Testa criação de calendário salvo"""
        calendar = SavedCalendar(
            user_id=1,
            nome='Calendário Janeiro 2024',
            configuracao='{"dias": 30, "incluir_sabado": true}',
            alocacoes='[{"dia": 1, "cluster_id": 1}]',
            total_clusters=10,
            total_clientes=150
        )
        
        self.assertEqual(calendar.nome, 'Calendário Janeiro 2024')
        self.assertEqual(calendar.total_clusters, 10)
        self.assertEqual(calendar.total_clientes, 150)
    
    def test_calendar_to_dict(self):
        """Testa serialização do calendário"""
        calendar = SavedCalendar(
            user_id=1,
            nome='Teste',
            configuracao='{"dias": 30}',
            alocacoes='[]',
            total_clusters=5,
            total_clientes=50
        )
        
        result = calendar.to_dict()
        
        self.assertIn('nome', result)
        self.assertIn('configuracao', result)
        self.assertIn('total_clusters', result)


if __name__ == '__main__':
    unittest.main()
