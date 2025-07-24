# Production startup script for Windows (PowerShell)
# SSE Tenant Manager

Write-Host "Starting SSE Tenant Manager in production mode..." -ForegroundColor Green

# Set production environment
$env:FLASK_ENV = "production"
$env:FLASK_APP = "app.py"

# Create necessary directories
if (!(Test-Path "flask_session")) { New-Item -ItemType Directory -Name "flask_session" }
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Name "logs" }

# Check if virtual environment exists
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install/upgrade dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host ""
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with your SSE API credentials." -ForegroundColor Red
    Write-Host "See README.md for configuration details." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the application with Waitress (Windows-compatible WSGI server)
Write-Host ""
Write-Host "Starting SSE Tenant Manager with Waitress..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python run_waitress.py
