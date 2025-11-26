import os
from datetime import timedelta

class Config:
    """Configuração base da aplicação Flask"""
    
    # Chave secreta para sessões e formulários (MUDE PARA PRODUÇÃO!)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-muito-segura-aqui'
    
    # Diretório base e pasta de bancos de dados
    basedir = os.path.abspath(os.path.dirname(__file__))
    databases_dir = os.path.join(basedir, 'databases')
    
    # Certificar que a pasta de bancos existe
    os.makedirs(databases_dir, exist_ok=True)
    
    # Configuração do banco de dados principal (usuários e autenticação)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(databases_dir, 'synapselLog_users_code.db')
    
    # Configuração para múltiplos bancos de dados
    SQLALCHEMY_BINDS = {
        'users_code': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_users_code.db'),
        'client_name': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_client_name.db'),
        'products': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_products.db'),
        'consummer': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_consummer.db'),
        'routs': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_routs.db'),
        'latlong': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_latlong.db'),
        'KNN': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_KNN.db'),
        'polygon': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_polygon.db'),
        'ml_features': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_neuraldatabase.db'),
        'neuraldatabaserout': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_neuraldatabaserout.db'),
        'order_history': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_order_history.db'),
        'logs': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_logs.db'),
        'client_scores': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_client_scores.db'),
        'saved_calendars': 'sqlite:///' + os.path.join(databases_dir, 'synapselLog_saved_calendars.db')
    }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações do SQLite para melhor performance e evitar locks
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'timeout': 30,  # Timeout de 30 segundos
            'check_same_thread': False
        },
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }

    # Configuração de sessão permanente
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}