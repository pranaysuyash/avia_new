"""
Enhanced Multi-Language Transcription Module
Integrates with existing STT system to provide advanced multi-language support
Part of Task 36: Implement advanced multi-language support
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import time
import streamlit as st

from language_support import (
    language_detector, multilingual_extractor, translation_service, 
    realtime_processor, get_language_name, get_supported_languages
)
from stt import TranscriptionResult, get_transcriber
import utils

logger = logging.getLogger(__name__)


@dataclass
class MultilingualTranscriptionResult:
    """Enhanced transcription result with multi-language support"""
    text: str
    confidence: float
    processing_time: float
    model_used: str
    primary_language: str
    detected_languages: List[Tuple[str, float]]
    has_code_switching: bool
    language_segments: Optional[List[Dict[str, Any]]] = None
    translations: Optional[Dict[str, str]] = None  # language_code -> translated_text
    entities: Optional[Dict[str, Any]] = None


class MultilingualTranscriber:
    """Enhanced transcriber with multi-language capabilities"""
    
    def __init__(self):
        self.base_transcriber = get_transcriber()
        self.supported_languages = get_supported_languages()
        
    def transcribe_with_language_detection(self, audio_path: str, 
                                         target_languages: List[str] = None,
                                         enable_translation: bool = False,
                                         enable_entity_extraction: bool = False) -> MultilingualTranscriptionResult:
        """
        Transcribe audio with automatic language detection and optional translation
        
        Args:
            audio_path: Path to audio file
            target_languages: Languages to translate to (optional)
            enable_translation: Whether to translate to target languages
            enable_entity_extraction: Whether to extract entities
            
        Returns:
            MultilingualTranscriptionResult with enhanced language information
        """
        start_time = time.time()
        
        # Step 1: Initial transcription with auto-detection
        logger.info("Starting multi-language transcription with auto-detection")
        
        try:
            # Use enhanced transcription with language detection
            base_result = self.base_transcriber.transcribe_enhanced(
                audio_path, 
                use_api=True, 
                language=None,  # Auto-detect
                enable_timestamps=True
            )
            
            # Step 2: Analyze language content
            detection_result = language_detector.detect_language(base_result.text)
            
            # Step 3: Re-transcribe with detected language if confidence is high
            if detection_result.confidence > 0.8 and detection_result.primary_language != 'en':
                logger.info(f"Re-transcribing with detected language: {detection_result.primary_language}")
                
                # Re-transcribe with specific language for better accuracy
                enhanced_result = self.base_transcriber.transcribe_enhanced(
                    audio_path,
                    use_api=True,
                    language=detection_result.primary_language,
                    enable_timestamps=True
                )
                
                # Use enhanced result if it's better
                if enhanced_result.confidence > base_result.confidence:
                    base_result = enhanced_result
            
            # Step 4: Handle translations if requested
            translations = {}
            if enable_translation and target_languages:
                for target_lang in target_languages:
                    if target_lang != detection_result.primary_language:
                        translation_result = translation_service.translate_text(
                            base_result.text,
                            target_lang,
                            detection_result.primary_language
                        )
                        
                        if 'translated_text' in translation_result:
                            translations[target_lang] = translation_result['translated_text']
            
            # Step 5: Extract entities if requested
            entities = None
            if enable_entity_extraction:
                if detection_result.has_code_switching:
                    entities = multilingual_extractor.extract_entities_multilingual(base_result.text)
                else:
                    entities = multilingual_extractor.extract_entities(
                        base_result.text, 
                        detection_result.primary_language
                    )
            
            processing_time = time.time() - start_time
            
            return MultilingualTranscriptionResult(
                text=base_result.text,
                confidence=base_result.confidence,
                processing_time=processing_time,
                model_used=f"{base_result.model_used}-multilingual",
                primary_language=detection_result.primary_language,
                detected_languages=detection_result.all_languages,
                has_code_switching=detection_result.has_code_switching,
                language_segments=detection_result.segments,
                translations=translations if translations else None,
                entities=entities
            )
            
        except Exception as e:
            logger.error(f"Multi-language transcription failed: {e}")
            # Fallback to basic transcription
            base_result = self.base_transcriber.transcribe(audio_path)
            
            return MultilingualTranscriptionResult(
                text=base_result.text,
                confidence=base_result.confidence,
                processing_time=time.time() - start_time,
                model_used=f"{base_result.model_used}-fallback",
                primary_language='en',
                detected_languages=[('en', 1.0)],
                has_code_switching=False,
                language_segments=None,
                translations=None,
                entities=None
            )
    
    def transcribe_streaming_multilingual(self, audio_chunks: List[str], 
                                        session_id: str = "default") -> List[Dict[str, Any]]:
        """
        Process streaming audio with real-time language detection
        
        Args:
            audio_chunks: List of audio chunk file paths
            session_id: Session identifier for tracking
            
        Returns:
            List of processing results for each chunk
        """
        results = []
        
        for i, chunk_path in enumerate(audio_chunks):
            try:
                # Transcribe chunk
                chunk_result = self.base_transcriber.transcribe(chunk_path, use_api=True)
                
                # Process with real-time language processor
                realtime_result = realtime_processor.process_streaming_text(
                    chunk_result.text, 
                    session_id
                )
                
                # Combine results
                combined_result = {
                    'chunk_index': i,
                    'text': chunk_result.text,
                    'confidence': chunk_result.confidence,
                    'detected_language': realtime_result['detected_language'],
                    'language_confidence': realtime_result['confidence'],
                    'language_switch_detected': realtime_result['language_switch_detected'],
                    'session_summary': realtime_result['session_languages']
                }
                
                results.append(combined_result)
                
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {e}")
                results.append({
                    'chunk_index': i,
                    'error': str(e)
                })
        
        return results
    
    def get_language_specific_models(self) -> Dict[str, List[str]]:
        """Get available models for each language"""
        models = {}
        
        for lang_info in self.supported_languages:
            lang_code = lang_info['code']
            available_models = []
            
            # Whisper supports all languages
            available_models.append('whisper')
            
            # Check if spaCy model is available for NER
            if lang_info['has_ner']:
                available_models.append('spacy_ner')
            
            models[lang_code] = available_models
        
        return models


class MultilingualTranscriptionUI:
    """UI components for multi-language transcription"""
    
    def __init__(self):
        self.transcriber = MultilingualTranscriber()
    
    def render_language_selection_interface(self) -> Dict[str, Any]:
        """Render language selection interface for transcription"""
        st.markdown("### 🌍 Multi-Language Transcription Settings")
        
        # Language detection mode
        detection_mode = st.radio(
            "Language Detection Mode",
            ["Auto-detect", "Specify language", "Multi-language (Code-switching)"],
            help="Choose how to handle language detection"
        )
        
        settings = {'detection_mode': detection_mode}
        
        if detection_mode == "Specify language":
            # Manual language selection
            languages = get_supported_languages()
            lang_options = [f"{lang['name']} ({lang['code']})" for lang in languages]
            lang_codes = [lang['code'] for lang in languages]
            
            selected_idx = st.selectbox(
                "Select transcription language:",
                range(len(lang_options)),
                format_func=lambda x: lang_options[x]
            )
            
            settings['specified_language'] = lang_codes[selected_idx]
        
        # Translation settings
        st.markdown("#### 🔄 Translation Options")
        enable_translation = st.checkbox("Enable automatic translation")
        
        if enable_translation:
            # Target languages for translation
            languages = get_supported_languages()
            lang_options = [f"{lang['name']} ({lang['code']})" for lang in languages]
            
            target_languages = st.multiselect(
                "Translate to languages:",
                lang_options,
                help="Select languages to translate the transcript to"
            )
            
            # Extract language codes
            target_codes = []
            for selection in target_languages:
                code = selection.split('(')[1].split(')')[0]
                target_codes.append(code)
            
            settings['enable_translation'] = True
            settings['target_languages'] = target_codes
        else:
            settings['enable_translation'] = False
            settings['target_languages'] = []
        
        # Entity extraction settings
        st.markdown("#### 🏷️ Entity Extraction Options")
        enable_entities = st.checkbox("Enable multi-language entity extraction")
        settings['enable_entity_extraction'] = enable_entities
        
        if enable_entities:
            entity_languages = st.multiselect(
                "Extract entities in languages:",
                lang_options,
                help="Select languages for entity extraction (auto-detected if empty)"
            )
            
            entity_codes = []
            for selection in entity_languages:
                code = selection.split('(')[1].split(')')[0]
                entity_codes.append(code)
            
            settings['entity_languages'] = entity_codes
        
        return settings
    
    def render_transcription_results(self, result: MultilingualTranscriptionResult):
        """Render enhanced transcription results with multi-language support"""
        st.markdown("## 📝 Multi-Language Transcription Results")
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Primary Language", get_language_name(result.primary_language))
        
        with col2:
            st.metric("Confidence", f"{result.confidence:.2%}")
        
        with col3:
            st.metric("Processing Time", f"{result.processing_time:.1f}s")
        
        with col4:
            code_switch_status = "Yes" if result.has_code_switching else "No"
            st.metric("Code-Switching", code_switch_status)
        
        # Language detection details
        if len(result.detected_languages) > 1:
            st.markdown("### 🔍 Language Detection Details")
            
            for lang_code, confidence in result.detected_languages:
                lang_name = get_language_name(lang_code)
                st.progress(confidence, text=f"{lang_name} ({lang_code}): {confidence:.2%}")
        
        # Main transcript
        st.markdown("### 📄 Original Transcript")
        
        # Handle RTL languages
        if language_detector.is_rtl_language(result.primary_language):
            st.markdown(f'<div dir="rtl" style="text-align: right; font-size: 16px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;">{result.text}</div>', unsafe_allow_html=True)
        else:
            st.text_area("", value=result.text, height=200, key="main_transcript")
        
        # Code-switching segments
        if result.has_code_switching and result.language_segments:
            st.markdown("### 🔀 Language Segments")
            
            for i, segment in enumerate(result.language_segments):
                lang_name = get_language_name(segment['language'])
                
                with st.expander(f"Segment {i+1}: {lang_name} ({segment['confidence']:.2%})"):
                    if language_detector.is_rtl_language(segment['language']):
                        st.markdown(f'<div dir="rtl" style="text-align: right; padding: 10px;">{segment["text"]}</div>', unsafe_allow_html=True)
                    else:
                        st.write(segment['text'])
        
        # Translations
        if result.translations:
            st.markdown("### 🔄 Translations")
            
            for lang_code, translation in result.translations.items():
                lang_name = get_language_name(lang_code)
                
                with st.expander(f"Translation to {lang_name}"):
                    if language_detector.is_rtl_language(lang_code):
                        st.markdown(f'<div dir="rtl" style="text-align: right; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">{translation}</div>', unsafe_allow_html=True)
                    else:
                        st.text_area("", value=translation, height=100, key=f"translation_{lang_code}")
        
        # Entities
        if result.entities:
            st.markdown("### 🏷️ Multi-Language Entities")
            
            if result.entities.get('has_code_switching'):
                # Multi-language entities
                st.info("Entities extracted from multiple languages detected in the text")
                
                # Group entities by language
                entities_by_lang = {}
                for entity in result.entities['entities']:
                    lang = entity.get('language', 'unknown')
                    if lang not in entities_by_lang:
                        entities_by_lang[lang] = []
                    entities_by_lang[lang].append(entity)
                
                for lang_code, entities in entities_by_lang.items():
                    lang_name = get_language_name(lang_code)
                    
                    with st.expander(f"Entities in {lang_name} ({len(entities)} found)"):
                        self._render_entity_list(entities)
            else:
                # Single language entities
                self._render_entity_list(result.entities.get('entities', []))
    
    def _render_entity_list(self, entities: List[Dict[str, Any]]):
        """Render list of entities"""
        if not entities:
            st.info("No entities found")
            return
        
        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.get('label', 'UNKNOWN')
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        # Display entities by type
        for entity_type, type_entities in entities_by_type.items():
            st.markdown(f"**{entity_type}** ({len(type_entities)})")
            
            entity_texts = [entity['text'] for entity in type_entities]
            st.write(", ".join(set(entity_texts)))  # Remove duplicates
    
    def render_streaming_interface(self, session_id: str = "default"):
        """Render interface for streaming multi-language transcription"""
        st.markdown("### 🎙️ Real-Time Multi-Language Transcription")
        
        # Session controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎬 Start Session"):
                realtime_processor.clear_session(session_id)
                st.success("New session started")
        
        with col2:
            if st.button("⏹️ Stop Session"):
                st.info("Session stopped")
        
        with col3:
            if st.button("🗑️ Clear Session"):
                realtime_processor.clear_session(session_id)
                st.success("Session cleared")
        
        # Real-time language monitor
        from language_support import multilingual_ui
        multilingual_ui.render_realtime_language_monitor(session_id)


# Global instance
multilingual_transcriber = MultilingualTranscriber()
multilingual_ui = MultilingualTranscriptionUI()