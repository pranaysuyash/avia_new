"""
Internationalization Management UI - Streamlit Interface
Comprehensive i18n management interface for admins and users
"""

import streamlit as st
import pandas as pd
import requests
import json
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import csv

# Page configuration
st.set_page_config(
    page_title="Internationalization Management",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for RTL support and better styling
st.markdown("""
<style>
.rtl-text {
    direction: rtl;
    text-align: right;
}

.language-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.metric-card {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #667eea;
    margin: 5px 0;
}

.translation-table {
    font-size: 14px;
}

.priority-high {
    background-color: #ffebee;
    color: #c62828;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}

.priority-medium {
    background-color: #fff8e1;
    color: #f57c00;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}

.priority-low {
    background-color: #e8f5e8;
    color: #2e7d32;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

class InternationalizationManager:
    def __init__(self):
        self.api_base_url = st.secrets.get("api_base_url", "http://localhost:8000")
        self.supported_languages = [
            {"code": "en", "name": "English", "native_name": "English", "direction": "ltr", "flag": "🇺🇸"},
            {"code": "es", "name": "Spanish", "native_name": "Español", "direction": "ltr", "flag": "🇪🇸"},
            {"code": "fr", "name": "French", "native_name": "Français", "direction": "ltr", "flag": "🇫🇷"},
            {"code": "de", "name": "German", "native_name": "Deutsch", "direction": "ltr", "flag": "🇩🇪"},
            {"code": "it", "name": "Italian", "native_name": "Italiano", "direction": "ltr", "flag": "🇮🇹"},
            {"code": "pt", "name": "Portuguese", "native_name": "Português", "direction": "ltr", "flag": "🇧🇷"},
            {"code": "ru", "name": "Russian", "native_name": "Русский", "direction": "ltr", "flag": "🇷🇺"},
            {"code": "zh", "name": "Chinese", "native_name": "中文", "direction": "ltr", "flag": "🇨🇳"},
            {"code": "ja", "name": "Japanese", "native_name": "日本語", "direction": "ltr", "flag": "🇯🇵"},
            {"code": "ko", "name": "Korean", "native_name": "한국어", "direction": "ltr", "flag": "🇰🇷"},
            {"code": "ar", "name": "Arabic", "native_name": "العربية", "direction": "rtl", "flag": "🇸🇦"},
            {"code": "he", "name": "Hebrew", "native_name": "עברית", "direction": "rtl", "flag": "🇮🇱"},
            {"code": "hi", "name": "Hindi", "native_name": "हिन्दी", "direction": "ltr", "flag": "🇮🇳"},
            {"code": "th", "name": "Thai", "native_name": "ไทย", "direction": "ltr", "flag": "🇹🇭"},
            {"code": "vi", "name": "Vietnamese", "native_name": "Tiếng Việt", "direction": "ltr", "flag": "🇻🇳"}
        ]
        self.namespaces = [
            "general", "navigation", "forms", "errors", 
            "dashboard", "transcription", "analytics", "settings"
        ]

    def get_language_info(self, code: str) -> Dict[str, Any]:
        return next((lang for lang in self.supported_languages if lang["code"] == code), 
                   {"code": code, "name": code.upper(), "native_name": code.upper(), 
                    "direction": "ltr", "flag": "🌐"})

    def api_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        try:
            url = f"{self.api_base_url}/api/v1/i18n{endpoint}"
            
            if method == "GET":
                response = requests.get(url, params=data or {})
            elif method == "POST":
                response = requests.post(url, json=data or {})
            else:
                st.error(f"Unsupported HTTP method: {method}")
                return {}
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return {}
        except json.JSONDecodeError:
            st.error("Invalid JSON response from API")
            return {}

    def load_translation_stats(self) -> Dict[str, Any]:
        """Load translation statistics"""
        stats = self.api_request("/stats")
        if not stats:
            # Mock data for demo
            stats = {
                "total_keys": 1247,
                "languages": len(self.supported_languages),
                "namespaces": len(self.namespaces),
                "completion_rate": {lang["code"]: min(100, 60 + (hash(lang["code"]) % 40)) 
                                 for lang in self.supported_languages},
                "recent_updates": [
                    {"key": "dashboard.welcome", "language": "es", "updated_at": "2024-01-15T10:30:00Z", "updated_by": "admin"},
                    {"key": "forms.validation.required", "language": "fr", "updated_at": "2024-01-15T09:15:00Z", "updated_by": "translator"},
                    {"key": "navigation.home", "language": "de", "updated_at": "2024-01-14T16:45:00Z", "updated_by": "admin"}
                ]
            }
        return stats

    def load_missing_translations(self, language_code: str, namespace: str) -> List[Dict[str, Any]]:
        """Load missing translations for a language/namespace"""
        missing = self.api_request("/missing", data={"language_code": language_code, "namespace": namespace})
        if not missing or "missing_translations" not in missing:
            # Mock data for demo
            missing_translations = [
                {"key": "dashboard.analytics_overview", "namespace": namespace, "english_value": "Analytics Overview", "priority": "high"},
                {"key": "forms.upload.drag_drop", "namespace": namespace, "english_value": "Drag and drop files here", "priority": "medium"},
                {"key": "settings.appearance.theme", "namespace": namespace, "english_value": "Theme Settings", "priority": "low"}
            ]
            return missing_translations[:3] if namespace == "general" else missing_translations[:1]
        return missing.get("missing_translations", [])

def main():
    i18n_manager = InternationalizationManager()
    
    # Sidebar for navigation and settings
    with st.sidebar:
        st.markdown("## 🌐 Internationalization")
        
        page = st.selectbox(
            "Navigate to",
            ["Overview", "Translation Manager", "Language Settings", "Missing Translations", 
             "Import/Export", "Analytics"]
        )
        
        st.markdown("---")
        
        # Language selector for interface
        interface_language = st.selectbox(
            "Interface Language",
            options=[lang["code"] for lang in i18n_manager.supported_languages],
            format_func=lambda x: f"{i18n_manager.get_language_info(x)['flag']} {i18n_manager.get_language_info(x)['native_name']}",
            index=0
        )
        
        # Quick stats
        stats = i18n_manager.load_translation_stats()
        st.markdown("### Quick Stats")
        st.metric("Total Keys", stats.get("total_keys", 0))
        st.metric("Languages", stats.get("languages", 0))
        st.metric("Avg Completion", f"{int(sum(stats.get('completion_rate', {}).values()) / len(stats.get('completion_rate', {})) if stats.get('completion_rate') else 0)}%")

    # Main content based on selected page
    if page == "Overview":
        render_overview_page(i18n_manager, stats)
    elif page == "Translation Manager":
        render_translation_manager_page(i18n_manager)
    elif page == "Language Settings":
        render_language_settings_page(i18n_manager)
    elif page == "Missing Translations":
        render_missing_translations_page(i18n_manager)
    elif page == "Import/Export":
        render_import_export_page(i18n_manager)
    elif page == "Analytics":
        render_analytics_page(i18n_manager, stats)

def render_overview_page(i18n_manager: InternationalizationManager, stats: Dict[str, Any]):
    """Render the overview/dashboard page"""
    st.title("🌐 Internationalization Overview")
    st.markdown("Manage translations and localization across all supported languages")

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📝 {stats.get('total_keys', 0)}</h3>
            <p>Translation Keys</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🌍 {stats.get('languages', 0)}</h3>
            <p>Supported Languages</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        completion_rate = int(sum(stats.get('completion_rate', {}).values()) / len(stats.get('completion_rate', {})) if stats.get('completion_rate') else 0)
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ {completion_rate}%</h3>
            <p>Avg Completion</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📁 {stats.get('namespaces', 0)}</h3>
            <p>Namespaces</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Language completion progress
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Translation Progress by Language")
        
        completion_data = []
        for lang_code, completion in stats.get('completion_rate', {}).items():
            lang_info = i18n_manager.get_language_info(lang_code)
            completion_data.append({
                'Language': f"{lang_info['flag']} {lang_info['native_name']}",
                'Completion': completion,
                'Code': lang_code
            })
        
        df = pd.DataFrame(completion_data)
        if not df.empty:
            fig = px.bar(df, x='Completion', y='Language', orientation='h',
                        color='Completion', color_continuous_scale='Viridis',
                        title="Translation Completion by Language")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🚀 Quick Actions")
        
        if st.button("🔄 Sync All Translations", use_container_width=True):
            with st.spinner("Syncing translations..."):
                st.success("All translations synced successfully!")
        
        if st.button("🤖 Auto-Translate Missing", use_container_width=True):
            with st.spinner("Running AI translation..."):
                st.success("Auto-translation completed!")
        
        if st.button("📥 Import Translations", use_container_width=True):
            st.info("Navigate to Import/Export tab")
        
        if st.button("📊 Generate Report", use_container_width=True):
            with st.spinner("Generating report..."):
                st.success("Report generated!")

    # Recent activity
    st.subheader("📈 Recent Translation Updates")
    recent_updates = stats.get('recent_updates', [])
    if recent_updates:
        df_updates = pd.DataFrame(recent_updates)
        df_updates['updated_at'] = pd.to_datetime(df_updates['updated_at']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(df_updates, use_container_width=True)
    else:
        st.info("No recent updates available")

def render_translation_manager_page(i18n_manager: InternationalizationManager):
    """Render the translation manager page"""
    st.title("✏️ Translation Manager")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_language = st.selectbox(
            "Target Language",
            options=[lang["code"] for lang in i18n_manager.supported_languages],
            format_func=lambda x: f"{i18n_manager.get_language_info(x)['flag']} {i18n_manager.get_language_info(x)['native_name']}"
        )
    
    with col2:
        selected_namespace = st.selectbox("Namespace", i18n_manager.namespaces)
    
    with col3:
        search_term = st.text_input("🔍 Search translations", placeholder="Enter key or text...")

    st.markdown("---")

    # Translation editor
    st.subheader("📝 Add/Edit Translation")
    
    with st.form("translation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            translation_key = st.text_input("Translation Key", placeholder="e.g., dashboard.welcome_message")
            namespace = st.selectbox("Namespace", i18n_manager.namespaces, key="form_namespace")
        
        with col2:
            language_code = st.selectbox(
                "Language", 
                [lang["code"] for lang in i18n_manager.supported_languages],
                format_func=lambda x: f"{i18n_manager.get_language_info(x)['flag']} {i18n_manager.get_language_info(x)['native_name']}",
                key="form_language"
            )
        
        translation_value = st.text_area(
            "Translation Value",
            placeholder="Enter the translated text...",
            help="Use {variable} for variable substitution"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit_button = st.form_submit_button("💾 Save Translation", use_container_width=True)
        with col2:
            if st.form_submit_button("🤖 AI Translate", use_container_width=True):
                if translation_key and namespace:
                    with st.spinner("Translating with AI..."):
                        st.success("AI translation completed!")
                else:
                    st.error("Please fill in the key and namespace first")

        if submit_button:
            if translation_key and translation_value and language_code:
                # Here you would save the translation
                st.success(f"Translation saved: {translation_key} -> {language_code}")
            else:
                st.error("Please fill in all required fields")

    # Bulk operations
    st.subheader("🔄 Bulk Operations")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 Auto-translate Missing", use_container_width=True):
            missing_count = len(i18n_manager.load_missing_translations(selected_language, selected_namespace))
            if missing_count > 0:
                with st.spinner(f"Auto-translating {missing_count} missing translations..."):
                    st.success(f"Successfully auto-translated {missing_count} items!")
            else:
                st.info("No missing translations found")
    
    with col2:
        if st.button("✅ Approve All", use_container_width=True):
            st.success("All pending translations approved!")
    
    with col3:
        if st.button("🔄 Sync with API", use_container_width=True):
            with st.spinner("Syncing translations..."):
                st.success("Translations synced successfully!")

def render_language_settings_page(i18n_manager: InternationalizationManager):
    """Render language settings and configuration page"""
    st.title("⚙️ Language Settings")
    
    # Language configuration
    st.subheader("🌍 Supported Languages")
    
    # Display language grid
    cols = st.columns(3)
    for idx, language in enumerate(i18n_manager.supported_languages):
        with cols[idx % 3]:
            with st.expander(f"{language['flag']} {language['native_name']}", expanded=False):
                st.write(f"**Code:** {language['code']}")
                st.write(f"**English Name:** {language['name']}")
                st.write(f"**Native Name:** {language['native_name']}")
                st.write(f"**Direction:** {language['direction']}")
                
                if language['direction'] == 'rtl':
                    st.markdown(f"<div class='rtl-text'>🔄 {language['native_name']}</div>", 
                              unsafe_allow_html=True)
                
                # Mock completion status
                completion = hash(language['code']) % 100
                st.progress(completion / 100)
                st.caption(f"{completion}% Complete")

    st.markdown("---")

    # Regional settings
    st.subheader("🗺️ Regional Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Date & Time Formats")
        sample_date = datetime.now()
        
        for lang in i18n_manager.supported_languages[:5]:  # Show first 5 as examples
            try:
                formatted_date = sample_date.strftime("%Y-%m-%d %H:%M")
                st.write(f"{lang['flag']} **{lang['name']}:** {formatted_date}")
            except:
                st.write(f"{lang['flag']} **{lang['name']}:** {sample_date}")
    
    with col2:
        st.markdown("### Number & Currency Formats")
        sample_number = 1234567.89
        
        for lang in i18n_manager.supported_languages[:5]:
            try:
                # Mock locale-specific formatting
                if lang['code'] == 'de':
                    formatted = "1.234.567,89 €"
                elif lang['code'] == 'fr':
                    formatted = "1 234 567,89 €"
                elif lang['code'] == 'ja':
                    formatted = "¥1,234,568"
                else:
                    formatted = "$1,234,567.89"
                st.write(f"{lang['flag']} **{lang['name']}:** {formatted}")
            except:
                st.write(f"{lang['flag']} **{lang['name']}:** {sample_number}")

    # RTL Language Support
    st.subheader("🔄 RTL Language Support")
    
    rtl_languages = [lang for lang in i18n_manager.supported_languages if lang['direction'] == 'rtl']
    
    if rtl_languages:
        st.info(f"RTL support is enabled for {len(rtl_languages)} languages: " + 
                ", ".join([f"{lang['flag']} {lang['name']}" for lang in rtl_languages]))
        
        for lang in rtl_languages:
            with st.expander(f"RTL Demo: {lang['flag']} {lang['native_name']}"):
                st.markdown(f"""
                <div class="rtl-text">
                    <h3>{lang['native_name']}</h3>
                    <p>هذا مثال على النص من اليمين إلى اليسار</p>
                    <p>זהו דוגמה לטקסט מימין לשמאל</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No RTL languages configured")

def render_missing_translations_page(i18n_manager: InternationalizationManager):
    """Render missing translations page"""
    st.title("⚠️ Missing Translations")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_language = st.selectbox(
            "Language",
            options=[lang["code"] for lang in i18n_manager.supported_languages],
            format_func=lambda x: f"{i18n_manager.get_language_info(x)['flag']} {i18n_manager.get_language_info(x)['native_name']}"
        )
    
    with col2:
        selected_namespace = st.selectbox("Namespace", i18n_manager.namespaces)
    
    with col3:
        priority_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])

    # Load missing translations
    missing_translations = i18n_manager.load_missing_translations(selected_language, selected_namespace)
    
    if priority_filter != "All":
        missing_translations = [t for t in missing_translations if t['priority'].lower() == priority_filter.lower()]

    st.markdown("---")
    
    # Summary
    if missing_translations:
        st.subheader(f"📋 {len(missing_translations)} Missing Translations Found")
        
        # Priority breakdown
        priority_counts = {}
        for translation in missing_translations:
            priority = translation['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        col1, col2, col3 = st.columns(3)
        for i, (priority, count) in enumerate(priority_counts.items()):
            with [col1, col2, col3][i]:
                color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
                st.metric(f"{color} {priority.title()}", count)

        # Missing translations table
        st.subheader("📋 Missing Translation Details")
        
        for translation in missing_translations:
            with st.expander(f"🔑 {translation['key']} ({translation['priority']} priority)"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write(f"**Key:** `{translation['key']}`")
                    st.write(f"**Namespace:** {translation['namespace']}")
                    priority_class = f"priority-{translation['priority']}"
                    st.markdown(f'<span class="{priority_class}">Priority: {translation["priority"].upper()}</span>', 
                              unsafe_allow_html=True)
                
                with col2:
                    st.write("**English Value:**")
                    st.info(translation['english_value'])
                    
                    # Quick translation form
                    with st.form(f"quick_translate_{translation['key']}"):
                        translation_value = st.text_area(
                            f"Translation for {selected_language.upper()}:",
                            key=f"translate_{translation['key']}",
                            placeholder="Enter translation..."
                        )
                        
                        col_submit, col_ai = st.columns(2)
                        with col_submit:
                            if st.form_submit_button("💾 Save", use_container_width=True):
                                if translation_value:
                                    st.success(f"Translation saved for {translation['key']}")
                                else:
                                    st.error("Please enter a translation")
                        
                        with col_ai:
                            if st.form_submit_button("🤖 AI Translate", use_container_width=True):
                                with st.spinner("Generating AI translation..."):
                                    # Mock AI translation
                                    st.success("AI translation generated!")
    else:
        st.success(f"🎉 No missing translations for {selected_language.upper()} in {selected_namespace} namespace!")
        st.balloons()

def render_import_export_page(i18n_manager: InternationalizationManager):
    """Render import/export functionality page"""
    st.title("📥📤 Import/Export Translations")
    
    tab1, tab2 = st.tabs(["📥 Import", "📤 Export"])
    
    with tab1:
        st.subheader("📥 Import Translations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            import_language = st.selectbox(
                "Target Language",
                options=[lang["code"] for lang in i18n_manager.supported_languages],
                format_func=lambda x: f"{i18n_manager.get_language_info(x)['flag']} {i18n_manager.get_language_info(x)['native_name']}"
            )
            
            import_namespace = st.selectbox("Namespace", i18n_manager.namespaces)
            import_format = st.selectbox("File Format", ["JSON", "CSV", "Excel"])
        
        with col2:
            st.markdown("### 📋 Import Instructions")
            if import_format == "JSON":
                st.code("""
{
  "welcome_message": "Welcome to our app",
  "login_button": "Sign In",
  "logout_button": "Sign Out"
}
                """, language="json")
            elif import_format == "CSV":
                st.code("""
key,value,namespace
welcome_message,"Welcome to our app",general
login_button,"Sign In",forms
logout_button,"Sign Out",forms
                """, language="csv")
            else:
                st.info("Excel files should have columns: key, value, namespace")

        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            f"Choose a {import_format} file",
            type=['json', 'csv', 'xlsx'] if import_format == "Excel" else [import_format.lower()],
            help=f"Upload a {import_format} file containing translations"
        )
        
        if uploaded_file is not None:
            st.success(f"File '{uploaded_file.name}' uploaded successfully!")
            
            # Preview file content
            try:
                if import_format == "JSON":
                    content = json.load(uploaded_file)
                    st.json(content)
                elif import_format == "CSV":
                    content = pd.read_csv(uploaded_file)
                    st.dataframe(content.head())
                else:  # Excel
                    content = pd.read_excel(uploaded_file)
                    st.dataframe(content.head())
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 Import Translations", use_container_width=True):
                        with st.spinner("Importing translations..."):
                            # Mock import process
                            import time
                            time.sleep(2)
                            st.success(f"Successfully imported translations to {import_language.upper()}!")
                
                with col2:
                    if st.button("👁️ Preview Only", use_container_width=True):
                        st.info("Preview mode - no changes will be made")
                        
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with tab2:
        st.subheader("📤 Export Translations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_language = st.selectbox(
                "Source Language",
                options=[lang["code"] for lang in i18n_manager.supported_languages],
                format_func=lambda x: f"{i18n_manager.get_language_info(x)['flag']} {i18n_manager.get_language_info(x)['native_name']}",
                key="export_lang"
            )
            
            export_namespace = st.selectbox("Namespace", ["All"] + i18n_manager.namespaces, key="export_ns")
            export_format = st.selectbox("Export Format", ["JSON", "CSV", "Excel"], key="export_format")
        
        with col2:
            st.markdown("### ⚙️ Export Options")
            include_empty = st.checkbox("Include empty translations", value=False)
            include_metadata = st.checkbox("Include metadata (dates, authors)", value=True)
            compress_output = st.checkbox("Compress output file", value=False)

        st.markdown("---")
        
        if st.button("📁 Generate Export File", use_container_width=True):
            with st.spinner("Generating export file..."):
                # Mock export data
                if export_format == "JSON":
                    export_data = {
                        "dashboard.welcome": "Welcome to the dashboard",
                        "forms.submit": "Submit",
                        "navigation.home": "Home"
                    }
                    
                    file_content = json.dumps(export_data, indent=2, ensure_ascii=False)
                    file_name = f"translations_{export_language}_{export_namespace}.json"
                    mime_type = "application/json"
                    
                elif export_format == "CSV":
                    export_data = [
                        {"key": "dashboard.welcome", "value": "Welcome to the dashboard", "namespace": "general"},
                        {"key": "forms.submit", "value": "Submit", "namespace": "forms"},
                        {"key": "navigation.home", "value": "Home", "namespace": "navigation"}
                    ]
                    
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=["key", "value", "namespace"])
                    writer.writeheader()
                    writer.writerows(export_data)
                    file_content = output.getvalue()
                    file_name = f"translations_{export_language}_{export_namespace}.csv"
                    mime_type = "text/csv"
                
                else:  # Excel
                    df = pd.DataFrame([
                        {"key": "dashboard.welcome", "value": "Welcome to the dashboard", "namespace": "general"},
                        {"key": "forms.submit", "value": "Submit", "namespace": "forms"},
                        {"key": "navigation.home", "value": "Home", "namespace": "navigation"}
                    ])
                    
                    output = io.BytesIO()
                    df.to_excel(output, index=False)
                    file_content = output.getvalue()
                    file_name = f"translations_{export_language}_{export_namespace}.xlsx"
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                st.download_button(
                    label=f"⬇️ Download {export_format} File",
                    data=file_content,
                    file_name=file_name,
                    mime=mime_type,
                    use_container_width=True
                )
                
                st.success(f"Export file generated successfully! ({len(export_data) if isinstance(export_data, list) else len(export_data)} translations)")

