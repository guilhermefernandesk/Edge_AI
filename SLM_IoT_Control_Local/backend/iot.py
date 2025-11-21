import requests
import json
import time

class IOT:
    def __init__(
        self,
        model,
        ollama_host
    ):
        self.model = model,
        self.ollama_host = ollama_host
        self.session = requests.Session()
        self.session.headers.update({"Connection": "keep-alive"})

    def create_interactive_prompt(self, temp, hum, button_state, ledRed, ledBlue, ledGreen, ldrValue, servoAngle, user_input):
        return f"""
Você é um controlador IoT SLM. Sempre responda com um JSON válido somente.
SYSTEM STATUS:
- temperature: {temp:.1f}
- humidity: {hum:.1f}
- button_pressed: {str(button_state).lower()}
- leds: red={str(ledRed).lower()}, blue={str(ledBlue).lower()}, green={str(ledGreen).lower()}
- ldr_value: {ldrValue}
- servo_angle: {servoAngle}
RULES:
1. Output ONLY this JSON structure:
{{
 "message": "",
 "leds": {{
     "red_led": bool,
     "green_led": bool,
     "blue_led": bool
 }},
 "servo_angle": int,
 "pomodoro": {{
     "start": bool,
     "stop": bool,
     "minutes": int,
 }}
}}
2. Do NOT add extra text outside the JSON.
3. If user asks information → keep hardware states unchanged.
4. If user requests an action → update the states.
5. Only ONE LED ON unless user explicitly requests multiple.
6. Evaluate conditions (e.g., "if", "quando") based on the system status temperature, humidity and ldr_value.
7. Be clear and short in "message".
USER INPUT: "{user_input}" 
"""

    def slm_inference(self, PROMPT):
        response = self.session.post(
            url=f"{self.ollama_host}/api/generate",
            json={
                "model": "gemma3",
                "prompt": PROMPT,
                "stream": False,
                "format":"json",
            }
        )
        print(response.json().get("response", {}))
        return response.json().get("response", {})

    def parse_interactive_response(self, response_text):
        """Parse the interactive SLM JSON response."""
        try: 
            response_text = json.loads(response_text)     
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
            # Extract Servo angle
            servo_angle = response_text.get('servo_angle', 0)
            return message, (red_led, blue_led, green_led), servo_angle, (pomodoro_start, pomodoro_stop, pomodoro_minutes)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response was: {response_text}")
            return "Error", (False, False, False), 0, (False, False, 0, 0)
    
    def query(self, body):
        # Create prompt with user input
        print("Sending requesto to IoT SLM...")
        start_time = time.time()
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
        message,(red, blue, green), servo_angle, (pomodoro_start, pomodoro_stop, pomodoro_minutes) = self.parse_interactive_response(response)
        end_time = time.time()
        latency = end_time - start_time
        print(f"Response latency: {latency:.2f} seconds using model: {self.model}")
        return message,(red, blue, green), servo_angle, (pomodoro_start, pomodoro_stop, pomodoro_minutes), response