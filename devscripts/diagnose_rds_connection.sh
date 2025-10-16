#!/bin/bash
#
# AWS RDS Connection Diagnostic Script
# Created: October 16, 2025
# Description: A diagnostic script to test AWS RDS connectivity with detailed logging and graceful fallback
#
# Usage: ./diagnose_rds_connection.sh [--local-fallback]
#   --local-fallback: Automatically switch to local DB if RDS connection fails

# Enable error handling
set -o pipefail

# Color definitions
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
PURPLE="\033[0;35m"
CYAN="\033[0;36m"
NC="\033[0m" # No Color
BOLD="\033[1m"

# Create log directory
LOG_DIR="$(dirname "$0")/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/rds_diagnostic_$(date +%Y%m%d_%H%M%S).log"

# Track success/failure metrics
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
START_TIME=$(date +%s)

# Initialize with default settings (will be overridden by .env if it exists)
DB_HOST="lipsync.c9qesoeo0b50.us-east-1.rds.amazonaws.com"
DB_PORT="5432"
DB_USER="lipsync"
DB_PASSWORD="PYQUw4VwDi36Jz9"
DB_NAME="postgres"
DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

# Check for local fallback flag
LOCAL_FALLBACK=0
if [[ "$1" == "--local-fallback" ]]; then
    LOCAL_FALLBACK=1
fi

# Function for logging with timestamps
log() {
    local level=$1
    local message=$2
    local color=$NC
    
    case $level in
        "INFO") color=$BLUE ;;
        "SUCCESS") color=$GREEN ;;
        "WARNING") color=$YELLOW ;;
        "ERROR") color=$RED ;;
        "CRITICAL") color=$RED$BOLD ;;
    esac
    
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo -e "${color}[$level]${NC} $timestamp - $message"
    echo "[$level] $timestamp - $message" >> "$LOG_FILE"
}

# Function to run a diagnostic check
run_check() {
    local name=$1
    local command=$2
    local success_msg=$3
    local failure_msg=$4
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    log "INFO" "Running check: $name"
    echo "$ $command" >> "$LOG_FILE"
    
    # Run command and capture output and exit status
    local output
    local status
    
    output=$(eval "$command" 2>&1)
    status=$?
    
    # Log full command output to file regardless of result
    echo "$output" >> "$LOG_FILE"
    echo "Exit status: $status" >> "$LOG_FILE"
    
    # Check result
    if [ $status -eq 0 ]; then
        log "SUCCESS" "$success_msg"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        # Print abbreviated output to console
        if [ -n "$output" ]; then
            echo -e "${GREEN}Output:${NC} ${output:0:100}${NC}$([ ${#output} -gt 100 ] && echo "...")"
        fi
        return 0
    else
        log "ERROR" "$failure_msg"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        # Print abbreviated error to console
        if [ -n "$output" ]; then
            echo -e "${RED}Error:${NC} ${output:0:200}${NC}$([ ${#output} -gt 200 ] && echo "...")"
        fi
        return 1
    fi
}

# Function to generate a summary report
generate_report() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    echo
    echo -e "${BOLD}════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}            RDS Connection Diagnostic Report        ${NC}"
    echo -e "${BOLD}════════════════════════════════════════════════════${NC}"
    echo 
    echo -e "Run time: $duration seconds"
    echo -e "Total checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
    echo
    echo -e "Host: $DB_HOST"
    echo -e "Port: $DB_PORT"
    echo -e "User: $DB_USER"
    echo -e "Database: $DB_NAME"
    echo
    echo -e "External IP: $(curl -s http://checkip.amazonaws.com)"
    echo -e "Full log: $LOG_FILE"
    echo -e "${BOLD}════════════════════════════════════════════════════${NC}"
}

# Function to switch to local database configuration
switch_to_local() {
    log "WARNING" "Switching to local database configuration"
    
    # Backup current .env
    if [ -f .env ]; then
        cp .env .env.rds.bak
        log "INFO" "Backed up current .env to .env.rds.bak"
    fi
    
    # Generate local .env file
    cat > .env << EOL
# Database - Local PostgreSQL (Auto-generated after RDS connection failure)
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
EOL

    log "SUCCESS" "Created local .env configuration"
    log "INFO" "To restore RDS settings, run: cp .env.rds.bak .env"
}

# Main script execution
log "INFO" "Starting RDS connection diagnostic"
log "INFO" "Log file: $LOG_FILE"

