/*
    Board: Franzininho WiFi Lab01
    IoT Control with SLM Ollama
    Author: Guilherme Fernandes
*/

#include "franzininho.h" // Include board configuration definitions
#include "oled.h"        // Include OLED display library
#include "pomodoro.h"    // Include Pomodoro timer library

#include <HTTPClient.h>  // Include HTTPClient library to make HTTP requests
#include <ArduinoJson.h> // Include ArduinoJson library for JSON manipulation

// ============================================================================
// DATA STRUCTURES
// ============================================================================

struct SensorData
{
  float temperature;
  float humidity;
  bool buttonPressed;
  int ldrValue;
  bool success;
};

struct LedStatus
{
  bool red;
  bool blue;
  bool green;
};

struct PomodoroStatus
{
  bool start;
  bool stop;
  int minutes;
};

struct responseLLM
{
  String message;
  LedStatus leds;
  int servoAngle;
  PomodoroStatus pomodoro;
  bool success;
};

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

String serverPath = API_URL;
String model = "gemma3"; // LLM model to be used
int servoAngle = 0;

// ============================================================================
// FUNÇÕES DE LEITURA DE SENSORES
// ============================================================================

struct SensorData readSensors()
{
  struct SensorData data;

  // Sensor reading
  data.temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();

  // Check if DHT sensor reading failed.
  if (isnan(data.humidity) || isnan(data.temperature))
  {
    Serial.println(F("[Sensor] ERROR: Failed to read from DHT11"));
    data.success = false;
    return data;
  }
  data.buttonPressed = btn.isPressed();
  data.ldrValue = analogRead(LDR);

  data.success = true;

  return data;
}

struct LedStatus readLedStatus()
{
  struct LedStatus status;
  status.red = digitalRead(LED_VERMELHO);
  status.blue = digitalRead(LED_AZUL);
  status.green = digitalRead(LED_VERDE);
  return status;
}

// ============================================================================
// HTTP COMMUNICATION FUNCTIONS
// ============================================================================

struct responseLLM sendToLlm(float temp, float hum, bool button_state, bool ledRed, bool ledBlue, bool ledGreen, int ldrValue, int servoAngle, String input)
{
  struct responseLLM response;

  String classification = sendClassificationToLlm(input);
  if (classification == "Error")
  {
    response.message = "Error: Invalid classification";
    response.success = false;
    return response;
  }

  HTTPClient http;                                    // Create an HTTP client instance
  http.setTimeout(120000);                            // Set read timeout to 120 seconds
  http.begin((serverPath + "/ollama").c_str());       // Start the connection to the server on the route
  http.addHeader("Content-Type", "application/json"); // Add the Content-Type header
  http.addHeader("Connection", "keep-alive");
  http.addHeader("keep-alive", "timeout=120");

  // Create request JSON
  DynamicJsonDocument doc(1024);
  doc["temperature"] = temp;
  doc["humidity"] = hum;
  doc["btn_pressed"] = button_state;
  doc["led_red"] = ledRed;
  doc["led_blue"] = ledBlue;
  doc["led_green"] = ledGreen;
  doc["ldr_value"] = ldrValue;
  doc["servo_angle"] = servoAngle;
  doc["user_input"] = input;
  doc["classification"] = classification;
  String jsonRequest;
  serializeJson(doc, jsonRequest);
  // Send request
  int httpCode = http.POST(jsonRequest);
  if (httpCode != HTTP_CODE_OK)
  {
    Serial.printf("[HTTP] ERROR: Code %d - %s\n",
                  httpCode, http.errorToString(httpCode).c_str());
    http.end();
    response.message = "Error: Invalid server response";
    response.success = false;
    return response;
  }
  // Process response
  String jsonResponse = http.getString();
  http.end();

  DynamicJsonDocument responseDoc(1024);
  DeserializationError error = deserializeJson(responseDoc, jsonResponse);

  if (error)
  {
    Serial.print(F("[HTTP] ERROR: Failed to parse JSON: "));
    Serial.println(error.c_str());
    response.message = "Error: Invalid server response";
    response.success = false;
    return response;
  }

  // Extrair dados da resposta
  Serial.println(String(responseDoc["response"]));

  response.message = responseDoc["message"] | "Sem resposta";
  response.leds.red = responseDoc["red_led"] | false;
  response.leds.blue = responseDoc["blue_led"] | false;
  response.leds.green = responseDoc["green_led"] | false;
  response.servoAngle = responseDoc["servo_angle"] | 0;
  response.pomodoro.start = responseDoc["pomodoro"]["start"] | false;
  response.pomodoro.stop = responseDoc["pomodoro"]["stop"] | false;
  response.pomodoro.minutes = responseDoc["pomodoro"]["minutes"] | 0;
  response.success = true;

  return response;
}

