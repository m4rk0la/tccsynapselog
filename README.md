# 🧠 SynapseLog - Gestão Inteligente de Vendas e Roteirização

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Sistema de análise geoespacial de vendas com machine learning para otimização logística.

## 🎯 Funcionalidades

- 📍 **Mapeamento Geoespacial**: Visualização de clientes em mapas interativos (Leaflet.js)
- 🗺️ **Gestão de Áreas**: Criação de polígonos/grupos de atendimento
- 📊 **Analytics em Tempo Real**: Dashboard com estatísticas de vendas por região
- 🚚 **Roteirização Inteligente**: Otimização de rotas com K-Means clustering
- 📈 **Histórico de Vendas**: Análise completa de performance comercial
- 🔐 **Multi-usuário**: Sistema de autenticação e isolamento de dados

## 🏗️ Arquitetura

### Multi-Database Strategy
Sistema com **11 bancos SQLite especializados**:

```
databases/
├── synapselLog_users_code.db       # Usuários e autenticação
├── synapselLog_client_name.db      # Cadastro de clientes
├── synapselLog_latlong.db          # Coordenadas geográficas
├── synapselLog_polygon.db          # Áreas/grupos no mapa
├── synapselLog_order_history.db    # Histórico de vendas
├── synapselLog_products.db         # Catálogo de produtos
├── synapselLog_routs.db            # Rotas planejadas
└── ... (+ 4 bancos ML/analytics)
```

### Stack Tecnológico

**Backend:**
- Python 3.8+
- Flask 2.0+ (Web Framework)
- SQLAlchemy (ORM multi-database)
- Pandas (ETL de dados)
- Scikit-learn (Machine Learning)
- Shapely (Processamento geoespacial)

**Frontend:**
- Leaflet.js (Mapas interativos)
- Chart.js (Visualizações)
- JavaScript Vanilla
- CSS3 (Tema dark customizado)

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Setup Rápido

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/synapselLog.git
cd synapselLog

# 2. Crie ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edite .env com suas configurações

# 5. Inicialize os bancos de dados
python scripts/setup/init_multiple_dbs.py

# 6. Crie usuário admin
python scripts/setup/create_admin.py

# 7. Execute a aplicação
python app.py
```

Acesse: `http://localhost:5000`

**Login padrão:**
- Email: `admin@synapselLog.com`
- Senha: `admin123`

## 📂 Estrutura do Projeto

```
my-flask-app/
├── app.py                    # Entry point
├── config.py                 # Configuração multi-database
├── requirements.txt
│
├── base/                     # Aplicação principal
│   ├── __init__.py          # Flask app factory
│   ├── routes.py            # 40+ endpoints
│   ├── models.py            # 12 SQLAlchemy models
│   ├── forms.py             # Flask-WTF forms
│   ├── utils.py             # Utilitários (hash, etc)
│   ├── templates/           # HTML templates
│   └── static/              # CSS/JS
│
├── data_processing/          # ETL pipelines
│   └── etl/                 # Processadores Excel
│
├── ml/                       # Machine Learning
│   ├── geo_utils.py         # Otimização geoespacial
│   └── neural_model.py      # Modelos preditivos
│
├── databases/                # SQLite databases
├── docs/                     # Documentação técnica
├── tests/                    # Testes unitários
└── scripts/                  # Scripts de gerenciamento
    ├── setup/               # Inicialização
    ├── maintenance/         # Manutenção do banco
    ├── debug/               # Debug e validação
    └── analysis/            # Análises de dados
```

## 📖 Documentação

- [📘 Sistema de Hash](docs/HASH_PADRONIZACAO.md) - **CRÍTICO: Leia primeiro!**
- [👥 Gerenciamento Multi-usuário](docs/USER_ID_MANAGEMENT.md)
- [🗄️ Estrutura de Bancos](docs/DATABASE_README.md)
- [📊 Dashboard Analytics](docs/PAINEL_STATS.md)
- [🔧 Guia de Scripts](docs/SCRIPTS_GUIDE.md)

