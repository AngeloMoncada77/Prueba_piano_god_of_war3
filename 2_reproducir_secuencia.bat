@echo off
chcp 65001 >nul
cd /d "%~dp0"
title PASO 2 - PIANO DE PANDORA (modo ritmo)
py -X utf8 reproducir_ritmo.py
echo.
pause
