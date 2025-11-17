
/*
    Board: Franzininho WiFi Lab01
    IoT Control with SLM via Ollama API
    Author: Guilherme Fernandes
    Example adapted from: Mjrovai - https://github.com/Mjrovai/EdgeML-with-Raspberry-Pi

*/

#include <DHT.h>         // Include DHT library
#include <button.h>      // Include library for button handling
#include "credentials.h" // Include WiFi and API credentials file
#include <WiFi.h>        // Include WiFi library to connect to wireless networks
#include <HTTPClient.h>  // Include HTTPClient library to make HTTP requests
#include <ArduinoJson.h> // Include ArduinoJson library for JSON manipulation

// ============================================================================
// CONFIGURATION DEFINITIONS
// ============================================================================

// Pins board
const uint8_t LED_VERMELHO = 14;
const uint8_t LED_VERDE = 13;
const uint8_t LED_AZUL = 12;
const uint8_t BOTAO_1 = 7;
const uint8_t BOTAO_2 = 6;
const uint8_t BOTAO_3 = 5;
const uint8_t BOTAO_4 = 4;
const uint8_t BOTAO_5 = 3;
const uint8_t BOTAO_6 = 2;
const uint8_t BUZZER = 17;
const uint8_t LDR = 1;
const uint8_t DHTPIN = 15;
#define DHTTYPE DHT11 // Sensor type definition

// ============================================================================
// DATA STRUCTURES
// ============================================================================

struct SensorData
{
  float temperature;
  float humidity;
  bool buttonPressed;
  bool success;
};

struct LedStatus
{
  bool red;
  bool blue;
  bool green;
};

struct responseLLM
{
  String message;
  LedStatus leds;
};

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

DHT dht(DHTPIN, DHTTYPE); // Initialize DHT sensor
Button btn(BOTAO_1);      // Create a Button object for the button as a pull-up input

// WiFi network credentials
const char *ssid = SSID;
const char *password = PASSWORD;
String serverPath = API_URL;

// LLM model to be used
String model = "gpt-oss:120b";

// ============================================================================
// CALLBACKS DE EVENTOS WiFi
// ============================================================================

// Evento WiFi IP
void WiFiGotIP(WiFiEvent_t event, WiFiEventInfo_t info) // WiFi IP event
{
  Serial.println(F("\n[WiFi] Successfully connected!"));
  Serial.print(F("[WiFi] IP Address: "));
  Serial.println(WiFi.localIP());
}

// Evento WiFi Desconectado
void WiFiStationDisconnected(WiFiEvent_t event, WiFiEventInfo_t info) // WiFi Disconnected event
{
  Serial.println("[WiFi] Disconnected from WiFi");
  Serial.print("[WiFi] Reason: ");
  Serial.println(info.wifi_sta_disconnected.reason);
  Serial.println("[WiFi] Trying to reconnect");
  WiFi.begin(ssid, password);
}

// ============================================================================
// INITIALIZATION FUNCTIONS
// ============================================================================

void initPins()
{
  pinMode(LED_VERMELHO, OUTPUT);
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_AZUL, OUTPUT);

  // Initial state of LEDs off
  digitalWrite(LED_VERMELHO, LOW);
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_AZUL, LOW);

  Serial.println(F("[Setup] Pins configured"));
}

void initWiFi()
{
  Serial.println(F("\n[WiFi] Initializing..."));

  WiFi.mode(WIFI_STA);
  WiFi.config(INADDR_NONE, INADDR_NONE, INADDR_NONE, INADDR_NONE);
  WiFi.disconnect(true); // Disconnect from any WiFi network
  delay(1000);           // Wait for 1 second

  // Register WiFi events
  WiFi.onEvent(WiFiGotIP, WiFiEvent_t::ARDUINO_EVENT_WIFI_STA_GOT_IP);
  WiFi.onEvent(WiFiStationDisconnected, WiFiEvent_t::ARDUINO_EVENT_WIFI_STA_DISCONNECTED);

  // Connect to the WiFi network
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[WiFi] Connected");
}

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
// LED CONTROL FUNCTIONS
// ============================================================================

void setLeds(bool red, bool blue, bool green)
{
  digitalWrite(LED_VERMELHO, red);
  digitalWrite(LED_AZUL, blue);
  digitalWrite(LED_VERDE, green);
}

// ============================================================================
// HTTP COMMUNICATION FUNCTIONS
// ============================================================================

