# ID Card Reader System — Requirements

## Intent
Extract structured data from IDs (driver's licenses, passports, employee badges) and detect basic fraud.

## Personas
- Security, government, HR onboarding, KYC/compliance

## User Stories & Acceptance
1) Field extraction
- As an operator, I scan an ID and get name, DOB, ID#, expiry, issuing authority.
- Acceptance: ≥99% on MRZ/AAMVA fields; confidence returned.
2) Fraud checks
- As security, I get alerts for mismatched checksums, tampered photo regions, expired IDs.
- Acceptance: checksum/expiry enforcement; tamper heuristics with manual review.

## Functional Requirements
- Inputs: Photos/scans; front/back for DL; MRZ for passports
- Outputs: JSON fields; face crop; barcodes/MRZ parsed
- Standards: AAMVA (DL/ID), ICAO 9303 (MRZ)
- Fraud: checksum, font/layout sanity, glare/blur warnings; photo vs. selfie (v2)

## Non‑Functional
- Latency P95 < 3s per ID (local), < 8s (remote); encrypt crops; audit
