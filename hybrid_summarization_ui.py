#!/usr/bin/env python3
"""
Hybrid Summarization System UI
Streamlit interface for Task 123: Build hybrid summarization system
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import time

# Import our summarization system
try:
    from hybrid_summarization_system import (
        SummarizationService, SummarizationRequest, SummaryResult,
        SummarizationType, SummaryLength, SummaryStyle
    )
except ImportError:
    st.error("Hybrid Summarization system not found.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Hybrid Summarization System",
    page_icon="📝",
    layout="wide"
)

# Initialize session state
if 'summarization_service' not in st.session_state:
    st.session_state.summarization_service = SummarizationService()

if 'summary_history' not in st.session_state:
    st.session_state.summary_history = []

def main():
    """Main application interface"""
    st.title("📝 Hybrid Summarization System")
    st.markdown("**Task 123: Build hybrid summarization system**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        [
            "🏠 Home",
            "📄 Single Document", 
            "📚 Multi-Document",
            "🔍 Query-Focused",
            "📊 Analytics"
        ]
    )
    
    # Route to appropriate page
    if page == "🏠 Home":
        show_home()
    elif page == "📄 Single Document":
        show_single_document()
    elif page == "📚 Multi-Document":
        show_multi_document()
    elif page == "🔍 Query-Focused":
        show_query_focused()
    elif page == "📊 Analytics":
        show_analytics()

if __name__ == "__main__":
    main()def
 show_home():
    """Show home page with overview"""
    st.header("🏠 Welcome to Hybrid Summarization")
    
    st.markdown("""
    This advanced summarization system combines multiple AI approaches:
    
    ### 🔧 **Features**
    - **Extractive Summarization**: Select key sentences from original text
    - **Abstractive Summarization**: Generate new text that captures meaning
    - **Hybrid Approach**: Combine both methods for optimal results
    - **Multi-Document**: Summarize multiple documents together
    - **Query-Focused**: Create summaries focused on specific questions
    """)
    
    # Quick demo section
    st.subheader("🎯 Quick Demo")
    
    demo_text = st.text_area(
        "Try a quick summary:",
        value="Artificial intelligence (AI) is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions. Companies are using AI for everything from customer service chatbots to autonomous vehicles. However, there are concerns about job displacement and the need for ethical AI development.",
        height=150
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        demo_type = st.selectbox("Type", ["Hybrid", "Extractive", "Abstractive"])
    
    with col2:
        demo_length = st.selectbox("Length", ["Short", "Medium", "Brief"])
    
    with col3:
        demo_style = st.selectbox("Style", ["Formal", "Casual", "Technical"])
    
    if st.button("Generate Quick Summary", type="primary"):
        if demo_text.strip():
            with st.spinner("Generating summary..."):
                try:
                    request = SummarizationRequest(
                        text=demo_text,
                        summary_type=SummarizationType(demo_type.lower()),
                        length=SummaryLength(demo_length.lower()),
                        style=SummaryStyle(demo_style.lower())
                    )
                    
                    result = asyncio.run(st.session_state.summarization_service.summarize(request))
                    
                    st.success("Summary generated successfully!")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("**Summary:**")
                        st.write(result.summary)
                    
                    with col2:
                        st.markdown("**Metrics:**")
                        st.metric("Words", result.word_count)
                        st.metric("Quality", f"{result.quality_score:.2f}")
                        st.metric("Compression", f"{result.compression_ratio:.1f}:1")
                
                except Exception as e:
                    st.error(f"Error generating summary: {str(e)}")
        else:
            st.warning("Please enter some text to summarize.")

def show_single_document():
    """Show single document summarization interface"""
    st.header("📄 Single Document Summarization")
    
    # Input methods
    input_method = st.radio(
        "Choose input method:",
        ["Text Input", "File Upload"]
    )
    
    text_content = ""
    
    if input_method == "Text Input":
        text_content = st.text_area(
            "Enter text to summarize:",
            height=300,
            placeholder="Paste your text here..."
        )
    
    elif input_method == "File Upload":
        uploaded_file = st.file_uploader(
            "Upload a text file",
            type=['txt', 'md'],
            help="Supported formats: TXT, MD"
        )
        
        if uploaded_file:
            try:
                text_content = str(uploaded_file.read(), "utf-8")
                st.success(f"File loaded: {len(text_content.split())} words")
                
                with st.expander("Preview uploaded content"):
                    st.text(text_content[:500] + "..." if len(text_content) > 500 else text_content)
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    if text_content.strip():
        # Configuration section
        st.subheader("⚙️ Summary Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            summary_type = st.selectbox(
                "Summarization Type",
                ["Hybrid", "Extractive", "Abstractive"],
                help="Hybrid combines both extractive and abstractive methods"
            )
        
        with col2:
            length = st.selectbox(
                "Summary Length",
                ["Brief", "Short", "Medium", "Long"],
                index=2
            )
        
        with col3:
            style = st.selectbox(
                "Writing Style",
                ["Formal", "Casual", "Technical", "Executive", "Academic"]
            )
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                max_sentences = st.number_input(
                    "Max Sentences (0 = auto)",
                    min_value=0, max_value=50, value=0
                )
                
                focus_keywords = st.text_input(
                    "Focus Keywords (comma-separated)",
                    placeholder="keyword1, keyword2, keyword3"
                )
            
            with col2:
                max_words = st.number_input(
                    "Max Words (0 = auto)",
                    min_value=0, max_value=1000, value=0
                )
                
                exclude_keywords = st.text_input(
                    "Exclude Keywords (comma-separated)",
                    placeholder="word1, word2, word3"
                )
        
        # Generate summary
        if st.button("Generate Summary", type="primary"):
            with st.spinner("Generating summary..."):
                try:
                    request = SummarizationRequest(
                        text=text_content,
                        summary_type=SummarizationType(summary_type.lower()),
                        length=SummaryLength(length.lower()),
                        style=SummaryStyle(style.lower()),
                        max_sentences=max_sentences if max_sentences > 0 else None,
                        max_words=max_words if max_words > 0 else None,
                        focus_keywords=[kw.strip() for kw in focus_keywords.split(",")] if focus_keywords else None,
                        exclude_keywords=[kw.strip() for kw in exclude_keywords.split(",")] if exclude_keywords else None
                    )
                    
                    start_time = time.time()
                    result = asyncio.run(st.session_state.summarization_service.summarize(request))
                    processing_time = time.time() - start_time
                    
                    # Store in history
                    st.session_state.summary_history.append({
                        'timestamp': datetime.now(),
                        'type': 'Single Document',
                        'summary_type': summary_type,
                        'result': result,
                        'processing_time': processing_time
                    })
                    
                    # Display results
                    display_summary_result(result, text_content)
                
                except Exception as e:
                    st.error(f"Error generating summary: {str(e)}")
    
    else:
        st.info("Please enter or upload text to summarize.")

def display_summary_result(result: SummaryResult, original_text: str):
    """Display summary result with metrics and options"""
    st.success("Summary generated successfully!")
    
    # Main summary display
    st.markdown("### 📝 Summary")
    st.write(result.summary)
    
    # Metrics dashboard
    st.markdown("### 📊 Summary Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Word Count", result.word_count)
    
    with col2:
        st.metric("Sentences", result.sentence_count)
    
    with col3:
        st.metric("Compression Ratio", f"{result.compression_ratio:.1f}:1")
    
    with col4:
        st.metric("Quality Score", f"{result.quality_score:.2f}")
    
    # Additional details
    col1, col2 = st.columns(2)
    
    with col1:
        if result.key_points:
            st.markdown("### 🎯 Key Points")
            for i, point in enumerate(result.key_points, 1):
                st.write(f"{i}. {point}")
    
    with col2:
        st.markdown("### ⚙️ Summary Details")
        st.write(f"**Type:** {result.summary_type.value.title()}")
        st.write(f"**Style:** {result.style.value.title()}")
        st.write(f"**Length:** {result.length.value.title()}")
        st.write(f"**Confidence:** {result.confidence_score:.2f}")
        st.write(f"**Processing Time:** {result.processing_time:.2f}s")
    
    # Export options
    st.markdown("### 💾 Export Options")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        # Create downloadable JSON
        export_data = {
            'summary': result.summary,
            'metrics': {
                'word_count': result.word_count,
                'sentence_count': result.sentence_count,
                'compression_ratio': result.compression_ratio,
                'quality_score': result.quality_score,
                'confidence_score': result.confidence_score
            },
            'key_points': result.key_points,
            'created_at': result.created_at.isoformat()
        }
        
        st.download_button(
            "📥 Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with export_col2:
        # Create text export
        text_export = f"""SUMMARY
{'-' * 50}
{result.summary}

