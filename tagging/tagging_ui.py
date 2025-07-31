"""
UI components for AI-powered tagging
"""

import streamlit as st
from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .tag_manager import TagManager, Tag, TagCategory
from .ai_providers import select_ai_provider, get_available_providers
import json
from datetime import datetime


def render_tagging_view(
    content: str,
    existing_tags: Optional[List[Tag]] = None,
    editable: bool = True
) -> List[Tag]:
    """Render the main tagging interface"""
    
    st.markdown("### 🏷️ AI-Powered Content Tagging")
    
    # Initialize session state
    if 'tags' not in st.session_state:
        st.session_state.tags = existing_tags or []
    
    # Tagging controls
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        # AI Provider selection
        provider = select_ai_provider()
    
    with col2:
        # Category filter
        selected_categories = st.multiselect(
            "Tag Categories",
            [cat.value for cat in TagCategory],
            default=[cat.value for cat in TagCategory][:5],
            help="Select categories to generate tags for"
        )
    
    with col3:
        max_tags = st.number_input(
            "Max Tags",
            min_value=5,
            max_value=50,
            value=20,
            help="Maximum number of tags to generate"
        )
    
    with col4:
        min_confidence = st.slider(
            "Min Confidence",
            0.0, 1.0, 0.5,
            help="Minimum confidence threshold"
        )
    
    # Generate tags button
    if st.button("🤖 Generate Tags", type="primary", disabled=not provider):
        with st.spinner("Analyzing content and generating tags..."):
            # Create tag manager
            manager = TagManager(ai_provider=provider)
            
            # Add custom rules
            _add_default_rules(manager)
            
            # Generate tags
            categories = [TagCategory(cat) for cat in selected_categories]
            tags = manager.generate_tags(
                content,
                max_tags=max_tags,
                min_confidence=min_confidence,
                categories=categories
            )
            
            # Store in session state
            st.session_state.tags = tags
            st.success(f"✅ Generated {len(tags)} tags!")
    
    # Display tags if available
    if st.session_state.tags:
        st.markdown("---")
        
        # Tag display options
        col1, col2 = st.columns([3, 1])
        
        with col1:
            display_mode = st.radio(
                "Display Mode",
                ["Cloud", "List", "Grid", "Analytics"],
                horizontal=True
            )
        
        with col2:
            if st.button("🗑️ Clear All Tags"):
                st.session_state.tags = []
                st.rerun()
        
        # Display tags based on mode
        if display_mode == "Cloud":
            render_tag_cloud(st.session_state.tags)
        elif display_mode == "List":
            st.session_state.tags = render_tag_list(st.session_state.tags, editable)
        elif display_mode == "Grid":
            st.session_state.tags = render_tag_grid(st.session_state.tags, editable)
        else:
            render_tag_analytics(st.session_state.tags, content)
        
        # Suggest related tags
        if st.button("💡 Suggest Related Tags"):
            with st.spinner("Finding related tags..."):
                manager = TagManager(ai_provider=provider)
                suggestions = manager.suggest_related_tags(
                    st.session_state.tags,
                    content,
                    max_suggestions=10
                )
                
                if suggestions:
                    st.markdown("#### Suggested Tags")
                    
                    # Show suggestions with add buttons
                    for i, suggestion in enumerate(suggestions):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"**{suggestion.text}** ({suggestion.category.value})")
                        
                        with col2:
                            st.write(f"{suggestion.confidence:.0%}")
                        
                        with col3:
                            if st.button("➕", key=f"add_suggestion_{i}"):
                                st.session_state.tags.append(suggestion)
                                st.rerun()
                else:
                    st.info("No additional suggestions found")
        
        # Export options
        st.markdown("---")
        render_export_options(st.session_state.tags)
    
    return st.session_state.tags


