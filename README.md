# SSE Tenant Manager

A production-ready Flask web application for managing Cisco SSE (Secure Service Edge) tenants through an intuitive web interface with comprehensive deployment and management tools.

## 🚀 Features

### Core Functionality

- 🔐 **OAuth 2.0 Authentication** - Secure authentication with SSE API
- 📋 **Complete Tenant Management** - List, view, create, edit, and delete tenants
- 🔍 **Advanced Search & Filter** - Real-time tenant search and filtering
- 📊 **Bulk Operations** - Select and delete multiple tenants efficiently
- 💾 **Data Export** - Download individual tenant data or bulk export as JSON
- � **Smart Token Management** - Automatic token renewal and status monitoring

### Production Management

- 🖥️ **Cross-Platform Scripts** - Enhanced production scripts for Linux/Mac, Windows, and CentOS
- 🔄 **Background Execution** - Applications run in background and persist after terminal exit
- 📊 **Process Management** - PID-based tracking with graceful shutdown capabilities
- 📋 **Status Monitoring** - Comprehensive status reporting and health checks
- 🎯 **Management Commands** - Standardized start/stop/restart/status operations
- 🚀 **Automated Deployment** - Complete CentOS deployment with web server integration

### User Interface

- 📱 **Fully Responsive Design** - Optimized for desktop, tablet, and mobile devices
- 🎨 **Modern Bootstrap 5 Interface** - Clean, professional, and intuitive design
- ⚡ **Real-time Updates** - Live token status indicator and dynamic content

## 🛠️ Production Scripts

### Quick Start Commands

| Platform | Command | Description |
|----------|---------|-------------|
| **Linux/Mac** | `./run_production.sh start` | Start with Gunicorn daemon |
| **Windows** | `run_production.bat start` | Start with Waitress background |
| **PowerShell** | `.\run_production.ps1 start` | Start with PowerShell management |
| **CentOS** | `sudo ./deploy_centos.sh` | Full system deployment |

### Available Commands

All production scripts support these standardized commands:

```bash
{start|stop|restart|status}
```

#### Examples:

```bash
# Start the application in background
./run_production.sh start

# Check application status
./run_production.sh status

# Restart the application
./run_production.sh restart

# Stop the application gracefully
./run_production.sh stop
```

### Features:

- ✅ **Background Execution** - Applications persist after terminal exit
- ✅ **PID Management** - Reliable process tracking with `logs/app.pid`
- ✅ **Graceful Shutdown** - SIGTERM followed by SIGKILL if necessary
- ✅ **Status Reporting** - Process details, URLs, and log locations
- ✅ **Error Handling** - Colored output with comprehensive error reporting
- ✅ **Log Management** - Separate access (`logs/access.log`) and error (`logs/error.log`) logs
- 📄 **Interactive Modal Dialogs** - Quick tenant details and actions without page refresh
- 🔍 **Enhanced Tenant Details** - Double-click any tenant row for comprehensive view

### Security & Reliability

- 🛡️ **Secure Session Management** - Server-side session storage with encryption
- 🔒 **Environment-based Configuration** - Secure credential management
- 🚨 **Comprehensive Error Handling** - Graceful error recovery and user feedback
- 📝 **Detailed Audit Logging** - Application and access logs for troubleshooting
- 🔧 **Intelligent API Handling** - Automatic retry logic for API compatibility issues

### Recent Enhancements

- ✅ **Fixed Update Functionality** - Resolved tenant update issues with proper API field mapping
- ✅ **Improved Error Handling** - Enhanced error recovery for API compatibility
- ✅ **Enhanced Export Features** - Both individual and bulk tenant data export
- ✅ **URL Routing Fixes** - Resolved edit link generation issues

## 📥 Installation

### From GitHub

```bash
# Clone the repository
git clone https://github.com/rajesharora27/sse-tenant-manager.git
cd sse-tenant-manager

# Create and configure environment
cp .env.template .env
# Edit .env with your SSE credentials

# Start production application
./run_production.sh start     # Linux/Mac
run_production.bat start      # Windows
.\run_production.ps1 start    # PowerShell
```

### Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **pip** (Python package manager)
- **Virtual environment support** (venv or conda)
- **SSE API Access** (Username and Password)

### System Requirements

| Platform | Server | Requirements |
|----------|--------|--------------|
| **Linux/Mac** | Gunicorn | Python 3.8+, pip, venv |
| **Windows** | Waitress | Python 3.8+, pip, venv |
| **CentOS** | Gunicorn + Apache/Nginx | Root access, systemd |

