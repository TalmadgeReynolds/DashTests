"""
Prometheus metrics definitions
"""
from prometheus_client import Counter, Histogram

# Counters
jobs_created_total = Counter(
    "jobs_created_total",
    "Total number of jobs created",
    ["method"]
)

jobs_failed_total = Counter(
    "jobs_failed_total",
    "Total number of jobs that failed",
    ["engine"]
)

# Histograms
provider_latency_ms = Histogram(
    "provider_latency_ms",
    "Provider API latency in milliseconds",
    ["engine"]
)

postfx_runtime_s = Histogram(
    "postfx_runtime_s",
    "Post-FX processing runtime in seconds",
    ["operation"]
)