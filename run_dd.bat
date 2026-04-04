@echo off
chcp 65001 >nul

cd /d "%~dp0"

echo ========================================
echo   AutoDoor - DD Version
echo   Input Method: DD Virtual Keyboard
echo ========================================
echo.

set AUTODOOR_USE_DD=1

if not exist "drivers\DD64.dll" (
    echo ERROR: DD64.dll not found in drivers folder
    echo Current directory: %CD%
    echo Please ensure drivers\DD64.dll exists
    echo.
    pause
    exit /b 1
)

echo Starting AutoDoor with DD Virtual Keyboard...
echo.

python autodoor.py

pause
