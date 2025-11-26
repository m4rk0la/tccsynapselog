# 📋 Fluxo do ETL - Histórico de Vendas

## 🎯 Objetivo
Importar histórico completo de vendas preservando TODOS os 33 campos do Excel na tabela `OrderHistory`, sem inserção automática em tabelas de clientes.

---

## 🔄 Fluxo de Execução

### 1️⃣ Carregar Dados (Células 1-4)
- ✅ Carregar Excel com histórico de vendas
- ✅ Gerar hash_cliente para cada id_unico_cliente
- ✅ Gerar product_code para cada produto
- ✅ Converter datas para datetime

### 2️⃣ Inserir em OrderHistory (Célula 5)
- ✅ Inserir **TODOS** os 33 campos do Excel + metadados
- ✅ Inserção em lotes de 100 registros
- ✅ Tratamento de erros individual por registro
- ✅ Estatísticas de velocidade e progresso

### 3️⃣ Verificar Clientes (Célula 6)
- ✅ Extrair clientes únicos do histórico
- ✅ Comparar com tabela ClientName existente
- ✅ **NÃO insere automaticamente**
- ✅ Cria lista `clientes_novos_df` com clientes não cadastrados

### 4️⃣ Popular Products (Células 7-8)
- ✅ Extrair produtos únicos
- ✅ Calcular preço médio
- ✅ Inserir em Products (sem duplicatas)

### 5️⃣ Estatísticas (Célula 9)
- ✅ Distribuição por status de pedido
- ✅ Distribuição por ano
- ✅ Análise financeira (valor total, ticket médio)
- ✅ Análise de entregas (tempo médio, atraso)
- ✅ Análise de avaliações (nota média)

### 6️⃣ Resumo Final (Célula 10)
- ✅ Contagem de registros em cada tabela
- ✅ **Alerta sobre clientes novos detectados**
- ✅ Próximos passos

---

## 🔴 Decisão sobre Clientes Novos (Células 11-14)

### Célula 11: Markdown - Alerta
Cabeçalho de aviso sobre clientes novos

### Célula 12: Exibir Clientes Novos
- 📊 Mostra lista de clientes não cadastrados
- 💾 Exporta para Excel: `clientes_novos_detectados.xlsx`
- 📋 DataFrame global: `clientes_novos_df`

### Célula 13: Função de Inserção (Simulação)
```python
inserir_clientes_novos(confirmar=False)  # SIMULAÇÃO
```
- ⚠️ Modo simulação por padrão
- 📊 Mostra quantos clientes seriam inseridos
- 🛡️ Não faz alterações no banco

### Célula 14: Confirmação Manual
```python
# inserir_clientes_novos(confirmar=True)  # CONFIRMAR
```
- 🔴 Comentada por padrão
- ✅ Usuário deve descomentar manualmente
- 🔒 Proteção contra inserção acidental

---

## 📊 Estrutura de Dados

### OrderHistory (Todos os 33 campos)
```python
- id_pedido
- id_item_pedido
- id_cliente
- id_unico_cliente
- hash_cliente  # Gerado pelo ETL
- id_produto
- product_code  # Gerado pelo ETL
- data_compra
- data_aprovacao
- data_envio_transportadora
- data_entrega_cliente
- data_estimada_entrega
- data_limite_envio
- status_pedido
- tempo_entrega_dias
- atraso_entrega_dias
- ano_compra
- mes_compra
- ano_mes_compra
- dia_semana_compra
- preco
- valor_frete
- valor_total_item
- valor_total_pagamento
- num_pagamentos
- tipos_pagamento
- max_parcelas
- cidade_cliente
- estado_cliente
- cep_cliente
- nota_avaliacao
- titulo_comentario
- mensagem_comentario
- data_criacao_avaliacao
- data_resposta_avaliacao
- user_id  # ID do usuário que importou
- created_at
- updated_at
```

### clientes_novos_df (Clientes para revisão)
```python
- hash_cliente
- id_unico_cliente
- cidade
- estado
- cep
```

---

## 🎛️ Controles do Usuário

### ✅ Inserção Automática
- **OrderHistory**: SIM - todos os registros
- **Products**: SIM - produtos únicos

### ⚠️ Inserção Manual (Requer Aprovação)
- **ClientName**: NÃO - exporta lista para revisão
- **LatLong**: NÃO - usar ETL específico de geolocalização

---

## 💡 Vantagens desta Abordagem

1. **Segurança**: Evita inserção acidental de clientes duplicados
2. **Revisão**: Usuário pode validar dados antes de cadastrar
3. **Rastreabilidade**: Lista exportada em Excel para auditoria
4. **Flexibilidade**: Pode editar `clientes_novos_df` antes de inserir
5. **Separação de Responsabilidades**: ETL de histórico ≠ ETL de clientes

---

## 📝 Exemplo de Uso

```python
# 1. Execute todas as células até o resumo (células 1-10)
# Resultado: OrderHistory populado, lista de clientes novos gerada

# 2. Revise o arquivo gerado
clientes_novos_detectados.xlsx

# 3. (Opcional) Filtre clientes específicos
clientes_novos_df = clientes_novos_df[clientes_novos_df['estado'] == 'DF']

# 4. Simule a inserção
inserir_clientes_novos(confirmar=False)

# 5. Confirme a inserção
inserir_clientes_novos(confirmar=True)
```

---

## 🔗 Integração com Outros ETLs

### ETL de Geolocalização (Separado)
```python
# Use este ETL para:
# - Popular LatLong para clientes novos
# - Usar serviço de geolocalização em batch
# - Cache de coordenadas por CEP
# - Tratamento de erros de API
```

### ETL de Roteirização (Futuro)
```python
# Pode usar OrderHistory para:
# - Calcular frequência de pedidos por cliente
# - Identificar rotas otimizadas
# - Prever demanda futura
```

---

## ⚙️ Configurações

### Variáveis Globais
```python
USER_ID = 1  # ID do usuário que está importando
batch_size = 100  # Tamanho do lote para inserção
```

### Arquivos Gerados
- `clientes_novos_detectados.xlsx` - Lista de clientes para revisão
- `historico_vendas_DF.xlsx` - Arquivo de entrada (deve existir)

---

## 🐛 Troubleshooting

### "Erro ao inserir no OrderHistory"
- Verifique tipos de dados (int, float, datetime)
- Confirme que todas as colunas existem no Excel
- Revise valores nulos/NaN

### "Clientes novos não aparecem"
- Verifique se `clientes_novos_df` foi criado
- Execute célula 12 novamente
- Confirme que hash_cliente está correto

### "Inserção muito lenta"
- Aumente `batch_size` (padrão: 100)
- Desabilite índices temporariamente
- Use inserção bulk do SQLAlchemy

---

## 📞 Suporte

Para dúvidas sobre este ETL:
1. Revise este documento
2. Consulte os comentários nas células do notebook
3. Verifique logs de erro no console
