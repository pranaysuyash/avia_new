"""
Internationalization and Localization System
Implements multi-language UI support, currency handling, regional pricing, 
compliance requirements, and cultural customization
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from babel import Locale, dates, numbers
from babel.core import get_global
from babel.support import Translations
import gettext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupportedLanguage(Enum):
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE_SIMPLIFIED = "zh_CN"
    CHINESE_TRADITIONAL = "zh_TW"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HINDI = "hi"
    DUTCH = "nl"
    SWEDISH = "sv"

class SupportedCurrency(Enum):
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    CAD = "CAD"  # Canadian Dollar
    AUD = "AUD"  # Australian Dollar
    JPY = "JPY"  # Japanese Yen
    CNY = "CNY"  # Chinese Yuan
    INR = "INR"  # Indian Rupee
    BRL = "BRL"  # Brazilian Real
    MXN = "MXN"  # Mexican Peso
    KRW = "KRW"  # South Korean Won
    SEK = "SEK"  # Swedish Krona
    NOK = "NOK"  # Norwegian Krone
    CHF = "CHF"  # Swiss Franc
    SGD = "SGD"  # Singapore Dollar

class ComplianceRegion(Enum):
    GDPR = "gdpr"      # European Union
    CCPA = "ccpa"      # California, USA
    PIPEDA = "pipeda"  # Canada
    LGPD = "lgpd"      # Brazil
    PDPA = "pdpa"      # Singapore
    APPI = "appi"      # Japan

@dataclass
class LocaleConfig:
    language: SupportedLanguage
    country_code: str
    currency: SupportedCurrency
    date_format: str
    time_format: str
    number_format: str
    rtl: bool = False
    compliance_region: Optional[ComplianceRegion] = None

@dataclass
class TranslationEntry:
    key: str
    language: SupportedLanguage
    translation: str
    context: Optional[str] = None
    pluralization: Optional[Dict[str, str]] = None

@dataclass
class CurrencyRate:
    from_currency: SupportedCurrency
    to_currency: SupportedCurrency
    rate: float
    last_updated: datetime

@dataclass
class RegionalPricing:
    region: str
    currency: SupportedCurrency
    base_price_multiplier: float
    tax_rate: float
    tax_name: str
    pricing_tiers: Dict[str, float]

class InternationalizationSystem:
    def __init__(self, db_path: str = "i18n_localization.db"):
        self.db_path = db_path
        self.current_locale = None
        self.translations = {}
        self.currency_rates = {}
        self.regional_pricing = {}
        self.init_database()
        self.load_default_translations()
        self.load_default_locales()
        
    def init_database(self):
        """Initialize the internationalization database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Translations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL,
                language TEXT NOT NULL,
                translation TEXT NOT NULL,
                context TEXT,
                pluralization TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(key, language)
            )
        ''')
        
        # Locales configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locales (
                id TEXT PRIMARY KEY,
                language TEXT NOT NULL,
                country_code TEXT NOT NULL,
                currency TEXT NOT NULL,
                date_format TEXT NOT NULL,
                time_format TEXT NOT NULL,
                number_format TEXT NOT NULL,
                rtl BOOLEAN DEFAULT 0,
                compliance_region TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(language, country_code)
            )
        ''')
        
        # Currency rates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS currency_rates (
                id TEXT PRIMARY KEY,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                rate REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_currency, to_currency)
            )
        ''')
        
        # Regional pricing table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regional_pricing (
                id TEXT PRIMARY KEY,
                region TEXT NOT NULL,
                currency TEXT NOT NULL,
                base_price_multiplier REAL DEFAULT 1.0,
                tax_rate REAL DEFAULT 0.0,
                tax_name TEXT DEFAULT 'Tax',
                pricing_tiers TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(region)
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                language TEXT NOT NULL,
                currency TEXT NOT NULL,
                timezone TEXT DEFAULT 'UTC',
                date_format TEXT,
                number_format TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Internationalization database initialized successfully")

    def load_default_translations(self):
        """Load default translations for supported languages"""
        default_translations = {
            # Navigation and UI
            "nav.home": {
                "en": "Home",
                "es": "Inicio",
                "fr": "Accueil",
                "de": "Startseite",
                "it": "Home",
                "pt": "Início",
                "ru": "Главная",
                "zh_CN": "首页",
                "zh_TW": "首頁",
                "ja": "ホーム",
                "ko": "홈",
                "ar": "الرئيسية",
                "hi": "होम",
                "nl": "Home",
                "sv": "Hem"
            },
            "nav.transcription": {
                "en": "Transcription",
                "es": "Transcripción",
                "fr": "Transcription",
                "de": "Transkription",
                "it": "Trascrizione",
                "pt": "Transcrição",
                "ru": "Транскрипция",
                "zh_CN": "转录",
                "zh_TW": "轉錄",
                "ja": "転写",
                "ko": "전사",
                "ar": "النسخ",
                "hi": "प्रतिलेखन",
                "nl": "Transcriptie",
                "sv": "Transkription"
            },
            "nav.analytics": {
                "en": "Analytics",
                "es": "Análisis",
                "fr": "Analytique",
                "de": "Analytik",
                "it": "Analisi",
                "pt": "Análise",
                "ru": "Аналитика",
                "zh_CN": "分析",
                "zh_TW": "分析",
                "ja": "分析",
                "ko": "분석",
                "ar": "التحليلات",
                "hi": "विश्लेषण",
                "nl": "Analytics",
                "sv": "Analys"
            },
            # Actions
            "action.upload": {
                "en": "Upload",
                "es": "Subir",
                "fr": "Télécharger",
                "de": "Hochladen",
                "it": "Carica",
                "pt": "Carregar",
                "ru": "Загрузить",
                "zh_CN": "上传",
                "zh_TW": "上傳",
                "ja": "アップロード",
                "ko": "업로드",
                "ar": "رفع",
                "hi": "अपलोड",
                "nl": "Uploaden",
                "sv": "Ladda upp"
            },
            "action.download": {
                "en": "Download",
                "es": "Descargar",
                "fr": "Télécharger",
                "de": "Herunterladen",
                "it": "Scarica",
                "pt": "Baixar",
                "ru": "Скачать",
                "zh_CN": "下载",
                "zh_TW": "下載",
                "ja": "ダウンロード",
                "ko": "다운로드",
                "ar": "تحميل",
                "hi": "डाउनलोड",
                "nl": "Downloaden",
                "sv": "Ladda ner"
            },
            # Status messages
            "status.processing": {
                "en": "Processing...",
                "es": "Procesando...",
                "fr": "Traitement en cours...",
                "de": "Verarbeitung...",
                "it": "Elaborazione...",
                "pt": "Processando...",
                "ru": "Обработка...",
                "zh_CN": "处理中...",
                "zh_TW": "處理中...",
                "ja": "処理中...",
                "ko": "처리 중...",
                "ar": "جاري المعالجة...",
                "hi": "प्रसंस्करण...",
                "nl": "Verwerken...",
                "sv": "Bearbetar..."
            },
            "status.completed": {
                "en": "Completed",
                "es": "Completado",
                "fr": "Terminé",
                "de": "Abgeschlossen",
                "it": "Completato",
                "pt": "Concluído",
                "ru": "Завершено",
                "zh_CN": "已完成",
                "zh_TW": "已完成",
                "ja": "完了",
                "ko": "완료",
                "ar": "مكتمل",
                "hi": "पूर्ण",
                "nl": "Voltooid",
                "sv": "Slutförd"
            },
            # Subscription and pricing
            "pricing.free": {
                "en": "Free",
                "es": "Gratis",
                "fr": "Gratuit",
                "de": "Kostenlos",
                "it": "Gratuito",
                "pt": "Grátis",
                "ru": "Бесплатно",
                "zh_CN": "免费",
                "zh_TW": "免費",
                "ja": "無料",
                "ko": "무료",
                "ar": "مجاني",
                "hi": "मुफ्त",
                "nl": "Gratis",
                "sv": "Gratis"
            },
            "pricing.monthly": {
                "en": "Monthly",
                "es": "Mensual",
                "fr": "Mensuel",
                "de": "Monatlich",
                "it": "Mensile",
                "pt": "Mensal",
                "ru": "Ежемесячно",
                "zh_CN": "每月",
                "zh_TW": "每月",
                "ja": "月額",
                "ko": "월간",
                "ar": "شهري",
                "hi": "मासिक",
                "nl": "Maandelijks",
                "sv": "Månadsvis"
            }
        }
        
        # Store translations in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for key, translations in default_translations.items():
            for lang_code, translation in translations.items():
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO translations (id, key, language, translation)
                        VALUES (?, ?, ?, ?)
                    ''', (f"{key}_{lang_code}", key, lang_code, translation))
                except Exception as e:
                    logger.error(f"Error inserting translation {key}_{lang_code}: {e}")
        
        conn.commit()
        conn.close()
        logger.info("Default translations loaded successfully")
    
    def load_default_locales(self):
        """Load default locale configurations"""
        default_locales = [
            # English locales
            LocaleConfig(SupportedLanguage.ENGLISH, "US", SupportedCurrency.USD, 
                        "%m/%d/%Y", "%I:%M %p", "#,##0.00", False, ComplianceRegion.CCPA),
            LocaleConfig(SupportedLanguage.ENGLISH, "GB", SupportedCurrency.GBP, 
                        "%d/%m/%Y", "%H:%M", "#,##0.00", False, ComplianceRegion.GDPR),
            LocaleConfig(SupportedLanguage.ENGLISH, "CA", SupportedCurrency.CAD, 
                        "%Y-%m-%d", "%H:%M", "#,##0.00", False, ComplianceRegion.PIPEDA),
            LocaleConfig(SupportedLanguage.ENGLISH, "AU", SupportedCurrency.AUD, 
                        "%d/%m/%Y", "%H:%M", "#,##0.00", False),
            
            # European locales
            LocaleConfig(SupportedLanguage.SPANISH, "ES", SupportedCurrency.EUR, 
                        "%d/%m/%Y", "%H:%M", "#.##0,00", False, ComplianceRegion.GDPR),
            LocaleConfig(SupportedLanguage.FRENCH, "FR", SupportedCurrency.EUR, 
                        "%d/%m/%Y", "%H:%M", "# ##0,00", False, ComplianceRegion.GDPR),
            LocaleConfig(SupportedLanguage.GERMAN, "DE", SupportedCurrency.EUR, 
                        "%d.%m.%Y", "%H:%M", "#.##0,00", False, ComplianceRegion.GDPR),
            LocaleConfig(SupportedLanguage.ITALIAN, "IT", SupportedCurrency.EUR, 
                        "%d/%m/%Y", "%H:%M", "#.##0,00", False, ComplianceRegion.GDPR),
            LocaleConfig(SupportedLanguage.PORTUGUESE, "PT", SupportedCurrency.EUR, 
                        "%d-%m-%Y", "%H:%M", "# ##0,00", False, ComplianceRegion.GDPR),
            LocaleConfig(SupportedLanguage.DUTCH, "NL", SupportedCurrency.EUR, 
                        "%d-%m-%Y", "%H:%M", "#.##0,00", False, ComplianceRegion.GDPR),
            LocaleConfig(SupportedLanguage.SWEDISH, "SE", SupportedCurrency.SEK, 
                        "%Y-%m-%d", "%H:%M", "# ##0,00", False, ComplianceRegion.GDPR),
            
            # Asian locales
            LocaleConfig(SupportedLanguage.CHINESE_SIMPLIFIED, "CN", SupportedCurrency.CNY, 
                        "%Y/%m/%d", "%H:%M", "#,##0.00", False),
            LocaleConfig(SupportedLanguage.CHINESE_TRADITIONAL, "TW", SupportedCurrency.USD, 
                        "%Y/%m/%d", "%H:%M", "#,##0.00", False),
            LocaleConfig(SupportedLanguage.JAPANESE, "JP", SupportedCurrency.JPY, 
                        "%Y/%m/%d", "%H:%M", "#,##0", False, ComplianceRegion.APPI),
            LocaleConfig(SupportedLanguage.KOREAN, "KR", SupportedCurrency.KRW, 
                        "%Y.%m.%d", "%H:%M", "#,##0", False),
            LocaleConfig(SupportedLanguage.HINDI, "IN", SupportedCurrency.INR, 
                        "%d/%m/%Y", "%H:%M", "#,##,##0.00", False),
            
            # Other locales
            LocaleConfig(SupportedLanguage.PORTUGUESE, "BR", SupportedCurrency.BRL, 
                        "%d/%m/%Y", "%H:%M", "#.##0,00", False, ComplianceRegion.LGPD),
            LocaleConfig(SupportedLanguage.SPANISH, "MX", SupportedCurrency.MXN, 
                        "%d/%m/%Y", "%H:%M", "#,##0.00", False),
            LocaleConfig(SupportedLanguage.RUSSIAN, "RU", SupportedCurrency.USD, 
                        "%d.%m.%Y", "%H:%M", "# ##0,00", False),
            LocaleConfig(SupportedLanguage.ARABIC, "SA", SupportedCurrency.USD, 
                        "%d/%m/%Y", "%H:%M", "#,##0.00", True),
        ]
        
        # Store locales in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for locale in default_locales:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO locales 
                    (id, language, country_code, currency, date_format, time_format, 
                     number_format, rtl, compliance_region)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"{locale.language.value}_{locale.country_code}",
                    locale.language.value,
                    locale.country_code,
                    locale.currency.value,
                    locale.date_format,
                    locale.time_format,
                    locale.number_format,
                    locale.rtl,
                    locale.compliance_region.value if locale.compliance_region else None
                ))
            except Exception as e:
                logger.error(f"Error inserting locale {locale.language.value}_{locale.country_code}: {e}")
        
        conn.commit()
        conn.close()
        logger.info("Default locales loaded successfully")
    
    # Translation Management
    def add_translation(self, key: str, language: SupportedLanguage, 
                       translation: str, context: Optional[str] = None,
                       pluralization: Optional[Dict[str, str]] = None):
        """Add or update a translation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        translation_id = f"{key}_{language.value}"
        pluralization_json = json.dumps(pluralization) if pluralization else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO translations 
            (id, key, language, translation, context, pluralization)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (translation_id, key, language.value, translation, context, pluralization_json))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added translation for {key} in {language.value}")

    def get_translation(self, key: str, language: SupportedLanguage, 
                       count: Optional[int] = None, **kwargs) -> str:
        """Get translation for a key in specified language"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT translation, pluralization FROM translations 
            WHERE key = ? AND language = ?
        ''', (key, language.value))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            # Fallback to English if translation not found
            if language != SupportedLanguage.ENGLISH:
                return self.get_translation(key, SupportedLanguage.ENGLISH, count, **kwargs)
            else:
                return f"[{key}]"  # Return key if no translation found
        
        translation, pluralization_json = result
        
        # Handle pluralization
        if count is not None and pluralization_json:
            try:
                pluralization = json.loads(pluralization_json)
                if count == 0 and 'zero' in pluralization:
                    translation = pluralization['zero']
                elif count == 1 and 'one' in pluralization:
                    translation = pluralization['one']
                elif 'other' in pluralization:
                    translation = pluralization['other']
            except json.JSONDecodeError:
                pass
        
        # Handle variable substitution
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError:
                pass  # Ignore missing variables
        
        return translation

    def get_all_translations(self, language: SupportedLanguage) -> Dict[str, str]:
        """Get all translations for a language"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, translation FROM translations 
            WHERE language = ?
        ''', (language.value,))
        
        translations = dict(cursor.fetchall())
        conn.close()
        
        return translations

    # Locale Management
    def set_user_locale(self, user_id: str, language: SupportedLanguage, 
                       currency: SupportedCurrency, timezone: str = "UTC"):
        """Set user's locale preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences 
            (user_id, language, currency, timezone)
            VALUES (?, ?, ?, ?)
        ''', (user_id, language.value, currency.value, timezone))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Set locale for user {user_id}: {language.value}, {currency.value}")

    def get_user_locale(self, user_id: str) -> Optional[Dict[str, str]]:
        """Get user's locale preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT language, currency, timezone FROM user_preferences 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "language": result[0],
                "currency": result[1],
                "timezone": result[2]
            }
        return None

    def get_locale_config(self, language: SupportedLanguage, 
                         country_code: str) -> Optional[LocaleConfig]:
        """Get locale configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT language, country_code, currency, date_format, time_format,
                   number_format, rtl, compliance_region
            FROM locales 
            WHERE language = ? AND country_code = ?
        ''', (language.value, country_code))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return LocaleConfig(
                language=SupportedLanguage(result[0]),
                country_code=result[1],
                currency=SupportedCurrency(result[2]),
                date_format=result[3],
                time_format=result[4],
                number_format=result[5],
                rtl=bool(result[6]),
                compliance_region=ComplianceRegion(result[7]) if result[7] else None
            )
        return None   
 # Currency and Pricing
    def add_currency_rate(self, from_currency: SupportedCurrency, 
                         to_currency: SupportedCurrency, rate: float):
        """Add or update currency exchange rate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        rate_id = f"{from_currency.value}_{to_currency.value}"
        
        cursor.execute('''
            INSERT OR REPLACE INTO currency_rates 
            (id, from_currency, to_currency, rate, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (rate_id, from_currency.value, to_currency.value, rate, datetime.now()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated currency rate: {from_currency.value} to {to_currency.value} = {rate}")

    def get_currency_rate(self, from_currency: SupportedCurrency, 
                         to_currency: SupportedCurrency) -> Optional[float]:
        """Get currency exchange rate"""
        if from_currency == to_currency:
            return 1.0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT rate FROM currency_rates 
            WHERE from_currency = ? AND to_currency = ?
        ''', (from_currency.value, to_currency.value))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None

    def convert_currency(self, amount: float, from_currency: SupportedCurrency, 
                        to_currency: SupportedCurrency) -> Optional[float]:
        """Convert amount from one currency to another"""
        rate = self.get_currency_rate(from_currency, to_currency)
        if rate is not None:
            return amount * rate
        return None

    def format_currency(self, amount: float, currency: SupportedCurrency, 
                       locale_code: str = "en_US") -> str:
        """Format currency amount according to locale"""
        try:
            locale = Locale.parse(locale_code)
            return numbers.format_currency(amount, currency.value, locale=locale)
        except Exception:
            # Fallback formatting
            return f"{currency.value} {amount:.2f}"

    # Regional Pricing
    def add_regional_pricing(self, region: str, currency: SupportedCurrency,
                           base_price_multiplier: float = 1.0, tax_rate: float = 0.0,
                           tax_name: str = "Tax", pricing_tiers: Dict[str, float] = None):
        """Add regional pricing configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        pricing_tiers_json = json.dumps(pricing_tiers or {})
        
        cursor.execute('''
            INSERT OR REPLACE INTO regional_pricing 
            (id, region, currency, base_price_multiplier, tax_rate, tax_name, pricing_tiers)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (region, region, currency.value, base_price_multiplier, 
              tax_rate, tax_name, pricing_tiers_json))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added regional pricing for {region}")

    def get_regional_pricing(self, region: str) -> Optional[RegionalPricing]:
        """Get regional pricing configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT region, currency, base_price_multiplier, tax_rate, 
                   tax_name, pricing_tiers
            FROM regional_pricing WHERE region = ?
        ''', (region,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            pricing_tiers = json.loads(result[5]) if result[5] else {}
            return RegionalPricing(
                region=result[0],
                currency=SupportedCurrency(result[1]),
                base_price_multiplier=result[2],
                tax_rate=result[3],
                tax_name=result[4],
                pricing_tiers=pricing_tiers
            )
        return None

    def calculate_regional_price(self, base_price: float, region: str, 
                               tier: str = "basic") -> Dict[str, Any]:
        """Calculate price for a specific region and tier"""
        regional_pricing = self.get_regional_pricing(region)
        
        if not regional_pricing:
            return {
                "base_price": base_price,
                "regional_price": base_price,
                "tax": 0.0,
                "total_price": base_price,
                "currency": SupportedCurrency.USD.value,
                "tax_name": "Tax"
            }
        
        # Apply regional multiplier
        regional_price = base_price * regional_pricing.base_price_multiplier
        
        # Apply tier-specific pricing if available
        if tier in regional_pricing.pricing_tiers:
            regional_price *= regional_pricing.pricing_tiers[tier]
        
        # Calculate tax
        tax_amount = regional_price * regional_pricing.tax_rate
        total_price = regional_price + tax_amount
        
        return {
            "base_price": base_price,
            "regional_price": regional_price,
            "tax": tax_amount,
            "total_price": total_price,
            "currency": regional_pricing.currency.value,
            "tax_name": regional_pricing.tax_name,
            "tax_rate": regional_pricing.tax_rate
        }

    # Date and Number Formatting
    def format_date(self, date: datetime, language: SupportedLanguage, 
                   country_code: str = "US") -> str:
        """Format date according to locale"""
        locale_config = self.get_locale_config(language, country_code)
        if locale_config:
            try:
                return date.strftime(locale_config.date_format)
            except Exception:
                pass
        
        # Fallback to default format
        return date.strftime("%Y-%m-%d")

    def format_time(self, time: datetime, language: SupportedLanguage, 
                   country_code: str = "US") -> str:
        """Format time according to locale"""
        locale_config = self.get_locale_config(language, country_code)
        if locale_config:
            try:
                return time.strftime(locale_config.time_format)
            except Exception:
                pass
        
        # Fallback to default format
        return time.strftime("%H:%M")

    def format_number(self, number: float, language: SupportedLanguage, 
                     country_code: str = "US") -> str:
        """Format number according to locale"""
        try:
            locale_code = f"{language.value}_{country_code}"
            locale = Locale.parse(locale_code)
            return numbers.format_decimal(number, locale=locale)
        except Exception:
            # Fallback formatting
            return f"{number:,.2f}"
    
    # Compliance Management
    def get_compliance_requirements(self, region: ComplianceRegion) -> Dict[str, Any]:
        """Get compliance requirements for a region"""
        compliance_data = {
            ComplianceRegion.GDPR: {
                "name": "General Data Protection Regulation",
                "region": "European Union",
                "data_retention_max_days": 2555,  # 7 years
                "consent_required": True,
                "right_to_deletion": True,
                "right_to_portability": True,
                "data_protection_officer_required": True,
                "breach_notification_hours": 72,
                "privacy_policy_required": True,
                "cookie_consent_required": True,
                "age_of_consent": 16
            },
            ComplianceRegion.CCPA: {
                "name": "California Consumer Privacy Act",
                "region": "California, USA",
                "data_retention_max_days": 1095,  # 3 years
                "consent_required": False,
                "right_to_deletion": True,
                "right_to_portability": True,
                "data_protection_officer_required": False,
                "breach_notification_hours": None,
                "privacy_policy_required": True,
                "cookie_consent_required": False,
                "age_of_consent": 13,
                "do_not_sell_required": True
            },
            ComplianceRegion.PIPEDA: {
                "name": "Personal Information Protection and Electronic Documents Act",
                "region": "Canada",
                "data_retention_max_days": 2555,  # 7 years
                "consent_required": True,
                "right_to_deletion": True,
                "right_to_portability": True,
                "data_protection_officer_required": False,
                "breach_notification_hours": 72,
                "privacy_policy_required": True,
                "cookie_consent_required": True,
                "age_of_consent": 13
            },
            ComplianceRegion.LGPD: {
                "name": "Lei Geral de Proteção de Dados",
                "region": "Brazil",
                "data_retention_max_days": 1825,  # 5 years
                "consent_required": True,
                "right_to_deletion": True,
                "right_to_portability": True,
                "data_protection_officer_required": True,
                "breach_notification_hours": 72,
                "privacy_policy_required": True,
                "cookie_consent_required": True,
                "age_of_consent": 13
            },
            ComplianceRegion.PDPA: {
                "name": "Personal Data Protection Act",
                "region": "Singapore",
                "data_retention_max_days": 1095,  # 3 years
                "consent_required": True,
                "right_to_deletion": True,
                "right_to_portability": False,
                "data_protection_officer_required": True,
                "breach_notification_hours": 72,
                "privacy_policy_required": True,
                "cookie_consent_required": True,
                "age_of_consent": 13
            },
            ComplianceRegion.APPI: {
                "name": "Act on Protection of Personal Information",
                "region": "Japan",
                "data_retention_max_days": 1825,  # 5 years
                "consent_required": True,
                "right_to_deletion": True,
                "right_to_portability": False,
                "data_protection_officer_required": False,
                "breach_notification_hours": 72,
                "privacy_policy_required": True,
                "cookie_consent_required": False,
                "age_of_consent": 13
            }
        }
        
        return compliance_data.get(region, {})

    def check_compliance(self, user_region: ComplianceRegion, 
                        user_age: Optional[int] = None) -> Dict[str, Any]:
        """Check compliance requirements for a user"""
        requirements = self.get_compliance_requirements(user_region)
        
        compliance_status = {
            "region": user_region.value,
            "requirements": requirements,
            "compliant": True,
            "issues": [],
            "required_actions": []
        }
        
        # Check age compliance
        if user_age is not None and requirements.get("age_of_consent"):
            if user_age < requirements["age_of_consent"]:
                compliance_status["compliant"] = False
                compliance_status["issues"].append("User below age of consent")
                compliance_status["required_actions"].append("Obtain parental consent")
        
        # Add required compliance actions
        if requirements.get("consent_required"):
            compliance_status["required_actions"].append("Obtain explicit user consent")
        
        if requirements.get("privacy_policy_required"):
            compliance_status["required_actions"].append("Display privacy policy")
        
        if requirements.get("cookie_consent_required"):
            compliance_status["required_actions"].append("Obtain cookie consent")
        
        if requirements.get("do_not_sell_required"):
            compliance_status["required_actions"].append("Provide 'Do Not Sell' option")
        
        return compliance_status

    # Cultural Customization
    def get_cultural_preferences(self, language: SupportedLanguage, 
                               country_code: str) -> Dict[str, Any]:
        """Get cultural preferences for a locale"""
        cultural_data = {
            "en_US": {
                "color_preferences": ["blue", "green", "red"],
                "image_style": "professional",
                "communication_style": "direct",
                "business_hours": "9:00-17:00",
                "weekend_days": ["saturday", "sunday"]
            },
            "zh_CN": {
                "color_preferences": ["red", "gold", "yellow"],
                "image_style": "harmonious",
                "communication_style": "indirect",
                "business_hours": "9:00-18:00",
                "weekend_days": ["saturday", "sunday"],
                "lucky_numbers": [8, 9],
                "unlucky_numbers": [4]
            },
            "ja_JP": {
                "color_preferences": ["white", "red", "blue"],
                "image_style": "minimalist",
                "communication_style": "formal",
                "business_hours": "9:00-18:00",
                "weekend_days": ["saturday", "sunday"]
            },
            "ar_SA": {
                "color_preferences": ["green", "gold", "white"],
                "image_style": "ornate",
                "communication_style": "respectful",
                "business_hours": "8:00-16:00",
                "weekend_days": ["friday", "saturday"],
                "rtl": True
            },
            "de_DE": {
                "color_preferences": ["blue", "gray", "white"],
                "image_style": "clean",
                "communication_style": "precise",
                "business_hours": "8:00-17:00",
                "weekend_days": ["saturday", "sunday"]
            }
        }
        
        locale_key = f"{language.value}_{country_code}"
        return cultural_data.get(locale_key, cultural_data.get("en_US", {}))

    # Utility Methods
    def load_sample_data(self):
        """Load sample currency rates and regional pricing"""
        # Sample currency rates (in real implementation, these would come from an API)
        sample_rates = [
            (SupportedCurrency.USD, SupportedCurrency.EUR, 0.85),
            (SupportedCurrency.USD, SupportedCurrency.GBP, 0.73),
            (SupportedCurrency.USD, SupportedCurrency.CAD, 1.25),
            (SupportedCurrency.USD, SupportedCurrency.JPY, 110.0),
            (SupportedCurrency.USD, SupportedCurrency.CNY, 6.45),
            (SupportedCurrency.USD, SupportedCurrency.INR, 74.5),
            (SupportedCurrency.USD, SupportedCurrency.BRL, 5.2),
            (SupportedCurrency.EUR, SupportedCurrency.USD, 1.18),
            (SupportedCurrency.GBP, SupportedCurrency.USD, 1.37),
        ]
        
        for from_curr, to_curr, rate in sample_rates:
            self.add_currency_rate(from_curr, to_curr, rate)
        
        # Sample regional pricing
        regional_configs = [
            ("US", SupportedCurrency.USD, 1.0, 0.08, "Sales Tax", {"basic": 1.0, "pro": 1.0, "enterprise": 1.0}),
            ("EU", SupportedCurrency.EUR, 0.85, 0.20, "VAT", {"basic": 1.0, "pro": 1.0, "enterprise": 1.0}),
            ("UK", SupportedCurrency.GBP, 0.73, 0.20, "VAT", {"basic": 1.0, "pro": 1.0, "enterprise": 1.0}),
            ("CA", SupportedCurrency.CAD, 1.25, 0.13, "HST", {"basic": 1.0, "pro": 1.0, "enterprise": 1.0}),
            ("JP", SupportedCurrency.JPY, 110.0, 0.10, "Consumption Tax", {"basic": 1.0, "pro": 1.0, "enterprise": 1.0}),
            ("CN", SupportedCurrency.CNY, 6.45, 0.06, "VAT", {"basic": 0.8, "pro": 0.8, "enterprise": 0.8}),
            ("IN", SupportedCurrency.INR, 74.5, 0.18, "GST", {"basic": 0.6, "pro": 0.6, "enterprise": 0.6}),
            ("BR", SupportedCurrency.BRL, 5.2, 0.17, "ICMS", {"basic": 0.7, "pro": 0.7, "enterprise": 0.7}),
        ]
        
        for region, currency, multiplier, tax_rate, tax_name, tiers in regional_configs:
            self.add_regional_pricing(region, currency, multiplier, tax_rate, tax_name, tiers)
        
        logger.info("Sample currency rates and regional pricing loaded")

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return [
            {"code": lang.value, "name": self.get_language_name(lang), "native_name": self.get_native_language_name(lang)}
            for lang in SupportedLanguage
        ]

    def get_language_name(self, language: SupportedLanguage) -> str:
        """Get English name of language"""
        names = {
            SupportedLanguage.ENGLISH: "English",
            SupportedLanguage.SPANISH: "Spanish",
            SupportedLanguage.FRENCH: "French",
            SupportedLanguage.GERMAN: "German",
            SupportedLanguage.ITALIAN: "Italian",
            SupportedLanguage.PORTUGUESE: "Portuguese",
            SupportedLanguage.RUSSIAN: "Russian",
            SupportedLanguage.CHINESE_SIMPLIFIED: "Chinese (Simplified)",
            SupportedLanguage.CHINESE_TRADITIONAL: "Chinese (Traditional)",
            SupportedLanguage.JAPANESE: "Japanese",
            SupportedLanguage.KOREAN: "Korean",
            SupportedLanguage.ARABIC: "Arabic",
            SupportedLanguage.HINDI: "Hindi",
            SupportedLanguage.DUTCH: "Dutch",
            SupportedLanguage.SWEDISH: "Swedish"
        }
        return names.get(language, language.value)

    def get_native_language_name(self, language: SupportedLanguage) -> str:
        """Get native name of language"""
        names = {
            SupportedLanguage.ENGLISH: "English",
            SupportedLanguage.SPANISH: "Español",
            SupportedLanguage.FRENCH: "Français",
            SupportedLanguage.GERMAN: "Deutsch",
            SupportedLanguage.ITALIAN: "Italiano",
            SupportedLanguage.PORTUGUESE: "Português",
            SupportedLanguage.RUSSIAN: "Русский",
            SupportedLanguage.CHINESE_SIMPLIFIED: "简体中文",
            SupportedLanguage.CHINESE_TRADITIONAL: "繁體中文",
            SupportedLanguage.JAPANESE: "日本語",
            SupportedLanguage.KOREAN: "한국어",
            SupportedLanguage.ARABIC: "العربية",
            SupportedLanguage.HINDI: "हिन्दी",
            SupportedLanguage.DUTCH: "Nederlands",
            SupportedLanguage.SWEDISH: "Svenska"
        }
        return names.get(language, language.value)

if __name__ == "__main__":
    # Example usage
    i18n = InternationalizationSystem()
    
    # Load sample data
    i18n.load_sample_data()
    
    # Test translations
    print("Testing translations:")
    print(f"English: {i18n.get_translation('nav.home', SupportedLanguage.ENGLISH)}")
    print(f"Spanish: {i18n.get_translation('nav.home', SupportedLanguage.SPANISH)}")
    print(f"Chinese: {i18n.get_translation('nav.home', SupportedLanguage.CHINESE_SIMPLIFIED)}")
    
    # Test currency conversion
    print(f"\nTesting currency conversion:")
    converted = i18n.convert_currency(100, SupportedCurrency.USD, SupportedCurrency.EUR)
    print(f"$100 USD = €{converted:.2f} EUR")
    
    # Test regional pricing
    print(f"\nTesting regional pricing:")
    us_pricing = i18n.calculate_regional_price(99.0, "US", "pro")
    print(f"US pricing: {us_pricing}")
    
    eu_pricing = i18n.calculate_regional_price(99.0, "EU", "pro")
    print(f"EU pricing: {eu_pricing}")
    
    print("\nInternationalization system ready!")