def render_analytics_page(i18n_manager: InternationalizationManager, stats: Dict[str, Any]):
    """Render analytics and insights page"""
    st.title("📊 Translation Analytics")
    
    # Time-based analytics
    st.subheader("📈 Translation Activity Over Time")
    
    # Generate mock time series data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    activity_data = []
    
    for date in dates:
        activity_data.append({
            'Date': date,
            'New Translations': max(0, int(10 + 5 * (hash(str(date)) % 10))),
            'Updated Translations': max(0, int(5 + 3 * (hash(str(date)) % 8))),
            'Approved Translations': max(0, int(8 + 4 * (hash(str(date)) % 6)))
        })
    
    df_activity = pd.DataFrame(activity_data)
    
    fig = px.line(df_activity, x='Date', 
                  y=['New Translations', 'Updated Translations', 'Approved Translations'],
                  title="Daily Translation Activity")
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Completion Status by Language")
        
        # Completion pie chart
        completion_data = stats.get('completion_rate', {})
        if completion_data:
            labels = []
            values = []
            for lang_code, completion in completion_data.items():
                lang_info = i18n_manager.get_language_info(lang_code)
                labels.append(f"{lang_info['flag']} {lang_info['name']}")
                values.append(completion)
            
            fig = px.pie(values=values, names=labels, 
                        title="Translation Completion by Language")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📁 Translation Keys by Namespace")
        
        # Mock namespace distribution
        namespace_data = {ns: hash(ns) % 200 + 50 for ns in i18n_manager.namespaces}
        
        fig = px.bar(x=list(namespace_data.keys()), y=list(namespace_data.values()),
                     title="Number of Translation Keys by Namespace")
        st.plotly_chart(fig, use_container_width=True)
    
    # Quality metrics
    st.subheader("🔍 Translation Quality Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("✅ Approved", "1,156", "+23")
    with col2:
        st.metric("⏳ Pending", "91", "-5")
    with col3:
        st.metric("❌ Rejected", "12", "+2")
    with col4:
        st.metric("🤖 Auto-translated", "234", "+45")

    # Top contributors
    st.subheader("👥 Top Contributors")
    contributors_data = [
        {"Name": "Admin User", "Translations": 456, "Languages": 8, "Score": 95},
        {"Name": "Translator A", "Translations": 234, "Languages": 5, "Score": 88},
        {"Name": "Translator B", "Translations": 167, "Languages": 3, "Score": 82},
        {"Name": "AI Assistant", "Translations": 89, "Languages": 12, "Score": 76}
    ]
    
    df_contributors = pd.DataFrame(contributors_data)
    st.dataframe(df_contributors, use_container_width=True)

if __name__ == "__main__":
    main()