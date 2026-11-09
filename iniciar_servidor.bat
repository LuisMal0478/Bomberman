@echo off
title Servidor Bomberman Multijugador
color 0B
echo ========================================================
echo       SERVIDOR DE BOMBERMAN - MULTIJUGADOR LOCAL / NUBE
echo ========================================================
echo.
echo Escuchando en el puerto 5555...
echo.
python server.py --host 0.0.0.0 --port 5555
pause

