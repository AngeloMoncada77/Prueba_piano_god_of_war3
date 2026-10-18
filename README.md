# Piano de Pandora Automático — God of War 3 (PC)

Macro de teclado que toca **sola** la melodía completa del puzzle del piano (el
instrumento gigante de Pandora) en la versión de PC: **25 toques con precisión
de milisegundos**, incluida la frase final después de la pausa larga.

## Cómo funciona

El puzzle es de ritmo: las gemas viajan por la banda y hay que apretar cada
botón **justo cuando pasan por la placa dorada** (a veces viajan dos juntas,
"en par"). El programa espera a que aprietes la tecla de arranque (**N**, tu R1
del juego) y desde ahí reproduce la melodía completa con los tiempos exactos
medidos de videos del juego real. No hay que tocar nada más.

## Uso

1. Doble clic en `2_reproducir_secuencia.bat`.
   (Si el juego no recibe las teclas: clic derecho → *Ejecutar como administrador*.)
2. Suena un pitido: el programa queda **ARMADO** y espera sin hacer nada.
3. Párate en el instrumento y aprieta **N** cuando quieras empezar.
4. No toques nada más hasta que termine. `ESC` cancela en cualquier momento.

Si el juego rechaza el intento y se reinicia, el programa queda listo otra vez:
aprieta **N** para el siguiente intento.

## Teclas

| Botón en el juego | Tecla del teclado |
|-------------------|-------------------|
| ✕                 | Espacio           |
| ○                 | Shift izquierdo   |
| □                 | O                 |
| △                 | L                 |

## Archivos

- `reproducir_ritmo.py` — el programa en sí (lo lanza el .bat).
- `ritmo.json` — melodía (25 toques) y tiempos exactos de cada nota; editable.
- `LEEME.txt` — guía completa en español: uso, calibración y solución de problemas.
- `_gancho.py` / `_teclas.py` — módulos internos (captura de teclas y envío de pulsaciones).
- `_ensayo_seco.py` — ensayo en seco: muestra los toques y tiempos sin tocar nada.
- `3_probar_retardo.bat` / `3_ver_titulo_ventana.bat` — utilidades opcionales (calibrar el primer toque / ver el título de la ventana del juego).

## Requisitos

- Windows + Python 3 (con el lanzador `py`).
- El juego en primer plano (ventana activa).
