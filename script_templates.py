#!/usr/bin/env python3
"""
Script Templates Management Module
Manages script templates and content generation presets for the admin panel
"""

import streamlit as st
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)

@dataclass
class ScriptTemplate:
    """Script template data structure"""
    id: str
    name: str
    description: str
    category: str
    template_text: str
    variables: List[str]  # List of variable names like {company_name}, {topic}
    style: str
    format_type: str  # monologue, dialogue, interview, etc.
    created_date: str = ""
    usage_count: int = 0
    is_default: bool = False
    
    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

@dataclass
class ContentPreset:
    """Content generation preset"""
    id: str
    name: str
    description: str
    prompt_template: str
    style_settings: Dict[str, Any]
    voice_profile_id: str
    category: str
    created_date: str = ""
    usage_count: int = 0
    
    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

class ScriptTemplateManager:
    """Manages script templates and content generation presets"""
    
    def __init__(self):
        self.templates_file = "script_templates.json"
        self.presets_file = "content_presets.json"
        self.default_templates = self._get_default_templates()
        self.default_presets = self._get_default_presets()
    
    def _get_default_templates(self) -> List[ScriptTemplate]:
        """Get default script templates"""
        return [
            ScriptTemplate(
                id="business_presentation",
                name="Business Presentation",
                description="Professional presentation template for business content",
                category="Business",
                template_text="""Good morning, everyone. Today I'd like to discuss {topic}.

{introduction}

Let me start by outlining the key points we'll cover:
1. {point_1}
2. {point_2}
3. {point_3}

{main_content}

In conclusion, {conclusion}

Thank you for your attention. Are there any questions?""",
                variables=["topic", "introduction", "point_1", "point_2", "point_3", "main_content", "conclusion"],
                style="formal",
                format_type="monologue",
                is_default=True
            ),
            
            ScriptTemplate(
                id="interview_format",
                name="Interview Format",
                description="Two-person interview template with questions and responses",
                category="Interview",
                template_text="""Interviewer: Welcome to our show. Today we're joined by {guest_name}, {guest_title}. Thank you for being here.

Guest: Thank you for having me.

Interviewer: Let's start with {opening_question}

Guest: {opening_response}

Interviewer: That's fascinating. Can you tell us more about {follow_up_topic}?

Guest: {detailed_response}

Interviewer: {additional_questions}

Guest: {final_thoughts}

Interviewer: Thank you so much for your time and insights.

Guest: My pleasure. Thank you for having me.""",
                variables=["guest_name", "guest_title", "opening_question", "opening_response", "follow_up_topic", "detailed_response", "additional_questions", "final_thoughts"],
                style="conversational",
                format_type="dialogue",
                is_default=True
            ),
            
            ScriptTemplate(
                id="educational_content",
                name="Educational Content",
                description="Educational content template for tutorials and lessons",
                category="Education",
                template_text="""Welcome to today's lesson on {subject}.

Learning Objectives:
By the end of this session, you will be able to:
- {objective_1}
- {objective_2}
- {objective_3}

Let's begin with the basics. {introduction_content}

Now, let's dive deeper into {main_topic}. {detailed_explanation}

Here's a practical example: {example}

Key takeaways from today's lesson:
1. {takeaway_1}
2. {takeaway_2}
3. {takeaway_3}

For your next steps, I recommend {recommendations}.

Thank you for learning with us today!""",
                variables=["subject", "objective_1", "objective_2", "objective_3", "introduction_content", "main_topic", "detailed_explanation", "example", "takeaway_1", "takeaway_2", "takeaway_3", "recommendations"],
                style="educational",
                format_type="monologue",
                is_default=True
            ),
            
            ScriptTemplate(
                id="podcast_intro",
                name="Podcast Introduction",
                description="Podcast episode introduction template",
                category="Media",
                template_text="""Welcome to {podcast_name}, the podcast where we {podcast_description}.

I'm your host, {host_name}.

In today's episode, we're exploring {episode_topic}. {episode_description}

{guest_introduction}

Before we dive in, a quick reminder to {call_to_action}.

Now, let's get started with {opening_segment}.""",
                variables=["podcast_name", "podcast_description", "host_name", "episode_topic", "episode_description", "guest_introduction", "call_to_action", "opening_segment"],
                style="conversational",
                format_type="monologue",
                is_default=True
            ),
            
            ScriptTemplate(
                id="product_demo",
                name="Product Demonstration",
                description="Product demo and walkthrough template",
                category="Marketing",
                template_text="""Hello, and welcome to this demonstration of {product_name}.

Today, I'll show you how {product_name} can {main_benefit}.

Let me start by showing you the key features:

Feature 1: {feature_1_description}
As you can see, {feature_1_demo}

Feature 2: {feature_2_description}
Here's how it works: {feature_2_demo}

Feature 3: {feature_3_description}
Let me demonstrate: {feature_3_demo}

The real power of {product_name} becomes clear when you {use_case_example}.

{closing_statement}

To learn more or get started, {call_to_action}.""",
                variables=["product_name", "main_benefit", "feature_1_description", "feature_1_demo", "feature_2_description", "feature_2_demo", "feature_3_description", "feature_3_demo", "use_case_example", "closing_statement", "call_to_action"],
                style="professional",
                format_type="monologue",
                is_default=True
            )
        ]
    
    def _get_default_presets(self) -> List[ContentPreset]:
        """Get default content generation presets"""
        return [
            ContentPreset(
                id="meeting_summary",
                name="Meeting Summary Generator",
                description="Generate meeting summaries from key points",
                prompt_template="Create a professional meeting summary covering: {topics}. Include action items and next steps. Keep it concise and actionable.",
                style_settings={"tone": "professional", "length": "medium", "format": "structured"},
                voice_profile_id="professional_female",
                category="Business"
            ),
            
            ContentPreset(
                id="training_content",
                name="Training Content Creator",
                description="Generate training content for specific topics",
                prompt_template="Create engaging training content about {subject}. Include learning objectives, key concepts, and practical examples. Make it suitable for {audience_level} learners.",
                style_settings={"tone": "educational", "length": "long", "format": "structured"},
                voice_profile_id="professional_male",
                category="Education"
            ),
            
            ContentPreset(
                id="podcast_script",
                name="Podcast Script Generator",
                description="Generate podcast episode scripts",
                prompt_template="Create a {duration}-minute podcast script about {topic}. Include an engaging introduction, main content with {num_segments} segments, and a compelling conclusion. Style: {style}",
                style_settings={"tone": "conversational", "length": "long", "format": "dialogue"},
                voice_profile_id="conversational_male",
                category="Media"
            ),
            
            ContentPreset(
                id="product_announcement",
                name="Product Announcement",
                description="Generate product announcement content",
                prompt_template="Create an exciting product announcement for {product_name}. Highlight key features: {features}. Target audience: {target_audience}. Include benefits and call-to-action.",
                style_settings={"tone": "enthusiastic", "length": "medium", "format": "presentation"},
                voice_profile_id="professional_female",
                category="Marketing"
            )
        ]
    
    def load_templates(self) -> List[ScriptTemplate]:
        """Load script templates from file"""
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r') as f:
                    data = json.load(f)
                    return [ScriptTemplate(**template) for template in data.get('templates', [])]
            else:
                # Initialize with default templates
                self.save_templates(self.default_templates)
                return self.default_templates
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            return self.default_templates
    
    def save_templates(self, templates: List[ScriptTemplate]):
        """Save script templates to file"""
        try:
            data = {
                'templates': [asdict(template) for template in templates],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.templates_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")
    
    def load_presets(self) -> List[ContentPreset]:
        """Load content presets from file"""
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r') as f:
                    data = json.load(f)
                    return [ContentPreset(**preset) for preset in data.get('presets', [])]
            else:
                # Initialize with default presets
                self.save_presets(self.default_presets)
                return self.default_presets
        except Exception as e:
            logger.error(f"Failed to load presets: {e}")
            return self.default_presets
    
    def save_presets(self, presets: List[ContentPreset]):
        """Save content presets to file"""
        try:
            data = {
                'presets': [asdict(preset) for preset in presets],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.presets_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save presets: {e}")
    
    def add_template(self, template: ScriptTemplate) -> bool:
        """Add a new script template"""
        try:
            templates = self.load_templates()
            
            # Check for duplicate IDs
            if any(t.id == template.id for t in templates):
                return False
            
            templates.append(template)
            self.save_templates(templates)
            return True
        except Exception as e:
            logger.error(f"Failed to add template: {e}")
            return False
    
    def update_template(self, template_id: str, updated_template: ScriptTemplate) -> bool:
        """Update an existing template"""
        try:
            templates = self.load_templates()
            
            for i, template in enumerate(templates):
                if template.id == template_id:
                    templates[i] = updated_template
                    self.save_templates(templates)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to update template: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        try:
            templates = self.load_templates()
            
            # Don't allow deletion of default templates
            template_to_delete = next((t for t in templates if t.id == template_id), None)
            if template_to_delete and template_to_delete.is_default:
                return False
            
            templates = [t for t in templates if t.id != template_id]
            self.save_templates(templates)
            return True
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return False
    
    def increment_template_usage(self, template_id: str):
        """Increment usage count for a template"""
        try:
            templates = self.load_templates()
            
            for template in templates:
                if template.id == template_id:
                    template.usage_count += 1
                    break
            
            self.save_templates(templates)
        except Exception as e:
            logger.error(f"Failed to increment template usage: {e}")
    
    def render_templates_ui(self):
        """Render script templates management UI"""
        st.header("📝 Script Templates & Content Presets")
        
        # Main tabs
        tab1, tab2, tab3 = st.tabs(["📚 Templates", "🎯 Presets", "📊 Usage Stats"])
        
        with tab1:
            self.render_templates_tab()
        
        with tab2:
            self.render_presets_tab()
        
        with tab3:
            self.render_usage_stats_tab()
    
    def render_templates_tab(self):
        """Render templates management tab"""
        st.subheader("Script Templates")
        
        # Sub-tabs for templates
        sub_tab1, sub_tab2 = st.tabs(["📋 View Templates", "➕ Add Template"])
        
        with sub_tab1:
            templates = self.load_templates()
            self.render_templates_list(templates)
        
        with sub_tab2:
            self.render_add_template_form()
    
    def render_templates_list(self, templates: List[ScriptTemplate]):
        """Render list of script templates"""
        if not templates:
            st.info("No templates available")
            return
        
        # Group by category
        categories = {}
        for template in templates:
            if template.category not in categories:
                categories[template.category] = []
            categories[template.category].append(template)
        
        # Display templates by category
        for category, category_templates in categories.items():
            st.markdown(f"### {category}")
            
            for template in category_templates:
                with st.expander(f"📝 {template.name}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Description:** {template.description}")
                        st.write(f"**Style:** {template.style}")
                        st.write(f"**Format:** {template.format_type}")
                        st.write(f"**Usage Count:** {template.usage_count}")
                        
                        if template.is_default:
                            st.badge("Default", type="primary")
                        else:
                            st.badge("Custom", type="secondary")
                        
                        # Variables
                        if template.variables:
                            st.write("**Variables:**")
                            variables_text = ", ".join([f"{{{var}}}" for var in template.variables])
                            st.code(variables_text)
                        
                        # Template preview
                        with st.expander("👁️ Preview Template"):
                            st.code(template.template_text, language="text")
                    
                    with col2:
                        # Use template button
                        if st.button(f"🚀 Use", key=f"use_template_{template.id}"):
                            st.session_state[f"using_template_{template.id}"] = True
                            self.increment_template_usage(template.id)
                            st.rerun()
                        
                        # Edit button (only for custom templates)
                        if not template.is_default:
                            if st.button(f"✏️ Edit", key=f"edit_template_{template.id}"):
                                st.session_state[f"editing_template_{template.id}"] = True
                                st.rerun()
                        
                        # Delete button (only for custom templates)
                        if not template.is_default:
                            if st.button(f"🗑️ Delete", key=f"delete_template_{template.id}"):
                                if self.delete_template(template.id):
                                    st.success(f"Deleted template: {template.name}")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete template")
                    
                    # Template usage form
                    if st.session_state.get(f"using_template_{template.id}", False):
                        self.render_template_usage_form(template)
                    
                    # Edit form
                    if st.session_state.get(f"editing_template_{template.id}", False):
                        self.render_edit_template_form(template)
    
    def render_template_usage_form(self, template: ScriptTemplate):
        """Render form to use a template with variable substitution"""
        st.markdown("---")
        st.markdown(f"**Using Template: {template.name}**")
        
        with st.form(f"use_template_form_{template.id}"):
            st.markdown("Fill in the template variables:")
            
            variable_values = {}
            
            # Create input fields for each variable
            for i, variable in enumerate(template.variables):
                if i % 2 == 0:
                    col1, col2 = st.columns(2)
                    current_col = col1
                else:
                    current_col = col2
                
                with current_col:
                    variable_values[variable] = st.text_area(
                        f"{variable.replace('_', ' ').title()}",
                        key=f"var_{template.id}_{variable}",
                        height=60
                    )
            
            col_generate, col_cancel = st.columns(2)
            
            with col_generate:
                generate_script = st.form_submit_button("🎯 Generate Script")
            
            with col_cancel:
                cancel_usage = st.form_submit_button("❌ Cancel")
            
            if generate_script:
                # Substitute variables in template
                generated_script = template.template_text
                for variable, value in variable_values.items():
                    generated_script = generated_script.replace(f"{{{variable}}}", value)
                
                st.markdown("### Generated Script:")
                st.text_area("Generated Content", value=generated_script, height=300)
                
                # Option to copy to admin panel
                if st.button("📋 Copy to Admin Panel"):
                    st.session_state['admin_generated_script'] = generated_script
                    st.success("Script copied to admin panel!")
            
            if cancel_usage:
                st.session_state[f"using_template_{template.id}"] = False
                st.rerun()
    
    def render_add_template_form(self):
        """Render form to add new template"""
        st.subheader("Add New Script Template")
        
        with st.form("add_template_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                template_name = st.text_input("Template Name*")
                template_description = st.text_area("Description*")
                template_category = st.selectbox(
                    "Category*",
                    ["Business", "Education", "Interview", "Media", "Marketing", "Entertainment", "Custom"]
                )
                template_style = st.selectbox(
                    "Style*",
                    ["formal", "conversational", "educational", "professional", "casual", "narrative"]
                )
            
            with col2:
                template_format = st.selectbox(
                    "Format Type*",
                    ["monologue", "dialogue", "interview", "presentation", "narrative"]
                )
                
                variables_input = st.text_area(
                    "Variables (one per line)*",
                    help="List variable names that will be replaced in the template (e.g., topic, company_name)",
                    height=100
                )
            
            template_text = st.text_area(
                "Template Text*",
                help="Use {variable_name} syntax for variables",
                height=200
            )
            
            submitted = st.form_submit_button("➕ Add Template")
            
            if submitted:
                if not all([template_name, template_description, template_category, template_text]):
                    st.error("Please fill in all required fields")
                else:
                    # Parse variables
                    variables = [var.strip() for var in variables_input.split('\n') if var.strip()]
                    
                    new_template = ScriptTemplate(
                        id="",  # Will be auto-generated
                        name=template_name,
                        description=template_description,
                        category=template_category,
                        template_text=template_text,
                        variables=variables,
                        style=template_style,
                        format_type=template_format,
                        is_default=False
                    )
                    
                    if self.add_template(new_template):
                        st.success(f"Added template: {template_name}")
                        st.rerun()
                    else:
                        st.error("Failed to add template")
    
    def render_edit_template_form(self, template: ScriptTemplate):
        """Render form to edit existing template"""
        st.markdown("---")
        st.markdown(f"**Editing Template: {template.name}**")
        
        with st.form(f"edit_template_form_{template.id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Template Name", value=template.name)
                new_description = st.text_area("Description", value=template.description)
                new_category = st.selectbox(
                    "Category",
                    ["Business", "Education", "Interview", "Media", "Marketing", "Entertainment", "Custom"],
                    index=["Business", "Education", "Interview", "Media", "Marketing", "Entertainment", "Custom"].index(template.category)
                )
                new_style = st.selectbox(
                    "Style",
                    ["formal", "conversational", "educational", "professional", "casual", "narrative"],
                    index=["formal", "conversational", "educational", "professional", "casual", "narrative"].index(template.style)
                )
            
            with col2:
                new_format = st.selectbox(
                    "Format Type",
                    ["monologue", "dialogue", "interview", "presentation", "narrative"],
                    index=["monologue", "dialogue", "interview", "presentation", "narrative"].index(template.format_type)
                )
                
                variables_text = '\n'.join(template.variables)
                new_variables_input = st.text_area(
                    "Variables (one per line)",
                    value=variables_text,
                    height=100
                )
            
            new_template_text = st.text_area(
                "Template Text",
                value=template.template_text,
                height=200
            )
            
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                save_changes = st.form_submit_button("💾 Save Changes")
            
            with col_cancel:
                cancel_edit = st.form_submit_button("❌ Cancel")
            
            if save_changes:
                # Parse variables
                new_variables = [var.strip() for var in new_variables_input.split('\n') if var.strip()]
                
                updated_template = ScriptTemplate(
                    id=template.id,
                    name=new_name,
                    description=new_description,
                    category=new_category,
                    template_text=new_template_text,
                    variables=new_variables,
                    style=new_style,
                    format_type=new_format,
                    created_date=template.created_date,
                    usage_count=template.usage_count,
                    is_default=template.is_default
                )
                
                if self.update_template(template.id, updated_template):
                    st.success("Template updated successfully")
                    st.session_state[f"editing_template_{template.id}"] = False
                    st.rerun()
                else:
                    st.error("Failed to update template")
            
            if cancel_edit:
                st.session_state[f"editing_template_{template.id}"] = False
                st.rerun()
    
    def render_presets_tab(self):
        """Render content presets tab"""
        st.subheader("Content Generation Presets")
        st.info("Content presets feature coming soon - will integrate with AI content generation")
    
    def render_usage_stats_tab(self):
        """Render usage statistics tab"""
        st.subheader("Template Usage Statistics")
        
        templates = self.load_templates()
        
        if not templates:
            st.info("No templates available")
            return
        
        # Sort by usage
        sorted_templates = sorted(templates, key=lambda t: t.usage_count, reverse=True)
        
        # Usage chart
        template_names = [t.name for t in sorted_templates]
        usage_counts = [t.usage_count for t in sorted_templates]
        
        if any(count > 0 for count in usage_counts):
            import plotly.express as px
            
            fig = px.bar(
                x=template_names,
                y=usage_counts,
                title="Template Usage Statistics",
                labels={'x': 'Template', 'y': 'Usage Count'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No usage data available yet")
        
        # Usage table
        st.markdown("### Detailed Usage")
        
        usage_data = []
        for template in sorted_templates:
            usage_data.append({
                'Template Name': template.name,
                'Category': template.category,
                'Style': template.style,
                'Format': template.format_type,
                'Usage Count': template.usage_count,
                'Type': 'Default' if template.is_default else 'Custom',
                'Created': template.created_date[:10] if template.created_date else 'N/A'
            })
        
        import pandas as pd
        df = pd.DataFrame(usage_data)
        st.dataframe(df, use_container_width=True)

# Global script template manager instance
script_template_manager = ScriptTemplateManager()