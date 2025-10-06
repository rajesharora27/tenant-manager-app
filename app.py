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
        if not session.get('authenticated') or not session.get('multiorg_username'):
            logger.warning("Unauthenticated access attempt")
            flash('Please authenticate with your multiorg credentials', 'warning')
            return redirect(url_for('authenticate'))
        
        # Check if token is still valid, if not redirect to re-authenticate
        if session.get('authenticated') and session.get('multiorg_username'):
            api_client = get_user_api_client()
            if api_client and not api_client.is_token_valid():
                logger.warning("Token expired, requiring re-authentication")
                session.pop('authenticated', None)
                flash('Session expired. Please re-authenticate.', 'warning')
                return redirect(url_for('authenticate'))
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

class SSEAPIClient:
    """API Client for Cisco SSE Tenant Management - Session-based multi-user support"""
    
    def __init__(self, username=None, password=None):
        # Configuration parameters from environment (don't change per user)
        self.base_url = os.getenv('BASE_URL', 'https://api.sse.cisco.com/')
        self.token_url = os.getenv('TOKEN_URL', 'https://api.sse.cisco.com/auth/v2/token')
        self.verify_ssl = os.getenv('VERIFY_SSL', 'true').lower() == 'true'
        
        # User-specific credentials (multiorg username/password)
        self.username = username
        self.password = password
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
        """Update existing tenant - simplified to update all fields as provided"""
        try:
            # Transform data for update API 
            update_data = {}
            
            # Copy all fields directly from form data
            for field in ['name', 'seats', 'comments', 'city', 'state', 'zipCode', 'addressLine1', 'addressLine2']:
                if field in tenant_data:
                    update_data[field] = tenant_data[field]
            
            # Handle countryCode with validation (must be exactly 2 characters)
            if 'countryCode' in tenant_data:
                country_code = tenant_data['countryCode'].strip()
                if len(country_code) == 2:
                    update_data['countryCode'] = country_code
                else:
                    logger.warning(f"Invalid country code length: {len(country_code)}, must be exactly 2 characters")
            
            # Handle adminDetails field - try different field names based on what API supports
            if 'adminDetails' in tenant_data:
                if tenant_data['adminDetails']:
                    admin_details_array = []
                    for admin in tenant_data['adminDetails']:
                        if isinstance(admin, dict) and 'email' in admin:
                            # Already in correct format
                            if admin['email'].strip():
                                admin_details_array.append({
                                    'email': admin['email'].strip(),
                                    'firstName': admin.get('firstName', '').strip(),
                                    'lastName': admin.get('lastName', '').strip()
                                })
                        elif isinstance(admin, str) and admin.strip():
                            # Convert email string to adminDetails object format
                            admin_details_array.append({
                                'email': admin.strip(),
                                'firstName': '',
                                'lastName': ''
                            })
                    
                    # Try adminDetails first, then fall back to adminEmails, then extraAdminEmails
                    admin_emails_list = [admin['email'] for admin in admin_details_array if admin['email']]
                    update_data['adminDetails'] = admin_details_array
                    logger.info(f"Updating adminDetails with: {admin_details_array}")
                else:
                    # Empty adminDetails
                    update_data['adminDetails'] = []
                    logger.info("Setting adminDetails to empty array")

            response = self._make_request('PUT', f'/admin/v2/tenants/{tenant_id}', json=update_data)
            
            if response.status_code == 200:
                tenant = response.json()
                logger.info(f"Successfully updated tenant {tenant_id}")
                return True, tenant
            elif response.status_code == 400:
                # Check if the error is about unsupported adminDetails field
                try:
                    error_detail = response.json()
                    error_message = error_detail.get('message', '')
                    
                    if 'adminDetails' in str(error_message):
                        logger.warning(f"adminDetails field not supported for this org, trying adminEmails")
                        # Remove adminDetails and try with adminEmails
                        update_data_fallback = {k: v for k, v in update_data.items() if k != 'adminDetails'}
                        
                        if 'adminDetails' in tenant_data and tenant_data['adminDetails']:
                            # Convert to simple email list
                            admin_emails_list = []
                            for admin in tenant_data['adminDetails']:
                                if isinstance(admin, dict) and 'email' in admin and admin['email'].strip():
                                    admin_emails_list.append(admin['email'].strip())
                                elif isinstance(admin, str) and admin.strip():
                                    admin_emails_list.append(admin.strip())
                            
                            if admin_emails_list:
                                update_data_fallback['adminEmails'] = admin_emails_list
                        
                        response = self._make_request('PUT', f'/admin/v2/tenants/{tenant_id}', json=update_data_fallback)
                        
                        if response.status_code == 200:
                            tenant = response.json()
                            logger.info(f"Successfully updated tenant {tenant_id} (using adminEmails fallback)")
                            return True, tenant
                        elif response.status_code == 400:
                            # Try extraAdminEmails as final fallback
                            logger.warning(f"adminEmails field not supported either, trying extraAdminEmails")
                            update_data_fallback2 = {k: v for k, v in update_data_fallback.items() if k != 'adminEmails'}
                            
                            if admin_emails_list:
                                update_data_fallback2['extraAdminEmails'] = admin_emails_list
                            
                            response = self._make_request('PUT', f'/admin/v2/tenants/{tenant_id}', json=update_data_fallback2)
                            
                            if response.status_code == 200:
                                tenant = response.json()
                                logger.info(f"Successfully updated tenant {tenant_id} (using extraAdminEmails fallback)")
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

