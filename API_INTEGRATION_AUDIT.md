# API Integration Audit — Streamlit, React Web, React Native, Electron

- Date: 2025-08-30
- Scope: Verify backend APIs implemented to date and their integration across Streamlit, React (web), React Native (mobile), and Electron (desktop) frontends. No code changes performed; this is a documentation audit with concrete findings and next steps.

**Summary**

- The backend exposes a rich FastAPI surface with both versioned (`/api/v1/...`) and legacy (`/api/...`) routes composed in `api/app.py` and additional minimal apps in `api/main.py` and `api/api_main.py`.
- React Web and Electron integrate broadly with the `/api/v1` routes (uploads, auth, analytics, collaboration, advanced features) and some WebSocket flows. Streamlit integrates via `api_client.py` and wrapper modules, mapping to many `/api/v1` and `/api` endpoints. React Native (mobile) integrates partially; Expo `mobile_app` still calls legacy, non-`v1` transcription endpoints and mismatched paths.
- Key discrepancies: mixed endpoint prefixes (`/api` vs `/api/v1`), mobile and Expo using legacy transcription routes, several WebSocket URLs referenced by web that are not clearly implemented, and a desktop queue monitor pointed at port 8001.


**Backend Overview**

- App composition: `api/app.py` (full router composition) integrates most features under `/api` and `/api/v1`. Other entrypoints exist (`api/main.py`, `api/api_main.py`, `api/production_app.py`) with different scopes.
- Notable routers and prefixes:
  - `uploads`: `/api/v1/uploads/...` via `api/endpoints/upload.py`.
  - `transcription_cached`: `/api/v1/transcription/cached/...` via `api/endpoints/transcription_cached.py`.
  - `transcription` (legacy): `/api/transcription/...` via `api/endpoints/transcription.py` (mounted under `/api` in `api/app.py`).
  - Auth: both `/api/v1/auth/...` (legacy router) and `/api/auth/...` (JWT auth endpoints) are included in `api/app.py`.
  - Many feature routers under `/api/v1`: realtime transcription, TTS, emotion/sentiment, hybrid summarization, VAD, analytics, etc. See `api/app.py` includes.
  - GraphQL: Strawberry-based GraphQL router via `api/graphql_api.py`; GraphQL endpoint included in `api/app.py` and `api/main.py` (with dev-only playground).
  - WebSocket: enhanced WebSocket router included under `/api/v1` when `USE_ENHANCED_WEBSOCKET=true`; additional WS in `api/enterprise_endpoints.py` (`/ws/processing/{client_id}`).


**Frontend Overview**

- Streamlit: `app.py` uses `api_wrappers.py` and `api_client.py` to call APIs (auth, uploads, transcription, analytics, TTS, etc.). Falls back to local modules if wrappers unavailable.
- React Web: `frontend/` (Vite) with service modules and hooks calling `/api/v1` for uploads, analytics, search, real‑time, entity linking, etc. WebSocket helpers present.
- React Native: `mobile/` integrates many `/api/v1` endpoints via `mobile/src/services/apiClient.ts` and `mobile/src/utils/mobile_api_client.js`; also has a separate `mobile_auth_service.js` hitting `/api/auth/*`.
- Expo App: `mobile_app/` uses `TranscriptionService.js` and `SyncService.js` with legacy, non‑versioned transcription routes like `/api/transcribe` and `/api/transcription/...`.
- Electron: `desktop_app/` main process monitors API health and dev servers; renderer `src/renderer/src/services/apiClient.ts` calls a wide set of `/api/v1` enterprise and core endpoints.


**Integration Mapping (by capability)**

- Auth
  - Backend: `/api/v1/auth/...` and `/api/auth/...` mounted in `api/app.py`.
  - Streamlit: `api_client.py` (`/api/v1/auth/login`, `/api/v1/auth/me`).
  - React Web: uses `/api/v1/...` through shared `apiService` patterns.
  - React Native: mixed usage: `mobile/src/services/apiClient.ts` uses `/api/v1/auth/*`, but `mobile/src/services/mobile_auth_service.js` and token refresh in `mobile/src/utils/mobile_api_client.js` use `/api/auth/*`.
  - Electron: renderer `apiClient.ts` uses `/api/v1/auth/*`.
  - Discrepancy: mixed prefixes across mobile; ensure both sets are supported or consolidate to one scheme.

- Uploads (Presigned + Multipart)
  - Backend: `/api/v1/uploads/presigned`, `/api/v1/uploads/multipart`, etc. (`api/endpoints/upload.py`).
  - Streamlit: uses `api_client.py` indirectly through wrappers when uploading via media/stt flows.
  - React Web: `frontend/src/hooks/usePresignedUpload.ts` integrates all upload flows.
  - React Native: no presigned upload usage found; uses direct multipart to `/api/v1/transcriptions` in `mobile/src/services/apiClient.ts`.
  - Electron: renderer uses `/api/v1` endpoints but no explicit presigned flow found.
  - Note: Consider aligning mobile to presigned for large files.

