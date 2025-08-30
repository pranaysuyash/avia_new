# Task Log — Frame OCR Indexing

- Title: Frame OCR Indexing (Quick Win)
- Date: 2025-08-30
- Owners: Backend, Web, PM (to be assigned)

- Context:
  Extract text from video frames (burned-in titles/lower-thirds) and index by timecode to enable search and time-jump across media that lacks transcripts. Identified as a high-value quick win in prior audits.

- Scope:
  - In scope:
    - Frame extraction (keyframe or interval sampling)
    - OCR with preprocessing, text normalization
    - Store time-coded OCR hits and index for search
    - Basic API for start/status/results (or integrate into existing search endpoints)
    - Web UI: show OCR matches in search results with time-jump
  - Out of scope:
    - Full visual moderation/policy engines
    - Complex bounding-box review UI; advanced layout analysis
    - Realtime OCR (batch only for now)

- Plan / Steps:
  1) Define schema for OCR jobs and hits; decide indexing approach (augment existing search vs. dedicated table + join)
  2) Specify sampling strategy (keyframes vs. N-second interval) and preprocessing pipeline
  3) Define API surface: start job, status, fetch results; or piggyback on search with a source filter
  4) Implement batch worker design (can reuse existing queue infra); set caps and throttles
  5) Add Web UI surfacing: search panel lists OCR matches; click jumps to timecode
  6) Add telemetry (cost/latency), feature flags, and retention policy for OCR text
  7) Verification with a golden video and load test on sample library

- Findings (assumptions to validate):
  - FFmpeg utilities are available for frame extraction; OCR endpoint exists in backend; search endpoints present
  - Strawberry GraphQL optional; REST sufficient for v1

- Decisions (to ratify via ADR 0001):
  - Start with interval sampling (e.g., 1s) with max frame cap per asset; add keyframe mode later
  - Use Tesseract + OpenCV preprocessing (grayscale/threshold) for v1; evaluate improvements post-MVP
  - Index by (media_id, t_start, t_end, text, confidence, lang)
  - Surface via REST; integrate into existing search facade with a `source=ocr` filter

- Actions (no code unless approved):
  - Draft schema and endpoints (see FRAME_OCR_INDEXING_DESIGN.md)
  - Prepare WS_ENDPOINTS.md updates if any streaming views are added (not planned for v1)

- Verification Plan:
  - Accuracy: >80% of expected strings on golden video; time-jump accuracy ±0.5s
  - Performance: P95 job completion under threshold on sample length; configurable caps
  - Errors: recoverable retries; job status transitions logged; user-visible error states

- Risks / Mitigations:
  - Cost/compute spikes → caps, throttles, batch windows
  - OCR accuracy on stylized fonts → allow preprocess config; capture confidence scores
  - Storage growth from hits → retention policies; summarize when needed

- Follow-ups / Next Tasks:
  - Add multi-language OCR support and auto language detection
  - Add position-based classification (title vs. lower-third) for relevance boosts
  - Optional review queue UI for low-confidence hits

