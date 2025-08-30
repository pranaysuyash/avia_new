# Platform Review — Findings Summary

- Date: 2025-08-30
- Scope: Consolidated findings from repo review covering backend APIs, Streamlit/React/React Native/Electron frontends, .kiro specs themes, and expansion opportunities. This document aggregates prior audits into a single, decision-ready brief.

**Executive Summary**
- Ambitious, feature-rich media platform with strong groundwork: transcription, analytics, collaboration, uploads, and multi-frontend coverage.
- Key gaps: API fragmentation (`/api` vs `/api/v1`), auth inconsistency, WebSocket endpoint drift, Electron queue service ambiguity, Expo mobile legacy paths.
- Product opportunity: education toolkit, provider hub (Replicate/FAL/OpenRouter), professional media supply chain (IMF/MXF/QC), rights/licensing, live/SSAI, and visual enrichment.
- Status: Demo/POC-ready with depth in many areas; requires consolidation and hardening for production.

**Architecture Snapshot (Backend)**
- Entrypoints: `api/app.py` (full router composition), `api/main.py`, `api/api_main.py`, `api/production_app.py`.
- Prefixes: mixed usage of `/api/...` and `/api/v1/...` across routers (`uploads` under `/api/v1`, analytics under `/api`, legacy transcription router under `/api/transcription`, cached under `/api/v1/transcription/cached`).
- GraphQL: Strawberry router present; dev playground available; client usage limited to web demo comps.
- WebSockets: enhanced router gated by `USE_ENHANCED_WEBSOCKET`; explicit WS at `/ws/processing/{client_id}`; several WS paths referenced in web lack confirmed handlers.

**Integration Status (Frontends)**
- Streamlit: Uses `api_client.py` + `api_wrappers.py`; generally aligned; depends on canonical auth route decision.
- React Web (Vite): Broad coverage of `/api/v1` endpoints; many WS references (collab, realtime, notifications, GraphQL) need validation; env config for `VITE_API_URL/WS` recommended.
- React Native: Mixed auth paths (`/api/v1/auth/*` and `/api/auth/*`); uses REST well; presigned uploads not leveraged; base URL/platform nuances present.
- Expo App (`mobile_app`): Uses legacy non-`v1` transcription endpoints (`/api/transcribe`, `/api/transcription/{id}`); likely mismatch with canonical API.
- Electron: Renderer integrates `/api/v1` extensively; queue monitor expects `http/ws://localhost:8001`—unclear if service is provided or should be on main API port.

**Issues & Risks**
- Prefix drift: inconsistent `/api` vs `/api/v1` usage across clients and routers → 404 risk and maintenance burden.
- Auth inconsistency: dual auth routers (`/api/v1/auth/*` and `/api/auth/*`); refresh unimplemented in `api/main.py`; clients mix both.
- WebSockets undefined: Several client-side WS URLs don’t map to clear server handlers; runtime failures likely.
- Multiple entrypoints: running the “wrong” app may yield missing endpoints.
- Scope sprawl: numerous advanced modules with uneven maturity and unclear E2E ownership.

**Strengths**
- Depth and breadth: uploads (presigned/multipart), cached transcription, analytics, TTS, VAD, hybrid summarization, entity linking; mobile/web/desktop surfaces.
- Infra signals: logging, Sentry scaffolding, rate-limiting hooks, CI/testing artifacts.
- Documentation: .kiro specs outline wide-ranging product/program tracks.

**Opportunities (New Value)**
- Education toolkit: lecture segmentation, study packs (flashcards/quizzes with rationales), OCR on frames, LMS export (LTI/SCORM), engagement analytics, accessibility QC.
- Provider hub for generative/editing: Replicate/FAL/OpenRouter adapters with routing, caching, cost/safety governance; image/video/audio editing tasks.
- Professional media supply chain: IMF/MXF parsing/validation, proxies/conform, EDL/AAF/XML roundtrip; QC (EBU R128/CALM, black/freeze/flash, VMAF/SSIM/PSNR).
- Rights/licensing & distribution: rights catalog, windows/territories/embargo, takedown workflows, platform packaging.
- Live/SSAI & brand safety: ingest (SRT/RTMP/HLS/DASH), live captions/translation, clipping/highlights, SSAI metadata, per-segment brand safety.
- Visual enrichment: frame OCR, logo/brand detection, product placement, object tracking; face privacy tiers; speaker–face linking.

**Quick Wins (Low Lift)**
- Frame OCR → index lower thirds/titles for search.
- Caption QC toolkit → timing, reading speed, overlap checks.
- Watermarked review links → per-viewer identifiers, expiry.
- Student toolkit v0 → time-coded notes, flashcards/quiz export (Anki/Notion).
- Provider hub MVP → thumbnails/B‑roll (Replicate/FAL), multi-model summaries (OpenRouter).
- Storage lifecycle policies UI → tiering and cost estimates.

**Strategic Initiatives (Multi-sprint)**
- Provider hub with governance (cost/latency telemetry, audit trails, model eval harness, safety/consent).
- Pro media supply chain and QC pack; NLE roundtrip; deliverable spec validation.
- Rights/licensing and monetization; usage metering and takedowns.
- Live ingest, clipping/highlights, SSAI metadata, brand safety.
- Legal hold, eDiscovery, forensic watermarking, content fingerprinting.
- Archive & FinOps: tiered storage, fixity, lifecycle policies, showback/chargeback.

**Recommended Next Steps (Engine/Integration)**
- Standardize API surface: choose `api/app.py` as canonical; standardize on `/api/v1` for public clients; alias/deprecate legacy.
- Reconcile auth: one scheme (prefer `/api/v1/auth/*`), implement refresh consistently, remove 501 placeholders.
- Publish WS matrix: definitive list of supported WS endpoints; align React web/electron to them; env-driven WS base.
- Client alignment: set `VITE_API_URL/WS`, unify RN/Expo base URLs and auth prefixes, decide Electron queue port.
- Add observability & guardrails: cost telemetry, quotas, caching; consent/watermark/mode flags for editing providers.

**Candidate Tasks (Execution-ready)**
- API consolidation
  - Alias `/api/*` → `/api/v1/*` where appropriate; update OpenAPI docs; write a deprecation note.
  - Implement `/api/v1/auth/refresh` and unify clients.
- WS reconciliation
  - Inventory and implement missing WS routes or update clients; publish WS endpoint doc.
- Client updates
  - React Web: set envs; fix GraphQL WS path; guard missing WS features.
  - React Native: switch all auth calls to `/api/v1/auth/*`; adopt presigned uploads for large files.
  - Expo: migrate transcription endpoints to `/api/v1/transcriptions` (or cached routes) and align exports/status.
  - Electron: route queue via API:8000 or document worker:8001; env-based base URLs.
- Quick wins
  - Frame OCR search integration; Caption QC; Student toolkit v0; Provider hub MVP (Replicate/OpenRouter).

**Traceability to Repo Docs**
- API integration audit: `API_INTEGRATION_AUDIT.md`.
- .kiro gaps & opportunities: `KIRO_TASKS_GAP_AUDIT.md` (expanded to education and provider integrations).
- Expansion plan (non-KIRO): `MEDIA_PLATFORM_EXPANSION_PLAN.md`.

If you want, I can turn the “Candidate Tasks” into a prioritized backlog with scope, owners, and acceptance criteria for the next sprint.

