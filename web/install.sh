#!/bin/bash

# =============================================================================
# BOLT - Installation Script
# =============================================================================
# Supports: Docker, Native, or Already inside Docker container
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SCRIPT_DIR}"
LOG_FILE="/var/log/bolt-install.log"
INSTALL_DIR_SYSTEM="/opt/bolt"

# Defaults
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
INSTALL_MODE="docker"  # docker, native, container

# =============================================================================
# Helper Functions
# =============================================================================

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() { echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG_FILE"; }
log_info() { echo -e "${CYAN}[i]${NC} $1" | tee -a "$LOG_FILE"; }

print_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║   ██████╗  ██████╗ ██╗  ████████╗                                ║"
    echo "║   ██╔══██╗██╔═══██╗██║  ╚══██╔══╝                                ║"
    echo "║   ██████╔╝██║   ██║██║     ██║                                   ║"
    echo "║   ██╔══██╗██║   ██║██║     ██║                                   ║"
    echo "║   ██████╔╝╚██████╔╝███████╗██║                                   ║"
    echo "║   ╚═════╝  ╚═════╝ ╚══════╝╚═╝                                   ║"
    echo "║                                                                  ║"
    echo "║   BOLT Management System - Installation Script                   ║"
    echo "║   Version: 2.2.0                                                 ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# =============================================================================
# Detect if running inside Docker
# =============================================================================

detect_container() {
    if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# =============================================================================
# Installation Mode Selection
# =============================================================================

ask_installation_mode() {
    echo ""
    log_info "Installation Mode"
    echo "─────────────────────────────────────────────────────────────────────"
    
    if detect_container; then
        echo -e "${YELLOW}⚠ Detected: Running inside Docker container${NC}"
        echo ""
        echo "  [1] Native inside container - Install Node.js, PostgreSQL directly here"
        echo "  [2] Exit - Run this script on host system with Docker instead"
        echo ""
        read -p "Select option [1]: " choice
        choice=${choice:-1}
        
        case $choice in
            1) INSTALL_MODE="container" ;;
            2) log_info "Exiting..."; exit 0 ;;
            *) log_error "Invalid option"; exit 1 ;;
        esac
    else
        echo "  [1] Docker (recommended) - Full containerization"
        echo "  [2] Native - Install directly on host server"
        echo ""
        read -p "Select option [1]: " choice
        choice=${choice:-1}
        
        case $choice in
            1) INSTALL_MODE="docker" ;;
            2) INSTALL_MODE="native" ;;
            *) log_error "Invalid option"; exit 1 ;;
        esac
    fi
    
    log "Selected: $INSTALL_MODE installation"
    echo ""
}

# =============================================================================
# Dependency Checks
# =============================================================================

check_dependencies() {
    log "Checking dependencies..."
    
    local missing_deps=()
    
    if [ "$INSTALL_MODE" = "docker" ]; then
        # Docker mode on host
        if ! command -v docker &> /dev/null; then
            missing_deps+=("docker")
        else
            log_success "Docker found: $(docker --version | grep -oP '\d+\.\d+\.\d+')"
            if ! docker info &> /dev/null; then
                log_error "Docker daemon not running!"
                exit 1
            fi
        fi
        
        if ! (command -v docker-compose &> /dev/null || docker compose version &> /dev/null); then
            missing_deps+=("docker-compose")
        fi
        
    elif [ "$INSTALL_MODE" = "native" ]; then
        # Native mode
        check_native_deps missing_deps
        
    elif [ "$INSTALL_MODE" = "container" ]; then
        # Inside container - need to install everything
        log_info "Container mode: Will install Node.js, PostgreSQL, Nginx inside this container"
        check_native_deps missing_deps
    fi
    
    # Common checks
    for cmd in git curl openssl; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        else
            log_success "$cmd found"
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_info "Installing: ${missing_deps[*]}"
        install_dependencies "${missing_deps[@]}"
    else
        log_success "All dependencies satisfied"
    fi
}

check_native_deps() {
    local -n deps=$1
    
    if ! command -v node &> /dev/null; then
        deps+=("nodejs")
    else
        local node_ver=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        [ "$node_ver" -lt 18 ] && deps+=("nodejs") || log_success "Node.js $(node --version)"
    fi
    
    command -v npm &> /dev/null || deps+=("npm")
    command -v psql &> /dev/null || deps+=("postgresql")
    command -v nginx &> /dev/null || deps+=("nginx")
    command -v pm2 &> /dev/null || deps+=("pm2")
}

