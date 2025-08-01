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
        st.info(f"Testing interface not implemented for {metadata.plugin_type.value} plugins")
    
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