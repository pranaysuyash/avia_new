# Intent-First Workflow

This codifies how we apply `intent_first_handbook.md` across code, docs, and ops.

## Daily Flow
- Start with an Intent Summary and quick Context Discovery.
- Apply Value/Risk/Effort and choose an action via the Decision Matrix.
- Prefer MVP completion for high-value, low–medium effort work.
- Document deferrals in TECH_DEBT.md or TEST_DEBT.md.
- Use ADRs for notable architectural/process decisions.

## Artifacts
- Checklist: `docs/engineering/templates/INTENT_FIRST_CHECKLIST.md`
- ADR template: `docs/engineering/templates/ADR_TEMPLATE.md`
- Tech debt log: `docs/engineering/TECH_DEBT.md`
- Test debt log: `docs/engineering/TEST_DEBT.md`
- PR template: `.github/PULL_REQUEST_TEMPLATE.md`

## Testing MVP Rule (for critical/high-priority)
- Cover happy path, one high-impact failure, and any compliance/security constraint.

## Traceability
- Link API YAMLs and JSON Schemas in PRs and ADRs.
- Note monitoring/alerts/dashboards changes.

## Decision Handoff
- Summarize Intent, Decision, and MVP scope in PRs and status updates.
- Schedule check-ins for deferred items (date or milestone).

