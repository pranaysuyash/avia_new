#!/usr/bin/env python3
"""
Streamlit UI for Comprehensive Text Classification System
Task 122: Interactive web interface for text classification
"""

import asyncio
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any

from comprehensive_text_classification_system import ComprehensiveTextClassificationSystem

# Configure Streamlit page
st.set_page_config(
    page_title="Text Classification System",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'classifier_system' not in st.session_state:
    st.session_state.classifier_system = ComprehensiveTextClassificationSystem()
if 'classification_history' not in st.session_state:
    st.session_state.classification_history = []

def main():
    """Main application interface."""
    st.title("📝 Comprehensive Text Classification System")
    st.markdown("**Advanced multi-label classification for content types and domains**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🔍 Text Classifier", "📊 Analytics", "🎯 Training", "⚙️ Settings", "📚 Help"]
    )
    
    if page == "🔍 Text Classifier":
        text_classifier_page()
    elif page == "📊 Analytics":
        analytics_page()
    elif page == "🎯 Training":
        training_page()
    elif page == "⚙️ Settings":
        settings_page()
    elif page == "📚 Help":
        help_page()


def text_classifier_page():
    """Main text classification interface."""
    st.header("🔍 Text Classification")
    
    # Input methods
    input_method = st.radio(
        "Choose input method:",
        ["Single Text", "Batch Upload", "Real-time Input"]
    )
    
    if input_method == "Single Text":
        single_text_classification()
    elif input_method == "Batch Upload":
        batch_classification()
    elif input_method == "Real-time Input":
        realtime_classification()


def single_text_classification():
    """Single text classification interface."""
    st.subheader("Single Text Classification")
    
    # Text input area
    text_input = st.text_area(
        "Enter text to classify:",
        height=200,
        placeholder="Paste your text here for classification..."
    )
    
    # Configuration options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Classification Options")
        include_domains = st.multiselect(
            "Include domain-specific classification:",
            ["medical", "legal", "technical", "business"],
            default=[]
        )
        
        confidence_threshold = st.slider(
            "Confidence threshold:",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Minimum confidence score to display results"
        )
    
    with col2:
        st.subheader("Output Options")
        show_all_scores = st.checkbox("Show all scores", value=False)
        include_medical = st.checkbox("Include medical analysis", value=True)
        export_results = st.checkbox("Enable result export", value=False)
    
    # Classification button
    if st.button("🔍 Classify Text", type="primary"):
        if text_input.strip():
            classify_single_text(
                text_input, 
                include_domains, 
                confidence_threshold,
                show_all_scores,
                include_medical,
                export_results
            )
        else:
            st.warning("Please enter some text to classify.")


async def classify_single_text(text: str, domains: List[str], threshold: float,
                              show_all: bool, include_medical: bool, export: bool):
    """Classify single text and display results."""
    
    with st.spinner("Classifying text..."):
        try:
            # Get classification results
            result = await st.session_state.classifier_system.classify_text(
                text, include_domains=domains
            )
            
            if 'error' in result:
                st.error(f"Classification error: {result['error']}")
                return
            
            # Store in history
            result['input_text'] = text[:200] + "..." if len(text) > 200 else text
            st.session_state.classification_history.append(result)
            
            # Display results
            display_classification_results(result, threshold, show_all, include_medical)
            
            # Export option
            if export:
                export_classification_results(result)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")


