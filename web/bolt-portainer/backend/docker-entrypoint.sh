#!/bin/bash
set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           BOLT Backend - Container Entrypoint                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[ENTRYPOINT]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

# Configuration
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-bolt_db}
DB_USER=${DB_USER:-bolt_user}
DB_PASSWORD=${DB_PASSWORD:-bolt_password}
MAX_RETRIES=${DB_MAX_RETRIES:-30}
RETRY_DELAY=${DB_RETRY_DELAY:-2}

log "Configuration:"
log "  Database Host: $DB_HOST"
log "  Database Port: $DB_PORT"
log "  Database Name: $DB_NAME"
log "  Database User: $DB_USER"
echo ""

# Function to wait for database
wait_for_database() {
    log "Waiting for database to be ready..."
    
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
            success "Database is reachable"
            
            # Test actual connection
            if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
                success "Database connection successful"
                return 0
            fi
        fi
        
        retries=$((retries + 1))
        warn "Database not ready yet (attempt $retries/$MAX_RETRIES)..."
        sleep $RETRY_DELAY
    done
    
    error "Database is not available after $MAX_RETRIES attempts"
    return 1
}

# Function to run database migrations
run_migrations() {
    log "Running database migrations..."
    
    if [ -f "dist/config/migrate.js" ]; then
        node dist/config/migrate.js
        success "Migrations completed"
    elif [ -f "dist/migrate.js" ]; then
        node dist/migrate.js
        success "Migrations completed"
    else
        warn "Migration script not found, skipping..."
    fi
}

# Function to initialize database schema
init_database() {
    log "Checking database schema..."
    
    # Check if tables exist
    local table_count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
" 2>/dev/null | xargs)
    
    if [ "$table_count" = "0" ] || [ -z "$table_count" ]; then
        warn "No tables found, initializing schema..."
        
        # Run schema initialization
        if [ -f "dist/config/init-schema.js" ]; then
            node dist/config/init-schema.js
            success "Schema initialized"
        elif [ -f "src/config/init-schema.sql" ]; then
            PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f src/config/init-schema.sql
            success "Schema initialized from SQL"
        else
            warn "Schema initialization script not found"
        fi
        
        # Seed initial data
        if [ -f "dist/config/seed.js" ]; then
            log "Seeding initial data..."
            node dist/config/seed.js
            success "Data seeded"
        fi
    else
        success "Database schema already exists ($table_count tables)"
    fi
}

# Function to create default admin user
create_admin_user() {
    log "Checking for default admin user..."
    
    local admin_exists=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT COUNT(*) FROM users WHERE username = 'admin';
" 2>/dev/null | xargs)
    
    if [ "$admin_exists" = "0" ] || [ -z "$admin_exists" ]; then
        warn "Creating default admin user..."
        
        # Generate secure password if not set
        JWT_SECRET=${JWT_SECRET:-$(openssl rand -base64 32)}
        
        # Create admin user via SQL or API
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
            INSERT INTO users (id, first_name, username, password, role, auth_type, status, created_at, updated_at)
            VALUES (
                gen_random_uuid(),
                'Administrator',
                'admin',
                '\$2a\$10\$YourHashedPasswordHere',
                'admin',
                'admin',
                'active',
                NOW(),
                NOW()
            )
            ON CONFLICT (username) DO NOTHING;
" 2>/dev/null || warn "Could not create admin user via SQL, will be created by application"
        
        success "Default admin user configured"
        echo ""
        echo "╔══════════════════════════════════════════════════════════════╗"
        echo "║  Default Login Credentials:                                  ║"
        echo "║  Username: admin                                             ║"
        echo "║  Password: admin123                                          ║"
        echo "║  Please change the password after first login!               ║"
        echo "╚══════════════════════════════════════════════════════════════╝"
        echo ""
    else
        success "Admin user already exists"
    fi
}

# Main execution
main() {
    # Wait for database
    if ! wait_for_database; then
        error "Cannot connect to database, exiting..."
        exit 1
    fi
    
    echo ""
    log "Database is ready, proceeding with initialization..."
    echo ""
    
    # Run migrations
    run_migrations
    
    # Initialize schema
    init_database
    
    # Create admin user
    create_admin_user
    
    echo ""
    success "Initialization complete!"
    echo ""
    log "Starting application..."
    echo ""
    
    # Execute the main command
    exec "$@"
}

# Run main
main "$@"
