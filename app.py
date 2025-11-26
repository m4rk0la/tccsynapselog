from base.routes import main as main_bp
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config
import os

def create_app(config_name=None):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__, template_folder='base/templates', static_folder='base/static')
    
    # Carrega configuração
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Importa e inicializa extensões
    from base.models import db
    db.init_app(app)
    
    migrate = Migrate()
    migrate.init_app(app, db)
    
    # Configura Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Rota de login
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Função para carregar usuário
    @login_manager.user_loader
    def load_user(user_id):
        from base.models import User
        return User.query.get(int(user_id))
    
    # Desabilita cache para desenvolvimento
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    
    # Registra blueprints
    app.register_blueprint(main_bp)
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
