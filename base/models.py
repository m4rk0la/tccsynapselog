from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

# Esta instância será inicializada pelo app.py
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modelo de usuário para autenticação - Banco: users_code"""
    
    __bind_key__ = 'users_code' 
    __tablename__ = 'users_code'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Campos de controle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')  # user, admin, manager
    
    def set_password(self, password):
        """Gera hash da senha para armazenamento seguro"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha fornecida está correta"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Atualiza o timestamp do último login"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    # MÉTODOS PARA BUSCAR DADOS RELACIONADOS EM OUTROS BANCOS
    def get_logs(self):
        """Busca todos os logs deste usuário"""
        return SystemLog.query.filter_by(user_id=self.id).all()
    
    def get_locations(self):
        """Busca todas as localizações deste usuário"""
        return LatLong.query.filter_by(id_user=self.id).all()
    
    def get_routes(self):
        """Busca todas as rotas deste usuário"""
        return Routs.query.filter_by(id_user=self.id).all()
    
    def __repr__(self):
        return f'<User {self.username}>'


class SystemLog(db.Model):
    """Modelo para logs do sistema - Banco: logs"""
    
    __bind_key__ = 'logs'
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)  # Referência ao User.id (banco users_code)
    action = db.Column(db.String(100), nullable=False)  # login, logout, create, update, delete
    resource = db.Column(db.String(100), nullable=True)  # recurso afetado
    details = db.Column(db.Text, nullable=True)  # detalhes em JSON
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 ou IPv6
    user_agent = db.Column(db.String(200), nullable=True)  # navegador/dispositivo
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(20), default='INFO')  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    def get_user(self):
        """Busca o usuário relacionado a este log"""
        if self.user_id:
            return User.query.get(self.user_id)
        return None
    
    def __repr__(self):
        return f'<SystemLog {self.action} - {self.timestamp}>'


class ClientName(db.Model):
    """Modelo para dados principais do sistema - Banco: client_name"""
    
    __bind_key__ = 'client_name'
    __tablename__ = 'client_data'
    
    name_client = db.Column(db.String(200), nullable=False)
    hash_client = db.Column(db.Text, nullable=True, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Referência ao User.id (banco users_code)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, hash_client):
        """Gera hash do nome do cliente para armazenamento seguro"""
        self.hash_client = generate_password_hash(hash_client)

    def __repr__(self):
        return f'<ClientName {self.name_client}>'


class LatLong(db.Model):
    """Modelo para dados de localização - Banco: latlong"""

    __bind_key__ = 'latlong'
    __tablename__ = 'latlong_data'
    
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, nullable=False)  # Referência ao User.id (banco users_code)
    hash_client = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=False) 
    longitude = db.Column(db.Float, nullable=False)
    user_point = db.Column(db.Boolean, nullable=True, default=False)  # False = Ponto de entrega/cliente; True = infraestrutura física (loja/galpão/depósito)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_user(self):
        """Busca o usuário que criou esta localização"""
        return User.query.get(self.id_user)
    
    def get_client(self):
        """Busca o cliente relacionado a esta localização"""
        if self.hash_client:
            return ClientName.query.filter_by(hash_client=self.hash_client).first()
        return None

    def __repr__(self):
        return f'<LatLong User:{self.id_user} {self.latitude},{self.longitude}>'
    
class Routs(db.Model):
    """Modelo para rotas - Banco: routs"""

    __bind_key__ = 'routs'
    __tablename__ = 'routs_data'
    
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, nullable=False)  # Referência ao User.id (banco users_code)
    route_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_user(self):
        """Busca o usuário que criou esta rota"""
        return User.query.get(self.id_user)
    
    def __repr__(self):
        return f'<Routs User:{self.id_user} - {self.timestamp}>'
    
