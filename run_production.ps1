# Production management script for Windows (PowerShell)
# Usage: .\run_production.ps1 {start|stop|restart|status}
# SSE Tenant Manager

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Action
)

$AppName = "tenant-manager-app"
$PidFile = "logs\app.pid"
$LogDir = "logs"
$AccessLog = "$LogDir\access.log"
$ErrorLog = "$LogDir\error.log"

# Set production environment
$env:FLASK_ENV = "production"
$env:FLASK_APP = "app.py"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

function Write-Status {
    param([string]$Message)
    Write-ColorOutput "[STATUS] $Message" "Cyan"
}

# Setup environment function
function Setup-Environment {
    # Create necessary directories
    if (!(Test-Path "flask_session")) { 
        New-Item -ItemType Directory -Name "flask_session" | Out-Null
    }
    if (!(Test-Path "logs")) { 
        New-Item -ItemType Directory -Name "logs" | Out-Null
    }

    # Check if virtual environment exists
    if (!(Test-Path "venv")) {
        Write-Info "Creating virtual environment..."
        python -m venv venv
    }

    # Activate virtual environment
    Write-Info "Activating virtual environment..."
    & ".\venv\Scripts\Activate.ps1"

    # Install/upgrade dependencies
    Write-Info "Installing/updating dependencies..."
    pip install -r requirements.txt | Out-Null

    # Check if .env file exists
    if (!(Test-Path ".env")) {
        Write-Warning ".env file not found!"
        Write-Warning "Please create a .env file with your SSE API credentials."
        Write-Warning "See README.md for configuration details."
    }
}

# Check if app is running
function Test-AppRunning {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
            return $true
        } else {
            # PID file exists but process is dead, clean it up
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
            return $false
        }
    }
    return $false
}

# Start the application
function Start-App {
    if (Test-AppRunning) {
        $pid = Get-Content $PidFile
        Write-Warning "$AppName is already running (PID: $pid)"
        return $false
    }

    Write-Info "Setting up environment..."
    Setup-Environment

    Write-Info "Starting $AppName in background..."
    
    try {
        # Start the application in background
        $process = Start-Process -FilePath "python" -ArgumentList "run_waitress.py" -NoNewWindow -PassThru -RedirectStandardOutput $AccessLog -RedirectStandardError $ErrorLog
        
        # Save PID
        $process.Id | Out-File $PidFile
        
        # Wait a moment and check if it started successfully
        Start-Sleep -Seconds 2
        
        if (Test-AppRunning) {
            Write-Info "$AppName started successfully (PID: $($process.Id))"
            Write-Info "Application is available at: http://localhost:5000"
            Write-Info "Access log: $AccessLog"
            Write-Info "Error log: $ErrorLog"
            return $true
        } else {
            Write-Error "Failed to start $AppName"
            return $false
        }
    } catch {
        Write-Error "Failed to start $AppName: $($_.Exception.Message)"
        return $false
    }
}

# Stop the application
function Stop-App {
    if (!(Test-AppRunning)) {
        Write-Warning "$AppName is not running"
        return $false
    }

    $pid = Get-Content $PidFile
    Write-Info "Stopping $AppName (PID: $pid)..."
    
    try {
        # Try graceful shutdown first
        Stop-Process -Id $pid -Force -ErrorAction Stop
        
        # Wait for process to stop
        $count = 0
        while ((Test-AppRunning) -and ($count -lt 10)) {
            Start-Sleep -Seconds 1
            $count++
        }
        
        # Clean up PID file
        if (Test-Path $PidFile) {
            Remove-Item $PidFile -Force
        }
        
        if (!(Test-AppRunning)) {
            Write-Info "$AppName stopped successfully"
            return $true
        } else {
            Write-Error "Failed to stop $AppName"
            return $false
        }
    } catch {
        Write-Error "Failed to stop $AppName: $($_.Exception.Message)"
        return $false
    }
}

# Restart the application
function Restart-App {
    Write-Info "Restarting $AppName..."
    Stop-App | Out-Null
    Start-Sleep -Seconds 2
    Start-App
}

# Show application status
function Get-AppStatus {
    if (Test-AppRunning) {
        $pid = Get-Content $PidFile
        Write-Status "$AppName is running (PID: $pid)"
        Write-Status "Application URL: http://localhost:5000"
        Write-Status "Access log: $AccessLog"
        Write-Status "Error log: $ErrorLog"
        
        # Show process details
        Write-Host ""
        Write-Status "Process details:"
        try {
            Get-Process -Id $pid | Format-Table Id, ProcessName, CPU, WorkingSet, StartTime -AutoSize
        } catch {
            Write-Warning "Cannot retrieve process details"
        }
        return $true
    } else {
        Write-Status "$AppName is not running"
        return $false
    }
}

# Show usage information
function Show-Usage {
    Write-Host "Usage: .\run_production.ps1 {start|stop|restart|status}"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  start   - Start the application in background"
    Write-Host "  stop    - Stop the application"
    Write-Host "  restart - Restart the application"
    Write-Host "  status  - Show application status"
    Write-Host ""
    Write-Host "The application will run in the background and persist after terminal exit."
    Write-Host "Access logs: $AccessLog"
    Write-Host "Error logs: $ErrorLog"
}

# Main script logic
switch ($Action) {
    "start" {
        $result = Start-App
        if ($result) { exit 0 } else { exit 1 }
    }
    "stop" {
        $result = Stop-App
        if ($result) { exit 0 } else { exit 1 }
    }
    "restart" {
        $result = Restart-App
        if ($result) { exit 0 } else { exit 1 }
    }
    "status" {
        $result = Get-AppStatus
        if ($result) { exit 0 } else { exit 1 }
    }
    default {
        Show-Usage
        exit 1
    }
}
