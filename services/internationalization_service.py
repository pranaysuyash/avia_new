"""
Internationalization (i18n) Service
Handles multi-language support, translations, and locale-specific formatting
"""

import json
import os
import re
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
import asyncio
import aiofiles
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SupportedLanguage(Enum):
    """Supported languages with their codes"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HEBREW = "he"
    HINDI = "hi"
    DUTCH = "nl"
    SWEDISH = "sv"
    NORWEGIAN = "no"
    DANISH = "da"
    FINNISH = "fi"
    POLISH = "pl"
    CZECH = "cs"
    HUNGARIAN = "hu"
    TURKISH = "tr"
    GREEK = "el"
    BULGARIAN = "bg"
    ROMANIAN = "ro"
    UKRAINIAN = "uk"
    THAI = "th"
    VIETNAMESE = "vi"
    INDONESIAN = "id"
    MALAY = "ms"


class TextDirection(Enum):
    """Text direction for different languages"""
    LTR = "ltr"  # Left-to-right
    RTL = "rtl"  # Right-to-left


@dataclass
class LocaleInfo:
    """Locale information for a language"""
    code: str
    name: str
    native_name: str
    direction: TextDirection
    date_format: str
    time_format: str
    currency_symbol: str
    decimal_separator: str
    thousands_separator: str
    flag_emoji: str


@dataclass
class TranslationContext:
    """Context for translations"""
    namespace: str = "general"
    component: Optional[str] = None
    user_id: Optional[int] = None
    variables: Optional[Dict[str, Any]] = None


class Translation(Base):
    """Database model for translations"""
    __tablename__ = "translations"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(500), nullable=False, index=True)
    language_code = Column(String(10), nullable=False, index=True)
    namespace = Column(String(100), default="general", index=True)
    value = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Translation(key='{self.key}', lang='{self.language_code}', namespace='{self.namespace}')>"


class UserLanguagePreference(Base):
    """User language preferences"""
    __tablename__ = "user_language_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    language_code = Column(String(10), nullable=False)
    is_primary = Column(Boolean, default=True)
    date_format_preference = Column(String(50), nullable=True)
    number_format_preference = Column(String(50), nullable=True)
    timezone = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InternationalizationService:
    """Service for handling internationalization"""
    
    def __init__(self):
        self.translations_cache: Dict[str, Dict[str, Dict[str, str]]] = {}
        self.locales_info = self._init_locales_info()
        self.rtl_languages = {
            SupportedLanguage.ARABIC.value,
            SupportedLanguage.HEBREW.value
        }
        self.cache_ttl = 3600  # 1 hour
        self._last_cache_update = {}
        
    def _init_locales_info(self) -> Dict[str, LocaleInfo]:
        """Initialize locale information for supported languages"""
        return {
            "en": LocaleInfo(
                code="en",
                name="English",
                native_name="English",
                direction=TextDirection.LTR,
                date_format="%m/%d/%Y",
                time_format="%I:%M %p",
                currency_symbol="$",
                decimal_separator=".",
                thousands_separator=",",
                flag_emoji="🇺🇸"
            ),
            "es": LocaleInfo(
                code="es",
                name="Spanish",
                native_name="Español",
                direction=TextDirection.LTR,
                date_format="%d/%m/%Y",
                time_format="%H:%M",
                currency_symbol="€",
                decimal_separator=",",
                thousands_separator=".",
                flag_emoji="🇪🇸"
            ),
            "fr": LocaleInfo(
                code="fr",
                name="French",
                native_name="Français",
                direction=TextDirection.LTR,
                date_format="%d/%m/%Y",
                time_format="%H:%M",
                currency_symbol="€",
                decimal_separator=",",
                thousands_separator=" ",
                flag_emoji="🇫🇷"
            ),
            "de": LocaleInfo(
                code="de",
                name="German",
                native_name="Deutsch",
                direction=TextDirection.LTR,
                date_format="%d.%m.%Y",
                time_format="%H:%M",
                currency_symbol="€",
                decimal_separator=",",
                thousands_separator=".",
                flag_emoji="🇩🇪"
            ),
            "zh-CN": LocaleInfo(
                code="zh-CN",
                name="Chinese (Simplified)",
                native_name="简体中文",
                direction=TextDirection.LTR,
                date_format="%Y/%m/%d",
                time_format="%H:%M",
                currency_symbol="¥",
                decimal_separator=".",
                thousands_separator=",",
                flag_emoji="🇨🇳"
            ),
            "ja": LocaleInfo(
                code="ja",
                name="Japanese",
                native_name="日本語",
                direction=TextDirection.LTR,
                date_format="%Y/%m/%d",
                time_format="%H:%M",
                currency_symbol="¥",
                decimal_separator=".",
                thousands_separator=",",
                flag_emoji="🇯🇵"
            ),
            "ar": LocaleInfo(
                code="ar",
                name="Arabic",
                native_name="العربية",
                direction=TextDirection.RTL,
                date_format="%d/%m/%Y",
                time_format="%H:%M",
                currency_symbol="ر.س",
                decimal_separator=".",
                thousands_separator=",",
                flag_emoji="🇸🇦"
            ),
            "he": LocaleInfo(
                code="he",
                name="Hebrew",
                native_name="עברית",
                direction=TextDirection.RTL,
                date_format="%d/%m/%Y",
                time_format="%H:%M",
                currency_symbol="₪",
                decimal_separator=".",
                thousands_separator=",",
                flag_emoji="🇮🇱"
            ),
            "ru": LocaleInfo(
                code="ru",
                name="Russian",
                native_name="Русский",
                direction=TextDirection.LTR,
                date_format="%d.%m.%Y",
                time_format="%H:%M",
                currency_symbol="₽",
                decimal_separator=",",
                thousands_separator=" ",
                flag_emoji="🇷🇺"
            ),
            "pt": LocaleInfo(
                code="pt",
                name="Portuguese",
                native_name="Português",
                direction=TextDirection.LTR,
                date_format="%d/%m/%Y",
                time_format="%H:%M",
                currency_symbol="R$",
                decimal_separator=",",
                thousands_separator=".",
                flag_emoji="🇧🇷"
            )
        }
    
    async def get_translation(
        self, 
        key: str, 
        language_code: str, 
        context: Optional[TranslationContext] = None,
        fallback: Optional[str] = None
    ) -> str:
        """Get translation for a key in specified language"""
        if context is None:
            context = TranslationContext()
            
        # Try to get from cache first
        cache_key = f"{language_code}:{context.namespace}"
        if cache_key in self.translations_cache:
            namespace_translations = self.translations_cache[cache_key]
            if key in namespace_translations:
                translation = namespace_translations[key]
                
                # Handle variable substitution
                if context.variables:
                    translation = self._substitute_variables(translation, context.variables)
                
                return translation
        
        # If not in cache, try to load from database or files
        translation = await self._load_translation_from_storage(key, language_code, context.namespace)
        
        if translation:
            # Handle variable substitution
            if context.variables:
                translation = self._substitute_variables(translation, context.variables)
            return translation
        
        # Fallback to English if not found
        if language_code != "en":
            english_translation = await self.get_translation(key, "en", context, fallback)
            if english_translation != fallback:
                return f"[EN] {english_translation}"
        
        # Return fallback or key if no translation found
        return fallback or f"[MISSING: {key}]"
    
    async def set_translation(
        self,
        db: Session,
        key: str,
        language_code: str,
        value: str,
        namespace: str = "general",
        user_id: Optional[int] = None
    ) -> bool:
        """Set or update a translation"""
        try:
            # Check if translation already exists
            existing = db.query(Translation).filter(
                Translation.key == key,
                Translation.language_code == language_code,
                Translation.namespace == namespace
            ).first()
            
            if existing:
                existing.value = value
                existing.updated_at = datetime.utcnow()
                if user_id:
                    existing.created_by = user_id
            else:
                translation = Translation(
                    key=key,
                    language_code=language_code,
                    namespace=namespace,
                    value=value,
                    created_by=user_id
                )
                db.add(translation)
            
            db.commit()
            
            # Update cache
            await self._update_cache(language_code, namespace, key, value)
            
            return True
        except Exception as e:
            db.rollback()
            print(f"Error setting translation: {e}")
            return False
    
    async def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Get list of supported languages"""
        return [
            {
                "code": locale.code,
                "name": locale.name,
                "native_name": locale.native_name,
                "direction": locale.direction.value,
                "flag": locale.flag_emoji
            }
            for locale in self.locales_info.values()
        ]
    
    def detect_language_from_text(self, text: str) -> str:
        """Detect language from text content"""
        # Simple detection based on character patterns
        # In production, use a proper language detection library like langdetect
        
        # Check for common patterns
        if re.search(r'[\u0600-\u06FF]', text):  # Arabic script
            return "ar"
        elif re.search(r'[\u0590-\u05FF]', text):  # Hebrew script
            return "he"
        elif re.search(r'[\u4e00-\u9fff]', text):  # Chinese characters
            return "zh-CN"
        elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):  # Japanese
            return "ja"
        elif re.search(r'[\uac00-\ud7af]', text):  # Korean
            return "ko"
        elif re.search(r'[\u0400-\u04ff]', text):  # Cyrillic (Russian)
            return "ru"
        else:
            # Default to English for Latin scripts
            return "en"
    
    def get_user_language_preference(self, db: Session, user_id: int) -> str:
        """Get user's preferred language"""
        preference = db.query(UserLanguagePreference).filter(
            UserLanguagePreference.user_id == user_id,
            UserLanguagePreference.is_primary == True
        ).first()
        
        return preference.language_code if preference else "en"
    
    async def set_user_language_preference(
        self,
        db: Session,
        user_id: int,
        language_code: str,
        timezone: Optional[str] = None,
        date_format: Optional[str] = None,
        number_format: Optional[str] = None
    ) -> bool:
        """Set user's language preference"""
        try:
            # Deactivate existing primary preference
            db.query(UserLanguagePreference).filter(
                UserLanguagePreference.user_id == user_id,
                UserLanguagePreference.is_primary == True
            ).update({"is_primary": False})
            
            # Create or update preference
            existing = db.query(UserLanguagePreference).filter(
                UserLanguagePreference.user_id == user_id,
                UserLanguagePreference.language_code == language_code
            ).first()
            
            if existing:
                existing.is_primary = True
                existing.timezone = timezone
                existing.date_format_preference = date_format
                existing.number_format_preference = number_format
                existing.updated_at = datetime.utcnow()
            else:
                preference = UserLanguagePreference(
                    user_id=user_id,
                    language_code=language_code,
                    is_primary=True,
                    timezone=timezone,
                    date_format_preference=date_format,
                    number_format_preference=number_format
                )
                db.add(preference)
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error setting language preference: {e}")
            return False
    
    def format_date(self, date_obj: Union[datetime, date], language_code: str) -> str:
        """Format date according to locale"""
        locale_info = self.locales_info.get(language_code, self.locales_info["en"])
        
        if isinstance(date_obj, datetime):
            return date_obj.strftime(locale_info.date_format)
        elif isinstance(date_obj, date):
            return date_obj.strftime(locale_info.date_format)
        else:
            return str(date_obj)
    
    def format_time(self, datetime_obj: datetime, language_code: str) -> str:
        """Format time according to locale"""
        locale_info = self.locales_info.get(language_code, self.locales_info["en"])
        return datetime_obj.strftime(locale_info.time_format)
    
    def format_number(self, number: Union[int, float, Decimal], language_code: str) -> str:
        """Format number according to locale"""
        locale_info = self.locales_info.get(language_code, self.locales_info["en"])
        
        # Convert to string with proper decimal places
        if isinstance(number, (int, Decimal)):
            number_str = str(number)
        else:
            number_str = f"{number:.2f}"
        
        # Split integer and decimal parts
        if '.' in number_str:
            integer_part, decimal_part = number_str.split('.')
        else:
            integer_part, decimal_part = number_str, ""
        
        # Add thousands separators
        if len(integer_part) > 3:
            reversed_int = integer_part[::-1]
            grouped = [reversed_int[i:i+3] for i in range(0, len(reversed_int), 3)]
            integer_part = locale_info.thousands_separator.join(grouped)[::-1]
        
        # Combine with decimal separator
        if decimal_part:
            return f"{integer_part}{locale_info.decimal_separator}{decimal_part}"
        else:
            return integer_part
    
    def format_currency(self, amount: Union[int, float, Decimal], language_code: str) -> str:
        """Format currency according to locale"""
        locale_info = self.locales_info.get(language_code, self.locales_info["en"])
        formatted_number = self.format_number(amount, language_code)
        
        # Different currency symbol positions for different locales
        if language_code in ["en"]:
            return f"{locale_info.currency_symbol}{formatted_number}"
        else:
            return f"{formatted_number} {locale_info.currency_symbol}"
    
    def is_rtl_language(self, language_code: str) -> bool:
        """Check if language is right-to-left"""
        return language_code in self.rtl_languages
    
    def get_text_direction(self, language_code: str) -> str:
        """Get text direction for language"""
        locale_info = self.locales_info.get(language_code, self.locales_info["en"])
        return locale_info.direction.value
    
    async def bulk_translate(
        self,
        texts: Dict[str, str],
        target_language: str,
        source_language: str = "en"
    ) -> Dict[str, str]:
        """Bulk translate texts using AI translation service"""
        
        translated_texts = {}
        
        # Try different translation providers in order of preference
        provider = os.getenv('TRANSLATION_PROVIDER', 'google').lower()
        
        try:
            if provider == 'google':
                translated_texts = await self._translate_with_google(
                    texts, target_language, source_language
                )
            elif provider == 'deepl':
                translated_texts = await self._translate_with_deepl(
                    texts, target_language, source_language
                )
            elif provider == 'azure':
                translated_texts = await self._translate_with_azure(
                    texts, target_language, source_language
                )
            elif provider == 'openai':
                translated_texts = await self._translate_with_openai(
                    texts, target_language, source_language
                )
            else:
                # Fallback to basic translation
                for key, text in texts.items():
                    translated_texts[key] = await self._basic_translate(
                        text, target_language, source_language
                    )
        except Exception as e:
            # If translation service fails, return original texts with warning
            import logging
            logging.error(f"Translation service failed: {e}")
            for key, text in texts.items():
                translated_texts[key] = text  # Return original
        
        return translated_texts
    
    async def _translate_with_google(
        self,
        texts: Dict[str, str],
        target_language: str,
        source_language: str
    ) -> Dict[str, str]:
        """Translate using Google Translate API"""
        try:
            from google.cloud import translate_v2 as translate
            
            client = translate.Client()
            translated = {}
            
            # Google Translate supports batch translation
            text_list = list(texts.values())
            results = client.translate(
                text_list,
                target_language=target_language,
                source_language=source_language if source_language != 'auto' else None
            )
            
            for key, result in zip(texts.keys(), results):
                translated[key] = result['translatedText']
            
            return translated
            
        except ImportError:
            # Google Cloud library not installed, try alternative
            return await self._translate_with_googletrans(texts, target_language, source_language)
    
    async def _translate_with_googletrans(
        self,
        texts: Dict[str, str],
        target_language: str,
        source_language: str
    ) -> Dict[str, str]:
        """Translate using googletrans library (free alternative)"""
        try:
            from googletrans import Translator
            
            translator = Translator()
            translated = {}
            
            for key, text in texts.items():
                result = translator.translate(
                    text,
                    dest=target_language,
                    src=source_language if source_language != 'auto' else 'auto'
                )
                translated[key] = result.text
            
            return translated
            
        except Exception:
            raise ValueError("Google Translate not available")
    
    async def _translate_with_deepl(
        self,
        texts: Dict[str, str],
        target_language: str,
        source_language: str
    ) -> Dict[str, str]:
        """Translate using DeepL API"""
        try:
            import deepl
            
            auth_key = os.getenv('DEEPL_AUTH_KEY')
            if not auth_key:
                raise ValueError("DeepL auth key not configured")
            
            translator = deepl.Translator(auth_key)
            translated = {}
            
            # Convert language codes to DeepL format
            target_lang = self._convert_to_deepl_code(target_language)
            source_lang = self._convert_to_deepl_code(source_language) if source_language != 'auto' else None
            
            for key, text in texts.items():
                result = translator.translate_text(
                    text,
                    target_lang=target_lang,
                    source_lang=source_lang
                )
                translated[key] = result.text
            
            return translated
            
        except ImportError:
            raise ValueError("DeepL library not installed")
    
    async def _translate_with_azure(
        self,
        texts: Dict[str, str],
        target_language: str,
        source_language: str
    ) -> Dict[str, str]:
        """Translate using Azure Cognitive Services"""
        try:
            import requests
            
            subscription_key = os.getenv('AZURE_TRANSLATOR_KEY')
            endpoint = os.getenv('AZURE_TRANSLATOR_ENDPOINT', 'https://api.cognitive.microsofttranslator.com')
            
            if not subscription_key:
                raise ValueError("Azure Translator key not configured")
            
            path = '/translate'
            constructed_url = endpoint + path
            
            params = {
                'api-version': '3.0',
                'to': target_language
            }
            
            if source_language != 'auto':
                params['from'] = source_language
            
            headers = {
                'Ocp-Apim-Subscription-Key': subscription_key,
                'Content-type': 'application/json',
                'X-ClientTraceId': str(os.urandom(16).hex())
            }
            
            # Prepare batch request
            body = [{'text': text} for text in texts.values()]
            
            response = requests.post(
                constructed_url,
                params=params,
                headers=headers,
                json=body
            )
            
            if response.status_code == 200:
                results = response.json()
                translated = {}
                
                for key, result in zip(texts.keys(), results):
                    translated[key] = result['translations'][0]['text']
                
                return translated
            else:
                raise ValueError(f"Azure Translator API error: {response.status_code}")
                
        except ImportError:
            raise ValueError("Requests library not available")
    
    async def _translate_with_openai(
        self,
        texts: Dict[str, str],
        target_language: str,
        source_language: str
    ) -> Dict[str, str]:
        """Translate using OpenAI GPT models"""
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            
            openai.api_key = api_key
            translated = {}
            
            # Get target language name
            target_name = self._get_language_name(target_language)
            
            for key, text in texts.items():
                prompt = f"Translate the following text to {target_name}:\n\n{text}"
                
                response = await asyncio.to_thread(
                    openai.ChatCompletion.create,
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are a professional translator. Translate text accurately to {target_name}."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=len(text) * 2  # Allow for expansion
                )
                
                translated[key] = response.choices[0].message.content.strip()
            
            return translated
            
        except ImportError:
            raise ValueError("OpenAI library not installed")
    
    async def _basic_translate(
        self,
        text: str,
        target_language: str,
        source_language: str
    ) -> str:
        """Basic translation fallback using dictionaries"""
        # This is a very basic fallback - in production, use proper translation services
        # For now, just return the original text with language indicator
        return f"[{target_language}] {text}"
    
    def _convert_to_deepl_code(self, language_code: str) -> str:
        """Convert language code to DeepL format"""
        # DeepL uses different language codes
        deepl_codes = {
            'en': 'EN-US',
            'de': 'DE',
            'fr': 'FR',
            'es': 'ES',
            'pt': 'PT-BR',
            'it': 'IT',
            'nl': 'NL',
            'pl': 'PL',
            'ru': 'RU',
            'ja': 'JA',
            'zh-CN': 'ZH'
        }
        return deepl_codes.get(language_code, language_code.upper())
    
    def _get_language_name(self, language_code: str) -> str:
        """Get language name from code"""
        for lang in SupportedLanguage:
            if lang.value == language_code:
                locale = self.locales.get(lang)
                if locale:
                    return locale.name
        return language_code
    
    async def export_translations(
        self,
        db: Session,
        language_code: str,
        namespace: Optional[str] = None,
        format: str = "json"
    ) -> bytes:
        """Export translations in specified format"""
        query = db.query(Translation).filter(Translation.language_code == language_code)
        
        if namespace:
            query = query.filter(Translation.namespace == namespace)
        
        translations = query.all()
        
        if format == "json":
            data = {}
            for translation in translations:
                if translation.namespace not in data:
                    data[translation.namespace] = {}
                data[translation.namespace][translation.key] = translation.value
            
            return json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Namespace", "Key", "Value", "Created", "Updated"])
            
            for translation in translations:
                writer.writerow([
                    translation.namespace,
                    translation.key,
                    translation.value,
                    translation.created_at.isoformat(),
                    translation.updated_at.isoformat()
                ])
            
            return output.getvalue().encode('utf-8')
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def import_translations(
        self,
        db: Session,
        data: bytes,
        language_code: str,
        format: str = "json",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Import translations from data"""
        try:
            if format == "json":
                content = json.loads(data.decode('utf-8'))
                imported_count = 0
                
                for namespace, translations in content.items():
                    for key, value in translations.items():
                        await self.set_translation(
                            db, key, language_code, value, namespace, user_id
                        )
                        imported_count += 1
                
                return {
                    "success": True,
                    "imported_count": imported_count,
                    "language": language_code
                }
            
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # Private methods
    
    def _substitute_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in translation text"""
        for key, value in variables.items():
            # Support both {{key}} and {key} patterns
            text = text.replace(f"{{{{{key}}}}}", str(value))
            text = text.replace(f"{{{key}}}", str(value))
        
        return text
    
    async def _load_translation_from_storage(
        self, 
        key: str, 
        language_code: str, 
        namespace: str
    ) -> Optional[str]:
        """Load translation from database or file storage"""
        # Try to load from file first (for performance)
        file_path = f"translations/{language_code}/{namespace}.json"
        
        if os.path.exists(file_path):
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    translations = json.loads(content)
                    return translations.get(key)
            except:
                pass
        
        # Fallback to database (this would be implemented with actual DB query)
        # For now, return None to indicate not found
        return None
    
    async def _update_cache(
        self, 
        language_code: str, 
        namespace: str, 
        key: str, 
        value: str
    ):
        """Update translation cache"""
        cache_key = f"{language_code}:{namespace}"
        
        if cache_key not in self.translations_cache:
            self.translations_cache[cache_key] = {}
        
        self.translations_cache[cache_key][key] = value
        self._last_cache_update[cache_key] = datetime.utcnow()


# Global service instance
i18n_service = InternationalizationService()