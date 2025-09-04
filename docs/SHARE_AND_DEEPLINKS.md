# Share Controls and Deep Links

Guidelines and examples for shareable views and deep-linked state.

## Utilities (Streamlit)
- `get_params()` reads compact query params to a dict of strings.
- `update_params({ key: value | None })` merges/removes keys.
- `render_share_inline(title?)` adds an inline copyable link.
- `render_share_block(title?)` adds a sidebar expander with the link.

## Key Patterns
- Use short, stable keys (e.g., `bi_period`, `rt_mode`).
- Only write non-default values to keep URLs tidy.
- Provide a Reset button that clears keys and logs `st_filters_cleared` with a scope.
- For tabs, reorder tabs so the selected tab appears first (Streamlit focuses the first tab).

## Examples (Streamlit)
- Business Intelligence: `?bi_tab=revenue&bi_period=Last%2090%20days`
- Real-Time Transcription: `?rt_tab=analytics&rt_engine=whisper_api&rt_lang=en&rt_sr=16000&rt_mode=vad&rt_chart=1`
- Admin Users: `?admin_page=👥%20User%20User%20Management&admin_user_status=Active&admin_user_page=2`
- Frame OCR: `?fo_tab=search`

## Web/Electron
- Use `components/shared/ShareViewButton.tsx` to copy the current URL (optionally add `extraParams`).
- Example:
```
<ShareViewButton className="px-2 py-1 text-xs border rounded" extraParams={{ panel: 'settings' }} />
```
- `useQueryParam.ts` helpers: `getQueryParam`, `setQueryParam`, `useQueryParam`.

## React Native
- Build deep links with `buildLink(screen, params)` in `mobile/src/utils/deeplink.ts`.
- Share via the native Share API and log events.
- Example:
```
const url = buildLink('transcription', { id: transcriptId });
await Share.share({ message: url });
await logUxEvent('share_transcription_view', { url, transcriptId });
```

