# Contract Signature & Seal Extraction — Design

## Architecture
- Preprocess: denoise/binarize; deskew; contrast enhancement
- Detection:
  - Signature: contour/texture features + CNN classifier (signature vs. non‑signature)
  - Seal: shape (circular/emblem) + text ring detection (Hough + OCR)
- Postprocess: merge overlapping bboxes; filter by size/aspect
- OCR context (optional): associate parties/names to pages
- Verification (v2): Siamese network embeddings vs. reference signature; similarity threshold

## Data Model
- `signature_hits`(id, doc_id, page, bbox, confidence, crop_url, created_at)
- `seal_hits`(id, doc_id, page, bbox, confidence, type, crop_url)
- `doc_jobs`(id, status, pages, runtime_ms, error)

## APIs (see API.yaml)
- POST /api/v1/docs/signatures/detect — create job
- GET /api/v1/docs/signatures/{job_id}/status — job status
- GET /api/v1/docs/signatures/{doc_id}/results — hits
- POST /api/v1/docs/signatures/verify — optional reference comparison (v2)

## Pipeline Template (high-level)
- Ingest → Preprocess → SignatureDetect + SealDetect → Merge → (Verify) → Export

## Observability
- Metrics: hits per doc, avg confidence, runtime/page; precision/recall on golden sets
- Logs: sample crops for auditing (secure storage)

## Risks & Mitigations
- Stylized signatures → expand training set; adjustable thresholds; human review queue
- Seals with low contrast → adaptive thresholding; local contrast normalization

