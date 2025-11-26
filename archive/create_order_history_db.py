"""
Script para criar o banco de dados de histórico de vendas
Executa: python create_order_history_db.py
"""

from app import create_app
from base.models import db, OrderHistory

def create_order_history_database():
    """Cria o banco de dados order_history com a tabela OrderHistory"""
    
    app = create_app()
    
    with app.app_context():
        # Cria apenas as tabelas vinculadas ao bind 'order_history'
        print("🔄 Criando banco de dados de histórico de vendas...")
        
        # Pega o engine do bind específico
        bind_key = 'order_history'
        engine = db.get_engine(app, bind=bind_key)
        
        # Cria apenas as tabelas deste bind
        OrderHistory.__table__.create(bind=engine, checkfirst=True)
        
        print("✅ Banco de dados 'order_history' criado com sucesso!")
        print(f"📁 Localização: databases/synapselLog_order_history.db")
        print(f"📊 Tabela: order_history_data")
        print(f"📋 Colunas: 33 colunas do modelo Excel + campos de controle")
        
        # Verifica se a tabela foi criada
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Tabelas criadas no banco order_history:")
        for table in tables:
            print(f"   ✓ {table}")
            
            # Lista as colunas
            columns = inspector.get_columns(table)
            print(f"     Colunas ({len(columns)}):")
            for col in columns:
                print(f"       - {col['name']} ({col['type']})")

if __name__ == "__main__":
    try:
        create_order_history_database()
    except Exception as e:
        print(f"❌ Erro ao criar banco de dados: {e}")
        import traceback
        traceback.print_exc()
