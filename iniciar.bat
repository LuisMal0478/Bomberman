@echo off
title Bomberman
echo Iniciando Bomberman...
python main.py
if errorlevel 1 (
    echo.
    echo Ocurrio un error al ejecutar el juego.
    pause
)