def render_tag_cloud(tags: List[Tag]):
    """Render tags as a word cloud"""
    
    if not tags:
        st.info("No tags to display")
        return
    
    # Prepare data for word cloud
    tag_html = '<div style="text-align: center; padding: 20px;">'
    
    # Calculate font sizes based on confidence and frequency
    max_confidence = max(tag.confidence for tag in tags)
    max_frequency = max(tag.frequency for tag in tags) or 1
    
    # Define colors for categories
    category_colors = {
        TagCategory.TOPIC: "#2196F3",
        TagCategory.PERSON: "#4CAF50",
        TagCategory.LOCATION: "#FF9800",
        TagCategory.ORGANIZATION: "#9C27B0",
        TagCategory.DATE: "#F44336",
        TagCategory.CONCEPT: "#00BCD4",
        TagCategory.TECHNICAL: "#795548",
        TagCategory.SENTIMENT: "#FFEB3B",
        TagCategory.ACTION: "#FF5722",
        TagCategory.PRODUCT: "#E91E63",
        TagCategory.EVENT: "#673AB7",
        TagCategory.CUSTOM: "#607D8B"
    }
    
    for tag in tags:
        # Calculate size based on confidence and frequency
        size_factor = (tag.confidence / max_confidence) * 0.7 + \
                     (tag.frequency / max_frequency) * 0.3
        font_size = 14 + (size_factor * 30)
        
        # Get color based on category
        color = category_colors.get(tag.category, "#666666")
        
        # Create tag HTML
        tag_html += f'''
        <span style="
            font-size: {font_size}px;
            color: {color};
            margin: 5px 10px;
            display: inline-block;
            padding: 2px 8px;
            border-radius: 15px;
            background-color: {color}20;
            cursor: pointer;
            transition: all 0.2s;
        " title="{tag.category.value} - {tag.confidence:.0%} confidence">
            {tag.text}
        </span>
        '''
    
    tag_html += '</div>'
    
    # Display word cloud
    st.markdown(tag_html, unsafe_allow_html=True)
    
    # Legend
    with st.expander("Category Legend"):
        cols = st.columns(4)
        for i, (category, color) in enumerate(category_colors.items()):
            col_idx = i % 4
            with cols[col_idx]:
                st.markdown(
                    f'<span style="color: {color};">●</span> {category.value}',
                    unsafe_allow_html=True
                )


