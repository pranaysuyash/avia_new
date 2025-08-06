"""
Internationalization and Localization UI
Streamlit interface for managing multi-language support, currency handling, 
regional pricing, and compliance requirements
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
from internationalization_localization import (
    InternationalizationSystem, SupportedLanguage, SupportedCurrency, 
    ComplianceRegion, LocaleConfig
)

def init_i18n_system():
    """Initialize the internationalization system"""
    if 'i18n_system' not in st.session_state:
        st.session_state.i18n_system = InternationalizationSystem()
    return st.session_state.i18n_system

def render_language_management():
    """Render language and translation management"""
    st.header("🌍 Language & Translation Management")
    
    i18n = init_i18n_system()
    
    # Add Translation
    st.subheader("Add New Translation")
    
    with st.expander("Add Translation", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            translation_key = st.text_input("Translation Key", placeholder="nav.home")
            language = st.selectbox("Language", [lang.value for lang in SupportedLanguage])
            translation_text = st.text_area("Translation", placeholder="Enter translation...")
        
        with col2:
            context = st.text_input("Context (optional)", placeholder="Navigation menu")
            
            # Pluralization support
            st.write("**Pluralization (optional)**")
            plural_zero = st.text_input("Zero form", placeholder="No items")
            plural_one = st.text_input("One form", placeholder="1 item")
            plural_other = st.text_input("Other form", placeholder="{count} items")
        
        if st.button("Add Translation"):
            if translation_key and translation_text:
                pluralization = None
                if plural_zero or plural_one or plural_other:
                    pluralization = {}
                    if plural_zero:
                        pluralization["zero"] = plural_zero
                    if plural_one:
                        pluralization["one"] = plural_one
                    if plural_other:
                        pluralization["other"] = plural_other
                
                i18n.add_translation(
                    translation_key, 
                    SupportedLanguage(language), 
                    translation_text, 
                    context, 
                    pluralization
                )
                st.success(f"✅ Added translation for {translation_key} in {language}")
            else:
                st.error("Please enter translation key and text")
    
    # Translation Testing
    st.subheader("🧪 Translation Testing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        test_key = st.text_input("Test Key", placeholder="nav.home")
    with col2:
        test_language = st.selectbox("Test Language", [lang.value for lang in SupportedLanguage], key="test_lang")
    with col3:
        test_count = st.number_input("Count (for pluralization)", min_value=0, value=1)
    
    if st.button("Test Translation"):
        if test_key:
            translation = i18n.get_translation(
                test_key, 
                SupportedLanguage(test_language), 
                count=test_count if test_count > 0 else None
            )
            st.success(f"**Translation:** {translation}")
        else:
            st.error("Please enter a translation key")
    
    # Supported Languages Overview
    st.subheader("📋 Supported Languages")
    
    languages = i18n.get_supported_languages()
    if languages:
        df = pd.DataFrame(languages)
        df.columns = ["Code", "English Name", "Native Name"]
        st.dataframe(df, use_container_width=True)
    
    # Translation Coverage
    st.subheader("📊 Translation Coverage")
    
    if st.button("Analyze Translation Coverage"):
        coverage_data = []
        
        for lang in SupportedLanguage:
            translations = i18n.get_all_translations(lang)
            coverage_data.append({
                "Language": i18n.get_native_language_name(lang),
                "Code": lang.value,
                "Translations": len(translations)
            })
        
        if coverage_data:
            df = pd.DataFrame(coverage_data)
            
            # Bar chart of translation counts
            fig = px.bar(
                df, 
                x='Language', 
                y='Translations',
                title="Translation Count by Language",
                color='Translations',
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

def render_currency_pricing():
    """Render currency and pricing management"""
    st.header("💰 Currency & Regional Pricing")
    
    i18n = init_i18n_system()
    
    # Currency Rate Management
    st.subheader("💱 Currency Exchange Rates")
    
    with st.expander("Add Currency Rate", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            from_currency = st.selectbox("From Currency", [curr.value for curr in SupportedCurrency])
        with col2:
            to_currency = st.selectbox("To Currency", [curr.value for curr in SupportedCurrency])
        with col3:
            exchange_rate = st.number_input("Exchange Rate", min_value=0.0, value=1.0, step=0.01)
        
        if st.button("Add Exchange Rate"):
            if from_currency != to_currency:
                i18n.add_currency_rate(
                    SupportedCurrency(from_currency),
                    SupportedCurrency(to_currency),
                    exchange_rate
                )
                st.success(f"✅ Added rate: {from_currency} → {to_currency} = {exchange_rate}")
            else:
                st.error("From and To currencies must be different")
    
    # Currency Conversion Testing
    st.subheader("🔄 Currency Conversion")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        convert_amount = st.number_input("Amount", min_value=0.0, value=100.0)
    with col2:
        convert_from = st.selectbox("From", [curr.value for curr in SupportedCurrency], key="convert_from")
    with col3:
        convert_to = st.selectbox("To", [curr.value for curr in SupportedCurrency], key="convert_to")
    with col4:
        if st.button("Convert"):
            converted = i18n.convert_currency(
                convert_amount,
                SupportedCurrency(convert_from),
                SupportedCurrency(convert_to)
            )
            if converted is not None:
                formatted_from = i18n.format_currency(convert_amount, SupportedCurrency(convert_from))
                formatted_to = i18n.format_currency(converted, SupportedCurrency(convert_to))
                st.success(f"{formatted_from} = {formatted_to}")
            else:
                st.error("Exchange rate not available")
    
    # Regional Pricing Management
    st.subheader("🌎 Regional Pricing")
    
    with st.expander("Add Regional Pricing", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            region = st.text_input("Region Code", placeholder="US")
            currency = st.selectbox("Currency", [curr.value for curr in SupportedCurrency], key="region_currency")
            base_multiplier = st.number_input("Base Price Multiplier", min_value=0.0, value=1.0, step=0.1)
        
        with col2:
            tax_rate = st.number_input("Tax Rate", min_value=0.0, max_value=1.0, value=0.08, step=0.01)
            tax_name = st.text_input("Tax Name", value="Tax")
        
        # Pricing tiers
        st.write("**Pricing Tiers**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            basic_multiplier = st.number_input("Basic Tier", min_value=0.0, value=1.0, step=0.1)
        with col2:
            pro_multiplier = st.number_input("Pro Tier", min_value=0.0, value=1.0, step=0.1)
        with col3:
            enterprise_multiplier = st.number_input("Enterprise Tier", min_value=0.0, value=1.0, step=0.1)
        
        if st.button("Add Regional Pricing"):
            if region:
                pricing_tiers = {
                    "basic": basic_multiplier,
                    "pro": pro_multiplier,
                    "enterprise": enterprise_multiplier
                }
                
                i18n.add_regional_pricing(
                    region,
                    SupportedCurrency(currency),
                    base_multiplier,
                    tax_rate,
                    tax_name,
                    pricing_tiers
                )
                st.success(f"✅ Added regional pricing for {region}")
            else:
                st.error("Please enter a region code")
    
    # Pricing Calculator
    st.subheader("🧮 Regional Pricing Calculator")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        base_price = st.number_input("Base Price (USD)", min_value=0.0, value=99.0)
    with col2:
        calc_region = st.text_input("Region", placeholder="US", key="calc_region")
    with col3:
        tier = st.selectbox("Tier", ["basic", "pro", "enterprise"])
    
    if st.button("Calculate Regional Price"):
        if calc_region:
            pricing = i18n.calculate_regional_price(base_price, calc_region, tier)
            
            st.subheader("💰 Pricing Breakdown")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Base Price", f"${pricing['base_price']:.2f}")
            with col2:
                st.metric("Regional Price", f"{pricing['currency']} {pricing['regional_price']:.2f}")
            with col3:
                st.metric(pricing['tax_name'], f"{pricing['currency']} {pricing['tax']:.2f}")
            with col4:
                st.metric("Total Price", f"{pricing['currency']} {pricing['total_price']:.2f}")
            
            # Show tax rate
            st.info(f"Tax Rate: {pricing['tax_rate']:.1%}")
        else:
            st.error("Please enter a region code")d
ef render_compliance_management():
    """Render compliance and regulatory management"""
    st.header("⚖️ Compliance & Regulatory Management")
    
    i18n = init_i18n_system()
    
    # Compliance Overview
    st.subheader("📋 Compliance Regions Overview")
    
    compliance_data = []
    for region in ComplianceRegion:
        requirements = i18n.get_compliance_requirements(region)
        if requirements:
            compliance_data.append({
                "Region": requirements.get("name", region.value),
                "Area": requirements.get("region", ""),
                "Consent Required": "✅" if requirements.get("consent_required") else "❌",
                "Right to Deletion": "✅" if requirements.get("right_to_deletion") else "❌",
                "Data Retention (Days)": requirements.get("data_retention_max_days", "N/A"),
                "Breach Notification (Hours)": requirements.get("breach_notification_hours", "N/A")
            })
    
    if compliance_data:
        df = pd.DataFrame(compliance_data)
        st.dataframe(df, use_container_width=True)
    
    # Compliance Checker
    st.subheader("🔍 Compliance Checker")
    
    col1, col2 = st.columns(2)
    
    with col1:
        check_region = st.selectbox("Compliance Region", [region.value for region in ComplianceRegion])
    with col2:
        user_age = st.number_input("User Age (optional)", min_value=0, max_value=120, value=25)
    
    if st.button("Check Compliance"):
        compliance_status = i18n.check_compliance(
            ComplianceRegion(check_region),
            user_age if user_age > 0 else None
        )
        
        # Display compliance status
        if compliance_status["compliant"]:
            st.success("✅ Compliant")
        else:
            st.error("❌ Non-Compliant")
        
        # Show requirements
        requirements = compliance_status["requirements"]
        if requirements:
            st.subheader("📋 Compliance Requirements")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Data Protection**")
                st.write(f"• Consent Required: {'Yes' if requirements.get('consent_required') else 'No'}")
                st.write(f"• Right to Deletion: {'Yes' if requirements.get('right_to_deletion') else 'No'}")
                st.write(f"• Right to Portability: {'Yes' if requirements.get('right_to_portability') else 'No'}")
                st.write(f"• Age of Consent: {requirements.get('age_of_consent', 'N/A')}")
            
            with col2:
                st.write("**Operational Requirements**")
                st.write(f"• Data Retention Max: {requirements.get('data_retention_max_days', 'N/A')} days")
                st.write(f"• Breach Notification: {requirements.get('breach_notification_hours', 'N/A')} hours")
                st.write(f"• DPO Required: {'Yes' if requirements.get('data_protection_officer_required') else 'No'}")
                st.write(f"• Privacy Policy: {'Yes' if requirements.get('privacy_policy_required') else 'No'}")
        
        # Show issues and actions
        if compliance_status["issues"]:
            st.subheader("⚠️ Compliance Issues")
            for issue in compliance_status["issues"]:
                st.warning(f"• {issue}")
        
        if compliance_status["required_actions"]:
            st.subheader("📝 Required Actions")
            for action in compliance_status["required_actions"]:
                st.info(f"• {action}")

def render_cultural_customization():
    """Render cultural customization management"""
    st.header("🎨 Cultural Customization")
    
    i18n = init_i18n_system()
    
    # Cultural Preferences
    st.subheader("🌍 Cultural Preferences by Locale")
    
    col1, col2 = st.columns(2)
    
    with col1:
        culture_language = st.selectbox("Language", [lang.value for lang in SupportedLanguage], key="culture_lang")
    with col2:
        culture_country = st.text_input("Country Code", placeholder="US", key="culture_country")
    
    if st.button("Get Cultural Preferences"):
        if culture_country:
            preferences = i18n.get_cultural_preferences(
                SupportedLanguage(culture_language),
                culture_country
            )
            
            if preferences:
                st.subheader("🎨 Cultural Preferences")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Visual Preferences**")
                    if "color_preferences" in preferences:
                        st.write(f"• Preferred Colors: {', '.join(preferences['color_preferences'])}")
                    if "image_style" in preferences:
                        st.write(f"• Image Style: {preferences['image_style']}")
                    if "rtl" in preferences:
                        st.write(f"• Right-to-Left: {'Yes' if preferences['rtl'] else 'No'}")
                
                with col2:
                    st.write("**Cultural Norms**")
                    if "communication_style" in preferences:
                        st.write(f"• Communication: {preferences['communication_style']}")
                    if "business_hours" in preferences:
                        st.write(f"• Business Hours: {preferences['business_hours']}")
                    if "weekend_days" in preferences:
                        st.write(f"• Weekend: {', '.join(preferences['weekend_days'])}")
                
                # Special cultural considerations
                if "lucky_numbers" in preferences:
                    st.write(f"**Lucky Numbers:** {', '.join(map(str, preferences['lucky_numbers']))}")
                if "unlucky_numbers" in preferences:
                    st.write(f"**Unlucky Numbers:** {', '.join(map(str, preferences['unlucky_numbers']))}")
            else:
                st.warning("No cultural preferences found for this locale")
        else:
            st.error("Please enter a country code")
    
    # Date and Number Formatting
    st.subheader("📅 Date & Number Formatting")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        format_language = st.selectbox("Language", [lang.value for lang in SupportedLanguage], key="format_lang")
    with col2:
        format_country = st.text_input("Country Code", placeholder="US", key="format_country")
    with col3:
        test_number = st.number_input("Test Number", value=1234.56)
    
    if st.button("Test Formatting"):
        if format_country:
            current_time = datetime.now()
            
            # Format date and time
            formatted_date = i18n.format_date(current_time, SupportedLanguage(format_language), format_country)
            formatted_time = i18n.format_time(current_time, SupportedLanguage(format_language), format_country)
            formatted_number = i18n.format_number(test_number, SupportedLanguage(format_language), format_country)
            
            st.subheader("🔤 Formatting Results")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Date Format", formatted_date)
            with col2:
                st.metric("Time Format", formatted_time)
            with col3:
                st.metric("Number Format", formatted_number)
        else:
            st.error("Please enter a country code")

def render_user_preferences():
    """Render user preference management"""
    st.header("👤 User Preferences")
    
    i18n = init_i18n_system()
    
    # Set User Preferences
    st.subheader("⚙️ Set User Locale Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        user_id = st.text_input("User ID", placeholder="user123")
        pref_language = st.selectbox("Preferred Language", [lang.value for lang in SupportedLanguage], key="pref_lang")
        pref_currency = st.selectbox("Preferred Currency", [curr.value for curr in SupportedCurrency], key="pref_curr")
    
    with col2:
        timezone = st.text_input("Timezone", value="UTC", placeholder="America/New_York")
        
        if st.button("Save Preferences"):
            if user_id:
                i18n.set_user_locale(
                    user_id,
                    SupportedLanguage(pref_language),
                    SupportedCurrency(pref_currency),
                    timezone
                )
                st.success(f"✅ Saved preferences for {user_id}")
            else:
                st.error("Please enter a User ID")
    
    # Get User Preferences
    st.subheader("🔍 Get User Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        lookup_user_id = st.text_input("Lookup User ID", placeholder="user123", key="lookup_user")
    
    with col2:
        if st.button("Get Preferences"):
            if lookup_user_id:
                preferences = i18n.get_user_locale(lookup_user_id)
                if preferences:
                    st.success("✅ User preferences found")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Language", preferences["language"])
                    with col2:
                        st.metric("Currency", preferences["currency"])
                    with col3:
                        st.metric("Timezone", preferences["timezone"])
                else:
                    st.warning("No preferences found for this user")
            else:
                st.error("Please enter a User ID")

def render_system_overview():
    """Render system overview and statistics"""
    st.header("📊 System Overview")
    
    i18n = init_i18n_system()
    
    # System Statistics
    st.subheader("📈 System Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Supported Languages", len(SupportedLanguage))
    with col2:
        st.metric("Supported Currencies", len(SupportedCurrency))
    with col3:
        st.metric("Compliance Regions", len(ComplianceRegion))
    with col4:
        # Count total translations
        total_translations = 0
        for lang in SupportedLanguage:
            translations = i18n.get_all_translations(lang)
            total_translations += len(translations)
        st.metric("Total Translations", total_translations)
    
    # Language Distribution
    st.subheader("🌍 Language Support Distribution")
    
    language_data = []
    for lang in SupportedLanguage:
        translations = i18n.get_all_translations(lang)
        language_data.append({
            "Language": i18n.get_native_language_name(lang),
            "Code": lang.value,
            "Translations": len(translations)
        })
    
    if language_data:
        df = pd.DataFrame(language_data)
        
        # Pie chart of language distribution
        fig = px.pie(
            df,
            values='Translations',
            names='Language',
            title="Translation Distribution by Language"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Currency Support
    st.subheader("💰 Currency Support")
    
    currency_data = []
    for curr in SupportedCurrency:
        currency_data.append({
            "Currency": curr.value,
            "Name": curr.name.replace('_', ' ').title()
        })
    
    df_curr = pd.DataFrame(currency_data)
    st.dataframe(df_curr, use_container_width=True)
    
    # Sample Data Loading
    st.subheader("🔄 System Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Load Sample Data"):
            with st.spinner("Loading sample currency rates and regional pricing..."):
                i18n.load_sample_data()
                st.success("✅ Sample data loaded successfully!")
    
    with col2:
        if st.button("Refresh System"):
            # Clear session state to reinitialize
            if 'i18n_system' in st.session_state:
                del st.session_state.i18n_system
            st.success("✅ System refreshed!")
            st.experimental_rerun()

def main():
    """Main internationalization and localization UI"""
    st.set_page_config(
        page_title="Internationalization & Localization",
        page_icon="🌍",
        layout="wide"
    )
    
    st.title("🌍 Internationalization & Localization")
    st.markdown("Comprehensive multi-language support, currency handling, and compliance management")
    
    # Initialize system
    i18n = init_i18n_system()
    
    # Sidebar navigation
    st.sidebar.title("I18n Modules")
    page = st.sidebar.selectbox("Choose a module", [
        "System Overview",
        "Language Management",
        "Currency & Pricing",
        "Compliance Management",
        "Cultural Customization",
        "User Preferences"
    ])
    
    # Render selected page
    if page == "System Overview":
        render_system_overview()
    elif page == "Language Management":
        render_language_management()
    elif page == "Currency & Pricing":
        render_currency_pricing()
    elif page == "Compliance Management":
        render_compliance_management()
    elif page == "Cultural Customization":
        render_cultural_customization()
    elif page == "User Preferences":
        render_user_preferences()
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Tip:** Use the sample data loader to populate the system with example translations and pricing!")

if __name__ == "__main__":
    main()