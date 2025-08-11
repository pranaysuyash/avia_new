!")
        st.rerun()

def main():
    """Main application with enterprise-grade UI"""
    # Get selected page from sidebar
    selected_page = render_enterprise_sidebar()
    
    # Route to appropriate page
    if selected_page == "dashboard":
        render_dashboard()
    elif selected_page == "upload":
        render_upload_interface()
    elif selected_page == "transcriptions":
        render_transcriptions_page()
    elif selected_page == "analysis":
        render_ai_analysis_page()
    elif selected_page == "team":
        render_team_page()
    elif selected_page == "settings":
        render_settings_page()

def render_transcriptions_page():
    """Render transcriptions management page"""
    ui.create_header(
        "Transcription Library",
        "Browse and manage all your transcribed content",
        "📚"
    )
    
    # Search and filters
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search transcriptions...", placeholder="Enter keywords, file names, or dates")
    
    with col2:
        filter_status = st.selectbox("Status", ["All", "Completed", "Processing", "Failed"])
    
    with col3:
        filter_date = st.selectbox("Date", ["All Time", "Today", "This Week", "This Month"])
    
    with col4:
        sort_by = st.selectbox("Sort By", ["Latest", "Oldest", "Name", "Size"])
    
    # Transcriptions table
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Mock data for demonstration
    transcriptions = [
        {
            "id": 1,
            "name": "Q4_Earnings_Call.mp4",
            "date": "2024-01-15 14:30",
            "duration": "45:32",
            "status": "completed",
            "accuracy": 98.5,
            "size": "256 MB"
        },
        {
            "id": 2,
            "name": "Product_Demo_2024.mp4",
            "date": "2024-01-15 10:15",
            "duration": "23:15",
            "status": "processing",
            "accuracy": 0,
            "size": "128 MB"
        },
        {
            "id": 3,
            "name": "Customer_Interview.wav",
            "date": "2024-01-14 16:45",
            "duration": "18:45",
            "status": "completed",
            "accuracy": 97.2,
            "size": "89 MB"
        }
    ]
    
    # Table header
    cols = st.columns([3, 2, 2, 2, 2, 1])
    with cols[0]:
        st.markdown("**File Name**")
    with cols[1]:
        st.markdown("**Date**")
    with cols[2]:
        st.markdown("**Duration**")
    with cols[3]:
        st.markdown("**Status**")
    with cols[4]:
        st.markdown("**Accuracy**")
    with cols[5]:
        st.markdown("**Actions**")
    
    st.markdown("---")
    
    # Table rows
    for trans in transcriptions:
        cols = st.columns([3, 2, 2, 2, 2, 1])
        
        with cols[0]:
            st.markdown(f"📄 {trans['name']}")
        
        with cols[1]:
            st.markdown(f"<small>{trans['date']}</small>", unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown(f"<small>{trans['duration']}</small>", unsafe_allow_html=True)
        
        with cols[3]:
            status_color = "success" if trans['status'] == "completed" else "warning"
            st.markdown(f"""
            <span class='status-badge {status_color}'>
                {trans['status'].upper()}
            </span>
            """, unsafe_allow_html=True)
        
        with cols[4]:
            if trans['accuracy'] > 0:
                st.markdown(f"<small>{trans['accuracy']}%</small>", unsafe_allow_html=True)
            else:
                st.markdown("<small>-</small>", unsafe_allow_html=True)
        
        with cols[5]:
            if st.button("👁️", key=f"view_{trans['id']}", help="View details"):
                st.session_state.selected_transcription = trans['id']

def render_ai_analysis_page():
    """Render AI analysis page"""
    ui.create_header(
        "AI Analysis Suite",
        "Advanced artificial intelligence tools for content analysis",
        "🧠"
    )
    
    # Analysis tools grid
    analysis_tools = [
        {
            "icon": "🎯",
            "title": "Entity Recognition",
            "description": "Extract names, organizations, dates, and locations from your content"
        },
        {
            "icon": "💭",
            "title": "Sentiment Analysis",
            "description": "Understand emotional tone and sentiment trends in conversations"
        },
        {
            "icon": "📊",
            "title": "Topic Modeling",
            "description": "Discover key topics and themes in your transcribed content"
        },
        {
            "icon": "🔍",
            "title": "Keyword Extraction",
            "description": "Identify important keywords and phrases automatically"
        },
        {
            "icon": "📈",
            "title": "Trend Analysis",
            "description": "Track patterns and trends across multiple transcriptions"
        },
        {
            "icon": "🤖",
            "title": "Custom Models",
            "description": "Train and deploy custom AI models for specific use cases"
        }
    ]
    
    st.markdown(ui.create_feature_grid(analysis_tools), unsafe_allow_html=True)
    
    # Quick analysis section
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 🚀 Quick Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        analysis_text = st.text_area(
            "Enter text for analysis",
            placeholder="Paste your text here for instant AI analysis...",
            height=150
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🧠 Analyze", use_container_width=True, type="primary"):
            if analysis_text:
                with st.spinner("Analyzing..."):
                    time.sleep(1)
                    st.success("Analysis complete!")
                    
                    # Mock results
                    st.markdown("""
                    <div class='enterprise-card'>
                        <h4>📊 Results</h4>
                        <p><strong>Sentiment:</strong> Positive (85%)</p>
                        <p><strong>Key Topics:</strong> Business, Technology, Innovation</p>
                        <p><strong>Entities:</strong> 3 people, 2 organizations</p>
                    </div>
                    """, unsafe_allow_html=True)

def render_team_page():
    """Render team collaboration page"""
    ui.create_header(
        "Team Workspace",
        "Collaborate with your team on transcription projects",
        "👥"
    )
    
    # Team stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(ui.create_metric_card(
            "Team Members",
            "12",
            "",
            "👤",
            "primary"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(ui.create_metric_card(
            "Active Projects",
            "5",
            "+2",
            "📁",
            "accent"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(ui.create_metric_card(
            "Shared Files",
            "234",
            "+15",
            "📄",
            "secondary"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(ui.create_metric_card(
            "Collaborations",
            "48",
            "+8",
            "🤝",
            "primary"
        ), unsafe_allow_html=True)
    
    # Team members
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 👥 Team Members")
    
    members = [
        {"name": "John Doe", "role": "Admin", "status": "Active", "projects": 8},
        {"name": "Jane Smith", "role": "Editor", "status": "Active", "projects": 5},
        {"name": "Mike Johnson", "role": "Viewer", "status": "Away", "projects": 3},
        {"name": "Sarah Williams", "role": "Editor", "status": "Active", "projects": 6}
    ]
    
    cols = st.columns(4)
    for i, member in enumerate(members):
        with cols[i % 4]:
            status_color = "#10B981" if member["status"] == "Active" else "#F59E0B"
            st.markdown(f"""
            <div class='enterprise-card' style='text-align: center;'>
                <div style='
                    width: 60px;
                    height: 60px;
                    border-radius: 30px;
                    background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 12px;
                    font-weight: 700;
                    font-size: 20px;
                '>{member['name'][0]}{member['name'].split()[1][0]}</div>
                <h4 style='margin: 0;'>{member['name']}</h4>
                <p style='color: #6B7280; margin: 4px 0;'>{member['role']}</p>
                <p style='color: {status_color}; font-size: 12px;'>● {member['status']}</p>
                <p style='color: #6B7280; font-size: 12px;'>{member['projects']} projects</p>
            </div>
            """, unsafe_allow_html=True)

def render_settings_page():
    """Render settings page"""
    ui.create_header(
        "Settings",
        "Configure your application preferences and integrations",
        "⚙️"
    )
    
    # Settings tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔑 API Keys", "🎨 Appearance", "🔔 Notifications", "🔒 Security", "🔗 Integrations"])
    
    with tab1:
        st.markdown("### API Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
            st.caption("Required for advanced AI features")
        
        with col2:
            elevenlabs_key = st.text_input("ElevenLabs API Key", type="password", placeholder="...")
            st.caption("Required for text-to-speech features")
        
        if st.button("💾 Save API Keys", type="primary"):
            st.success("API keys saved successfully!")
    
    with tab2:
        st.markdown("### Theme Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            theme_mode = st.radio("Color Mode", ["☀️ Light", "🌙 Dark", "🔄 Auto"])
            accent_color = st.selectbox("Accent Color", ["Blue", "Purple", "Green", "Orange"])
        
        with col2:
            font_size = st.select_slider("Font Size", ["Small", "Medium", "Large"])
            enable_animations = st.checkbox("Enable Animations", value=True)
        
        if st.button("💾 Save Appearance Settings", type="primary"):
            st.success("Appearance settings saved!")
    
    with tab3:
        st.markdown("### Notification Preferences")
        
        st.checkbox("Email notifications for completed transcriptions", value=True)
        st.checkbox("Browser push notifications", value=False)
        st.checkbox("Weekly summary reports", value=True)
        st.checkbox("System maintenance alerts", value=True)
        
        notification_email = st.text_input("Notification Email", placeholder="user@example.com")
        
        if st.button("💾 Save Notification Settings", type="primary"):
            st.success("Notification settings saved!")
    
    with tab4:
        st.markdown("### Security Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Two-factor authentication", value=False)
            st.checkbox("Session timeout (30 min)", value=True)
            st.checkbox("IP whitelisting", value=False)
        
        with col2:
            st.checkbox("Encrypt stored files", value=True)
            st.checkbox("Audit logging", value=True)
            st.checkbox("GDPR compliance mode", value=False)
        
        if st.button("💾 Save Security Settings", type="primary"):
            st.success("Security settings saved!")
    
    with tab5:
        st.markdown("### Third-party Integrations")
        
        integrations = [
            {"name": "Slack", "icon": "💬", "status": "Connected"},
            {"name": "Google Drive", "icon": "📁", "status": "Not Connected"},
            {"name": "Dropbox", "icon": "📦", "status": "Not Connected"},
            {"name": "Microsoft Teams", "icon": "👥", "status": "Connected"},
            {"name": "Zoom", "icon": "🎥", "status": "Not Connected"},
            {"name": "Salesforce", "icon": "☁️", "status": "Not Connected"}
        ]
        
        cols = st.columns(3)
        for i, integration in enumerate(integrations):
            with cols[i % 3]:
                status_color = "#10B981" if integration["status"] == "Connected" else "#6B7280"
                st.markdown(f"""
                <div class='enterprise-card'>
                    <div style='display: flex; align-items: center; justify-content: space-between;'>
                        <div style='display: flex; align-items: center; gap: 12px;'>
                            <span style='font-size: 24px;'>{integration['icon']}</span>
                            <div>
                                <div style='font-weight: 600;'>{integration['name']}</div>
                                <div style='color: {status_color}; font-size: 12px;'>{integration['status']}</div>
                            </div>
                        </div>
                        <button style='
                            background: {"#EF4444" if integration["status"] == "Connected" else "#10B981"};
                            color: white;
                            border: none;
                            padding: 4px 12px;
                            border-radius: 6px;
                            font-size: 12px;
                            cursor: pointer;
                        '>{"Disconnect" if integration["status"] == "Connected" else "Connect"}</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
