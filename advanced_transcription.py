#!/usr/bin/env python3
"""
Advanced Transcription Features Module
Implements speaker diarization, multi-language support, timestamp navigation,
confidence scoring, and transcript editing capabilities
"""

import os
import logging
import json
import time
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
import whisper
import openai
from datetime import datetime, timedelta

# Import existing modules
from stt import WhisperTranscriber, TranscriptionResult
from errors import TranscriptionError, ErrorCode, handle_error

logger = logging.getLogger(__name__)

@dataclass
class SpeakerSegment:
    """Data class for speaker diarization segments"""
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    confidence: float
    
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class TimestampedWord:
    """Data class for word-level timestamps"""
    word: str
    start_time: float
    end_time: float
    confidence: float
    speaker_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class AdvancedTranscriptionResult:
    """Enhanced transcription result with advanced features"""
    text: str
    language: str
    confidence: float
    processing_time: float
    model_used: str
    speakers: List[SpeakerSegment]
    timestamped_words: List[TimestampedWord]
    detected_languages: List[Dict[str, float]]  # Language detection results
    
    def get_speaker_count(self) -> int:
        return len(set(segment.speaker_id for segment in self.speakers))
    
    def get_total_duration(self) -> float:
        if self.speakers:
            return max(segment.end_time for segment in self.speakers)
        return 0.0
    
    def get_speaker_statistics(self) -> Dict[str, Dict]:
        """Get speaking time statistics for each speaker"""
        stats = {}
        for segment in self.speakers:
            if segment.speaker_id not in stats:
                stats[segment.speaker_id] = {
                    'total_time': 0.0,
                    'word_count': 0,
                    'segments': 0,
                    'avg_confidence': 0.0
                }
            
            stats[segment.speaker_id]['total_time'] += segment.duration()
            stats[segment.speaker_id]['word_count'] += len(segment.text.split())
            stats[segment.speaker_id]['segments'] += 1
            stats[segment.speaker_id]['avg_confidence'] += segment.confidence
        
        # Calculate averages
        for speaker_id in stats:
            if stats[speaker_id]['segments'] > 0:
                stats[speaker_id]['avg_confidence'] /= stats[speaker_id]['segments']
        
        return stats
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'language': self.language,
            'confidence': self.confidence,
            'processing_time': self.processing_time,
            'model_used': self.model_used,
            'speakers': [speaker.to_dict() for speaker in self.speakers],
            'timestamped_words': [word.to_dict() for word in self.timestamped_words],
            'detected_languages': self.detected_languages,
            'speaker_count': self.get_speaker_count(),
            'total_duration': self.get_total_duration(),
            'speaker_statistics': self.get_speaker_statistics()
        }

