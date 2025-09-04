# Pipeline & Template Builder Platform — Tasks

- Phase 0 — Foundations
  - Decide canonical API prefixes; RBAC scopes; manifest signing approach
  - Define node IO type system; param schemas; cost estimator contracts

- Phase 1 — Canvas + Catalog (MVP editor)
  - Build canvas editor (pan/zoom, drag, connect, undo/redo, snap)
  - Node palette with core nodes (Ingest, Transcribe, OCR, Enhance, Redact, Summarize, Index, Export, Publish, Webhook, Decision)
  - Inspector panel (params, validation, cost/time estimates)
  - DAG validation (acyclicity, type checks, policy gate placement)

- Phase 2 — Templates & Versioning
  - Save/load templates; semantic versions; diff/rollback
  - Parameters with defaults and validation; secrets references
  - Manifest export (JSON/YAML) with signatures; CI lints

- Phase 3 — Compile & Run
  - Compiler generates execution plan; idempotency and retry policies
  - Orchestrator adapter to submit per-node jobs; run tracker
  - Triggers: upload/label/webhook/cron/manual; concurrency caps; dry-run

- Phase 4 — Observability & Guardrails
  - Per-node metrics/logs; run timeline; bottleneck heatmaps
  - Policy engine: preconditions/approvals; rights/redaction checks before publish
  - Notifications on failures; rerun from failed node

- Phase 5 — Sharing & Governance
  - RBAC for templates/runs/triggers; activity audit; workspace scoping
  - Template library with search/tags; import/clone; featured recipes

- Phase 6 — Extensibility & SDK
  - Node SDK for custom tasks; node registry; marketplace hooks (future)
  - Sample custom nodes (e.g., watermark, IMF validator, social poster)

- Phase 7 — UX Polish & Accessibility
  - Keyboard-first interactions; focus rings; screen-reader labels
  - Onboarding tour; templated wizards (QC Pack, Creator Pack)

- Phase 8 — Hardening
  - Load tests on large DAGs; failure injection; backup/restore of templates
  - Security review: least privilege secrets; manifest signing; audit coverage

