"""
Script para criar banco de dados de scores RFM de clientes
Executa após o setup inicial ou quando adicionar modelo ClientScore
"""

import sys
import os

# Adicionar root ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from base import create_app, db
from base.models import ClientScore

def init_client_scores_database():
    """Inicializa banco de dados de scores RFM"""
    app = create_app()
    
    with app.app_context():
        try:
            # Criar tabela ClientScore
            print("🔧 Criando banco de dados de scores RFM...")
            
            # Verifica se bind existe
            if 'client_scores' not in db.engines:
                print("❌ Erro: bind 'client_scores' não encontrado em config.py")
                return False
            
            # Cria tabelas para o bind client_scores
            db.create_all(bind_key='client_scores')
            
            # Verifica se criou
            inspector = db.inspect(db.engines['client_scores'])
            tables = inspector.get_table_names()
            
            if 'client_scores_data' in tables:
                print("✅ Banco synapselLog_client_scores.db criado com sucesso!")
                print(f"   Tabelas: {tables}")
                return True
            else:
                print("⚠️ Tabela não foi criada. Verifique o modelo ClientScore.")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao criar banco: {str(e)}")
            return False

if __name__ == '__main__':
    print("="*60)
    print("SYNAPSELLOG - Inicialização de Banco de Scores RFM")
    print("="*60)
    
    success = init_client_scores_database()
    
    if success:
        print("\n🎉 Setup concluído! Próximos passos:")
        print("   1. Execute upload de histórico de vendas")
        print("   2. Calcule scores: python -c 'from ml.client_scoring import calcular_scores_para_usuario; calcular_scores_para_usuario(1)'")
    else:
        print("\n⚠️ Revise os erros acima e tente novamente.")
        sys.exit(1)