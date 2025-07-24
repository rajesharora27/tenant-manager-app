"""
SSE Tenant Manager Web Application
A Flask-based web app for managing Cisco SSE tenants
"""

import os
import requests
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
# from flask_session import Session  # Disabled due to compatibility issues
from dotenv import load_dotenv
import logging
import urllib3

# Disable SSL warnings when verification is disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv('.env', override=True)

app = Flask(__name__)

# Configure secure secret key
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    # Generate a secure random key for development
    secret_key = os.urandom(32).hex()
    print("WARNING: Using auto-generated SECRET_KEY. For production, set SECRET_KEY in .env file")
elif len(secret_key) < 16:
    print("WARNING: SECRET_KEY is too short. Use at least 16 characters for security")

app.secret_key = secret_key

# Configure Flask sessions (using built-in Flask sessions for better compatibility)
app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SEND_FILE_MAX_AGE_DEFAULT=timedelta(hours=1)
)

# Note: Using built-in Flask sessions instead of Flask-Session extension
# to avoid compatibility issues with newer Werkzeug versions

# Configure logging
log_level = logging.INFO if os.environ.get('FLASK_ENV') == 'production' else logging.DEBUG
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def require_auth(f):
    """Decorator to require authentication for routes"""
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            logger.warning("Unauthenticated access attempt")
            flash('Please authenticate first', 'warning')
            return redirect(url_for('authenticate'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

class SSEAPIClient:
    """API Client for Cisco SSE Tenant Management"""
    
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'https://api.sse.cisco.com/')
        self.username = os.getenv('USERNAME')
        self.password = os.getenv('PASSWORD')
        self.token_url = os.getenv('TOKEN_URL', 'https://api.sse.cisco.com/auth/v2/token')
        self.verify_ssl = os.getenv('VERIFY_SSL', 'true').lower() == 'true'
        self.access_token = None
        self.token_expires_at = None
        
        if not self.base_url.endswith('/'):
            self.base_url += '/'
    
    def _get_basic_auth_header(self):
        """Generate Basic Authentication header"""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    def is_token_valid(self):
        """Check if current token is still valid"""
        if not self.access_token or not self.token_expires_at:
            return False
        return datetime.now() < self.token_expires_at - timedelta(minutes=5)
    
    def authenticate(self):
        """Authenticate and get access token"""
        if self.is_token_valid():
            logger.info("Using existing valid token")
            return True, "Using existing authentication token"
        
        try:
            headers = {
                'Authorization': self._get_basic_auth_header(),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {'grant_type': 'client_credentials'}
            
            logger.info(f"Authenticating with {self.token_url}")
            response = requests.post(self.token_url, headers=headers, data=data, 
                                   timeout=30, verify=self.verify_ssl)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info(f"Authentication successful! Token expires in {expires_in} seconds")
                return True, "Authentication successful"
            elif response.status_code == 429:
                error_msg = "Rate limit exceeded. Please wait before trying again."
                logger.error(error_msg)
                return False, error_msg
            else:
                error_msg = f"Authentication failed: {response.status_code}"
                logger.error(error_msg)
                return False, error_msg
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.is_token_valid():
            success, message = self.authenticate()
            if not success:
                raise Exception(f"Authentication failed: {message}")
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make authenticated API request"""
        self._ensure_authenticated()
        
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        headers.setdefault('Content-Type', 'application/json')
        
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        
        try:
            response = requests.request(
                method, url, headers=headers, verify=self.verify_ssl, 
                timeout=30, **kwargs
            )
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise
    
    def get_tenants(self):
        """Fetch all tenants"""
        try:
            response = self._make_request('GET', '/admin/v2/tenants')
            
            if response.status_code == 200:
                data = response.json()
                # Handle different response formats: data.data, data.tenants, or data directly
                if isinstance(data, dict):
                    tenants = data.get('data', data.get('tenants', []))
                else:
                    tenants = data  # API returns list directly
                logger.info(f"Successfully fetched {len(tenants)} tenants")
                return True, tenants
            else:
                error_msg = f"Failed to fetch tenants: {response.status_code}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error fetching tenants: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_tenant(self, tenant_id):
        """Fetch single tenant"""
        try:
            response = self._make_request('GET', f'/admin/v2/tenants/{tenant_id}')
            
            if response.status_code == 200:
                tenant = response.json()
                logger.info(f"Successfully fetched tenant {tenant_id}")
                return True, tenant
            else:
                error_msg = f"Failed to fetch tenant: {response.status_code}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error fetching tenant: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def create_tenant(self, tenant_data):
        """Create new tenant"""
        try:
            response = self._make_request('POST', '/admin/v2/tenants', json=tenant_data)
            
            if response.status_code in [200, 201]:
                tenant = response.json()
                logger.info(f"Successfully created tenant {tenant.get('id', tenant.get('organizationId', 'unknown'))}")
                return True, tenant
            else:
                error_msg = f"Failed to create tenant: {response.status_code}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error creating tenant: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def update_tenant(self, tenant_id, tenant_data):
        """Update existing tenant"""
        try:
            # Transform data for update API which has different field names
            update_data = {}
            
            # Copy basic fields that are the same
            for field in ['name', 'seats', 'comments', 'city', 'state', 'zipCode', 'countryCode', 'addressLine1', 'addressLine2']:
                if field in tenant_data:
                    update_data[field] = tenant_data[field]
            
            # Transform admin email fields for update API
            admin_emails = []
            if 'primaryAdminEmail' in tenant_data:
                admin_emails.append(tenant_data['primaryAdminEmail'])
            if 'extraAdminEmails' in tenant_data:
                admin_emails.extend(tenant_data['extraAdminEmails'])
            
            if admin_emails:
                update_data['adminEmails'] = admin_emails
            
            response = self._make_request('PUT', f'/admin/v2/tenants/{tenant_id}', json=update_data)
            
            if response.status_code == 200:
                tenant = response.json()
                logger.info(f"Successfully updated tenant {tenant_id}")
                return True, tenant
            elif response.status_code == 400:
                # Check if the error is about unsupported adminEmails field
                try:
                    error_detail = response.json()
                    if 'adminEmails' in error_detail.get('message', ''):
                        logger.warning(f"adminEmails field not supported for this org, retrying without it")
                        # Remove adminEmails and try again
                        update_data_without_emails = {k: v for k, v in update_data.items() if k != 'adminEmails'}
                        
                        response = self._make_request('PUT', f'/admin/v2/tenants/{tenant_id}', json=update_data_without_emails)
                        
                        if response.status_code == 200:
                            tenant = response.json()
                            logger.info(f"Successfully updated tenant {tenant_id} (without adminEmails)")
                            return True, tenant
                except:
                    pass
                
                error_msg = f"Failed to update tenant: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                logger.error(error_msg)
                return False, error_msg
            else:
                error_msg = f"Failed to update tenant: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error updating tenant: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def delete_tenant(self, tenant_id):
        """Delete single tenant using the multiple delete endpoint"""
        try:
            # Use the multiple delete endpoint with a single ID
            response = self._make_request('DELETE', f'/admin/v2/tenants?organizationIds={tenant_id}')
            
            if response.status_code in [200, 202, 204]:
                logger.info(f"Successfully deleted tenant {tenant_id}")
                return True, "Tenant deleted successfully"
            else:
                error_msg = f"Failed to delete tenant: {response.status_code}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error deleting tenant: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def delete_multiple_tenants(self, tenant_ids):
        """Delete multiple tenants"""
        try:
            # Use query parameters as per the API specification
            ids_param = ','.join(tenant_ids)
            response = self._make_request('DELETE', f'/admin/v2/tenants?organizationIds={ids_param}')
            
            if response.status_code in [200, 202, 204]:
                logger.info(f"Successfully deleted {len(tenant_ids)} tenants")
                return True, f"Successfully deleted {len(tenant_ids)} tenants"
            else:
                error_msg = f"Failed to delete tenants: {response.status_code}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error deleting tenants: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

# Initialize API client
api_client = SSEAPIClient()

# Jinja2 filters
def render_extra_admin_emails(value):
    """Render extraAdminEmails as a comma-separated string"""
    if value is None:
        return ''
    if isinstance(value, list):
        return ', '.join([str(e).strip() for e in value if str(e).strip()])
    if isinstance(value, str):
        return value.strip()
    return str(value)

app.jinja_env.filters['render_extra_admin_emails'] = render_extra_admin_emails

@app.before_request
def load_session():
    """Ensure session persistence"""
    if not session.get('_id'):
        session['_id'] = os.urandom(16).hex()
    session.permanent = True

@app.route('/')
@require_auth
def index():
    """Dashboard with overview"""
    return render_template('index.html')

@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    """Authentication page"""
    config_data = {
        'BASE_URL': os.getenv('BASE_URL', 'https://api.sse.cisco.com/'),
        'TOKEN_URL': os.getenv('TOKEN_URL', 'https://api.sse.cisco.com/auth/v2/token'),
        'USERNAME': os.getenv('USERNAME', ''),
        'VERIFY_SSL': os.getenv('VERIFY_SSL', 'true')
    }

    if request.method == 'POST':
        # Update environment with user input
        for key in ['BASE_URL', 'TOKEN_URL', 'USERNAME', 'PASSWORD', 'VERIFY_SSL']:
            value = request.form.get(key)
            if value:
                os.environ[key] = value
                if key != 'PASSWORD':
                    config_data[key] = value

        # Re-initialize API client
        global api_client
        api_client = SSEAPIClient()

        success, message = api_client.authenticate()
        logger.info(f"Authentication result: success={success}")

        if success:
            session.permanent = True
            session['authenticated'] = True
            session['auth_time'] = datetime.now().isoformat()
            flash(f'✅ {message}', 'success')
            return redirect(url_for('index'))
        else:
            flash(f'❌ {message}', 'error')

    return render_template('authenticate.html', config=config_data)

@app.route('/tenants')
@require_auth
def list_tenants():
    """List all tenants"""
    success, result = api_client.get_tenants()
    
    if success:
        return render_template('tenants.html', tenants=result)
    else:
        flash(f'❌ {result}', 'error')
        return render_template('tenants.html', tenants=[])

@app.route('/tenant/<tenant_id>')
@require_auth
def tenant_detail(tenant_id):
    """Show tenant details"""
    success, result = api_client.get_tenant(tenant_id)
    
    if success:
        return render_template('tenant_detail.html', tenant=result)
    else:
        flash(f'❌ {result}', 'error')
        return redirect(url_for('list_tenants'))

@app.route('/tenant/create', methods=['GET', 'POST'])
@require_auth
def create_tenant():
    """Create new tenant"""
    if request.method == 'POST':
        tenant_data = {
            'name': request.form.get('name'),
            'seats': int(request.form.get('seats', 0)),
            'comments': request.form.get('comments', ''),
            'city': request.form.get('city', ''),
            'state': request.form.get('state', ''),
            'zipCode': request.form.get('zipCode', ''),
            'countryCode': request.form.get('countryCode', ''),
            'addressLine1': request.form.get('addressLine1', ''),
            'addressLine2': request.form.get('addressLine2', ''),
            'primaryAdminEmail': request.form.get('primaryAdminEmail', ''),
            'primaryAdminFirstName': request.form.get('primaryAdminFirstName', ''),
            'primaryAdminLastName': request.form.get('primaryAdminLastName', ''),
        }
        
        # Clean empty fields
        tenant_data = {k: v for k, v in tenant_data.items() if v}
        
        # Handle extra admin emails
        extra_emails = request.form.get('extraAdminEmails', '').strip()
        if extra_emails:
            tenant_data['extraAdminEmails'] = [email.strip() for email in extra_emails.split(',') if email.strip()]
        
        success, result = api_client.create_tenant(tenant_data)
        
        if success:
            tenant_id = result.get('id', result.get('organizationId'))
            flash(f'✅ Tenant created successfully!', 'success')
            return redirect(url_for('tenant_detail', tenant_id=tenant_id))
        else:
            flash(f'❌ {result}', 'error')
    
    # Prepare default values from environment variables
    defaults = {
        'name': os.getenv('TENANT_NAME', ''),
        'seats': os.getenv('SEATS', '100'),
        'comments': os.getenv('COMMENTS', ''),
        'city': os.getenv('CITY', ''),
        'state': os.getenv('STATE', ''),
        'zipCode': os.getenv('ZIPCODE', ''),
        'countryCode': os.getenv('COUNTRY_CODE', 'US'),
        'addressLine1': os.getenv('ADDRESS_LINE1', ''),
        'addressLine2': os.getenv('ADDRESS_LINE2', ''),
        'primaryAdminEmail': os.getenv('ADMIN_EMAIL', ''),
        'primaryAdminFirstName': os.getenv('ADMIN_FIRSTNAME', ''),
        'primaryAdminLastName': os.getenv('ADMIN_LASTNAME', ''),
        'extraAdminEmails': os.getenv('EXTRA_ADMIN_EMAILS', ''),
    }
    
    return render_template('create_tenant.html', defaults=defaults)

@app.route('/tenant/<tenant_id>/edit', methods=['GET', 'POST'])
@require_auth
def edit_tenant(tenant_id):
    """Edit existing tenant"""
    if request.method == 'POST':
        tenant_data = {
            'name': request.form.get('name'),
            'seats': int(request.form.get('seats', 0)),
            'comments': request.form.get('comments', ''),
            'city': request.form.get('city', ''),
            'state': request.form.get('state', ''),
            'zipCode': request.form.get('zipCode', ''),
            'countryCode': request.form.get('countryCode', ''),
            'addressLine1': request.form.get('addressLine1', ''),
            'addressLine2': request.form.get('addressLine2', ''),
            'primaryAdminEmail': request.form.get('primaryAdminEmail', ''),
            'primaryAdminFirstName': request.form.get('primaryAdminFirstName', ''),
            'primaryAdminLastName': request.form.get('primaryAdminLastName', ''),
        }
        
        # Clean empty fields
        tenant_data = {k: v for k, v in tenant_data.items() if v}
        
        # Handle extra admin emails
        extra_emails = request.form.get('extraAdminEmails', '').strip()
        if extra_emails:
            tenant_data['extraAdminEmails'] = [email.strip() for email in extra_emails.split(',') if email.strip()]
        
        success, result = api_client.update_tenant(tenant_id, tenant_data)
        
        if success:
            flash(f'✅ Tenant updated successfully!', 'success')
            return redirect(url_for('tenant_detail', tenant_id=tenant_id))
        else:
            flash(f'❌ {result}', 'error')
    
    # GET request - fetch current tenant data
    success, tenant = api_client.get_tenant(tenant_id)
    
    if success:
        # Prepare default values from environment variables (for fallbacks)
        defaults = {
            'name': os.getenv('TENANT_NAME', ''),
            'seats': os.getenv('SEATS', '100'),
            'comments': os.getenv('COMMENTS', ''),
            'city': os.getenv('CITY', ''),
            'state': os.getenv('STATE', ''),
            'zipCode': os.getenv('ZIPCODE', ''),
            'countryCode': os.getenv('COUNTRY_CODE', 'US'),
            'addressLine1': os.getenv('ADDRESS_LINE1', ''),
            'addressLine2': os.getenv('ADDRESS_LINE2', ''),
            'primaryAdminEmail': os.getenv('ADMIN_EMAIL', ''),
            'primaryAdminFirstName': os.getenv('ADMIN_FIRSTNAME', ''),
            'primaryAdminLastName': os.getenv('ADMIN_LASTNAME', ''),
            'extraAdminEmails': os.getenv('EXTRA_ADMIN_EMAILS', ''),
        }
        
        return render_template('edit_tenant.html', tenant=tenant, tenant_id=tenant_id, defaults=defaults)
    else:
        flash(f'❌ {tenant}', 'error')
        return redirect(url_for('list_tenants'))

@app.route('/tenant/<tenant_id>/delete', methods=['POST'])
@require_auth
def delete_tenant(tenant_id):
    """Delete single tenant"""
    success, result = api_client.delete_tenant(tenant_id)
    
    if success:
        flash(f'✅ {result}', 'success')
    else:
        flash(f'❌ {result}', 'error')
    
    return redirect(url_for('list_tenants'))

@app.route('/tenants/delete', methods=['POST'])
@require_auth
def delete_multiple_tenants():
    """Delete multiple tenants"""
    tenant_ids = request.form.getlist('tenant_ids')
    
    if not tenant_ids:
        flash('❌ No tenants selected for deletion', 'error')
        return redirect(url_for('list_tenants'))
    
    success, result = api_client.delete_multiple_tenants(tenant_ids)
    
    if success:
        flash(f'✅ {result}', 'success')
    else:
        flash(f'❌ {result}', 'error')
    
    return redirect(url_for('list_tenants'))

@app.route('/api/token-status')
@require_auth
def token_status():
    """API endpoint to check token validity and remaining time"""
    try:
        is_valid = api_client.is_token_valid()
        
        expires_in = None
        if api_client.token_expires_at:
            remaining = api_client.token_expires_at - datetime.now()
            expires_in = max(0, int(remaining.total_seconds()))
            if expires_in == 0:
                is_valid = False
        
        return jsonify({
            'valid': is_valid,
            'expires_in': expires_in,
            'expires_at': api_client.token_expires_at.isoformat() if api_client.token_expires_at else None
        })
    except Exception as e:
        logger.error(f"Error checking token status: {str(e)}")
        return jsonify({'valid': False, 'error': 'Unable to check token status'}), 500

@app.route('/tenants/export')
@require_auth
def export_all_tenants():
    """Export all tenants as JSON"""
    success, result = api_client.get_tenants()
    
    if success:
        from flask import Response
        import json
        
        # Create JSON response
        json_data = json.dumps(result, indent=2)
        
        # Create download response
        response = Response(
            json_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=all_tenants_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
        return response
    else:
        flash(f'❌ Failed to export tenants: {result}', 'error')
        return redirect(url_for('list_tenants'))

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    api_client.access_token = None
    api_client.token_expires_at = None
    flash('👋 Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
