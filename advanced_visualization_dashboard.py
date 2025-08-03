#!/usr/bin/env python3
"""
Advanced Visualization and Analytics Dashboard (Task 43)
Interactive dashboard with word clouds, sentiment analysis, speaker networks, and comparative analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import json
import re
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
import seaborn as sns

# Import required libraries for text analysis
try:
    import spacy
    from textblob import TextBlob
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.cluster import KMeans
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
except ImportError as e:
    st.error(f"Required libraries not installed: {e}")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TranscriptData:
    """Data structure for transcript information"""
    id: str
    title: str
    content: str
    timestamp: datetime
    speakers: List[str]
    duration: float
    metadata: Dict[str, Any]

@dataclass
class SentimentPoint:
    """Data structure for sentiment analysis points"""
    timestamp: float
    sentiment: float
    confidence: float
    text: str
    speaker: Optional[str] = None

@dataclass
class TopicData:
    """Data structure for topic modeling results"""
    topic_id: int
    keywords: List[str]
    weight: float
    documents: List[str]

class AdvancedVisualizationDashboard:
    """Advanced visualization and analytics dashboard"""
    
    def __init__(self):
        self.setup_nltk()
        self.setup_spacy()
        
        # Initialize session state
        if 'transcript_data' not in st.session_state:
            st.session_state.transcript_data = self.load_sample_data()
        if 'selected_transcripts' not in st.session_state:
            st.session_state.selected_transcripts = []
        if 'analysis_cache' not in st.session_state:
            st.session_state.analysis_cache = {}
    
    def setup_nltk(self):
        """Setup NLTK dependencies"""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            with st.spinner("Downloading NLTK data..."):
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
    
    def setup_spacy(self):
        """Setup spaCy model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            st.error("spaCy English model not found. Please install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def load_sample_data(self) -> List[TranscriptData]:
        """Load sample transcript data for demonstration"""
        sample_transcripts = [
            TranscriptData(
                id="transcript_1",
                title="Team Meeting - Q1 Planning",
                content="""
                John: Good morning everyone. Let's start with our Q1 planning session. I'm excited about the new initiatives we're launching.
                Sarah: Thanks John. I've been working on the marketing strategy and I think we have some great opportunities ahead.
                Mike: The technical implementation looks challenging but achievable. We'll need to allocate more resources to the backend development.
                Sarah: I agree with Mike. The user experience is crucial for our success. We should focus on making it intuitive and engaging.
                John: Excellent points. Let's also consider the budget implications. We need to be strategic about our investments.
                Mike: The performance metrics from last quarter show we're on the right track. Customer satisfaction is up 15%.
                Sarah: That's fantastic news! The feedback we've received has been overwhelmingly positive.
                John: Let's make sure we maintain this momentum. What are the key challenges we need to address?
                Mike: Scalability is our biggest concern. We need to ensure our infrastructure can handle the growth.
                Sarah: From a marketing perspective, we need to expand our reach while maintaining quality.
                """,
                timestamp=datetime.now() - timedelta(days=7),
                speakers=["John", "Sarah", "Mike"],
                duration=1800.0,  # 30 minutes
                metadata={"meeting_type": "planning", "department": "product", "priority": "high"}
            ),
            TranscriptData(
                id="transcript_2",
                title="Customer Interview - Product Feedback",
                content="""
                Interviewer: Thank you for taking the time to speak with us today. How has your experience been with our product?
                Customer: Overall, I'm quite satisfied. The interface is clean and easy to navigate. However, there are some areas for improvement.
                Interviewer: That's great to hear! Could you tell us more about the areas that need improvement?
                Customer: The loading times can be frustrating, especially during peak hours. Sometimes it takes too long to process requests.
                Interviewer: I understand. Performance is definitely something we're working on. What features do you find most valuable?
                Customer: The analytics dashboard is incredibly useful. It gives me insights I never had before. The reporting features are also excellent.
                Interviewer: Wonderful! Are there any features you'd like to see added?
                Customer: I'd love to see better integration with third-party tools. Also, mobile support could be enhanced.
                Interviewer: Those are excellent suggestions. How likely are you to recommend our product to others?
                Customer: I'd definitely recommend it. Despite the minor issues, it's been a game-changer for our business.
                """,
                timestamp=datetime.now() - timedelta(days=3),
                speakers=["Interviewer", "Customer"],
                duration=900.0,  # 15 minutes
                metadata={"meeting_type": "interview", "department": "research", "priority": "medium"}
            ),
            TranscriptData(
                id="transcript_3",
                title="Technical Review - System Architecture",
                content="""
                Lead: Let's review the current system architecture and identify potential improvements.
                Developer1: The microservices approach has been working well, but we're seeing some latency issues between services.
                Developer2: I've noticed that too. The database queries are becoming a bottleneck, especially for complex reports.
                Lead: What solutions are you considering?
                Developer1: We could implement caching at multiple levels. Redis for session data and application-level caching for frequently accessed data.
                Developer2: That sounds good. We should also consider database optimization. Some of our queries could be more efficient.
                Lead: Excellent. What about scalability concerns?
                Developer1: Horizontal scaling is working, but we need better load balancing. The current setup isn't distributing traffic optimally.
                Developer2: Auto-scaling policies need refinement too. We're sometimes over-provisioning resources.
                Lead: These are all valid points. Let's prioritize these improvements and create a roadmap.
                Developer1: Security should also be a priority. We need to implement better authentication and authorization mechanisms.
                Developer2: Agreed. The current system has some vulnerabilities that need addressing.
                """,
                timestamp=datetime.now() - timedelta(days=1),
                speakers=["Lead", "Developer1", "Developer2"],
                duration=2400.0,  # 40 minutes
                metadata={"meeting_type": "technical", "department": "engineering", "priority": "high"}
            )
        ]
        return sample_transcripts
    
    def render_header(self):
        """Render the dashboard header"""
        st.title("📊 Advanced Visualization & Analytics Dashboard")
        st.markdown("Interactive analytics with word clouds, sentiment analysis, speaker networks, and comparative insights")
        
        # Transcript selection
        st.subheader("📋 Select Transcripts for Analysis")
        
        transcript_options = {t.title: t.id for t in st.session_state.transcript_data}
        selected_titles = st.multiselect(
            "Choose transcripts to analyze:",
            options=list(transcript_options.keys()),
            default=list(transcript_options.keys())[:2],
            help="Select one or more transcripts for comparative analysis"
        )
        
        st.session_state.selected_transcripts = [transcript_options[title] for title in selected_titles]
        
        if not st.session_state.selected_transcripts:
            st.warning("Please select at least one transcript to begin analysis.")
            return False
        
        return True
    
    def get_selected_transcripts(self) -> List[TranscriptData]:
        """Get the currently selected transcripts"""
        return [t for t in st.session_state.transcript_data if t.id in st.session_state.selected_transcripts]
    
    def render_word_cloud_analysis(self):
        """Render interactive word cloud analysis"""
        st.header("☁️ Interactive Word Cloud Analysis")
        
        selected_transcripts = self.get_selected_transcripts()
        
        if not selected_transcripts:
            st.info("No transcripts selected for word cloud analysis.")
            return
        
        # Word cloud options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_words = st.slider("Maximum Words", 50, 500, 200)
        
        with col2:
            min_word_length = st.slider("Minimum Word Length", 2, 8, 3)
        
        with col3:
            colormap = st.selectbox("Color Scheme", 
                                  ["viridis", "plasma", "inferno", "magma", "Blues", "Reds", "Greens"])
        
        # Generate word clouds for each transcript
        for transcript in selected_transcripts:
            st.subheader(f"Word Cloud: {transcript.title}")
            
            # Process text
            processed_text = self.preprocess_text_for_wordcloud(transcript.content, min_word_length)
            
            if processed_text:
                # Generate word cloud
                wordcloud = WordCloud(
                    width=800, 
                    height=400, 
                    max_words=max_words,
                    colormap=colormap,
                    background_color='white',
                    relative_scaling=0.5,
                    random_state=42
                ).generate(processed_text)
                
                # Display word cloud
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
                plt.close()
                
                # Word frequency analysis
                with st.expander(f"Word Frequency Analysis - {transcript.title}"):
                    word_freq = self.get_word_frequencies(processed_text)
                    
                    # Create frequency chart
                    top_words = dict(list(word_freq.items())[:20])
                    
                    fig = px.bar(
                        x=list(top_words.values()),
                        y=list(top_words.keys()),
                        orientation='h',
                        title=f"Top 20 Words - {transcript.title}",
                        labels={'x': 'Frequency', 'y': 'Words'}
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Clickable word analysis
                    selected_word = st.selectbox(
                        f"Analyze word usage in {transcript.title}:",
                        options=list(top_words.keys()),
                        key=f"word_select_{transcript.id}"
                    )
                    
                    if selected_word:
                        contexts = self.find_word_contexts(transcript.content, selected_word)
                        st.write(f"**'{selected_word}' appears {len(contexts)} times:**")
                        for i, context in enumerate(contexts[:5], 1):
                            st.write(f"{i}. ...{context}...")
            else:
                st.warning(f"No suitable words found for word cloud in {transcript.title}")
    
    def preprocess_text_for_wordcloud(self, text: str, min_length: int = 3) -> str:
        """Preprocess text for word cloud generation"""
        # Remove speaker labels and clean text
        text = re.sub(r'^[A-Za-z]+:', '', text, flags=re.MULTILINE)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = text.lower()
        
        # Tokenize and filter
        words = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        
        # Additional stop words for meeting transcripts
        meeting_stop_words = {'said', 'say', 'says', 'think', 'know', 'like', 'really', 'well', 'good', 'great', 'okay', 'yes', 'no'}
        stop_words.update(meeting_stop_words)
        
        filtered_words = [
            word for word in words 
            if len(word) >= min_length 
            and word not in stop_words 
            and word.isalpha()
        ]
        
        return ' '.join(filtered_words)
    
    def get_word_frequencies(self, text: str) -> Dict[str, int]:
        """Get word frequency counts"""
        words = text.split()
        return dict(Counter(words).most_common(50))
    
    def find_word_contexts(self, text: str, word: str, context_length: int = 50) -> List[str]:
        """Find contexts where a word appears"""
        contexts = []
        text_lower = text.lower()
        word_lower = word.lower()
        
        start = 0
        while True:
            pos = text_lower.find(word_lower, start)
            if pos == -1:
                break
            
            context_start = max(0, pos - context_length)
            context_end = min(len(text), pos + len(word) + context_length)
            context = text[context_start:context_end].strip()
            contexts.append(context)
            start = pos + 1
        
        return contexts
    
    def render_sentiment_flow_analysis(self):
        """Render sentiment flow visualization over time"""
        st.header("📈 Sentiment Flow Analysis")
        
        selected_transcripts = self.get_selected_transcripts()
        
        if not selected_transcripts:
            st.info("No transcripts selected for sentiment analysis.")
            return
        
        # Sentiment analysis options
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_granularity = st.selectbox(
                "Analysis Granularity",
                ["Sentence", "Paragraph", "Speaker Turn"],
                help="Choose how to segment the text for sentiment analysis"
            )
        
        with col2:
            smoothing_window = st.slider("Smoothing Window", 1, 10, 3, 
                                       help="Number of points to average for smoother curves")
        
        # Analyze sentiment for each transcript
        for transcript in selected_transcripts:
            st.subheader(f"Sentiment Timeline: {transcript.title}")
            
            sentiment_data = self.analyze_sentiment_flow(transcript, analysis_granularity)
            
            if sentiment_data:
                # Create sentiment flow chart
                fig = go.Figure()
                
                # Apply smoothing if requested
                if smoothing_window > 1:
                    sentiment_values = self.smooth_data([s.sentiment for s in sentiment_data], smoothing_window)
                    confidence_values = self.smooth_data([s.confidence for s in sentiment_data], smoothing_window)
                else:
                    sentiment_values = [s.sentiment for s in sentiment_data]
                    confidence_values = [s.confidence for s in sentiment_data]
                
                timestamps = [s.timestamp for s in sentiment_data]
                
                # Sentiment line
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=sentiment_values,
                    mode='lines+markers',
                    name='Sentiment',
                    line=dict(color='blue', width=2),
                    hovertemplate='<b>Time:</b> %{x:.1f}s<br><b>Sentiment:</b> %{y:.2f}<extra></extra>'
                ))
                
                # Confidence area
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=confidence_values,
                    mode='lines',
                    name='Confidence',
                    line=dict(color='rgba(255,0,0,0.3)', width=1),
                    yaxis='y2',
                    hovertemplate='<b>Time:</b> %{x:.1f}s<br><b>Confidence:</b> %{y:.2f}<extra></extra>'
                ))
                
                # Add neutral line
                fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Neutral")
                
                # Update layout
                fig.update_layout(
                    title=f"Sentiment Flow - {transcript.title}",
                    xaxis_title="Time (seconds)",
                    yaxis_title="Sentiment Score",
                    yaxis2=dict(
                        title="Confidence",
                        overlaying='y',
                        side='right',
                        range=[0, 1]
                    ),
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Sentiment statistics
                with st.expander(f"Sentiment Statistics - {transcript.title}"):
                    avg_sentiment = np.mean(sentiment_values)
                    sentiment_std = np.std(sentiment_values)
                    avg_confidence = np.mean(confidence_values)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Average Sentiment", f"{avg_sentiment:.3f}")
                    
                    with col2:
                        st.metric("Sentiment Variability", f"{sentiment_std:.3f}")
                    
                    with col3:
                        st.metric("Average Confidence", f"{avg_confidence:.3f}")
                    
                    with col4:
                        positive_ratio = len([s for s in sentiment_values if s > 0.1]) / len(sentiment_values)
                        st.metric("Positive Ratio", f"{positive_ratio:.1%}")
                    
                    # Most positive and negative segments
                    most_positive = max(sentiment_data, key=lambda x: x.sentiment)
                    most_negative = min(sentiment_data, key=lambda x: x.sentiment)
                    
                    st.write("**Most Positive Segment:**")
                    st.write(f"*Score: {most_positive.sentiment:.3f}* - {most_positive.text[:200]}...")
                    
                    st.write("**Most Negative Segment:**")
                    st.write(f"*Score: {most_negative.sentiment:.3f}* - {most_negative.text[:200]}...")
    
    def analyze_sentiment_flow(self, transcript: TranscriptData, granularity: str) -> List[SentimentPoint]:
        """Analyze sentiment flow over time"""
        cache_key = f"sentiment_{transcript.id}_{granularity}"
        
        if cache_key in st.session_state.analysis_cache:
            return st.session_state.analysis_cache[cache_key]
        
        sentiment_points = []
        
        if granularity == "Sentence":
            segments = sent_tokenize(transcript.content)
        elif granularity == "Paragraph":
            segments = transcript.content.split('\n\n')
        else:  # Speaker Turn
            segments = self.split_by_speaker_turns(transcript.content)
        
        total_duration = transcript.duration
        segment_duration = total_duration / len(segments) if segments else 0
        
        for i, segment in enumerate(segments):
            if segment.strip():
                # Clean segment text
                clean_text = re.sub(r'^[A-Za-z]+:', '', segment.strip())
                
                if clean_text:
                    # Analyze sentiment using TextBlob
                    blob = TextBlob(clean_text)
                    sentiment_score = blob.sentiment.polarity
                    confidence = abs(blob.sentiment.subjectivity)
                    
                    timestamp = i * segment_duration
                    
                    sentiment_points.append(SentimentPoint(
                        timestamp=timestamp,
                        sentiment=sentiment_score,
                        confidence=confidence,
                        text=clean_text
                    ))
        
        st.session_state.analysis_cache[cache_key] = sentiment_points
        return sentiment_points
    
    def split_by_speaker_turns(self, text: str) -> List[str]:
        """Split text by speaker turns"""
        lines = text.strip().split('\n')
        turns = []
        current_turn = []
        
        for line in lines:
            line = line.strip()
            if line and ':' in line and re.match(r'^[A-Za-z]+:', line):
                if current_turn:
                    turns.append('\n'.join(current_turn))
                current_turn = [line]
            elif line:
                current_turn.append(line)
        
        if current_turn:
            turns.append('\n'.join(current_turn))
        
        return turns
    
    def smooth_data(self, data: List[float], window: int) -> List[float]:
        """Apply moving average smoothing to data"""
        if window <= 1:
            return data
        
        smoothed = []
        for i in range(len(data)):
            start = max(0, i - window // 2)
            end = min(len(data), i + window // 2 + 1)
            smoothed.append(np.mean(data[start:end]))
        
        return smoothed
    
    def render_speaker_interaction_network(self):
        """Render speaker interaction network graphs"""
        st.header("🕸️ Speaker Interaction Networks")
        
        selected_transcripts = self.get_selected_transcripts()
        
        if not selected_transcripts:
            st.info("No transcripts selected for network analysis.")
            return
        
        # Network analysis options
        col1, col2 = st.columns(2)
        
        with col1:
            interaction_threshold = st.slider("Interaction Threshold", 1, 10, 2,
                                            help="Minimum interactions to show connection")
        
        with col2:
            layout_algorithm = st.selectbox("Layout Algorithm", 
                                          ["spring", "circular", "kamada_kawai", "random"])
        
        # Analyze each transcript
        for transcript in selected_transcripts:
            if len(transcript.speakers) < 2:
                st.info(f"Skipping {transcript.title} - needs at least 2 speakers for network analysis")
                continue
            
            st.subheader(f"Speaker Network: {transcript.title}")
            
            # Build interaction network
            network_data = self.build_speaker_network(transcript)
            
            if network_data:
                # Create network graph
                G = nx.Graph()
                
                # Add nodes (speakers)
                for speaker in transcript.speakers:
                    G.add_node(speaker)
                
                # Add edges (interactions)
                for (speaker1, speaker2), weight in network_data['interactions'].items():
                    if weight >= interaction_threshold:
                        G.add_edge(speaker1, speaker2, weight=weight)
                
                if G.edges():
                    # Generate layout
                    if layout_algorithm == "spring":
                        pos = nx.spring_layout(G, k=1, iterations=50)
                    elif layout_algorithm == "circular":
                        pos = nx.circular_layout(G)
                    elif layout_algorithm == "kamada_kawai":
                        pos = nx.kamada_kawai_layout(G)
                    else:
                        pos = nx.random_layout(G)
                    
                    # Create Plotly network visualization
                    fig = self.create_network_plot(G, pos, network_data)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Network statistics
                    with st.expander(f"Network Statistics - {transcript.title}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Speakers", len(G.nodes()))
                            st.metric("Total Interactions", len(G.edges()))
                        
                        with col2:
                            density = nx.density(G)
                            st.metric("Network Density", f"{density:.3f}")
                            
                            if G.edges():
                                avg_clustering = nx.average_clustering(G)
                                st.metric("Average Clustering", f"{avg_clustering:.3f}")
                        
                        with col3:
                            # Most active speaker
                            speaker_activity = network_data['speaker_stats']
                            most_active = max(speaker_activity.items(), key=lambda x: x[1]['total_words'])
                            st.metric("Most Active Speaker", most_active[0])
                            st.metric("Words Spoken", most_active[1]['total_words'])
                        
                        # Detailed speaker statistics
                        st.write("**Speaker Statistics:**")
                        speaker_df = pd.DataFrame([
                            {
                                'Speaker': speaker,
                                'Total Words': stats['total_words'],
                                'Speaking Turns': stats['turns'],
                                'Avg Words/Turn': stats['total_words'] / max(stats['turns'], 1),
                                'Interactions': len([edge for edge in G.edges() if speaker in edge])
                            }
                            for speaker, stats in speaker_activity.items()
                        ])
                        st.dataframe(speaker_df, use_container_width=True)
                else:
                    st.warning(f"No significant interactions found in {transcript.title} with current threshold")
    
    def build_speaker_network(self, transcript: TranscriptData) -> Dict[str, Any]:
        """Build speaker interaction network data"""
        cache_key = f"network_{transcript.id}"
        
        if cache_key in st.session_state.analysis_cache:
            return st.session_state.analysis_cache[cache_key]
        
        lines = transcript.content.strip().split('\n')
        interactions = defaultdict(int)
        speaker_stats = defaultdict(lambda: {'total_words': 0, 'turns': 0})
        
        previous_speaker = None
        
        for line in lines:
            line = line.strip()
            if ':' in line and re.match(r'^[A-Za-z]+:', line):
                parts = line.split(':', 1)
                current_speaker = parts[0].strip()
                text = parts[1].strip() if len(parts) > 1 else ""
                
                # Update speaker statistics
                word_count = len(text.split())
                speaker_stats[current_speaker]['total_words'] += word_count
                speaker_stats[current_speaker]['turns'] += 1
                
                # Record interaction
                if previous_speaker and previous_speaker != current_speaker:
                    pair = tuple(sorted([previous_speaker, current_speaker]))
                    interactions[pair] += 1
                
                previous_speaker = current_speaker
        
        network_data = {
            'interactions': dict(interactions),
            'speaker_stats': dict(speaker_stats)
        }
        
        st.session_state.analysis_cache[cache_key] = network_data
        return network_data
    
    def create_network_plot(self, G: nx.Graph, pos: Dict, network_data: Dict) -> go.Figure:
        """Create Plotly network visualization"""
        # Extract node and edge information
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        node_text = list(G.nodes())
        
        # Node sizes based on total words spoken
        speaker_stats = network_data['speaker_stats']
        node_sizes = [speaker_stats[node]['total_words'] / 10 for node in G.nodes()]
        
        # Edge traces
        edge_x = []
        edge_y = []
        edge_weights = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_weights.append(G[edge[0]][edge[1]]['weight'])
        
        # Create figure
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='rgba(125,125,125,0.5)'),
            hoverinfo='none',
            mode='lines',
            name='Interactions'
        ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            hovertext=[f"{node}<br>Words: {speaker_stats[node]['total_words']}<br>Turns: {speaker_stats[node]['turns']}" 
                      for node in G.nodes()],
            marker=dict(
                size=node_sizes,
                color='lightblue',
                line=dict(width=2, color='darkblue'),
                sizemode='diameter',
                sizemin=20
            ),
            name='Speakers'
        ))
        
        fig.update_layout(
            title="Speaker Interaction Network",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text="Node size represents total words spoken",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(color='gray', size=12)
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=500
        )
        
        return fig
    
    def render_topic_evolution_timeline(self):
        """Render topic evolution timeline visualization"""
        st.header("📈 Topic Evolution Timeline")
        
        selected_transcripts = self.get_selected_transcripts()
        
        if not selected_transcripts:
            st.info("No transcripts selected for topic analysis.")
            return
        
        # Topic modeling options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            num_topics = st.slider("Number of Topics", 2, 10, 5)
        
        with col2:
            time_segments = st.slider("Time Segments", 5, 20, 10)
        
        with col3:
            min_topic_weight = st.slider("Min Topic Weight", 0.0, 0.5, 0.1)
        
        # Analyze topics for each transcript
        for transcript in selected_transcripts:
            st.subheader(f"Topic Evolution: {transcript.title}")
            
            topic_timeline = self.analyze_topic_evolution(transcript, num_topics, time_segments)
            
            if topic_timeline:
                # Create topic evolution heatmap
                fig = self.create_topic_timeline_plot(topic_timeline, min_topic_weight)
                st.plotly_chart(fig, use_container_width=True)
                
                # Topic details
                with st.expander(f"Topic Details - {transcript.title}"):
                    for topic_id, topic_data in topic_timeline['topics'].items():
                        st.write(f"**Topic {topic_id}:** {', '.join(topic_data['keywords'][:5])}")
                        
                        # Show example segments for this topic
                        strong_segments = [
                            (seg_id, weight) for seg_id, topics in topic_timeline['segments'].items()
                            for topic, weight in topics.items() if topic == topic_id and weight > min_topic_weight
                        ]
                        
                        if strong_segments:
                            best_segment = max(strong_segments, key=lambda x: x[1])
                            segment_text = topic_timeline['segment_texts'][best_segment[0]]
                            st.write(f"*Example (weight: {best_segment[1]:.3f}):* {segment_text[:200]}...")
    
    def analyze_topic_evolution(self, transcript: TranscriptData, num_topics: int, time_segments: int) -> Dict[str, Any]:
        """Analyze topic evolution over time"""
        cache_key = f"topics_{transcript.id}_{num_topics}_{time_segments}"
        
        if cache_key in st.session_state.analysis_cache:
            return st.session_state.analysis_cache[cache_key]
        
        # Split transcript into time segments
        content_lines = [line.strip() for line in transcript.content.split('\n') if line.strip()]
        segment_size = len(content_lines) // time_segments
        
        segments = []
        segment_texts = {}
        
        for i in range(time_segments):
            start_idx = i * segment_size
            end_idx = (i + 1) * segment_size if i < time_segments - 1 else len(content_lines)
            
            segment_lines = content_lines[start_idx:end_idx]
            segment_text = ' '.join(segment_lines)
            
            # Clean text for topic modeling
            clean_text = re.sub(r'^[A-Za-z]+:', '', segment_text, flags=re.MULTILINE)
            clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
            
            segments.append(clean_text)
            segment_texts[i] = segment_text
        
        # Perform topic modeling
        try:
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                min_df=1,
                max_df=0.8,
                ngram_range=(1, 2)
            )
            
            doc_term_matrix = vectorizer.fit_transform(segments)
            
            if doc_term_matrix.shape[0] > 0 and doc_term_matrix.shape[1] > 0:
                lda = LatentDirichletAllocation(
                    n_components=num_topics,
                    random_state=42,
                    max_iter=10
                )
                
                lda.fit(doc_term_matrix)
                
                # Extract topics
                feature_names = vectorizer.get_feature_names_out()
                topics = {}
                
                for topic_idx, topic in enumerate(lda.components_):
                    top_words_idx = topic.argsort()[-10:][::-1]
                    top_words = [feature_names[i] for i in top_words_idx]
                    topics[topic_idx] = {
                        'keywords': top_words,
                        'weights': topic[top_words_idx].tolist()
                    }
                
                # Get topic weights for each segment
                doc_topic_matrix = lda.transform(doc_term_matrix)
                segment_topics = {}
                
                for seg_idx, topic_weights in enumerate(doc_topic_matrix):
                    segment_topics[seg_idx] = {
                        topic_idx: weight for topic_idx, weight in enumerate(topic_weights)
                    }
                
                timeline_data = {
                    'topics': topics,
                    'segments': segment_topics,
                    'segment_texts': segment_texts,
                    'time_segments': time_segments
                }
                
                st.session_state.analysis_cache[cache_key] = timeline_data
                return timeline_data
            
        except Exception as e:
            logger.error(f"Topic modeling error: {e}")
        
        return None
    
    def create_topic_timeline_plot(self, timeline_data: Dict, min_weight: float) -> go.Figure:
        """Create topic evolution timeline plot"""
        topics = timeline_data['topics']
        segments = timeline_data['segments']
        time_segments = timeline_data['time_segments']
        
        # Prepare data for heatmap
        topic_ids = list(topics.keys())
        segment_ids = list(range(time_segments))
        
        z_data = []
        hover_text = []
        
        for topic_id in topic_ids:
            topic_row = []
            hover_row = []
            
            for seg_id in segment_ids:
                weight = segments[seg_id].get(topic_id, 0)
                topic_row.append(weight if weight >= min_weight else 0)
                
                keywords = ', '.join(topics[topic_id]['keywords'][:3])
                hover_row.append(f"Topic {topic_id}<br>Keywords: {keywords}<br>Weight: {weight:.3f}")
            
            z_data.append(topic_row)
            hover_text.append(hover_row)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=[f"Segment {i+1}" for i in segment_ids],
            y=[f"Topic {i}" for i in topic_ids],
            hovertext=hover_text,
            hovertemplate='%{hovertext}<extra></extra>',
            colorscale='Viridis',
            colorbar=dict(title="Topic Weight")
        ))
        
        fig.update_layout(
            title="Topic Evolution Over Time",
            xaxis_title="Time Segments",
            yaxis_title="Topics",
            height=400
        )
        
        return fig
    
    def render_comparative_analysis(self):
        """Render comparative analysis charts between multiple sessions"""
        st.header("📊 Comparative Analysis")
        
        selected_transcripts = self.get_selected_transcripts()
        
        if len(selected_transcripts) < 2:
            st.info("Please select at least 2 transcripts for comparative analysis.")
            return
        
        # Comparison options
        comparison_type = st.selectbox(
            "Comparison Type",
            ["Sentiment Comparison", "Word Usage Comparison", "Speaker Activity", "Topic Similarity", "Duration Analysis"]
        )
        
        if comparison_type == "Sentiment Comparison":
            self.render_sentiment_comparison(selected_transcripts)
        elif comparison_type == "Word Usage Comparison":
            self.render_word_usage_comparison(selected_transcripts)
        elif comparison_type == "Speaker Activity":
            self.render_speaker_activity_comparison(selected_transcripts)
        elif comparison_type == "Topic Similarity":
            self.render_topic_similarity_comparison(selected_transcripts)
        elif comparison_type == "Duration Analysis":
            self.render_duration_analysis(selected_transcripts)
    
    def render_sentiment_comparison(self, transcripts: List[TranscriptData]):
        """Render sentiment comparison between transcripts"""
        st.subheader("Sentiment Comparison")
        
        sentiment_data = []
        
        for transcript in transcripts:
            # Get overall sentiment
            clean_text = re.sub(r'^[A-Za-z]+:', '', transcript.content, flags=re.MULTILINE)
            blob = TextBlob(clean_text)
            
            sentiment_data.append({
                'Transcript': transcript.title,
                'Sentiment Score': blob.sentiment.polarity,
                'Subjectivity': blob.sentiment.subjectivity,
                'Duration (min)': transcript.duration / 60,
                'Speaker Count': len(transcript.speakers)
            })
        
        df = pd.DataFrame(sentiment_data)
        
        # Create comparison chart
        fig = px.scatter(
            df,
            x='Sentiment Score',
            y='Subjectivity',
            size='Duration (min)',
            color='Speaker Count',
            hover_name='Transcript',
            title="Sentiment vs Subjectivity Comparison",
            labels={
                'Sentiment Score': 'Sentiment (Negative ← → Positive)',
                'Subjectivity': 'Subjectivity (Objective ← → Subjective)'
            }
        )
        
        fig.add_vline(x=0, line_dash="dash", line_color="gray", annotation_text="Neutral")
        fig.add_hline(y=0.5, line_dash="dash", line_color="gray", annotation_text="Balanced")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary table
        st.write("**Sentiment Summary:**")
        st.dataframe(df, use_container_width=True)
    
    def render_word_usage_comparison(self, transcripts: List[TranscriptData]):
        """Render word usage comparison"""
        st.subheader("Word Usage Comparison")
        
        # Get top words for each transcript
        all_word_counts = {}
        transcript_words = {}
        
        for transcript in transcripts:
            processed_text = self.preprocess_text_for_wordcloud(transcript.content)
            word_freq = self.get_word_frequencies(processed_text)
            transcript_words[transcript.title] = word_freq
            
            for word, count in word_freq.items():
                if word not in all_word_counts:
                    all_word_counts[word] = {}
                all_word_counts[word][transcript.title] = count
        
        # Find common words
        common_words = [
            word for word, counts in all_word_counts.items()
            if len(counts) >= len(transcripts) // 2  # Word appears in at least half the transcripts
        ][:20]
        
        if common_words:
            # Create comparison data
            comparison_data = []
            for word in common_words:
                for transcript in transcripts:
                    count = transcript_words[transcript.title].get(word, 0)
                    comparison_data.append({
                        'Word': word,
                        'Transcript': transcript.title,
                        'Count': count
                    })
            
            df = pd.DataFrame(comparison_data)
            
            # Create grouped bar chart
            fig = px.bar(
                df,
                x='Word',
                y='Count',
                color='Transcript',
                title="Common Word Usage Comparison",
                barmode='group'
            )
            
            fig.update_layout(height=500, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No common words found across selected transcripts.")
    
    def render_speaker_activity_comparison(self, transcripts: List[TranscriptData]):
        """Render speaker activity comparison"""
        st.subheader("Speaker Activity Comparison")
        
        activity_data = []
        
        for transcript in transcripts:
            network_data = self.build_speaker_network(transcript)
            speaker_stats = network_data['speaker_stats']
            
            for speaker, stats in speaker_stats.items():
                activity_data.append({
                    'Transcript': transcript.title,
                    'Speaker': speaker,
                    'Total Words': stats['total_words'],
                    'Speaking Turns': stats['turns'],
                    'Avg Words per Turn': stats['total_words'] / max(stats['turns'], 1)
                })
        
        if activity_data:
            df = pd.DataFrame(activity_data)
            
            # Create comparison charts
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = px.bar(
                    df,
                    x='Speaker',
                    y='Total Words',
                    color='Transcript',
                    title="Total Words by Speaker",
                    barmode='group'
                )
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                fig2 = px.bar(
                    df,
                    x='Speaker',
                    y='Speaking Turns',
                    color='Transcript',
                    title="Speaking Turns by Speaker",
                    barmode='group'
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # Summary table
            st.write("**Speaker Activity Summary:**")
            st.dataframe(df, use_container_width=True)
    
    def render_topic_similarity_comparison(self, transcripts: List[TranscriptData]):
        """Render topic similarity comparison"""
        st.subheader("Topic Similarity Analysis")
        
        # Extract key topics from each transcript
        transcript_topics = {}
        
        for transcript in transcripts:
            processed_text = self.preprocess_text_for_wordcloud(transcript.content)
            
            # Simple keyword extraction
            words = processed_text.split()
            word_freq = Counter(words)
            top_words = [word for word, count in word_freq.most_common(10)]
            transcript_topics[transcript.title] = top_words
        
        # Calculate similarity matrix
        similarity_matrix = []
        transcript_names = list(transcript_topics.keys())
        
        for i, transcript1 in enumerate(transcript_names):
            row = []
            for j, transcript2 in enumerate(transcript_names):
                if i == j:
                    similarity = 1.0
                else:
                    # Jaccard similarity
                    set1 = set(transcript_topics[transcript1])
                    set2 = set(transcript_topics[transcript2])
                    similarity = len(set1.intersection(set2)) / len(set1.union(set2))
                row.append(similarity)
            similarity_matrix.append(row)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=similarity_matrix,
            x=transcript_names,
            y=transcript_names,
            colorscale='RdYlBu',
            text=[[f"{val:.3f}" for val in row] for row in similarity_matrix],
            texttemplate="%{text}",
            textfont={"size": 12},
            colorbar=dict(title="Similarity Score")
        ))
        
        fig.update_layout(
            title="Topic Similarity Matrix",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show topic keywords
        st.write("**Top Keywords by Transcript:**")
        for transcript, keywords in transcript_topics.items():
            st.write(f"**{transcript}:** {', '.join(keywords)}")
    
    def render_duration_analysis(self, transcripts: List[TranscriptData]):
        """Render duration and timing analysis"""
        st.subheader("Duration and Timing Analysis")
        
        duration_data = []
        
        for transcript in transcripts:
            # Calculate speaking statistics
            network_data = self.build_speaker_network(transcript)
            speaker_stats = network_data['speaker_stats']
            
            total_words = sum(stats['total_words'] for stats in speaker_stats.values())
            total_turns = sum(stats['turns'] for stats in speaker_stats.values())
            
            duration_data.append({
                'Transcript': transcript.title,
                'Duration (min)': transcript.duration / 60,
                'Total Words': total_words,
                'Total Turns': total_turns,
                'Words per Minute': total_words / (transcript.duration / 60),
                'Turns per Minute': total_turns / (transcript.duration / 60),
                'Avg Words per Turn': total_words / max(total_turns, 1),
                'Speaker Count': len(transcript.speakers)
            })
        
        df = pd.DataFrame(duration_data)
        
        # Create comparison charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(
                df,
                x='Transcript',
                y='Duration (min)',
                title="Meeting Duration Comparison",
                color='Speaker Count',
                text='Duration (min)'
            )
            fig1.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.scatter(
                df,
                x='Words per Minute',
                y='Turns per Minute',
                size='Duration (min)',
                color='Speaker Count',
                hover_name='Transcript',
                title="Speaking Pace Analysis"
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Summary statistics
        st.write("**Duration Analysis Summary:**")
        st.dataframe(df, use_container_width=True)
    
    def run(self):
        """Run the advanced visualization dashboard"""
        st.set_page_config(
            page_title="Advanced Visualization Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Render header and check if transcripts are selected
        if not self.render_header():
            return
        
        # Sidebar navigation
        st.sidebar.title("📊 Dashboard Navigation")
        
        analysis_type = st.sidebar.selectbox(
            "Select Analysis Type",
            [
                "Word Cloud Analysis",
                "Sentiment Flow",
                "Speaker Networks",
                "Topic Evolution",
                "Comparative Analysis"
            ]
        )
        
        # Render selected analysis
        if analysis_type == "Word Cloud Analysis":
            self.render_word_cloud_analysis()
        elif analysis_type == "Sentiment Flow":
            self.render_sentiment_flow_analysis()
        elif analysis_type == "Speaker Networks":
            self.render_speaker_interaction_network()
        elif analysis_type == "Topic Evolution":
            self.render_topic_evolution_timeline()
        elif analysis_type == "Comparative Analysis":
            self.render_comparative_analysis()
        
        # Footer
        st.markdown("---")
        st.markdown("**Advanced Visualization Dashboard** - Interactive analytics for transcript analysis")

def main():
    """Main function to run the dashboard"""
    dashboard = AdvancedVisualizationDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()