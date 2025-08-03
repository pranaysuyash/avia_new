"""
Advanced Multi-Language Support Module
Handles language detection, code-switching, and multi-language entity extraction
Enhanced for Task 36: Implement advanced multi-language support
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import langdetect
from langdetect import detect_langs, LangDetectException
import pycountry
import re
import time
from collections import defaultdict
import streamlit as st

logger = logging.getLogger(__name__)

# Supported languages with their configurations
SUPPORTED_LANGUAGES = {
    # Major languages with full support
    'en': {'name': 'English', 'spacy_model': 'en_core_web_sm', 'whisper_code': 'en', 'rtl': False},
    'es': {'name': 'Spanish', 'spacy_model': 'es_core_news_sm', 'whisper_code': 'es', 'rtl': False},
    'fr': {'name': 'French', 'spacy_model': 'fr_core_news_sm', 'whisper_code': 'fr', 'rtl': False},
    'de': {'name': 'German', 'spacy_model': 'de_core_news_sm', 'whisper_code': 'de', 'rtl': False},
    'it': {'name': 'Italian', 'spacy_model': 'it_core_news_sm', 'whisper_code': 'it', 'rtl': False},
    'pt': {'name': 'Portuguese', 'spacy_model': 'pt_core_news_sm', 'whisper_code': 'pt', 'rtl': False},
    'ru': {'name': 'Russian', 'spacy_model': 'ru_core_news_sm', 'whisper_code': 'ru', 'rtl': False},
    'ja': {'name': 'Japanese', 'spacy_model': 'ja_core_news_sm', 'whisper_code': 'ja', 'rtl': False},
    'ko': {'name': 'Korean', 'spacy_model': 'ko_core_news_sm', 'whisper_code': 'ko', 'rtl': False},
    'zh': {'name': 'Chinese', 'spacy_model': 'zh_core_web_sm', 'whisper_code': 'zh', 'rtl': False},
    'ar': {'name': 'Arabic', 'spacy_model': 'ar_core_web_sm', 'whisper_code': 'ar', 'rtl': True},
    'he': {'name': 'Hebrew', 'spacy_model': None, 'whisper_code': 'he', 'rtl': True},
    'hi': {'name': 'Hindi', 'spacy_model': None, 'whisper_code': 'hi', 'rtl': False},
    'nl': {'name': 'Dutch', 'spacy_model': 'nl_core_news_sm', 'whisper_code': 'nl', 'rtl': False},
    'pl': {'name': 'Polish', 'spacy_model': 'pl_core_news_sm', 'whisper_code': 'pl', 'rtl': False},
    'tr': {'name': 'Turkish', 'spacy_model': None, 'whisper_code': 'tr', 'rtl': False},
    'sv': {'name': 'Swedish', 'spacy_model': 'sv_core_news_sm', 'whisper_code': 'sv', 'rtl': False},
    'da': {'name': 'Danish', 'spacy_model': 'da_core_news_sm', 'whisper_code': 'da', 'rtl': False},
    'no': {'name': 'Norwegian', 'spacy_model': 'nb_core_news_sm', 'whisper_code': 'no', 'rtl': False},
    'fi': {'name': 'Finnish', 'spacy_model': 'fi_core_news_sm', 'whisper_code': 'fi', 'rtl': False},
    'cs': {'name': 'Czech', 'spacy_model': None, 'whisper_code': 'cs', 'rtl': False},
    'el': {'name': 'Greek', 'spacy_model': 'el_core_news_sm', 'whisper_code': 'el', 'rtl': False},
    'uk': {'name': 'Ukrainian', 'spacy_model': 'uk_core_news_sm', 'whisper_code': 'uk', 'rtl': False},
    'ro': {'name': 'Romanian', 'spacy_model': 'ro_core_news_sm', 'whisper_code': 'ro', 'rtl': False},
    'hu': {'name': 'Hungarian', 'spacy_model': None, 'whisper_code': 'hu', 'rtl': False},
    'bg': {'name': 'Bulgarian', 'spacy_model': None, 'whisper_code': 'bg', 'rtl': False},
    'hr': {'name': 'Croatian', 'spacy_model': 'hr_core_news_sm', 'whisper_code': 'hr', 'rtl': False},
    'sk': {'name': 'Slovak', 'spacy_model': None, 'whisper_code': 'sk', 'rtl': False},
    'sl': {'name': 'Slovenian', 'spacy_model': 'sl_core_news_sm', 'whisper_code': 'sl', 'rtl': False},
    'lt': {'name': 'Lithuanian', 'spacy_model': 'lt_core_news_sm', 'whisper_code': 'lt', 'rtl': False},
    'lv': {'name': 'Latvian', 'spacy_model': 'lv_core_news_sm', 'whisper_code': 'lv', 'rtl': False},
    'et': {'name': 'Estonian', 'spacy_model': None, 'whisper_code': 'et', 'rtl': False},
    'id': {'name': 'Indonesian', 'spacy_model': None, 'whisper_code': 'id', 'rtl': False},
    'ms': {'name': 'Malay', 'spacy_model': None, 'whisper_code': 'ms', 'rtl': False},
    'th': {'name': 'Thai', 'spacy_model': None, 'whisper_code': 'th', 'rtl': False},
    'vi': {'name': 'Vietnamese', 'spacy_model': None, 'whisper_code': 'vi', 'rtl': False},
    'ta': {'name': 'Tamil', 'spacy_model': None, 'whisper_code': 'ta', 'rtl': False},
    'te': {'name': 'Telugu', 'spacy_model': None, 'whisper_code': 'te', 'rtl': False},
    'mr': {'name': 'Marathi', 'spacy_model': None, 'whisper_code': 'mr', 'rtl': False},
    'bn': {'name': 'Bengali', 'spacy_model': None, 'whisper_code': 'bn', 'rtl': False},
    'ur': {'name': 'Urdu', 'spacy_model': None, 'whisper_code': 'ur', 'rtl': True},
    'fa': {'name': 'Persian', 'spacy_model': None, 'whisper_code': 'fa', 'rtl': True},
    'ca': {'name': 'Catalan', 'spacy_model': 'ca_core_news_sm', 'whisper_code': 'ca', 'rtl': False},
    'eu': {'name': 'Basque', 'spacy_model': None, 'whisper_code': 'eu', 'rtl': False},
    'gl': {'name': 'Galician', 'spacy_model': None, 'whisper_code': 'gl', 'rtl': False},
    'sq': {'name': 'Albanian', 'spacy_model': None, 'whisper_code': 'sq', 'rtl': False},
    'mk': {'name': 'Macedonian', 'spacy_model': 'mk_core_news_sm', 'whisper_code': 'mk', 'rtl': False},
    'is': {'name': 'Icelandic', 'spacy_model': 'is_core_news_sm', 'whisper_code': 'is', 'rtl': False},
    'ga': {'name': 'Irish', 'spacy_model': None, 'whisper_code': 'ga', 'rtl': False},
    'cy': {'name': 'Welsh', 'spacy_model': None, 'whisper_code': 'cy', 'rtl': False},
    'mt': {'name': 'Maltese', 'spacy_model': None, 'whisper_code': 'mt', 'rtl': False},
    'tl': {'name': 'Tagalog', 'spacy_model': None, 'whisper_code': 'tl', 'rtl': False},
}


@dataclass
class LanguageDetectionResult:
    """Result of language detection"""
    primary_language: str
    confidence: float
    all_languages: List[Tuple[str, float]]  # List of (language_code, confidence)
    has_code_switching: bool
    segments: Optional[List[Dict[str, Any]]] = None  # For code-switching segments


@dataclass
class CodeSwitchSegment:
    """Segment with language switch"""
    text: str
    language: str
    start_pos: int
    end_pos: int
    confidence: float


class LanguageDetector:
    """Advanced language detection with code-switching support"""
    
    def __init__(self):
        self.min_confidence = 0.7
        self.code_switch_threshold = 0.3
        
    def detect_language(self, text: str) -> LanguageDetectionResult:
        """
        Detect language(s) in text with confidence scores
        
        Args:
            text: Text to analyze
            
        Returns:
            LanguageDetectionResult with primary language and all detected languages
        """
        try:
            # Detect all possible languages with probabilities
            langs = detect_langs(text)
            
            # Convert to our format
            all_languages = [(lang.lang, lang.prob) for lang in langs]
            
            # Primary language
            primary_lang = all_languages[0][0] if all_languages else 'en'
            primary_confidence = all_languages[0][1] if all_languages else 0.0
            
            # Check for code-switching (multiple languages with significant probability)
            significant_langs = [lang for lang in all_languages if lang[1] > self.code_switch_threshold]
            has_code_switching = len(significant_langs) > 1
            
            # If code-switching detected, analyze segments
            segments = None
            if has_code_switching:
                segments = self._detect_code_switch_segments(text)
            
            return LanguageDetectionResult(
                primary_language=primary_lang,
                confidence=primary_confidence,
                all_languages=all_languages,
                has_code_switching=has_code_switching,
                segments=segments
            )
            
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}")
            return LanguageDetectionResult(
                primary_language='en',
                confidence=0.0,
                all_languages=[('en', 0.0)],
                has_code_switching=False
            )
    
    def _detect_code_switch_segments(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect segments where language switches occur
        
        Args:
            text: Text to analyze for code-switching
            
        Returns:
            List of segments with language information
        """
        # Split text into sentences for segment analysis
        import re
        sentences = re.split(r'[.!?]+', text)
        segments = []
        
        current_pos = 0
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            try:
                # Detect language for this segment
                lang = langdetect.detect(sentence)
                confidence = max([l.prob for l in detect_langs(sentence) if l.lang == lang])
                
                segments.append({
                    'text': sentence.strip(),
                    'language': lang,
                    'start_pos': current_pos,
                    'end_pos': current_pos + len(sentence),
                    'confidence': confidence
                })
            except:
                # If detection fails for segment, skip it
                pass
            
            current_pos += len(sentence) + 1  # +1 for punctuation
        
        return segments
    
    def is_supported_language(self, language_code: str) -> bool:
        """Check if language is supported"""
        return language_code in SUPPORTED_LANGUAGES
    
    def get_language_info(self, language_code: str) -> Optional[Dict[str, Any]]:
        """Get language configuration information"""
        return SUPPORTED_LANGUAGES.get(language_code)
    
    def get_whisper_language_code(self, language_code: str) -> str:
        """Get Whisper-compatible language code"""
        lang_info = self.get_language_info(language_code)
        return lang_info['whisper_code'] if lang_info else 'en'
    
    def get_spacy_model(self, language_code: str) -> Optional[str]:
        """Get spaCy model name for language"""
        lang_info = self.get_language_info(language_code)
        return lang_info['spacy_model'] if lang_info else None
    
    def is_rtl_language(self, language_code: str) -> bool:
        """Check if language is right-to-left"""
        lang_info = self.get_language_info(language_code)
        return lang_info.get('rtl', False) if lang_info else False