# Load environment variables if .env exists
if [ -f .env ]; then
    log "INFO" "Loading environment variables from .env"
    source .env
    
    # Extract variables from DATABASE_URL if present
    if [[ -n "$DATABASE_URL" ]]; then
        if [[ "$DATABASE_URL" =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
            DB_USER="${BASH_REMATCH[1]}"
            DB_PASSWORD="${BASH_REMATCH[2]}"
            DB_HOST="${BASH_REMATCH[3]}"
            DB_PORT="${BASH_REMATCH[4]}"
            DB_NAME="${BASH_REMATCH[5]}"
            log "INFO" "Extracted database details from DATABASE_URL"
        else
            log "WARNING" "Could not parse DATABASE_URL: $DATABASE_URL"
        fi
    else
        # Try to build from individual variables
        log "INFO" "Building connection string from individual variables"
        if [[ -n "$POSTGRES_USER" && -n "$POSTGRES_HOST" ]]; then
            DB_USER="${POSTGRES_USER}"
            DB_PASSWORD="${POSTGRES_PASSWORD}"
            DB_HOST="${POSTGRES_HOST}"
            DB_PORT="${POSTGRES_PORT:-5432}"
            DB_NAME="${POSTGRES_DB}"
            DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
        fi
    fi
else
    log "WARNING" "No .env file found, using default values"
fi

# Check #1: Confirm RDS hostname resolves via DNS
run_check "DNS resolution" \
    "getent hosts $DB_HOST || host $DB_HOST 2>/dev/null || nslookup $DB_HOST 2>/dev/null || dig +short $DB_HOST 2>/dev/null" \
    "RDS hostname DNS resolution successful" \
    "Failed to resolve RDS hostname"

# Check #2: Test TCP connection to RDS endpoint
run_check "TCP connection" \
    "timeout 5 bash -c '</dev/tcp/$DB_HOST/$DB_PORT' 2>/dev/null" \
    "TCP connection to RDS ($DB_HOST:$DB_PORT) successful" \
    "Failed to establish TCP connection to RDS ($DB_HOST:$DB_PORT)"

# Check #3: Check if psql client is available
run_check "PSQL availability" \
    "command -v psql" \
    "PostgreSQL client is installed" \
    "PostgreSQL client (psql) is not installed"

# Check #4: Test basic psql connection
run_check "PSQL connection" \
    "PGPASSWORD='$DB_PASSWORD' psql -h '$DB_HOST' -p '$DB_PORT' -U '$DB_USER' -d '$DB_NAME' -c 'SELECT 1;' -t" \
    "PostgreSQL connection successful" \
    "PostgreSQL connection failed"

# Check #5: Test server version and basic info
if run_check "Database version" \
    "PGPASSWORD='$DB_PASSWORD' psql -h '$DB_HOST' -p '$DB_PORT' -U '$DB_USER' -d '$DB_NAME' -c 'SELECT version();' -t" \
    "Retrieved PostgreSQL server version" \
    "Failed to retrieve PostgreSQL server version"; then
    
    # Additional checks only if basic connection works
    
    # Check #6: Test user permissions
    run_check "User permissions" \
        "PGPASSWORD='$DB_PASSWORD' psql -h '$DB_HOST' -p '$DB_PORT' -U '$DB_USER' -d '$DB_NAME' -c \"SELECT has_table_privilege('$DB_USER', 'screenplays', 'SELECT');\" -t" \
        "User has required permissions" \
        "User may not have required permissions"
    
    # Check #7: Check if screenplays table exists
    run_check "Screenplays table" \
        "PGPASSWORD='$DB_PASSWORD' psql -h '$DB_HOST' -p '$DB_PORT' -U '$DB_USER' -d '$DB_NAME' -c \"SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'screenplays');\" -t" \
        "Screenplays table exists" \
        "Screenplays table does not exist"
fi

# Generate report with summary information
generate_report

# Determine if we should fallback to local database
if [ $FAILED_CHECKS -gt 0 ] && [ $LOCAL_FALLBACK -eq 1 ]; then
    log "WARNING" "Connection issues detected, switching to local database"
    switch_to_local
    log "INFO" "Please restart your application to use the local database"
fi

# Final status message
if [ $FAILED_CHECKS -eq 0 ]; then
    log "SUCCESS" "All checks passed! RDS connection is working properly"
    exit 0
else
    log "ERROR" "$FAILED_CHECKS out of $TOTAL_CHECKS checks failed"
    
    # Provide recommendation based on failures
    if [ $LOCAL_FALLBACK -eq 0 ]; then
        log "INFO" "Run this script with --local-fallback to automatically switch to local database"
        log "INFO" "Verify your security groups allow access from IP: $(curl -s http://checkip.amazonaws.com)"
    fi
    
    exit 1
fi