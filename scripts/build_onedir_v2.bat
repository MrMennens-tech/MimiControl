@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ============================================================================
REM  MimiControl Studio v2 - PyInstaller onedir build-script
REM  Mennens.Tech
REM ============================================================================
REM
REM  GEBRUIK:
REM    Dubbelklik dit bestand. Output verschijnt in
REM    ..\releases\MimiControl Studio v2\
REM
REM  Dit script overschrijft NIET de v1-release:
REM    releases\MimiControl Studio\
REM    releases\MimiControl-Studio-onedir.zip
REM    releases\MimiControl Studio.exe
REM
REM  De hele v2-map kun je kopiëren naar een andere PC (geen Python nodig).
REM  Zipnaam: MimiControl-Studio-v<VERSIE>-onedir.zip; verhoog VERSIE hieronder
REM  per release, dan blijft de vorige zip (bv. v2.1) bewaard.
REM  hooks\hook-mediapipe.py verzorgt collect-all mediapipe (niet ook als vlag).
REM  Uitgesloten (niet nodig, scheelt MB's): scipy, PyQt, sounddevice, pandas.
REM  matplotlib moet blijven: mediapipe importeert het zelf.
REM ============================================================================

set "SCRIPTDIR=%~dp0"
set "VERSIE=2.2"
set "ZIPNAAM=MimiControl-Studio-v%VERSIE%-onedir.zip"
set "PROJECTDIR=%SCRIPTDIR%.."
cd /d "%PROJECTDIR%"

echo.
echo [MimiControl Studio v2] PyInstaller onedir build
echo ------------------------------------------------------------

REM Controleer of Python beschikbaar is
python --version >nul 2>&1
if errorlevel 1 (
    echo [FOUT] Python niet gevonden. Installeer Python of voeg het aan PATH toe.
    pause
    exit /b 1
)

REM Controleer of PyInstaller geïnstalleerd is (via python -m, niet PATH)
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [INFO] PyInstaller niet gevonden. Installeren...
    pip install --user pyinstaller
    if errorlevel 1 (
        echo [FOUT] PyInstaller kon niet worden geïnstalleerd.
        pause
        exit /b 1
    )
    echo [OK] PyInstaller geïnstalleerd.
) else (
    echo [OK] PyInstaller gevonden.
)

REM Bepaal pad naar CustomTkinter
for /f "delims=" %%i in ('python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"') do set CTK_PATH=%%i
if "%CTK_PATH%"=="" (
    echo [FOUT] CustomTkinter niet gevonden. Installeer met: pip install customtkinter
    pause
    exit /b 1
)
echo [OK] CustomTkinter pad: %CTK_PATH%

REM Maak releases map aan
if not exist "releases" mkdir releases

REM Controleer data-bestanden
if not exist "app_v2\face_landmarker.task" (
    echo [WAARSCHUWING] app_v2\face_landmarker.task niet gevonden.
)

echo.
echo [INFO] Build starten...
echo.

if exist "app_v2\face_landmarker.task" (
    python -m PyInstaller --onedir ^
        --noconfirm ^
        --windowed ^
        --exclude-module scipy ^
        --exclude-module PyQt6 ^
        --exclude-module PyQt5 ^
        --exclude-module PySide6 ^
        --exclude-module sounddevice ^
        --exclude-module pandas ^
        --exclude-module IPython ^
        --exclude-module pytest ^
        --name "MimiControl Studio v2" ^
        --distpath "releases" ^
        --icon "app_v2\assets\mimicontrol.ico" ^
        --add-data "app_v2\face_landmarker.task;." ^
        --add-data "app_v2\assets\logo_mennens.png;assets" ^
        --add-data "app_v2\assets\mimicontrol.ico;assets" ^
        --add-data "%CTK_PATH%;customtkinter" ^
        --additional-hooks-dir hooks ^
        --copy-metadata mediapipe ^
        --hidden-import customtkinter ^
        --hidden-import mediapipe ^
        --hidden-import mediapipe.tasks.c ^
        --hidden-import mediapipe.tasks.python ^
        --hidden-import mediapipe.tasks.python.core.mediapipe_c_bindings ^
        --hidden-import mediapipe.tasks.python.vision ^
        --hidden-import cv2 ^
        --hidden-import numpy ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import PIL._tkinter_finder ^
        --hidden-import pyautogui ^
        --hidden-import paths ^
        app_v2\mimiexplorer_ctk.py
) else (
    python -m PyInstaller --onedir ^
        --noconfirm ^
        --windowed ^
        --exclude-module scipy ^
        --exclude-module PyQt6 ^
        --exclude-module PyQt5 ^
        --exclude-module PySide6 ^
        --exclude-module sounddevice ^
        --exclude-module pandas ^
        --exclude-module IPython ^
        --exclude-module pytest ^
        --name "MimiControl Studio v2" ^
        --distpath "releases" ^
        --icon "app_v2\assets\mimicontrol.ico" ^
        --add-data "app_v2\assets\logo_mennens.png;assets" ^
        --add-data "app_v2\assets\mimicontrol.ico;assets" ^
        --add-data "%CTK_PATH%;customtkinter" ^
        --additional-hooks-dir hooks ^
        --copy-metadata mediapipe ^
        --hidden-import customtkinter ^
        --hidden-import mediapipe ^
        --hidden-import mediapipe.tasks.c ^
        --hidden-import mediapipe.tasks.python ^
        --hidden-import mediapipe.tasks.python.core.mediapipe_c_bindings ^
        --hidden-import mediapipe.tasks.python.vision ^
        --hidden-import cv2 ^
        --hidden-import numpy ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import PIL._tkinter_finder ^
        --hidden-import pyautogui ^
        --hidden-import paths ^
        app_v2\mimiexplorer_ctk.py
)

if errorlevel 1 (
    echo.
    echo [FOUT] Build mislukt.
    pause
    exit /b 1
)

REM Hulp-bestanden voor distributie naar andere PC's
copy /Y "%SCRIPTDIR%onedir_launcher_v2.bat" "releases\MimiControl Studio v2\Start MimiControl Studio v2.bat" >nul
copy /Y "%SCRIPTDIR%onedir_controleer_v2.bat" "releases\MimiControl Studio v2\Controleer installatie.bat" >nul

REM Zip alleen v2; raak de v1-zip niet aan.
REM Geen trailing backslash in het pad: 'map\' + quote breekt PowerShell.
if exist "releases\%ZIPNAAM%" del "releases\%ZIPNAAM%"
powershell -NoProfile -Command "Compress-Archive -Path 'releases\MimiControl Studio v2' -DestinationPath 'releases\%ZIPNAAM%' -Force"

if errorlevel 1 (
    echo.
    echo [FOUT] Zip maken mislukt.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [KLAAR] Build v2 voltooid!
echo ============================================================
echo.
echo Output staat in: %CD%\releases\MimiControl Studio v2\
echo Zip voor andere PC: %CD%\releases\%ZIPNAAM%
echo.
echo DISTRIBUTIE NAAR ANDERE PC:
echo   1. Kopieer het ZIP-bestand OF de hele map "MimiControl Studio v2"
echo   2. Pak uit / plaats op doel-PC (niet alleen de .exe!)
echo   3. Start "Start MimiControl Studio v2.bat" of "MimiControl Studio v2.exe"
echo.
echo Optioneel bij problemen: "Controleer installatie.bat"
echo.
echo Bij DLL-fout: installeer VC++ Redistributable x64:
echo   https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.
pause
