# Ops Runbook

Metrics: jobs_created_total, jobs_failed_total, provider_latency_ms{engine=}, postfx_runtime_s
Logs: JSON, include job_id, provider_job_id, step, latency_ms
Dash: success rate, p95 latency, PostFX runtime
Common fixes: scale workers, check Redis, verify webhook secrets
