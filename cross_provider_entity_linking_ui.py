#!/usr/bin/env python3
"""
Streamlit UI for Cross-Provider Entity Linking System.
Provides comprehensive interface for entity linking, disambiguation, and relationship exploration.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from plotly.subplots import make_subplots
import json
from datetime import datetime
from typing import Dict, List, Any
import time

from cross_provider_entity_linking import (
    CrossProviderEntityLinker,
    create_entity_linker,
    link_entities_in_text
)

# Page configuration
st.set_page_config(
    page_title="Cross-Provider Entity Linking",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'linker' not in st.session_state:
    st.session_state.linker = None
if 'processing_history' not in st.session_state:
    st.session_state.processing_history = []
if 'current_results' not in st.session_state:
    st.session_state.current_results = None


@st.cache_resource
def get_entity_linker(providers: List[str]):
    """Get cached entity linker instance."""
    try:
        return create_entity_linker(providers)
    except Exception as e:
        st.error(f"Failed to initialize entity linker: {e}")
        return None


def render_sidebar():
    """Render sidebar configuration."""
    st.sidebar.title("🔗 Entity Linking")
    st.sidebar.markdown("---")
    
    # Provider Selection
    st.sidebar.subheader("🔧 Provider Configuration")
    
    available_providers = ["wikipedia", "wikidata", "dbpedia", "huggingface"]
    selected_providers = st.sidebar.multiselect(
        "Select Providers",
        available_providers,
        default=["wikipedia", "wikidata"],
        help="Choose which knowledge bases to use for entity linking"
    )
    
    # Linking Settings
    st.sidebar.subheader("⚙️ Linking Settings")
    
    confidence_threshold = st.sidebar.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        help="Minimum confidence score for entity links"
    )
    
    max_candidates = st.sidebar.slider(
        "Max Candidates per Entity",
        min_value=1,
        max_value=10,
        value=5,
        help="Maximum number of candidate links to consider"
    )
    
    # Advanced Options
    with st.sidebar.expander("🔬 Advanced Options"):
        enable_disambiguation = st.checkbox("Enable Disambiguation", value=True)
        extract_relationships = st.checkbox("Extract Relationships", value=True)
        build_entity_graph = st.checkbox("Build Entity Graph", value=True)
        show_provider_details = st.checkbox("Show Provider Details", value=False)
    
    # Initialize linker
    if selected_providers and st.sidebar.button("Initialize Linker"):
        with st.spinner("Initializing entity linker..."):
            linker = get_entity_linker(selected_providers)
            if linker:
                linker.confidence_threshold = confidence_threshold
                linker.max_candidates = max_candidates
                st.session_state.linker = linker
                st.sidebar.success("✅ Linker initialized!")
            else:
                st.sidebar.error("❌ Failed to initialize linker")
    
    return {
        'providers': selected_providers,
        'confidence_threshold': confidence_threshold,
        'max_candidates': max_candidates,
        'enable_disambiguation': enable_disambiguation,
        'extract_relationships': extract_relationships,
        'build_entity_graph': build_entity_graph,
        'show_provider_details': show_provider_details
    }


def render_text_input():
    """Render text input interface."""
    st.subheader("📝 Text Input")
    
    # Input methods
    input_method = st.radio(
        "Input Method",
        ["Direct Text", "Upload File", "Sample Texts"],
        horizontal=True
    )
    
    text_content = ""
    
    if input_method == "Direct Text":
        text_content = st.text_area(
            "Enter text for entity linking",
            height=200,
            placeholder="Enter text containing entities to be linked..."
        )
    
    elif input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload text file",
            type=['txt', 'md'],
            help="Upload a text file for entity linking"
        )
        
        if uploaded_file:
            text_content = str(uploaded_file.read(), "utf-8")
            st.text_area("File content preview", value=text_content[:500] + "...", height=100, disabled=True)
    
    elif input_method == "Sample Texts":
        sample_texts = {
            "Technology News": """
            Apple Inc. announced that Tim Cook will present the new iPhone at the Apple Park
            in Cupertino, California. The event will be streamed live from the Steve Jobs Theater.
            Microsoft and Google are also expected to announce new products this quarter.
            """,
            "Historical Text": """
            During World War II, Winston Churchill served as Prime Minister of the United Kingdom.
            The Battle of Britain took place in 1940, with the Royal Air Force defending against
            the German Luftwaffe. Franklin D. Roosevelt was President of the United States at the time.
            """,
            "Academic Paper": """
            The research was conducted at Stanford University by Dr. Sarah Johnson and her team.
            The study, published in Nature, examined the effects of climate change on Arctic ice.
            The findings were presented at the International Climate Conference in Geneva, Switzerland.
            """,
            "Business Article": """
            Tesla CEO Elon Musk announced that the company will build a new Gigafactory in Berlin, Germany.
            The facility will produce Model Y vehicles for the European market. The announcement was made
            at the Tesla Design Studio in Hawthorne, California.
            """
        }
        
        selected_sample = st.selectbox("Choose sample text", list(sample_texts.keys()))
        text_content = sample_texts[selected_sample]
        st.text_area("Sample text", value=text_content, height=150, disabled=True)
    
    return text_content


def process_text(text: str, config: Dict[str, Any]):
    """Process text for entity linking."""
    if not st.session_state.linker:
        st.error("⚠️ Please initialize the entity linker first.")
        return None
    
    if not text.strip():
        st.warning("⚠️ Please enter some text to process.")
        return None
    
    with st.spinner("Processing text for entity linking..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Update linker settings
            linker = st.session_state.linker
            linker.confidence_threshold = config['confidence_threshold']
            linker.max_candidates = config['max_candidates']
            
            status_text.text("Extracting entities...")
            progress_bar.progress(0.2)
            
            # Process text
            results = linker.process_text(text)
            
            status_text.text("Linking entities across providers...")
            progress_bar.progress(0.6)
            
            # Add processing metadata
            results['config'] = config
            results['processing_time'] = time.time()
            
            status_text.text("Building entity graph...")
            progress_bar.progress(0.8)
            
            # Store results
            st.session_state.current_results = results
            st.session_state.processing_history.append({
                'timestamp': datetime.now(),
                'text_preview': text[:100] + "..." if len(text) > 100 else text,
                'entities_found': len(results['entity_links']),
                'providers_used': results['processing_metadata']['providers_used']
            })
            
            progress_bar.progress(1.0)
            status_text.text("✅ Processing completed!")
            
            return results
            
        except Exception as e:
            st.error(f"❌ Processing failed: {e}")
            return None


def render_results_overview(results: Dict[str, Any]):
    """Render results overview with key metrics."""
    st.subheader("📊 Results Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Entities Extracted",
            len(results['entities']),
            help="Total number of entities found in the text"
        )
    
    with col2:
        st.metric(
            "Entities Linked",
            len(results['entity_links']),
            help="Number of entities successfully linked to knowledge bases"
        )
    
    with col3:
        st.metric(
            "Relationships Found",
            len(results['relationships']),
            help="Number of relationships discovered between entities"
        )
    
    with col4:
        avg_confidence = sum(link['confidence'] for link in results['entity_links']) / max(len(results['entity_links']), 1)
        st.metric(
            "Avg Confidence",
            f"{avg_confidence:.2f}",
            help="Average confidence score of entity links"
        )
    
    # Provider distribution
    if results['entity_links']:
        provider_counts = {}
        for link in results['entity_links']:
            provider = link['source']
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Provider distribution pie chart
            fig = px.pie(
                values=list(provider_counts.values()),
                names=list(provider_counts.keys()),
                title="Entity Links by Provider"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Confidence distribution histogram
            confidences = [link['confidence'] for link in results['entity_links']]
            fig = px.histogram(
                x=confidences,
                nbins=10,
                title="Confidence Score Distribution",
                labels={'x': 'Confidence Score', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)


def render_entity_details(results: Dict[str, Any]):
    """Render detailed entity information."""
    st.subheader("🏷️ Entity Details")
    
    if not results['entity_links']:
        st.info("No entities were successfully linked.")
        return
    
    # Entity selection
    entity_options = [f"{link['mention']} → {link['entity_name']}" for link in results['entity_links']]
    selected_entity_idx = st.selectbox(
        "Select entity to explore",
        range(len(entity_options)),
        format_func=lambda x: entity_options[x]
    )
    
    if selected_entity_idx is not None:
        selected_link = results['entity_links'][selected_entity_idx]
        
        # Entity information
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Entity Information:**")
            st.write(f"**Mention:** {selected_link['mention']}")
            st.write(f"**Linked Name:** {selected_link['entity_name']}")
            st.write(f"**Source:** {selected_link['source']}")
            st.write(f"**Confidence:** {selected_link['confidence']:.3f}")
            
            if selected_link.get('description'):
                st.write(f"**Description:** {selected_link['description']}")
            
            if selected_link.get('entity_id'):
                st.write(f"**Entity ID:** `{selected_link['entity_id']}`")
        
        with col2:
            # Confidence gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=selected_link['confidence'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Confidence"},
                gauge={
                    'axis': {'range': [None, 1]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 0.5], 'color': "lightgray"},
                        {'range': [0.5, 0.8], 'color': "yellow"},
                        {'range': [0.8, 1], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.9
                    }
                }
            ))
            fig.update_layout(height=200)
            st.plotly_chart(fig, use_container_width=True)
        
        # Properties
        if selected_link.get('properties'):
            st.write("**Properties:**")
            properties_df = pd.DataFrame([
                {'Property': k, 'Value': ', '.join(v) if isinstance(v, list) else str(v)}
                for k, v in selected_link['properties'].items()
            ])
            st.dataframe(properties_df, use_container_width=True)


def render_provider_comparison(results: Dict[str, Any]):
    """Render provider comparison analysis."""
    st.subheader("🔍 Provider Comparison")
    
    if not results.get('provider_results'):
        st.info("No provider-specific results available.")
        return
    
    # Create comparison table
    comparison_data = []
    for provider, links in results['provider_results'].items():
        if links:
            avg_confidence = sum(link['confidence'] for link in links) / len(links)
            comparison_data.append({
                'Provider': provider.title(),
                'Links Found': len(links),
                'Avg Confidence': avg_confidence,
                'Unique Entities': len(set(link['entity_name'] for link in links))
            })
    
    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)
        
        # Detailed provider results
        st.write("**Detailed Provider Results:**")
        
        for provider, links in results['provider_results'].items():
            if links:
                with st.expander(f"{provider.title()} ({len(links)} links)"):
                    for link in links:
                        st.write(f"• **{link['mention']}** → {link['entity_name']} (conf: {link['confidence']:.2f})")
                        if link.get('description'):
                            st.write(f"  _{link['description'][:100]}..._")


def render_entity_graph(results: Dict[str, Any]):
    """Render entity relationship graph."""
    st.subheader("🕸️ Entity Relationship Graph")
    
    if not results['relationships']:
        st.info("No relationships found between entities.")
        return
    
    # Build graph
    G = nx.Graph()
    
    # Add nodes (entities)
    for link in results['entity_links']:
        G.add_node(
            link['entity_name'],
            confidence=link['confidence'],
            source=link['source']
        )
    
    # Add edges (relationships)
    for rel in results['relationships']:
        if rel['subject_entity'] in G.nodes and rel['object_entity'] in G.nodes:
            G.add_edge(
                rel['subject_entity'],
                rel['object_entity'],
                predicate=rel['predicate'],
                confidence=rel['confidence']
            )
    
    if G.number_of_nodes() == 0:
        st.info("No connected entities found for graph visualization.")
        return
    
    # Graph statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nodes", G.number_of_nodes())
    with col2:
        st.metric("Edges", G.number_of_edges())
    with col3:
        st.metric("Connected Components", nx.number_connected_components(G))
    
    # Create network visualization
    try:
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Extract node and edge information
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        node_text = list(G.nodes())
        node_colors = [G.nodes[node].get('confidence', 0.5) for node in G.nodes()]
        
        # Create edges
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create plotly figure
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='gray'),
            hoverinfo='none',
            mode='lines'
        ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=20,
                color=node_colors,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Confidence")
            )
        ))
        
        fig.update_layout(
            title="Entity Relationship Graph",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text="Node size and color represent entity confidence",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(size=12)
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating graph visualization: {e}")
    
    # Relationship details
    if results['relationships']:
        st.write("**Relationship Details:**")
        relationships_df = pd.DataFrame(results['relationships'])
        st.dataframe(relationships_df, use_container_width=True)


def render_export_options(results: Dict[str, Any]):
    """Render export options for results."""
    st.subheader("📤 Export Results")
    
    if not results:
        st.info("No results to export.")
        return
    
    # Export format selection
    export_format = st.selectbox(
        "Export Format",
        ["JSON", "CSV (Entity Links)", "CSV (Relationships)", "Text Summary"]
    )
    
    # Generate export content
    if export_format == "JSON":
        export_content = json.dumps(results, indent=2, default=str)
        filename = f"entity_linking_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        mime_type = "application/json"
    
    elif export_format == "CSV (Entity Links)":
        if results['entity_links']:
            df = pd.DataFrame(results['entity_links'])
            export_content = df.to_csv(index=False)
            filename = f"entity_links_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            mime_type = "text/csv"
        else:
            st.warning("No entity links to export.")
            return
    
    elif export_format == "CSV (Relationships)":
        if results['relationships']:
            df = pd.DataFrame(results['relationships'])
            export_content = df.to_csv(index=False)
            filename = f"entity_relationships_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            mime_type = "text/csv"
        else:
            st.warning("No relationships to export.")
            return
    
    elif export_format == "Text Summary":
        summary_lines = [
            f"Entity Linking Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            f"Text processed: {len(results['text'])} characters",
            f"Entities extracted: {len(results['entities'])}",
            f"Entities linked: {len(results['entity_links'])}",
            f"Relationships found: {len(results['relationships'])}",
            f"Providers used: {', '.join(results['processing_metadata']['providers_used'])}",
            "",
            "Entity Links:",
            "-" * 20
        ]
        
        for link in results['entity_links']:
            summary_lines.append(f"• {link['mention']} → {link['entity_name']} ({link['source']}, conf: {link['confidence']:.2f})")
        
        if results['relationships']:
            summary_lines.extend([
                "",
                "Relationships:",
                "-" * 20
            ])
            for rel in results['relationships'][:10]:  # Limit to first 10
                summary_lines.append(f"• {rel['subject_entity']} {rel['predicate']} {rel['object_entity']}")
        
        export_content = "\n".join(summary_lines)
        filename = f"entity_linking_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        mime_type = "text/plain"
    
    # Download button
    st.download_button(
        label=f"📥 Download {export_format}",
        data=export_content,
        file_name=filename,
        mime=mime_type
    )
    
    # Preview
    with st.expander("Preview Export Content"):
        if export_format == "JSON":
            st.json(results)
        else:
            st.text(export_content[:1000] + "..." if len(export_content) > 1000 else export_content)


def render_processing_history():
    """Render processing history."""
    st.subheader("📚 Processing History")
    
    if not st.session_state.processing_history:
        st.info("No processing history available.")
        return
    
    # Display history
    history_df = pd.DataFrame(st.session_state.processing_history)
    history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
    history_df = history_df.sort_values('timestamp', ascending=False)
    
    st.dataframe(history_df, use_container_width=True)
    
    # Clear history button
    if st.button("🗑️ Clear History"):
        st.session_state.processing_history = []
        st.rerun()


def main():
    """Main application function."""
    st.title("🔗 Cross-Provider Entity Linking")
    st.markdown("Link entities across Wikipedia, Wikidata, DBpedia, and Hugging Face models")
    
    # Render sidebar
    config = render_sidebar()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Process Text",
        "📊 Results",
        "🔍 Analysis",
        "📤 Export",
        "📚 History"
    ])
    
    with tab1:
        # Text input and processing
        text_content = render_text_input()
        
        if text_content and st.button("🚀 Process Text", type="primary"):
            results = process_text(text_content, config)
            if results:
                st.success("✅ Text processed successfully!")
    
    with tab2:
        # Results display
        if st.session_state.current_results:
            render_results_overview(st.session_state.current_results)
            render_entity_details(st.session_state.current_results)
        else:
            st.info("No results to display. Process some text first.")
    
    with tab3:
        # Analysis and visualization
        if st.session_state.current_results:
            if config['show_provider_details']:
                render_provider_comparison(st.session_state.current_results)
            
            if config['build_entity_graph']:
                render_entity_graph(st.session_state.current_results)
        else:
            st.info("No results to analyze. Process some text first.")
    
    with tab4:
        # Export options
        if st.session_state.current_results:
            render_export_options(st.session_state.current_results)
        else:
            st.info("No results to export. Process some text first.")
    
    with tab5:
        # Processing history
        render_processing_history()


if __name__ == "__main__":
    main()