# 🗄️ Sistema de Múltiplos Bancos de Dados - SynapseLog

## 📊 Visão Geral

O SynapseLog utiliza um sistema de **múltiplos bancos de dados SQLite** especializados para diferentes domínios de dados, incluindo bancos específicos para Machine Learning com Redes Neurais, otimizando performance e organização.

## 📁 Estrutura dos Bancos

```
databases/
├── synapselLog_users_code.db          # 👥 Usuários e Autenticação
├── synapselLog_client_name.db         # 🏢 Dados de Clientes com Hash
├── synapselLog_products.db            # 📦 Catálogo de Produtos
├── synapselLog_consummer.db           # 🛒 Informações de Consumo
├── synapselLog_latlong.db             # 🗺️ Coordenadas (Latitude/Longitude)
├── synapselLog_routs.db               # 🛣️ Rotas Compiladas
├── synapselLog_KNN.db                 # 🚚 Rotas com Clientes (KNN)
├── synapselLog_polygon.db             # 📐 Polígonos Geográficos
├── synapselLog_neuraldatabase.db      # 🧠 Features para Redes Neurais
├── synapselLog_neuraldatabaserout.db  # 🤖 Resultados/Scores da IA
└── synapselLog_logs.db                # 📝 Logs do Sistema
└── synapselLog_logs.db                #  Logs do Sistema
```

## 🗃️ Detalhes dos Bancos

### 👥 **Users Code Database** (`synapselLog_users_code.db`)
- **Finalidade:** Autenticação e gestão de usuários
- **Tabelas:** `users_code`
- **Modelo:** `User`
- **Campos principais:**
  - `id`, `username`, `email`, `password_hash`
  - `created_at`, `last_login`, `is_active`, `role`

### 🏢 **Client Name Database** (`synapselLog_client_name.db`)
- **Finalidade:** Dados de clientes com hash de segurança
- **Tabelas:** `client_data`
- **Modelo:** `ClientName`
- **Campos principais:**
  - `name_client`, `hash_client` (chave primária)

### 🗺️ **Lat/Long Database** (`synapselLog_latlong.db`)
- **Finalidade:** Coordenadas geográficas dos usuários
- **Tabelas:** `latlong_data`
- **Modelo:** `LatLong`
- **Campos principais:**
  - `id`, `id_user` (FK para User), `hash_client`
  - `latitude`, `longitude`, `user_point`, `created_at`

### 🛣️ **Routes Database** (`synapselLog_routs.db`)
- **Finalidade:** Rotas básicas do sistema
- **Tabelas:** `routs_data`
- **Modelo:** `Routs`
- **Campos principais:**
  - `id`, `id_user` (FK para User), `route_name`
  - `start_lat`, `start_lng`, `end_lat`, `end_lng`, `timestamp`

### 🚚 **Routes with Client Database** (`synapselLog_KNN.db`)
- **Finalidade:** Rotas otimizadas com clientes (algoritmo KNN)
- **Tabelas:** `KNN_data`
- **Modelo:** `KNN`
- **Campos principais:**
  - `id`, `id_user` (FK para User), `client_hash`
  - `route_optimization`, `knn_score`, `created_at`

### 📐 **Polygon Database** (`synapselLog_polygon.db`)
- **Finalidade:** Polígonos geográficos definidos pelo usuário
- **Tabelas:** `polygon_data`
- **Modelo:** `Polygon`
- **Campos principais:**
  - `id`, `id_user` (FK para User), `polygon_name`
  - `coordinates_json`, `area`, `created_at`

### � **Products Database** (`synapselLog_products.db`)
- **Finalidade:** Catálogo de produtos do sistema
- **Tabelas:** `products_data`
- **Modelo:** `Products`
- **Campos principais:**
  - `id`, `product_name`, `category`
  - `price`, `description`, `created_at`

### 🛒 **Consumer Database** (`synapselLog_consummer.db`)
- **Finalidade:** Dados de consumo e comportamento
- **Tabelas:** `consummer_data`
- **Modelo:** `Consummer`
- **Campos principais:**
  - `id`, `id_user` (FK para User), `consumption_type`
  - `quantity`, `frequency`, `preferences_json`

### 🧠 **Neural Database** (`synapselLog_neuraldatabase.db`)
- **Finalidade:** Features processadas para Machine Learning
- **Tabelas:** `neural_features`
- **Modelo:** `NDBFeatures`
- **Campos principais:**
  - `id`, `id_user` (FK para User), `feature_vector`
  - `processed_data`, `training_ready`, `created_at`

### 🤖 **Neural Database Routes** (`synapselLog_neuraldatabaserout.db`)
- **Finalidade:** Resultados e scores das redes neurais para rotas
- **Tabelas:** `neural_routes_results`
- **Campos principais:**
  - `id`, `route_id`, `neural_score`
  - `prediction_accuracy`, `model_version`

### 📝 **Logs Database** (`synapselLog_logs.db`)
- **Finalidade:** Registro de ações e eventos do sistema
- **Tabelas:** `system_logs`
- **Modelo:** `SystemLog`
- **Campos principais:**
  - `id`, `user_id` (FK para User), `action`, `resource`
  - `details`, `ip_address`, `user_agent`, `timestamp`, `level`

