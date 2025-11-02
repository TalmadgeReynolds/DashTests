#!/bin/bash
###############################################################################
# DashTests AI Lip-Sync Application Runner
# 
# Comprehensive script to run the full-stack application:
# - Backend API (FastAPI)
# - Background Worker (Redis queues)
# - Frontend UI (React + Vite)
# - Database (PostgreSQL)
# - Redis Cache
#
# Usage:
#   ./run.sh              # Run full stack (default)
#   ./run.sh full         # Run full stack (backend + frontend + worker)
#   ./run.sh api          # Run API server only
#   ./run.sh worker       # Run background worker only
#   ./run.sh frontend     # Run frontend dev server only
#   ./run.sh backend      # Run API + worker (no frontend)
#   ./run.sh test [path]  # Run tests
#   ./run.sh setup        # Setup only (install deps, migrate DB)
#
###############################################################################

# Exit on error
set -e

# Determine script directory for reliable path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

###############################################################################
# Color output functions
###############################################################################

function echo_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

function echo_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

function echo_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

function echo_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

function echo_section() {
    echo ""
    echo -e "\033[1;36m═══════════════════════════════════════════════════\033[0m"
    echo -e "\033[1;36m  $1\033[0m"
    echo -e "\033[1;36m═══════════════════════════════════════════════════\033[0m"
    echo ""
}

###############################################################################
# Environment setup
###############################################################################

function setup_env() {
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        echo_warning "No .env file found. Creating one with development defaults..."
        cat > .env << 'EOF'
# Database configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=lipsync
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Storage configuration
S3_BUCKET_NAME=lipsync-storage
AWS_ACCESS_KEY_ID=mockaccess
AWS_SECRET_ACCESS_KEY=mocksecret
AWS_REGION=us-west-2
MOCK_STORAGE=true

# API provider keys (mock mode for easy development)
HEYGEN_API_KEY=mockkey
VEO_API_KEY=mockkey
ELEVENLABS_API_KEY=mockkey
OPENAI_API_KEY=mockkey
ANTHROPIC_API_KEY=mockkey

# Webhook secrets
WEBHOOK_SECRET_HEYGEN=mocksecret

# Application settings
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Mock settings (enabled by default for easy development)
MOCK_PROVIDERS=true
HEYGEN_MOCK_MODE=true
VEO_MOCK_MODE=true
ELEVENLABS_MOCK_MODE=true
EOF
        echo_success "Created .env file with development defaults"
        echo_info "Edit .env file to use real API keys and services"
    fi
    
    # Load environment variables
echo_info "Loading environment variables..."
export $(grep -v '^#' .env 2>/dev/null | xargs) || true
# Explicitly set API keys if they're not set
if [ -z "$OPENAI_API_KEY" ]; then
  export OPENAI_API_KEY=$(grep "^OPENAI_API_KEY=" .env | cut -d= -f2-)
  echo_info "Set OpenAI API key from .env file"
fi
if [ -z "$ANTHROPIC_API_KEY" ]; then
  export ANTHROPIC_API_KEY=$(grep "^ANTHROPIC_API_KEY=" .env | cut -d= -f2-)
  echo_info "Set Anthropic API key from .env file"
fi
echo_success "Environment loaded"
}

###############################################################################
# Security Group Auto-Update
###############################################################################

