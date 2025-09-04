# Test Debt Log (Intent-First)

Purpose: Capture tests intentionally deferred via the testing quick filter, with rationale.

## How to Use
- Use when business impact is low, code is stable, or covered by higher-level tests.
- Always ensure MVP tests exist for critical/high-priority flows.

## Template
```
- Title:
- Component / Feature:
- Risk / Impact:
- Current Coverage:
- Rationale for Deferral:
- Minimal Safeguards in Place (smoke tests, monitoring):
- Decision: Defer (Test Debt)
- Proposed Next Check-in: <date or milestone>
- Owner:
```

## Entries
- Title: Schema and Template Validation in CI
  - Component / Feature: JSON Schemas and Pipeline Template Examples
  - Risk / Impact: Medium — prevents invalid contracts/templates from drifting
  - Current Coverage: Manual validation only; `jq` sanity checks run locally
  - Rationale for Deferral: Docs-first phase; CI wiring pending
  - Minimal Safeguards in Place (smoke tests, monitoring): Local `jq` checks; reviewer checklist
  - Decision: Defer (Test Debt)
  - Proposed Next Check-in: Next CI/CD iteration
  - Owner: Platform/DevEx

- Title: Postman Collection Smoke Tests (Newman)
  - Component / Feature: Medical, Invoice, ID API collections
  - Risk / Impact: Medium — ensures example requests remain valid
  - Current Coverage: Collections exist; no automated runs
  - Rationale for Deferral: No live env for CI yet; placeholders
  - Minimal Safeguards in Place (smoke tests, monitoring): Manual runs by developers
  - Decision: Defer (Test Debt)
  - Proposed Next Check-in: After staging env readiness
  - Owner: API Team

- Title: Selfie Verification Flow Test
  - Component / Feature: ID Card Reader — selfie match (optional)
  - Risk / Impact: Low — optional path; gating via param
  - Current Coverage: None (docs-only)
  - Rationale for Deferral: No runtime; path is optional in spec
  - Minimal Safeguards in Place (smoke tests, monitoring): N/A
  - Decision: Defer (Test Debt)
  - Proposed Next Check-in: When implementing runtime
  - Owner: Identity
