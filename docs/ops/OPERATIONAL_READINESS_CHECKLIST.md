# Operational Readiness Checklist (Per Feature Track)

This checklist ensures each feature track can be safely operated in production. Mark N/A where appropriate.

## Common (All Tracks)
- [ ] SLOs defined (availability, latency P50/P95, error rate) and alerting in place
- [ ] Dashboards for key metrics; runbooks for common incidents
- [ ] Rate limits/quotas; backpressure; retries; idempotency
- [ ] Secrets/IAM least privilege; audit logging enabled; PII handling documented
- [ ] Canary deployments and rollback procedures
- [ ] Cost telemetry and budgets; capacity plan; on-call ownership

## Pipeline & Template Builder
- [ ] Template registry backups; manifest signing; linter in CI
- [ ] DAG compile failures produce actionable diagnostics
- [ ] Policy gates enforced for publish/export; audit of approvals
- [ ] Large-DAG performance tested; editor regressions monitored

## Frame OCR Indexing
- [ ] OCR accuracy baseline/golden dataset; tracking of precision/recall
- [ ] Sampling caps; concurrency limits; off-peak schedules
- [ ] Storage retention for hits; summarization for repeated banners
- [ ] Cost per minute monitored; GPU/CPU allocation strategy

## Creator Publish Packs
- [ ] Provider quotas and fallbacks; content moderation hooks
- [ ] Platform posting errors retried; partial success behavior defined
- [ ] A/B testing flows; asset retention policy

## Education Learning Augmentation
- [ ] Export integrations (Anki/Notion) secrets rotation and retries
- [ ] Accessibility checks (caption QC) before distribution
- [ ] Privacy for student data; FERPA/COPPA alignment

## Live/SSAI & Highlights
- [ ] WS event stability; latency budgets for detection and clipping
- [ ] SSAI metadata validation; vendor integration tests
- [ ] DVR windows tuned; failure modes (drop features under load)

