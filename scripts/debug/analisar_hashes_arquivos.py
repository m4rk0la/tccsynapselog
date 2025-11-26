"""
Script para analisar os arquivos de clientes e vendas
e descobrir qual campo usar para fazer o match dos hashes
"""

import pandas as pd
from base.utils import generate_client_hash

print("=" * 80)
print("🔍 ANÁLISE DE ARQUIVOS - Clientes vs Histórico de Vendas")
print("=" * 80)

# Solicita os caminhos dos arquivos
print("\n📂 Informe os caminhos dos arquivos:")
print("-" * 80)
arquivo_clientes = input("Caminho do arquivo de CLIENTES (Excel): ").strip().strip('"')
arquivo_vendas = input("Caminho do arquivo de HISTÓRICO DE VENDAS (Excel/CSV): ").strip().strip('"')

try:
    # 1. Carrega arquivo de clientes
    print("\n📊 CARREGANDO ARQUIVO DE CLIENTES...")
    print("-" * 80)
    
    if arquivo_clientes.endswith('.csv'):
        df_clientes = pd.read_csv(arquivo_clientes)
    else:
        df_clientes = pd.read_excel(arquivo_clientes, engine='openpyxl')
    
    print(f"✅ {len(df_clientes)} clientes carregados")
    print(f"Colunas: {list(df_clientes.columns)}")
    
    # Mostra amostra
    print("\n📝 AMOSTRA DE CLIENTES (primeiras 3 linhas):")
    print(df_clientes.head(3).to_string())
    
    # 2. Carrega arquivo de vendas
    print("\n\n📊 CARREGANDO ARQUIVO DE HISTÓRICO DE VENDAS...")
    print("-" * 80)
    
    if arquivo_vendas.endswith('.csv'):
        df_vendas = pd.read_csv(arquivo_vendas)
    else:
        df_vendas = pd.read_excel(arquivo_vendas, engine='openpyxl')
    
    print(f"✅ {len(df_vendas)} vendas carregadas")
    print(f"Colunas: {list(df_vendas.columns)}")
    
    # Mostra amostra
    print("\n📝 AMOSTRA DE VENDAS (primeiras 3 linhas):")
    print(df_vendas.head(3).to_string())
    
    # 3. Identifica campos de identificação
    print("\n\n🔑 CAMPOS DE IDENTIFICAÇÃO DISPONÍVEIS:")
    print("-" * 80)
    
    print("\n🧑 No arquivo de CLIENTES, temos:")
    for col in df_clientes.columns:
        valores_unicos = df_clientes[col].nunique()
        print(f"  - {col}: {valores_unicos:,} valores únicos")
    
    print("\n📦 No arquivo de VENDAS, temos:")
    for col in df_vendas.columns:
        if 'cliente' in col.lower() or 'customer' in col.lower() or 'id' in col.lower():
            valores_unicos = df_vendas[col].nunique()
            print(f"  - {col}: {valores_unicos:,} valores únicos")
    
    # 4. Pergunta qual campo usar
    print("\n\n❓ CONFIGURAÇÃO:")
    print("-" * 80)
    print("Para fazer o match entre clientes e vendas, precisamos saber:")
    
    campo_cliente = input("\n1️⃣  Qual campo do arquivo de CLIENTES deve ser usado como identificador? ").strip()
    campo_venda = input("2️⃣  Qual campo do arquivo de VENDAS corresponde ao cliente? ").strip()
    
    # 5. Testa correspondência
    print("\n\n🧪 TESTE DE CORRESPONDÊNCIA:")
    print("-" * 80)
    
    # Valores únicos de cada arquivo
    valores_clientes = set(df_clientes[campo_cliente].dropna().astype(str).unique())
    valores_vendas = set(df_vendas[campo_venda].dropna().astype(str).unique())
    
    print(f"\n📊 Valores únicos em CLIENTES[{campo_cliente}]: {len(valores_clientes):,}")
    print(f"📊 Valores únicos em VENDAS[{campo_venda}]: {len(valores_vendas):,}")
    
    # Interseção direta
    match_direto = valores_clientes.intersection(valores_vendas)
    print(f"\n✅ Match DIRETO (sem hash): {len(match_direto):,} valores")
    
    if len(match_direto) > 0:
        print(f"\n🎉 ÓTIMA NOTÍCIA! Os valores já fazem match direto!")
        print(f"Você pode usar o campo '{campo_cliente}' em ambos os arquivos.")
        print("\n📝 Exemplos de valores que fazem match:")
        for i, valor in enumerate(list(match_direto)[:5], 1):
            print(f"  {i}. {valor}")
    else:
        print(f"\n⚠️  Não há match direto. Vamos testar com hash...")
        
        # Gera hashes
        print("\n🔄 Gerando hashes usando generate_client_hash()...")
        
        hashes_clientes = {generate_client_hash(str(v)): str(v) for v in valores_clientes}
        hashes_vendas = {generate_client_hash(str(v)): str(v) for v in valores_vendas}
        
        # Match com hash
        match_com_hash = set(hashes_clientes.keys()).intersection(set(hashes_vendas.keys()))
        
        print(f"✅ Match COM HASH: {len(match_com_hash):,} valores")
        
        if len(match_com_hash) > 0:
            print(f"\n🎉 ENCONTRAMOS MATCH COM HASH!")
            print("\n📝 Exemplos de hashes que fazem match:")
            for i, hash_valor in enumerate(list(match_com_hash)[:5], 1):
                valor_cliente = hashes_clientes[hash_valor]
                valor_venda = hashes_vendas[hash_valor]
                print(f"  {i}. Hash: {hash_valor[:16]}...")
                print(f"     Cliente: {valor_cliente}")
                print(f"     Venda: {valor_venda}")
                print()
        else:
            print(f"\n❌ Ainda não há match com hash!")
            print("\n🔍 Vamos investigar mais:")
            
            # Mostra amostras
            print("\n📋 Amostra de valores em CLIENTES:")
            for i, v in enumerate(list(valores_clientes)[:5], 1):
                h = generate_client_hash(str(v))
                print(f"  {i}. Valor: {v}")
                print(f"     Hash: {h}")
            
            print("\n📋 Amostra de valores em VENDAS:")
            for i, v in enumerate(list(valores_vendas)[:5], 1):
                h = generate_client_hash(str(v))
                print(f"  {i}. Valor: {v}")
                print(f"     Hash: {h}")
    
    # 6. Recomendação
    print("\n\n💡 RECOMENDAÇÃO:")
    print("=" * 80)
    
    if len(match_direto) > 0:
        percentual = (len(match_direto) / len(valores_vendas)) * 100
        print(f"✅ Use os valores DIRETOS (sem hash)")
        print(f"✅ Match: {len(match_direto):,} de {len(valores_vendas):,} ({percentual:.1f}%)")
        print(f"\n📝 Configure o ETL para usar:")
        print(f"   - Clientes: campo '{campo_cliente}'")
        print(f"   - Vendas: campo '{campo_venda}'")
        print(f"   - Função hash: generate_client_hash()")
    elif len(match_com_hash) > 0:
        percentual = (len(match_com_hash) / len(valores_vendas)) * 100
        print(f"✅ Use HASH gerado pela função generate_client_hash()")
        print(f"✅ Match: {len(match_com_hash):,} de {len(valores_vendas):,} ({percentual:.1f}%)")
        print(f"\n📝 Configure o ETL para usar:")
        print(f"   - Clientes: generate_client_hash({campo_cliente})")
        print(f"   - Vendas: generate_client_hash({campo_venda})")
    else:
        print(f"❌ NÃO há correspondência entre os arquivos!")
        print(f"\n🤔 Possíveis causas:")
        print(f"   1. Os campos escolhidos não são correspondentes")
        print(f"   2. Os dados estão em formatos diferentes")
        print(f"   3. Pode haver necessidade de limpeza/normalização")
        print(f"\n💡 Tente escolher outros campos ou verifique os dados")
    
    print("=" * 80)

except Exception as e:
    print(f"\n❌ ERRO: {str(e)}")
    import traceback
    traceback.print_exc()
