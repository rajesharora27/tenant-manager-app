@echo off
REM Production startup script for Windows

REM Set production environment
set FLASK_ENV=production
set FLASK_APP=app.py

REM Create necessary directories
if not exist "flask_session" mkdir flask_session
if not exist "logs" mkdir logs

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
pip install -r requirements.txt

REM Start the application with Waitress (Windows-compatible WSGI server)
echo Starting SSE Tenant Manager in production mode...
python run_waitress.py

pause
