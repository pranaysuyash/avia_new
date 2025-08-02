#!/usr/bin/env python3
"""
Test batch upload functionality
"""

import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def test_batch_upload():
    """Test batch upload with multiple files"""
    print("Testing batch upload functionality...")
    
    # Test files from our audio directory
    test_files = [
        "/Users/pranay/Projects/LLM/video/ner/test_data/audio/business_meeting.wav",
        "/Users/pranay/Projects/LLM/video/ner/test_data/audio/customer_service.wav",
        "/Users/pranay/Projects/LLM/video/ner/test_data/audio/educational_lecture.wav"
    ]
    
    # Prepare files for upload
    files = []
    for file_path in test_files:
        try:
            with open(file_path, 'rb') as f:
                files.append(('files', (file_path.split('/')[-1], f.read(), 'audio/wav')))
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            continue
    
    if not files:
        print("No valid files found for testing")
        return
    
    # Prepare form data
    data = {
        'language': 'auto',
        'enable_diarization': True,
        'extract_entities': True
    }
    
    try:
        # Upload batch
        print(f"Uploading batch of {len(files)} files...")
        response = requests.post(f"{API_BASE}/transcription/batch", files=files, data=data)
        
        print(f"Batch upload response: {response.status_code}")
        result = response.json()
        
        if result['success']:
            batch_data = result['data']
            print(f"✅ Batch processed successfully!")
            print(f"   Batch ID: {batch_data['batch_id']}")
            print(f"   Total files: {batch_data['total_files']}")
            print(f"   Completed: {batch_data['completed']}")
            print(f"   Failed: {batch_data['failed']}")
            
            print("\nFile results:")
            for file_result in batch_data['results']:
                status = "✅" if file_result['status'] == 'completed' else "❌"
                print(f"   {status} {file_result['file_name']}: {file_result['status']}")
                if file_result['status'] == 'completed':
                    print(f"      Transcript ID: {file_result['transcript_id']}")
                    print(f"      Processing time: {file_result['processing_time']:.1f}s")
        else:
            print(f"❌ Batch upload failed: {result}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_search():
    """Test search functionality"""
    print("\nTesting search functionality...")
    
    try:
        # Test search with different queries
        queries = ["meeting", "strategy", "customer", "AI"]
        
        for query in queries:
            response = requests.get(f"{API_BASE}/search", params={'q': query, 'sortBy': 'relevance'})
            
            if response.status_code == 200:
                result = response.json()
                count = result['data']['total_count']
                print(f"   Search '{query}': {count} results found")
            else:
                print(f"   Search '{query}': Failed with status {response.status_code}")
                
    except Exception as e:
        print(f"❌ Search test failed: {e}")

def test_advanced_analytics():
    """Test advanced analytics"""
    print("\nTesting advanced analytics...")
    
    try:
        response = requests.get(f"{API_BASE}/analytics/advanced")
        
        if response.status_code == 200:
            result = response.json()
            analytics = result['data']
            
            print("✅ Advanced analytics retrieved:")
            print(f"   Weekly growth: {analytics['usage']['weekly_growth']}%")
            print(f"   Average processing time: {analytics['performance']['avg_processing_time']}s")
            print(f"   Success rate: {analytics['performance']['success_rate']}%")
            print(f"   Total words processed: {analytics['content']['total_words']:,}")
        else:
            print(f"❌ Analytics failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")

if __name__ == "__main__":
    test_batch_upload()
    test_search()
    test_advanced_analytics()
    print("\n🎉 All extra features integration tests completed!")