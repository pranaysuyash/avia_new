# Intent‑First UI Playbook

Purpose: Provide concrete, copy‑pasteable patterns that align UX with the Intent‑First Handbook — focusing on outcomes, clarity, and risk‑managed MVPs.

## Page Frame Pattern
- Use a consistent header on every page: breadcrumb → title → subtitle, plus environment/role chips.

Example:

```python
from enhanced_components_refactored import render_page_frame

render_page_frame(
    title="👑 Admin Dashboard",
    subtitle="Unified administrative interface for system management",
    breadcrumb=["Admin"],
    env_label=st.session_state.get('env', 'Demo'),
    role_label=st.session_state.get('user', {}).get('role', 'guest')
)
```

Guidelines:
- Title: concrete and task‑oriented; subtitle: why it matters.
- Breadcrumb: 1–3 levels; avoid deep hierarchies.
- Chips: show env (“Demo”, “Staging”, “Prod”) and role.

## Tabs & Deep Links (Query Params)
- Always deep link primary navigation state to support back/forward, bookmarking, and sharing.

Enhanced tabs with query‑param sync:

```python
from enhanced_components_refactored import enhanced_tabs

tabs = ["Overview", "Analytics", "Activity", "Alerts"]
selected_tab = enhanced_tabs(
    tabs,
    key="dashboard_tabs",
    query_param="admin_tab",
    default="Overview"
)
```

Sidebar section radio with query‑param sync:

```python
sections = ["Dashboard", "Users", "Teams", "Subscriptions", "System", "Reports"]
# Read from query params
qp = st.experimental_get_query_params() or {}
selected_section = qp.get("admin_section", [None])[0]
index = sections.index(selected_section) if selected_section in sections else 0
main_section = st.radio("Main Section", sections, index=index, key="admin_main_section")
# Write back if changed
if main_section != selected_section:
    current = st.experimental_get_query_params() or {}
    current["admin_section"] = [main_section]
    st.experimental_set_query_params(**current)
```

## Standardized States: Loading / Empty / Error / Success
- Remove ambiguity between “loading” and “no data”. Prefer explicit empty states and helpful errors.

Loading (wrap fetches or long work):

```python
from enhanced_components_refactored import enhanced_loading_state
with st.spinner("Loading usage metrics…"):
    data = fetch_metrics()
```

Empty state with action:

```python
from enhanced_components_refactored import render_empty_state
render_empty_state(
    title="No results yet",
    description="Upload media to see analysis here.",
    icon="📭",
    action_label="Upload Media",
    action_callback=lambda: st.sidebar.button("Open Uploader", key="open_uploader")
)
```

Error with details under expander:

```python
from enhanced_components_refactored import show_error_message
show_error_message(
    "Could not reach API",
    details="Timeout contacting /api/v1/admin/stats"
)
```

Success message:

```python
from enhanced_components_refactored import show_success_message
show_success_message("Report generated and sent to your email")
```

## Demo vs. Production Transparency
- When showing mock/fallback data, label it clearly.
- Example (sidebar stats fallback): `st.caption("Demo data — API unavailable or running in demo mode")`
- Add `env_label` in `render_page_frame` per session/env.

## Progressive Disclosure & Primary Actions
- For dense forms (e.g., Export, Orchestration), show the 1–3 primary actions first.
- Put advanced options inside `st.expander("Advanced")` with defaults pre‑filled.

## Accessibility Guardrails
- Ensure WCAG‑friendly contrast (check `ui_styles_refactored.py` colors).
- Avoid icon‑only actions; include text labels.
- Provide visible focus styles and logical keyboard order.

## Performance Guardrails
- Cache derived data (`st.cache_data`) and slow resources (`st.cache_resource`).
- Defer heavy plots behind toggles; paginate tables.
- Simple budgets: P95 < 350ms for UI actions, charts < 1.5s.

## Observability of UX (MVP)
- Log a few key events to a JSONL for analysis during MVP:

```python
import json, time

def log_ux_event(event, **kwargs):
    ts = int(time.time())
    st.session_state.setdefault("ux_events", []).append({"ts": ts, "event": event, **kwargs})

# Usage
log_ux_event("screen_view", screen="admin_overview")
log_ux_event("tab_change", tab=selected_tab)
```

Later: send to a backend endpoint and add an Admin view to inspect UX telemetry.

## Privacy Controls (UI)
- Mask PII by default when role/env requires it.
- Gate sensitive downloads with a confirm step showing what’s included.
- Use environment/role chips to set context expectations.

---

Use this playbook in PRs alongside the Intent‑First checklist and ADR template.