## 🚀 Quick Deployment

### Production Deployment (CentOS)

```bash
# Full automated deployment
sudo ./deploy_centos.sh --apache

# With Nginx
sudo ./deploy_centos.sh --nginx

# With custom domain and SSL
sudo ./deploy_centos.sh --nginx --domain myapp.company.com --ssl
```

### Development Setup
- ✅ **Cross-platform Compatibility** - Tested on Windows, Linux, and macOS

## 📋 Requirements

- Python 3.8 or higher
- Internet connection for SSE API access
- Web browser with JavaScript enabled

## 🔧 Installation & Setup

### 1. Clone or Download

Download the application files to your local machine.

### 2. Environment Configuration

Copy the provided template and configure your environment:

```bash
cp .env.template .env
```

Then edit the `.env` file with your specific values. The template includes all available configuration options:

```env
# Base URL for the API
BASE_URL=https://api.sse.cisco.com/

# Authentication credentials (REQUIRED)
USERNAME=your_sse_username_here
PASSWORD=your_sse_password_here
TOKEN_URL=https://api.sse.cisco.com/auth/v2/token

# Flask app configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=False

# SSL Configuration (for corporate environments)
VERIFY_SSL=true

# Default values for Create Tenant form (Optional - customize as needed)
TENANT_NAME=Your Company Name
ADMIN_FIRSTNAME=Admin
ADMIN_LASTNAME=User
ADMIN_EMAIL=admin@yourcompany.com
ADDRESS_LINE1=123 Main Street
ADDRESS_LINE2=Suite 100
CITY=Your City
STATE=Your State
ZIPCODE=12345
COUNTRY_CODE=US
SEATS=100
COMMENTS=Production tenant
EXTRA_ADMIN_EMAILS=admin2@yourcompany.com,admin3@yourcompany.com
```

**⚠️ Important:**

- Never commit the `.env` file to version control
- Only `USERNAME` and `PASSWORD` are required - all other values have defaults
- Use `.env.template` as your reference for all available options
- For production, generate a strong SECRET_KEY using: `python -c "import os; print(os.urandom(32).hex())"`

## 🚀 Running the Application

### Windows

#### Development Mode

```cmd
run.bat
```

#### Production Mode

**Option 1 - Batch File:**

```cmd
run_production.bat
```

**Option 2 - PowerShell (Recommended):**

```powershell
.\run_production.ps1
```

**Option 3 - Direct Python:**

```cmd
python run_waitress.py
```

**Note for Windows:** The production scripts use Waitress instead of Gunicorn since Gunicorn is Unix-only. Waitress provides similar performance and production capabilities for Windows environments.

### Linux/Mac

#### Development Mode

```bash
python app.py
```

#### Production Mode

```bash
chmod +x run_production.sh
./run_production.sh
```

**Note for Linux/Mac:** The production script uses Gunicorn, which is the recommended WSGI server for Unix-based systems.

### Manual Setup (All Platforms)

#### 1. Create Virtual Environment

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Run Application

**Development:**

```bash
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows
python app.py
```

**Production:**

```bash
export FLASK_ENV=production   # Linux/Mac
set FLASK_ENV=production      # Windows
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## 🌐 Accessing the Application

1. Open your web browser
2. Navigate to: `http://localhost:5000`
3. Enter your SSE API credentials on the authentication page
4. Start managing your tenants!

## 📖 Usage Guide

### Authentication

1. On first access, you'll be prompted to authenticate
2. Enter your SSE API credentials
3. The system will validate and store your session

### Managing Tenants

- **View All Tenants:** Click "Tenants" in the navigation
- **Search:** Use the search box to filter tenants by name, ID, seats, or email
- **View Details:** Double-click any tenant row to see full details
- **Create Tenant:** Click "Create Tenant" and fill out the form
- **Edit Tenant:** Click the edit button in tenant details or list
- **Delete Tenant:** Use the delete button (single) or select multiple for bulk deletion
- **Export Data:** Click the export button to download tenant data as JSON

### Token Status

- Monitor your authentication status in the top-right corner
- Green: Token valid (>30 minutes remaining)
- Yellow: Token valid but expiring soon (<30 minutes)
- Red: Token invalid or expired (<5 minutes)

## 🔧 Configuration Options

### Environment Variables

#### Required Configuration

