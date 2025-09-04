# Runbook — OCR Accuracy Regression

Severity: SEV-3 (quality degraded)

## Symptoms
- Drop in OCR precision/recall on golden dataset
- Increased user reports of missed/incorrect lower-thirds

## Immediate Actions
1) Triage
- Compare model/version in recent runs; check preprocessing changes
- Re-run golden set; compute deltas; inspect samples

2) Mitigation
- Roll back to previous OCR/params; pin model version
- Increase preprocessing (threshold/contrast) temporarily
- Raise confidence threshold; flag low-confidence for review

3) Communication
- Post status to stakeholders; ETA for rollback/hotfix

## Root Cause & Follow-up
- Add canary jobs for new models/params; gate rollout on SLOs
- Expand golden dataset coverage (fonts, languages)
- Capture per-language metrics; route by language

## Dashboards & Queries
- OCR accuracy over time, confidence distributions, per-language breakdown

