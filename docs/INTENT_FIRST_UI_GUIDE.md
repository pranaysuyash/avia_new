# Intent-First UI Guide

This guide documents the Intent-First patterns implemented across the app: deep-linkable views, share controls, lightweight telemetry, and responsive skeletons. It lists keys, utilities, and extension patterns across Streamlit, Web/Electron, and React Native.

## Streamlit (Python)
- Utilities: `streamlit_intent_utils.py`
  - `get_params()`, `update_params(dict)`: Deep-link state via query params.
  - `render_share_inline(title?)`, `render_share_block(title?)`: Copyable share links.
  - `log_ux_event(event, payload?)`: Appends to `ux_events_streamlit.jsonl`.
  - `render_skeleton_list/line/block`: Lightweight loading skeletons.
- Telemetry Viewer: `streamlit_telemetry_viewer.py` (view/clear/download UX events).
- Key screens (deep-link keys in parentheses):
  - `timestamping_system_ui.py` (`ts_content`, `ts_time`, `ts_tab`)
  - `export_ui.py` (`exp_*` such as `exp_anon`, `exp_format`, `exp_bulk`, `exp_perms`)
  - `content_management_ui.py` (`cms_page`, `cms_q`, `cms_quality`, `cms_status`, `cms_types`, `cms_tags`, `cms_date`, `cms_dur`)
  - `predictive_analytics_ui.py` (`pa_module`)
  - `business_intelligence_ui.py` (`bi_period`, `bi_start`, `bi_end`)
    - Tabs: `bi_tab` (exec|revenue|users|pred|ops); skeletons around heavy charts.
  - `quality_assessment_ui.py` (`qa_med`, `qa_view`, `qa_range`)
  - `ai_customization_ui.py` (`aic_tab`)
  - `content_insights_ui.py` (`ci_sent`, `ci_topics`, `ci_sum`, `ci_speakers`)
  - `image_annotation_ui.py` (`ia_mode`, `ia_tool`)
  - `frame_ocr_job_manager_ui.py` (`fojm_page`, `fojm_tenant`, `fojm_auto`)
  - `frame_ocr_ui.py` tabs: `fo_tab` (process|jobs|search|analytics)
  - Inline share/reset added to: `frame_ocr_ui.py`, `advanced_noise_reduction_system_ui.py`, `batch_interface.py`.
  - `advanced_search_system_ui.py` tabs: `as_tab` (search|analytics|settings|help)
  - `real_time_transcription_ui.py` settings: `rt_engine`, `rt_lang`, `rt_sr`, `rt_chunk`, `rt_conf`, `rt_mode`, `rt_chart`; tabs: `rt_tab` (live|analytics|export|status)
  - `media_intelligence_ui.py` (`mi_type`, `mi_deep`, `mi_highlights`, `mi_thumbs`, `mi_scene`)
  - `admin_dashboard_ui.py` page + filters:
    - Page: `admin_page`
    - Users: `admin_user_query`, `admin_user_status`, `admin_user_tier`, `admin_user_sort`, `admin_user_dir`, `admin_user_size`, `admin_user_page`
    - Revenue: `admin_rev_period` (`Custom` via `admin_rev_start`, `admin_rev_end`)
    - Tickets: `admin_tk_status`, `admin_tk_pri`, `admin_tk_sort`, `admin_tk_dir`, `admin_tk_size`, `admin_tk_page`

## React Web + Electron
- Shared utilities (web): `components/shared/`
  - `uxTelemetry.ts`: `logUxEvent`, `getUxEvents`, `clearUxEvents` (localStorage buffer, Electron IPC).
  - `useQueryParam.ts`: `getQueryParam`, `setQueryParam`, `useQueryParam` hook.
  - `ShareViewButton.tsx`: Copies current URL with optional extra params; logs `share_view_copied`.
- Electron renderer: `desktop_app/src/renderer/src/`
  - `services/uxTelemetry.ts`: Renderer-side telemetry buffer + IPC sink.
  - `components/dev/DevTelemetryOverlay.tsx`: Toggle with `?dev_telemetry=1`.
  - `components/layout/Header.tsx`: Header “Share” button logs `share_view_copied`.
  - Screens integrate deep-links and share as applicable (e.g., Advanced Search, Settings, Workspaces, etc.).
- Electron main/preload:
  - `desktop_app/src/main.js`: Handles IPC `ux:log` and menu actions.
  - `desktop_app/src/preload.js`: Exposes `electronAPI.logUxEvent` to renderer.

## React Native (Mobile)
- Telemetry: `mobile/src/utils/uxTelemetry.ts` (AsyncStorage buffer; `logUxEvent` et al.).
- Deep links: `mobile/src/navigation/AppNavigator.tsx` (`linking` config; prefixes `nerapp://`, `https://app.ner`).
- Deeplink builder: `mobile/src/utils/deeplink.ts` (`buildLink(screen, params)`).
- Example screens with Share + telemetry:
  - Settings: `mobile/src/components/settings/Settings.tsx` (shares `nerapp://settings?tab=...`).
  - Dashboard, Search, TranscriptionResults, Preprocessing, Medical, Analytics, etc.

## Share/Reset + Usage Tips
- Prefer stable, compact keys for URL/state (e.g., `bi_period` vs verbose names).
- Only write params that differ from defaults to keep links tidy.
- Log meaningful user intent (e.g., `search_executed`, `share_*_view`, `page_view`).
- Keep telemetry best-effort and non-blocking.
 - Provide both inline share (near headers) and sidebar block share; add a Reset button that clears relevant keys and logs `st_filters_cleared`.

## Examples
- Real-Time: `?rt_tab=analytics&rt_engine=whisper_api&rt_lang=en&rt_sr=16000&rt_mode=vad&rt_chart=1`
- BI: `?bi_tab=revenue&bi_period=Last%2090%20days`
- Admin Users: `?admin_page=👥%20User%20Management&admin_user_status=Active&admin_user_page=2`
- Frame OCR: `?fo_tab=search`

## Where To Extend Next
- Streamlit: Add deep-link keys for any remaining filters or tabs following the patterns above.
- Web/Electron: Use `ShareViewButton` in view headers; log key intent events.
- Mobile: Add header Share actions where missing; ensure `buildLink()` points to the correct route.
