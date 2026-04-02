#!/bin/sh
set -e

echo "=== Frontend Container Starting ==="

# Set default values
export FRONTEND_PORT=${FRONTEND_PORT:-80}
export BACKEND_HOST=${BACKEND_HOST:-backend}
export BACKEND_PORT=${BACKEND_PORT:-3001}

echo "Frontend Port: $FRONTEND_PORT"
echo "Backend Host: $BACKEND_HOST"
echo "Backend Port: $BACKEND_PORT"

# Generate nginx configuration from template
echo "Generating nginx configuration..."
envsubst '$FRONTEND_PORT $BACKEND_HOST $BACKEND_PORT' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Verify configuration
echo "Testing nginx configuration..."
nginx -t

echo "=== Frontend Container Ready ==="

# Execute the main command
exec "$@"
