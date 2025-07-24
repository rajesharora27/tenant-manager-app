@echo off
REM SSE Tenant Manager - Windows Startup Script

echo Starting SSE Tenant Manager...
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please create a .env file with your SSE API credentials.
    echo See README.md for configuration details.
    echo.
    pause
    exit /b 1
)

REM Start the Flask application
echo.
echo Starting Flask application on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause
