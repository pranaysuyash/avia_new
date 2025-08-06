"""
Marketing and Growth Features UI
Streamlit interface for managing referral programs, affiliate marketing, social sharing, and A/B testing
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from marketing_growth_system import MarketingGrowthSystem, CampaignType, ABTestStatus

def init_marketing_system():
    """Initialize the marketing system"""
    if 'marketing_system' not in st.session_state:
        st.session_state.marketing_system = MarketingGrowthSystem()
    return st.session_state.marketing_system

def render_referral_program_management():
    """Render referral program management interface"""
    st.header("🎯 Referral Program Management")
    
    marketing = init_marketing_system()
    
    # Create new referral program
    with st.expander("Create New Referral Program", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            program_name = st.text_input("Program Name", placeholder="Launch Referral Program")
            reward_type = st.selectbox("Reward Type", ["credit", "discount", "cash"])
            reward_amount = st.number_input("Reward Amount ($)", min_value=0.0, value=25.0)
            
        with col2:
            referrer_reward = st.number_input("Referrer Reward ($)", min_value=0.0, value=25.0)
            referee_reward = st.number_input("Referee Reward ($)", min_value=0.0, value=25.0)
            minimum_spend = st.number_input("Minimum Spend ($)", min_value=0.0, value=50.0)
        
        expiry_days = st.number_input("Expiry Days", min_value=1, value=60)
        terms_conditions = st.text_area("Terms & Conditions", 
                                       placeholder="Enter terms and conditions...")
        
        if st.button("Create Referral Program"):
            if program_name:
                program_id = marketing.create_referral_program(
                    name=program_name,
                    reward_type=reward_type,
                    reward_amount=reward_amount,
                    referrer_reward=referrer_reward,
                    referee_reward=referee_reward,
                    minimum_spend=minimum_spend,
                    expiry_days=expiry_days,
                    terms_conditions=terms_conditions
                )
                st.success(f"✅ Created referral program: {program_name}")
                st.info(f"Program ID: {program_id}")
            else:
                st.error("Please enter a program name")
    
    # Referral code generator
    st.subheader("Generate Referral Codes")
    col1, col2 = st.columns(2)
    
    with col1:
        user_id = st.text_input("User ID", placeholder="user123")
        program_id = st.text_input("Program ID", placeholder="Enter program ID")
    
    with col2:
        if st.button("Generate Referral Code"):
            if user_id and program_id:
                try:
                    referral_code = marketing.generate_referral_code(program_id, user_id)
                    st.success(f"🎫 Generated referral code: **{referral_code}**")
                    
                    # Show shareable link
                    base_url = "https://transcription-app.com"
                    share_link = f"{base_url}/signup?ref={referral_code}"
                    st.code(share_link, language="text")
                    
                except Exception as e:
                    st.error(f"Error generating referral code: {str(e)}")
            else:
                st.error("Please enter both User ID and Program ID")
    
    # Referral analytics
    st.subheader("📊 Referral Analytics")
    analytics = marketing.get_referral_analytics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Referrals", analytics["total_referrals"])
    with col2:
        st.metric("Completed Referrals", analytics["completed_referrals"])
    with col3:
        st.metric("Conversion Rate", f"{analytics['conversion_rate']:.1f}%")
    with col4:
        st.metric("Avg Conversion Days", f"{analytics['avg_conversion_days']:.1f}")

def render_affiliate_marketing():
    """Render affiliate marketing interface"""
    st.header("🤝 Affiliate Marketing")
    
    marketing = init_marketing_system()
    
    # Create new affiliate partner
    with st.expander("Add New Affiliate Partner", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            partner_name = st.text_input("Partner Name", placeholder="Tech Blogger")
            partner_email = st.text_input("Email", placeholder="partner@example.com")
            
        with col2:
            commission_rate = st.number_input("Commission Rate (%)", min_value=0.0, max_value=50.0, value=15.0)
            payment_method = st.selectbox("Payment Method", ["paypal", "bank_transfer", "check"])
        
        if st.button("Add Affiliate Partner"):
            if partner_name and partner_email:
                partner_id = marketing.create_affiliate_partner(
                    name=partner_name,
                    email=partner_email,
                    commission_rate=commission_rate,
                    payment_method=payment_method
                )
                if partner_id:
                    st.success(f"✅ Added affiliate partner: {partner_name}")
                    st.info(f"Partner ID: {partner_id}")
                else:
                    st.error("Failed to create affiliate partner (email may already exist)")
            else:
                st.error("Please enter partner name and email")
    
    # Track affiliate conversion
    st.subheader("Track Affiliate Conversion")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tracking_code = st.text_input("Tracking Code", placeholder="AFF_12345678")
    with col2:
        conversion_value = st.number_input("Conversion Value ($)", min_value=0.0, value=100.0)
    with col3:
        user_id = st.text_input("User ID", placeholder="user456")
    
    if st.button("Track Conversion"):
        if tracking_code and user_id:
            success = marketing.track_affiliate_conversion(tracking_code, conversion_value, user_id)
            if success:
                st.success(f"✅ Tracked conversion: ${conversion_value} via {tracking_code}")
            else:
                st.error("Failed to track conversion (invalid tracking code or partner not approved)")
        else:
            st.error("Please enter tracking code and user ID")
    
    # Affiliate analytics
    st.subheader("📊 Affiliate Analytics")
    analytics = marketing.get_affiliate_analytics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Partners", analytics["total_partners"])
    with col2:
        st.metric("Active Partners", analytics["active_partners"])
    with col3:
        st.metric("Total Earnings", f"${analytics['total_earnings']:.2f}")
    with col4:
        st.metric("Avg Earnings/Partner", f"${analytics['avg_earnings_per_partner']:.2f}")

def render_social_sharing():
    """Render social sharing interface"""
    st.header("📱 Social Sharing")
    
    marketing = init_marketing_system()
    
    # Create social share template
    with st.expander("Create Social Share Template", expanded=False):
        platform = st.selectbox("Platform", ["twitter", "linkedin", "facebook", "reddit"])
        
        template_text = st.text_area("Template Text", 
                                   placeholder="Check out this amazing transcription I created!")
        
        hashtags_input = st.text_input("Hashtags (comma-separated)", 
                                     placeholder="transcription, AI, productivity")
        hashtags = [tag.strip() for tag in hashtags_input.split(",") if tag.strip()]
        
        call_to_action = st.text_input("Call to Action", 
                                     placeholder="Try it yourself!")
        
        image_url = st.text_input("Image URL (optional)", 
                                placeholder="https://example.com/image.jpg")
        
        if st.button("Create Template"):
            if template_text and call_to_action:
                template_id = marketing.create_social_share_template(
                    platform=platform,
                    template_text=template_text,
                    hashtags=hashtags,
                    call_to_action=call_to_action,
                    image_url=image_url if image_url else None
                )
                st.success(f"✅ Created social share template for {platform}")
                st.info(f"Template ID: {template_id}")
            else:
                st.error("Please enter template text and call to action")
    
    # Generate share URLs
    st.subheader("Generate Share URLs")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        template_id = st.text_input("Template ID", placeholder="Enter template ID")
    with col2:
        user_id = st.text_input("User ID", placeholder="user123", key="social_user_id")
    with col3:
        content_id = st.text_input("Content ID", placeholder="content456")
    
    if st.button("Generate Share URLs"):
        if template_id and user_id and content_id:
            urls = marketing.generate_share_url(template_id, user_id, content_id)
            if urls:
                st.success("✅ Generated share URLs:")
                for platform, url in urls.items():
                    st.markdown(f"**{platform.title()}:** [Share Link]({url})")
                    st.code(url, language="text")
            else:
                st.error("Failed to generate URLs (invalid template ID)")
        else:
            st.error("Please enter all required fields")

def render_ab_testing():
    """Render A/B testing interface"""
    st.header("🧪 A/B Testing")
    
    marketing = init_marketing_system()
    
    # Create A/B test
    with st.expander("Create New A/B Test", expanded=False):
        test_name = st.text_input("Test Name", placeholder="Landing Page Headline Test")
        test_description = st.text_area("Description", 
                                       placeholder="Testing different headlines for conversion...")
        
        st.subheader("Test Variants")
        num_variants = st.number_input("Number of Variants", min_value=2, max_value=5, value=2)
        
        variants = []
        for i in range(num_variants):
            st.write(f"**Variant {i+1}**")
            col1, col2 = st.columns(2)
            
            with col1:
                variant_name = st.text_input(f"Name", value=f"Variant {chr(65+i)}", key=f"variant_name_{i}")
                variant_desc = st.text_input(f"Description", key=f"variant_desc_{i}")
            
            with col2:
                traffic_pct = st.number_input(f"Traffic %", min_value=0.0, max_value=100.0, 
                                            value=100.0/num_variants, key=f"traffic_{i}")
                
                # Configuration as JSON
                config_json = st.text_area(f"Config (JSON)", 
                                         value='{"headline": "Default Headline"}',
                                         key=f"config_{i}")
            
            try:
                config = json.loads(config_json)
                variants.append({
                    "name": variant_name,
                    "description": variant_desc,
                    "traffic_percentage": traffic_pct,
                    "config": config
                })
            except json.JSONDecodeError:
                st.error(f"Invalid JSON in Variant {i+1} config")
        
        if st.button("Create A/B Test"):
            if test_name and len(variants) >= 2:
                test_id = marketing.create_ab_test(test_name, test_description, variants)
                st.success(f"✅ Created A/B test: {test_name}")
                st.info(f"Test ID: {test_id}")
            else:
                st.error("Please enter test name and at least 2 variants")
    
    # Get test variant for user
    st.subheader("Get Test Variant")
    col1, col2 = st.columns(2)
    
    with col1:
        test_id = st.text_input("Test ID", placeholder="Enter test ID")
    with col2:
        user_id = st.text_input("User ID", placeholder="user123", key="ab_user_id")
    
    if st.button("Get Variant"):
        if test_id and user_id:
            variant = marketing.get_ab_test_variant(test_id, user_id)
            if variant:
                st.success(f"✅ User assigned to: **{variant['name']}**")
                st.json(variant['config'])
            else:
                st.error("Test not found or no variants available")
        else:
            st.error("Please enter test ID and user ID")

def render_landing_page_analytics():
    """Render landing page analytics interface"""
    st.header("📈 Landing Page Analytics")
    
    marketing = init_marketing_system()
    
    # Track landing page visit
    with st.expander("Track Landing Page Visit", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            page_url = st.text_input("Page URL", placeholder="https://app.com/landing")
            visitor_id = st.text_input("Visitor ID", placeholder="visitor123")
            session_id = st.text_input("Session ID", placeholder="session456")
        
        with col2:
            source = st.text_input("Source", placeholder="google")
            medium = st.text_input("Medium", placeholder="cpc")
            campaign = st.text_input("Campaign", placeholder="summer_2024")
        
        if st.button("Track Visit"):
            if page_url and visitor_id and session_id:
                visit_id = marketing.track_landing_page_visit(
                    page_url, visitor_id, session_id, source, medium, campaign
                )
                st.success(f"✅ Tracked landing page visit")
                st.info(f"Visit ID: {visit_id}")
            else:
                st.error("Please enter page URL, visitor ID, and session ID")
    
    # Track conversion
    st.subheader("Track Conversion")
    col1, col2 = st.columns(2)
    
    with col1:
        visit_id = st.text_input("Visit ID", placeholder="Enter visit ID")
    with col2:
        conversion_value = st.number_input("Conversion Value ($)", min_value=0.0, value=1.0)
    
    if st.button("Track Conversion"):
        if visit_id:
            marketing.track_landing_page_conversion(visit_id, conversion_value)
            st.success(f"✅ Tracked conversion: ${conversion_value}")
        else:
            st.error("Please enter visit ID")

def render_analytics_dashboard():
    """Render comprehensive analytics dashboard"""
    st.header("📊 Marketing Analytics Dashboard")
    
    marketing = init_marketing_system()
    
    # Time period selector
    period = st.selectbox("Analytics Period", [7, 14, 30, 60, 90], index=2)
    
    # Conversion analytics
    conversion_analytics = marketing.get_conversion_analytics(period)
    
    # Conversion by type chart
    if conversion_analytics["by_type"]:
        st.subheader("Conversions by Type")
        df_type = pd.DataFrame(conversion_analytics["by_type"])
        
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(df_type, values='count', names='type', 
                           title="Conversion Distribution")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(df_type, x='type', y='total_value', 
                           title="Revenue by Conversion Type")
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Conversion by source chart
    if conversion_analytics["by_source"]:
        st.subheader("Conversions by Source")
        df_source = pd.DataFrame(conversion_analytics["by_source"])
        
        fig_source = px.bar(df_source, x='source', y='count', 
                          title="Conversions by Traffic Source")
        st.plotly_chart(fig_source, use_container_width=True)
    
    # Summary metrics
    st.subheader("Summary Metrics")
    
    # Referral metrics
    referral_analytics = marketing.get_referral_analytics()
    affiliate_analytics = marketing.get_affiliate_analytics()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Referral Conversion Rate", f"{referral_analytics['conversion_rate']:.1f}%")
        st.metric("Total Referrals", referral_analytics['total_referrals'])
    
    with col2:
        st.metric("Active Affiliates", affiliate_analytics['active_partners'])
        st.metric("Total Affiliate Earnings", f"${affiliate_analytics['total_earnings']:.2f}")
    
    with col3:
        total_conversions = sum(item['count'] for item in conversion_analytics['by_type'])
        total_revenue = sum(item['total_value'] for item in conversion_analytics['by_type'])
        st.metric("Total Conversions", total_conversions)
        st.metric("Total Revenue", f"${total_revenue:.2f}")

def main():
    """Main marketing and growth UI"""
    st.set_page_config(
        page_title="Marketing & Growth Features",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Marketing & Growth Features")
    st.markdown("Manage referral programs, affiliate marketing, social sharing, and A/B testing")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a section", [
        "Referral Programs",
        "Affiliate Marketing", 
        "Social Sharing",
        "A/B Testing",
        "Landing Page Analytics",
        "Analytics Dashboard"
    ])
    
    # Render selected page
    if page == "Referral Programs":
        render_referral_program_management()
    elif page == "Affiliate Marketing":
        render_affiliate_marketing()
    elif page == "Social Sharing":
        render_social_sharing()
    elif page == "A/B Testing":
        render_ab_testing()
    elif page == "Landing Page Analytics":
        render_landing_page_analytics()
    elif page == "Analytics Dashboard":
        render_analytics_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Tip:** Use these features to grow your user base and optimize conversions!")

if __name__ == "__main__":
    main()