@echo off
chcp 65001 >nul
cd /d "%~dp0"
title PASO 1 - GRABAR secuencia del piano
py -X utf8 grabar.py
echo.
pause
