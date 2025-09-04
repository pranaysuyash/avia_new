# Tech Debt Log (Intent-First)

Purpose: Track technical debt consciously deferred using the Intent-First quick filter.

## How to Use
- When effort is high and value is low/unclear, document here instead of removing.
- Include enough context for future prioritization; tie to user/business value if/when it emerges.

## Template
```
- Title:
- Area / Component:
- Original Intent:
- Evidence / References:
- Value Assessment: (User, Business)
- Effort & Risk: (estimate + risks)
- Decision: Defer (Tech Debt)
- Proposed Next Check-in: <date or milestone>
- Owner:
```

## Entries
- Title: Starter Library Thumbnails for New Templates
  - Area / Component: Pipeline Template Starter Library
  - Original Intent: Provide discoverable thumbnails for `tpl_medical_intake_v1`, `tpl_invoice_ap_v1`, `tpl_id_parse_v1`
  - Evidence / References: `docs/specs/pipeline-template-builder/examples/STARTER_LIBRARY.json`
  - Value Assessment: User: Medium (UX polish) | Business: Low-Medium (professionalism)
  - Effort & Risk: Effort Low (image creation); Risk Low
  - Decision: Defer (Tech Debt)
  - Proposed Next Check-in: Next docs polish milestone
  - Owner: Docs/Design

- Title: OpenAPI Client SDK Generation & CI Publishing
  - Area / Component: API Clients
  - Original Intent: Generate client SDKs from API YAMLs and publish artifacts
  - Evidence / References: API YAMLs under `docs/specs/*/API.yaml`
  - Value Assessment: User: Medium-High (dev velocity) | Business: Medium
  - Effort & Risk: Effort Medium; Risk Low-Medium (versioning, CI integration)
  - Decision: Defer (Tech Debt)
  - Proposed Next Check-in: After API stabilization
  - Owner: Platform

- Title: Pipeline Template Linter Integration in CI
  - Area / Component: Pipeline Templates
  - Original Intent: Validate templates and params via CLI in CI
  - Evidence / References: `docs/specs/pipeline-template-builder/CLI_LINTER_PLAN.md`, `CLI_LINTER_STUB.md`
  - Value Assessment: User: Medium (fewer bad templates) | Business: Medium (quality)
  - Effort & Risk: Effort Medium; Risk Low
  - Decision: Defer (Tech Debt)
  - Proposed Next Check-in: When adding next set of templates
  - Owner: DevEx
