# -*- coding: utf-8 -*-
"""PASO 1: graba la secuencia de teclas que presiones, en orden.

Uso:
    py grabar.py       -> graba hasta que presiones ESC
    py grabar.py 6     -> graba 6 teclas y se detiene solo
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _gancho import GrabadorTeclas

BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(BASE, "secuencia.json")


def main():
    limite = 0
    if len(sys.argv) > 1:
        try:
            limite = int(sys.argv[1])
        except ValueError:
            print("El argumento debe ser un numero (cantidad de teclas).")
            return 2

    print()
    print("=== PASO 1: GRABAR LA SECUENCIA DEL PIANO ===")
    print()
    print("1) Cuando empiece la cuenta regresiva, pasate al juego")
    print("   (haz clic en su ventana o Alt+Tab).")
    print("2) Ubicate en la parte del piano y mira las teclas que pide, EN ORDEN.")
    print("3) Presiona esas teclas con calma, 1 o 2 segundos entre una y otra.")
    print("   No importa si el juego rechaza el intento: solo grabamos el ORDEN.")
    print("   Puedes ignorar lo que haga el juego mientras grabas.")
    if limite:
        print("4) La grabacion se detiene sola despues de %d teclas." % limite)
    else:
        print("4) Cuando termines, presiona ESC.")
        print("   (Ese ESC NO lo recibe el juego, es seguro.)")
    print()
    for s in range(6, 0, -1):
        print("  %d..." % s, flush=True)
        time.sleep(1.0)
    print()
    print("Grabando... hazlo ahora.", flush=True)

    grabador = GrabadorTeclas(limite=limite)
    if not grabador.instalar():
        print("ERROR: no se pudo instalar el gancho de teclado.")
        return 1
    try:
        grabador.correr()
    except KeyboardInterrupt:
        pass
    finally:
        grabador.quitar()

    if not grabador.teclas:
        print()
        print("No se grabo ninguna tecla. ¿Seguro que pasaste al juego?")
        print("Vuelve a ejecutar 1_grabar_secuencia.bat e intentalo de nuevo.")
        return 1

    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump({"teclas": grabador.teclas}, f, ensure_ascii=False, indent=2)

    print()
    print("Secuencia grabada (en orden):")
    for i, t in enumerate(grabador.teclas, 1):
        print("  %d. %s" % (i, t["nombre"]))
    print()
    print("GUARDADO en: %s" % ARCHIVO)
    print("Ahora ejecuta: 2_reproducir_secuencia.bat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
