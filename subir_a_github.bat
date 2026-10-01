@echo off
chcp 65001 > nul
title Subir Enology Data Toolkit a GitHub
echo ========================================================
echo   🍇 SUBIENDO ENOLOGY DATA TOOLKIT A GITHUB
echo   Repositorio: crisgonzalezhWineMaker/enology-data-toolkit
echo ========================================================
cd /d "%~dp0"

echo.
echo Verificando autenticación con GitHub...
gh auth status > nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [!] Es necesario autenticar tu cuenta una sola vez:
    echo     1. Copia el código de 8 dígitos que aparecerá abajo.
    echo     2. Presiona ENTER para abrir GitHub en tu navegador y pégalo.
    echo.
    gh auth login --web -h github.com -p https
    gh auth setup-git
)

echo.
echo Subiendo código al repositorio remoto...
git push -u origin main

echo.
if %errorlevel% equ 0 (
    echo ========================================================
    echo   🎉 ¡PROYECTO SUBIDO CON ÉXITO A GITHUB!
    echo   Visítalo en:
    echo   https://github.com/crisgonzalezhWineMaker/enology-data-toolkit
    echo ========================================================
) else (
    echo.
    echo [X] Ocurrió un inconveniente al subir el repositorio.
)
pause
