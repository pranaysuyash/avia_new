"""
AI Provider Integrations Module
Integrates multiple AI API providers to enhance transcription app functionality
"""

import logging
import requests
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import base64
import io
from PIL import Image
import streamlit as st

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Types of AI providers"""
    TEXT_TO_SPEECH = "tts"
    SPEECH_TO_TEXT = "stt"
    IMAGE_GENERATION = "image_gen"
    VIDEO_GENERATION = "video_gen"
    TEXT_GENERATION = "text_gen"
    AUDIO_PROCESSING = "audio_proc"
    VIDEO_PROCESSING = "video_proc"
    MULTIMODAL = "multimodal"


@dataclass
class ProviderConfig:
    """Configuration for an AI provider"""
    name: str
    provider_type: ProviderType
    api_key_env: str
    base_url: str
    supported_features: List[str]
    pricing_tier: str  # "free", "low", "medium", "high"
    quality_rating: int  # 1-5 scale


class AIProviderManager:
    """Manages multiple AI provider integrations"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.active_providers = {}
        self._load_active_providers()
    
    def _initialize_providers(self) -> Dict[str, ProviderConfig]:
        """Initialize all available AI providers"""
        return {
            # Text-to-Speech Providers
            "elevenlabs": ProviderConfig(
                name="ElevenLabs",
                provider_type=ProviderType.TEXT_TO_SPEECH,
                api_key_env="ELEVENLABS_API_KEY",
                base_url="https://api.elevenlabs.io/v1",
                supported_features=["tts", "voice_cloning", "multilingual"],
                pricing_tier="medium",
                quality_rating=5
            ),
            "openai_tts": ProviderConfig(
                name="OpenAI TTS",
                provider_type=ProviderType.TEXT_TO_SPEECH,
                api_key_env="OPENAI_API_KEY",
                base_url="https://api.openai.com/v1",
                supported_features=["tts", "streaming", "multilingual"],
                pricing_tier="low",
                quality_rating=4
            ),
            "play_ht": ProviderConfig(
                name="Play.HT",
                provider_type=ProviderType.TEXT_TO_SPEECH,
                api_key_env="PLAYHT_API_KEY",
                base_url="https://api.play.ht/api/v2",
                supported_features=["tts", "multi_speaker", "40_languages"],
                pricing_tier="medium",
                quality_rating=4
            ),
            "resemble_ai": ProviderConfig(
                name="Resemble AI",
                provider_type=ProviderType.TEXT_TO_SPEECH,
                api_key_env="RESEMBLE_API_KEY",
                base_url="https://app.resemble.ai/api/v2",
                supported_features=["custom_voices", "real_time", "voice_cloning"],
                pricing_tier="high",
                quality_rating=5
            ),
            
            # Speech-to-Text Providers
            "deepgram": ProviderConfig(
                name="Deepgram",
                provider_type=ProviderType.SPEECH_TO_TEXT,
                api_key_env="DEEPGRAM_API_KEY",
                base_url="https://api.deepgram.com/v1",
                supported_features=["real_time", "diarization", "low_latency"],
                pricing_tier="low",
                quality_rating=5
            ),
            "assemblyai": ProviderConfig(
                name="AssemblyAI",
                provider_type=ProviderType.SPEECH_TO_TEXT,
                api_key_env="ASSEMBLYAI_API_KEY",
                base_url="https://api.assemblyai.com/v2",
                supported_features=["sentiment", "keywords", "real_time"],
                pricing_tier="medium",
                quality_rating=4
            ),
            
            # Image Generation Providers
            "stability_ai": ProviderConfig(
                name="Stability AI",
                provider_type=ProviderType.IMAGE_GENERATION,
                api_key_env="STABILITY_API_KEY",
                base_url="https://api.stability.ai/v1",
                supported_features=["stable_diffusion", "high_res", "styles"],
                pricing_tier="medium",
                quality_rating=5
            ),
            "fal_ai": ProviderConfig(
                name="Fal.ai",
                provider_type=ProviderType.IMAGE_GENERATION,
                api_key_env="FAL_API_KEY",
                base_url="https://fal.run/fal-ai",
                supported_features=["fast_inference", "diffusion", "video"],
                pricing_tier="low",
                quality_rating=4
            ),
            "runware": ProviderConfig(
                name="Runware",
                provider_type=ProviderType.IMAGE_GENERATION,
                api_key_env="RUNWARE_API_KEY",
                base_url="https://api.runware.ai/v1",
                supported_features=["sub_second", "upscaling", "background_removal"],
                pricing_tier="low",
                quality_rating=4
            ),
            
            # Video Generation Providers
            "runway": ProviderConfig(
                name="Runway",
                provider_type=ProviderType.VIDEO_GENERATION,
                api_key_env="RUNWAY_API_KEY",
                base_url="https://api.dev.runwayml.com/v1",
                supported_features=["gen4", "text_to_video", "image_to_video"],
                pricing_tier="high",
                quality_rating=5
            ),
            "luma_ai": ProviderConfig(
                name="Luma AI",
                provider_type=ProviderType.VIDEO_GENERATION,
                api_key_env="LUMA_API_KEY",
                base_url="https://api.lumalabs.ai/dream-machine/v1",
                supported_features=["4k_video", "text_to_video", "keyframes"],
                pricing_tier="high",
                quality_rating=5
            ),
            "pika_labs": ProviderConfig(
                name="Pika Labs",
                provider_type=ProviderType.VIDEO_GENERATION,
                api_key_env="PIKA_API_KEY",
                base_url="https://api.pika.art/v1",
                supported_features=["cinematic", "animated", "effects"],
                pricing_tier="medium",
                quality_rating=4
            ),
            "d_id": ProviderConfig(
                name="D-ID",
                provider_type=ProviderType.VIDEO_GENERATION,
                api_key_env="DID_API_KEY",
                base_url="https://api.d-id.com",
                supported_features=["talking_heads", "real_time", "100_languages"],
                pricing_tier="medium",
                quality_rating=4
            ),
            
            # Multimodal Providers
            "replicate": ProviderConfig(
                name="Replicate",
                provider_type=ProviderType.MULTIMODAL,
                api_key_env="REPLICATE_API_TOKEN",
                base_url="https://api.replicate.com/v1",
                supported_features=["community_models", "image", "video", "audio", "text"],
                pricing_tier="medium",
                quality_rating=4
            ),
            "comet_api": ProviderConfig(
                name="CometAPI",
                provider_type=ProviderType.MULTIMODAL,
                api_key_env="COMET_API_KEY",
                base_url="https://api.cometapi.com/v1",
                supported_features=["500_models", "unified_billing", "low_latency"],
                pricing_tier="medium",
                quality_rating=4
            ),
            "aiml_api": ProviderConfig(
                name="AIMLAPI",
                provider_type=ProviderType.MULTIMODAL,
                api_key_env="AIMLAPI_KEY",
                base_url="https://api.aimlapi.com/v1",
                supported_features=["300_models", "99_uptime", "video", "text", "image"],
                pricing_tier="medium",
                quality_rating=4
            )
        }
    
    def _load_active_providers(self):
        """Load active providers based on available API keys"""
        import os
        
        for provider_id, config in self.providers.items():
            api_key = os.getenv(config.api_key_env)
            if api_key:
                self.active_providers[provider_id] = {
                    'config': config,
                    'api_key': api_key,
                    'status': 'active'
                }
                logger.info(f"Loaded provider: {config.name}")
    
    def get_providers_by_type(self, provider_type: ProviderType) -> Dict[str, ProviderConfig]:
        """Get all providers of a specific type"""
        return {
            pid: config for pid, config in self.providers.items()
            if config.provider_type == provider_type and pid in self.active_providers
        }
    
    def get_best_provider(self, provider_type: ProviderType, 
                         feature_requirements: List[str] = None) -> Optional[str]:
        """Get the best provider for a specific type and requirements"""
        candidates = self.get_providers_by_type(provider_type)
        
        if not candidates:
            return None
        
        # Filter by feature requirements
        if feature_requirements:
            candidates = {
                pid: config for pid, config in candidates.items()
                if any(req in config.supported_features for req in feature_requirements)
            }
        
        if not candidates:
            return None
        
        # Sort by quality rating and pricing
        best_provider = max(candidates.items(), 
                          key=lambda x: (x[1].quality_rating, -ord(x[1].pricing_tier[0])))
        
        return best_provider[0]


