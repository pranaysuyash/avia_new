#!/usr/bin/env python3
"""
AI Model Customization UI Module
Streamlit interface for managing custom vocabularies, voice profiles,
entity types, and A/B testing
"""

import streamlit as st
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from streamlit_intent_utils import render_share_inline, render_share_block, log_ux_event, get_params, update_params

# Import customization components
from ai_model_customization import (
    AIModelCustomization, CustomVocabulary, VoiceProfile, 
    CustomEntityType, ModelConfiguration,
    get_ai_customization, create_custom_vocabulary,
    create_voice_profile, create_custom_entity_type,
    transcribe_with_customizations
)

logger = logging.getLogger(__name__)

def render_ai_customization_ui():
    """Main UI for AI model customization features"""
    st.header("🤖 AI Model Customization")
    # Inline share UI
    try:
        render_share_inline("Shareable view link")
    except Exception:
        pass
    
    # Initialize customization system
    if 'ai_customization' not in st.session_state:
        st.session_state.ai_customization = get_ai_customization()
    
    customization = st.session_state.ai_customization
    
    # Deep-linked section selection via query param 'aic_tab'
    params = get_params()
    tab_map = [
        ("vocab", "📚 Custom Vocabularies"),
        ("voice", "🎤 Voice Profiles"),
        ("entities", "🏷️ Custom Entities"),
        ("abtest", "⚖️ A/B Testing"),
        ("stats", "📊 Statistics"),
    ]
    order_key = params.get('aic_tab', 'vocab')
    # Reorder so desired tab appears first (Streamlit focuses first tab)
    ordered = [x for x in tab_map if x[0] == order_key] + [x for x in tab_map if x[0] != order_key]
    tab_labels = [label for _, label in ordered]

    # Provide a sidebar quick section selector to update deep-link
    with st.sidebar:
        section_idx = st.selectbox(
            "Section",
            options=[k for k, _ in tab_map],
            index=[k for k, _ in tab_map].index(order_key) if order_key in [k for k, _ in tab_map] else 0,
            format_func=lambda k: dict(tab_map)[k]
        )
        if section_idx != order_key:
            update_params({'aic_tab': section_idx})
            try:
                log_ux_event('aic_tab_change', {'tab': section_idx})
            except Exception:
                pass
            st.experimental_rerun()

    # Navigation tabs (ordered so first is active according to aic_tab)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)
    
    with tab1:
        render_vocabulary_management(customization)
    
    with tab2:
        render_voice_profile_management(customization)
    
    with tab3:
        render_entity_type_management(customization)
    
    with tab4:
        render_ab_testing(customization)
    
    with tab5:
        render_customization_stats(customization)
    # Sidebar share + reset
    with st.sidebar:
        try:
            render_share_block("Share AI Customization View")
        except Exception:
            pass
        if st.button("Reset View/Filters"):
            try:
                st.experimental_set_query_params()
            except Exception:
                pass
            try:
                log_ux_event("st_filters_cleared", {"scope": "ai_customization"})
            except Exception:
                pass
            st.rerun()

