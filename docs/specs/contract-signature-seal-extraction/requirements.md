# Contract Signature & Seal Extraction — Requirements

## Intent
Extract and verify signatures, notary seals, and legal stamps from scanned or photographed documents; provide presence checks, crops, and optional authenticity signals.

## Personas
- Paralegals, attorneys, court clerks, compliance officers

## User Stories & Acceptance
1) Detect signatures and notary seals
- As a paralegal, I upload a PDF and receive signature and seal locations with confidence.
- Acceptance: ≥95% presence detection on golden set; <1% FP on non‑signature marks.
2) Export crops for exhibits
- As an attorney, I export cropped signature images for exhibits.
- Acceptance: Crops include entire signature with 10–20px margin.
3) Batch processing
- As a clerk, I process envelopes of contracts with a summary report of missing signatures.
- Acceptance: Per‑doc summary with pass/fail; runtime within SLA.
4) Optional verification (v2)
- As compliance, I compare signatures to a reference and get a similarity score.
- Acceptance: Threshold policy configurable; clear disclaimers.

## Functional Requirements
- Inputs: Images (JPEG/PNG), PDFs (scanned), multipage; 300 DPI recommended
- Outputs: JSON (bboxes, confidence, page), PNG crops, summary report
- Detection: signature vs. non‑signature marks; notary seal (circular/embossed) detection
- OCR context (optional) to link names/parties and pages
- Batch API; idempotent runs; retries/backoff; audit logs

## Non‑Functional
- HIPAA/GDPR: encryption at rest, access logs, retention policies
- Performance: P95 < 15s per 10‑page doc (CPU baseline); scalable workers
- Accuracy monitoring: precision/recall dashboards; golden set evaluation

