# -*- coding: utf-8 -*-
"""PASO 3 - PRUEBA DEL RETARDO (una sola apretada).

Herramienta de calibracion del piano de Pandora (God of War 3).

En vez de tocar toda la secuencia (18 toques), esta version aprieta UNA
sola vez la PRIMERA tecla (la X) despues de "retardo_ms" desde tu
pulsacion de la tecla de arranque (N). Las demas teclas se ignoran.
Asi se ve facil si el tiempo de espera esta bien:

  - Si la X cae ANTES de que la primera gema llegue a la zona: subir
    retardo_ms (de a 300 ms, en ritmo.json).
  - Si cae DESPUES (la gema ya paso): bajarlo.

Cuando la X caiga justo, usar 2_reproducir_secuencia.bat (secuencia
completa). ESC cancela. La configuracion esta en ritmo.json.
"""

import ctypes
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _gancho import GrabadorTeclas
from reproducir_ritmo import (
    MAPA_TECLAS,
    _apretar,
    _entero,
    _pitido,
    _soltar,
    cargar_ritmo,
    dormir_hasta,
    vk_de_arranque,
)


def main():
    try:
        ctypes.WinDLL("winmm").timeBeginPeriod(1)
    except Exception:
        pass

    cfg = cargar_ritmo()
    retardo_ms = max(0, _entero(cfg, "retardo_ms", 5500))
    retardo = retardo_ms / 1000.0
    hold = max(0, _entero(cfg, "hold_ms", 80)) / 1000.0
    cuenta = max(0, _entero(cfg, "cuenta_regresiva_s", 10))
    usar_vk = bool(cfg.get("usar_vk", False))
    tecla_txt = str(cfg.get("tecla_arranque") or "").strip().upper() or "la tecla de arranque"
    vk_arranque = vk_de_arranque(cfg.get("tecla_arranque"), 0x4E)

    print()
    print("=== PASO 3: PRUEBA DEL RETARDO (calibracion) ===")
    print()
    print("Esto NO toca la secuencia completa: aprieta SOLO LA PRIMERA X")
    print("(la de la primera gema) para ver si el tiempo de espera esta bien.")
    print()
    print("Valor actual: retardo_ms = %d  (la X sale %.2f s despues de tu %s)"
          % (retardo_ms, retardo, tecla_txt))
    print()
    print("MODO DE USO:")
    print("  1. Estate parado en el instrumento, listo para arrancar.")
    print("  2. Cuando quieras, apreta %s en el juego (es tu R1). Solo" % tecla_txt)
    print("     reacciona a %s: el resto del teclado se ignora." % tecla_txt)
    print("  3. Espera la apretada y mira la PRIMERA gema:")
    print("     - Si la X cae ANTES de que llegue a la zona: subir el numero")
    print("       (ej: %d) y probar de nuevo." % (retardo_ms + 300))
    print("     - Si cae DESPUES (ya paso): bajarlo (ej: %d)."
          % max(0, retardo_ms - 300))
    print("     Se edita 'retardo_ms' en ritmo.json y se repite la prueba.")
    print("  4. Para repetir: espera 'Todo listo' y apreta %s otra vez." % tecla_txt)
    print()
    print("ESC = cancelar (el juego no lo recibe).")
    print()

    gancho = GrabadorTeclas()
    resultado = {}

    def _hilo_gancho():
        # El gancho debe instalarse Y bombear mensajes en el MISMO hilo.
        resultado["ok"] = gancho.instalar()
        if resultado["ok"]:
            gancho.correr()

    hilo = threading.Thread(target=_hilo_gancho, daemon=True)
    hilo.start()
    while "ok" not in resultado:
        time.sleep(0.01)
    if not resultado["ok"]:
        print("ERROR: no pude instalar el gancho de teclado.")
        print("Proba ejecutando el .bat como administrador (clic derecho).")
        return 1

    if cuenta:
        print("Cuenta regresiva: pasate al juego AHORA.")
        for s in range(cuenta, 0, -1):
            time.sleep(1.0)
            print("  ...%d" % s, flush=True)
        print()

    consumidos = len(gancho.teclas)
    print("ARMADO. Apreta %s cuando quieras probar..." % tecla_txt, flush=True)
    _pitido()

    k = MAPA_TECLAS["x"]
    intentos = 0
    ultimo_aviso = time.perf_counter()
    try:
        while not gancho.terminado:
            # esperar SOLO la tecla de arranque: las demas se ignoran
            reg = None
            while reg is None and not gancho.terminado:
                if len(gancho.teclas) == consumidos:
                    time.sleep(0.002)
                    ahora = time.perf_counter()
                    if ahora - ultimo_aviso > 20.0:
                        ultimo_aviso = ahora
                        print("  (sigo esperando: apreta %s cuando quieras)" % tecla_txt,
                              flush=True)
                    continue
                nuevos = gancho.teclas[consumidos:]
                consumidos = len(gancho.teclas)
                for ev in nuevos:
                    if int(ev.get("vk", 0)) == vk_arranque:
                        reg = ev
                        break
            if gancho.terminado:
                break
            ultimo_aviso = time.perf_counter()
            t_arranque = gancho._t0 + float(reg["t"])
            intentos += 1
            print("%s detectada. La X sale en %.2fs..." % (tecla_txt, retardo),
                  flush=True)
            dormir_hasta(t_arranque + retardo)
            _apretar(k, usar_vk)
            if hold:
                time.sleep(hold)
            _soltar(k, usar_vk)
            print("> X apretada. Mira el juego: ¿la X cayo justo cuando la gema")
            print("  llego a la zona?  Si no: cambia retardo_ms en ritmo.json")
            print("  (+300 = mas tarde / -300 = mas temprano) y repite la prueba.")
            consumidos = len(gancho.teclas)
            time.sleep(6.0)
            consumidos = len(gancho.teclas)
            print("Todo listo: apreta %s otra vez para la siguiente prueba." % tecla_txt,
                  flush=True)
            _pitido()
    except KeyboardInterrupt:
        pass
    finally:
        gancho.quitar()
        try:
            ctypes.WinDLL("winmm").timeEndPeriod(1)
        except Exception:
            pass

    print()
    if gancho.terminado:
        print("Cancelado con ESC (el juego no recibio el ESC).")
    print("Pruebas hechas: %d." % intentos)
    print("Cuando la X caiga justo: usa 2_reproducir_secuencia.bat (completo).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print("Cancelado.")
        sys.exit(130)
