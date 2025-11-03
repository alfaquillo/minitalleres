#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include "FreeRTOS.h"
#include "task.h"
#include "timers.h"
#include "semphr.h"
#include "queue.h"
#include "console.h"

/* ------------------ Definiciones ------------------ */
typedef struct adivinanza {
    uint8_t valor;
    TaskHandle_t jugador;
} adivinanza;

#define MAX_ADIVINANZAS 10   // Tamaño de la cola
#define NUM_JUGADORES 3      // Número de tareas jugadoras
#define MIN_VAL 1
#define MAX_VAL 20

QueueHandle_t cola;
TaskHandle_t jugadores_handles[NUM_JUGADORES];

/* ------------------ Tarea Jugadora ------------------ */
void TareaJugador(void *param)
{
    TickType_t ultimo_cambio = xTaskGetTickCount();
    char nombre[16];
    snprintf(nombre, sizeof(nombre), "Jugador%lu", (unsigned long)xTaskGetCurrentTaskHandle());

    for (;;)
    {
        adivinanza a;
        a.valor = (rand() % (MAX_VAL - MIN_VAL + 1)) + MIN_VAL;
        a.jugador = xTaskGetCurrentTaskHandle();

        console_print("%s hace adivinanza: %d\n", nombre, a.valor);
        xQueueSend(cola, &a, portMAX_DELAY);

        // Espera aleatoria para simular pensamiento
        vTaskDelay(pdMS_TO_TICKS(500 + rand() % 500));
    }
}

/* ------------------ Tarea Mago ------------------ */
void TareaMago(void *param)
{
    uint8_t numero_magico = (rand() % (MAX_VAL - MIN_VAL + 1)) + MIN_VAL;
    console_print("Mago ha generado un número mágico!\n");

    TickType_t inicio = xTaskGetTickCount();
    int jugadores_restantes = NUM_JUGADORES;

    for (;;)
    {
        adivinanza a;
        if (xQueueReceive(cola, &a, portMAX_DELAY) == pdTRUE)
        {
            console_print("Mago recibió adivinanza %d de jugador\n", a.valor);

            if (a.valor == numero_magico)
            {
                console_print("Jugador adivinó el número y es eliminado!\n");
                vTaskDelete(a.jugador);
                jugadores_restantes--;

                if (jugadores_restantes == 1)
                {
                    // Encontrar jugador restante
                    for (int i = 0; i < NUM_JUGADORES; i++)
                    {
                        eTaskState state = eTaskGetState(jugadores_handles[i]);
                        if (state != eDeleted)
                        {
                            TickType_t fin = xTaskGetTickCount();
                            console_print("Juego terminado! Ganador: Jugador%u, duración: %lu ticks\n",
                                          i, (unsigned long)(fin - inicio));
                        }
                    }
                    vTaskDelete(NULL); // Terminar Mago
                }

                // Generar un nuevo número mágico
                numero_magico = (rand() % (MAX_VAL - MIN_VAL + 1)) + MIN_VAL;
                console_print("Mago genera un nuevo número mágico!\n");
            }
        }
    }
}

/* ------------------ Función principal ------------------ */
void main_taskguesser(void)
{
    // Crear cola
    cola = xQueueCreate(MAX_ADIVINANZAS, sizeof(adivinanza));

    // Crear tareas jugadoras
    for (int i = 0; i < NUM_JUGADORES; i++)
    {
        xTaskCreate(
            TareaJugador,
            "Jugador",
            1000,
            NULL,
            1,
            &jugadores_handles[i]
        );
    }

    // Crear tarea Mago con mayor prioridad
    xTaskCreate(
        TareaMago,
        "Mago",
        1000,
        NULL,
        2, // Prioridad mayor
        NULL
    );

    // Iniciar el scheduler
    vTaskStartScheduler();

    // Si llega aquí, algo falló
    for (;;)
    {
    }
}