- Transcription (Batch CRUD)
  - Backend: `/api/transcriptions` CRUD in `api/main.py` (user‑scoped) and multiple routers in `api/app.py`, plus cached endpoints `/api/v1/transcription/cached/...`.
  - Streamlit: `api_wrappers.STTWrapper` via `api_client.py` (create/fetch result semantics).
  - React Web: services for cached transcription in `frontend/src/services/cacheService.ts` (`/api/v1/transcription/cached/...`). General transcription list/detail appear under analytics/UX components.
  - React Native: `mobile/src/services/apiClient.ts` includes `/api/v1/transcriptions` list/detail and upload.
  - Expo App: `mobile_app/src/services/TranscriptionService.js` uses legacy non‑`v1` paths: `/api/transcribe`, `/api/transcription/{id}`, `/api/transcriptions`.
  - Discrepancy: Expo’s legacy paths diverge from `/api/v1` and backend pluralization; risks 404s unless legacy routers remain mounted.

- Real‑Time Transcription and Collaboration (WebSocket)
  - Backend: WS via enhanced router under `/api/v1` (see `api/app.py`). Explicit WS: `api/enterprise_endpoints.py` at `/ws/processing/{client_id}`. GraphQL subscriptions available via Strawberry.
  - React Web: numerous WS URLs referenced, e.g. `/api/v1/realtime-transcription/ws/{sessionId}`, `/api/v1/collaboration/ws/{...}`, `/api/translation/stream`, `/api/graphql/ws`, `/api/v1/notifications/ws`, `/api/distributed/monitor`, `/ws/processing`.
  - Streamlit: no direct WS in main app; uses synchronous flows.
  - React Native: limited WS usage; primarily REST.
  - Electron: queue WS in renderer (`ws://localhost:8001/api/queue/ws`).
  - Discrepancy: Several WS URLs referenced in web don’t have clear corresponding handlers in `api/` (only a subset found). Electron expects a worker at port 8001 for queue WS; confirm existence.

- Analytics, Search, Insights
  - Backend: multiple routers in `api/endpoints` (analytics, search, content insights) mounted in `api/app.py`.
  - Streamlit: uses `api_client.py` to generate reports and fetch metrics (via admin and analytics UIs).
  - React Web: `frontend/src/api/analytics.ts`, `frontend/src/api/search.ts`, components consume `/api/v1/...` routes.
  - React Native: `mobile/src/api/analytics.ts` and services call `/api/v1/analytics/...`.
  - Electron: renderer `apiClient.ts` integrates `/api/v1/analytics/...`.
  - Status: Broadly integrated across web, desktop, partial mobile.

- Entity Linking and NER
  - Backend: NER router (`api/endpoints/ner.py`), entity linking (`cross_provider_entity_linking.py`), entity extraction APIs.
  - React Web: components under `frontend/src/components/entity/*` use `/api/v1/entity-linking/*`.
  - Streamlit: uses `ner_basic` and `ner_advanced` via `api_wrappers`.
  - React Native: limited direct linking; some NER present via transcription displays.
  - Electron: renderer integrates collaboration/annotations more than linking.

- TTS, Audio Enhancement, VAD, Hybrid Summarization, Emotion/Sentiment
  - Backend: routers mounted with `/api/v1` in `api/app.py`.
  - React Web: `frontend/src/api/*` modules integrate these (`realTimeTranscription.ts`, `hybridSummarization.ts`, `emotionSentimentDetection.ts`).
  - React Native: counterparts under `mobile/src/api/*` exist and call `/api/v1`.
  - Streamlit: exposed via `api_wrappers.TTSWrapper` and advanced processing UI.
  - Electron: limited direct use; some analytics and rendering.

- GraphQL
  - Backend: Strawberry GraphQL in `api/graphql_api.py`; router included in `api/app.py` (plus dev playground in `api/main.py`).
  - React Web: `GraphQLSubscriptionManager` present and used in `App_full.tsx`/`App_complex.tsx`.
  - React Native, Electron, Streamlit: no direct GraphQL client usage found.


**Key Discrepancies and Risks**

- Endpoint prefix drift
  - Symptom: Both `/api/...` and `/api/v1/...` exist and are used inconsistently across clients (especially mobile).
  - Impact: Higher risk of 404s or hitting different auth flows; harder to maintain.
  - Recommendation: Standardize on `/api/v1` for all public clients. Keep `/api` routed internally or deprecate with redirects. Provide a thin compatibility layer if needed.

- Expo mobile legacy transcription routes
  - Symptom: `mobile_app/src/services/TranscriptionService.js` uses `/api/transcribe`, `/api/transcription/{id}`, and `/api/transcriptions` (singular/plural mismatch and no `/v1`).
  - Impact: Likely 404/501 against the current composition unless legacy app is the server.
  - Recommendation: Update to `/api/v1/transcriptions` CRUD and `/api/v1/transcription/cached/*` where applicable. Align export/status paths; ensure upload uses presigned or supported multipart.

