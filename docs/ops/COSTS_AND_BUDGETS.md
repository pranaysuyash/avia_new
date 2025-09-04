# Costs & Budgets — Defaults, Caps, and Envelopes

This document defines default caps/quotas and expected cost envelopes per pipeline template and feature track.

## Defaults & Quotas (Per Tenant)
- OCR frames per asset: max 5,000 (interval sampling) — override by policy
- ASR minutes per day: max 600 min/day — burst 2x for 1 hour
- Gen tasks (thumbnails/B‑roll): max 50 tasks/day — per provider quotas applied
- Live highlights: max 3 concurrent streams — 60 min DVR window
- Storage retention for derived artifacts: 30 days (reports/packs), 90 days (OCR hits)

## Cost Envelopes (Indicative)
- Frame OCR Indexing (30 min asset)
  - Sampling 1 fps → ~1,800 frames; CPU OCR @ $0.001/frame → ~$1.80
  - With preprocessing and retries → +15%
- Creator Publish Pack (one asset, 2 platforms)
  - ASR (30 min) @ $0.006/min → $0.18; LLM summary @ $0.05; thumbnails (2) @ $0.05 each; captions burn-in negligible
  - Total ~$0.33 + egress/storage
- Education Lecture Pack (60 min)
  - ASR (60 min) $0.36; slide OCR sampling 0.5 fps ~1,800 frames → ~$1.80; LLM study pack $0.10
  - Total ~$2.26 + export costs
- Legal eDiscovery Pack (per hour)
  - ASR (60 min) $0.36; OCR 1 fps 3,600 frames → $3.60; redaction compute $0.20; export $0.05
  - Total ~$4.21 + storage
- Live/SSAI Highlights (per stream hour)
  - ASR.Live $0.50; OCR scoreboard negligible; detection compute $0.30; clips egress $0.40
  - Total ~$1.20 + egress

## Budgeting & Alerts
- Soft budget per tenant per month (default $250); hard cap $500 with grace policies
- Alerts at 50%/80%/100%; drilldowns by workflow/template
- Off-peak scheduling discounts: -20% during 00:00–06:00 local time

## Controls & Governance
- Preflight cost simulation in pipeline inspector (P50/P95 ranges)
- Require approval for runs > 2x daily average cost
- Deny list for providers/models by policy; cost-per-call thresholds

