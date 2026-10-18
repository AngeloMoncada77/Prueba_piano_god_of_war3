# -*- coding: utf-8 -*-
"""PASO 2 (modo RITMO) - Piano de Pandora, God of War 3.

El puzzle es de RITMO: las gemas viajan por la banda del instrumento y hay
que apretar cada boton JUSTO cuando pasa por la placa dorada central.
A veces viajan dos juntas (un "par") y se aprietan a la vez.

Este programa hace todo por vos:

  1) Avisa con un pitido y espera. NO hay cuenta regresiva: se queda
     esperando a que TU aprietes la tecla de arranque (N). Las demas
     teclas se ignoran por completo: si no tocas N, no pasa nada.
  2) Desde esa N espera "retardo_ms" (lo que tarda la primera gema en
     llegar) y toca la secuencia completa con los tiempos reales de la
     melodia ("intervalos_ms": cada nota tiene su propia espera).
  3) Espera unos segundos y queda listo otra vez: cuando el juego se
     reinicie, apreta de nuevo N.

ESC cancela (el juego no lo recibe).

La configuracion esta en ritmo.json.
"""

import ctypes
import json
import os
import sys
import threading
import time

try:
    import winsound
except Exception:  # pragma: no cover
    winsound = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _gancho import GrabadorTeclas
from _teclas import enfocar_ventana_por_titulo, enviar_scan, enviar_vk

BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_RITMO = os.path.join(BASE, "ritmo.json")

# Mapeo de los botones del juego a las teclas del teclado del usuario.
# (Confirmado por el usuario: X=Espacio, circulo=Shift izq, cuadrado=O, triangulo=L)
MAPA_TECLAS = {
    "x": {"vk": 0x20, "scan": 0x39, "ext": False, "nombre": "X (espacio)"},
    "circulo": {"vk": 0xA0, "scan": 0x2A, "ext": False, "nombre": "circulo (Shift izq)"},
    "cuadrado": {"vk": 0x4F, "scan": 0x18, "ext": False, "nombre": "cuadrado (O)"},
    "triangulo": {"vk": 0x4C, "scan": 0x26, "ext": False, "nombre": "triangulo (L)"},
}

# Melodia real completa del puzzle, medida nota por nota de los videos de
# referencia (25 toques; los pares van juntos). Es la misma que trae ritmo.json.
PASOS_POR_DEFECTO = [
    ["x"], ["x"], ["x"],
    ["circulo"], ["cuadrado"], ["circulo"], ["cuadrado"],
    ["x"], ["triangulo"],
    ["cuadrado"],
    ["circulo"], ["triangulo"],
    ["cuadrado", "x"],
    ["cuadrado"],
    ["triangulo"],
    ["cuadrado", "x"],
    ["triangulo"],
    ["triangulo", "circulo"],
    ["triangulo", "circulo"],
    ["x"],
    ["cuadrado"],
    ["cuadrado", "x"],
    ["circulo"],
    ["triangulo"],
    ["triangulo", "circulo"],
]

# Espera (ms) DESDE cada toque hasta el siguiente, medida del video real
# y ajustada al equipo del usuario (compensacion fina de los tramos rapidos).
INTERVALOS_POR_DEFECTO = [
    1167, 1333, 1367, 1966, 700, 633, 700, 634, 1850,
    670, 696, 600, 2000, 633, 666, 700, 700, 3090,
    720, 690, 670, 760, 630, 600,
]

CFG_POR_DEFECTO = {
    "retardo_ms": 5800,          # desde TU N hasta el 1er toque (ajustado con tu video)
    "intervalo_ms": 650,         # plan B si falta intervalos_ms
    "intervalos_ms": INTERVALOS_POR_DEFECTO,  # ritmo real: espera de cada toque al siguiente
    "hold_ms": 80,               # cuanto se mantiene apretada cada tecla
    "espera_entre_intentos_s": 8,
    "max_intentos": 40,
    "tecla_arranque": "n",       # con ESTA tecla arranca (N = tu R1); las demas se ignoran
    "cuenta_regresiva_s": 0,     # sin cuenta regresiva: arranca cuando aprietes N
    "usar_vk": False,            # plan B: enviar por codigo virtual
    "ventana_titulo": "",        # opcional: parte del titulo de la ventana del juego
    "pasos": PASOS_POR_DEFECTO,
}