def render_tag_list(tags: List[Tag], editable: bool) -> List[Tag]:
    """Render tags as an editable list"""
    
    updated_tags = tags.copy()
    
    # Group by category
    categories = {}
    for tag in tags:
        if tag.category not in categories:
            categories[tag.category] = []
        categories[tag.category].append(tag)
    
    # Display each category
    for category, category_tags in categories.items():
        st.subheader(f"{category.value.title()} ({len(category_tags)})")
        
        for i, tag in enumerate(category_tags):
            tag_key = f"{category.value}_{i}"
            
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                if editable:
                    new_text = st.text_input(
                        "Tag",
                        value=tag.text,
                        key=f"tag_text_{tag_key}",
                        label_visibility="collapsed"
                    )
                    if new_text != tag.text:
                        tag.text = new_text
                else:
                    st.write(tag.text)
            
            with col2:
                st.write(f"{tag.confidence:.0%}")
            
            with col3:
                st.write(f"×{tag.frequency}")
            
            with col4:
                st.write(tag.source)
            
            with col5:
                if editable and st.button("🗑️", key=f"delete_{tag_key}"):
                    updated_tags.remove(tag)
                    st.rerun()
    
    # Add new tag
    if editable:
        st.markdown("---")
        with st.expander("➕ Add Custom Tag"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                new_tag_text = st.text_input("Tag Text")
            
            with col2:
                new_tag_category = st.selectbox(
                    "Category",
                    [cat.value for cat in TagCategory]
                )
            
            with col3:
                new_tag_confidence = st.slider(
                    "Confidence",
                    0.0, 1.0, 0.8,
                    key="new_tag_confidence"
                )
            
            if st.button("Add Tag", type="primary"):
                if new_tag_text:
                    manager = TagManager()
                    new_tag = Tag(
                        id=manager._generate_tag_id(new_tag_text),
                        text=new_tag_text,
                        category=TagCategory(new_tag_category),
                        confidence=new_tag_confidence,
                        frequency=1,
                        source='manual',
                        metadata={'added_by': 'user'},
                        created_at=datetime.now()
                    )
                    updated_tags.append(new_tag)
                    st.success(f"Added tag: {new_tag_text}")
                    st.rerun()
    
    return updated_tags


def render_tag_grid(tags: List[Tag], editable: bool) -> List[Tag]:
    """Render tags in a grid layout"""
    
    # Group by category
    categories = {}
    for tag in tags:
        if tag.category not in categories:
            categories[tag.category] = []
        categories[tag.category].append(tag)
    
    # Create grid for each category
    for category, category_tags in categories.items():
        st.subheader(f"{category.value.title()}")
        
        # Calculate columns based on number of tags
        num_cols = min(4, len(category_tags))
        if num_cols > 0:
            cols = st.columns(num_cols)
            
            for i, tag in enumerate(category_tags):
                col_idx = i % num_cols
                
                with cols[col_idx]:
                    # Tag card
                    with st.container():
                        st.markdown(f"""
                        <div style="
                            background-color: #f0f0f0;
                            padding: 10px;
                            border-radius: 8px;
                            margin-bottom: 10px;
                        ">
                            <strong>{tag.text}</strong><br>
                            <small>
                                Confidence: {tag.confidence:.0%}<br>
                                Frequency: {tag.frequency}<br>
                                Source: {tag.source}
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if editable:
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✏️", key=f"edit_grid_{tag.id}"):
                                    st.session_state[f"editing_tag_{tag.id}"] = True
                            with col2:
                                if st.button("🗑️", key=f"delete_grid_{tag.id}"):
                                    tags.remove(tag)
                                    st.rerun()
    
    return tags


def render_tag_analytics(tags: List[Tag], content: str):
    """Render tag analytics and insights"""
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tags", len(tags))
    
    with col2:
        avg_confidence = sum(tag.confidence for tag in tags) / len(tags) if tags else 0
        st.metric("Avg Confidence", f"{avg_confidence:.0%}")
    
    with col3:
        unique_categories = len(set(tag.category for tag in tags))
        st.metric("Categories", unique_categories)
    
    with col4:
        total_frequency = sum(tag.frequency for tag in tags)
        st.metric("Total Frequency", total_frequency)
    
    # Category distribution
    st.markdown("### 📊 Category Distribution")
    category_counts = {}
    for tag in tags:
        category = tag.category.value
        category_counts[category] = category_counts.get(category, 0) + 1
    
    if category_counts:
        fig_category = px.pie(
            values=list(category_counts.values()),
            names=list(category_counts.keys()),
            title="Tags by Category"
        )
        st.plotly_chart(fig_category, use_container_width=True)
    
    # Confidence distribution
    st.markdown("### 📈 Confidence Distribution")
    confidences = [tag.confidence for tag in tags]
    if confidences:
        fig_confidence = px.histogram(
            x=confidences,
            nbins=20,
            title="Tag Confidence Distribution",
            labels={'x': 'Confidence', 'y': 'Count'}
        )
        st.plotly_chart(fig_confidence, use_container_width=True)
    
    # Source analysis
    st.markdown("### 🔍 Tag Sources")
    source_counts = {}
    for tag in tags:
        source_counts[tag.source] = source_counts.get(tag.source, 0) + 1
    
    if source_counts:
        source_df = pd.DataFrame(
            list(source_counts.items()),
            columns=['Source', 'Count']
        )
        fig_source = px.bar(
            source_df,
            x='Source',
            y='Count',
            title="Tags by Source"
        )
        st.plotly_chart(fig_source, use_container_width=True)
    
    # Top tags by frequency
    st.markdown("### 🏆 Top Tags by Frequency")
    sorted_tags = sorted(tags, key=lambda t: t.frequency, reverse=True)[:10]
    
    if sorted_tags:
        freq_data = []
        for tag in sorted_tags:
            freq_data.append({
                'Tag': tag.text,
                'Category': tag.category.value,
                'Frequency': tag.frequency,
                'Confidence': f"{tag.confidence:.0%}"
            })
        
        freq_df = pd.DataFrame(freq_data)
        st.dataframe(freq_df, use_container_width=True)
    
    # Tag co-occurrence (simplified)
    st.markdown("### 🔗 Tag Relationships")
    if len(tags) > 1:
        # Find tags that appear close to each other in content
        relationships = []
        
        for i, tag1 in enumerate(tags):
            for tag2 in tags[i+1:]:
                # Check if tags appear within 200 characters of each other
                pos1 = content.lower().find(tag1.text.lower())
                pos2 = content.lower().find(tag2.text.lower())
                
                if pos1 >= 0 and pos2 >= 0 and abs(pos1 - pos2) < 200:
                    relationships.append({
                        'Tag 1': tag1.text,
                        'Tag 2': tag2.text,
                        'Distance': abs(pos1 - pos2)
                    })
        
        if relationships:
            # Show top relationships
            rel_df = pd.DataFrame(relationships)
            rel_df = rel_df.sort_values('Distance').head(10)
            st.dataframe(rel_df, use_container_width=True)
        else:
            st.info("No close relationships found between tags")


def render_tag_editor(tag: Tag) -> Tag:
    """Render tag editor form"""
    
    with st.form(key=f"tag_editor_{tag.id}"):
        st.markdown("### ✏️ Edit Tag")
        
        # Tag text
        new_text = st.text_input("Tag Text", value=tag.text)
        
        # Category
        new_category = st.selectbox(
            "Category",
            [cat.value for cat in TagCategory],
            index=[cat.value for cat in TagCategory].index(tag.category.value)
        )
        
        # Confidence
        new_confidence = st.slider(
            "Confidence",
            0.0, 1.0, tag.confidence,
            help="Tag confidence score"
        )
        
        # Metadata
        st.markdown("#### Metadata")
        metadata_str = st.text_area(
            "Metadata (JSON)",
            value=json.dumps(tag.metadata, indent=2),
            height=100
        )
        
        # Submit button
        if st.form_submit_button("💾 Save Changes"):
            # Update tag
            tag.text = new_text
            tag.category = TagCategory(new_category)
            tag.confidence = new_confidence
            
            try:
                tag.metadata = json.loads(metadata_str)
            except:
                st.error("Invalid JSON in metadata")
            
            st.success("Tag updated!")
    
    return tag


def render_export_options(tags: List[Tag]):
    """Render tag export options"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    manager = TagManager()
    
    with col1:
        if st.button("📥 Export JSON"):
            json_data = manager.export_tags(tags, "json")
            st.download_button(
                "Download JSON",
                json_data,
                "tags.json",
                "application/json"
            )
    
    with col2:
        if st.button("📥 Export CSV"):
            csv_data = manager.export_tags(tags, "csv")
            st.download_button(
                "Download CSV",
                csv_data,
                "tags.csv",
                "text/csv"
            )
    
    with col3:
        if st.button("📥 Export Text"):
            text_data = manager.export_tags(tags, "text")
            st.download_button(
                "Download Text",
                text_data,
                "tags.txt",
                "text/plain"
            )
    
    with col4:
        if st.button("💾 Save Profile"):
            # Save tag profile for reuse
            profile_name = st.text_input("Profile Name", key="profile_name")
            if profile_name:
                filepath = f"tag_profiles/{profile_name}.json"
                manager.save_tag_profile(tags, filepath)
                st.success(f"Saved profile: {profile_name}")


def _add_default_rules(manager: TagManager):
    """Add default tagging rules"""
    
    # Programming language detection
    manager.add_custom_rule(
        name="python_detection",
        tag="Python",
        category="technical",
        keywords=["python", "pandas", "numpy", "django", "flask"]
    )
    
    manager.add_custom_rule(
        name="javascript_detection",
        tag="JavaScript",
        category="technical",
        keywords=["javascript", "node", "react", "vue", "angular"]
    )
    
    # AI/ML detection
    manager.add_custom_rule(
        name="ai_ml_detection",
        tag="AI/ML",
        category="technical",
        keywords=["artificial intelligence", "machine learning", "neural network", "deep learning"]
    )
    
    # Business terms
    manager.add_custom_rule(
        name="business_strategy",
        tag="Business Strategy",
        category="concept",
        keywords=["strategy", "competitive advantage", "market analysis", "business plan"]
    )
    
    # Sentiment patterns
    manager.add_custom_rule(
        name="positive_sentiment",
        tag="Positive",
        category="sentiment",
        pattern=r"\b(excellent|amazing|fantastic|great|wonderful|love|best)\b",
        confidence=0.8
    )
    
    manager.add_custom_rule(
        name="negative_sentiment",
        tag="Negative",
        category="sentiment",
        pattern=r"\b(terrible|awful|horrible|worst|hate|bad|poor)\b",
        confidence=0.8
    )