class KNN(db.Model):
    """Modelo para rotas com cliente - Banco: routs_w_client"""

    __bind_key__ = 'KNN'
    __tablename__ = 'KNN_data'

    id = db.Column(db.Integer, primary_key=True)
    id_client = db.Column(db.Integer, nullable=False)  # Referência ao ClientName.hash_client
    group_number = db.Column(db.Integer, nullable=True)
    polygon_id = db.Column(db.Integer, nullable=False)  # Referência ao Polygon.id
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_client(self):
        """Busca o cliente relacionado a esta rota"""
        return ClientName.query.get(self.id_client)
    def get_polygon(self):
        """Busca o polígono relacionado a esta rota"""
        return Polygon.query.get(self.polygon_id)
    def __repr__(self):
        return f'<KNN Client:{self.id_client} - Polygon:{self.polygon_id}>'
    
class Polygon(db.Model):
    """Modelo para polígonos - Banco: polygon"""

    __bind_key__ = 'polygon'
    __tablename__ = 'polygon_data'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    group_name = db.Column(db.String(100), nullable=True)
    geojson_data = db.Column(db.Text, nullable=False)  # Armazena coordenadas em formato JSON
    max_clients_per_day = db.Column(db.Integer, nullable=True)  # Máximo de clientes por dia (None = sem limite)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Polygon {self.group_name} - {self.id}>'

class Products(db.Model):
    """Modelo para produtos - Banco: products"""

    __bind_key__ = 'products'
    __tablename__ = 'products_data'

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    product_type = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Products {self.product_name} - ${self.price}>'
    
class Consummer(db.Model):
    """Modelo para consumidores - Banco: consummer"""

    __bind_key__ = 'consummer'
    __tablename__ = 'consummer_data'

    id = db.Column(db.Integer, primary_key=True)
    id_client = db.Column(db.Integer, nullable=False)  # Referência ao ClientName.hash_client
    id_user = db.Column(db.Integer, nullable=False)  # Referência ao User.id (banco users_code)
    product = db.Column(db.String(100), nullable=False)
    product_code = db.Column(db.String(120), unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=True)
    order_status = db.Column(db.Integer, default=0)
    order_delivered_customer_date = db.Column(db.DateTime, nullable=True)
    seller_distance_km = db.Column(db.Float, nullable=True)
    review_score = db.Column(db.Integer, nullable=True)
    review_creation_data = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def get_client(self):
        """Busca o cliente relacionado a este consumidor"""
        return ClientName.query.get(self.id_client)
    def get_user(self):
        """Busca o usuário que criou este consumidor"""
        return User.query.get(self.id_user)

    def __repr__(self):
        return f'<Consummer {self.product} - {self.product_code}>'

class NDBFeatures(db.Model):
    """Modelo para dados de análise - Banco: ml_features"""

    __bind_key__ = 'ml_features'
    __tablename__ = 'ml_features_data' 

    id = db.Column(db.Integer, primary_key=True)
    client_hash = db.Column(db.Text, nullable=True)
    freq_salle_client = db.Column(db.Float, nullable=True)
    tax_order_delivered = db.Column(db.Float, nullable=True)
    sum_distance_km = db.Column(db.Float, nullable=True)
    time_moved = db.Column(db.Float, nullable=True)

    def get_client(self):
        """Busca o cliente relacionado a esta análise"""
        if self.client_hash:
            return ClientName.query.filter_by(hash_client=self.client_hash).first()
        return None
    def __repr__(self):
        return f'<NDBFeatures Client:{self.client_hash} - Freq:{self.freq_salle_client}>'

class NDBOut (db.Model):
    """Modelo para resultados de análise - Banco: neuraldatabaserout"""

    __bind_key__ = 'neuraldatabaserout'
    __tablename__ = 'ndbout_data' 

    id = db.Column(db.Integer, primary_key=True)
    rout_number = db.Column(db.Integer, nullable=True)
    model_version = db.Column(db.String(10), nullable=True)
    score = db.Column(db.Float, nullable=True)
    num_cliets = db.Column(db.Integer, nullable=True)
    sum_distance_km = db.Column(db.Float, nullable=True)
    time_moved = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)

    def get_client(self):
        """Busca o cliente relacionado a este resultado"""
        if self.client_hash:
            return ClientName.query.filter_by(hash_client=self.client_hash).first()
        
    def get_rout_number(self):
        """Busca a rota relacionada a este resultado"""
        if self.rout_number:
            return Routs.query.get(self.rout_number)
        return None


class OrderHistory(db.Model):
    """Modelo para histórico completo de vendas - Banco: order_history"""

    __bind_key__ = 'order_history'
    __tablename__ = 'order_history_data'
    
    # Chave primária
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Identificadores de pedido e item
    id_pedido = db.Column(db.String(100), nullable=False, index=True)
    id_item_pedido = db.Column(db.Integer, nullable=True)
    
    # Identificadores de cliente (relacionados com ClientName)
    id_cliente = db.Column(db.String(100), nullable=True)
    id_unico_cliente = db.Column(db.String(100), nullable=False, index=True)
    hash_cliente = db.Column(db.Text, nullable=True, index=True)  # Hash gerado do id_unico_cliente
    
    # Identificador de produto (relacionado com Products)
    id_produto = db.Column(db.String(100), nullable=True)
    product_code = db.Column(db.String(120), nullable=True)  # Código gerado para Products
    
    # Datas do pedido
    data_compra = db.Column(db.DateTime, nullable=True)
    data_aprovacao = db.Column(db.DateTime, nullable=True)
    data_envio_transportadora = db.Column(db.DateTime, nullable=True)
    data_entrega_cliente = db.Column(db.DateTime, nullable=True)
    data_estimada_entrega = db.Column(db.DateTime, nullable=True)
    data_limite_envio = db.Column(db.DateTime, nullable=True)
    
    # Status e métricas de entrega
    status_pedido = db.Column(db.String(50), nullable=True)
    tempo_entrega_dias = db.Column(db.Integer, nullable=True)
    atraso_entrega_dias = db.Column(db.Integer, nullable=True)
    
    # Campos calculados de data
    ano_compra = db.Column(db.Integer, nullable=True)
    mes_compra = db.Column(db.Integer, nullable=True)
    ano_mes_compra = db.Column(db.String(7), nullable=True)  # Formato: YYYY-MM
    dia_semana_compra = db.Column(db.Integer, nullable=True)  # 0=segunda, 6=domingo
    
    # Valores financeiros
    preco = db.Column(db.Float, nullable=True)
    valor_frete = db.Column(db.Float, nullable=True)
    valor_total_item = db.Column(db.Float, nullable=True)
    valor_total_pagamento = db.Column(db.Float, nullable=True)
    
    # Informações de pagamento
    num_pagamentos = db.Column(db.Integer, nullable=True)
    tipos_pagamento = db.Column(db.String(200), nullable=True)  # Pode conter múltiplos tipos separados por vírgula
    max_parcelas = db.Column(db.Integer, nullable=True)
    
    # Localização do cliente
    cidade_cliente = db.Column(db.String(100), nullable=True)
    estado_cliente = db.Column(db.String(2), nullable=True)
    cep_cliente = db.Column(db.String(10), nullable=True)
    
    # Dados de avaliação/review
    nota_avaliacao = db.Column(db.Integer, nullable=True)  # 1 a 5
    titulo_comentario = db.Column(db.String(200), nullable=True)
    mensagem_comentario = db.Column(db.Text, nullable=True)
    data_criacao_avaliacao = db.Column(db.DateTime, nullable=True)
    data_resposta_avaliacao = db.Column(db.DateTime, nullable=True)
    
    # Metadados de controle
    user_id = db.Column(db.Integer, nullable=True)  # Usuário que importou este registro
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Métodos de relacionamento
    def get_client(self):
        """Busca o cliente relacionado a este pedido"""
        if self.hash_cliente:
            return ClientName.query.filter_by(hash_client=self.hash_cliente).first()
        return None
    
    def get_product(self):
        """Busca o produto relacionado a este pedido"""
        if self.product_code:
            return Products.query.filter_by(product_code=self.product_code).first()
        return None
    
    def get_user(self):
        """Busca o usuário que importou este registro"""
        if self.user_id:
            return User.query.get(self.user_id)
        return None
    
    def __repr__(self):
        return f'<OrderHistory {self.id_pedido} - Cliente:{self.hash_cliente}>'
    
