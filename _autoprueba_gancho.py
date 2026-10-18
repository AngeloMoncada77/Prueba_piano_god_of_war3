# -*- coding: utf-8 -*-
"""Autoprueba interna: verifica que el GANCHO de grabacion funcione.

Abre una ventanita breve, se inyectan 3 teclas y comprueba que el
grabador las capture en orden. Solo diagnostico.
"""

import json
import os
import sys
import time

os.environ["PIANO_PERMITIR_INYECTADAS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _gancho import GrabadorTeclas
from _teclas import enviar_scan, titulo_ventana_al_frente

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTADO = os.path.join(BASE, "_autoprueba_gancho.json")

PRUEBA = [(0x1E, False), (0x1F, False), (0x48, True)]  # a, s, flecha arriba


def guardar(datos):
    with open(RESULTADO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def main():
    import tkinter as tk

    root = tk.Tk()
    root.title("autoprueba del gancho")
    root.geometry("320x90+30+30")
    root.attributes("-topmost", True)
    tk.Label(root, text="Prueba automatica del gancho...").pack(expand=True)
    root.focus_force()

    grabador = GrabadorTeclas()
    if not grabador.instalar():
        guardar({"error": "no se pudo instalar el gancho"})
        root.destroy()
        return 1

    def disparar():
        if "autoprueba" not in titulo_ventana_al_frente().lower():
            root.focus_force()
            root.after(500, disparar)
            return
        for scan, ext in PRUEBA:
            enviar_scan(scan, ext=ext, arriba=False)
            time.sleep(0.06)
            enviar_scan(scan, ext=ext, arriba=True)
            time.sleep(0.08)
        root.after(600, terminar)

    def terminar():
        grabador.quitar()
        guardar({"esperadas": ["A", "S", "Flecha arriba"],
                 "grabadas": grabador.teclas})
        root.destroy()

    root.after(1000, disparar)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
