@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo MimiControl Studio v2 - installatiecontrole
echo ===========================================
echo.

set "OK=1"

if not exist "MimiControl Studio v2.exe" (
    echo [X] MimiControl Studio v2.exe ontbreekt
    set "OK=0"
) else (
    echo [OK] MimiControl Studio v2.exe
)

if not exist "_internal\python310.dll" (
    echo [X] _internal\python310.dll ontbreekt - KOPIEER DE HELE MAP!
    set "OK=0"
) else (
    echo [OK] _internal\python310.dll
)

if not exist "_internal\VCRUNTIME140.dll" (
    echo [X] _internal\VCRUNTIME140.dll ontbreekt
    set "OK=0"
) else (
    echo [OK] _internal\VCRUNTIME140.dll
)

if not exist "_internal\face_landmarker.task" (
    echo [!] _internal\face_landmarker.task ontbreekt - mimiek werkt mogelijk niet
) else (
    echo [OK] face_landmarker.task
)

for /f %%a in ('dir /s /b "_internal\*.*" 2^>nul ^| find /c /v ""') do set "AANTAL=%%a"
echo.
echo Bestanden in _internal: %AANTAL%
if %AANTAL% LSS 100 (
    echo [!] Te weinig bestanden - installatie waarschijnlijk incompleet
    echo     Verwacht: honderden bestanden ^(~300 MB^)
    set "OK=0"
)

echo.
if "%OK%"=="0" (
    echo RESULTAAT: INSTALLATIE ONVOLLEDIG
    echo.
    echo Tip: gebruik MimiControl-Studio-v2-onedir.zip en pak alles uit.
    echo Niet alleen de .exe kopieren!
) else (
    echo RESULTAAT: Installatie lijkt compleet.
    echo.
    echo Start via "Start MimiControl Studio v2.bat"
    echo.
    echo Blijft de app crashen? Installeer op deze PC:
    echo Visual C++ Redistributable 2015-2022 ^(x64^):
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
)

echo.
pause
