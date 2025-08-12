"""
Streamlit UI for Advanced Features
Comprehensive interface for all newly implemented systems
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import io
import json
from PIL import Image
import requests

# Import systems
from batch_transcription_system import BatchTranscriptionSystem, Priority
from punctuation_restoration import PunctuationRestorer
from advanced_timestamping_system import AdvancedTimestampingSystem
from keyword_extraction_system import AdvancedKeywordExtractor
from event_extraction_system import EventExtractor
from visual_content_analysis import VisualContentAnalyzer
from text_classification_system import TextClassificationSystem

# Page configuration
st.set_page_config(
    page_title="Advanced Features Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'batch_system' not in st.session_state:
    st.session_state.batch_system = None
if 'active_batches' not in st.session_state:
    st.session_state.active_batches = []
if 'classification_models' not in st.session_state:
    st.session_state.classification_models = {}


def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🚀 Advanced Features Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    feature = st.sidebar.selectbox(
        "Select Feature",
        [
            "Overview",
            "Batch Processing",
            "Punctuation Restoration",
            "Advanced Timestamping",
            "Keyword Extraction",
            "Event Extraction",
            "Visual Analysis",
            "Text Classification"
        ]
    )
    
    # Route to appropriate feature
    if feature == "Overview":
        show_overview()
    elif feature == "Batch Processing":
        show_batch_processing()
    elif feature == "Punctuation Restoration":
        show_punctuation_restoration()
    elif feature == "Advanced Timestamping":
        show_timestamping()
    elif feature == "Keyword Extraction":
        show_keyword_extraction()
    elif feature == "Event Extraction":
        show_event_extraction()
    elif feature == "Visual Analysis":
        show_visual_analysis()
    elif feature == "Text Classification":
        show_text_classification()


def show_overview():
    """Show overview dashboard"""
    st.header("System Overview")
    
    # Feature status grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📦 Batch Processing</h3>
            <p>Active Batches: 0</p>
            <p>Status: ✅ Ready</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>✏️ Punctuation</h3>
            <p>Models Loaded: 3</p>
            <p>Status: ✅ Ready</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>⏱️ Timestamping</h3>
            <p>Precision: Word-level</p>
            <p>Status: ✅ Ready</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>🔍 Keywords</h3>
            <p>Methods: 6</p>
            <p>Status: ✅ Ready</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity
    st.subheader("Recent Activity")
    
    activity_data = pd.DataFrame({
        'Time': pd.date_range(start='2024-01-01 09:00', periods=10, freq='1H'),
        'Feature': ['Batch Processing', 'Text Classification', 'Visual Analysis'] * 3 + ['Event Extraction'],
        'Action': ['Created batch', 'Trained model', 'Analyzed image'] * 3 + ['Extracted events'],
        'Status': ['Completed'] * 10
    })
    
    st.dataframe(activity_data, use_container_width=True)
    
    # Performance metrics
    st.subheader("Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Processing speed chart
        fig = go.Figure(data=[
            go.Bar(name='Avg Time (s)', x=['Batch', 'Punctuation', 'Keywords', 'Events'], 
                   y=[45, 2.3, 1.5, 3.2])
        ])
        fig.update_layout(title="Average Processing Time", height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Accuracy chart
        fig = go.Figure(data=[
            go.Bar(name='Accuracy (%)', x=['Classification', 'Event Detection', 'OCR', 'Face Detection'],
                   y=[92, 87, 95, 98])
        ])
        fig.update_layout(title="Model Accuracy", height=300)
        st.plotly_chart(fig, use_container_width=True)


def show_batch_processing():
    """Batch processing interface"""
    st.header("📦 Batch Transcription Processing")
    
    tabs = st.tabs(["Create Batch", "Monitor Batches", "Statistics"])
    
    with tabs[0]:
        st.subheader("Create New Batch")
        
        col1, col2 = st.columns(2)
        
        with col1:
            batch_name = st.text_input("Batch Name", placeholder="Q4 Earnings Calls")
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            
            # File upload
            uploaded_files = st.file_uploader(
                "Upload Audio/Video Files",
                type=['mp3', 'wav', 'mp4', 'avi', 'mov'],
                accept_multiple_files=True
            )
        
        with col2:
            webhook_url = st.text_input("Webhook URL (Optional)", placeholder="https://your-webhook.com")
            
            st.write("**Configuration**")
            language = st.selectbox("Language", ["Auto-detect", "English", "Spanish", "French", "German"])
            enable_diarization = st.checkbox("Enable Speaker Diarization")
            enable_translation = st.checkbox("Enable Translation")
        
        if st.button("Create Batch", type="primary"):
            if batch_name and uploaded_files:
                with st.spinner("Creating batch..."):
                    # Simulate batch creation
                    st.success(f"✅ Batch '{batch_name}' created with {len(uploaded_files)} files")
                    st.info(f"Batch ID: batch_12345")
            else:
                st.error("Please provide batch name and upload files")
    
    with tabs[1]:
        st.subheader("Active Batches")
        
        # Sample batch data
        batch_data = pd.DataFrame({
            'Batch ID': ['batch_001', 'batch_002', 'batch_003'],
            'Name': ['Q4 Earnings', 'Customer Interviews', 'Training Videos'],
            'Status': ['Processing', 'Queued', 'Completed'],
            'Progress': [65, 0, 100],
            'Priority': ['High', 'Medium', 'Low'],
            'Files': [10, 25, 5]
        })
        
        # Display batches with progress bars
        for _, batch in batch_data.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                st.write(f"**{batch['Name']}**")
                st.progress(batch['Progress'] / 100)
            
            with col2:
                status_color = {
                    'Processing': '🔄',
                    'Queued': '⏳',
                    'Completed': '✅'
                }
                st.write(f"{status_color.get(batch['Status'], '')} {batch['Status']}")
            
            with col3:
                st.write(f"Priority: {batch['Priority']}")
            
            with col4:
                if batch['Status'] == 'Processing':
                    if st.button("Pause", key=f"pause_{batch['Batch ID']}"):
                        st.info(f"Paused {batch['Name']}")
                elif batch['Status'] == 'Completed':
                    if st.button("Download", key=f"download_{batch['Batch ID']}"):
                        st.info("Downloading results...")
    
    with tabs[2]:
        st.subheader("Batch Statistics")
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Batches", "156", "+12 this week")
        with col2:
            st.metric("Files Processed", "3,842", "+234 today")
        with col3:
            st.metric("Avg Processing Time", "4.2 min", "-0.5 min")
        with col4:
            st.metric("Success Rate", "98.5%", "+0.3%")
        
        # Processing timeline
        timeline_data = pd.DataFrame({
            'Date': pd.date_range(start='2024-01-01', periods=30),
            'Batches': [5 + i % 3 for i in range(30)],
            'Files': [50 + i * 2 % 20 for i in range(30)]
        })
        
        fig = px.line(timeline_data, x='Date', y=['Batches', 'Files'],
                      title="Processing Activity (Last 30 Days)")
        st.plotly_chart(fig, use_container_width=True)


def show_punctuation_restoration():
    """Punctuation restoration interface"""
    st.header("✏️ Punctuation Restoration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        text_input = st.text_area(
            "Enter text without punctuation",
            value="hello my name is john i work at a tech company in san francisco we are building amazing products that help people communicate better what do you think about artificial intelligence",
            height=150
        )
        
        col1_1, col1_2 = st.columns(2)
        with col1_1:
            model = st.selectbox("Model", ["T5", "BERT", "RoBERTa", "Pegasus"])
        with col1_2:
            mode = st.selectbox("Mode", ["Comprehensive", "Fast", "Balanced"])
    
    with col2:
        st.write("**Settings**")
        confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.7)
        preserve_formatting = st.checkbox("Preserve Formatting", value=True)
        fix_grammar = st.checkbox("Fix Grammar", value=True)
        restore_case = st.checkbox("Restore Case", value=True)
    
    if st.button("Restore Punctuation", type="primary"):
        with st.spinner("Processing..."):
            # Simulate restoration
            restored_text = "Hello, my name is John. I work at a tech company in San Francisco. We are building amazing products that help people communicate better. What do you think about artificial intelligence?"
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Original Text")
                st.write(text_input)
            
            with col2:
                st.subheader("Restored Text")
                st.success(restored_text)
            
            # Show corrections
            st.subheader("Corrections Made")
            corrections_df = pd.DataFrame({
                'Position': [0, 5, 22, 61, 111],
                'Correction': ['Capital H', 'Comma after name', 'Period', 'Period', 'Question mark'],
                'Confidence': [0.95, 0.88, 0.92, 0.90, 0.94]
            })
            st.dataframe(corrections_df, use_container_width=True)


def show_timestamping():
    """Advanced timestamping interface"""
    st.header("⏱️ Advanced Timestamping")
    
    uploaded_file = st.file_uploader("Upload Audio/Video File", type=['mp3', 'wav', 'mp4'])
    
    if uploaded_file:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.audio(uploaded_file)
            
            granularity = st.select_slider(
                "Timestamp Granularity",
                options=["Sentence", "Word", "Phoneme", "Character"],
                value="Word"
            )
        
        with col2:
            st.write("**Export Options**")
            export_format = st.selectbox("Format", ["JSON", "SRT", "VTT", "ASS"])
            include_confidence = st.checkbox("Include Confidence Scores", value=True)
            enable_search = st.checkbox("Enable Search", value=True)
            create_chapters = st.checkbox("Auto-detect Chapters", value=False)
        
        if st.button("Generate Timestamps", type="primary"):
            with st.spinner("Generating timestamps..."):
                # Simulate timestamp generation
                st.success("Timestamps generated successfully!")
                
                # Display sample timestamps
                st.subheader("Timestamp Preview")
                
                timestamp_data = pd.DataFrame({
                    'Start': ['00:00:00.000', '00:00:00.250', '00:00:00.500', '00:00:00.750'],
                    'End': ['00:00:00.250', '00:00:00.500', '00:00:00.750', '00:00:01.000'],
                    'Text': ['Hello', 'world', 'this', 'is'],
                    'Confidence': [0.98, 0.95, 0.97, 0.96]
                })
                
                st.dataframe(timestamp_data, use_container_width=True)
                
                # Search functionality
                if enable_search:
                    search_term = st.text_input("Search in transcript", placeholder="Enter word to find...")
                    if search_term:
                        st.info(f"Found '{search_term}' at 00:00:12.450")


def show_keyword_extraction():
    """Keyword extraction interface"""
    st.header("🔍 Keyword Extraction")
    
    text_input = st.text_area(
        "Enter text for keyword extraction",
        value="""Artificial intelligence and machine learning are revolutionizing the technology industry. 
        Companies are investing billions in AI research and development. Natural language processing 
        enables computers to understand human language. Deep learning neural networks can recognize 
        patterns in complex data. The future of AI looks promising with applications in healthcare, 
        finance, and autonomous vehicles.""",
        height=150
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        methods = st.multiselect(
            "Extraction Methods",
            ["RAKE", "TF-IDF", "TextRank", "LDA", "YAKE", "KeyBERT"],
            default=["RAKE", "TF-IDF", "TextRank"]
        )
    
    with col2:
        max_keywords = st.number_input("Max Keywords", min_value=5, max_value=50, value=20)
        include_phrases = st.checkbox("Include Key Phrases", value=True)
    
    with col3:
        visualization = st.selectbox("Visualization", ["Word Cloud", "Network Graph", "Bar Chart"])
        extract_topics = st.checkbox("Extract Topics", value=True)
    
    if st.button("Extract Keywords", type="primary"):
        with st.spinner("Extracting keywords..."):
            # Simulate keyword extraction
            keywords = [
                ("artificial intelligence", 0.95),
                ("machine learning", 0.92),
                ("deep learning", 0.88),
                ("neural networks", 0.85),
                ("natural language processing", 0.83),
                ("technology", 0.80),
                ("AI research", 0.78),
                ("autonomous vehicles", 0.75),
                ("healthcare", 0.72),
                ("finance", 0.70)
            ]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Top Keywords")
                keywords_df = pd.DataFrame(keywords, columns=['Keyword', 'Score'])
                st.dataframe(keywords_df, use_container_width=True)
            
            with col2:
                st.subheader("Visualization")
                if visualization == "Bar Chart":
                    fig = px.bar(keywords_df, x='Score', y='Keyword', orientation='h',
                                title="Keyword Importance Scores")
                    st.plotly_chart(fig, use_container_width=True)
            
            if extract_topics:
                st.subheader("Discovered Topics")
                topics = {
                    "Topic 1": ["AI", "intelligence", "learning", "neural"],
                    "Topic 2": ["technology", "research", "development", "companies"],
                    "Topic 3": ["healthcare", "finance", "vehicles", "applications"]
                }
                
                for topic, words in topics.items():
                    st.write(f"**{topic}**: {', '.join(words)}")


def show_event_extraction():
    """Event extraction interface"""
    st.header("📅 Event Extraction")
    
    text_input = st.text_area(
        "Enter text with events and dates",
        value="""The quarterly review meeting is scheduled for next Monday at 2 PM in the conference room.
        John will present the Q3 results. The deadline for the financial report is October 15th.
        We agreed to launch the new product on November 1st. Sarah needs to complete the market analysis by Friday.
        The team must submit their timesheets by tomorrow 5 PM.""",
        height=150
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        extract_actions = st.checkbox("Extract Action Items", value=True)
        build_timeline = st.checkbox("Build Timeline", value=True)
        reference_date = st.date_input("Reference Date", value=datetime.now())
    
    with col2:
        export_format = st.selectbox("Export Format", ["None", "ICS (Calendar)", "JSON"])
        detect_deadlines = st.checkbox("Detect Deadlines", value=True)
        extract_participants = st.checkbox("Extract Participants", value=True)
    
    if st.button("Extract Events", type="primary"):
        with st.spinner("Extracting events..."):
            # Display extracted events
            st.subheader("Extracted Events")
            
            events_data = pd.DataFrame({
                'Event': ['Quarterly Review Meeting', 'Financial Report Deadline', 'Product Launch'],
                'Type': ['Meeting', 'Deadline', 'Milestone'],
                'Date': ['Next Monday 2 PM', 'October 15th', 'November 1st'],
                'Participants': ['John', '-', 'Team'],
                'Location': ['Conference Room', '-', '-']
            })
            
            st.dataframe(events_data, use_container_width=True)
            
            if extract_actions:
                st.subheader("Action Items")
                
                actions_data = pd.DataFrame({
                    'Action': ['Present Q3 results', 'Complete market analysis', 'Submit timesheets'],
                    'Assignee': ['John', 'Sarah', 'Team'],
                    'Deadline': ['-', 'Friday', 'Tomorrow 5 PM'],
                    'Priority': ['High', 'High', 'Medium']
                })
                
                st.dataframe(actions_data, use_container_width=True)
            
            if build_timeline:
                st.subheader("Event Timeline")
                
                # Create timeline visualization
                timeline_fig = go.Figure()
                
                dates = pd.date_range(start='2024-10-01', periods=60)
                events = [
                    ('2024-10-07', 'Review Meeting'),
                    ('2024-10-15', 'Report Deadline'),
                    ('2024-11-01', 'Product Launch')
                ]
                
                for date, event in events:
                    timeline_fig.add_trace(go.Scatter(
                        x=[pd.to_datetime(date)],
                        y=[1],
                        mode='markers+text',
                        marker=dict(size=15),
                        text=[event],
                        textposition='top center'
                    ))
                
                timeline_fig.update_layout(
                    title="Event Timeline",
                    xaxis_title="Date",
                    yaxis=dict(visible=False),
                    height=300,
                    showlegend=False
                )
                
                st.plotly_chart(timeline_fig, use_container_width=True)


def show_visual_analysis():
    """Visual content analysis interface"""
    st.header("🖼️ Visual Content Analysis")
    
    uploaded_file = st.file_uploader("Upload Image or Video", type=['jpg', 'jpeg', 'png', 'mp4', 'avi'])
    
    if uploaded_file:
        if uploaded_file.type.startswith('image'):
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Analysis Options**")
            detect_objects = st.checkbox("Detect Objects", value=True)
            detect_faces = st.checkbox("Detect Faces", value=True)
            extract_text = st.checkbox("Extract Text (OCR)", value=True)
            scene_description = st.checkbox("Generate Scene Description", value=True)
        
        with col2:
            st.write("**Privacy Settings**")
            privacy_mode = st.selectbox("Privacy Mode", ["None", "Blur Faces", "Pixelate Faces", "Remove Faces"])
            safety_check = st.checkbox("Safety Content Check", value=True)
            
        if st.button("Analyze Visual Content", type="primary"):
            with st.spinner("Analyzing..."):
                # Display analysis results
                st.success("Analysis complete!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if detect_objects:
                        st.subheader("Detected Objects")
                        objects_data = pd.DataFrame({
                            'Object': ['Person', 'Car', 'Building', 'Tree', 'Sky'],
                            'Confidence': [0.98, 0.95, 0.92, 0.88, 0.90],
                            'Count': [2, 1, 3, 5, 1]
                        })
                        st.dataframe(objects_data, use_container_width=True)
                
                with col2:
                    if detect_faces:
                        st.subheader("Face Detection")
                        st.metric("Faces Detected", 2)
                        if privacy_mode != "None":
                            st.info(f"Privacy mode applied: {privacy_mode}")
                
                if scene_description:
                    st.subheader("Scene Description")
                    st.write("A sunny outdoor scene with two people standing near a red car in front of modern office buildings. Trees line the street and the sky is clear blue.")
                
                if extract_text:
                    st.subheader("Extracted Text (OCR)")
                    st.code("STOP\nNo Parking\n8AM - 6PM\nMonday - Friday")
                
                if safety_check:
                    st.subheader("Safety Scores")
                    safety_scores = {
                        'Safe': 0.98,
                        'Violence': 0.01,
                        'Adult': 0.005,
                        'Offensive': 0.005
                    }
                    
                    fig = go.Figure(data=[
                        go.Bar(x=list(safety_scores.keys()), y=list(safety_scores.values()))
                    ])
                    fig.update_layout(title="Content Safety Analysis", height=300)
                    st.plotly_chart(fig, use_container_width=True)


def show_text_classification():
    """Text classification interface"""
    st.header("🏷️ Text Classification")
    
    tabs = st.tabs(["Classify Text", "Train Model", "Active Learning", "Model Management"])
    
    with tabs[0]:
        st.subheader("Classify Text")
        
        text_input = st.text_area(
            "Enter text to classify",
            value="The stock market experienced significant volatility today as tech companies reported mixed earnings results.",
            height=100
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            classification_type = st.selectbox(
                "Classification Type",
                ["Zero-shot", "Pre-trained Model", "Custom Model"]
            )
            
            if classification_type == "Zero-shot":
                candidate_labels = st.text_input(
                    "Candidate Labels (comma-separated)",
                    value="business, technology, sports, politics, entertainment"
                )
            else:
                model_key = st.selectbox("Select Model", ["model_001", "model_002", "custom_model"])
        
        with col2:
            threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.5)
            show_all_scores = st.checkbox("Show All Scores", value=True)
        
        if st.button("Classify", type="primary"):
            with st.spinner("Classifying..."):
                # Display classification results
                st.subheader("Classification Results")
                
                if classification_type == "Zero-shot":
                    results = [
                        ("business", 0.82),
                        ("technology", 0.65),
                        ("politics", 0.23),
                        ("sports", 0.15),
                        ("entertainment", 0.08)
                    ]
                else:
                    results = [
                        ("Financial", 0.91),
                        ("Technology", 0.72),
                        ("News", 0.68)
                    ]
                
                # Display as bar chart
                results_df = pd.DataFrame(results, columns=['Label', 'Confidence'])
                fig = px.bar(results_df, x='Confidence', y='Label', orientation='h',
                            title="Classification Confidence Scores")
                st.plotly_chart(fig, use_container_width=True)
                
                # Show predicted label
                st.success(f"**Predicted Label:** {results[0][0]} (Confidence: {results[0][1]:.2%})")
    
    with tabs[1]:
        st.subheader("Train New Model")
        
        col1, col2 = st.columns(2)
        
        with col1:
            training_data = st.file_uploader("Upload Training Data (CSV)", type=['csv'])
            classification_type = st.selectbox(
                "Classification Type",
                ["Binary", "Multiclass", "Multi-label", "Hierarchical"]
            )
            model_type = st.selectbox(
                "Model Type",
                ["Logistic Regression", "Random Forest", "SVM", "BERT", "DistilBERT"]
            )
        
        with col2:
            test_size = st.slider("Test Size", 0.1, 0.4, 0.2)
            cross_validate = st.checkbox("Cross Validation", value=True)
            save_model = st.checkbox("Save Model", value=True)
            
        if st.button("Train Model", type="primary"):
            with st.spinner("Training model..."):
                # Simulate training
                progress = st.progress(0)
                for i in range(100):
                    progress.progress(i + 1)
                
                st.success("Model trained successfully!")
                
                # Display performance metrics
                st.subheader("Model Performance")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Accuracy", "92.3%")
                with col2:
                    st.metric("Precision", "91.5%")
                with col3:
                    st.metric("Recall", "90.8%")
                with col4:
                    st.metric("F1 Score", "91.1%")
                
                # Confusion matrix
                st.subheader("Confusion Matrix")
                confusion_matrix = [[45, 3, 2], [4, 38, 3], [2, 2, 41]]
                fig = px.imshow(confusion_matrix, text_auto=True,
                              labels=dict(x="Predicted", y="Actual"),
                              x=['Class A', 'Class B', 'Class C'],
                              y=['Class A', 'Class B', 'Class C'])
                st.plotly_chart(fig, use_container_width=True)
    
    with tabs[2]:
        st.subheader("Active Learning")
        
        st.write("Select uncertain samples for manual labeling to improve model performance.")
        
        # Display uncertain samples
        samples_data = pd.DataFrame({
            'Text': [
                'The new policy affects both consumers and businesses...',
                'Scientists made a breakthrough in quantum computing...',
                'The team secured funding for expansion...'
            ],
            'Predicted Label': ['Politics', 'Technology', 'Business'],
            'Uncertainty': [0.62, 0.58, 0.55],
            'Action': ['Label', 'Label', 'Label']
        })
        
        st.dataframe(samples_data, use_container_width=True)
        
        # Labeling interface
        st.write("**Label Sample:**")
        selected_sample = st.selectbox("Select Sample", samples_data['Text'].tolist())
        new_label = st.selectbox("Assign Label", ["Business", "Technology", "Politics", "Science", "Other"])
        
        if st.button("Submit Label"):
            st.success("Label submitted! Model will be updated.")
    
    with tabs[3]:
        st.subheader("Model Management")
        
        # List of models
        models_data = pd.DataFrame({
            'Model ID': ['model_001', 'model_002', 'model_003'],
            'Type': ['Multiclass', 'Binary', 'Multi-label'],
            'Algorithm': ['Random Forest', 'BERT', 'Logistic Regression'],
            'Accuracy': [0.923, 0.956, 0.887],
            'Created': ['2024-01-01', '2024-01-05', '2024-01-10']
        })
        
        st.dataframe(models_data, use_container_width=True)
        
        # Model actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export Model"):
                st.info("Model exported to model_export.pkl")
        
        with col2:
            if st.button("Delete Model"):
                st.warning("Are you sure? This action cannot be undone.")
        
        with col3:
            if st.button("View Details"):
                st.info("Loading model details...")


if __name__ == "__main__":
    main()