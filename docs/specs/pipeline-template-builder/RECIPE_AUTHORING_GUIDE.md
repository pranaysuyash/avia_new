# Recipe Authoring Guide — Pipelines & Templates

This guide helps non-engineers author safe, reusable pipelines.

## Principles
- Keep recipes focused; prefer composability over monoliths.
- Parameterize anything tenant/content-dependent; set sensible defaults.
- Add guardrails (policies) before publish/export actions.

## Parameters & Validation
- Use clear names and units (e.g., `interval_s`, `loudness_target_lufs`).
- Provide min/max and enums where possible; document ranges in template description.
- Reference parameters in node configs using `${param_name}`.

## Cost & Time Tips
- Show estimates in the inspector; warn on P95 outliers.
- Cap frame sampling and durations; use off-peak schedules for heavy jobs.
- Cache re-usable outputs (e.g., transcripts) when possible.

## Safety & Compliance
- Add PII redaction and rights checks as policy gates before export/publish.
- Require human review for low-confidence or sensitive detections.
- Ensure audit logs are enabled for changes and runs.

## Testing & Promotion
- Dry-run with a representative asset; verify outputs and logs.
- Define success criteria (acceptance) and runbook for failures.
- Version and tag releases; use signed manifests for CI contract checks.

## Documentation Checklist
- [ ] Intent and expected outcomes
- [ ] Parameters and defaults explained
- [ ] Inputs/outputs examples and formats
- [ ] Guardrails (policies) and thresholds
- [ ] Cost/time expectations
- [ ] Failure modes and recovery steps

## Common Patterns
- QC Packs: Ingest → QC nodes → Report (policy: block on critical failures)
- Creator Packs: Ingest → ASR → LLM titles/hashtags → Gen thumbnails/B‑roll → Captions → Publish
- Education Packs: Ingest → ASR → Chapterize → (OCR) → Study pack → Export
- Legal Packs: Ingest → ASR+OCR → Privilege detect → Redact → Bates → Export
- Live Packs: Ingest.Live → ASR.Live + Scoreboard OCR → Detect highlights → Clip → SSAI + Events

