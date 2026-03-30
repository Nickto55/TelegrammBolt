#!/bin/bash

# =============================================================================
# BOLT - Installation Script
# =============================================================================
# This script installs and configures the BOLT DSE Management System
# with Docker OR native installation, SSL certificates, and database support
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SCRIPT_DIR}"
LOG_FILE="/var/log/bolt-install.log"
BACKUP_DIR="/var/backups/bolt"

# Default values
DOMAIN=""
EMAIL=""
DB_HOST=""
DB_PORT="5432"
DB_NAME="bolt_db"
DB_USER="bolt_user"
DB_PASSWORD=""
BACKEND_PORT="3001"
FRONTEND_PORT="5173"
USE_EXTERNAL_DB=false
USE_SSL=false
USE_DOCKER=true
NODE_VERSION="18"
INSTALL_DIR_SYSTEM="/opt/bolt"

# =============================================================================
# Helper Functions
# =============================================================================

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${CYAN}[i]${NC} $1" | tee -a "$LOG_FILE"
}

print_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║   ██████╗  ██████╗ ██╗  ████████╗                                ║"
    echo "║   ██╔══██╗██╔═══██╗██║  ╚══██╔══╝                                ║"
    echo "║   ██████╔╝██║   ██║██║     ██║                                   ║"
    echo "║   ██╔══██╗██║   ██║██║     ██║                                   ║"
    echo "║   ██████╔╝╚██████╔╝███████╗██║                                   ║"
    echo "║   ╚═════╝  ╚═════╝ ╚══════╝╚═╝                                   ║"
    echo "║                                                                  ║"
    echo "║   Management System - Installation Script                        ║"
    echo "║   Version: 2.1.0                                                 ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# =============================================================================
# Installation Mode Selection
# =============================================================================

ask_installation_mode() {
    echo ""
    log_info "Installation Mode"
    echo "─────────────────────────────────────────────────────────────────────"
    echo -e "${CYAN}Choose installation method:${NC}"
    echo ""
    echo "  [1] Docker (recommended) - Easy setup, isolated containers"
    echo "  [2] Native - Install directly on server (Node.js, PostgreSQL, Nginx)"
    echo ""
    
    read -p "Select option [1]: " choice
    choice=${choice:-1}
    
    case $choice in
        1)
            USE_DOCKER=true
            log "Selected: Docker installation"
            ;;
        2)
            USE_DOCKER=false
            log "Selected: Native installation"
            ;;
        *)
            log_error "Invalid option"
            exit 1
            ;;
    esac
    echo ""
}

# =============================================================================
# Dependency Checks
# =============================================================================

