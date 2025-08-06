"""
Customer Support System UI
Streamlit interface for comprehensive customer support features.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any

from customer_support_system import (
    CustomerSupportSystem,
    TicketStatus,
    TicketPriority,
    ArticleCategory,
    TutorialType
)

# Page configuration
st.set_page_config(
    page_title="Customer Support Center",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize support system
if 'support_system' not in st.session_state:
    st.session_state.support_system = CustomerSupportSystem()

if 'chat_session_id' not in st.session_state:
    st.session_state.chat_session_id = None

def main():
    """Main application"""
    st.title("🎧 Video NER Support Center")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        [
            "Dashboard",
            "Support Tickets",
            "Live Chat",
            "Help Center",
            "Tutorials",
            "Community Forum",
            "Feedback & Features",
            "FAQ",
            "Contact Support"
        ]
    )
    
    # User info (mock)
    st.sidebar.divider()
    st.sidebar.subheader("User Info")
    user_id = st.sidebar.text_input("User ID", value="user123", key="user_id")
    
    # Route to appropriate page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Support Tickets":
        show_support_tickets(user_id)
    elif page == "Live Chat":
        show_live_chat(user_id)
    elif page == "Help Center":
        show_help_center()
    elif page == "Tutorials":
        show_tutorials()
    elif page == "Community Forum":
        show_community_forum(user_id)
    elif page == "Feedback & Features":
        show_feedback_features(user_id)
    elif page == "FAQ":
        show_faq()
    elif page == "Contact Support":
        show_contact_support(user_id)

def show_dashboard():
    """Show support dashboard"""
    st.header("Support Dashboard")
    
    support_system = st.session_state.support_system
    dashboard_data = support_system.get_support_dashboard()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Open Tickets",
            dashboard_data["tickets"]["open_tickets"],
            delta=f"{dashboard_data['tickets']['total_tickets']} total"
        )
    
    with col2:
        avg_resolution = dashboard_data["tickets"]["avg_resolution_time_hours"]
        st.metric(
            "Avg Resolution Time",
            f"{avg_resolution:.1f}h" if avg_resolution > 0 else "N/A",
            delta="Target: 24h"
        )
    
    with col3:
        satisfaction = dashboard_data["tickets"]["satisfaction_score"]
        st.metric(
            "Satisfaction Score",
            f"{satisfaction:.1f}/5" if satisfaction > 0 else "N/A",
            delta="+0.2 this month"
        )
    
    with col4:
        st.metric(
            "Active Forum Posts",
            dashboard_data["forum"]["total_posts"],
            delta=f"{dashboard_data['forum']['active_users']} active users"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ticket Status Distribution")
        if dashboard_data["tickets"]["status_distribution"]:
            fig = px.pie(
                values=list(dashboard_data["tickets"]["status_distribution"].values()),
                names=list(dashboard_data["tickets"]["status_distribution"].keys()),
                color_discrete_map={
                    "open": "#ff4b4b",
                    "in_progress": "#ffa500",
                    "waiting_customer": "#ffeb3b",
                    "resolved": "#4caf50",
                    "closed": "#9e9e9e"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tickets yet")
    
    with col2:
        st.subheader("Feedback Categories")
        if dashboard_data["feedback"]["category_distribution"]:
            fig = px.bar(
                x=list(dashboard_data["feedback"]["category_distribution"].keys()),
                y=list(dashboard_data["feedback"]["category_distribution"].values()),
                labels={"x": "Category", "y": "Count"}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No feedback yet")
    
    # Resources overview
    st.subheader("Support Resources")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info(f"📚 **{dashboard_data['help_articles']['total']}** Help Articles")
        st.caption(f"{dashboard_data['help_articles']['faq_items']} FAQ items")
    
    with col2:
        st.info(f"🎥 **{dashboard_data['tutorials']['total']}** Tutorials")
        st.caption(f"{dashboard_data['tutorials']['learning_paths']} learning paths")
    
    with col3:
        st.info(f"💬 **{dashboard_data['chat_sessions']}** Chat Sessions")
        st.caption("AI-powered support")
    
    with col4:
        st.info(f"✨ **{dashboard_data['feedback']['total_feature_requests']}** Feature Requests")
        st.caption(f"Avg rating: {dashboard_data['feedback']['average_rating']:.1f}/5")
    
    # Trending feature requests
    if dashboard_data["feedback"]["trending_features"]:
        st.subheader("Trending Feature Requests")
        for feature in dashboard_data["feedback"]["trending_features"][:3]:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{feature['title']}**")
                st.caption(feature['description'][:100] + "...")
            with col2:
                st.metric("Upvotes", feature['upvotes'])

def show_support_tickets(user_id: str):
    """Show support tickets interface"""
    st.header("Support Tickets")
    
    support_system = st.session_state.support_system
    
    tab1, tab2, tab3 = st.tabs(["Create Ticket", "My Tickets", "Ticket Management"])
    
    with tab1:
        st.subheader("Create New Ticket")
        
        col1, col2 = st.columns(2)
        
        with col1:
            subject = st.text_input("Subject")
            category = st.selectbox(
                "Category",
                ["technical", "billing", "feature_request", "account", "other"]
            )
            priority = st.selectbox(
                "Priority",
                ["", "low", "medium", "high", "urgent"],
                help="Leave blank for auto-detection"
            )
        
        with col2:
            description = st.text_area("Description", height=150)
            
            # File attachment (mock)
            uploaded_file = st.file_uploader("Attach file (optional)")
        
        if st.button("Submit Ticket", type="primary"):
            if subject and description:
                # Create ticket
                ticket_priority = TicketPriority[priority.upper()] if priority else None
                
                ticket = support_system.ticket_manager.create_ticket(
                    user_id=user_id,
                    subject=subject,
                    description=description,
                    category=category,
                    priority=ticket_priority,
                    attachments=[{"name": uploaded_file.name, "size": uploaded_file.size}] if uploaded_file else None
                )
                
                st.success(f"✅ Ticket created: {ticket.id}")
                st.info(f"Priority: {ticket.priority.value}")
                st.balloons()
            else:
                st.error("Please fill in all required fields")
    
    with tab2:
        st.subheader("My Tickets")
        
        # Get user's tickets
        user_tickets = [
            t for t in support_system.ticket_manager.tickets.values()
            if t.user_id == user_id
        ]
        
        if user_tickets:
            # Display tickets
            for ticket in sorted(user_tickets, key=lambda t: t.created_at, reverse=True):
                with st.expander(f"{ticket.id} - {ticket.subject}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Status:** {ticket.status.value}")
                        st.write(f"**Priority:** {ticket.priority.value}")
                    
                    with col2:
                        st.write(f"**Category:** {ticket.category}")
                        st.write(f"**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M')}")
                    
                    with col3:
                        if ticket.resolved_at:
                            st.write(f"**Resolved:** {ticket.resolved_at.strftime('%Y-%m-%d %H:%M')}")
                        if ticket.satisfaction_rating:
                            st.write(f"**Rating:** {'⭐' * ticket.satisfaction_rating}")
                    
                    st.divider()
                    
                    # Conversation history
                    st.write("**Conversation:**")
                    for msg in ticket.conversation:
                        if msg["type"] == "customer":
                            st.write(f"🧑 **You:** {msg['message']}")
                        elif msg["type"] == "agent":
                            st.write(f"🎧 **Support:** {msg['message']}")
                        else:
                            st.caption(f"ℹ️ {msg['message']}")
                    
                    # Add reply
                    if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                        reply = st.text_area(f"Add reply to {ticket.id}", key=f"reply_{ticket.id}")
                        if st.button(f"Send Reply", key=f"send_{ticket.id}"):
                            if reply:
                                support_system.ticket_manager.add_reply(
                                    ticket.id, reply, is_agent=False
                                )
                                st.success("Reply sent!")
                                st.rerun()
        else:
            st.info("You have no support tickets yet")
    
    with tab3:
        st.subheader("Ticket Management")
        
        # Show all tickets (admin view)
        all_tickets = list(support_system.ticket_manager.tickets.values())
        
        if all_tickets:
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_status = st.multiselect(
                    "Status Filter",
                    [s.value for s in TicketStatus],
                    default=["open", "in_progress"]
                )
            with col2:
                filter_priority = st.multiselect(
                    "Priority Filter",
                    [p.value for p in TicketPriority]
                )
            with col3:
                filter_category = st.multiselect(
                    "Category Filter",
                    ["technical", "billing", "feature_request", "account", "other"]
                )
            
            # Filter tickets
            filtered_tickets = all_tickets
            if filter_status:
                filtered_tickets = [t for t in filtered_tickets if t.status.value in filter_status]
            if filter_priority:
                filtered_tickets = [t for t in filtered_tickets if t.priority.value in filter_priority]
            if filter_category:
                filtered_tickets = [t for t in filtered_tickets if t.category in filter_category]
            
            # Display as table
            if filtered_tickets:
                df = pd.DataFrame([
                    {
                        "ID": t.id,
                        "Subject": t.subject[:50] + "..." if len(t.subject) > 50 else t.subject,
                        "Status": t.status.value,
                        "Priority": t.priority.value,
                        "Category": t.category,
                        "Created": t.created_at.strftime('%Y-%m-%d %H:%M'),
                        "User": t.user_id
                    }
                    for t in filtered_tickets
                ])
                
                st.dataframe(df, use_container_width=True)
                
                # Metrics
                metrics = support_system.ticket_manager.get_ticket_metrics()
                st.write(f"**Average Resolution Time:** {metrics['avg_resolution_time_hours']:.1f} hours")
            else:
                st.info("No tickets match the selected filters")
        else:
            st.info("No tickets in the system yet")

def show_live_chat(user_id: str):
    """Show live chat interface"""
    st.header("Live Chat Support")
    
    support_system = st.session_state.support_system
    
    # Start chat session if not exists
    if st.session_state.chat_session_id is None:
        st.session_state.chat_session_id = support_system.chat_support.start_chat_session(user_id)
    
    # Chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat history
        chat_container = st.container()
        
        with chat_container:
            if st.session_state.chat_session_id in support_system.chat_support.chat_sessions:
                messages = support_system.chat_support.chat_sessions[st.session_state.chat_session_id]
                
                for msg in messages:
                    if msg["role"] == "assistant":
                        st.chat_message("assistant").write(msg["message"])
                        
                        # Show suggested articles if any
                        if "suggested_articles" in msg and msg["suggested_articles"]:
                            with st.expander("📚 Suggested Articles"):
                                for article in msg["suggested_articles"]:
                                    st.write(f"- [{article['title']}]({article['url']})")
                    else:
                        st.chat_message("user").write(msg["message"])
        
        # Chat input
        user_message = st.chat_input("Type your message...")
        
        if user_message:
            # Process message
            response = support_system.chat_support.process_message(
                st.session_state.chat_session_id,
                user_message
            )
            
            # Check if escalated
            if response.get("escalated"):
                if response.get("agent_available"):
                    st.info("🎧 Connecting you to a live agent...")
                else:
                    st.warning("⏰ Our agents are currently offline. Creating a support ticket...")
                    
                    # Create ticket
                    ticket = support_system.ticket_manager.create_ticket(
                        user_id=user_id,
                        subject="Chat escalation request",
                        description=f"User requested human support. Last message: {user_message}",
                        category="chat_escalation"
                    )
                    st.success(f"Ticket created: {ticket.id}")
            
            st.rerun()
    
    with col2:
        st.subheader("Quick Actions")
        
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state.chat_session_id = support_system.chat_support.start_chat_session(user_id)
            st.rerun()
        
        if st.button("📧 Email Transcript", use_container_width=True):
            st.info("Chat transcript sent to your email!")
        
        st.divider()
        
        st.subheader("Common Topics")
        topics = ["Transcription Help", "Billing Questions", "Technical Issues", "Feature Requests"]
        
        for topic in topics:
            if st.button(topic, use_container_width=True, key=f"topic_{topic}"):
                support_system.chat_support.process_message(
                    st.session_state.chat_session_id,
                    f"I need help with {topic.lower()}"
                )
                st.rerun()

def show_help_center():
    """Show help center with articles"""
    st.header("Help Center")
    
    support_system = st.session_state.support_system
    
    # Search bar
    search_query = st.text_input("🔍 Search help articles...", placeholder="Enter keywords...")
    
    # Category filter
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        selected_category = st.selectbox(
            "Category",
            ["All"] + [cat.value for cat in ArticleCategory]
        )
    
    # Get articles
    if search_query:
        articles = support_system.help_docs.search_articles(search_query)
    else:
        articles = list(support_system.help_docs.articles.values())
    
    # Filter by category
    if selected_category != "All":
        articles = [a for a in articles if a.category.value == selected_category]
    
    # Display articles
    if articles:
        for article in articles:
            with st.expander(f"📄 {article.title}"):
                # Article metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"Category: {article.category.value}")
                with col2:
                    st.caption(f"Views: {article.views}")
                with col3:
                    helpfulness = 0
                    if article.helpful_count + article.not_helpful_count > 0:
                        helpfulness = article.helpful_count / (article.helpful_count + article.not_helpful_count) * 100
                    st.caption(f"Helpful: {helpfulness:.0f}%")
                
                st.divider()
                
                # Article content
                st.markdown(article.content)
                
                # Feedback
                st.divider()
                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    if st.button("👍 Helpful", key=f"helpful_{article.id}"):
                        support_system.help_docs.mark_article_helpful(article.id, True)
                        st.success("Thanks for your feedback!")
                with col2:
                    if st.button("👎 Not Helpful", key=f"not_helpful_{article.id}"):
                        support_system.help_docs.mark_article_helpful(article.id, False)
                        st.info("We'll work on improving this article")
                
                # Related articles
                if article.related_articles:
                    st.caption("**Related Articles:**")
                    for related_id in article.related_articles:
                        if related_id in support_system.help_docs.articles:
                            related = support_system.help_docs.articles[related_id]
                            st.write(f"- {related.title}")
    else:
        st.info("No articles found. Try different search terms.")
    
    # Popular articles sidebar
    with st.sidebar:
        st.subheader("Popular Articles")
        
        # Get top articles by views
        top_articles = sorted(
            support_system.help_docs.articles.values(),
            key=lambda a: a.views,
            reverse=True
        )[:5]
        
        for article in top_articles:
            if st.button(article.title, key=f"popular_{article.id}"):
                st.session_state.selected_article = article.id

def show_tutorials():
    """Show tutorials and learning paths"""
    st.header("Video Tutorials & Guides")
    
    support_system = st.session_state.support_system
    
    # User type selection for learning path
    col1, col2 = st.columns([1, 3])
    with col1:
        user_type = st.selectbox(
            "I am a...",
            ["beginner", "developer", "power_user"]
        )
    
    # Show recommended learning path
    st.subheader(f"Recommended Learning Path for {user_type.replace('_', ' ').title()}")
    
    learning_path = support_system.tutorials.get_learning_path(user_type)
    
    if learning_path:
        for i, tutorial in enumerate(learning_path):
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.write(f"**Step {i+1}**")
                
                # Tutorial type icon
                if tutorial.type == TutorialType.VIDEO:
                    st.write("🎥 Video")
                elif tutorial.type == TutorialType.INTERACTIVE:
                    st.write("🖱️ Interactive")
                else:
                    st.write("📄 Article")
            
            with col2:
                st.write(f"**{tutorial.title}**")
                st.caption(tutorial.description)
                st.write(f"⏱️ {tutorial.duration_minutes} minutes | 🎯 {tutorial.difficulty}")
                
                # Learning objectives
                with st.expander("Learning Objectives"):
                    for obj in tutorial.learning_objectives:
                        st.write(f"✓ {obj}")
            
            with col3:
                if st.button("Start Tutorial", key=f"start_{tutorial.id}"):
                    st.info(f"Opening tutorial: {tutorial.content_url}")
                    
                    # Track view
                    tutorial.views += 1
    
    st.divider()
    
    # All tutorials
    st.subheader("All Tutorials")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox(
            "Type",
            ["All"] + [t.value for t in TutorialType]
        )
    with col2:
        filter_difficulty = st.selectbox(
            "Difficulty",
            ["All", "beginner", "intermediate", "advanced"]
        )
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest", "Most Popular", "Highest Rated", "Duration"]
        )
    
    # Get and filter tutorials
    tutorials = list(support_system.tutorials.tutorials.values())
    
    if filter_type != "All":
        tutorials = [t for t in tutorials if t.type.value == filter_type]
    
    if filter_difficulty != "All":
        tutorials = [t for t in tutorials if t.difficulty == filter_difficulty]
    
    # Sort tutorials
    if sort_by == "Newest":
        tutorials.sort(key=lambda t: t.created_at, reverse=True)
    elif sort_by == "Most Popular":
        tutorials.sort(key=lambda t: t.views, reverse=True)
    elif sort_by == "Highest Rated":
        tutorials.sort(key=lambda t: t.rating, reverse=True)
    elif sort_by == "Duration":
        tutorials.sort(key=lambda t: t.duration_minutes)
    
    # Display tutorials grid
    for i in range(0, len(tutorials), 3):
        cols = st.columns(3)
        
        for j, col in enumerate(cols):
            if i + j < len(tutorials):
                tutorial = tutorials[i + j]
                
                with col:
                    # Tutorial card
                    st.write(f"**{tutorial.title}**")
                    st.caption(f"{tutorial.type.value} • {tutorial.duration_minutes} min")
                    st.write(tutorial.description[:100] + "...")
                    
                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Views", tutorial.views)
                    with col2:
                        st.metric("Rating", f"{tutorial.rating:.1f}⭐" if tutorial.rating > 0 else "N/A")
                    with col3:
                        st.metric("Completed", f"{tutorial.completion_rate:.0f}%")
                    
                    if st.button("Watch Now", key=f"watch_{tutorial.id}", use_container_width=True):
                        st.info(f"Opening: {tutorial.content_url}")

def show_community_forum(user_id: str):
    """Show community forum"""
    st.header("Community Forum")
    
    support_system = st.session_state.support_system
    
    tab1, tab2, tab3 = st.tabs(["Browse Posts", "Create Post", "My Activity"])
    
    with tab1:
        # Search and filters
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_query = st.text_input("Search forum...", placeholder="Search posts...")
        with col2:
            filter_category = st.selectbox(
                "Category",
                ["All"] + support_system.forum.categories
            )
        with col3:
            show_solved_only = st.checkbox("Solved only")
        
        # Get posts
        if search_query:
            posts = support_system.forum.search_posts(
                search_query,
                category=filter_category if filter_category != "All" else None,
                solved_only=show_solved_only
            )
        else:
            posts = list(support_system.forum.posts.values())
            if filter_category != "All":
                posts = [p for p in posts if p.category == filter_category]
            if show_solved_only:
                posts = [p for p in posts if p.is_solved]
        
        # Display posts
        if posts:
            for post in sorted(posts, key=lambda p: p.created_at, reverse=True):
                with st.expander(
                    f"{'✅' if post.is_solved else '❓'} {post.title} - "
                    f"{post.category} ({len(post.replies)} replies)"
                ):
                    # Post header
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Author:** {post.author_id}")
                        st.write(f"**Posted:** {post.created_at.strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Tags:** {', '.join(post.tags)}")
                    with col2:
                        st.metric("Views", post.views)
                        st.metric("Upvotes", post.upvotes)
                    
                    st.divider()
                    
                    # Post content
                    st.write(post.content)
                    
                    # Upvote button
                    if st.button(f"👍 Upvote ({post.upvotes})", key=f"upvote_{post.id}"):
                        support_system.forum.upvote_post(post.id, user_id)
                        st.success("Upvoted!")
                        st.rerun()
                    
                    # Replies
                    if post.replies:
                        st.divider()
                        st.write(f"**Replies ({len(post.replies)}):**")
                        
                        for reply in post.replies:
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                st.write(f"**{reply['author_id']}:** {reply['content']}")
                                if reply["id"] == post.accepted_answer_id:
                                    st.success("✅ Accepted Answer")
                            with col2:
                                st.caption(f"👍 {reply['upvotes']}")
                    
                    # Add reply
                    reply_content = st.text_area(f"Add reply to {post.id}", key=f"forum_reply_{post.id}")
                    if st.button("Post Reply", key=f"post_reply_{post.id}"):
                        if reply_content:
                            support_system.forum.add_reply(post.id, user_id, reply_content)
                            st.success("Reply posted!")
                            st.rerun()
        else:
            st.info("No forum posts found")
    
    with tab2:
        st.subheader("Create New Post")
        
        title = st.text_input("Post Title")
        category = st.selectbox("Category", support_system.forum.categories)
        content = st.text_area("Content", height=200)
        tags = st.text_input("Tags (comma-separated)")
        
        if st.button("Create Post", type="primary"):
            if title and content:
                post = support_system.forum.create_post(
                    author_id=user_id,
                    title=title,
                    content=content,
                    category=category,
                    tags=[tag.strip() for tag in tags.split(",")] if tags else []
                )
                st.success(f"Post created: {post.title}")
                st.balloons()
            else:
                st.error("Please fill in all required fields")
    
    with tab3:
        st.subheader("My Forum Activity")
        
        # User stats
        col1, col2, col3 = st.columns(3)
        with col1:
            user_posts = [p for p in support_system.forum.posts.values() if p.author_id == user_id]
            st.metric("My Posts", len(user_posts))
        with col2:
            st.metric("Reputation", support_system.forum.user_reputation.get(user_id, 0))
        with col3:
            total_upvotes = sum(p.upvotes for p in user_posts)
            st.metric("Total Upvotes", total_upvotes)
        
        # My posts
        if user_posts:
            st.write("**My Recent Posts:**")
            for post in sorted(user_posts, key=lambda p: p.created_at, reverse=True)[:5]:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{'✅' if post.is_solved else '❓'} {post.title}")
                with col2:
                    st.caption(f"{len(post.replies)} replies")
                with col3:
                    st.caption(f"👍 {post.upvotes}")

def show_feedback_features(user_id: str):
    """Show feedback and feature request interface"""
    st.header("Feedback & Feature Requests")
    
    support_system = st.session_state.support_system
    
    tab1, tab2, tab3 = st.tabs(["Submit Feedback", "Feature Requests", "My Feedback"])
    
    with tab1:
        st.subheader("Submit Feedback")
        
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox(
                "Feedback Category",
                support_system.feedback.feedback_categories
            )
            subject = st.text_input("Subject")
        
        with col2:
            rating = st.slider("Overall Rating", 1, 5, 3)
            description = st.text_area("Description", height=150)
        
        if st.button("Submit Feedback", type="primary"):
            if subject and description:
                feedback_id = support_system.feedback.submit_feedback(
                    user_id=user_id,
                    category=category,
                    subject=subject,
                    description=description,
                    rating=rating
                )
                st.success("Thank you for your feedback!")
                
                if category == "Feature Request":
                    st.info("Your feature request has been added to our roadmap consideration")
            else:
                st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Feature Requests")
        
        # Trending features
        trending_features = support_system.feedback.get_trending_features(10)
        
        if trending_features:
            st.write("**🔥 Trending Feature Requests:**")
            
            for feature in trending_features:
                with st.expander(f"{feature['title']} ({feature['upvotes']} upvotes)"):
                    st.write(feature['description'])
                    st.write(f"**Status:** {feature['status']}")
                    st.write(f"**Tags:** {', '.join(feature['tags'])}")
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button(f"👍 Upvote", key=f"upvote_feature_{feature['id']}"):
                            support_system.feedback.upvote_feature_request(feature['id'], user_id)
                            st.success("Upvoted!")
                            st.rerun()
                    
                    # Comments
                    if feature['comments']:
                        st.divider()
                        st.write("**Comments:**")
                        for comment in feature['comments'][-3:]:  # Show last 3 comments
                            st.write(f"💬 {comment}")
        else:
            st.info("No feature requests yet")
        
        # Submit new feature request
        st.divider()
        st.write("**Submit New Feature Request:**")
        
        new_title = st.text_input("Feature Title", key="new_feature_title")
        new_description = st.text_area("Feature Description", key="new_feature_desc")
        
        if st.button("Submit Feature Request"):
            if new_title and new_description:
                request_id = support_system.feedback.create_feature_request(
                    user_id, new_title, new_description
                )
                st.success("Feature request submitted!")
                st.rerun()
    
    with tab3:
        st.subheader("My Feedback History")
        
        # Get user's feedback
        user_feedback = [
            f for f in support_system.feedback.feedback_items
            if f["user_id"] == user_id
        ]
        
        if user_feedback:
            for feedback in sorted(user_feedback, key=lambda f: f["created_at"], reverse=True):
                with st.expander(f"{feedback['subject']} - {feedback['category']}"):
                    st.write(feedback['description'])
                    if feedback['rating']:
                        st.write(f"**Rating:** {'⭐' * feedback['rating']}")
                    st.write(f"**Status:** {feedback['status']}")
                    st.caption(f"Submitted: {feedback['created_at']}")
        else:
            st.info("You haven't submitted any feedback yet")

def show_faq():
    """Show FAQ section"""
    st.header("Frequently Asked Questions")
    
    support_system = st.session_state.support_system
    
    # Category filter
    categories = list(set(faq["category"] for faq in support_system.help_docs.faq_items))
    selected_category = st.selectbox("Filter by category", ["All"] + categories)
    
    # Display FAQ items
    faq_items = support_system.help_docs.faq_items
    if selected_category != "All":
        faq_items = [faq for faq in faq_items if faq["category"] == selected_category]
    
    for i, faq in enumerate(faq_items):
        with st.expander(f"❓ {faq['question']}"):
            st.write(faq['answer'])
            st.caption(f"Category: {faq['category']}")
            
            # Helpful feedback
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("👍 Helpful", key=f"faq_helpful_{i}"):
                    st.success("Thanks!")
            with col2:
                if st.button("👎 Not helpful", key=f"faq_not_helpful_{i}"):
                    st.info("We'll improve this answer")

def show_contact_support(user_id: str):
    """Show contact support options"""
    st.header("Contact Support")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📧 Email Support")
        st.write("For non-urgent inquiries")
        st.info("support@vidner.com")
        st.caption("Response time: 24-48 hours")
        
        if st.button("Compose Email", use_container_width=True):
            st.info("Opening email client...")
    
    with col2:
        st.subheader("💬 Live Chat")
        st.write("For immediate assistance")
        st.info("Available 9 AM - 6 PM EST")
        st.caption("Average wait time: 2 minutes")
        
        if st.button("Start Live Chat", use_container_width=True):
            st.switch_page("pages/Live_Chat.py")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📞 Phone Support")
        st.write("For urgent issues")
        st.info("+1 (555) 123-4567")
        st.caption("Business hours: 9 AM - 6 PM EST")
    
    with col2:
        st.subheader("🎫 Support Ticket")
        st.write("Track your issue")
        st.info("Average resolution: 24 hours")
        st.caption("Get email updates")
        
        if st.button("Create Ticket", use_container_width=True):
            st.switch_page("pages/Support_Tickets.py")
    
    st.divider()
    
    # Business hours
    st.subheader("Business Hours")
    
    hours = {
        "Monday - Friday": "9:00 AM - 6:00 PM EST",
        "Saturday": "10:00 AM - 4:00 PM EST",
        "Sunday": "Closed"
    }
    
    for day, time in hours.items():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"**{day}:**")
        with col2:
            st.write(time)
    
    # Emergency support
    st.divider()
    st.subheader("🚨 Emergency Support")
    st.warning(
        "For critical production issues outside business hours, "
        "please call our emergency hotline: **+1 (555) 999-8888**"
    )
    st.caption("Emergency support is available 24/7 for Enterprise customers only")

if __name__ == "__main__":
    main()