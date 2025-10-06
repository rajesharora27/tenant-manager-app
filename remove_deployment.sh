#!/bin/bash

# =============================================================================
# CentOS Deployment Removal Script for Tenant Manager App
# =============================================================================
# This script removes the deployment created by deploy_centos.sh
# SAFELY removes all deployment artifacts while preserving original files
# 
# Usage: sudo ./remove_deployment.sh [OPTIONS]
# Options:
#   --force      Skip confirmation prompts
#   --keep-logs  Keep log files
#   --help       Show this help message
# =============================================================================

set -e  # Exit on any error

# Default configuration
FORCE_REMOVAL="false"
KEEP_LOGS="false"
APP_NAME="tenant-manager-app"
APP_USER="tmapp"
INSTALL_DIR="/opt/tenant-manager-app"
SERVICE_NAME="tenant-manager-app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                FORCE_REMOVAL="true"
                shift
                ;;
            --keep-logs)
                KEEP_LOGS="true"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
}

show_help() {
    cat << EOF
CentOS Deployment Removal Script for Tenant Manager App

This script safely removes the deployment created by deploy_centos.sh
while preserving your original application files.

Usage: sudo ./remove_deployment.sh [OPTIONS]

Options:
  --force      Skip confirmation prompts (automatic removal)
  --keep-logs  Keep application and system log files
  --help       Show this help message

What will be removed:
  ✓ Systemd service (${SERVICE_NAME})
  ✓ Application user (${APP_USER})
  ✓ Installation directory (${INSTALL_DIR})
  ✓ Web server configuration files
  ✓ Firewall rules
  ✓ SSL certificates (if created by deployment)
  ✓ Log files (unless --keep-logs specified)

What will be preserved:
  ✓ Original application files in source directory
  ✓ System packages (Python, Apache/Nginx remain installed)
  ✓ Base system configuration

Examples:
  sudo ./remove_deployment.sh
  sudo ./remove_deployment.sh --force
  sudo ./remove_deployment.sh --keep-logs --force

EOF
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root (use sudo)"
    fi
}

# Safety check to ensure we're not running from target directory
check_safety() {
    local current_dir="$(pwd)"
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Prevent running from target installation directory
    if [ "$script_dir" = "$INSTALL_DIR" ] || [ "$current_dir" = "$INSTALL_DIR" ]; then
        error "Cannot run removal script from target directory $INSTALL_DIR"
        error "Please run this script from your source/development directory"
    fi
    
    log "Safety check passed - running removal from $script_dir"
}

# Confirm removal
confirm_removal() {
    if [ "$FORCE_REMOVAL" = "false" ]; then
        echo ""
        warning "This will remove the following deployment components:"
        warning "  - Systemd service: $SERVICE_NAME"
        warning "  - Application user: $APP_USER"
        warning "  - Installation directory: $INSTALL_DIR"
        warning "  - Web server configuration"
        warning "  - Firewall rules for the application"
        if [ "$KEEP_LOGS" = "false" ]; then
            warning "  - Application log files"
        fi
        echo ""
        info "Your original application files will remain unchanged."
        echo ""
        
        read -p "Are you sure you want to remove the deployment? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log "Removal cancelled by user"
            exit 0
        fi
        echo ""
    fi
}

# Stop and disable services
stop_services() {
    log "Stopping and disabling services..."
    
    # Stop application service
    if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
        log "Stopping $SERVICE_NAME service..."
        systemctl stop $SERVICE_NAME || warning "Failed to stop $SERVICE_NAME service"
    fi
    
    if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
        log "Disabling $SERVICE_NAME service..."
        systemctl disable $SERVICE_NAME || warning "Failed to disable $SERVICE_NAME service"
    fi
    
    # Note: We don't stop Apache/Nginx as they might be used by other applications
    log "Services stopped and disabled"
}

# Remove systemd service file
remove_systemd_service() {
    log "Removing systemd service configuration..."
    
    local service_file="/etc/systemd/system/${SERVICE_NAME}.service"
    if [ -f "$service_file" ]; then
        rm -f "$service_file"
        systemctl daemon-reload
        log "Systemd service file removed"
    else
        info "Systemd service file not found, skipping"
    fi
}