class ClientScore(db.Model):
    """
    Modelo para armazenar scores RFM de clientes
    
    Calculado após import de histórico de vendas para priorização
    em roteirização e análise de segmentação.
    """
    __bind_key__ = 'client_scores'
    __tablename__ = 'client_scores_data'
    
    id = db.Column(db.Integer, primary_key=True)
    hash_cliente = db.Column(db.String(32), nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Scores normalizados (0-100)
    score_total = db.Column(db.Float, nullable=False, index=True)
    score_recencia = db.Column(db.Float, nullable=True)
    score_frequencia = db.Column(db.Float, nullable=True)
    score_valor = db.Column(db.Float, nullable=True)
    score_satisfacao = db.Column(db.Float, nullable=True)
    
    # Features brutas usadas no cálculo
    total_pedidos = db.Column(db.Integer, nullable=True)
    valor_total_vendas = db.Column(db.Float, nullable=True)
    ticket_medio = db.Column(db.Float, nullable=True)
    dias_desde_ultima_compra = db.Column(db.Integer, nullable=True)
    
    # Metadados
    model_version = db.Column(db.String(20), nullable=True, default='v1.0_RFM')
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice composto para queries rápidas
    __table_args__ = (
        db.Index('idx_user_hash', 'user_id', 'hash_cliente'),
        db.Index('idx_user_score', 'user_id', 'score_total'),
    )
    
    def __repr__(self):
        return f'<ClientScore {self.hash_cliente[:8]}... Score:{self.score_total:.1f}>'
    
    def to_dict(self):
        """Serializa para JSON"""
        return {
            'hash_cliente': self.hash_cliente,
            'score_total': round(self.score_total, 2),
            'score_recencia': round(self.score_recencia, 2) if self.score_recencia else None,
            'score_frequencia': round(self.score_frequencia, 2) if self.score_frequencia else None,
            'score_valor': round(self.score_valor, 2) if self.score_valor else None,
            'score_satisfacao': round(self.score_satisfacao, 2) if self.score_satisfacao else None,
            'total_pedidos': self.total_pedidos,
            'valor_total_vendas': round(self.valor_total_vendas, 2) if self.valor_total_vendas else None,
            'ticket_medio': round(self.ticket_medio, 2) if self.ticket_medio else None,
            'dias_desde_ultima_compra': self.dias_desde_ultima_compra,
            'segmento': self.get_segmento(),
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }
    
    def get_segmento(self):
        """Retorna segmento baseado no score total"""
        if self.score_total >= 80:
            return 'VIP'
        elif self.score_total >= 60:
            return 'Alto Valor'
        elif self.score_total >= 40:
            return 'Médio'
        else:
            return 'Em Risco'

class SavedCalendar(db.Model):
    """
    Modelo para armazenar calendários de roteirização salvos
    
    Permite salvar configurações de calendário com clusters alocados por dia
    para reutilização futura e histórico de planejamento.
    """
    __bind_key__ = 'saved_calendars'
    __tablename__ = 'saved_calendars_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Informações básicas
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    
    # Configuração do calendário (JSON)
    configuracao = db.Column(db.Text, nullable=False)  # {dias, incluir_sabado, incluir_domingo, max_clientes_dia}
    
    # Dados das alocações (JSON)
    alocacoes = db.Column(db.Text, nullable=False)  # Lista de {dia, cluster_id, num_clientes, score_medio, polygon_name}
    
    # Estatísticas
    total_clusters = db.Column(db.Integer, nullable=False)
    total_clientes = db.Column(db.Integer, nullable=False)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índices
    __table_args__ = (
        db.Index('idx_user_created', 'user_id', 'created_at'),
    )
    
    def get_user(self):
        """Busca o usuário que criou este calendário"""
        return User.query.get(self.user_id)
    
    def __repr__(self):
        return f'<SavedCalendar {self.nome} - User:{self.user_id}>'
    
    def to_dict(self):
        """Serializa para JSON"""
        import json
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'configuracao': json.loads(self.configuracao) if self.configuracao else {},
            'alocacoes': json.loads(self.alocacoes) if self.alocacoes else [],
            'total_clusters': self.total_clusters,
            'total_clientes': self.total_clientes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
