#!/usr/bin/env python3
"""
Content Sourcing Strategy for Smart Recommendations
Multiple content sources: user uploads, YouTube integration, public content platform, and curated content
"""

import streamlit as st
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import requests
import json
from dataclasses import dataclass
from pathlib import Path
import hashlib

from content_recommendations import ContentItem, recommendation_engine

logger = logging.getLogger(__name__)

@dataclass
class ContentSource:
    """Represents a content source configuration"""
    source_type: str  # 'user_upload', 'youtube', 'public_platform', 'curated'
    source_id: str
    name: str
    description: str
    enabled: bool
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit: int = 100  # requests per hour
    content_types: List[str] = None  # ['audio', 'video', 'podcast']

class ContentSourceManager:
    """Manages multiple content sources for the recommendation system"""
    
    def __init__(self):
        self.sources: Dict[str, ContentSource] = {}
        self.initialize_default_sources()
    
    def initialize_default_sources(self):
        """Initialize default content sources"""
        
        # User uploads (primary source)
        self.sources['user_upload'] = ContentSource(
            source_type='user_upload',
            source_id='user_upload',
            name='User Uploads',
            description='Content uploaded directly by users through the transcription interface',
            enabled=True,
            content_types=['audio', 'video']
        )
        
        # YouTube integration
        self.sources['youtube'] = ContentSource(
            source_type='youtube',
            source_id='youtube_api',
            name='YouTube Integration',
            description='Public YouTube videos with transcripts/captions',
            enabled=bool(os.getenv('YOUTUBE_API_KEY')),
            api_key=os.getenv('YOUTUBE_API_KEY'),
            base_url='https://www.googleapis.com/youtube/v3',
            rate_limit=10000,  # YouTube API quota
            content_types=['video']
        )
        
        # Public content platform
        self.sources['public_platform'] = ContentSource(
            source_type='public_platform',
            source_id='public_content',
            name='Public Content Library',
            description='Community-contributed public content with open licensing',
            enabled=True,
            content_types=['audio', 'video', 'podcast']
        )
        
        # Curated educational content
        self.sources['curated_education'] = ContentSource(
            source_type='curated',
            source_id='education_curated',
            name='Educational Content',
            description='Curated educational content from open sources',
            enabled=True,
            content_types=['lecture', 'tutorial', 'course']
        )
        
        # Podcast integration
        self.sources['podcast_feeds'] = ContentSource(
            source_type='podcast',
            source_id='podcast_rss',
            name='Podcast Feeds',
            description='RSS feeds from popular podcasts with transcripts',
            enabled=True,
            content_types=['podcast', 'audio']
        )

class YouTubeContentSource:
    """YouTube content integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://www.googleapis.com/youtube/v3'
    
    def search_videos(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search YouTube videos with captions"""
        try:
            # Search for videos
            search_url = f"{self.base_url}/search"
            search_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'videoCaption': 'closedCaption',  # Only videos with captions
                'maxResults': max_results,
                'key': self.api_key
            }
            
            response = requests.get(search_url, params=search_params)
            response.raise_for_status()
            
            search_results = response.json()
            videos = []
            
            for item in search_results.get('items', []):
                video_info = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'channel_title': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail_url': item['snippet']['thumbnails']['default']['url']
                }
                videos.append(video_info)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error searching YouTube videos: {e}")
            return []
    
    def get_video_captions(self, video_id: str) -> Optional[str]:
        """Get captions/transcript for a YouTube video"""
        try:
            # Get caption tracks
            captions_url = f"{self.base_url}/captions"
            captions_params = {
                'part': 'snippet',
                'videoId': video_id,
                'key': self.api_key
            }
            
            response = requests.get(captions_url, params=captions_params)
            response.raise_for_status()
            
            captions_data = response.json()
            
            # Find English captions
            for item in captions_data.get('items', []):
                if item['snippet']['language'] == 'en':
                    caption_id = item['id']
                    
                    # Download caption content
                    download_url = f"{self.base_url}/captions/{caption_id}"
                    download_params = {
                        'key': self.api_key,
                        'tfmt': 'srt'  # SubRip format
                    }
                    
                    caption_response = requests.get(download_url, params=download_params)
                    caption_response.raise_for_status()
                    
                    # Parse SRT to plain text
                    return self._parse_srt_to_text(caption_response.text)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting YouTube captions: {e}")
            return None
    
    def _parse_srt_to_text(self, srt_content: str) -> str:
        """Parse SRT subtitle format to plain text"""
        lines = srt_content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip sequence numbers and timestamps
            if line and not line.isdigit() and '-->' not in line:
                # Remove HTML tags if present
                import re
                clean_line = re.sub(r'<[^>]+>', '', line)
                if clean_line:
                    text_lines.append(clean_line)
        
        return ' '.join(text_lines)
    
    def create_content_item_from_youtube(self, video_info: Dict, transcript: str) -> ContentItem:
        """Create ContentItem from YouTube video"""
        
        content_id = f"youtube_{video_info['video_id']}"
        
        # Extract basic entities (simplified)
        entities = [
            {
                'text': video_info['channel_title'],
                'type': 'ORG',
                'confidence': 0.9
            }
        ]
        
        # Estimate duration (would need additional API call for exact duration)
        estimated_duration = len(transcript.split()) * 0.5  # ~0.5 seconds per word
        
        content_item = ContentItem(
            id=content_id,
            title=video_info['title'],
            transcript=transcript,
            entities=entities,
            topics=[],  # Will be extracted automatically
            tags=['youtube', 'public_content'],
            duration=estimated_duration,
            language='en',
            confidence=0.85,  # YouTube captions are generally good quality
            created_at=video_info['published_at'],
            user_id='youtube_source',
            file_info={
                'source': 'youtube',
                'video_id': video_info['video_id'],
                'channel': video_info['channel_title'],
                'url': f"https://www.youtube.com/watch?v={video_info['video_id']}",
                'thumbnail': video_info['thumbnail_url']
            }
        )
        
        return content_item