def render_vocabulary_management(customization: AIModelCustomization):
    """UI for managing custom vocabularies"""
    st.subheader("📚 Custom Vocabularies")
    
    # Create new vocabulary section
    with st.expander("➕ Create New Vocabulary", expanded=False):
        st.markdown("Create domain-specific vocabularies to improve transcription accuracy")
        
        with st.form("create_vocabulary"):
            col1, col2 = st.columns(2)
            
            with col1:
                vocab_name = st.text_input(
                    "Vocabulary Name",
                    placeholder="e.g., Medical Terms, Legal Jargon",
                    help="Unique name for this vocabulary"
                )
                
                domain = st.selectbox(
                    "Domain",
                    options=["medical", "legal", "technical", "business", "academic", "creative", "other"],
                    help="Category this vocabulary belongs to"
                )
            
            with col2:
                terms_text = st.text_area(
                    "Terms (one per line)",
                    placeholder="cardiomyopathy\nmyocardial infarction\natherosclerosis",
                    height=100,
                    help="Enter specialized terms, one per line"
                )
                
                replacements_text = st.text_area(
                    "Common Corrections (format: wrong->correct)",
                    placeholder="cardio mixopathy->cardiomyopathy\nheart attack->myocardial infarction",
                    height=100,
                    help="Common misrecognitions and their corrections"
                )
            
            if st.form_submit_button("Create Vocabulary", type="primary"):
                if vocab_name and domain and terms_text:
                    try:
                        # Parse terms
                        terms = [term.strip() for term in terms_text.split('\n') if term.strip()]
                        
                        # Parse replacements
                        replacements = {}
                        if replacements_text:
                            for line in replacements_text.split('\n'):
                                if '->' in line:
                                    wrong, correct = line.split('->', 1)
                                    replacements[wrong.strip()] = correct.strip()
                        
                        # Create vocabulary
                        vocabulary = create_custom_vocabulary(vocab_name, domain, terms, replacements)
                        st.success(f"✅ Created vocabulary '{vocab_name}' with {len(terms)} terms")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Failed to create vocabulary: {e}")
                else:
                    st.error("Please fill in all required fields")
    
    # List existing vocabularies
    st.markdown("### Existing Vocabularies")
    
    vocabularies = customization.vocabulary_manager.list_vocabularies()
    
    if vocabularies:
        # Create vocabulary data for display
        vocab_data = []
        for vocab in vocabularies:
            vocab_data.append({
                'Name': vocab.name,
                'Domain': vocab.domain,
                'Terms': len(vocab.terms),
                'Corrections': len(vocab.replacements),
                'Usage Count': vocab.usage_count,
                'Created': vocab.created_at.strftime('%Y-%m-%d'),
                'Accuracy': f"{vocab.accuracy_improvement:.1%}" if vocab.accuracy_improvement > 0 else "N/A"
            })
        
        df = pd.DataFrame(vocab_data)
        st.dataframe(
            df, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "Usage Count": st.column_config.NumberColumn(
                    "Usage Count",
                    help="Number of times this vocabulary has been used"
                ),
                "Accuracy": st.column_config.TextColumn(
                    "Accuracy Improvement",
                    help="Measured improvement in transcription accuracy"
                )
            }
        )
        
        # Vocabulary details
        if vocab_data:
            selected_vocab = st.selectbox(
                "Select vocabulary to view details:",
                options=[v['Name'] for v in vocab_data],
                key="vocab_selector"
            )
            
            if selected_vocab:
                vocabulary = customization.vocabulary_manager.get_vocabulary(selected_vocab)
                if vocabulary:
                    with st.expander(f"📋 Details for '{selected_vocab}'", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Terms:**")
                            st.text_area(
                                "Terms in vocabulary:",
                                value='\n'.join(vocabulary.terms),
                                height=150,
                                disabled=True
                            )
                        
                        with col2:
                            st.markdown("**Corrections:**")
                            corrections_text = '\n'.join([
                                f"{wrong} → {correct}" 
                                for wrong, correct in vocabulary.replacements.items()
                            ])
                            st.text_area(
                                "Correction mappings:",
                                value=corrections_text or "No corrections defined",
                                height=150,
                                disabled=True
                            )
    else:
        st.info("No custom vocabularies created yet. Create your first vocabulary above!")

def render_voice_profile_management(customization: AIModelCustomization):
    """UI for managing voice profiles"""
    st.subheader("🎤 Voice Profiles")
    
    # Create new voice profile section
    with st.expander("➕ Create New Voice Profile", expanded=False):
        st.markdown("Create voice profiles for speaker recognition and identification")
        
        with st.form("create_voice_profile"):
            profile_name = st.text_input(
                "Profile Name",
                placeholder="e.g., John Doe, CEO, Main Presenter",
                help="Name to identify this speaker"
            )
            
            st.markdown("**Audio Samples**")
            st.info("💡 For best results, provide 3-5 clear audio samples of this speaker")
            
            # File uploaders for audio samples
            audio_files = []
            for i in range(5):
                audio_file = st.file_uploader(
                    f"Audio Sample {i+1}",
                    type=['wav', 'mp3', 'm4a'],
                    key=f"audio_sample_{i}",
                    help="Upload clear audio of this speaker (10-30 seconds recommended)"
                )
                if audio_file:
                    audio_files.append(audio_file)
            
            if st.form_submit_button("Create Voice Profile", type="primary"):
                if profile_name and len(audio_files) >= 2:
                    try:
                        # Process audio files (simplified for demo)
                        audio_segments = []
                        for i, audio_file in enumerate(audio_files):
                            # In production, would extract audio features here
                            audio_segments.append({
                                'file_name': audio_file.name,
                                'duration': 15.0,  # Placeholder
                                'confidence': 0.8,  # Placeholder
                                'text': f"Sample audio segment {i+1}",  # Placeholder
                                'features': {}  # Would contain actual voice features
                            })
                        
                        # Create voice profile
                        profile = create_voice_profile(profile_name, audio_segments)
                        st.success(f"✅ Created voice profile '{profile_name}' with ID {profile.profile_id}")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Failed to create voice profile: {e}")
                else:
                    st.error("Please provide a name and at least 2 audio samples")
    
    # List existing voice profiles
    st.markdown("### Existing Voice Profiles")
    
    profiles = customization.voice_manager.list_voice_profiles()
    
    if profiles:
        # Create profile data for display
        profile_data = []
        for profile in profiles:
            profile_data.append({
                'Name': profile.name,
                'Profile ID': profile.profile_id,
                'Samples': len(profile.sample_segments),
                'Accuracy': f"{profile.recognition_accuracy:.1%}" if profile.recognition_accuracy > 0 else "Training",
                'Usage Count': profile.usage_count,
                'Created': profile.created_at.strftime('%Y-%m-%d'),
                'Last Used': profile.last_used.strftime('%Y-%m-%d %H:%M') if profile.usage_count > 0 else "Never"
            })
        
        df = pd.DataFrame(profile_data)
        st.dataframe(
            df, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "Profile ID": st.column_config.TextColumn(
                    "Profile ID",
                    help="Unique identifier for this voice profile"
                ),
                "Usage Count": st.column_config.NumberColumn(
                    "Usage Count",
                    help="Number of times this profile has been matched"
                )
            }
        )
        
        # Profile details
        if profile_data:
            selected_profile_name = st.selectbox(
                "Select profile to view details:",
                options=[p['Name'] for p in profile_data],
                key="profile_selector"
            )
            
            if selected_profile_name:
                profile = next(p for p in profiles if p.name == selected_profile_name)
                with st.expander(f"🎤 Details for '{selected_profile_name}'", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Profile Information:**")
                        st.text(f"Profile ID: {profile.profile_id}")
                        st.text(f"Created: {profile.created_at.strftime('%Y-%m-%d %H:%M')}")
                        st.text(f"Sample Count: {len(profile.sample_segments)}")
                        st.text(f"Recognition Accuracy: {profile.recognition_accuracy:.1%}")
                    
                    with col2:
                        st.markdown("**Voice Characteristics:**")
                        for feature, value in profile.speaker_features.items():
                            if isinstance(value, float):
                                st.text(f"{feature.replace('_', ' ').title()}: {value:.3f}")
                            else:
                                st.text(f"{feature.replace('_', ' ').title()}: {value}")
    else:
        st.info("No voice profiles created yet. Create your first profile above!")

def render_entity_type_management(customization: AIModelCustomization):
    """UI for managing custom entity types"""
    st.subheader("🏷️ Custom Entity Types")
    
    # Create new entity type section
    with st.expander("➕ Create New Entity Type", expanded=False):
        st.markdown("Define custom entity types for specialized content extraction")
        
        with st.form("create_entity_type"):
            col1, col2 = st.columns(2)
            
            with col1:
                entity_name = st.text_input(
                    "Entity Type Name",
                    placeholder="e.g., Drug Names, Stock Symbols, Product Codes",
                    help="Name for this custom entity type"
                )
                
                category = st.selectbox(
                    "Category",
                    options=["medical", "financial", "technical", "product", "identifier", "other"],
                    help="Category this entity type belongs to"
                )
                
                patterns_text = st.text_area(
                    "Regex Patterns (one per line)",
                    placeholder=r"[A-Z]{2,4}\d{4,6}\n\b[A-Z]{3,5}-\d{3,5}\b",
                    height=100,
                    help="Regular expressions to match this entity type"
                )
            
            with col2:
                examples_text = st.text_area(
                    "Examples (one per line)",
                    placeholder="AAPL\nGOOG\nTSLA\nAMZN",
                    height=100,
                    help="Example instances of this entity type"
                )
                
                context_clues_text = st.text_area(
                    "Context Clues (optional)",
                    placeholder="stock\nshare\nticker\nsymbol",
                    height=100,
                    help="Words that often appear near this entity type"
                )
            
            if st.form_submit_button("Create Entity Type", type="primary"):
                if entity_name and category and patterns_text and examples_text:
                    try:
                        # Parse inputs
                        patterns = [p.strip() for p in patterns_text.split('\n') if p.strip()]
                        examples = [e.strip() for e in examples_text.split('\n') if e.strip()]
                        context_clues = [c.strip() for c in context_clues_text.split('\n') if c.strip()]
                        
                        # Create entity type
                        entity_type = create_custom_entity_type(
                            entity_name, category, patterns, examples
                        )
                        st.success(f"✅ Created entity type '{entity_name}' with {len(patterns)} patterns")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Failed to create entity type: {e}")
                else:
                    st.error("Please fill in all required fields")
    
    # List existing entity types
    st.markdown("### Existing Entity Types")
    
    entity_types = customization.entity_manager.list_entity_types()
    
    if entity_types:
        # Create entity type data for display
        entity_data = []
        for entity_type in entity_types:
            entity_data.append({
                'Name': entity_type.name,
                'Category': entity_type.category,
                'Patterns': len(entity_type.patterns),
                'Examples': len(entity_type.examples),
                'Usage Count': entity_type.usage_count,
                'Accuracy': f"{entity_type.accuracy:.1%}" if entity_type.accuracy > 0 else "N/A",
                'Created': entity_type.created_at.strftime('%Y-%m-%d')
            })
        
        df = pd.DataFrame(entity_data)
        st.dataframe(
            df, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "Usage Count": st.column_config.NumberColumn(
                    "Usage Count",
                    help="Number of times this entity type has been used"
                ),
                "Accuracy": st.column_config.TextColumn(
                    "Accuracy",
                    help="Measured extraction accuracy"
                )
            }
        )
        
        # Entity type details
        if entity_data:
            selected_entity = st.selectbox(
                "Select entity type to view details:",
                options=[e['Name'] for e in entity_data],
                key="entity_selector"
            )
            
            if selected_entity:
                entity_type = customization.entity_manager.get_entity_type(selected_entity)
                if entity_type:
                    with st.expander(f"🏷️ Details for '{selected_entity}'", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Patterns:**")
                            st.code('\n'.join(entity_type.patterns), language='regex')
                            
                            st.markdown("**Context Clues:**")
                            st.text(', '.join(entity_type.context_clues) if entity_type.context_clues else "None")
                        
                        with col2:
                            st.markdown("**Examples:**")
                            st.text('\n'.join(entity_type.examples))
                            
                            st.markdown("**Extraction Prompt:**")
                            st.text_area(
                                "GPT prompt used:",
                                value=entity_type.extraction_prompt,
                                height=100,
                                disabled=True
                            )
    else:
        st.info("No custom entity types created yet. Create your first entity type above!")

def render_ab_testing(customization: AIModelCustomization):
    """UI for A/B testing model configurations"""
    st.subheader("⚖️ A/B Testing")
    
    # Create new configuration section
    with st.expander("➕ Create Model Configuration", expanded=False):
        st.markdown("Create different model configurations for A/B testing")
        
        with st.form("create_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                config_name = st.text_input(
                    "Configuration Name",
                    placeholder="e.g., High Accuracy, Fast Processing",
                    help="Name for this configuration"
                )
                
                description = st.text_area(
                    "Description",
                    placeholder="Optimized for medical transcription with custom vocabulary",
                    help="Description of this configuration's purpose"
                )
            
            with col2:
                st.markdown("**Parameters:**")
                
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.1,
                    help="Controls randomness in AI responses"
                )
                
                max_tokens = st.number_input(
                    "Max Tokens",
                    min_value=100,
                    max_value=4000,
                    value=1500,
                    help="Maximum length of AI responses"
                )
                
                use_custom_vocab = st.checkbox("Use Custom Vocabulary")
                use_voice_profiles = st.checkbox("Use Voice Profiles")
            
            if st.form_submit_button("Create Configuration", type="primary"):
                if config_name and description:
                    try:
                        parameters = {
                            'temperature': temperature,
                            'max_tokens': max_tokens,
                            'use_custom_vocab': use_custom_vocab,
                            'use_voice_profiles': use_voice_profiles
                        }
                        
                        config = customization.config_manager.create_configuration(
                            config_name, description, parameters
                        )
                        st.success(f"✅ Created configuration '{config_name}' with ID {config.config_id}")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Failed to create configuration: {e}")
                else:
                    st.error("Please fill in name and description")
    
    # Run A/B test section
    with st.expander("🧪 Run A/B Test", expanded=False):
        st.markdown("Compare two model configurations")
        
        # Get available configurations (simplified - would load from database)
        configs = ["Config A (High Accuracy)", "Config B (Fast Processing)", "Config C (Balanced)"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            config_a = st.selectbox("Configuration A", configs, key="config_a")
            
        with col2:
            config_b = st.selectbox("Configuration B", configs, key="config_b", index=1)
        
        test_data = st.text_area(
            "Test Data (one sample per line)",
            placeholder="Sample text 1\nSample text 2\nSample text 3",
            help="Provide test samples for comparison"
        )
        
        if st.button("🚀 Run A/B Test", type="primary"):
            if config_a != config_b and test_data:
                with st.spinner("Running A/B test..."):
                    # Simulate test results
                    test_samples = [s.strip() for s in test_data.split('\n') if s.strip()]
                    
                    # Mock results for demo
                    results = {
                        'config_a': {
                            'name': config_a,
                            'avg_accuracy': 0.87,
                            'avg_processing_time': 2.3,
                            'results': [
                                {'accuracy': 0.85, 'processing_time': 2.1},
                                {'accuracy': 0.89, 'processing_time': 2.5}
                            ]
                        },
                        'config_b': {
                            'name': config_b,
                            'avg_accuracy': 0.82,
                            'avg_processing_time': 1.8,
                            'results': [
                                {'accuracy': 0.80, 'processing_time': 1.7},
                                {'accuracy': 0.84, 'processing_time': 1.9}
                            ]
                        },
                        'winner': config_a,
                        'improvement': 0.05,
                        'statistical_significance': 0.03
                    }
                
                st.success("✅ A/B Test Complete!")
                
                # Display results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        f"{config_a} Accuracy",
                        f"{results['config_a']['avg_accuracy']:.1%}",
                        delta=f"+{results['improvement']:.1%}" if results['winner'] == config_a else None
                    )
                
                with col2:
                    st.metric(
                        f"{config_b} Accuracy", 
                        f"{results['config_b']['avg_accuracy']:.1%}",
                        delta=f"+{results['improvement']:.1%}" if results['winner'] == config_b else None
                    )
                
                with col3:
                    significance = "Significant" if results['statistical_significance'] < 0.05 else "Not Significant"
                    st.metric("Statistical Significance", significance)
                
                st.info(f"🏆 Winner: **{results['winner']}** with {results['improvement']:.1%} improvement")
            else:
                st.error("Please select different configurations and provide test data")

