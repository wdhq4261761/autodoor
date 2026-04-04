@echo off
chcp 65001 >nul
echo ========================================
echo   AutoDoor Standard Build Script
echo   Input Method: PyAutoGUI
echo ========================================
echo.

set AUTODOOR_USE_DD=0

if exist "build" rmdir /s /q "build"
if exist "dist\autodoor" rmdir /s /q "dist\autodoor"

echo [1/3] Checking dependencies...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [2/3] Building standard version...
pyinstaller autodoor.spec --noconfirm

echo.
echo [3/3] Build complete!
echo.
echo Output: dist\autodoor\
echo Input Method: PyAutoGUI (Standard)
echo.
pause
