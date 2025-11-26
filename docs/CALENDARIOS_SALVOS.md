# Calendários Salvos - Sistema de Roteirização

## Visão Geral

O sistema de **Calendários Salvos** permite que usuários salvem configurações completas de calendários de roteirização, incluindo:
- Configurações do calendário (dias, inclusão de sábado/domingo, máximo de clientes por dia)
- Alocações de clusters por dia
- Estatísticas agregadas (total de clusters e clientes)

## Arquitetura

### 1. Modelo de Dados (`SavedCalendar`)

**Banco de dados:** `synapselLog_saved_calendars.db`

```python
class SavedCalendar(db.Model):
    id: int                  # Chave primária
    user_id: int            # ID do usuário (relação com users_code)
    nome: str               # Nome do calendário
    descricao: str          # Descrição opcional
    configuracao: JSON      # Configurações do calendário
    alocacoes: JSON         # Lista de alocações dia->cluster
    total_clusters: int     # Total de clusters alocados
    total_clientes: int     # Total de clientes nos clusters
    created_at: datetime    # Data de criação
    updated_at: datetime    # Data da última atualização
```

### 2. Estrutura de Dados

#### Configuração (JSON)
```json
{
    "dias": 30,
    "incluir_sabado": false,
    "incluir_domingo": false,
    "max_clientes_dia": 50
}
```

#### Alocações (JSON Array)
```json
[
    {
        "dia": 1,
        "cluster_id": 3,
        "num_clientes": 45,
        "score_medio": 67.5,
        "polygon_name": "Zona Sul",
        "clientes": [
            {
                "hash_cliente": "a1b2c3d4...",
                "latitude": -23.5505,
                "longitude": -46.6333,
                "score": 72.3
            },
            {
                "hash_cliente": "e5f6g7h8...",
                "latitude": -23.5489,
                "longitude": -46.6388,
                "score": 65.1
            }
        ]
    },
    {
        "dia": 2,
        "cluster_id": 1,
        "num_clientes": 38,
        "score_medio": 82.3,
        "polygon_name": "Centro",
        "clientes": [...]
    }
]
```

## Como Consultar Clientes de um Cluster

### Método 1: Via JSON Salvo (Download Local)

Quando você salva um calendário, o sistema gera um arquivo JSON com **todos os clientes**:

```json
{
  "nome": "Calendário Novembro 2025",
  "alocacoes": [
    {
      "dia": 1,
      "cluster_id": 3,
      "clientes": [
        {
          "hash_cliente": "abc123...",
          "latitude": -23.5505,
          "longitude": -46.6333,
          "score": 72.3
        }
      ]
    }
  ]
}
```

### Método 2: Via API - Clientes de um Dia Específico

**Endpoint:** `GET /autenticado/roteirizacao/calendario/<calendario_id>/clientes/<dia>`

**Exemplo:**
```bash
GET /autenticado/roteirizacao/calendario/42/clientes/1
```

**Resposta:**
```json
{
    "success": true,
    "dia": 1,
    "cluster_id": 3,
    "polygon_name": "Zona Sul",
    "num_clientes": 45,
    "score_medio": 67.5,
    "clientes": [
        {
            "hash_cliente": "a1b2c3d4...",
            "nome": "Cliente ABC Ltda",
            "cidade": "São Paulo",
            "estado": "SP",
            "latitude": -23.5505,
            "longitude": -46.6333,
            "score": 72.3
        },
        {
            "hash_cliente": "e5f6g7h8...",
            "nome": "Loja XYZ",
            "cidade": "São Paulo",
            "estado": "SP",
            "latitude": -23.5489,
            "longitude": -46.6388,
            "score": 65.1
        }
    ]
}
```

### Método 3: Via API - Exportar Todos os Clientes

**Endpoint:** `GET /autenticado/roteirizacao/calendario/<calendario_id>/exportar-clientes`

**Exemplo:**
```bash
GET /autenticado/roteirizacao/calendario/42/exportar-clientes
```

**Resposta:**
```json
{
    "success": true,
    "resultado": {
        "calendario_id": 42,
        "nome_calendario": "Calendário Novembro 2025",
        "created_at": "2025-11-12T10:30:15.123Z",
        "dias": [
            {
                "dia": 1,
                "cluster_id": 3,
                "polygon_name": "Zona Sul",
                "num_clientes": 45,
                "score_medio": 67.5,
                "clientes": [...]
            },
            {
                "dia": 2,
                "cluster_id": 1,
                "polygon_name": "Centro",
                "num_clientes": 38,
                "score_medio": 82.3,
                "clientes": [...]
            }
        ]
    }
}
```

