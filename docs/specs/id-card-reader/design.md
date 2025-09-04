# ID Card Reader System — Design

## Architecture
- Detection & Alignment: detect card edges; perspective correct; glare/blur scoring
- Zones:
  - MRZ (passports): segment lines; parse checksums; field mapping
  - AAMVA PDF417 (DL): decode barcode; cross-check with printed OCR
- OCR: printed fields; face region crop; optional selfie compare (v2)
- Validation: standard checksums, expiry/date validation, issuing authority tables

## Data Model
- `ids`(id, type, issuing_country/state, number, name, dob, expiry, authority, status)
- `fraud_flags`(id, code, message, severity)
- `assets`(id, parent_id, kind, url)

## APIs
- POST /api/v1/ids/parse (upload front/back)
- GET /api/v1/ids/{id}
- POST /api/v1/ids/{id}/verify-selfie (v2)

## Observability
- Parse success rates by type; checksum failure rate; glare/blur scores; latency

## Risks & Mitigations
- Low quality captures → guided capture UX; live glare/edge hints; quality gates