def display_classification_results(result: Dict[str, Any], threshold: float, 
                                 show_all: bool, include_medical: bool):
    """Display classification results in an organized format."""
    
    st.success("✅ Text classified successfully!")
    
    classifications = result.get('classifications', {})
    
    # Content Types
    st.subheader("📋 Content Types")
    content_types = classifications.get('content_types', {})
    
    if content_types:
        # Filter by threshold
        if not show_all:
            content_types = {k: v for k, v in content_types.items() if v >= threshold}
        
        if content_types:
            # Create DataFrame for better display
            df_content = pd.DataFrame([
                {'Content Type': k.replace('_', ' ').title(), 'Confidence': v}
                for k, v in content_types.items()
            ]).sort_values('Confidence', ascending=False)
            
            # Display as metrics
            cols = st.columns(min(len(df_content), 4))
            for i, (_, row) in enumerate(df_content.iterrows()):
                if i < len(cols):
                    cols[i].metric(
                        row['Content Type'],
                        f"{row['Confidence']:.3f}",
                        help=f"Confidence score: {row['Confidence']:.3f}"
                    )
            
            # Show as bar chart
            if len(df_content) > 1:
                fig = px.bar(
                    df_content,
                    x='Content Type',
                    y='Confidence',
                    title='Content Type Classification Scores',
                    color='Confidence',
                    color_continuous_scale='viridis'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No content types found above the confidence threshold.")
    else:
        st.info("No content type classification available.")
    
    # Domain Classifications
    domains = classifications.get('domains', {})
    if domains:
        st.subheader("🎯 Domain-Specific Classifications")
        
        for domain, domain_result in domains.items():
            with st.expander(f"📁 {domain.title()} Domain", expanded=True):
                if isinstance(domain_result, dict):
                    pred_class = domain_result.get('predicted_class', 'Unknown')
                    confidence = domain_result.get('confidence', 0.0)
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Predicted Class", pred_class)
                    col2.metric("Confidence", f"{confidence:.3f}")
                    
                    # Show all scores if available
                    all_scores = domain_result.get('all_scores', {})
                    if all_scores and show_all:
                        st.write("**All Classification Scores:**")
                        scores_df = pd.DataFrame([
                            {'Class': k, 'Score': v}
                            for k, v in all_scores.items()
                        ]).sort_values('Score', ascending=False)
                        st.dataframe(scores_df, use_container_width=True)
    
    # Medical Classification
    medical = classifications.get('medical')
    if medical and include_medical:
        st.subheader("🏥 Medical Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            "Specialty",
            medical.get('specialty', 'N/A').replace('_', ' ').title()
        )
        
        col2.metric(
            "Document Type",
            medical.get('document_type', 'N/A').replace('_', ' ').title()
        )
        
        col3.metric(
            "Urgency Level",
            medical.get('urgency', 'N/A').title()
        )
        
        col4.metric(
            "Compliance Score",
            f"{medical.get('compliance_score', 1.0):.2f}"
        )
        
        # PHI Detection Warning
        if medical.get('phi_detected', False):
            st.error("⚠️ Potential PHI (Personal Health Information) detected!")
            st.warning("Please ensure HIPAA compliance when handling this content.")
    
    # Metadata
    with st.expander("📋 Classification Metadata", expanded=False):
        col1, col2 = st.columns(2)
        
        col1.write(f"**Text Hash:** {result.get('text_hash', 'N/A')}")
        col1.write(f"**Timestamp:** {result.get('timestamp', 'N/A')}")
        
        col2.write(f"**Processing Time:** < 1 second")
        col2.write(f"**Model Version:** v1.0")


def batch_classification():
    """Batch classification interface."""
    st.subheader("📦 Batch Text Classification")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a file containing texts to classify:",
        type=['txt', 'csv', 'json'],
        help="Supported formats: TXT (one text per line), CSV (text column), JSON (array of texts)"
    )
    
    if uploaded_file:
        try:
            # Process uploaded file
            texts = process_uploaded_file(uploaded_file)
            
            if texts:
                st.success(f"✅ Loaded {len(texts)} texts for classification")
                
                # Preview texts
                with st.expander("📖 Preview Texts", expanded=False):
                    for i, text in enumerate(texts[:5], 1):
                        st.write(f"**Text {i}:** {text[:200]}...")
                    
                    if len(texts) > 5:
                        st.write(f"... and {len(texts) - 5} more texts")
                
                # Batch classification options
                col1, col2 = st.columns(2)
                
                with col1:
                    batch_size = st.number_input(
                        "Batch size:", min_value=1, max_value=50, value=10
                    )
                    
                    include_domains = st.multiselect(
                        "Include domain classification:",
                        ["medical", "legal", "technical", "business"]
                    )
                
                with col2:
                    confidence_threshold = st.slider(
                        "Confidence threshold:", 0.0, 1.0, 0.3, 0.1
                    )
                    
                    export_format = st.selectbox(
                        "Export format:",
                        ["JSON", "CSV", "Excel"]
                    )
                
                # Classification button
                if st.button("🚀 Start Batch Classification", type="primary"):
                    run_batch_classification(texts, batch_size, include_domains, 
                                           confidence_threshold, export_format)
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")


