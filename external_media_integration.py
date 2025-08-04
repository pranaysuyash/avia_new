"""
External Media Source Integration System
Handles integration with YouTube, Zoom, RSS feeds, and cloud storage services
"""

import os
import re
import json
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from urllib.parse import urlparse, parse_qs
import tempfile
import feedparser
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MediaSource:
    """Represents an external media source"""
    source_type: str  # youtube, zoom, podcast, gdrive, dropbox
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ExtractionResult:
    """Result of media extraction"""
    success: bool
    local_path: Optional[str] = None
    media_info: Optional[MediaSource] = None
    error_message: Optional[str] = None

class YouTubeIntegration:
    """YouTube video/audio extraction and processing"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video information from YouTube API"""
        if not self.api_key:
            logger.warning("YouTube API key not provided")
            return None
        
        try:
            url = f"{self.base_url}/videos"
            params = {
                'part': 'snippet,contentDetails,statistics',
                'id': video_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('items'):
                return data['items'][0]
            return None
            
        except Exception as e:
            logger.error(f"Error fetching YouTube video info: {e}")
            return None
    
    def download_audio(self, url: str, output_dir: str = "temp") -> ExtractionResult:
        """Download audio from YouTube video using yt-dlp"""
        try:
            import yt_dlp
            
            video_id = self.extract_video_id(url)
            if not video_id:
                return ExtractionResult(
                    success=False,
                    error_message="Invalid YouTube URL"
                )
            
            # Get video info
            video_info = self.get_video_info(video_id)
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
                'extractaudio': True,
                'audioformat': 'wav',
                'audioquality': '192K',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info without downloading first
                info = ydl.extract_info(url, download=False)
                
                # Create media source object
                media_source = MediaSource(
                    source_type="youtube",
                    url=url,
                    title=info.get('title'),
                    description=info.get('description'),
                    duration=info.get('duration'),
                    metadata={
                        'uploader': info.get('uploader'),
                        'upload_date': info.get('upload_date'),
                        'view_count': info.get('view_count'),
                        'like_count': info.get('like_count')
                    }
                )
                
                # Download the audio
                ydl.download([url])
                
                # Find the downloaded file
                expected_filename = ydl.prepare_filename(info).replace('.webm', '.wav').replace('.m4a', '.wav')
                
                return ExtractionResult(
                    success=True,
                    local_path=expected_filename,
                    media_info=media_source
                )
                
        except ImportError:
            return ExtractionResult(
                success=False,
                error_message="yt-dlp not installed. Install with: pip install yt-dlp"
            )
        except Exception as e:
            logger.error(f"Error downloading YouTube audio: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Download failed: {str(e)}"
            )

class ZoomIntegration:
    """Zoom meeting recording integration"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.zoom.us/v2"
        self.access_token = None
    
    def authenticate(self) -> bool:
        """Authenticate with Zoom API"""
        try:
            # This is a simplified example - in production, use proper OAuth flow
            auth_url = "https://zoom.us/oauth/token"
            
            # For server-to-server OAuth (requires JWT or OAuth app)
            # Implementation depends on your Zoom app type
            logger.info("Zoom authentication would be implemented here")
            return True
            
        except Exception as e:
            logger.error(f"Zoom authentication failed: {e}")
            return False
    
    def get_meeting_recordings(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get recordings for a specific meeting"""
        if not self.access_token:
            if not self.authenticate():
                return None
        
        try:
            url = f"{self.base_url}/meetings/{meeting_id}/recordings"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching Zoom recordings: {e}")
            return None
    
    def download_recording(self, download_url: str, output_path: str) -> ExtractionResult:
        """Download Zoom recording"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Create media source
            media_source = MediaSource(
                source_type="zoom",
                url=download_url,
                title=f"Zoom Recording - {datetime.now().strftime('%Y-%m-%d')}",
                metadata={'download_url': download_url}
            )
            
            return ExtractionResult(
                success=True,
                local_path=output_path,
                media_info=media_source
            )
            
        except Exception as e:
            logger.error(f"Error downloading Zoom recording: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Download failed: {str(e)}"
            )

class PodcastRSSIntegration:
    """Podcast RSS feed processing"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AudioTranscriptionApp/1.0'
        })
    
    def parse_rss_feed(self, rss_url: str) -> List[MediaSource]:
        """Parse RSS feed and extract podcast episodes"""
        try:
            feed = feedparser.parse(rss_url)
            episodes = []
            
            for entry in feed.entries:
                # Find audio enclosure
                audio_url = None
                for enclosure in getattr(entry, 'enclosures', []):
                    if enclosure.type.startswith('audio/'):
                        audio_url = enclosure.href
                        break
                
                if audio_url:
                    episode = MediaSource(
                        source_type="podcast",
                        url=audio_url,
                        title=entry.get('title', 'Unknown Episode'),
                        description=entry.get('summary', ''),
                        metadata={
                            'published': entry.get('published'),
                            'author': entry.get('author'),
                            'podcast_title': feed.feed.get('title'),
                            'episode_url': entry.get('link')
                        }
                    )
                    episodes.append(episode)
            
            return episodes
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}")
            return []
    
    def download_episode(self, episode: MediaSource, output_dir: str = "temp") -> ExtractionResult:
        """Download podcast episode"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate safe filename
            safe_title = re.sub(r'[^\w\s-]', '', episode.title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{safe_title}.mp3"
            output_path = os.path.join(output_dir, filename)
            
            # Download the file
            response = self.session.get(episode.url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return ExtractionResult(
                success=True,
                local_path=output_path,
                media_info=episode
            )
            
        except Exception as e:
            logger.error(f"Error downloading podcast episode: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Download failed: {str(e)}"
            )

class CloudStorageIntegration:
    """Google Drive and Dropbox integration"""
    
    def __init__(self):
        self.gdrive_service = None
        self.dropbox_client = None
    
    def setup_google_drive(self, credentials_path: str):
        """Setup Google Drive API client"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            import pickle
            
            SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
            
            creds = None
            token_path = 'token.pickle'
            
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.gdrive_service = build('drive', 'v3', credentials=creds)
            return True
            
        except ImportError:
            logger.error("Google Drive API not installed. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return False
        except Exception as e:
            logger.error(f"Error setting up Google Drive: {e}")
            return False
    
    def setup_dropbox(self, access_token: str):
        """Setup Dropbox API client"""
        try:
            import dropbox
            self.dropbox_client = dropbox.Dropbox(access_token)
            return True
            
        except ImportError:
            logger.error("Dropbox API not installed. Install with: pip install dropbox")
            return False
        except Exception as e:
            logger.error(f"Error setting up Dropbox: {e}")
            return False
    
    def download_from_gdrive(self, file_id: str, output_path: str) -> ExtractionResult:
        """Download file from Google Drive"""
        if not self.gdrive_service:
            return ExtractionResult(
                success=False,
                error_message="Google Drive not configured"
            )
        
        try:
            # Get file metadata
            file_metadata = self.gdrive_service.files().get(fileId=file_id).execute()
            
            # Download file
            request = self.gdrive_service.files().get_media(fileId=file_id)
            
            with open(output_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            
            media_source = MediaSource(
                source_type="gdrive",
                url=f"https://drive.google.com/file/d/{file_id}",
                title=file_metadata.get('name'),
                file_size=int(file_metadata.get('size', 0)),
                metadata=file_metadata
            )
            
            return ExtractionResult(
                success=True,
                local_path=output_path,
                media_info=media_source
            )
            
        except Exception as e:
            logger.error(f"Error downloading from Google Drive: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Download failed: {str(e)}"
            )
    
    def download_from_dropbox(self, file_path: str, output_path: str) -> ExtractionResult:
        """Download file from Dropbox"""
        if not self.dropbox_client:
            return ExtractionResult(
                success=False,
                error_message="Dropbox not configured"
            )
        
        try:
            # Get file metadata
            metadata = self.dropbox_client.files_get_metadata(file_path)
            
            # Download file
            with open(output_path, 'wb') as f:
                self.dropbox_client.files_download_to_file(f, file_path)
            
            media_source = MediaSource(
                source_type="dropbox",
                url=f"https://dropbox.com{file_path}",
                title=metadata.name,
                file_size=metadata.size,
                metadata={
                    'path_lower': metadata.path_lower,
                    'client_modified': metadata.client_modified.isoformat() if metadata.client_modified else None,
                    'server_modified': metadata.server_modified.isoformat() if metadata.server_modified else None
                }
            )
            
            return ExtractionResult(
                success=True,
                local_path=output_path,
                media_info=media_source
            )
            
        except Exception as e:
            logger.error(f"Error downloading from Dropbox: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Download failed: {str(e)}"
            )

class ExternalMediaManager:
    """Main manager for external media source integration"""
    
    def __init__(self):
        self.youtube = YouTubeIntegration()
        self.zoom = None  # Initialize when needed
        self.podcast = PodcastRSSIntegration()
        self.cloud_storage = CloudStorageIntegration()
        self.temp_dir = "temp/external_media"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def setup_zoom(self, api_key: str, api_secret: str):
        """Setup Zoom integration"""
        self.zoom = ZoomIntegration(api_key, api_secret)
    
    def detect_source_type(self, url: str) -> str:
        """Detect the type of external media source"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'zoom.us' in domain:
            return 'zoom'
        elif 'drive.google.com' in domain:
            return 'gdrive'
        elif 'dropbox.com' in domain:
            return 'dropbox'
        elif url.endswith('.xml') or url.endswith('.rss') or 'rss' in url.lower():
            return 'podcast'
        else:
            return 'unknown'
    
    def process_external_source(self, url: str, **kwargs) -> ExtractionResult:
        """Process external media source based on URL"""
        source_type = self.detect_source_type(url)
        
        try:
            if source_type == 'youtube':
                return self.youtube.download_audio(url, self.temp_dir)
            
            elif source_type == 'zoom':
                if not self.zoom:
                    return ExtractionResult(
                        success=False,
                        error_message="Zoom integration not configured"
                    )
                # Extract meeting ID from URL and process
                meeting_id = kwargs.get('meeting_id')
                if not meeting_id:
                    return ExtractionResult(
                        success=False,
                        error_message="Meeting ID required for Zoom recordings"
                    )
                
                recordings = self.zoom.get_meeting_recordings(meeting_id)
                if recordings and recordings.get('recording_files'):
                    # Download first audio recording
                    for recording in recordings['recording_files']:
                        if recording.get('file_type') == 'M4A':
                            output_path = os.path.join(self.temp_dir, f"zoom_recording_{meeting_id}.m4a")
                            return self.zoom.download_recording(recording['download_url'], output_path)
                
                return ExtractionResult(
                    success=False,
                    error_message="No audio recordings found"
                )
            
            elif source_type == 'podcast':
                episodes = self.podcast.parse_rss_feed(url)
                if episodes:
                    # Download the first episode by default
                    episode_index = kwargs.get('episode_index', 0)
                    if episode_index < len(episodes):
                        return self.podcast.download_episode(episodes[episode_index], self.temp_dir)
                
                return ExtractionResult(
                    success=False,
                    error_message="No podcast episodes found"
                )
            
            elif source_type == 'gdrive':
                file_id = self._extract_gdrive_file_id(url)
                if file_id:
                    output_path = os.path.join(self.temp_dir, f"gdrive_{file_id}")
                    return self.cloud_storage.download_from_gdrive(file_id, output_path)
                
                return ExtractionResult(
                    success=False,
                    error_message="Invalid Google Drive URL"
                )
            
            elif source_type == 'dropbox':
                # Extract file path from Dropbox URL
                file_path = kwargs.get('file_path')
                if file_path:
                    output_path = os.path.join(self.temp_dir, f"dropbox_{os.path.basename(file_path)}")
                    return self.cloud_storage.download_from_dropbox(file_path, output_path)
                
                return ExtractionResult(
                    success=False,
                    error_message="Dropbox file path required"
                )
            
            else:
                return ExtractionResult(
                    success=False,
                    error_message=f"Unsupported source type: {source_type}"
                )
                
        except Exception as e:
            logger.error(f"Error processing external source: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Processing failed: {str(e)}"
            )
    
    def _extract_gdrive_file_id(self, url: str) -> Optional[str]:
        """Extract file ID from Google Drive URL"""
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'/open\?id=([a-zA-Z0-9-_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_supported_sources(self) -> List[str]:
        """Get list of supported external media sources"""
        return ['youtube', 'zoom', 'podcast', 'gdrive', 'dropbox']
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary downloaded files"""
        try:
            import time
            current_time = time.time()
            
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > (max_age_hours * 3600):
                        os.remove(file_path)
                        logger.info(f"Cleaned up old temp file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize the external media manager
    manager = ExternalMediaManager()
    
    # Test YouTube integration
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"Processing YouTube URL: {youtube_url}")
    
    result = manager.process_external_source(youtube_url)
    if result.success:
        print(f"Successfully downloaded: {result.local_path}")
        print(f"Media info: {result.media_info}")
    else:
        print(f"Failed: {result.error_message}")
    
    # Test podcast RSS feed
    rss_url = "https://feeds.npr.org/510289/podcast.xml"  # NPR Planet Money
    print(f"\nProcessing RSS feed: {rss_url}")
    
    result = manager.process_external_source(rss_url, episode_index=0)
    if result.success:
        print(f"Successfully downloaded: {result.local_path}")
        print(f"Media info: {result.media_info}")
    else:
        print(f"Failed: {result.error_message}")
    
    print(f"\nSupported sources: {manager.get_supported_sources()}")