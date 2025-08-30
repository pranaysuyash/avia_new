# ADR 0001 — Select Frame OCR Indexing as First Quick Win

- Date: 2025-08-30
- Status: Accepted

## Context
Multiple quick wins were considered to deliver immediate value while we consolidate the API surface: Caption QC (web-only), Frame OCR Indexing, and Provider Hub MVP (Replicate/OpenRouter). We need to pick one to lead with.

## Options Considered
- A) Caption QC Toolkit (client-only)
- B) Frame OCR Indexing (batch server + search + light UI)
- C) Provider Hub MVP (model adapters + governance)

## Decision
Choose B) Frame OCR Indexing as the first initiative.

## Rationale
- High user/business value: unlocks search in non-transcribed/archival footage; differentiates product.
- Clear scope and integration: reuse FFmpeg/ocr/search patterns; batch model with low operational risk.
- Builds toward visual enrichment roadmap (logo/brand detection, product placement, object tracking).
- Caption QC remains a close second; we will pick it up right after initial OCR delivery.

## Consequences
- Positive: Quick demoable value; search expands immediately; limited client changes.
- Negative: Requires compute budget for OCR; accuracy varies with stylized text; needs caps.
- Rollback: Can disable via feature flag and retain OCR text for already-processed assets; no client-breaking changes.

## Follow-up
- Implement design in FRAME_OCR_INDEXING_DESIGN.md
- Add tasks to backlog per team; define acceptance criteria and metrics.

