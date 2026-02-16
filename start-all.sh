#!/bin/bash

echo "============================================"
echo "  Starting KCL Ticketing System"
echo "============================================"
echo ""
echo "Starting Backend (Django) and Frontend (React)..."
echo ""
echo "Backend will run on: http://localhost:8000"
echo "Frontend will run on: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the servers"
echo "============================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start backend in background
echo "Starting Django backend..."
cd "$SCRIPT_DIR"
python manage.py runserver &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "Starting React frontend..."
cd "$SCRIPT_DIR/frontend"
npm start &
FRONTEND_PID=$!

echo ""
echo "Both servers are running!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop both servers, press Ctrl+C or run:"
echo "kill $BACKEND_PID $FRONTEND_PID"

# Wait for user interrupt
wait