install_dependencies() {
    local deps=("$@")
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
    else
        log_error "Cannot detect OS"
        exit 1
    fi
    
    log "OS: $OS"
    
    for dep in "${deps[@]}"; do
        case $dep in
            docker)
                log "Installing Docker..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    apt-get update
                    apt-get install -y apt-transport-https ca-certificates curl gnupg
                    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list
                    apt-get update
                    apt-get install -y docker-ce docker-compose-plugin
                fi
                ;;
            nodejs)
                log "Installing Node.js 18..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
                    apt-get install -y nodejs
                elif [[ "$OS" == *"Alpine"* ]]; then
                    apk add --update nodejs npm
                fi
                ;;
            postgresql)
                log "Installing PostgreSQL..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    apt-get update
                    apt-get install -y postgresql postgresql-contrib
                    service postgresql start || true
                elif [[ "$OS" == *"Alpine"* ]]; then
                    apk add postgresql
                    mkdir -p /run/postgresql
                    chown postgres:postgres /run/postgresql
                    su - postgres -c "initdb -D /var/lib/postgresql/data" || true
                    su - postgres -c "pg_ctl start -D /var/lib/postgresql/data" || true
                fi
                ;;
            nginx)
                log "Installing Nginx..."
                if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
                    apt-get install -y nginx
                elif [[ "$OS" == *"Alpine"* ]]; then
                    apk add nginx
                fi
                mkdir -p /run/nginx
                ;;
            pm2)
                log "Installing PM2..."
                npm install -g pm2
                ;;
            git|curl|openssl)
                if [[ "$OS" == *"Alpine"* ]]; then
                    apk add "$dep"
                else
                    apt-get install -y "$dep"
                fi
                ;;
        esac
    done
    
    log_success "Dependencies installed"
}

# =============================================================================
# Configuration
# =============================================================================

ask_domain() {
    echo ""
    log_info "Domain Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    read -p "Configure custom domain? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Domain (e.g., bolt.example.com): " DOMAIN
        [ -z "$DOMAIN" ] && { log_error "Domain empty"; exit 1; }
        
        read -p "Enable SSL with Let's Encrypt? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            USE_SSL=true
            read -p "Email for Let's Encrypt: " EMAIL
            [ -z "$EMAIL" ] && { log_error "Email required"; exit 1; }
        fi
    else
        DOMAIN="localhost"
        log "Using localhost"
    fi
}

ask_database() {
    echo ""
    log_info "Database Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    
    if [ "$INSTALL_MODE" = "container" ]; then
        log_info "Container mode: Using local PostgreSQL"
        USE_EXTERNAL_DB=false
        DB_HOST="localhost"
        DB_PORT="5432"
        DB_NAME="bolt_db"
        DB_USER="bolt_user"
        DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
        setup_local_postgres
        return
    fi
    
    read -p "Use external PostgreSQL? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        USE_EXTERNAL_DB=true
        read -p "DB Host: " DB_HOST
        read -p "DB Port [5432]: " DB_PORT; DB_PORT=${DB_PORT:-5432}
        read -p "DB Name [bolt_db]: " DB_NAME; DB_NAME=${DB_NAME:-bolt_db}
        read -p "DB User [bolt_user]: " DB_USER; DB_USER=${DB_USER:-bolt_user}
        read -s -p "DB Password: " DB_PASSWORD; echo
        [ -z "$DB_PASSWORD" ] && { log_error "Password required"; exit 1; }
    else
        USE_EXTERNAL_DB=false
        if [ "$INSTALL_MODE" = "docker" ]; then
            DB_HOST="postgres"
            DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
        else
            DB_HOST="localhost"
            DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
            setup_local_postgres
        fi
        DB_NAME="bolt_db"
        DB_USER="bolt_user"
        DB_PORT="5432"
    fi
}

