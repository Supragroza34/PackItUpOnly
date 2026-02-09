@echo off
echo ============================================
echo   Starting KCL Ticketing System
echo ============================================
echo.
echo Starting Backend (Django) and Frontend (React)...
echo.
echo Backend will run on: http://localhost:8000
echo Frontend will run on: http://localhost:3000
echo.
echo Press Ctrl+C in either window to stop the servers
echo ============================================
echo.

start "Django Backend" cmd /k "python manage.py runserver"
timeout /t 3 /nobreak > nul
start "React Frontend" cmd /k "cd frontend && npm start"

echo.
echo Both servers are starting in separate windows...
echo.
pause
