#!/bin/bash

# =============================================================================
# BOLT - Management Script v2.2
# =============================================================================
# Fixed: Proper environment loading for PM2 and Node.js
# =============================================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR_SYSTEM="/opt/bolt"
ENV_FILE="$INSTALL_DIR_SYSTEM/.env"

detect_mode() {
    if [ -f "$SCRIPT_DIR/docker-compose.yml" ] && [ -d "$SCRIPT_DIR/.git" ] 2>/dev/null; then
        echo "docker"
    elif [ -d "$INSTALL_DIR_SYSTEM/backend" ]; then
        echo "native"
    elif [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        echo "container"
    else
        echo "unknown"
    fi
}

INSTALL_MODE=$(detect_mode)

log() { echo -e "${BLUE}[BOLT]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${CYAN}[i]${NC} $1"; }

print_help() {
    cat << EOF
╔══════════════════════════════════════════════════════════════════╗
║                    BOLT Management Script v2.2                     ║
║                    Mode: ${INSTALL_MODE^^}                                 ║
╚══════════════════════════════════════════════════════════════════╝

Usage: ./bolt.sh [command] [options]

Commands:
  start              Start all services
  stop               Stop all services
  restart            Restart all services
  status             Show service status
  logs [service]     View logs (backend/frontend/postgres/nginx)
  env                Edit environment configuration
  fix                Fix/repair installation
  update             Update to latest version
  backup             Create manual backup
  db [command]       Database operations (backup/restore/console)
  shell [service]    Open shell (backend/postgres/nginx)
  clean              Clean up resources
  reset              Reset all data (DANGEROUS!)
  install            Run full installation
  help               Show this help message

EOF
}

load_env() {
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker not installed"
        exit 1
    fi
    if ! docker info &> /dev/null; then
        error "Docker daemon not running"
        exit 1
    fi
}

# =============================================================================
# Fix Environment Configuration
# =============================================================================

cmd_env() {
    log "Editing environment..."
    if command -v nano &> /dev/null; then
        nano "$ENV_FILE"
    elif command -v vim &> /dev/null; then
        vim "$ENV_FILE"
    else
        cat "$ENV_FILE"
        info "Edit manually: $ENV_FILE"
    fi
}

cmd_fix() {
    log "Repairing installation..."
    load_env
    
    if [ "$INSTALL_MODE" != "native" ] && [ "$INSTALL_MODE" != "container" ]; then
        error "Fix only for native/container mode"
        return 1
    fi
    
    local backend_dir="$INSTALL_DIR_SYSTEM/backend"
    
    if [ ! -d "$backend_dir" ]; then
        error "Backend not found at $backend_dir"
        return 1
    fi
    
    # Ensure .env exists in backend directory
    if [ ! -f "$backend_dir/.env" ]; then
        log "Creating .env in backend directory..."
        if [ -f "$ENV_FILE" ]; then
            cp "$ENV_FILE" "$backend_dir/.env"
        else
            # Create minimal .env
            cat > "$backend_dir/.env" << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bolt_db
DB_USER=bolt_user
DB_PASSWORD=${DB_PASSWORD:-bolt_password}
JWT_SECRET=$(openssl rand -base64 32)
JWT_EXPIRES_IN=7d
PORT=3001
NODE_ENV=production
EOF
        fi
    fi
    
    # Ensure .env exists in parent directory too (for compatibility)
    if [ ! -f "$ENV_FILE" ]; then
        cp "$backend_dir/.env" "$ENV_FILE"
    fi
    
    # Find entry point
    local entry=""
    for f in "dist/main.js" "dist/index.js" "main.js" "index.js" "server.js"; do
        if [ -f "$backend_dir/$f" ]; then
            entry="$f"
            break
        fi
    done
    
    if [ -z "$entry" ]; then
        error "Cannot find entry point in $backend_dir"
        ls -la "$backend_dir"
        return 1
    fi
    
    success "Found entry point: $entry"
    
    # Create ecosystem file with proper environment loading
    cat > "$INSTALL_DIR_SYSTEM/ecosystem.config.js" << EOF
module.exports = {
  apps: [{
    name: 'bolt-backend',
    cwd: '$backend_dir',
    script: '$entry',
    exec_mode: 'fork',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: ${BACKEND_PORT:-3001}
    },
    // Load .env file explicitly
    env_file: '$backend_dir/.env',
    log_file: '/var/log/bolt/backend.log',
    out_file: '/var/log/bolt/backend.out.log',
    error_file: '/var/log/bolt/backend.error.log',
    merge_logs: true,
    time: true,
    // Ensure working directory is correct
    cwd: '$backend_dir'
  }]
};
EOF
    
    # Create wrapper script that loads .env properly
    cat > "$backend_dir/start.sh" << EOF
#!/bin/bash
# BOLT Backend Startup Script
set -e

cd "\$(dirname "\$0")"

# Load environment from .env file
if [ -f .env ]; then
    export \$(grep -v '^#' .env | xargs -d '\n' 2>/dev/null || grep -v '^#' .env | xargs)
fi

# Additional exports for compatibility
export NODE_ENV=production
export PORT=\${PORT:-3001}

echo "Starting BOLT Backend..."
echo "NODE_ENV: \$NODE_ENV"
echo "PORT: \$PORT"
echo "DB_HOST: \$DB_HOST"

# Run the application
exec node $entry
EOF
    chmod +x "$backend_dir/start.sh"
    
    # Alternative: Create a Node.js launcher that loads dotenv
    cat > "$backend_dir/launcher.js" << 'EOF'
// Launcher script that ensures dotenv is loaded
const path = require('path');
const fs = require('fs');

// Try to load .env
const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
    require('dotenv').config({ path: envPath });
    console.log('Loaded .env from:', envPath);
} else {
    console.warn('No .env file found at:', envPath);
}

