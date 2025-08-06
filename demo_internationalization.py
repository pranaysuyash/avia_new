"""
Demo script for Internationalization and Localization System
Demonstrates multi-language support, currency handling, regional pricing, and compliance
"""

import os
from datetime import datetime
from internationalization_localization import (
    InternationalizationSystem, SupportedLanguage, SupportedCurrency, ComplianceRegion
)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n--- {title} ---")

def demo_multi_language_support(i18n):
    """Demo multi-language UI support"""
    print_header("🌍 MULTI-LANGUAGE UI SUPPORT")
    
    print_section("Translation Testing Across Languages")
    
    # Test key translations across multiple languages
    test_keys = ["nav.home", "nav.transcription", "action.upload", "status.processing", "pricing.monthly"]
    
    # Test languages
    test_languages = [
        SupportedLanguage.ENGLISH,
        SupportedLanguage.SPANISH, 
        SupportedLanguage.FRENCH,
        SupportedLanguage.GERMAN,
        SupportedLanguage.CHINESE_SIMPLIFIED,
        SupportedLanguage.JAPANESE,
        SupportedLanguage.ARABIC
    ]
    
    print(f"{'Key':<20} {'English':<15} {'Spanish':<15} {'French':<15} {'German':<15} {'Chinese':<10} {'Japanese':<10} {'Arabic':<10}")
    print("-" * 120)
    
    for key in test_keys:
        translations = []
        for lang in test_languages:
            translation = i18n.get_translation(key, lang)
            # Truncate long translations for display
            if len(translation) > 12:
                translation = translation[:9] + "..."
            translations.append(translation)
        
        print(f"{key:<20} {translations[0]:<15} {translations[1]:<15} {translations[2]:<15} "
              f"{translations[3]:<15} {translations[4]:<10} {translations[5]:<10} {translations[6]:<10}")
    
    print_section("Adding Custom Translations")
    
    # Add some custom translations
    custom_translations = [
        ("demo.welcome", "Welcome to our platform!", "¡Bienvenido a nuestra plataforma!", "Bienvenue sur notre plateforme!"),
        ("demo.features", "Explore our features", "Explora nuestras características", "Explorez nos fonctionnalités"),
        ("demo.support", "24/7 Customer Support", "Soporte al Cliente 24/7", "Support Client 24/7")
    ]
    
    for key, en_text, es_text, fr_text in custom_translations:
        i18n.add_translation(key, SupportedLanguage.ENGLISH, en_text)
        i18n.add_translation(key, SupportedLanguage.SPANISH, es_text)
        i18n.add_translation(key, SupportedLanguage.FRENCH, fr_text)
        print(f"✅ Added translations for {key}")
    
    print_section("Pluralization Support")
    
    # Add pluralized translation
    pluralization = {
        "zero": "No files uploaded",
        "one": "1 file uploaded", 
        "other": "{count} files uploaded"
    }
    
    i18n.add_translation(
        "files.uploaded",
        SupportedLanguage.ENGLISH,
        "{count} files uploaded",
        pluralization=pluralization
    )
    
    # Test pluralization
    for count in [0, 1, 5, 23]:
        plural_text = i18n.get_translation("files.uploaded", SupportedLanguage.ENGLISH, count=count)
        print(f"   Count {count}: {plural_text}")

def demo_currency_support(i18n):
    """Demo global currency support"""
    print_header("💰 GLOBAL CURRENCY SUPPORT")
    
    print_section("Loading Sample Currency Rates")
    i18n.load_sample_data()
    print("✅ Sample currency rates loaded")
    
    print_section("Currency Conversion Examples")
    
    base_amount = 99.99
    base_currency = SupportedCurrency.USD
    
    target_currencies = [
        SupportedCurrency.EUR,
        SupportedCurrency.GBP, 
        SupportedCurrency.CAD,
        SupportedCurrency.JPY,
        SupportedCurrency.CNY,
        SupportedCurrency.INR
    ]
    
    print(f"Converting ${base_amount} USD to other currencies:")
    print(f"{'Currency':<15} {'Converted Amount':<20} {'Formatted':<25}")
    print("-" * 60)
    
    for currency in target_currencies:
        converted = i18n.convert_currency(base_amount, base_currency, currency)
        if converted:
            # Format currency based on locale
            if currency == SupportedCurrency.EUR:
                formatted = i18n.format_currency(converted, currency, "de_DE")
            elif currency == SupportedCurrency.GBP:
                formatted = i18n.format_currency(converted, currency, "en_GB")
            elif currency == SupportedCurrency.JPY:
                formatted = i18n.format_currency(converted, currency, "ja_JP")
            else:
                formatted = f"{currency.value} {converted:.2f}"
            
            print(f"{currency.value:<15} {converted:<20.2f} {formatted:<25}")
        else:
            print(f"{currency.value:<15} {'Rate not available':<20} {'N/A':<25}")

