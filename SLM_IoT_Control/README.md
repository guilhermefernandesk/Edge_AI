# SLM IoT Control

Este projeto implementa um sistema básico de controle IoT utilizando um **Small Language Model (SLM)** via API. A solução é composta por um backend em Python e um firmware embarcado rodando em uma Franzininho WiFi.

---

## 📌 Demonstrações

Para demonstrações visuais, consulte o projeto relacionado [SLM IoT Control Local](../SLM_IoT_Control_Local/) que inclui vídeos e slides.

---

## Arquitetura

A solução é dividida em dois módulos principais:

1. **Backend (`/backend`)**:
   - **Servidor Web (`server.py`)**: Uma aplicação Flask que expõe endpoints para a comunicação com o modelo de IA via API e a placa embarcada via HTTP.

2. **Embarcado (`/embarcado`)**:
   - **Firmware (`embarcado.ino`)**: Código para o microcontrolador (compatível com Arduino/Franzininho) que gerencia os componentes de hardware (sensores DHT11, botões, LEDs) e se comunica com o backend via HTTP.

---

## Pré-requisitos

- Hardware:
  - Placa Franzininho WiFi Lab01
- Ambiente Python com Flask e dependências (ver server.py)
- Acesso à API do modelo SLM (ex: Ollama API)

---

## Configuração

1. Navegue até a pasta `backend`.
2. Crie um arquivo chamado `.env` com as seguintes variáveis (ajuste conforme necessário):

   ```env
   SECRET_KEY=your_secret_key
   API_KEY=your_api_key
   ```

3. Navegue até a pasta `embarcado`.
4. Crie um arquivo chamado `credentials.h` com o seguinte conteúdo:
   ```c
   const char *SSID = "";
   const char *PASSWORD = "";
   const char *API_URL = "http://<IP_DO_SERVIDOR>:<PORTA>";
   ```

---

## Como Executar

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd Edge_AI/SLM_IoT_Control
   ```

2. **Configure o ambiente:**
   - Crie o arquivo `backend/.env` conforme descrito na seção **Configuração**.

3. **Execute o servidor backend:**
   ```bash
   python backend/server.py
   ```

4. **Grave o firmware no dispositivo embarcado:**
   - Abra o arquivo `embarcado/embarcado.ino` na IDE do Arduino.
   - Configure as credenciais de sua rede WiFi no arquivo `credentials.h`.
   - Atualize a variável `API_URL` com o endereço do servidor backend.
   - Compile e envie o código para a sua placa.

---

## Como Usar

Envie comandos de texto para o endpoint do servidor Flask (ex: via POST request) para controlar os LEDs baseado no estado dos sensores e botões.

**Exemplos de comandos:**
- "Qual é a temperatura atual?"
- "Ligue o LED azul"
- "Se o botão estiver pressionado, ligue o LED vermelho"

---

## Estrutura do Projeto

```
SLM_IoT_Control/
├── README.md                # Este arquivo
├── backend/
│   ├── .env                 # (Exemplo) Arquivo de configuração
│   └── server.py            # Servidor Flask
└── embarcado/
    └── embarcado.ino        # Firmware do dispositivo
```

## 📜 Licença

Este projeto está licenciado sob a [GPL-3.0 license](../LICENSE). Fique à vontade para utilizar e modificar o código com a devida atribuição.

---

## 💻 Autor

Desenvolvido por [Guilherme Fernandes](https://github.com/guilhermefernandesk)

<a href="https://www.linkedin.com/in/iguilherme" target="_blank"><img src="https://img.shields.io/badge/-LinkedIn-%230077B5?style=for-the-badge&logo=linkedin&logoColor=white" target="_blank"></a>