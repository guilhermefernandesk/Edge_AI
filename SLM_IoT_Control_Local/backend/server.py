from flask import Flask, request as rq, jsonify
import os
from dotenv import load_dotenv
from rag import RAG
from agent import AGENT
from iot import IOT

load_dotenv()
app = Flask(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST")
MODEL = "gemma3"

useIOT = IOT(
    model=MODEL,
    ollama_host=OLLAMA_HOST
)

useRAG = RAG(
    persist_dir="chroma_db",
    model=MODEL,
    urls = [
        "https://raw.githubusercontent.com/Franzininho/docs-franzininho-site/main/docs/FranzininhoWiFiLAB01/franzininho-wifi-lab01.md",
        "https://docs.franzininho.com.br/docs/franzininho-wifi/franzininho-wifi/"
    ],
    pdfs= [],
    text=[]
)

useAGENT = AGENT(
    model=MODEL,
    ollama_host=OLLAMA_HOST
)

@app.route("/classification", methods=["POST"])
def classification():
    body = rq.get_json()
    print(body["user_input"])
    # Agent
    classification = useAGENT.ask_ollama_for_classification(body["user_input"])
    print(f"Classification: {classification}")
    return jsonify({
        "classification": classification
    })

@app.route("/ollama", methods=["POST"]) 
def ollama():
    body = rq.get_json()

    classification = body["classification"]
    
    if classification == "iot":
        message,(red, blue, green), servo_angle, (pomodoro_start, pomodoro_stop, pomodoro_minutes), response = useIOT.query(body)
        return jsonify({
            "message": message,
            "red_led": red,
            "blue_led": blue,
            "green_led": green,
            "servo_angle": servo_angle,
            "pomodoro": {
                "start": pomodoro_start,
                "stop": pomodoro_stop,
                "minutes": pomodoro_minutes,
            },
            "response": response
        })
    
    elif classification == "documentation":
        message = useRAG.query(body["user_input"])
        return jsonify({
            "message": message
        })
    
    else:
        message = useAGENT.ask_ollama(body["user_input"])
        return jsonify({
            "message": message
        })
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)