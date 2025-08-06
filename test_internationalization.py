"""
Test suite for Internationalization and Localization System
Tests multi-language support, currency handling, regional pricing, and compliance
"""

import pytest
import os
import tempfile
from datetime import datetime
from internationalization_localization import (
    InternationalizationSystem, SupportedLanguage, SupportedCurrency, 
    ComplianceRegion, LocaleConfig
)

class TestInternationalizationSystem:
    
    @pytest.fixture
    def i18n_system(self):
        """Create a temporary internationalization system for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            db_path = tmp_file.name
        
        system = InternationalizationSystem(db_path)
        yield system
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_database_initialization(self, i18n_system):
        """Test that the database is properly initialized"""
        assert os.path.exists(i18n_system.db_path)
        
        # Test that tables were created
        import sqlite3
        conn = sqlite3.connect(i18n_system.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['translations', 'locales', 'currency_rates', 
                          'regional_pricing', 'user_preferences']
        
        for table in expected_tables:
            assert table in tables
        
        conn.close()
    
    def test_default_translations_loading(self, i18n_system):
        """Test that default translations are loaded"""
        # Test getting a translation
        translation = i18n_system.get_translation("nav.home", SupportedLanguage.ENGLISH)
        assert translation == "Home"
        
        # Test Spanish translation
        spanish_translation = i18n_system.get_translation("nav.home", SupportedLanguage.SPANISH)
        assert spanish_translation == "Inicio"
        
        # Test Chinese translation
        chinese_translation = i18n_system.get_translation("nav.home", SupportedLanguage.CHINESE_SIMPLIFIED)
        assert chinese_translation == "首页"
    
    def test_translation_management(self, i18n_system):
        """Test adding and retrieving translations"""
        # Add a new translation
        i18n_system.add_translation(
            "test.message", 
            SupportedLanguage.ENGLISH, 
            "This is a test message"
        )
        
        # Retrieve the translation
        translation = i18n_system.get_translation("test.message", SupportedLanguage.ENGLISH)
        assert translation == "This is a test message"
        
        # Test fallback to English for missing translation
        missing_translation = i18n_system.get_translation("test.message", SupportedLanguage.FRENCH)
        assert missing_translation == "This is a test message"  # Falls back to English
        
        # Test missing key
        missing_key = i18n_system.get_translation("nonexistent.key", SupportedLanguage.ENGLISH)
        assert missing_key == "[nonexistent.key]"
    
    def test_pluralization(self, i18n_system):
        """Test pluralization support"""
        # Add translation with pluralization
        pluralization = {
            "zero": "No items",
            "one": "1 item",
            "other": "{count} items"
        }
        
        i18n_system.add_translation(
            "items.count",
            SupportedLanguage.ENGLISH,
            "{count} items",
            pluralization=pluralization
        )
        
        # Test different plural forms
        zero_form = i18n_system.get_translation("items.count", SupportedLanguage.ENGLISH, count=0)
        assert zero_form == "No items"
        
        one_form = i18n_system.get_translation("items.count", SupportedLanguage.ENGLISH, count=1)
        assert one_form == "1 item"
        
        other_form = i18n_system.get_translation("items.count", SupportedLanguage.ENGLISH, count=5)
        assert other_form == "{count} items"
    
    def test_variable_substitution(self, i18n_system):
        """Test variable substitution in translations"""
        # Add translation with variables
        i18n_system.add_translation(
            "welcome.message",
            SupportedLanguage.ENGLISH,
            "Welcome, {name}! You have {count} messages."
        )
        
        # Test variable substitution
        message = i18n_system.get_translation(
            "welcome.message", 
            SupportedLanguage.ENGLISH,
            name="John",
            count=5
        )
        assert message == "Welcome, John! You have 5 messages."
    
    def test_locale_configuration(self, i18n_system):
        """Test locale configuration management"""
        # Get a locale configuration
        us_locale = i18n_system.get_locale_config(SupportedLanguage.ENGLISH, "US")
        
        assert us_locale is not None
        assert us_locale.language == SupportedLanguage.ENGLISH
        assert us_locale.country_code == "US"
        assert us_locale.currency == SupportedCurrency.USD
        assert us_locale.compliance_region == ComplianceRegion.CCPA
        assert us_locale.rtl == False
        
        # Test RTL locale
        arabic_locale = i18n_system.get_locale_config(SupportedLanguage.ARABIC, "SA")
        if arabic_locale:
            assert arabic_locale.rtl == True
    
    def test_user_preferences(self, i18n_system):
        """Test user preference management"""
        user_id = "test_user_123"
        
        # Set user preferences
        i18n_system.set_user_locale(
            user_id,
            SupportedLanguage.SPANISH,
            SupportedCurrency.EUR,
            "Europe/Madrid"
        )
        
        # Get user preferences
        preferences = i18n_system.get_user_locale(user_id)
        
        assert preferences is not None
        assert preferences["language"] == "es"
        assert preferences["currency"] == "EUR"
        assert preferences["timezone"] == "Europe/Madrid"
        
        # Test non-existent user
        missing_prefs = i18n_system.get_user_locale("nonexistent_user")
        assert missing_prefs is None
    
    def test_currency_management(self, i18n_system):
        """Test currency rate management and conversion"""
        # Add currency rates
        i18n_system.add_currency_rate(SupportedCurrency.USD, SupportedCurrency.EUR, 0.85)
        i18n_system.add_currency_rate(SupportedCurrency.EUR, SupportedCurrency.USD, 1.18)
        
        # Test getting currency rates
        usd_to_eur = i18n_system.get_currency_rate(SupportedCurrency.USD, SupportedCurrency.EUR)
        assert usd_to_eur == 0.85
        
        eur_to_usd = i18n_system.get_currency_rate(SupportedCurrency.EUR, SupportedCurrency.USD)
        assert eur_to_usd == 1.18
        
        # Test same currency rate
        same_currency = i18n_system.get_currency_rate(SupportedCurrency.USD, SupportedCurrency.USD)
        assert same_currency == 1.0
        
        # Test currency conversion
        converted_amount = i18n_system.convert_currency(100, SupportedCurrency.USD, SupportedCurrency.EUR)
        assert converted_amount == 85.0
        
        # Test missing rate
        missing_rate = i18n_system.get_currency_rate(SupportedCurrency.USD, SupportedCurrency.JPY)
        assert missing_rate is None
        
        missing_conversion = i18n_system.convert_currency(100, SupportedCurrency.USD, SupportedCurrency.JPY)
        assert missing_conversion is None
    
    def test_currency_formatting(self, i18n_system):
        """Test currency formatting"""
        # Test USD formatting
        usd_formatted = i18n_system.format_currency(1234.56, SupportedCurrency.USD, "en_US")
        assert "$" in usd_formatted
        assert "1,234.56" in usd_formatted or "1234.56" in usd_formatted
        
        # Test EUR formatting
        eur_formatted = i18n_system.format_currency(1234.56, SupportedCurrency.EUR, "de_DE")
        assert "EUR" in eur_formatted or "€" in eur_formatted
    
    def test_regional_pricing(self, i18n_system):
        """Test regional pricing management"""
        # Add regional pricing
        pricing_tiers = {"basic": 1.0, "pro": 1.2, "enterprise": 1.5}
        
        i18n_system.add_regional_pricing(
            "EU",
            SupportedCurrency.EUR,
            0.85,  # Base multiplier
            0.20,  # 20% VAT
            "VAT",
            pricing_tiers
        )
        
        # Get regional pricing
        eu_pricing = i18n_system.get_regional_pricing("EU")
        
        assert eu_pricing is not None
        assert eu_pricing.region == "EU"
        assert eu_pricing.currency == SupportedCurrency.EUR
        assert eu_pricing.base_price_multiplier == 0.85
        assert eu_pricing.tax_rate == 0.20
        assert eu_pricing.tax_name == "VAT"
        assert eu_pricing.pricing_tiers["pro"] == 1.2
        
        # Test price calculation
        pricing = i18n_system.calculate_regional_price(100.0, "EU", "pro")
        
        assert pricing["base_price"] == 100.0
        assert pricing["regional_price"] == 100.0 * 0.85 * 1.2  # Base * multiplier * tier
        assert pricing["currency"] == "EUR"
        assert pricing["tax_name"] == "VAT"
        assert pricing["tax_rate"] == 0.20
        
        # Calculate expected values
        expected_regional = 100.0 * 0.85 * 1.2
        expected_tax = expected_regional * 0.20
        expected_total = expected_regional + expected_tax
        
        assert abs(pricing["tax"] - expected_tax) < 0.01
        assert abs(pricing["total_price"] - expected_total) < 0.01
    
    def test_date_time_formatting(self, i18n_system):
        """Test date and time formatting"""
        test_date = datetime(2024, 8, 6, 14, 30, 0)
        
        # Test US date formatting
        us_date = i18n_system.format_date(test_date, SupportedLanguage.ENGLISH, "US")
        assert "08/06/2024" in us_date or "8/6/2024" in us_date
        
        # Test US time formatting
        us_time = i18n_system.format_time(test_date, SupportedLanguage.ENGLISH, "US")
        assert "2:30 PM" in us_time or "14:30" in us_time
        
        # Test German date formatting
        de_date = i18n_system.format_date(test_date, SupportedLanguage.GERMAN, "DE")
        assert "06.08.2024" in de_date or "6.8.2024" in de_date
    
    def test_number_formatting(self, i18n_system):
        """Test number formatting"""
        test_number = 1234.56
        
        # Test US number formatting
        us_number = i18n_system.format_number(test_number, SupportedLanguage.ENGLISH, "US")
        assert "1,234.56" in us_number or "1234.56" in us_number
        
        # Test German number formatting (uses comma for decimal)
        de_number = i18n_system.format_number(test_number, SupportedLanguage.GERMAN, "DE")
        # German formatting might use different separators
        assert "1234" in de_number
    
    def test_compliance_requirements(self, i18n_system):
        """Test compliance requirements"""
        # Test GDPR requirements
        gdpr_requirements = i18n_system.get_compliance_requirements(ComplianceRegion.GDPR)
        
        assert gdpr_requirements["name"] == "General Data Protection Regulation"
        assert gdpr_requirements["consent_required"] == True
        assert gdpr_requirements["right_to_deletion"] == True
        assert gdpr_requirements["breach_notification_hours"] == 72
        assert gdpr_requirements["age_of_consent"] == 16
        
        # Test CCPA requirements
        ccpa_requirements = i18n_system.get_compliance_requirements(ComplianceRegion.CCPA)
        
        assert ccpa_requirements["name"] == "California Consumer Privacy Act"
        assert ccpa_requirements["consent_required"] == False
        assert ccpa_requirements["do_not_sell_required"] == True
        assert ccpa_requirements["age_of_consent"] == 13
    
    def test_compliance_checking(self, i18n_system):
        """Test compliance checking"""
        # Test compliant user
        compliant_status = i18n_system.check_compliance(ComplianceRegion.GDPR, 18)
        
        assert compliant_status["region"] == "gdpr"
        assert compliant_status["compliant"] == True
        assert len(compliant_status["required_actions"]) > 0
        
        # Test non-compliant user (under age)
        non_compliant_status = i18n_system.check_compliance(ComplianceRegion.GDPR, 15)
        
        assert non_compliant_status["compliant"] == False
        assert "User below age of consent" in non_compliant_status["issues"]
        assert "Obtain parental consent" in non_compliant_status["required_actions"]
    
    def test_cultural_preferences(self, i18n_system):
        """Test cultural preferences"""
        # Test US cultural preferences
        us_culture = i18n_system.get_cultural_preferences(SupportedLanguage.ENGLISH, "US")
        
        assert "color_preferences" in us_culture
        assert "communication_style" in us_culture
        assert us_culture["communication_style"] == "direct"
        assert "saturday" in us_culture["weekend_days"]
        
        # Test Chinese cultural preferences
        cn_culture = i18n_system.get_cultural_preferences(SupportedLanguage.CHINESE_SIMPLIFIED, "CN")
        
        assert "lucky_numbers" in cn_culture
        assert 8 in cn_culture["lucky_numbers"]
        assert 4 in cn_culture["unlucky_numbers"]
        assert us_culture["communication_style"] == "indirect"
        
        # Test Arabic RTL preferences
        ar_culture = i18n_system.get_cultural_preferences(SupportedLanguage.ARABIC, "SA")
        
        assert ar_culture.get("rtl") == True
        assert "friday" in ar_culture["weekend_days"]
    
    def test_supported_languages(self, i18n_system):
        """Test supported languages functionality"""
        languages = i18n_system.get_supported_languages()
        
        assert len(languages) == len(SupportedLanguage)
        
        # Check that each language has required fields
        for lang in languages:
            assert "code" in lang
            assert "name" in lang
            assert "native_name" in lang
        
        # Test specific language names
        english_name = i18n_system.get_language_name(SupportedLanguage.ENGLISH)
        assert english_name == "English"
        
        native_chinese = i18n_system.get_native_language_name(SupportedLanguage.CHINESE_SIMPLIFIED)
        assert native_chinese == "简体中文"
    
    def test_sample_data_loading(self, i18n_system):
        """Test sample data loading"""
        # Load sample data
        i18n_system.load_sample_data()
        
        # Test that currency rates were loaded
        usd_to_eur = i18n_system.get_currency_rate(SupportedCurrency.USD, SupportedCurrency.EUR)
        assert usd_to_eur is not None
        assert usd_to_eur > 0
        
        # Test that regional pricing was loaded
        us_pricing = i18n_system.get_regional_pricing("US")
        assert us_pricing is not None
        assert us_pricing.currency == SupportedCurrency.USD
        
        eu_pricing = i18n_system.get_regional_pricing("EU")
        assert eu_pricing is not None
        assert eu_pricing.currency == SupportedCurrency.EUR
    
    def test_error_handling(self, i18n_system):
        """Test error handling for edge cases"""
        # Test invalid locale
        invalid_locale = i18n_system.get_locale_config(SupportedLanguage.ENGLISH, "INVALID")
        assert invalid_locale is None
        
        # Test invalid regional pricing
        invalid_pricing = i18n_system.get_regional_pricing("INVALID_REGION")
        assert invalid_pricing is None
        
        # Test price calculation for invalid region
        invalid_price = i18n_system.calculate_regional_price(100.0, "INVALID_REGION")
        assert invalid_price["currency"] == "USD"  # Falls back to default
        assert invalid_price["total_price"] == 100.0  # No tax applied

def test_integration_workflow():
    """Integration test for the complete internationalization workflow"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name
    
    try:
        i18n = InternationalizationSystem(db_path)
        
        # Step 1: Load sample data
        i18n.load_sample_data()
        
        # Step 2: Set user preferences
        user_id = "integration_test_user"
        i18n.set_user_locale(user_id, SupportedLanguage.SPANISH, SupportedCurrency.EUR, "Europe/Madrid")
        
        # Step 3: Get user preferences
        preferences = i18n.get_user_locale(user_id)
        assert preferences["language"] == "es"
        assert preferences["currency"] == "EUR"
        
        # Step 4: Test translations
        spanish_home = i18n.get_translation("nav.home", SupportedLanguage.SPANISH)
        assert spanish_home == "Inicio"
        
        # Step 5: Test currency conversion
        converted = i18n.convert_currency(100, SupportedCurrency.USD, SupportedCurrency.EUR)
        assert converted is not None
        assert converted > 0
        
        # Step 6: Test regional pricing
        eu_pricing = i18n.calculate_regional_price(99.0, "EU", "pro")
        assert eu_pricing["currency"] == "EUR"
        assert eu_pricing["tax_rate"] > 0
        
        # Step 7: Test compliance
        compliance = i18n.check_compliance(ComplianceRegion.GDPR, 25)
        assert compliance["region"] == "gdpr"
        assert len(compliance["required_actions"]) > 0
        
        # Step 8: Test cultural preferences
        culture = i18n.get_cultural_preferences(SupportedLanguage.SPANISH, "ES")
        assert "color_preferences" in culture
        
        # Step 9: Test formatting
        test_date = datetime.now()
        formatted_date = i18n.format_date(test_date, SupportedLanguage.SPANISH, "ES")
        assert len(formatted_date) > 0
        
        print("✅ Integration test completed successfully!")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    # Run integration test
    test_integration_workflow()
    
    # Run pytest if available
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic integration test only")
        print("Install pytest to run full test suite: pip install pytest")