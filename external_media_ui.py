"""
External Media Integration UI Components
Streamlit interface for external media source integration
"""

import streamlit as st
import os
from typing import Dict, List, Optional
import tempfile
from external_media_integration import ExternalMediaManager, MediaSource, ExtractionResult
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExternalMediaUI:
    """Streamlit UI for external media integration"""
    
    def __init__(self):
        self.manager = ExternalMediaManager()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'external_media_results' not in st.session_state:
            st.session_state.external_media_results = []
        if 'processing_status' not in st.session_state:
            st.session_state.processing_status = None
    
    def render_main_interface(self):
        """Render the main external media integration interface"""
        st.header("🌐 External Media Integration")
        st.markdown("Import and process media from external sources")
        
        # Create tabs for different source types
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎥 YouTube", 
            "📹 Zoom", 
            "🎙️ Podcasts", 
            "☁️ Cloud Storage",
            "📊 Results"
        ])
        
        with tab1:
            self.render_youtube_interface()
        
        with tab2:
            self.render_zoom_interface()
        
        with tab3:
            self.render_podcast_interface()
        
        with tab4:
            self.render_cloud_storage_interface()
        
        with tab5:
            self.render_results_interface()
    
    def render_youtube_interface(self):
        """Render YouTube integration interface"""
        st.subheader("YouTube Video Processing")
        st.markdown("Extract audio from YouTube videos for transcription")
        
        # YouTube URL input
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Enter a YouTube video URL to extract audio"
        )
        
        # API key configuration
        with st.expander("⚙️ YouTube API Configuration (Optional)"):
            api_key = st.text_input(
                "YouTube API Key",
                type="password",
                help="Optional: Provide YouTube API key for enhanced metadata"
            )
            if api_key:
                self.manager.youtube.api_key = api_key
        
        # Quality settings
        col1, col2 = st.columns(2)
        with col1:
            audio_quality = st.selectbox(
                "Audio Quality",
                ["192K", "128K", "96K", "64K"],
                index=0,
                help="Select audio quality for extraction"
            )
        
        with col2:
            audio_format = st.selectbox(
                "Audio Format",
                ["wav", "mp3", "m4a"],
                index=0,
                help="Select output audio format"
            )
        
        # Process button
        if st.button("🎵 Extract Audio from YouTube", type="primary"):
            if youtube_url:
                self.process_youtube_video(youtube_url, audio_quality, audio_format)
            else:
                st.error("Please enter a YouTube URL")
    
    def render_zoom_interface(self):
        """Render Zoom integration interface"""
        st.subheader("Zoom Meeting Recordings")
        st.markdown("Access and process Zoom meeting recordings")
        
        # Zoom API configuration
        with st.expander("🔑 Zoom API Configuration", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                zoom_api_key = st.text_input(
                    "Zoom API Key",
                    type="password",
                    help="Your Zoom API key"
                )
            with col2:
                zoom_api_secret = st.text_input(
                    "Zoom API Secret",
                    type="password",
                    help="Your Zoom API secret"
                )
            
            if zoom_api_key and zoom_api_secret:
                self.manager.setup_zoom(zoom_api_key, zoom_api_secret)
                st.success("✅ Zoom API configured")
        
        # Meeting ID input
        meeting_id = st.text_input(
            "Meeting ID",
            placeholder="123-456-789",
            help="Enter the Zoom meeting ID"
        )
        
        # Recording type selection
        recording_type = st.selectbox(
            "Recording Type",
            ["Audio Only", "Video with Audio", "Chat Transcript"],
            help="Select the type of recording to download"
        )
        
        # Process button
        if st.button("📹 Download Zoom Recording", type="primary"):
            if meeting_id:
                if zoom_api_key and zoom_api_secret:
                    self.process_zoom_recording(meeting_id, recording_type)
                else:
                    st.error("Please configure Zoom API credentials")
            else:
                st.error("Please enter a meeting ID")
    
    def render_podcast_interface(self):
        """Render podcast RSS integration interface"""
        st.subheader("Podcast RSS Feeds")
        st.markdown("Import episodes from podcast RSS feeds")
        
        # RSS URL input
        rss_url = st.text_input(
            "RSS Feed URL",
            placeholder="https://feeds.example.com/podcast.xml",
            help="Enter the RSS feed URL of the podcast"
        )
        
        # Load feed button
        if st.button("📡 Load Podcast Feed"):
            if rss_url:
                self.load_podcast_feed(rss_url)
            else:
                st.error("Please enter an RSS feed URL")
        
        # Display episodes if loaded
        if 'podcast_episodes' in st.session_state and st.session_state.podcast_episodes:
            st.subheader("Available Episodes")
            
            episodes = st.session_state.podcast_episodes
            
            # Episode selection
            episode_options = [
                f"{i+1}. {ep.title[:60]}..." if len(ep.title) > 60 else f"{i+1}. {ep.title}"
                for i, ep in enumerate(episodes)
            ]
            
            selected_episode_idx = st.selectbox(
                "Select Episode",
                range(len(episode_options)),
                format_func=lambda x: episode_options[x]
            )
            
            # Show episode details
            if selected_episode_idx is not None:
                episode = episodes[selected_episode_idx]
                
                with st.expander("📝 Episode Details", expanded=True):
                    st.write(f"**Title:** {episode.title}")
                    st.write(f"**Description:** {episode.description[:200]}...")
                    if episode.metadata:
                        st.write(f"**Published:** {episode.metadata.get('published', 'Unknown')}")
                        st.write(f"**Podcast:** {episode.metadata.get('podcast_title', 'Unknown')}")
                
                # Download button
                if st.button("🎙️ Download Episode", type="primary"):
                    self.process_podcast_episode(episode)
    
    def render_cloud_storage_interface(self):
        """Render cloud storage integration interface"""
        st.subheader("Cloud Storage Integration")
        st.markdown("Import media files from Google Drive and Dropbox")
        
        # Service selection
        service = st.selectbox(
            "Cloud Service",
            ["Google Drive", "Dropbox"],
            help="Select the cloud storage service"
        )
        
        if service == "Google Drive":
            self.render_google_drive_interface()
        else:
            self.render_dropbox_interface()
    
    def render_google_drive_interface(self):
        """Render Google Drive interface"""
        st.markdown("### Google Drive")
        
        # Credentials upload
        with st.expander("🔑 Google Drive Setup", expanded=True):
            st.markdown("""
            To use Google Drive integration:
            1. Create a project in Google Cloud Console
            2. Enable the Google Drive API
            3. Create credentials (OAuth 2.0 Client ID)
            4. Download the credentials JSON file
            """)
            
            credentials_file = st.file_uploader(
                "Upload Credentials JSON",
                type=['json'],
                help="Upload your Google Drive API credentials file"
            )
            
            if credentials_file:
                # Save credentials temporarily
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(credentials_file.getvalue().decode())
                    credentials_path = f.name
                
                if self.manager.cloud_storage.setup_google_drive(credentials_path):
                    st.success("✅ Google Drive configured")
                    os.unlink(credentials_path)  # Clean up temp file
                else:
                    st.error("❌ Failed to configure Google Drive")
        
        # File URL input
        gdrive_url = st.text_input(
            "Google Drive File URL",
            placeholder="https://drive.google.com/file/d/...",
            help="Enter the shareable Google Drive file URL"
        )
        
        # Process button
        if st.button("☁️ Download from Google Drive", type="primary"):
            if gdrive_url:
                self.process_gdrive_file(gdrive_url)
            else:
                st.error("Please enter a Google Drive URL")
    
    def render_dropbox_interface(self):
        """Render Dropbox interface"""
        st.markdown("### Dropbox")
        
        # Access token input
        with st.expander("🔑 Dropbox Setup", expanded=True):
            st.markdown("""
            To use Dropbox integration:
            1. Create a Dropbox app at https://www.dropbox.com/developers/apps
            2. Generate an access token
            3. Enter the access token below
            """)
            
            access_token = st.text_input(
                "Dropbox Access Token",
                type="password",
                help="Your Dropbox app access token"
            )
            
            if access_token:
                if self.manager.cloud_storage.setup_dropbox(access_token):
                    st.success("✅ Dropbox configured")
                else:
                    st.error("❌ Failed to configure Dropbox")
        
        # File path input
        file_path = st.text_input(
            "Dropbox File Path",
            placeholder="/path/to/your/file.mp3",
            help="Enter the full path to the file in your Dropbox"
        )
        
        # Process button
        if st.button("📦 Download from Dropbox", type="primary"):
            if file_path and access_token:
                self.process_dropbox_file(file_path)
            else:
                st.error("Please enter file path and configure Dropbox")
    
    def render_results_interface(self):
        """Render results and history interface"""
        st.subheader("Processing Results")
        
        if st.session_state.external_media_results:
            st.markdown(f"**Total processed files:** {len(st.session_state.external_media_results)}")
            
            # Display results
            for i, result in enumerate(st.session_state.external_media_results):
                with st.expander(f"📁 {result.media_info.title if result.media_info else f'File {i+1}'}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        if result.success:
                            st.success("✅ Successfully processed")
                            st.write(f"**Source:** {result.media_info.source_type.title()}")
                            st.write(f"**Title:** {result.media_info.title}")
                            st.write(f"**Local Path:** {result.local_path}")
                            
                            if result.media_info.description:
                                st.write(f"**Description:** {result.media_info.description[:100]}...")
                            
                            # Show metadata
                            if result.media_info.metadata:
                                with st.expander("📊 Metadata"):
                                    st.json(result.media_info.metadata)
                        else:
                            st.error("❌ Processing failed")
                            st.write(f"**Error:** {result.error_message}")
                    
                    with col2:
                        if result.success and result.local_path and os.path.exists(result.local_path):
                            # File info
                            file_size = os.path.getsize(result.local_path)
                            st.metric("File Size", f"{file_size / (1024*1024):.1f} MB")
                            
                            # Action buttons
                            if st.button(f"🎵 Play Audio {i+1}", key=f"play_{i}"):
                                try:
                                    st.audio(result.local_path)
                                except Exception as e:
                                    st.error(f"Cannot play audio: {e}")
                            
                            if st.button(f"🚀 Process for Transcription {i+1}", key=f"transcribe_{i}"):
                                st.info("This would integrate with the main transcription pipeline")
                                # Here you would integrate with your main transcription system
            
            # Clear results button
            if st.button("🗑️ Clear All Results"):
                st.session_state.external_media_results = []
                st.rerun()
        
        else:
            st.info("No processed files yet. Use the tabs above to import media from external sources.")
        
        # Cleanup section
        with st.expander("🧹 Cleanup"):
            st.markdown("Manage temporary files and cleanup")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clean Temp Files"):
                    self.manager.cleanup_temp_files()
                    st.success("Temporary files cleaned up")
            
            with col2:
                max_age = st.number_input("Max Age (hours)", min_value=1, max_value=168, value=24)
                if st.button("⏰ Clean Old Files"):
                    self.manager.cleanup_temp_files(max_age)
                    st.success(f"Files older than {max_age} hours cleaned up")
    
    def process_youtube_video(self, url: str, quality: str, format: str):
        """Process YouTube video"""
        with st.spinner("🎵 Extracting audio from YouTube..."):
            try:
                result = self.manager.process_external_source(url)
                
                if result.success:
                    st.success(f"✅ Successfully extracted audio: {result.media_info.title}")
                    st.session_state.external_media_results.append(result)
                    
                    # Show preview
                    if result.local_path and os.path.exists(result.local_path):
                        st.audio(result.local_path)
                else:
                    st.error(f"❌ Failed to extract audio: {result.error_message}")
                    
            except Exception as e:
                st.error(f"❌ Error processing YouTube video: {str(e)}")
    
    def process_zoom_recording(self, meeting_id: str, recording_type: str):
        """Process Zoom recording"""
        with st.spinner("📹 Downloading Zoom recording..."):
            try:
                result = self.manager.process_external_source(
                    f"https://zoom.us/rec/{meeting_id}",
                    meeting_id=meeting_id
                )
                
                if result.success:
                    st.success(f"✅ Successfully downloaded recording")
                    st.session_state.external_media_results.append(result)
                else:
                    st.error(f"❌ Failed to download recording: {result.error_message}")
                    
            except Exception as e:
                st.error(f"❌ Error processing Zoom recording: {str(e)}")
    
    def load_podcast_feed(self, rss_url: str):
        """Load podcast RSS feed"""
        with st.spinner("📡 Loading podcast feed..."):
            try:
                episodes = self.manager.podcast.parse_rss_feed(rss_url)
                
                if episodes:
                    st.session_state.podcast_episodes = episodes
                    st.success(f"✅ Loaded {len(episodes)} episodes")
                else:
                    st.error("❌ No episodes found in RSS feed")
                    
            except Exception as e:
                st.error(f"❌ Error loading RSS feed: {str(e)}")
    
    def process_podcast_episode(self, episode: MediaSource):
        """Process podcast episode"""
        with st.spinner("🎙️ Downloading podcast episode..."):
            try:
                result = self.manager.podcast.download_episode(episode)
                
                if result.success:
                    st.success(f"✅ Successfully downloaded: {episode.title}")
                    st.session_state.external_media_results.append(result)
                    
                    # Show preview
                    if result.local_path and os.path.exists(result.local_path):
                        st.audio(result.local_path)
                else:
                    st.error(f"❌ Failed to download episode: {result.error_message}")
                    
            except Exception as e:
                st.error(f"❌ Error downloading episode: {str(e)}")
    
    def process_gdrive_file(self, url: str):
        """Process Google Drive file"""
        with st.spinner("☁️ Downloading from Google Drive..."):
            try:
                result = self.manager.process_external_source(url)
                
                if result.success:
                    st.success(f"✅ Successfully downloaded from Google Drive")
                    st.session_state.external_media_results.append(result)
                else:
                    st.error(f"❌ Failed to download: {result.error_message}")
                    
            except Exception as e:
                st.error(f"❌ Error downloading from Google Drive: {str(e)}")
    
    def process_dropbox_file(self, file_path: str):
        """Process Dropbox file"""
        with st.spinner("📦 Downloading from Dropbox..."):
            try:
                result = self.manager.process_external_source(
                    f"https://dropbox.com{file_path}",
                    file_path=file_path
                )
                
                if result.success:
                    st.success(f"✅ Successfully downloaded from Dropbox")
                    st.session_state.external_media_results.append(result)
                else:
                    st.error(f"❌ Failed to download: {result.error_message}")
                    
            except Exception as e:
                st.error(f"❌ Error downloading from Dropbox: {str(e)}")

# Main function for standalone testing
def main():
    st.set_page_config(
        page_title="External Media Integration",
        page_icon="🌐",
        layout="wide"
    )
    
    ui = ExternalMediaUI()
    ui.render_main_interface()

if __name__ == "__main__":
    main()