check_root() {
    log "Checking root privileges..."
    if [[ $EUID -eq 0 ]]; then
        if [ "$USE_DOCKER" = false ]; then
            log_warning "Native installation recommended as non-root user with sudo"
        else
            log_warning "Running as root. It's recommended to use a non-root user with sudo."
        fi
        read -p "Continue as root? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    log_success "Privilege check passed"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

check_dependencies() {
    log "Checking system dependencies..."
    
    local missing_deps=()
    
    if [ "$USE_DOCKER" = true ]; then
        # Docker mode checks
        if ! check_command "docker"; then
            missing_deps+=("docker")
        else
            local docker_version=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
            log_success "Docker found: v$docker_version"
        fi
        
        if check_command "docker-compose"; then
            local compose_version=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+' | head -1)
            log_success "Docker Compose found: v$compose_version"
        elif docker compose version &> /dev/null; then
            log_success "Docker Compose (plugin) found"
        else
            missing_deps+=("docker-compose")
        fi
        
        if ! docker info &> /dev/null; then
            log_error "Docker daemon is not running!"
            log_info "Please start Docker: sudo systemctl start docker"
            exit 1
        fi
    else
        # Native mode checks
        if ! check_command "node"; then
            missing_deps+=("nodejs")
        else
            local node_version=$(node --version | grep -oP '\d+' | head -1)
            if [ "$node_version" -lt 18 ]; then
                log_warning "Node.js version $node_version found, but 18+ recommended"
                missing_deps+=("nodejs-upgrade")
            else
                log_success "Node.js found: $(node --version)"
            fi
        fi
        
        if ! check_command "npm"; then
            missing_deps+=("npm")
        else
            log_success "npm found: v$(npm --version)"
        fi
        
        if ! check_command "psql"; then
            missing_deps+=("postgresql")
        else
            log_success "PostgreSQL client found"
        fi
        
        if ! check_command "nginx"; then
            missing_deps+=("nginx")
        else
            log_success "Nginx found: v$(nginx -v 2>&1 | grep -oP '\d+\.\d+\.\d+')"
        fi
        
        if ! check_command "pm2"; then
            missing_deps+=("pm2")
        fi
        
        if ! check_command "systemctl"; then
            log_warning "systemctl not found, will use alternative service management"
        fi
    fi
    
    # Common checks
    if ! check_command "git"; then
        missing_deps+=("git")
    else
        log_success "Git found: v$(git --version | grep -oP '\d+\.\d+\.\d+' | head -1)"
    fi
    
    if ! check_command "curl"; then
        missing_deps+=("curl")
    else
        log_success "curl found"
    fi
    
    if ! check_command "openssl"; then
        missing_deps+=("openssl")
    else
        log_success "OpenSSL found"
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Installing missing dependencies..."
        install_dependencies "${missing_deps[@]}"
    else
        log_success "All dependencies satisfied"
    fi
}

install_dependencies() {
    local deps=("$@")
    
    # Detect OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
    else
        log_error "Cannot detect operating system"
        exit 1
    fi
    
    log "Detected OS: $OS"
    
    for dep in "${deps[@]}"; do
        case $dep in
            docker)
                log "Installing Docker..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    sudo apt-get update
                    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
                    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                    sudo apt-get update
                    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
                    sudo usermod -aG docker $USER
                    log_warning "Please log out and log back in for Docker permissions to take effect"
                elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
                    sudo yum install -y yum-utils
                    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
                    sudo systemctl start docker
                    sudo systemctl enable docker
                    sudo usermod -aG docker $USER
                else
                    log_error "Automatic installation not supported for $OS"
                    exit 1
                fi
                ;;
            docker-compose)
                log "Installing Docker Compose..."
                sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                sudo chmod +x /usr/local/bin/docker-compose
                ;;
            nodejs|nodejs-upgrade)
                log "Installing Node.js ${NODE_VERSION}..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
                    sudo apt-get install -y nodejs
                elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
                    curl -fsSL https://rpm.nodesource.com/setup_${NODE_VERSION}.x | sudo bash -
                    sudo yum install -y nodejs
                fi
                ;;
            npm)
                log "npm will be installed with Node.js"
                ;;
            postgresql)
                log "Installing PostgreSQL..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    sudo apt-get update
                    sudo apt-get install -y postgresql postgresql-contrib
                    sudo systemctl enable postgresql
                    sudo systemctl start postgresql
                elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
                    sudo yum install -y postgresql-server postgresql-contrib
                    sudo postgresql-setup initdb
                    sudo systemctl enable postgresql
                    sudo systemctl start postgresql
                fi
                ;;
            nginx)
                log "Installing Nginx..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    sudo apt-get update && sudo apt-get install -y nginx
                elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
                    sudo yum install -y nginx
                    sudo systemctl enable nginx
                    sudo systemctl start nginx
                fi
                ;;
            pm2)
                log "Installing PM2..."
                sudo npm install -g pm2
                sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME
                ;;
            git)
                log "Installing Git..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    sudo apt-get update && sudo apt-get install -y git
                elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
                    sudo yum install -y git
                fi
                ;;
            curl)
                log "Installing curl..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    sudo apt-get update && sudo apt-get install -y curl
                elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
                    sudo yum install -y curl
                fi
                ;;
            openssl)
                log "Installing OpenSSL..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    sudo apt-get update && sudo apt-get install -y openssl
                elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
                    sudo yum install -y openssl
                fi
                ;;
        esac
    done
    
    log_success "Dependencies installed successfully"
}

# =============================================================================
# Configuration Functions
# =============================================================================

ask_domain() {
    echo ""
    log_info "Domain Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    read -p "Do you want to configure a custom domain? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your domain (e.g., bolt.example.com): " DOMAIN
        
        if [ -z "$DOMAIN" ]; then
            log_error "Domain cannot be empty"
            exit 1
        fi
        
        if ! [[ "$DOMAIN" =~ ^[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)*$ ]]; then
            log_error "Invalid domain format"
            exit 1
        fi
        
        log "Domain set to: $DOMAIN"
        
        read -p "Do you want to enable SSL with Let's Encrypt? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            USE_SSL=true
            read -p "Enter email for Let's Encrypt notifications: " EMAIL
            if [ -z "$EMAIL" ]; then
                log_error "Email is required for Let's Encrypt"
                exit 1
            fi
            log "SSL will be configured with Let's Encrypt"
        fi
    else
        DOMAIN="localhost"
        log "Using localhost (no domain configured)"
    fi
}