setup_local_postgres() {
    log "Setting up PostgreSQL..."
    
    if command -v systemctl &> /dev/null; then
        # Systemd system
        sudo -u postgres psql << EOF 2>/dev/null || true
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
        sudo systemctl restart postgresql 2>/dev/null || true
    else
        # Container/no systemd - run postgres manually
        if [ ! -d "/var/lib/postgresql/data" ] || [ -z "$(ls -A /var/lib/postgresql/data 2>/dev/null)" ]; then
            mkdir -p /var/lib/postgresql/data
            chown postgres:postgres /var/lib/postgresql/data
            su - postgres -c "initdb -D /var/lib/postgresql/data" 2>/dev/null || true
        fi
        
        # Start PostgreSQL if not running
        if ! pg_isready -U postgres &> /dev/null; then
            su - postgres -c "pg_ctl start -D /var/lib/postgresql/data -l /var/lib/postgresql/logfile" 2>/dev/null || \
            pg_ctl start -D /var/lib/postgresql/data -l /var/lib/postgresql/logfile 2>/dev/null || true
            sleep 3
        fi
        
        # Create user and database
        su - postgres -c "psql << EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF" 2>/dev/null || \
        psql -U postgres << EOF 2>/dev/null || true
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
    fi
    
    log_success "PostgreSQL configured"
}

ask_ports() {
    echo ""
    log_info "Port Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    
    read -p "Backend port [3001]: " BACKEND_PORT
    BACKEND_PORT=${BACKEND_PORT:-3001}
    
    if [ "$INSTALL_MODE" = "docker" ]; then
        read -p "Frontend port [5173]: " FRONTEND_PORT
        FRONTEND_PORT=${FRONTEND_PORT:-5173}
    else
        FRONTEND_PORT="80"
        log "Frontend will use port 80 (Nginx)"
    fi
    
    log "Backend: $BACKEND_PORT, Frontend: $FRONTEND_PORT"
}

# =============================================================================
# Environment & Configs
# =============================================================================

generate_env_file() {
    log "Generating .env..."
    
    local jwt_secret=$(openssl rand -base64 32)
    local env_path="$INSTALL_DIR/.env"
    [ "$INSTALL_MODE" != "docker" ] && env_path="$INSTALL_DIR_SYSTEM/.env"
    
    mkdir -p "$(dirname "$env_path")"
    
    cat > "$env_path" << EOF
DOMAIN=$DOMAIN
USE_SSL=$USE_SSL
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
JWT_SECRET=$jwt_secret
JWT_EXPIRES_IN=7d
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
NODE_ENV=production
CORS_ORIGIN=http://localhost:$([ "$INSTALL_MODE" = "docker" ] && echo "$FRONTEND_PORT" || echo "80")
UPLOAD_DIR=$([ "$INSTALL_MODE" = "docker" ] && echo "./uploads" || echo "/opt/bolt/uploads")
MAX_FILE_SIZE=10485760
LETSENCRYPT_EMAIL=$EMAIL
EOF

    log_success "Environment file created"
}