# Session-based API clients (no global client)
def get_user_api_client():
    """Get API client for current user session"""
    if not session.get('multiorg_username'):
        return None
    
    # Create client with session credentials
    client = SSEAPIClient(
        username=session.get('multiorg_username'),
        password=session.get('multiorg_password')
    )
    
    # Restore token from session if available
    if session.get('access_token') and session.get('token_expires_at'):
        try:
            client.access_token = session.get('access_token')
            client.token_expires_at = datetime.fromisoformat(session.get('token_expires_at'))
        except:
            # Invalid token data in session, will re-authenticate
            pass
    
    return client

def save_user_session(client):
    """Save API client token info to session"""
    if client.access_token and client.token_expires_at:
        session['access_token'] = client.access_token
        session['token_expires_at'] = client.token_expires_at.isoformat()
    else:
        session.pop('access_token', None)
        session.pop('token_expires_at', None)

# Jinja2 filters
def render_admin_details(value):
    """Render adminDetails as a comma-separated string of emails"""
    if value is None:
        return ''
    if isinstance(value, list):
        # Extract emails from adminDetails objects
        emails = []
        for admin in value:
            if isinstance(admin, dict) and 'email' in admin:
                if admin['email'].strip():
                    emails.append(admin['email'].strip())
            elif isinstance(admin, str) and admin.strip():
                emails.append(admin.strip())
        return ', '.join(emails)
    if isinstance(value, str):
        return value.strip()
    return str(value)

app.jinja_env.filters['render_admin_details'] = render_admin_details

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
    user_info = {
        'username': session.get('multiorg_username'),
        'auth_time': session.get('auth_time'),
        'session_id': session.get('_id')
    }
    
    # Get token info if available
    api_client = get_user_api_client()
    if api_client and api_client.token_expires_at:
        user_info['token_expires_at'] = api_client.token_expires_at.isoformat()
        user_info['token_valid'] = api_client.is_token_valid()
    
    return render_template('index.html', user_info=user_info)

@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    """Authentication page - Multi-org user authentication"""
    # Configuration data (read-only, from environment)
    config_data = {
        'BASE_URL': os.getenv('BASE_URL', 'https://api.sse.cisco.com/'),
        'TOKEN_URL': os.getenv('TOKEN_URL', 'https://api.sse.cisco.com/auth/v2/token'),
        'VERIFY_SSL': os.getenv('VERIFY_SSL', 'true')
    }

    if request.method == 'POST':
        # Get multiorg credentials from form
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('❌ Please provide both multiorg username and password', 'error')
            return render_template('authenticate.html', config=config_data)

        # Create API client with user credentials
        api_client = SSEAPIClient(username=username, password=password)

        try:
            success, message = api_client.authenticate()
            logger.info(f"Authentication result for user {username}: success={success}")

            if success:
                # Store user credentials and session info
                session.permanent = True
                session['authenticated'] = True
                session['multiorg_username'] = username
                session['multiorg_password'] = password  # Store encrypted in production
                session['auth_time'] = datetime.now().isoformat()
                session['user_display_name'] = username
                
                # Save token info to session
                save_user_session(api_client)
                
                flash(f'✅ {message} (User: {username})', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'❌ {message}', 'error')
                
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            flash(f'❌ {error_msg}', 'error')

    return render_template('authenticate.html', config=config_data)

@app.route('/tenants')
@require_auth
def list_tenants():
    """List all tenants"""
    api_client = get_user_api_client()
    if not api_client:
        flash('❌ No API client available', 'error')
        return redirect(url_for('authenticate'))
    
    success, result = api_client.get_tenants()
    save_user_session(api_client)  # Save any token updates
    
    if success:
        return render_template('tenants.html', tenants=result)
    else:
        flash(f'❌ {result}', 'error')
        return render_template('tenants.html', tenants=[])