String sendClassificationToLlm(String input)
{
  HTTPClient http;                                      // Create an HTTP client instance
  http.setTimeout(60000);                               // Set read timeout to 60 seconds
  http.begin((serverPath + "/classification").c_str()); // Start the connection to the server on the route
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Connection", "keep-alive");
  // Create request JSON
  DynamicJsonDocument doc(1024);
  doc["user_input"] = input;
  String jsonRequest;
  serializeJson(doc, jsonRequest);
  // Send request
  int httpCode = http.POST(jsonRequest);
  if (httpCode != HTTP_CODE_OK)
  {
    Serial.printf("[HTTP_1] ERROR: Code %d - %s\n", httpCode, http.errorToString(httpCode).c_str());
    http.end();
    return "Error";
  }
  // Process response
  String jsonResponse = http.getString();
  http.end();

  DynamicJsonDocument responseDoc(1024);
  DeserializationError error = deserializeJson(responseDoc, jsonResponse);

  if (error)
  {
    Serial.print(F("[HTTP_2] ERROR: Failed to parse JSON: "));
    Serial.println(error.c_str());
    return "Error";
  }
  // Extrair dados da resposta
  String classification = responseDoc["classification"];
  return classification;
}

// ============================================================================
// INTERFACE FUNCTIONS
// ============================================================================

void printSystemStatus(float temp, float hum, bool button_state, bool ledRed, bool ledBlue, bool ledGreen, int ldrValue, int servoAngle)
{
  Serial.println(F("\n============================================================"));
  Serial.println(F("             SYSTEM STATUS"));
  Serial.println(F("============================================================"));
  Serial.println("DHT11 Sensor: Temp = " + String(temp, 1) + "°C, Humidity: " + String(hum, 1) + "%");
  Serial.println("LDR Value: " + String(ldrValue));
  Serial.println("Servo Angle: " + String(servoAngle) + "°");
  Serial.println("Button: " + String(button_state ? "PRESSED" : "NOT PRESSED"));
  Serial.println("LED Status:");
  Serial.println("Red LED: " + String(ledRed ? "● ON" : "○ OFF"));
  Serial.println("Blue LED: " + String(ledBlue ? "● ON" : "○ OFF"));
  Serial.println("Green LED: " + String(ledGreen ? "● ON" : "○ OFF"));
  Serial.println();
}

void printMenu()
{
  Serial.println(F("============================================================"));
  Serial.println("Controle IoT com SLM");
  Serial.println("Modelo usado: " + model);
  Serial.println(F("============================================================"));
  Serial.println("Comandos que você pode tentar:");
  Serial.println("  - Como está o ambiente para estudar?");
  Serial.println("  - Coloque o servo em 45 graus");
  Serial.println("  - Ligue o LED azul");
  Serial.println("  - Inicie um pomodoro de 10 minutos");
  Serial.println("  - Qual pino está o DHT11 nessa placa?");
  Serial.println("  - Qual é a temperatura atual?");
  Serial.println("  - Desligue todos os LEDs");
  Serial.println("  - Vai chover com base nas condições atuais?");
  Serial.println("  - Digite 'status' para ver o status do sistema");
  Serial.println(F("============================================================"));
  Serial.println();
}

// ============================================================================
// MAIN FUNCTIONS
// ============================================================================

void setup()
{
  initFranzininho();
  printMenu();
}

void loop()
{
  btn.update();
  updatePomodoro();
  if (Serial.available())
  {

    // Read user input
    String input = Serial.readStringUntil('\n');
    Serial.print("You: ");
    Serial.println(input);

    // Get current system status
    struct LedStatus ledSts = readLedStatus();
    struct SensorData data = readSensors();

    // Check if sensor data is valid, if not, return
    if (!data.success)
    {
      Serial.println("Assistant: Error - Unable to read sensor data. Please try again.");
      return;
    }

    // Handle status command
    if (input.equalsIgnoreCase("status"))
    {
      printSystemStatus(data.temperature, data.humidity, data.buttonPressed, ledSts.red, ledSts.blue, ledSts.green, data.ldrValue, servoAngle);
      return;
    }

    // Send data to the LLM and get the response
    struct responseLLM response = sendToLlm(data.temperature, data.humidity, data.buttonPressed, ledSts.red, ledSts.blue, ledSts.green, data.ldrValue, servoAngle, input);

    // Get SLM response
    Serial.println("\nAssistant: [Thinking...]");

    // Display assistant's message
    Serial.println("Assistant: " + response.message);

    // Mostra no display (resposta IA)
    showMessage("Assistant: " + response.message);

    if (!response.success)
    {
      return;
    }

    // Control LEDs based on response
    setLeds(response.leds.red, response.leds.blue, response.leds.green);

    // Ajusta servo
    servoAngle = response.servoAngle;
    // myServo.write(servoAngle);

    // Configura o pomodoro
    if (response.pomodoro.start)
    {
      int minutes = response.pomodoro.minutes;
      startPomodoro(minutes);
    }
    else if (response.pomodoro.stop)
    {
      stopPomodoro();
    }
    printMenu();
  }
}
