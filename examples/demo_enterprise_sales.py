"""
Demo script for Enterprise Sales and Onboarding System
Demonstrates all features including pricing calculator, demo scheduling,
trial management, white-label customization, and customer success tracking.
"""

import streamlit as st
from enterprise_sales_ui import render_enterprise_sales_dashboard

def main():
    """Main demo application"""
    st.set_page_config(
        page_title="Enterprise Sales & Onboarding Demo",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    
    .success-card {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .warning-card {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enterprise Sales & Onboarding System</h1>
        <p>Comprehensive enterprise sales tools for custom pricing, demo management, trials, and customer success</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo information
    with st.expander("ℹ️ About This Demo", expanded=False):
        st.markdown("""
        This demo showcases the **Enterprise Sales and Onboarding System** with the following features:
        
        ### 🎯 Key Features
        - **Custom Pricing Calculator**: Generate tailored pricing for enterprise clients
        - **Demo Scheduling**: Manage demo requests and scheduling
        - **Trial Management**: Create and track trial accounts with conversion metrics
        - **White-Label Customization**: Configure branded deployments for clients
        - **Onboarding Workflows**: Guide new customers through structured onboarding
        - **Customer Success Tracking**: Monitor health scores and engagement metrics
        
        ### 🚀 How to Use
        1. Use the sidebar to navigate between different tools
        2. Start with the **Sales Dashboard** for an overview
        3. Try the **Pricing Calculator** to create custom enterprise pricing
        4. Schedule demos and manage trials
        5. Configure white-label deployments
        6. Track customer success metrics
        
        ### 📊 Sample Data
        The demo includes sample data to demonstrate all features. In production, this would connect to your CRM and customer database.
        """)
    
    # Render the main dashboard
    render_enterprise_sales_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>Enterprise Sales & Onboarding System Demo | Built with Streamlit</p>
        <p>🔧 Features: Custom Pricing • Demo Management • Trial Tracking • White-Label Config • Customer Success</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()