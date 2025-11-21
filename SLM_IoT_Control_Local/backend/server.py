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

@app.route("/ollama", methods=["POST"]) 
def ollama():
    body = rq.get_json()

    # Agent
    # classification = useAGENT.ask_ollama_for_classification(body["user_input"])
    classification = useAGENT.manual_classification(body["user_input"])
    print(f"Classification: {classification}")

    if classification == "Error":
        return jsonify({"message": "Error: Could not parse SLM response."})
    
    elif classification == "iot":
        message,(red, blue, green), servo_angle, (pomodoro_start, pomodoro_stop, pomodoro_minutes, pomodoro_seconds) = useIOT.query(body)
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
                "seconds": pomodoro_seconds
            }
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