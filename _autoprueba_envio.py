# -*- coding: utf-8 -*-
"""Autoprueba interna: verifica que el envio de teclas por scancode funcione.

Abre una ventanita breve, se envia 5 teclas a si misma y guarda el
resultado en _autoprueba_resultado.json. Es solo diagnostico.
"""

import ctypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _teclas import enviar_scan, titulo_ventana_al_frente

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTADO = os.path.join(BASE, "_autoprueba_resultado.json")

PRUEBA = [("a", 0x1E, False), ("s", 0x1F, False), ("Arriba", 0x48, True),
          ("Izquierda", 0x4B, True), ("Espacio", 0x39, False)]

recibidas = []


def guardar(datos):
    with open(RESULTADO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def main():
    import tkinter as tk

    root = tk.Tk()
    root.title("autoprueba de teclado")
    root.geometry("320x90+30+30")
    root.attributes("-topmost", True)
    etiqueta = tk.Label(root, text="Prueba automatica en curso...")
    etiqueta.pack(expand=True)
    root.bind("<KeyPress>", lambda e: recibidas.append((e.keysym, e.keycode)))
    root.focus_force()

    def tiene_foco():
        return "autoprueba" in titulo_ventana_al_frente().lower()

    def disparar():
        if not tiene_foco():
            root.focus_force()
            root.after(500, disparar)
            return
        for _nombre, scan, ext in PRUEBA:
            enviar_scan(scan, ext=ext, arriba=False)
            time.sleep(0.07)
            enviar_scan(scan, ext=ext, arriba=True)
            time.sleep(0.10)
        root.after(600, terminar)

    def terminar():
        guardar({"enviadas": [p[0] for p in PRUEBA], "recibidas": recibidas})
        root.destroy()

    root.after(1000, disparar)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
