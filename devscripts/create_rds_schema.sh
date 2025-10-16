#!/bin/bash
#
# AWS RDS Database Schema Creation Script
# Created: October 14, 2025
# Description: Creates the complete database schema for the AI Lip-Sync Companion App
#
# Usage: ./create_rds_schema.sh [--force]
#   --force: Skip confirmation prompt and proceed with schema creation

# Enable verbose debugging
set -e
set -x
set -v

# Enable PS4 for detailed trace output
export PS4='+${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]:+${FUNCNAME[0]}():} '

# Text formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Global variables for metrics
START_TIME=$(date +%s)
SUCCESS_COUNT=0
SKIPPED_COUNT=0
WARNING_COUNT=0
FAILURE_COUNT=0

# Create a log directory and file
LOG_DIR="$(dirname "$0")/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/schema_creation_$(date +"%Y%m%d_%H%M%S").log"
EXECUTION_ID=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || date +"%Y%m%d_%H%M%S")

# Logger function with levels and file output
function log() {
  local level=$1
  local message=$2
  local color=$NC
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  local caller_info=$(caller 0)
  local line_num=$(echo "$caller_info" | awk '{print $1}')
  local calling_function=$(echo "$caller_info" | awk '{print $2}')
  
  case $level in
    INFO) color=$BLUE ;;
    SUCCESS) color=$GREEN; ((SUCCESS_COUNT++)) ;;
    WARNING) color=$YELLOW; ((WARNING_COUNT++)) ;;
    ERROR) color=$RED; ((FAILURE_COUNT++)) ;;
    SKIPPED) color=$CYAN; ((SKIPPED_COUNT++)) ;;
    DEBUG) color=$GRAY ;;
    *) color=$NC ;;
  esac
  
  # Output to console with color
  echo -e "${color}[${level}]${NC} ${message} (line:${line_num}, func:${calling_function})"
  
  # Output to log file without color codes
  echo "[$timestamp] [${level}] [EXEC:$EXECUTION_ID] [${line_num}:${calling_function}] ${message}" >> "$LOG_FILE"
  
  # For DEBUG and ERROR levels, add to stderr as well
  if [[ "$level" == "DEBUG" || "$level" == "ERROR" ]]; then
    echo "[$timestamp] [${level}] [L${line_num}:${calling_function}] ${message}" >&2
  fi
}

# Load database connection parameters from .env file
ENV_FILE="/workspaces/DashTests/.env"
if [ ! -f "$ENV_FILE" ]; then
  log "ERROR" "Environment file not found: $ENV_FILE"
  exit 1
fi

# Source the .env file to get environment variables
source "$ENV_FILE"

# Use database connection parameters from .env
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-lipsync}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

# If DATABASE_URL is defined, parse and use it (overrides individual params)
if [ ! -z "${DATABASE_URL:-}" ]; then
  log "INFO" "Found DATABASE_URL, extracting connection parameters..."
  # Extract components from DATABASE_URL (postgresql://user:password@host:port/dbname)
  if [[ "$DATABASE_URL" =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
    log "INFO" "Successfully parsed DATABASE_URL"
  else
    log "WARNING" "Could not parse DATABASE_URL, using individual parameters"
  fi
fi

# Command-line parameters
FORCE=false
REMOVE_LOCKS=false

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --force)
    FORCE=true
    shift
    ;;
    --remove-locks)
    REMOVE_LOCKS=true
    shift
    ;;
  esac
done

