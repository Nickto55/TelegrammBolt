#!/bin/bash

# =============================================================================
# BOLT - Management Script v2.1
# =============================================================================
# Fixed: Auto-detects correct entry point for NestJS/Node.js apps
# =============================================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR_SYSTEM="/opt/bolt"
ENV_FILE="$SCRIPT_DIR/.env"
[ -f "$INSTALL_DIR_SYSTEM/.env" ] && ENV_FILE="$INSTALL_DIR_SYSTEM/.env"

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
║                    BOLT Management Script v2.1                   ║
║                    Mode: ${INSTALL_MODE^^}                                 ║
╚══════════════════════════════════════════════════════════════════╝

Usage: ./bolt.sh [command] [options]

Commands:
  start              Start all services
  stop               Stop all services
  restart            Restart all services
  status             Show service status
  logs [service]     View logs (backend/frontend/postgres/nginx)
  update             Update to latest version
  backup             Create manual backup
  restore [file]     Restore from backup file
  shell [service]    Open shell (backend/postgres/nginx)
  db [command]       Database operations (backup/restore/console)
  clean              Clean up resources
  reset              Reset all data (DANGEROUS!)
  fix                Fix/repair installation
  install            Run full installation
  help               Show this help message

EOF
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
}

load_env() {
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
    fi
}

# =============================================================================
# Find Entry Point
# =============================================================================

find_entry_point() {
    local backend_dir="$1"
    
    # Check common locations
    local candidates=(
        "main.js"
        "index.js"
        "server.js"
        "app.js"
        "dist/main.js"
        "dist/index.js"
        "dist/server.js"
        "build/main.js"
        "src/main.js"
    )
    
    for candidate in "${candidates[@]}"; do
        if [ -f "$backend_dir/$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done
    
    # Find any JS file that looks like entry point
    local found=$(find "$backend_dir" -maxdepth 2 -name "*.js" -type f 2>/dev/null | \
        grep -E "(main|index|server|app)" | head -1)
    
    if [ -n "$found" ]; then
        echo "$(basename "$found")"
        return 0
    fi
    
    # Last resort - first JS file in dist or root
    found=$(find "$backend_dir" -maxdepth 2 -name "*.js" -type f 2>/dev/null | head -1)
    if [ -n "$found" ]; then
        echo "$(basename "$found")"
        return 0
    fi
    
    return 1
}

# =============================================================================
# Fix Installation
# =============================================================================

cmd_fix() {
    log "Repairing installation..."
    load_env
    
    if [ "$INSTALL_MODE" != "native" ] && [ "$INSTALL_MODE" != "container" ]; then
        error "Fix command only for native/container mode"
        return 1
    fi
    
    local backend_dir="$INSTALL_DIR_SYSTEM/backend"
    
    if [ ! -d "$backend_dir" ]; then
        error "Backend not found at $backend_dir"
        return 1
    fi
    
    # Find correct entry point
    local entry=$(find_entry_point "$backend_dir")
    if [ -z "$entry" ]; then
        error "Cannot find entry point in $backend_dir"
        ls -la "$backend_dir"
        return 1
    fi
    
    success "Found entry point: $entry"
    
    # Update PM2 ecosystem config
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
    env: { NODE_ENV: 'production' },
    log_file: '/var/log/bolt/backend.log',
    out_file: '/var/log/bolt/backend.out.log',
    error_file: '/var/log/bolt/backend.error.log',
    merge_logs: true,
    time: true
  }]
};
EOF
    
    # Create fallback start script
    cat > "$backend_dir/start.sh" << EOF
#!/bin/bash
cd \$(dirname "\$0")
export NODE_ENV=production
[ -f ../.env ] && export \$(grep -v '^#' ../.env | xargs 2>/dev/null)
[ -f .env ] && export \$(grep -v '^#' .env | xargs 2>/dev/null)
exec node $entry
EOF
    chmod +x "$backend_dir/start.sh"
    
    success "Configuration fixed"
    info "Entry point: $entry"
    info "Restart with: ./bolt.sh restart"
}

# =============================================================================
# Service Management
# =============================================================================

docker_start() {
    log "Starting BOLT services (Docker)..."
    check_docker
    cd "$SCRIPT_DIR"
    docker-compose up -d
    success "Services started"
    
    sleep 5
    
    if curl -s "http://localhost:${BACKEND_PORT:-3001}/health" > /dev/null 2>&1 || \
       curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
        success "Backend ready at http://localhost:${BACKEND_PORT:-3001}"
    else
        warn "Backend may still be starting..."
    fi
}

docker_stop() {
    log "Stopping..."
    check_docker
    cd "$SCRIPT_DIR"
    docker-compose down
    success "Stopped"
}

docker_restart() {
    docker_stop
    sleep 2
    docker_start
}

docker_status() {
    log "Docker Status"
    check_docker
    cd "$SCRIPT_DIR"
    docker-compose ps
    
    echo ""
    info "Health Checks"
    if curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
        success "Backend: OK"
    else
        error "Backend: Not responding"
    fi
}

