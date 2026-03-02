@echo off
cd /d "%~dp0"

echo ============================================
echo   KCL Ticketing System - First Time Setup
echo ============================================
echo.

echo [1/4] Checking Prerequisites...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo   ✓ Python found

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js 14+ from: https://nodejs.org/
    pause
    exit /b 1
)
echo   ✓ Node.js found

REM Check if Ollama is installed
ollama version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama is not installed!
    echo.
    echo The AI Chatbot feature requires Ollama.
    echo.
    echo Please install Ollama:
    echo   1. Download from: https://ollama.ai/download
    echo   2. Install the application
    echo   3. Re-run this setup script
    echo.
    echo Press any key to continue WITHOUT AI Chatbot support...
    pause >nul
    set OLLAMA_INSTALLED=0
) else (
    echo   ✓ Ollama found
    set OLLAMA_INSTALLED=1
)
echo.

echo [2/4] Setting up Backend...
echo Installing Python dependencies...
pip install -r requirements.txt
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

echo [3/4] Setting up Frontend...
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

if %OLLAMA_INSTALLED%==1 (
    echo [4/4] Setting up AI Chatbot ^(Ollama^)...
    echo Checking for llama2 model...
    ollama list | findstr "llama2" >nul 2>&1
    if errorlevel 1 (
        echo   Model not found. Downloading llama2 model ^(~4GB, this may take several minutes^)...
        ollama pull llama2
        if errorlevel 1 (
            echo [WARNING] Failed to download llama2 model.
            echo You can download it later by running: ollama pull llama2
        ) else (
            echo   ✓ llama2 model downloaded successfully
        )
    ) else (
        echo   ✓ llama2 model already installed
    )
    echo.
    echo Testing Ollama...
    ollama run llama2 "Hi" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Ollama test failed. The AI Chatbot may not work.
    ) else (
        echo   ✓ Ollama is working correctly
    )
    echo AI Chatbot setup complete!
) else (
    echo [4/4] Skipping AI Chatbot setup ^(Ollama not installed^)
)
echo.

echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo To start the application:
echo   Run 'start-all.bat' to launch both servers.
echo.
if %OLLAMA_INSTALLED%==0 (
    echo NOTE: AI Chatbot is disabled. Install Ollama to enable it:
    echo   https://ollama.ai/download
    echo.
)
pause