# Function to execute SQL with error handling
function execute_sql() {
  local sql="$1"
  local description="$2"
  local stop_on_error=${3:-false}
  
  echo "--- EXECUTE_SQL FUNCTION: $description ---"
  log "INFO" "Executing: ${description}..."
  echo "SQL to execute: ${sql:0:100}...(truncated)"
  
  echo "Running psql command with: DB_HOST=$DB_HOST, DB_PORT=$DB_PORT, DB_USER=$DB_USER, DB_NAME=$DB_NAME"
  if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql" >> "$LOG_FILE" 2>&1; then
    log "SUCCESS" "${description} completed"
    echo "--- SQL EXECUTION SUCCESSFUL ---"
    return 0
  else
    log "WARNING" "${description} failed, checking if it's safe to continue..."
    
    # Check error type - if it's because object already exists, we can continue
    local error_output
    error_output=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql" 2>&1)
    
    if echo "$error_output" | grep -q "already exists"; then
      log "SKIPPED" "Object already exists, continuing..."
      echo "$error_output" >> "$LOG_FILE"
      return 0
    else
      log "ERROR" "${description} failed with error:"
      echo "$error_output" | tee -a "$LOG_FILE"
      if [ "$stop_on_error" = true ]; then
        log "ERROR" "Critical error encountered, stopping execution"
        exit 1
      fi
      return 1
    fi
  fi
}

function execute_transaction() {
  local sql="$1"
  local description="$2"
  local stop_on_error=${3:-false}
  
  log "INFO" "Executing transaction: ${description}..."
  
  # Create a temporary SQL file with transaction controls
  local temp_sql_file=$(mktemp)
  echo "BEGIN;" > "$temp_sql_file"
  echo "$sql" >> "$temp_sql_file"
  echo "COMMIT;" >> "$temp_sql_file"
  
  if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$temp_sql_file" >> "$LOG_FILE" 2>&1; then
    log "SUCCESS" "${description} completed"
    rm -f "$temp_sql_file"
    return 0
  else
    log "ERROR" "${description} failed, transaction rolled back"
    log "DEBUG" "Error details:"
    
    # Retry with explicit output to capture error
    local error_output
    error_output=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "BEGIN; $sql ROLLBACK;" 2>&1)
    echo "$error_output" | tee -a "$LOG_FILE"
    
    rm -f "$temp_sql_file"
    if [ "$stop_on_error" = true ]; then
      log "ERROR" "Critical transaction error encountered, stopping execution"
      exit 1
    fi
    return 1
  fi
}