| Variable   | Description      | Example             |
| ---------- | ---------------- | ------------------- |
| `USERNAME` | SSE API username | `your_api_username` |
| `PASSWORD` | SSE API password | `your_api_password` |

#### API Configuration

| Variable     | Description             | Default                                   |
| ------------ | ----------------------- | ----------------------------------------- |
| `BASE_URL`   | SSE API base URL        | `https://api.sse.cisco.com/`              |
| `TOKEN_URL`  | OAuth token endpoint    | `https://api.sse.cisco.com/auth/v2/token` |
| `VERIFY_SSL` | Enable SSL verification | `true`                                    |

#### Flask Application Settings

| Variable      | Description              | Default        |
| ------------- | ------------------------ | -------------- |
| `SECRET_KEY`  | Flask session secret key | Auto-generated |
| `FLASK_ENV`   | Environment mode         | `production`   |
| `FLASK_DEBUG` | Enable debug mode        | `False`        |

#### Default Form Values (Optional)

These values pre-populate the Create Tenant form for convenience:

| Variable             | Description              | Default                                 |
| -------------------- | ------------------------ | --------------------------------------- |
| `TENANT_NAME`        | Default tenant name      | `CXPM Security`                         |
| `ADMIN_FIRSTNAME`    | Default admin first name | `Admin`                                 |
| `ADMIN_LASTNAME`     | Default admin last name  | `User`                                  |
| `ADMIN_EMAIL`        | Default admin email      | `admin@company.com`                     |
| `ADDRESS_LINE1`      | Default address line 1   | `123 Main Street`                       |
| `ADDRESS_LINE2`      | Default address line 2   | `Suite 100`                             |
| `CITY`               | Default city             | `New York`                              |
| `STATE`              | Default state/province   | `NY`                                    |
| `ZIPCODE`            | Default postal code      | `10001`                                 |
| `COUNTRY_CODE`       | Default country code     | `US`                                    |
| `SEATS`              | Default seat count       | `100`                                   |
| `COMMENTS`           | Default comments         | `Production tenant`                     |
| `EXTRA_ADMIN_EMAILS` | Additional admin emails  | `admin2@company.com,admin3@company.com` |

**💡 Tip:** Customize the default form values to match your organization's typical tenant configuration. This saves time when creating multiple tenants.

### Production Deployment

For production deployment:

1. **Set `FLASK_ENV=production`**
2. **Use a strong `SECRET_KEY`**
3. **Enable SSL/HTTPS**
4. **Configure reverse proxy (nginx/Apache)**
5. **Set up monitoring and logging**

### Example nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📁 Project Structure

```
tenant-manager-app/
├── app.py                  # Main Flask application (425 lines, optimized)
├── wsgi.py                 # WSGI entry point for production
├── run_waitress.py         # Waitress launcher for Windows
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration (create from template)
├── .env.template          # Environment template with all options
├── .gitignore             # Git ignore rules
├── README.md              # This documentation
├── DEPLOYMENT_CHECKLIST.md # Production deployment guide
├── CLEANUP_SUMMARY.md     # Production cleanup documentation
├── run.bat                # Windows batch script (development)
├── run.ps1                # Windows PowerShell script (development)
├── run_production.bat     # Production startup script (Windows batch)
├── run_production.ps1     # Production startup script (Windows PowerShell)
├── run_production.sh      # Production startup script (Linux/Mac)
├── static/                # Static assets
│   ├── favicon.ico        # Website icon
│   └── style.css          # CSS styles
├── templates/             # HTML templates
│   ├── base.html          # Base template with navigation
│   ├── index.html         # Dashboard
│   ├── authenticate.html  # Authentication page
│   ├── tenants.html       # Tenant list
│   ├── tenant_detail.html # Tenant details
│   ├── create_tenant.html # Create tenant form
│   ├── edit_tenant.html   # Edit tenant form
│   ├── redirect.html      # OAuth redirect handler
│   ├── 404.html           # 404 error page
│   └── 500.html           # 500 error page
├── flask_session/         # Session storage (auto-created)
└── logs/                  # Application logs (auto-created)
```

## 🐛 Troubleshooting

### Common Issues

#### Authentication Fails

- Verify your SSE API credentials in `.env`
- Check network connectivity to SSE API
- Ensure `VERIFY_SSL=false` if using self-signed certificates

#### Application Won't Start

- Ensure Python 3.8+ is installed
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify port 5000 is not in use by another application

#### Gunicorn Error on Windows

