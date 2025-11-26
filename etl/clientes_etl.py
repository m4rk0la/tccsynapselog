import pandas as pd
from datetime import datetime
from base.models import db, ClientName, LatLong, SystemLog
import time
from sqlalchemy.exc import OperationalError

def processar_etl_clientes(file_path, user_id, ip_address=None, user_agent=None):
    """
    ETL para processar arquivo de clientes e inserir nos bancos de dados
    """
    try:
        # Log de início do processo
        log_inicio = SystemLog(
            user_id=user_id,
            action='ETL_START',
            resource='clientes_upload',
            details=f'Iniciando processamento do arquivo: {file_path}',
            ip_address=ip_address,
            user_agent=user_agent,
            level='INFO'
        )
        db.session.add(log_inicio)
        db.session.commit()
        
        # 1. EXTRAÇÃO - Carrega o arquivo Excel
        df_clientes = pd.read_excel(file_path, engine='openpyxl')
        
        if df_clientes.empty:
            raise ValueError("Arquivo vazio ou sem dados válidos")
        
        # 2. TRANSFORMAÇÃO
        # IMPORTANTE: Usa o identificador original DIRETO como hash_client
        # Não aplica nenhuma transformação de hash
        df_clientes['Nome_Hash'] = df_clientes['Nome'].astype(str)
        df_clientes['User_ID'] = user_id
        
        # Mantém apenas os 5 primeiros dígitos do CEP
        df_clientes['CEP'] = df_clientes['CEP'].astype(str).str[:5]
        
        # Separa dados para diferentes tabelas
        df_nomes = df_clientes[['Nome', 'Nome_Hash', 'User_ID', 'Cidade', 'Estado']].copy()
        df_latlong = df_clientes[['Nome_Hash', 'CEP', 'Latitude', 'Longitude']].dropna(subset=['Latitude', 'Longitude']).copy()
        
        # 3. CARREGAMENTO (LOAD)
        registros_inseridos = {'clientes': 0, 'localizacoes': 0, 'duplicados': 0}
        
        # Inserir dados de clientes no banco client_name
        for _, row in df_nomes.iterrows():
            # Verifica se já existe (evita duplicatas)
            cliente_existente = ClientName.query.filter_by(hash_client=row['Nome_Hash']).first()
            
            if not cliente_existente:
                novo_cliente = ClientName(
                    name_client=row['Nome'],
                    hash_client=row['Nome_Hash'],
                    user_id=row['User_ID'],
                    cidade=row['Cidade'],
                    estado=row['Estado']
                )
                db.session.add(novo_cliente)
                registros_inseridos['clientes'] += 1
            else:
                registros_inseridos['duplicados'] += 1
        
        # Commit com retry em caso de database locked
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.session.commit()
                break
            except OperationalError as e:
                if 'database is locked' in str(e) and attempt < max_retries - 1:
                    print(f"⚠️  Database locked, tentativa {attempt + 1}/{max_retries}...")
                    time.sleep(1)
                    continue
                else:
                    raise
        
        # Inserir dados de localização no banco latlong
        for _, row in df_latlong.iterrows():
            # Verifica se já existe localização para este cliente
            loc_existente = LatLong.query.filter_by(
                hash_client=row['Nome_Hash'],
                id_user=user_id
            ).first()
            
            if not loc_existente:
                nova_localizacao = LatLong(
                    id_user=user_id,
                    hash_client=row['Nome_Hash'],
                    latitude=float(row['Latitude']),
                    longitude=float(row['Longitude']),
                    user_point=False  # Cliente, não infraestrutura
                )
                db.session.add(nova_localizacao)
                registros_inseridos['localizacoes'] += 1
        
        # Commit das inserções com retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.session.commit()
                break
            except OperationalError as e:
                if 'database is locked' in str(e) and attempt < max_retries - 1:
                    print(f"⚠️  Database locked, tentativa {attempt + 1}/{max_retries}...")
                    time.sleep(1)
                    continue
                else:
                    raise
        
        # Log de sucesso
        log_sucesso = SystemLog(
            user_id=user_id,
            action='ETL_SUCCESS',
            resource='clientes_upload',
            details=f'Processamento concluído: {registros_inseridos}',
            ip_address=ip_address,
            user_agent=user_agent,
            level='INFO'
        )
        db.session.add(log_sucesso)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Dados importados com sucesso!',
            'data': {
                'total_linhas_arquivo': len(df_clientes),
                'clientes_inseridos': registros_inseridos['clientes'],
                'localizacoes_inseridas': registros_inseridos['localizacoes'],
                'duplicados_ignorados': registros_inseridos['duplicados'],
                'colunas_processadas': list(df_clientes.columns)
            }
        }
        
    except Exception as e:
        # Rollback em caso de erro
        db.session.rollback()
        
        # Log de erro
        log_erro = SystemLog(
            user_id=user_id,
            action='ETL_ERROR',
            resource='clientes_upload',
            details=f'Erro no processamento: {str(e)}',
            ip_address=ip_address,
            user_agent=user_agent,
            level='ERROR'
        )
        db.session.add(log_erro)
        db.session.commit()
        
        return {
            'success': False,
            'error': f'Erro no processamento ETL: {str(e)}',
            'data': None
        }

def get_estatisticas_usuario(user_id):
    """
    Retorna estatísticas dos dados do usuário
    """
    try:
        total_clientes = ClientName.query.filter_by(user_id=user_id).count()
        total_localizacoes = LatLong.query.filter_by(id_user=user_id).count()
        
        return {
            'total_clientes': total_clientes,
            'total_localizacoes': total_localizacoes,
            'ultimo_upload': SystemLog.query.filter_by(
                user_id=user_id, 
                action='ETL_SUCCESS'
            ).order_by(SystemLog.timestamp.desc()).first()
        }
    except Exception as e:
        return {'error': str(e)}