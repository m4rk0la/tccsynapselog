#!/usr/bin/env python3
"""
Script para inicializar os 11 bancos de dados especializados do S                  # Cria produto de exemplo
            print("📦 Criando produto de exemplo...")
            sample_product = Products(
                product_name='Produto Teste',
                product_type='categoria_teste',
                price=99.99
            )Cria produto de exemplo
            print("📦 Criando produto de exemplo...")
            sample_product = Products(
                product_name='Produto Teste',
                product_type='categoria_teste',
                price=99.99
            )g
- Autenticação, Geolocalização, Machine Learning, Logs e mais
Execute com: python init_multiple_dbs.py
"""

from app import create_app
from base.models import db, User, SystemLog, ClientName, LatLong, Routs, KNN, Polygon, Products, Consummer, NDBFeatures, NDBOut
from flask_migrate import init, migrate, upgrade
import os

def init_multiple_databases():
    """Inicializa múltiplos bancos de dados do SynapseLog"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Inicializando múltiplos bancos de dados...")
        
        # Lista dos bancos configurados
        databases = {
            'users_code': 'Usuários e Autenticação',
            'client_name': 'Dados de Clientes (Hash)',
            'latlong': 'Coordenadas Geográficas',
            'routs': 'Rotas Básicas',
            'KNN': 'Rotas Otimizadas (KNN)',
            'polygon': 'Polígonos Geográficos',
            'products': 'Catálogo de Produtos',
            'consummer': 'Dados de Consumo',
            'ml_features': 'Features para Machine Learning',
            'neuraldatabaserout': 'Resultados das Redes Neurais',
            'logs': 'Logs do Sistema'
        }
        
        print(f"📊 Bancos configurados: {len(databases)}")
        for key, desc in databases.items():
            db_path = app.config['SQLALCHEMY_BINDS'][key]
            print(f"   {key}: {desc}")
            print(f"      Caminho: {db_path}")
        
        print("\n🔧 Criando tabelas em todos os bancos...")
        
        try:
            # Cria todas as tabelas em todos os bancos
            db.create_all()
            
            print("✅ Todas as tabelas criadas com sucesso!")
            
            # Verifica se já existe usuário admin
            admin = User.query.filter_by(email='admin@synapselLog.com').first()
            if not admin:
                print("👤 Criando usuário administrador...")
                admin = User(
                    username='admin',
                    email='admin@synapselLog.com',
                    role='admin'
                )
                admin.set_password('123456')
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuário admin criado!")
            else:
                print("ℹ️  Usuário admin já existe!")
            
            # Cria alguns logs de exemplo
            print("📝 Criando logs de exemplo...")
            sample_log = SystemLog(
                user_id=admin.id,
                action='system_init',
                resource='database',
                details='Inicialização dos múltiplos bancos de dados',
                level='INFO'
            )
            db.session.add(sample_log)
            
            # Cria cliente de exemplo
            print("🏢 Criando cliente de exemplo...")
            sample_client = ClientName(
                name_client='Cliente Teste',
                hash_client='hash_cliente_teste_001'
            )
            db.session.add(sample_client)
            
            # Cria coordenada de exemplo
            print("🗺️ Criando coordenada de exemplo...")
            sample_location = LatLong(
                id_user=admin.id,
                hash_client='hash_cliente_teste_001',
                latitude=-23.5505,
                longitude=-46.6333,
                user_point=True  # True = infraestrutura física (loja/galpão)
            )
            db.session.add(sample_location)
            
            # Cria produto de exemplo
            print("� Criando produto de exemplo...")
            sample_product = Products(
                product_name='Produto Teste',
                product_type='categoria_teste',
                price=99.99,
            )
            db.session.add(sample_product)
            
            db.session.commit()
            print("✅ Dados de exemplo criados!")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar bancos: {e}")
            return False

def list_database_contents():
    """Lista o conteúdo de todos os bancos"""
    app = create_app()
    
    with app.app_context():
        print("\n📋 Resumo dos bancos de dados:")
        
        # Contagem de usuários
        user_count = User.query.count()
        print(f"👥 Usuários: {user_count}")
        
        # Contagem de logs
        log_count = SystemLog.query.count()
        print(f"📝 Logs: {log_count}")
        
        # Contagem de clientes
        client_count = ClientName.query.count()
        print(f"🏢 Clientes: {client_count}")
        
        # Contagem de coordenadas
        location_count = LatLong.query.count()
        print(f"🗺️ Coordenadas: {location_count}")
        
        # Contagem de rotas
        routes_count = Routs.query.count()
        print(f"🛣️ Rotas: {routes_count}")
        
        # Contagem de produtos
        products_count = Products.query.count()
        print(f"📦 Produtos: {products_count}")
        
        # Contagem de polígonos
        polygon_count = Polygon.query.count()
        print(f"📐 Polígonos: {polygon_count}")
        
        # Contagem de dados de consumo
        consumer_count = Consummer.query.count()
        print(f"� Dados de consumo: {consumer_count}")
        
        # Contagem de features neurais
        neural_count = NDBFeatures.query.count()
        print(f"🧠 Features neurais: {neural_count}")

if __name__ == "__main__":
    print("🚀 Inicializando sistema SynapseLog com múltiplos bancos...")
    
    if init_multiple_databases():
        print("\n🎉 Sistema inicializado com sucesso!")
        list_database_contents()
        
        print("\n📁 Localização dos bancos:")
        print("   � databases/synapselLog_users_code.db")
        print("   🏢 databases/synapselLog_client_name.db")
        print("   �️ databases/synapselLog_latlong.db")
        print("   🛣️ databases/synapselLog_routs.db")
        print("   🚚 databases/synapselLog_routswclient.db")
        print("   � databases/synapselLog_polygon.db")
        print("   📦 databases/synapselLog_products.db")
        print("   � databases/synapselLog_consummer.db")
        print("   🧠 databases/synapselLog_neuraldatabase.db")
        print("   🤖 databases/synapselLog_neuraldatabaserout.db")
        print("   📝 databases/synapselLog_logs.db")
        
        print("\n🔑 Credenciais de acesso:")
        print("   Email: admin@synapselLog.com")
        print("   Senha: 123456")
        print("\n🌐 Acesse: http://localhost:5000")
    else:
        print("💥 Falha na inicialização!")