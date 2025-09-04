# ID Card Reader System — Tasks

- Phase 0 — Standards & Samples
  - Implement MRZ and AAMVA parsers; collect sample IDs (synthetic where needed)
- Phase 1 — MVP Parse
  - Front/back upload; alignment; MRZ/PDF417 decode; OCR printed fields; JSON
- Phase 2 — Fraud Heuristics
  - Checksum, expiry, layout checks; glare/blur scoring; manual review queue
- Phase 3 — APIs & UX
  - Jobs, results, face crop assets; guided capture hints; audit logs
- Phase 4 — Hardening
  - Performance tuning; encryption policies; legal reviews by region