ask_database() {
    echo ""
    log_info "Database Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    
    if [ "$USE_DOCKER" = false ]; then
        log_info "Native mode: PostgreSQL must be installed on this server"
        read -p "Use local PostgreSQL or external database? (local/external) [local]: " db_choice
        db_choice=${db_choice:-local}
        
        if [[ "$db_choice" == "external" ]]; then
            USE_EXTERNAL_DB=true
        else
            USE_EXTERNAL_DB=false
            DB_HOST="localhost"
            DB_PORT="5432"
            
            # Check if PostgreSQL is running
            if ! sudo systemctl is-active --quiet postgresql 2>/dev/null; then
                log_warning "PostgreSQL service not running, attempting to start..."
                sudo systemctl start postgresql
            fi
        fi
    else
        read -p "Do you have an external PostgreSQL database? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            USE_EXTERNAL_DB=true
        fi
    fi
    
    if [ "$USE_EXTERNAL_DB" = true ]; then
        read -p "Enter database host (IP or hostname): " DB_HOST
        if [ -z "$DB_HOST" ]; then
            log_error "Database host cannot be empty"
            exit 1
        fi
        
        read -p "Enter database port [5432]: " DB_PORT
        DB_PORT=${DB_PORT:-5432}
        
        read -p "Enter database name [bolt_db]: " DB_NAME
        DB_NAME=${DB_NAME:-bolt_db}
        
        read -p "Enter database user [bolt_user]: " DB_USER
        DB_USER=${DB_USER:-bolt_user}
        
        read -s -p "Enter database password: " DB_PASSWORD
        echo
        if [ -z "$DB_PASSWORD" ]; then
            log_error "Database password cannot be empty"
            exit 1
        fi
        
        # Test connection
        log "Testing database connection..."
        if command -v psql &> /dev/null; then
            export PGPASSWORD="$DB_PASSWORD"
            if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
                log_success "Database connection successful"
            else
                log_warning "Could not connect to database"
                read -p "Continue anyway? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
            unset PGPASSWORD
        fi
    else
        if [ "$USE_DOCKER" = true ]; then
            log "Using built-in PostgreSQL container"
            DB_HOST="postgres"
            DB_PORT="5432"
            DB_NAME="bolt_db"
            DB_USER="bolt_user"
            DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
        else
            log "Using local PostgreSQL"
            DB_HOST="localhost"
            DB_PORT="5432"
            DB_NAME="bolt_db"
            DB_USER="bolt_user"
            DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
            
            # Create database and user
            setup_local_postgres
        fi
    fi
}

setup_local_postgres() {
    log "Setting up local PostgreSQL database..."
    
    # Create user and database
    sudo -u postgres psql << EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF
    
    # Configure pg_hba.conf for local connections
    local pg_hba_path=$(sudo -u postgres psql -t -c "SHOW hba_file;" 2>/dev/null | xargs)
    if [ -f "$pg_hba_path" ]; then
        log "Configuring PostgreSQL authentication..."
        # Backup original
        sudo cp "$pg_hba_path" "${pg_hba_path}.backup"
        # Allow local connections with md5
        sudo bash -c "echo 'local   all             all                                     md5' >> $pg_hba_path"
        sudo systemctl reload postgresql
    fi
    
    log_success "Local PostgreSQL configured"
}

ask_ports() {
    echo ""
    log_info "Port Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    
    read -p "Backend API port [3001]: " BACKEND_PORT
    BACKEND_PORT=${BACKEND_PORT:-3001}
    
    if [ "$USE_DOCKER" = true ]; then
        read -p "Frontend port [5173]: " FRONTEND_PORT
        FRONTEND_PORT=${FRONTEND_PORT:-5173}
    else
        FRONTEND_PORT="80"
        log "Native mode: Frontend will be served by Nginx on port 80/443"
    fi
    
    # Check if ports are available
    if check_command "lsof"; then
        if lsof -Pi :"$BACKEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warning "Port $BACKEND_PORT is already in use!"
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
        
        if [ "$USE_DOCKER" = true ]; then
            if lsof -Pi :"$FRONTEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
                log_warning "Port $FRONTEND_PORT is already in use!"
                read -p "Continue anyway? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
        fi
    fi
    
    log "Backend port: $BACKEND_PORT"
    [ "$USE_DOCKER" = true ] && log "Frontend port: $FRONTEND_PORT"
}

# =============================================================================
# SSL Certificate Functions
# =============================================================================