class MultilingualEntityExtractor:
    """Entity extraction with multi-language support"""
    
    def __init__(self):
        self.loaded_models = {}
        self.language_detector = LanguageDetector()
        
    def load_language_model(self, language_code: str):
        """Load spaCy model for specific language"""
        if language_code in self.loaded_models:
            return self.loaded_models[language_code]
        
        model_name = self.language_detector.get_spacy_model(language_code)
        if not model_name:
            logger.warning(f"No spaCy model available for language: {language_code}")
            return None
        
        try:
            import spacy
            model = spacy.load(model_name)
            self.loaded_models[language_code] = model
            logger.info(f"Loaded spaCy model for {language_code}: {model_name}")
            return model
        except Exception as e:
            logger.error(f"Failed to load spaCy model {model_name}: {e}")
            return None
    
    def extract_entities(self, text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract entities with automatic language detection
        
        Args:
            text: Text to analyze
            language: Language code (optional, will auto-detect if not provided)
            
        Returns:
            Dictionary with entities and language information
        """
        # Detect language if not provided
        if not language:
            detection_result = self.language_detector.detect_language(text)
            language = detection_result.primary_language
        
        # Load appropriate model
        nlp = self.load_language_model(language)
        if not nlp:
            # Fallback to English
            nlp = self.load_language_model('en')
            if not nlp:
                return {
                    'entities': [],
                    'language': language,
                    'error': 'No NLP model available'
                }
        
        # Process text
        doc = nlp(text)
        
        # Extract entities
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
        
        return {
            'entities': entities,
            'language': language,
            'model': self.language_detector.get_spacy_model(language)
        }
    
    def extract_entities_multilingual(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from text with code-switching support
        
        Args:
            text: Text that may contain multiple languages
            
        Returns:
            Dictionary with entities from all detected languages
        """
        # Detect languages and segments
        detection_result = self.language_detector.detect_language(text)
        
        if not detection_result.has_code_switching:
            # Single language - process normally
            return self.extract_entities(text, detection_result.primary_language)
        
        # Multiple languages detected - process segments
        all_entities = []
        language_segments = []
        
        if detection_result.segments:
            for segment in detection_result.segments:
                segment_entities = self.extract_entities(
                    segment['text'], 
                    segment['language']
                )
                
                # Adjust entity positions to full text
                for entity in segment_entities['entities']:
                    entity['start'] += segment['start_pos']
                    entity['end'] += segment['start_pos']
                    entity['language'] = segment['language']
                    all_entities.append(entity)
                
                language_segments.append({
                    'text': segment['text'],
                    'language': segment['language'],
                    'confidence': segment['confidence']
                })
        
        return {
            'entities': all_entities,
            'languages': detection_result.all_languages,
            'primary_language': detection_result.primary_language,
            'has_code_switching': True,
            'language_segments': language_segments
        }


def get_language_name(language_code: str) -> str:
    """Get human-readable language name from code"""
    if language_code in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[language_code]['name']
    
    # Try pycountry
    try:
        lang = pycountry.languages.get(alpha_2=language_code)
        if lang:
            return lang.name
    except:
        pass
    
    return language_code.upper()


def get_supported_languages() -> List[Dict[str, Any]]:
    """Get list of all supported languages with their capabilities"""
    languages = []
    for code, info in SUPPORTED_LANGUAGES.items():
        languages.append({
            'code': code,
            'name': info['name'],
            'has_ner': info['spacy_model'] is not None,
            'has_transcription': True,
            'is_rtl': info['rtl']
        })
    return sorted(languages, key=lambda x: x['name'])


class TranslationService:
    """Translation service with multiple provider support"""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available translation providers"""
        try:
            # Try to initialize OpenAI for translation
            import openai
            from config import Config
            config = Config()
            if config.openai_api_key:
                self.providers['openai'] = openai.OpenAI(api_key=config.openai_api_key)
                logger.info("OpenAI translation provider initialized")
        except Exception as e:
            logger.warning(f"OpenAI translation provider not available: {e}")
        
        try:
            # Try to initialize Google Translate
            from googletrans import Translator
            self.providers['google'] = Translator()
            logger.info("Google Translate provider initialized")
        except Exception as e:
            logger.warning(f"Google Translate provider not available: {e}")
    
    def translate_text(self, text: str, target_language: str, source_language: str = None, 
                      provider: str = 'auto') -> Dict[str, Any]:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (auto-detect if None)
            provider: Translation provider ('auto', 'openai', 'google')
            
        Returns:
            Dictionary with translation result
        """
        if provider == 'auto':
            # Choose best available provider
            if 'openai' in self.providers:
                provider = 'openai'
            elif 'google' in self.providers:
                provider = 'google'
            else:
                return {'error': 'No translation provider available'}
        
        try:
            if provider == 'openai':
                return self._translate_with_openai(text, target_language, source_language)
            elif provider == 'google':
                return self._translate_with_google(text, target_language, source_language)
            else:
                return {'error': f'Unknown provider: {provider}'}
        except Exception as e:
            logger.error(f"Translation failed with {provider}: {e}")
            return {'error': str(e)}
    
    def _translate_with_openai(self, text: str, target_language: str, 
                              source_language: str = None) -> Dict[str, Any]:
        """Translate using OpenAI GPT"""
        client = self.providers.get('openai')
        if not client:
            return {'error': 'OpenAI provider not available'}
        
        target_lang_name = get_language_name(target_language)
        source_lang_name = get_language_name(source_language) if source_language else "auto-detected language"
        
        prompt = f"""Translate the following text from {source_lang_name} to {target_lang_name}. 
        Provide only the translation without any additional text or explanations.
        
        Text to translate: {text}"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        translated_text = response.choices[0].message.content.strip()
        
        return {
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language,
            'provider': 'openai',
            'confidence': 0.9  # OpenAI generally provides high-quality translations
        }
    
    def _translate_with_google(self, text: str, target_language: str, 
                              source_language: str = None) -> Dict[str, Any]:
        """Translate using Google Translate"""
        translator = self.providers.get('google')
        if not translator:
            return {'error': 'Google Translate provider not available'}
        
        result = translator.translate(text, dest=target_language, src=source_language)
        
        return {
            'translated_text': result.text,
            'source_language': result.src,
            'target_language': target_language,
            'provider': 'google',
            'confidence': 0.85  # Google Translate confidence estimate
        }
    
    def get_available_providers(self) -> List[str]:
        """Get list of available translation providers"""
        return list(self.providers.keys())


class RealTimeLanguageProcessor:
    """Real-time language processing with switching detection"""
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self.translation_service = TranslationService()
        self.session_languages = defaultdict(list)
        self.language_history = []
        
    def process_streaming_text(self, text_chunk: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Process streaming text with real-time language detection
        
        Args:
            text_chunk: New text chunk from streaming
            session_id: Session identifier for tracking
            
        Returns:
            Processing result with language information
        """
        # Detect language of current chunk
        detection_result = self.language_detector.detect_language(text_chunk)
        
        # Update session language history
        self.session_languages[session_id].append({
            'text': text_chunk,
            'language': detection_result.primary_language,
            'confidence': detection_result.confidence,
            'timestamp': time.time()
        })
        
        # Check for language switching
        language_switch = self._detect_language_switch(session_id)
        
        return {
            'text': text_chunk,
            'detected_language': detection_result.primary_language,
            'confidence': detection_result.confidence,
            'all_languages': detection_result.all_languages,
            'language_switch_detected': language_switch,
            'session_languages': self._get_session_language_summary(session_id)
        }
    
    def _detect_language_switch(self, session_id: str) -> bool:
        """Detect if language has switched in recent chunks"""
        history = self.session_languages[session_id]
        if len(history) < 2:
            return False
        
        # Check last few chunks for language consistency
        recent_chunks = history[-3:]  # Last 3 chunks
        languages = [chunk['language'] for chunk in recent_chunks]
        
        # If we have different languages in recent chunks, it's a switch
        return len(set(languages)) > 1
    
    def _get_session_language_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of languages used in session"""
        history = self.session_languages[session_id]
        if not history:
            return {}
        
        # Count language occurrences
        language_counts = defaultdict(int)
        for chunk in history:
            language_counts[chunk['language']] += 1
        
        # Calculate percentages
        total_chunks = len(history)
        language_percentages = {
            lang: (count / total_chunks) * 100 
            for lang, count in language_counts.items()
        }
        
        return {
            'total_chunks': total_chunks,
            'languages_detected': list(language_counts.keys()),
            'primary_language': max(language_counts, key=language_counts.get),
            'language_distribution': language_percentages,
            'has_code_switching': len(language_counts) > 1
        }
    
    def translate_in_real_time(self, text: str, target_language: str, 
                              source_language: str = None) -> Dict[str, Any]:
        """Translate text in real-time with caching"""
        # Use translation service
        return self.translation_service.translate_text(
            text, target_language, source_language
        )
    
    def clear_session(self, session_id: str):
        """Clear session language history"""
        if session_id in self.session_languages:
            del self.session_languages[session_id]


class AdvancedMultilingualUI:
    """Advanced UI components for multi-language support"""
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self.translation_service = TranslationService()
        self.realtime_processor = RealTimeLanguageProcessor()
    
    def render_language_selector(self, key: str = "language_selector") -> str:
        """Render enhanced language selector with search"""
        st.markdown("### 🌍 Language Settings")
        
        # Get supported languages
        languages = get_supported_languages()
        
        # Create searchable language selector
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Language search
            search_term = st.text_input("🔍 Search languages", key=f"{key}_search")
            
            # Filter languages based on search
            if search_term:
                filtered_languages = [
                    lang for lang in languages 
                    if search_term.lower() in lang['name'].lower()
                ]
            else:
                filtered_languages = languages
            
            # Language selection
            language_options = [f"{lang['name']} ({lang['code']})" for lang in filtered_languages]
            language_codes = [lang['code'] for lang in filtered_languages]
            
            selected_idx = st.selectbox(
                "Select Language",
                range(len(language_options)),
                format_func=lambda x: language_options[x],
                key=f"{key}_select"
            )
            
            selected_language = language_codes[selected_idx] if filtered_languages else 'en'
        
        with col2:
            # Language capabilities
            if filtered_languages:
                selected_lang_info = filtered_languages[selected_idx]
                st.markdown("**Capabilities:**")
                st.write(f"🎯 NER: {'✅' if selected_lang_info['has_ner'] else '❌'}")
                st.write(f"🎤 Transcription: {'✅' if selected_lang_info['has_transcription'] else '❌'}")
                st.write(f"📝 RTL: {'✅' if selected_lang_info['is_rtl'] else '❌'}")
        
        return selected_language
    
    def render_translation_interface(self, text: str, source_language: str = None):
        """Render translation interface"""
        st.markdown("### 🔄 Translation")
        
        if not text.strip():
            st.info("Enter text to enable translation")
            return
        
        # Auto-detect source language if not provided
        if not source_language:
            detection = self.language_detector.detect_language(text)
            source_language = detection.primary_language
            st.info(f"Detected language: {get_language_name(source_language)} ({source_language})")
        
        # Target language selection
        target_languages = get_supported_languages()
        target_options = [f"{lang['name']} ({lang['code']})" for lang in target_languages]
        target_codes = [lang['code'] for lang in target_languages]
        
        target_idx = st.selectbox(
            "Translate to:",
            range(len(target_options)),
            format_func=lambda x: target_options[x],
            key="translation_target"
        )
        
        target_language = target_codes[target_idx]
        
        # Translation button
        if st.button("🔄 Translate", key="translate_button"):
            with st.spinner("Translating..."):
                result = self.translation_service.translate_text(
                    text, target_language, source_language
                )
                
                if 'error' in result:
                    st.error(f"Translation failed: {result['error']}")
                else:
                    st.success("Translation completed!")
                    
                    # Display translation
                    st.markdown("**Translation:**")
                    
                    # Handle RTL languages
                    if self.language_detector.is_rtl_language(target_language):
                        st.markdown(f'<div dir="rtl" style="text-align: right; font-size: 16px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">{result["translated_text"]}</div>', unsafe_allow_html=True)
                    else:
                        st.text_area("", value=result['translated_text'], height=100, key="translation_result")
                    
                    # Translation metadata
                    st.markdown("**Translation Details:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Provider", result.get('provider', 'Unknown'))
                    with col2:
                        st.metric("Confidence", f"{result.get('confidence', 0):.2f}")
                    with col3:
                        st.metric("Source → Target", f"{source_language} → {target_language}")
    
    def render_code_switching_analysis(self, text: str):
        """Render code-switching analysis interface"""
        st.markdown("### 🔀 Code-Switching Analysis")
        
        if not text.strip():
            st.info("Enter text to analyze code-switching")
            return
        
        # Analyze code-switching
        detection_result = self.language_detector.detect_language(text)
        
        if not detection_result.has_code_switching:
            st.success(f"Single language detected: {get_language_name(detection_result.primary_language)}")
            return
        
        st.warning("Code-switching detected! Multiple languages found in text.")
        
        # Display language distribution
        st.markdown("**Language Distribution:**")
        for lang_code, confidence in detection_result.all_languages:
            lang_name = get_language_name(lang_code)
            st.progress(confidence, text=f"{lang_name} ({lang_code}): {confidence:.2%}")
        
        # Display segments if available
        if detection_result.segments:
            st.markdown("**Language Segments:**")
            for i, segment in enumerate(detection_result.segments):
                lang_name = get_language_name(segment['language'])
                
                with st.expander(f"Segment {i+1}: {lang_name} ({segment['confidence']:.2%})"):
                    if self.language_detector.is_rtl_language(segment['language']):
                        st.markdown(f'<div dir="rtl" style="text-align: right;">{segment["text"]}</div>', unsafe_allow_html=True)
                    else:
                        st.write(segment['text'])
    
    def render_realtime_language_monitor(self, session_id: str = "default"):
        """Render real-time language monitoring interface"""
        st.markdown("### 📊 Real-Time Language Monitor")
        
        # Get session summary
        summary = self.realtime_processor._get_session_language_summary(session_id)
        
        if not summary:
            st.info("No real-time data available. Start processing audio to see language statistics.")
            return
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Chunks", summary['total_chunks'])
        
        with col2:
            st.metric("Languages Detected", len(summary['languages_detected']))
        
        with col3:
            primary_lang_name = get_language_name(summary['primary_language'])
            st.metric("Primary Language", primary_lang_name)
        
        # Language distribution chart
        if summary['language_distribution']:
            st.markdown("**Language Distribution:**")
            
            # Create a simple bar chart using progress bars
            for lang_code, percentage in summary['language_distribution'].items():
                lang_name = get_language_name(lang_code)
                st.progress(percentage / 100, text=f"{lang_name}: {percentage:.1f}%")
        
        # Code-switching indicator
        if summary['has_code_switching']:
            st.warning("🔀 Code-switching detected in this session")
        else:
            st.success("✅ Consistent language usage")


# Global instances
language_detector = LanguageDetector()
multilingual_extractor = MultilingualEntityExtractor()
translation_service = TranslationService()
realtime_processor = RealTimeLanguageProcessor()
multilingual_ui = AdvancedMultilingualUI()