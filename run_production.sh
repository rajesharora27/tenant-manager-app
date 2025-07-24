#!/bin/bash
# Production startup script for Linux/Mac

# Set production environment
export FLASK_ENV=production
export FLASK_APP=app.py

# Create necessary directories
mkdir -p flask_session
mkdir -p logs

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
pip install -r requirements.txt

# Start the application with Gunicorn
echo "Starting SSE Tenant Manager in production mode..."
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log app:app
