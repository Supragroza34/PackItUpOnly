@echo off
setlocal enabledelayedexpansion

REM Root of the project
cd /d "%~dp0"

echo === Running backend (Django) tests ===

REM Activate virtualenv if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python manage.py test
if errorlevel 1 (
    echo Backend tests failed!
    exit /b 1
)

echo.
echo === Running frontend (React) tests ===
cd frontend

REM Run Jest tests once (no watch mode, CI environment)
set CI=true
call npm test -- --watch=false
if errorlevel 1 (
    echo Frontend tests failed!
    exit /b 1
)

cd ..

echo.
echo All tests completed.
