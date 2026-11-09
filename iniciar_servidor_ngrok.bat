@echo off
title Servidor Bomberman + ngrok
color 0B
echo ========================================================
echo       SERVIDOR BOMBERMAN + TUNEL NGROK (MULTIJUGADOR)
echo ========================================================
echo.
echo Iniciando servidor en segundo plano...
start "Servidor Bomberman" /min python server.py --host 0.0.0.0 --port 5555

echo.
echo Comprobando si ngrok esta instalado...
where ngrok >nul 2>nul
if errorlevel 1 (
    echo.
    echo [AVISO] ngrok no esta instalado en tu sistema.
    echo Descargalo gratis de: https://ngrok.com/download
    echo Y coloca el archivo ngrok.exe en esta misma carpeta o en el PATH de Windows.
    echo.
    pause
    exit /b
)

echo Iniciando tunel en puerto 5555...
echo Copia la direccion 'tcp://0.tcp.ngrok.io:XXXXX' que aparecera a continuacion
echo y pasasela a tus amigos (sin el 'tcp://').
echo.
ngrok tcp 5555
pause

