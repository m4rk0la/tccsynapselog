import pandas as pd
from datetime import datetime

def criar_modelo_excel():
    colunas = [
        'id_pedido',
        'id_item_pedido',
        'id_cliente',
        'id_unico_cliente',
        'id_produto',
        'data_compra',
        'data_aprovacao',
        'data_envio_transportadora',
        'data_entrega_cliente',
        'data_estimada_entrega',
        'data_limite_envio',
        'status_pedido',
        'tempo_entrega_dias',
        'atraso_entrega_dias',
        'ano_compra',
        'mes_compra',
        'ano_mes_compra',
        'dia_semana_compra',
        'preco',
        'valor_frete',
        'valor_total_item',
        'valor_total_pagamento',
        'num_pagamentos',
        'tipos_pagamento',
        'max_parcelas',
        'cidade_cliente',
        'estado_cliente',
        'cep_cliente',
        'nota_avaliacao',
        'titulo_comentario',
        'mensagem_comentario',
        'data_criacao_avaliacao',
        'data_resposta_avaliacao'
    ]
    exemplo = {
        'id_pedido': 'exemplo_pedido_001',
        'id_item_pedido': 1,
        'id_cliente': 'exemplo_cliente_001',
        'id_unico_cliente': 'exemplo_unico_001',
        'id_produto': 'exemplo_produto_001',
        'data_compra': '2024-01-15 10:30:00',
        'data_aprovacao': '2024-01-15 11:00:00',
        'data_envio_transportadora': '2024-01-16 09:00:00',
        'data_entrega_cliente': '2024-01-20 14:30:00',
        'data_estimada_entrega': '2024-01-22 23:59:59',
        'data_limite_envio': '2024-01-17 23:59:59',
        'status_pedido': 'delivered',
        'tempo_entrega_dias': 5,
        'atraso_entrega_dias': -2,
        'ano_compra': 2024,
        'mes_compra': 1,
        'ano_mes_compra': '2024-01',
        'dia_semana_compra': 0,
        'preco': 99.90,
        'valor_frete': 15.50,
        'valor_total_item': 115.40,
        'valor_total_pagamento': 115.40,
        'num_pagamentos': 1,
        'tipos_pagamento': 'credit_card',
        'max_parcelas': 3,
        'cidade_cliente': 'Brasília',
        'estado_cliente': 'DF',
        'cep_cliente': '70000',
        'nota_avaliacao': 5,
        'titulo_comentario': 'Excelente produto!',
        'mensagem_comentario': 'Produto chegou antes do prazo e em perfeitas condições.',
        'data_criacao_avaliacao': '2024-01-21 10:00:00',
        'data_resposta_avaliacao': '2024-01-21 15:00:00'
    }
    df_modelo = pd.DataFrame([exemplo])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f'modelo_historico_vendas_{timestamp}.xlsx'
    df_modelo.to_excel(nome_arquivo, index=False, engine='openpyxl')


if __name__ == "__main__":
    try:
        arquivo = criar_modelo_excel()
        print(f"\n✅ Processo concluído! Arquivo criado: {arquivo}")
    except Exception as e:
        print(f"\n❌ Erro ao criar arquivo modelo: {str(e)}")
        import traceback
        traceback.print_exc()