## Funcionalidades

### 1. Salvar Calendário

**Endpoint:** `POST /autenticado/roteirizacao/salvar-calendario`

**Fluxo:**
1. Usuário clica no botão "Salvar Calendário" na Parte 4
2. Sistema solicita nome do calendário via `prompt()`
3. Frontend coleta todas as alocações de `clustersAlocados`
4. Gera arquivo JSON para download local
5. Envia dados para o backend via POST
6. Backend salva no banco `saved_calendars`
7. Retorna confirmação com ID do calendário salvo

**Payload de exemplo:**
```json
{
    "nome": "Calendário Novembro 2025",
    "descricao": null,
    "data_criacao": "2025-11-12T10:30:00.000Z",
    "configuracao": {
        "dias": 30,
        "incluir_sabado": false,
        "incluir_domingo": false,
        "max_clientes_dia": 50
    },
    "alocacoes": [...],
    "total_clusters": 15,
    "total_clientes": 623
}
```

**Resposta de sucesso:**
```json
{
    "success": true,
    "message": "Calendário salvo com sucesso",
    "id": 42,
    "calendario": {
        "id": 42,
        "nome": "Calendário Novembro 2025",
        "configuracao": {...},
        "alocacoes": [...],
        "total_clusters": 15,
        "total_clientes": 623,
        "created_at": "2025-11-12T10:30:15.123Z",
        "updated_at": "2025-11-12T10:30:15.123Z"
    }
}
```

### 2. Listar Calendários

**Endpoint:** `GET /autenticado/roteirizacao/calendarios`

Retorna todos os calendários salvos do usuário, ordenados por data de criação (mais recentes primeiro).

**Resposta:**
```json
{
    "success": true,
    "calendarios": [
        {
            "id": 42,
            "nome": "Calendário Novembro 2025",
            "descricao": null,
            "configuracao": {...},
            "alocacoes": [...],
            "total_clusters": 15,
            "total_clientes": 623,
            "created_at": "2025-11-12T10:30:15.123Z",
            "updated_at": "2025-11-12T10:30:15.123Z"
        }
    ]
}
```

### 3. Obter Calendário Específico

**Endpoint:** `GET /autenticado/roteirizacao/calendario/<id>`

Retorna um calendário específico pelo ID (validando ownership do usuário).

**Resposta:**
```json
{
    "success": true,
    "calendario": {
        "id": 42,
        "nome": "Calendário Novembro 2025",
        ...
    }
}
```

### 4. Obter Clientes de um Cluster (Dia Específico)

**Endpoint:** `GET /autenticado/roteirizacao/calendario/<calendario_id>/clientes/<dia>`

Retorna lista detalhada de clientes alocados em um dia específico do calendário.

**Parâmetros:**
- `calendario_id`: ID do calendário salvo
- `dia`: Número do dia (1-30)

**Exemplo:** `GET /calendario/42/clientes/1`

**Resposta:**
```json
{
    "success": true,
    "dia": 1,
    "cluster_id": 3,
    "polygon_name": "Zona Sul",
    "num_clientes": 45,
    "score_medio": 67.5,
    "clientes": [
        {
            "hash_cliente": "a1b2c3...",
            "nome": "Cliente ABC Ltda",
            "cidade": "São Paulo",
            "estado": "SP",
            "latitude": -23.5505,
            "longitude": -46.6333,
            "score": 72.3
        }
    ]
}
```

### 5. Exportar Todos os Clientes do Calendário

**Endpoint:** `GET /autenticado/roteirizacao/calendario/<calendario_id>/exportar-clientes`

Retorna estrutura completa com todos os dias e clientes do calendário.

**Uso:** Geração de relatórios, planilhas Excel, visualizações detalhadas

**Resposta:**
```json
{
    "success": true,
    "resultado": {
        "calendario_id": 42,
        "nome_calendario": "Calendário Novembro 2025",
        "created_at": "2025-11-12T10:30:15.123Z",
        "dias": [
            {
                "dia": 1,
                "cluster_id": 3,
                "polygon_name": "Zona Sul",
                "clientes": [...]
            }
        ]
    }
}
```

## Frontend

### Botão Salvar Calendário

