@echo off
title Build MapScout Standalone Executable
chcp 65001 >nul
cd /d "%~dp0\.."
cls

echo ===============================================================================
echo                 MapScout v2.5 — Standalone Executable Builder
echo          Compiles a 1-Click Portable .exe (No Python Required by End-Users)
echo ===============================================================================
echo.

:: 1. Verify Python & PyInstaller
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH!
    pause
    exit /b 1
)

echo [*] Checking PyInstaller installation...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [*] Installing PyInstaller...
    python -m pip install --upgrade setuptools pyinstaller
)

:: 2. Clean previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: 3. Compile standalone single-file binary
echo.
echo [*] Compiling MapScout.exe with PyInstaller... (This may take 1-2 minutes)
pyinstaller --name "MapScout" ^
    --onefile ^
    --clean ^
    --console ^
    --collect-all seleniumbase ^
    --collect-all rich ^
    --collect-all bs4 ^
    --hidden-import "seleniumbase" ^
    --hidden-import "selenium" ^
    --hidden-import "pandas" ^
    --hidden-import "requests" ^
    --hidden-import "rich" ^
    --hidden-import "bs4" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller compilation failed! Check the output above.
    pause
    exit /b 1
)

echo.
echo ===============================================================================
echo [✓] SUCCESS! MapScout.exe has been compiled successfully!
echo Binary Location: dist\MapScout.exe
echo ===============================================================================
echo.
pause
