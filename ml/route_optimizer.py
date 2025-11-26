"""
Route Optimizer - Algoritmo KNN com Filtro de Tamanho
======================================================

Implementa roteirização inteligente usando K-Means clustering em 2 fases:
1. Clustering inicial baseado no número de dias
2. Filtro pós-processamento para dividir grupos que excedem o limite

Autor: SynapseLog
Data: 2025-11-12
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.exceptions import ConvergenceWarning
import numpy as np
import math
from typing import List, Dict, Optional, Tuple
import logging
import warnings

logger = logging.getLogger(__name__)


def create_routes_knn(
    clients_data: List[Dict], 
    n_days: int = 5, 
    max_clients_per_day: Optional[int] = None
) -> List[Dict]:
    """
    Cria rotas usando KNN com filtro de tamanho por dia.
    
    Fluxo:
    1. Clustering inicial com n_days clusters
    2. Filtro: se cluster > max_clients_per_day, divide em sub-clusters
    
    Args:
        clients_data: Lista de dicionários com dados dos clientes
                     Formato esperado: [{'hash_client': str, 'name': str, 'lat': float, 'lng': float}, ...]
        n_days: Número de dias/grupos desejados
        max_clients_per_day: Máximo de clientes por dia (None = sem limite)
    
    Returns:
        Lista de dicionários representando os grupos/rotas
        Formato: [{'group_number': int, 'day': int, 'clients': List[Dict], 
                   'total_clients': int, 'center': Dict, 'is_split': bool}, ...]
    """
    if not clients_data:
        logger.warning("create_routes_knn: Lista de clientes vazia")
        return []
    
    total_clients = len(clients_data)
    logger.info(f"🎯 Iniciando roteirização: {total_clients} clientes, {n_days} dias, limite: {max_clients_per_day}")
    
    # Se não definiu limite, usa todos os clientes divididos pelos dias
    if max_clients_per_day is None:
        max_clients_per_day = math.ceil(total_clients / n_days)
        logger.info(f"📊 Sem limite definido, usando {max_clients_per_day} clientes/dia")
    
    # Preparar coordenadas para clustering
    coordinates = np.array([[c['lat'], c['lng']] for c in clients_data])
    
    # Fase 1: Clustering inicial com n_days clusters
    n_clusters = min(n_days, total_clients)
    logger.info(f"🔵 Fase 1: Criando {n_clusters} clusters iniciais")
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(coordinates)
    
    # Organizar clientes por cluster inicial
    initial_clusters = {}
    for idx, label in enumerate(cluster_labels):
        if label not in initial_clusters:
            initial_clusters[label] = []
        initial_clusters[label].append(clients_data[idx])
    
    logger.info(f"✅ Fase 1 concluída: {len(initial_clusters)} clusters criados")
    for cluster_id, clients in initial_clusters.items():
        logger.info(f"   Cluster {cluster_id}: {len(clients)} clientes")
    
    # Fase 2: Aplicar filtro - dividir clusters que excedem o limite
    logger.info(f"🟢 Fase 2: Aplicando filtro de tamanho (máx: {max_clients_per_day})")
    
    final_groups = []
    group_number = 1
    split_count = 0
    
    for cluster_id, cluster_clients in initial_clusters.items():
        if len(cluster_clients) <= max_clients_per_day:
            # Cluster OK - adiciona direto
            logger.info(f"   ✓ Cluster {cluster_id}: {len(cluster_clients)} clientes (OK)")
            final_groups.append({
                'group_number': group_number,
                'day': group_number,
                'clients': cluster_clients,
                'total_clients': len(cluster_clients),
                'center': _calculate_center(cluster_clients),
                'is_split': False,
                'original_cluster': cluster_id
            })
            group_number += 1
        else:
            # Cluster excede limite - aplicar filtro de divisão
            logger.info(f"   ⚠️ Cluster {cluster_id}: {len(cluster_clients)} clientes (EXCEDE limite)")
            sub_clusters = _apply_size_filter(cluster_clients, max_clients_per_day)
            logger.info(f"      → Dividido em {len(sub_clusters)} sub-clusters")
            split_count += 1
            
            for idx, sub_cluster in enumerate(sub_clusters):
                final_groups.append({
                    'group_number': group_number,
                    'day': group_number,
                    'clients': sub_cluster,
                    'total_clients': len(sub_cluster),
                    'center': _calculate_center(sub_cluster),
                    'is_split': True,
                    'original_cluster': cluster_id,
                    'sub_cluster_index': idx
                })
                logger.info(f"         Sub-cluster {idx + 1}: {len(sub_cluster)} clientes")
                group_number += 1
    
    logger.info(f"🎉 Roteirização concluída: {len(final_groups)} grupos finais ({split_count} clusters divididos)")
    
    return final_groups


def _apply_size_filter(clients: List[Dict], max_size: int, depth: int = 0) -> List[List[Dict]]:
    """
    Filtro: divide cluster grande em sub-clusters respeitando max_size.
    Usa KNN novamente para manter proximidade geográfica.
    
    Args:
        clients: Lista de clientes do cluster grande
        max_size: Tamanho máximo permitido
        depth: Profundidade da recursão (proteção contra loop infinito)
    
    Returns:
        Lista de sub-clusters
    """
    # ⚠️ PROTEÇÃO: Limite de recursão para evitar stack overflow
    if depth > 10:
        logger.warning(f"⚠️ Limite de recursão atingido! Dividindo {len(clients)} clientes em chunks de {max_size}")
        return [clients[i:i + max_size] for i in range(0, len(clients), max_size)]
    
    if len(clients) <= max_size:
        return [clients]
    
    # Calcular quantos sub-clusters são necessários
    n_subclusters = math.ceil(len(clients) / max_size)
    logger.debug(f"      _apply_size_filter (depth={depth}): {len(clients)} clientes → {n_subclusters} sub-clusters")
    
    # ⚠️ PROTEÇÃO: Verificar se há coordenadas únicas suficientes
    coordinates = np.array([[c['lat'], c['lng']] for c in clients])
    unique_coords = np.unique(coordinates, axis=0)
    
    if len(unique_coords) < n_subclusters:
        logger.warning(f"⚠️ Apenas {len(unique_coords)} coordenadas únicas para {n_subclusters} clusters!")
        logger.warning(f"   Usando divisão simples por chunks para evitar convergência")
        return [clients[i:i + max_size] for i in range(0, len(clients), max_size)]
    
    # Aplicar KNN para dividir mantendo proximidade (suprimindo warnings)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=ConvergenceWarning)
        kmeans = KMeans(n_clusters=n_subclusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(coordinates)
    
    # ⚠️ PROTEÇÃO: Verificar se KMeans realmente dividiu
    n_clusters_found = len(np.unique(labels))
    if n_clusters_found < n_subclusters:
        logger.warning(f"⚠️ KMeans retornou apenas {n_clusters_found} clusters (esperava {n_subclusters})")
        logger.warning(f"   Usando divisão simples por chunks")
        return [clients[i:i + max_size] for i in range(0, len(clients), max_size)]
    
    # Organizar em sub-clusters
    subclusters = {}
    for idx, label in enumerate(labels):
        if label not in subclusters:
            subclusters[label] = []
        subclusters[label].append(clients[idx])
    
    # Garantir que nenhum sub-cluster excede max_size
    final_subclusters = []
    for subcluster in subclusters.values():
        if len(subcluster) <= max_size:
            final_subclusters.append(subcluster)
        else:
            # Recursão se ainda estiver grande (incrementando depth)
            logger.debug(f"         Recursão necessária: sub-cluster com {len(subcluster)} clientes")
            final_subclusters.extend(_apply_size_filter(subcluster, max_size, depth + 1))
    
    return final_subclusters


def _calculate_center(clients: List[Dict]) -> Dict[str, float]:
    """
    Calcula o centro geográfico (centroide) de um grupo de clientes.
    
    Args:
        clients: Lista de clientes com 'lat' e 'lng'
    
    Returns:
        Dicionário com 'lat' e 'lng' do centro
    """
    if not clients:
        return {'lat': 0, 'lng': 0}
    
    avg_lat = sum(c['lat'] for c in clients) / len(clients)
    avg_lng = sum(c['lng'] for c in clients) / len(clients)
    
    return {'lat': avg_lat, 'lng': avg_lng}


# ============================================================================
# FUNÇÕES AUXILIARES PARA INTEGRAÇÃO COM KMM.py
# ============================================================================

def convert_kmm_to_optimizer_format(df_clientes: pd.DataFrame) -> List[Dict]:
    """
    Converte DataFrame do KMM.py para formato esperado pelo route_optimizer.
    
    Args:
        df_clientes: DataFrame com colunas 'latitude', 'longitude', 'hash_client', etc.
    
    Returns:
        Lista de dicionários no formato esperado por create_routes_knn
    """
    clients_data = []
    for _, row in df_clientes.iterrows():
        client_dict = {
            'hash_client': row.get('hash_client'),
            'name': row.get('name', 'Cliente sem nome'),
            'lat': row['latitude'],
            'lng': row['longitude'],
            'id': row.get('id')
        }
        # Adiciona polygon_id se disponível
        if 'polygon_id' in row and pd.notna(row['polygon_id']):
            client_dict['polygon_id'] = int(row['polygon_id'])
        
        clients_data.append(client_dict)
    return clients_data


def format_result_for_api(groups: List[Dict], scores_map: Dict = None, polygons_map: Dict = None) -> Dict:
    """
    Formata resultado do route_optimizer para resposta da API.
    
    Args:
        groups: Lista de grupos retornada por create_routes_knn
        scores_map: Mapeamento de hash_client -> score (opcional)
        polygons_map: Mapeamento de polygon_id -> nome do grupo (opcional)
    
    Returns:
        Dicionário formatado para JSON response
    """
    if scores_map is None:
        scores_map = {}
    if polygons_map is None:
        polygons_map = {}
    
    result = {
        'success': True,
        'total_groups': len(groups),
        'total_clients': sum(g['total_clients'] for g in groups),
        'split_groups': sum(1 for g in groups if g['is_split']),
        'groups': []
    }
    
    for group in groups:
        # Calcula score médio do grupo
        group_scores = []
        polygon_ids = set()
        for client in group['clients']:
            hash_client = client.get('hash_client')
            if hash_client and hash_client in scores_map:
                group_scores.append(scores_map[hash_client]['score_total'])
            
            # Coleta IDs dos polígonos de origem (se disponível)
            if 'polygon_id' in client:
                polygon_ids.add(client['polygon_id'])
        
        score_medio = round(sum(group_scores) / len(group_scores), 2) if group_scores else 0
        
        # Determina segmento predominante
        segmento = _get_segmento_by_score(score_medio) if score_medio > 0 else None
        
        # Determina nome do polígono de origem (se houver apenas um)
        original_polygon_name = None
        original_polygon_id = None
        if len(polygon_ids) == 1:
            pid = list(polygon_ids)[0]
            original_polygon_id = pid
            original_polygon_name = polygons_map.get(pid, 'Grupo não identificado')
        elif len(polygon_ids) > 1:
            original_polygon_name = f"Múltiplos grupos ({len(polygon_ids)})"
        
        result['groups'].append({
            'group_number': group['group_number'],
            'day': group['day'],
            'total_clients': group['total_clients'],
            'is_split': group['is_split'],
            'score_medio': score_medio,
            'segmento_predominante': segmento,
            'center': group['center'],
            'clients': group['clients'],
            'original_polygon_id': original_polygon_id,
            'original_polygon_name': original_polygon_name
        })
    
    return result


def _get_segmento_by_score(score: float) -> str:
    """Retorna segmento baseado no score total."""
    if score >= 80:
        return 'VIP'
    elif score >= 60:
        return 'Alto Valor'
    elif score >= 40:
        return 'Médio'
    else:
        return 'Em Risco'


# ============================================================================
# TESTES UNITÁRIOS
# ============================================================================

if __name__ == '__main__':
    # Teste básico do algoritmo
    print("🧪 Testando route_optimizer.py\n")
    
    # Dados de teste
    test_clients = [
        {'hash_client': f'hash_{i}', 'name': f'Cliente {i}', 'lat': -23.5 + i*0.01, 'lng': -46.6 + i*0.01}
        for i in range(50)
    ]
    
    print(f"📊 Dados de teste: {len(test_clients)} clientes\n")
    
    # Teste 1: Sem limite
    print("=" * 60)
    print("TESTE 1: Sem limite de clientes por dia")
    print("=" * 60)
    groups1 = create_routes_knn(test_clients, n_days=5, max_clients_per_day=None)
    print(f"\n✅ Resultado: {len(groups1)} grupos")
    for g in groups1:
        print(f"   Grupo {g['group_number']}: {g['total_clients']} clientes | Split: {g['is_split']}")
    
    # Teste 2: Com limite de 12
    print("\n" + "=" * 60)
    print("TESTE 2: Limite de 12 clientes por dia")
    print("=" * 60)
    groups2 = create_routes_knn(test_clients, n_days=5, max_clients_per_day=12)
    print(f"\n✅ Resultado: {len(groups2)} grupos")
    for g in groups2:
        print(f"   Grupo {g['group_number']}: {g['total_clients']} clientes | Split: {g['is_split']}")
    
    # Teste 3: Limite muito pequeno (força múltiplas divisões)
    print("\n" + "=" * 60)
    print("TESTE 3: Limite de 5 clientes por dia (múltiplas divisões)")
    print("=" * 60)
    groups3 = create_routes_knn(test_clients, n_days=3, max_clients_per_day=5)
    print(f"\n✅ Resultado: {len(groups3)} grupos")
    for g in groups3:
        print(f"   Grupo {g['group_number']}: {g['total_clients']} clientes | Split: {g['is_split']}")
    
    print("\n" + "=" * 60)
    print("✅ Todos os testes concluídos!")
    print("=" * 60)
