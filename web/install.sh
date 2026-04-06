#!/bin/bash

# =============================================================================
# BOLT - Installation Script
# =============================================================================
# This script installs and configures the BOLT DSE Management System
# with Docker, SSL certificates, and external database support
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
    echo "║   DSE Management System - Installation Script                    ║"
    echo "║   Version: 2.0.0                                                 ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# =============================================================================
# Dependency Checks
# =============================================================================

check_root() {
    log "Checking root privileges..."
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. It's recommended to use a non-root user with sudo."
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
    
    # Check Docker
    if ! check_command "docker"; then
        missing_deps+=("docker")
    else
        local docker_version=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
        log_success "Docker found: v$docker_version"
    fi
    
    # Check Docker Compose
    if check_command "docker-compose"; then
        local compose_version=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+' | head -1)
        log_success "Docker Compose found: v$compose_version"
    elif docker compose version &> /dev/null; then
        log_success "Docker Compose (plugin) found"
    else
        missing_deps+=("docker-compose")
    fi
    
    # Check Git
    if ! check_command "git"; then
        missing_deps+=("git")
    else
        local git_version=$(git --version | grep -oP '\d+\.\d+\.\d+' | head -1)
        log_success "Git found: v$git_version"
    fi
    
    # Check curl
    if ! check_command "curl"; then
        missing_deps+=("curl")
    else
        log_success "curl found"
    fi
    
    # Check OpenSSL (for SSL certificates)
    if ! check_command "openssl"; then
        missing_deps+=("openssl")
    else
        log_success "OpenSSL found"
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running!"
        log_info "Please start Docker: sudo systemctl start docker"
        exit 1
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
                    log_info "Please install Docker manually: https://docs.docker.com/get-docker/"
                    exit 1
                fi
                ;;
            docker-compose)
                log "Installing Docker Compose..."
                sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                sudo chmod +x /usr/local/bin/docker-compose
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
        
        # Validate domain format
        if ! [[ "$DOMAIN" =~ ^[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)*$ ]]; then
            log_error "Invalid domain format"
            exit 1
        fi
        
        log "Domain set to: $DOMAIN"
        
        # Ask for SSL
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
    
    read -p "Do you have an external PostgreSQL database? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        USE_EXTERNAL_DB=true
        
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
            if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
                log_success "Database connection successful"
            else
                log_warning "Could not connect to database. Please ensure:"
                log_info "  - Database server is running"
                log_info "  - Credentials are correct"
                log_info "  - Firewall allows connection on port $DB_PORT"
                log_info "  - PostgreSQL accepts remote connections"
                read -p "Continue anyway? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
        else
            log_warning "psql not found, skipping connection test"
        fi
    else
        log "Using built-in PostgreSQL container"
        DB_HOST="postgres"
        DB_PORT="5432"
        DB_NAME="bolt_db"
        DB_USER="bolt_user"
        DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
    fi
}

ask_ports() {
    echo ""
    log_info "Port Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    
    read -p "Backend API port [3001]: " BACKEND_PORT
    BACKEND_PORT=${BACKEND_PORT:-3001}
    
    read -p "Frontend port [5173]: " FRONTEND_PORT
    FRONTEND_PORT=${FRONTEND_PORT:-5173}
    
    # Check if ports are available
    if lsof -Pi :"$BACKEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "Port $BACKEND_PORT is already in use!"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    if lsof -Pi :"$FRONTEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "Port $FRONTEND_PORT is already in use!"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log "Backend port: $BACKEND_PORT"
    log "Frontend port: $FRONTEND_PORT"
}

# =============================================================================
# SSL Certificate Functions
# =============================================================================

