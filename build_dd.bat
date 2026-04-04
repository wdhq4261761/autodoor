@echo off
chcp 65001 >nul
echo ========================================
echo   AutoDoor DD Build Script
echo   Input Method: DD Virtual Keyboard
echo ========================================
echo.

set AUTODOOR_USE_DD=1

if not exist "drivers\DD64.dll" (
    echo ERROR: DD64.dll not found
    echo Please put DD64.dll in drivers folder
    echo.
    pause
    exit /b 1
)

if exist "build" rmdir /s /q "build"
if exist "dist\autodoor_dd" rmdir /s /q "dist\autodoor_dd"

echo [1/3] Checking dependencies...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [2/3] Building DD version...
pyinstaller autodoor_dd.spec --noconfirm

echo.
echo [3/3] Build complete!
echo.
echo Output: dist\autodoor_dd\
echo Input Method: DD Virtual Keyboard (DD Version)
echo.
echo NOTE: DD version may be flagged by antivirus software
echo.
pause
