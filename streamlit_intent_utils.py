"""
Intent-First Streamlit utilities for deep-linked UI state and lightweight telemetry.
"""

from __future__ import annotations

import json
import time
from typing import Dict, Any, Optional

import streamlit as st


def _flatten_params(params: Dict[str, list[str]]) -> Dict[str, str]:
    flat: Dict[str, str] = {}
    for k, v in params.items():
        if isinstance(v, list):
            flat[k] = v[0] if v else ""
        else:
            flat[k] = str(v)
    return flat


def get_params() -> Dict[str, str]:
    try:
        # Streamlit >=1.32 has st.query_params; fall back to experimental API
        qp = getattr(st, "query_params", None)
        if qp is not None:
            return {k: str(v) for k, v in qp.items()}
        return _flatten_params(st.experimental_get_query_params())
    except Exception:
        return {}


def update_params(updates: Dict[str, Optional[str]]) -> None:
    try:
        params = get_params()
        for k, v in updates.items():
            if v is None or v == "":
                params.pop(k, None)
            else:
                params[k] = str(v)
        st.experimental_set_query_params(**params)
    except Exception:
        pass


def build_share_url(extra: Optional[Dict[str, str]] = None) -> str:
    try:
        base = st.experimental_get_query_params  # type: ignore[attr-defined]
    except Exception:
        base = None
    params = get_params().copy()
    if extra:
        params.update({k: str(v) for k, v in extra.items()})
    # Compose full URL from browser location if available
    try:
        # Streamlit exposes the base path in the DOM; we can't access here directly.
        # Use a relative URL with query string which is shareable within the app context.
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            return f"?{query}"
        return "."
    except Exception:
        return "."


def render_share_block(title: str = "Share This View") -> None:
    url = build_share_url()
    with st.sidebar.expander(title, expanded=False):
        st.code(url)
        st.caption("Copy this link to share the current filters and view state.")


def render_share_inline(title: str = "Shareable link") -> None:
    try:
        url = build_share_url()
        col_a, col_b = st.columns([5, 1])
        with col_a:
            st.text_input(title, value=url, help="Copy this link to share the current view.", label_visibility="visible")
        with col_b:
            # Streamlit cannot copy to clipboard directly; provide a UX hint
            st.caption("Cmd/Ctrl+C")
    except Exception:
        st.caption(title)
        st.code(build_share_url())


def log_ux_event(event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    try:
        ev = {
            "ts": int(time.time() * 1000),
            "event": event,
            "session": st.session_state.get("session_id") or st.session_state.get("_session_id"),
        }
        if payload:
            ev.update(payload)
        line = json.dumps(ev, ensure_ascii=False) + "\n"
        with open("ux_events_streamlit.jsonl", "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # best effort only
        pass


# Lightweight skeleton helpers
def render_skeleton_line(width: str = "100%", height: int = 12, radius: int = 6, margin: str = "6px 0") -> None:
    st.markdown(
        f"""
        <div style="width:{width};height:{height}px;border-radius:{radius}px;background:#e6e8eb;margin:{margin};"></div>
        """,
        unsafe_allow_html=True,
    )


def render_skeleton_block(width: str = "100%", height: int = 120, radius: int = 8, margin: str = "8px 0") -> None:
    st.markdown(
        f"""
        <div style="width:{width};height:{height}px;border-radius:{radius}px;background:#e6e8eb;margin:{margin};"></div>
        """,
        unsafe_allow_html=True,
    )


def render_skeleton_list(items: int = 3) -> None:
    for _ in range(max(items, 0)):
        render_skeleton_line(width="60%", height=16)
        render_skeleton_line(width="90%", height=12)
        render_skeleton_line(width="80%", height=12)
        render_skeleton_block(height=1, margin="4px 0")