docker_logs() {
    local service="$1"
    check_docker
    cd "$SCRIPT_DIR"
    if [ -n "$service" ]; then
        docker-compose logs -f "$service"
    else
        docker-compose logs -f
    fi
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
    if command -v pm2 &> /dev/null; then
        cd "$INSTALL_DIR_SYSTEM"
        
        # Check if ecosystem exists
        if [ -f "ecosystem.config.js" ]; then
            pm2 start ecosystem.config.js 2>/dev/null || pm2 restart ecosystem.config.js
        else
            # Direct start with auto-detect
            local backend_dir="$INSTALL_DIR_SYSTEM/backend"
            local entry=$(find_entry_point "$backend_dir")
            
            if [ -n "$entry" ]; then
                cd "$backend_dir"
                pm2 start "$entry" --name "bolt-backend" || pm2 restart "bolt-backend"
            else
                error "Cannot find entry point"
                return 1
            fi
        fi
        
        pm2 save
        success "Backend started with PM2"
    else
        # Direct node execution
        local backend_dir="$INSTALL_DIR_SYSTEM/backend"
        local entry=$(find_entry_point "$backend_dir")
        
        if [ -n "$entry" ]; then
            cd "$backend_dir"
            nohup node "$entry" > /var/log/bolt/backend.log 2>&1 &
            success "Backend started (PID: $!)"
        else
            error "Cannot find entry point"
            return 1
        fi
    fi
    
    sleep 3
    if curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
        success "Backend responding on port ${BACKEND_PORT:-3001}"
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

native_restart() {
    native_stop
    sleep 2
    native_start
}

native_status() {
    log "Native Status"
    
    if command -v pm2 &> /dev/null; then
        pm2 status
    fi
    
    echo ""
    info "Process Checks"
    
    if pgrep -f "node.*main\|node.*index\|node.*server" > /dev/null; then
        success "Backend process: Running"
    else
        error "Backend process: Not running"
    fi
    
    if curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
        success "Backend API: Responding"
    else
        error "Backend API: Not responding"
    fi
    
    if pgrep nginx > /dev/null; then
        success "Nginx: Running"
    fi
}

native_logs() {
    local service="$1"
    
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
# Unified Commands
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
    load_env
    case "$INSTALL_MODE" in
        docker) docker_restart ;;
        native|container) native_restart ;;
        *) error "Unknown mode"; exit 1 ;;
    esac
}

cmd_status() {
    load_env
    case "$INSTALL_MODE" in
        docker) docker_status ;;
        native|container) native_status ;;
        *) error "Unknown mode"; exit 1 ;;
    esac
}

cmd_logs() {
    load_env
    case "$INSTALL_MODE" in
        docker) docker_logs "$1" ;;
        native|container) native_logs "$1" ;;
        *) error "Unknown mode"; exit 1 ;;
    esac
}

# =============================================================================
# Other Commands (Backup, Restore, DB, etc.)
# =============================================================================

cmd_backup() {
    load_env
    local backup_dir="/var/backups/bolt"
    mkdir -p "$backup_dir"
    local date_stamp=$(date +%Y%m%d_%H%M%S)
    
    log "Creating backup..."
    
    # Database
    case "$INSTALL_MODE" in
        docker)
            docker-compose exec -T postgres pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" 2>/dev/null | gzip > "$backup_dir/db_$date_stamp.sql.gz" || \
            warn "DB backup failed"
            ;;
        native|container)
            pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" 2>/dev/null | gzip > "$backup_dir/db_$date_stamp.sql.gz" || \
            sudo -u postgres pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" 2>/dev/null | gzip > "$backup_dir/db_$date_stamp.sql.gz" || \
            warn "DB backup failed"
            ;;
    esac
    
    # Uploads
    local upload_dir="$INSTALL_DIR_SYSTEM/uploads"
    [ "$INSTALL_MODE" = "docker" ] && upload_dir="$SCRIPT_DIR/uploads"
    
    if [ -d "$upload_dir" ] && [ "$(ls -A "$upload_dir" 2>/dev/null)" ]; then
        tar -czf "$backup_dir/uploads_$date_stamp.tar.gz" -C "$(dirname "$upload_dir")" "$(basename "$upload_dir")" 2>/dev/null || true
    fi
    
    success "Backup: $backup_dir"
    ls -lh "$backup_dir"/*.gz 2>/dev/null | tail -5
}

cmd_db() {
    load_env
    local cmd="$1"
    
    case "$cmd" in
        backup) cmd_backup ;;
        restore)
            # List backups
            ls -la /var/backups/bolt/ 2>/dev/null || ls -la "${SCRIPT_DIR}/backups/" 2>/dev/null || error "No backups"
            ;;
        console|psql)
            case "$INSTALL_MODE" in
                docker) docker-compose exec postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" ;;
                native|container) 
                    psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" 2>/dev/null || \
                    sudo -u postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}"
                    ;;
            esac
            ;;
        *) info "Commands: backup, restore, console" ;;
    esac
}

cmd_shell() {
    load_env
    local svc="$1"
    case "$INSTALL_MODE" in
        docker)
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

cmd_update() {
    log "Updating..."
    load_env
    
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
    
    case "$INSTALL_MODE" in
        docker)
            cd "$SCRIPT_DIR"
            docker-compose down -v
            rm -rf uploads/*
            ;;
        native|container)
            native_stop
            rm -rf "$INSTALL_DIR_SYSTEM/uploads/*"
            sudo -u postgres psql -c "DROP DATABASE ${DB_NAME:-bolt_db};" 2>/dev/null || true
            ;;
    esac
    success "Reset complete"
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
        backup) cmd_backup ;;
        db) cmd_db "$2" ;;
        shell) cmd_shell "$2" ;;
        update) cmd_update ;;
        clean) cmd_clean ;;
        reset) cmd_reset ;;
        fix) cmd_fix ;;
        install) bash "${SCRIPT_DIR}/install.sh" ;;
        help|--help|-h|*) print_help ;;
    esac
}

main "$@"