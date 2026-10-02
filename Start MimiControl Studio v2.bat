@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  ============================================
echo    MimiControl Studio v2 - Mennens.Tech
echo    NIEUWE VERSIE — experimentele layout
echo  ============================================
echo.
echo  Dit is de GUI-overhaul naast de bestaande Studio.
echo  De oude versie start u met:  Start MimiControl Studio.bat
echo.

python -c "import customtkinter, mediapipe, cv2, pyautogui" >nul 2>&1
if errorlevel 1 (
    echo  Ontbrekende onderdelen worden geinstalleerd, even geduld...
    echo.
    pip install --user -r requirements.txt
)
python -c "import customtkinter, mediapipe, cv2, pyautogui" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [FOUT] Dependencies konden niet worden geinstalleerd.
    echo         Controleer uw internetverbinding en Python-installatie.
    echo.
    pause
    exit /b 1
)

echo.
echo  MimiControl Studio v2 wordt gestart...
echo.

where pythonw >nul 2>&1
if errorlevel 1 (
    python app_v2\mimiexplorer_ctk.py
    if errorlevel 1 (
        echo.
        echo  [FOUT] MimiControl Studio v2 is onverwacht gestopt.
        echo         Er is mogelijk een fout opgetreden.
        echo.
        pause
        exit /b 1
    )
) else (
    start "" pythonw app_v2\mimiexplorer_ctk.py
)