def demo_regional_pricing(i18n):
    """Demo region-specific pricing and tax handling"""
    print_header("🌎 REGIONAL PRICING & TAX HANDLING")
    
    print_section("Regional Pricing Configuration")
    
    base_price = 99.0
    regions = ["US", "EU", "UK", "CA", "JP", "CN", "IN", "BR"]
    tiers = ["basic", "pro", "enterprise"]
    
    print(f"Base Price: ${base_price} USD")
    print(f"\n{'Region':<8} {'Tier':<12} {'Regional Price':<15} {'Tax':<10} {'Total':<12} {'Currency':<8}")
    print("-" * 75)
    
    for region in regions:
        for tier in tiers:
            pricing = i18n.calculate_regional_price(base_price, region, tier)
            
            print(f"{region:<8} {tier:<12} {pricing['regional_price']:<15.2f} "
                  f"{pricing['tax']:<10.2f} {pricing['total_price']:<12.2f} {pricing['currency']:<8}")
    
    print_section("Tax Information by Region")
    
    print(f"{'Region':<8} {'Tax Name':<15} {'Tax Rate':<10} {'Currency':<8}")
    print("-" * 45)
    
    for region in regions:
        pricing = i18n.calculate_regional_price(base_price, region)
        print(f"{region:<8} {pricing['tax_name']:<15} {pricing['tax_rate']:<10.1%} {pricing['currency']:<8}")

def demo_compliance_requirements(i18n):
    """Demo local compliance requirements"""
    print_header("⚖️ COMPLIANCE REQUIREMENTS")
    
    print_section("Compliance Regions Overview")
    
    regions = [ComplianceRegion.GDPR, ComplianceRegion.CCPA, ComplianceRegion.PIPEDA, 
               ComplianceRegion.LGPD, ComplianceRegion.PDPA, ComplianceRegion.APPI]
    
    print(f"{'Region':<8} {'Name':<35} {'Area':<15} {'Consent':<8} {'Age':<4} {'Breach Hours':<12}")
    print("-" * 90)
    
    for region in regions:
        requirements = i18n.get_compliance_requirements(region)
        if requirements:
            print(f"{region.value:<8} {requirements['name'][:34]:<35} "
                  f"{requirements['region'][:14]:<15} "
                  f"{'Yes' if requirements['consent_required'] else 'No':<8} "
                  f"{requirements['age_of_consent']:<4} "
                  f"{requirements.get('breach_notification_hours', 'N/A'):<12}")
    
    print_section("Compliance Checking Examples")
    
    # Test compliance for different user scenarios
    test_scenarios = [
        (ComplianceRegion.GDPR, 25, "Adult EU user"),
        (ComplianceRegion.GDPR, 15, "Minor EU user"),
        (ComplianceRegion.CCPA, 18, "Adult California user"),
        (ComplianceRegion.PIPEDA, 16, "Adult Canadian user"),
        (ComplianceRegion.LGPD, 12, "Minor Brazilian user")
    ]
    
    for region, age, description in test_scenarios:
        compliance = i18n.check_compliance(region, age)
        
        status = "✅ Compliant" if compliance["compliant"] else "❌ Non-Compliant"
        print(f"\n{description} ({region.value.upper()}, age {age}): {status}")
        
        if compliance["issues"]:
            print("   Issues:")
            for issue in compliance["issues"]:
                print(f"     • {issue}")
        
        if compliance["required_actions"]:
            print("   Required Actions:")
            for action in compliance["required_actions"][:3]:  # Show first 3
                print(f"     • {action}")

