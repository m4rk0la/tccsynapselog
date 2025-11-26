# 🔄 Mudança: nome_cliente → id_cliente

## ✅ Alterações Realizadas

### 1. `base/routes.py` - Rota `/autenticado/historicovendas`

**Antes:**
```python
colunas_obrigatorias = ['id_pedido', 'nome_cliente', 'data_compra', 'valor_total_pagamento']
hash_cliente = str(row['nome_cliente'])
```

**Depois:**
```python
colunas_obrigatorias = ['id_pedido', 'id_cliente', 'data_compra', 'valor_total_pagamento']
hash_cliente = str(row['id_cliente'])
```

### 2. `scripts/debug/diagnostico_banco_vazio.py`

**Antes:**
```python
print("      - nome_cliente (obrigatório)")
```

**Depois:**
```python
print("      - id_cliente (obrigatório)")
```

### 3. Documentação Criada

- ✅ Criado `docs/FORMATO_EXCEL_HISTORICO_VENDAS.md` com formato completo

## 📋 Formato Atual do Excel

### Colunas Obrigatórias:
1. `id_pedido` - Identificador do pedido
2. `id_cliente` - Identificador do cliente (**MUDOU DE nome_cliente**)
3. `data_compra` - Data da compra
4. `valor_total_pagamento` - Valor total

### Colunas Opcionais:
- `nota_avaliacao` - Avaliação (1-5)
- `status_pedido` - Status
- `metodo_pagamento` - Forma de pagamento

## 🔍 Como o Sistema Funciona Agora

1. **Upload**: Usuário envia Excel com coluna `id_cliente`
2. **Validação**: Sistema verifica se `id_cliente` existe
3. **Processamento**: Para cada linha:
   ```python
   hash_cliente = str(row['id_cliente'])  # Cópia direta, sem hash MD5
   ```
4. **Armazenamento**: Venda salva no `OrderHistory` com `hash_cliente = id_cliente`
5. **RFM Automático**: Scores calculados após importação

## 📊 Exemplo de Dados

```csv
id_pedido,id_cliente,data_compra,valor_total_pagamento,nota_avaliacao
PED-001,João Silva,2025-01-15,150.50,5.0
PED-002,Maria Santos,2025-01-16,320.00,4.5
PED-003,João Silva,2025-01-20,89.90,4.0
```

## 🎯 Benefícios da Mudança

1. ✅ **Alinhado com padrão**: `id_cliente` é mais semântico que `nome_cliente`
2. ✅ **Flexível**: Pode ser nome, código, ou qualquer identificador
3. ✅ **Compatível**: Funciona com datasets padrão (ex: Olist)
4. ✅ **Sem confusão**: Nome correto reflete que é um identificador

## ⚠️ Ação Necessária

Se você já tem arquivos Excel com `nome_cliente`:

**Opção 1 - Renomear coluna:**
```
Abra o Excel → Renomeie "nome_cliente" para "id_cliente"
```

**Opção 2 - Use script Python:**
```python
import pandas as pd
df = pd.read_excel('seu_arquivo.xlsx')
df.rename(columns={'nome_cliente': 'id_cliente'}, inplace=True)
df.to_excel('seu_arquivo_atualizado.xlsx', index=False)
```

## 🚀 Teste Agora

1. Reinicie o servidor Flask (se ainda não reiniciou)
2. Prepare Excel com coluna `id_cliente`
3. Faça upload via `/autenticado/historicovendas`
4. Verifique dados com script: `python scripts/debug/verificar_historico_vendas.py`
