@echo off
title Subir Bomberman a GitHub
color 0A
echo ========================================================
echo       SUBIR PROYECTO BOMBERMAN A GITHUB PARA RAILWAY
echo ========================================================
echo.
echo 1. Crea un repositorio vacio en https://github.com/new
echo 2. Copia la URL de tu repositorio (ejemplo: https://github.com/tu_usuario/tu_repo.git)
echo.
set /p REPO_URL="Pega aqui la URL de tu repositorio de GitHub: "

if "%REPO_URL%"=="" (
    echo No ingresaste ninguna URL. Operacion cancelada.
    pause
    exit /b
)

echo.
echo Vinculando con GitHub y subiendo archivos...
git remote remove origin 2>nul
git remote add origin %REPO_URL%
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo Ocurrio un error al subir. Verifica tus credenciales o permisos de GitHub.
) else (
    echo.
    echo ========================================================
    echo  ¡PROYECTO SUBIDO CON EXITO A GITHUB!
    echo ========================================================
    echo Ya puedes ir a https://railway.app y desplegar tu repositorio.
)
pause
