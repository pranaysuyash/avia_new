"""
API Wrappers for Streamlit Apps

Provides wrapper modules that mimic the interface of direct backend modules
but use the API client internally. This allows for minimal changes when
refactoring from direct imports to API usage.
"""

import base64
import tempfile
import os
from typing import Dict, Any, List, Optional, Tuple
from api_client import get_api_client

# Try to import streamlit, but don't fail if not available
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    
    # Mock st object for non-Streamlit contexts
    class MockSt:
        def error(self, msg):
            print(f"ERROR: {msg}")
    
    st = MockSt()

class MediaWrapper:
    """Wrapper for media module functionality using API"""
    
    def __init__(self):
        self.api_client = get_api_client()
    
    def extract_audio(self, file_path: str) -> str:
        """Extract audio from video file"""
        try:
            response = self.api_client.process_media_file(
                file_path, 
                operation="extract_audio"
            )
            
            if response.get("success"):
                # Save extracted audio to temp file
                audio_data = base64.b64decode(response["audio_data"])
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    tmp.write(audio_data)
                    return tmp.name
            else:
                raise Exception(response.get("error", "Failed to extract audio"))
        except Exception as e:
            st.error(f"Media processing error: {str(e)}")
            raise
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """Get media file information"""
        return self.api_client.get_media_info(file_path)
    
    def is_valid_media_file(self, file_path: str) -> bool:
        """Check if file is valid media"""
        try:
            info = self.get_media_info(file_path)
            return info.get("valid", False)
        except:
            return False

class STTWrapper:
    """Wrapper for speech-to-text functionality using API"""
    
    def __init__(self):
        self.api_client = get_api_client()
    
    def transcribe(self, audio_path: str, language: str = "en-US", **kwargs) -> Dict[str, Any]:
        """Transcribe audio file"""
        try:
            # Create transcription
            response = self.api_client.create_transcription(
                audio_path,
                language=language,
                **kwargs
            )
            
            if response.get("transcription_id"):
                # Poll for completion
                transcription_id = response["transcription_id"]
                
                # In a real implementation, you'd poll the status endpoint
                # For now, we'll assume synchronous processing
                result = self.api_client.get_transcription_result(transcription_id)
                
                # Convert to expected format
                return {
                    'text': result.get('text', ''),
                    'segments': result.get('segments', []),
                    'language': result.get('language', language),
                    'duration': result.get('duration', 0),
                    'confidence': result.get('confidence', 0)
                }
            else:
                raise Exception(response.get("error", "Failed to create transcription"))
        except Exception as e:
            st.error(f"Transcription error: {str(e)}")
            raise
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages for transcription"""
        # This would normally come from an API endpoint
        return ["en-US", "es-ES", "fr-FR", "de-DE", "ja-JP", "ko-KR", "zh-CN"]

class NERBasicWrapper:
    """Wrapper for basic NER functionality using API"""
    
    def __init__(self):
        self.api_client = get_api_client()
    
    def extract_entities(self, text: str, entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Extract entities from text"""
        try:
            response = self.api_client.extract_entities(text, entity_types)
            
            if response.get("success"):
                return response.get("entities", [])
            else:
                raise Exception(response.get("error", "Failed to extract entities"))
        except Exception as e:
            st.error(f"NER error: {str(e)}")
            raise
    
    def get_entity_types(self) -> List[str]:
        """Get supported entity types"""
        return self.api_client.get_entity_types()

class NERAdvancedWrapper:
    """Wrapper for advanced NER functionality using API"""
    
    def __init__(self):
        self.api_client = get_api_client()
        self.basic_ner = NERBasicWrapper()
    
    def extract_entities_advanced(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities with advanced options"""
        # For now, use basic extraction
        # In a real implementation, this would use a specific advanced endpoint
        entities = self.basic_ner.extract_entities(text)
        
        # Group by type if requested
        if options.get("group_by_type", False):
            grouped = {}
            for entity in entities:
                entity_type = entity.get("type", "UNKNOWN")
                if entity_type not in grouped:
                    grouped[entity_type] = []
                grouped[entity_type].append(entity)
            
            return {
                "entities": entities,
                "grouped": grouped,
                "summary": {
                    "total": len(entities),
                    "types": list(grouped.keys())
                }
            }
        
        return {"entities": entities}

class TTSWrapper:
    """Wrapper for text-to-speech functionality using API"""
    
    def __init__(self):
        self.api_client = get_api_client()
    
    def synthesize(self, text: str, voice: str = "en-US-Standard-A", **options) -> str:
        """Synthesize speech from text"""
        try:
            response = self.api_client.synthesize_speech(text, voice, **options)
            
            if response.get("success"):
                # Save audio to temp file
                audio_data = base64.b64decode(response["audio_data"])
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                    tmp.write(audio_data)
                    return tmp.name
            else:
                raise Exception(response.get("error", "Failed to synthesize speech"))
        except Exception as e:
            st.error(f"TTS error: {str(e)}")
            raise
    
    def get_voices(self, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available TTS voices"""
        return self.api_client.get_tts_voices(language)

class UtilsWrapper:
    """Wrapper for utility functions"""
    
    def __init__(self):
        self.api_client = get_api_client()
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def save_results(self, results: Dict[str, Any], filename: str) -> bool:
        """Save results to file"""
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Failed to save results: {str(e)}")
            return False

# Create singleton instances
media = MediaWrapper()
stt = STTWrapper()
ner_basic = NERBasicWrapper()
ner_advanced = NERAdvancedWrapper()
tts = TTSWrapper()
utils = UtilsWrapper()