#!/bin/bash
# Production management script for Linux/Mac
# Usage: ./run_production.sh {start|stop|restart|status}

APP_NAME="tenant-manager-app"
PID_FILE="logs/app.pid"
LOG_DIR="logs"
ACCESS_LOG="$LOG_DIR/access.log"
ERROR_LOG="$LOG_DIR/error.log"

# Set production environment
export FLASK_ENV=production
export FLASK_APP=app.py

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_status() {
    echo -e "${BLUE}[STATUS]${NC} $1"
}

# Setup function
setup_environment() {
    # Create necessary directories
    mkdir -p flask_session
    mkdir -p logs

    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install/upgrade dependencies
    log_info "Installing/updating dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
}

# Start function
start_app() {
    if is_running; then
        log_warning "$APP_NAME is already running (PID: $(cat $PID_FILE))"
        return 1
    fi

    log_info "Setting up environment..."
    setup_environment

    log_info "Starting $APP_NAME in background..."
    
    # Start Gunicorn in daemon mode
    nohup gunicorn \
        --bind 0.0.0.0:5000 \
        --workers 4 \
        --timeout 120 \
        --daemon \
        --pid $PID_FILE \
        --access-logfile $ACCESS_LOG \
        --error-logfile $ERROR_LOG \
        app:app > /dev/null 2>&1

    # Wait a moment and check if it started successfully
    sleep 2
    if is_running; then
        log_info "$APP_NAME started successfully (PID: $(cat $PID_FILE))"
        log_info "Application is available at: http://localhost:5000"
        log_info "Access log: $ACCESS_LOG"
        log_info "Error log: $ERROR_LOG"
        return 0
    else
        log_error "Failed to start $APP_NAME"
        return 1
    fi
}

# Stop function
stop_app() {
    if ! is_running; then
        log_warning "$APP_NAME is not running"
        return 1
    fi

    local pid=$(cat $PID_FILE)
    log_info "Stopping $APP_NAME (PID: $pid)..."
    
    # Try graceful shutdown first
    kill $pid 2>/dev/null
    
    # Wait for graceful shutdown
    local count=0
    while is_running && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if is_running; then
        log_warning "Graceful shutdown failed, forcing termination..."
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
    
    # Clean up PID file
    if [ -f $PID_FILE ]; then
        rm $PID_FILE
    fi
    
    if ! is_running; then
        log_info "$APP_NAME stopped successfully"
        return 0
    else
        log_error "Failed to stop $APP_NAME"
        return 1
    fi
}

# Restart function
restart_app() {
    log_info "Restarting $APP_NAME..."
    stop_app
    sleep 2
    start_app
}

# Status function
status_app() {
    if is_running; then
        local pid=$(cat $PID_FILE)
        log_status "$APP_NAME is running (PID: $pid)"
        log_status "Application URL: http://localhost:5000"
        log_status "Access log: $ACCESS_LOG"
        log_status "Error log: $ERROR_LOG"
        
        # Show process details
        if command -v ps > /dev/null; then
            echo
            log_status "Process details:"
            ps -p $pid -o pid,ppid,cmd,etime,pcpu,pmem 2>/dev/null || log_warning "Cannot retrieve process details"
        fi
        return 0
    else
        log_status "$APP_NAME is not running"
        return 1
    fi
}

# Check if app is running
is_running() {
    if [ -f $PID_FILE ]; then
        local pid=$(cat $PID_FILE)
        if kill -0 $pid 2>/dev/null; then
            return 0
        else
            # PID file exists but process is dead, clean it up
            rm $PID_FILE
            return 1
        fi
    fi
    return 1
}

# Show usage
show_usage() {
    echo "Usage: $0 {start|stop|restart|status}"
    echo ""
    echo "Commands:"
    echo "  start   - Start the application in background"
    echo "  stop    - Stop the application"
    echo "  restart - Restart the application"
    echo "  status  - Show application status"
    echo ""
    echo "The application will run in the background and persist after terminal exit."
    echo "Access logs: $ACCESS_LOG"
    echo "Error logs: $ERROR_LOG"
}

# Main script logic
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        status_app
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

exit $?
