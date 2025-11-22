# SLM IoT Controle Local

Este projeto implementa um sistema de controle IoT utilizando um **Small
Language Model (SLM)** operando **localmente**. A solução é composta por
um backend em Python e um firmware embarcado rodando em uma Franzininho WiFi.

---

## 📌 Demonstrações

### 🎥 Vídeo de apresentação (YouTube)

**IA + ESP32: Controle Inteligente com SLM e RAG**\
https://www.youtube.com/watch?v=EmVz2de6mFM

### 🖼️ Slides da apresentação (Canva)

https://www.canva.com/design/DAG44doStrU/cigTMy_lTB2ts6HHZrW2Tg/view

---

## Arquitetura

A solução é dividida em dois módulos principais:

1.  **Backend (`/backend`)**:

    - **Servidor Web (`server.py`)**: Uma aplicação Flask que expõe endpoints para a comunicação entre Ollama e a Placa.
    - **Agente de IA (`agent.py`)**: O cérebro do sistema. Utiliza um modelo de linguagem (via Ollama) para interpretar as solicitações do usuário.
    - **Lógica de RAG (`rag.py`)**: Implementa o padrão Retrieval-Augmented Generation para fornecer contexto relevante ao agente.
    - **Controle do IoT (`iot.py`)**: Contém a lógica para se comunicar com o dispositivo embarcado via requisições **HTTP**.
    - **Dockerfile**: Define o ambiente para o serviço de backend, garantindo que todas as dependências sejam instaladas.

2.  **Embarcado (`/embarcado`)**:
    - **Firmware (`embarcado.ino`)**: Código para o microcontrolador (compatível com Arduino/Franzininho) que gerencia os componentes de hardware e se comunica com o backend via HTTP.
    - **Drivers de Hardware (`oled.h`, `franzininho.h`)**: Bibliotecas para controlar o display OLED e interagir com a placa Franzininho.
    - **Módulo Pomodoro (`pomodoro.h`)**: Lógica de controle do temporizador Pomodoro.

---

## Pré-requisitos

- [Docker](https://www.docker.com/get-started/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Hardware:
  - Placa Franzininho WiFi Lab01

---

## Configuração

Antes de iniciar os serviços, é necessário criar um arquivo de configuração para o backend.

1.  Navegue até a pasta `backend`.
2.  Crie um arquivo chamado `.env` com o seguinte conteúdo:

    ```env
    OLLAMA_HOST=http://ollama:11434
    ```

3.  Navegue até a pasta `embarcado`.
4.  Crie um arquivo chamado `.credentials` com o seguinte conteúdo:
    ```env
    const char *SSID = "";
    const char *PASSWORD = "";
    const char *API_URL = "http://<IP_DO_SERVIDOR>:<PORTA>";
    ```

---

## Como Executar

1.  **Clone o repositório:**
    ```bash
    git clone <url-do-repositorio>
    cd Edge_AI/SLM_IoT_Control_Local
    ```
2.  **Configure o ambiente:**

    - Crie o arquivo `backend/.env` conforme descrito na seção **Configuração**.

3.  **Suba os serviços com Docker Compose:**

    ```bash
    docker-compose up -d
    ```

4.  **Grave o firmware no dispositivo embarcado:**
    - Abra o arquivo `embarcado/embarcado.ino` na IDE do Arduino.
    - Configure as credenciais de sua rede WiFi.
    - Atualize a variável que aponta para o servidor backend com o mesmo `SERVER_IP` que você definiu no arquivo `.env`.
    - Compile e envie o código para a sua placa.
------------------------------------------------------------------------
## Como Usar

Exemplos de comandos no monitor serial:

**Exemplos de comandos:**

-   **"Inicie um Pomodoro de 25 minutos."**\
-   **"Ligue o LED azul"**\
-   **"Qual microcontrolador da Franzininho?."**
------------------------------------------------------------------------
## Estrutura do Projeto

```
SLM_IoT_Control_Local/
├── docker-compose.yaml      # Orquestração dos serviços
├── readme.md                # Este arquivo
├── backend/
│   ├── .env                 # (Exemplo) Arquivo de configuração
│   ├── agent.py             # Agente de IA
│   ├── Dockerfile           # Ambiente do backend
│   ├── iot.py               # Lógica de controle IoT (HTTP)
│   ├── rag.py               # Lógica de RAG
│   ├── requirements.txt     # Dependências Python
│   └── server.py            # Servidor Flask
└── embarcado/
    ├── embarcado.ino        # Firmware do dispositivo
    ├── franzininho.h        # Definições da placa
    ├── oled.h               # Driver do display OLED
    └── pomodoro.h           # Lógica do Pomodoro
```

## 📜 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE). Fique à vontade para utilizar e modificar o código com a devida atribuição.

---

## 💻 Autor

Desenvolvido por [Guilherme Fernandes](https://github.com/guilhermefernandesk)

<a href="https://www.linkedin.com/in/iguilherme" target="_blank"><img src="https://img.shields.io/badge/-LinkedIn-%230077B5?style=for-the-badge&logo=linkedin&logoColor=white" target="_blank"></a>