def demo_cultural_customization(i18n):
    """Demo cultural customization for different markets"""
    print_header("🎨 CULTURAL CUSTOMIZATION")
    
    print_section("Cultural Preferences by Market")
    
    markets = [
        (SupportedLanguage.ENGLISH, "US", "United States"),
        (SupportedLanguage.CHINESE_SIMPLIFIED, "CN", "China"),
        (SupportedLanguage.JAPANESE, "JP", "Japan"),
        (SupportedLanguage.ARABIC, "SA", "Saudi Arabia"),
        (SupportedLanguage.GERMAN, "DE", "Germany"),
        (SupportedLanguage.SPANISH, "ES", "Spain")
    ]
    
    for language, country, market_name in markets:
        print(f"\n🌍 {market_name} ({language.value}_{country})")
        
        preferences = i18n.get_cultural_preferences(language, country)
        
        if preferences:
            print(f"   Colors: {', '.join(preferences.get('color_preferences', []))}")
            print(f"   Communication: {preferences.get('communication_style', 'N/A')}")
            print(f"   Business Hours: {preferences.get('business_hours', 'N/A')}")
            print(f"   Weekend: {', '.join(preferences.get('weekend_days', []))}")
            print(f"   RTL Support: {'Yes' if preferences.get('rtl') else 'No'}")
            
            if 'lucky_numbers' in preferences:
                print(f"   Lucky Numbers: {', '.join(map(str, preferences['lucky_numbers']))}")
            if 'unlucky_numbers' in preferences:
                print(f"   Unlucky Numbers: {', '.join(map(str, preferences['unlucky_numbers']))}")
    
    print_section("Date and Number Formatting")
    
    test_date = datetime(2024, 8, 6, 14, 30, 0)
    test_number = 1234.56
    
    print(f"Test Date: {test_date}")
    print(f"Test Number: {test_number}")
    print()
    
    print(f"{'Market':<15} {'Date Format':<12} {'Time Format':<10} {'Number Format':<15}")
    print("-" * 55)
    
    for language, country, market_name in markets:
        formatted_date = i18n.format_date(test_date, language, country)
        formatted_time = i18n.format_time(test_date, language, country)
        formatted_number = i18n.format_number(test_number, language, country)
        
        print(f"{market_name[:14]:<15} {formatted_date:<12} {formatted_time:<10} {formatted_number:<15}")

def demo_user_preferences(i18n):
    """Demo user preference management"""
    print_header("👤 USER PREFERENCE MANAGEMENT")
    
    print_section("Setting User Preferences")
    
    # Sample users with different preferences
    users = [
        ("user_us", SupportedLanguage.ENGLISH, SupportedCurrency.USD, "America/New_York"),
        ("user_es", SupportedLanguage.SPANISH, SupportedCurrency.EUR, "Europe/Madrid"),
        ("user_jp", SupportedLanguage.JAPANESE, SupportedCurrency.JPY, "Asia/Tokyo"),
        ("user_cn", SupportedLanguage.CHINESE_SIMPLIFIED, SupportedCurrency.CNY, "Asia/Shanghai"),
        ("user_br", SupportedLanguage.PORTUGUESE, SupportedCurrency.BRL, "America/Sao_Paulo")
    ]
    
    for user_id, language, currency, timezone in users:
        i18n.set_user_locale(user_id, language, currency, timezone)
        print(f"✅ Set preferences for {user_id}: {language.value}, {currency.value}, {timezone}")
    
    print_section("Retrieving User Preferences")
    
    print(f"{'User ID':<12} {'Language':<10} {'Currency':<10} {'Timezone':<20}")
    print("-" * 55)
    
    for user_id, _, _, _ in users:
        preferences = i18n.get_user_locale(user_id)
        if preferences:
            print(f"{user_id:<12} {preferences['language']:<10} "
                  f"{preferences['currency']:<10} {preferences['timezone']:<20}")
    
    print_section("Personalized Experience Examples")
    
    # Show how preferences affect user experience
    for user_id, _, _, _ in users[:3]:  # Show first 3 users
        preferences = i18n.get_user_locale(user_id)
        if preferences:
            language = SupportedLanguage(preferences['language'])
            currency = SupportedCurrency(preferences['currency'])
            
            # Get localized content
            welcome = i18n.get_translation("demo.welcome", language)
            
            # Get regional pricing
            region_map = {"USD": "US", "EUR": "EU", "JPY": "JP"}
            region = region_map.get(currency.value, "US")
            pricing = i18n.calculate_regional_price(99.0, region, "pro")
            
            print(f"\n👤 {user_id.upper()}:")
            print(f"   Welcome Message: {welcome}")
            print(f"   Pro Plan Price: {pricing['currency']} {pricing['total_price']:.2f}")

