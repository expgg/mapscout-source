@echo off
title MapScout v2.5 - Engineered by Al Hossain Rifat
chcp 65001 >nul
cd /d "%~dp0"
cls

echo ===============================================================================
echo                      MapScout v2.5 — Enterprise Edition
echo            Autonomous Google Maps Lead Harvester ^& B2B Engine
echo                         Engineered by Al Hossain Rifat
echo ===============================================================================
echo.

:: 1. Verify Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Auto-check and install dependencies if missing
python -c "import seleniumbase, pandas, requests, rich, bs4" >nul 2>&1
if errorlevel 1 (
    echo [*] Required Python packages not found. Auto-installing now...
    if exist config\requirements.txt (
        python -m pip install -r config\requirements.txt
    ) else (
        python -m pip install seleniumbase pandas requests rich beautifulsoup4 lxml
    )
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies. Please run scripts\INSTALL_DEPENDENCIES.bat manually.
        pause
        exit /b 1
    )
    echo [✓] Packages installed successfully!
    echo.
)

:: 3. Launch the engine (passes any optional command-line arguments)
python main.py %*

if errorlevel 1 (
    echo.
    echo [!] Session stopped or exited.
    pause
)