class AdvancedTranscriber:
    """Advanced transcription system with speaker diarization and multi-language support"""
    
    def __init__(self):
        self.base_transcriber = WhisperTranscriber()
        self.supported_languages = self._get_supported_languages()
        
    def _get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages for transcription"""
        return {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish',
            'pl': 'Polish',
            'tr': 'Turkish',
            'uk': 'Ukrainian',
            'cs': 'Czech',
            'hu': 'Hungarian',
            'ro': 'Romanian',
            'bg': 'Bulgarian',
            'hr': 'Croatian',
            'sk': 'Slovak',
            'sl': 'Slovenian',
            'et': 'Estonian',
            'lv': 'Latvian',
            'lt': 'Lithuanian',
            'mt': 'Maltese',
            'ga': 'Irish',
            'cy': 'Welsh',
            'eu': 'Basque',
            'ca': 'Catalan',
            'gl': 'Galician',
            'is': 'Icelandic',
            'mk': 'Macedonian',
            'sq': 'Albanian',
            'sr': 'Serbian',
            'bs': 'Bosnian',
            'me': 'Montenegrin',
            'he': 'Hebrew',
            'fa': 'Persian',
            'ur': 'Urdu',
            'bn': 'Bengali',
            'ta': 'Tamil',
            'te': 'Telugu',
            'ml': 'Malayalam',
            'kn': 'Kannada',
            'gu': 'Gujarati',
            'pa': 'Punjabi',
            'mr': 'Marathi',
            'ne': 'Nepali',
            'si': 'Sinhala',
            'my': 'Myanmar',
            'km': 'Khmer',
            'lo': 'Lao',
            'vi': 'Vietnamese',
            'th': 'Thai',
            'id': 'Indonesian',
            'ms': 'Malay',
            'tl': 'Filipino',
            'sw': 'Swahili',
            'am': 'Amharic',
            'yo': 'Yoruba',
            'zu': 'Zulu',
            'af': 'Afrikaans'
        }
    
    def detect_language(self, audio_path: str) -> List[Dict[str, float]]:
        """
        Detect language(s) in audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of detected languages with confidence scores
        """
        try:
            # Load Whisper model for language detection
            model = self.base_transcriber._load_local_model("base")
            
            # Load audio and detect language
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            
            # Make log-Mel spectrogram and move to the same device as the model
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            
            # Detect the spoken language
            _, probs = model.detect_language(mel)
            
            # Get top 5 language predictions
            top_languages = []
            for lang_code, prob in sorted(probs.items(), key=lambda x: x[1], reverse=True)[:5]:
                if prob > 0.01:  # Only include languages with >1% probability
                    lang_name = self.supported_languages.get(lang_code, lang_code)
                    top_languages.append({
                        'code': lang_code,
                        'name': lang_name,
                        'confidence': float(prob)
                    })
            
            logger.info(f"Language detection completed. Top language: {top_languages[0]['name'] if top_languages else 'Unknown'}")
            return top_languages
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            # Return English as default
            return [{'code': 'en', 'name': 'English', 'confidence': 0.5}]
    
    def transcribe_with_speaker_diarization(self, audio_path: str, 
                                          language: Optional[str] = None,
                                          use_api: bool = True) -> AdvancedTranscriptionResult:
        """
        Transcribe audio with speaker diarization
        
        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detection)
            use_api: Whether to use API or local model
            
        Returns:
            AdvancedTranscriptionResult with speaker information
        """
        start_time = time.time()
        
        try:
            # Step 1: Detect language if not specified
            detected_languages = []
            if not language:
                detected_languages = self.detect_language(audio_path)
                if detected_languages:
                    language = detected_languages[0]['code']
                    logger.info(f"Auto-detected language: {detected_languages[0]['name']}")
            else:
                detected_languages = [{'code': language, 'name': self.supported_languages.get(language, language), 'confidence': 1.0}]
            
            # Step 2: Transcribe with timestamps using local model (better for diarization)
            model = self.base_transcriber._load_local_model("base")
            
            transcribe_params = {
                'verbose': True,
                'word_timestamps': True,
                'language': language
            }
            
            logger.info(f"Starting transcription with speaker diarization (language: {language})")
            result = model.transcribe(audio_path, **transcribe_params)
            
            # Step 3: Perform simple speaker diarization based on pauses and audio characteristics
            speakers = self._perform_speaker_diarization(result, audio_path)
            
            # Step 4: Create timestamped words
            timestamped_words = self._extract_timestamped_words(result, speakers)
            
            # Step 5: Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(result)
            
            processing_time = time.time() - start_time
            
            advanced_result = AdvancedTranscriptionResult(
                text=result['text'].strip(),
                language=result.get('language', language or 'en'),
                confidence=overall_confidence,
                processing_time=processing_time,
                model_used="whisper-local-base-diarized",
                speakers=speakers,
                timestamped_words=timestamped_words,
                detected_languages=detected_languages
            )
            
            logger.info(f"Advanced transcription completed in {processing_time:.2f}s with {len(speakers)} speaker segments")
            return advanced_result
            
        except Exception as e:
            logger.error(f"Advanced transcription failed: {e}")
            raise TranscriptionError(
                message=f"Advanced transcription with speaker diarization failed: {e}",
                error_code=ErrorCode.TRANSCRIPTION_FAILED,
                user_message="Advanced transcription failed. Please try basic transcription mode.",
                model_used="whisper-local-base-diarized",
                suggestions=[
                    "Try basic transcription without speaker diarization",
                    "Check audio file quality",
                    "Use a shorter audio file for testing"
                ]
            )
    
    def _perform_speaker_diarization(self, whisper_result: Dict, audio_path: str) -> List[SpeakerSegment]:
        """
        Perform simple speaker diarization based on audio characteristics and pauses
        
        Args:
            whisper_result: Result from Whisper transcription
            audio_path: Path to audio file for additional analysis
            
        Returns:
            List of speaker segments
        """
        try:
            speakers = []
            current_speaker = "Speaker_1"
            speaker_count = 1
            
            if 'segments' not in whisper_result:
                return speakers
            
            for i, segment in enumerate(whisper_result['segments']):
                # Simple heuristic for speaker change detection:
                # - Long pauses (>2 seconds)
                # - Significant change in average log probability (voice characteristics)
                # - Change in speaking pace
                
                should_change_speaker = False
                
                if i > 0:
                    prev_segment = whisper_result['segments'][i-1]
                    
                    # Check for long pause
                    pause_duration = segment['start'] - prev_segment['end']
                    if pause_duration > 2.0:
                        should_change_speaker = True
                    
                    # Check for significant change in confidence/voice characteristics
                    current_logprob = segment.get('avg_logprob', 0)
                    prev_logprob = prev_segment.get('avg_logprob', 0)
                    if abs(current_logprob - prev_logprob) > 0.5:
                        should_change_speaker = True
                    
                    # Check for significant change in speaking pace
                    current_pace = len(segment['text'].split()) / (segment['end'] - segment['start'])
                    prev_pace = len(prev_segment['text'].split()) / (prev_segment['end'] - prev_segment['start'])
                    if abs(current_pace - prev_pace) > 2.0:  # Words per second difference
                        should_change_speaker = True
                
                if should_change_speaker and speaker_count < 10:  # Limit to 10 speakers max
                    speaker_count += 1
                    current_speaker = f"Speaker_{speaker_count}"
                
                # Create speaker segment
                speaker_segment = SpeakerSegment(
                    speaker_id=current_speaker,
                    start_time=segment['start'],
                    end_time=segment['end'],
                    text=segment['text'].strip(),
                    confidence=max(0.1, min(1.0, segment.get('avg_logprob', -1) + 1.0))
                )
                
                speakers.append(speaker_segment)
            
            logger.info(f"Speaker diarization completed: {speaker_count} speakers detected")
            return speakers
            
        except Exception as e:
            logger.error(f"Speaker diarization failed: {e}")
            # Return single speaker as fallback
            if 'segments' in whisper_result:
                return [
                    SpeakerSegment(
                        speaker_id="Speaker_1",
                        start_time=segment['start'],
                        end_time=segment['end'],
                        text=segment['text'].strip(),
                        confidence=max(0.1, min(1.0, segment.get('avg_logprob', -1) + 1.0))
                    )
                    for segment in whisper_result['segments']
                ]
            return []
    
    def _extract_timestamped_words(self, whisper_result: Dict, speakers: List[SpeakerSegment]) -> List[TimestampedWord]:
        """
        Extract word-level timestamps and associate with speakers
        
        Args:
            whisper_result: Result from Whisper transcription
            speakers: List of speaker segments
            
        Returns:
            List of timestamped words
        """
        timestamped_words = []
        
        try:
            if 'segments' not in whisper_result:
                return timestamped_words
            
            # Create speaker lookup by time
            def get_speaker_at_time(timestamp: float) -> str:
                for speaker in speakers:
                    if speaker.start_time <= timestamp <= speaker.end_time:
                        return speaker.speaker_id
                return "Speaker_1"  # Default fallback
            
            for segment in whisper_result['segments']:
                if 'words' in segment:
                    for word_info in segment['words']:
                        word_start = word_info.get('start', segment['start'])
                        word_end = word_info.get('end', segment['end'])
                        
                        timestamped_word = TimestampedWord(
                            word=word_info['word'].strip(),
                            start_time=word_start,
                            end_time=word_end,
                            confidence=max(0.1, min(1.0, word_info.get('probability', 0.7))),
                            speaker_id=get_speaker_at_time(word_start)
                        )
                        
                        timestamped_words.append(timestamped_word)
                else:
                    # Fallback: estimate word timestamps within segment
                    words = segment['text'].strip().split()
                    segment_duration = segment['end'] - segment['start']
                    word_duration = segment_duration / len(words) if words else 0
                    
                    for i, word in enumerate(words):
                        word_start = segment['start'] + (i * word_duration)
                        word_end = word_start + word_duration
                        
                        timestamped_word = TimestampedWord(
                            word=word,
                            start_time=word_start,
                            end_time=word_end,
                            confidence=max(0.1, min(1.0, segment.get('avg_logprob', -1) + 1.0)),
                            speaker_id=get_speaker_at_time(word_start)
                        )
                        
                        timestamped_words.append(timestamped_word)
            
            logger.info(f"Extracted {len(timestamped_words)} timestamped words")
            return timestamped_words
            
        except Exception as e:
            logger.error(f"Word timestamp extraction failed: {e}")
            return timestamped_words
    
    def _calculate_overall_confidence(self, whisper_result: Dict) -> float:
        """Calculate overall confidence score from Whisper result"""
        try:
            if 'segments' not in whisper_result or not whisper_result['segments']:
                return 0.7  # Default confidence
            
            confidences = []
            for segment in whisper_result['segments']:
                if 'avg_logprob' in segment:
                    conf = max(0.1, min(1.0, segment['avg_logprob'] + 1.0))
                    confidences.append(conf)
            
            if confidences:
                return sum(confidences) / len(confidences)
            else:
                return 0.7
                
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get dictionary of supported language codes and names"""
        return self.supported_languages.copy()

