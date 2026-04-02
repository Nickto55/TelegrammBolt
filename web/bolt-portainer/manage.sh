#!/bin/bash

# =============================================================================
# BOLT - Management Script
# =============================================================================
# Unified control point for Docker Compose services
# Usage: ./manage.sh [command] [options]
# =============================================================================

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
ENV_FILE="$SCRIPT_DIR/.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m'

# Logging
log() { echo -e "${BLUE}[MANAGE]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${CYAN}[i]${NC} $1"; }

# =============================================================================
# Helper Functions
# =============================================================================

show_help() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║                    BOLT Management Script                        ║
╚══════════════════════════════════════════════════════════════════╝

Usage: ./manage.sh [COMMAND] [OPTIONS]

Commands:
    start [service]         Start all services or specific service
    stop [service]          Stop all services or specific service
    restart [service]       Restart all services or specific service
    status                  Show status of all services
    logs [service]          Show logs (all or specific service)
    ps                      List running containers
    up                      Alias for 'start'
    down                    Stop and remove containers
    build [service]         Build or rebuild services
    pull                    Pull latest images
    exec <service> <cmd>    Execute command in container
    shell <service>         Open interactive shell in container
    clean                   Remove stopped containers and unused images
    reset                   Stop and remove all data (DANGEROUS!)
    update                  Update to latest version
    backup                  Create backup of database and uploads
    restore <file>          Restore from backup file
    health                  Check health of all services
    env                     Show current environment configuration

Services:
    postgres, backend, frontend

Options for logs:
    -f, --follow            Follow log output
    -n, --tail N            Show last N lines

Examples:
    ./manage.sh start                    # Start all services
    ./manage.sh start backend            # Start only backend
    ./manage.sh stop                     # Stop all services
    ./manage.sh restart                  # Restart all services
    ./manage.sh status                   # Show service status
    ./manage.sh logs                     # Show all logs
    ./manage.sh logs backend -f          # Follow backend logs
    ./manage.sh logs postgres --tail 50  # Show last 50 lines
    ./manage.sh shell backend            # Open shell in backend
    ./manage.sh exec postgres psql -U bolt_user  # Run psql
    ./manage.sh backup                   # Create backup
    ./manage.sh health                   # Check health

EOF
}

# Check if .env exists
check_env() {
    if [ ! -f "$ENV_FILE" ]; then
        error "Environment file not found: $ENV_FILE"
        error "Please run ./install.sh first"
        exit 1
    fi
}

# Load environment variables
load_env() {
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs 2>/dev/null) || true
    fi
}

# Get compose command (docker compose or docker-compose)
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        error "Docker Compose not found"
        exit 1
    fi
}

COMPOSE_CMD=$(get_compose_cmd)

# Run docker-compose command
compose() {
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

# =============================================================================
# Command Implementations
# =============================================================================

cmd_start() {
    local service="$1"
    
    if [ -n "$service" ]; then
        log "Starting service: $service"
        compose up -d "$service"
        success "Service $service started"
    else
        log "Starting all services..."
        compose up -d
        success "All services started"
        
        echo ""
        info "Service URLs:"
        echo -e "  Frontend:    ${CYAN}http://localhost:${FRONTEND_PORT:-80}${NC}"
        echo -e "  Backend API: ${CYAN}http://localhost:${BACKEND_PORT:-3001}${NC}"
    fi
}

cmd_stop() {
    local service="$1"
    
    if [ -n "$service" ]; then
        log "Stopping service: $service"
        compose stop "$service"
        success "Service $service stopped"
    else
        log "Stopping all services..."
        compose stop
        success "All services stopped"
    fi
}

cmd_restart() {
    local service="$1"
    
    if [ -n "$service" ]; then
        log "Restarting service: $service"
        compose restart "$service"
        success "Service $service restarted"
    else
        log "Restarting all services..."
        compose restart
        success "All services restarted"
    fi
}

cmd_status() {
    echo ""
    info "Container Status"
    echo "─────────────────────────────────────────────────────────────────────"
    compose ps
    
    echo ""
    info "Health Status"
    echo "─────────────────────────────────────────────────────────────────────"
    
    local backend_url="http://localhost:${BACKEND_PORT:-3001}/health"
    local frontend_url="http://localhost:${FRONTEND_PORT:-80}"
    
    # Check Backend
    if curl -s "$backend_url" > /dev/null 2>&1; then
        local health=$(curl -s "$backend_url" 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        if [ "$health" = "ok" ]; then
            success "Backend API: $backend_url - OK"
        else
            warn "Backend API: $backend_url - Responding but unhealthy"
        fi
    else
        error "Backend API: $backend_url - Not responding"
    fi
    
    # Check Frontend
    if curl -s "$frontend_url" > /dev/null 2>&1; then
        success "Frontend: $frontend_url - OK"
    else
        error "Frontend: $frontend_url - Not responding"
    fi
    
    # Check Database
    if compose exec -T postgres pg_isready -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" > /dev/null 2>&1; then
        success "Database: Connected"
    else
        error "Database: Not responding"
    fi
}

cmd_logs() {
    local service=""
    local follow=false
    local tail=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--follow)
                follow=true
                shift
                ;;
            -n|--tail)
                tail="$2"
                shift 2
                ;;
            -*)
                error "Unknown option: $1"
                exit 1
                ;;
            *)
                service="$1"
                shift
                ;;
        esac
    done
    
    local args=""
    [ "$follow" = true ] && args="$args -f"
    [ -n "$tail" ] && args="$args --tail $tail"
    
    if [ -n "$service" ]; then
        log "Showing logs for: $service"
        compose logs $args "$service"
    else
        log "Showing logs for all services"
        compose logs $args
    fi
}