def _entero(cfg, clave, defecto):
    try:
        return int(cfg.get(clave, defecto))
    except (TypeError, ValueError):
        return int(defecto)


def vk_de_arranque(txt, defecto=0x4E):
    """Convierte la tecla de arranque ("n") a su codigo virtual (N = 0x4E)."""
    txt = str(txt or "").strip().upper()
    if len(txt) == 1 and "A" <= txt <= "Z":
        return ord(txt)
    return defecto


def pasos_validos(pasos):
    if not isinstance(pasos, list) or not pasos:
        return False
    for paso in pasos:
        if not isinstance(paso, list) or not paso:
            return False
        for nombre in paso:
            if nombre not in MAPA_TECLAS:
                return False
    return True


def cargar_ritmo():
    cfg = dict(CFG_POR_DEFECTO)
    try:
        with open(ARCHIVO_RITMO, encoding="utf-8") as f:
            datos = json.load(f)
        if isinstance(datos, dict):
            cfg.update(datos)
    except FileNotFoundError:
        print("AVISO: no existe ritmo.json; uso la secuencia y tiempos por defecto.")
    except Exception as e:
        print("AVISO: ritmo.json tiene un error (%s); uso valores por defecto." % e)
    if not pasos_validos(cfg.get("pasos")):
        print("AVISO: la lista de pasos en ritmo.json no es valida;")
        print("uso la secuencia oficial por defecto.")
        cfg["pasos"] = PASOS_POR_DEFECTO
    return cfg


def dormir_hasta(objetivo):
    """Espera precisa (con giro activo en los ultimos milisegundos)."""
    while True:
        restante = objetivo - time.perf_counter()
        if restante <= 0:
            return
        if restante > 0.003:
            time.sleep(min(restante - 0.001, 0.05))


def _apretar(k, usar_vk):
    if usar_vk:
        enviar_vk(k["vk"], False)
    else:
        enviar_scan(k["scan"], k["ext"], False)


def _soltar(k, usar_vk):
    if usar_vk:
        enviar_vk(k["vk"], True)
    else:
        enviar_scan(k["scan"], k["ext"], True)


def tocar_paso(paso, cfg, objetivo):
    dormir_hasta(objetivo)
    usable = cfg.get("usar_vk", False)
    teclas = [MAPA_TECLAS[n] for n in paso]
    for k in teclas:
        _apretar(k, usable)
    hold = max(0, _entero(cfg, "hold_ms", 80)) / 1000.0
    if hold:
        time.sleep(hold)
    for k in teclas:
        _soltar(k, usable)


def describir_pasos(pasos):
    partes = []
    for p in pasos:
        partes.append(" + ".join(MAPA_TECLAS[n]["nombre"] for n in p))
    return " -> ".join(partes)


def _pitido():
    """Pitido corto: avisa que el programa quedo ARMADO (util en pantalla completa)."""
    if winsound is None:
        return
    try:
        winsound.Beep(880, 350)
    except Exception:
        pass


