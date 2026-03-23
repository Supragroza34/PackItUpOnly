@echo off
cd /d "%~dp0"

echo ============================================
echo   KCL Ticketing System - First Time Setup
echo ============================================
echo.

echo [1/3] Checking Prerequisites...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Python version is at least 3.8
python -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.8+ is required, but an older version is installed!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo   ✓ Python 3.8+ found

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js 14+ from: https://nodejs.org/
    pause
    exit /b 1
)
echo   ✓ Node.js found

echo.

echo [2/3] Setting up Backend...
echo Installing Python dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies!
    pause
    exit /b 1
)
echo Running database migrations...
python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Failed to run database migrations!
    pause
    exit /b 1
)
echo Backend setup complete!
echo.

echo [3/3] Setting up Frontend...
cd frontend
echo Installing Node.js dependencies...
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies!
    cd ..
    pause
    exit /b 1
)
cd ..
echo Frontend setup complete!
echo.

echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo To start the application:
echo   Run 'start-all.bat' to launch both servers.
echo.
pause