**Localização:** Fim da seção Parte 4 (após layout de calendário + inventário)

**HTML:**
```html
<div class="salvar-calendario-container">
    <button class="btn-salvar-calendario" onclick="salvarCalendario()">
        <svg>...</svg>
        <span>Salvar Calendário</span>
    </button>
</div>
```

**CSS:** `roteirizacao.css` (linhas ~1400+)
- Botão com gradiente roxo (#667eea → #764ba2)
- Animação de hover com efeito de brilho
- Ícone SVG de disquete animado
- Estado de loading com spinner

### Função JavaScript: `salvarCalendario()`

**Validações:**
- Verifica se há clusters alocados
- Solicita nome do calendário ao usuário
- Gera nome padrão se usuário cancelar prompt

**Ações:**
1. Prepara objeto `calendarioData` com todas as informações
2. Exporta JSON para download local (fallback)
3. Envia POST para `/autenticado/roteirizacao/salvar-calendario`
4. Exibe alertas de sucesso ou erro

**Tratamento de Erros:**
- Se POST falhar, arquivo ainda é exportado localmente
- Usuário é notificado sobre o status de cada operação

## Casos de Uso

### Caso 1: Salvar Calendário Completo
```
Usuário:
1. Cria roteirização na Parte 3
2. Aloca clusters no calendário na Parte 4
3. Clica em "Salvar Calendário"
4. Insere nome "Rotas Janeiro 2026"
5. Recebe confirmação e arquivo JSON baixado
```

### Caso 2: Calendário sem Alocações
```
Usuário:
1. Clica em "Salvar Calendário" sem alocar clusters
2. Recebe alerta: "Não há clusters alocados no calendário"
3. Operação cancelada
```

### Caso 3: Erro de Conexão
```
Usuário:
1. Aloca clusters e clica em "Salvar"
2. POST falha por erro de rede
3. Arquivo JSON é baixado localmente (backup)
4. Alerta: "Arquivo exportado, mas não foi possível salvar no sistema"
```

## Melhorias Futuras

1. **Carregar Calendário Salvo:**
   - Endpoint para restaurar calendário no frontend
   - Botão "Carregar Calendário" na Parte 4
   - Modal de seleção com lista de calendários salvos

2. **Editar Calendário:**
   - Endpoint PUT para atualizar calendário existente
   - Detectar mudanças nas alocações
   - Histórico de versões

3. **Compartilhar Calendário:**
   - Exportar para formatos PDF/Excel
   - Compartilhar entre usuários (permissões)
   - Templates públicos de calendários

4. **Análise de Calendários:**
   - Comparar eficiência entre calendários salvos
   - Métricas: total de km, tempo médio, utilização de dias
   - Sugestões de otimização

5. **Integração com Agenda:**
   - Sincronizar com Google Calendar/Outlook
   - Lembretes de visitas por cluster
   - Notificações push

## Arquivos Modificados

- `base/models.py` - Modelo `SavedCalendar`
- `base/routes.py` - 3 endpoints de API
- `config.py` - Bind para `saved_calendars` database
- `base/templates/roteirizacao.html` - Botão e função JS
- `base/static/css/roteirizacao.css` - Estilos do botão

## Banco de Dados

**Arquivo:** `databases/synapselLog_saved_calendars.db`

**Tabela:** `saved_calendars_data`

**Índices:**
- `idx_user_created`: (user_id, created_at) - Queries de listagem rápidas

**Comandos SQLite:**
```sql
-- Ver todos os calendários
SELECT id, user_id, nome, total_clusters, total_clientes, created_at 
FROM saved_calendars_data 
ORDER BY created_at DESC;

-- Calendários de um usuário
SELECT * FROM saved_calendars_data WHERE user_id = 1;

-- Estatísticas
SELECT 
    user_id,
    COUNT(*) as total_calendarios,
    SUM(total_clusters) as total_clusters,
    SUM(total_clientes) as total_clientes
FROM saved_calendars_data
GROUP BY user_id;
```

## Dependências

- **Flask-Login** - Autenticação e `current_user`
- **SQLAlchemy** - ORM e múltiplos binds
- **JSON** - Serialização de configurações e alocações

## Logs

```python
logger.info(f"Calendário '{nome}' salvo pelo usuário {username}")
logger.error(f"Erro ao salvar calendário: {error}", exc_info=True)
```

---

**Última atualização:** 12/11/2025  
**Versão:** 1.0
