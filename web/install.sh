#!/bin/bash

# =============================================================================
# BOLT - Installation Script v2.4
# =============================================================================
# Fixed: npm install fallback when package-lock.json missing
# =============================================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SCRIPT_DIR}"
LOG_FILE="/var/log/bolt-install.log"
INSTALL_DIR_SYSTEM="/opt/bolt"
INSTALL_MODE="docker"

log() { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG_FILE"; }
log_info() { echo -e "${CYAN}[i]${NC} $1" | tee -a "$LOG_FILE"; }

print_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║   BOLT Management System - Installation Script v2.4              ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

detect_container() {
    [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null
}

ask_installation_mode() {
    echo ""
    log_info "Select Installation Mode"
    echo "─────────────────────────────────────────────────────────────────────"
    
    if detect_container; then
        echo -e "${YELLOW}⚠ Running inside Docker container${NC}"
        echo "  [1] Install inside this container (Node.js + PostgreSQL)"
        echo "  [2] Exit and run on host instead"
        read -p "Select [1]: " choice
        choice=${choice:-1}
        case $choice in
            1) INSTALL_MODE="container" ;;
            *) exit 0 ;;
        esac
    else
        echo "  [1] Docker (recommended)"
        echo "  [2] Native (direct install)"
        read -p "Select [1]: " choice
        choice=${choice:-1}
        case $choice in
            1) INSTALL_MODE="docker" ;;
            2) INSTALL_MODE="native" ;;
            *) log_error "Invalid"; exit 1 ;;
        esac
    fi
    log "Mode: $INSTALL_MODE"
}

install_deps() {
    local pkgs=("$@")
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "alpine" ]]; then
            apk add --update ${pkgs[@]}
        else
            apt-get update && apt-get install -y ${pkgs[@]}
        fi
    fi
}

