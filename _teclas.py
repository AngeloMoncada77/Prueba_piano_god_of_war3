# -*- coding: utf-8 -*-
"""Teclado de bajo nivel para Windows, sin dependencias externas.

- enviar_scan() : envia pulsaciones por codigo de escaneo (scancode),
  que es lo que mejor entienden los juegos y emuladores.
- enviar_vk()   : plan B, por codigo virtual (por si el juego lo pide).
- ayuda para traer al frente la ventana del juego.
"""

import ctypes
import ctypes.wintypes as wt
import time

usuario32 = ctypes.WinDLL("user32", use_last_error=True)

ULONG_PTR = ctypes.c_size_t

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR))


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR))


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg", wt.DWORD), ("wParamL", wt.WORD), ("wParamH", wt.WORD))


class _UnionEntrada(ctypes.Union):
    _fields_ = (("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT))


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = (("type", wt.DWORD), ("u", _UnionEntrada))


usuario32.SendInput.argtypes = (wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
usuario32.SendInput.restype = wt.UINT


def _enviar(entrada):
    if usuario32.SendInput(1, ctypes.byref(entrada), ctypes.sizeof(INPUT)) != 1:
        raise ctypes.WinError(ctypes.get_last_error())


def enviar_scan(scan, ext=False, arriba=False):
    """Presiona o suelta una tecla por codigo de escaneo."""
    banderas = KEYEVENTF_SCANCODE
    if ext:
        banderas |= KEYEVENTF_EXTENDEDKEY
    if arriba:
        banderas |= KEYEVENTF_KEYUP
    _enviar(INPUT(type=INPUT_KEYBOARD,
                  u=_UnionEntrada(ki=KEYBDINPUT(0, scan, banderas, 0, 0))))


def presionar_scan(scan, ext, hold_ms):
    enviar_scan(scan, ext, False)
    time.sleep(max(0, hold_ms) / 1000.0)
    enviar_scan(scan, ext, True)


def enviar_vk(vk, arriba=False):
    """Presiona o suelta una tecla por codigo virtual (plan B)."""
    banderas = KEYEVENTF_KEYUP if arriba else 0
    _enviar(INPUT(type=INPUT_KEYBOARD,
                  u=_UnionEntrada(ki=KEYBDINPUT(vk, 0, banderas, 0, 0))))


def presionar_vk(vk, hold_ms):
    enviar_vk(vk, False)
    time.sleep(max(0, hold_ms) / 1000.0)
    enviar_vk(vk, True)


# --- nombres de teclas (solo para mostrar; la grabacion usa scancodes) ---

NOMBRES_VK = {0x08: "Retroceso", 0x09: "Tab", 0x0D: "Enter", 0x10: "Shift", 0x11: "Ctrl",
              0x12: "Alt", 0x13: "Pausa", 0x14: "BloqMayus", 0x1B: "Escape", 0x20: "Espacio",
              0x21: "AvPag", 0x22: "RePag", 0x23: "Fin", 0x24: "Inicio",
              0x25: "Flecha izquierda", 0x26: "Flecha arriba", 0x27: "Flecha derecha",
              0x28: "Flecha abajo", 0x2D: "Insert", 0x2E: "Supr",
              0xA0: "Shift izq", 0xA1: "Shift der", 0xA2: "Ctrl izq", 0xA3: "Ctrl der",
              0xA4: "Alt izq", 0xA5: "Alt der",
              0xBA: "Punto y coma", 0xBB: "Igual", 0xBC: "Coma", 0xBD: "Guion",
              0xBE: "Punto", 0xBF: "Barra", 0xC0: "Acento",
              0xDB: "Corchete ab", 0xDC: "Barra invertida", 0xDD: "Corchete ce", 0xDE: "Comilla"}
for _i in range(26):
    NOMBRES_VK[0x41 + _i] = chr(65 + _i)
for _i in range(10):
    NOMBRES_VK[0x30 + _i] = str(_i)
    NOMBRES_VK[0x60 + _i] = "Num " + str(_i)
for _i in range(24):
    NOMBRES_VK[0x70 + _i] = "F" + str(_i + 1)


def nombre_de(vk):
    return NOMBRES_VK.get(int(vk), "Tecla(0x%02X)" % int(vk))


# --- ventanas (para poder enfocar el juego automaticamente) ---

usuario32.GetForegroundWindow.restype = ctypes.c_void_p
usuario32.GetWindowTextLengthW.argtypes = (ctypes.c_void_p,)
usuario32.GetWindowTextLengthW.restype = ctypes.c_int
usuario32.GetWindowTextW.argtypes = (ctypes.c_void_p, wt.LPWSTR, ctypes.c_int)
usuario32.GetWindowTextW.restype = ctypes.c_int
usuario32.IsWindowVisible.argtypes = (ctypes.c_void_p,)
usuario32.IsWindowVisible.restype = wt.BOOL
usuario32.SetForegroundWindow.argtypes = (ctypes.c_void_p,)
usuario32.SetForegroundWindow.restype = wt.BOOL


def titulo_de_ventana(hwnd):
    largo = usuario32.GetWindowTextLengthW(hwnd)
    if largo <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(largo + 1)
    usuario32.GetWindowTextW(hwnd, buf, largo + 1)
    return buf.value


def titulo_ventana_al_frente():
    return titulo_de_ventana(usuario32.GetForegroundWindow())


def enfocar_ventana_por_titulo(fragmento):
    """Trae al frente la primera ventana visible cuyo titulo contenga el texto."""
    fragmento = fragmento.lower()
    encontradas = []
    proc_tipo = ctypes.WINFUNCTYPE(wt.BOOL, ctypes.c_void_p, ctypes.c_ssize_t)

    def _cb(hwnd, _lparam):
        if usuario32.IsWindowVisible(hwnd):
            titulo = titulo_de_ventana(hwnd)
            if titulo and fragmento in titulo.lower():
                encontradas.append(hwnd)
                return False
        return True

    proc = proc_tipo(_cb)
    usuario32.EnumWindows.argtypes = (proc_tipo, ctypes.c_ssize_t)
    usuario32.EnumWindows.restype = wt.BOOL
    usuario32.EnumWindows(proc, 0)
    if encontradas:
        usuario32.SetForegroundWindow(encontradas[0])
        return True
    return False