cmd_ps() {
    compose ps
}

cmd_down() {
    log "Stopping and removing containers..."
    compose down
    success "Containers removed"
}

cmd_build() {
    local service="$1"
    
    if [ -n "$service" ]; then
        log "Building service: $service"
        compose build --no-cache "$service"
    else
        log "Building all services..."
        compose build --no-cache
    fi
    success "Build completed"
}

cmd_pull() {
    log "Pulling latest images..."
    compose pull
    success "Images pulled"
}

cmd_exec() {
    local service="$1"
    shift
    
    if [ -z "$service" ]; then
        error "Service name required"
        exit 1
    fi
    
    if [ $# -eq 0 ]; then
        error "Command required"
        exit 1
    fi
    
    compose exec "$service" "$@"
}

cmd_shell() {
    local service="$1"
    
    if [ -z "$service" ]; then
        error "Service name required"
        echo "Available services: postgres, backend, frontend"
        exit 1
    fi
    
    local shell_cmd="/bin/sh"
    
    case "$service" in
        postgres|db)
            service="postgres"
            shell_cmd="/bin/bash"
            ;;
        backend|api)
            service="backend"
            ;;
        frontend|nginx)
            service="frontend"
            shell_cmd="/bin/sh"
            ;;
    esac
    
    log "Opening shell in $service..."
    compose exec "$service" "$shell_cmd"
}

cmd_clean() {
    log "Cleaning up Docker resources..."
    
    # Remove stopped containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful!)
    # docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    success "Cleanup completed"
}

cmd_reset() {
    echo ""
    warn "⚠⚠⚠  DANGER: This will DELETE ALL DATA!  ⚠⚠⚠"
    echo ""
    echo "This action will:"
    echo "  - Stop all services"
    echo "  - Remove all containers"
    echo "  - Remove all volumes (including database data!)"
    echo "  - Remove all uploaded files"
    echo ""
    echo "This CANNOT be undone!"
    echo ""
    
    read -p "Type 'DELETE EVERYTHING' to confirm: " confirm
    
    if [ "$confirm" != "DELETE EVERYTHING" ]; then
        log "Reset cancelled"
        exit 0
    fi
    
    log "Resetting BOLT..."
    compose down -v
    rm -rf "$SCRIPT_DIR/uploads/*"
    success "BOLT has been reset"
    log "Run './manage.sh start' to start fresh"
}

cmd_update() {
    log "Updating BOLT..."
    
    # Pull latest images
    compose pull
    
    # Rebuild local images
    compose build --no-cache
    
    # Restart services
    compose up -d
    
    success "Update completed"
}

cmd_backup() {
    local backup_dir="$SCRIPT_DIR/backups"
    local date_stamp=$(date +%Y%m%d_%H%M%S)
    
    mkdir -p "$backup_dir"
    
    log "Creating backup..."
    
    # Backup database
    log "Backing up database..."
    if compose exec -T postgres pg_dump -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" 2>/dev/null | gzip > "$backup_dir/db_$date_stamp.sql.gz"; then
        success "Database backup: backups/db_$date_stamp.sql.gz"
    else
        error "Database backup failed"
    fi
    
    # Backup uploads
    if [ -d "$SCRIPT_DIR/uploads" ] && [ "$(ls -A $SCRIPT_DIR/uploads 2>/dev/null)" ]; then
        log "Backing up uploads..."
        tar -czf "$backup_dir/uploads_$date_stamp.tar.gz" -C "$SCRIPT_DIR" uploads 2>/dev/null
        success "Uploads backup: backups/uploads_$date_stamp.tar.gz"
    fi
    
    # Backup configuration
    log "Backing up configuration..."
    tar -czf "$backup_dir/config_$date_stamp.tar.gz" -C "$SCRIPT_DIR" .env docker-compose.yml nginx 2>/dev/null
    success "Config backup: backups/config_$date_stamp.tar.gz"
    
    # Cleanup old backups (keep 30 days)
    find "$backup_dir" -name "*.gz" -mtime +30 -delete 2>/dev/null || true
    
    echo ""
    success "Backup completed in $backup_dir"
}

