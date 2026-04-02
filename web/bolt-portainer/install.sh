#!/bin/bash

# =============================================================================
# BOLT - Installation Script for Portainer/Docker
# =============================================================================
# Usage:
#   ./install.sh                    - Interactive mode
#   ./install.sh --help             - Show help
#   ./install.sh --non-interactive  - Use defaults or environment variables
# =============================================================================

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging
log() { echo -e "${BLUE}[INSTALL]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${CYAN}[i]${NC} $1"; }

# Default values
DB_NAME="bolt_db"
DB_USER="bolt_user"
DB_PASSWORD=""
DB_PORT="5432"
BACKEND_PORT="3001"
FRONTEND_PORT="80"
NODE_ENV="production"
JWT_SECRET=""
CORS_ORIGIN=""
NON_INTERACTIVE=false

# =============================================================================
# Help Function
# =============================================================================

show_help() {
    cat << EOF
╔══════════════════════════════════════════════════════════════════╗
║                    BOLT Installation Script                      ║
╚══════════════════════════════════════════════════════════════════╝

Usage: ./install.sh [OPTIONS]

Options:
    -h, --help              Show this help message
    -n, --non-interactive   Run in non-interactive mode (use defaults/env vars)
    --db-name NAME          Database name (default: bolt_db)
    --db-user USER          Database user (default: bolt_user)
    --db-password PASS      Database password (required)
    --db-port PORT          Database port (default: 5432)
    --backend-port PORT     Backend API port (default: 3001)
    --frontend-port PORT    Frontend port (default: 80)
    --jwt-secret SECRET     JWT secret key (auto-generated if not provided)
    --cors-origin URL       CORS origin URL

Environment Variables:
    All options can also be set via environment variables:
    DB_NAME, DB_USER, DB_PASSWORD, DB_PORT, BACKEND_PORT, FRONTEND_PORT, JWT_SECRET, CORS_ORIGIN

Examples:
    # Interactive installation
    ./install.sh

    # Non-interactive with all options
    ./install.sh --non-interactive \
        --db-password "secure_password" \
        --backend-port 3001 \
        --frontend-port 8080

    # Using environment variables
    DB_PASSWORD="mypass" BACKEND_PORT=3001 ./install.sh --non-interactive

EOF
}

# =============================================================================
# Parse Arguments
# =============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -n|--non-interactive)
                NON_INTERACTIVE=true
                shift
                ;;
            --db-name)
                DB_NAME="$2"
                shift 2
                ;;
            --db-user)
                DB_USER="$2"
                shift 2
                ;;
            --db-password)
                DB_PASSWORD="$2"
                shift 2
                ;;
            --db-port)
                DB_PORT="$2"
                shift 2
                ;;
            --backend-port)
                BACKEND_PORT="$2"
                shift 2
                ;;
            --frontend-port)
                FRONTEND_PORT="$2"
                shift 2
                ;;
            --jwt-secret)
                JWT_SECRET="$2"
                shift 2
                ;;
            --cors-origin)
                CORS_ORIGIN="$2"
                shift 2
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# =============================================================================
# Load Environment Variables
# =============================================================================

load_env_vars() {
    # Override defaults with environment variables if set
    DB_NAME="${DB_NAME:-${DB_NAME_ENV:-bolt_db}}"
    DB_USER="${DB_USER:-${DB_USER_ENV:-bolt_user}}"
    DB_PASSWORD="${DB_PASSWORD:-$DB_PASSWORD_ENV}"
    DB_PORT="${DB_PORT:-${DB_PORT_ENV:-5432}}"
    BACKEND_PORT="${BACKEND_PORT:-${BACKEND_PORT_ENV:-3001}}"
    FRONTEND_PORT="${FRONTEND_PORT:-${FRONTEND_PORT_ENV:-80}}"
    JWT_SECRET="${JWT_SECRET:-$JWT_SECRET_ENV}"
    CORS_ORIGIN="${CORS_ORIGIN:-$CORS_ORIGIN_ENV}"
}