struct responseLLM sendToLlm(float temp, float hum, bool button_state, bool ledRed, bool ledBlue, bool ledGreen, String input)
{
  struct responseLLM response;

  HTTPClient http;                                    // Create an HTTP client instance
  http.setTimeout(15000);
  http.begin((serverPath + "/ollama").c_str());       // Start the connection to the server on the route
  http.addHeader("Content-Type", "application/json"); // Add the Content-Type header

  // Create request JSON
  DynamicJsonDocument doc(1024);
  doc["temperature"] = temp;
  doc["humidity"] = hum;
  doc["btn_pressed"] = button_state;
  doc["led_red"] = ledRed;
  doc["led_blue"] = ledBlue;
  doc["led_green"] = ledGreen;
  doc["user_input"] = input;
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
    return response;
  }

  // Extrair dados da resposta
  response.message = responseDoc["message"] | "Sem resposta";
  response.leds.red = responseDoc["red_led"] | false;
  response.leds.blue = responseDoc["blue_led"] | false;
  response.leds.green = responseDoc["green_led"] | false;

  return response;
}

// ============================================================================
// INTERFACE FUNCTIONS
// ============================================================================

void printSystemStatus(float temp, float hum, bool button_state, bool ledRed, bool ledBlue, bool ledGreen)
{
  Serial.println(F("\n============================================================"));
  Serial.println(F("             SYSTEM STATUS"));
  Serial.println(F("============================================================"));
  Serial.println("DHT11 Sensor: Temp = " + String(temp, 1) + "°C, Humidity: " + String(hum, 1) + "%");
  Serial.println("Button: " + String(button_state ? "PRESSED" : "NOT PRESSED"));
  Serial.println("\nLED Status:");
  Serial.println(" Red LED: " + String(ledRed ? "● ON" : "○ OFF"));
  Serial.println(" Blue LED: " + String(ledBlue ? "● ON" : "○ OFF"));
  Serial.println(" Green LED: " + String(ledGreen ? "● ON" : "○ OFF"));
  Serial.println();
}

void printMenu()
{
  Serial.println(F("============================================================"));
  Serial.println("IoT Environmental Monitoring System - Interactive Mode");
  Serial.println("Using Model: " + model);
  Serial.println(F("============================================================"));
  Serial.println("Commands you can try:");
  Serial.println("  - What's the current temperature?");
  Serial.println("  - What are the actual conditions?");
  Serial.println("  - Turn on the blue LED");
  Serial.println("  - If temperature is above 20°C, turn on blue LED");
  Serial.println("  - If button is pressed, turn on red LED");
  Serial.println("  - Turn on all LEDs");
  Serial.println("  - Turn off all LEDs");
  Serial.println("  - Will it rain based on current conditions?");
  Serial.println("  - Type 'status' to see system status");
  Serial.println(F("============================================================"));
  Serial.println();
}

// ============================================================================
// MAIN FUNCTIONS
// ============================================================================

void setup()
{
  Serial.begin(115200);

  Serial.println(F("========================================"));
  Serial.println(F("  Franzininho WiFi Lab01 - Starting"));
  Serial.println(F("========================================"));

  // Initialize pins
  initPins();

  // Initialize WiFi
  initWiFi();

  // Initialize DHT sensor
  dht.begin();
  Serial.println(F("[Setup] DHT11 sensor initialized"));
  Serial.println(F("[Setup] System ready!"));

  printMenu();
}

void loop()
{
  btn.update();
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
      printSystemStatus(data.temperature, data.humidity, data.buttonPressed, ledSts.red, ledSts.blue, ledSts.green);
      return;
    }

    // Send data to the LLM and get the response
    struct responseLLM response = sendToLlm(data.temperature, data.humidity, data.buttonPressed, ledSts.red, ledSts.blue, ledSts.green, input);

    // Get SLM response
    Serial.println("\nAssistant: [Thinking...]");

    // Display assistant's message
    Serial.println("Assistant: " + response.message);

    // Control LEDs based on response
    setLeds(response.leds.red, response.leds.blue, response.leds.green);

    // Display updated system status
    Serial.println("\nLED Update: Red= " + String(response.leds.red ? "ON" : "OFF") + ", Blue= " + String(response.leds.blue ? "ON" : "OFF") + ", Green= " + String(response.leds.green ? "ON" : "OFF"));

    printMenu();
  }
  // Small delay to not overload the loop
  delay(10);
}