def main():
    try:
        ctypes.WinDLL("winmm").timeBeginPeriod(1)
    except Exception:
        pass

    cfg = cargar_ritmo()
    pasos = cfg["pasos"]
    retardo = max(0, _entero(cfg, "retardo_ms", 1000)) / 1000.0
    intervalo = max(0.08, _entero(cfg, "intervalo_ms", 650) / 1000.0)
    intervalos = cfg.get("intervalos_ms")  # opcional: lista de demoras por paso
    espera_intento = max(1, _entero(cfg, "espera_entre_intentos_s", 8))
    max_intentos = max(1, _entero(cfg, "max_intentos", 40))
    cuenta = max(0, _entero(cfg, "cuenta_regresiva_s", 6))
    tecla_txt = str(cfg.get("tecla_arranque") or "").strip().upper() or "la tecla de arranque"
    vk_arranque = vk_de_arranque(cfg.get("tecla_arranque"), 0x4E)

    print()
    print("=== PASO 2: PIANO DE PANDORA (MODO RITMO) ===")
    print()
    print("Secuencia que voy a tocar (%d toques, los pares van juntos):" % len(pasos))
    print("  %s" % describir_pasos(pasos))
    print()
    print("Ritmo: primer toque a los %.2fs de TU N (tecla de arranque)," % retardo)
    print("y luego cada nota con SU tiempo real (medido del juego).")
    print()

    if cfg.get("ventana_titulo"):
        if enfocar_ventana_por_titulo(cfg["ventana_titulo"]):
            print("Ventana del juego enfocada: %s" % cfg["ventana_titulo"])
            time.sleep(1.0)
        else:
            print("No encontre la ventana '%s'; pasate al juego manualmente."
                  % cfg["ventana_titulo"])

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

    print("MODO DE USO:")
    print("  1. Estate parado en el instrumento, como para empezar el minijuego.")
    print("  2. Cuando quieras, apreta %s en el juego (es tu R1). NO hay cuenta" % tecla_txt)
    print("     regresiva: el programa no hace nada hasta que toques %s." % tecla_txt)
    print("     Solo reacciona a esa tecla; el resto del teclado se ignora.")
    print("  3. OJO: despues de tocar %s hay unos 5,8 segundos de silencio" % tecla_txt)
    print("     (la primera gema todavia viaja). No toques nada y espera.")
    print("  4. Si el juego se reinicia (fallo el intento), espera a que diga")
    print("     'Todo listo' y apreta otra vez %s para el siguiente intento." % tecla_txt)
    print()
    print("ESC = cancelar (el juego no lo recibe).")
    print()
    if cuenta:
        print("Cuenta regresiva: pasate al juego AHORA.")
        for s in range(cuenta, 0, -1):
            time.sleep(1.0)
            print("  ...%d" % s, flush=True)
        print()

    consumidos = len(gancho.teclas)   # olvidar lo apretado al pasar al juego
    print("ARMADO. Apreta %s cuando quieras arrancar..." % tecla_txt, flush=True)
    _pitido()

    intentos = 0
    ultimo_aviso = time.perf_counter()
    try:
        while not gancho.terminado and intentos < max_intentos:
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
            print("%s detectada. Intento %d: toco en %.2fs..."
                  % (tecla_txt, intentos, retardo), flush=True)

            t_objetivo = t_arranque + retardo
            for i, paso in enumerate(pasos):
                if gancho.terminado:
                    break
                tocar_paso(paso, cfg, t_objetivo)
                if intervalos and i < len(intervalos):
                    try:
                        delta = float(intervalos[i]) / 1000.0
                    except (TypeError, ValueError):
                        delta = intervalo
                    t_objetivo += max(0.05, delta)
                else:
                    t_objetivo += intervalo

            if gancho.terminado:
                break
            print("Secuencia enviada (%d toques). Silencio por %ds..."
                  % (len(pasos), espera_intento), flush=True)
            consumidos = len(gancho.teclas)   # descartar lo ocurrido durante la reproduccion
            time.sleep(espera_intento)
            consumidos = len(gancho.teclas)
            print("Todo listo: para otro intento, apreta otra vez %s cuando el" % tecla_txt)
            print("juego este preparado.", flush=True)
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
    print("Se enviaron %d intento(s)." % intentos)
    print("Si el juego lo acepto: ¡pasaste el piano! Si no, avisale a la IA")
    print("para ajustar el ritmo (retardo_ms / intervalos_ms en ritmo.json).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print("Cancelado.")
        sys.exit(130)
