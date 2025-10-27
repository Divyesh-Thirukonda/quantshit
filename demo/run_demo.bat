@echo off
REM Demo runner script for the arbitrage bot (Windows)
REM This script runs the bot with fake market data

echo Starting Arbitrage Bot Demo...
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Run the demo
python demo\demo_runner.py

REM Deactivate virtual environment
deactivate
