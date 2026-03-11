@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: =============================================================================
:: MimiControl Studio - Build Onefile Executable
:: =============================================================================
::
:: Gebruik:
::   1. Zorg dat face_landmarker.task in deze map staat (download van mediapipe)
::   2. Dubbelklik build_onefile.bat of voer uit in de projectmap
::   3. De .exe verschijnt in dist\MimiControl Studio.exe
::
:: Vereisten: Python met alle dependencies uit requirements.txt
:: =============================================================================

set "SCRIPTDIR=%~dp0"
set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"
cd /d "%SCRIPTDIR%"

echo.
echo [MimiControl Studio] Build-proces gestart...
echo.

:: Controleer of PyInstaller geïnstalleerd is
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [Waarschuwing] PyInstaller niet gevonden. Installeren...
    pip install --user pyinstaller
    if errorlevel 1 (
        echo [Fout] Kon PyInstaller niet installeren.
        pause
        exit /b 1
    )
    echo [OK] PyInstaller geïnstalleerd.
) else (
    echo [OK] PyInstaller gevonden.
)

:: Bepaal CustomTkinter data-pad
for /f "delims=" %%i in ('python -c "import customtkinter; print(customtkinter.__path__[0])" 2^>nul') do set "CTK_PATH=%%i"
if not defined CTK_PATH (
    echo [Fout] Kon CustomTkinter niet vinden. Is customtkinter geïnstalleerd?
    pause
    exit /b 1
)
echo [OK] CustomTkinter data: %CTK_PATH%

:: Bouw de executable
echo.
echo [MimiControl Studio] PyInstaller wordt uitgevoerd...
echo.

if exist "face_landmarker.task" (
    python -m PyInstaller --onefile --windowed --name "MimiControl Studio" ^
        --icon "assets\mimicontrol.ico" ^
        --add-data "face_landmarker.task;." ^
        --add-data "assets\logo_mennens.png;assets" ^
        --add-data "assets\mimicontrol.ico;assets" ^
        --add-data "%CTK_PATH%;customtkinter" ^
        --hidden-import=customtkinter ^
        --hidden-import=mediapipe ^
        --hidden-import=cv2 ^
        --hidden-import=PIL ^
        --hidden-import=PIL._tkinter_finder ^
        --hidden-import=pyautogui ^
        mimiexplorer_ctk.py
) else (
    echo [Waarschuwing] face_landmarker.task niet gevonden. Build zonder model. Plaats het bestand in de map voor volledige functionaliteit.
    echo.
    python -m PyInstaller --onefile --windowed --name "MimiControl Studio" ^
        --icon "assets\mimicontrol.ico" ^
        --add-data "assets\logo_mennens.png;assets" ^
        --add-data "assets\mimicontrol.ico;assets" ^
        --add-data "%CTK_PATH%;customtkinter" ^
        --hidden-import=customtkinter ^
        --hidden-import=mediapipe ^
        --hidden-import=cv2 ^
        --hidden-import=PIL ^
        --hidden-import=PIL._tkinter_finder ^
        --hidden-import=pyautogui ^
        mimiexplorer_ctk.py
)

if errorlevel 1 (
    echo.
    echo [Fout] Build mislukt.
    pause
    exit /b 1
)

echo.
echo [Succes] Build voltooid!
echo    Executable: dist\MimiControl Studio.exe
echo.
pause
