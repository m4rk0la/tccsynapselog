import pandas as pd
import numpy as np
import os
from datetime import datetime

# Função para ler arquivo em diferentes formatos
def ler_arquivo_para_dataframe(caminho_arquivo):
    extensao = os.path.splitext(caminho_arquivo)[1].lower()
    if extensao == '.csv':
        df = pd.read_csv(caminho_arquivo)
    elif extensao in ['.xls', '.xlsx']:
        df = pd.read_excel(caminho_arquivo)
    elif extensao == '.json':
        df = pd.read_json(caminho_arquivo)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {extensao}")
    return df

# Conversão e limpeza dos tipos das colunas
if not pd.api.types.is_integer_dtype(df['ID']):
    df['ID'] = pd.to_numeric(df['ID'], errors='coerce').astype('Int64')
if not pd.api.types.is_float_dtype(df['Preço']):
    df['Preço'] = pd.to_numeric(df['Preço'], errors='coerce')
if df['Tipo'].dtype != 'O':
    df['Tipo'] = df['Tipo'].astype(str)
df['Tipo'] = df['Tipo'].str[:100]
if df['Nome'].dtype != 'O':
    df['Nome'] = df['Nome'].astype(str)
df['Nome'] = df['Nome'].str[:100]

# Exemplo de agrupamento de produtos por categoria
produtos_por_categoria = df.groupby('Tipo')['Nome'].apply(lambda x: x.dropna().tolist()).to_dict()

# Exemplo de função para salvar no banco de dados (mock, pois não temos o modelo Products nem db configurado aqui)

def salvar_produtos_no_banco(df):
    # Supondo que db e Products estejam definidos no contexto Flask
    produtos = []
    for _, row in df.iterrows():
        if pd.isna(row['Nome']) or pd.isna(row['Preço']):
            continue
        produto = Products(
            product_name=row['Nome'][:100],
            product_type=row['Tipo'][:100] if not pd.isna(row['Tipo']) else None,
            price=float(row['Preço']),
            created_at=datetime.utcnow()
        )
        produtos.append(produto)
    db.session.bulk_save_objects(produtos)
    db.session.commit()