check_dependencies() {
    log "Checking dependencies..."
    
    if [ "$INSTALL_MODE" = "docker" ]; then
        if ! command -v docker &> /dev/null; then
            log "Installing Docker..."
            install_deps ca-certificates curl gnupg
            install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
            apt-get update && apt-get install -y docker-ce docker-compose-plugin
        fi
        docker info &> /dev/null || { log_error "Docker not running"; exit 1; }
    else
        if ! command -v node &> /dev/null || [ "$(node --version | cut -d'v' -f2 | cut -d'.' -f1)" -lt 18 ]; then
            log "Installing Node.js 18..."
            if [[ "$(cat /etc/os-release 2>/dev/null | grep ^ID=)" == *"alpine"* ]]; then
                install_deps nodejs npm
            else
                curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
                install_deps nodejs
            fi
        fi
        log_success "Node.js $(node --version)"
        
        if ! command -v psql &> /dev/null; then
            log "Installing PostgreSQL..."
            install_deps postgresql postgresql-contrib
            service postgresql start 2>/dev/null || true
        fi
        
        if ! command -v nginx &> /dev/null; then
            log "Installing Nginx..."
            install_deps nginx
            mkdir -p /run/nginx
        fi
        
        if ! command -v pm2 &> /dev/null; then
            log "Installing PM2..."
            npm install -g pm2
        fi
    fi
    
    local needed=()
    for cmd in git curl openssl; do
        command -v "$cmd" &> /dev/null || needed+=("$cmd")
    done
    [ ${#needed[@]} -gt 0 ] && install_deps "${needed[@]}"
    log_success "Dependencies OK"
}

ask_config() {
    echo ""
    log_info "Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    
    read -p "Custom domain? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Domain: " DOMAIN
        read -p "SSL with Let's Encrypt? (y/N): " -n 1 -r
        echo
        [[ $REPLY =~ ^[Yy]$ ]] && { USE_SSL=true; read -p "Email: " EMAIL; }
    else
        DOMAIN="localhost"
    fi
    
    DB_NAME="bolt_db"
    DB_USER="bolt_user"
    DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
    
    if [ "$INSTALL_MODE" = "docker" ]; then
        DB_HOST="postgres"
    else
        DB_HOST="localhost"
        setup_postgres
    fi
    
    read -p "Backend port [3001]: " BACKEND_PORT
    BACKEND_PORT=${BACKEND_PORT:-3001}
    [ "$INSTALL_MODE" = "docker" ] && { read -p "Frontend port [5173]: " FRONTEND_PORT; FRONTEND_PORT=${FRONTEND_PORT:-5173}; } || FRONTEND_PORT=80
    
    log "Config: $DOMAIN, Backend:$BACKEND_PORT, DB:$DB_HOST"
}

setup_postgres() {
    log "Setting up PostgreSQL..."
    
    if ! pg_isready -U postgres &>/dev/null; then
        if command -v systemctl &>/dev/null; then
            systemctl start postgresql
        else
            mkdir -p /var/lib/postgresql/data /run/postgresql
            chown postgres:postgres /var/lib/postgresql/data /run/postgresql 2>/dev/null || true
            su - postgres -c "pg_ctl start -D /var/lib/postgresql/data -l /var/lib/postgresql/logfile" 2>/dev/null || true
        fi
        sleep 2
    fi
    
    local sql="CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD'; CREATE DATABASE $DB_NAME OWNER $DB_USER; GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    su - postgres -c "psql -c \"$sql\"" 2>/dev/null || sudo -u postgres psql -c "$sql" 2>/dev/null || psql -U postgres -c "$sql" 2>/dev/null || true
    
    log_success "PostgreSQL ready"
}

# =============================================================================
# NPM Install with fallback
# =============================================================================

npm_install_safe() {
    log "Installing npm dependencies..."
    
    if [ -f "package-lock.json" ]; then
        log "Found package-lock.json, using npm ci"
        npm ci
    else
        log_warning "No package-lock.json, using npm install"
        npm install
    fi
}

find_entry_point() {
    local dir="$1"
    for f in "main.js" "index.js" "server.js" "dist/main.js" "dist/index.js" "dist/server.js" "build/main.js" "build/index.js"; do
        [ -f "$dir/$f" ] && { echo "$f"; return; }
    done
    find "$dir" -name "*.js" -type f 2>/dev/null | grep -E "(main|index|server|app|start)" | head -1 | sed "s|$dir/||"
}

install_backend() {
    log "Installing Backend..."
    
    local src_dir="$INSTALL_DIR/bolt-backend"
    local target_dir="$INSTALL_DIR_SYSTEM/backend"
    
    [ -d "$target_dir" ] && rm -rf "$target_dir"
    mkdir -p "$target_dir"
    
    if [ ! -d "$src_dir" ]; then
        log_error "Backend source not found at $src_dir"
        return 1
    fi
    
    cd "$src_dir"
    
    # Install dependencies (with fallback)
    npm_install_safe
    
    # Build
    npm run build 2>/dev/null || npm run compile 2>/dev/null || true
    
    # Copy files
    if [ -d "dist" ] && [ "$(ls -A dist 2>/dev/null)" ]; then
        cp -r dist/* "$target_dir/"
    elif [ -d "build" ] && [ "$(ls -A build 2>/dev/null)" ]; then
        cp -r build/* "$target_dir/"
    else
        # No build output - copy source
        log_warning "No build directory, copying source files"
        cp -r . "$target_dir/"
        # Remove node_modules and reinstall in target to ensure native modules match
        rm -rf "$target_dir/node_modules"
        cd "$target_dir"
        npm_install_safe
        cd "$src_dir"
    fi
    
    # Ensure node_modules exists in target
    if [ ! -d "$target_dir/node_modules" ] && [ -d "node_modules" ]; then
        cp -r node_modules "$target_dir/"
    fi
    
    # Copy package.json if not exists
    [ -f "$target_dir/package.json" ] || cp package.json "$target_dir/"
    
    cd "$INSTALL_DIR"
    
    # Find entry point
    local entry=$(find_entry_point "$target_dir")
    if [ -z "$entry" ]; then
        log_error "Cannot find entry point in $target_dir"
        ls -la "$target_dir"
        return 1
    fi
    
    log_success "Backend entry: $entry"
    echo "$entry" > "$target_dir/.entrypoint"
    
    # Create startup script
    cat > "$target_dir/start.sh" << EOF
#!/bin/bash
cd \$(dirname "\$0")
export NODE_ENV=production
if [ -f ../.env ]; then
    export \$(grep -v '^#' ../.env | xargs 2>/dev/null)
fi
exec node $entry
EOF
    chmod +x "$target_dir/start.sh"
}

install_frontend() {
    log "Installing Frontend..."
    
    local src_dir="$INSTALL_DIR/app"
    local target_dir="$INSTALL_DIR_SYSTEM/frontend"
    
    [ -d "$target_dir" ] && rm -rf "$target_dir"
    mkdir -p "$target_dir"
    
    if [ ! -d "$src_dir" ]; then
        log_warning "Frontend source not found at $src_dir, skipping"
        return
    fi
    
    cd "$src_dir"
    npm_install_safe
    npm run build 2>/dev/null || true
    
    if [ -d "dist" ] && [ "$(ls -A dist 2>/dev/null)" ]; then
        cp -r dist/* "$target_dir/"
    elif [ -d "build" ] && [ "$(ls -A build 2>/dev/null)" ]; then
        cp -r build/* "$target_dir/"
    else
        cp -r . "$target_dir/"
    fi
    
    cd "$INSTALL_DIR"
    log_success "Frontend installed"
}

generate_configs() {
    log "Generating configs..."
    
    mkdir -p "$INSTALL_DIR_SYSTEM" /var/log/bolt
    
    cat > "$INSTALL_DIR_SYSTEM/.env" << EOF
DOMAIN=$DOMAIN
USE_SSL=$USE_SSL
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
JWT_SECRET=$(openssl rand -base64 32)
JWT_EXPIRES_IN=7d
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
NODE_ENV=production
CORS_ORIGIN=http://localhost:$FRONTEND_PORT
UPLOAD_DIR=$INSTALL_DIR_SYSTEM/uploads
MAX_FILE_SIZE=10485760
EOF

    local nginx_conf="/etc/nginx/conf.d/bolt.conf"
    [ -d "/etc/nginx/sites-available" ] && nginx_conf="/etc/nginx/sites-available/bolt"
    
    mkdir -p "$(dirname "$nginx_conf")"
    
    cat > "$nginx_conf" << EOF
server {
    listen 80;
    server_name $DOMAIN;
    root $INSTALL_DIR_SYSTEM/frontend;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 86400;
    }
    
    location /socket.io {
        proxy_pass http://localhost:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF

    if [ -d "/etc/nginx/sites-enabled" ]; then
        ln -sf "$nginx_conf" /etc/nginx/sites-enabled/bolt 2>/dev/null || true
        rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
    fi

    cat > "$INSTALL_DIR_SYSTEM/ecosystem.config.js" << 'EOF'
module.exports = {
  apps: [{
    name: 'bolt-backend',
    cwd: '/opt/bolt/backend',
    script: './start.sh',
    exec_mode: 'fork',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: { NODE_ENV: 'production' },
    log_file: '/var/log/bolt/backend.log',
    out_file: '/var/log/bolt/backend.out.log',
    error_file: '/var/log/bolt/backend.error.log',
    merge_logs: true,
    time: true
  }]
};
EOF

    log_success "Configs generated"
}

start_services() {
    log "Starting services..."
    
    nginx -t 2>/dev/null && (nginx -s reload 2>/dev/null || nginx 2>/dev/null || true)
    
    cd "$INSTALL_DIR_SYSTEM"
    pm2 start ecosystem.config.js
    pm2 save 2>/dev/null || true
    
    local attempt=1
    while [ $attempt -le 30 ]; do
        if curl -s "http://localhost:$BACKEND_PORT/health" &>/dev/null || \
           curl -s "http://localhost:$BACKEND_PORT/api/health" &>/dev/null || \
           curl -s "http://localhost:$BACKEND_PORT" &>/dev/null; then
            log_success "Backend responding on port $BACKEND_PORT"
            return
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_warning "Backend may still be starting, check: pm2 logs"
}

docker_install() {
    log "Docker installation..."
    
    cat > "$INSTALL_DIR/docker-compose.yml" << EOF
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: $DB_NAME
      POSTGRES_USER: $DB_USER
      POSTGRES_PASSWORD: $DB_PASSWORD
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "$DB_PORT:5432"
  backend:
    build: ./bolt-backend
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=$DB_NAME
      - DB_USER=$DB_USER
      - DB_PASSWORD=$DB_PASSWORD
      - JWT_SECRET=$(openssl rand -base64 32)
      - PORT=3001
    ports:
      - "$BACKEND_PORT:3001"
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - postgres
  frontend:
    image: nginx:alpine
    ports:
      - "$FRONTEND_PORT:80"
    volumes:
      - ./app/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend
volumes:
  postgres_data:
EOF

    if [ -d "app" ]; then
        cd app
        [ -f package-lock.json ] && npm ci || npm install
        npm run build
        cd ..
    fi
    
    docker-compose up --build -d
    
    local attempt=1
    while [ $attempt -le 30 ]; do
        if curl -s "http://localhost:$BACKEND_PORT/health" &>/dev/null; then
            log_success "Services ready"
            return
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    log_warning "Services starting, check: docker-compose logs -f"
}

print_summary() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Installation Complete!                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    log_info "Mode: ${INSTALL_MODE^^}"
    echo "  Frontend: http://localhost:$FRONTEND_PORT"
    echo "  Backend:  http://localhost:$BACKEND_PORT"
    echo "  Admin:    admin / admin123"
    echo ""
    
    if [ "$INSTALL_MODE" = "docker" ]; then
        echo "  docker-compose logs -f"
        echo "  docker-compose down"
    else
        echo "  Logs: pm2 logs  или  tail -f /var/log/bolt/*.log"
        echo "  PM2:  pm2 status | restart | stop"
    fi
    echo ""
}

main() {
    mkdir -p /var/log /tmp
    touch "$LOG_FILE" 2>/dev/null || LOG_FILE="/tmp/bolt-install.log"
    
    print_banner
    log "Starting BOLT installation..."
    
    ask_installation_mode
    check_dependencies
    ask_config
    
    if [ "$INSTALL_MODE" = "docker" ]; then
        docker_install
    else
        install_backend
        install_frontend
        generate_configs
        start_services
    fi
    
    print_summary
}

trap 'echo; log_error "Interrupted"; exit 1' INT TERM
main "$@"