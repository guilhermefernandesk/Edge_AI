#ifndef OLED_H
#define OLED_H

#include <Arduino.h>
// Libraries for OLED display
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SSD1306_I2C_ADDRESS 0x3C // Defina o endereço I2C do display OLED

// Defina a largura e altura do display OLED
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1); // Crie uma instância do display

// ==============================
//      INICIALIZA O DISPLAY
// ==============================
void initDisplay()
{
    // Inicialize a comunicação I2C
    Wire.begin();

    // Inicialize o display com o endereço I2C
    if (!display.begin(SSD1306_SWITCHCAPVCC, SSD1306_I2C_ADDRESS))
    {
        Serial.println(F("[OLED] SSD1306 allocation failed"));
        for (;;)
            ;
    }
    // Limpe o buffer do display
    display.clearDisplay();
    // Defina a cor do texto
    display.setTextColor(SSD1306_WHITE);
    display.display();
    Serial.println(F("[OLED] Display initialized"));
}

// ==============================
//     EXIBE POMODORO
// ==============================
void showPomodoro(int min, int sec, int state)
{
    display.clearDisplay();

    display.setTextSize(1);
    display.setCursor(0, 0);

    if (state == 1)
        display.print("Pomodoro ativo");
    else if (state == 2)
        display.print("Descanso");

    display.setTextSize(2);
    display.setCursor(10, 30);
    display.printf("%02d:%02d", min, sec);

    display.display();
}

// ==============================
//     EXIBE TEXTO GERAL
// ==============================
void showMessage(String msg)
{
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(msg);
    display.display();
}

// ==============================
//       LIMPA DISPLAY
// ==============================
void clearDisplay()
{
    display.clearDisplay();
    display.display();
}

#endif // OLED_H