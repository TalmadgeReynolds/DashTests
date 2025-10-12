# Webhook Contracts & Verification

## Heygen
Headers: X-Heygen-Signature: sha256=HMAC(body, WEBHOOK_SECRET_HEYGEN)
Body: { provider_job_id, status, output_url? }

Rules:
- Verify HMAC; constant-time compare
- Idempotent; ignore if terminal
- Respond 200 only after DB commit
