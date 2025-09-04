# Pipeline Templates — Acceptance Criteria

This document defines acceptance for each example template: inputs/outputs, happy paths, and failure handling.

## QC Pack — Broadcast Basics (QC_PACK.json)
- Inputs: media file (video with audio)
- Outputs: QC report (PDF), per-check structured results
- Happy Path:
  - Flash/black/PSE/loudness checks run and produce results
  - Policy gate blocks export when PSE fails; otherwise report generated
- Failure Handling:
  - Unsupported codec → error with guidance
  - Analysis timeout → retry once; mark check as inconclusive with warning

## Creator Publish Pack — Shorts/Reels (CREATOR_PUBLISH_PACK.json)
- Inputs: source media
- Outputs: social-ready assets (captioned video variants, thumbnails), titles/hashtags
- Happy Path:
  - ASR → summary → B‑roll/thumbnail → caption burn-in → social pack export
  - Platforms list honored; assets named per platform
- Failure Handling:
  - Provider failure (B‑roll/thumbnail) → retry/fallback style; continue with partial outputs
  - Caption burn-in off → produce captions as sidecar

## Education — Lecture to Study Pack (EDUCATION_LECTURE_PACK.json)
- Inputs: lecture media (slides/whiteboard optional)
- Outputs: study pack (flashcards/quizzes), chapters, exports (Anki/Notion)
- Happy Path:
  - ASR → chapterize → (optional) frame OCR → LLM study pack → export
- Failure Handling:
  - OCR disabled/unavailable → proceed with transcript only
  - Export target unreachable → produce local export; log retry instructions

## Legal — eDiscovery Production Pack (LEGAL_EDISCOVERY_PACK.json)
- Inputs: case media assets
- Outputs: redacted, Bates-stamped production set (TIFF/PDF), case timeline
- Happy Path:
  - ASR + OCR → privilege detection → redaction → Bates → export
  - Policy requires human review for privilege hits above threshold
- Failure Handling:
  - Privilege detection offline → require manual review; block export
  - Bates stamp collision → increment suffix; log resolution

## Live/SSAI — Highlights & Metadata Pack (LIVE_HIGHLIGHTS_PACK.json)
- Inputs: live stream (HLS/RTMP) with DVR window
- Outputs: highlight clips, SSAI metadata/events, WS events
- Happy Path:
  - Ingest → ASR + scoreboard OCR → highlight detection → clip → SSAI publish + events
- Failure Handling:
  - Latency budget breach → warn; drop lower-priority features (e.g., ASR hints)
  - Clip generation error → retry with shorter window; log failure with timestamps

