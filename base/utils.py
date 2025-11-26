"""
Funções utilitárias centralizadas para todo o sistema SynapseLog
"""
import hashlib


def generate_client_hash(identificador):
    """
    Gera hash único e consistente para um cliente.
    
    IMPORTANTE: Esta é a função OFICIAL do sistema.
    Use esta função em TODOS os ETLs e scripts para garantir consistência.
    
    Parâmetros:
        identificador: Pode ser nome do cliente, ID único, CPF/CNPJ, etc.
                      O importante é que seja sempre o MESMO valor para o mesmo cliente.
    
    Retorna:
        str: Hash MD5 em hexadecimal (32 caracteres)
    
    Exemplos:
        >>> generate_client_hash('Cliente ABC Ltda')
        'a1b2c3d4e5f6...'
        
        >>> generate_client_hash('12345678900')
        'x9y8z7w6v5u4...'
    """
    # Converte para string e remove espaços extras
    id_str = str(identificador).strip()
    
    # Normaliza para minúsculas para evitar problemas de case-sensitivity
    id_str = id_str.lower()
    
    # Gera hash MD5
    return hashlib.md5(id_str.encode('utf-8')).hexdigest()


def generate_product_code(id_produto):
    """
    Gera código único para um produto.
    
    Parâmetros:
        id_produto: Identificador do produto
    
    Retorna:
        str: Código no formato PROD_XXXXX
    """
    return f"PROD_{str(id_produto)}"


def validate_hash(hash_string):
    """
    Valida se uma string é um hash MD5 válido.
    
    Parâmetros:
        hash_string: String a ser validada
    
    Retorna:
        bool: True se for um hash MD5 válido (32 caracteres hexadecimais)
    """
    if not hash_string or len(hash_string) != 32:
        return False
    
    try:
        int(hash_string, 16)  # Tenta converter de hexadecimal
        return True
    except ValueError:
        return False