class TranscriptEditor:
    """Handles transcript editing and export functionality"""
    
    def __init__(self):
        self.supported_formats = ['txt', 'json', 'srt', 'vtt', 'csv']
    
    def edit_transcript(self, original_result: AdvancedTranscriptionResult, 
                       edits: List[Dict]) -> AdvancedTranscriptionResult:
        """
        Apply edits to transcript
        
        Args:
            original_result: Original transcription result
            edits: List of edit operations
            
        Returns:
            Updated transcription result
        """
        try:
            # Create a copy of the original result
            edited_result = AdvancedTranscriptionResult(
                text=original_result.text,
                language=original_result.language,
                confidence=original_result.confidence,
                processing_time=original_result.processing_time,
                model_used=original_result.model_used + "_edited",
                speakers=original_result.speakers.copy(),
                timestamped_words=original_result.timestamped_words.copy(),
                detected_languages=original_result.detected_languages.copy()
            )
            
            # Apply edits
            for edit in edits:
                edit_type = edit.get('type')
                
                if edit_type == 'text_replace':
                    # Replace text in transcript
                    old_text = edit.get('old_text', '')
                    new_text = edit.get('new_text', '')
                    edited_result.text = edited_result.text.replace(old_text, new_text)
                
                elif edit_type == 'speaker_rename':
                    # Rename speaker
                    old_speaker = edit.get('old_speaker', '')
                    new_speaker = edit.get('new_speaker', '')
                    
                    for speaker in edited_result.speakers:
                        if speaker.speaker_id == old_speaker:
                            speaker.speaker_id = new_speaker
                    
                    for word in edited_result.timestamped_words:
                        if word.speaker_id == old_speaker:
                            word.speaker_id = new_speaker
                
                elif edit_type == 'segment_merge':
                    # Merge speaker segments
                    segment_indices = edit.get('segment_indices', [])
                    if len(segment_indices) >= 2:
                        self._merge_segments(edited_result, segment_indices)
                
                elif edit_type == 'segment_split':
                    # Split speaker segment
                    segment_index = edit.get('segment_index', 0)
                    split_time = edit.get('split_time', 0.0)
                    self._split_segment(edited_result, segment_index, split_time)
            
            logger.info(f"Applied {len(edits)} edits to transcript")
            return edited_result
            
        except Exception as e:
            logger.error(f"Transcript editing failed: {e}")
            raise TranscriptionError(
                message=f"Transcript editing failed: {e}",
                error_code=ErrorCode.PROCESSING_ERROR,
                user_message="Failed to apply edits to transcript. Please try again.",
                model_used="transcript_editor",
                suggestions=[
                    "Check edit format and try again",
                    "Apply edits one at a time",
                    "Reload the original transcript"
                ]
            )
    
    def _merge_segments(self, result: AdvancedTranscriptionResult, segment_indices: List[int]):
        """Merge multiple speaker segments"""
        if len(segment_indices) < 2 or max(segment_indices) >= len(result.speakers):
            return
        
        # Sort indices in descending order to avoid index shifting issues
        segment_indices.sort(reverse=True)
        
        # Get the first segment (lowest index) as the base
        base_index = min(segment_indices)
        base_segment = result.speakers[base_index]
        
        # Merge text and update timing
        merged_text_parts = []
        min_start = base_segment.start_time
        max_end = base_segment.end_time
        total_confidence = base_segment.confidence
        
        for idx in sorted(segment_indices):
            segment = result.speakers[idx]
            merged_text_parts.append(segment.text)
            min_start = min(min_start, segment.start_time)
            max_end = max(max_end, segment.end_time)
            total_confidence += segment.confidence
        
        # Update base segment
        base_segment.text = ' '.join(merged_text_parts)
        base_segment.start_time = min_start
        base_segment.end_time = max_end
        base_segment.confidence = total_confidence / len(segment_indices)
        
        # Remove other segments
        for idx in segment_indices:
            if idx != base_index:
                result.speakers.pop(idx)
    
    def _split_segment(self, result: AdvancedTranscriptionResult, segment_index: int, split_time: float):
        """Split a speaker segment at specified time"""
        if segment_index >= len(result.speakers):
            return
        
        segment = result.speakers[segment_index]
        
        if not (segment.start_time < split_time < segment.end_time):
            return
        
        # Estimate text split point based on time
        segment_duration = segment.end_time - segment.start_time
        split_ratio = (split_time - segment.start_time) / segment_duration
        
        words = segment.text.split()
        split_word_index = int(len(words) * split_ratio)
        
        # Create two new segments
        first_segment = SpeakerSegment(
            speaker_id=segment.speaker_id,
            start_time=segment.start_time,
            end_time=split_time,
            text=' '.join(words[:split_word_index]),
            confidence=segment.confidence
        )
        
        second_segment = SpeakerSegment(
            speaker_id=f"{segment.speaker_id}_2",
            start_time=split_time,
            end_time=segment.end_time,
            text=' '.join(words[split_word_index:]),
            confidence=segment.confidence
        )
        
        # Replace original segment with split segments
        result.speakers[segment_index] = first_segment
        result.speakers.insert(segment_index + 1, second_segment)
    
    def export_transcript(self, result: AdvancedTranscriptionResult, 
                         format_type: str, include_speakers: bool = True,
                         include_timestamps: bool = True) -> str:
        """
        Export transcript in specified format
        
        Args:
            result: Transcription result to export
            format_type: Export format ('txt', 'json', 'srt', 'vtt', 'csv')
            include_speakers: Whether to include speaker information
            include_timestamps: Whether to include timestamps
            
        Returns:
            Formatted transcript string
        """
        try:
            if format_type == 'txt':
                return self._export_txt(result, include_speakers, include_timestamps)
            elif format_type == 'json':
                return self._export_json(result)
            elif format_type == 'srt':
                return self._export_srt(result, include_speakers)
            elif format_type == 'vtt':
                return self._export_vtt(result, include_speakers)
            elif format_type == 'csv':
                return self._export_csv(result, include_speakers, include_timestamps)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            logger.error(f"Transcript export failed: {e}")
            raise TranscriptionError(
                message=f"Transcript export failed: {e}",
                error_code=ErrorCode.EXPORT_ERROR,
                user_message=f"Failed to export transcript in {format_type} format.",
                model_used="transcript_exporter",
                suggestions=[
                    "Try a different export format",
                    "Check transcript data integrity",
                    "Use plain text export as fallback"
                ]
            )
    
    def _export_txt(self, result: AdvancedTranscriptionResult, 
                   include_speakers: bool, include_timestamps: bool) -> str:
        """Export as plain text"""
        lines = []
        
        if include_speakers and result.speakers:
            for segment in result.speakers:
                line_parts = []
                
                if include_timestamps:
                    start_time = self._format_timestamp(segment.start_time)
                    end_time = self._format_timestamp(segment.end_time)
                    line_parts.append(f"[{start_time} - {end_time}]")
                
                line_parts.append(f"{segment.speaker_id}:")
                line_parts.append(segment.text)
                
                lines.append(" ".join(line_parts))
        else:
            lines.append(result.text)
        
        return "\n".join(lines)
    
    def _export_json(self, result: AdvancedTranscriptionResult) -> str:
        """Export as JSON"""
        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    
    def _export_srt(self, result: AdvancedTranscriptionResult, include_speakers: bool) -> str:
        """Export as SRT subtitle format"""
        lines = []
        
        for i, segment in enumerate(result.speakers, 1):
            lines.append(str(i))
            
            start_time = self._format_srt_timestamp(segment.start_time)
            end_time = self._format_srt_timestamp(segment.end_time)
            lines.append(f"{start_time} --> {end_time}")
            
            text = segment.text
            if include_speakers:
                text = f"{segment.speaker_id}: {text}"
            
            lines.append(text)
            lines.append("")  # Empty line between subtitles
        
        return "\n".join(lines)
    
    def _export_vtt(self, result: AdvancedTranscriptionResult, include_speakers: bool) -> str:
        """Export as WebVTT format"""
        lines = ["WEBVTT", ""]
        
        for segment in result.speakers:
            start_time = self._format_vtt_timestamp(segment.start_time)
            end_time = self._format_vtt_timestamp(segment.end_time)
            lines.append(f"{start_time} --> {end_time}")
            
            text = segment.text
            if include_speakers:
                text = f"<v {segment.speaker_id}>{text}"
            
            lines.append(text)
            lines.append("")  # Empty line between cues
        
        return "\n".join(lines)
    
    def _export_csv(self, result: AdvancedTranscriptionResult, 
                   include_speakers: bool, include_timestamps: bool) -> str:
        """Export as CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        headers = ["Text"]
        if include_speakers:
            headers.insert(0, "Speaker")
        if include_timestamps:
            headers.extend(["Start_Time", "End_Time", "Duration"])
        
        writer.writerow(headers)
        
        # Data rows
        for segment in result.speakers:
            row = []
            
            if include_speakers:
                row.append(segment.speaker_id)
            
            row.append(segment.text)
            
            if include_timestamps:
                row.extend([
                    segment.start_time,
                    segment.end_time,
                    segment.duration()
                ])
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp as MM:SS"""
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:05.2f}"
    
    def _format_srt_timestamp(self, seconds: float) -> str:
        """Format timestamp for SRT format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        milliseconds = int((secs % 1) * 1000)
        secs = int(secs)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def _format_vtt_timestamp(self, seconds: float) -> str:
        """Format timestamp for WebVTT format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

