"""
Integration utilities for semantic search with the main transcription app
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

from .transcript_library import TranscriptLibrary, TranscriptEntry, TranscriptMetadata

logger = logging.getLogger(__name__)


class SemanticSearchIntegration:
    """Integration layer for semantic search with main app"""
    
    def __init__(self, transcript_library: Optional[TranscriptLibrary] = None):
        self.transcript_library = transcript_library or TranscriptLibrary()
    
    def add_transcription_result(self, 
                               transcript_text: str,
                               file_info: Dict[str, Any] = None,
                               analysis_results: Dict[str, Any] = None,
                               speaker_segments: list = None) -> bool:
        """
        Add a transcription result to the semantic search library
        
        Args:
            transcript_text: The transcribed text
            file_info: Information about the source file
            analysis_results: Results from entity extraction and analysis
            speaker_segments: Speaker diarization results
            
        Returns:
            True if successfully added
        """
        try:
            # Generate transcript ID from content hash and timestamp
            content_hash = hashlib.md5(transcript_text.encode()).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            transcript_id = f"transcript_{timestamp}_{content_hash}"
            
            # Extract file information
            file_path = file_info.get('file_path') if file_info else None
            file_name = file_info.get('file_name', 'Unknown') if file_info else 'Unknown'
            file_size = file_info.get('file_size') if file_info else None
            duration = file_info.get('duration') if file_info else None
            
            # Determine category based on analysis results
            category = self._determine_category(transcript_text, analysis_results)
            
            # Extract tags from entities
            tags = self._extract_tags_from_analysis(analysis_results)
            
            # Count speakers
            speaker_count = None
            if speaker_segments:
                unique_speakers = set()
                for segment in speaker_segments:
                    if 'speaker' in segment:
                        unique_speakers.add(segment['speaker'])
                speaker_count = len(unique_speakers)
            
            # Create metadata
            metadata = TranscriptMetadata(
                transcript_id=transcript_id,
                title=self._generate_title(file_name, transcript_text),
                file_path=file_path,
                duration=duration,
                file_size=file_size,
                language='en',  # Default to English, could be detected
                speaker_count=speaker_count,
                tags=tags,
                category=category,
                source='upload'  # Default source
            )
            
            # Create transcript entry
            transcript_entry = TranscriptEntry(
                metadata=metadata,
                content=transcript_text,
                entities=analysis_results.get('entities', {}) if analysis_results else {},
                speaker_segments=speaker_segments or [],
                analysis_results=analysis_results or {}
            )
            
            # Add to library
            success = self.transcript_library.add_transcript(transcript_entry)
            
            if success:
                logger.info(f"Added transcription result to semantic search library: {transcript_id}")
            else:
                logger.error(f"Failed to add transcription result to library: {transcript_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding transcription result to semantic search: {e}")
            return False
    
    def search_similar_content(self, query: str, limit: int = 10) -> list:
        """
        Search for similar content in the library
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of similar transcripts
        """
        try:
            results = self.transcript_library.search_transcripts(
                query, 
                search_type="semantic",
                limit=limit
            )
            
            # Convert to simple format for main app
            simplified_results = []
            for transcript in results:
                simplified_results.append({
                    'transcript_id': transcript.metadata.transcript_id,
                    'title': transcript.metadata.title,
                    'content_preview': transcript.content[:200] + '...' if len(transcript.content) > 200 else transcript.content,
                    'similarity_score': transcript.analysis_results.get('search_score', 0),
                    'category': transcript.metadata.category,
                    'duration': transcript.metadata.duration,
                    'created_at': transcript.metadata.created_at.isoformat() if transcript.metadata.created_at else None
                })
            
            return simplified_results
            
        except Exception as e:
            logger.error(f"Error searching similar content: {e}")
            return []
    
    def get_transcript_recommendations(self, user_history: list = None, limit: int = 5) -> list:
        """
        Get content recommendations
        
        Args:
            user_history: List of transcript IDs user has viewed
            limit: Maximum recommendations
            
        Returns:
            List of recommended transcripts
        """
        try:
            if not user_history:
                # Get recent transcripts if no history
                recent_transcripts = self.transcript_library.list_transcripts(limit=limit)
                return [self._transcript_to_dict(t) for t in recent_transcripts]
            
            recommendations = self.transcript_library.get_recommendations(user_history, limit)
            return [self._transcript_to_dict(t) for t in recommendations]
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics for display in main app"""
        try:
            return self.transcript_library.get_library_stats()
        except Exception as e:
            logger.error(f"Error getting library stats: {e}")
            return {}
    
    def _determine_category(self, transcript_text: str, analysis_results: Dict[str, Any]) -> str:
        """Determine transcript category based on content and analysis"""
        if not analysis_results:
            return "General"
        
        # Simple heuristic-based categorization
        text_lower = transcript_text.lower()
        
        # Meeting indicators
        meeting_keywords = ['meeting', 'agenda', 'action item', 'follow up', 'next steps', 'minutes']
        if any(keyword in text_lower for keyword in meeting_keywords):
            return "Meeting"
        
        # Interview indicators
        interview_keywords = ['interview', 'question', 'tell me about', 'experience', 'background']
        if any(keyword in text_lower for keyword in interview_keywords):
            return "Interview"
        
        # Lecture/Educational indicators
        lecture_keywords = ['lecture', 'lesson', 'chapter', 'today we will', 'homework', 'assignment']
        if any(keyword in text_lower for keyword in lecture_keywords):
            return "Education"
        
        # Customer service indicators
        service_keywords = ['customer', 'support', 'issue', 'problem', 'help', 'assistance']
        if any(keyword in text_lower for keyword in service_keywords):
            return "Customer Service"
        
        return "General"
    
    def _extract_tags_from_analysis(self, analysis_results: Dict[str, Any]) -> list:
        """Extract relevant tags from analysis results"""
        tags = []
        
        if not analysis_results:
            return tags
        
        # Extract from entities
        entities = analysis_results.get('entities', {})
        
        # Add organization names as tags
        if 'organizations' in entities:
            for org in entities['organizations'][:3]:  # Limit to top 3
                if len(org) > 2:  # Skip very short names
                    tags.append(org)
        
        # Add key topics if available
        if 'key_topics' in analysis_results:
            tags.extend(analysis_results['key_topics'][:5])  # Limit to top 5
        
        # Add sentiment as tag if available
        if 'sentiment' in analysis_results:
            sentiment = analysis_results['sentiment']
            if isinstance(sentiment, dict) and 'label' in sentiment:
                tags.append(f"sentiment_{sentiment['label'].lower()}")
        
        return list(set(tags))  # Remove duplicates
    
    def _generate_title(self, file_name: str, transcript_text: str) -> str:
        """Generate a meaningful title for the transcript"""
        # Use file name if available and meaningful
        if file_name and file_name != 'Unknown' and not file_name.startswith('temp_'):
            # Remove file extension
            title = file_name.rsplit('.', 1)[0]
            return title
        
        # Generate title from first sentence or words
        sentences = transcript_text.split('.')
        if sentences and len(sentences[0]) > 10:
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 50:
                first_sentence = first_sentence[:50] + '...'
            return first_sentence
        
        # Fallback to first few words
        words = transcript_text.split()[:8]
        if words:
            title = ' '.join(words)
            if len(title) > 50:
                title = title[:50] + '...'
            return title
        
        # Final fallback
        return f"Transcript {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    def _transcript_to_dict(self, transcript: TranscriptEntry) -> Dict[str, Any]:
        """Convert transcript entry to dictionary for main app"""
        return {
            'transcript_id': transcript.metadata.transcript_id,
            'title': transcript.metadata.title,
            'content_preview': transcript.content[:200] + '...' if len(transcript.content) > 200 else transcript.content,
            'category': transcript.metadata.category,
            'duration': transcript.metadata.duration,
            'speaker_count': transcript.metadata.speaker_count,
            'tags': transcript.metadata.tags,
            'created_at': transcript.metadata.created_at.isoformat() if transcript.metadata.created_at else None,
            'recommendation_score': transcript.analysis_results.get('recommendation_score', 0)
        }


# Global instance for easy access
semantic_integration = SemanticSearchIntegration()