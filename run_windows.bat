@echo off
setlocal

echo ===================================================
echo   Market Trade Alert Light - Windows Launcher
echo ===================================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org and try again.
    pause
    exit /b 1
)

:: Create venv if not exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate

:: Install requirements
if exist "requirements.txt" (
    echo [INFO] Checking dependencies...
    pip install -r requirements.txt
)

:: Run Application
echo [INFO] Starting Application...
python main.py

pause
