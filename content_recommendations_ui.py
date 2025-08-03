#!/usr/bin/env python3
"""
Smart Content Recommendations UI (Task 42)
User interface for content recommendations, trending topics, and content discovery
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json

from content_recommendations import (
    recommendation_engine, ContentItem, UserProfile,
    create_content_item_from_session
)
from session_manager import session_manager

def render_content_recommendations_interface():
    """Main interface for content recommendations"""
    
    st.markdown("## 🎯 Smart Content Recommendations")
    st.markdown("Discover similar content, get personalized suggestions, and explore trending topics.")
    
    # Create tabs for different recommendation features
    similar_tab, personalized_tab, trending_tab, gaps_tab, stats_tab = st.tabs([
        "🔍 Similar Content",
        "👤 For You",
        "📈 Trending",
        "🎯 Content Gaps",
        "📊 Library Stats"
    ])
    
    with similar_tab:
        render_similar_content_tab()
    
    with personalized_tab:
        render_personalized_recommendations_tab()
    
    with trending_tab:
        render_trending_content_tab()
    
    with gaps_tab:
        render_content_gaps_tab()
    
    with stats_tab:
        render_library_stats_tab()


def render_similar_content_tab():
    """Render similar content recommendations"""
    
    st.markdown("### 🔍 Find Similar Content")
    
    # Add current session to recommendations if available
    if session_manager.has_results():
        if st.button("📝 Add Current Session to Library"):
            add_current_session_to_library()
    
    # Get available content
    content_items = recommendation_engine.content_items
    
    if not content_items:
        st.info("No content in library yet. Process some audio/video files to build your content library.")
        return
    
    # Content selection
    content_options = {f"{item.title} ({item.created_at[:10]})": item.id 
                      for item in content_items.values()}
    
    selected_title = st.selectbox(
        "Select content to find similar items:",
        options=list(content_options.keys()),
        help="Choose a content item to find similar content"
    )
    
    if selected_title:
        selected_id = content_options[selected_title]
        selected_content = content_items[selected_id]
        
        # Display selected content info
        with st.expander("📄 Selected Content Details", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Duration", f"{selected_content.duration/60:.1f} min")
            
            with col2:
                st.metric("Confidence", f"{selected_content.confidence:.1%}")
            
            with col3:
                st.metric("Views", selected_content.view_count)
            
            st.markdown("**Topics:**")
            if selected_content.topics:
                st.write(", ".join(selected_content.topics))
            else:
                st.write("No topics identified")
            
            st.markdown("**Tags:**")
            if selected_content.tags:
                st.write(", ".join(selected_content.tags))
            else:
                st.write("No tags available")
            
            st.text_area("Transcript Preview:", value=selected_content.transcript[:300] + "...", height=100)
        
        # Find similar content
        similar_items = recommendation_engine.get_similar_content(selected_id, limit=10)
        
        if similar_items:
            st.markdown("### 🎯 Similar Content Found")
            
            for i, (similar_content, similarity_score) in enumerate(similar_items, 1):
                with st.expander(f"#{i} {similar_content.title} (Similarity: {similarity_score:.2f})", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Duration:** {similar_content.duration/60:.1f} minutes")
                        st.write(f"**Created:** {similar_content.created_at[:10]}")
                        st.write(f"**Topics:** {', '.join(similar_content.topics) if similar_content.topics else 'None'}")
                        st.text_area(f"Preview {i}:", value=similar_content.transcript[:200] + "...", height=80, key=f"preview_{i}")
                    
                    with col2:
                        st.metric("Similarity", f"{similarity_score:.1%}")
                        st.metric("Confidence", f"{similar_content.confidence:.1%}")
                        st.metric("Views", similar_content.view_count)
                        
                        if st.button(f"👁️ View Details", key=f"view_{i}"):
                            # Update user profile for interaction tracking
                            recommendation_engine.update_user_profile("default_user", similar_content.id, "view")
                            st.success(f"Viewing {similar_content.title}")
        else:
            st.info("No similar content found. Try adding more content to your library.")


def render_personalized_recommendations_tab():
    """Render personalized recommendations"""
    
    st.markdown("### 👤 Personalized Recommendations")
    
    # User profile section
    user_id = st.text_input("User ID", value="default_user", help="Enter your user ID for personalized recommendations")
    
    # Display user profile if exists
    if user_id in recommendation_engine.user_profiles:
        profile = recommendation_engine.user_profiles[user_id]
        
        with st.expander("👤 Your Profile", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Your Interests:**")
                if profile.interests:
                    for topic, score in sorted(profile.interests.items(), key=lambda x: x[1], reverse=True)[:10]:
                        st.write(f"• {topic}: {score:.1%}")
                else:
                    st.write("No interests identified yet")
            
            with col2:
                st.markdown("**Viewing History:**")
                st.write(f"Total items viewed: {len(profile.viewing_history)}")
                st.write(f"Preferred languages: {', '.join(profile.preferred_languages)}")
                st.write(f"Profile created: {profile.created_at[:10]}")
    else:
        st.info(f"No profile found for user '{user_id}'. Interact with content to build your profile.")
    
    # Get personalized recommendations
    recommendations = recommendation_engine.get_personalized_recommendations(user_id, limit=15)
    
    if recommendations:
        st.markdown("### 🎯 Recommended For You")
        
        # Display recommendations in a nice format
        for i, (content, score) in enumerate(recommendations, 1):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{i}. {content.title}**")
                    st.write(f"Duration: {content.duration/60:.1f} min | Created: {content.created_at[:10]}")
                    if content.topics:
                        st.write(f"Topics: {', '.join(content.topics[:3])}")
                    st.write(content.transcript[:150] + "...")
                
                with col2:
                    st.metric("Match Score", f"{score:.1%}")
                    st.metric("Quality", f"{content.confidence:.1%}")
                
                with col3:
                    if st.button(f"👁️ View", key=f"rec_view_{i}"):
                        recommendation_engine.update_user_profile(user_id, content.id, "view")
                        st.success("Added to your viewing history!")
                    
                    if st.button(f"👍 Like", key=f"rec_like_{i}"):
                        # Boost interest in content topics
                        if user_id not in recommendation_engine.user_profiles:
                            recommendation_engine.user_profiles[user_id] = UserProfile(
                                user_id=user_id,
                                interests={},
                                viewing_history=[],
                                search_history=[],
                                preferred_languages=["en"],
                                preferred_duration_range=(0.0, 3600.0),
                                created_at=datetime.now().isoformat(),
                                last_updated=datetime.now().isoformat()
                            )
                        
                        profile = recommendation_engine.user_profiles[user_id]
                        for topic in content.topics:
                            current_score = profile.interests.get(topic, 0.0)
                            profile.interests[topic] = min(1.0, current_score + 0.2)
                        
                        recommendation_engine.save_data()
                        st.success("Thanks for the feedback!")
                
                st.markdown("---")
    else:
        st.info("No personalized recommendations available. View some content to get personalized suggestions.")


def render_trending_content_tab():
    """Render trending content"""
    
    st.markdown("### 📈 Trending Content")
    
    # Time window selection
    time_window = st.selectbox(
        "Trending Period",
        options=[1, 3, 7, 14, 30],
        index=2,
        format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}",
        help="Select the time period for trending analysis"
    )
    
    # Get trending content
    trending_items = recommendation_engine.get_trending_content(limit=20, time_window_days=time_window)
    
    if trending_items:
        st.markdown(f"### 🔥 Trending in Last {time_window} Day{'s' if time_window > 1 else ''}")
        
        # Create trending chart
        if len(trending_items) > 1:
            trending_data = []
            for content, score in trending_items[:10]:
                trending_data.append({
                    "Title": content.title[:30] + "..." if len(content.title) > 30 else content.title,
                    "Trending Score": score,
                    "Views": content.view_count,
                    "Duration (min)": content.duration / 60
                })
            
            df = pd.DataFrame(trending_data)
            
            if not df.empty:
                fig = px.bar(
                    df, 
                    x="Trending Score", 
                    y="Title",
                    orientation='h',
                    title=f"Top Trending Content (Last {time_window} Days)",
                    color="Views",
                    color_continuous_scale="viridis"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Display trending items
        for i, (content, trending_score) in enumerate(trending_items, 1):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**#{i} {content.title}**")
                    st.write(f"Duration: {content.duration/60:.1f} min | Views: {content.view_count}")
                    if content.topics:
                        st.write(f"Topics: {', '.join(content.topics[:3])}")
                    
                    # Show last accessed if available
                    if content.last_accessed:
                        last_access = datetime.fromisoformat(content.last_accessed)
                        days_ago = (datetime.now() - last_access).days
                        st.write(f"Last viewed: {days_ago} day{'s' if days_ago != 1 else ''} ago")
                
                with col2:
                    st.metric("Trending Score", f"{trending_score:.1f}")
                    st.metric("Quality", f"{content.confidence:.1%}")
                
                with col3:
                    if st.button(f"👁️ View", key=f"trend_view_{i}"):
                        recommendation_engine.update_user_profile("default_user", content.id, "view")
                        st.success("Viewing trending content!")
                
                st.markdown("---")
    else:
        st.info("No trending content available. Add more content and interactions to see trends.")


def render_content_gaps_tab():
    """Render content gap analysis"""
    
    st.markdown("### 🎯 Content Gap Analysis")
    st.markdown("Discover what topics and content types are missing from your library.")
    
    # Perform gap analysis
    gap_analysis = recommendation_engine.analyze_content_gaps()
    
    if gap_analysis["total_content"] == 0:
        st.info("No content in library yet. Add some content to perform gap analysis.")
        return
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Topics", gap_analysis["total_topics"])
    
    with col2:
        st.metric("Total Content", gap_analysis["total_content"])
    
    with col3:
        st.metric("Avg Topics/Content", f"{gap_analysis['average_topics_per_content']:.1f}")
    
    # Underrepresented topics
    st.markdown("#### 📉 Underrepresented Topics")
    
    underrepresented = gap_analysis["underrepresented_topics"]
    
    if underrepresented:
        # Create visualization
        under_data = []
        for topic_info in underrepresented[:10]:
            under_data.append({
                "Topic": topic_info["topic"],
                "Coverage %": topic_info["coverage_ratio"] * 100,
                "Content Count": topic_info["current_count"],
                "Priority": topic_info["suggested_priority"]
            })
        
        df_under = pd.DataFrame(under_data)
        
        if not df_under.empty:
            fig = px.bar(
                df_under,
                x="Coverage %",
                y="Topic",
                orientation='h',
                color="Priority",
                color_discrete_map={"high": "red", "medium": "orange", "low": "green"},
                title="Topics with Low Coverage"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Display recommendations
        st.markdown("**📝 Content Creation Suggestions:**")
        
        for topic_info in underrepresented[:5]:
            priority_color = "🔴" if topic_info["suggested_priority"] == "high" else "🟡"
            st.write(f"{priority_color} **{topic_info['topic']}** - Only {topic_info['current_count']} content items ({topic_info['coverage_ratio']:.1%} coverage)")
    else:
        st.success("✅ All topics are well represented in your content library!")
    
    # Missing trending topics
    st.markdown("#### 🔥 Missing Trending Topics")
    
    missing_trends = gap_analysis["missing_trending_topics"]
    
    if missing_trends:
        st.markdown("**🎯 Trending Topics You Should Cover:**")
        
        for i, trend_info in enumerate(missing_trends[:10], 1):
            priority_color = "🔴" if trend_info["suggested_priority"] == "high" else "🟡"
            st.write(f"{i}. {priority_color} **{trend_info['keyword']}** (Trend Score: {trend_info['trend_score']:.2f})")
        
        # Create trending topics chart
        trend_data = []
        for trend_info in missing_trends[:8]:
            trend_data.append({
                "Keyword": trend_info["keyword"],
                "Trend Score": trend_info["trend_score"],
                "Priority": trend_info["suggested_priority"]
            })
        
        df_trends = pd.DataFrame(trend_data)
        
        if not df_trends.empty:
            fig = px.bar(
                df_trends,
                x="Trend Score",
                y="Keyword",
                orientation='h',
                color="Priority",
                color_discrete_map={"high": "red", "medium": "orange"},
                title="Missing Trending Keywords"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("✅ You're covering all the trending topics!")
    
    # Content creation suggestions
    st.markdown("#### 💡 Content Creation Ideas")
    
    if underrepresented or missing_trends:
        st.markdown("**Based on the analysis, consider creating content about:**")
        
        suggestions = []
        
        # Add high-priority underrepresented topics
        for topic_info in underrepresented[:3]:
            if topic_info["suggested_priority"] == "high":
                suggestions.append(f"More content about **{topic_info['topic']}** (currently only {topic_info['coverage_ratio']:.1%} coverage)")
        
        # Add trending topics
        for trend_info in missing_trends[:3]:
            suggestions.append(f"Content featuring **{trend_info['keyword']}** (trending keyword)")
        
        for suggestion in suggestions:
            st.write(f"• {suggestion}")
    else:
        st.success("🎉 Your content library has excellent topic coverage!")


def render_library_stats_tab():
    """Render content library statistics"""
    
    st.markdown("### 📊 Content Library Statistics")
    
    # Get library stats
    stats = recommendation_engine.get_content_stats()
    
    if stats["total_content"] == 0:
        st.info("No content in library yet. Process some audio/video files to see statistics.")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Content", stats["total_content"])
    
    with col2:
        st.metric("Total Hours", f"{stats['total_duration_hours']:.1f}")
    
    with col3:
        st.metric("Avg Duration", f"{stats['average_duration_minutes']:.1f} min")
    
    with col4:
        st.metric("Total Users", stats["total_users"])
    
    # Language distribution
    st.markdown("#### 🌍 Language Distribution")
    
    if stats["language_distribution"]:
        lang_data = []
        for lang, count in stats["language_distribution"].items():
            lang_data.append({"Language": lang, "Count": count})
        
        df_lang = pd.DataFrame(lang_data)
        
        fig = px.pie(
            df_lang,
            values="Count",
            names="Language",
            title="Content by Language"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Topic distribution
    st.markdown("#### 🏷️ Topic Distribution")
    
    if stats["top_topics"]:
        topic_data = []
        for topic, count in list(stats["top_topics"].items())[:10]:
            topic_data.append({"Topic": topic, "Count": count})
        
        df_topics = pd.DataFrame(topic_data)
        
        fig = px.bar(
            df_topics,
            x="Count",
            y="Topic",
            orientation='h',
            title="Top 10 Topics"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Quality distribution
    st.markdown("#### ⭐ Quality Distribution")
    
    quality_data = []
    for quality, count in stats["quality_distribution"].items():
        quality_data.append({"Quality": quality.title(), "Count": count})
    
    df_quality = pd.DataFrame(quality_data)
    
    fig = px.bar(
        df_quality,
        x="Quality",
        y="Count",
        color="Quality",
        color_discrete_map={"High": "green", "Medium": "orange", "Low": "red"},
        title="Content Quality Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.markdown("#### 📈 Recent Activity")
    
    content_items = list(recommendation_engine.content_items.values())
    
    if content_items:
        # Sort by creation date
        content_items.sort(key=lambda x: x.created_at, reverse=True)
        
        st.markdown("**Recently Added Content:**")
        
        for i, content in enumerate(content_items[:5], 1):
            created_date = datetime.fromisoformat(content.created_at)
            days_ago = (datetime.now() - created_date).days
            
            st.write(f"{i}. **{content.title}** - {days_ago} day{'s' if days_ago != 1 else ''} ago ({content.view_count} views)")
    
    # User engagement
    if stats["total_users"] > 0:
        st.markdown("#### 👥 User Engagement")
        
        total_views = sum(content.view_count for content in recommendation_engine.content_items.values())
        avg_views_per_content = total_views / max(stats["total_content"], 1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Views", total_views)
        
        with col2:
            st.metric("Avg Views/Content", f"{avg_views_per_content:.1f}")


def add_current_session_to_library():
    """Add current session results to the recommendation library"""
    
    if not session_manager.has_results():
        st.error("No session results available to add.")
        return
    
    try:
        # Get current session results
        results = session_manager.get_results()
        
        # Create content item
        content_item = create_content_item_from_session(results, "default_user")
        
        # Generate smart tags
        content_item.tags = recommendation_engine.generate_smart_tags(content_item)
        
        # Add to recommendation engine
        recommendation_engine.add_content_item(content_item)
        
        # Update user profile
        recommendation_engine.update_user_profile("default_user", content_item.id, "view")
        
        st.success(f"✅ Added '{content_item.title}' to your content library!")
        st.info(f"Generated {len(content_item.tags)} smart tags: {', '.join(content_item.tags[:5])}...")
        
    except Exception as e:
        st.error(f"Error adding content to library: {str(e)}")


def render_smart_tagging_interface():
    """Render smart tagging interface for content"""
    
    st.markdown("### 🏷️ Smart Content Tagging")
    
    if not session_manager.has_results():
        st.info("Process some audio/video content first to generate smart tags.")
        return
    
    results = session_manager.get_results()
    
    # Create temporary content item for tag generation
    temp_content = create_content_item_from_session(results)
    
    # Generate smart tags
    if st.button("🎯 Generate Smart Tags"):
        with st.spinner("Generating smart tags..."):
            smart_tags = recommendation_engine.generate_smart_tags(temp_content)
            
            st.success(f"Generated {len(smart_tags)} smart tags!")
            
            # Display tags by category
            tag_categories = {
                "Content Type": [tag for tag in smart_tags if tag.startswith("type:")],
                "Topics": [tag for tag in smart_tags if tag.startswith("topic:")],
                "People": [tag for tag in smart_tags if tag.startswith("person:")],
                "Organizations": [tag for tag in smart_tags if tag.startswith("organization:")],
                "Locations": [tag for tag in smart_tags if tag.startswith("location:")],
                "Attributes": [tag for tag in smart_tags if not any(tag.startswith(prefix) for prefix in ["type:", "topic:", "person:", "organization:", "location:"])]
            }
            
            for category, tags in tag_categories.items():
                if tags:
                    st.markdown(f"**{category}:**")
                    for tag in tags:
                        # Clean up tag display
                        display_tag = tag.split(":", 1)[1] if ":" in tag else tag
                        st.write(f"• {display_tag}")
            
            # Option to add to library with these tags
            if st.button("📚 Add to Library with These Tags"):
                temp_content.tags = smart_tags
                recommendation_engine.add_content_item(temp_content)
                recommendation_engine.update_user_profile("default_user", temp_content.id, "view")
                st.success("Content added to library with smart tags!")