// Also try parent directory
const parentEnvPath = path.join(__dirname, '..', '.env');
if (fs.existsSync(parentEnvPath) && !fs.existsSync(envPath)) {
    require('dotenv').config({ path: parentEnvPath });
    console.log('Loaded .env from parent:', parentEnvPath);
}

// Start the actual application
const entryPoint = process.argv[2] || 'dist/main.js';
console.log('Starting:', entryPoint);
require(path.join(__dirname, entryPoint));
EOF
    
    success "Configuration fixed"
    info "Files updated:"
    info "  - $backend_dir/.env"
    info "  - $INSTALL_DIR_SYSTEM/ecosystem.config.js"
    info "  - $backend_dir/start.sh"
    info "  - $backend_dir/launcher.js"
    info ""
    info "Restart with: ./bolt.sh restart"
}

# =============================================================================
# Service Management
# =============================================================================

docker_start() {
    log "Starting BOLT (Docker)..."
    check_docker
    cd "$SCRIPT_DIR"
    docker-compose up -d
    success "Services started"
    sleep 5
    
    if curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
        success "Backend ready"
    else
        warn "Backend starting..."
    fi
}

docker_stop() {
    log "Stopping..."
    check_docker
    cd "$SCRIPT_DIR"
    docker-compose down
    success "Stopped"
}

