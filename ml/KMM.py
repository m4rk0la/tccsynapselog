import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo_utils import GeoUtils


def filter_clients_by_selected_polygons(customers_df, selected_polygon_ids, polygons_data):
    """
    Filtra clientes que estão dentro dos polígonos selecionados de forma otimizada.
    Adiciona coluna 'polygon_id' indicando a qual polígono cada cliente pertence.
    
    Args:
        customers_df (pd.DataFrame): DataFrame com todos os clientes (latitude, longitude)
        selected_polygon_ids (list): Lista de IDs dos polígonos selecionados
        polygons_data (list): Lista completa de polígonos com formato:
                             [{'id': 1, 'name': 'Grupo A', 'coordinates': [[lat, lon], ...]}, ...]
    
    Returns:
        pd.DataFrame: DataFrame filtrado contendo apenas clientes dentro das áreas selecionadas
                     com coluna 'polygon_id' adicionada
        dict: Dicionário com contagem de clientes por polígono {polygon_id: count}
    """
    if customers_df.empty:
        return pd.DataFrame(), {}
    
    selected_polygons = [p for p in polygons_data if p['id'] in selected_polygon_ids]
    
    if not selected_polygons:
        return pd.DataFrame(), {}
    
    clients_list = customers_df.to_dict('records')
    
    clients_by_polygon = GeoUtils.filter_clients_by_polygons_optimized(
        clients_list, 
        selected_polygons
    )
    
    # Mapeia clientes para seus polígonos
    client_to_polygon = {}
    clients_count = {}
    
    for polygon_id, clients in clients_by_polygon.items():
        clients_count[polygon_id] = len(clients)
        for client in clients:
            client_id = client.get('id') or client.get('hash_client')
            if client_id:
                client_to_polygon[client_id] = polygon_id
    
    # Filtra DataFrame
    unique_client_ids = set(client_to_polygon.keys())
    
    if 'id' in customers_df.columns:
        filtered_df = customers_df[customers_df['id'].isin(unique_client_ids)].copy()
        filtered_df['polygon_id'] = filtered_df['id'].map(client_to_polygon)
    elif 'hash_client' in customers_df.columns:
        filtered_df = customers_df[customers_df['hash_client'].isin(unique_client_ids)].copy()
        filtered_df['polygon_id'] = filtered_df['hash_client'].map(client_to_polygon)
    else:
        filtered_df = customers_df.copy()
    
    return filtered_df, clients_count

def run_kmeans_clustering(customers_df, days, selected_polygon_ids=None, polygons_data=None):
    """
    Executa o algoritmo K-Means para agrupar clientes.
    Opcionalmente filtra clientes por polígonos selecionados antes do clustering.

    Args:
        customers_df (pd.DataFrame): DataFrame contendo os dados dos clientes.
                                     Deve incluir colunas 'latitude' and 'longitude'.
        days (int): O número de dias para dividir os clientes, usado para calcular 'k'.
        selected_polygon_ids (list, optional): Lista de IDs dos polígonos para filtrar clientes.
        polygons_data (list, optional): Lista de dados dos polígonos (necessário se selected_polygon_ids for fornecido).

    Returns:
        pd.DataFrame: O DataFrame dos clientes (filtrados se aplicável) com uma nova coluna 'cluster'
                      indicando o grupo ao qual cada cliente pertence.
        int: O número de clusters (grupos) criados.
        dict: Contagem de clientes por polígono (se filtragem foi aplicada), ou None.
    """
    clients_count = None
    if selected_polygon_ids and polygons_data:
        customers_df, clients_count = filter_clients_by_selected_polygons(
            customers_df, 
            selected_polygon_ids, 
            polygons_data
        )
    
    if customers_df.empty or 'latitude' not in customers_df.columns or 'longitude' not in customers_df.columns:
        return pd.DataFrame(), 0, clients_count

    if not isinstance(days, int) or days <= 0:
        raise ValueError("O número de dias deve ser um inteiro positivo.")

    num_customers = len(customers_df)
    if num_customers == 0:
        return pd.DataFrame(), 0, clients_count

    # Calcula o número de clusters (k)
    # Usamos math.ceil para garantir que todos os clientes sejam agrupados
    k = math.ceil(num_customers / days)
    
    # Garante que k não seja maior que o número de clientes
    k = min(k, num_customers)

    # Seleciona as coordenadas para o clustering
    coordinates = customers_df[['latitude', 'longitude']].values

    # Instancia e treina o modelo K-Means
    # n_init='auto' é o padrão recomendado para versões futuras do scikit-learn
    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
    kmeans.fit(coordinates)

    # Adiciona os rótulos dos clusters ao DataFrame original
    customers_df_copy = customers_df.copy()
    customers_df_copy['cluster'] = kmeans.labels_

    return customers_df_copy, k, clients_count

if __name__ == '__main__':
    # Exemplo de uso (para teste direto do script)
    # Criando um DataFrame de exemplo com dados de clientes
    data = {
        'id': range(1, 21),
        'nome': [f'Cliente {i}' for i in range(1, 21)],
        # Coordenadas simuladas em uma área geográfica
        'latitude': np.random.uniform(-23.5, -23.6, 20),
        'longitude': np.random.uniform(-46.6, -46.7, 20)
    }
    df_clientes = pd.DataFrame(data)

    # Polígonos de exemplo
    polygons_example = [
        {
            'id': 1,
            'name': 'Grupo A',
            'coordinates': [
                [-23.55, -46.65],
                [-23.55, -46.60],
                [-23.52, -46.60],
                [-23.52, -46.65],
                [-23.55, -46.65]
            ]
        }
    ]

    # Input do usuário (simulado)
    dias_input = 5
    polygon_ids = [1]  # Filtrar apenas pelo Grupo A

    print(f"Número de clientes total: {len(df_clientes)}")
    print(f"Número de dias para roteirização: {dias_input}")
    
    try:
        # Executa o clustering COM filtragem por polígonos
        df_clusterizado, num_grupos, clients_count = run_kmeans_clustering(
            df_clientes, 
            dias_input,
            selected_polygon_ids=polygon_ids,
            polygons_data=polygons_example
        )

        if clients_count:
            print(f"\nClientes por polígono: {clients_count}")

        print(f"\nClientes filtrados: {len(df_clusterizado)}")
        print(f"O K-Means gerou {num_grupos} grupos.")
        
        if not df_clusterizado.empty:
            print("\nDataFrame com os clusters atribuídos:")
            print(df_clusterizado.head())

            # Mostra a contagem de clientes por grupo
            print("\nContagem de clientes por grupo:")
            print(df_clusterizado['cluster'].value_counts().sort_index())
        else:
            print("\nNenhum cliente encontrado nas áreas selecionadas.")

    except ValueError as e:
        print(f"Erro: {e}")
