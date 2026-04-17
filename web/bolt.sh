#!/bin/bash

# =============================================================================
# BOLT - Management Script
# =============================================================================
# Usage: ./bolt.sh [command] [options]
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
COMPOSE_FILE="$SCRIPT_DIR/docker compose.yml"
ENV_FILE="$SCRIPT_DIR/.env"

# =============================================================================
# Helper Functions
# =============================================================================

log() { echo -e "${BLUE}[BOLT]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${CYAN}[i]${NC} $1"; }

print_help() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║                    BOLT Management Script                        ║
╚══════════════════════════════════════════════════════════════════╝

Usage: ./bolt.sh [command] [options]

Commands:
  start              Start all services
  stop               Stop all services
  restart            Restart all services
  status             Show service status
  logs [service]     View logs (optionally for specific service)
  update             Update to latest version
  backup             Create manual backup
  restore [file]     Restore from backup file
  shell [service]    Open shell in container (backend/frontend/postgres)
  db [command]       Database operations
    db backup        Backup database
    db restore       Restore database
    db migrate       Run migrations
    db console       Open psql console
  cert [command]     SSL certificate operations
    cert renew       Renew Let's Encrypt certificate
    cert status      Check certificate status
  clean              Clean up unused Docker resources
  reset              Reset all data (DANGEROUS!)
  install            Run full installation
  help               Show this help message

Examples:
  ./bolt.sh start                    # Start all services
  ./bolt.sh logs backend             # View backend logs
  ./bolt.sh shell postgres           # Open PostgreSQL console
  ./bolt.sh db backup                # Backup database
  ./bolt.sh cert renew               # Renew SSL certificate

EOF
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi
}

load_env() {
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
    else
        warn "Environment file not found: $ENV_FILE"
    fi
}

# =============================================================================
# Service Management
# =============================================================================

cmd_start() {
    log "Starting BOLT services..."
    check_docker
    cd "$SCRIPT_DIR"
    docker compose up -d
    success "Services started"
    
    info "Waiting for services to be ready..."
    sleep 5
    
    if curl -s "http://localhost:${BACKEND_PORT:-3001}/health" > /dev/null 2>&1; then
        success "Backend is ready at http://localhost:${BACKEND_PORT:-3001}"
    else
        warn "Backend may still be starting..."
    fi
    
    info "Frontend available at http://localhost:${FRONTEND_PORT:-5173}"
}

cmd_stop() {
    log "Stopping BOLT services..."
    check_docker
    cd "$SCRIPT_DIR"
    docker compose down
    success "Services stopped"
}

cmd_restart() {
    log "Restarting BOLT services..."
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    log "Service Status"
    echo "─────────────────────────────────────────────────────────────────────"
    
    check_docker
    cd "$SCRIPT_DIR"
    
    # Docker Compose status
    docker compose ps
    
    echo ""
    info "Health Checks"
    echo "─────────────────────────────────────────────────────────────────────"
    
    # Backend health
    if curl -s "http://localhost:${BACKEND_PORT:-3001}/health" > /dev/null 2>&1; then
        success "Backend API: OK"
    else
        error "Backend API: Not responding"
    fi
    
    # Frontend
    if curl -s "http://localhost:${FRONTEND_PORT:-5173}" > /dev/null 2>&1; then
        success "Frontend: OK"
    else
        error "Frontend: Not responding"
    fi
    
    # Database
    if docker compose exec -T postgres pg_isready -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" > /dev/null 2>&1; then
        success "Database: OK"
    else
        warn "Database: Check skipped or not available"
    fi
}

cmd_logs() {
    local service="$1"
    check_docker
    cd "$SCRIPT_DIR"
    
    if [ -n "$service" ]; then
        docker compose logs -f "$service"
    else
        docker compose logs -f
    fi
}

# =============================================================================
# Update & Maintenance
# =============================================================================

cmd_update() {
    log "Updating BOLT..."
    check_docker
    cd "$SCRIPT_DIR"
    
    # Pull latest images
    docker compose pull
    
    # Rebuild local images
    docker compose build --no-cache
    
    # Restart services
    docker compose up -d
    
    success "Update completed"
}

cmd_backup() {
    local backup_dir="${SCRIPT_DIR}/backups"
    local date_stamp=$(date +%Y%m%d_%H%M%S)
    
    mkdir -p "$backup_dir"
    
    log "Creating backup..."
    
    # Backup database
    if docker compose exec -T postgres pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" > "$backup_dir/db_$date_stamp.sql" 2>/dev/null; then
        gzip "$backup_dir/db_$date_stamp.sql"
        success "Database backup: backups/db_$date_stamp.sql.gz"
    else
        warn "Database backup skipped (PostgreSQL container not running)"
    fi
    
    # Backup uploads
    if [ -d "${SCRIPT_DIR}/uploads" ]; then
        tar -czf "$backup_dir/uploads_$date_stamp.tar.gz" -C "$SCRIPT_DIR" uploads
        success "Uploads backup: backups/uploads_$date_stamp.tar.gz"
    fi
    
    # Backup configuration
    tar -czf "$backup_dir/config_$date_stamp.tar.gz" -C "$SCRIPT_DIR" .env docker compose.yml nginx
    success "Config backup: backups/config_$date_stamp.tar.gz"
    
    # Cleanup old backups (keep 30 days)
    find "$backup_dir" -name "*.gz" -mtime +30 -delete 2>/dev/null || true
    
    success "Backup completed in $backup_dir"
}