native_start() {
    log "Starting BOLT (Native)..."
    
    # Start PostgreSQL
    if command -v systemctl &> /dev/null; then
        systemctl start postgresql 2>/dev/null || true
    elif command -v service &> /dev/null; then
        service postgresql start 2>/dev/null || true
    fi
    
    # Start Nginx
    if command -v systemctl &> /dev/null; then
        systemctl start nginx 2>/dev/null || true
    elif command -v service &> /dev/null; then
        service nginx start 2>/dev/null || true
    else
        nginx 2>/dev/null || true
    fi
    
    # Start Backend
    local backend_dir="$INSTALL_DIR_SYSTEM/backend"
    
    if [ ! -d "$backend_dir" ]; then
        error "Backend not found at $backend_dir"
        return 1
    fi
    
    # Check if fix is needed
    if [ ! -f "$backend_dir/.env" ] || [ ! -f "$INSTALL_DIR_SYSTEM/ecosystem.config.js" ]; then
        warn "Configuration incomplete, running fix..."
        cmd_fix
    fi
    
    if command -v pm2 &> /dev/null; then
        cd "$INSTALL_DIR_SYSTEM"
        
        # Try ecosystem first
        if [ -f "ecosystem.config.js" ]; then
            pm2 start ecosystem.config.js 2>/dev/null || pm2 restart ecosystem.config.js
        else
            # Fallback to direct start with launcher
            cd "$backend_dir"
            pm2 start launcher.js --name "bolt-backend" || pm2 restart "bolt-backend"
        fi
        
        pm2 save
        success "Backend started with PM2"
    else
        # Direct start
        cd "$backend_dir"
        nohup ./start.sh > /var/log/bolt/backend.log 2>&1 &
        success "Backend started (PID: $!)"
    fi
    
    sleep 3
    if curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
        success "Backend responding on port ${BACKEND_PORT:-3001}"
    else
        warn "Backend may still be starting, check: ./bolt.sh logs"
    fi
}

native_stop() {
    log "Stopping..."
    
    if command -v pm2 &> /dev/null; then
        pm2 stop bolt-backend 2>/dev/null || true
        pm2 delete bolt-backend 2>/dev/null || true
    fi
    
    pkill -f "node.*bolt" 2>/dev/null || true
    
    if command -v systemctl &> /dev/null; then
        systemctl stop nginx 2>/dev/null || true
    elif command -v service &> /dev/null; then
        service nginx stop 2>/dev/null || true
    fi
    
    success "Stopped"
}

