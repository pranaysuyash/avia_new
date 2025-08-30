# Frame OCR Indexing — Design & Implementation Plan (No Code Changes)

- Owner: Backend, Web
- Status: Design approved by ADR 0001
- Goal: Extract text from video frames, index by timecode, and expose in search with time-jump.

## Objectives
- Enable search across burned-in text (titles/lower-thirds) for videos lacking transcripts.
- Keep v1 simple, batch-oriented, and cost-aware with feature flags and caps.

## Assumptions
- FFmpeg available for frame extraction; OCR service (Tesseract + OpenCV preprocess) feasible.
- Search/read APIs exist; can be extended to include an OCR source.

## Architecture
- Components
  - Frame Sampler: extracts frames at fixed interval (e.g., 1s) with maximum frame cap; optional keyframe mode next.
  - OCR Worker: preprocess (grayscale, threshold), run Tesseract, normalize text, compute confidence.
  - Indexer: write time-coded hits to persistence; expose via search.
  - Orchestrator: creates OCR jobs, tracks status, enforces caps and retries.

- Data Model
  - Table: `ocr_jobs`
    - `id`, `media_id`, `status` (queued|running|completed|failed|cancelled)
    - `sampling_mode` (interval/keyframe), `interval_s`, `max_frames`
    - `lang`, `frames_processed`, `chars_extracted`, `duration_ms`, `cost_cents`
    - `created_at`, `started_at`, `finished_at`, `error`
  - Table: `ocr_hits`
    - `id`, `media_id`, `t_start`, `t_end`
    - `text`, `confidence` (0–1), `lang`
    - Optional: `bbox` (x,y,w,h) if contour detection added later
    - `created_at`

- Indexing Strategy
  - v1: query `ocr_hits` directly with `ILIKE`/trigram for substring match; paginate by time.
  - v2: push to existing search index (if any) with `source=ocr` to unify results.

## API Surface (v1 proposal)
- `POST /api/v1/ocr/index/{media_id}`
  - Body: `{ sampling_mode?: 'interval'|'keyframe', interval_s?: number, lang?: string }`
  - Response: `{ job_id }`
- `GET /api/v1/ocr/index/{job_id}/status`
  - Response: job metadata + progress
- `GET /api/v1/ocr/results`
  - Query: `media_id`, `q` (text), `offset`, `limit`
  - Response: `{ hits: [{ t_start, t_end, text, confidence }], total }`
- Search integration (optional v1): extend existing `/api/v1/search` with `source=ocr` toggle

## Web UI
- Search panel: add OCR tab/filter; list results with snippet and timecode.
- Player integration: clicking result seeks to `t_start`.
- Admin: basic job monitoring (status list), optional retry/cancel.

## Sampling & Preprocessing
- Default: interval=1s, max_frames per media (e.g., 5k) to cap cost.
- Preprocess heuristics: grayscale → adaptive threshold; optional ROI (bottom third) for lower-thirds.
- Language: default English; allow override; detect later.

## Feature Flags & Limits
- Toggle per environment/team.
- Per-job caps: frames, duration, concurrency.
- Rate limits per user/team.

## Observability & Cost
- Telemetry: frames processed, OCR throughput, P50/P95 latency.
- Cost estimates per minute processed; budget alerts optional later.

## Privacy & Compliance
- Configurable retention for `ocr_hits`; keep text minimal.
- If policy requires, redact faces/regions before OCR (future).

## Verification
- Golden video with known lower-thirds → target >80% match; time-jump within ±0.5s.
- Load test across N assets with caps enforced; error handling (timeouts, partials).

## Risks & Mitigations
- Stylized/low-contrast text → preprocessing configs; report low-confidence hits.
- Cost overruns → frame caps, interval, nightly windows.
- Storage growth → TTL on hits, summarize long-form assets.

## Milestones
- Week 1: POC pipeline; schema finalized; API mocked; metrics defined.
- Week 2: Batch orchestration; APIs; basic web surfacing; telemetry; docs.

