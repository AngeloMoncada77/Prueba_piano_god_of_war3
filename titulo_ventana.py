# -*- coding: utf-8 -*-
"""Muestra el titulo de la ventana que este al frente (para configurarla)."""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _teclas import titulo_ventana_al_frente


def main():
    print()
    print("=== VER EL TITULO DE LA VENTANA DEL JUEGO ===")
    print()
    print("En unos segundos te muestro que ventana esta al frente.")
    print("Haz clic AHORA en la ventana del juego (dejala al frente).")
    print()
    for s in range(5, 0, -1):
        print("  %d..." % s, flush=True)
        time.sleep(1.0)
    t = titulo_ventana_al_frente()
    print()
    print("Ventana al frente: '%s'" % t)
    print()
    print("Copia ese titulo (o una parte corta de el) y pasalo a la IA para")
    print("ponerlo en config.json -> ventana_titulo (enfoca el juego solo).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
