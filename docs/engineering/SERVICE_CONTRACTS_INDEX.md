# Service Contracts Index — Endpoints ↔ Pydantic Models

This index lists key endpoints and the request/response Pydantic models to standardize contracts.

## Pipeline & Templates
- POST /api/v1/pipelines/compile → req: CompileRequest, res: CompileResponse
- POST /api/v1/pipelines/run → req: RunRequest, res: RunAccepted
- GET /api/v1/pipelines/runs/{run_id} → res: RunDetail (graph, node execs)
- Templates CRUD → Template, TemplateVersion

## Frame OCR Indexing
- POST /api/v1/ocr/index/{media_id} → OCRJobCreate
- GET /api/v1/ocr/index/{job_id}/status → OCRJobStatus
- GET /api/v1/ocr/results → OCRResults (total, hits[OCRHit])

## Caption QC
- POST /api/v1/captions/qc/validate → CaptionSegments | CaptionFileUpload; res: QCResults (issues[], summary)
- POST /api/v1/captions/qc/report → QCReportRequest; res: ReportLocation

## Education Study Packs
- POST /api/v1/education/study-packs → StudyPackCreate; res: JobAccepted
- GET /status → JobStatus; POST /export/{target} → ExportAccepted

## Creator Publish Packs
- POST /api/v1/publish/packs/creator → CreatorPackCreate; res: JobAccepted
- GET /status → JobStatus; GET /assets → AssetsList; POST /post → PostAccepted

## Live/SSAI & Highlights
- POST /api/v1/live/streams/{stream_id}/highlights/detect → DetectRequest; res: Accepted
- GET /highlights → HighlightEvents (events[])
- GET /clips → ClipList; POST /ssai/publish → SSAIPublishRequest; res: Accepted

## Medical Form Processing
- POST /api/v1/medical/forms → MedicalFormJobCreate; res: JobAccepted
- GET /status → JobStatus; GET /results → MedicalFormResults (fields[], issues[])
- POST /export → ExportRequest; res: ReportLocation
  - Schemas: common [JobAccepted](../schemas/common/JobAccepted.schema.json), [JobStatus](../schemas/common/JobStatus.schema.json), [ExportRequest](../schemas/common/ExportRequest.schema.json), [ReportLocation](../schemas/common/ReportLocation.schema.json), domain [MedicalFormResults](../schemas/medical-form-processing/MedicalFormResults.schema.json)

## Invoice Processing Automation
- POST /api/v1/invoices → InvoiceJobCreate; res: JobAccepted
- GET /status → JobStatus; GET /results → InvoiceResults (header, lines[])
- POST /export → ExportRequest; res: ExportAccepted/ReportLocation
  - Schemas: common [JobAccepted](../schemas/common/JobAccepted.schema.json), [JobStatus](../schemas/common/JobStatus.schema.json), [ExportRequest](../schemas/common/ExportRequest.schema.json), [ReportLocation](../schemas/common/ReportLocation.schema.json), domain [InvoiceResults](../schemas/invoice-processing-automation/InvoiceResults.schema.json)

## ID Card Reader
- POST /api/v1/ids/parse → IDParseJobCreate; res: JobAccepted
- GET /api/v1/ids/{id} → IDParseResult (fields, fraud flags, assets)
- POST /verify-selfie → SelfieVerifyRequest; res: SimilarityScore
  - Schemas: common [JobAccepted](../schemas/common/JobAccepted.schema.json), [JobStatus](../schemas/common/JobStatus.schema.json); domain [IDParseResult](../schemas/id-card-reader/IDParseResult.schema.json)

Note: Define these models in a shared `contracts` package (pydantic v2), and use them consistently across FastAPI handlers and client SDKs. Auto-generate OpenAPI and client stubs where useful.