METRICS
{'-' * 50}
Word Count: {result.word_count}
Sentences: {result.sentence_count}
Compression Ratio: {result.compression_ratio:.1f}:1
Quality Score: {result.quality_score:.2f}

KEY POINTS
{'-' * 50}
{chr(10).join([f"{i}. {point}" for i, point in enumerate(result.key_points, 1)])}

Generated: {result.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        st.download_button(
            "📄 Download TXT",
            data=text_export,
            file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )d
ef show_multi_document():
    """Show multi-document summarization interface"""
    st.header("📚 Multi-Document Summarization")
    
    st.markdown("""
    Combine and summarize multiple documents to create a unified summary.
    """)
    
    # Document management
    if 'documents' not in st.session_state:
        st.session_state.documents = []
    
    # Add document section
    st.subheader("➕ Add Documents")
    
    with st.expander("Add New Document", expanded=len(st.session_state.documents) == 0):
        doc_title = st.text_input("Document Title (optional)")
        doc_content = st.text_area("Document Content", height=200)
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("Add Document"):
                if doc_content.strip():
                    doc_id = f"doc_{len(st.session_state.documents) + 1}"
                    st.session_state.documents.append({
                        'id': doc_id,
                        'title': doc_title or f"Document {len(st.session_state.documents) + 1}",
                        'content': doc_content,
                        'word_count': len(doc_content.split()),
                        'added_at': datetime.now()
                    })
                    st.success("Document added!")
                    st.rerun()
                else:
                    st.warning("Please enter document content.")
        
        with col2:
            uploaded_files = st.file_uploader(
                "Or upload multiple files",
                type=['txt', 'md'],
                accept_multiple_files=True
            )
            
            if uploaded_files:
                for file in uploaded_files:
                    try:
                        content = str(file.read(), "utf-8")
                        doc_id = f"doc_{len(st.session_state.documents) + 1}"
                        st.session_state.documents.append({
                            'id': doc_id,
                            'title': file.name,
                            'content': content,
                            'word_count': len(content.split()),
                            'added_at': datetime.now()
                        })
                    except Exception as e:
                        st.error(f"Error reading {file.name}: {str(e)}")
                
                if uploaded_files:
                    st.success(f"Added {len(uploaded_files)} documents!")
                    st.rerun()
    
    # Display current documents
    if st.session_state.documents:
        st.subheader(f"📋 Current Documents ({len(st.session_state.documents)})")
        
        for i, doc in enumerate(st.session_state.documents):
            with st.expander(f"{doc['title']} ({doc['word_count']} words)"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.text_area(
                        "Content:",
                        value=doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content'],
                        height=100,
                        disabled=True,
                        key=f"doc_preview_{i}"
                    )
                
                with col2:
                    st.write(f"**Added:** {doc['added_at'].strftime('%Y-%m-%d %H:%M')}")
                    if st.button(f"Remove", key=f"remove_{i}"):
                        st.session_state.documents.pop(i)
                        st.rerun()
        
        # Summarization configuration
        st.subheader("⚙️ Multi-Document Summary Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            summary_type = st.selectbox(
                "Summarization Type",
                ["Hybrid", "Extractive", "Abstractive"],
                key="multi_doc_type"
            )
        
        with col2:
            length = st.selectbox(
                "Summary Length",
                ["Brief", "Short", "Medium", "Long"],
                index=2,
                key="multi_doc_length"
            )
        
        with col3:
            style = st.selectbox(
                "Writing Style",
                ["Formal", "Technical", "Executive", "Academic"],
                key="multi_doc_style"
            )
        
        # Generate multi-document summary
        if st.button("Generate Multi-Document Summary", type="primary"):
            with st.spinner("Processing multiple documents..."):
                try:
                    request = SummarizationRequest(
                        text="",  # Will be filled by multi-doc summarizer
                        summary_type=SummarizationType(summary_type.lower()),
                        length=SummaryLength(length.lower()),
                        style=SummaryStyle(style.lower())
                    )
                    
                    start_time = time.time()
                    result = asyncio.run(
                        st.session_state.summarization_service.summarize_documents(
                            st.session_state.documents, request
                        )
                    )
                    processing_time = time.time() - start_time
                    
                    # Store in history
                    st.session_state.summary_history.append({
                        'timestamp': datetime.now(),
                        'type': 'Multi-Document',
                        'summary_type': summary_type,
                        'result': result,
                        'processing_time': processing_time,
                        'document_count': len(st.session_state.documents)
                    })
                    
                    # Display results
                    combined_text = " ".join([doc['content'] for doc in st.session_state.documents])
                    display_summary_result(result, combined_text)
                
                except Exception as e:
                    st.error(f"Error generating multi-document summary: {str(e)}")
        
        # Clear documents
        if st.button("Clear All Documents", type="secondary"):
            st.session_state.documents = []
            st.rerun()
    
    else:
        st.info("Add documents above to begin multi-document summarization.")

def show_query_focused():
    """Show query-focused summarization interface"""
    st.header("🔍 Query-Focused Summarization")
    
    st.markdown("""
    Generate summaries that focus on specific questions or topics of interest.
    """)
    
    # Input text
    text_content = st.text_area(
        "Enter text to summarize:",
        height=250,
        placeholder="Paste your text here..."
    )
    
    # Query input
    query = st.text_input(
        "Enter your question or focus topic:",
        placeholder="What are the main benefits of artificial intelligence?",
        help="Be specific about what you want to learn from the text"
    )
    
    if text_content.strip() and query.strip():
        # Configuration
        col1, col2, col3 = st.columns(3)
        
        with col1:
            length = st.selectbox(
                "Summary Length",
                ["Brief", "Short", "Medium", "Long"],
                index=1,
                key="query_length"
            )
        
        with col2:
            style = st.selectbox(
                "Writing Style",
                ["Formal", "Casual", "Technical", "Executive"],
                key="query_style"
            )
        
        with col3:
            max_sentences = st.number_input(
                "Max Sentences",
                min_value=1, max_value=20, value=5,
                key="query_sentences"
            )
        
        # Generate query-focused summary
        if st.button("Generate Query-Focused Summary", type="primary"):
            with st.spinner("Analyzing text for your query..."):
                try:
                    request = SummarizationRequest(
                        text=text_content,
                        summary_type=SummarizationType.QUERY_FOCUSED,
                        length=SummaryLength(length.lower()),
                        style=SummaryStyle(style.lower()),
                        query=query,
                        max_sentences=max_sentences
                    )
                    
                    start_time = time.time()
                    result = asyncio.run(st.session_state.summarization_service.summarize(request))
                    processing_time = time.time() - start_time
                    
                    # Store in history
                    st.session_state.summary_history.append({
                        'timestamp': datetime.now(),
                        'type': 'Query-Focused',
                        'query': query,
                        'result': result,
                        'processing_time': processing_time
                    })
                    
                    # Display results with query context
                    st.success("Query-focused summary generated!")
                    
                    st.markdown(f"**Query:** {query}")
                    st.markdown("**Summary:**")
                    st.write(result.summary)
                    
                    # Show metrics and extracted sentences
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Metrics:**")
                        st.metric("Words", result.word_count)
                        st.metric("Quality Score", f"{result.quality_score:.2f}")
                        st.metric("Relevance", f"{result.confidence_score:.2f}")
                    
                    with col2:
                        if result.extracted_sentences:
                            st.markdown("**Key Sentences:**")
                            for i, sentence in enumerate(result.extracted_sentences[:3], 1):
                                st.write(f"{i}. {sentence}")
                
                except Exception as e:
                    st.error(f"Error generating query-focused summary: {str(e)}")
    
    elif not text_content.strip():
        st.info("Please enter text to summarize.")
    elif not query.strip():
        st.info("Please enter a question or focus topic.")

def show_analytics():
    """Show analytics and summary history"""
    st.header("📊 Analytics & History")
    
    if not st.session_state.summary_history:
        st.info("No summaries generated yet. Create some summaries to see analytics here.")
        return
    
    # Summary statistics
    st.subheader("📈 Summary Statistics")
    
    total_summaries = len(st.session_state.summary_history)
    avg_processing_time = sum(h.get('processing_time', 0) for h in st.session_state.summary_history) / total_summaries
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Summaries", total_summaries)
    
    with col2:
        st.metric("Avg Processing Time", f"{avg_processing_time:.2f}s")
    
    with col3:
        type_counts = {}
        for h in st.session_state.summary_history:
            t = h.get('type', 'Unknown')
            type_counts[t] = type_counts.get(t, 0) + 1
        most_used = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "None"
        st.metric("Most Used Type", most_used)
    
    with col4:
        avg_quality = sum(h['result'].quality_score for h in st.session_state.summary_history) / total_summaries
        st.metric("Avg Quality Score", f"{avg_quality:.2f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Summary type distribution
        type_data = {}
        for h in st.session_state.summary_history:
            t = h.get('summary_type', 'Unknown')
            type_data[t] = type_data.get(t, 0) + 1
        
        if type_data:
            fig = px.pie(
                values=list(type_data.values()),
                names=list(type_data.keys()),
                title="Summary Types Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Quality scores over time
        if len(st.session_state.summary_history) > 1:
            quality_data = []
            for i, h in enumerate(st.session_state.summary_history):
                quality_data.append({
                    'Index': i + 1,
                    'Quality Score': h['result'].quality_score,
                    'Type': h.get('summary_type', 'Unknown')
                })
            
            df = pd.DataFrame(quality_data)
            fig = px.line(df, x='Index', y='Quality Score', color='Type',
                         title="Quality Scores Over Time")
            st.plotly_chart(fig, use_container_width=True)
    
    # Summary history table
    st.subheader("📋 Summary History")
    
    history_data = []
    for i, h in enumerate(st.session_state.summary_history):
        history_data.append({
            'ID': i + 1,
            'Timestamp': h['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'Type': h.get('type', 'Unknown'),
            'Summary Type': h.get('summary_type', 'Unknown'),
            'Word Count': h['result'].word_count,
            'Quality Score': f"{h['result'].quality_score:.2f}",
            'Processing Time': f"{h.get('processing_time', 0):.2f}s"
        })
    
    if history_data:
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
        
        # Export history
        if st.button("📥 Export History"):
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                data=csv,
                file_name=f"summary_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )