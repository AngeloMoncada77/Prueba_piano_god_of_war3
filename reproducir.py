# -*- coding: utf-8 -*-
"""PASO 2: reproduce la secuencia grabada, con tiempos precisos, varias veces.

Se configura con config.json (mira el LEEME.txt).
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _teclas import (enfocar_ventana_por_titulo, enviar_vk, nombre_de,
                     presionar_scan, presionar_vk)

BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_SEC = os.path.join(BASE, "secuencia.json")
ARCHIVO_CFG = os.path.join(BASE, "config.json")

CFG_POR_DEFECTO = {
    "retardo_inicial_s": 6,
    "intentos": 8,
    "pausa_entre_intentos_ms": 3000,
    "hold_ms": 90,
    "gap_ms": 160,
    "modo": "pasos",          # "pasos" = tiempos uniformes | "fiel" = tiempos de la grabacion
    "factor_tiempo": 1.0,
    "usar_vk": False,         # plan B: enviar por codigo virtual en vez de scancode
    "ventana_titulo": "",     # opcional: parte del titulo de la ventana del juego
}


def cargar_config():
    cfg = dict(CFG_POR_DEFECTO)
    try:
        with open(ARCHIVO_CFG, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except FileNotFoundError:
        pass
    except Exception as e:
        print("AVISO: config.json tiene un error (%s); uso los valores por defecto." % e)
    return cfg


def cargar_secuencia():
    try:
        with open(ARCHIVO_SEC, encoding="utf-8") as f:
            datos = json.load(f)
        teclas = datos["teclas"]
        if not teclas:
            raise ValueError("vacia")
        return teclas
    except FileNotFoundError:
        print("No existe secuencia.json todavia.")
        print("Ejecuta primero: 1_grabar_secuencia.bat")
        sys.exit(1)
    except Exception as e:
        print("No pude leer secuencia.json (%s)." % e)
        print("Vuelve a grabarla con 1_grabar_secuencia.bat")
        sys.exit(1)


def enviar_tecla(t, cfg):
    hold = int(cfg["hold_ms"])
    if cfg.get("usar_vk"):
        presionar_vk(int(t["vk"]), hold)
    else:
        presionar_scan(int(t["scan"]), bool(t.get("ext", False)), hold)


def main():
    cfg = cargar_config()
    teclas = cargar_secuencia()
    intentos = max(1, int(cfg["intentos"]))

    nombres = " -> ".join(t.get("nombre") or nombre_de(t.get("vk", 0)) for t in teclas)
    print()
    print("=== PASO 2: REPRODUCIR LA SECUENCIA DEL PIANO ===")
    print()
    print("Secuencia que voy a enviar:")
    print("  %s" % nombres)
    print()
    if cfg["modo"] == "fiel":
        print("Modo: fiel a la grabacion (factor %s)" % cfg["factor_tiempo"])
    else:
        print("Modo: pasos (tecla presionada %s ms, separacion %s ms)"
              % (cfg["hold_ms"], cfg["gap_ms"]))
    print("Intentos: %d  (pausa de %s ms entre intentos)"
          % (intentos, cfg["pausa_entre_intentos_ms"]))
    print()

    if cfg.get("ventana_titulo"):
        if enfocar_ventana_por_titulo(cfg["ventana_titulo"]):
            print("Ventana del juego enfocada: %s" % cfg["ventana_titulo"])
        else:
            print("No encontre la ventana '%s'; pasate al juego manualmente."
                  % cfg["ventana_titulo"])

    print("Pasate al juego AHORA (clic en su ventana o Alt+Tab). Cuenta regresiva:")
    for s in range(int(cfg["retardo_inicial_s"]), 0, -1):
        print("  %d..." % s, flush=True)
        time.sleep(1.0)
    print()

    for intento in range(1, intentos + 1):
        print("Enviando secuencia... (intento %d/%d)" % (intento, intentos), flush=True)
        t_anterior = None
        for i, t in enumerate(teclas):
            if cfg["modo"] == "fiel" and t.get("t") is not None:
                t_actual = float(t["t"])
                if t_anterior is not None:
                    espera = max(0.0, (t_actual - t_anterior) * float(cfg["factor_tiempo"]))
                    time.sleep(min(espera, 2.5))
                t_anterior = t_actual
            elif i > 0:
                time.sleep(max(0, int(cfg["gap_ms"])) / 1000.0)
            enviar_tecla(t, cfg)
        if intento < intentos:
            time.sleep(max(0, int(cfg["pausa_entre_intentos_ms"])) / 1000.0)

    print()
    print("FIN. Si el juego lo acepto: ¡ya esta, pasaste el piano!")
    print("Si no funciono, cierra esta ventana y avisale a la IA para ajustar")
    print("los tiempos en config.json (o probar el plan B).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print("Cancelado.")
        sys.exit(130)
