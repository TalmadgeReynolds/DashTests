# Error & Retry Matrix

Classes: ProviderError, TransientProviderError, PostFxError, ValidationError
Retries:
- 5xx/429/network: exp backoff (base 500ms, jitter, max 5 tries)
- 4xx: no retry
- PostFx fail: 1 retry if CPU fallback available
Surfaced JSON: { status:'error', code:'PROVIDER_TIMEOUT', message, detail?, request_id? }