function update_security_group() {
    echo_info "Attempting to update AWS security group with current IP..."
    
    # Get security group ID from environment
    if [ -z "$RDS_SECURITY_GROUP_ID" ]; then
        echo_error "RDS_SECURITY_GROUP_ID not found in .env file"
        return 1
    fi
    
    # Get current public IP
    CURRENT_IP=$(curl -s http://checkip.amazonaws.com)
    if [ -z "$CURRENT_IP" ]; then
        echo_error "Could not determine your public IP address"
        return 1
    fi
    
    echo_info "Your current IP: $CURRENT_IP"
    echo_info "Security Group: $RDS_SECURITY_GROUP_ID"
    
    # Use us-east-1 region (where RDS is located)
    AWS_REGION_SG="us-east-1"
    
    # Add rule for PostgreSQL access from current IP
    if aws ec2 authorize-security-group-ingress \
        --group-id "$RDS_SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 5432 \
        --cidr "$CURRENT_IP/32" \
        --region "$AWS_REGION_SG" 2>/dev/null; then
        echo_success "Successfully added your IP ($CURRENT_IP) to security group"
        return 0
    else
        # Check if rule already exists (this is actually a success case)
        if aws ec2 describe-security-groups \
            --group-ids "$RDS_SECURITY_GROUP_ID" \
            --region "$AWS_REGION_SG" 2>/dev/null | grep -q "$CURRENT_IP/32"; then
            echo_success "Your IP ($CURRENT_IP) is already authorized in security group"
            return 0
        else
            echo_error "Failed to update security group"
            return 1
        fi
    fi
}

###############################################################################
# Database setup
###############################################################################

function setup_database() {
    echo_info "Checking database availability..."
    
    DB_AVAILABLE=false
    
    # Check if DATABASE_URL contains RDS or other remote DB endpoints
    if [[ "$DATABASE_URL" =~ .*\.rds\. ]] || [[ "$DATABASE_URL" =~ .*\.amazonaws\.com ]] || [[ "$POSTGRES_HOST" =~ .*\.rds\. ]] || [[ "$POSTGRES_HOST" =~ .*\.amazonaws\.com ]]; then
        echo_info "AWS RDS database detected"
        
        # Try connecting to the RDS database with retry logic and auto-update security group
        if command -v pg_isready > /dev/null; then
            MAX_RETRIES=3
            RETRY_COUNT=0
            SG_UPDATED=false
            
            while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                if pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} > /dev/null 2>&1; then
                    echo_success "Connected to AWS RDS database successfully"
                    DB_AVAILABLE=true
                    return 0
                else
                    RETRY_COUNT=$((RETRY_COUNT + 1))
                    echo_warning "Connection attempt $RETRY_COUNT of $MAX_RETRIES failed"
                    
                    # On first failure, try updating security group
                    if [ $RETRY_COUNT -eq 1 ] && [ "$SG_UPDATED" = false ]; then
                        echo_info "Attempting to update security group automatically..."
                        if update_security_group; then
                            SG_UPDATED=true
                            echo_info "Waiting 5 seconds for security group rules to propagate..."
                            sleep 5
                        else
                            echo_error "Failed to update security group. Cannot connect to RDS."
                            echo_error "Please check:"
                            echo_error "  1. AWS CLI is configured with valid credentials"
                            echo_error "  2. Your IAM user has ec2:AuthorizeSecurityGroupIngress permission"
                            echo_error "  3. RDS_SECURITY_GROUP_ID in .env is correct: $RDS_SECURITY_GROUP_ID"
                            exit 1
                        fi
                    elif [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                        echo_info "Waiting 3 seconds before retry..."
                        sleep 3
                    fi
                fi
            done
            
            # If we get here, all retries failed
            echo_error "Failed to connect to AWS RDS database after $MAX_RETRIES attempts"
            echo_error "Security group was updated but connection still failed. Please check:"
            echo_error "  1. Database credentials in .env are correct"
            echo_error "  2. RDS instance is running and accessible"
            echo_error "  3. Network connectivity to AWS"
            exit 1
        fi
    fi
    
    # Check if PostgreSQL is already running locally
    if command -v pg_isready > /dev/null; then
        if pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} > /dev/null 2>&1; then
            echo_success "PostgreSQL is already running"
            DB_AVAILABLE=true
            return 0
        fi
    fi
    
    # Try to start with docker-compose if available
    if [ "$DB_AVAILABLE" = false ] && command -v docker-compose > /dev/null; then
        echo_info "Starting PostgreSQL and Redis with docker-compose..."
        docker-compose up -d postgres redis 2>/dev/null || true
        
        # Wait for database to be ready (max 30 seconds)
        echo_info "Waiting for PostgreSQL to be ready..."
        for i in {1..30}; do
            if pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} > /dev/null 2>&1; then
                echo_success "PostgreSQL is ready"
                DB_AVAILABLE=true
                break
            fi
            echo -n "."
            sleep 1
        done
        echo ""
    fi
    
    # Fallback to standalone Docker if docker-compose failed
    if [ "$DB_AVAILABLE" = false ] && command -v docker > /dev/null; then
        echo_info "Starting PostgreSQL with Docker (standalone)..."
        docker run --rm -d --name lipsync-postgres \
            -e POSTGRES_USER=${POSTGRES_USER:-postgres} \
            -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
            -e POSTGRES_DB=${POSTGRES_DB:-lipsync} \
            -p ${POSTGRES_PORT:-5432}:5432 \
            postgres:15 2>/dev/null || echo_warning "Could not start PostgreSQL container"
        
        # Wait for database
        echo_info "Waiting for PostgreSQL to be ready..."
        for i in {1..30}; do
            if pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} > /dev/null 2>&1; then
                echo_success "PostgreSQL is ready"
                DB_AVAILABLE=true
                break
            fi
            echo -n "."
            sleep 1
        done
        echo ""
    fi
    
    if [ "$DB_AVAILABLE" = false ]; then
        echo_warning "Could not connect to PostgreSQL!"
        echo_warning "Database features will not work. Start PostgreSQL manually to enable."
        echo_info "Continuing without database..."
        return 0
    fi
}