class EnhancedTTSService:
    """Enhanced Text-to-Speech service with multiple providers"""
    
    def __init__(self, provider_manager: AIProviderManager):
        self.provider_manager = provider_manager
    
    def synthesize_speech(self, text: str, voice_id: str = None, 
                         provider: str = None, **kwargs) -> Dict[str, Any]:
        """Synthesize speech using the best available provider"""
        
        if not provider:
            provider = self.provider_manager.get_best_provider(
                ProviderType.TEXT_TO_SPEECH,
                feature_requirements=kwargs.get('features', [])
            )
        
        if not provider:
            return {'error': 'No TTS provider available'}
        
        provider_config = self.provider_manager.providers[provider]
        
        try:
            if provider == "elevenlabs":
                return self._synthesize_elevenlabs(text, voice_id, **kwargs)
            elif provider == "openai_tts":
                return self._synthesize_openai(text, voice_id, **kwargs)
            elif provider == "play_ht":
                return self._synthesize_playht(text, voice_id, **kwargs)
            elif provider == "resemble_ai":
                return self._synthesize_resemble(text, voice_id, **kwargs)
            else:
                return {'error': f'Provider {provider} not implemented'}
                
        except Exception as e:
            logger.error(f"TTS synthesis failed with {provider}: {e}")
            return {'error': str(e)}
    
    def _synthesize_elevenlabs(self, text: str, voice_id: str = None, **kwargs) -> Dict[str, Any]:
        """Synthesize using ElevenLabs API"""
        api_key = self.provider_manager.active_providers['elevenlabs']['api_key']
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id or 'pNInz6obpgDQGcFmaJgB'}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text,
            "model_id": kwargs.get('model_id', 'eleven_monolingual_v1'),
            "voice_settings": kwargs.get('voice_settings', {
                "stability": 0.5,
                "similarity_boost": 0.5
            })
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            return {
                'audio_data': response.content,
                'format': 'mp3',
                'provider': 'elevenlabs',
                'voice_id': voice_id
            }
        else:
            return {'error': f'ElevenLabs API error: {response.status_code}'}
    
    def _synthesize_openai(self, text: str, voice_id: str = None, **kwargs) -> Dict[str, Any]:
        """Synthesize using OpenAI TTS API"""
        import openai
        
        api_key = self.provider_manager.active_providers['openai_tts']['api_key']
        client = openai.OpenAI(api_key=api_key)
        
        response = client.audio.speech.create(
            model=kwargs.get('model', 'tts-1'),
            voice=voice_id or 'alloy',
            input=text,
            response_format=kwargs.get('format', 'mp3')
        )
        
        return {
            'audio_data': response.content,
            'format': kwargs.get('format', 'mp3'),
            'provider': 'openai_tts',
            'voice_id': voice_id
        }
    
    def get_available_voices(self, provider: str = None) -> List[Dict[str, Any]]:
        """Get available voices from providers"""
        voices = []
        
        providers_to_check = [provider] if provider else self.provider_manager.active_providers.keys()
        
        for prov in providers_to_check:
            if prov == "elevenlabs":
                voices.extend(self._get_elevenlabs_voices())
            elif prov == "openai_tts":
                voices.extend(self._get_openai_voices())
            elif prov == "play_ht":
                voices.extend(self._get_playht_voices())
        
        return voices
    
    def _get_elevenlabs_voices(self) -> List[Dict[str, Any]]:
        """Get ElevenLabs voices"""
        try:
            api_key = self.provider_manager.active_providers['elevenlabs']['api_key']
            
            headers = {"xi-api-key": api_key}
            response = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers)
            
            if response.status_code == 200:
                voices_data = response.json()
                return [
                    {
                        'id': voice['voice_id'],
                        'name': voice['name'],
                        'provider': 'elevenlabs',
                        'language': voice.get('labels', {}).get('language', 'en'),
                        'gender': voice.get('labels', {}).get('gender', 'unknown')
                    }
                    for voice in voices_data.get('voices', [])
                ]
        except Exception as e:
            logger.error(f"Failed to get ElevenLabs voices: {e}")
        
        return []
    
    def _get_openai_voices(self) -> List[Dict[str, Any]]:
        """Get OpenAI TTS voices"""
        return [
            {'id': 'alloy', 'name': 'Alloy', 'provider': 'openai_tts', 'language': 'en', 'gender': 'neutral'},
            {'id': 'echo', 'name': 'Echo', 'provider': 'openai_tts', 'language': 'en', 'gender': 'male'},
            {'id': 'fable', 'name': 'Fable', 'provider': 'openai_tts', 'language': 'en', 'gender': 'neutral'},
            {'id': 'onyx', 'name': 'Onyx', 'provider': 'openai_tts', 'language': 'en', 'gender': 'male'},
            {'id': 'nova', 'name': 'Nova', 'provider': 'openai_tts', 'language': 'en', 'gender': 'female'},
            {'id': 'shimmer', 'name': 'Shimmer', 'provider': 'openai_tts', 'language': 'en', 'gender': 'female'}
        ]