setup_ssl() {
    if [ "$USE_SSL" = false ]; then
        return 0
    fi
    
    log "Setting up SSL certificates with Let's Encrypt..."
    
    if ! check_command "certbot"; then
        log "Installing Certbot..."
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            if [[ "$NAME" == *"Ubuntu"* ]] || [[ "$NAME" == *"Debian"* ]]; then
                sudo apt-get update
                sudo apt-get install -y certbot python3-certbot-nginx
            elif [[ "$NAME" == *"CentOS"* ]] || [[ "$NAME" == *"Red Hat"* ]] || [[ "$NAME" == *"Fedora"* ]]; then
                sudo yum install -y certbot python3-certbot-nginx
            fi
        fi
    fi
    
    if [ "$USE_DOCKER" = true ]; then
        # Docker mode: certificates for Nginx container
        sudo mkdir -p "$INSTALL_DIR/nginx/ssl"
        
        if sudo certbot certonly --standalone -d "$DOMAIN" --agree-tos --email "$EMAIL" --non-interactive; then
            log_success "SSL certificate obtained successfully"
            
            sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$INSTALL_DIR/nginx/ssl/"
            sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$INSTALL_DIR/nginx/ssl/"
            sudo chmod 644 "$INSTALL_DIR/nginx/ssl/fullchain.pem"
            sudo chmod 600 "$INSTALL_DIR/nginx/ssl/privkey.pem"
            
            # Setup auto-renewal for Docker
            (sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --deploy-hook 'docker-compose -f $INSTALL_DIR/docker-compose.yml restart nginx'") | sudo crontab -
        else
            log_error "Failed to obtain SSL certificate"
            exit 1
        fi
    else
        # Native mode: use certbot with Nginx plugin
        if sudo certbot --nginx -d "$DOMAIN" --agree-tos --email "$EMAIL" --non-interactive; then
            log_success "SSL certificate obtained and configured"
            
            # Setup auto-renewal
            (sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet") | sudo crontab -
        else
            log_error "Failed to obtain SSL certificate"
            exit 1
        fi
    fi
    
    log_success "SSL auto-renewal configured"
}

# =============================================================================
# Docker Configuration
# =============================================================================

generate_env_file() {
    log "Generating environment configuration..."
    
    local jwt_secret=$(openssl rand -base64 32)
    local env_path="$INSTALL_DIR/.env"
    
    [ "$USE_DOCKER" = false ] && env_path="$INSTALL_DIR_SYSTEM/.env"
    
    cat > "$env_path" << EOF
# =============================================================================
# BOLT Environment Configuration
# Generated: $(date)
# Installation Mode: $([ "$USE_DOCKER" = true ] && echo "Docker" || echo "Native")
# =============================================================================

# Domain Configuration
DOMAIN=$DOMAIN
USE_SSL=$USE_SSL

# Database Configuration
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# JWT Configuration
JWT_SECRET=$jwt_secret
JWT_EXPIRES_IN=7d

# Server Configuration
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
NODE_ENV=production

# CORS
CORS_ORIGIN=$([ "$USE_DOCKER" = true ] && echo "http://localhost:$FRONTEND_PORT" || echo "https://$DOMAIN")

# Email for Let's Encrypt
LETSENCRYPT_EMAIL=$EMAIL

# File Upload
UPLOAD_DIR=$([ "$USE_DOCKER" = true ] && echo "./uploads" || echo "/opt/bolt/uploads")
MAX_FILE_SIZE=10485760

# =============================================================================
EOF
    
    log_success "Environment file created"
}

generate_docker_compose() {
    log "Generating Docker Compose configuration..."
    
    if [ "$USE_EXTERNAL_DB" = true ]; then
        cat > "$INSTALL_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: ./bolt-backend
      dockerfile: Dockerfile
    container_name: bolt-backend
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - NODE_ENV=production
      - PORT=3001
    ports:
      - "${BACKEND_PORT}:3001"
    volumes:
      - backend_uploads:/app/uploads
      - ./logs:/app/logs
    networks:
      - bolt-network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: nginx:alpine
    container_name: bolt-frontend
    restart: unless-stopped
    ports:
      - "${FRONTEND_PORT}:80"
    volumes:
      - ./app/dist:/usr/share/nginx/html:ro
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
    networks:
      - bolt-network

volumes:
  backend_uploads:
    driver: local

networks:
  bolt-network:
    driver: bridge
EOF
    else
        cat > "$INSTALL_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: bolt-postgres
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "${DB_PORT}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - bolt-network

  backend:
    build:
      context: ./bolt-backend
      dockerfile: Dockerfile
    container_name: bolt-backend
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - NODE_ENV=production
      - PORT=3001
      - DB_HOST=postgres
    ports:
      - "${BACKEND_PORT}:3001"
    volumes:
      - backend_uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - bolt-network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: nginx:alpine
    container_name: bolt-frontend
    restart: unless-stopped
    ports:
      - "${FRONTEND_PORT}:80"
    volumes:
      - ./app/dist:/usr/share/nginx/html:ro
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
    networks:
      - bolt-network

volumes:
  postgres_data:
    driver: local
  backend_uploads:
    driver: local

networks:
  bolt-network:
    driver: bridge
EOF
    fi
    
    log_success "Docker Compose file created"
}

generate_nginx_config() {
    log "Generating Nginx configuration..."
    
    if [ "$USE_DOCKER" = true ]; then
        mkdir -p "$INSTALL_DIR/nginx"
        local nginx_conf_path="$INSTALL_DIR/nginx/nginx.conf"
    else
        sudo mkdir -p "/etc/nginx/sites-available" "/etc/nginx/sites-enabled"
        local nginx_conf_path="/etc/nginx/sites-available/bolt"
    fi
    
    if [ "$USE_SSL" = true ]; then
        cat > "$nginx_conf_path" << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\\\$server_name\\\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate $([ "$USE_DOCKER" = true ] && echo "/etc/nginx/ssl/fullchain.pem" || echo "/etc/letsencrypt/live/$DOMAIN/fullchain.pem");
    ssl_certificate_key $([ "$USE_DOCKER" = true ] && echo "/etc/nginx/ssl/privkey.pem" || echo "/etc/letsencrypt/live/$DOMAIN/privkey.pem");
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    root $([ "$USE_DOCKER" = true ] && echo "/usr/share/nginx/html" || echo "/opt/bolt/frontend/dist");
    index index.html;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    location / {
        try_files \\\$uri \\\$uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    location /api {
        proxy_pass http://$([ "$USE_DOCKER" = true ] && echo "backend" || echo "localhost"):$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_cache_bypass \\\$http_upgrade;
        proxy_read_timeout 86400;
    }

    location /socket.io {
        proxy_pass http://$([ "$USE_DOCKER" = true ] && echo "backend" || echo "localhost"):$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_read_timeout 86400;
    }

    location ~* \\\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    else
        cat > "$nginx_conf_path" << EOF
server {
    listen 80;
    server_name $([ "$USE_DOCKER" = true ] && echo "localhost" || echo "$DOMAIN");

    root $([ "$USE_DOCKER" = true ] && echo "/usr/share/nginx/html" || echo "/opt/bolt/frontend/dist");
    index index.html;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    location / {
        try_files \\\$uri \\\$uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    location /api {
        proxy_pass http://$([ "$USE_DOCKER" = true ] && echo "backend" || echo "localhost"):$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_cache_bypass \\\$http_upgrade;
        proxy_read_timeout 86400;
    }

    location /socket.io {
        proxy_pass http://$([ "$USE_DOCKER" = true ] && echo "backend" || echo "localhost"):$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_read_timeout 86400;
    }

    location ~* \\\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    fi
    
    # For native mode, enable the site
    if [ "$USE_DOCKER" = false ]; then
        sudo ln -sf "$nginx_conf_path" "/etc/nginx/sites-enabled/bolt"
        # Remove default site if exists
        sudo rm -f "/etc/nginx/sites-enabled/default"
        sudo nginx -t && sudo systemctl reload nginx
    fi
    
    log_success "Nginx configuration created"
}

# =============================================================================
# Native Installation Functions
# =============================================================================

setup_directories_native() {
    log "Setting up directories for native installation..."
    
    sudo mkdir -p "$INSTALL_DIR_SYSTEM"
    sudo mkdir -p "$INSTALL_DIR_SYSTEM/backend"
    sudo mkdir -p "$INSTALL_DIR_SYSTEM/frontend"
    sudo mkdir -p "$INSTALL_DIR_SYSTEM/uploads"
    sudo mkdir -p "$INSTALL_DIR_SYSTEM/logs"
    sudo mkdir -p "/var/log/bolt"
    
    # Set permissions
    sudo chown -R $USER:$USER "$INSTALL_DIR_SYSTEM"
    
    log_success "Directories created at $INSTALL_DIR_SYSTEM"
}

install_backend_native() {
    log "Installing backend (native)..."
    
    cd "$INSTALL_DIR"
    
    if [ -d "bolt-backend" ]; then
        log "Building backend from local source..."
        cd bolt-backend
        
        # Install dependencies
        npm ci
        
        # Build application
        npm run build
        
        # Copy to system directory
        cp -r dist/* "$INSTALL_DIR_SYSTEM/backend/"
        cp -r node_modules "$INSTALL_DIR_SYSTEM/backend/"
        cp package.json "$INSTALL_DIR_SYSTEM/backend/"
        
        cd ..
    else
        log_error "Backend source not found at ./bolt-backend"
        exit 1
    fi
    
    log_success "Backend installed"
}

install_frontend_native() {
    log "Installing frontend (native)..."
    
    cd "$INSTALL_DIR"
    
    if [ -d "app" ]; then
        log "Building frontend from local source..."
        cd app
        
        # Install dependencies
        npm ci
        
        # Build application
        npm run build
        
        # Copy to system directory
        cp -r dist/* "$INSTALL_DIR_SYSTEM/frontend/"
        
        cd ..
    else
        log_warning "Frontend source not found at ./app, skipping..."
    fi
    
    log_success "Frontend installed"
}

create_systemd_services() {
    log "Creating systemd services..."
    
    # Backend service
    sudo tee /etc/systemd/system/bolt-backend.service > /dev/null << EOF
[Unit]
Description=BOLT Backend API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR_SYSTEM/backend
Environment=NODE_ENV=production
EnvironmentFile=$INSTALL_DIR_SYSTEM/.env
ExecStart=/usr/bin/node $INSTALL_DIR_SYSTEM/backend/main.js
Restart=always
RestartSec=10
StandardOutput=append:/var/log/bolt/backend.log
StandardError=append:/var/log/bolt/backend-error.log

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable bolt-backend
    
    log_success "Systemd services created"
}

create_pm2_config() {
    log "Creating PM2 configuration..."
    
    cat > "$INSTALL_DIR_SYSTEM/ecosystem.config.js" << EOF
module.exports = {
  apps: [{
    name: 'bolt-backend',
    script: '$INSTALL_DIR_SYSTEM/backend/main.js',
    instances: 1,
    exec_mode: 'fork',
    env: {
      NODE_ENV: 'production'
    },
    env_file: '$INSTALL_DIR_SYSTEM/.env',
    log_file: '/var/log/bolt/backend.log',
    error_file: '/var/log/bolt/backend-error.log',
    out_file: '/var/log/bolt/backend.log',
    merge_logs: true,
    time: true,
    restart_delay: 3000,
    max_restarts: 5,
    min_uptime: '10s'
  }]
};
EOF

    log_success "PM2 configuration created"
}

start_services_native() {
    log "Starting services (native)..."
    
    # Start backend with PM2 or systemd
    if check_command "pm2"; then
        cd "$INSTALL_DIR_SYSTEM"
        pm2 start ecosystem.config.js
        pm2 save
        sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME
    else
        sudo systemctl start bolt-backend
    fi
    
    # Ensure Nginx is running
    if check_command "systemctl"; then
        sudo systemctl restart nginx
    fi
    
    log_success "Services started"
}

# =============================================================================
# Docker Installation Functions
# =============================================================================

build_images() {
    log "Building Docker images..."
    
    cd "$INSTALL_DIR"
    docker-compose build backend
    log_success "Docker images built successfully"
}

start_services_docker() {
    log "Starting BOLT services (Docker)..."
    
    cd "$INSTALL_DIR"
    
    mkdir -p logs uploads
    
    docker-compose pull
    docker-compose up -d
    
    log_success "Services started"
}

wait_for_services_docker() {
    log "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
            log_success "Backend is ready"
            break
        fi
        
        log "Waiting for backend... ($attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Backend failed to start within expected time"
        return 1
    fi
    
    if [ "$USE_EXTERNAL_DB" = false ]; then
        attempt=1
        while [ $attempt -le $max_attempts ]; do
            if docker-compose exec -T postgres pg_isready -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
                log_success "Database is ready"
                break
            fi
            
            log "Waiting for database... ($attempt/$max_attempts)"
            sleep 2
            attempt=$((attempt + 1))
        done
        
        if [ $attempt -gt $max_attempts ]; then
            log_error "Database failed to start within expected time"
            return 1
        fi
    fi
    
    return 0
}

# =============================================================================
# Service Checks
# =============================================================================

check_services() {
    echo ""
    log_info "Service Status Check"
    echo "─────────────────────────────────────────────────────────────────────"
    
    local all_ok=true
    
    # Check Backend
    if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
        log_success "Backend API: http://localhost:$BACKEND_PORT ✓"
    else
        log_error "Backend API: Not responding ✗"
        all_ok=false
    fi
    
    # Check Frontend
    local frontend_url=$([ "$USE_DOCKER" = true ] && echo "http://localhost:$FRONTEND_PORT" || echo "http://localhost")
    if curl -s "$frontend_url" > /dev/null 2>&1; then
        log_success "Frontend: $frontend_url ✓"
    else
        log_error "Frontend: Not responding ✗"
        all_ok=false
    fi
    
    # Check Database
    if [ "$USE_EXTERNAL_DB" = true ]; then
        export PGPASSWORD="$DB_PASSWORD"
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
            log_success "External Database: Connected ✓"
        else
            log_error "External Database: Connection failed ✗"
            all_ok=false
        fi
        unset PGPASSWORD
    else
        if [ "$USE_DOCKER" = true ]; then
            if docker-compose exec -T postgres pg_isready -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
                log_success "Database Container: Running ✓"
            else
                log_error "Database Container: Not responding ✗"
                all_ok=false
            fi
        else
            if sudo -u postgres psql -c "SELECT 1;" > /dev/null 2>&1; then
                log_success "Local PostgreSQL: Running ✓"
            else
                log_error "Local PostgreSQL: Not responding ✗"
                all_ok=false
            fi
        fi
    fi
    
    if [ "$all_ok" = true ]; then
        return 0
    else
        return 1
    fi
}

# =============================================================================
# Backup Functions
# =============================================================================

setup_backups() {
    log "Setting up automatic backups..."
    
    mkdir -p "$BACKUP_DIR"
    
    if [ "$USE_DOCKER" = true ]; then
        # Docker backup script
        cat > "$INSTALL_DIR/backup.sh" << EOF
#!/bin/bash
BACKUP_DIR="$BACKUP_DIR"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p "\$BACKUP_DIR"

if [ -f .env ]; then
    source .env
    if [ "\$USE_EXTERNAL_DB" = "true" ]; then
        PGPASSWORD="\$DB_PASSWORD" pg_dump -h "\$DB_HOST" -p "\$DB_PORT" -U "\$DB_USER" -d "\$DB_NAME" > "\$BACKUP_DIR/db_backup_\$DATE.sql"
    else
        docker-compose exec -T postgres pg_dump -U "\$DB_USER" -d "\$DB_NAME" > "\$BACKUP_DIR/db_backup_\$DATE.sql"
    fi
    gzip "\$BACKUP_DIR/db_backup_\$DATE.sql"
fi

tar -czf "\$BACKUP_DIR/uploads_backup_\$DATE.tar.gz" -C "\$(dirname "\$0")" uploads 2>/dev/null || true

find "\$BACKUP_DIR" -name "*.gz" -mtime +7 -delete

echo "Backup completed: \$DATE"
EOF
        chmod +x "$INSTALL_DIR/backup.sh"
        (crontab -l 2>/dev/null; echo "0 2 * * * $INSTALL_DIR/backup.sh >> /var/log/bolt-backup.log 2>&1") | crontab -
    else
        # Native backup script
        cat > "$INSTALL_DIR_SYSTEM/backup.sh" << EOF
#!/bin/bash
BACKUP_DIR="$BACKUP_DIR"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p "\$BACKUP_DIR"

source $INSTALL_DIR_SYSTEM/.env

if [ "\$USE_EXTERNAL_DB" != "true" ]; then
    sudo -u postgres pg_dump -U "\$DB_USER" -d "\$DB_NAME" > "\$BACKUP_DIR/db_backup_\$DATE.sql"
    gzip "\$BACKUP_DIR/db_backup_\$DATE.sql"
fi

tar -czf "\$BACKUP_DIR/uploads_backup_\$DATE.tar.gz" -C "$INSTALL_DIR_SYSTEM" uploads 2>/dev/null || true

find "\$BACKUP_DIR" -name "*.gz" -mtime +7 -delete

echo "Backup completed: \$DATE"
EOF
        chmod +x "$INSTALL_DIR_SYSTEM/backup.sh"
        (crontab -l 2>/dev/null; echo "0 2 * * * $INSTALL_DIR_SYSTEM/backup.sh >> /var/log/bolt-backup.log 2>&1") | crontab -
    fi
    
    log_success "Automatic backups configured (daily at 2:00 AM)"
}

# =============================================================================
# Summary
# =============================================================================

print_summary() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Installation Complete!                        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    log_info "Installation Mode: $([ "$USE_DOCKER" = true ] && echo "Docker" || echo "Native")"
    echo ""
    log_info "Access Information"
    echo "─────────────────────────────────────────────────────────────────────"
    
    if [ "$USE_DOCKER" = true ]; then
        echo -e "  ${CYAN}Frontend:${NC}    http://localhost:$FRONTEND_PORT"
    else
        echo -e "  ${CYAN}Frontend:${NC}    http://localhost (Nginx)"
        [ "$USE_SSL" = true ] && echo -e "  ${CYAN}HTTPS:${NC}       https://$DOMAIN"
    fi
    
    echo -e "  ${CYAN}Backend API:${NC} http://localhost:$BACKEND_PORT/api"
    echo -e "  ${CYAN}Health Check:${NC} http://localhost:$BACKEND_PORT/health"
    
    if [ "$USE_SSL" = true ]; then
        echo ""
        log_info "SSL Configuration"
        echo "─────────────────────────────────────────────────────────────────────"
        echo -e "  ${CYAN}Domain:${NC} https://$DOMAIN"
    fi
    
    echo ""
    log_info "Default Login Credentials"
    echo "─────────────────────────────────────────────────────────────────────"
    echo -e "  ${CYAN}Username:${NC} admin"
    echo -e "  ${CYAN}Password:${NC} admin123"
    echo -e "  ${YELLOW}⚠ Please change the password after first login!${NC}"
    
    echo ""
    log_info "Useful Commands"
    echo "─────────────────────────────────────────────────────────────────────"
    
    if [ "$USE_DOCKER" = true ]; then
        echo -e "  ${CYAN}View logs:${NC}        cd $INSTALL_DIR && docker-compose logs -f"
        echo -e "  ${CYAN}Stop services:${NC}    cd $INSTALL_DIR && docker-compose down"
        echo -e "  ${CYAN}Restart:${NC}          cd $INSTALL_DIR && docker-compose restart"
        echo -e "  ${CYAN}Update:${NC}           cd $INSTALL_DIR && docker-compose pull && docker-compose up -d"
        echo -e "  ${CYAN}Backup:${NC}           $INSTALL_DIR/backup.sh"
    else
        echo -e "  ${CYAN}View logs:${NC}        tail -f /var/log/bolt/backend.log"
        if check_command "pm2"; then
            echo -e "  ${CYAN}PM2 status:${NC}       pm2 status"
            echo -e "  ${CYAN}Restart backend:${NC}  pm2 restart bolt-backend"
            echo -e "  ${CYAN}Stop backend:${NC}   pm2 stop bolt-backend"
        else
            echo -e "  ${CYAN}Restart backend:${NC}  sudo systemctl restart bolt-backend"
            echo -e "  ${CYAN}Stop backend:${NC}   sudo systemctl stop bolt-backend"
        fi
        echo -e "  ${CYAN}Nginx reload:${NC}    sudo systemctl reload nginx"
        echo -e "  ${CYAN}Backup:${NC}           $INSTALL_DIR_SYSTEM/backup.sh"
    fi
    
    echo ""
    log_info "Configuration Files"
    echo "─────────────────────────────────────────────────────────────────────"
    
    if [ "$USE_DOCKER" = true ]; then
        echo -e "  ${CYAN}Environment:${NC}     $INSTALL_DIR/.env"
        echo -e "  ${CYAN}Docker Compose:${NC}  $INSTALL_DIR/docker-compose.yml"
        echo -e "  ${CYAN}Nginx Config:${NC}   $INSTALL_DIR/nginx/nginx.conf"
    else
        echo -e "  ${CYAN}Environment:${NC}     $INSTALL_DIR_SYSTEM/.env"
        echo -e "  ${CYAN}Backend:${NC}        $INSTALL_DIR_SYSTEM/backend/"
        echo -e "  ${CYAN}Frontend:${NC}       $INSTALL_DIR_SYSTEM/frontend/"
        echo -e "  ${CYAN}Nginx Config:${NC}   /etc/nginx/sites-available/bolt"
        if check_command "pm2"; then
            echo -e "  ${CYAN}PM2 Config:${NC}     $INSTALL_DIR_SYSTEM/ecosystem.config.js"
        else
            echo -e "  ${CYAN}Systemd Service:${NC} /etc/systemd/system/bolt-backend.service"
        fi
    fi
    
    if [ "$USE_EXTERNAL_DB" = false ]; then
        echo ""
        log_info "Database Information"
        echo "─────────────────────────────────────────────────────────────────────"
        if [ "$USE_DOCKER" = true ]; then
            echo -e "  ${CYAN}Host:${NC}     localhost (Docker container)"
        else
            echo -e "  ${CYAN}Host:${NC}     localhost (PostgreSQL service)"
        fi
        echo -e "  ${CYAN}Port:${NC}     $DB_PORT"
        echo -e "  ${CYAN}Database:${NC} $DB_NAME"
        echo -e "  ${CYAN}User:${NC}     $DB_USER"
    fi
    
    echo ""
    echo -e "${GREEN}Thank you for installing BOLT!${NC}"
    echo ""
}

# =============================================================================
# Main Installation Flow
# =============================================================================

main() {
    # Create log directory
    sudo mkdir -p "$(dirname "$LOG_FILE")"
    sudo touch "$LOG_FILE"
    sudo chmod 666 "$LOG_FILE"
    
    print_banner
    
    log "Starting BOLT installation..."
    log "Installation directory: $INSTALL_DIR"
    log "Log file: $LOG_FILE"
    
    # Choose installation mode first
    ask_installation_mode
    
    # Pre-installation checks
    check_root
    check_dependencies
    
    # Configuration
    ask_domain
    ask_database
    ask_ports
    
    # SSL Setup
    if [ "$USE_SSL" = true ]; then
        setup_ssl
    fi
    
    # Generate environment file
    generate_env_file
    
    if [ "$USE_DOCKER" = true ]; then
        # Docker installation
        generate_docker_compose
        generate_nginx_config
        build_images
        start_services_docker
        
        if wait_for_services_docker; then
            setup_backups
            check_services
            print_summary
        else
            log_error "Installation completed with errors"
            exit 1
        fi
    else
        # Native installation
        setup_directories_native
        generate_nginx_config
        install_backend_native
        install_frontend_native
        
        if check_command "pm2"; then
            create_pm2_config
        else
            create_systemd_services
        fi
        
        start_services_native
        setup_backups
        check_services
        print_summary
    fi
}

# Handle script interruption
trap 'log_error "Installation interrupted"; exit 1' INT TERM

# Run main function
main "$@"