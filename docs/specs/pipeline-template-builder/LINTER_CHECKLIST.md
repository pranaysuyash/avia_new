# Pipeline Template Linter — Checklist & Rules

Use this checklist to validate templates before publishing or running.

## Structure & Schema
- [ ] Template validates against TEMPLATE_SCHEMA.json (id/name/version/dag required)
- [ ] `parameters` conforms to `parameters_schema` (types, ranges, enums)
- [ ] No additionalProperties unless explicitly allowed

## DAG Integrity
- [ ] Graph is acyclic (no cycles)
- [ ] All `edges.from` and `edges.to` reference existing node ports
- [ ] Node IO types are compatible across connections (e.g., Video → Video)
- [ ] Max nodes per template not exceeded (e.g., 100)

## Node Definitions
- [ ] Every node uses a known `def` from the catalog
- [ ] Required params present for each node; defaults injected where applicable
- [ ] Secrets references resolved or explicitly marked for runtime injection

## Policies & Guardrails
- [ ] Pre-publish checks (PII/rights) present before Export/Publish nodes
- [ ] Policy severities appropriate (block vs warn)
- [ ] Latency budgets apply to time-sensitive nodes (e.g., Detect.Highlights)

## IO Contracts
- [ ] Template-level `io.inputs` and `io.outputs` defined and match DAG ends
- [ ] Node `io.in`/`io.out` arrays present for compile-time checks
- [ ] Parameter substitutions (`${param}`) resolved in context

## Cost & Performance
- [ ] Estimators produce cost/time P50/P95 within acceptable bounds
- [ ] Sampling caps set for heavy tasks (OCR/ASR/Gen)
- [ ] Concurrency caps set on triggers to avoid overload

## Triggers & Scheduling
- [ ] Trigger types valid (upload/label/webhook/cron/manual)
- [ ] Cron expressions validated; time zone documented
- [ ] Dry-run preview produces expected plan

## Compliance & Audit
- [ ] Audit logs enabled for template changes and runs
- [ ] Critical nodes (redaction/privilege) have human-review paths
- [ ] Data retention for outputs documented (reports/productions)

## UX & Documentation
- [ ] Template has description and thumbnail
- [ ] Parameters documented (names/units, min/max, enums)
- [ ] Acceptance criteria covered in examples/ACCEPTANCE_CRITERIA.md

