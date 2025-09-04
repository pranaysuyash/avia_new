# Intent-First Checklist

Purpose: Ensure changes align with user/business value, minimize risk, and ship MVPs confidently.

## 1) Intent Summary
- What outcome are we delivering? Who benefits and how?

## 2) Context Discovery
- Related code/docs/specs searched:
- Adjacent systems (UI/Backend/DB/Infra) touched:
- History reviewed (issues/PRs/commits/notes):

## 3) Value, Risk, Effort
- User value: High / Medium / Low (why)
- Business value: High / Medium / Low (why)
- Technical effort: Hours / Days / Weeks (estimate)
- Operational risk: Low / Medium / High (monitoring, cost, security, compliance)

## 4) Decision Matrix Outcome
- Action: Complete now (MVP) | Plan for later | Document tech/test debt | Remove (with approval)
- Scope chosen (MVP vs. enhancements):

## 5) MVP Tests (Critical paths only)
- Happy path covered? Y/N
- One high-impact failure mode? Y/N
- Security/data/compliance constraint? Y/N

## 6) Traceability
- Linked specs (API YAMLs, schemas):
- ADR (if applicable):
- Monitoring/alerts updates:

## 7) Rollout
- Migration/backfill needed? Y/N
- Feature flags/kill-switch? Y/N
- Post-deploy checks & dashboards:

Guiding reference: `intent_first_handbook.md`