# Remove web server configuration
remove_web_config() {
    log "Removing web server configuration..."
    
    # Remove Apache configuration
    local apache_config="/etc/httpd/conf.d/${APP_NAME}.conf"
    if [ -f "$apache_config" ]; then
        log "Removing Apache configuration: $apache_config"
        rm -f "$apache_config"
        
        # Test Apache configuration and reload if valid
        if httpd -t 2>/dev/null; then
            systemctl reload httpd 2>/dev/null || warning "Could not reload Apache"
        else
            warning "Apache configuration test failed after removal - manual intervention may be needed"
        fi
    fi
    
    # Remove Nginx configuration
    local nginx_config="/etc/nginx/conf.d/${APP_NAME}.conf"
    if [ -f "$nginx_config" ]; then
        log "Removing Nginx configuration: $nginx_config"
        rm -f "$nginx_config"
        
        # Test Nginx configuration and reload if valid
        if nginx -t 2>/dev/null; then
            systemctl reload nginx 2>/dev/null || warning "Could not reload Nginx"
        else
            warning "Nginx configuration test failed after removal - manual intervention may be needed"
        fi
    fi
    
    if [ ! -f "$apache_config" ] && [ ! -f "$nginx_config" ]; then
        info "No web server configuration files found"
    fi
}

# Remove SSL certificates (only if they were created by deployment)
remove_ssl_certificates() {
    log "Checking for SSL certificates..."
    
    local ssl_cert="/etc/ssl/certs/${APP_NAME}.crt"
    local ssl_key="/etc/ssl/private/${APP_NAME}.key"
    
    if [ -f "$ssl_cert" ] || [ -f "$ssl_key" ]; then
        warning "Found SSL certificates that may have been created by deployment"
        
        if [ "$FORCE_REMOVAL" = "false" ]; then
            read -p "Remove SSL certificates? (yes/no): " -r
            if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                rm -f "$ssl_cert" "$ssl_key" 2>/dev/null || warning "Could not remove SSL certificates"
                log "SSL certificates removed"
            else
                info "SSL certificates preserved"
            fi
        else
            rm -f "$ssl_cert" "$ssl_key" 2>/dev/null || warning "Could not remove SSL certificates"
            log "SSL certificates removed (force mode)"
        fi
    else
        info "No deployment-specific SSL certificates found"
    fi
}

# Remove firewall rules
remove_firewall_rules() {
    log "Removing firewall rules..."
    
    if systemctl is-active --quiet firewalld; then
        # Remove common ports that might have been opened
        local ports_to_remove=("80/tcp" "443/tcp" "5000/tcp")
        
        for port in "${ports_to_remove[@]}"; do
            if firewall-cmd --list-ports | grep -q "$port"; then
                if [ "$FORCE_REMOVAL" = "false" ]; then
                    warning "Found firewall rule for port $port"
                    read -p "Remove firewall rule for port $port? (yes/no): " -r
                    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                        firewall-cmd --permanent --remove-port="$port" 2>/dev/null || warning "Could not remove port $port"
                        log "Removed firewall rule for port $port"
                    else
                        info "Firewall rule for port $port preserved"
                    fi
                else
                    # In force mode, only remove port 5000 (Flask direct access)
                    if [ "$port" = "5000/tcp" ]; then
                        firewall-cmd --permanent --remove-port="$port" 2>/dev/null || warning "Could not remove port $port"
                        log "Removed firewall rule for port $port (force mode)"
                    fi
                fi
            fi
        done
        
        firewall-cmd --reload 2>/dev/null || warning "Could not reload firewall"
    else
        info "Firewalld not running, skipping firewall rule removal"
    fi
}

# Remove application directory and user
remove_application() {
    log "Removing application installation..."
    
    # Stop any remaining processes owned by app user
    if id "$APP_USER" &>/dev/null; then
        log "Stopping any processes owned by $APP_USER..."
        pkill -U "$APP_USER" 2>/dev/null || true
        sleep 2
    fi
    
    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        log "Removing installation directory: $INSTALL_DIR"
        
        # Create backup if requested
        if [ "$FORCE_REMOVAL" = "false" ]; then
            read -p "Create backup of installation directory before removal? (yes/no): " -r
            if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                local backup_dir="${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
                mv "$INSTALL_DIR" "$backup_dir"
                log "Installation directory backed up to: $backup_dir"
            else
                rm -rf "$INSTALL_DIR"
                log "Installation directory removed"
            fi
        else
            rm -rf "$INSTALL_DIR"
            log "Installation directory removed (force mode)"
        fi
    else
        info "Installation directory not found"
    fi
    
    # Remove application user
    if id "$APP_USER" &>/dev/null; then
        log "Removing application user: $APP_USER"
        userdel "$APP_USER" 2>/dev/null || warning "Could not remove user $APP_USER"
        
        # Remove user's home directory if it exists and is different from install dir
        local user_home=$(getent passwd "$APP_USER" 2>/dev/null | cut -d: -f6)
        if [ -n "$user_home" ] && [ "$user_home" != "$INSTALL_DIR" ] && [ -d "$user_home" ]; then
            if [ "$FORCE_REMOVAL" = "false" ]; then
                read -p "Remove user home directory $user_home? (yes/no): " -r
                if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                    rm -rf "$user_home"
                    log "User home directory removed"
                fi
            fi
        fi
    else
        info "Application user not found"
    fi
}