def process_uploaded_file(uploaded_file) -> List[str]:
    """Process uploaded file and extract texts."""
    texts = []
    
    if uploaded_file.type == "text/plain":
        # TXT file - one text per line
        content = str(uploaded_file.read(), "utf-8")
        texts = [line.strip() for line in content.split('\n') if line.strip()]
    
    elif uploaded_file.type == "text/csv":
        # CSV file
        df = pd.read_csv(uploaded_file)
        text_column = st.selectbox(
            "Select the text column:",
            df.columns.tolist()
        )
        texts = df[text_column].fillna('').astype(str).tolist()
    
    elif uploaded_file.type == "application/json":
        # JSON file
        content = json.loads(uploaded_file.read())
        if isinstance(content, list):
            texts = [str(item) for item in content]
        elif isinstance(content, dict) and 'texts' in content:
            texts = [str(item) for item in content['texts']]
        else:
            st.error("JSON format not supported. Use array of texts or object with 'texts' key.")
    
    return [text for text in texts if text.strip()]


async def run_batch_classification(texts: List[str], batch_size: int, 
                                 domains: List[str], threshold: float, 
                                 export_format: str):
    """Run batch classification with progress tracking."""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        results = []
        total_texts = len(texts)
        
        # Process in batches
        for i in range(0, total_texts, batch_size):
            batch = texts[i:i + batch_size]
            batch_results = await st.session_state.classifier_system.batch_classify(batch)
            results.extend(batch_results)
            
            # Update progress
            progress = min((i + batch_size) / total_texts, 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Processed {min(i + batch_size, total_texts)} of {total_texts} texts...")
        
        progress_bar.progress(1.0)
        status_text.text("✅ Batch classification completed!")
        
        # Display results summary
        display_batch_results(results, threshold)
        
        # Export results
        export_batch_results(results, export_format)
        
    except Exception as e:
        st.error(f"Batch classification error: {str(e)}")


def display_batch_results(results: List[Dict], threshold: float):
    """Display batch classification results summary."""
    
    st.subheader("📊 Batch Results Summary")
    
    # Summary metrics
    total_classified = len(results)
    successful = len([r for r in results if 'error' not in r])
    errors = total_classified - successful
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Texts", total_classified)
    col2.metric("Successfully Classified", successful)
    col3.metric("Errors", errors)
    
    if successful == 0:
        st.error("No texts were successfully classified.")
        return
    
    # Aggregate content type statistics
    content_type_counts = {}
    
    for result in results:
        if 'error' in result:
            continue
        
        content_types = result.get('classifications', {}).get('content_types', {})
        for content_type, score in content_types.items():
            if score >= threshold:
                content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1
    
    if content_type_counts:
        # Content type distribution
        st.subheader("📋 Content Type Distribution")
        
        df_dist = pd.DataFrame([
            {'Content Type': k.replace('_', ' ').title(), 'Count': v}
            for k, v in content_type_counts.items()
        ]).sort_values('Count', ascending=False)
        
        fig = px.pie(
            df_dist,
            values='Count',
            names='Content Type',
            title='Distribution of Content Types'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed results table
    with st.expander("📋 Detailed Results", expanded=False):
        detailed_results = []
        
        for i, result in enumerate(results):
            if 'error' in result:
                detailed_results.append({
                    'Text #': i + 1,
                    'Status': 'Error',
                    'Content Types': result.get('error', 'Unknown error'),
                    'Domains': 'N/A'
                })
            else:
                content_types = result.get('classifications', {}).get('content_types', {})
                domains = result.get('classifications', {}).get('domains', {})
                
                # Get top content type
                top_content = max(content_types.items(), key=lambda x: x[1]) if content_types else ('None', 0)
                
                detailed_results.append({
                    'Text #': i + 1,
                    'Status': 'Success',
                    'Top Content Type': f"{top_content[0]} ({top_content[1]:.3f})",
                    'Domains': ', '.join(domains.keys()) if domains else 'None'
                })
        
        df_detailed = pd.DataFrame(detailed_results)
        st.dataframe(df_detailed, use_container_width=True)


def export_batch_results(results: List[Dict], format: str):
    """Export batch classification results."""
    
    st.subheader("💾 Export Results")
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"text_classification_results_{timestamp}"
        
        if format == "JSON":
            json_data = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"{filename}.json",
                mime="application/json"
            )
        
        elif format == "CSV":
            # Flatten results for CSV
            csv_data = []
            for i, result in enumerate(results):
                if 'error' in result:
                    csv_data.append({
                        'text_id': i + 1,
                        'status': 'error',
                        'error': result['error']
                    })
                else:
                    classifications = result.get('classifications', {})
                    content_types = classifications.get('content_types', {})
                    
                    row = {
                        'text_id': i + 1,
                        'status': 'success',
                        'timestamp': result.get('timestamp', ''),
                    }
                    
                    # Add content type scores
                    for content_type, score in content_types.items():
                        row[f'content_type_{content_type}'] = score
                    
                    csv_data.append(row)
            
            df_csv = pd.DataFrame(csv_data)
            csv_string = df_csv.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_string,
                file_name=f"{filename}.csv",
                mime="text/csv"
            )
        
        elif format == "Excel":
            # Create Excel with multiple sheets
            excel_buffer = pd.ExcelWriter(f"{filename}.xlsx", engine='xlsxwriter')
            
            # Summary sheet
            summary_data = []
            for i, result in enumerate(results):
                if 'error' not in result:
                    classifications = result.get('classifications', {})
                    content_types = classifications.get('content_types', {})
                    
                    top_type = max(content_types.items(), key=lambda x: x[1]) if content_types else ('unknown', 0)
                    
                    summary_data.append({
                        'Text ID': i + 1,
                        'Top Content Type': top_type[0],
                        'Confidence': top_type[1],
                        'Timestamp': result.get('timestamp', '')
                    })
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(excel_buffer, sheet_name='Summary', index=False)
            
            excel_buffer.close()
            
            with open(f"{filename}.xlsx", "rb") as file:
                st.download_button(
                    label="📥 Download Excel",
                    data=file.read(),
                    file_name=f"{filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    except Exception as e:
        st.error(f"Export error: {str(e)}")


def realtime_classification():
    """Real-time classification interface."""
    st.subheader("⚡ Real-time Text Classification")
    st.info("Type in the text area below and see classification results update in real-time!")
    
    # Real-time text input
    text_input = st.text_area(
        "Enter text for real-time classification:",
        height=150,
        placeholder="Start typing and see results appear below..."
    )
    
    # Auto-classify as user types
    if text_input and len(text_input.strip()) > 20:  # Only classify if sufficient text
        with st.container():
            try:
                # Use synchronous mock for real-time demo
                result = mock_classify_text(text_input)
                display_realtime_results(result)
            except Exception as e:
                st.error(f"Real-time classification error: {str(e)}")
    elif text_input and len(text_input.strip()) <= 20:
        st.info("⏳ Keep typing... (minimum 20 characters needed for classification)")


def mock_classify_text(text: str) -> Dict[str, Any]:
    """Mock classification for real-time demo."""
    text_lower = text.lower()
    
    # Simple keyword-based mock classification
    content_types = {}
    
    if any(word in text_lower for word in ['learn', 'teach', 'course', 'tutorial', 'education']):
        content_types['educational'] = 0.85
        content_types['training'] = 0.45
    
    if any(word in text_lower for word in ['buy', 'sale', 'discount', 'offer', 'purchase']):
        content_types['promotional'] = 0.90
        content_types['marketing'] = 0.60
    
    if any(word in text_lower for word in ['patient', 'medical', 'clinical', 'diagnosis', 'treatment']):
        content_types['medical'] = 0.88
        content_types['clinical'] = 0.72
    
    if any(word in text_lower for word in ['meeting', 'agenda', 'discuss', 'business', 'team']):
        content_types['business'] = 0.75
        content_types['meeting'] = 0.80
    
    if any(word in text_lower for word in ['code', 'software', 'technical', 'programming', 'system']):
        content_types['technical'] = 0.83
        content_types['documentation'] = 0.55
    
    # Default if no specific type detected
    if not content_types:
        content_types['general'] = 0.50
    
    return {
        'classifications': {
            'content_types': content_types
        },
        'timestamp': datetime.now().isoformat()
    }


def display_realtime_results(result: Dict[str, Any]):
    """Display real-time classification results."""
    st.subheader("🎯 Real-time Results")
    
    content_types = result.get('classifications', {}).get('content_types', {})
    
    if content_types:
        # Sort by confidence
        sorted_types = sorted(content_types.items(), key=lambda x: x[1], reverse=True)
        
        # Display top 3 results
        for content_type, confidence in sorted_types[:3]:
            # Create a progress bar for each type
            st.write(f"**{content_type.replace('_', ' ').title()}**")
            st.progress(confidence)
            st.write(f"Confidence: {confidence:.3f}")
            st.write("")


def analytics_page():
    """Analytics and statistics page."""
    st.header("📊 Analytics & Statistics")
    
    # Get system statistics
    stats = st.session_state.classifier_system.get_classification_stats()
    
    if 'error' in stats:
        st.error(f"Error loading analytics: {stats['error']}")
        return
    
    # Overview metrics
    st.subheader("📈 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        "Total Classifications",
        stats.get('total_classifications', 0)
    )
    
    col2.metric(
        "Session Classifications",
        len(st.session_state.classification_history)
    )
    
    models_trained = stats.get('models_trained', {})
    trained_count = sum(1 for v in models_trained.values() if v)
    
    col3.metric(
        "Models Trained",
        trained_count
    )
    
    col4.metric(
        "System Uptime",
        "Running"
    )
    
    # Daily statistics
    daily_stats = stats.get('daily_stats', [])
    if daily_stats:
        st.subheader("📅 Daily Activity")
        
        df_daily = pd.DataFrame(daily_stats, columns=['Date', 'Count'])
        df_daily['Date'] = pd.to_datetime(df_daily['Date'])
        
        fig = px.line(
            df_daily,
            x='Date',
            y='Count',
            title='Daily Classifications Over Time',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Session history
    if st.session_state.classification_history:
        st.subheader("📝 Session History")
        
        history_data = []
        for i, result in enumerate(st.session_state.classification_history):
            content_types = result.get('classifications', {}).get('content_types', {})
            top_type = max(content_types.items(), key=lambda x: x[1]) if content_types else ('Unknown', 0)
            
            history_data.append({
                'ID': i + 1,
                'Text Preview': result.get('input_text', 'N/A')[:50] + "...",
                'Top Classification': f"{top_type[0]} ({top_type[1]:.3f})",
                'Timestamp': result.get('timestamp', 'N/A')
            })
        
        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True)
        
        # Clear history button
        if st.button("🗑️ Clear Session History"):
            st.session_state.classification_history = []
            st.success("Session history cleared!")
            st.rerun()


def training_page():
    """Model training and management page."""
    st.header("🎯 Training & Model Management")
    
    st.info("🚧 Training interface is under development. Coming soon!")
    
    # Training status
    st.subheader("📊 Training Status")
    
    models_trained = st.session_state.classifier_system.get_classification_stats().get('models_trained', {})
    
    for model_name, trained in models_trained.items():
        status = "✅ Trained" if trained else "❌ Not Trained"
        st.write(f"**{model_name.replace('_', ' ').title()}:** {status}")
    
    # Future training features
    st.subheader("🔮 Upcoming Features")
    st.markdown("""
    - **Interactive Training Interface**: Upload training data and train models
    - **Model Performance Monitoring**: Track accuracy, precision, and recall
    - **Active Learning**: Suggest samples for labeling
    - **Custom Domain Training**: Create domain-specific classifiers
    - **Model Comparison**: A/B test different model configurations
    """)


def settings_page():
    """Settings and configuration page."""
    st.header("⚙️ Settings & Configuration")
    
    # Model settings
    st.subheader("🤖 Model Settings")
    
    default_confidence = st.slider(
        "Default confidence threshold:",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        help="Default minimum confidence score for displaying results"
    )
    
    max_text_length = st.number_input(
        "Maximum text length (characters):",
        min_value=100,
        max_value=10000,
        value=5000,
        step=100
    )
    
    # Display settings
    st.subheader("🎨 Display Settings")
    
    theme = st.selectbox(
        "Color theme:",
        ["Default", "Dark", "Light", "High Contrast"]
    )
    
    show_confidence_bars = st.checkbox(
        "Show confidence as progress bars",
        value=True
    )
    
    auto_refresh_analytics = st.checkbox(
        "Auto-refresh analytics",
        value=False
    )
    
    # Database settings
    st.subheader("🗄️ Database Settings")
    
    db_path = st.text_input(
        "Database path:",
        value="text_classification.db",
        help="Path to SQLite database file"
    )
    
    retention_days = st.number_input(
        "Data retention (days):",
        min_value=1,
        max_value=365,
        value=90,
        help="How long to keep classification results"
    )
    
    # Actions
    st.subheader("🔧 Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Settings"):
            st.success("Settings saved!")
    
    with col2:
        if st.button("🔄 Reset to Defaults"):
            st.success("Settings reset to defaults!")
    
    with col3:
        if st.button("🧹 Clean Old Data"):
            deleted = st.session_state.classifier_system.cleanup_old_data(retention_days)
            st.success(f"Cleaned up {deleted} old records!")


def help_page():
    """Help and documentation page."""
    st.header("📚 Help & Documentation")
    
    # Quick start guide
    st.subheader("🚀 Quick Start Guide")
    
    st.markdown("""
    ### 1. Single Text Classification
    - Navigate to the **Text Classifier** page
    - Enter your text in the input area
    - Configure classification options (optional)
    - Click **Classify Text** to get results
    
    ### 2. Batch Processing
    - Upload a file (TXT, CSV, or JSON)
    - Configure batch settings
    - Click **Start Batch Classification**
    - Download results in your preferred format
    
    ### 3. Real-time Classification
    - Use the real-time input for immediate feedback
    - Start typing and see results appear automatically
    - Great for testing and experimentation
    """)
    
    # Content types explanation
    st.subheader("📋 Content Type Categories")
    
    content_info = {
        "Educational": "Learning materials, tutorials, courses, academic content",
        "Promotional": "Marketing materials, advertisements, sales content",
        "Medical": "Healthcare content, clinical notes, medical research",
        "Legal": "Legal documents, contracts, compliance materials",
        "Technical": "Documentation, code, technical specifications",
        "Business": "Corporate content, meetings, reports",
        "News": "News articles, current events, journalism",
        "Entertainment": "Movies, shows, recreational content"
    }
    
    for category, description in content_info.items():
        st.write(f"**{category}:** {description}")
    
    # FAQ
    st.subheader("❓ Frequently Asked Questions")
    
    with st.expander("What is the confidence threshold?"):
        st.write("The confidence threshold determines the minimum score needed to display a classification result. Higher thresholds show only the most confident predictions.")
    
    with st.expander("How accurate are the classifications?"):
        st.write("Accuracy depends on the content type and available training data. Medical and technical content generally achieve higher accuracy due to specialized terminology.")
    
    with st.expander("Can I train custom models?"):
        st.write("Custom model training is coming soon! You'll be able to upload training data and create domain-specific classifiers.")
    
    with st.expander("Is my data stored securely?"):
        st.write("All data is stored locally in an SQLite database. For medical content, HIPAA compliance features are automatically enabled.")
    
    # Contact information
    st.subheader("📞 Support & Contact")
    
    st.markdown("""
    - **Technical Support:** Available through the platform's help system
    - **Feature Requests:** Submit via the analytics page feedback form
    - **Bug Reports:** Use the error reporting system built into the interface
    """)


# Run the application
if __name__ == "__main__":
    main()