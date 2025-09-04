#!/usr/bin/env python3
"""
Demo script for intelligent content chunking and segmentation
Demonstrates Task 37 implementation
"""

import streamlit as st
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from segmentation.intelligent_chunking import render_intelligent_chunking_interface

def main():
    """Main demo application"""
    st.set_page_config(
        page_title="Intelligent Content Chunking Demo",
        page_icon="✂️",
        layout="wide"
    )
    
    st.title("✂️ Intelligent Content Chunking & Segmentation")
    st.markdown("**Task 37 Implementation Demo**")
    
    st.markdown("""
    This demo showcases the intelligent content chunking and segmentation system with:
    
    - 🧠 **Semantic chunking** based on topic boundaries
    - 🗣️ **Speaker-based segmentation** for multi-person conversations  
    - ⏰ **Time-based chunking** with configurable intervals
    - 🔇 **Silence-based automatic segmentation**
    - 📖 **Manual chapter marking** with visual timeline editor
    """)
    
    # Sample data
    sample_transcript = """
    Good morning everyone, and welcome to our quarterly business review meeting. My name is Sarah Johnson, and I'll be facilitating today's discussion.
    
    Let's start with our financial performance. This quarter, we've seen remarkable growth across all our key metrics. Revenue increased by 23% compared to the same period last year, reaching $2.4 million. Our customer acquisition cost has decreased by 15%, while customer lifetime value has grown by 18%.
    
    Now, moving on to our product development updates. The engineering team, led by Michael Chen, has successfully launched three major features this quarter. The new analytics dashboard has received overwhelmingly positive feedback from our beta users, with a 94% satisfaction rate.
    
    I'd like to invite Michael to share more details about the technical achievements. Michael, could you walk us through the key innovations?
    
    Thank you, Sarah. Yes, I'm excited to share what we've accomplished. The new machine learning pipeline we implemented has reduced processing time by 40%. We've also enhanced our API performance, achieving 99.9% uptime this quarter.
    
    That's fantastic, Michael. Now, let's discuss our marketing initiatives. The campaign we launched in September has exceeded all expectations. Our social media engagement increased by 67%, and we've gained 15,000 new followers across all platforms.
    
    Looking ahead to next quarter, we have several exciting projects in the pipeline. We're planning to expand into two new markets and launch our mobile application. The beta testing for the mobile app will begin next month.
    
    Before we wrap up, are there any questions or concerns from the team? This is a great opportunity to address any challenges you might be facing.
    
    Thank you all for your hard work and dedication. I'm confident that with our continued collaboration, we'll achieve even greater success in the coming quarter. Have a great rest of your day!
    """
    
    sample_timestamps = [
        (0.0, 8.0, "Good morning everyone, and welcome to our quarterly business review meeting."),
        (8.0, 12.0, "My name is Sarah Johnson, and I'll be facilitating today's discussion."),
        (15.0, 20.0, "Let's start with our financial performance."),
        (20.0, 28.0, "This quarter, we've seen remarkable growth across all our key metrics."),
        (28.0, 35.0, "Revenue increased by 23% compared to the same period last year, reaching $2.4 million."),
        (35.0, 45.0, "Our customer acquisition cost has decreased by 15%, while customer lifetime value has grown by 18%."),
        (50.0, 55.0, "Now, moving on to our product development updates."),
        (55.0, 65.0, "The engineering team, led by Michael Chen, has successfully launched three major features this quarter."),
        (65.0, 75.0, "The new analytics dashboard has received overwhelmingly positive feedback from our beta users, with a 94% satisfaction rate."),
        (80.0, 88.0, "I'd like to invite Michael to share more details about the technical achievements."),
        (88.0, 92.0, "Michael, could you walk us through the key innovations?"),
        (95.0, 100.0, "Thank you, Sarah. Yes, I'm excited to share what we've accomplished."),
        (100.0, 108.0, "The new machine learning pipeline we implemented has reduced processing time by 40%."),
        (108.0, 118.0, "We've also enhanced our API performance, achieving 99.9% uptime this quarter."),
        (125.0, 130.0, "That's fantastic, Michael. Now, let's discuss our marketing initiatives."),
        (130.0, 138.0, "The campaign we launched in September has exceeded all expectations."),
        (138.0, 148.0, "Our social media engagement increased by 67%, and we've gained 15,000 new followers across all platforms."),
        (155.0, 162.0, "Looking ahead to next quarter, we have several exciting projects in the pipeline."),
        (162.0, 170.0, "We're planning to expand into two new markets and launch our mobile application."),
        (170.0, 175.0, "The beta testing for the mobile app will begin next month."),
        (180.0, 188.0, "Before we wrap up, are there any questions or concerns from the team?"),
        (188.0, 195.0, "This is a great opportunity to address any challenges you might be facing."),
        (200.0, 208.0, "Thank you all for your hard work and dedication."),
        (208.0, 218.0, "I'm confident that with our continued collaboration, we'll achieve even greater success in the coming quarter."),
        (218.0, 222.0, "Have a great rest of your day!")
    ]
    
    sample_speakers = ["Sarah Johnson", "Michael Chen"]
    
    # Input options
    st.sidebar.header("Demo Options")
    
    use_sample_data = st.sidebar.checkbox(
        "Use Sample Data",
        value=True,
        help="Use pre-loaded sample transcript and timestamps"
    )
    
    if use_sample_data:
        transcript = sample_transcript
        timestamps = sample_timestamps
        speakers = sample_speakers
        audio_path = None  # No audio file for demo
        
        st.sidebar.success("✅ Using sample business meeting data")
        
        # Show sample data info
        with st.sidebar.expander("Sample Data Info", expanded=False):
            st.write(f"**Transcript Length:** {len(transcript)} characters")
            st.write(f"**Timestamps:** {len(timestamps)} segments")
            st.write(f"**Speakers:** {', '.join(speakers)}")
            st.write(f"**Duration:** ~{max(t[1] for t in timestamps):.0f} seconds")
    
    else:
        # Custom input
        st.sidebar.info("Enter your own transcript data")
        
        transcript = st.text_area(
            "Transcript Text",
            height=200,
            placeholder="Enter your transcript here..."
        )
        
        # Simple timestamp input
        timestamp_text = st.text_area(
            "Timestamps (optional)",
            height=100,
            placeholder="Format: start_time,end_time,text (one per line)\nExample: 0.0,5.0,Hello world"
        )
        
        speakers_text = st.text_input(
            "Speakers (optional)",
            placeholder="Enter speaker names separated by commas"
        )
        
        # Parse inputs
        timestamps = []
        if timestamp_text:
            for line in timestamp_text.strip().split('\n'):
                parts = line.split(',', 2)
                if len(parts) == 3:
                    try:
                        start_time = float(parts[0])
                        end_time = float(parts[1])
                        text = parts[2]
                        timestamps.append((start_time, end_time, text))
                    except ValueError:
                        continue
        
        speakers = []
        if speakers_text:
            speakers = [s.strip() for s in speakers_text.split(',') if s.strip()]
        
        audio_path = None
    
    # Main interface
    if transcript:
        st.markdown("---")
        
        # Render the intelligent chunking interface
        segments = render_intelligent_chunking_interface(
            transcript=transcript,
            timestamps=timestamps if timestamps else None,
            speakers=speakers if speakers else None,
            audio_path=audio_path,
            editable=True
        )
        
        # Show results summary
        if segments:
            st.markdown("---")
            st.markdown("### 📋 Processing Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Segments", len(segments))
            
            with col2:
                avg_length = sum(len(seg.text) for seg in segments) / len(segments)
                st.metric("Avg Length", f"{avg_length:.0f} chars")
            
            with col3:
                unique_speakers = len(set(seg.speaker for seg in segments if seg.speaker))
                st.metric("Speakers", unique_speakers)
            
            with col4:
                if timestamps:
                    duration = max(seg.end_time for seg in segments if seg.end_time)
                    st.metric("Duration", f"{duration:.1f}s")
                else:
                    st.metric("Duration", "N/A")
            
            # Segment type breakdown
            segment_types = {}
            for seg in segments:
                seg_type = seg.type.value
                segment_types[seg_type] = segment_types.get(seg_type, 0) + 1
            
            if segment_types:
                st.markdown("**Segment Types:**")
                type_cols = st.columns(len(segment_types))
                
                for i, (seg_type, count) in enumerate(segment_types.items()):
                    with type_cols[i]:
                        st.metric(
                            seg_type.replace('_', ' ').title(),
                            count
                        )
    
    else:
        st.info("👆 Please enter a transcript or enable sample data to begin segmentation.")
    
    # Help section
    with st.expander("ℹ️ How to Use", expanded=False):
        st.markdown("""
        ### Getting Started
        
        1. **Enable Sample Data** in the sidebar to try the demo with pre-loaded content
        2. Or **enter your own transcript** and optional timestamp data
        3. The system will automatically process and segment your content
        
        ### Features Available
        
        - **Timeline View**: Visual timeline with interactive segments
        - **List View**: Detailed list of all segments with editing capabilities  
        - **Grid View**: Organized grid layout grouped by segment type
        - **Chapter Editor**: Create and manage manual chapter markers
        - **Analytics**: Comprehensive statistics about your segmentation
        
        ### Segmentation Methods
        
        - **Semantic**: Groups content by topic similarity
        - **Structural**: Identifies patterns like introductions, conclusions, questions
        - **Temporal**: Creates segments based on time intervals
        - **Silence**: Uses audio silence detection (requires audio file)
        - **Hybrid**: Combines multiple methods for best results
        
        ### Export Options
        
        Export your segments in multiple formats:
        - JSON for data processing
        - SRT for subtitles
        - VTT for web video
        - Plain text for documentation
        """)

if __name__ == "__main__":
    main()