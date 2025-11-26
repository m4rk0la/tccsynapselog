#!/usr/bin/env python3
"""
Script para gerenciar múltiplos bancos de dados do SynapseLog
Execute com: python manage_databases.py
"""

from app import create_app
from base.models import db, User, SystemLog, DataEntry, AnalyticsData
import os
from datetime import datetime

def show_database_info():
    """Exibe informações detalhadas dos bancos"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🗄️  SISTEMA DE MÚLTIPLOS BANCOS DE DADOS - SYNAPSELLOG")
        print("=" * 60)
        
        databases = app.config['SQLALCHEMY_BINDS']
        
        for key, uri in databases.items():
            file_path = uri.replace('sqlite:///', '')
            file_exists = os.path.exists(file_path)
            file_size = os.path.getsize(file_path) if file_exists else 0
            
            print(f"\n📊 BANCO: {key.upper()}")
            print(f"   📍 Caminho: {file_path}")
            print(f"   📏 Tamanho: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            print(f"   ✅ Status: {'Existe' if file_exists else 'Não encontrado'}")
            
            if file_exists:
                try:
                    if key == 'users':
                        count = User.query.count()
                        last_user = User.query.order_by(User.created_at.desc()).first()
                        print(f"   👥 Total de usuários: {count}")
                        if last_user:
                            print(f"   🆕 Último usuário: {last_user.username}")
                    
                    elif key == 'logs':
                        count = SystemLog.query.count()
                        last_log = SystemLog.query.order_by(SystemLog.timestamp.desc()).first()
                        print(f"   📝 Total de logs: {count}")
                        if last_log:
                            print(f"   🕒 Último log: {last_log.action} - {last_log.timestamp}")
                    
                    elif key == 'data':
                        count = DataEntry.query.count()
                        last_entry = DataEntry.query.order_by(DataEntry.created_at.desc()).first()
                        print(f"   📊 Total de entradas: {count}")
                        if last_entry:
                            print(f"   📄 Última entrada: {last_entry.title}")
                    
                    elif key == 'analytics':
                        count = AnalyticsData.query.count()
                        last_event = AnalyticsData.query.order_by(AnalyticsData.timestamp.desc()).first()
                        print(f"   📈 Total de eventos: {count}")
                        if last_event:
                            print(f"   🎯 Último evento: {last_event.event_type}")
                
                except Exception as e:
                    print(f"   ⚠️  Erro ao ler dados: {e}")

def create_sample_data():
    """Cria dados de exemplo em todos os bancos"""
    app = create_app()
    
    with app.app_context():
        print("\n🔧 Criando dados de exemplo...")
        
        try:
            # Logs de exemplo
            sample_logs = [
                SystemLog(action='user_login', resource='authentication', level='INFO', 
                         details='Login de usuário admin'),
                SystemLog(action='data_create', resource='data_entry', level='INFO',
                         details='Nova entrada de dados criada'),
                SystemLog(action='system_backup', resource='database', level='INFO',
                         details='Backup automático realizado')
            ]
            
            for log in sample_logs:
                db.session.add(log)
            
            # Dados de exemplo
            sample_data = [
                DataEntry(title='Projeto Alpha', content='Descrição do projeto Alpha',
                         category='projetos', created_by=1, tags='projeto,alpha,desenvolvimento'),
                DataEntry(title='Relatório Q3', content='Relatório trimestral Q3 2025',
                         category='relatorios', created_by=1, tags='relatório,q3,2025'),
                DataEntry(title='Manual do Sistema', content='Documentação técnica',
                         category='documentacao', created_by=1, tags='manual,documentação,sistema')
            ]
            
            for data in sample_data:
                db.session.add(data)
            
            # Analytics de exemplo
            sample_analytics = [
                AnalyticsData(event_type='page_view', page_url='/painel', user_id=1),
                AnalyticsData(event_type='button_click', event_data='{"button": "save"}', user_id=1),
                AnalyticsData(event_type='form_submit', event_data='{"form": "contact"}', user_id=1)
            ]
            
            for analytics in sample_analytics:
                db.session.add(analytics)
            
            db.session.commit()
            print("✅ Dados de exemplo criados com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao criar dados: {e}")
            db.session.rollback()

def backup_databases():
    """Cria backup dos bancos de dados"""
    print("\n💾 Criando backup dos bancos...")
    
    backup_dir = "c:\\Users\\marco\\OneDrive\\Documentos\\TCC\\my-flask-app\\backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    db_dir = "c:\\Users\\marco\\OneDrive\\Documentos\\TCC\\my-flask-app\\databases"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        import shutil
        for db_file in os.listdir(db_dir):
            if db_file.endswith('.db'):
                source = os.path.join(db_dir, db_file)
                backup_name = f"{db_file.replace('.db', '')}_{timestamp}.db"
                dest = os.path.join(backup_dir, backup_name)
                shutil.copy2(source, dest)
                print(f"✅ Backup criado: {backup_name}")
        
        print(f"📁 Backups salvos em: {backup_dir}")
        
    except Exception as e:
        print(f"❌ Erro no backup: {e}")

if __name__ == "__main__":
    print("🛠️  Gerenciador de Bancos de Dados SynapseLog")
    
    while True:
        print("\n" + "="*50)
        print("OPÇÕES DISPONÍVEIS:")
        print("1. 📊 Mostrar informações dos bancos")
        print("2. 🔧 Criar dados de exemplo")
        print("3. 💾 Fazer backup dos bancos")
        print("4. 🚪 Sair")
        print("="*50)
        
        choice = input("\nEscolha uma opção (1-4): ").strip()
        
        if choice == '1':
            show_database_info()
        elif choice == '2':
            create_sample_data()
        elif choice == '3':
            backup_databases()
        elif choice == '4':
            print("👋 Saindo...")
            break
        else:
            print("❌ Opção inválida! Tente novamente.")