#!/bin/bash

echo "============================================"
echo "  KCL Ticketing System - First Time Setup"
echo "============================================"
echo ""

echo "[1/4] Checking Prerequisites..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERROR] Python is not installed!"
    echo "Please install Python 3.8+ from: https://www.python.org/downloads/"
    exit 1
fi
echo "  ✓ Python found"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed!"
    echo "Please install Node.js 14+ from: https://nodejs.org/"
    exit 1
fi
echo "  ✓ Node.js found"

# Check if Ollama is installed
OLLAMA_INSTALLED=0
if ! command -v ollama &> /dev/null; then
    echo "[WARNING] Ollama is not installed!"
    echo ""
    echo "The AI Chatbot feature requires Ollama."
    echo ""
    echo "Please install Ollama:"
    echo "  1. Download from: https://ollama.ai/download"
    echo "  2. Install the application"
    echo "  3. Re-run this setup script"
    echo ""
    echo "Press any key to continue WITHOUT AI Chatbot support..."
    read -n 1 -s
    echo ""
else
    echo "  ✓ Ollama found"
    OLLAMA_INSTALLED=1
fi
echo ""

echo "[2/4] Setting up Backend..."
echo "Installing Python dependencies..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
else
    PYTHON_CMD=python
    PIP_CMD=pip
fi

$PIP_CMD install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install Python dependencies!"
    exit 1
fi

echo "Running database migrations..."
$PYTHON_CMD manage.py migrate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to run database migrations!"
    exit 1
fi
echo "Backend setup complete!"
echo ""

echo "[3/4] Setting up Frontend..."
cd frontend
echo "Installing Node.js dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install Node.js dependencies!"
    cd ..
    exit 1
fi
cd ..
echo "Frontend setup complete!"
echo ""

if [ $OLLAMA_INSTALLED -eq 1 ]; then
    echo "[4/4] Setting up AI Chatbot (Ollama)..."
    echo "Checking for llama2 model..."
    if ! ollama list | grep -q "llama2"; then
        echo "  Model not found. Downloading llama2 model (~4GB, this may take several minutes)..."
        ollama pull llama2
        if [ $? -ne 0 ]; then
            echo "[WARNING] Failed to download llama2 model."
            echo "You can download it later by running: ollama pull llama2"
        else
            echo "  ✓ llama2 model downloaded successfully"
        fi
    else
        echo "  ✓ llama2 model already installed"
    fi
    echo ""
    echo "Testing Ollama..."
    if ollama run llama2 "Hi" &> /dev/null; then
        echo "  ✓ Ollama is working correctly"
    else
        echo "[WARNING] Ollama test failed. The AI Chatbot may not work."
    fi
    echo "AI Chatbot setup complete!"
else
    echo "[4/4] Skipping AI Chatbot setup (Ollama not installed)"
fi
echo ""

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "To start the application:"
echo "  Run ./start-all.sh to launch both servers."
echo ""
if [ $OLLAMA_INSTALLED -eq 0 ]; then
    echo "NOTE: AI Chatbot is disabled. Install Ollama to enable it:"
    echo "  https://ollama.ai/download"
    echo ""
fi