class EnhancedSTTService:
    """Enhanced Speech-to-Text service with multiple providers"""
    
    def __init__(self, provider_manager: AIProviderManager):
        self.provider_manager = provider_manager
    
    def transcribe_audio(self, audio_path: str, provider: str = None, **kwargs) -> Dict[str, Any]:
        """Transcribe audio using the best available provider"""
        
        if not provider:
            provider = self.provider_manager.get_best_provider(
                ProviderType.SPEECH_TO_TEXT,
                feature_requirements=kwargs.get('features', [])
            )
        
        if not provider:
            return {'error': 'No STT provider available'}
        
        try:
            if provider == "deepgram":
                return self._transcribe_deepgram(audio_path, **kwargs)
            elif provider == "assemblyai":
                return self._transcribe_assemblyai(audio_path, **kwargs)
            else:
                return {'error': f'Provider {provider} not implemented'}
                
        except Exception as e:
            logger.error(f"STT transcription failed with {provider}: {e}")
            return {'error': str(e)}
    
    def _transcribe_deepgram(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """Transcribe using Deepgram API"""
        api_key = self.provider_manager.active_providers['deepgram']['api_key']
        
        url = "https://api.deepgram.com/v1/listen"
        
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/wav"
        }
        
        params = {
            "model": kwargs.get('model', 'nova-2'),
            "language": kwargs.get('language', 'en'),
            "smart_format": True,
            "diarize": kwargs.get('diarization', False),
            "punctuate": True,
            "utterances": True
        }
        
        with open(audio_path, 'rb') as audio_file:
            response = requests.post(url, headers=headers, params=params, data=audio_file)
        
        if response.status_code == 200:
            result = response.json()
            
            transcript = ""
            if 'results' in result and 'channels' in result['results']:
                for channel in result['results']['channels']:
                    for alternative in channel['alternatives']:
                        transcript += alternative['transcript']
            
            return {
                'transcript': transcript,
                'confidence': result.get('results', {}).get('channels', [{}])[0].get('alternatives', [{}])[0].get('confidence', 0),
                'provider': 'deepgram',
                'language': kwargs.get('language', 'en'),
                'raw_response': result
            }
        else:
            return {'error': f'Deepgram API error: {response.status_code}'}


