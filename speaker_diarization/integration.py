"""
Integration of speaker diarization with transcription pipeline
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import asyncio
from pathlib import Path

from .diarization_manager import DiarizationManager, DiarizationResult, SpeakerSegment
from .providers import PyannoteProvider, SimpleVADProvider, MockProvider

logger = logging.getLogger(__name__)


class TranscriptionDiarizationIntegrator:
    """Integrates speaker diarization with transcription results"""
    
    def __init__(self):
        self.diarization_manager = DiarizationManager()
        self.providers = {
            'pyannote': PyannoteProvider,
            'simple_vad': SimpleVADProvider,
            'mock': MockProvider
        }
        
    def get_provider(self, provider_name: str, config: Dict[str, Any] = None) -> Optional[Any]:
        """Get a diarization provider by name"""
        provider_class = self.providers.get(provider_name)
        if provider_class:
            provider = provider_class(config or {})
            if provider.is_available():
                return provider
            else:
                logger.warning(f"Provider {provider_name} is not available")
        return None
    
    async def process_with_diarization(self,
                                     audio_path: str,
                                     transcript: str,
                                     provider_name: str = 'mock',
                                     config: Dict[str, Any] = None) -> Tuple[str, DiarizationResult]:
        """Process audio with both transcription and diarization"""
        # Get provider
        provider = self.get_provider(provider_name, config)
        if not provider:
            # Fallback to mock provider
            logger.warning(f"Provider {provider_name} not available, using mock provider")
            provider = self.get_provider('mock', config)
        
        # Set provider in manager
        self.diarization_manager.set_provider(provider)
        
        # Run diarization
        diarization_result = await self.diarization_manager.process_audio(
            audio_path,
            min_segment_duration=config.get('min_segment_duration', 1.0),
            max_speakers=config.get('max_speakers'),
            use_cache=config.get('use_cache', True)
        )
        
        # Align with transcript if we have word-level timestamps
        if transcript:
            enhanced_transcript = self.align_transcript_with_speakers(
                transcript,
                diarization_result
            )
        else:
            enhanced_transcript = transcript
        
        return enhanced_transcript, diarization_result
    
    def align_transcript_with_speakers(self,
                                     transcript: str,
                                     diarization_result: DiarizationResult) -> str:
        """Align transcript text with speaker segments"""
        # For now, return a simple formatted version
        # In a real implementation, this would use word-level timestamps
        
        lines = []
        current_speaker = None
        
        for segment in diarization_result.segments:
            speaker_info = diarization_result.speakers.get(segment.speaker_id)
            speaker_label = speaker_info.label if speaker_info else segment.speaker_id
            
            if current_speaker != speaker_label:
                lines.append(f"\n[{speaker_label}]")
                current_speaker = speaker_label
            
            # Add timestamp
            timestamp = f"[{segment.start_time:.1f}s - {segment.end_time:.1f}s]"
            
            # Add text (placeholder for now)
            if segment.text:
                lines.append(f"{timestamp} {segment.text}")
            else:
                # Extract portion of transcript based on timing
                # This is a simplified approach
                words_per_second = len(transcript.split()) / diarization_result.audio_duration
                start_word = int(segment.start_time * words_per_second)
                end_word = int(segment.end_time * words_per_second)
                
                transcript_words = transcript.split()
                segment_text = ' '.join(transcript_words[start_word:end_word])
                
                if segment_text:
                    lines.append(f"{timestamp} {segment_text}")
        
        return '\n'.join(lines)
    
    def create_enhanced_export_data(self,
                                  transcript: str,
                                  diarization_result: DiarizationResult,
                                  entities: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create enhanced export data with speaker information"""
        export_data = {
            'transcript': transcript,
            'speakers': {},
            'segments': [],
            'entities': entities or [],
            'metadata': {
                'has_speakers': True,
                'speaker_count': len(diarization_result.speakers),
                'audio_duration': diarization_result.audio_duration
            }
        }
        
        # Add speaker information
        for speaker_id, speaker_info in diarization_result.speakers.items():
            export_data['speakers'][speaker_id] = {
                'label': speaker_info.label or speaker_id,
                'color': speaker_info.color,
                'total_time': speaker_info.total_time,
                'segment_count': speaker_info.segment_count,
                'speaking_percentage': getattr(speaker_info, 'speaking_percentage', 0)
            }
        
        # Add segments with text
        for segment in diarization_result.segments:
            export_data['segments'].append({
                'speaker_id': segment.speaker_id,
                'speaker_label': diarization_result.speakers[segment.speaker_id].label or segment.speaker_id,
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'duration': segment.duration,
                'text': segment.text or '',
                'confidence': segment.confidence
            })
        
        return export_data
    
    def format_for_srt_with_speakers(self,
                                   diarization_result: DiarizationResult,
                                   transcript: str) -> str:
        """Format transcript as SRT with speaker labels"""
        srt_lines = []
        
        # Simple approach: create one subtitle per speaker segment
        for idx, segment in enumerate(diarization_result.segments):
            speaker_info = diarization_result.speakers.get(segment.speaker_id)
            speaker_label = speaker_info.label if speaker_info else segment.speaker_id
            
            # Format timestamps
            start_time = self._seconds_to_srt_time(segment.start_time)
            end_time = self._seconds_to_srt_time(segment.end_time)
            
            # Get text for this segment
            text = segment.text or f"[{speaker_label} speaking]"
            
            # Add speaker label to text
            text_with_speaker = f"[{speaker_label}] {text}"
            
            # Create SRT entry
            srt_lines.append(f"{idx + 1}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text_with_speaker)
            srt_lines.append("")  # Empty line between entries
        
        return '\n'.join(srt_lines)
    
    def format_for_vtt_with_speakers(self,
                                   diarization_result: DiarizationResult,
                                   transcript: str) -> str:
        """Format transcript as WebVTT with speaker labels"""
        vtt_lines = ["WEBVTT", ""]
        
        for idx, segment in enumerate(diarization_result.segments):
            speaker_info = diarization_result.speakers.get(segment.speaker_id)
            speaker_label = speaker_info.label if speaker_info else segment.speaker_id
            speaker_color = speaker_info.color if speaker_info else '#FFFFFF'
            
            # Format timestamps
            start_time = self._seconds_to_vtt_time(segment.start_time)
            end_time = self._seconds_to_vtt_time(segment.end_time)
            
            # Get text for this segment
            text = segment.text or f"[{speaker_label} speaking]"
            
            # Add speaker label with color
            text_with_speaker = f'<v {speaker_label}><c.speaker{idx % 10}>{text}</c></v>'
            
            # Create VTT entry
            vtt_lines.append(f"{start_time} --> {end_time}")
            vtt_lines.append(text_with_speaker)
            vtt_lines.append("")  # Empty line between entries
        
        # Add style section for speaker colors
        style_section = ["", "STYLE", "::cue(.speaker0) { color: #FF6B6B; }"]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
                 '#FF9FF3', '#54A0FF', '#48DBFB', '#A29BFE', '#FD79A8']
        
        for i in range(10):
            style_section.append(f"::cue(.speaker{i}) {{ color: {colors[i]}; }}")
        
        return '\n'.join(style_section + [""] + vtt_lines)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to WebVTT time format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"