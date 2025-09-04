"""
Demo script for External Media Integration System
Demonstrates the capabilities of importing media from various external sources
"""

import os
import sys
from pathlib import Path
import logging
from external_media_integration import ExternalMediaManager, MediaSource

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_youtube_integration():
    """Demonstrate YouTube integration"""
    print("\n" + "="*60)
    print("🎥 YOUTUBE INTEGRATION DEMO")
    print("="*60)
    
    manager = ExternalMediaManager()
    
    # Example YouTube URLs (using public domain or creative commons videos)
    test_urls = [
        "https://www.youtube.com/watch?v=C0DPdy98e4c",  # Test video
        "https://youtu.be/ScMzIvxBSi4",  # Short URL format
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📹 Processing YouTube URL {i}: {url}")
        
        try:
            # Detect source type
            source_type = manager.detect_source_type(url)
            print(f"   Detected source type: {source_type}")
            
            # Extract video ID
            video_id = manager.youtube.extract_video_id(url)
            print(f"   Video ID: {video_id}")
            
            # Get video info (if API key is available)
            if manager.youtube.api_key:
                video_info = manager.youtube.get_video_info(video_id)
                if video_info:
                    print(f"   Title: {video_info['snippet']['title']}")
                    print(f"   Duration: {video_info['contentDetails']['duration']}")
            
            # Note: Actual download is commented out to avoid large files in demo
            print("   ⚠️  Audio download skipped in demo (would download actual file)")
            # result = manager.process_external_source(url)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

def demo_podcast_integration():
    """Demonstrate podcast RSS integration"""
    print("\n" + "="*60)
    print("🎙️ PODCAST RSS INTEGRATION DEMO")
    print("="*60)
    
    manager = ExternalMediaManager()
    
    # Example RSS feeds (using public feeds)
    test_feeds = [
        "https://feeds.npr.org/510289/podcast.xml",  # NPR Planet Money
        "https://feeds.megaphone.fm/stuffyoushouldknow",  # Stuff You Should Know
    ]
    
    for i, rss_url in enumerate(test_feeds, 1):
        print(f"\n📡 Processing RSS Feed {i}: {rss_url}")
        
        try:
            # Parse RSS feed
            episodes = manager.podcast.parse_rss_feed(rss_url)
            
            if episodes:
                print(f"   ✅ Found {len(episodes)} episodes")
                
                # Show first 3 episodes
                for j, episode in enumerate(episodes[:3]):
                    print(f"\n   Episode {j+1}:")
                    print(f"     Title: {episode.title}")
                    print(f"     Description: {episode.description[:100]}...")
                    if episode.metadata:
                        print(f"     Published: {episode.metadata.get('published', 'Unknown')}")
                        print(f"     Podcast: {episode.metadata.get('podcast_title', 'Unknown')}")
                
                # Note: Actual download is commented out
                print("\n   ⚠️  Episode download skipped in demo (would download actual file)")
                # result = manager.podcast.download_episode(episodes[0])
                
            else:
                print("   ❌ No episodes found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def demo_cloud_storage_integration():
    """Demonstrate cloud storage integration"""
    print("\n" + "="*60)
    print("☁️ CLOUD STORAGE INTEGRATION DEMO")
    print("="*60)
    
    manager = ExternalMediaManager()
    
    # Example URLs (these are fake for demo purposes)
    test_urls = [
        "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view",
        "https://www.dropbox.com/s/example123/audio_file.mp3?dl=0"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔗 Processing Cloud Storage URL {i}: {url}")
        
        try:
            # Detect source type
            source_type = manager.detect_source_type(url)
            print(f"   Detected source type: {source_type}")
            
            if source_type == "gdrive":
                file_id = manager._extract_gdrive_file_id(url)
                print(f"   Google Drive File ID: {file_id}")
                print("   ⚠️  Google Drive download requires API setup")
                
            elif source_type == "dropbox":
                print("   ⚠️  Dropbox download requires access token setup")
            
            print("   ⚠️  Actual download skipped in demo (requires authentication)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

def demo_zoom_integration():
    """Demonstrate Zoom integration"""
    print("\n" + "="*60)
    print("📹 ZOOM INTEGRATION DEMO")
    print("="*60)
    
    manager = ExternalMediaManager()
    
    print("🔑 Zoom Integration Setup:")
    print("   - Requires Zoom API key and secret")
    print("   - Supports OAuth 2.0 authentication")
    print("   - Can access meeting recordings")
    print("   - Downloads audio/video files")
    
    # Example meeting ID (fake for demo)
    meeting_id = "123-456-789"
    print(f"\n📋 Example Meeting ID: {meeting_id}")
    
    print("   ⚠️  Zoom integration requires API credentials")
    print("   ⚠️  Demo skipped (would require actual Zoom API setup)")

def demo_source_detection():
    """Demonstrate source type detection"""
    print("\n" + "="*60)
    print("🔍 SOURCE TYPE DETECTION DEMO")
    print("="*60)
    
    manager = ExternalMediaManager()
    
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://zoom.us/rec/share/abc123",
        "https://feeds.npr.org/510289/podcast.xml",
        "https://drive.google.com/file/d/abc123/view",
        "https://www.dropbox.com/s/abc123/file.mp3",
        "https://example.com/unknown-source",
    ]
    
    print("🎯 Testing URL detection:")
    for url in test_urls:
        source_type = manager.detect_source_type(url)
        print(f"   {source_type:10} <- {url}")

def demo_supported_features():
    """Demonstrate supported features and capabilities"""
    print("\n" + "="*60)
    print("✨ SUPPORTED FEATURES DEMO")
    print("="*60)
    
    manager = ExternalMediaManager()
    
    print("🎯 Supported External Sources:")
    sources = manager.get_supported_sources()
    for source in sources:
        print(f"   ✅ {source.title()}")
    
    print("\n🔧 Key Features:")
    features = [
        "YouTube video/audio extraction using yt-dlp",
        "Zoom meeting recording download via API",
        "Podcast RSS feed parsing and episode download",
        "Google Drive file access with OAuth",
        "Dropbox file download with access tokens",
        "Automatic source type detection",
        "Metadata extraction and preservation",
        "Temporary file management and cleanup",
        "Error handling and retry logic",
        "Progress tracking and status updates"
    ]
    
    for feature in features:
        print(f"   ✅ {feature}")
    
    print("\n📋 File Format Support:")
    formats = [
        "Audio: MP3, WAV, M4A, OGG, FLAC",
        "Video: MP4, AVI, MOV, MKV (audio extraction)",
        "Podcast: RSS/XML feed parsing",
        "Cloud: Any file type supported by storage service"
    ]
    
    for format_info in formats:
        print(f"   ✅ {format_info}")

def demo_error_handling():
    """Demonstrate error handling capabilities"""
    print("\n" + "="*60)
    print("🛡️ ERROR HANDLING DEMO")
    print("="*60)
    
    manager = ExternalMediaManager()
    
    # Test various error scenarios
    error_scenarios = [
        ("Invalid YouTube URL", "https://example.com/not-youtube"),
        ("Malformed URL", "not-a-url-at-all"),
        ("Unsupported source", "https://unsupported-site.com/media"),
        ("Empty URL", ""),
    ]
    
    print("🧪 Testing error scenarios:")
    for scenario_name, test_url in error_scenarios:
        print(f"\n   Testing: {scenario_name}")
        print(f"   URL: {test_url}")
        
        try:
            if test_url:
                source_type = manager.detect_source_type(test_url)
                print(f"   Detected type: {source_type}")
                
                # This would normally fail gracefully
                result = manager.process_external_source(test_url)
                if not result.success:
                    print(f"   ✅ Handled gracefully: {result.error_message}")
                else:
                    print(f"   ⚠️  Unexpected success")
            else:
                print("   ✅ Empty URL handled")
                
        except Exception as e:
            print(f"   ✅ Exception caught: {e}")

def demo_cleanup_operations():
    """Demonstrate cleanup and maintenance operations"""
    print("\n" + "="*60)
    print("🧹 CLEANUP OPERATIONS DEMO")
    print("="*60)
    
    manager = ExternalMediaManager()
    
    print("📁 Temporary Directory Management:")
    print(f"   Temp directory: {manager.temp_dir}")
    print(f"   Directory exists: {os.path.exists(manager.temp_dir)}")
    
    # Create some fake temp files for demo
    temp_files = ["demo_file1.mp3", "demo_file2.wav", "demo_file3.m4a"]
    
    print("\n📝 Creating demo temp files:")
    for filename in temp_files:
        file_path = os.path.join(manager.temp_dir, filename)
        try:
            with open(file_path, 'w') as f:
                f.write("demo content")
            print(f"   ✅ Created: {filename}")
        except Exception as e:
            print(f"   ❌ Failed to create {filename}: {e}")
    
    # List files
    try:
        files = os.listdir(manager.temp_dir)
        print(f"\n📋 Files in temp directory: {len(files)}")
        for file in files:
            print(f"   - {file}")
    except Exception as e:
        print(f"   ❌ Error listing files: {e}")
    
    # Cleanup demo
    print("\n🧹 Cleanup operations:")
    try:
        manager.cleanup_temp_files(max_age_hours=0)  # Clean all files
        print("   ✅ Cleanup completed")
        
        # Check remaining files
        remaining_files = os.listdir(manager.temp_dir)
        print(f"   📋 Remaining files: {len(remaining_files)}")
        
    except Exception as e:
        print(f"   ❌ Cleanup error: {e}")

def main():
    """Run the complete demo"""
    print("🌐 EXTERNAL MEDIA INTEGRATION SYSTEM DEMO")
    print("=" * 80)
    print("This demo showcases the capabilities of the external media integration system.")
    print("Note: Some operations are simulated to avoid downloading large files.")
    
    try:
        # Run all demo sections
        demo_source_detection()
        demo_supported_features()
        demo_youtube_integration()
        demo_podcast_integration()
        demo_cloud_storage_integration()
        demo_zoom_integration()
        demo_error_handling()
        demo_cleanup_operations()
        
        print("\n" + "="*80)
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\n📋 Next Steps:")
        print("   1. Install required dependencies: yt-dlp, feedparser, google-api-python-client, dropbox")
        print("   2. Configure API keys for YouTube, Zoom, Google Drive, Dropbox")
        print("   3. Test with actual media sources")
        print("   4. Integrate with main transcription pipeline")
        print("   5. Deploy to production environment")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()