## 🔑 Funcionalidades Principais

### 1. Importação de Dados
```bash
# Upload de clientes via Excel
POST /autenticado/clientes
- Valida planilha
- Gera hash MD5 padronizado
- Insere em ClientName + LatLong
```

### 2. Mapeamento de Áreas
```bash
# Criar grupos geográficos
POST /autenticado/grupos
- Desenha polígonos no mapa
- Salva GeoJSON
- Associa clientes automaticamente
```

### 3. Dashboard Analytics
```bash
# Estatísticas em tempo real
GET /autenticado/painel
- Clientes por área
- Gráficos interativos
- Auto-refresh (30s)
```

### 4. Roteirização
```bash
# Otimização de rotas
POST /autenticado/roteirizacao/processar
- K-Means clustering
- Divisão por dias de entrega
- Export de rotas
```

## 🧪 Testes

```bash
# Testes unitários
python -m unittest discover -s tests

# Validação de sistema
python scripts/debug/check_db.py
python scripts/debug/test_hash_consistency.py
python scripts/debug/test_join_vendas_clientes.py
```

## 🔐 Sistema de Hash (Crítico!)

**TODAS as referências cliente/pedido usam hash MD5 padronizado:**

```python
from base.utils import generate_client_hash

# ✅ SEMPRE use esta função
hash_value = generate_client_hash(client_id)
# Normalização: trim + lowercase + MD5
```

**Documentação completa:** `docs/HASH_PADRONIZACAO.md`

## 🛠️ Scripts de Gerenciamento

```bash
# Setup inicial completo
python scripts/setup.py

# Verificar estado dos bancos
python scripts/debug/check_db.py

# Limpar dados (CUIDADO!)
python scripts/maintenance/limpar_banco.py

# Analisar hashes
python scripts/debug/analisar_hashes_arquivos.py
```

## 📊 Casos de Uso

### Exemplo 1: Import de Clientes
```python
# 1. Upload Excel com colunas: ID, Nome, Cidade, Lat, Long
# 2. Sistema gera hash MD5 do ID
# 3. Insere em 2 bancos: ClientName + LatLong
# 4. Marca no mapa automaticamente
```

### Exemplo 2: Análise de Vendas por Região
```python
# 1. Desenha área "Zona Sul" no mapa
# 2. Sistema filtra clientes dentro do polígono
# 3. JOIN com histórico de vendas (via hash)
# 4. Dashboard mostra total vendido na Zona Sul
```

## ⚠️ Limitações Conhecidas

- ⚠️ SQLite (não PostgreSQL) - sem foreign keys cross-database
- ⚠️ Sem cache layer (Redis recomendado para produção)
- ⚠️ UI não responsiva para mobile (em desenvolvimento)
- ⚠️ Testes unitários precisam atualização

## 🚧 Roadmap

- [ ] Migração para PostgreSQL
- [ ] API REST completa
- [ ] Export Excel/PDF de relatórios
- [ ] WebSocket para updates em tempo real
- [ ] Internacionalização (i18n)
- [ ] Docker/Kubernetes deployment
- [ ] Testes E2E com Selenium

## 🎓 Contexto Acadêmico

Este projeto é um **TCC (Trabalho de Conclusão de Curso)** focado em:
- Análise geoespacial de vendas
- Machine Learning aplicado à logística
- Business Intelligence com dashboards interativos
- Geomarketing e segmentação de clientes

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: nova funcionalidade'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

**Antes de contribuir, leia:**
- `docs/HASH_PADRONIZACAO.md` (sistema de hash)
- `.github/copilot-instructions.md` (padrões do projeto)

## 📄 Licença

Este projeto está sob a licença MIT. Veja `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Marco** - [GitHub](https://github.com/seu-usuario)

## 🙏 Agradecimentos

- Leaflet.js
- Flask
- Shapely
- Python

---

**⭐ Se este projeto foi útil, considere dar uma estrela!**

📧 Contato: seu-email@example.com