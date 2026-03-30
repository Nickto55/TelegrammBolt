#!/bin/bash

# =============================================================================
# BOLT - Management Script v2.0
# =============================================================================
# Usage: ./bolt.sh [command] [options]
# Supports: Docker, Native, and Container modes
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR_SYSTEM="/opt/bolt"
ENV_FILE="$SCRIPT_DIR/.env"
[ -f "$INSTALL_DIR_SYSTEM/.env" ] && ENV_FILE="$INSTALL_DIR_SYSTEM/.env"

# Detect installation mode
detect_mode() {
    if [ -f "$SCRIPT_DIR/docker-compose.yml" ] && [ -d "$SCRIPT_DIR/.git" ] 2>/dev/null; then
        echo "docker"
    elif [ -d "$INSTALL_DIR_SYSTEM/backend" ] && [ -f "$INSTALL_DIR_SYSTEM/ecosystem.config.js" ]; then
        echo "native"
    elif [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        echo "container"
    else
        echo "unknown"
    fi
}

INSTALL_MODE=$(detect_mode)

# =============================================================================
# Helper Functions
# =============================================================================

log() { echo -e "${BLUE}[BOLT]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${CYAN}[i]${NC} $1"; }

print_help() {
    cat << EOF
╔══════════════════════════════════════════════════════════════════╗
║                    BOLT Management Script v2.0                   ║
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
  install            Run full installation
  help               Show this help message

Examples:
  ./bolt.sh start                    # Start all services
  ./bolt.sh logs backend             # View backend logs
  ./bolt.sh db backup                # Backup database
  ./bolt.sh shell postgres           # Open database console

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
    else
        warn "Environment file not found: $ENV_FILE"
    fi
}

# =============================================================================
# Service Management - Docker Mode
# =============================================================================

docker_start() {
    log "Starting BOLT services (Docker)..."
    check_docker
    cd "$SCRIPT_DIR"
    docker-compose up -d
    success "Services started"
    
    info "Waiting for services..."
    sleep 5
    
    if curl -s "http://localhost:${BACKEND_PORT:-3001}/health" > /dev/null 2>&1 || \
       curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
        success "Backend ready at http://localhost:${BACKEND_PORT:-3001}"
    else
        warn "Backend may still be starting..."
    fi
    
    info "Frontend: http://localhost:${FRONTEND_PORT:-5173}"
}

docker_stop() {
    log "Stopping BOLT services..."
    check_docker
    cd "$SCRIPT_DIR"
    docker-compose down
    success "Services stopped"
}

docker_restart() {
    log "Restarting..."
    docker_stop
    sleep 2
    docker_start
}

docker_status() {
    log "Service Status (Docker)"
    echo "─────────────────────────────────────────────────────────────────────"
    check_docker
    cd "$SCRIPT_DIR"
    docker-compose ps
    
    echo ""
    info "Health Checks"
    echo "─────────────────────────────────────────────────────────────────────"
    
    if curl -s "http://localhost:${BACKEND_PORT:-3001}/health" > /dev/null 2>&1 || \
       curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
        success "Backend API: OK"
    else
        error "Backend API: Not responding"
    fi
    
    if curl -s "http://localhost:${FRONTEND_PORT:-5173}" > /dev/null 2>&1; then
        success "Frontend: OK"
    else
        error "Frontend: Not responding"
    fi
    
    if docker-compose exec -T postgres pg_isready -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" > /dev/null 2>&1; then
        success "Database: OK"
    else
        warn "Database: Check skipped"
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

# =============================================================================
# Service Management - Native/Container Mode
# =============================================================================

native_start() {
    log "Starting BOLT services (Native)..."
    
    # Start PostgreSQL if local
    if command -v systemctl &> /dev/null && systemctl is-active --quiet postgresql 2>/dev/null; then
        success "PostgreSQL already running"
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
    
    # Start Backend with PM2
    if command -v pm2 &> /dev/null; then
        cd "$INSTALL_DIR_SYSTEM"
        pm2 start ecosystem.config.js 2>/dev/null || pm2 restart ecosystem.config.js
        pm2 save
        success "Backend started with PM2"
    else
        # Direct start
        cd "$INSTALL_DIR_SYSTEM/backend"
        nohup ./start.sh > /var/log/bolt/backend.log 2>&1 &
        success "Backend started directly"
    fi
    
    sleep 3
    if curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
        success "Backend ready on port ${BACKEND_PORT:-3001}"
    fi
}

native_stop() {
    log "Stopping BOLT services..."
    
    if command -v pm2 &> /dev/null; then
        pm2 stop bolt-backend 2>/dev/null || true
        pm2 delete bolt-backend 2>/dev/null || true
    fi
    
    # Kill node processes
    pkill -f "node.*main.js" 2>/dev/null || true
    
    if command -v systemctl &> /dev/null; then
        systemctl stop nginx 2>/dev/null || true
    elif command -v service &> /dev/null; then
        service nginx stop 2>/dev/null || true
    fi
    
    success "Services stopped"
}

native_restart() {
    native_stop
    sleep 2
    native_start
}

native_status() {
    log "Service Status (Native)"
    echo "─────────────────────────────────────────────────────────────────────"
    
    # Check PM2
    if command -v pm2 &> /dev/null; then
        pm2 status
    fi
    
    echo ""
    info "Process Checks"
    echo "─────────────────────────────────────────────────────────────────────"
    
    if pgrep -f "node.*main.js" > /dev/null; then
        success "Backend process: Running"
    else
        error "Backend process: Not running"
    fi
    
    if curl -s "http://localhost:${BACKEND_PORT:-3001}" > /dev/null 2>&1; then
        success "Backend API: Responding"
    else
        error "Backend API: Not responding"
    fi
    
    if curl -s "http://localhost:80" > /dev/null 2>&1; then
        success "Nginx: Responding"
    else
        warn "Nginx: Check manually"
    fi
    
    if pgrep nginx > /dev/null; then
        success "Nginx process: Running"
    fi
}

native_logs() {
    local service="$1"
    
    case "$service" in
        backend|api)
            if [ -f "/var/log/bolt/backend.log" ]; then
                tail -f "/var/log/bolt/backend.log"
            elif command -v pm2 &> /dev/null; then
                pm2 logs bolt-backend
            else
                error "No logs found"
            fi
            ;;
        nginx)
            tail -f /var/log/nginx/access.log /var/log/nginx/error.log 2>/dev/null || \
            tail -f /var/log/nginx/*.log 2>/dev/null || \
            error "Nginx logs not found"
            ;;
        postgres|db)
            if [ -f "/var/log/postgresql/postgresql.log" ]; then
                tail -f /var/log/postgresql/postgresql.log
            else
                error "PostgreSQL logs not found"
            fi
            ;;
        *)
            info "Available logs: backend, nginx, postgres"
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
        *) error "Unknown installation mode"; exit 1 ;;
    esac
}

cmd_stop() {
    load_env
    case "$INSTALL_MODE" in
        docker) docker_stop ;;
        native|container) native_stop ;;
        *) error "Unknown installation mode"; exit 1 ;;
    esac
}

cmd_restart() {
    load_env
    case "$INSTALL_MODE" in
        docker) docker_restart ;;
        native|container) native_restart ;;
        *) error "Unknown installation mode"; exit 1 ;;
    esac
}

cmd_status() {
    load_env
    case "$INSTALL_MODE" in
        docker) docker_status ;;
        native|container) native_status ;;
        *) error "Unknown installation mode"; exit 1 ;;
    esac
}

cmd_logs() {
    load_env
    case "$INSTALL_MODE" in
        docker) docker_logs "$1" ;;
        native|container) native_logs "$1" ;;
        *) error "Unknown installation mode"; exit 1 ;;
    esac
}

# =============================================================================
# Update & Maintenance
# =============================================================================

cmd_update() {
    log "Updating BOLT..."
    load_env
    
    case "$INSTALL_MODE" in
        docker)
            check_docker
            cd "$SCRIPT_DIR"
            docker-compose pull
            docker-compose build --no-cache
            docker-compose up -d
            ;;
        native|container)
            cd "$SCRIPT_DIR"
            git pull 2>/dev/null || warn "Git pull failed"
            bash install.sh
            ;;
    esac
    
    success "Update completed"
}

cmd_backup() {
    load_env
    local backup_dir="${SCRIPT_DIR}/backups"
    [ "$INSTALL_MODE" = "native" ] && backup_dir="/var/backups/bolt"
    
    mkdir -p "$backup_dir"
    local date_stamp=$(date +%Y%m%d_%H%M%S)
    
    log "Creating backup..."
    
    # Database backup
    case "$INSTALL_MODE" in
        docker)
            if docker-compose exec -T postgres pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" > "$backup_dir/db_$date_stamp.sql" 2>/dev/null; then
                gzip "$backup_dir/db_$date_stamp.sql"
                success "Database: db_$date_stamp.sql.gz"
            fi
            ;;
        native|container)
            if command -v pg_dump &> /dev/null; then
                pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" | gzip > "$backup_dir/db_$date_stamp.sql.gz" 2>/dev/null || \
                sudo -u postgres pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" | gzip > "$backup_dir/db_$date_stamp.sql.gz"
                success "Database: db_$date_stamp.sql.gz"
            fi
            ;;
    esac
    
    # Uploads backup
    local upload_dir="${SCRIPT_DIR}/uploads"
    [ "$INSTALL_MODE" = "native" ] && upload_dir="$INSTALL_DIR_SYSTEM/uploads"
    
    if [ -d "$upload_dir" ] && [ "$(ls -A "$upload_dir" 2>/dev/null)" ]; then
        tar -czf "$backup_dir/uploads_$date_stamp.tar.gz" -C "$(dirname "$upload_dir")" "$(basename "$upload_dir")"
        success "Uploads: uploads_$date_stamp.tar.gz"
    fi
    
    # Config backup
    if [ "$INSTALL_MODE" = "docker" ]; then
        tar -czf "$backup_dir/config_$date_stamp.tar.gz" -C "$SCRIPT_DIR" .env docker-compose.yml nginx 2>/dev/null || true
    else
        tar -czf "$backup_dir/config_$date_stamp.tar.gz" -C "$INSTALL_DIR_SYSTEM" .env ecosystem.config.js 2>/dev/null || true
    fi
    success "Config: config_$date_stamp.tar.gz"
    
    # Cleanup old backups
    find "$backup_dir" -name "*.gz" -mtime +30 -delete 2>/dev/null || true
    
    success "Backup in $backup_dir"
}

cmd_restore() {
    load_env
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        local backup_dir="${SCRIPT_DIR}/backups"
        [ "$INSTALL_MODE" = "native" ] && backup_dir="/var/backups/bolt"
        
        log "Available backups:"
        ls -la "$backup_dir" 2>/dev/null || error "No backups found"
        return
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "Backup not found: $backup_file"
        exit 1
    fi
    
    warn "This will overwrite existing data!"
    read -p "Type 'yes' to confirm: " confirm
    [ "$confirm" != "yes" ] && { log "Cancelled"; return; }
    
    log "Restoring from $backup_file..."
    
    if [[ "$backup_file" == *"db_"* ]]; then
        case "$INSTALL_MODE" in
            docker)
                if [[ "$backup_file" == *".gz" ]]; then
                    gunzip -c "$backup_file" | docker-compose exec -T postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}"
                else
                    docker-compose exec -T postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" < "$backup_file"
                fi
                ;;
            native|container)
                if [[ "$backup_file" == *".gz" ]]; then
                    gunzip -c "$backup_file" | psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" 2>/dev/null || \
                    sudo -u postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" < <(gunzip -c "$backup_file")
                else
                    psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" < "$backup_file" 2>/dev/null || \
                    sudo -u postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" < "$backup_file"
                fi
                ;;
        esac
        success "Database restored"
    fi
    
    if [[ "$backup_file" == *"uploads_"* ]]; then
        local upload_dir="${SCRIPT_DIR}"
        [ "$INSTALL_MODE" = "native" ] && upload_dir="$INSTALL_DIR_SYSTEM"
        tar -xzf "$backup_file" -C "$upload_dir"
        success "Uploads restored"
    fi
}

cmd_clean() {
    log "Cleaning up..."
    
    case "$INSTALL_MODE" in
        docker)
            docker container prune -f
            docker image prune -f
            docker volume prune -f
            docker network prune -f
            ;;
        native|container)
            # Clean npm cache
            npm cache clean --force 2>/dev/null || true
            # Clean logs
            find /var/log/bolt -name "*.log" -mtime +7 -delete 2>/dev/null || true
            ;;
    esac
    
    success "Cleanup completed"
}

cmd_reset() {
    warn "⚠⚠⚠ DANGER: This will DELETE ALL DATA! ⚠⚠⚠"
    echo "This will:"
    echo "  - Stop all services"
    echo "  - Delete all data"
    echo ""
    read -p "Type 'DELETE EVERYTHING' to confirm: " confirm
    [ "$confirm" != "DELETE EVERYTHING" ] && { log "Cancelled"; return; }
    
    log "Resetting BOLT..."
    
    case "$INSTALL_MODE" in
        docker)
            cd "$SCRIPT_DIR"
            docker-compose down -v
            rm -rf uploads/*
            ;;
        native|container)
            native_stop
            rm -rf "$INSTALL_DIR_SYSTEM/uploads/*"
            # Drop and recreate database
            psql -U postgres -c "DROP DATABASE IF EXISTS ${DB_NAME:-bolt_db};" 2>/dev/null || \
            sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME:-bolt_db};"
            setup_postgres
            ;;
    esac
    
    success "Reset completed. Run './bolt.sh start' to start fresh."
}

# =============================================================================
# Database Operations
# =============================================================================

cmd_db() {
    load_env
    local subcommand="$1"
    
    case "$subcommand" in
        backup)
            cmd_backup
            ;;
        restore)
            cmd_restore "$2"
            ;;
        console|psql|shell)
            case "$INSTALL_MODE" in
                docker)
                    docker-compose exec postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}"
                    ;;
                native|container)
                    psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" 2>/dev/null || \
                    sudo -u postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}"
                    ;;
            esac
            ;;
        migrate)
            case "$INSTALL_MODE" in
                docker)
                    docker-compose exec backend npm run db:migrate 2>/dev/null || \
                    docker-compose exec backend npx sequelize-cli db:migrate
                    ;;
                native|container)
                    cd "$INSTALL_DIR_SYSTEM/backend"
                    npm run db:migrate 2>/dev/null || npx sequelize-cli db:migrate
                    ;;
            esac
            success "Migrations completed"
            ;;
        *)
            info "Database commands:"
            echo "  db backup    - Backup database"
            echo "  db restore   - Restore database"
            echo "  db console   - Open psql console"
            echo "  db migrate   - Run migrations"
            ;;
    esac
}

# =============================================================================
# Shell Access
# =============================================================================

cmd_shell() {
    load_env
    local service="$1"
    
    [ -z "$service" ] && { error "Specify: backend, postgres, or nginx"; exit 1; }
    
    case "$INSTALL_MODE" in
        docker)
            case "$service" in
                backend|api) docker-compose exec backend /bin/sh ;;
                postgres|db) docker-compose exec postgres /bin/bash ;;
                nginx|frontend) docker-compose exec frontend /bin/sh ;;
                *) error "Unknown service: $service" ;;
            esac
            ;;
        native|container)
            case "$service" in
                backend|api)
                    cd "$INSTALL_DIR_SYSTEM/backend"
                    /bin/bash
                    ;;
                postgres|db)
                    sudo -u postgres /bin/bash 2>/dev/null || su - postgres
                    ;;
                nginx)
                    cd /etc/nginx && /bin/bash
                    ;;
                *) error "Unknown service: $service" ;;
            esac
            ;;
    esac
}

# =============================================================================
# SSL Certificate (Docker only primarily)
# =============================================================================

cmd_cert() {
    load_env
    local subcommand="$1"
    
    case "$subcommand" in
        renew)
            if command -v certbot &> /dev/null; then
                sudo certbot renew --force-renewal
                [ "$INSTALL_MODE" = "docker" ] && docker-compose restart nginx
                [ "$INSTALL_MODE" = "native" ] && sudo systemctl reload nginx 2>/dev/null || true
                success "Certificate renewed"
            else
                error "certbot not installed"
            fi
            ;;
        status)
            sudo certbot certificates 2>/dev/null || info "No certificates found"
            ;;
        *)
            info "SSL commands: cert renew, cert status"
            ;;
    esac
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
        update) cmd_update ;;
        backup) cmd_backup ;;
        restore) cmd_restore "$2" ;;
        shell) cmd_shell "$2" ;;
        db) cmd_db "$2" "$3" ;;
        cert) cmd_cert "$2" ;;
        clean) cmd_clean ;;
        reset) cmd_reset ;;
        install) bash "${SCRIPT_DIR}/install.sh" ;;
        help|--help|-h) print_help ;;
        *) print_help; exit 1 ;;
    esac
}

main "$@"