generate_nginx_config() {
    log "Generating Nginx config..."
    
    local nginx_conf=""
    local upstream_host=$([ "$INSTALL_MODE" = "docker" ] && echo "backend" || echo "localhost")
    
    if [ "$INSTALL_MODE" = "docker" ]; then
        mkdir -p "$INSTALL_DIR/nginx"
        nginx_conf="$INSTALL_DIR/nginx/nginx.conf"
    else
        mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled 2>/dev/null || \
        mkdir -p /etc/nginx/conf.d 2>/dev/null || true
        nginx_conf="/etc/nginx/sites-available/bolt"
        [ -d "/etc/nginx/conf.d" ] && nginx_conf="/etc/nginx/conf.d/bolt.conf"
    fi
    
    cat > "$nginx_conf" << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    root $([ "$INSTALL_MODE" = "docker" ] && echo "/usr/share/nginx/html" || echo "$INSTALL_DIR_SYSTEM/frontend");
    index index.html;

    location / {
        try_files \\\$uri \\\$uri/ /index.html;
    }

    location /api {
        proxy_pass http://$upstream_host:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_read_timeout 86400;
    }

    location /socket.io {
        proxy_pass http://$upstream_host:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF

    # Enable site for native mode
    if [ "$INSTALL_MODE" != "docker" ]; then
        if [ -d "/etc/nginx/sites-enabled" ]; then
            ln -sf "$nginx_conf" /etc/nginx/sites-enabled/bolt 2>/dev/null || true
            rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
        fi
        nginx -t 2>/dev/null && (nginx -s reload 2>/dev/null || nginx 2>/dev/null || true)
    fi
    
    log_success "Nginx configured"
}

generate_docker_compose() {
    [ "$INSTALL_MODE" != "docker" ] && return
    
    log "Generating docker-compose.yml..."
    
    cat > "$INSTALL_DIR/docker-compose.yml" << EOF
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: bolt-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: $DB_NAME
      POSTGRES_USER: $DB_USER
      POSTGRES_PASSWORD: $DB_PASSWORD
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "$DB_PORT:5432"
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
      - DB_HOST=postgres
    ports:
      - "$BACKEND_PORT:3001"
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - postgres
    networks:
      - bolt-network

  frontend:
    image: nginx:alpine
    container_name: bolt-frontend
    restart: unless-stopped
    ports:
      - "$FRONTEND_PORT:80"
    volumes:
      - ./app/dist:/usr/share/nginx/html:ro
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
    networks:
      - bolt-network

volumes:
  postgres_data:

networks:
  bolt-network:
EOF

    log_success "Docker Compose created"
}

# =============================================================================
# Installation
# =============================================================================

install_native() {
    log "Native installation..."
    
    mkdir -p "$INSTALL_DIR_SYSTEM"/{backend,frontend,uploads,logs}
    
    # Backend
    if [ -d "bolt-backend" ]; then
        cd bolt-backend
        npm ci
        npm run build
        cp -r dist/* "$INSTALL_DIR_SYSTEM/backend/"
        cp -r node_modules "$INSTALL_DIR_SYSTEM/backend/"
        cp package.json "$INSTALL_DIR_SYSTEM/backend/"
        cd ..
    fi
    
    # Frontend
    if [ -d "app" ]; then
        cd app
        npm ci
        npm run build
        cp -r dist/* "$INSTALL_DIR_SYSTEM/frontend/"
        cd ..
    fi
    
    # PM2 config
    cat > "$INSTALL_DIR_SYSTEM/ecosystem.config.js" << EOF
module.exports = {
  apps: [{
    name: 'bolt-backend',
    script: '$INSTALL_DIR_SYSTEM/backend/main.js',
    env: { NODE_ENV: 'production' },
    env_file: '$INSTALL_DIR_SYSTEM/.env',
    log_file: '/var/log/bolt/backend.log',
    restart_delay: 3000
  }]
};
EOF

    # Start services
    if command -v pm2 &> /dev/null; then
        cd "$INSTALL_DIR_SYSTEM"
        pm2 start ecosystem.config.js
        pm2 save 2>/dev/null || true
    else
        # Direct node execution
        cd "$INSTALL_DIR_SYSTEM/backend"
        nohup node main.js > /var/log/bolt/backend.log 2>&1 &
    fi
    
    # Start nginx
    if command -v nginx &> /dev/null; then
        nginx 2>/dev/null || nginx -s reload 2>/dev/null || true
    fi
}

install_container() {
    log "Container mode installation..."
    
    # Same as native but optimized for container environment
    install_native
    
    # Keep container running
    log_info "Setup complete. Use 'tail -f /var/log/bolt/backend.log' to monitor"
    log_info "Or run: pm2 logs"
}

install_docker() {
    log "Docker installation..."
    
    docker-compose build backend
    docker-compose up -d
    
    # Wait for startup
    local attempt=1
    while [ $attempt -le 30 ]; do
        if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
            log_success "Services ready"
            break
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
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
    log_info "Mode: ${INSTALL_MODE^^}"
    echo ""
    echo "  Frontend: http://localhost:$([ "$INSTALL_MODE" = "docker" ] && echo "$FRONTEND_PORT" || echo "80")"
    echo "  Backend:  http://localhost:$BACKEND_PORT"
    echo ""
    echo "  Admin:    admin / admin123"
    echo ""
    
    if [ "$INSTALL_MODE" = "docker" ]; then
        echo "  Commands:"
        echo "    docker-compose logs -f"
        echo "    docker-compose down"
    else
        echo "  Logs: tail -f /var/log/bolt/backend.log"
        [ -f "$INSTALL_DIR_SYSTEM/ecosystem.config.js" ] && echo "    pm2 status"
    fi
    echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
    mkdir -p /var/log
    touch "$LOG_FILE" 2>/dev/null || LOG_FILE="/tmp/bolt-install.log"
    
    print_banner
    log "Starting BOLT installation..."
    
    ask_installation_mode
    check_dependencies
    ask_domain
    ask_database
    ask_ports
    generate_env_file
    generate_nginx_config
    
    case $INSTALL_MODE in
        docker)
            generate_docker_compose
            install_docker
            ;;
        native)
            install_native
            ;;
        container)
            install_container
            ;;
    esac
    
    print_summary
}

trap 'log_error "Interrupted"; exit 1' INT TERM
main "$@"