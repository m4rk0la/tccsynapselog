"""
Testes para configuração da aplicação (config.py)
"""
import unittest
import os
from config import Config, DevelopmentConfig, ProductionConfig, config


class TestConfig(unittest.TestCase):
    """Testes para configuração base"""
    
    def test_config_has_secret_key(self):
        """Testa se configuração tem SECRET_KEY"""
        self.assertIsNotNone(Config.SECRET_KEY)
    
    def test_config_has_database_uri(self):
        """Testa se configuração tem URI do banco"""
        self.assertIsNotNone(Config.SQLALCHEMY_DATABASE_URI)
    
    def test_config_has_binds(self):
        """Testa se configuração tem múltiplos bancos"""
        self.assertIsNotNone(Config.SQLALCHEMY_BINDS)
        self.assertIsInstance(Config.SQLALCHEMY_BINDS, dict)
    
    def test_databases_directory_created(self):
        """Testa se diretório de bancos foi criado"""
        self.assertTrue(os.path.exists(Config.databases_dir))
    
    def test_all_binds_configured(self):
        """Testa se todos os bancos necessários estão configurados"""
        required_binds = [
            'users_code', 'client_name', 'products', 'consummer',
            'routs', 'latlong', 'KNN', 'polygon', 'ml_features',
            'neuraldatabaserout', 'order_history', 'logs',
            'client_scores', 'saved_calendars'
        ]
        
        for bind in required_binds:
            self.assertIn(bind, Config.SQLALCHEMY_BINDS)
    
    def test_track_modifications_disabled(self):
        """Testa se track modifications está desabilitado"""
        self.assertFalse(Config.SQLALCHEMY_TRACK_MODIFICATIONS)


class TestDevelopmentConfig(unittest.TestCase):
    """Testes para configuração de desenvolvimento"""
    
    def test_development_debug_enabled(self):
        """Testa se DEBUG está habilitado em desenvolvimento"""
        self.assertTrue(DevelopmentConfig.DEBUG)
    
    def test_development_inherits_base(self):
        """Testa se herda configuração base"""
        self.assertTrue(hasattr(DevelopmentConfig, 'SECRET_KEY'))
        self.assertTrue(hasattr(DevelopmentConfig, 'SQLALCHEMY_BINDS'))


class TestProductionConfig(unittest.TestCase):
    """Testes para configuração de produção"""
    
    def test_production_debug_disabled(self):
        """Testa se DEBUG está desabilitado em produção"""
        self.assertFalse(ProductionConfig.DEBUG)
    
    def test_production_inherits_base(self):
        """Testa se herda configuração base"""
        self.assertTrue(hasattr(ProductionConfig, 'SECRET_KEY'))


class TestConfigDictionary(unittest.TestCase):
    """Testes para dicionário de configurações"""
    
    def test_config_dict_has_environments(self):
        """Testa se dicionário tem ambientes configurados"""
        self.assertIn('development', config)
        self.assertIn('production', config)
        self.assertIn('default', config)
    
    def test_default_is_development(self):
        """Testa se padrão é desenvolvimento"""
        self.assertEqual(config['default'], DevelopmentConfig)


if __name__ == '__main__':
    unittest.main()
