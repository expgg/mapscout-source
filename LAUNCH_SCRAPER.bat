@echo off
title MapScout v2.5 - Engineered by Al Hossain Rifat
chcp 65001 >nul
cd /d "%~dp0"
cls

echo ===============================================================================
echo                      MapScout v2.5 -- Enterprise Edition
echo            Autonomous Google Maps Lead Harvester and B2B Engine
echo                         Engineered by Al Hossain Rifat
echo ===============================================================================
echo.

:: 1. Priority: Check if Standalone MapScout.exe exists (Zero Python Required!)
if exist "%~dp0MapScout.exe" (
    echo [*] Standalone MapScout engine detected. Launching directly...
    "%~dp0MapScout.exe" %*
    goto :finish
)

if exist "%~dp0dist\MapScout.exe" (
    echo [*] Standalone MapScout engine detected in dist\. Launching directly...
    "%~dp0dist\MapScout.exe" %*
    goto :finish
)

:: 2. Auto-Detect Python / py launcher / common install paths
set "PY_CMD="

python --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    goto :py_found
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
    goto :py_found
)

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD=%%D\python.exe"
        goto :py_found
    )
)

for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD=%%D\python.exe"
        goto :py_found
    )
)

:py_not_found
echo [!] Python is not installed or not in your system PATH.
echo.
echo [*] Downloading 1-Click Standalone MapScout.exe (~150 MB, no Python needed)...
echo     Source: https://github.com/expgg/mapscout-source/releases/download/v2.5/MapScout.exe
echo.
curl -L -o "%~dp0MapScout.exe" "https://github.com/expgg/mapscout-source/releases/download/v2.5/MapScout.exe"
if exist "%~dp0MapScout.exe" (
    echo [OK] Download complete! Launching MapScout Engine...
    "%~dp0MapScout.exe" %*
    goto :finish
) else (
    echo [ERROR] Failed to download MapScout.exe.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:py_found
:: 3. Auto-check and install dependencies if missing
%PY_CMD% -c "import seleniumbase, pandas, requests, rich, bs4" >nul 2>&1
if errorlevel 1 (
    echo [*] Required Python packages not found. Auto-installing now...
    if exist config\requirements.txt (
        %PY_CMD% -m pip install -r config\requirements.txt
    ) else if exist requirements.txt (
        %PY_CMD% -m pip install -r requirements.txt
    ) else (
        %PY_CMD% -m pip install seleniumbase pandas requests rich beautifulsoup4 lxml
    )
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies. Please run scripts\INSTALL_DEPENDENCIES.bat manually.
        pause
        exit /b 1
    )
    echo [OK] Packages installed successfully!
    echo.
)

:: 4. Launch the engine (passes any optional command-line arguments)
%PY_CMD% main.py %*

:finish
if errorlevel 1 (
    echo.
    echo [!] Session stopped or exited.
    pause
)
