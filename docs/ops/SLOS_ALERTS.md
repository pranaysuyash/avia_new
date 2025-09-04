# Service Level Objectives & Alert Rules (Initial)

This document proposes SLO targets and example alerting rules (Prometheus-style) per track.

## Common SLOs (per service)
- Availability: 99.9%
- Latency: P95 < 500ms for read APIs; P95 < 2s for write/submit
- Error rate: < 1% 5xx (per minute)

## Pipeline & Template Builder
- Compile P95 < 2s; Run submit P95 < 1s
- Alert: compile_errors_rate > 5% over 5m

## Frame OCR Indexing
- Job completion for 30 min asset: P95 < 20m (config capped); accuracy >= 80% on golden set
- Alert: ocr_job_backlog > 200 OR ocr_accuracy_delta < -5% vs baseline

## Creator Publish Packs
- Job P95 < 10m; provider error rate < 3% with retries
- Alert: provider_429_rate > threshold OR pack_post_failures > threshold

## Live/SSAI & Highlights
- WS stability: disconnect_rate < 2%/min; event latency P95 < 500ms
- Alert: ws_disconnect_rate > 5% OR highlight_detection_latency_p95 > 800ms

## Example Prometheus Rules (YAML)
```yaml
- alert: HighErrorRate
  expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.01
  for: 10m
  labels:
    severity: page
  annotations:
    summary: High 5xx error rate

- alert: PipelineCompileFailures
  expr: rate(pipeline_compile_failures_total[5m]) > 0.05
  for: 10m
  labels:
    severity: ticket
  annotations:
    summary: Pipeline compile failure rate above 5%

- alert: WSDisconnects
  expr: rate(ws_disconnects_total[1m]) / rate(ws_connections_total[1m]) > 0.05
  for: 5m
  labels:
    severity: page
  annotations:
    summary: WebSocket disconnect rate above 5%
```

