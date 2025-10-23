#!/bin/bash

# Script to add your current IP to RDS security group
# Prerequisites: AWS CLI installed and configured with appropriate permissions

# Get security group from .env file if possible
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
  echo "Loading security group from .env file..."
  SG_FROM_ENV=$(grep RDS_SECURITY_GROUP_ID "$ENV_FILE" | cut -d '=' -f2)
  if [ ! -z "$SG_FROM_ENV" ]; then
    SECURITY_GROUP_ID=$SG_FROM_ENV
    echo "Found security group in .env: $SECURITY_GROUP_ID"
  fi
fi

# If not found in .env, use the hardcoded value
if [ -z "$SECURITY_GROUP_ID" ]; then
  echo "No security group found in .env, using default"
  SECURITY_GROUP_ID="sg-0293118a072a350d7"
fi

echo "Using security group: $SECURITY_GROUP_ID"

# Get your current public IP address
CURRENT_IP=$(curl -s http://checkip.amazonaws.com)
if [ -z "$CURRENT_IP" ]; then
  echo "Error: Could not determine your public IP address"
  exit 1
fi

echo "Your current public IP is: $CURRENT_IP"

# Get AWS region from .env file if possible
AWS_REGION="us-east-1" # Default to us-east-1 where RDS is typically located
# Force us-east-1 as the region for this script
AWS_REGION="us-east-1"
echo "Using AWS region: $AWS_REGION"

# Add rule for PostgreSQL access from your current IP
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 5432 \
  --cidr "$CURRENT_IP/32" \
  --region $AWS_REGION

if [ $? -eq 0 ]; then
  echo "Successfully added your IP to the security group"
  echo "Try connecting to RDS again now"
  
  # Check for RDS connection script to verify connection
  if [ -f "$(dirname "$0")/test_db_connection.sh" ]; then
    echo "Would you like to test the database connection now? (y/n)"
    read -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      bash "$(dirname "$0")/test_db_connection.sh"
    fi
  fi
else
  echo "Failed to add rule to security group"
  echo "Please verify:"
  echo "1. Your AWS credentials have permission to modify security groups"
  echo "2. The security group ID ($SECURITY_GROUP_ID) is correct"
  echo "3. The region ($AWS_REGION) is correct for your RDS instance"
  echo ""
  echo "You may need to add your IP manually in the AWS Console"
fi