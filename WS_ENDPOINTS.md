# WebSocket Endpoints Matrix

Authoritative mapping of WebSocket (WS) routes referenced by clients vs. implemented on the server.

Legend
- Status: Implemented | Likely | Unknown | Not Implemented
- Action: Verify | Implement | Update Client | Remove/Flag

Client References (from frontend code)
- GraphQL subscriptions
  - Client: `frontend/src/components/graphql/GraphQLSubscriptionManager.tsx`
  - Path: `ws://<WS_BASE>/api/graphql/ws` (hardcoded)
  - Status: Unknown (Strawberry commonly upgrades on `/api/graphql`)
  - Action: Verify actual mount; update to `.../api/graphql` and env-drive base

- Realtime Transcription
  - Client: `frontend/src/components/transcription/RealTimeTranscription.tsx`
  - Path: `ws://<WS_BASE>/api/v1/realtime-transcription/ws/{sessionId}`
  - Status: Unknown (no direct handler located in API scan)
  - Action: Verify/Implement or flag in UI

- Collaboration
  - Client: `frontend/src/components/collaboration/CollaborativeEditor.tsx`
  - Path: `ws://<WS_BASE>/api/v1/collaboration/ws`
  - Status: Unknown
  - Action: Verify/Implement or flag in UI

- Notifications
  - Client: `frontend/src/components/notifications/NotificationCenter.tsx`
  - Path: `ws://<WS_BASE>/api/v1/notifications/ws`
  - Status: Unknown
  - Action: Verify/Implement or flag in UI

- Transcript Collaboration (alt path)
  - Client: `frontend/src/components/transcription/CollaborativeTranscriptEditor.tsx`
  - Path: `ws://<WS_BASE>/ws/transcript/{transcriptionId}/{sessionId}`
  - Status: Unknown
  - Action: Align to supported path or remove

- Distributed Monitor
  - Client: `frontend/src/components/distributed/DistributedProcessingMonitor.tsx`
  - Path: `ws://<WS_BASE>/api/distributed/monitor`
  - Status: Unknown
  - Action: Verify/Implement or remove

- Translation Stream
  - Client: `frontend/src/components/translation/RealtimeTranslation.tsx`
  - Path: `ws://<WS_BASE>/api/translation/stream`
  - Status: Unknown
  - Action: Verify/Implement or flag in UI

- Electron Queue WS
  - Client: `desktop_app/src/renderer/src/screens/ProcessingQueue.tsx`
  - Path: `ws://localhost:8001/api/queue/ws`
  - Status: Unknown (external worker vs. main API)
  - Action: Decide on 8001 worker or route via main API; env-drive base

Server-Side (from API scan)
- Processing WS (enterprise endpoints)
  - Server: `api/enterprise_endpoints.py`
  - Path: `/ws/processing/{client_id}`
  - Status: Implemented
  - Notes: Not currently mapped by web client components

- Enhanced WS Router (toggle)
  - Server: `api/app.py` `USE_ENHANCED_WEBSOCKET`
  - Path: `/api/v1/...` (varies)
  - Status: Likely (conditional)
  - Notes: Needs explicit route list

- GraphQL Router
  - Server: `api/graphql_api.py`
  - Path: `/api/graphql`
  - Status: Implemented
  - Notes: Confirm WS upgrades path with Strawberry

Actions Summary
- Publish WS base envs across clients (`VITE_WS_URL`, `DESKTOP_WS_URL`).
- Verify/implement the listed WS endpoints or gate features behind flags.
- Update hardcoded `ws://localhost:...` to use env-driven base.

