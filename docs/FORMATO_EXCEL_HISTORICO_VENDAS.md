# 📋 Formato do Excel para Histórico de Vendas

## Colunas Obrigatórias

Seu arquivo Excel **deve** conter as seguintes colunas:

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `id_pedido` | Texto/Número | Identificador único do pedido | "PED-001", "12345" |
| `id_cliente` | Texto | Identificador do cliente | "CLI-001", "João Silva" |
| `data_compra` | Data | Data da compra | 2025-01-15, 15/01/2025 |
| `valor_total_pagamento` | Número | Valor total pago | 150.50, 1200.00 |

## Colunas Opcionais

Você pode incluir essas colunas para dados adicionais:

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `nota_avaliacao` | Número | Avaliação do cliente (1-5) | 4, 5 |
| `status_pedido` | Texto | Status do pedido | "entregue", "cancelado" |
| `metodo_pagamento` | Texto | Forma de pagamento | "cartão", "pix", "boleto" |

## ⚠️ Importante

1. **Nome das colunas**: Devem ser exatamente como listado acima (case-sensitive)
2. **Formato do arquivo**: `.xlsx` ou `.xls`
3. **Linhas vazias**: Serão ignoradas
4. **Duplicatas**: Pedidos com mesmo `id_pedido` para o mesmo usuário serão ignorados

## 📊 Exemplo de Estrutura

```
| id_pedido | id_cliente    | data_compra | valor_total_pagamento | nota_avaliacao | status_pedido |
|-----------|---------------|-------------|----------------------|----------------|---------------|
| PED-001   | João Silva    | 2025-01-15  | 150.50               | 5.0            | entregue      |
| PED-002   | Maria Santos  | 2025-01-16  | 320.00               | 4.5            | entregue      |
| PED-003   | Pedro Costa   | 2025-01-17  | 89.90                | 4.0            | em_transito   |
```

## 🔄 Processo de Importação

1. Acesse `/autenticado/historicovendas`
2. Clique em "Escolher arquivo"
3. Selecione seu arquivo Excel
4. Clique em "Importar"
5. Aguarde o processamento
6. **Automático**: Após importação, os scores RFM serão calculados automaticamente

## 🧠 Cálculo Automático de Scores RFM

Após a importação bem-sucedida, o sistema automaticamente:

- Analisa recência (última compra)
- Calcula frequência (número de pedidos)
- Soma valor monetário (total gasto)
- Considera satisfação (média das avaliações)
- Gera score total (0-100) para cada cliente

## 📌 Hash do Cliente

O sistema usa o valor de `id_cliente` como identificador único (hash). Por exemplo:

- Se `id_cliente = "João Silva"`, então `hash_cliente = "João Silva"`
- Se `id_cliente = "CLI-001"`, então `hash_cliente = "CLI-001"`

**Não há transformação MD5 ou qualquer outra criptografia** - o valor é copiado diretamente.

## ❌ Erros Comuns

1. **"Colunas obrigatórias faltando"**: Verifique se os nomes das colunas estão corretos
2. **"Formato inválido"**: Use apenas arquivos `.xlsx` ou `.xls`
3. **"Nenhum arquivo enviado"**: Selecione um arquivo antes de clicar em Importar
4. **Muitos registros duplicados**: O mesmo `id_pedido` já existe no banco

## 🎯 Dicas

- Use nomes descritivos para `id_cliente` (ex: nome completo)
- Mantenha `id_pedido` único em todo o histórico
- Preencha `nota_avaliacao` quando disponível para melhorar análise RFM
- Datas podem estar em vários formatos (Excel converte automaticamente)
- Valores monetários devem usar `.` como separador decimal
