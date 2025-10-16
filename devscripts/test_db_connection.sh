#!/bin/bash
# Simple test script to connect to PostgreSQL and create a table

set -e
set -x

# Source the environment file
source /workspaces/DashTests/.env

# Extract DB connection parameters from DATABASE_URL
if [[ "$DATABASE_URL" =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
  DB_USER="${BASH_REMATCH[1]}"
  DB_PASSWORD="${BASH_REMATCH[2]}"
  DB_HOST="${BASH_REMATCH[3]}"
  DB_PORT="${BASH_REMATCH[4]}"
  DB_NAME="${BASH_REMATCH[5]}"
  echo "Successfully parsed DATABASE_URL"
fi

echo "Testing connection to database: $DB_HOST:$DB_PORT/$DB_NAME"

# Test connection
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null; then
  echo "Connection successful!"
  
  # Try creating a simple test table
  echo "Creating a test table..."
  if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE TABLE IF NOT EXISTS test_connection (id SERIAL PRIMARY KEY, test_date TIMESTAMP DEFAULT NOW());" > /dev/null; then
    echo "Test table created successfully."
    
    # Insert a test record
    echo "Inserting a test record..."
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "INSERT INTO test_connection (test_date) VALUES (NOW()) RETURNING id;" > /dev/null; then
      echo "Record inserted successfully."
      
      # Query the test table
      echo "Querying the test table..."
      PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT * FROM test_connection ORDER BY id DESC LIMIT 5;"
    else
      echo "Failed to insert record."
    fi
  else
    echo "Failed to create test table."
  fi
else
  echo "Connection failed!"
fi

echo "Script completed."