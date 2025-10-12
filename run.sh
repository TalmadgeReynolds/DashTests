#!/bin/bash
# Self-contained script to run the DashTests application
# Just execute this script with no arguments to run everything

# Exit on any error
set -e

# Function to display colored output
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

# Create or use .env file
if [ ! -f .env ]; then
    echo_info "No .env file found. Creating one with development defaults (using mock providers)..."
    cat > .env << EOF
# Database configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=lipsync
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Storage configuration
S3_BUCKET_NAME=lipsync-storage
AWS_ACCESS_KEY_ID=mockaccess
AWS_SECRET_ACCESS_KEY=mocksecret
AWS_REGION=us-west-2
MOCK_STORAGE=true

# API provider keys (using mock mode by default for easy startup)
HEYGEN_API_KEY=mockkey
VEO_API_KEY=mockkey
ELEVENLABS_API_KEY=mockkey

# Webhook secrets
WEBHOOK_SECRET_HEYGEN=mocksecret

# Logging
LOG_LEVEL=INFO

# Mock settings (true by default for easy development startup)
MOCK_PROVIDERS=true
HEYGEN_MOCK_MODE=true
VEO_MOCK_MODE=true
ELEVENLABS_MOCK_MODE=true
EOF
    echo_info "Created .env file with development defaults (mock providers enabled)"
    echo_info "Edit .env file if you want to use real provider services"
fi

# Load environment variables automatically
echo_info "Loading environment variables..."
set -a
source .env
set +a

# Ensure database is available - either start Docker or verify connection
echo_info "Setting up database..."

# Try to connect to existing database
DB_AVAILABLE=false
if command -v pg_isready > /dev/null; then
    if pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} > /dev/null 2>&1; then
        echo_success "Database is already running"
        DB_AVAILABLE=true
    fi
fi

# If database not available and Docker exists, try to start it
if [ "$DB_AVAILABLE" = false ] && command -v docker > /dev/null; then
    if command -v docker-compose > /dev/null; then
        echo_info "Starting PostgreSQL with docker-compose..."
        docker-compose up -d postgres || echo_warning "Failed to start PostgreSQL with docker-compose"
        
        # Wait for database to be ready
        for i in {1..10}; do
            if pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} > /dev/null 2>&1; then
                echo_success "Database is ready."
                DB_AVAILABLE=true
                break
            fi
            echo -n "."
            sleep 1
        done
    else
        echo_info "Starting PostgreSQL with Docker..."
        docker run --rm -d --name postgres \
            -e POSTGRES_USER=${POSTGRES_USER:-postgres} \
            -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
            -e POSTGRES_DB=${POSTGRES_DB:-lipsync} \
            -p ${POSTGRES_PORT:-5432}:5432 \
            postgres:13 || echo_warning "Failed to start PostgreSQL with Docker"
            
        # Wait for database to be ready
        for i in {1..10}; do
            if pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} > /dev/null 2>&1; then
                echo_success "Database is ready."
                DB_AVAILABLE=true
                break
            fi
            echo -n "."
            sleep 1
        done
    fi
fi

if [ "$DB_AVAILABLE" = false ]; then
    echo_warning "Could not connect to database. Some features may not work correctly."
fi

# Set up Python environment automatically
# Detect and use existing venv if we're in one, otherwise create a new one
if [ -z "$VIRTUAL_ENV" ]; then
    # Create venv if it doesn't exist
    if [ ! -d "venv" ]; then
        echo_info "Creating Python virtual environment..."
        python3 -m venv venv || python -m venv venv
    fi
    
    # Activate the virtual environment
    echo_info "Activating virtual environment..."
    source venv/bin/activate
else
    echo_info "Using existing virtual environment: $VIRTUAL_ENV"
fi

# Install dependencies automatically
echo_info "Installing dependencies..."
pip install -r requirements.txt

# Check if ffmpeg is installed (required for video processing)
if ! command -v ffmpeg &> /dev/null; then
    echo_warning "ffmpeg is not installed. Video processing features will not work correctly."
fi

# Initialize database automatically
echo_info "Initializing database..."
python -c "from backend.db import init_db; init_db()" || echo_warning "Database init failed, but continuing"

# Run migrations automatically
echo_info "Running database migrations..."
alembic upgrade head

# Determine mode from command line or run full stack by default
MODE=${1:-"full"}

case "$MODE" in
    "api")
        echo_info "Starting API server only..."
        uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
        
    "worker")
        QUEUE=$2
        if [ -n "$QUEUE" ]; then
            echo_info "Starting worker for queue: $QUEUE"
            python -m backend.worker --queue $QUEUE
        else
            echo_info "Starting worker for all queues"
            python -m backend.worker
        fi
        ;;
        
    "test")
        echo_info "Running tests..."
        TEST_PATH=${2:-"tests"}
        python -m pytest $TEST_PATH -v
        ;;
        
    "full"|*)
        # Run everything - the default behavior
        echo_info "Starting full application stack (API + Worker)..."
        
        # Start API server in background
        uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
        API_PID=$!
        echo_success "API server running on http://0.0.0.0:8000 (PID: $API_PID)"
        
        # Create a trap to handle Ctrl+C and other signals
        trap "echo_info 'Shutting down services...'; kill $API_PID; exit" SIGINT SIGTERM
        
        # Start worker in foreground
        echo_info "Starting worker process..."
        python -m backend.worker
        
        # If worker exits, kill API server
        echo_info "Worker exited, shutting down API server..."
        kill $API_PID 2>/dev/null || true
        ;;
esac