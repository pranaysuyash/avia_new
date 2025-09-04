# Runbook — WebSocket Instability

Severity: SEV-3 (intermittent) to SEV-2 (major) if persistent

## Symptoms
- Frequent disconnects/reconnects; missed events in real-time collab/notifications
- Elevated 101/close codes; client error logs

## Immediate Actions
1) Triage
- Verify WS server health; CPU/mem; connection counts
- Check reverse proxy timeouts/keep-alive settings
- Inspect error codes (1006/1001) and server logs

2) Mitigation
- Increase ping/heartbeat; adjust idle timeouts
- Reduce message payloads; enable compression if not harmful
- Scale WS pods; session stickiness if needed

3) Communication
- Inform users of degraded real-time features; suggest manual refresh fallback

## Root Cause & Follow-up
- Publish WS endpoint matrix; remove unused client endpoints
- Load test WS; set clear SLOs and alerts
- Add backpressure in event producers; retry queues

## Dashboards & Queries
- Active connections, disconnect rate, message send failures, p99 latency

