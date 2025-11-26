```mermaid
graph TD
    subgraph "Camada de Ingestão"
        Fontes["Fontes de Dados (Sistemas, Arquivos)"]
        ADF[Azure Data Factory]
    end

    subgraph "TBC-01: Data Lake (Staging)"
        ADLS[Azure Data Lake Storage Gen2]
    end

    subgraph "TBC-02: Data Warehouse"
        Synapse[Azure Synapse Analytics (SQE Pool)]
    end

    subgraph "TBC-03: Modelo Semântico"
        AAS[Azure Analysis Services]
    end

    subgraph "Camada de Consumo"
        subgraph "Consumo via API (com Cache)"
            APIM[Azure API Management]
            FuncAPI["Azure Function (Lógica da API)"]
            Redis[Azure Cache for Redis]
        end
        subgraph "Consumo via Relatórios Python"
            FuncPy["Azure Function (Gera Relatórios)"]
            Relatorios["Relatórios Finais (A, B, C, D)"]
        end
    end

    %% FLUXO DE DADOS (ETL/ELT)
    Fontes -->|1. Coleta| ADF
    ADF -->|2. Carrega Bruto| ADLS
    ADF -->|3. Pipeline ETL/ELT| Synapse
    Synapse -->|4. Leitura p/ Modelo| AAS

    %% FLUXO DE ORQUESTRAÇÃO
    ADF -.->|5. Gatilho de Refresh| AAS

    %% FLUXO DE CONSUMO - RELATÓRIOS
    AAS -->|6. Consulta (Python)| FuncPy
    FuncPy -->|7. Gera Arquivo| Relatorios

    %% FLUXO DE CONSUMO - API
    APIM -->|8. Requisição API| FuncAPI
    FuncAPI -->|9. Verifica Cache| Redis
    Redis -->|10. 'Cache Hit'| FuncAPI
    FuncAPI -->|11. 'Cache Miss'| AAS
    AAS -->|12. Retorna Dados| FuncAPI
    FuncAPI -->|13. Salva no Cache| Redis
    FuncAPI -->|14. Resposta API| APIM

    %% Classes para Estilo (opcional)
    classDef ingest fill:#cde4ff,stroke:#6699ff
    classDef staging fill:#d5f5e3,stroke:#58d68d
    classDef dw fill:#fcf3cf,stroke:#f1c40f
    classDef semantic fill:#fadbd8,stroke:#e74c3c
    classDef consume fill:#eaecee,stroke:#a6acaf

    class ADF,Fontes ingest
    class ADLS staging
    class Synapse dw
    class AAS semantic
    class APIM,FuncAPI,Redis,FuncPy,Relatorios consume
```