class PublicContentPlatform:
    """Public content platform for community contributions"""
    
    def __init__(self):
        self.content_directory = Path("public_content")
        self.content_directory.mkdir(exist_ok=True)
        self.metadata_file = self.content_directory / "metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """Load public content metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                'content_items': {},
                'contributors': {},
                'categories': [],
                'last_updated': datetime.now().isoformat()
            }
    
    def save_metadata(self):
        """Save public content metadata"""
        self.metadata['last_updated'] = datetime.now().isoformat()
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def submit_public_content(self, content_item: ContentItem, contributor_info: Dict) -> bool:
        """Submit content to public platform"""
        try:
            # Validate content
            if not self._validate_content(content_item):
                return False
            
            # Add public content tags
            content_item.tags.extend(['public_content', 'community_contributed'])
            
            # Store contributor info
            contributor_id = contributor_info.get('id', 'anonymous')
            self.metadata['contributors'][contributor_id] = {
                'name': contributor_info.get('name', 'Anonymous'),
                'email': contributor_info.get('email', ''),
                'contributions': self.metadata['contributors'].get(contributor_id, {}).get('contributions', 0) + 1,
                'last_contribution': datetime.now().isoformat()
            }
            
            # Store content metadata
            self.metadata['content_items'][content_item.id] = {
                'title': content_item.title,
                'contributor': contributor_id,
                'submitted_at': datetime.now().isoformat(),
                'topics': content_item.topics,
                'language': content_item.language,
                'duration': content_item.duration,
                'license': contributor_info.get('license', 'CC BY-SA 4.0'),
                'status': 'pending_review'  # Would need moderation
            }
            
            # Add to recommendation engine
            recommendation_engine.add_content_item(content_item)
            
            # Save metadata
            self.save_metadata()
            
            return True
            
        except Exception as e:
            logger.error(f"Error submitting public content: {e}")
            return False
    
    def _validate_content(self, content_item: ContentItem) -> bool:
        """Validate content for public platform"""
        # Basic validation rules
        if len(content_item.transcript) < 100:  # Minimum transcript length
            return False
        
        if content_item.confidence < 0.7:  # Minimum quality threshold
            return False
        
        if content_item.duration < 30:  # Minimum duration (30 seconds)
            return False
        
        # Check for inappropriate content (simplified)
        inappropriate_keywords = ['spam', 'advertisement', 'promotional']
        transcript_lower = content_item.transcript.lower()
        
        if any(keyword in transcript_lower for keyword in inappropriate_keywords):
            return False
        
        return True
    
    def get_public_content(self, category: Optional[str] = None, limit: int = 20) -> List[ContentItem]:
        """Get public content items"""
        try:
            public_items = []
            
            for content_id, metadata in self.metadata['content_items'].items():
                if metadata['status'] == 'approved':  # Only approved content
                    if category and category not in metadata.get('topics', []):
                        continue
                    
                    # Would load full content item from storage
                    # For now, create a placeholder
                    content_item = self._create_placeholder_item(content_id, metadata)
                    public_items.append(content_item)
                    
                    if len(public_items) >= limit:
                        break
            
            return public_items
            
        except Exception as e:
            logger.error(f"Error getting public content: {e}")
            return []
    
    def _create_placeholder_item(self, content_id: str, metadata: Dict) -> ContentItem:
        """Create placeholder content item from metadata"""
        return ContentItem(
            id=content_id,
            title=metadata['title'],
            transcript="[Public content - full transcript available on request]",
            entities=[],
            topics=metadata['topics'],
            tags=['public_content', 'community_contributed'],
            duration=metadata['duration'],
            language=metadata['language'],
            confidence=0.8,
            created_at=metadata['submitted_at'],
            user_id='public_platform',
            file_info={
                'source': 'public_platform',
                'contributor': metadata['contributor'],
                'license': metadata['license']
            }
        )

