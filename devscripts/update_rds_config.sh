#!/bin/bash

# Backup current .env file
if [ -f .env ]; then
    cp .env .env.backup
    echo "Backed up original .env to .env.backup"
fi

# Get DB connection details from existing file or prompt user
if grep -q "DATABASE_URL" .env 2>/dev/null; then
    echo "Found existing DATABASE_URL in .env"
    # Extract info from existing DATABASE_URL
    source .env
    
    # Parse existing DATABASE_URL
    if [[ "$DATABASE_URL" =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASSWORD="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"
        echo "Successfully parsed DATABASE_URL"
    else
        echo "Failed to parse existing DATABASE_URL, please enter details:"
        read -p "Database User: " DB_USER
        read -sp "Database Password: " DB_PASSWORD; echo
        read -p "Database Host: " DB_HOST
        read -p "Database Port [5432]: " DB_PORT
        DB_PORT=${DB_PORT:-5432}
        read -p "Database Name: " DB_NAME
    fi
else
    echo "No DATABASE_URL found, please enter details:"
    read -p "Database User: " DB_USER
    read -sp "Database Password: " DB_PASSWORD; echo
    read -p "Database Host: " DB_HOST
    read -p "Database Port [5432]: " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    read -p "Database Name: " DB_NAME
fi

# Build the database connection string
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Update or create .env file
cat > .env << EOF
# Database - AWS RDS PostgreSQL
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=${DB_NAME}
POSTGRES_HOST=${DB_HOST}
POSTGRES_PORT=${DB_PORT}
DATABASE_URL=${DATABASE_URL}

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# Storage configuration
STORAGE_ENDPOINT=minio:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=lipsync
STORAGE_USE_SSL=false
STORAGE_PUBLIC_ENDPOINT=http://localhost:9000

# Mock settings for easy development
MOCK_PROVIDERS=true
VEO3_MOCK_MODE=true
ELEVENLABS_MOCK_MODE=true
HEYGEN_MOCK_MODE=true
POSTFX_MOCK_MODE=true

# Webhook secrets
WEBHOOK_SECRET_HEYGEN=test-webhook-secret
EOF

echo "Updated .env file with proper database configuration"
echo "To test connection, run: ./devscripts/test_db_connection.sh"