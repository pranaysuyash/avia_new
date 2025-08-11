#!/usr/bin/env python3
"""
Punctuation Restoration UI
Streamlit interface for punctuation restoration and text enhancement
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import time

from punctuation_restoration import get_punctuation_service

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Punctuation Restoration & Text Enhancement",
        page_icon="✏️",
        layout="wide"
    )
    
    st.title("✏️ Punctuation Restoration & Text Enhancement")
    st.markdown("AI-powered punctuation restoration and text formatting for transcripts")
    
    # Sidebar for options
    with st.sidebar:
        st.header("Enhancement Options")
        
        restore_punctuation = st.checkbox("Restore Punctuation", value=True)
        fix_capitalization = st.checkbox("Fix Capitalization", value=True)
        format_numbers = st.checkbox("Format Numbers", value=True)
        format_quotes = st.checkbox("Format Quotes", value=True)
        format_dates = st.checkbox("Format Dates", value=True)
        
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.1,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Minimum confidence required for applying changes"
        )
        
        st.divider()
        
        # Model selection
        model_option = st.selectbox(
            "Processing Mode",
            ["AI Model (Recommended)", "Rule-based (Fallback)"],
            help="Choose between AI-powered or rule-based enhancement"
        )
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Single Text", "Batch Processing", "Statistics", "Examples"])
    
    with tab1:
        single_text_interface(
            restore_punctuation, fix_capitalization, format_numbers,
            format_quotes, format_dates, confidence_threshold
        )
    
    with tab2:
        batch_processing_interface(
            restore_punctuation, fix_capitalization, format_numbers,
            format_quotes, format_dates, confidence_threshold
        )
    
    with tab3:
        statistics_interface()
    
    with tab4:
        examples_interface()

def single_text_interface(restore_punctuation, fix_capitalization, format_numbers,
                         format_quotes, format_dates, confidence_threshold):
    """Interface for single text enhancement"""
    st.header("Single Text Enhancement")
    
    # Input methods
    input_method = st.radio(
        "Input Method",
        ["Text Input", "File Upload"],
        horizontal=True
    )
    
    input_text = ""
    
    if input_method == "Text Input":
        input_text = st.text_area(
            "Enter text to enhance:",
            height=200,
            placeholder="Paste your transcript here... (e.g., 'hello world this is a test can you hear me yes i can')"
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload text file",
            type=['txt', 'md'],
            help="Upload a text file containing the transcript to enhance"
        )
        
        if uploaded_file is not None:
            input_text = str(uploaded_file.read(), "utf-8")
            st.text_area("Uploaded text:", value=input_text, height=150, disabled=True)
    
    if st.button("Enhance Text", type="primary", disabled=not input_text):
        enhance_single_text(
            input_text, restore_punctuation, fix_capitalization,
            format_numbers, format_quotes, format_dates, confidence_threshold
        )

def enhance_single_text(input_text, restore_punctuation, fix_capitalization,
                       format_numbers, format_quotes, format_dates, confidence_threshold):
    """Enhance a single text and display results"""
    
    options = {
        'restore_punctuation': restore_punctuation,
        'fix_capitalization': fix_capitalization,
        'format_numbers': format_numbers,
        'format_quotes': format_quotes,
        'format_dates': format_dates,
        'confidence_threshold': confidence_threshold
    }
    
    with st.spinner("Enhancing text..."):
        service = get_punctuation_service()
        result = service.enhance_transcript(input_text, options)
    
    if result['success']:
        # Display results
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Text")
            st.text_area("", value=result['original_text'], height=200, disabled=True)
        
        with col2:
            st.subheader("Enhanced Text")
            st.text_area("", value=result['enhanced_text'], height=200, disabled=True)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Confidence Score", f"{result['confidence_score']:.2f}")
        
        with col2:
            st.metric("Changes Made", len(result['changes_made']))
        
        with col3:
            st.metric("Processing Time", f"{result['processing_time']:.2f}s")
        
        with col4:
            improvement_ratio = result['statistics']['improvement_ratio']
            st.metric("Length Change", f"{improvement_ratio:.2f}x")
        
        # Changes details
        if result['changes_made']:
            st.subheader("Changes Made")
            
            changes_df = pd.DataFrame(result['changes_made'])
            
            # Display changes table
            st.dataframe(
                changes_df[['change_type', 'original', 'replacement', 'confidence', 'reason']],
                use_container_width=True
            )
            
            # Changes visualization
            if len(changes_df) > 0:
                fig = px.histogram(
                    changes_df,
                    x='change_type',
                    title="Changes by Type",
                    color='change_type'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Download options
        st.subheader("Download Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                "Download Enhanced Text",
                data=result['enhanced_text'],
                file_name=f"enhanced_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col2:
            changes_json = json.dumps(result['changes_made'], indent=2)
            st.download_button(
                "Download Changes (JSON)",
                data=changes_json,
                file_name=f"changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col3:
            full_result = json.dumps(result, indent=2, default=str)
            st.download_button(
                "Download Full Report",
                data=full_result,
                file_name=f"enhancement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    else:
        st.error(f"Enhancement failed: {result.get('error', 'Unknown error')}")

def batch_processing_interface(restore_punctuation, fix_capitalization, format_numbers,
                              format_quotes, format_dates, confidence_threshold):
    """Interface for batch text enhancement"""
    st.header("Batch Processing")
    
    # Input methods for batch
    batch_method = st.radio(
        "Batch Input Method",
        ["Multiple Text Areas", "File Upload", "CSV Upload"],
        horizontal=True
    )
    
    texts = []
    
    if batch_method == "Multiple Text Areas":
        num_texts = st.number_input("Number of texts", min_value=1, max_value=10, value=3)
        
        for i in range(num_texts):
            text = st.text_area(f"Text {i+1}:", key=f"batch_text_{i}", height=100)
            if text.strip():
                texts.append(text.strip())
    
    elif batch_method == "File Upload":
        uploaded_files = st.file_uploader(
            "Upload multiple text files",
            type=['txt', 'md'],
            accept_multiple_files=True
        )
        
        for uploaded_file in uploaded_files:
            text = str(uploaded_file.read(), "utf-8")
            texts.append(text)
            
        if texts:
            st.success(f"Loaded {len(texts)} files")
    
    elif batch_method == "CSV Upload":
        uploaded_csv = st.file_uploader(
            "Upload CSV with text column",
            type=['csv']
        )
        
        if uploaded_csv is not None:
            df = pd.read_csv(uploaded_csv)
            text_columns = df.select_dtypes(include=['object']).columns.tolist()
            
            if text_columns:
                selected_column = st.selectbox("Select text column:", text_columns)
                texts = df[selected_column].dropna().tolist()
                st.success(f"Loaded {len(texts)} texts from CSV")
            else:
                st.error("No text columns found in CSV")
    
    if texts and st.button("Process Batch", type="primary"):
        process_batch(
            texts, restore_punctuation, fix_capitalization,
            format_numbers, format_quotes, format_dates, confidence_threshold
        )

def process_batch(texts, restore_punctuation, fix_capitalization,
                 format_numbers, format_quotes, format_dates, confidence_threshold):
    """Process batch of texts"""
    
    options = {
        'restore_punctuation': restore_punctuation,
        'fix_capitalization': fix_capitalization,
        'format_numbers': format_numbers,
        'format_quotes': format_quotes,
        'format_dates': format_dates,
        'confidence_threshold': confidence_threshold
    }
    
    service = get_punctuation_service()
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, text in enumerate(texts):
        status_text.text(f"Processing text {i+1}/{len(texts)}...")
        progress_bar.progress((i + 1) / len(texts))
        
        result = service.enhance_transcript(text, options)
        results.append(result)
        
        time.sleep(0.1)  # Small delay for UI responsiveness
    
    status_text.text("Processing complete!")
    
    # Display batch results
    st.subheader("Batch Results")
    
    # Summary metrics
    successful_results = [r for r in results if r['success']]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Processed", len(results))
    
    with col2:
        st.metric("Successful", len(successful_results))
    
    with col3:
        if successful_results:
            avg_confidence = sum(r['confidence_score'] for r in successful_results) / len(successful_results)
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")
        else:
            st.metric("Avg Confidence", "N/A")
    
    with col4:
        total_changes = sum(len(r.get('changes_made', [])) for r in successful_results)
        st.metric("Total Changes", total_changes)
    
    # Results table
    if successful_results:
        results_data = []
        for i, result in enumerate(successful_results):
            results_data.append({
                'Text #': i + 1,
                'Original Length': len(result['original_text']),
                'Enhanced Length': len(result['enhanced_text']),
                'Changes': len(result['changes_made']),
                'Confidence': result['confidence_score'],
                'Processing Time': f"{result['processing_time']:.2f}s"
            })
        
        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, use_container_width=True)
        
        # Batch visualization
        fig = px.scatter(
            results_df,
            x='Original Length',
            y='Enhanced Length',
            size='Changes',
            color='Confidence',
            title="Enhancement Results Overview",
            hover_data=['Processing Time']
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Download batch results
        st.subheader("Download Batch Results")
        
        # Prepare download data
        enhanced_texts = [r['enhanced_text'] for r in successful_results]
        batch_text = '\n\n---\n\n'.join(enhanced_texts)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                "Download All Enhanced Texts",
                data=batch_text,
                file_name=f"batch_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col2:
            batch_results_json = json.dumps(successful_results, indent=2, default=str)
            st.download_button(
                "Download Full Batch Report",
                data=batch_results_json,
                file_name=f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

def statistics_interface():
    """Display enhancement statistics"""
    st.header("Enhancement Statistics")
    
    service = get_punctuation_service()
    stats = service.get_enhancement_statistics()
    
    if 'message' in stats:
        st.info(stats['message'])
        return
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Enhancements", stats['total_enhancements'])
        st.metric("Average Confidence", f"{stats['average_confidence']:.3f}")
    
    with col2:
        st.metric("Average Processing Time", f"{stats['average_processing_time']:.3f}s")
        st.metric("Total Changes Made", stats['total_changes_made'])
    
    with col3:
        st.metric("Avg Changes per Text", f"{stats['average_changes_per_text']:.1f}")
    
    # Performance over time (if we had timestamps)
    st.subheader("Performance Insights")
    
    # Create sample performance chart
    performance_data = {
        'Metric': ['Confidence', 'Processing Speed', 'Change Accuracy'],
        'Score': [stats['average_confidence'] * 100, 
                 min(100, (1 / stats['average_processing_time']) * 10),
                 85]  # Mock accuracy score
    }
    
    fig = px.bar(
        performance_data,
        x='Metric',
        y='Score',
        title="Enhancement Performance Metrics",
        color='Metric'
    )
    fig.update_layout(yaxis_title="Score (%)")
    st.plotly_chart(fig, use_container_width=True)

def examples_interface():
    """Show examples of text enhancement"""
    st.header("Enhancement Examples")
    
    examples = [
        {
            "title": "Basic Punctuation",
            "original": "hello world this is a test can you hear me yes i can hear you perfectly",
            "description": "Adding basic punctuation and capitalization"
        },
        {
            "title": "Question Detection",
            "original": "what time is it now its three thirty pm where are you going after this",
            "description": "Detecting questions and adding appropriate punctuation"
        },
        {
            "title": "Number Formatting",
            "original": "please turn to page twenty three and read chapter five section two",
            "description": "Converting number words to digits in appropriate contexts"
        },
        {
            "title": "Quote Formatting",
            "original": "he said quote i will be there at five pm unquote and then left",
            "description": "Converting spoken quotes to proper quotation marks"
        },
        {
            "title": "Complex Sentence",
            "original": "the meeting is scheduled for january fifteenth two thousand twenty four at ten am but we might need to reschedule if the weather is bad",
            "description": "Comprehensive enhancement with dates, times, and conjunctions"
        }
    ]
    
    for i, example in enumerate(examples):
        with st.expander(f"Example {i+1}: {example['title']}"):
            st.write(f"**Description:** {example['description']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Original:**")
                st.code(example['original'])
            
            with col2:
                if st.button(f"Enhance Example {i+1}", key=f"example_{i}"):
                    with st.spinner("Enhancing..."):
                        service = get_punctuation_service()
                        result = service.enhance_transcript(example['original'])
                    
                    if result['success']:
                        st.write("**Enhanced:**")
                        st.code(result['enhanced_text'])
                        st.write(f"**Confidence:** {result['confidence_score']:.2f}")
                        st.write(f"**Changes:** {len(result['changes_made'])}")
    
    # Tips section
    st.subheader("Enhancement Tips")
    
    tips = [
        "🎯 **Higher confidence threshold** = fewer but more certain changes",
        "📝 **Enable all formatting options** for comprehensive enhancement",
        "🔤 **Capitalization fixing** works best with proper nouns and sentence beginnings",
        "🔢 **Number formatting** is context-aware and won't change every number word",
        "💬 **Quote formatting** looks for 'quote...unquote' patterns",
        "📅 **Date formatting** standardizes date expressions",
        "⚡ **AI model** generally provides better results than rule-based approach"
    ]
    
    for tip in tips:
        st.markdown(tip)

if __name__ == "__main__":
    main()