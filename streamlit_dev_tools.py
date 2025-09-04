"""
Streamlit Dev Tools

Convenience launcher for developer utilities like the Telemetry Viewer.
Run: streamlit run streamlit_dev_tools.py
"""

import streamlit as st

st.set_page_config(page_title="Dev Tools", page_icon="🧰", layout="centered")

st.title("🧰 Developer Tools")
st.caption("Quick access to local debug utilities.")

st.markdown("""
- Telemetry Viewer: Inspect, refresh, download, and clear Streamlit UX events.

Use the buttons below to open in a new browser tab.
""")

col1, = st.columns(1)
with col1:
    st.page_link("streamlit_telemetry_viewer.py", label="🧭 Open Telemetry Viewer", icon="🧭")

st.divider()
st.markdown("""
Tips
- Use deep-link query params visible in the URL to share specific views (filters, toggles, tabs).
- Clear deep-linked state from sidebars with the provided Reset buttons.
""")

