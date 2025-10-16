#!/bin/bash

# Script to add your current IP to RDS security group
# Prerequisites: AWS CLI installed and configured with appropriate permissions

# Security group ID from your RDS instance
SECURITY_GROUP_ID="sg-0293118a072a350d7"

# Get your current public IP address
CURRENT_IP=$(curl -s http://checkip.amazonaws.com)
if [ -z "$CURRENT_IP" ]; then
  echo "Error: Could not determine your public IP address"
  exit 1
fi

echo "Your current public IP is: $CURRENT_IP"

# Add rule for PostgreSQL access from your current IP
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 5432 \
  --cidr "$CURRENT_IP/32" \
  --description "Temporary access from Codespace"

if [ $? -eq 0 ]; then
  echo "Successfully added your IP to the security group"
  echo "Try connecting to RDS again now"
else
  echo "Failed to add rule to security group"
  echo "Please add your IP manually in the AWS Console"
fi