###############################################################################
# Redis setup
###############################################################################

function setup_redis() {
    echo_info "Checking Redis availability..."
    
    REDIS_AVAILABLE=false
    
    # Check if Redis is already running
    if command -v redis-cli > /dev/null; then
        if redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ping > /dev/null 2>&1; then
            echo_success "Redis is already running"
            REDIS_AVAILABLE=true
            return 0
        fi
    fi
    
    # Try to start with docker-compose if available
    if [ "$REDIS_AVAILABLE" = false ] && command -v docker-compose > /dev/null; then
        echo_info "Starting Redis with docker-compose..."
        docker-compose up -d redis 2>/dev/null || true
        
        # Wait for Redis
        sleep 2
        if command -v redis-cli > /dev/null && redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ping > /dev/null 2>&1; then
            echo_success "Redis is ready"
            REDIS_AVAILABLE=true
            return 0
        fi
    fi
    
    # Fallback to standalone Docker
    if [ "$REDIS_AVAILABLE" = false ] && command -v docker > /dev/null; then
        echo_info "Starting Redis with Docker (standalone)..."
        docker run --rm -d --name lipsync-redis \
            -p ${REDIS_PORT:-6379}:6379 \
            redis:7 2>/dev/null || echo_warning "Could not start Redis container"
        
        sleep 2
        if command -v redis-cli > /dev/null && redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ping > /dev/null 2>&1; then
            echo_success "Redis is ready"
            REDIS_AVAILABLE=true
            return 0
        fi
    fi
    
    if [ "$REDIS_AVAILABLE" = false ]; then
        echo_warning "Could not connect to Redis. Worker functionality may be limited."
    fi
}

###############################################################################
# Python backend setup
###############################################################################

function setup_python_backend() {
    echo_info "Setting up Python backend environment..."
    
    # Check which Python we're using
    if [ -n "$VIRTUAL_ENV" ]; then
        echo_info "Using existing virtual environment: $VIRTUAL_ENV"
    else
        echo_info "Using system Python: $(which python3 || which python)"
    fi
    
    # Install/update Python dependencies
    echo_info "Installing Python dependencies..."
    if pip install --quiet --upgrade pip > /dev/null 2>&1 && pip install --quiet -r requirements.txt 2>&1; then
        echo_success "Python dependencies installed"
    else
        echo_warning "Some Python dependencies may not have installed correctly"
        echo_info "Continuing anyway..."
    fi
    
    # Check for required system tools
    if ! command -v ffmpeg &> /dev/null; then
        echo_warning "ffmpeg is not installed. Video post-processing will not work."
        echo_info "Install ffmpeg: sudo apt-get install ffmpeg (Linux) or brew install ffmpeg (Mac)"
    fi
}

function init_database() {
    echo_info "Initializing database schema..."
    
    # Check if we're using an RDS database
    if [[ "$DATABASE_URL" =~ .*\.rds\. ]] || [[ "$DATABASE_URL" =~ .*\.amazonaws\.com ]] || [[ "$POSTGRES_HOST" =~ .*\.rds\. ]] || [[ "$POSTGRES_HOST" =~ .*\.amazonaws\.com ]]; then
        echo_info "Using AWS RDS database - checking alembic setup"
        
        # Run the setup_alembic.py script to configure alembic for RDS
        if python setup_alembic.py; then
            echo_success "AWS RDS alembic setup complete"
        else
            echo_warning "AWS RDS alembic setup failed"
            return 1
        fi
    else
        # Regular database initialization for local DB
        if python -c "from backend.db import init_db; init_db()" 2>/dev/null; then
            echo_success "Database schema initialized"
        else
            echo_warning "Database init skipped (database not available)"
            return 0
        fi
        
        echo_info "Running database migrations..."
        if alembic upgrade head 2>/dev/null; then
            echo_success "Database migrations complete"
        else
            echo_warning "Database migrations skipped (database not available)"
        fi
    fi
}

