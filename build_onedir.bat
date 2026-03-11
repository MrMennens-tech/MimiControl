@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ============================================================================
REM  MimiControl Studio - PyInstaller onedir build-script
REM  Mennens.Tech
REM ============================================================================
REM
REM  GEBRUIK:
REM    Dubbelklik dit bestand of voer het uit vanaf de projectmap:
REM      build_onedir.bat
REM
REM  VERSCHIL --onedir vs --onefile:
REM    --onedir: Bouwt een MAP met de .exe en alle dependencies. Start sneller
REM             op, is makkelijker te debuggen (je ziet alle bestanden), en
REM             updates zijn eenvoudiger (alleen gewijzigde bestanden vervangen).
REM    --onefile: Bouwt één grote .exe. Handig voor distributie, maar start
REM              trager (alle bestanden worden eerst uitgepakt) en debugging
REM              is lastiger.
REM
REM  OUTPUT: dist\MimiControl Studio\
REM  De hele map kun je kopiëren naar een andere PC om de app te gebruiken.
REM ============================================================================

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

REM Controleer of PyInstaller geïnstalleerd is
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller niet gevonden. Installeren...
    pip install pyinstaller
    if errorlevel 1 (
        echo [FOUT] PyInstaller kon niet worden geïnstalleerd.
        pause
        exit /b 1
    )
    echo [OK] PyInstaller geïnstalleerd.
) else (
    echo [OK] PyInstaller gevonden.
)

REM Ga naar de map van dit script
cd /d "%~dp0"

REM Bepaal pad naar CustomTkinter (moet mee als data)
for /f "delims=" %%i in ('python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"') do set CTK_PATH=%%i
if "%CTK_PATH%"=="" (
    echo [FOUT] CustomTkinter niet gevonden. Installeer met: pip install customtkinter
    pause
    exit /b 1
)
echo [OK] CustomTkinter pad: %CTK_PATH%

REM Controleer of verplichte data-bestanden bestaan
if not exist "face_landmarker.task" (
    echo [WAARSCHUWING] face_landmarker.task niet gevonden.
    echo             Start de app eenmaal om het model te downloaden, of download het handmatig.
)
set "LOGO_PATH=assets\logo_mennens.png"
if not exist "!LOGO_PATH!" if exist "..\assets\logo_mennens.png" set "LOGO_PATH=..\assets\logo_mennens.png"
if not exist "!LOGO_PATH!" (
    echo [WAARSCHUWING] assets\logo_mennens.png niet gevonden.
)

REM Bouw de --add-data strings (Windows: ; als scheidingsteken)

echo.
echo [INFO] Build starten...
echo.

if exist "face_landmarker.task" (
    pyinstaller --onedir ^
        --windowed ^
        --name "MimiControl Studio" ^
        --add-data "face_landmarker.task;." ^
        --add-data "!LOGO_PATH!;assets" ^
        --add-data "%CTK_PATH%;customtkinter" ^
        --hidden-import customtkinter ^
        --hidden-import mediapipe ^
        --hidden-import mediapipe.tasks.python ^
        --hidden-import mediapipe.tasks.python.vision ^
        --hidden-import cv2 ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import PIL._tkinter_finder ^
        --hidden-import pyautogui ^
        mimiexplorer_ctk.py
) else (
    pyinstaller --onedir ^
        --windowed ^
        --name "MimiControl Studio" ^
        --add-data "!LOGO_PATH!;assets" ^
        --add-data "%CTK_PATH%;customtkinter" ^
        --hidden-import customtkinter ^
        --hidden-import mediapipe ^
        --hidden-import mediapipe.tasks.python ^
        --hidden-import mediapipe.tasks.python.vision ^
        --hidden-import cv2 ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import PIL._tkinter_finder ^
        --hidden-import pyautogui ^
        mimiexplorer_ctk.py
)

if errorlevel 1 (
    echo.
    echo [FOUT] Build mislukt.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [KLAAR] Build voltooid!
echo ============================================================
echo.
echo Output staat in: %CD%\dist\MimiControl Studio\
echo.
echo Je kunt de hele map "MimiControl Studio" kopiëren naar een andere
echo PC om de applicatie te gebruiken - alle benodigde bestanden zitten
echo erin.
echo.
echo Start de app via: MimiControl Studio.exe
echo.
pause
