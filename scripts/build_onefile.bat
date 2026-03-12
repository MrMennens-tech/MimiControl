@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: =============================================================================
:: MimiControl Studio - Build Onefile Executable
:: =============================================================================
::
:: Gebruik:
::   1. Dubbelklik build_onefile.bat
::   2. De .exe verschijnt in ..\releases\MimiControl Studio.exe
::
:: Vereisten: Python met alle dependencies uit requirements.txt
:: =============================================================================

set "SCRIPTDIR=%~dp0"
set "PROJECTDIR=%SCRIPTDIR%.."
cd /d "%PROJECTDIR%"

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

:: Maak releases map aan als die niet bestaat
if not exist "releases" mkdir releases

:: Bouw de executable
echo.
echo [MimiControl Studio] PyInstaller wordt uitgevoerd...
echo.

if exist "app\face_landmarker.task" (
    python -m PyInstaller --onefile --windowed --name "MimiControl Studio" ^
        --distpath "releases" ^
        --icon "app\assets\mimicontrol.ico" ^
        --add-data "app\face_landmarker.task;." ^
        --add-data "app\assets\logo_mennens.png;assets" ^
        --add-data "app\assets\mimicontrol.ico;assets" ^
        --add-data "%CTK_PATH%;customtkinter" ^
        --hidden-import=customtkinter ^
        --hidden-import=mediapipe ^
        --hidden-import=cv2 ^
        --hidden-import=PIL ^
        --hidden-import=PIL._tkinter_finder ^
        --hidden-import=pyautogui ^
        app\mimiexplorer_ctk.py
) else (
    echo [Waarschuwing] face_landmarker.task niet gevonden in app\. Build zonder model.
    echo.
    python -m PyInstaller --onefile --windowed --name "MimiControl Studio" ^
        --distpath "releases" ^
        --icon "app\assets\mimicontrol.ico" ^
        --add-data "app\assets\logo_mennens.png;assets" ^
        --add-data "app\assets\mimicontrol.ico;assets" ^
        --add-data "%CTK_PATH%;customtkinter" ^
        --hidden-import=customtkinter ^
        --hidden-import=mediapipe ^
        --hidden-import=cv2 ^
        --hidden-import=PIL ^
        --hidden-import=PIL._tkinter_finder ^
        --hidden-import=pyautogui ^
        app\mimiexplorer_ctk.py
)

if errorlevel 1 (
    echo.
    echo [Fout] Build mislukt.
    pause
    exit /b 1
)

echo.
echo [Succes] Build voltooid!
echo    Executable: releases\MimiControl Studio.exe
echo.
pause
