from flask import Flask, request as rq, jsonify
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")

model = "gpt-oss:120b"

api_key = os.getenv("API_KEY")

def create_interactive_prompt(temp, hum, button_state, ledRed, ledBlue, ledGreen, user_input):
    return f"""
You are an IoT system assistant controlling an environmental monitoring 
system with LED indicators.

CURRENT SYSTEM STATUS:
- DHT11: Temperature {temp:.1f}°C, Humidity {hum:.1f}%
- Button: {"PRESSED" if button_state else "NOT PRESSED"}
- Red LED: {"ON" if ledRed else "OFF"}
- Blue LED: {"ON" if ledBlue else "OFF"}
- Green LED: {"ON" if ledGreen else "OFF"}

USER REQUEST: "{user_input}"

INSTRUCTIONS:
You must analyze the user's request and respond with a JSON object 
containing two fields:

1. "message": A helpful text response to the user
2. "leds": LED control object with three boolean fields: 
"red_led", "blue_led", "green_led"

EXAMPLES:

User: "what's the current temperature?"
Response: {{"message": "The current temperature is {temp:.1f}°C from DHT11.", "leds": {{"red_led": {str(ledRed).lower()}, "blue_led": {str(ledBlue).lower()}, "green_led": {str(ledGreen).lower()}}}}}

User: "turn on the blue led"
Response: {{"message": "Blue LED turned on.", "leds": {{"red_led": false, "blue_led": true, "green_led": false}}}}

User: "if temperature is above 20°C, turn on blue led"
Response: {{"message": "Temperature is {temp:.1f}°C, which is {'above' if temp > 20 else 'below or equal to'} 20°C. {'blue LED turned on.' if temp > 20 else 'No action taken.'}", "leds": {{"red_led": false, "blue_led": {str(temp > 20).lower()}, "green_led": {str(temp <= 20).lower()}}}}}

User: "if button is pressed, turn on red led"
Response: {{"message": "Button is {'pressed' if button_state else 'not pressed'}. {'Red LED turned on.' if button_state else 'No action taken.'}", "leds": {{"red_led": {str(button_state).lower()}, "blue_led": false, "green_led": {str(not button_state).lower()}}}}}

User: "turn on all leds"
Response: {{"message": "All LEDs turned on.", "leds": {{"red_led": true, "blue_led": true, "green_led": true}}}}

User: "turn off all leds"
Response: {{"message": "All LEDs turned off.", "leds": {{"red_led": false, "blue_led": false, "green_led": false}}}}

User: "will it rain?"
Response: {{"message": "Based on temperature of {temp:.1f}°C and humidity of {hum:.1f}%, [your analysis here]. LEDs unchanged.", "leds": {{"red_led": {str(ledRed).lower()}, "blue_led": {str(ledBlue).lower()}, "green_led": {str(ledGreen).lower()}}}}}

User: "if button is pressed, switch (Change, Reverse) the led states"
Response: {{"message": "Button is {'pressed' if button_state else 'not pressed'}. {'LED states switched.' if button_state else 'No action taken.'}", "leds": {{"red_led": {str(not ledRed and button_state).lower()}, "blue_led": {str(not ledBlue and button_state).lower()}, "green_led": {str(not ledGreen and button_state).lower()}}}}}

RULES:
- Always respond with valid JSON containing both "message" and "leds" fields
- If the user is just asking for information, keep the current LED states
- If the user gives a command, update the LED states accordingly
- If the command has a condition (if/when), evaluate it based on current sensor data
- Be conversational and helpful in your message
- Only ONE LED should be on at a time UNLESS the user explicitly asks for multiple LEDs

Respond with ONLY the JSON, no other text.
"""

def slm_inference(PROMPT, MODEL):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": False
    }
    # Make the API request to Ollama Cloud
    response = requests.post(
        url="https://ollama.com/api/chat",
        headers={
            "Authorization": f"Bearer {SECRET_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload)
    )
    print(response.json().get("message"))
    return response.json().get("message", {}).get("content", "No response provided.")

def parse_interactive_response(response_text):
    """Parse the interactive SLM JSON response."""
    try:      
        response_text = json.loads(response_text)
        message = response_text.get("message", "")
        # Extract LED states
        leds = response_text.get('leds', {})
        red_led = leds.get('red_led', False)
        blue_led = leds.get('blue_led', False)
        green_led = leds.get('green_led', False)
        return message, (red_led, blue_led, green_led)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response was: {response_text}")
        return "Error: Could not parse SLM response.", (False, False, False)
 
@app.route("/ollama", methods=["POST"]) 
def ollama():
    body = rq.get_json()
    # Create prompt with user input
    system_prompt = create_interactive_prompt(
        body["temperature"],
        body["humidity"],
        body["btn_pressed"],
        body["led_red"], 
        body["led_blue"],
        body["led_green"],
        body["user_input"]
    )
    # Get SLM response
    response = slm_inference(system_prompt, model)
    #Parse response
    message,(red, blue, green) = parse_interactive_response(response)
    return jsonify({
        "message": message,
        "red_led": red,
        "blue_led": blue,
        "green_led": green
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)