class CuratedContentSource:
    """Curated educational and professional content"""
    
    def __init__(self):
        self.curated_sources = {
            'ted_talks': {
                'name': 'TED Talks',
                'description': 'Curated TED Talks with transcripts',
                'api_url': 'https://www.ted.com/talks',
                'content_type': 'educational'
            },
            'coursera_lectures': {
                'name': 'Coursera Public Lectures',
                'description': 'Open Coursera course content',
                'api_url': 'https://www.coursera.org/api',
                'content_type': 'educational'
            },
            'conference_talks': {
                'name': 'Conference Presentations',
                'description': 'Tech conference talks and presentations',
                'content_type': 'professional'
            }
        }
    
    def get_curated_content(self, source: str, topic: str, limit: int = 10) -> List[ContentItem]:
        """Get curated content from specific source"""
        # This would integrate with actual APIs
        # For now, return sample curated content
        
        sample_curated = [
            {
                'title': f'TED Talk: The Future of {topic.title()}',
                'transcript': f'This is a curated TED talk about {topic}. The content discusses innovative approaches and future perspectives...',
                'duration': 1200,  # 20 minutes
                'topics': [topic, 'innovation', 'future'],
                'source': 'ted_talks'
            },
            {
                'title': f'Conference Talk: Advanced {topic.title()} Techniques',
                'transcript': f'Professional conference presentation covering advanced {topic} methodologies and best practices...',
                'duration': 2700,  # 45 minutes
                'topics': [topic, 'professional', 'advanced'],
                'source': 'conference_talks'
            }
        ]
        
        curated_items = []
        
        for item_data in sample_curated[:limit]:
            content_id = hashlib.md5(f"{item_data['title']}{item_data['source']}".encode()).hexdigest()
            
            content_item = ContentItem(
                id=f"curated_{content_id}",
                title=item_data['title'],
                transcript=item_data['transcript'],
                entities=[],
                topics=item_data['topics'],
                tags=['curated_content', item_data['source']],
                duration=item_data['duration'],
                language='en',
                confidence=0.9,  # Curated content is high quality
                created_at=datetime.now().isoformat(),
                user_id='curated_source',
                file_info={
                    'source': 'curated',
                    'original_source': item_data['source'],
                    'content_type': 'educational'
                }
            )
            
            curated_items.append(content_item)
        
        return curated_items

class ContentAggregator:
    """Aggregates content from multiple sources"""
    
    def __init__(self):
        self.source_manager = ContentSourceManager()
        self.youtube_source = None
        self.public_platform = PublicContentPlatform()
        self.curated_source = CuratedContentSource()
        
        # Initialize YouTube if API key available
        if os.getenv('YOUTUBE_API_KEY'):
            self.youtube_source = YouTubeContentSource(os.getenv('YOUTUBE_API_KEY'))
    
    def aggregate_content_for_topic(self, topic: str, max_per_source: int = 5) -> List[ContentItem]:
        """Aggregate content from all sources for a specific topic"""
        aggregated_content = []
        
        # Get content from each enabled source
        for source_id, source in self.source_manager.sources.items():
            if not source.enabled:
                continue
            
            try:
                if source.source_type == 'youtube' and self.youtube_source:
                    youtube_videos = self.youtube_source.search_videos(topic, max_per_source)
                    for video in youtube_videos:
                        transcript = self.youtube_source.get_video_captions(video['video_id'])
                        if transcript:
                            content_item = self.youtube_source.create_content_item_from_youtube(video, transcript)
                            aggregated_content.append(content_item)
                
                elif source.source_type == 'public_platform':
                    public_content = self.public_platform.get_public_content(topic, max_per_source)
                    aggregated_content.extend(public_content)
                
                elif source.source_type == 'curated':
                    curated_content = self.curated_source.get_curated_content(source_id, topic, max_per_source)
                    aggregated_content.extend(curated_content)
                
            except Exception as e:
                logger.error(f"Error aggregating content from {source_id}: {e}")
        
        return aggregated_content
    
    def get_content_source_stats(self) -> Dict[str, Any]:
        """Get statistics about content sources"""
        stats = {
            'total_sources': len(self.source_manager.sources),
            'enabled_sources': sum(1 for s in self.source_manager.sources.values() if s.enabled),
            'source_breakdown': {}
        }
        
        for source_id, source in self.source_manager.sources.items():
            stats['source_breakdown'][source_id] = {
                'name': source.name,
                'enabled': source.enabled,
                'content_types': source.content_types,
                'has_api_key': bool(source.api_key)
            }
        
        return stats

# Global content aggregator instance
content_aggregator = ContentAggregator()