cmd_restore() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        # List available backups
        log "Available backups:"
        ls -la "${SCRIPT_DIR}/backups/" 2>/dev/null || error "No backups found"
        return
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    warn "This will overwrite existing data!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log "Restore cancelled"
        return
    fi
    
    log "Restoring from $backup_file..."
    
    # Restore database
    if [[ "$backup_file" == *"db_"* ]]; then
        if [[ "$backup_file" == *".gz" ]]; then
            gunzip -c "$backup_file" | docker compose exec -T postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}"
        else
            docker compose exec -T postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" < "$backup_file"
        fi
        success "Database restored"
    fi
    
    # Restore uploads
    if [[ "$backup_file" == *"uploads_"* ]]; then
        tar -xzf "$backup_file" -C "$SCRIPT_DIR"
        success "Uploads restored"
    fi
}

cmd_clean() {
    log "Cleaning up Docker resources..."
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    success "Cleanup completed"
}

cmd_reset() {
    warn "⚠⚠⚠ DANGER: This will DELETE ALL DATA! ⚠⚠⚠"
    echo "This action will:"
    echo "  - Stop all services"
    echo "  - Delete all containers"
    echo "  - Delete all volumes (including database)"
    echo "  - Delete all uploads"
    echo ""
    read -p "Type 'DELETE EVERYTHING' to confirm: " confirm
    
    if [ "$confirm" != "DELETE EVERYTHING" ]; then
        log "Reset cancelled"
        return
    fi
    
    log "Resetting BOLT..."
    cd "$SCRIPT_DIR"
    
    # Stop and remove everything
    docker compose down -v
    
    # Remove uploads
    rm -rf "${SCRIPT_DIR}/uploads/*"
    
    success "BOLT has been reset. Run './bolt.sh start' to start fresh."
}

# =============================================================================
# Database Operations
# =============================================================================

cmd_db() {
    local subcommand="$1"
    
    case "$subcommand" in
        backup)
            local backup_dir="${SCRIPT_DIR}/backups"
            local date_stamp=$(date +%Y%m%d_%H%M%S)
            mkdir -p "$backup_dir"
            
            log "Backing up database..."
            docker compose exec -T postgres pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" | gzip > "$backup_dir/db_$date_stamp.sql.gz"
            success "Database backup: backups/db_$date_stamp.sql.gz"
            ;;
            
        restore)
            local backup_file="$2"
            if [ -z "$backup_file" ]; then
                error "Please specify backup file"
                exit 1
            fi
            
            if [ ! -f "$backup_file" ]; then
                error "Backup file not found"
                exit 1
            fi
            
            warn "This will overwrite the current database!"
            read -p "Continue? (yes/no): " confirm
            
            if [ "$confirm" = "yes" ]; then
                log "Restoring database..."
                if [[ "$backup_file" == *".gz" ]]; then
                    gunzip -c "$backup_file" | docker compose exec -T postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}"
                else
                    docker compose exec -T postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" < "$backup_file"
                fi
                success "Database restored"
            fi
            ;;
            
        migrate)
            log "Running database migrations..."
            docker compose exec backend npm run db:migrate
            success "Migrations completed"
            ;;
            
        console|psql)
            log "Opening PostgreSQL console..."
            docker compose exec postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}"
            ;;
            
        *)
            info "Database commands:"
            echo "  ./bolt.sh db backup    - Backup database"
            echo "  ./bolt.sh db restore   - Restore database"
            echo "  ./bolt.sh db migrate   - Run migrations"
            echo "  ./bolt.sh db console   - Open psql console"
            ;;
    esac
}

# =============================================================================
# SSL Certificate Operations
# =============================================================================

cmd_cert() {
    local subcommand="$1"
    
    case "$subcommand" in
        renew)
            log "Renewing SSL certificate..."
            sudo certbot renew --force-renewal
            docker compose restart nginx
            success "Certificate renewed"
            ;;
            
        status)
            log "SSL Certificate Status"
            echo "─────────────────────────────────────────────────────────────────────"
            sudo certbot certificates 2>/dev/null || info "No certificates found"
            ;;
            
        *)
            info "SSL certificate commands:"
            echo "  ./bolt.sh cert renew   - Renew certificate"
            echo "  ./bolt.sh cert status  - Check certificate status"
            ;;
    esac
}

# =============================================================================
# Shell Access
# =============================================================================

cmd_shell() {
    local service="$1"
    
    if [ -z "$service" ]; then
        error "Please specify service: backend, frontend, or postgres"
        exit 1
    fi
    
    case "$service" in
        backend|api)
            docker compose exec backend /bin/sh
            ;;
        frontend|nginx)
            docker compose exec frontend /bin/sh
            ;;
        postgres|db|database)
            docker compose exec postgres /bin/bash
            ;;
        *)
            error "Unknown service: $service"
            echo "Available services: backend, frontend, postgres"
            exit 1
            ;;
    esac
}

# =============================================================================
# Main
# =============================================================================

main() {
    load_env
    
    case "$1" in
        start)
            cmd_start
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs "$2"
            ;;
        update)
            cmd_update
            ;;
        backup)
            cmd_backup
            ;;
        restore)
            cmd_restore "$2"
            ;;
        shell)
            cmd_shell "$2"
            ;;
        db)
            cmd_db "$2" "$3"
            ;;
        cert)
            cmd_cert "$2"
            ;;
        clean)
            cmd_clean
            ;;
        reset)
            cmd_reset
            ;;
        install)
            bash "${SCRIPT_DIR}/install.sh"
            ;;
        help|--help|-h)
            print_help
            ;;
        *)
            print_help
            exit 1
            ;;
    esac
}

main "$@"
