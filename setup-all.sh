#!/bin/bash

echo "============================================"
echo "  KCL Ticketing System - First Time Setup"
echo "============================================"
echo ""

echo "[1/2] Setting up Backend..."
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "Running database migrations..."
python manage.py migrate
echo "Backend setup complete!"
echo ""

echo "[2/2] Setting up Frontend..."
cd frontend
echo "Installing Node.js dependencies..."
npm install
cd ..
echo "Frontend setup complete!"
echo ""

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "To start the application:"
echo "  - Windows: Run start-all.bat"
echo "  - Mac/Linux: Run ./start-all.sh"
echo ""
