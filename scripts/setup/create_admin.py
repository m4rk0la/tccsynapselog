#!/usr/bin/env python3
"""
Script para criar um usuário administrador
Execute com: python create_admin.py
"""

from app import create_app
from base.models import User, db

def create_admin_user():
    """Cria um usuário administrador para testar o sistema"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Criando usuário administrador...")
        
        # Verifica se já existe um admin
        admin = User.query.filter_by(email='admin@synapselLog.com').first()
        if admin:
            print("ℹ️  Usuário admin já existe!")
            print(f"   Email: admin@synapselLog.com")
            print(f"   Username: {admin.username}")
            return
        
        # Cria novo usuário admin
        admin = User(
            username='admin',
            email='admin@synapselLog.com'
        )
        admin.set_password('123456')  # MUDE EM PRODUÇÃO!
        
        try:
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário administrador criado com sucesso!")
            print("📧 Email: admin@synapselLog.com")
            print("🔑 Senha: 123456")
            print("⚠️  IMPORTANTE: Mude a senha em produção!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar usuário: {e}")

if __name__ == "__main__":
    print("👤 Criando usuário administrador para SynapseLog...")
    create_admin_user()
    print("\n🚀 Agora você pode fazer login em: http://localhost:5000")