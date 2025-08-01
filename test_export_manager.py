#!/usr/bin/env python3
"""
Test export manager functionality
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from export_manager import MultimediaExporter, ExportConfig, SharingManager, ShareConfig


def test_export_manager():
    """Test export manager functionality"""
    print("📤 Testing Export Manager")
    print("=" * 50)
    
    # Sample transcript data
    sample_data = {
        'id': 'test_transcript_001',
        'title': 'Sample Team Meeting',
        'transcript': '''Welcome everyone to our weekly team meeting. I'm excited to share updates on our project progress.

First, let's review what we accomplished this week. Our development team successfully implemented the new authentication system, which has improved security and user experience. The testing results show 99.9% uptime and positive user feedback.

However, we did encounter some challenges with the API integration. The third-party service experienced unexpected downtime, which delayed our feature rollout by two days. Our team worked overtime to implement a fallback solution.

Moving forward, we need to focus on three key areas: improving system reliability, enhancing user onboarding, and expanding our feature set. These improvements will help us meet our Q4 goals.

Sarah, can you provide an update on the marketing campaign? And Mike, please share the latest analytics data from our user engagement metrics.

Let's schedule individual follow-up meetings to address specific technical issues. Thank you all for your dedication and hard work.''',
        'duration': 180.5,
        'language': 'en',
        'confidence': 0.95,
        'created_at': '2024-01-15T10:30:00',
        'speakers': ['Manager', 'Sarah', 'Mike'],
        'entities': [
            {'text': 'authentication system', 'label': 'TECHNOLOGY', 'confidence': 0.9, 'start': 120, 'end': 140},
            {'text': 'Q4 goals', 'label': 'TIMELINE', 'confidence': 0.85, 'start': 450, 'end': 458},
            {'text': 'Sarah', 'label': 'PERSON', 'confidence': 0.95, 'start': 520, 'end': 525},
            {'text': 'Mike', 'label': 'PERSON', 'confidence': 0.95, 'start': 580, 'end': 584},
            {'text': 'API integration', 'label': 'TECHNOLOGY', 'confidence': 0.88, 'start': 280, 'end': 295}
        ],
        'speaker_segments': [
            {
                'speaker_id': 'Manager',
                'start_time': 0.0,
                'duration': 15.5,
                'text': 'Welcome everyone to our weekly team meeting.',
                'confidence': 0.95
            },
            {
                'speaker_id': 'Manager', 
                'start_time': 15.5,
                'duration': 25.0,
                'text': 'First, let\'s review what we accomplished this week.',
                'confidence': 0.92
            },
            {
                'speaker_id': 'Sarah',
                'start_time': 120.0,
                'duration': 20.0,
                'text': 'The marketing campaign is showing great results.',
                'confidence': 0.89
            },
            {
                'speaker_id': 'Mike',
                'start_time': 140.0,
                'duration': 18.5,
                'text': 'User engagement has increased by 35% this month.',
                'confidence': 0.91
            }
        ]
    }
    
    # Create temp directory for exports
    temp_dir = tempfile.mkdtemp()
    exporter = MultimediaExporter(temp_dir)
    
    try:
        print(f"\n📁 Using temp directory: {temp_dir}")
        
        # Test different export formats
        formats_to_test = ['pdf', 'docx', 'json', 'csv', 'html', 'txt', 'xml', 'md']
        
        for export_format in formats_to_test:
            print(f"\n{export_format.upper()} Export Test:")
            
            try:
                config = ExportConfig(
                    format=export_format,
                    include_metadata=True,
                    include_entities=True,
                    include_speaker_info=True
                )
                
                export_path = exporter.export_transcript(sample_data, config)
                
                # Check if file was created
                if os.path.exists(export_path):
                    file_size = os.path.getsize(export_path)
                    print(f"✅ {export_format.upper()}: {Path(export_path).name} ({file_size:,} bytes)")
                    
                    # Quick content validation for text formats
                    if export_format in ['txt', 'md', 'html', 'xml']:
                        with open(export_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'team meeting' in content.lower():
                                print(f"   Content validation: ✅")
                            else:
                                print(f"   Content validation: ❌")
                    
                    # Cleanup individual file
                    os.unlink(export_path)
                else:
                    print(f"❌ {export_format.upper()}: Export file not created")
                    
            except Exception as e:
                print(f"❌ {export_format.upper()}: Export failed - {str(e)}")
        
        # Test bulk export package
        print(f"\n📦 Bulk Export Package Test:")
        
        try:
            package_formats = ['pdf', 'json', 'csv', 'html']
            package_path = exporter.create_export_package(
                sample_data,
                package_formats,
                include_media=False
            )
            
            if os.path.exists(package_path):
                package_size = os.path.getsize(package_path)
                print(f"✅ Package created: {Path(package_path).name} ({package_size:,} bytes)")
                
                # Verify ZIP contents
                import zipfile
                with zipfile.ZipFile(package_path, 'r') as zip_file:
                    files = zip_file.namelist()
                    print(f"   Package contains {len(files)} files:")
                    for file_name in files:
                        print(f"     📄 {file_name}")
                
                # Cleanup package
                os.unlink(package_path)
            else:
                print(f"❌ Package creation failed")
                
        except Exception as e:
            print(f"❌ Package creation failed: {str(e)}")
        
        # Test sharing manager
        print(f"\n🔗 Sharing Manager Test:")
        
        try:
            sharing_manager = SharingManager()
            
            # Create a test file for sharing
            test_file = os.path.join(temp_dir, "test_share.txt")
            with open(test_file, 'w') as f:
                f.write("Test content for sharing")
            
            share_config = ShareConfig(
                platform='link',
                permissions='read',
                expiry_hours=24,
                password_protected=False
            )
            
            share_info = sharing_manager.create_shareable_link(test_file, share_config)
            
            print(f"✅ Share link created:")
            print(f"   Share ID: {share_info['share_id']}")
            print(f"   Link: {share_info['shareable_link']}")
            print(f"   Permissions: {share_info['permissions']}")
            print(f"   Expires: {share_info.get('expires_at', 'Never')}")
            
            # Test email content generation
            email_content = sharing_manager.generate_email_content(
                share_info, 
                "Here's the transcript from our meeting today."
            )
            
            print(f"✅ Email content generated:")
            print(f"   Subject: {email_content['subject']}")
            print(f"   Body length: {len(email_content['body'])} characters")
            
        except Exception as e:
            print(f"❌ Sharing test failed: {str(e)}")
        
        print(f"\n✅ Export manager tests completed!")
        
    except Exception as e:
        print(f"\n❌ Export manager test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"🧹 Cleaned up temp directory")


if __name__ == "__main__":
    print("🧪 Export Manager Test Suite")
    print("=" * 50)
    
    test_export_manager()
    
    print("\n🎉 Export manager testing completed!")