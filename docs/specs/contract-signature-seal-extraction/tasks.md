# Contract Signature & Seal Extraction — Tasks

- Phase 0 — Dataset & Metrics
  - Assemble golden set (signed/unsigned, seals, varied quality)
  - Define precision/recall targets; dashboard wiring

- Phase 1 — Detection MVP
  - Preprocessing (binarize/denoise/deskew)
  - Signature detector (contour+CNN); Seal detector (shape+OCR ring)
  - JSON outputs + crops; per‑doc summary report

- Phase 2 — Batch API & Observability
  - Async job APIs; idempotency; retries; audit logs
  - Metrics (runtime/page, hits/doc, confidence); alerts on drift

- Phase 3 — Verification (v2)
  - Embedding model for signature compare; threshold policy; disclaimers
  - Secure storage of reference signatures; access controls

- Phase 4 — Integrations & UX
  - Doc viewer overlays; exceptions queue; export to case systems
  - Pipeline template published; starter manifest with params

- Phase 5 — Hardening
  - Performance tuning; backpressure; retention policies; compliance review
