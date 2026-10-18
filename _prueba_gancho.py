# -*- coding: utf-8 -*-
"""Prueba automatica del disparo SOLO-CON-N y del flujo de intentos.

No toca el juego:
  - reemplaza el envio real de teclas por un registro en memoria;
  - usa teclas inyectadas de prueba (A, B, N, ESC) que el gancho acepta
    gracias a PIANO_PERMITIR_INYECTADAS=1.

Plan de teclas de prueba:
  t=0.5s  A  (NO debe arrancar nada)
  t=1.5s  B  (NO debe arrancar nada)
  t=2.5s  N  (arranca intento 1)
  t=4.0s  A  (se ignora: esperando)
  t=5.0s  N  (arranca intento 2)
  t=6.5s  ESC (corta; el gancho lo bloquea)
"""

import json
import os
import sys
import tempfile
import threading
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.environ["PIANO_PERMITIR_INYECTADAS"] = "1"

import reproducir_ritmo as rr  # noqa: E402
import _teclas  # noqa: E402

cfg = {
    "retardo_ms": 60,
    "intervalo_ms": 50,
    "intervalos_ms": [50, 50],
    "hold_ms": 1,
    "espera_entre_intentos_s": 1,
    "max_intentos": 5,
    "tecla_arranque": "n",
    "cuenta_regresiva_s": 0,
    "usar_vk": False,
    "ventana_titulo": "",
    "pasos": [["x"], ["circulo"], ["triangulo"]],
}
ruta = os.path.join(tempfile.gettempdir(), "ritmo_prueba_gancho.json")
with open(ruta, "w", encoding="utf-8") as f:
    json.dump(cfg, f)
rr.ARCHIVO_RITMO = ruta

registro = []
def falso_tocar(paso, _cfg, _objetivo):
    registro.append((round(time.perf_counter(), 2), "+".join(paso)))
rr.tocar_paso = falso_tocar
rr._pitido = lambda: None

VK_A, VK_B, VK_N, VK_ESC = 0x41, 0x42, 0x4E, 0x1B
inyectadas = []


def _pulsar(vk):
    _teclas.enviar_vk(vk, False)
    time.sleep(0.015)
    _teclas.enviar_vk(vk, True)


def inyector():
    plan = [(0.5, VK_A), (1.5, VK_B), (2.5, VK_N),
            (4.0, VK_A), (5.0, VK_N), (6.5, VK_ESC)]
    inicio = time.perf_counter()
    for cuando, vk in plan:
        while time.perf_counter() - inicio < cuando:
            time.sleep(0.005)
        inyectadas.append((round(time.perf_counter(), 2), "0x%02X" % vk))
        _pulsar(vk)


hilo = threading.Thread(target=inyector, daemon=True)
hilo.start()

rc = rr.main()

print()
print("=== RESULTADO DE LA PRUEBA ===")
print("rc de main:", rc)
print("teclas inyectadas (t, vk):", inyectadas)
print("toques registrados (t, paso):", registro)
print()

ok = True

if len(registro) != 6:
    print("FALLO: esperaba 6 toques (2 intentos x 3 pasos), hubo %d." % len(registro))
    ok = False

if registro:
    t0 = registro[0][0]
    # primeras teclas inyectadas A(0.5) y B(1.5): NO deben disparar;
    # el primer toque debe caer despues de la N (t >= ~2.4)
    t_a = inyectadas[0][0]
    t_b = inyectadas[1][0]
    t_n = inyectadas[2][0]
    if t0 <= t_b + 0.2:
        print("FALLO: el primer toque salio ANTES de la N (t=%.2f, N=%.2f):"
              " alguna tecla que no es N disparo la secuencia." % (t0, t_n))
        ok = False
    else:
        print("BIEN: A(%.2f) y B(%.2f) se ignoraron; los toques empezaron"
              " despues de N(%.2f)." % (t_a, t_b, t_n))

if ok:
    print()
    print("TODO OK: solo N arranca la secuencia; las demas teclas no hacen nada.")

sys.exit(0 if ok else 1)
