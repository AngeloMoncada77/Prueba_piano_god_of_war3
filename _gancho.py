# -*- coding: utf-8 -*-
"""Gancho (hook) global de teclado para grabar las teclas fisicas, en orden.

No requiere permisos de administrador (el juego tampoco deberia pedirlos;
si el juego corre como administrador, busca el LEEME).
"""

import ctypes
import ctypes.wintypes as wt
import os
import time

from _teclas import nombre_de, usuario32

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.GetModuleHandleW.argtypes = (wt.LPCWSTR,)
kernel32.GetModuleHandleW.restype = ctypes.c_void_p

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
LLKHF_EXTENDED = 0x01
LLKHF_INJECTED = 0x10
VK_ESCAPE = 0x1B


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = (("vkCode", wt.DWORD), ("scanCode", wt.DWORD), ("flags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t))


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int,
                              ctypes.c_size_t, ctypes.c_ssize_t)

usuario32.SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC, ctypes.c_void_p, wt.DWORD)
usuario32.SetWindowsHookExW.restype = ctypes.c_void_p
usuario32.UnhookWindowsHookEx.argtypes = (ctypes.c_void_p,)
usuario32.UnhookWindowsHookEx.restype = wt.BOOL
usuario32.CallNextHookEx.argtypes = (ctypes.c_void_p, ctypes.c_int,
                                     ctypes.c_size_t, ctypes.c_ssize_t)
usuario32.CallNextHookEx.restype = ctypes.c_ssize_t
usuario32.PostQuitMessage.argtypes = (ctypes.c_int,)
usuario32.GetMessageW.argtypes = (ctypes.POINTER(wt.MSG), ctypes.c_void_p, wt.UINT, wt.UINT)
usuario32.GetMessageW.restype = ctypes.c_int
usuario32.TranslateMessage.argtypes = (ctypes.POINTER(wt.MSG),)
usuario32.DispatchMessageW.argtypes = (ctypes.POINTER(wt.MSG),)
usuario32.DispatchMessageW.restype = ctypes.c_ssize_t


class GrabadorTeclas:
    """Graba las teclas fisicas que se presionan, en orden y con tiempos.

    ESC termina la grabacion y NO se le entrega al juego (se bloquea).
    """

    def __init__(self, limite=0, permitir_inyectadas=None):
        self.teclas = []
        self.limite = int(limite) if limite else 0
        self.terminado = False
        if permitir_inyectadas is None:
            permitir_inyectadas = os.environ.get("PIANO_PERMITIR_INYECTADAS") == "1"
        self.permitir_inyectadas = bool(permitir_inyectadas)
        self._presionadas = set()
        self._t0 = time.perf_counter()
        self._proc = None
        self._hook = None

    def instalar(self):
        def _proc(nCode, wParam, lParam):
            if nCode == 0:
                kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = int(kb.vkCode)
                flags = int(kb.flags)
                inyectada = bool(flags & LLKHF_INJECTED)
                if inyectada and not self.permitir_inyectadas:
                    pass
                elif wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    if vk == VK_ESCAPE:
                        self.terminado = True
                        usuario32.PostQuitMessage(0)
                        return 1
                    if self.terminado:
                        return 1
                    if vk not in self._presionadas:
                        self._presionadas.add(vk)
                        self.teclas.append({
                            "vk": vk,
                            "scan": int(kb.scanCode),
                            "ext": bool(flags & LLKHF_EXTENDED),
                            "t": round(time.perf_counter() - self._t0, 4),
                            "nombre": nombre_de(vk),
                        })
                        if self.limite and len(self.teclas) >= self.limite:
                            self.terminado = True
                            usuario32.PostQuitMessage(0)
                elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                    self._presionadas.discard(vk)
            return usuario32.CallNextHookEx(None, nCode, wParam, lParam)

        self._proc = HOOKPROC(_proc)  # mantener referencia viva
        self._hook = usuario32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._proc, kernel32.GetModuleHandleW(None), 0)
        return bool(self._hook)

    def correr(self):
        """Bombea mensajes hasta que llegue ESC (o se alcance el limite)."""
        msg = wt.MSG()
        while usuario32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            usuario32.TranslateMessage(ctypes.byref(msg))
            usuario32.DispatchMessageW(ctypes.byref(msg))

    def quitar(self):
        if self._hook:
            usuario32.UnhookWindowsHookEx(self._hook)
            self._hook = None