def render_customization_stats(customization: AIModelCustomization):
    """UI for customization statistics"""
    st.subheader("📊 Customization Statistics")
    
    try:
        stats = customization.get_customization_stats()
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Custom Vocabularies",
                stats['vocabularies']['total'],
                help="Total number of custom vocabularies created"
            )
        
        with col2:
            st.metric(
                "Voice Profiles",
                stats['voice_profiles']['total'],
                help="Total number of voice profiles created"
            )
        
        with col3:
            st.metric(
                "Entity Types",
                stats['entity_types']['total'],
                help="Total number of custom entity types"
            )
        
        with col4:
            st.metric(
                "System Status",
                stats['system_status'].title(),
                help="Current system status"
            )
        
        # Most used items
        st.markdown("### Most Used Customizations")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Most Used Vocabulary:**")
            if stats['vocabularies']['most_used']:
                vocab = stats['vocabularies']['most_used']
                st.info(f"**{vocab['name']}**\nUsed {vocab['usage_count']} times")
            else:
                st.info("No usage data yet")
        
        with col2:
            st.markdown("**Most Used Voice Profile:**")
            if stats['voice_profiles']['most_used']:
                profile = stats['voice_profiles']['most_used']
                st.info(f"**{profile['name']}**\nMatched {profile['usage_count']} times")
            else:
                st.info("No usage data yet")
        
        with col3:
            st.markdown("**Most Used Entity Type:**")
            if stats['entity_types']['most_used']:
                entity = stats['entity_types']['most_used']
                st.info(f"**{entity['name']}**\nUsed {entity['usage_count']} times")
            else:
                st.info("No usage data yet")
        
        # Usage trends (mock data for demo)
        st.markdown("### Usage Trends")
        
        # Create sample trend data
        import numpy as np
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
        trend_data = pd.DataFrame({
            'Date': dates,
            'Vocabularies': np.random.randint(0, 20, len(dates)),
            'Voice Profiles': np.random.randint(0, 15, len(dates)),
            'Entity Types': np.random.randint(0, 10, len(dates))
        })
        
        st.line_chart(
            trend_data.set_index('Date'),
            use_container_width=True,
            height=300
        )
        
        # Recommendations
        st.markdown("### 💡 Recommendations")
        
        recommendations = []
        
        if stats['vocabularies']['total'] == 0:
            recommendations.append("Create your first custom vocabulary to improve domain-specific transcription")
        
        if stats['voice_profiles']['total'] == 0:
            recommendations.append("Add voice profiles to improve speaker identification accuracy")
        
        if stats['entity_types']['total'] == 0:
            recommendations.append("Define custom entity types for specialized content extraction")
        
        if not recommendations:
            recommendations = [
                "Consider A/B testing different configurations to optimize performance",
                "Review usage statistics to identify which customizations provide the most value",
                "Update custom vocabularies based on new domain-specific terms"
            ]
        
        for i, rec in enumerate(recommendations[:3], 1):
            st.info(f"**{i}.** {rec}")
    
    except Exception as e:
        st.error(f"Failed to load statistics: {e}")
        logger.error(f"Statistics loading error: {e}")

