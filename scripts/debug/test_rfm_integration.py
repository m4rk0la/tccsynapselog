"""
Script de teste para verificar integração RFM
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from ml.client_scoring import calcular_scores_para_usuario, obter_estatisticas_scores, obter_clientes_segmento

print("="*60)
print("TESTE DE INTEGRAÇÃO RFM")
print("="*60)

app = create_app()

with app.app_context():
    print("\n✅ Contexto Flask criado")
    
    # Teste 1: Import de funções
    print("✅ Funções RFM importadas com sucesso:")
    print(f"   - calcular_scores_para_usuario: {calcular_scores_para_usuario}")
    print(f"   - obter_estatisticas_scores: {obter_estatisticas_scores}")
    print(f"   - obter_clientes_segmento: {obter_clientes_segmento}")
    
    # Teste 2: Verificar modelo ClientScore
    from base.models import ClientScore
    print(f"\n✅ Modelo ClientScore: {ClientScore}")
    
    # Teste 3: Verificar bind no config
    from flask import current_app
    binds = current_app.config.get('SQLALCHEMY_BINDS', {})
    if 'client_scores' in binds:
        print(f"✅ Bind 'client_scores' configurado: {binds['client_scores']}")
    else:
        print("❌ Bind 'client_scores' NÃO configurado!")
    
    # Teste 4: Verificar se tabela existe
    from base import db
    try:
        inspector = db.inspect(db.engines['client_scores'])
        tables = inspector.get_table_names()
        print(f"\n✅ Tabelas no banco client_scores: {tables}")
        
        if 'client_scores_data' in tables:
            print("✅ Tabela 'client_scores_data' existe!")
        else:
            print("❌ Tabela 'client_scores_data' NÃO existe!")
    except Exception as e:
        print(f"⚠️ Erro ao inspecionar banco: {e}")
    
    # Teste 5: Contar scores existentes
    try:
        total_scores = ClientScore.query.count()
        print(f"\n📊 Total de scores no banco: {total_scores}")
        
        if total_scores > 0:
            # Mostrar exemplo
            exemplo = ClientScore.query.first()
            print(f"✅ Exemplo de score:")
            print(f"   Hash: {exemplo.hash_cliente[:8]}...")
            print(f"   Score Total: {exemplo.score_total:.2f}")
            print(f"   Segmento: {exemplo.get_segmento()}")
    except Exception as e:
        print(f"⚠️ Erro ao contar scores: {e}")
    
    print("\n" + "="*60)
    print("✅ TODOS OS TESTES CONCLUÍDOS!")
    print("="*60)
