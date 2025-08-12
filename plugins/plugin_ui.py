"""
Streamlit UI components for plugin management
"""

import streamlit as st
import json
from typing import Dict, Any, List
from .plugin_manager import plugin_manager, PluginType, PluginStatus


def render_plugin_settings():
    """Render plugin management interface"""
    
    st.header("🔌 Plugin Settings")
    
    # System status
    stats = plugin_manager.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Plugins", stats['total_plugins'])
    with col2:
        st.metric("Active Plugins", stats['active_plugins'])
    with col3:
        st.metric("Plugin Types", len(stats['plugin_types']))
    with col4:
        st.metric("Hooks Registered", stats['hooks_registered'])
    
    # Tabs for different plugin management functions
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Installed Plugins", "➕ Add Plugin", "🛠️ Plugin Store", "📊 Statistics"])
    
    with tab1:
        render_installed_plugins()
    
    with tab2:
        render_add_plugin()
    
    with tab3:
        render_plugin_store()
    
    with tab4:
        render_plugin_statistics()


def render_installed_plugins():
    """Render list of installed plugins"""
    
    st.subheader("Installed Plugins")
    
    plugins = plugin_manager.list_plugins()
    
    if not plugins:
        st.info("No plugins installed.")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox(
            "Filter by Type",
            options=["All"] + [t.value for t in PluginType],
            index=0
        )
    
    with col2:
        filter_status = st.selectbox(
            "Filter by Status", 
            options=["All"] + [s.value for s in PluginStatus],
            index=0
        )
    
    # Plugin list
    for plugin_id, plugin in plugins:
        metadata = plugin.get_metadata()
        
        # Apply filters
        if filter_type != "All" and metadata.plugin_type.value != filter_type:
            continue
        if filter_status != "All" and plugin.status.value != filter_status:
            continue
        
        # Plugin card
        with st.expander(f"🔌 {metadata.name} v{metadata.version} {'✅' if plugin.status == PluginStatus.ACTIVE else '❌'}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Information:**")
                st.write(f"• **ID:** `{plugin_id}`")
                st.write(f"• **Type:** {metadata.plugin_type.value.replace('_', ' ').title()}")
                st.write(f"• **Status:** {plugin.status.value.title()}")
                st.write(f"• **Author:** {metadata.author}")
                st.write(f"• **Created:** {metadata.created_at.strftime('%Y-%m-%d')}")
                
                if plugin.error_message:
                    st.error(f"**Error:** {plugin.error_message}")
                
                if plugin.last_executed:
                    st.write(f"• **Last Executed:** {plugin.last_executed.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                st.write("**Description:**")
                st.write(metadata.description)
                
                if metadata.dependencies:
                    st.write("**Dependencies:**")
                    for dep in metadata.dependencies:
                        st.write(f"• {dep}")
            
            # Plugin actions
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if plugin.status == PluginStatus.INACTIVE:
                    if st.button("▶️ Activate", key=f"activate_{plugin_id}"):
                        import asyncio
                        success = asyncio.run(plugin_manager.initialize_plugin(plugin_id))
                        if success:
                            st.success("Plugin activated!")
                            st.rerun()
                        else:
                            st.error("Failed to activate plugin")
                else:
                    if st.button("⏸️ Deactivate", key=f"deactivate_{plugin_id}"):
                        plugin.status = PluginStatus.INACTIVE
                        st.success("Plugin deactivated!")
                        st.rerun()
            
            with col2:
                if st.button("⚙️ Configure", key=f"config_{plugin_id}"):
                    st.session_state[f"configure_plugin_{plugin_id}"] = True
                    st.rerun()
            
            with col3:
                if st.button("🧪 Test", key=f"test_{plugin_id}"):
                    st.session_state[f"test_plugin_{plugin_id}"] = True
                    st.rerun()
            
            with col4:
                if st.button("🗑️ Remove", key=f"remove_{plugin_id}", type="secondary"):
                    if st.session_state.get(f"confirm_remove_{plugin_id}", False):
                        plugin_manager.unregister_plugin(plugin_id)
                        st.success("Plugin removed!")
                        st.rerun()
                    else:
                        st.session_state[f"confirm_remove_{plugin_id}"] = True
                        st.warning("Click again to confirm removal")
            
            # Handle configuration
            if st.session_state.get(f"configure_plugin_{plugin_id}", False):
                render_plugin_configuration(plugin_id, plugin)
            
            # Handle testing
            if st.session_state.get(f"test_plugin_{plugin_id}", False):
                render_plugin_test(plugin_id, plugin)


def render_plugin_configuration(plugin_id: str, plugin):
    """Render plugin configuration interface"""
    
    st.write("---")
    st.write("**Plugin Configuration:**")
    
    # Get configuration schema
    config_schema = plugin.get_config_schema()
    current_config = plugin.config
    
    with st.form(f"config_form_{plugin_id}"):
        new_config = {}
        
        if config_schema and 'properties' in config_schema:
            for prop_name, prop_schema in config_schema['properties'].items():
                prop_type = prop_schema.get('type', 'string')
                prop_description = prop_schema.get('description', '')
                current_value = current_config.get(prop_name, prop_schema.get('default'))
                
                if prop_type == 'string':
                    new_config[prop_name] = st.text_input(
                        prop_name.replace('_', ' ').title(),
                        value=current_value or '',
                        help=prop_description
                    )
                elif prop_type == 'number':
                    new_config[prop_name] = st.number_input(
                        prop_name.replace('_', ' ').title(),
                        value=float(current_value) if current_value else 0.0,
                        help=prop_description
                    )
                elif prop_type == 'boolean':
                    new_config[prop_name] = st.checkbox(
                        prop_name.replace('_', ' ').title(),
                        value=bool(current_value) if current_value else False,
                        help=prop_description
                    )
                elif prop_type == 'array':
                    # Simple array input as JSON
                    array_value = json.dumps(current_value) if current_value else '[]'
                    array_input = st.text_area(
                        prop_name.replace('_', ' ').title(),
                        value=array_value,
                        help=f"{prop_description} (JSON format)"
                    )
                    try:
                        new_config[prop_name] = json.loads(array_input)
                    except json.JSONDecodeError:
                        st.error(f"Invalid JSON for {prop_name}")
                        new_config[prop_name] = current_value
        else:
            # Generic JSON configuration
            config_json = json.dumps(current_config, indent=2)
            config_input = st.text_area(
                "Configuration (JSON)",
                value=config_json,
                height=200
            )
            
            try:
                new_config = json.loads(config_input)
            except json.JSONDecodeError:
                st.error("Invalid JSON configuration")
                new_config = current_config
        
        # Submit buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Configuration", type="primary"):
                if plugin.update_config(new_config):
                    plugin_manager.save_plugin_config(plugin_id, new_config)
                    st.success("✅ Configuration saved!")
                    st.session_state[f"configure_plugin_{plugin_id}"] = False
                    st.rerun()
                else:
                    st.error("❌ Invalid configuration")
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state[f"configure_plugin_{plugin_id}"] = False
                st.rerun()


def render_plugin_test(plugin_id: str, plugin):
    """Render plugin testing interface"""
    
    st.write("---")
    st.write("**Plugin Test:**")
    
    metadata = plugin.get_metadata()
    
    if metadata.plugin_type == PluginType.ENTITY_EXTRACTION:
        # Entity extraction plugin test
        test_text = st.text_area(
            "Test Text",
            value="John Smith works at Microsoft in Seattle. He can be reached at john@microsoft.com or (555) 123-4567.",
            height=100
        )
        
        if st.button("🧪 Test Entity Extraction", key=f"test_run_{plugin_id}"):
            if plugin.status == PluginStatus.ACTIVE:
                try:
                    import asyncio
                    entities = asyncio.run(plugin_manager.execute_plugin(plugin_id, test_text))
                    
                    st.write("**Extracted Entities:**")
                    if entities:
                        for entity in entities:
                            st.write(f"• **{entity.entity_type}**: {entity.text} (confidence: {entity.confidence:.2f})")
                    else:
                        st.info("No entities extracted")
                        
                except Exception as e:
                    st.error(f"Test failed: {e}")
            else:
                st.error("Plugin must be active to test")
    
    else:
        # Implement testing interface based on plugin type
        if metadata.plugin_type == PluginType.TRANSCRIPTION:
            st.subheader("🎙️ Transcription Plugin Test")
            test_audio = st.file_uploader("Upload test audio", type=['wav', 'mp3', 'm4a'])
            if test_audio and st.button("Transcribe Audio"):
                try:
                    # Mock transcription test
                    st.success("Mock transcription result would appear here")
                    st.text_area("Transcription Result", 
                               value=f"[Mock] Transcription of {test_audio.name} would appear here...",
                               height=200)
                except Exception as e:
                    st.error(f"Transcription test failed: {e}")
                    
        elif metadata.plugin_type == PluginType.NER:
            st.subheader("🔍 NER Plugin Test")
            test_text = st.text_area("Enter test text", 
                                   placeholder="Enter text to extract entities from...")
            if test_text and st.button("Extract Entities"):
                try:
                    # Mock NER test
                    st.success("Mock entity extraction result would appear here")
                    st.json({
                        "entities": [
                            {"text": "John Doe", "type": "PERSON", "confidence": 0.95},
                            {"text": "New York", "type": "LOCATION", "confidence": 0.87}
                        ]
                    })
                except Exception as e:
                    st.error(f"NER test failed: {e}")
                    
        elif metadata.plugin_type == PluginType.TRANSLATION:
            st.subheader("🌐 Translation Plugin Test")
            source_text = st.text_area("Source text", 
                                     placeholder="Enter text to translate...")
            target_lang = st.selectbox("Target language", 
                                     options=["es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"])
            if source_text and st.button("Translate"):
                try:
                    # Mock translation test
                    st.success("Mock translation result would appear here")
                    st.text_area("Translation Result", 
                               value=f"[{target_lang.upper()}] {source_text}",
                               height=100)
                except Exception as e:
                    st.error(f"Translation test failed: {e}")
                    
        elif metadata.plugin_type == PluginType.TTS:
            st.subheader("🔊 TTS Plugin Test")
            tts_text = st.text_area("Text to synthesize", 
                                  placeholder="Enter text to convert to speech...")
            if tts_text and st.button("Synthesize Speech"):
                try:
                    # Mock TTS test
                    st.success("Mock TTS result would appear here")
                    st.audio(data=None, format="audio/wav")  # Placeholder for audio player
                    st.info("Audio synthesis would be available here with synthesized speech")
                except Exception as e:
                    st.error(f"TTS test failed: {e}")
                    
        else:
            st.info(f"Testing interface not yet implemented for {metadata.plugin_type.value} plugins")
    
    if st.button("❌ Close Test", key=f"close_test_{plugin_id}"):
        st.session_state[f"test_plugin_{plugin_id}"] = False
        st.rerun()


def render_add_plugin():
    """Render add plugin interface"""
    
    st.subheader("Add New Plugin")
    
    # Plugin upload
    st.write("**Upload Plugin File:**")
    uploaded_file = st.file_uploader(
        "Choose plugin file",
        type=['py'],
        help="Upload a Python file containing a plugin class"
    )
    
    if uploaded_file:
        st.info("📁 Plugin file uploaded. In a real implementation, this would:")
        st.write("• Validate the plugin code")
        st.write("• Check for required methods and metadata")
        st.write("• Install dependencies if needed")
        st.write("• Register the plugin")
        
        if st.button("📦 Install Plugin"):
            st.success("✅ Plugin installed successfully! (Mock)")
    
    st.write("---")
    
    # Manual plugin registration
    st.write("**Manual Plugin Registration:**")
    
    with st.form("manual_plugin_form"):
        plugin_name = st.text_input("Plugin Name")
        plugin_type = st.selectbox(
            "Plugin Type",
            options=[t.value for t in PluginType]
        )
        plugin_description = st.text_area("Description")
        
        if st.form_submit_button("➕ Register Plugin"):
            if plugin_name:
                st.success(f"✅ Plugin '{plugin_name}' registered! (Mock)")
            else:
                st.error("❌ Please provide plugin name")


def render_plugin_store():
    """Render plugin store interface"""
    
    st.subheader("Plugin Store")
    
    # Mock plugin store
    available_plugins = [
        {
            'name': 'Medical Entity Extractor',
            'type': 'Entity Extraction',
            'description': 'Specialized entity extraction for medical terminology',
            'author': 'MedTech Solutions',
            'version': '2.1.0',
            'downloads': 1250,
            'rating': 4.8
        },
        {
            'name': 'Legal Document Processor',
            'type': 'Entity Extraction', 
            'description': 'Extract legal entities and case references',
            'author': 'LegalTech Inc',
            'version': '1.5.2',
            'downloads': 890,
            'rating': 4.6
        },
        {
            'name': 'Financial Data Extractor',
            'type': 'Entity Extraction',
            'description': 'Extract financial entities, amounts, and dates',
            'author': 'FinanceAI',
            'version': '3.0.1',
            'downloads': 2100,
            'rating': 4.9
        }
    ]
    
    # Search and filter
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("🔍 Search plugins", placeholder="Enter search term...")
    with col2:
        category_filter = st.selectbox("Filter by Category", ["All", "Entity Extraction", "Preprocessing", "Export"])
    
    # Plugin cards
    for plugin_info in available_plugins:
        if search_term and search_term.lower() not in plugin_info['name'].lower():
            continue
        
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{plugin_info['name']}** v{plugin_info['version']}")
                st.write(f"*{plugin_info['type']} • by {plugin_info['author']}*")
                st.write(plugin_info['description'])
            
            with col2:
                st.metric("Downloads", plugin_info['downloads'])
                st.write(f"⭐ {plugin_info['rating']}/5.0")
            
            with col3:
                if st.button("📦 Install", key=f"install_{plugin_info['name']}"):
                    st.success(f"✅ {plugin_info['name']} installed! (Mock)")
                
                if st.button("ℹ️ Details", key=f"details_{plugin_info['name']}"):
                    st.info("Plugin details would be shown here")
                    # Actually show plugin details
                    with st.expander("📋 Plugin Information", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Plugin ID:** {plugin.plugin_id}")
                            st.write(f"**Name:** {metadata.name}")
                            st.write(f"**Version:** {metadata.version}")
                            st.write(f"**Author:** {metadata.author}")
                        with col2:
                            st.write(f"**Type:** {metadata.plugin_type.value.title()}")
                            st.write(f"**Status:** {plugin.status.value.title()}")
                            st.write(f"**Created:** {plugin.created_at.strftime('%Y-%m-%d %H:%M')}")
                            st.write(f"**Last Updated:** {plugin.updated_at.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Plugin configuration
                    with st.expander("⚙️ Configuration", expanded=False):
                        st.write("Plugin configuration options would be shown here")
                        # Show mock configuration options
                        if metadata.plugin_type == PluginType.TRANSCRIPTION:
                            st.slider("Confidence Threshold", 0.0, 1.0, 0.8, 0.1)
                            st.selectbox("Model Size", ["tiny", "base", "small", "medium", "large"])
                            st.checkbox("Enable Diarization", value=True)
                        elif metadata.plugin_type == PluginType.NER:
                            st.multiselect("Entity Types", 
                                         ["PERSON", "ORGANIZATION", "LOCATION", "DATE", "MONEY"],
                                         default=["PERSON", "ORGANIZATION"])
                            st.slider("Confidence Threshold", 0.0, 1.0, 0.7, 0.1)
                        elif metadata.plugin_type == PluginType.TRANSLATION:
                            st.selectbox("Source Language Detection", ["Auto", "Manual"])
                            st.checkbox("Enable Context Preservation", value=True)
            
            st.write("---")


def render_plugin_statistics():
    """Render plugin system statistics"""
    
    st.subheader("Plugin Statistics")
    
    stats = plugin_manager.get_stats()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Plugins", stats['total_plugins'])
    with col2:
        st.metric("Active Plugins", stats['active_plugins'])
    with col3:
        st.metric("Inactive Plugins", stats['inactive_plugins'])
    with col4:
        st.metric("Error Plugins", stats['error_plugins'])
    
    # Plugin types breakdown
    st.write("**Plugin Types:**")
    if stats['plugin_types']:
        for plugin_type, count in stats['plugin_types'].items():
            st.write(f"• {plugin_type.replace('_', ' ').title()}: {count}")
    else:
        st.info("No plugins installed")
    
    # Usage statistics (mock)
    st.write("---")
    st.write("**Usage Statistics:**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Plugin Executions Today", "127")
    with col2:
        st.metric("Average Execution Time", "0.8s")
    with col3:
        st.metric("Success Rate", "98.4%")
    
    # Performance chart (mock)
    st.write("---")
    st.write("**Performance Trends:**")
    st.info("📊 Performance charts would be displayed here")
    # Actually show performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⏱️ Processing Time")
        # Mock performance data
        import pandas as pd
        import plotly.express as px
        import numpy as np
        
        # Generate mock performance data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        processing_times = np.random.exponential(scale=2.0, size=30)  # Exponential distribution for processing times
        data = pd.DataFrame({
            'Date': dates,
            'Processing Time (seconds)': processing_times
        })
        
        fig = px.line(data, x='Date', y='Processing Time (seconds)', 
                     title='Average Processing Time Over Time')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Success Rate")
        # Generate mock success rate data
        success_rates = np.random.beta(9, 1, size=30)  # High success rate distribution
        data_success = pd.DataFrame({
            'Date': dates,
            'Success Rate (%)': success_rates * 100
        })
        
        fig2 = px.line(data_success, x='Date', y='Success Rate (%)',
                      title='Plugin Success Rate Over Time')
        st.plotly_chart(fig2, use_container_width=True)
    
    # Resource utilization
    st.subheader("💻 Resource Utilization")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cpu_usage = np.random.normal(45, 15, size=30)  # Normal distribution for CPU usage
        cpu_data = pd.DataFrame({
            'Date': dates,
            'CPU Usage (%)': np.clip(cpu_usage, 0, 100)
        })
        fig3 = px.line(cpu_data, x='Date', y='CPU Usage (%)',
                      title='CPU Usage')
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        memory_usage = np.random.normal(60, 20, size=30)  # Normal distribution for memory usage
        memory_data = pd.DataFrame({
            'Date': dates,
            'Memory Usage (%)': np.clip(memory_usage, 0, 100)
        })
        fig4 = px.line(memory_data, x='Date', y='Memory Usage (%)',
                      title='Memory Usage')
        st.plotly_chart(fig4, use_container_width=True)
    
    with col3:
        # Error rates
        error_rates = np.random.exponential(scale=0.5, size=30)  # Low error rate distribution
        error_data = pd.DataFrame({
            'Date': dates,
            'Error Rate (%)': np.clip(error_rates, 0, 10)
        })
        fig5 = px.line(error_data, x='Date', y='Error Rate (%)',
                      title='Error Rate')
        st.plotly_chart(fig5, use_container_width=True)