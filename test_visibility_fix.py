#!/usr/bin/env python3
"""
Quick test for visibility fix
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from theme_manager import apply_custom_theme

def test_visibility():
    # Apply the fixed theme
    apply_custom_theme()
    
    # Emergency visibility CSS
    st.markdown("""
    <style>
    /* EMERGENCY TEXT VISIBILITY FIX */
    * {
        color: #000000 !important;
    }
    
    .stMarkdown, .stMarkdown *, .stText, .stText *, 
    p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar text */
    .css-1d391kg, .css-1d391kg *, 
    [data-testid="stSidebar"], [data-testid="stSidebar"] * {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    
    /* Input labels */
    .stSelectbox > label, .stFileUploader > label, 
    .stSlider > label, .stCheckbox > label {
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 1.2em !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🧪 VISIBILITY TEST")
    st.markdown("**This text should now be BLACK and BOLD**")
    
    st.sidebar.title("Sidebar Test")
    st.sidebar.markdown("**This sidebar text should be BLACK and VISIBLE**")
    
    test_option = st.selectbox("Can you see this label clearly?", ["Yes - Much Better!", "No - Still Hard to Read"])
    
    if test_option == "Yes - Much Better!":
        st.success("✅ Visibility fix is working!")
    else:
        st.error("❌ Still needs more work")
    
    st.markdown("### Text Visibility Test")
    st.markdown("- Regular text should be **black** and **bold**")
    st.markdown("- Headers should be **very visible**")
    st.markdown("- All labels should be **easy to read**")

if __name__ == "__main__":
    test_visibility()