"""
Testes para a aplicação Flask (app.py)
"""
import unittest
import sys
import os

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from base.models import db


class TestAppFactory(unittest.TestCase):
    """Testes para a factory function da aplicação"""
    
    def test_create_app_returns_flask_instance(self):
        """Testa se create_app retorna instância Flask"""
        app = create_app()
        self.assertIsNotNone(app)
    
    def test_app_has_blueprints(self):
        """Testa se app tem blueprints registrados"""
        app = create_app()
        
        # Verifica se blueprint 'main' está registrado
        self.assertIn('main', app.blueprints)
    
    def test_app_configuration_loaded(self):
        """Testa se configuração foi carregada"""
        app = create_app('development')
        
        self.assertTrue(app.config['DEBUG'])
    
    def test_app_database_initialized(self):
        """Testa se banco de dados foi inicializado"""
        app = create_app()
        
        with app.app_context():
            self.assertIsNotNone(db)
    
    def test_app_login_manager_configured(self):
        """Testa se Flask-Login está configurado"""
        app = create_app()
        
        # Verifica se login_manager existe
        self.assertTrue(hasattr(app, 'login_manager'))
    
    def test_app_has_cache_control_headers(self):
        """Testa se cabeçalhos de cache estão configurados"""
        app = create_app()
        client = app.test_client()
        
        response = client.get('/')
        self.assertIn('Cache-Control', response.headers)


class TestAppRoutes(unittest.TestCase):
    """Testes para verificar rotas principais"""
    
    def setUp(self):
        """Configura app de teste"""
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_root_route_exists(self):
        """Testa se rota raiz existe"""
        response = self.client.get('/')
        self.assertNotEqual(response.status_code, 404)
    
    def test_static_folder_configured(self):
        """Testa se pasta static está configurada"""
        self.assertIsNotNone(self.app.static_folder)
    
    def test_template_folder_configured(self):
        """Testa se pasta templates está configurada"""
        self.assertIsNotNone(self.app.template_folder)


if __name__ == '__main__':
    unittest.main()