@app.route('/tenant/<tenant_id>')
@require_auth
def tenant_detail(tenant_id):
    """Show tenant details"""
    api_client = get_user_api_client()
    if not api_client:
        flash('❌ No API client available', 'error')
        return redirect(url_for('authenticate'))
    
    success, result = api_client.get_tenant(tenant_id)
    save_user_session(api_client)  # Save any token updates
    
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
        api_client = get_user_api_client()
        if not api_client:
            flash('❌ No API client available', 'error')
            return redirect(url_for('authenticate'))
        
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
        
        # Handle admin details - convert email list to adminDetails format
        admin_details = request.form.get('adminDetails', '').strip()
        if admin_details:
            admin_details_array = []
            for email in admin_details.split(','):
                email = email.strip()
                if email:
                    admin_details_array.append({
                        'email': email,
                        'firstName': '',
                        'lastName': ''
                    })
            tenant_data['adminDetails'] = admin_details_array
        
        success, result = api_client.create_tenant(tenant_data)
        save_user_session(api_client)  # Save any token updates
        
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
        'adminDetails': os.getenv('ADMIN_DETAILS', ''),
    }
    
    return render_template('create_tenant.html', defaults=defaults)

@app.route('/tenant/<tenant_id>/edit', methods=['GET', 'POST'])
@require_auth
def edit_tenant(tenant_id):
    """Edit existing tenant"""
    api_client = get_user_api_client()
    if not api_client:
        flash('❌ No API client available', 'error')
        return redirect(url_for('authenticate'))
    
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
            # Note: primaryAdminEmail, primaryAdminFirstName, and primaryAdminLastName 
            # are excluded from updates for security reasons
        }
        
        # Clean empty fields
        tenant_data = {k: v for k, v in tenant_data.items() if v}
        
        # Handle admin details - convert email list to adminDetails format
        admin_details = request.form.get('adminDetails', '').strip()
        if admin_details:
            admin_details_array = []
            for email in admin_details.split(','):
                email = email.strip()
                if email:
                    admin_details_array.append({
                        'email': email,
                        'firstName': '',
                        'lastName': ''
                    })
            tenant_data['adminDetails'] = admin_details_array
        
        success, result = api_client.update_tenant(tenant_id, tenant_data)
        save_user_session(api_client)  # Save any token updates
        
        if success:
            flash(f'✅ Tenant updated successfully!', 'success')
            return redirect(url_for('tenant_detail', tenant_id=tenant_id))
        else:
            flash(f'❌ {result}', 'error')
    
    # GET request - fetch current tenant data
    success, tenant = api_client.get_tenant(tenant_id)
    save_user_session(api_client)  # Save any token updates
    
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
            'adminDetails': os.getenv('ADMIN_DETAILS', ''),
        }
        
        return render_template('edit_tenant.html', tenant=tenant, tenant_id=tenant_id, defaults=defaults)
    else:
        flash(f'❌ {tenant}', 'error')
        return redirect(url_for('list_tenants'))

@app.route('/tenant/<tenant_id>/delete', methods=['POST'])
@require_auth
def delete_tenant(tenant_id):
    """Delete single tenant"""
    api_client = get_user_api_client()
    if not api_client:
        flash('❌ No API client available', 'error')
        return redirect(url_for('authenticate'))
    
    success, result = api_client.delete_tenant(tenant_id)
    save_user_session(api_client)  # Save any token updates
    
    if success:
        flash(f'✅ {result}', 'success')
    else:
        flash(f'❌ {result}', 'error')
    
    return redirect(url_for('list_tenants'))

@app.route('/tenants/delete', methods=['POST'])
@require_auth
def delete_multiple_tenants():
    """Delete multiple tenants"""
    api_client = get_user_api_client()
    if not api_client:
        flash('❌ No API client available', 'error')
        return redirect(url_for('authenticate'))
    
    tenant_ids = request.form.getlist('tenant_ids')
    
    if not tenant_ids:
        flash('❌ No tenants selected for deletion', 'error')
        return redirect(url_for('list_tenants'))
    
    success, result = api_client.delete_multiple_tenants(tenant_ids)
    save_user_session(api_client)  # Save any token updates
    
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
        api_client = get_user_api_client()
        if not api_client:
            return jsonify({'valid': False, 'error': 'No API client available'}), 400
        
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
            'expires_at': api_client.token_expires_at.isoformat() if api_client.token_expires_at else None,
            'username': session.get('multiorg_username')
        })
    except Exception as e:
        logger.error(f"Error checking token status: {str(e)}")
        return jsonify({'valid': False, 'error': 'Unable to check token status'}), 500

@app.route('/tenants/export')
@require_auth
def export_all_tenants():
    """Export all tenants as JSON"""
    api_client = get_user_api_client()
    if not api_client:
        flash('❌ No API client available', 'error')
        return redirect(url_for('authenticate'))
    
    success, result = api_client.get_tenants()
    save_user_session(api_client)  # Save any token updates
    
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
                'Content-Disposition': f'attachment; filename=all_tenants_{session.get("multiorg_username", "user")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
        return response
    else:
        flash(f'❌ Failed to export tenants: {result}', 'error')
        return redirect(url_for('list_tenants'))

@app.route('/logout')
def logout():
    """Logout and clear session"""
    username = session.get('multiorg_username', 'User')
    session.clear()
    flash(f'👋 Logged out successfully ({username})', 'info')
    return redirect(url_for('authenticate'))

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
