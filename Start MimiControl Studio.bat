@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  ============================================
echo    MimiControl Studio - Mennens.Tech
echo  ============================================
echo.

echo  Bezig met controleren van dependencies...
echo.
pip install --user -r requirements.txt
if errorlevel 1 (
    echo.
    echo  [FOUT] Dependencies konden niet worden geinstalleerd.
    echo         Controleer uw internetverbinding en Python-installatie.
    echo.
    pause
    exit /b 1
)

echo.
echo  MimiControl Studio wordt gestart...
echo.

where pythonw >nul 2>&1
if errorlevel 1 (
    python mimiexplorer_ctk.py
    if errorlevel 1 (
        echo.
        echo  [FOUT] MimiControl Studio is onverwacht gestopt.
        echo         Er is mogelijk een fout opgetreden.
        echo.
        pause
        exit /b 1
    )
) else (
    start "" pythonw mimiexplorer_ctk.py
)
