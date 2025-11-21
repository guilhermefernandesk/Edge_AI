#ifndef FRANZININHO_H
#define FRANZININHO_H

#include <Arduino.h>

#include <WiFi.h>        // Include WiFi library to connect to wireless networks
#include <DHT.h>         // Include DHT library
#include <button.h>      // Include library for button handling
#include "credentials.h" // Include WiFi and API credentials file
#include "oled.h"        // Include OLED display library

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

extern DHT dht(DHTPIN, DHTTYPE); // Initialize DHT sensor
extern Button btn(BOTAO_1);      // Create a Button object for the button as a pull-up input

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

// WiFi network credentials
const char *ssid = SSID;
const char *password = PASSWORD;

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
    pinMode(LDR, INPUT);

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
// LED CONTROL FUNCTIONS
// ============================================================================

void setLeds(bool red, bool blue, bool green)
{
    digitalWrite(LED_VERMELHO, red);
    digitalWrite(LED_AZUL, blue);
    digitalWrite(LED_VERDE, green);
}

void initFranzininho()
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

    // Initialize OLED display
    initDisplay();

    Serial.println(F("[Setup] System ready!"));
}

#endif // FRANZININHO_H