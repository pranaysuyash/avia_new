#!/usr/bin/env python3
"""Test script for video processing workflow"""

import requests
import json
import os

BASE_URL = "http://localhost:8000/api/v1"

print("1. Creating test video file...")
# Create a test video file (using the audio file as a placeholder)
test_file = "test_audio.wav"  # Using audio file as placeholder for testing

print("\n2. Uploading video file...")
with open(test_file, "rb") as f:
    files = {"file": (test_file, f, "video/mp4")}  # Pretend it's a video
    upload_response = requests.post(
        f"{BASE_URL}/video/upload",
        files=files
    )

if upload_response.status_code == 200:
    upload_data = upload_response.json()["data"]
    file_id = upload_data["file_id"]
    print(f"Video uploaded successfully. File ID: {file_id}")
else:
    print(f"Upload failed: {upload_response.text}")
    exit(1)

print("\n3. Analyzing video...")
analyze_response = requests.post(
    f"{BASE_URL}/video/analyze/{file_id}",
    json={
        "extract_frames": True,
        "detect_scenes": True,
        "generate_thumbnails": True,
        "keyframe_interval": 10.0,
        "thumbnail_count": 5
    }
)

if analyze_response.status_code == 200:
    analysis_data = analyze_response.json()["data"]
    print("Video analysis completed!")
    print(f"Duration: {analysis_data['duration']} seconds")
    print(f"FPS: {analysis_data['fps']}")
    print(f"Resolution: {analysis_data['resolution']['width']}x{analysis_data['resolution']['height']}")
    print(f"Scenes detected: {len(analysis_data['scenes'])}")
    print(f"Keyframes extracted: {len(analysis_data['keyframes'])}")
    print(f"Thumbnails generated: {len(analysis_data['thumbnails'])}")
else:
    print(f"Analysis failed: {analyze_response.text}")
    exit(1)

print("\n4. Getting video scenes...")
scenes_response = requests.get(f"{BASE_URL}/video/scenes/{file_id}?min_duration=1.0")

if scenes_response.status_code == 200:
    scenes_data = scenes_response.json()["data"]
    print(f"Retrieved {scenes_data['filtered_scenes']} scenes (from {scenes_data['total_scenes']} total)")
    for i, scene in enumerate(scenes_data['scenes'][:3]):
        print(f"  Scene {i+1}: {scene['start_time']:.1f}s - {scene['end_time']:.1f}s ({scene['duration']:.1f}s)")
else:
    print(f"Failed to get scenes: {scenes_response.text}")

print("\n5. Getting video metadata...")
metadata_response = requests.get(f"{BASE_URL}/video/metadata/{file_id}")

if metadata_response.status_code == 200:
    metadata = metadata_response.json()["data"]
    print(f"Video codec: {metadata['technical_details']['codec']}")
    print(f"Bitrate: {metadata['technical_details']['bitrate']} bps")
    print(f"File size: {metadata['basic_info']['file_size']} bytes")
else:
    print(f"Failed to get metadata: {metadata_response.text}")

print("\n✅ Video processing tests completed!")