# Handle locks function
function handle_locks() {
  # Define lock file path
  LOCK_FILE="/tmp/create_rds_schema.lock"
  
  # If --remove-locks was specified, remove any existing lock files
  if [ "$REMOVE_LOCKS" = true ]; then
    if [ -e "$LOCK_FILE" ]; then
      log "INFO" "Removing lock file as requested with --remove-locks"
      rm -f "$LOCK_FILE"
      log "SUCCESS" "Lock file removed successfully"
    else
      log "INFO" "No lock file found to remove"
    fi
  fi
  
  # Check if lock file exists
  if [ -e "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
    log "DEBUG" "Found lock file with PID: $PID"
    
    # Try to detect if the process is still running
    if [[ "$PID" =~ ^[0-9]+$ ]] && ps -p "$PID" > /dev/null 2>&1; then
      log "ERROR" "Another instance of this script is already running (PID: $PID)"
      echo "Use --remove-locks to forcibly remove the lock if you're sure no other instance is running."
      exit 1
    else
      log "WARNING" "Found stale lock file from PID: $PID. Previous execution may have crashed."
      log "INFO" "Automatically removing stale lock file"
      rm -f "$LOCK_FILE"
      if [ ! -e "$LOCK_FILE" ]; then
        log "SUCCESS" "Stale lock file successfully removed"
      else
        log "ERROR" "Failed to remove stale lock file. Check permissions or use sudo."
        exit 1
      fi
    fi
  fi
  
  # Create new lock file
  echo $$ > "$LOCK_FILE"
  log "DEBUG" "Created new lock file with current PID: $$"
}

# Handle locks before proceeding
handle_locks

# Cleanup function to remove lock on exit
function cleanup() {
  echo "--- ENTERING CLEANUP FUNCTION ---"
  log "INFO" "Cleaning up and removing lock file"
  
  if [ -e "$LOCK_FILE" ]; then
    # Check if it's our lock file by comparing PIDs
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    if [ "$LOCK_PID" = "$$" ]; then
      rm -f "$LOCK_FILE"
      if [ ! -e "$LOCK_FILE" ]; then
        log "DEBUG" "Lock file successfully removed"
      else
        log "WARNING" "Failed to remove lock file: $LOCK_FILE"
      fi
    else
      log "WARNING" "Lock file PID ($LOCK_PID) does not match current PID ($$), not removing"
    fi
  else
    log "DEBUG" "No lock file found to remove"
  fi
  
  # Calculate execution time
  local end_time=$(date +%s)
  local duration=$((end_time - START_TIME))
  local minutes=$((duration / 60))
  local seconds=$((duration % 60))
  
  log "INFO" "Script execution completed in ${minutes}m ${seconds}s"
  echo "--- CLEANUP FUNCTION EXECUTED ---"
  log "INFO" "Summary: $SUCCESS_COUNT success, $SKIPPED_COUNT skipped, $WARNING_COUNT warnings, $FAILURE_COUNT failures"
  echo -e "${BLUE}[INFO]${NC} Full logs available at: $LOG_FILE"
}

# Main function
main() {
  echo "--- MAIN FUNCTION STARTED ---"
  echo "DEBUG: DB_HOST=$DB_HOST"
  echo "DEBUG: DB_PORT=$DB_PORT"
  echo "DEBUG: DB_NAME=$DB_NAME"
  echo "DEBUG: DB_USER=$DB_USER"
  
  # Check connection to database with more detailed information
  log "INFO" "Testing connection to database ($DB_HOST:$DB_PORT)..."
  
  log "DEBUG" "Running: PGPASSWORD=******* psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
  
  # Test connection with more detailed output
  echo "Testing connection with detailed output:"
  PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" || true
  
  # Run the actual check
  echo "Attempting to connect with: psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
  echo "Running direct psql test..."
  PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 'Connection test successful';"
  echo "Direct psql test completed with exit code $?"
  
  PG_VERSION_OUTPUT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" 2>&1)
  CONNECTION_RESULT=$?
  echo "Connection result code: $CONNECTION_RESULT"
  echo "Connection output: $PG_VERSION_OUTPUT"
  
  # Try running a very simple table creation test
  echo "Attempting to create a simple test table..."
  TEST_TABLE_RESULT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE TABLE IF NOT EXISTS connection_test (id SERIAL PRIMARY KEY, test_time TIMESTAMP DEFAULT NOW());" 2>&1)
  echo "Test table creation result: $? - $TEST_TABLE_RESULT"
  
  if [ $CONNECTION_RESULT -ne 0 ]; then
    log "ERROR" "Cannot connect to database. Please check your credentials and network connectivity."
    log "INFO" "Verify that:"
    echo "  1. The AWS RDS instance is running and publicly accessible"
    echo "  2. Security groups allow connections from this IP address"
    echo "  3. Database credentials are correct"
    echo "  4. The database '$DB_NAME' exists"
    log "DEBUG" "Connection error: $PG_VERSION_OUTPUT"
    log "DEBUG" "Connection exit code: $CONNECTION_RESULT"
    
    # Try ping to check network connectivity
    ping -c 1 $DB_HOST || echo "Cannot ping host - network connectivity issue or host blocking ICMP"
    
    exit 1
  fi
  log "SUCCESS" "Database connection successful - $(echo "$PG_VERSION_OUTPUT" | grep 'PostgreSQL' | sed 's/ on .*//g')"
  
  # Continue with schema creation
  
  # Confirm before proceeding
  if [ "$FORCE" = false ]; then
    echo -e "${YELLOW}[WARNING]${NC} This script will create the complete database schema for the AI Lip-Sync Companion App."
    echo -e "It will create tables, indexes, and other database objects in the '${BOLD}${DB_NAME}${NC}' database."
    echo -e "Existing objects with the same name will be skipped (this script is idempotent)."
    echo ""
    echo -e "Database: ${BOLD}${DB_NAME}${NC}"
    echo -e "Host: ${BOLD}${DB_HOST}${NC}"
    echo -e "User: ${BOLD}${DB_USER}${NC}"
    echo ""
    read -p "Do you want to proceed? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${RED}[ABORT]${NC} Schema creation cancelled"
      exit 1
    fi
  fi
  
  # Check if schema already exists by looking for our tracking table
  CHECKPOINT_TABLE="schema_checkpoints"
  log "INFO" "Checking for existing schema deployment..."
  echo "CHECKPOINT_TABLE=$CHECKPOINT_TABLE"
  
  echo "Checking if checkpoint table exists..."
  CHECKPOINT_EXISTS=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tc "SELECT to_regclass('$CHECKPOINT_TABLE');" 2>&1)
  CHECKPOINT_EXISTS_CODE=$?
  echo "Checkpoint exists query result: $CHECKPOINT_EXISTS (Exit code: $CHECKPOINT_EXISTS_CODE)"
  
  if [ "$CHECKPOINT_EXISTS" != "" ] && [ "$CHECKPOINT_EXISTS" != "NULL" ]; then
    log "INFO" "Found existing schema deployment. Checking version..."
    
    echo "Querying schema version..."
    SCHEMA_VERSION=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tc "SELECT MAX(version) FROM $CHECKPOINT_TABLE;" 2>&1)
    echo "Schema version query result: $SCHEMA_VERSION (Exit code: $?)"
    log "INFO" "Current schema version: $SCHEMA_VERSION"
    
    # Get the latest completed checkpoint
    echo "Querying latest checkpoint..."
    LATEST_CHECKPOINT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tc "SELECT checkpoint FROM $CHECKPOINT_TABLE WHERE status = 'COMPLETED' ORDER BY applied_at DESC LIMIT 1;" 2>&1)
    echo "Latest checkpoint query result: $LATEST_CHECKPOINT (Exit code: $?)"
    log "INFO" "Latest completed checkpoint: $LATEST_CHECKPOINT"
  else
    echo "No checkpoint table found, will create it"
  fi
  
  # Create checkpoint table if it doesn't exist
  execute_sql "CREATE TABLE IF NOT EXISTS $CHECKPOINT_TABLE (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    checkpoint VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_id VARCHAR(50) NOT NULL
  );" "Creating schema checkpoint tracking table" true
  
  # Record the start of schema creation
  SCHEMA_VERSION="1.0.0"
  execute_sql "INSERT INTO $CHECKPOINT_TABLE (version, checkpoint, status, execution_id) VALUES ('$SCHEMA_VERSION', 'schema_creation_start', 'IN_PROGRESS', '$EXECUTION_ID');" "Recording schema creation start" true
  
  log "INFO" "Starting schema creation (version $SCHEMA_VERSION, execution $EXECUTION_ID)..."
  
  function record_checkpoint() {
    local checkpoint="$1"
    local status="$2"
    
    echo "--- RECORD_CHECKPOINT: $checkpoint - $status ---"
    log "DEBUG" "Recording checkpoint: $checkpoint - $status"
    echo "EXECUTION_ID=$EXECUTION_ID, SCHEMA_VERSION=$SCHEMA_VERSION"
    echo "CHECKPOINT_TABLE=$CHECKPOINT_TABLE"
    
    local sql="INSERT INTO $CHECKPOINT_TABLE (version, checkpoint, status, execution_id) VALUES ('$SCHEMA_VERSION', '$checkpoint', '$status', '$EXECUTION_ID');"
    echo "SQL for checkpoint: $sql"
    
    execute_sql "$sql" "Recording checkpoint $checkpoint" false
    
    echo "--- RECORD_CHECKPOINT COMPLETED ---"
  }
  
  # Enable required extensions
  record_checkpoint "extensions" "IN_PROGRESS"
  execute_sql "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" "Enabling uuid-ossp extension"
  execute_sql "CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";" "Enabling pg_trgm extension"
  execute_sql "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";" "Enabling pgcrypto extension"
  execute_sql "CREATE EXTENSION IF NOT EXISTS \"fuzzystrmatch\";" "Enabling fuzzystrmatch extension" 
  execute_sql "CREATE EXTENSION IF NOT EXISTS \"btree_gin\";" "Enabling btree_gin extension"
  record_checkpoint "extensions" "COMPLETED"
  
  # Users table
  record_checkpoint "users_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}'::JSONB
  );" "Creating users table"
  record_checkpoint "users_table" "COMPLETED"
  
  # Organizations table
  record_checkpoint "organizations_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    plan_type VARCHAR(50) DEFAULT 'free',
    settings JSONB DEFAULT '{}'::JSONB,
    contact_email VARCHAR(255)
  );" "Creating organizations table"
  record_checkpoint "organizations_table" "COMPLETED"
  
  # Organization members
  record_checkpoint "org_members_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS org_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (organization_id, user_id)
  );" "Creating organization members table"
  record_checkpoint "org_members_table" "COMPLETED"
  
  # Create unique index on organizations
  record_checkpoint "organizations_indices" "IN_PROGRESS"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations USING gin (name gin_trgm_ops);" "Creating organizations name search index"
  record_checkpoint "organizations_indices" "COMPLETED"
  
  # API keys table
  record_checkpoint "api_keys_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    permissions JSONB DEFAULT '[]'::JSONB,
    is_active BOOLEAN DEFAULT true,
    CHECK (user_id IS NOT NULL OR organization_id IS NOT NULL)
  );" "Creating API keys table"
  record_checkpoint "api_keys_table" "COMPLETED"
  
  # Avatars table
  record_checkpoint "avatars_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS avatars (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    image_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    avatar_type VARCHAR(50) NOT NULL DEFAULT 'photo',
    metadata JSONB DEFAULT '{}'::JSONB,
    provider VARCHAR(50),
    provider_avatar_id VARCHAR(255),
    is_public BOOLEAN DEFAULT false
  );" "Creating avatars table"
  record_checkpoint "avatars_table" "COMPLETED"
  
  # Scripts table
  record_checkpoint "scripts_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS scripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tags TEXT[],
    is_template BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::JSONB
  );" "Creating scripts table"
  record_checkpoint "scripts_table" "COMPLETED"
  
  # Full-text search vector for scripts
  record_checkpoint "scripts_search" "IN_PROGRESS"
  execute_sql "ALTER TABLE scripts ADD COLUMN IF NOT EXISTS search_vector tsvector;" "Adding search vector to scripts"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_scripts_search ON scripts USING GIN(search_vector);" "Creating scripts search index"
  
  # Update trigger for scripts search
  execute_sql "CREATE OR REPLACE FUNCTION scripts_search_trigger() RETURNS trigger AS $$
  BEGIN
    NEW.search_vector :=
      setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
      setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
    RETURN NEW;
  END
  $$ LANGUAGE plpgsql;" "Creating scripts search trigger function"
  
  execute_sql "DROP TRIGGER IF EXISTS scripts_search_update ON scripts;" "Dropping old scripts search trigger"
  execute_sql "CREATE TRIGGER scripts_search_update BEFORE INSERT OR UPDATE ON scripts
    FOR EACH ROW EXECUTE FUNCTION scripts_search_trigger();" "Creating scripts search trigger"
  record_checkpoint "scripts_search" "COMPLETED"
  
  # Audio clips table
  record_checkpoint "audio_clips_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS audio_clips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    audio_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_seconds FLOAT,
    transcript TEXT,
    source VARCHAR(50) DEFAULT 'upload',
    metadata JSONB DEFAULT '{}'::JSONB
  );" "Creating audio clips table"
  record_checkpoint "audio_clips_table" "COMPLETED"
  
  # Voices table
  record_checkpoint "voices_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS voices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    provider VARCHAR(50) NOT NULL,
    provider_voice_id VARCHAR(255) NOT NULL,
    language VARCHAR(10) DEFAULT 'en-US',
    gender VARCHAR(20),
    is_cloned BOOLEAN DEFAULT false,
    reference_audio_url TEXT,
    settings JSONB DEFAULT '{}'::JSONB,
    is_public BOOLEAN DEFAULT false
  );" "Creating voices table"
  record_checkpoint "voices_table" "COMPLETED"
  
  # Jobs table
  record_checkpoint "jobs_table" "IN_PROGRESS"
  execute_sql "CREATE TYPE job_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed',
    'cancelled'
  );" "Creating job status enum type" false
  
  execute_sql "CREATE TYPE job_type AS ENUM (
    'lipsync',
    'tts',
    'avatar_generation',
    'image_generation',
    'video_enhancement',
    'video_editing'
  );" "Creating job type enum type" false
  
  execute_sql "CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    job_type job_type NOT NULL,
    status job_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    input_data JSONB NOT NULL,
    output_data JSONB,
    error_details TEXT,
    priority INTEGER DEFAULT 0,
    webhook_url TEXT,
    callback_url TEXT,
    metadata JSONB DEFAULT '{}'::JSONB
  );" "Creating jobs table"
  record_checkpoint "jobs_table" "COMPLETED"
  
  # Job results table for completed media
  record_checkpoint "job_results_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS job_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    media_url TEXT NOT NULL,
    media_type VARCHAR(50) NOT NULL,
    duration_seconds FLOAT,
    width INTEGER,
    height INTEGER,
    fps FLOAT,
    metadata JSONB DEFAULT '{}'::JSONB
  );" "Creating job results table"
  record_checkpoint "job_results_table" "COMPLETED"
  
  # Job logs table for detailed tracking
  record_checkpoint "job_logs_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS job_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    level VARCHAR(20) NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}'::JSONB
  );" "Creating job logs table"
  record_checkpoint "job_logs_table" "COMPLETED"
  
  # Create indices for job queries
  record_checkpoint "job_indices" "IN_PROGRESS"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);" "Creating jobs user index"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_jobs_organization_id ON jobs(organization_id);" "Creating jobs organization index"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);" "Creating jobs status index"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);" "Creating jobs creation time index"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_job_logs_job_id ON job_logs(job_id);" "Creating job logs index"
  record_checkpoint "job_indices" "COMPLETED"
  
  # Screenplays table
  record_checkpoint "screenplays_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS screenplays (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    pdf_url TEXT NOT NULL,
    text_content TEXT,
    page_count INTEGER,
    file_size_bytes BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );" "Creating screenplays table"
  record_checkpoint "screenplays_table" "COMPLETED"
  
  # Full-text search vector for screenplays
  record_checkpoint "screenplays_search" "IN_PROGRESS"
  execute_sql "ALTER TABLE screenplays ADD COLUMN IF NOT EXISTS search_vector tsvector;" "Adding search vector to screenplays"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_screenplays_search ON screenplays USING GIN(search_vector);" "Creating screenplays search index"
  
  # Update trigger for screenplays search
  execute_sql "CREATE OR REPLACE FUNCTION screenplays_search_trigger() RETURNS trigger AS $$
  BEGIN
    NEW.search_vector :=
      setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
      setweight(to_tsvector('english', COALESCE(NEW.text_content, '')), 'C');
    RETURN NEW;
  END
  $$ LANGUAGE plpgsql;" "Creating screenplays search trigger function"
  
  execute_sql "DROP TRIGGER IF EXISTS screenplays_search_update ON screenplays;" "Dropping old screenplays search trigger"
  execute_sql "CREATE TRIGGER screenplays_search_update BEFORE INSERT OR UPDATE ON screenplays
    FOR EACH ROW EXECUTE FUNCTION screenplays_search_trigger();" "Creating screenplays search trigger"
  record_checkpoint "screenplays_search" "COMPLETED"
  
  # Usage tracking and quotas
  record_checkpoint "usage_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS usage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    unit VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    details JSONB DEFAULT '{}'::JSONB
  );" "Creating usage records table"
  
  execute_sql "CREATE TABLE IF NOT EXISTS quotas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID UNIQUE REFERENCES organizations(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    limit_value INTEGER NOT NULL,
    period VARCHAR(20) NOT NULL DEFAULT 'month',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reset_day INTEGER DEFAULT 1
  );" "Creating quotas table"
  record_checkpoint "usage_table" "COMPLETED"
  
  # Add all necessary indices
  record_checkpoint "additional_indices" "IN_PROGRESS"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);" "Creating users email index"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_usage_records_organization_id ON usage_records(organization_id);" "Creating usage records org index"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_usage_records_timestamp ON usage_records(timestamp);" "Creating usage records timestamp index"
  execute_sql "CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);" "Creating API keys hash index"
  record_checkpoint "additional_indices" "COMPLETED"
  
  # Create schema version tracking table for future upgrades
  record_checkpoint "schema_version_table" "IN_PROGRESS"
  execute_sql "CREATE TABLE IF NOT EXISTS schema_version (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by VARCHAR(100),
    script_name VARCHAR(255)
  );" "Creating schema version table"
  
  # Insert initial schema version
  execute_sql "INSERT INTO schema_version (version, description, applied_by, script_name) 
    VALUES ('1.0.0', 'Initial schema creation', '$USER', 'create_rds_schema.sh');" "Recording schema version"
  record_checkpoint "schema_version_table" "COMPLETED"
  
  # Final checkpoint
  record_checkpoint "schema_creation_complete" "IN_PROGRESS"
  execute_sql "UPDATE $CHECKPOINT_TABLE SET status = 'COMPLETED' WHERE checkpoint = 'schema_creation_start' AND execution_id = '$EXECUTION_ID';" "Updating initial checkpoint status"
  record_checkpoint "schema_creation_complete" "COMPLETED"
  
  log "SUCCESS" "Database schema creation completed successfully"
  
  # Health check
  function schema_health_check() {
    log "INFO" "Performing schema health check..."
    
    local health_check_sql="
    SELECT 
      schemaname, 
      tablename, 
      pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) as size,
      pg_relation_size(schemaname || '.' || tablename) as size_bytes,
      (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = tables.schemaname AND tablename = tables.tablename) as index_count
    FROM pg_tables as tables
    WHERE 
      schemaname = 'public' AND 
      tablename NOT LIKE 'pg_%' AND
      tablename NOT LIKE 'sql_%'
    ORDER BY 
      table_name;
    "
    
    echo -e "\n${CYAN}Schema Health Check Results:${NC}"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$health_check_sql"
    
    log "INFO" "Health check complete"
  }
  
  # Run health check
  schema_health_check
  
  # For debugging purposes, provide commands for further verification
  echo -e "\n${YELLOW}Useful verification commands:${NC}"
  echo -e "# List all tables\nPGPASSWORD=\"$DB_PASSWORD\" psql -h \"$DB_HOST\" -p \"$DB_PORT\" -U \"$DB_USER\" -d \"$DB_NAME\" -c \"\\dt\""
  
  echo -e "\n# View schema version\nPGPASSWORD=\"$DB_PASSWORD\" psql -h \"$DB_HOST\" -p \"$DB_PORT\" -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT * FROM schema_version;\""
  
  echo "--- MAIN FUNCTION COMPLETED SUCCESSFULLY ---"
}

# Set trap for a specific signal to get more debug info
trap 'echo "ERROR TRAP: Script received error on line $LINENO"' ERR

# Call the main function with error handling
echo "About to call main function..."
if main; then
  echo "Main function returned successfully with exit code $?"
else
  echo "CRITICAL: Main function failed with exit code $?"
  # Print the call stack for debugging
  echo "Call stack at error:"
  local i=0
  while caller $i; do
    ((i++))
  done
fi

echo "Main function call completed, now setting cleanup trap"

# Set trap for cleanup
trap cleanup EXIT

echo "Script finished successfully"
exit 0
