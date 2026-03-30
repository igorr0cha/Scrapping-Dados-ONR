# Scrapping Dados ONR (Cartórios CNJ)

Este projeto é um integrador automatizado desenvolvido em Python para extrair dados detalhados de serventias (cartórios) extrajudiciais em todo o território brasileiro, utilizando a API oficial do **Justiça Aberta (CNJ)**.

O sistema realiza uma varredura completa por UF e Cidade, coleta informações enriquecidas de cada CNS (Cadastro Nacional de Serventia) e armazena os dados de forma estruturada em um banco de dados **SQL Server**.

## 🚀 Funcionalidades

* **Extração Nacional:** Cobertura de todas as 27 Unidades Federativas (UFs).
* **Enriquecimento de Dados:** Além dos dados básicos, o sistema busca automaticamente:
    * Localização detalhada (Endereço, Número, Bairro, CEP).
    * Contatos (Telefone, E-mail, Website).
    * Responsáveis (Titulares e Substitutos).
    * Horários de funcionamento formatados.
* **Sistema de Checkpoint Inteligente:** * **Pulo de Cidade:** Verifica se a quantidade de cartórios no banco coincide com a da API para pular cidades já processadas em O(1).
    * **Pulo de CNS:** Filtra individualmente registros já existentes para evitar chamadas desnecessárias à API.
* **Processamento Paralelo:** Uso de `ThreadPoolExecutor` para otimizar as requisições de enriquecimento de dados.
* **Sincronização Robusta:** Utiliza a lógica de *Upsert* (merge) via SQLAlchemy para garantir que os dados sejam atualizados sem duplicidade.

## 🛠️ Tecnologias e Requisitos

* **Linguagem:** Python 3.10+
* **Banco de Dados:** SQL Server.
* **Driver Necessário:** [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).
* **Bibliotecas Principais:**
    * `SQLAlchemy`: ORM para persistência de dados.
    * `Requests`: Consumo da API REST.
    * `PyODBC`: Conectividade com SQL Server.
    * `python-dotenv`: Gerenciamento de variáveis de ambiente.

## ⚙️ Configuração

1.  **Instalação de Dependências:**
    ```bash
    pip install requests sqlalchemy pyodbc python-dotenv
    ```

2.  **Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz do projeto seguindo o modelo:
    ```env
    DB_SERVER=seu_servidor
    DB_NAME=DBSGI
    DB_USER=seu_usuario
    DB_PASS=sua_senha
    ```

3.  **Criação da Tabela:**
    Execute o script SQL contido no arquivo `schema.sql` no seu ambiente SQL Server para criar a tabela `CARV_CNJ`.

## 📂 Estrutura de Dados (CARV_CNJ)

Os dados são consolidados com a seguinte estrutura principal:

| Campo | Descrição |
| :--- | :--- |
| `CARVCns` | Chave Primária (Identificador único do cartório) |
| `CARVNome` | Denominação Fantasia |
| `CARVEnd` | Endereço completo formatado |
| `CARVStatus` | Situação atual (Ex: Ativo) |
| `CARVAtribuicoes` | Lista de especialidades (Naturezas) |
| `CARVResponsavel` | Nome do Titular/Responsável |
| `CARVHorarioFuncionamento` | Grade de horários formatada |
| `CARVDataAtualizacao` | Timestamp da última sincronização |



## 🖥️ Como Executar

Para iniciar o processo de extração e sincronização:

```bash
python main.py
