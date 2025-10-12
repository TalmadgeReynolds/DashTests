#!/usr/bin/env python
"""
Script to simulate a webhook request from Heygen to test the webhook implementation.
"""
import os
import sys
import json
import hmac
import hashlib
import argparse
import requests
from datetime import datetime, timezone

def main():
    parser = argparse.ArgumentParser(description='Send test webhook to local server')
    parser.add_argument('--url', default='http://localhost:8000/webhooks/heygen',
                        help='Webhook URL (default: http://localhost:8000/webhooks/heygen)')
    parser.add_argument('--secret', default=os.environ.get('WEBHOOK_SECRET_HEYGEN', 'test-secret'),
                        help='Webhook secret key (default: from WEBHOOK_SECRET_HEYGEN env var)')
    parser.add_argument('--job-id', default=f'test-job-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                        help='Provider job ID (default: auto-generated)')
    parser.add_argument('--status', default='DONE', choices=['DONE', 'ERROR'],
                        help='Job status (default: DONE)')
    parser.add_argument('--output-url', default='https://example.com/output.mp4',
                        help='Output URL (default: https://example.com/output.mp4)')
    
    args = parser.parse_args()
    
    # Create webhook payload
    payload = {
        "provider_job_id": args.job_id,
        "status": args.status,
        "output_url": args.output_url,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Convert payload to JSON string
    payload_bytes = json.dumps(payload).encode()
    
    # Generate signature
    signature = hmac.new(
        args.secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    # Set headers
    headers = {
        'Content-Type': 'application/json',
        'X-Heygen-Signature': f'sha256={signature}'
    }
    
    print(f"Sending webhook to {args.url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Signature: sha256={signature}")
    
    try:
        # Send webhook request
        response = requests.post(args.url, headers=headers, json=payload)
        
        # Print response details
        print("\nResponse:")
        print(f"Status Code: {response.status_code}")
        print(f"Body: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error sending webhook: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())