- Mixed auth endpoints in mobile
  - Symptom: `mobile/src/services/apiClient.ts` calls `/api/v1/auth/*` while `mobile/src/services/mobile_auth_service.js` and token refresh use `/api/auth/*`.
  - Impact: Inconsistent token formats/claims and refresh behavior; refresh in `api/main.py` returns 501, while `api/endpoints/auth_endpoints.py` supports `/api/auth/refresh`.
  - Recommendation: Consolidate to a single auth scheme (prefer `/api/v1/auth/*` or keep `/api/auth/*` if that’s the authoritative JWT service) and ensure refresh flow is implemented and used consistently.

- WebSocket endpoints coverage
  - Symptom: Web references several WS URLs that aren’t obviously implemented (e.g., `/api/distributed/monitor`, `/api/v1/collaboration/ws`, `/api/v1/notifications/ws`, `/api/graphql/ws`). Only a subset is present in `api/`.
  - Impact: Runtime connection failures and degraded UX for realtime features.
  - Recommendation: Inventory WS routes in code and either implement missing handlers or update the web client to match available endpoints. Document expected WS base URL via envs (`VITE_WS_URL`).

- Desktop queue service at port 8001
  - Symptom: Electron renderer points at `http://localhost:8001/api/queue/...` and `ws://localhost:8001/api/queue/ws`.
  - Impact: Requires an auxiliary service; unclear if it’s provisioned. Backend `api/endpoints/queue.py` mounts under `/api`, but on what port?
  - Recommendation: Either route queue endpoints through the main API port (8000) or document/launch the queue worker on 8001 in desktop startup.

- Multiple backend entrypoints
  - Symptom: `api/main.py`, `api/app.py`, `api/api_main.py`, and `api/production_app.py` exist with different router sets.
  - Impact: Clients may point at an API process that lacks expected routes (e.g., `api/main.py` includes fewer routers).
  - Recommendation: Define the canonical server (e.g., `api/app.py`) and ensure all clients target it. Remove or clearly mark minimal apps as test‑only.


**Actionable Next Steps**

- Standardize client base URLs and prefixes
  - React Web: confirm `VITE_API_URL` and `VITE_WS_URL` in `.env` point to the canonical API.
  - React Native: unify on `/api/v1` routes; adjust `mobile_auth_service.js` and `mobile_api_client.js` refresh path to the chosen auth scheme.
  - Expo App: migrate `TranscriptionService.js` to `/api/v1/transcriptions` and cached endpoints; remove legacy paths.
  - Electron: confirm queue API lives on 8000 or bundle/start a worker on 8001; update URLs accordingly.

- Reconcile auth implementations
  - Choose one auth router as source of truth. Ensure login, me, refresh, logout are consistent across all clients. Remove or alias duplicates.

- WebSocket alignment
  - Publish a definitive list of WS endpoints supported by the backend and update `frontend/src/*` to match. Provide env‑configurable WS base.

- Documentation and sanity checks
  - Publish a simple “API surface vs client usage” matrix in repo docs. Add integration tests or smoke scripts per client that hit key endpoints and WS connections.


**Reference Pointers (non‑exhaustive)**

- Backend
  - Routers: `api/app.py`, `api/main.py`, `api/api_main.py`, `api/endpoints/*`, `api/graphql_api.py`.
  - Transcription (cached): `api/endpoints/transcription_cached.py`.
  - Uploads: `api/endpoints/upload.py`.
  - WebSocket samples: `api/enterprise_endpoints.py`.

- Streamlit
  - App: `app.py`.
  - Client/wrappers: `api_client.py`, `api_wrappers.py`.

- React Web
  - Services: `frontend/src/services/api.ts`, `frontend/src/services/cacheService.ts`.
  - APIs: `frontend/src/api/*` (analytics, search, realtime, emotion, hybrid summarization).
  - WS: `frontend/src/services/websocketManager.ts`, `frontend/src/hooks/useWebSocket.ts` and various components.

- React Native
  - Client: `mobile/src/utils/mobile_api_client.js`.
  - Services/APIs: `mobile/src/services/apiClient.ts`, `mobile/src/services/mobile_auth_service.js`, `mobile/src/api/*`.

- Expo App
  - Services: `mobile_app/src/services/TranscriptionService.js`, `mobile_app/src/services/SyncService.js`.

- Electron
  - Main: `desktop_app/src/main.js` (health checks), `desktop_app/src/main_fixed.js`.
  - Renderer API: `desktop_app/src/renderer/src/services/apiClient.ts`.


**Verification Status (high level)**

- Streamlit: Integrated to many core APIs via wrappers; generally aligned with `/api/v1` usage through `api_client.py`.
- React Web: Broad coverage of `/api/v1` endpoints; several WS URLs should be validated against backend availability.
- React Native: Partial coverage on `/api/v1`; mixed auth paths; presigned uploads not used.
- Electron: Broad REST coverage against `/api/v1`; queue service assumes port 8001.


If you want, I can convert this audit into a concrete checklist per team (web, mobile, desktop) with exact file line references to change and an ordering for implementation.