cmd_restore() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        # List available backups
        info "Available backups:"
        ls -lh "$SCRIPT_DIR/backups/" 2>/dev/null || error "No backups found"
        echo ""
        info "Usage: ./manage.sh restore <backup_file>"
        exit 0
    fi
    
    if [ ! -f "$backup_file" ]; then
        # Try to find in backups directory
        if [ -f "$SCRIPT_DIR/backups/$backup_file" ]; then
            backup_file="$SCRIPT_DIR/backups/$backup_file"
        else
            error "Backup file not found: $backup_file"
            exit 1
        fi
    fi
    
    warn "This will overwrite existing data!"
    read -p "Continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log "Restore cancelled"
        exit 0
    fi
    
    log "Restoring from: $backup_file"
    
    # Restore database
    if [[ "$backup_file" == *"db_"* ]]; then
        log "Restoring database..."
        if [[ "$backup_file" == *".gz" ]]; then
            gunzip -c "$backup_file" | compose exec -T postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}"
        else
            compose exec -T postgres psql -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" < "$backup_file"
        fi
        success "Database restored"
    fi
    
    # Restore uploads
    if [[ "$backup_file" == *"uploads_"* ]]; then
        log "Restoring uploads..."
        tar -xzf "$backup_file" -C "$SCRIPT_DIR"
        success "Uploads restored"
    fi
    
    # Restart services
    log "Restarting services..."
    compose restart
}

cmd_health() {
    echo ""
    info "Health Check"
    echo "─────────────────────────────────────────────────────────────────────"
    
    local backend_url="http://localhost:${BACKEND_PORT:-3001}/health"
    
    # Check Backend
    local response=$(curl -s "$backend_url" 2>/dev/null)
    if [ -n "$response" ]; then
        success "Backend API: Healthy"
        echo "Response: $response"
    else
        error "Backend API: Unhealthy"
    fi
    
    # Check Database
    if compose exec -T postgres pg_isready -U "${DB_USER:-bolt_user}" -d "${DB_NAME:-bolt_db}" > /dev/null 2>&1; then
        success "Database: Healthy"
    else
        error "Database: Unhealthy"
    fi
    
    # Container status
    echo ""
    info "Container Health Status"
    echo "─────────────────────────────────────────────────────────────────────"
    compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"
}

cmd_env() {
    echo ""
    info "Environment Configuration"
    echo "─────────────────────────────────────────────────────────────────────"
    
    if [ -f "$ENV_FILE" ]; then
        cat "$ENV_FILE" | grep -v '^#' | grep -v '^$'
    else
        error ".env file not found"
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    # Check if help is requested
    if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi
    
    # Load environment
    load_env
    
    # Parse command
    local command="$1"
    shift
    
    case "$command" in
        start|up)
            check_env
            cmd_start "$@"
            ;;
        stop)
            check_env
            cmd_stop "$@"
            ;;
        restart)
            check_env
            cmd_restart "$@"
            ;;
        status)
            check_env
            cmd_status
            ;;
        logs)
            check_env
            cmd_logs "$@"
            ;;
        ps)
            check_env
            cmd_ps
            ;;
        down)
            check_env
            cmd_down
            ;;
        build)
            check_env
            cmd_build "$@"
            ;;
        pull)
            check_env
            cmd_pull
            ;;
        exec)
            check_env
            cmd_exec "$@"
            ;;
        shell)
            check_env
            cmd_shell "$@"
            ;;
        clean)
            cmd_clean
            ;;
        reset)
            check_env
            cmd_reset
            ;;
        update)
            check_env
            cmd_update
            ;;
        backup)
            check_env
            cmd_backup
            ;;
        restore)
            check_env
            cmd_restore "$@"
            ;;
        health)
            check_env
            cmd_health
            ;;
        env)
            cmd_env
            ;;
        *)
            error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Handle script interruption
trap '' INT

# Run main
main "$@"
