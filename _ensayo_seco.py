# -*- coding: utf-8 -*-
"""Ensayo en seco: imprime el cronograma completo de la secuencia SIN tocar teclas.

Usa exactamente la misma configuracion (ritmo.json) y la misma matematica de
tiempos que reproducir_ritmo.py, para verificar antes de jugar.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reproducir_ritmo import MAPA_TECLAS, cargar_ritmo


def main():
    cfg = cargar_ritmo()
    retardo = cfg["retardo_ms"] / 1000.0
    intervalo = cfg["intervalo_ms"] / 1000.0
    pasos = cfg["pasos"]
    intervalos = cfg.get("intervalos_ms")

    print("retardo_ms = %d | intervalo_ms = %d | hold_ms = %d"
          % (cfg["retardo_ms"], cfg["intervalo_ms"], cfg["hold_ms"]))
    print()
    print("%2s  %9s  %s" % ("#", "tiempo", "teclas"))
    t = retardo
    pares = 0
    for i, paso in enumerate(pasos, 1):
        if len(paso) > 1:
            pares += 1
        nombres = " + ".join(MAPA_TECLAS[n]["nombre"] for n in paso)
        print("%2d  %7.2fs  %s" % (i, t, nombres))
        if intervalos and i - 1 < len(intervalos):
            try:
                delta = float(intervalos[i - 1]) / 1000.0
            except (TypeError, ValueError):
                delta = intervalo
        else:
            delta = intervalo
        t += delta

    print()
    print("Total: %d toques (%d pares). Ultimo toque a los %.2fs de tu pulsacion."
          % (len(pasos), pares, t - delta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
