#!/usr/bin/env python3
"""
Script para inicializar o banco de dados e migrações
Execute com: python init_db.py
"""

from app import app, db
from flask_migrate import init, migrate, upgrade
import os

def init_database():
    """Inicializa o banco de dados e migrações"""
    with app.app_context():
        print("🔧 Inicializando sistema de migrações...")
        
        # Verifica se já existe pasta migrations
        if not os.path.exists('migrations'):
            try:
                init()
                print("✅ Sistema de migrações inicializado!")
            except Exception as e:
                print(f"❌ Erro ao inicializar migrações: {e}")
                return False
        else:
            print("ℹ️  Sistema de migrações já existe!")
        
        print("🔧 Criando migração inicial...")
        try:
            migrate(message='Criação inicial das tabelas')
            print("✅ Migração criada!")
        except Exception as e:
            print(f"⚠️  Aviso na criação da migração: {e}")
        
        print("🔧 Aplicando migrações ao banco de dados...")
        try:
            upgrade()
            print("✅ Banco de dados criado e atualizado!")
            print(f"📁 Arquivo do banco: {app.config['SQLALCHEMY_DATABASE_URI']}")
            return True
        except Exception as e:
            print(f"❌ Erro ao aplicar migrações: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Inicializando banco de dados SynapseLog...")
    if init_database():
        print("🎉 Banco de dados configurado com sucesso!")
        print("\n📋 Próximos passos:")
        print("   1. Execute: python app.py")
        print("   2. Acesse: http://localhost:5000")
    else:
        print("💥 Falha na configuração do banco de dados!")