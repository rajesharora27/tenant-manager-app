@echo off
REM Production management script for Windows
REM Usage: run_production.bat {start|stop|restart|status}

setlocal enabledelayedexpansion

set APP_NAME=tenant-manager-app
set PID_FILE=logs\app.pid
set LOG_DIR=logs
set ACCESS_LOG=%LOG_DIR%\access.log
set ERROR_LOG=%LOG_DIR%\error.log

REM Set production environment
set FLASK_ENV=production
set FLASK_APP=app.py

REM Function to setup environment
:setup_environment
if not exist "flask_session" mkdir flask_session
if not exist "logs" mkdir logs

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo [INFO] Installing/updating dependencies...
pip install -r requirements.txt >nul 2>&1
goto :eof

REM Function to check if app is running
:is_running
if exist "%PID_FILE%" (
    set /p pid=<"%PID_FILE%"
    tasklist /fi "PID eq !pid!" 2>nul | find "!pid!" >nul
    if !errorlevel! equ 0 (
        exit /b 0
    ) else (
        del "%PID_FILE%" 2>nul
        exit /b 1
    )
) else (
    exit /b 1
)

REM Function to start the application
:start_app
call :is_running
if !errorlevel! equ 0 (
    set /p pid=<"%PID_FILE%"
    echo [WARNING] %APP_NAME% is already running ^(PID: !pid!^)
    exit /b 1
)

echo [INFO] Setting up environment...
call :setup_environment

echo [INFO] Starting %APP_NAME% in background...

REM Start application using run_waitress.py in background
start /b python run_waitress.py >nul 2>&1

REM Get the PID of the started process
timeout /t 2 >nul
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe" ^| find /v "PID"') do (
    set "app_pid=%%i"
    set "app_pid=!app_pid:"=!"
)

if defined app_pid (
    echo !app_pid! > "%PID_FILE%"
    echo [INFO] %APP_NAME% started successfully ^(PID: !app_pid!^)
    echo [INFO] Application is available at: http://localhost:5000
    echo [INFO] Access log: %ACCESS_LOG%
    echo [INFO] Error log: %ERROR_LOG%
    exit /b 0
) else (
    echo [ERROR] Failed to start %APP_NAME%
    exit /b 1
)

REM Function to stop the application
:stop_app
call :is_running
if !errorlevel! neq 0 (
    echo [WARNING] %APP_NAME% is not running
    exit /b 1
)

set /p pid=<"%PID_FILE%"
echo [INFO] Stopping %APP_NAME% ^(PID: !pid!^)...

REM Try to terminate the process
taskkill /PID !pid! /F >nul 2>&1

REM Clean up PID file
if exist "%PID_FILE%" del "%PID_FILE%"

REM Verify it's stopped
call :is_running
if !errorlevel! neq 0 (
    echo [INFO] %APP_NAME% stopped successfully
    exit /b 0
) else (
    echo [ERROR] Failed to stop %APP_NAME%
    exit /b 1
)

REM Function to restart the application
:restart_app
echo [INFO] Restarting %APP_NAME%...
call :stop_app
timeout /t 2 >nul
call :start_app
goto :eof

REM Function to show status
:status_app
call :is_running
if !errorlevel! equ 0 (
    set /p pid=<"%PID_FILE%"
    echo [STATUS] %APP_NAME% is running ^(PID: !pid!^)
    echo [STATUS] Application URL: http://localhost:5000
    echo [STATUS] Access log: %ACCESS_LOG%
    echo [STATUS] Error log: %ERROR_LOG%
    
    REM Show process details
    echo.
    echo [STATUS] Process details:
    tasklist /fi "PID eq !pid!" /fo table 2>nul
    exit /b 0
) else (
    echo [STATUS] %APP_NAME% is not running
    exit /b 1
)

REM Function to show usage
:show_usage
echo Usage: %~nx0 {start^|stop^|restart^|status}
echo.
echo Commands:
echo   start   - Start the application in background
echo   stop    - Stop the application
echo   restart - Restart the application
echo   status  - Show application status
echo.
echo The application will run in the background and persist after terminal exit.
echo Access logs: %ACCESS_LOG%
echo Error logs: %ERROR_LOG%
goto :eof

REM Main script logic
if "%1"=="start" (
    call :start_app
) else if "%1"=="stop" (
    call :stop_app
) else if "%1"=="restart" (
    call :restart_app
) else if "%1"=="status" (
    call :status_app
) else (
    call :show_usage
    exit /b 1
)

exit /b %errorlevel%
