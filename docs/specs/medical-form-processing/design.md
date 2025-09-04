# Medical Form Processing — Design

## Architecture
- Form Type Classification: CNN/Transformer on page thumbnails; template mapping
- Zoning: template-defined regions for fields; fallback to learned layout (LayoutLM/Donut)
- OCR: Printed (Tesseract/PaddleOCR), Handwriting (CRNN/TrOCR) with medical vocabulary
- Checkboxes: blob/contour detection; proximity to label
- Validation: rules engine for formats, ranges, required sets; cross-field consistency
- Export: JSON/CSV; FHIR Bundle (Patient/Observation/MedicationStatement) optional

## Data Model
- `forms`(id, type, pages, status, created_at)
- `fields`(id, form_id, name, value, confidence, page, bbox)
- `issues`(id, form_id, code, message, severity)

## APIs
- POST /api/v1/medical/forms: create job (upload)
- GET /api/v1/medical/forms/{job_id}/status: status
- GET /api/v1/medical/forms/{form_id}/results: fields + issues
- POST /api/v1/medical/forms/{form_id}/export: JSON/CSV/FHIR

## Pipeline Template (High-Level)
Ingest → Classify → Zone → OCR (Printed/Handwriting) → Validate → Export

## Observability
- Metrics: fields/form, confidence histograms, validation failures, runtime/page
- Dashboards: per-template accuracy; error breakdown; retraining candidates

## Risks & Mitigations
- Handwriting variability → active learning loops; per-clinic templates; human-in-the-loop
- Template drift → dynamic layout models; versioned templates
