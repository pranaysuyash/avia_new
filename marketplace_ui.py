#!/usr/bin/env python3
"""
Marketplace UI Components (Task 51)
Streamlit interface for marketplace and template system
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import time

from marketplace_system import (
    MarketplaceSystem, MarketplaceItem, Template, EntityExtractionRule,
    VoiceModel, ScriptTemplate, MarketplaceItemType, ItemCategory,
    LicenseType, ItemStatus
)

class MarketplaceUI:
    """UI components for marketplace functionality"""
    
    def __init__(self):
        if 'marketplace_system' not in st.session_state:
            st.session_state.marketplace_system = MarketplaceSystem()
        
        self.marketplace = st.session_state.marketplace_system
        
        # Initialize session state
        if 'selected_item' not in st.session_state:
            st.session_state.selected_item = None
        if 'user_collections' not in st.session_state:
            st.session_state.user_collections = []
    
    def render_marketplace_interface(self):
        """Render the main marketplace interface"""
        st.set_page_config(
            page_title="Marketplace & Templates",
            page_icon="🏪",
            layout="wide"
        )
        
        st.title("🏪 Marketplace & Template System")
        
        # Sidebar navigation
        with st.sidebar:
            st.header("Navigation")
            
            page = st.selectbox(
                "Select Section:",
                [
                    "🏪 Marketplace",
                    "📋 Templates",
                    "🔍 Entity Rules",
                    "🎤 Voice Models",
                    "📝 Script Library",
                    "⭐ My Collections",
                    "📤 Upload Content",
                    "📊 Analytics"
                ]
            )
            
            # User info
            st.divider()
            st.subheader("User Info")
            user_id = st.text_input("User ID:", value="demo_user")
            st.session_state.current_user = user_id
        
        # Route to appropriate page
        if page == "🏪 Marketplace":
            self._render_marketplace_overview()
        elif page == "📋 Templates":
            self._render_templates()
        elif page == "🔍 Entity Rules":
            self._render_entity_rules()
        elif page == "🎤 Voice Models":
            self._render_voice_models()
        elif page == "📝 Script Library":
            self._render_script_library()
        elif page == "⭐ My Collections":
            self._render_user_collections()
        elif page == "📤 Upload Content":
            self._render_upload_content()
        elif page == "📊 Analytics":
            self._render_marketplace_analytics()
    
    def _render_marketplace_overview(self):
        """Render marketplace overview"""
        st.header("🏪 Marketplace Overview")
        
        # Get marketplace overview
        overview = self.marketplace.get_marketplace_overview()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Items", f"{overview.get('total_items', 0):,}")
        
        with col2:
            st.metric("Total Downloads", f"{overview.get('total_downloads', 0):,}")
        
        with col3:
            st.metric("Average Rating", f"{overview.get('average_rating', 0):.1f}⭐")
        
        with col4:
            st.metric("New This Week", overview.get('recent_items', 0))
        
        # Search and filters
        st.subheader("🔍 Discover Content")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_query = st.text_input(
                "Search marketplace:",
                placeholder="Search templates, rules, voices, scripts..."
            )
        
        with col2:
            item_type_filter = st.selectbox(
                "Item Type:",
                options=["All"] + [t.value.title() for t in MarketplaceItemType],
                index=0
            )
        
        with col3:
            category_filter = st.selectbox(
                "Category:",
                options=["All"] + [c.value.title() for c in ItemCategory],
                index=0
            )
        
        # Search results
        if search_query or item_type_filter != "All" or category_filter != "All":
            with st.spinner("Searching marketplace..."):
                results = self.marketplace.search_marketplace(
                    search_query or "",
                    item_type=item_type_filter.lower() if item_type_filter != "All" else None,
                    category=category_filter.lower() if category_filter != "All" else None
                )
                
                st.subheader(f"📋 Search Results ({len(results)} found)")
                self._display_marketplace_items(results)
        
        # Featured items
        st.subheader("⭐ Featured Items")
        featured_items = self.marketplace.get_featured_items(limit=6)
        self._display_marketplace_items(featured_items, columns=3)
        
        # Trending items
        st.subheader("🔥 Trending This Week")
        trending_items = self.marketplace.community.get_trending_items(limit=6)
        self._display_marketplace_items(trending_items, columns=3)
        
        # Categories overview
        st.subheader("📊 Browse by Category")
        
        items_by_type = overview.get('items_by_type', {})
        if items_by_type:
            col1, col2 = st.columns(2)
            
            with col1:
                # Items by type chart
                fig = px.pie(
                    values=list(items_by_type.values()),
                    names=[t.title() for t in items_by_type.keys()],
                    title="Items by Type"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Category buttons
                st.write("**Quick Browse:**")
                
                for item_type, count in items_by_type.items():
                    if st.button(f"{item_type.title()} ({count})", key=f"browse_{item_type}"):
                        # Filter by this type
                        type_items = self.marketplace.db.get_marketplace_items(
                            item_type=item_type, limit=20
                        )
                        st.session_state.browse_results = type_items
                        st.rerun()
        
        # Display browse results if available
        if 'browse_results' in st.session_state:
            st.subheader("📋 Browse Results")
            self._display_marketplace_items(st.session_state.browse_results)
            
            if st.button("Clear Results"):
                del st.session_state.browse_results
                st.rerun()
    
    def _render_templates(self):
        """Render templates section"""
        st.header("📋 Template Marketplace")
        
        # Template categories
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("Categories")
            
            categories = self.marketplace.template_marketplace.template_categories
            selected_category = st.radio(
                "Select Category:",
                options=["All"] + list(categories.keys()),
                format_func=lambda x: categories.get(x, x).title() if x != "All" else "All Categories"
            )
        
        with col2:
            # Get templates
            if selected_category == "All":
                templates = self.marketplace.template_marketplace.get_templates()
            else:
                templates = self.marketplace.template_marketplace.get_templates(category=selected_category)
            
            st.subheader(f"Available Templates ({len(templates)})")
            
            # Search templates
            search_query = st.text_input("Search templates:", placeholder="Search by name or description...")
            
            if search_query:
                templates = self.marketplace.template_marketplace.search_templates(
                    search_query, selected_category if selected_category != "All" else None
                )
            
            # Display templates
            for template in templates:
                with st.expander(f"📋 {template.name}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {template.description}")
                        st.write(f"**Use Case:** {template.use_case}")
                        st.write(f"**Category:** {template.category.title()}")
                        
                        if template.tags:
                            st.write(f"**Tags:** {', '.join(template.tags)}")
                    
                    with col2:
                        st.write(f"**Downloads:** {template.download_count:,}")
                        st.write(f"**Rating:** {template.rating:.1f}⭐")
                        st.write(f"**Created:** {template.created_at.strftime('%Y-%m-%d')}")
                        
                        if st.button(f"Use Template", key=f"use_template_{template.template_id}"):
                            self._show_template_usage(template)
                        
                        if st.button(f"Download", key=f"download_template_{template.template_id}"):
                            self._download_template(template)
        
        # Create new template section
        st.divider()
        st.subheader("➕ Create New Template")
        
        with st.expander("Create Template"):
            self._render_create_template_form()
    
    def _render_entity_rules(self):
        """Render entity extraction rules section"""
        st.header("🔍 Entity Extraction Rules")
        
        # Entity types
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("Entity Types")
            
            entity_types = self.marketplace.entity_marketplace.entity_types
            selected_type = st.radio(
                "Select Type:",
                options=["All"] + list(entity_types.keys()),
                format_func=lambda x: entity_types.get(x, x) if x != "All" else "All Types"
            )
        
        with col2:
            # Get entity rules
            if selected_type == "All":
                rules = self.marketplace.entity_marketplace.get_entity_rules()
            else:
                rules = self.marketplace.entity_marketplace.get_entity_rules(entity_type=selected_type)
            
            st.subheader(f"Available Rules ({len(rules)})")
            
            # Display rules
            for rule in rules:
                with st.expander(f"🔍 {rule.name}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {rule.description}")
                        st.write(f"**Entity Type:** {rule.entity_type}")
                        st.write(f"**Pattern:** `{rule.pattern}`")
                        
                        if rule.regex_pattern:
                            st.write(f"**Regex:** `{rule.regex_pattern}`")
                        
                        if rule.examples:
                            st.write("**Examples:**")
                            for example in rule.examples[:3]:
                                st.write(f"• {example}")
                    
                    with col2:
                        st.write(f"**Accuracy:** {rule.accuracy_score:.1f}%")
                        st.write(f"**Usage Count:** {rule.usage_count:,}")
                        st.write(f"**Created:** {rule.created_at.strftime('%Y-%m-%d')}")
                        
                        # Test rule
                        st.write("**Test Rule:**")
                        test_text = st.text_area(
                            "Test text:",
                            placeholder="Enter text to test the rule...",
                            key=f"test_{rule.rule_id}",
                            height=100
                        )
                        
                        if st.button(f"Test", key=f"test_rule_{rule.rule_id}") and test_text:
                            result = self.marketplace.entity_marketplace.test_entity_rule(
                                rule.rule_id, test_text
                            )
                            
                            if 'matches' in result:
                                st.success(f"Found {result['match_count']} matches:")
                                for match in result['matches']:
                                    st.write(f"• **{match['text']}** ({match['entity_type']})")
                            else:
                                st.error(result.get('error', 'No matches found'))
        
        # Create new rule section
        st.divider()
        st.subheader("➕ Create New Entity Rule")
        
        with st.expander("Create Entity Rule"):
            self._render_create_entity_rule_form()
    
    def _render_voice_models(self):
        """Render voice models section"""
        st.header("🎤 Voice Model Library")
        
        # Voice filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            language_filter = st.selectbox(
                "Language:",
                options=["All"] + list(self.marketplace.voice_marketplace.supported_languages.values()),
                index=0
            )
        
        with col2:
            gender_filter = st.selectbox(
                "Gender:",
                options=["All", "Male", "Female", "Neutral"],
                index=0
            )
        
        with col3:
            accent_filter = st.selectbox(
                "Accent:",
                options=["All", "American", "British", "Australian", "Canadian"],
                index=0
            )
        
        # Get voice models
        language_code = None
        if language_filter != "All":
            # Find language code
            for code, name in self.marketplace.voice_marketplace.supported_languages.items():
                if name == language_filter:
                    language_code = code
                    break
        
        voice_models = self.marketplace.voice_marketplace.get_voice_models(
            language=language_code,
            gender=gender_filter.lower() if gender_filter != "All" else None
        )
        
        st.subheader(f"Available Voice Models ({len(voice_models)})")
        
        # Display voice models
        for model in voice_models:
            with st.expander(f"🎤 {model.name}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Description:** {model.description}")
                    st.write(f"**Language:** {model.language.upper()}")
                    st.write(f"**Gender:** {model.gender.title()}")
                    st.write(f"**Accent:** {model.accent.title()}")
                    
                    # Voice preview
                    st.write("**Preview:**")
                    preview_text = st.text_input(
                        "Preview text:",
                        value="Hello, this is a sample of my voice.",
                        key=f"preview_{model.model_id}"
                    )
                    
                    if st.button(f"Generate Preview", key=f"preview_voice_{model.model_id}"):
                        preview_result = self.marketplace.voice_marketplace.preview_voice_model(
                            model.model_id, preview_text
                        )
                        
                        if 'audio_url' in preview_result:
                            st.success("Preview generated!")
                            st.write(f"Duration: {preview_result['estimated_duration']:.1f} seconds")
                            st.info("In production, audio player would be displayed here")
                        else:
                            st.error(preview_result.get('error', 'Preview failed'))
                
                with col2:
                    st.write(f"**Quality Score:** {model.quality_score:.1f}/10")
                    st.write(f"**Downloads:** {model.download_count:,}")
                    st.write(f"**File Size:** {model.file_size / 1024 / 1024:.1f} MB" if model.file_size > 0 else "N/A")
                    st.write(f"**Created:** {model.created_at.strftime('%Y-%m-%d')}")
                    
                    if st.button(f"Download Model", key=f"download_voice_{model.model_id}"):
                        self._download_voice_model(model)
        
        # Upload new voice model
        st.divider()
        st.subheader("➕ Upload Voice Model")
        
        with st.expander("Upload Voice Model"):
            self._render_upload_voice_model_form()
    
    def _render_script_library(self):
        """Render script template library"""
        st.header("📝 Script Template Library")
        
        # Script categories
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("Categories")
            
            categories = self.marketplace.script_library.template_categories
            selected_category = st.radio(
                "Select Category:",
                options=["All"] + list(categories.keys()),
                format_func=lambda x: categories.get(x, x).title() if x != "All" else "All Categories"
            )
        
        with col2:
            # Get script templates
            if selected_category == "All":
                scripts = self.marketplace.script_library.get_script_templates()
            else:
                scripts = self.marketplace.script_library.get_script_templates(category=selected_category)
            
            st.subheader(f"Available Scripts ({len(scripts)})")
            
            # Display script templates
            for script in scripts:
                with st.expander(f"📝 {script.name}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {script.description}")
                        st.write(f"**Category:** {script.category.title()}")
                        
                        # Show template content (truncated)
                        content_preview = script.template_content[:200] + "..." if len(script.template_content) > 200 else script.template_content
                        st.write(f"**Template:**")
                        st.code(content_preview)
                        
                        # Variables
                        if script.variables:
                            st.write(f"**Variables:** {', '.join(script.variables)}")
                        
                        # Examples
                        if script.examples:
                            st.write("**Examples:**")
                            for example in script.examples[:2]:
                                st.write(f"• {example}")
                    
                    with col2:
                        st.write(f"**Usage Count:** {script.usage_count:,}")
                        st.write(f"**Rating:** {script.rating:.1f}⭐")
                        st.write(f"**Created:** {script.created_at.strftime('%Y-%m-%d')}")
                        
                        # Generate script
                        st.write("**Generate Script:**")
                        
                        if script.variables:
                            variable_values = {}
                            for var in script.variables:
                                variable_values[var] = st.text_input(
                                    f"{var}:",
                                    key=f"var_{script.template_id}_{var}",
                                    placeholder=f"Enter {var}..."
                                )
                            
                            if st.button(f"Generate", key=f"generate_{script.template_id}"):
                                if all(variable_values.values()):
                                    result = self.marketplace.script_library.generate_script(
                                        script.template_id, variable_values
                                    )
                                    
                                    if 'generated_content' in result:
                                        st.success("Script generated!")
                                        st.text_area(
                                            "Generated Script:",
                                            value=result['generated_content'],
                                            height=150,
                                            key=f"generated_{script.template_id}"
                                        )
                                        st.write(f"Word count: {result['word_count']}")
                                    else:
                                        st.error(result.get('error', 'Generation failed'))
                                else:
                                    st.warning("Please fill in all variables")
        
        # Create new script template
        st.divider()
        st.subheader("➕ Create New Script Template")
        
        with st.expander("Create Script Template"):
            self._render_create_script_template_form()    def
 _render_user_collections(self):
        """Render user collections"""
        st.header("⭐ My Collections")
        
        user_id = st.session_state.get('current_user', 'demo_user')
        
        # Create new collection
        with st.expander("➕ Create New Collection"):
            with st.form("create_collection"):
                col1, col2 = st.columns(2)
                
                with col1:
                    collection_name = st.text_input("Collection Name:")
                    is_public = st.checkbox("Make Public")
                
                with col2:
                    description = st.text_area("Description:", height=100)
                
                if st.form_submit_button("Create Collection"):
                    if collection_name:
                        collection_id = self.marketplace.community.create_user_collection(
                            user_id, collection_name, description, is_public
                        )
                        
                        if collection_id:
                            st.success(f"Collection '{collection_name}' created!")
                            st.rerun()
                        else:
                            st.error("Failed to create collection")
                    else:
                        st.error("Please enter a collection name")
        
        # Display existing collections (mock data for demo)
        st.subheader("📚 Your Collections")
        
        # Mock collections for demo
        mock_collections = [
            {
                'name': 'Meeting Templates',
                'description': 'Templates for various meeting types',
                'item_count': 5,
                'is_public': False,
                'created_at': datetime.now() - timedelta(days=10)
            },
            {
                'name': 'Voice Models',
                'description': 'Favorite voice models for TTS',
                'item_count': 3,
                'is_public': True,
                'created_at': datetime.now() - timedelta(days=5)
            }
        ]
        
        for i, collection in enumerate(mock_collections):
            with st.expander(f"📁 {collection['name']} ({collection['item_count']} items)"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Description:** {collection['description']}")
                    st.write(f"**Visibility:** {'Public' if collection['is_public'] else 'Private'}")
                    st.write(f"**Created:** {collection['created_at'].strftime('%Y-%m-%d')}")
                
                with col2:
                    if st.button(f"View Items", key=f"view_collection_{i}"):
                        st.info("Collection items would be displayed here")
                    
                    if st.button(f"Edit", key=f"edit_collection_{i}"):
                        st.info("Edit collection functionality would be implemented here")
                    
                    if st.button(f"Delete", key=f"delete_collection_{i}"):
                        st.warning("Delete collection functionality would be implemented here")
    
    def _render_upload_content(self):
        """Render content upload interface"""
        st.header("📤 Upload Content")
        
        # Content type selection
        content_type = st.selectbox(
            "What would you like to upload?",
            options=[
                "📋 Template",
                "🔍 Entity Rule",
                "🎤 Voice Model",
                "📝 Script Template"
            ]
        )
        
        if content_type == "📋 Template":
            self._render_create_template_form()
        elif content_type == "🔍 Entity Rule":
            self._render_create_entity_rule_form()
        elif content_type == "🎤 Voice Model":
            self._render_upload_voice_model_form()
        elif content_type == "📝 Script Template":
            self._render_create_script_template_form()
    
    def _render_marketplace_analytics(self):
        """Render marketplace analytics"""
        st.header("📊 Marketplace Analytics")
        
        # Get overview data
        overview = self.marketplace.get_marketplace_overview()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Items", f"{overview.get('total_items', 0):,}")
        
        with col2:
            st.metric("Total Downloads", f"{overview.get('total_downloads', 0):,}")
        
        with col3:
            st.metric("Average Rating", f"{overview.get('average_rating', 0):.1f}⭐")
        
        with col4:
            st.metric("New This Week", overview.get('recent_items', 0))
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Items by type
            items_by_type = overview.get('items_by_type', {})
            if items_by_type:
                fig = px.pie(
                    values=list(items_by_type.values()),
                    names=[t.title() for t in items_by_type.keys()],
                    title="Items by Type"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Mock download trends
            dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, 0, -1)]
            downloads = [45, 52, 38, 61, 47, 55, 63]
            
            fig = px.line(
                x=dates,
                y=downloads,
                title="Daily Downloads (Last 7 Days)",
                labels={'x': 'Date', 'y': 'Downloads'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Popular items
        st.subheader("🔥 Most Popular Items")
        
        featured_items = self.marketplace.get_featured_items(limit=5)
        
        if featured_items:
            for item in featured_items:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{item.name}** ({item.item_type.title()})")
                    st.write(item.description[:100] + "..." if len(item.description) > 100 else item.description)
                
                with col2:
                    st.write(f"⭐ {item.rating:.1f}")
                
                with col3:
                    st.write(f"📥 {item.download_count:,}")
                
                with col4:
                    st.write(f"💰 ${item.price:.2f}" if item.price > 0 else "Free")
        
        # User contributions
        st.subheader("👥 Top Contributors")
        
        # Mock contributor data
        contributors = [
            {'name': 'User_001', 'items': 12, 'downloads': 1250, 'rating': 4.8},
            {'name': 'User_002', 'items': 8, 'downloads': 890, 'rating': 4.6},
            {'name': 'User_003', 'items': 15, 'downloads': 2100, 'rating': 4.9},
        ]
        
        df_contributors = pd.DataFrame(contributors)
        st.dataframe(df_contributors, use_container_width=True)
    
    def _display_marketplace_items(self, items: List[MarketplaceItem], columns: int = 2):
        """Display marketplace items in a grid"""
        if not items:
            st.info("No items found.")
            return
        
        # Create columns
        cols = st.columns(columns)
        
        for i, item in enumerate(items):
            with cols[i % columns]:
                with st.container():
                    # Item header
                    st.subheader(f"{item.name}")
                    st.write(f"*{item.item_type.title()} • {item.category.title()}*")
                    
                    # Description
                    description = item.description[:150] + "..." if len(item.description) > 150 else item.description
                    st.write(description)
                    
                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"⭐ {item.rating:.1f}")
                    with col2:
                        st.write(f"📥 {item.download_count:,}")
                    with col3:
                        st.write(f"💰 ${item.price:.2f}" if item.price > 0 else "Free")
                    
                    # Tags
                    if item.tags:
                        tag_text = " ".join([f"`{tag}`" for tag in item.tags[:3]])
                        st.write(tag_text)
                    
                    # Actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"View Details", key=f"view_{item.item_id}"):
                            self._show_item_details(item)
                    
                    with col2:
                        if st.button(f"Download", key=f"download_{item.item_id}"):
                            self._download_item(item)
                    
                    st.divider()
    
    def _render_create_template_form(self):
        """Render create template form"""
        with st.form("create_template"):
            st.subheader("Create New Template")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Template Name:")
                category = st.selectbox(
                    "Category:",
                    options=list(self.marketplace.template_marketplace.template_categories.keys())
                )
                use_case = st.text_input("Use Case:")
            
            with col2:
                description = st.text_area("Description:", height=100)
                tags = st.text_input("Tags (comma-separated):")
            
            # Template data
            st.write("**Template Configuration:**")
            
            sections = st.text_area(
                "Sections (one per line):",
                placeholder="Introduction\nMain Content\nConclusion",
                height=100
            )
            
            fields = st.text_area(
                "Fields (one per line):",
                placeholder="title\ndate\nauthor",
                height=100
            )
            
            if st.form_submit_button("Create Template"):
                if name and description and category:
                    template_data = {
                        "sections": [s.strip() for s in sections.split('\n') if s.strip()],
                        "fields": [f.strip() for f in fields.split('\n') if f.strip()],
                        "format": "structured"
                    }
                    
                    tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []
                    
                    template_id = self.marketplace.template_marketplace.create_template(
                        name, description, category, use_case or "General use",
                        template_data, st.session_state.get('current_user', 'demo_user'), tag_list
                    )
                    
                    if template_id:
                        st.success(f"Template '{name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create template")
                else:
                    st.error("Please fill in all required fields")
    
    def _render_create_entity_rule_form(self):
        """Render create entity rule form"""
        with st.form("create_entity_rule"):
            st.subheader("Create New Entity Rule")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Rule Name:")
                entity_type = st.selectbox(
                    "Entity Type:",
                    options=list(self.marketplace.entity_marketplace.entity_types.keys())
                )
                pattern = st.text_input("Pattern:", placeholder="Inc|LLC|Corp|Ltd")
            
            with col2:
                description = st.text_area("Description:", height=100)
                regex_pattern = st.text_input("Regex Pattern (optional):", placeholder=r'\b[A-Z][a-zA-Z\s]+(?:Inc|LLC|Corp|Ltd)\b')
            
            # Context rules and examples
            context_rules = st.text_area(
                "Context Rules (one per line):",
                placeholder="Must be followed by business terms\nShould be capitalized",
                height=80
            )
            
            examples = st.text_area(
                "Examples (one per line):",
                placeholder="Apple Inc\nMicrosoft Corporation\nGoogle LLC",
                height=80
            )
            
            if st.form_submit_button("Create Rule"):
                if name and description and entity_type and pattern:
                    context_list = [c.strip() for c in context_rules.split('\n') if c.strip()] if context_rules else []
                    example_list = [e.strip() for e in examples.split('\n') if e.strip()] if examples else []
                    
                    rule_id = self.marketplace.entity_marketplace.create_entity_rule(
                        name, description, entity_type, pattern,
                        st.session_state.get('current_user', 'demo_user'),
                        regex_pattern or None, context_list, example_list
                    )
                    
                    if rule_id:
                        st.success(f"Entity rule '{name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create entity rule")
                else:
                    st.error("Please fill in all required fields")
    
    def _render_upload_voice_model_form(self):
        """Render upload voice model form"""
        with st.form("upload_voice_model"):
            st.subheader("Upload Voice Model")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Voice Name:")
                language = st.selectbox(
                    "Language:",
                    options=list(self.marketplace.voice_marketplace.supported_languages.keys()),
                    format_func=lambda x: self.marketplace.voice_marketplace.supported_languages[x]
                )
                gender = st.selectbox("Gender:", options=["male", "female", "neutral"])
            
            with col2:
                description = st.text_area("Description:", height=100)
                accent = st.selectbox("Accent:", options=["american", "british", "australian", "canadian", "neutral"])
            
            # File upload
            model_file = st.file_uploader(
                "Voice Model File:",
                type=['wav', 'mp3', 'flac'],
                help="Upload the voice model file"
            )
            
            sample_audio = st.file_uploader(
                "Sample Audio (optional):",
                type=['wav', 'mp3'],
                help="Upload a sample audio file to preview the voice"
            )
            
            if st.form_submit_button("Upload Voice Model"):
                if name and description and language and gender and accent:
                    # In production, would handle file upload and processing
                    model_id = self.marketplace.voice_marketplace.add_voice_model(
                        name, description, language, gender, accent,
                        st.session_state.get('current_user', 'demo_user')
                    )
                    
                    if model_id:
                        st.success(f"Voice model '{name}' uploaded successfully!")
                        st.info("In production, the uploaded files would be processed and stored.")
                        st.rerun()
                    else:
                        st.error("Failed to upload voice model")
                else:
                    st.error("Please fill in all required fields")
    
    def _render_create_script_template_form(self):
        """Render create script template form"""
        with st.form("create_script_template"):
            st.subheader("Create New Script Template")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Template Name:")
                category = st.selectbox(
                    "Category:",
                    options=list(self.marketplace.script_library.template_categories.keys())
                )
            
            with col2:
                description = st.text_area("Description:", height=100)
            
            # Template content
            template_content = st.text_area(
                "Template Content:",
                placeholder="Welcome to {podcast_name}, I'm your host {host_name}...",
                height=150,
                help="Use {variable_name} for variables that users can customize"
            )
            
            # Variables
            variables = st.text_input(
                "Variables (comma-separated):",
                placeholder="podcast_name, host_name, topic",
                help="List the variables used in your template"
            )
            
            # Examples
            examples = st.text_area(
                "Examples (one per line):",
                placeholder="Welcome to Tech Talk, I'm your host John Smith...",
                height=100
            )
            
            if st.form_submit_button("Create Script Template"):
                if name and description and category and template_content and variables:
                    variable_list = [v.strip() for v in variables.split(',') if v.strip()]
                    example_list = [e.strip() for e in examples.split('\n') if e.strip()] if examples else []
                    
                    template_id = self.marketplace.script_library.create_script_template(
                        name, description, category, template_content, variable_list,
                        st.session_state.get('current_user', 'demo_user'), example_list
                    )
                    
                    if template_id:
                        st.success(f"Script template '{name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create script template")
                else:
                    st.error("Please fill in all required fields")
    
    def _show_item_details(self, item: MarketplaceItem):
        """Show detailed item information"""
        with st.expander(f"📋 {item.name} - Details", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Description:** {item.description}")
                st.write(f"**Type:** {item.item_type.title()}")
                st.write(f"**Category:** {item.category.title()}")
                st.write(f"**Version:** {item.version}")
                st.write(f"**License:** {item.license_type.title()}")
                
                if item.tags:
                    st.write(f"**Tags:** {', '.join(item.tags)}")
                
                if item.requirements:
                    st.write("**Requirements:**")
                    for req in item.requirements:
                        st.write(f"• {req}")
            
            with col2:
                st.write(f"**Author:** {item.author_name}")
                st.write(f"**Created:** {item.created_at.strftime('%Y-%m-%d')}")
                st.write(f"**Updated:** {item.updated_at.strftime('%Y-%m-%d')}")
                st.write(f"**Downloads:** {item.download_count:,}")
                st.write(f"**Rating:** {item.rating:.1f}⭐ ({item.rating_count} reviews)")
                st.write(f"**Price:** ${item.price:.2f}" if item.price > 0 else "Free")
            
            # Reviews section
            st.subheader("📝 Reviews")
            reviews = self.marketplace.community.get_reviews(item.item_id, limit=3)
            
            if reviews:
                for review in reviews:
                    st.write(f"**{review.user_id}** - {'⭐' * review.rating}")
                    st.write(review.comment)
                    st.write(f"*{review.created_at.strftime('%Y-%m-%d')}*")
                    st.divider()
            else:
                st.info("No reviews yet. Be the first to review!")
            
            # Add review
            with st.form(f"add_review_{item.item_id}"):
                st.write("**Add Your Review:**")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    rating = st.selectbox("Rating:", options=[1, 2, 3, 4, 5], index=4)
                with col2:
                    comment = st.text_area("Comment:", placeholder="Share your experience...")
                
                if st.form_submit_button("Submit Review"):
                    if comment:
                        review_id = self.marketplace.community.add_review(
                            item.item_id, st.session_state.get('current_user', 'demo_user'),
                            rating, comment
                        )
                        
                        if review_id:
                            st.success("Review submitted!")
                            st.rerun()
                        else:
                            st.error("Failed to submit review")
                    else:
                        st.error("Please enter a comment")
    
    def _download_item(self, item: MarketplaceItem):
        """Download marketplace item"""
        result = self.marketplace.download_item(
            item.item_id, st.session_state.get('current_user', 'demo_user')
        )
        
        if 'error' in result:
            st.error(result['error'])
        else:
            st.success(f"Downloaded {item.name}!")
            st.info("In production, the download would start automatically.")
    
    def _download_template(self, template: Template):
        """Download template"""
        st.success(f"Downloaded template: {template.name}")
        st.json(template.template_data)
    
    def _download_voice_model(self, model: VoiceModel):
        """Download voice model"""
        st.success(f"Downloaded voice model: {model.name}")
        st.info("In production, the voice model file would be downloaded.")
    
    def _show_template_usage(self, template: Template):
        """Show template usage interface"""
        with st.expander(f"📋 Using Template: {template.name}", expanded=True):
            st.write("**Template Data:**")
            st.json(template.template_data)
            
            st.write("**How to use:**")
            st.write("1. Copy the template structure")
            st.write("2. Customize the sections and fields for your needs")
            st.write("3. Apply to your transcription workflow")
            
            if st.button(f"Apply Template", key=f"apply_{template.template_id}"):
                st.success("Template applied to your workspace!")

def main():
    """Main function for testing the UI"""
    marketplace_ui = MarketplaceUI()
    marketplace_ui.render_marketplace_interface()

if __name__ == "__main__":
    main()