native_logs() {
    local service="${1:-backend}"
    
    case "$service" in
        backend|api|"")
            if command -v pm2 &> /dev/null; then
                pm2 logs bolt-backend --lines 100
            else
                tail -f /var/log/bolt/backend.log 2>/dev/null || \
                tail -f /var/log/bolt/*.log 2>/dev/null || \
                error "No logs found"
            fi
            ;;
        nginx)
            tail -f /var/log/nginx/*.log 2>/dev/null || error "Nginx logs not found"
            ;;
        postgres|db)
            tail -f /var/log/postgresql/*.log 2>/dev/null || error "PG logs not found"
            ;;
        *)
            info "Available: backend, nginx, postgres"
            ;;
    esac
}

# =============================================================================
# Main Commands
# =============================================================================

cmd_start() {
    load_env
    case "$INSTALL_MODE" in
        docker) docker_start ;;
        native|container) native_start ;;
        *) error "Unknown mode: $INSTALL_MODE"; exit 1 ;;
    esac
}

cmd_stop() {
    load_env
    case "$INSTALL_MODE" in
        docker) docker_stop ;;
        native|container) native_stop ;;
        *) error "Unknown mode"; exit 1 ;;
    esac
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    load_env
    case "$INSTALL_MODE" in
        docker)
            check_docker
            cd "$SCRIPT_DIR"
            docker-compose ps
            ;;
        native|container)
            if command -v pm2 &> /dev/null; then
                pm2 status
            fi
            echo ""
            info "Health Checks"
            if curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
                success "Backend: OK"
            else
                error "Backend: Not responding"
            fi
            ;;
    esac
}

cmd_logs() {
    load_env
    case "$INSTALL_MODE" in
        docker)
            check_docker
            cd "$SCRIPT_DIR"
            docker-compose logs -f "${1:-}"
            ;;
        native|container)
            native_logs "$1"
            ;;
    esac
}

# =============================================================================
# Other Commands
# =============================================================================

cmd_db() {
    load_env
    local cmd="$1"
    
    case "$cmd" in
        console|psql)
            case "$INSTALL_MODE" in
                docker)
                    check_docker
                    cd "$SCRIPT_DIR"
                    docker-compose exec postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}"
                    ;;
                native|container)
                    psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" 2>/dev/null || \
                    sudo -u postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}"
                    ;;
            esac
            ;;
        backup)
            local backup_dir="/var/backups/bolt"
            mkdir -p "$backup_dir"
            local date_stamp=$(date +%Y%m%d_%H%M%S)
            
            case "$INSTALL_MODE" in
                docker)
                    docker-compose exec -T postgres pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" | gzip > "$backup_dir/db_$date_stamp.sql.gz"
                    ;;
                native|container)
                    pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" 2>/dev/null | gzip > "$backup_dir/db_$date_stamp.sql.gz" || \
                    sudo -u postgres pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" | gzip > "$backup_dir/db_$date_stamp.sql.gz"
                    ;;
            esac
            success "Database backup: $backup_dir/db_$date_stamp.sql.gz"
            ;;
        *)
            info "DB commands: console, backup"
            ;;
    esac
}

cmd_shell() {
    load_env
    local svc="$1"
    case "$INSTALL_MODE" in
        docker)
            check_docker
            case "$svc" in
                backend) docker-compose exec backend /bin/sh ;;
                postgres) docker-compose exec postgres /bin/bash ;;
                *) error "Use: backend, postgres" ;;
            esac
            ;;
        native|container)
            case "$svc" in
                backend) cd "$INSTALL_DIR_SYSTEM/backend" && /bin/bash ;;
                postgres) sudo -u postgres /bin/bash 2>/dev/null || su - postgres ;;
                *) error "Use: backend, postgres" ;;
            esac
            ;;
    esac
}

cmd_clean() {
    log "Cleaning..."
    case "$INSTALL_MODE" in
        docker)
            docker system prune -f
            ;;
        native|container)
            npm cache clean --force 2>/dev/null || true
            find /var/log/bolt -name "*.log" -mtime +7 -delete 2>/dev/null || true
            ;;
    esac
    success "Cleaned"
}

cmd_reset() {
    warn "⚠ DELETE ALL DATA?"
    read -p "Type 'DELETE': " confirm
    [ "$confirm" != "DELETE" ] && return
    
    cmd_stop
    case "$INSTALL_MODE" in
        docker)
            cd "$SCRIPT_DIR"
            docker-compose down -v
            rm -rf uploads/*
            ;;
        native|container)
            rm -rf "$INSTALL_DIR_SYSTEM/uploads/*"
            sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME:-bolt_db};" 2>/dev/null || true
            ;;
    esac
    success "Reset complete"
}

cmd_update() {
    log "Updating..."
    case "$INSTALL_MODE" in
        docker)
            check_docker
            cd "$SCRIPT_DIR"
            docker-compose pull && docker-compose up -d
            ;;
        native|container)
            cd "$SCRIPT_DIR"
            git pull 2>/dev/null || true
            bash install.sh
            ;;
    esac
    success "Updated"
}

# =============================================================================
# Main
# =============================================================================

main() {
    load_env 2>/dev/null || true
    
    case "$1" in
        start) cmd_start ;;
        stop) cmd_stop ;;
        restart) cmd_restart ;;
        status) cmd_status ;;
        logs) cmd_logs "$2" ;;
        env) cmd_env ;;
        fix) cmd_fix ;;
        db) cmd_db "$2" ;;
        shell) cmd_shell "$2" ;;
        backup) cmd_db backup ;;
        clean) cmd_clean ;;
        reset) cmd_reset ;;
        update) cmd_update ;;
        install) bash "${SCRIPT_DIR}/install.sh" ;;
        help|--help|-h|*) print_help ;;
    esac
}

main "$@"