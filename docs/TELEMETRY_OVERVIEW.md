# Telemetry Overview

This document explains how UX telemetry is captured across platforms and how to inspect it.

## Goals
- Lightweight, best-effort logging that never blocks UI.
- Local-only by default; safe payloads (no PII unless explicitly required).
- Easy to extend from any screen or event.

## Streamlit
- API: `streamlit_intent_utils.log_ux_event(event, payload?)`
- Sink: Appends JSON lines to `ux_events_streamlit.jsonl` in the working directory.
- Viewer: `streamlit_telemetry_viewer.py`
  - Refresh, Clear All, Download JSON.
- Example:
```
from streamlit_intent_utils import log_ux_event
log_ux_event('search_executed', {'q': query, 'count': len(results)})
```

## Web/Electron (React)
- API (web): `components/shared/uxTelemetry.ts`
  - `logUxEvent(event: string, payload?: Record<string, unknown>)`
  - Buffers to `localStorage` (`ux_events_buffer`), forwards to Electron main via `window.electronAPI.logUxEvent` when present.
- Renderer services: `desktop_app/src/renderer/src/services/uxTelemetry.ts` performs the same role for the Electron renderer bundle.
- Dev overlay: `?dev_telemetry=1` shows `DevTelemetryOverlay` (latest ~100 events).
- Example:
```
import { logUxEvent } from '../shared/uxTelemetry';
logUxEvent('page_view', { path: location.pathname });
```

## React Native
- API: `mobile/src/utils/uxTelemetry.ts`
  - `logUxEvent(event, payload)` writes to `AsyncStorage` (in-memory fallback).
  - Helpers: `getUxEvents`, `clearUxEvents`.
- Viewer: `mobile/src/screens/TelemetryViewer.tsx`.
- Example:
```
await logUxEvent('share_media_upload_view', { url });
```

## Naming and Payloads
- Use verb-noun event names: `share_view_copied`, `search_executed`, `page_view`, `sidebar_toggle`.
- Keep payloads minimal, strings/numbers/booleans where possible.
- Do not include sensitive/PII unless approved.

## Troubleshooting
- Streamlit: Ensure app has write permissions; check `ux_events_streamlit.jsonl` exists.
- Web/Electron: Inspect localStorage; verify `electronAPI.logUxEvent` exists in desktop builds.
- Mobile: Verify AsyncStorage is installed; use the Telemetry Viewer screen.

