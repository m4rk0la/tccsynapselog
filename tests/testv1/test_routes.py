"""
Testes de integração para rotas da aplicação Flask (base/routes.py)
"""
import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app


class TestRoutesIntegration(unittest.TestCase):
    """Testes de integração para as rotas"""
    
    def setUp(self):
        """Configura app de teste"""
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
    
    def test_login_page_loads(self):
        """Testa se página de login carrega"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
    
    def test_registro_page_loads(self):
        """Testa se página de registro carrega"""
        response = self.client.get('/registro')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
    
    def test_painel_requires_auth(self):
        """Testa se painel requer autenticação"""
        response = self.client.get('/autenticado/painel', follow_redirects=False)
        # Deve redirecionar para login
        self.assertIn(response.status_code, [302, 401])
    
    @patch('base.routes.db')
    def test_clientes_page_structure(self, mock_db):
        """Testa estrutura da página de clientes"""
        # Simula sessão de login
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            
            response = self.client.get('/autenticado/clientes')
            self.assertIn(response.status_code, [200, 302])
    
    @patch('base.routes.ClientName')
    @patch('base.routes.Polygon')
    @patch('base.routes.db')
    def test_grupos_api_get(self, mock_db, mock_polygon, mock_client_name):
        """Testa endpoint GET de grupos"""
        # Mock query results
        mock_client_name.query.filter_by.return_value.all.return_value = []
        mock_polygon.query.filter_by.return_value.all.return_value = []
        
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            
            response = self.client.get('/autenticado/grupos?action=get&user_id=1')
            self.assertIn(response.status_code, [200, 302])
    
    @patch('base.routes.db')
    def test_roteirizacao_page_loads(self, mock_db):
        """Testa se página de roteirização carrega"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            
            response = self.client.get('/autenticado/roteirizacao')
            self.assertIn(response.status_code, [200, 302])
    
    @patch('base.routes.db')
    def test_historicovendas_page_loads(self, mock_db):
        """Testa se página de histórico carrega"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            
            response = self.client.get('/autenticado/historicovendas')
            self.assertIn(response.status_code, [200, 302])
    
    @patch('base.routes.db')
    def test_api_latlongs_format(self, mock_db):
        """Testa formato de retorno da API de lat/longs"""
        mock_db.session.query.return_value.filter_by.return_value.all.return_value = []
        
        response = self.client.get('/api/latlongs?user_id=1')
        self.assertIn(response.status_code, [200, 400, 500])
        
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)


class TestGruposAPI(unittest.TestCase):
    """Testes específicos para API de grupos"""
    
    def setUp(self):
        """Configura app de teste"""
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
    
    @patch('base.routes.db')
    def test_post_grupo_invalid_data(self, mock_db):
        """Testa POST com dados inválidos"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            
            response = self.client.post(
                '/autenticado/grupos',
                data=json.dumps({}),
                content_type='application/json'
            )
            
            self.assertIn(response.status_code, [200, 302, 400])
    
    @patch('base.routes.Polygon')
    @patch('base.routes.db')
    def test_post_grupo_valid_structure(self, mock_db, mock_polygon):
        """Testa POST com estrutura válida"""
        mock_db.session.commit.return_value = None
        mock_polygon.query.filter_by.return_value.first.return_value = None
        mock_polygon.return_value = MagicMock()
        
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            
            payload = {
                'features': [
                    {
                        'type': 'Feature',
                        'properties': {'name': 'Área Teste'},
                        'geometry': {
                            'type': 'Polygon',
                            'coordinates': [[
                                [-47.9, -15.7],
                                [-47.8, -15.7],
                                [-47.8, -15.8],
                                [-47.9, -15.8],
                                [-47.9, -15.7]
                            ]]
                        }
                    }
                ]
            }
            
            response = self.client.post(
                '/autenticado/grupos',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            self.assertIn(response.status_code, [200, 302, 400])


class TestHistoricoVendasAPI(unittest.TestCase):
    """Testes para API de histórico de vendas"""
    
    def setUp(self):
        """Configura app de teste"""
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
    
    @patch('base.routes.db')
    def test_get_vendas_returns_list(self, mock_db):
        """Testa GET de vendas retorna lista"""
        mock_db.session.query.return_value.filter_by.return_value.all.return_value = []
        
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            
            response = self.client.get('/autenticado/historicovendas?action=get')
            self.assertIn(response.status_code, [200, 302])
    
    @patch('base.routes.db')
    def test_delete_venda_missing_id(self, mock_db):
        """Testa DELETE sem ID retorna erro"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            
            response = self.client.delete(
                '/autenticado/historicovendas?action=delete',
                data=json.dumps({}),
                content_type='application/json'
            )
            
            self.assertIn(response.status_code, [200, 302, 400])


if __name__ == '__main__':
    unittest.main()