## � Relacionamentos

### Estrutura de Relacionamentos Cross-Database:
```
users_code (id) → latlong_data (id_user)
users_code (id) → routs_data (id_user)
users_code (id) → routswclient_data (id_user)
users_code (id) → polygon_data (id_user)
users_code (id) → consummer_data (id_user)
users_code (id) → neural_features (id_user)
users_code (id) → system_logs (user_id)

client_data (hash_client) → latlong_data (hash_client)
routs_data (id) → neural_routes_results (route_id)
```

### Fluxo de Dados:
1. **Usuário faz login** → Validação em `users_code` e registro em `system_logs`
2. **Coleta de dados geográficos** → Entrada em `latlong_data` vinculada ao usuário
3. **Criação de rotas** → Dados em `routs_data` e processamento em `routswclient_data`
4. **Machine Learning** → Features em `neural_features` e resultados em `neural_routes_results`
5. **Análise de polígonos** → Geometrias em `polygon_data` para análise territorial

### Métodos Helper para Relacionamentos:
Devido às limitações do SQLite com foreign keys cross-database, foram implementados métodos helper nos modelos para simular relacionamentos:
- `User.get_locations()` - Busca coordenadas do usuário
- `User.get_routes()` - Recupera rotas do usuário
- `LatLong.get_user()` - Obtém dados do usuário proprietário

## �🛠️ Scripts de Gerenciamento

### Inicialização
```bash
# Criar todos os bancos e tabelas
python init_multiple_dbs.py

# Criar apenas usuário admin
python create_admin.py
```

### Gerenciamento
```bash
# Interface de gerenciamento interativa
python manage_databases.py
```

### Comandos Python
```python
from manage_databases import show_database_info, create_sample_data, backup_databases

# Mostrar informações
show_database_info()

# Criar dados de exemplo
create_sample_data()

# Fazer backup
backup_databases()
```

## ⚙️ Configuração

### Arquivo: `config.py`
```python
SQLALCHEMY_BINDS = {
    'users_code': 'sqlite:///databases/synapselLog_users_code.db',
    'client_name': 'sqlite:///databases/synapselLog_client_name.db',
    'products': 'sqlite:///databases/synapselLog_products.db',
    'consummer': 'sqlite:///databases/synapselLog_consummer.db',
    'routs': 'sqlite:///databases/synapselLog_routs.db',
    'latlong': 'sqlite:///databases/synapselLog_latlong.db',
    'routswclient': 'sqlite:///databases/synapselLog_routswclient.db',
    'polygon': 'sqlite:///databases/synapselLog_polygon.db',
    'neuraldatabase': 'sqlite:///databases/synapselLog_neuraldatabase.db',
    'neuraldatabaserout': 'sqlite:///databases/synapselLog_neuraldatabaserout.db',
    'logs': 'sqlite:///databases/synapselLog_logs.db'
}
```

### Uso nos Modelos
```python
class User(db.Model):
    __bind_key__ = 'users_code'  # Especifica o banco
    # ... campos do modelo

class LatLong(db.Model):
    __bind_key__ = 'latlong'
    # ... campos do modelo

class NDBFeatures(db.Model):
    __bind_key__ = 'neuraldatabase'
    # ... campos do modelo
```

## 🔧 Comandos Úteis

### Verificar Status dos Bancos
```bash
# Listar arquivos
ls databases/

# Verificar tamanhos
du -sh databases/*

# Informações detalhadas
python -c "from manage_databases import show_database_info; show_database_info()"
```

### Backup Manual
```bash
# Criar pasta de backup
mkdir backups

# Copiar bancos
cp databases/*.db backups/
```

### Migração de Dados
```bash
# Criar nova migração
flask db migrate -m "descrição da mudança"

# Aplicar migrações
flask db upgrade
```

## 🚀 Vantagens do Sistema

1. **📈 Performance:** Dados separados por tipo/função com otimização específica
2. **🔧 Manutenção:** Backups e manutenção independentes por domínio
3. **📊 Escalabilidade:** Fácil migração para outros SGBDs especializados
4. **🔒 Segurança:** Isolamento de dados sensíveis em bancos dedicados
5. **📝 Logs:** Sistema de auditoria robusto e separado
6. **🧠 ML Ready:** Bancos especializados para processamento neural e rotas otimizadas
7. **🗺️ Geolocalização:** Gestão eficiente de dados geográficos e polígonos

## 🔑 Credenciais Padrão

- **Email:** `admin@synapselLog.com`
- **Senha:** `123456`
- **Role:** `admin`

> ⚠️ **IMPORTANTE:** Altere a senha padrão em produção!

## 📞 Suporte

Para problemas com bancos de dados:

1. Execute `python manage_databases.py`
2. Verifique logs de erro
3. Use backup para restaurar se necessário
4. Recrie bancos com `python init_multiple_dbs.py` se crítico

---

*Documentação atualizada em: 22 de Setembro de 2025*