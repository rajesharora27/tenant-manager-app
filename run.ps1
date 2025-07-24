# SSE Tenant Manager - PowerShell Startup Script

Write-Host "Starting SSE Tenant Manager..." -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}
else {
    Write-Host "Virtual environment not found. Creating one..." -ForegroundColor Yellow
    python -m venv venv
    & "venv\Scripts\Activate.ps1"
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with your SSE API credentials." -ForegroundColor Red
    Write-Host "See README.md for configuration details." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the Flask application
Write-Host ""
Write-Host "Starting Flask application on http://localhost:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    python app.py
}
catch {
    Write-Host "Error starting application: $_" -ForegroundColor Red
}
finally {
    Write-Host ""
    Read-Host "Press Enter to exit"
}