# =============================================================================
# Validation Functions
# =============================================================================

validate_port() {
    local port=$1
    local name=$2
    
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        error "Invalid $name: $port. Must be a number between 1 and 65535."
        return 1
    fi
    
    # Check if port is already in use
    if command -v lsof &> /dev/null && lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        warn "Port $port is already in use!"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
    
    return 0
}

validate_password() {
    local password=$1
    
    if [ -z "$password" ]; then
        error "Database password cannot be empty"
        return 1
    fi
    
    if [ ${#password} -lt 8 ]; then
        warn "Password is less than 8 characters. Consider using a stronger password."
    fi
    
    return 0
}

# =============================================================================
# Interactive Input
# =============================================================================

interactive_input() {
    echo ""
    info "Database Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    
    # Database name
    read -p "Database name [$DB_NAME]: " input
    DB_NAME="${input:-$DB_NAME}"
    
    # Database user
    read -p "Database user [$DB_USER]: " input
    DB_USER="${input:-$DB_USER}"
    
    # Database password
    while true; do
        read -s -p "Database password (min 8 chars): " input
        echo
        if [ -n "$input" ]; then
            DB_PASSWORD="$input"
            if validate_password "$DB_PASSWORD"; then
                break
            fi
        else
            error "Password is required"
        fi
    done
    
    # Database port
    read -p "Database port [$DB_PORT]: " input
    DB_PORT="${input:-$DB_PORT}"
    validate_port "$DB_PORT" "database port" || exit 1
    
    echo ""
    info "Port Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    
    # Backend port
    read -p "Backend API port [$BACKEND_PORT]: " input
    BACKEND_PORT="${input:-$BACKEND_PORT}"
    validate_port "$BACKEND_PORT" "backend port" || exit 1
    
    # Frontend port
    read -p "Frontend port [$FRONTEND_PORT]: " input
    FRONTEND_PORT="${input:-$FRONTEND_PORT}"
    validate_port "$FRONTEND_PORT" "frontend port" || exit 1
    
    echo ""
    info "Security Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    
    # JWT Secret
    if [ -z "$JWT_SECRET" ]; then
        JWT_SECRET=$(openssl rand -base64 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
        success "Generated JWT secret automatically"
    fi
    
    # CORS Origin
    read -p "CORS origin (e.g., http://localhost, https://yourdomain.com) [$CORS_ORIGIN]: " input
    CORS_ORIGIN="${input:-${CORS_ORIGIN:-http://localhost:$FRONTEND_PORT}}"
}

# =============================================================================
# Generate .env File
# =============================================================================

generate_env_file() {
    log "Generating .env file..."
    
    # Backup existing .env
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        warn "Existing .env backed up"
    fi
    
    cat > "$ENV_FILE" << EOF
# =============================================================================
# BOLT Environment Configuration
# Generated: $(date '+%Y-%m-%d %H:%M:%S')
# =============================================================================

# Database Configuration
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_PORT=$DB_PORT

# Server Configuration
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
NODE_ENV=$NODE_ENV

# Security Configuration
JWT_SECRET=$JWT_SECRET
JWT_EXPIRES_IN=7d

# CORS Configuration
CORS_ORIGIN=$CORS_ORIGIN

# Application Configuration
LOG_LEVEL=info
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# =============================================================================
EOF
    
    chmod 600 "$ENV_FILE"
    success ".env file created at $ENV_FILE"
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

preflight_checks() {
    log "Running pre-flight checks..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    success "Docker found"
    
    # Check Docker Compose
    if docker compose version &> /dev/null; then
        success "Docker Compose (plugin) found"
    elif command -v docker-compose &> /dev/null; then
        success "Docker Compose found"
    else
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    success "Docker daemon is running"
    
    # Check directory structure
    if [ ! -f "$SCRIPT_DIR/docker-compose.yml" ]; then
        error "docker-compose.yml not found in $SCRIPT_DIR"
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p "$SCRIPT_DIR/uploads" "$SCRIPT_DIR/logs" "$SCRIPT_DIR/backups"
    success "Directory structure verified"
}

# =============================================================================
# Build and Start
# =============================================================================

build_and_start() {
    log "Building Docker images..."
    cd "$SCRIPT_DIR"
    
    # Build images
    docker-compose build --no-cache
    success "Docker images built"
    
    log "Starting services..."
    docker-compose up -d
    success "Services started"
    
    # Wait for services
    log "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    local retries=0
    local max_retries=30
    
    while [ $retries -lt $max_retries ]; do
        if docker-compose ps | grep -q "healthy"; then
            success "Services are healthy"
            break
        fi
        
        retries=$((retries + 1))
        log "Waiting for services to become healthy... ($retries/$max_retries)"
        sleep 5
    done
    
    if [ $retries -eq $max_retries ]; then
        warn "Services may not be fully ready yet"
        warn "Check status with: ./manage.sh status"
    fi
}

# =============================================================================
# Print Summary
# =============================================================================

print_summary() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Installation Complete!                        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    info "Service URLs"
    echo "─────────────────────────────────────────────────────────────────────"
    echo -e "  Frontend:    ${CYAN}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "  Backend API: ${CYAN}http://localhost:$BACKEND_PORT${NC}"
    echo -e "  Health:      ${CYAN}http://localhost:$BACKEND_PORT/health${NC}"
    echo ""
    info "Default Credentials"
    echo "─────────────────────────────────────────────────────────────────────"
    echo -e "  Username: ${CYAN}admin${NC}"
    echo -e "  Password: ${CYAN}admin123${NC}"
    echo -e "  ${YELLOW}⚠️  Please change the password after first login!${NC}"
    echo ""
    info "Management Commands"
    echo "─────────────────────────────────────────────────────────────────────"
    echo -e "  Start:   ${CYAN}./manage.sh start${NC}"
    echo -e "  Stop:    ${CYAN}./manage.sh stop${NC}"
    echo -e "  Status:  ${CYAN}./manage.sh status${NC}"
    echo -e "  Logs:    ${CYAN}./manage.sh logs${NC}"
    echo ""
    info "Configuration File"
    echo "─────────────────────────────────────────────────────────────────────"
    echo -e "  ${CYAN}$ENV_FILE${NC}"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo ""
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║   ██████╗  ██████╗ ██╗  ████████╗                               ║"
    echo "║   ██╔══██╗██╔═══██╗██║  ╚══██╔══╝                               ║"
    echo "║   ██████╔╝██║   ██║██║     ██║                                  ║"
    echo "║   ██╔══██╗██║   ██║██║     ██║                                  ║"
    echo "║   ██████╔╝╚██████╔╝███████╗██║                                  ║"
    echo "║   ╚═════╝  ╚═════╝ ╚══════╝╚═╝                                  ║"
    echo "║                                                                  ║"
    echo "║   Installation Script for Portainer/Docker                       ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    
    # Parse arguments
    parse_arguments "$@"
    
    # Load environment variables
    load_env_vars
    
    # Interactive or non-interactive mode
    if [ "$NON_INTERACTIVE" = false ]; then
        interactive_input
    else
        # Validate required fields for non-interactive mode
        if [ -z "$DB_PASSWORD" ]; then
            error "Database password is required in non-interactive mode"
            error "Use --db-password or set DB_PASSWORD environment variable"
            exit 1
        fi
        
        # Generate JWT secret if not provided
        if [ -z "$JWT_SECRET" ]; then
            JWT_SECRET=$(openssl rand -base64 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
        fi
        
        # Set default CORS origin
        if [ -z "$CORS_ORIGIN" ]; then
            CORS_ORIGIN="http://localhost:$FRONTEND_PORT"
        fi
        
        info "Running in non-interactive mode"
    fi
    
    # Run pre-flight checks
    preflight_checks
    
    # Generate .env file
    generate_env_file
    
    # Build and start
    build_and_start
    
    # Print summary
    print_summary
}

# Handle script interruption
trap 'error "Installation interrupted"; exit 1' INT TERM

# Run main
main "$@"
