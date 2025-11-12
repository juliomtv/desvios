# DTS - Desvios no Trabalho (v3 - Completo)

Este é um aplicativo web construído com Flask e Pandas para registrar desvios no trabalho, visualizar estatísticas em um dashboard e exportar os dados para análise em formato XLSX.

## Estrutura do Projeto

```
dts_app/
├── app.py              # Aplicação principal Flask com rotas, autenticação e lógica de análise
├── data/
│   └── desvios.csv     # Arquivo onde os desvios são armazenados
└── templates/
    ├── index.html      # Formulário de registro de desvios (Design TechnipFMC)
    ├── login.html      # Página de login para supervisores
    └── dashboard.html  # Dashboard de visualização de desvios
```

## Pré-requisitos

Você precisa ter o Python 3 instalado.

## Instalação e Execução

1.  **Navegue até o diretório do projeto:**
    ```bash
    cd dts_app
    ```

2.  **Instale as dependências (Novas dependências adicionadas!):**
    ```bash
    pip3 install Flask pandas openpyxl Flask-HTTPAuth
    ```

3.  **Execute o aplicativo:**
    ```bash
    python3 app.py
    ```

O aplicativo estará acessível em `http://127.0.0.1:5000`.

## Funcionalidades

-   **Registro de Desvios:** Formulário na página inicial (`/`) com campo de texto livre para o tipo de desvio.
-   **Dashboard (Acesso Restrito):**
    -   Acesse em `/login`.
    -   **Login:** `gestao`
    -   **Senha:** `technipfmc`
    -   Mostra os 5 desvios mais e menos frequentes.
-   **Download do Relatório (Acesso Restrito):**
    -   Disponível no Dashboard.
    -   Exporta os dados para o formato **XLSX (Excel)**, garantindo que cada dado esteja em sua célula correta.
    -   A rota de download é protegida por login.

## Observação sobre a Senha do Arquivo

A rota de download é protegida por login e senha. O arquivo XLSX em si não possui senha, pois a biblioteca  não suporta nativamente a criptografia de arquivos. A segurança é garantida pelo acesso restrito ao Dashboard.
