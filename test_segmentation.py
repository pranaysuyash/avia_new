#!/usr/bin/env python3
"""
Test script to demonstrate advanced segmentation features
"""

import streamlit as st
from segmentation import SegmentManager, SegmentType, render_segmentation_view
import time


# Sample transcript for testing
SAMPLE_TRANSCRIPT = """
Good morning everyone, and welcome to today's presentation on climate change and renewable energy solutions. My name is Dr. Sarah Johnson, and I'm the lead researcher at the Environmental Sciences Institute. Today, we'll be exploring the latest developments in sustainable technology and their potential impact on our future.

Let me start by discussing the current state of our climate. Over the past decade, we've observed unprecedented changes in global temperature patterns. The data shows a consistent warming trend, with the last five years being the warmest on record. This has led to significant impacts on ecosystems worldwide, from melting polar ice caps to shifting weather patterns.

Now, let's talk about renewable energy solutions. Solar power technology has advanced remarkably in recent years. The efficiency of photovoltaic cells has increased by over 40% since 2010, while costs have dropped by nearly 80%. This makes solar energy increasingly competitive with traditional fossil fuels.

Wind energy is another crucial component of our renewable future. Modern wind turbines can generate enough electricity to power thousands of homes. Offshore wind farms, in particular, show tremendous potential due to stronger and more consistent wind patterns over the ocean.

But what about energy storage? This is perhaps the most critical challenge we face. Battery technology is improving rapidly, with lithium-ion batteries becoming more efficient and affordable. However, we need breakthrough innovations in grid-scale storage to fully transition to renewable energy.

Let me address a common question: Is renewable energy reliable enough to replace fossil fuels? The answer is increasingly yes. With proper infrastructure and energy storage solutions, renewable sources can provide consistent, reliable power. Countries like Denmark and Costa Rica have already demonstrated this is possible.

Moving on to policy implications. Governments worldwide are implementing carbon pricing mechanisms and renewable energy incentives. These policies are essential for accelerating the transition to clean energy. The European Union's Green Deal and China's carbon neutrality pledge are excellent examples of ambitious climate policies.

Another important point is the economic opportunity. The renewable energy sector has created millions of jobs globally. From manufacturing to installation and maintenance, green jobs are growing faster than any other sector. This transition isn't just good for the environment; it's good for the economy.

In conclusion, while climate change presents enormous challenges, we have the technology and knowledge to address them. The transition to renewable energy is not only necessary but increasingly feasible and economically attractive. Each of us has a role to play in this transformation, whether through personal choices or supporting progressive policies.

Thank you for your attention. I'm happy to answer any questions you might have about climate change or renewable energy solutions. Who would like to start?
"""


