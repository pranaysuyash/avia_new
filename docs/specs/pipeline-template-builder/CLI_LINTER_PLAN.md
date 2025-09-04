# Pipeline Template Linter — CLI Plan

## Goals
- Provide a simple CLI to validate templates against schema, run structural and policy checks, and print actionable diagnostics.

## Commands
- `pipeline-lint validate <file|dir>` — JSON Schema validation + parameters_schema conformance
- `pipeline-lint dag <file|dir>` — DAG checks (acyclic, node refs, port type compatibility, max nodes)
- `pipeline-lint policy <file|dir>` — Guardrails (pre-publish checks, latency budgets)
- `pipeline-lint io <file|dir>` — Template-level IO vs DAG start/end validation
- `pipeline-lint all <file|dir>` — Run all checks; exit nonzero on errors

## Output Format
- Default: human-readable with severity (INFO/WARN/ERROR) and path pointers
- `--json`: machine-readable diagnostics (file, rule_id, severity, message, node/edge refs)
- `--summary`: counts by severity and rule

## Rules Mapping (subset)
- SCHEMA_001: Template validates TEMPLATE_SCHEMA.json
- PARAM_001: Parameters conform to parameters_schema
- DAG_001: Graph is acyclic
- DAG_002: Edge endpoints reference existing nodes/ports
- IO_001: Node IO types compatible
- IO_002: Template io.inputs/io.outputs align with DAG
- POL_001: Pre-publish policy before Export/Publish nodes
- POL_002: Latency budgets on time-sensitive nodes
- SIZE_001: Max nodes <= 100
- SECR_001: Secrets references reviewed/resolved

## Exit Codes
- 0: no errors, warnings may exist
- 1: one or more ERROR diagnostics
- 2: invalid CLI usage

## File Layout
- `bin/pipeline-lint` — CLI entry (future)
- `lib/rules/*.js` — rule implementations
- `lib/schema/*.json` — JSON Schemas (include TEMPLATE_SCHEMA.json)
- `lib/checks/*.js` — composite checks (dag/io/policy)
- `lib/reporters/*.js` — text/json/summary reporters

## CI Integration
- Add a job to run `pipeline-lint all docs/specs/pipeline-template-builder/examples/*.json`
- Fail on errors; warnings allowed with threshold via `--max-warn`

