@echo off
chcp 65001 >nul

cd /d "%~dp0"

echo ========================================
echo   AutoDoor - Standard Version
echo   Input Method: PyAutoGUI
echo ========================================
echo.

set AUTODOOR_USE_DD=0

echo Starting AutoDoor with PyAutoGUI...
echo.

python autodoor.py

pause
