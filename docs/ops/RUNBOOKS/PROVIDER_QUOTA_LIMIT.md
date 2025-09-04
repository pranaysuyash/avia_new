# Runbook — Provider Quota Limit / Rate Limit

Severity: SEV-3 (degraded) to SEV-2 (major) if sustained

## Symptoms
- 429/RateLimitExceeded from providers (Replicate/FAL/OpenRouter/social APIs)
- Elevated error rates in Creator Packs or posting endpoints
- Queues backing up; retries increasing

## Immediate Actions
1) Triage
- Check provider status page / incident feeds
- Inspect error samples and headers (Retry-After, X-RateLimit-Remaining)
- Verify our quotas/usage in provider dashboards

2) Mitigation
- Enable backoff policies (exponential + jitter); reduce concurrency
- Switch to fallback providers/models when available
- Defer non-critical jobs; enable off-peak scheduling
- For posting: queue posts; inform users via UI banner

3) Communication
- Post status; set expectations on delays; update incident channel

## Root Cause & Follow-up
- Adjust concurrency caps per tenant; refine cost/usage budgets
- Add per-provider circuit breakers; automated failover
- Improve caching for repeated generation requests

## Dashboards & Queries
- Error rate by provider, 429 counts, queue wait times, retries, success recovery time

