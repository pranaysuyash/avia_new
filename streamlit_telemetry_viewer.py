"""
Streamlit Telemetry Viewer

Inspect, refresh, download, and clear local UX telemetry events captured by log_ux_event.
"""

import json
import os
from typing import List, Dict, Any

import streamlit as st

UX_FILE = "ux_events_streamlit.jsonl"


def read_events(path: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return events
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        pass
    return events


def write_clear(path: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass


def main() -> None:
    st.set_page_config(page_title="Telemetry Viewer", page_icon="🧭", layout="wide")
    st.title("🧭 Telemetry Viewer (Streamlit)")
    st.caption("Local UX events written to ux_events_streamlit.jsonl")

    col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 6])
    with col_a:
        if st.button("Refresh"):
            st.rerun()
    with col_b:
        if st.button("Clear All"):
            write_clear(UX_FILE)
            st.success("Cleared all events")
            st.rerun()
    with col_c:
        events = read_events(UX_FILE)
        st.download_button(
            label="Download JSON",
            data=json.dumps(events, indent=2).encode("utf-8"),
            file_name="ux_events_streamlit.json",
            mime="application/json",
        )

    st.divider()

    events = read_events(UX_FILE)
    st.subheader(f"Events ({len(events)})")

    if not events:
        st.info("No events recorded yet.")
        return

    # Show latest first
    events = list(reversed(events))
    # Tabular quick view
    compact = [
        {"ts": e.get("ts") or e.get("srv_ts"), "event": e.get("event"), "payload": {k: v for k, v in e.items() if k not in {"ts", "srv_ts", "event"}}}
        for e in events
    ]
    st.dataframe(compact, use_container_width=True)

    with st.expander("Raw JSON", expanded=False):
        st.code(json.dumps(events, indent=2), language="json")


if __name__ == "__main__":
    main()

