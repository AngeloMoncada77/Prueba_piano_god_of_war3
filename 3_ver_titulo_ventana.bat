@echo off
chcp 65001 >nul
cd /d "%~dp0"
title VER TITULO de la ventana del juego
py -X utf8 titulo_ventana.py
echo.
pause
