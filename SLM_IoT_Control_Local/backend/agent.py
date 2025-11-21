import requests

class AGENT:
    def __init__(
        self,
        model,
        ollama_host
    ):
        self.model = model
        self.ollama_host = ollama_host
        self.session = requests.Session()
        self.session.headers.update({"Connection": "keep-alive"})

    def ask_ollama_for_classification(self, user_input):
        classification_prompt = f"""
Classifique a intenção do usuário em UMA palavra das 3 categorias a seguir.
- iot: perguntas sobre sensores, atuadores, comandos, LEDs, temperatura, DHT11, GPIO, microcontrolador executando ações.
- documentation: perguntas sobre Franzininho, especificações, pinos, módulos, datasheet, tutoriais.
- general: qualquer outra coisa.
Regras:
- Responda SOMENTE com exatamente uma dessas palavras.
- Não adicione nenhuma frase, explicação ou texto adicional.
Pergunta: {user_input}
Resposta:
"""
        try:
            print(f"Sending classification request to Ollama")
            response = self.session.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": classification_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 5,
                        "top_k": 5,
                        "top_p": 0.5,
                        "stop": ["\n"], 
                        "seed": 42
                    }
                }
            )
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
                return "Error"

            response_text = response.json().get("response", "")
            return response_text
                    
        except Exception as e:
            print(f"Error connecting to Ollama: {str(e)}")
            return "Error"

    def ask_ollama(self, query):
        try:
            print(f"Sending query to Ollama")
            forced_query = (
            "Responda APENAS com 1 frase curta, com no máximo 12 palavras. "
            "Não use exemplos, listas ou explicações. "
            "Não escreva mais de UMA sentença. "
            f"Pergunta: {query}\nResposta:"
            )
            response = self.session.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": forced_query,
                    "stream": False
                }
            )
            if response.status_code == 200:
                print(f"Response from Ollama: {response.json().get('response', '')}")
                return response.json().get("response", "")
            else:
                return f"Error: Received status code {response.status_code} from Ollama."
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"

    def manual_classification(self, user_input: str) -> str:
        text = user_input.lower().strip()

        iot_keywords = [
            "ligue", "desligue", "acenda", "apague",
            "led", "servo", "angulo", "ângulo",
            "temperatura", "umidade", "humidade",
            "dht11", "sensor", "ldr", "pomodoro",
            "comece", "inicie", "pare", "status",
            "pwm", "gpio", "motor", "acionar"
        ]
        if any(kw in text for kw in iot_keywords):
            return "iot"

        # Regras para Documentação
        documentation_keywords = [
        "franzininho", "datasheet", "pino", "pinos",
        "wifi lab", "lab01", "tutorial", "especificação",
        "documentação", "qual pino", "como funciona"
        ]   
        if any(kw in text for kw in documentation_keywords):
            return "documentation"

        # Caso não bata com nada
        return "general"