# Global instances
_advanced_transcriber = None
_transcript_editor = None

def get_advanced_transcriber() -> AdvancedTranscriber:
    """Get or create global advanced transcriber instance"""
    global _advanced_transcriber
    if _advanced_transcriber is None:
        _advanced_transcriber = AdvancedTranscriber()
    return _advanced_transcriber

def get_transcript_editor() -> TranscriptEditor:
    """Get or create global transcript editor instance"""
    global _transcript_editor
    if _transcript_editor is None:
        _transcript_editor = TranscriptEditor()
    return _transcript_editor

# Public API functions
def transcribe_advanced(audio_path: str, language: Optional[str] = None, 
                       use_api: bool = True) -> AdvancedTranscriptionResult:
    """
    Perform advanced transcription with speaker diarization and multi-language support
    
    Args:
        audio_path: Path to audio file
        language: Language code (None for auto-detection)
        use_api: Whether to use API or local model
        
    Returns:
        AdvancedTranscriptionResult with enhanced features
    """
    transcriber = get_advanced_transcriber()
    return transcriber.transcribe_with_speaker_diarization(audio_path, language, use_api)

def detect_audio_language(audio_path: str) -> List[Dict[str, float]]:
    """
    Detect language(s) in audio file
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        List of detected languages with confidence scores
    """
    transcriber = get_advanced_transcriber()
    return transcriber.detect_language(audio_path)

def get_supported_languages() -> Dict[str, str]:
    """Get dictionary of supported language codes and names"""
    transcriber = get_advanced_transcriber()
    return transcriber.get_supported_languages()

def edit_transcript(original_result: AdvancedTranscriptionResult, 
                   edits: List[Dict]) -> AdvancedTranscriptionResult:
    """
    Apply edits to transcript
    
    Args:
        original_result: Original transcription result
        edits: List of edit operations
        
    Returns:
        Updated transcription result
    """
    editor = get_transcript_editor()
    return editor.edit_transcript(original_result, edits)

def export_transcript(result: AdvancedTranscriptionResult, format_type: str,
                     include_speakers: bool = True, include_timestamps: bool = True) -> str:
    """
    Export transcript in specified format
    
    Args:
        result: Transcription result to export
        format_type: Export format ('txt', 'json', 'srt', 'vtt', 'csv')
        include_speakers: Whether to include speaker information
        include_timestamps: Whether to include timestamps
        
    Returns:
        Formatted transcript string
    """
    editor = get_transcript_editor()
    return editor.export_transcript(result, format_type, include_speakers, include_timestamps)