@echo off
chcp 65001 >nul
cd /d "%~dp0"
title PASO 3 - PRUEBA DEL RETARDO (calibracion)
py -X utf8 probar_retardo.py
echo.
pause