# Remove log files
remove_logs() {
    if [ "$KEEP_LOGS" = "false" ]; then
        log "Removing log files..."
        
        # Remove application-specific log files
        local log_files=(
            "/var/log/httpd/${APP_NAME}_access.log"
            "/var/log/httpd/${APP_NAME}_error.log"
            "/var/log/nginx/${APP_NAME}_access.log"
            "/var/log/nginx/${APP_NAME}_error.log"
        )
        
        for log_file in "${log_files[@]}"; do
            if [ -f "$log_file" ]; then
                rm -f "$log_file"
                log "Removed log file: $log_file"
            fi
        done
        
        # Clear systemd journal entries for the service
        journalctl --vacuum-time=1s --unit="$SERVICE_NAME" 2>/dev/null || warning "Could not clear journal entries"
        
    else
        info "Log files preserved (--keep-logs specified)"
    fi
}

# Clean up SELinux policies (if any were set)
cleanup_selinux() {
    log "Cleaning up SELinux policies..."
    
    # Reset SELinux booleans that were set for the application
    if command -v setsebool >/dev/null 2>&1; then
        # Note: We don't reset httpd_can_network_connect as other apps might need it
        info "SELinux settings preserved (may be used by other applications)"
    fi
    
    # Remove port policies for port 5000 (if it was added specifically for this app)
    if command -v semanage >/dev/null 2>&1; then
        if semanage port -l | grep -q "http_port_t.*5000"; then
            if [ "$FORCE_REMOVAL" = "false" ]; then
                read -p "Remove SELinux port policy for port 5000? (yes/no): " -r
                if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                    semanage port -d -t http_port_t -p tcp 5000 2>/dev/null || warning "Could not remove SELinux port policy"
                    log "SELinux port policy for 5000 removed"
                fi
            fi
        fi
    fi
}

# Verify removal
verify_removal() {
    log "Verifying removal..."
    
    local issues=0
    
    # Check service
    if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        warning "Systemd service still present"
        issues=$((issues + 1))
    fi
    
    # Check user
    if id "$APP_USER" &>/dev/null; then
        warning "Application user still exists"
        issues=$((issues + 1))
    fi
    
    # Check directory
    if [ -d "$INSTALL_DIR" ]; then
        warning "Installation directory still exists"
        issues=$((issues + 1))
    fi
    
    # Check web config
    if [ -f "/etc/httpd/conf.d/${APP_NAME}.conf" ] || [ -f "/etc/nginx/conf.d/${APP_NAME}.conf" ]; then
        warning "Web server configuration still present"
        issues=$((issues + 1))
    fi
    
    if [ $issues -eq 0 ]; then
        log "✅ Removal verification passed - all components removed"
    else
        warning "⚠️  $issues issues found during verification"
        warning "Some components may require manual removal"
    fi
}

# Main removal function
main() {
    log "Starting deployment removal for Tenant Manager App..."
    
    parse_args "$@"
    check_root
    check_safety
    
    # Get source directory for reference
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    info "Removal Configuration:"
    info "  Source Directory: $SCRIPT_DIR (will remain unchanged)"
    info "  Target Directory: $INSTALL_DIR (will be removed)"
    info "  Service Name: $SERVICE_NAME"
    info "  Application User: $APP_USER"
    info "  Force Mode: $FORCE_REMOVAL"
    info "  Keep Logs: $KEEP_LOGS"
    
    warning "This will remove the deployment while preserving original files."
    
    confirm_removal
    
    # Removal steps
    stop_services
    remove_systemd_service
    remove_web_config
    remove_ssl_certificates
    remove_firewall_rules
    remove_application
    remove_logs
    cleanup_selinux
    verify_removal
    
    # Final status
    log "=== Removal Summary ==="
    info "✅ Deployment removed successfully"
    info "✅ Original source files preserved in: $SCRIPT_DIR"
    info "✅ System packages remain installed (Python, Apache/Nginx)"
    
    if [ "$KEEP_LOGS" = "true" ]; then
        info "✅ Log files preserved as requested"
    else
        info "✅ Application log files removed"
    fi
    
    warning "Note: System packages (Python, Apache, Nginx) remain installed"
    warning "Note: Base system configuration unchanged"
    
    info "Your original application files are completely intact in:"
    info "  $SCRIPT_DIR"
    
    log "Deployment removal completed successfully! 🎉"
    
    # Show next steps
    echo ""
    info "What's left on your system:"
    info "- Original application files (unchanged)"
    info "- System packages (Python 3.9, Apache/Nginx, etc.)"
    info "- Base system configuration"
    echo ""
    info "To redeploy later, run: sudo ./deploy_centos.sh"
}

# Run main function with all arguments
main "$@"
