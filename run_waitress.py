#!/usr/bin/env python3
"""
Production server launcher using Waitress for Windows compatibility.
"""
import os
import sys
from waitress import serve

# Ensure we can import our app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    print("Starting SSE Tenant Manager with Waitress...")
    print("Server running on http://0.0.0.0:5000")
    print("Press Ctrl+C to stop")
    serve(app, host='0.0.0.0', port=5000, threads=4)
except ImportError as e:
    print(f"Error importing app: {e}")
    print("Please ensure app.py is in the current directory")
    sys.exit(1)
except KeyboardInterrupt:
    print("\nServer stopped by user")
    sys.exit(0)