class ContentGenerationService:
    """Service for generating visual content from transcripts"""
    
    def __init__(self, provider_manager: AIProviderManager):
        self.provider_manager = provider_manager
    
    def generate_thumbnail(self, transcript: str, provider: str = None, **kwargs) -> Dict[str, Any]:
        """Generate thumbnail image from transcript"""
        
        if not provider:
            provider = self.provider_manager.get_best_provider(
                ProviderType.IMAGE_GENERATION,
                feature_requirements=['fast_inference']
            )
        
        if not provider:
            return {'error': 'No image generation provider available'}
        
        # Create prompt from transcript
        prompt = self._create_image_prompt(transcript, kwargs.get('style', 'professional'))
        
        try:
            if provider == "stability_ai":
                return self._generate_stability_ai(prompt, **kwargs)
            elif provider == "fal_ai":
                return self._generate_fal_ai(prompt, **kwargs)
            elif provider == "runware":
                return self._generate_runware(prompt, **kwargs)
            else:
                return {'error': f'Provider {provider} not implemented'}
                
        except Exception as e:
            logger.error(f"Image generation failed with {provider}: {e}")
            return {'error': str(e)}
    
    def generate_video_summary(self, transcript: str, provider: str = None, **kwargs) -> Dict[str, Any]:
        """Generate video summary from transcript"""
        
        if not provider:
            provider = self.provider_manager.get_best_provider(
                ProviderType.VIDEO_GENERATION,
                feature_requirements=['text_to_video']
            )
        
        if not provider:
            return {'error': 'No video generation provider available'}
        
        # Create video prompt from transcript
        prompt = self._create_video_prompt(transcript, kwargs.get('style', 'professional'))
        
        try:
            if provider == "runway":
                return self._generate_runway_video(prompt, **kwargs)
            elif provider == "luma_ai":
                return self._generate_luma_video(prompt, **kwargs)
            elif provider == "d_id":
                return self._generate_did_video(transcript, **kwargs)
            else:
                return {'error': f'Provider {provider} not implemented'}
                
        except Exception as e:
            logger.error(f"Video generation failed with {provider}: {e}")
            return {'error': str(e)}
    
    def _create_image_prompt(self, transcript: str, style: str) -> str:
        """Create image generation prompt from transcript"""
        # Extract key concepts from transcript
        words = transcript.lower().split()
        key_concepts = []
        
        # Simple keyword extraction (could be enhanced with NLP)
        important_words = ['meeting', 'presentation', 'discussion', 'analysis', 'project', 
                          'business', 'technology', 'data', 'strategy', 'team']
        
        for word in important_words:
            if word in words:
                key_concepts.append(word)
        
        if not key_concepts:
            key_concepts = ['professional', 'business']
        
        prompt = f"A {style} illustration representing {', '.join(key_concepts[:3])}, clean design, modern aesthetic"
        
        return prompt
    
    def _create_video_prompt(self, transcript: str, style: str) -> str:
        """Create video generation prompt from transcript"""
        # Summarize transcript for video prompt
        summary = transcript[:200] + "..." if len(transcript) > 200 else transcript
        
        prompt = f"A {style} video visualization of: {summary}"
        
        return prompt


# Global instances
provider_manager = AIProviderManager()
enhanced_tts = EnhancedTTSService(provider_manager)
enhanced_stt = EnhancedSTTService(provider_manager)
content_generator = ContentGenerationService(provider_manager)