If you see `ModuleNotFoundError: No module named 'fcntl'`, this is because Gunicorn doesn't work on Windows. Use the provided Windows scripts instead:

- **Development:** `run.bat` (uses Flask development server)
- **Production:** `run_production.bat` (uses Waitress WSGI server)

#### Token Expires Frequently

- Check system clock synchronization
- Verify network stability
- Consider increasing token refresh intervals

#### Sessions Not Persisting

- Ensure `flask_session/` directory is writable
- Check that `SECRET_KEY` is set and consistent
- Verify cookies are enabled in your browser

#### Cookie/Session Errors

If you see `TypeError: cannot use a string pattern on a bytes-like object` errors:

- This was a Flask-Session extension compatibility issue that has been resolved
- The application now uses built-in Flask sessions for better compatibility
- Ensure SECRET_KEY is a string: `python -c "import os; print(os.urandom(32).hex())"`

### Getting Help

1. Check the application logs in `logs/` directory
2. Enable debug mode by setting `FLASK_ENV=development`
3. Review browser console for JavaScript errors
4. Verify network connectivity to SSE API endpoints

## �️ Troubleshooting

### Common Issues and Solutions

#### Authentication Issues

**Problem:** "Authentication failed" or 401 errors
**Solutions:**

- Verify USERNAME and PASSWORD in `.env` file
- Check if account has proper SSE API permissions
- Ensure TOKEN_URL is correct for your SSE environment
- Try regenerating API credentials in SSE console

#### Tenant Update Issues

**Problem:** Tenant updates fail with "Keys not supported" errors
**Solution:** This is handled automatically. The application will retry updates without unsupported fields (like adminEmails for certain organization types).

#### Connection Issues

**Problem:** "Connection timeout" or SSL errors
**Solutions:**

- Check internet connectivity
- Verify BASE_URL points to correct SSE environment
- For corporate networks, check if proxy/firewall allows SSE API access
- If SSL issues persist, temporarily set `VERIFY_SSL=false` (not recommended for production)

#### UI/Display Issues

**Problem:** Tenant list empty or not loading
**Solutions:**

- Check browser console for JavaScript errors
- Verify authentication status in top-right corner
- Refresh the page and try again
- Check if your account has permissions to list tenants

#### Performance Issues

**Problem:** Slow loading or timeouts
**Solutions:**

- Use production mode with `run_production.bat` or `run_production.sh`
- Check network latency to SSE API endpoints
- Monitor system resources (CPU/memory)

### Debug Mode

To enable detailed logging for troubleshooting:

1. Set `FLASK_ENV=development` in `.env`
2. Set `FLASK_DEBUG=True` in `.env`
3. Restart the application
4. Check console output for detailed error messages

### Getting Help

1. Check the application logs in the terminal
2. Review browser console for client-side errors
3. Verify your SSE API credentials and permissions
4. Test API connectivity using curl or Postman
5. Ensure all required environment variables are set

## �🔐 Security Considerations

- **Credentials:** Store API credentials in `.env` file, never in code
- **HTTPS:** Use HTTPS in production environments
- **Session Security:** Configure secure session cookies for production
- **Network:** Restrict network access to SSE API endpoints as needed
- **Logging:** Monitor access logs for suspicious activity

## 📄 License

This project is provided as-is for managing Cisco SSE tenants. Ensure compliance with your organization's security policies and Cisco's terms of service.

## 🚀 Quick Start Summary

1. **Download/clone the project**
2. **Copy `.env.template` to `.env` and configure your SSE credentials**
3. **Run appropriate startup script for your platform**
4. **Open http://localhost:5000 in your browser**
5. **Authenticate and start managing tenants!**

**Essential Steps:**

```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your credentials (only USERNAME and PASSWORD are required)
# All other values have sensible defaults

# Windows - Production Mode (Recommended)
run_production.bat
# or
.\run_production.ps1

# Linux/Mac - Production Mode (Recommended)
./run_production.sh

# Development Mode (Any Platform)
python app.py
```

**✅ All Features Working:**

- Create, Read, Update, Delete tenants
- Bulk operations and export functionality
- Real-time search and filtering
- Responsive UI with modal dialogs
- Automatic token management
- Cross-platform compatibility

**🎯 Production Ready:** The application has been thoroughly tested and all known issues have been resolved.
run_production.bat

# Linux/Mac

chmod +x run_production.sh && ./run_production.sh

```

---

**Need help?** Check the troubleshooting section or review the application logs for detailed error information.
```