###############################################################################
# Frontend setup
###############################################################################

function setup_frontend() {
    echo_info "Setting up React frontend..."
    
    if [ ! -d "frontend" ]; then
        echo_warning "Frontend directory not found. Skipping frontend setup."
        return 1
    fi
    
    cd frontend
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        echo_warning "Node.js is not installed. Frontend will not be available."
        echo_info "Install Node.js 18+ to enable the frontend."
        cd ..
        return 1
    fi
    
    # Check if dependencies need to be installed
    if [ ! -d "node_modules" ]; then
        echo_info "Installing frontend dependencies..."
        npm install
        echo_success "Frontend dependencies installed"
    else
        echo_info "Frontend dependencies already installed"
    fi
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        echo_info "Creating frontend .env file..."
        cat > .env << 'EOF'
# API Configuration
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=http://localhost:8000
EOF
        echo_success "Frontend .env created"
    fi
    
    cd ..
    echo_success "Frontend ready"
}

###############################################################################
# Service control functions
###############################################################################

# Global PIDs for cleanup
API_PID=""
WORKER_PID=""
FRONTEND_PID=""

function cleanup() {
    echo_info "Shutting down services..."
    
    if [ -n "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
        echo_info "API server stopped"
    fi
    
    if [ -n "$WORKER_PID" ]; then
        kill $WORKER_PID 2>/dev/null || true
        echo_info "Worker stopped"
    fi
    
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo_info "Frontend stopped"
    fi
    
    echo_success "All services stopped"
    exit 0
}

# Trap signals for graceful shutdown
trap cleanup SIGINT SIGTERM EXIT

###############################################################################
# Main execution logic
###############################################################################

function run_api() {
    echo_section "Starting API Server"
    echo_info "Backend will start without requiring database (will skip if DB not available)"
    echo_info "Using mock mode for providers (set ELEVENLABS_MOCK_MODE=false to use real API)"
    echo ""
    uvicorn backend.main:app \
        --host ${API_HOST:-0.0.0.0} \
        --port ${API_PORT:-8000} \
        --reload \
        --log-level ${LOG_LEVEL:-info}
}

function run_worker() {
    echo_section "Starting Background Worker"
    QUEUE=$1
    if [ -n "$QUEUE" ]; then
        echo_info "Worker mode: Specific queue ($QUEUE)"
        python -m backend.worker --queue $QUEUE
    else
        echo_info "Worker mode: All queues"
        python -m backend.worker
    fi
}

function run_frontend() {
    echo_section "Starting Frontend Dev Server"
    cd frontend
    npm run dev
}

function run_backend_only() {
    echo_section "Starting Backend Services (API + Worker)"
    
    # Start API in background
    uvicorn backend.main:app \
        --host ${API_HOST:-0.0.0.0} \
        --port ${API_PORT:-8000} \
        --reload \
        --log-level ${LOG_LEVEL:-info} &
    API_PID=$!
    echo_success "API server running on http://${API_HOST:-0.0.0.0}:${API_PORT:-8000} (PID: $API_PID)"
    
    # Wait for API to start
    sleep 2
    
    # Start worker in foreground
    echo_info "Starting worker process..."
    python -m backend.worker
}

function run_full_stack() {
    echo_section "Starting Full Stack Application"
    echo_info "Services: API + Worker + Frontend"
    echo_info "Note: Services will start even if dependencies are not fully available"
    echo ""
    
    # Start API server
    echo_info "Starting API server..."
    if uvicorn backend.main:app \
        --host ${API_HOST:-0.0.0.0} \
        --port ${API_PORT:-8000} \
        --reload \
        --log-level ${LOG_LEVEL:-debug} &
    then
        API_PID=$!
        echo_success "✓ API server: http://localhost:${API_PORT:-8000}"
        echo_info "  - API docs: http://localhost:${API_PORT:-8000}/docs"
        echo_info "  - Health: http://localhost:${API_PORT:-8000}/health"
    else
        echo_warning "⚠ API server may have issues starting"
    fi
    
    # Wait for API to start
    sleep 2
    
    # Start worker
    echo_info "Starting background worker..."
    if python -m backend.worker &
    then
        WORKER_PID=$!
        echo_success "✓ Worker running (PID: $WORKER_PID)"
    else
        echo_warning "⚠ Worker may not be available (Redis might not be running)"
    fi
    
    # Wait for backend to stabilize
    sleep 2
    
    # Start frontend
    echo_info "Starting frontend dev server..."
    if [ -d "frontend" ]; then
        cd frontend
        if npm run dev > /tmp/frontend.log 2>&1 &
        then
            FRONTEND_PID=$!
            cd ..
            sleep 3
            echo_success "✓ Frontend: http://localhost:5173"
        else
            cd ..
            echo_warning "⚠ Frontend failed to start (check /tmp/frontend.log)"
        fi
    else
        echo_warning "⚠ Frontend directory not found"
    fi
    
    echo ""
    echo_success "═══════════════════════════════════════════════════"
    echo_success "  Application Started!"
    echo_success "═══════════════════════════════════════════════════"
    [ -n "$FRONTEND_PID" ] && echo_info "  Frontend:  http://localhost:5173"
    [ -n "$API_PID" ] && echo_info "  API:       http://localhost:${API_PORT:-8000}"
    [ -n "$API_PID" ] && echo_info "  API Docs:  http://localhost:${API_PORT:-8000}/docs"
    echo_success "═══════════════════════════════════════════════════"
    echo ""
    [ -n "$API_PID" ] || [ -n "$FRONTEND_PID" ] || echo_warning "Note: Some services may not be fully functional"
    echo_info "Logs are shown directly in this terminal window for easier debugging"
    echo_info "Press Ctrl+C to stop all services"
    
    # Wait for any process to exit
    wait
}

function run_tests() {
    echo_section "Running Tests"
    TEST_PATH=${1:-"tests"}
    
    echo_info "Test path: $TEST_PATH"
    echo_info "Running pytest..."
    python -m pytest $TEST_PATH -v --tb=short --color=yes
}

function run_setup_only() {
    echo_section "Setup Mode"
    echo_info "Installing dependencies and initializing database..."
    echo_success "Setup complete! Run './run.sh' to start the application."
}

###############################################################################
# Command dispatcher
###############################################################################

MODE=${1:-"full"}

case "$MODE" in
    "api")
        setup_env
        setup_database
        setup_redis
        setup_python_backend
        run_api
        ;;
        
    "worker")
        QUEUE=$2
        setup_env
        setup_database
        setup_redis
        setup_python_backend
        run_worker "$QUEUE"
        ;;
        
    "frontend")
        setup_env
        setup_frontend
        run_frontend
        ;;
        
    "backend")
        setup_env
        setup_database
        setup_redis
        setup_python_backend
        init_database
        run_backend_only
        ;;
        
    "test")
        TEST_PATH=$2
        setup_env
        setup_python_backend
        run_tests "$TEST_PATH"
        ;;
        
    "setup")
        setup_env
        setup_database
        setup_redis
        setup_python_backend
        setup_frontend
        init_database
        run_setup_only
        ;;
        
    "full"|"")
        echo_section "AI Lip-Sync Application"
        echo_info "Mode: Full Stack"
        echo_info "Note: Will start even if database/Redis are not available"
        echo ""
        
        setup_env
        setup_database || echo_warning "Database not available - continuing without it"
        setup_redis || echo_warning "Redis not available - worker features will be limited"
        setup_python_backend
        setup_frontend
        init_database || echo_warning "Database init skipped"
        run_full_stack
        ;;
        
    "help"|"--help"|"-h")
        echo_section "DashTests AI Lip-Sync Application"
        echo ""
        echo "Usage: ./run.sh [MODE] [OPTIONS]"
        echo ""
        echo "Modes:"
        echo "  (none)        Run full stack (default) - API + Worker + Frontend"
        echo "  full          Run full stack - API + Worker + Frontend"
        echo "  api           Run API server only"
        echo "  worker        Run background worker only"
        echo "  frontend      Run frontend dev server only"
        echo "  backend       Run backend only (API + Worker, no frontend)"
        echo "  test [path]   Run tests (default: all tests in tests/)"
        echo "  setup         Setup dependencies and database only"
        echo "  help          Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run.sh                    # Start full stack"
        echo "  ./run.sh api                # Start API only"
        echo "  ./run.sh worker             # Start worker only"
        echo "  ./run.sh test               # Run all tests"
        echo "  ./run.sh test tests/unit    # Run specific tests"
        echo ""
        echo "Services:"
        echo "  Frontend:  http://localhost:3000"
        echo "  API:       http://localhost:8000"
        echo "  API Docs:  http://localhost:8000/docs"
        echo ""
        ;;
        
    *)
        echo_error "Unknown mode: $MODE"
        echo_info "Run './run.sh help' for usage information"
        exit 1
        ;;
esac