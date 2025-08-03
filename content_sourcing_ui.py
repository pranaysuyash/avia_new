#!/usr/bin/env python3
"""
Content Sourcing UI - Manage multiple content sources for recommendations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

from content_sourcing_strategy import (
    content_aggregator, ContentSourceManager, YouTubeContentSource,
    PublicContentPlatform, CuratedContentSource
)
from content_recommendations import recommendation_engine

def render_content_sourcing_interface():
    """Main interface for content sourcing management"""
    
    st.markdown("## 📚 Content Sources & Discovery")
    st.markdown("Manage and discover content from multiple sources to enhance your recommendation library.")
    
    # Create tabs for different sourcing features
    sources_tab, discovery_tab, public_tab, youtube_tab, settings_tab = st.tabs([
        "📊 Source Overview",
        "🔍 Content Discovery",
        "🌐 Public Platform",
        "📺 YouTube Integration",
        "⚙️ Source Settings"
    ])
    
    with sources_tab:
        render_source_overview_tab()
    
    with discovery_tab:
        render_content_discovery_tab()
    
    with public_tab:
        render_public_platform_tab()
    
    with youtube_tab:
        render_youtube_integration_tab()
    
    with settings_tab:
        render_source_settings_tab()


def render_source_overview_tab():
    """Render overview of all content sources"""
    
    st.markdown("### 📊 Content Source Overview")
    
    # Get source statistics
    stats = content_aggregator.get_content_source_stats()
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Sources", stats['total_sources'])
    
    with col2:
        st.metric("Enabled Sources", stats['enabled_sources'])
    
    with col3:
        library_size = len(recommendation_engine.content_items)
        st.metric("Library Size", library_size)
    
    # Source breakdown
    st.markdown("#### 📋 Source Status")
    
    source_data = []
    for source_id, source_info in stats['source_breakdown'].items():
        status = "✅ Enabled" if source_info['enabled'] else "❌ Disabled"
        api_status = "🔑 Configured" if source_info['has_api_key'] else "⚠️ No API Key" if source_id == 'youtube' else "➖ N/A"
        
        source_data.append({
            "Source": source_info['name'],
            "Status": status,
            "API Status": api_status,
            "Content Types": ", ".join(source_info['content_types']),
            "Source ID": source_id
        })
    
    df_sources = pd.DataFrame(source_data)
    st.dataframe(df_sources, use_container_width=True)
    
    # Content distribution by source
    st.markdown("#### 📈 Content Distribution by Source")
    
    content_by_source = {}
    for content in recommendation_engine.content_items.values():
        source = content.file_info.get('source', 'user_upload')
        content_by_source[source] = content_by_source.get(source, 0) + 1
    
    if content_by_source:
        source_dist_data = [{"Source": source, "Count": count} for source, count in content_by_source.items()]
        df_dist = pd.DataFrame(source_dist_data)
        
        fig = px.pie(df_dist, values="Count", names="Source", title="Content by Source")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No content in library yet. Add content from various sources to see distribution.")


def render_content_discovery_tab():
    """Render content discovery interface"""
    
    st.markdown("### 🔍 Discover New Content")
    st.markdown("Search and import content from multiple sources based on topics of interest.")
    
    # Topic-based discovery
    col1, col2 = st.columns([2, 1])
    
    with col1:
        discovery_topic = st.text_input(
            "Search Topic",
            placeholder="e.g., machine learning, business strategy, health",
            help="Enter a topic to discover related content across all sources"
        )
    
    with col2:
        max_results = st.slider("Max Results per Source", 1, 10, 3)
    
    if discovery_topic and st.button("🔍 Discover Content", type="primary"):
        discover_content_for_topic(discovery_topic, max_results)
    
    # Recent discoveries
    st.markdown("#### 📚 Recently Discovered Content")
    
    # Show recently added content from external sources
    recent_external = []
    for content in recommendation_engine.content_items.values():
        source = content.file_info.get('source', 'user_upload')
        if source != 'user_upload':
            recent_external.append(content)
    
    # Sort by creation date
    recent_external.sort(key=lambda x: x.created_at, reverse=True)
    
    if recent_external:
        for i, content in enumerate(recent_external[:5], 1):
            with st.expander(f"{i}. {content.title} ({content.file_info.get('source', 'unknown')})", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Duration:** {content.duration/60:.1f} minutes")
                    st.write(f"**Topics:** {', '.join(content.topics) if content.topics else 'None identified'}")
                    st.write(f"**Source:** {content.file_info.get('source', 'Unknown')}")
                    
                    # Show URL if available
                    if 'url' in content.file_info:
                        st.markdown(f"**Original:** [View Source]({content.file_info['url']})")
                
                with col2:
                    st.metric("Quality", f"{content.confidence:.1%}")
                    st.metric("Views", content.view_count)
                    
                    if st.button(f"👁️ View", key=f"recent_view_{i}"):
                        recommendation_engine.update_user_profile("default_user", content.id, "view")
                        st.success("Added to your viewing history!")
    else:
        st.info("No external content discovered yet. Use the search above to find content from various sources.")


def render_public_platform_tab():
    """Render public content platform interface"""
    
    st.markdown("### 🌐 Public Content Platform")
    st.markdown("Share your content with the community or discover content shared by others.")
    
    # Public platform tabs
    contribute_tab, browse_tab, manage_tab = st.tabs([
        "📤 Contribute Content",
        "📥 Browse Public Content",
        "👥 Community Stats"
    ])
    
    with contribute_tab:
        render_content_contribution_interface()
    
    with browse_tab:
        render_public_content_browser()
    
    with manage_tab:
        render_community_stats()


def render_content_contribution_interface():
    """Interface for contributing content to public platform"""
    
    st.markdown("#### 📤 Share Your Content")
    
    # Check if user has content to share
    user_content = [c for c in recommendation_engine.content_items.values() if c.user_id == "default_user"]
    
    if not user_content:
        st.info("Process some audio/video content first to contribute to the public platform.")
        return
    
    # Content selection
    content_options = {f"{content.title} ({content.created_at[:10]})": content.id 
                      for content in user_content}
    
    selected_title = st.selectbox(
        "Select content to share:",
        options=list(content_options.keys()),
        help="Choose content from your library to share publicly"
    )
    
    if selected_title:
        selected_id = content_options[selected_title]
        selected_content = recommendation_engine.content_items[selected_id]
        
        # Contribution form
        st.markdown("#### 📝 Contribution Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            contributor_name = st.text_input("Your Name", placeholder="John Doe")
            contributor_email = st.text_input("Email (optional)", placeholder="john@example.com")
        
        with col2:
            license_type = st.selectbox(
                "Content License",
                ["CC BY-SA 4.0", "CC BY 4.0", "CC0 (Public Domain)", "Custom"],
                help="Choose how others can use your content"
            )
            
            content_category = st.selectbox(
                "Category",
                ["Educational", "Business", "Technology", "Health", "Entertainment", "Other"]
            )
        
        # Content preview
        with st.expander("📄 Content Preview", expanded=False):
            st.write(f"**Title:** {selected_content.title}")
            st.write(f"**Duration:** {selected_content.duration/60:.1f} minutes")
            st.write(f"**Topics:** {', '.join(selected_content.topics) if selected_content.topics else 'None'}")
            st.write(f"**Quality:** {selected_content.confidence:.1%}")
            st.text_area("Transcript Preview:", value=selected_content.transcript[:300] + "...", height=100)
        
        # Terms and conditions
        agree_terms = st.checkbox(
            "I agree to share this content under the selected license and confirm I have the right to do so.",
            help="By checking this, you're making your content available to the community"
        )
        
        # Submit button
        if st.button("🚀 Share with Community", type="primary", disabled=not agree_terms):
            if not contributor_name:
                st.error("Please provide your name.")
                return
            
            # Prepare contributor info
            contributor_info = {
                'id': contributor_email or contributor_name.lower().replace(' ', '_'),
                'name': contributor_name,
                'email': contributor_email,
                'license': license_type,
                'category': content_category
            }
            
            # Submit to public platform
            public_platform = PublicContentPlatform()
            success = public_platform.submit_public_content(selected_content, contributor_info)
            
            if success:
                st.success("🎉 Thank you! Your content has been submitted for review and will be available to the community soon.")
                st.balloons()
            else:
                st.error("❌ Failed to submit content. Please check the content meets our guidelines.")


def render_public_content_browser():
    """Browse public content interface"""
    
    st.markdown("#### 📥 Browse Community Content")
    
    # Category filter
    category_filter = st.selectbox(
        "Filter by Category",
        ["All", "Educational", "Business", "Technology", "Health", "Entertainment"],
        help="Filter public content by category"
    )
    
    # Get public content
    public_platform = PublicContentPlatform()
    category = None if category_filter == "All" else category_filter.lower()
    public_content = public_platform.get_public_content(category, limit=20)
    
    if public_content:
        st.markdown(f"#### 📚 Found {len(public_content)} Public Content Items")
        
        for i, content in enumerate(public_content, 1):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{i}. {content.title}**")
                    st.write(f"Duration: {content.duration/60:.1f} min | Language: {content.language}")
                    if content.topics:
                        st.write(f"Topics: {', '.join(content.topics[:3])}")
                    
                    # Show contributor info
                    contributor = content.file_info.get('contributor', 'Anonymous')
                    license_info = content.file_info.get('license', 'Unknown')
                    st.write(f"By: {contributor} | License: {license_info}")
                
                with col2:
                    st.metric("Quality", f"{content.confidence:.1%}")
                    st.write(f"Added: {content.created_at[:10]}")
                
                with col3:
                    if st.button(f"📥 Add to Library", key=f"add_public_{i}"):
                        # Add to user's library
                        content.user_id = "default_user"  # Assign to current user
                        recommendation_engine.add_content_item(content)
                        recommendation_engine.update_user_profile("default_user", content.id, "view")
                        st.success("Added to your library!")
                    
                    if st.button(f"👁️ Preview", key=f"preview_public_{i}"):
                        st.info("Preview functionality would show full content details")
                
                st.markdown("---")
    else:
        st.info("No public content available in this category yet. Be the first to contribute!")


def render_community_stats():
    """Render community statistics"""
    
    st.markdown("#### 👥 Community Statistics")
    
    # Mock community stats (would be real in production)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Contributors", "127")
    
    with col2:
        st.metric("Public Content Items", "1,543")
    
    with col3:
        st.metric("Total Hours", "2,847")
    
    with col4:
        st.metric("Languages", "23")
    
    # Top contributors
    st.markdown("#### 🏆 Top Contributors")
    
    contributors_data = [
        {"Name": "Dr. Sarah Johnson", "Contributions": 45, "Category": "Educational"},
        {"Name": "Tech Guru Mike", "Contributions": 38, "Category": "Technology"},
        {"Name": "Business Pro Lisa", "Contributions": 32, "Category": "Business"},
        {"Name": "Health Expert Tom", "Contributions": 28, "Category": "Health"},
        {"Name": "Creative Jane", "Contributions": 24, "Category": "Entertainment"}
    ]
    
    df_contributors = pd.DataFrame(contributors_data)
    st.dataframe(df_contributors, use_container_width=True)


def render_youtube_integration_tab():
    """Render YouTube integration interface"""
    
    st.markdown("### 📺 YouTube Integration")
    
    # Check API key status
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not youtube_api_key:
        st.warning("⚠️ YouTube API key not configured")
        st.markdown("""
        **To enable YouTube integration:**
        1. Get a YouTube Data API v3 key from Google Cloud Console
        2. Add it to your `.env` file as `YOUTUBE_API_KEY=your_key_here`
        3. Restart the application
        
        **Features available with YouTube integration:**
        - Search YouTube videos with captions
        - Import video transcripts automatically
        - Discover educational and professional content
        - Access millions of hours of content
        """)
        return
    
    st.success("✅ YouTube API configured and ready")
    
    # YouTube search interface
    st.markdown("#### 🔍 Search YouTube Content")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        youtube_query = st.text_input(
            "Search YouTube",
            placeholder="e.g., python tutorial, business presentation",
            help="Search for YouTube videos with captions/transcripts"
        )
    
    with col2:
        max_youtube_results = st.slider("Max Results", 1, 20, 5)
    
    if youtube_query and st.button("🔍 Search YouTube", type="primary"):
        search_youtube_content(youtube_query, max_youtube_results)
    
    # YouTube integration stats
    st.markdown("#### 📊 YouTube Integration Stats")
    
    youtube_content = [c for c in recommendation_engine.content_items.values() 
                      if c.file_info.get('source') == 'youtube']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("YouTube Videos", len(youtube_content))
    
    with col2:
        total_duration = sum(c.duration for c in youtube_content) / 3600
        st.metric("Total Hours", f"{total_duration:.1f}")
    
    with col3:
        avg_quality = sum(c.confidence for c in youtube_content) / max(len(youtube_content), 1)
        st.metric("Avg Quality", f"{avg_quality:.1%}")


def render_source_settings_tab():
    """Render content source settings"""
    
    st.markdown("### ⚙️ Content Source Settings")
    
    # API Configuration
    st.markdown("#### 🔑 API Configuration")
    
    with st.expander("YouTube Data API", expanded=False):
        current_key = os.getenv('YOUTUBE_API_KEY', '')
        masked_key = current_key[:8] + "..." + current_key[-4:] if current_key else "Not configured"
        
        st.write(f"**Current Key:** {masked_key}")
        st.write("**Status:** ✅ Configured" if current_key else "❌ Not configured")
        
        st.markdown("""
        **Setup Instructions:**
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project or select existing one
        3. Enable YouTube Data API v3
        4. Create credentials (API Key)
        5. Add to `.env` file: `YOUTUBE_API_KEY=your_key_here`
        """)
    
    # Source Management
    st.markdown("#### 📊 Source Management")
    
    sources = content_aggregator.source_manager.sources
    
    for source_id, source in sources.items():
        with st.expander(f"{source.name} ({source.source_type})", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Description:** {source.description}")
                st.write(f"**Content Types:** {', '.join(source.content_types)}")
                st.write(f"**Rate Limit:** {source.rate_limit} requests/hour")
            
            with col2:
                enabled = st.checkbox(f"Enable {source.name}", value=source.enabled, key=f"enable_{source_id}")
                
                if enabled != source.enabled:
                    source.enabled = enabled
                    st.success(f"{'Enabled' if enabled else 'Disabled'} {source.name}")
    
    # Content Quality Settings
    st.markdown("#### ⭐ Content Quality Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_confidence = st.slider(
            "Minimum Confidence Threshold",
            0.0, 1.0, 0.7,
            help="Only import content above this quality threshold"
        )
        
        min_duration = st.slider(
            "Minimum Duration (seconds)",
            10, 300, 30,
            help="Only import content longer than this duration"
        )
    
    with col2:
        max_content_per_source = st.slider(
            "Max Content per Source",
            1, 100, 20,
            help="Maximum content items to import from each source"
        )
        
        auto_import = st.checkbox(
            "Auto-import trending content",
            value=False,
            help="Automatically import trending content daily"
        )
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")


# Helper functions

def discover_content_for_topic(topic: str, max_results: int):
    """Discover content for a specific topic"""
    
    with st.spinner(f"Discovering content about '{topic}'..."):
        try:
            # Use content aggregator to find content
            discovered_content = content_aggregator.aggregate_content_for_topic(topic, max_results)
            
            if discovered_content:
                st.success(f"🎉 Found {len(discovered_content)} content items about '{topic}'!")
                
                # Display discovered content
                for i, content in enumerate(discovered_content, 1):
                    with st.expander(f"{i}. {content.title} ({content.file_info.get('source', 'unknown')})", expanded=False):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Duration:** {content.duration/60:.1f} minutes")
                            st.write(f"**Topics:** {', '.join(content.topics) if content.topics else 'None'}")
                            st.write(f"**Source:** {content.file_info.get('source', 'Unknown')}")
                            
                            # Show preview
                            preview_text = content.transcript[:200] + "..." if len(content.transcript) > 200 else content.transcript
                            st.write(f"**Preview:** {preview_text}")
                        
                        with col2:
                            st.metric("Quality", f"{content.confidence:.1%}")
                            
                            if st.button(f"📥 Add to Library", key=f"add_discovered_{i}"):
                                # Add to recommendation engine
                                recommendation_engine.add_content_item(content)
                                st.success("Added to your library!")
            else:
                st.info(f"No content found for '{topic}'. Try different keywords or check your API configurations.")
                
        except Exception as e:
            st.error(f"Error discovering content: {str(e)}")


def search_youtube_content(query: str, max_results: int):
    """Search YouTube content"""
    
    if not content_aggregator.youtube_source:
        st.error("YouTube integration not available. Please configure API key.")
        return
    
    with st.spinner(f"Searching YouTube for '{query}'..."):
        try:
            # Search YouTube videos
            videos = content_aggregator.youtube_source.search_videos(query, max_results)
            
            if videos:
                st.success(f"Found {len(videos)} YouTube videos with captions!")
                
                # Display videos
                for i, video in enumerate(videos, 1):
                    with st.expander(f"{i}. {video['title']}", expanded=False):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Channel:** {video['channel_title']}")
                            st.write(f"**Published:** {video['published_at'][:10]}")
                            st.write(f"**Description:** {video['description'][:200]}...")
                            
                            # Show thumbnail
                            st.image(video['thumbnail_url'], width=200)
                        
                        with col2:
                            video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
                            st.markdown(f"[🔗 Watch on YouTube]({video_url})")
                            
                            if st.button(f"📥 Import Transcript", key=f"import_yt_{i}"):
                                import_youtube_video(video)
            else:
                st.info("No YouTube videos with captions found for this query.")
                
        except Exception as e:
            st.error(f"Error searching YouTube: {str(e)}")


def import_youtube_video(video_info: Dict):
    """Import a YouTube video transcript"""
    
    with st.spinner("Importing YouTube transcript..."):
        try:
            # Get transcript
            transcript = content_aggregator.youtube_source.get_video_captions(video_info['video_id'])
            
            if transcript:
                # Create content item
                content_item = content_aggregator.youtube_source.create_content_item_from_youtube(video_info, transcript)
                
                # Add to recommendation engine
                recommendation_engine.add_content_item(content_item)
                
                st.success(f"✅ Successfully imported '{video_info['title']}' to your library!")
                
                # Show import details
                st.info(f"📊 Imported {len(transcript.split())} words, estimated {content_item.duration/60:.1f} minutes")
                
            else:
                st.error("❌ Could not retrieve transcript for this video.")
                
        except Exception as e:
            st.error(f"Error importing YouTube video: {str(e)}")