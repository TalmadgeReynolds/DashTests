# Self-Contained Run Script

The `run.sh` script is completely self-contained and automatic. Just run it once with no arguments and it will handle everything for you.

## How It Works

Simply run:

```bash
./run.sh
```

## What It Does Automatically

- Creates a `.env` file if none exists with mock provider settings for easy development
- Sets up a Python virtual environment
- Installs all dependencies
- Tries to connect to an existing PostgreSQL database
- Starts PostgreSQL using Docker if available and database isn't already running
- Initializes the database and applies migrations
- Starts both the API server and worker process

## Optional Modes

You can also run specific components if needed:

```bash
# Start API server only
./run.sh api

# Start worker only (all queues)
./run.sh worker

# Start worker for a specific queue
./run.sh worker queue_name

# Run tests
./run.sh test

# Run specific tests
./run.sh test path/to/tests
```

## Configuration

The script automatically creates a development-friendly `.env` file with mock providers enabled. This lets you run the application immediately without any real API keys or services.

### Using Real Services

To use real services instead of mocks, edit the `.env` file after it's created and set:

```
MOCK_PROVIDERS=false
HEYGEN_MOCK_MODE=false
VEO_MOCK_MODE=false
ELEVENLABS_MOCK_MODE=false
```

Then add your real API keys:

```
# API provider keys
HEYGEN_API_KEY=your-real-key-here
VEO_API_KEY=your-real-key-here
ELEVENLABS_API_KEY=your-real-key-here

# Storage configuration 
AWS_ACCESS_KEY_ID=your-real-key-here
AWS_SECRET_ACCESS_KEY=your-real-key-here
```

## Prerequisites

The script tries to handle everything automatically, but these are helpful to have:

- Python 3.11+
- Docker (optional, but helpful for running PostgreSQL)
- FFmpeg (for video processing features)
- PostgreSQL (if not using Docker)

## Database Options

The script tries multiple approaches to get a database:

1. First, it looks for an existing PostgreSQL connection
2. If that fails, it tries to start PostgreSQL using docker-compose
3. If docker-compose isn't available, it tries to start PostgreSQL with regular Docker
4. If all database options fail, it will warn you but still try to run with limited functionality