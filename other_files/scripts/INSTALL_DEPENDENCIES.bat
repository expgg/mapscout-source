@echo off
title Install Dependencies - Google Maps Lead Harvester
chcp 65001 >nul
cd /d "%~dp0\.."
cls

echo ===============================================================================
echo            Google Maps Lead Harvester - Package Installer
echo                    Engineered by Al Hossain Rifat
echo ===============================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [*] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [*] Installing required packages from config\requirements.txt...
python -m pip install -r config\requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Package installation encountered errors.
    pause
    exit /b 1
)

echo.
echo [✓] All dependencies installed successfully!
echo You can now run LAUNCH_SCRAPER.bat to begin harvesting leads.
echo.
pause
