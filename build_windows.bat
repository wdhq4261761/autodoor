@echo off
REM Set code page to UTF-8
chcp 65001 >nul

echo Starting to build AutoDoor OCR System (Windows version)...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not added to environment variables
    pause
    exit /b 1
)

REM Verify module structure
echo Verifying module structure...
for %%m in (core ui modules input utils) do (
    if exist "%%m" (
        echo [OK] Module '%%m' found
    ) else (
        echo [ERROR] Module '%%m' not found
        pause
        exit /b 1
    )
)

REM Check for existing virtual environment
set VENV_PATH=
if exist ".venv\Scripts\activate.bat" (
    set VENV_PATH=.venv
    echo Found existing virtual environment: .venv
) else if exist "venv\Scripts\activate.bat" (
    set VENV_PATH=venv
    echo Found existing virtual environment: venv
)

REM If no virtual environment found, create one
if "%VENV_PATH%"=="" (
    echo Creating new virtual environment...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    set VENV_PATH=.venv
)

REM Activate virtual environment
echo Activating virtual environment: %VENV_PATH%
call %VENV_PATH%\Scripts\activate.bat

REM Check if pyinstaller is installed
%VENV_PATH%\Scripts\pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing pyinstaller...
    %VENV_PATH%\Scripts\pip install pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to install pyinstaller
        pause
        exit /b 1
    )
)

REM Clean old build files
if exist build (
    echo Cleaning old build files...
    rmdir /s /q build
)
if exist dist (
    echo Cleaning old distribution files...
    rmdir /s /q dist
)

REM Build with PyInstaller, force rebuild
echo Building with PyInstaller...
%VENV_PATH%\Scripts\pyinstaller autodoor.spec --noconfirm --clean
if %ERRORLEVEL% neq 0 (
    echo Error: Build failed
    pause
    exit /b 1
)

REM Verify build output
if exist "dist\autodoor\autodoor.exe" (
    echo [OK] Build successful: autodoor.exe found
    dir "dist\autodoor\autodoor.exe"
) else (
    echo [ERROR] Build failed: autodoor.exe not found
    pause
    exit /b 1
)

echo.
echo Build successful!
echo Executable location: dist\autodoor\autodoor.exe
echo Please copy the entire dist\autodoor directory to the target machine to run
echo.
pause
