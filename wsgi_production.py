#!/usr/bin/env python3
"""
Production WSGI Configuration for Tenant Manager App
Optimized for deployment at /tenant-manager-app endpoint
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_dir))

# Import the Flask application
from app import app

# Configure for production
app.config.update(
    ENV='production',
    DEBUG=False,
    TESTING=False,
    SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(32).hex())
)

# Configure application for subpath deployment
class PrefixMiddleware:
    """
    WSGI middleware to handle deployment under a URL prefix
    Ensures the app works correctly at /tenant-manager-app endpoint
    """
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix.rstrip('/')

    def __call__(self, environ, start_response):
        if self.prefix and environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
        elif self.prefix and environ['PATH_INFO'] == '/':
            # Redirect root to our app prefix
            status = '302 Found'
            headers = [('Location', self.prefix + '/')]
            start_response(status, headers)
            return [b'']
        return self.app(environ, start_response)

# Wrap the app with prefix middleware for /tenant-manager-app deployment
application = PrefixMiddleware(app, '/tenant-manager-app')

# For gunicorn: this is the WSGI callable
if __name__ == "__main__":
    # For development testing
    app.run(host='0.0.0.0', port=5000, debug=False)
