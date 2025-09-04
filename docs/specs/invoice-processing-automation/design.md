# Invoice Processing Automation — Design

## Architecture
- Classification: invoice vs. receipt; vendor template hints
- OCR: printed text; detect currency; normalize numbers
- Table Extraction: detect table grids or use structure prediction (TableNet/DeepDeSRT)
- Header Parsing: regex/ML for invoice#/PO/date; vendor master matching (fuzzy)
- Validation: subtotal sum, tax rates, total=Σlines+tax; duplicate detection via hash
- Export: JSON/CSV; ERP/AP (NetSuite/SAP/QuickBooks) connectors

## Data Model
- `invoices`(id, vendor_id?, number, date, subtotal, tax, total, currency, status)
- `invoice_lines`(id, invoice_id, line_no, desc, qty, unit_price, amount)
- `issues`(id, invoice_id, code, message, severity)

## APIs
- POST /api/v1/invoices: create job (upload)
- GET /api/v1/invoices/{job_id}/status
- GET /api/v1/invoices/{inv_id}/results
- POST /api/v1/invoices/{inv_id}/export (csv/xlsx/connector)

## Observability
- Accuracy by vendor/template; line extraction coverage; validation failure rates
- Costs per invoice; runtime P50/P95

## Risks & Mitigations
- Varied templates → template library + ML; vendor-specific hints
- Poor scans → denoise/deskew; request re‑upload for low quality
