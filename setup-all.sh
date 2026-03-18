#!/bin/bash

echo "============================================"
echo "  KCL Ticketing System - First Time Setup"
echo "============================================"
echo ""

echo "[1/3] Checking Prerequisites..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERROR] Python is not installed!"
    echo "Please install Python 3.8+ from: https://www.python.org/downloads/"
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

# Check if Python version is at least 3.8
if ! $PYTHON_CMD -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" &> /dev/null; then
    echo "[ERROR] Python 3.8+ is required, but an older version is installed!"
    echo "Please install Python 3.8+ from: https://www.python.org/downloads/"
    exit 1
fi
echo "  ✓ Python 3.8+ found"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed!"
    echo "Please install Node.js 14+ from: https://nodejs.org/"
    exit 1
fi
echo "  ✓ Node.js found"

echo ""

echo "[2/3] Setting up Backend..."
echo "Installing Python dependencies..."

$PYTHON_CMD -m pip install -r requirements.txt
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

echo "[3/3] Setting up Frontend..."
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

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "To start the application:"
echo "  Run ./start-all.sh to launch both servers."
echo ""
