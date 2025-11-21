#ifndef POMODORO_H
#define POMODORO_H

#include <Arduino.h>
#include "franzininho.h" // Include board configuration definitions
#include "oled.h"        // Include OLED display library

// Pomodoro variables (non-blocking)
enum PomState
{
    STOPPED,
    RUNNING,
    BREAKING
};

PomState pomState = STOPPED;

unsigned long pomStartMillis = 0;
unsigned long pomPausedMillis = 0;
unsigned long pomDurationMillis = 0;

// Variáveis globais (para exibir no OLED)
int pomRemainingMinutes = 0;
int pomRemainingSeconds = 0;

// ----- Pomodoro control functions -----
void startPomodoro(int minutes)
{
    pomDurationMillis = (unsigned long)minutes * 60UL * 1000UL;
    pomStartMillis = millis();
    pomState = RUNNING;
    Serial.printf("[Pomodoro] Start %d min\n", minutes);
    showMessage("Pomodoro started for " + String(minutes) + " min");
    setLeds(false, false, true); // green = running
}

void pausePomodoro()
{
    if (pomState == RUNNING)
    {
        pomPausedMillis = millis();
        pomState = BREAKING;
        Serial.println("[Pomodoro] Paused");
        // displayMessage("Pomodoro paused", "");
        // setLed(false, false, true); // blue = paused
    }
}

void resumePomodoro()
{
    if (pomState == BREAKING)
    {
        unsigned long pausedFor = millis() - pomPausedMillis;
        pomStartMillis += pausedFor; // shift start
        pomState = RUNNING;
        Serial.println("[Pomodoro] Resumed");

        // displayMessage("Pomodoro resumed", "");
        // setLed(false, true, false);
    }
}

void stopPomodoro()
{
    pomState = STOPPED;
    pomDurationMillis = 0;
    pomStartMillis = 0;
    Serial.println("[Pomodoro] Stopped");
    // displayMessage("Pomodoro stopped", "");
    // setLed(false, false, false);
}

void startBreak()
{
    pomDurationMillis = 5UL * 60UL * 1000UL; // 5 minutos
    pomStartMillis = millis();

    pomState = BREAKING;

    Serial.println("[Pomodoro] Descanso 5 min");
    showMessage("Descanso 5 min");

    setLeds(false, true, false);
}

// ====== ATUALIZAÇÃO NÃO-BLOQUEANTE ======
void updatePomodoro()
{
    if (pomState == STOPPED)
        return;

    unsigned long elapsed = millis() - pomStartMillis;

    if (elapsed >= pomDurationMillis)
    {
        if (pomState == RUNNING)
        {
            // Fim do pomodoro principal
            Serial.println("[Pomodoro] Finalizado!");

            showMessage("Pomodoro finalizado. Descanse 5 min.");

            setLeds(true, false, false); // vermelho = fim

            startBreak();
            return;
        }
        else if (pomState == BREAKING)
        {
            // Fim da pausa
            Serial.println("[Pomodoro] Ciclo completo");

            showMessage("Ciclo completo!");

            setLeds(false, false, false);
            pomState = STOPPED;
            return;
        }
    }

    unsigned long remaining = pomDurationMillis - elapsed;

    pomRemainingMinutes = remaining / 60000UL;
    pomRemainingSeconds = (remaining % 60000UL) / 1000UL;

    // Atualiza OLED externamente:
    showPomodoro(pomRemainingMinutes, pomRemainingSeconds, pomState);
}

#endif // POMODORO_H