setup_ssl() {
    if [ "$USE_SSL" = false ]; then
        return 0
    fi
    
    log "Setting up SSL certificates with Let's Encrypt..."
    
    # Install certbot if not present
    if ! check_command "certbot"; then
        log "Installing Certbot..."
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            if [[ "$NAME" == *"Ubuntu"* ]] || [[ "$NAME" == *"Debian"* ]]; then
                sudo apt-get update
                sudo apt-get install -y certbot
            elif [[ "$NAME" == *"CentOS"* ]] || [[ "$NAME" == *"Red Hat"* ]] || [[ "$NAME" == *"Fedora"* ]]; then
                sudo yum install -y certbot
            fi
        fi
    fi
    
    # Create directories
    sudo mkdir -p "/etc/letsencrypt/live/$DOMAIN"
    sudo mkdir -p "$INSTALL_DIR/nginx/ssl"
    
    # Stop any service on port 80 temporarily
    log "Obtaining SSL certificate for $DOMAIN..."
    
    # Use standalone mode for initial certificate
    if sudo certbot certonly --standalone -d "$DOMAIN" --agree-tos --email "$EMAIL" --non-interactive; then
        log_success "SSL certificate obtained successfully"
        
        # Copy certificates
        sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$INSTALL_DIR/nginx/ssl/"
        sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$INSTALL_DIR/nginx/ssl/"
        sudo chmod 644 "$INSTALL_DIR/nginx/ssl/fullchain.pem"
        sudo chmod 600 "$INSTALL_DIR/nginx/ssl/privkey.pem"
        
        # Setup auto-renewal
        log "Setting up certificate auto-renewal..."
        (sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --deploy-hook 'docker-compose -f $INSTALL_DIR/docker-compose.yml restart nginx'") | sudo crontab -
        
        log_success "SSL auto-renewal configured"
    else
        log_error "Failed to obtain SSL certificate"
        log_info "Please ensure:"
        log_info "  - Domain $DOMAIN points to this server"
        log_info "  - Port 80 is open in firewall"
        log_info "  - No other service is using port 80"
        exit 1
    fi
}

# =============================================================================
# Docker Configuration
# =============================================================================

generate_env_file() {
    log "Generating environment configuration..."
    
    local jwt_secret=$(openssl rand -base64 32)
    
    cat > "$INSTALL_DIR/.env" << EOF
# =============================================================================
# BOLT Environment Configuration
# Generated: $(date)
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
CORS_ORIGIN=http://localhost:$FRONTEND_PORT

# Email for Let's Encrypt
LETSENCRYPT_EMAIL=$EMAIL

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# =============================================================================
EOF
    
    log_success "Environment file created at $INSTALL_DIR/.env"
}

generate_docker_compose() {
    log "Generating Docker Compose configuration..."
    
    if [ "$USE_EXTERNAL_DB" = true ]; then
        # Without PostgreSQL service
        cat > "$INSTALL_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  # Backend API
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

  # Frontend
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
        # With PostgreSQL service
        cat > "$INSTALL_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database
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

  # Backend API
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

  # Frontend
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
    
    mkdir -p "$INSTALL_DIR/nginx"
    
    if [ "$USE_SSL" = true ]; then
        cat > "$INSTALL_DIR/nginx/nginx.conf" << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Frontend
    location / {
        try_files \$uri \$uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # API Proxy
    location /api {
        proxy_pass http://backend:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }

    # WebSocket
    location /socket.io {
        proxy_pass http://backend:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    # Static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    else
        cat > "$INSTALL_DIR/nginx/nginx.conf" << 'EOF'
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Frontend
    location / {
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # API Proxy
    location /api {
        proxy_pass http://backend:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # WebSocket
    location /socket.io {
        proxy_pass http://backend:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    fi
    
    log_success "Nginx configuration created"
}

# =============================================================================
# Installation Functions
# =============================================================================

build_images() {
    log "Building Docker images..."
    
    cd "$INSTALL_DIR"
    
    # Build backend
    log "Building backend image..."
    docker-compose build backend
    
    log_success "Docker images built successfully"
}

start_services() {
    log "Starting BOLT services..."
    
    cd "$INSTALL_DIR"
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p uploads
    
    # Pull images
    docker-compose pull
    
    # Start services
    docker-compose up -d
    
    log_success "Services started"
}

wait_for_services() {
    log "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    # Wait for backend
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
        log_info "Check logs: docker-compose logs backend"
        return 1
    fi
    
    # Wait for database if using internal
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

create_admin_user() {
    log "Creating default admin user..."
    
    # Wait a bit more for database migrations
    sleep 5
    
    log_success "Default admin user will be created on first backend startup"
    log_info "Username: admin"
    log_info "Password: admin123"
    log_warning "Please change the password after first login!"
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
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        log_success "Frontend: http://localhost:$FRONTEND_PORT ✓"
    else
        log_error "Frontend: Not responding ✗"
        all_ok=false
    fi
    
    # Check Database
    if [ "$USE_EXTERNAL_DB" = true ]; then
        if command -v psql &> /dev/null; then
            if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
                log_success "External Database: Connected ✓"
            else
                log_error "External Database: Connection failed ✗"
                all_ok=false
            fi
        else
            log_warning "External Database: psql not installed, skipping check"
        fi
    else
        if docker-compose exec -T postgres pg_isready -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
            log_success "Database Container: Running ✓"
        else
            log_error "Database Container: Not responding ✗"
            all_ok=false
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
    
    # Create backup script
    cat > "$INSTALL_DIR/backup.sh" << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/bolt"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
if [ -f .env ]; then
    source .env
    if [ "$USE_EXTERNAL_DB" = "true" ]; then
        PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/db_backup_$DATE.sql"
    else
        docker-compose exec -T postgres pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/db_backup_$DATE.sql"
    fi
    gzip "$BACKUP_DIR/db_backup_$DATE.sql"
fi

# Backup uploads
tar -czf "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" -C "$(dirname "$0")" uploads 2>/dev/null || true

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x "$INSTALL_DIR/backup.sh"
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * $INSTALL_DIR/backup.sh >> /var/log/bolt-backup.log 2>&1") | crontab -
    
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
    log_info "Access Information"
    echo "─────────────────────────────────────────────────────────────────────"
    echo -e "  ${CYAN}Frontend:${NC}    http://localhost:$FRONTEND_PORT"
    echo -e "  ${CYAN}Backend API:${NC} http://localhost:$BACKEND_PORT/api"
    echo -e "  ${CYAN}Health Check:${NC} http://localhost:$BACKEND_PORT/health"
    
    if [ "$USE_SSL" = true ]; then
        echo ""
        log_info "SSL Configuration"
        echo "─────────────────────────────────────────────────────────────────────"
        echo -e "  ${CYAN}HTTPS:${NC} https://$DOMAIN"
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
    echo -e "  ${CYAN}View logs:${NC}        cd $INSTALL_DIR && docker-compose logs -f"
    echo -e "  ${CYAN}Stop services:${NC}    cd $INSTALL_DIR && docker-compose down"
    echo -e "  ${CYAN}Restart:${NC}          cd $INSTALL_DIR && docker-compose restart"
    echo -e "  ${CYAN}Update:${NC}           cd $INSTALL_DIR && docker-compose pull && docker-compose up -d"
    echo -e "  ${CYAN}Backup:${NC}           $INSTALL_DIR/backup.sh"
    
    echo ""
    log_info "Configuration Files"
    echo "─────────────────────────────────────────────────────────────────────"
    echo -e "  ${CYAN}Environment:${NC}     $INSTALL_DIR/.env"
    echo -e "  ${CYAN}Docker Compose:${NC}  $INSTALL_DIR/docker-compose.yml"
    echo -e "  ${CYAN}Nginx Config:${NC}   $INSTALL_DIR/nginx/nginx.conf"
    
    if [ "$USE_EXTERNAL_DB" = false ]; then
        echo ""
        log_info "Database Information"
        echo "─────────────────────────────────────────────────────────────────────"
        echo -e "  ${CYAN}Host:${NC}     localhost (Docker container)"
        echo -e "  ${CYAN}Port:${NC}     $DB_PORT"
        echo -e "  ${CYAN}Database:${NC} $DB_NAME"
        echo -e "  ${CYAN}User:${NC}     $DB_USER"
    else
        echo ""
        log_info "External Database"
        echo "─────────────────────────────────────────────────────────────────────"
        echo -e "  ${CYAN}Host:${NC}     $DB_HOST"
        echo -e "  ${CYAN}Port:${NC}     $DB_PORT"
        echo -e "  ${CYAN}Database:${NC} $DB_NAME"
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
    
    # Pre-installation checks
    check_root
    check_dependencies
    
    # Configuration
    ask_domain
    ask_database
    ask_ports
    
    # SSL Setup (if enabled)
    if [ "$USE_SSL" = true ]; then
        setup_ssl
    fi
    
    # Generate configuration files
    generate_env_file
    generate_docker_compose
    generate_nginx_config
    
    # Build and start
    build_images
    start_services
    
    # Wait for services
    if wait_for_services; then
        create_admin_user
        setup_backups
        
        # Final checks
        if check_services; then
            print_summary
        else
            log_warning "Some services may not be fully ready yet"
            log_info "Please check the logs: docker-compose logs -f"
            print_summary
        fi
    else
        log_error "Installation completed with errors"
        log_info "Please check the logs: docker-compose logs -f"
        exit 1
    fi
}

# Handle script interruption
trap 'log_error "Installation interrupted"; exit 1' INT TERM

# Run main function
main "$@"