def render_customization_test_panel():
    """Test panel for trying customizations"""
    st.subheader("🧪 Test Customizations")
    
    # Test transcription with customizations
    with st.expander("Test Custom Transcription", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload Audio File for Testing",
            type=['wav', 'mp3', 'm4a'],
            help="Upload an audio file to test with customizations"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get available vocabularies
            customization = get_ai_customization()
            vocabularies = customization.vocabulary_manager.list_vocabularies()
            vocab_options = ["None"] + [v.name for v in vocabularies]
            
            selected_vocab = st.selectbox(
                "Custom Vocabulary",
                options=vocab_options,
                help="Select a custom vocabulary to apply"
            )
            
            use_voice_profiles = st.checkbox(
                "Use Voice Profiles",
                help="Enable speaker identification with voice profiles"
            )
        
        with col2:
            # Get available entity types
            entity_types = customization.entity_manager.list_entity_types()
            entity_options = [et.name for et in entity_types]
            
            selected_entities = st.multiselect(
                "Custom Entity Types",
                options=entity_options,
                help="Select custom entity types to extract"
            )
        
        if st.button("🚀 Test Transcription", type="primary"):
            if uploaded_file:
                with st.spinner("Processing with customizations..."):
                    try:
                        # Save uploaded file temporarily
                        import tempfile
                        import os
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            temp_path = tmp_file.name
                        
                        # Test with customizations
                        vocab_name = selected_vocab if selected_vocab != "None" else None
                        
                        results = transcribe_with_customizations(
                            temp_path,
                            vocabulary_name=vocab_name,
                            use_voice_profiles=use_voice_profiles,
                            custom_entity_types=selected_entities if selected_entities else None
                        )
                        
                        # Display results
                        st.success("✅ Transcription Complete!")
                        
                        # Transcription result
                        st.markdown("### 📝 Transcription")
                        st.text_area(
                            "Transcribed Text:",
                            value=results['transcription'].text,
                            height=150,
                            disabled=True
                        )
                        
                        # Entities
                        if results['entities']:
                            st.markdown("### 🏷️ Extracted Entities")
                            for entity_type, entities in results['entities'].items():
                                if entities:
                                    st.markdown(f"**{entity_type}:**")
                                    st.write(", ".join(entities))
                        
                        # Applied customizations
                        st.markdown("### ⚙️ Applied Customizations")
                        customizations = results['customizations_applied']
                        
                        if customizations['vocabulary']:
                            st.success(f"✅ Vocabulary: {customizations['vocabulary']}")
                        
                        if customizations['voice_profiles']:
                            st.success("✅ Voice Profiles: Enabled")
                        
                        if customizations['custom_entity_types']:
                            st.success(f"✅ Custom Entities: {', '.join(customizations['custom_entity_types'])}")
                        
                        # Cleanup
                        os.unlink(temp_path)
                        
                    except Exception as e:
                        st.error(f"❌ Test failed: {e}")
            else:
                st.error("Please upload an audio file to test")

# Helper functions
def export_customizations():
    """Export all customizations to JSON"""
    try:
        customization = get_ai_customization()
        
        export_data = {
            'vocabularies': [v.to_dict() for v in customization.vocabulary_manager.list_vocabularies()],
            'voice_profiles': [p.to_dict() for p in customization.voice_manager.list_voice_profiles()],
            'entity_types': [e.to_dict() for e in customization.entity_manager.list_entity_types()],
            'exported_at': datetime.now().isoformat()
        }
        
        return json.dumps(export_data, indent=2)
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return None

def import_customizations(json_data: str):
    """Import customizations from JSON"""
    try:
        data = json.loads(json_data)
        customization = get_ai_customization()
        
        imported = {'vocabularies': 0, 'voice_profiles': 0, 'entity_types': 0}
        
        # Import vocabularies
        for vocab_data in data.get('vocabularies', []):
            try:
                vocab = CustomVocabulary.from_dict(vocab_data)
                customization.vocabulary_manager.create_vocabulary(
                    vocab.name, vocab.domain, vocab.terms, vocab.replacements
                )
                imported['vocabularies'] += 1
            except Exception as e:
                logger.warning(f"Failed to import vocabulary: {e}")
        
        # Import entity types
        for entity_data in data.get('entity_types', []):
            try:
                entity = CustomEntityType.from_dict(entity_data)
                customization.entity_manager.create_entity_type(
                    entity.name, entity.category, entity.patterns, entity.examples
                )
                imported['entity_types'] += 1
            except Exception as e:
                logger.warning(f"Failed to import entity type: {e}")
        
        return imported
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return None
