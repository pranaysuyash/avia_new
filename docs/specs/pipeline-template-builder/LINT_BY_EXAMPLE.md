# Pipeline Template Lint — Examples

This document shows common mistakes in templates and the linter messages they trigger.

## 1) Cycle in DAG (BAD_CYCLE.json)
- Symptom: Edges create a loop A→B→C→A
- Linter: DAG Integrity → ERROR: Cycle detected at edge C.out → A.in (nodes: A→B→C). Remove the cycle.

## 2) Parameter out of range (BAD_PARAM_RANGE.json)
- Symptom: `clip_length_s` set to 120 but schema allows ≤ 60
- Linter: Parameters → ERROR: clip_length_s (120) violates schema [4..60]. Fix the value or relax schema.

## 3) Unknown node definition (BAD_UNKNOWN_NODE.json)
- Symptom: Node `Magic.Enhance` not in catalog
- Linter: Node Definitions → ERROR: Unknown def "Magic.Enhance". Choose a known node or register a custom node.

## 4) IO type mismatch (BAD_IO_TYPES.json)
- Symptom: Connect Text.Segments → Video input
- Linter: IO Contracts → ERROR: Incompatible port types (Text.Segments → Video). Insert a transform node or change connection.

## 5) Missing guardrail before Publish (BAD_NO_POLICY.json)
- Symptom: Pipeline has Publish.SocialPack but no PII/rights policy
- Linter: Policies → WARN: No pre-publish policy found before Publish.SocialPack. Add Redact/Policy gate.

## 6) Missing template IO (BAD_TEMPLATE_IO.json)
- Symptom: Template lacks `io.inputs` but DAG expects input
- Linter: IO Contracts → WARN: Template-level IO missing for DAG start/end. Define io.inputs/io.outputs.

## 7) Secrets not resolved (BAD_SECRETS.json)
- Symptom: Node param references `${SECRET_API_KEY}` with no runtime injection plan
- Linter: Node Definitions → WARN: Secrets reference detected; ensure runtime injection mapping.

