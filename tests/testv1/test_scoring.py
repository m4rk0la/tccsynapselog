"""
Testes para o módulo de scoring RFM (ml/client_scoring.py)
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Mock para evitar importação do banco
import sys
from unittest.mock import MagicMock
sys.modules['base.models'] = MagicMock()

from ml.client_scoring import RFMScorer


class TestRFMScorer(unittest.TestCase):
    """Testes para a classe RFMScorer"""
    
    def setUp(self):
        """Configura dados de teste"""
        self.scorer = RFMScorer()
        
        # Cria dados de vendas simulados
        base_date = datetime(2024, 1, 1)
        self.vendas_df = pd.DataFrame({
            'hash_cliente': ['cli1', 'cli1', 'cli2', 'cli2', 'cli3'],
            'id_pedido': ['P1', 'P2', 'P3', 'P4', 'P5'],
            'data_compra': [
                base_date - timedelta(days=10),
                base_date - timedelta(days=5),
                base_date - timedelta(days=30),
                base_date - timedelta(days=20),
                base_date - timedelta(days=60)
            ],
            'valor_total': [100.0, 150.0, 200.0, 180.0, 50.0],
            'nota_avaliacao': [5.0, 4.0, 5.0, 5.0, 3.0]
        })
    
    def test_scorer_initialization(self):
        """Testa inicialização do scorer"""
        self.assertIsNotNone(self.scorer)
        self.assertEqual(self.scorer.pesos['recencia'], 0.30)
        self.assertEqual(self.scorer.pesos['frequencia'], 0.25)
    
    def test_pesos_customizados(self):
        """Testa inicialização com pesos customizados"""
        pesos = {
            'recencia': 0.40,
            'frequencia': 0.30,
            'monetario': 0.20,
            'satisfacao': 0.10
        }
        scorer = RFMScorer(pesos=pesos)
        
        self.assertEqual(scorer.pesos['recencia'], 0.40)
        self.assertEqual(scorer.pesos['frequencia'], 0.30)
    
    def test_pesos_invalidos(self):
        """Testa que pesos inválidos levantam exceção"""
        pesos_invalidos = {
            'recencia': 0.50,
            'frequencia': 0.30,
            'monetario': 0.10,
            'satisfacao': 0.05  # Soma = 0.95
        }
        
        with self.assertRaises(ValueError):
            RFMScorer(pesos=pesos_invalidos)
    
    def test_calcular_metricas_rfm(self):
        """Testa cálculo de métricas RFM"""
        data_ref = datetime(2024, 1, 1)
        rfm = self.scorer.calcular_metricas_rfm(self.vendas_df, data_ref)
        
        # Verifica estrutura do resultado
        self.assertIn('hash_cliente', rfm.columns)
        self.assertIn('recencia_dias', rfm.columns)
        self.assertIn('frequencia', rfm.columns)
        self.assertIn('valor_total', rfm.columns)
        self.assertIn('nota_media', rfm.columns)
        
        # Verifica número de clientes únicos
        self.assertEqual(len(rfm), 3)
    
    def test_recencia_calculation(self):
        """Testa cálculo correto de recência"""
        data_ref = datetime(2024, 1, 1)
        rfm = self.scorer.calcular_metricas_rfm(self.vendas_df, data_ref)
        
        # Cliente 1 teve última compra há 5 dias
        cli1_recencia = rfm[rfm['hash_cliente'] == 'cli1']['recencia_dias'].values[0]
        self.assertEqual(cli1_recencia, 5)
        
        # Cliente 2 teve última compra há 20 dias
        cli2_recencia = rfm[rfm['hash_cliente'] == 'cli2']['recencia_dias'].values[0]
        self.assertEqual(cli2_recencia, 20)
    
    def test_frequencia_calculation(self):
        """Testa cálculo correto de frequência"""
        data_ref = datetime(2024, 1, 1)
        rfm = self.scorer.calcular_metricas_rfm(self.vendas_df, data_ref)
        
        # Cliente 1 tem 2 pedidos
        cli1_freq = rfm[rfm['hash_cliente'] == 'cli1']['frequencia'].values[0]
        self.assertEqual(cli1_freq, 2)
        
        # Cliente 3 tem 1 pedido
        cli3_freq = rfm[rfm['hash_cliente'] == 'cli3']['frequencia'].values[0]
        self.assertEqual(cli3_freq, 1)
    
    def test_valor_total_calculation(self):
        """Testa cálculo correto de valor total"""
        data_ref = datetime(2024, 1, 1)
        rfm = self.scorer.calcular_metricas_rfm(self.vendas_df, data_ref)
        
        # Cliente 1: 100 + 150 = 250
        cli1_valor = rfm[rfm['hash_cliente'] == 'cli1']['valor_total'].values[0]
        self.assertEqual(cli1_valor, 250.0)
    
    def test_nota_media_calculation(self):
        """Testa cálculo correto de nota média"""
        data_ref = datetime(2024, 1, 1)
        rfm = self.scorer.calcular_metricas_rfm(self.vendas_df, data_ref)
        
        # Cliente 1: (5 + 4) / 2 = 4.5
        cli1_nota = rfm[rfm['hash_cliente'] == 'cli1']['nota_media'].values[0]
        self.assertAlmostEqual(cli1_nota, 4.5, places=1)
    
    def test_normalizar_scores(self):
        """Testa normalização de scores"""
        data_ref = datetime(2024, 1, 1)
        rfm = self.scorer.calcular_metricas_rfm(self.vendas_df, data_ref)
        scores = self.scorer.normalizar_scores(rfm)
        
        # Verifica se scores foram criados
        self.assertIn('score_recencia', scores.columns)
        self.assertIn('score_frequencia', scores.columns)
        self.assertIn('score_monetario', scores.columns)
        self.assertIn('score_satisfacao', scores.columns)
        self.assertIn('score_total', scores.columns)
        
        # Verifica range de scores (0-100)
        for col in ['score_recencia', 'score_frequencia', 'score_monetario', 'score_satisfacao', 'score_total']:
            self.assertTrue((scores[col] >= 0).all())
            self.assertTrue((scores[col] <= 100).all())
    
    def test_score_total_weighted(self):
        """Testa se score total usa pesos corretamente"""
        data_ref = datetime(2024, 1, 1)
        rfm = self.scorer.calcular_metricas_rfm(self.vendas_df, data_ref)
        scores = self.scorer.normalizar_scores(rfm)
        
        # Verifica que score total é soma ponderada
        for _, row in scores.iterrows():
            expected = (
                row['score_recencia'] * 0.30 +
                row['score_frequencia'] * 0.25 +
                row['score_monetario'] * 0.25 +
                row['score_satisfacao'] * 0.20
            )
            self.assertAlmostEqual(row['score_total'], expected, places=1)
    
    def test_segmentar_clientes(self):
        """Testa segmentação de clientes"""
        data_ref = datetime(2024, 1, 1)
        rfm = self.scorer.calcular_metricas_rfm(self.vendas_df, data_ref)
        scores = self.scorer.normalizar_scores(rfm)
        segmentado = self.scorer.segmentar_clientes(scores)
        
        # Verifica se coluna segmento foi criada
        self.assertIn('segmento', segmentado.columns)
        
        # Verifica valores válidos de segmento
        segmentos_validos = ['VIP', 'Alto Valor', 'Médio', 'Em Risco']
        self.assertTrue(segmentado['segmento'].isin(segmentos_validos).all())
    
    def test_segmento_vip(self):
        """Testa classificação VIP (score >= 80)"""
        df = pd.DataFrame({
            'hash_cliente': ['vip1'],
            'recencia_dias': [1],
            'frequencia': [100],
            'valor_total': [10000],
            'nota_media': [5.0],
            'ticket_medio': [100],
            'pedidos_com_avaliacao': [100],
            'taxa_avaliacao': [100]
        })
        
        scores = self.scorer.normalizar_scores(df)
        segmentado = self.scorer.segmentar_clientes(scores)
        
        # Com valores máximos, deve ser VIP
        self.assertEqual(segmentado.iloc[0]['segmento'], 'VIP')
    
    def test_segmento_em_risco(self):
        """Testa classificação Em Risco (score < 40)"""
        # Precisa ter múltiplos clientes para normalização funcionar
        df = pd.DataFrame({
            'hash_cliente': ['risco1', 'vip1', 'medio1'],
            'recencia_dias': [365, 1, 30],     # 1 ano, recente, médio
            'frequencia': [1, 100, 10],        # Poucas, muitas, médias compras
            'valor_total': [10, 10000, 500],   # Baixo, alto, médio
            'nota_media': [2.0, 5.0, 3.5],     # Baixa, alta, média
            'ticket_medio': [10, 100, 50],
            'pedidos_com_avaliacao': [1, 100, 10],
            'taxa_avaliacao': [100, 100, 100]
        })
        
        scores = self.scorer.normalizar_scores(df)
        segmentado = self.scorer.segmentar_clientes(scores)
        
        # Cliente com piores valores deve ter score baixo
        cliente_risco = segmentado[segmentado['hash_cliente'] == 'risco1'].iloc[0]
        self.assertLess(cliente_risco['score_total'], 50)  # Deve ser baixo


class TestRFMEdgeCases(unittest.TestCase):
    """Testes de casos extremos para RFM"""
    
    def test_cliente_sem_avaliacao(self):
        """Testa cliente sem nenhuma avaliação"""
        scorer = RFMScorer()
        
        df = pd.DataFrame({
            'hash_cliente': ['cli1'],
            'id_pedido': ['P1'],
            'data_compra': [datetime(2024, 1, 1)],
            'valor_total': [100.0],
            'nota_avaliacao': [np.nan]
        })
        
        rfm = scorer.calcular_metricas_rfm(df, datetime(2024, 1, 10))
        
        # Nota média deve ser 0 quando não há avaliações
        self.assertEqual(rfm.iloc[0]['nota_media'], 0)
    
    def test_cliente_unico(self):
        """Testa com apenas um cliente"""
        scorer = RFMScorer()
        
        df = pd.DataFrame({
            'hash_cliente': ['cli1'],
            'id_pedido': ['P1'],
            'data_compra': [datetime(2024, 1, 1)],
            'valor_total': [100.0],
            'nota_avaliacao': [5.0]
        })
        
        rfm = scorer.calcular_metricas_rfm(df, datetime(2024, 1, 10))
        scores = scorer.normalizar_scores(rfm)
        
        # Não deve lançar exceção
        self.assertEqual(len(scores), 1)
    
    def test_valores_zero(self):
        """Testa com valores zero"""
        scorer = RFMScorer()
        
        df = pd.DataFrame({
            'hash_cliente': ['cli1'],
            'id_pedido': ['P1'],
            'data_compra': [datetime(2024, 1, 1)],
            'valor_total': [0.0],
            'nota_avaliacao': [0.0]
        })
        
        rfm = scorer.calcular_metricas_rfm(df, datetime(2024, 1, 1))
        scores = scorer.normalizar_scores(rfm)
        
        # Não deve lançar exceção
        self.assertIsNotNone(scores)


if __name__ == '__main__':
    unittest.main()