def demo_system_overview(i18n):
    """Demo system capabilities overview"""
    print_header("📊 SYSTEM CAPABILITIES OVERVIEW")
    
    print_section("Supported Languages")
    print(f"Total Languages Supported: {len(SupportedLanguage)}")
    
    languages = i18n.get_supported_languages()
    for i, lang in enumerate(languages, 1):
        print(f"{i:2d}. {lang['native_name']} ({lang['name']}) - {lang['code']}")
    
    print_section("Supported Currencies")
    print(f"Total Currencies Supported: {len(SupportedCurrency)}")
    
    currencies = list(SupportedCurrency)
    for i, curr in enumerate(currencies, 1):
        print(f"{i:2d}. {curr.value} - {curr.name.replace('_', ' ').title()}")
    
    print_section("Compliance Regions")
    print(f"Total Compliance Regions: {len(ComplianceRegion)}")
    
    for i, region in enumerate(ComplianceRegion, 1):
        requirements = i18n.get_compliance_requirements(region)
        region_name = requirements.get("name", region.value) if requirements else region.value
        print(f"{i}. {region.value.upper()} - {region_name}")
    
    print_section("Translation Coverage")
    
    # Count translations per language
    total_translations = 0
    for lang in SupportedLanguage:
        translations = i18n.get_all_translations(lang)
        count = len(translations)
        total_translations += count
        print(f"{i18n.get_native_language_name(lang):<15} {count:>3} translations")
    
    print(f"\nTotal Translations: {total_translations}")

def main():
    """Run the complete internationalization and localization demo"""
    print("🌍 INTERNATIONALIZATION & LOCALIZATION DEMO")
    print("=" * 70)
    print("This demo showcases comprehensive multi-language support, currency handling,")
    print("regional pricing, compliance requirements, and cultural customization.")
    
    # Initialize system
    i18n = InternationalizationSystem("demo_i18n.db")
    
    try:
        # Run all demos
        demo_multi_language_support(i18n)
        demo_currency_support(i18n)
        demo_regional_pricing(i18n)
        demo_compliance_requirements(i18n)
        demo_cultural_customization(i18n)
        demo_user_preferences(i18n)
        demo_system_overview(i18n)
        
        print_header("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("All internationalization and localization features demonstrated.")
        print("The system is ready for global deployment!")
        
        print("\n💡 Next Steps:")
        print("1. Run the Streamlit UI: streamlit run internationalization_ui.py")
        print("2. Run tests: python test_internationalization.py")
        print("3. Integrate with your main application")
        print("4. Configure additional languages and regions as needed")
        print("5. Set up automated translation workflows")
        
        print("\n🌍 Global Readiness Features:")
        print("• 15+ language support with native translations")
        print("• 15+ currency support with real-time conversion")
        print("• Regional pricing with local tax handling")
        print("• 6 major compliance frameworks (GDPR, CCPA, PIPEDA, etc.)")
        print("• Cultural customization for different markets")
        print("• Comprehensive date/time/number formatting")
        print("• User preference management and personalization")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup demo database
        if os.path.exists("demo_i18n.db"):
            os.remove("demo_i18n.db")
            print("\n🧹 Demo database cleaned up")

if __name__ == "__main__":
    main()