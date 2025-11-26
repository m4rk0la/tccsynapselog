"""
Metodologia:
- Recência (R): Dias desde última compra (peso 30%)
- Frequência (F): Total de pedidos (peso 25%)
- Monetário (M): Valor total gasto (peso 25%)
- Satisfação (S): Nota média avaliações (peso 20%)

Score Total: R×0.30 + F×0.25 + M×0.25 + S×0.20 (escala 0-100)

Segmentos:
- VIP: Score >= 80
- Alto Valor: Score >= 60
- Médio: Score >= 40
- Em Risco: Score < 40

"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import logging

from base.models import db, OrderHistory, ClientScore

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RFMScorer:
    
    def __init__(self, pesos=None):
        """
        Parâmetros:
        -----------
        pesos : dict, opcional
            Dicionário com pesos para cada dimensão
            Formato: {'recencia': float, 'frequencia': float, 
                     'monetario': float, 'satisfacao': float}
            Default: {'recencia': 0.30, 'frequencia': 0.25, 
                     'monetario': 0.25, 'satisfacao': 0.20}
        """
        self.pesos = pesos or {
            'recencia': 0.30,
            'frequencia': 0.25,
            'monetario': 0.25,
            'satisfacao': 0.20
        }
        
        soma_pesos = sum(self.pesos.values())
        if not np.isclose(soma_pesos, 1.0):
            raise ValueError(
                f"Pesos devem somar 1.0 (atual: {soma_pesos:.3f}). "
                f"Recebido: {self.pesos}"
            )
        
        self.scaler = MinMaxScaler()
        logger.info(f"RFMScorer inicializado | Pesos: {self.pesos}")
    
    def calcular_metricas_rfm(self, vendas_df, data_referencia=None):
        """
        Parâmetros:
        -----------
        vendas_df : DataFrame
            DataFrame com colunas obrigatórias:
            - hash_cliente: Identificador único do cliente
            - data_compra: Data da compra (datetime)
            - id_pedido: ID do pedido (para contagem)
            - valor_total: Valor monetário do pedido
            - nota_avaliacao: Nota de satisfação (0-5)
        
        data_referencia : datetime, opcional
            Data de referência para cálculo de recência
            Default: datetime.now()
        
        Retorna:
        --------
        DataFrame com métricas agregadas:
        - hash_cliente
        - recencia_dias: Dias desde última compra
        - frequencia: Número total de pedidos
        - valor_total: Soma de todos os pedidos
        - nota_media: Média das avaliações
        - ticket_medio: Valor médio por pedido
        - taxa_avaliacao: % de pedidos avaliados
        """
        if data_referencia is None:
            data_referencia = datetime.now()
        
        vendas_df['data_compra'] = pd.to_datetime(vendas_df['data_compra'])
        
        rfm = vendas_df.groupby('hash_cliente').agg({
            'data_compra': lambda x: (data_referencia - x.max()).days,
            'id_pedido': 'count',
            'valor_total': 'sum',
            'nota_avaliacao': lambda x: x.dropna().mean() if len(x.dropna()) > 0 else 0
        }).reset_index()
        
        rfm.columns = ['hash_cliente', 'recencia_dias', 'frequencia', 'valor_total', 'nota_media']

        rfm['ticket_medio'] = vendas_df.groupby('hash_cliente')['valor_total'].mean().values
        rfm['pedidos_com_avaliacao'] = vendas_df.groupby('hash_cliente')['nota_avaliacao'].apply(
            lambda x: x.notna().sum()
        ).values
        rfm['taxa_avaliacao'] = (rfm['pedidos_com_avaliacao'] / rfm['frequencia'] * 100).round(2)
        
        logger.info(f"Métricas RFM calculadas | {len(rfm)} clientes")
        return rfm
    
    def normalizar_scores(self, rfm_df):
        """
        Recência: Invertida (menos dias = maior score)
        Frequência: Direta (mais pedidos = maior score)
        Monetário: Direta (mais gasto = maior score)
        Satisfação: Conversão linear 0-5 → 0-100
        """
        scores_df = rfm_df.copy()
        
        if scores_df['recencia_dias'].max() > 0:
            recencia_invertida = scores_df[['recencia_dias']].values
            recencia_norm = self.scaler.fit_transform(recencia_invertida)
            scores_df['score_recencia'] = ((1 - recencia_norm) * 100).flatten()
        else:
            scores_df['score_recencia'] = 100.0 
        
        if scores_df['frequencia'].max() > scores_df['frequencia'].min():
            scores_df['score_frequencia'] = (
                self.scaler.fit_transform(scores_df[['frequencia']]) * 100
            ).flatten()
        else:
            scores_df['score_frequencia'] = 100.0 
        
        if scores_df['valor_total'].max() > scores_df['valor_total'].min():
            scores_df['score_monetario'] = (
                self.scaler.fit_transform(scores_df[['valor_total']]) * 100
            ).flatten()
        else:
            scores_df['score_monetario'] = 100.0
        
        scores_df['score_satisfacao'] = (scores_df['nota_media'] / 5) * 100
        scores_df['score_total'] = (
            scores_df['score_recencia'] * self.pesos['recencia'] +
            scores_df['score_frequencia'] * self.pesos['frequencia'] +
            scores_df['score_monetario'] * self.pesos['monetario'] +
            scores_df['score_satisfacao'] * self.pesos['satisfacao']
        )
        
        score_cols = ['score_recencia', 'score_frequencia', 'score_monetario', 
                     'score_satisfacao', 'score_total']
        for col in score_cols:
            scores_df[col] = scores_df[col].round(2)
        
        logger.info(f"Scores normalizados | Média: {scores_df['score_total'].mean():.2f}")
        return scores_df
    
    def segmentar_clientes(self, scores_df):
        """
        Segmentos:
        - VIP: >= 80 (Top 20% esperado)
        - Alto Valor: >= 60 (20-40%)
        - Médio: >= 40 (40-60%)
        - Em Risco: < 40 (Bottom 40%)
        """
        def classificar(score):
            if score >= 80:
                return 'VIP'
            elif score >= 60:
                return 'Alto Valor'
            elif score >= 40:
                return 'Médio'
            else:
                return 'Em Risco'
        
        scores_df['segmento'] = scores_df['score_total'].apply(classificar)

        distribuicao = scores_df['segmento'].value_counts()
        logger.info(f"Segmentação | {distribuicao.to_dict()}")
        
        return scores_df


def calcular_scores_para_usuario(user_id, pesos=None, forcar_recalculo=False):
    """
    Calcula e persiste scores RFM para todos os clientes de um usuário
    
    Fluxo:
    1. Busca vendas do OrderHistory (bind: order_history)
    2. Calcula métricas RFM com RFMScorer
    3. Salva em ClientScore (bind: client_scores)
    """
    logger.info(f"{'='*60}")
    logger.info(f"Calculando scores RFM | user_id={user_id}")
    logger.info(f"{'='*60}")
    
    try:
        vendas = OrderHistory.query.filter_by(user_id=user_id).all()
        
        if not vendas:
            raise ValueError(f"Nenhuma venda encontrada para user_id={user_id}")
        
        vendas_data = [{
            'hash_cliente': v.hash_cliente,
            'id_pedido': v.id_pedido,
            'data_compra': v.data_compra,
            'valor_total': v.valor_total_pagamento or 0,
            'nota_avaliacao': v.nota_avaliacao
        } for v in vendas]
        
        df_vendas = pd.DataFrame(vendas_data)
        logger.info(f"{len(vendas)} registros carregados | {df_vendas['hash_cliente'].nunique()} clientes únicos")
        
        scorer = RFMScorer(pesos=pesos)
        df_rfm = scorer.calcular_metricas_rfm(df_vendas)
        df_scores = scorer.normalizar_scores(df_rfm)
        df_segmentado = scorer.segmentar_clientes(df_scores)
        
        model_version = 'v1.0_RFM'
        registros_salvos = 0
        registros_atualizados = 0
        
        for _, row in df_segmentado.iterrows():
            score_existente = ClientScore.query.filter_by(
                hash_cliente=row['hash_cliente'],
                user_id=user_id
            ).first()
            
            if score_existente:
                score_existente.score_total = float(row['score_total'])
                score_existente.score_recencia = float(row['score_recencia'])
                score_existente.score_frequencia = float(row['score_frequencia'])
                score_existente.score_valor = float(row['score_monetario'])
                score_existente.score_satisfacao = float(row['score_satisfacao'])
                score_existente.total_pedidos = int(row['frequencia'])
                score_existente.valor_total_vendas = float(row['valor_total'])
                score_existente.ticket_medio = float(row['ticket_medio'])
                score_existente.dias_desde_ultima_compra = int(row['recencia_dias'])
                score_existente.model_version = model_version
                score_existente.updated_at = datetime.utcnow()
                registros_atualizados += 1
            else:
                novo_score = ClientScore(
                    hash_cliente=row['hash_cliente'],
                    user_id=user_id,
                    score_total=float(row['score_total']),
                    score_recencia=float(row['score_recencia']),
                    score_frequencia=float(row['score_frequencia']),
                    score_valor=float(row['score_monetario']),
                    score_satisfacao=float(row['score_satisfacao']),
                    total_pedidos=int(row['frequencia']),
                    valor_total_vendas=float(row['valor_total']),
                    ticket_medio=float(row['ticket_medio']),
                    dias_desde_ultima_compra=int(row['recencia_dias']),
                    model_version=model_version
                )
                db.session.add(novo_score)
                registros_salvos += 1
        
        db.session.commit()
        
        total = registros_salvos + registros_atualizados
        score_medio = df_segmentado['score_total'].mean()
        distribuicao = df_segmentado['segmento'].value_counts().to_dict()
        
        logger.info(f"Scores persistidos | Novos: {registros_salvos} | Atualizados: {registros_atualizados}")
        logger.info(f"Score médio: {score_medio:.2f} | Distribuição: {distribuicao}")
        
        return {
            'registros_salvos': total,
            'clientes_analisados': len(df_segmentado),
            'score_medio': round(score_medio, 2),
            'distribuicao': distribuicao
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular scores: {str(e)}", exc_info=True)
        db.session.rollback()
        raise


def obter_estatisticas_scores(user_id):

    scores = ClientScore.query.filter_by(user_id=user_id).all()
    
    if not scores:
        logger.warning(f"Nenhum score encontrado para user_id={user_id}")
        return None
    
    scores_totais = [s.score_total for s in scores]
    ultima_atualizacao = max([s.updated_at or s.calculated_at for s in scores])
    
    return {
        'total_clientes': len(scores),
        'score_medio': round(np.mean(scores_totais), 2),
        'score_mediano': round(np.median(scores_totais), 2),
        'score_min': round(np.min(scores_totais), 2),
        'score_max': round(np.max(scores_totais), 2),
        'desvio_padrao': round(np.std(scores_totais), 2),
        'distribuicao': {
            'VIP': len([s for s in scores if s.score_total >= 80]),
            'Alto Valor': len([s for s in scores if 60 <= s.score_total < 80]),
            'Médio': len([s for s in scores if 40 <= s.score_total < 60]),
            'Em Risco': len([s for s in scores if s.score_total < 40])
        },
        'ultima_atualizacao': ultima_atualizacao.isoformat()
    }


def obter_clientes_segmento(user_id, segmento):
    scores = ClientScore.query.filter_by(user_id=user_id).all()
    filtrados = [s for s in scores if s.get_segmento() == segmento]
    filtrados.sort(key=lambda x: x.score_total, reverse=True)
    
    return filtrados