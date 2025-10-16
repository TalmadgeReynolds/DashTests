#!/bin/bash
# Script to configure the local environment to use a local PostgreSQL instance
# instead of RDS when RDS is not accessible

# Check if we can connect to the RDS database
source .env

if [[ "$DATABASE_URL" =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
  DB_USER="${BASH_REMATCH[1]}"
  DB_PASSWORD="${BASH_REMATCH[2]}"
  DB_HOST="${BASH_REMATCH[3]}"
  DB_PORT="${BASH_REMATCH[4]}"
  DB_NAME="${BASH_REMATCH[5]}"
  echo "Successfully parsed DATABASE_URL"
fi

echo "Testing connection to RDS database..."
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
  echo "RDS connection successful! Using RDS database."
  exit 0
else
  echo "Could not connect to RDS database. Switching to local development configuration."
  
  # Back up the current .env file
  cp .env .env.rds.bak
  echo "Backed up original .env to .env.rds.bak"
  
  # Create a new .env file with local database settings
  cat > .env << EOF
# Database - Local PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=lipsync
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lipsync

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# Storage configuration
STORAGE_ENDPOINT=localhost:9000
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

  echo "Updated .env with local development configuration."
  echo "To restore the RDS configuration, run: cp .env.rds.bak .env"
  
  exit 0
fi