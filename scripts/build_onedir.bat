@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ============================================================================
REM  MimiControl Studio - PyInstaller onedir build-script
REM  Mennens.Tech
REM ============================================================================
REM
REM  GEBRUIK:
REM    Dubbelklik dit bestand. Output verschijnt in ..\releases\MimiControl Studio\
REM
REM  VERSCHIL --onedir vs --onefile:
REM    --onedir:  Bouwt een MAP met de .exe en alle dependencies. Start sneller
REM               op en is makkelijker te debuggen.
REM    --onefile: Bouwt een enkele .exe. Handig voor distributie, maar start
REM               trager op.
REM
REM  De hele map kun je kopiëren naar een andere PC om de app te gebruiken.
REM ============================================================================

set "SCRIPTDIR=%~dp0"
set "PROJECTDIR=%SCRIPTDIR%.."
cd /d "%PROJECTDIR%"

echo.
echo [MimiControl Studio] PyInstaller onedir build
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
if not exist "app\face_landmarker.task" (
    echo [WAARSCHUWING] app\face_landmarker.task niet gevonden.
)

echo.
echo [INFO] Build starten...
echo.

if exist "app\face_landmarker.task" (
    python -m PyInstaller --onedir ^
        --windowed ^
        --name "MimiControl Studio" ^
        --distpath "releases" ^
        --icon "app\assets\mimicontrol.ico" ^
        --add-data "app\face_landmarker.task;." ^
        --add-data "app\assets\logo_mennens.png;assets" ^
        --add-data "app\assets\mimicontrol.ico;assets" ^
        --add-data "%CTK_PATH%;customtkinter" ^
        --additional-hooks-dir hooks ^
        --collect-all mediapipe ^
        --copy-metadata mediapipe ^
        --hidden-import customtkinter ^
        --hidden-import mediapipe ^
        --hidden-import mediapipe.tasks.c ^
        --hidden-import mediapipe.tasks.python ^
        --hidden-import mediapipe.tasks.python.core.mediapipe_c_bindings ^
        --hidden-import mediapipe.tasks.python.vision ^
        --hidden-import cv2 ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import PIL._tkinter_finder ^
        --hidden-import pyautogui ^
        --hidden-import paths ^
        app\mimiexplorer_ctk.py
) else (
    python -m PyInstaller --onedir ^
        --windowed ^
        --name "MimiControl Studio" ^
        --distpath "releases" ^
        --icon "app\assets\mimicontrol.ico" ^
        --add-data "app\assets\logo_mennens.png;assets" ^
        --add-data "app\assets\mimicontrol.ico;assets" ^
        --add-data "%CTK_PATH%;customtkinter" ^
        --additional-hooks-dir hooks ^
        --collect-all mediapipe ^
        --copy-metadata mediapipe ^
        --hidden-import customtkinter ^
        --hidden-import mediapipe ^
        --hidden-import mediapipe.tasks.c ^
        --hidden-import mediapipe.tasks.python ^
        --hidden-import mediapipe.tasks.python.core.mediapipe_c_bindings ^
        --hidden-import mediapipe.tasks.python.vision ^
        --hidden-import cv2 ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import PIL._tkinter_finder ^
        --hidden-import pyautogui ^
        --hidden-import paths ^
        app\mimiexplorer_ctk.py
)

if errorlevel 1 (
    echo.
    echo [FOUT] Build mislukt.
    pause
    exit /b 1
)

REM Hulp-bestanden voor distributie naar andere PC's
copy /Y "%SCRIPTDIR%onedir_launcher.bat" "releases\MimiControl Studio\Start MimiControl Studio.bat" >nul
copy /Y "%SCRIPTDIR%onedir_controleer.bat" "releases\MimiControl Studio\Controleer installatie.bat" >nul

REM Zip voor betrouwbare overdracht (voorkomt incomplete kopieen)
if exist "releases\MimiControl-Studio-onedir.zip" del "releases\MimiControl-Studio-onedir.zip"
powershell -NoProfile -Command "Compress-Archive -Path 'releases\MimiControl Studio' -DestinationPath 'releases\MimiControl-Studio-onedir.zip' -Force" 2>nul

echo.
echo ============================================================
echo [KLAAR] Build voltooid!
echo ============================================================
echo.
echo Output staat in: %CD%\releases\MimiControl Studio\
echo Zip voor andere PC: %CD%\releases\MimiControl-Studio-onedir.zip
echo.
echo DISTRIBUTIE NAAR ANDERE PC:
echo   1. Kopieer het ZIP-bestand OF de hele map "MimiControl Studio"
echo   2. Pak uit / plaats op doel-PC (niet alleen de .exe!)
echo   3. Draai eerst "Controleer installatie.bat"
echo   4. Start via "Start MimiControl Studio.bat"
echo.
echo Bij DLL-fout: installeer VC++ Redistributable x64:
echo   https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.
pause