def main():
    st.set_page_config(
        page_title="Advanced Segmentation Demo",
        page_icon="📑",
        layout="wide"
    )
    
    st.title("📑 Advanced Segmentation Demo")
    st.markdown("Demonstrating intelligent transcript segmentation with multiple methods")
    
    # Create tabs for different demos
    tab1, tab2, tab3 = st.tabs(["Live Demo", "Method Comparison", "Custom Text"])
    
    with tab1:
        st.header("🔄 Live Segmentation Demo")
        
        # Method selection
        col1, col2 = st.columns([2, 1])
        with col1:
            method = st.selectbox(
                "Select Segmentation Method",
                ["hybrid", "semantic", "structural", "temporal"],
                help="Choose the segmentation algorithm"
            )
        
        with col2:
            if st.button("🚀 Generate Segments", type="primary"):
                with st.spinner(f"Applying {method} segmentation..."):
                    # Simulate processing time
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    # Create segment manager
                    manager = SegmentManager()
                    
                    # Generate segments
                    segments = manager.segment_transcript(
                        SAMPLE_TRANSCRIPT,
                        method=method
                    )
                    
                    # Store in session state
                    st.session_state.demo_segments = segments
                    st.success(f"✅ Generated {len(segments)} segments using {method} method!")
        
        # Display segments if available
        if 'demo_segments' in st.session_state:
            segments = st.session_state.demo_segments
            
            # Show summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Segments", len(segments))
            with col2:
                avg_length = sum(len(s.text) for s in segments) / len(segments)
                st.metric("Avg Length", f"{avg_length:.0f} chars")
            with col3:
                types = set(s.type.value for s in segments)
                st.metric("Segment Types", len(types))
            with col4:
                total_keywords = sum(len(s.keywords) for s in segments)
                st.metric("Total Keywords", total_keywords)
            
            # Render segmentation view
            st.markdown("---")
            updated_segments = render_segmentation_view(
                SAMPLE_TRANSCRIPT,
                segments,
                editable=True
            )
            
            # Update session state if changed
            if updated_segments != segments:
                st.session_state.demo_segments = updated_segments
    
    with tab2:
        st.header("📊 Method Comparison")
        
        if st.button("🔍 Compare All Methods"):
            manager = SegmentManager()
            methods = ["hybrid", "semantic", "structural", "temporal"]
            
            comparison_data = []
            
            # Progress bar
            progress = st.progress(0)
            
            for i, method in enumerate(methods):
                with st.spinner(f"Processing {method}..."):
                    segments = manager.segment_transcript(SAMPLE_TRANSCRIPT, method=method)
                    
                    comparison_data.append({
                        'Method': method.title(),
                        'Segments': len(segments),
                        'Avg Length': sum(len(s.text) for s in segments) / len(segments),
                        'Types': len(set(s.type.value for s in segments)),
                        'Keywords': sum(len(s.keywords) for s in segments)
                    })
                    
                    progress.progress((i + 1) / len(methods))
            
            # Display comparison
            import pandas as pd
            df = pd.DataFrame(comparison_data)
            
            st.dataframe(df, use_container_width=True)
            
            # Visualizations
            import plotly.express as px
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = px.bar(df, x='Method', y='Segments', title='Number of Segments by Method')
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                fig2 = px.bar(df, x='Method', y='Avg Length', title='Average Segment Length by Method')
                st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        st.header("✏️ Custom Text Segmentation")
        
        # Text input
        custom_text = st.text_area(
            "Enter your text to segment",
            height=300,
            placeholder="Paste or type your text here..."
        )
        
        if custom_text:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                custom_method = st.selectbox(
                    "Segmentation Method",
                    ["hybrid", "semantic", "structural", "temporal"],
                    key="custom_method"
                )
            
            with col2:
                if st.button("🔄 Segment Custom Text", type="primary"):
                    with st.spinner("Segmenting..."):
                        manager = SegmentManager()
                        custom_segments = manager.segment_transcript(
                            custom_text,
                            method=custom_method
                        )
                        st.session_state.custom_segments = custom_segments
                        st.success(f"Generated {len(custom_segments)} segments!")
            
            # Display custom segments
            if 'custom_segments' in st.session_state:
                st.markdown("---")
                render_segmentation_view(
                    custom_text,
                    st.session_state.custom_segments,
                    editable=True
                )
    
    # Sidebar with information
    with st.sidebar:
        st.header("📚 About Advanced Segmentation")
        
        st.markdown("""
        ### Features
        - **Intelligent Chunking**: Automatically divides text into meaningful segments
        - **Multiple Methods**: Choose from semantic, structural, temporal, or hybrid approaches
        - **Interactive Editing**: Modify segments, types, and metadata
        - **Keyword Extraction**: Automatic identification of key terms
        - **Export Formats**: JSON, SRT, VTT, and plain text
        
        ### Segment Types
        - 🟢 **Introduction**: Opening statements
        - 🔵 **Main Topic**: Primary content sections
        - 🔷 **Sub Topic**: Secondary points
        - 🟣 **Conclusion**: Closing statements
        - 🟠 **Question**: Interrogative segments
        - 🟡 **Answer**: Response segments
        - ⚫ **Transition**: Connecting phrases
        - 🟤 **Speaker Change**: Different speakers
        - ⚪ **Pause**: Silence or breaks
        - 🔴 **Custom**: User-defined segments
        
        ### Use Cases
        - Video subtitling and captioning
        - Podcast transcription organization
        - Meeting minutes structuring
        - Educational content indexing
        - Content analysis and summarization
        """)


if __name__ == "__main__":
    main()