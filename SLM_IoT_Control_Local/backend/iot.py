import requests
import json
import re

class IOT:
    def __init__(
        self,
        model,
        ollama_host
    ):
        self.model = model,
        self.ollama_host = ollama_host

    def create_interactive_prompt(self, temp, hum, button_state, ledRed, ledBlue, ledGreen, ldrValue, servoAngle, user_input):
        return f"""
    You are an IoT system assistant controlling a study productivity device using
    SLM. You must ALWAYS respond with valid JSON.

    CURRENT SYSTEM STATUS:
    - DHT11: Temperature {temp:.1f}°C, Humidity {hum:.1f}%
    - Button: {"PRESSED" if button_state else "NOT PRESSED"}
    - Red LED: {"ON" if ledRed else "OFF"}
    - Blue LED: {"ON" if ledBlue else "OFF"}
    - Green LED: {"ON" if ledGreen else "OFF"}
    - LDR Value: {ldrValue}
    - Servo Angle: {servoAngle}°

    SYSTEM CAPABILITIES:
    - Control red, blue, and green LEDs (only one ON unless user requests multiple)
    - Set servo angle 0–180 degrees
    - Start/stop Pomodoro timer
    - Provide study comfort analysis using sensors
    - Retrieve technical documentation answers via RAG

    USER REQUEST: "{user_input}" 

    YOUR RESPONSE MUST FOLLOW THIS EXACT JSON STRUCTURE:
    {{
    "message": "...",
    "leds": {{
        "red_led": true/false,
        "green_led": true/false,
        "blue_led": true/false
    }},
    "servo_angle": 0–180 or null,
    "pomodoro": {{
        "start": true/false,
        "stop": true/false,
        "minutes": int,
        "seconds": int
    }}
    }}

    EXAMPLES:

    User: "Qual a temperatura atual?"
    Response:
    {{
    "message": "A temperatura atual é {temp:.1f}°C.",
    "leds": {{"red_led": {str(ledRed).lower()}, "green_led": {str(ledGreen).lower()}, "blue_led": {str(ledBlue).lower()}}},
    "servo_angle": {servoAngle},
    "pomodoro": {{"start": false, "stop": false, "minutes": 0, "seconds": 0}}
    }}

    User: "Coloque o servo em 50 graus"
    Response:
    {{
    "message": "Servo ajustado para 50 graus.",
    "leds": {{"red_led": {str(ledRed).lower()}, "green_led": {str(ledGreen).lower()}, "blue_led": {str(ledBlue).lower()}}},
    "servo_angle": 50,
    "pomodoro": {{"start": false, "stop": false, "minutes": 0, "seconds": 0}}
    }}

    User: "Ligue o led azul"
    Response:
    {{
    "message": "LED azul ligado.",
    "leds": {{"red_led": false, "blue_led": true, "green_led": false}},
    "servo_angle": 50,
    "pomodoro": {{"start": false, "stop": false, "minutes": 0, "seconds": 0}}
    }}

    User: "Se a temperatura estiver acima de 20°C, ligue o led azul"
    Response: {{"message": "Temperature is {temp:.1f}°C, which is {'above' if temp > 20 else 'below or equal to'} 20°C. {'blue LED turned on.' if temp > 20 else 'No action taken.'}", "leds": {{"red_led": false, "blue_led": {str(temp > 20).lower()}, "green_led": {str(temp <= 20).lower()}}}, "servo_angle": {servoAngle}, "pomodoro": {{"start": false, "stop": false, "minutes": 0, "seconds": 0}}}}

    User: "Se o botão estiver pressionado, ligue o led vermelho"
    Response: {{"message": "Button is {'pressed' if button_state else 'not pressed'}. {'Red LED turned on.' if button_state else 'No action taken.'}", "leds": {{"red_led": {str(button_state).lower()}, "blue_led": false, "green_led": {str(not button_state).lower()}}}, "servo_angle": {servoAngle}, "pomodoro": {{"start": false, "stop": false, "minutes": 0, "seconds": 0}}}}

    User: "turn off all leds"
    Response: {{"message": "All LEDs turned off.", "leds": {{"red_led": false, "blue_led": false, "green_led": false}}, "servo_angle": {servoAngle}, "pomodoro": {{"start": false, "stop": false, "minutes": 0, "seconds": 0}}}}

    User: "will it rain?"
    Response: {{"message": "Based on temperature of {temp:.1f}°C and humidity of {hum:.1f}%, [your analysis here]. LEDs unchanged.", "leds": {{"red_led": {str(ledRed).lower()}, "blue_led": {str(ledBlue).lower()}, "green_led": {str(ledGreen).lower()}}}, "servo_angle": {servoAngle}, "pomodoro": {{"start": false, "stop": false, "minutes": 0, "seconds": 0}}}}

    RULES:
    - ALWAYS output valid JSON — never explanations outside JSON.
    - If the user asks for info, keep hardware states unchanged.
    - If they request actions, update the states.
    - If the command has a condition (if/when), evaluate it based on current sensor data
    - Be conversational and helpful in your message
    - Only ONE LED should be on at a time UNLESS the user explicitly asks for multiple LEDs

    Respond with ONLY the JSON, no other text.
    """

    def slm_inference(self, PROMPT):
        response = requests.post(
            url=f"{self.ollama_host}/api/generate",
            json={
                "model": self.model,
                "prompt": PROMPT,
                "stream": False
            }
        )
        print(response.json())
        return response.json().get("message", {}).get("content", "No response provided.")

    def parse_interactive_response(self, response_text):
        """Parse the interactive SLM JSON response."""
        try: 
            # Extrai apenas o JSON dentro do texto
            json_str = re.search(r"\{.*\}", response_text, re.DOTALL).group(0)
            response_text = json.loads(json_str)     
            # response_text = json.loads(response_text)
            message = response_text.get("message", "")
            # Extract LED states
            leds = response_text.get('leds', {})
            red_led = leds.get('red_led', False)
            blue_led = leds.get('blue_led', False)
            green_led = leds.get('green_led', False)
            # Extract Pomoodoro info
            pomodoro = response_text.get('pomodoro', {})
            pomodoro_start = pomodoro.get('start', False)
            pomodoro_stop = pomodoro.get('stop', False)
            pomodoro_minutes = pomodoro.get('minutes', 0)
            pomodoro_seconds = pomodoro.get('seconds', 0)
            # Extract Servo angle
            servo_angle = response_text.get('servo_angle', 0)
            return message, (red_led, blue_led, green_led), servo_angle, (pomodoro_start, pomodoro_stop, pomodoro_minutes, pomodoro_seconds)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response was: {response_text}")
            return "Error", (False, False, False), 0, (False, False, 0, 0)
    
    def query(self, body):
        # Create prompt with user input
        system_prompt = self.create_interactive_prompt(
            body["temperature"],
            body["humidity"],
            body["btn_pressed"],
            body["led_red"], 
            body["led_blue"],
            body["led_green"],
            body["ldr_value"],
            body["servo_angle"],
            body["user_input"]
        )
        # Get SLM response
        response = self.slm_inference(system_prompt)
        #Parse response
        message,(red, blue, green), servo_angle, (pomodoro_start, pomodoro_stop, pomodoro_minutes, pomodoro_seconds) = self.parse_interactive_response(response)
        return message,(red, blue, green), servo_angle, (pomodoro_start, pomodoro_stop, pomodoro_minutes, pomodoro_seconds)