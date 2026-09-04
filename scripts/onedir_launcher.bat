@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "_internal\python310.dll" (
    echo.
    echo [FOUT] Installatie incompleet!
    echo.
    echo Het bestand _internal\python310.dll ontbreekt.
    echo Kopieer de HELE map "MimiControl Studio" naar deze PC,
    echo of pak MimiControl-Studio-onedir.zip volledig uit.
    echo.
    pause
    exit /b 1
)

REM Fallback: zorg dat Windows DLLs in _internal kan vinden
set "PATH=%~dp0_internal;%PATH%"

start "" "%~dp0MimiControl Studio.exe"
