#!/usr/bin/env python3
"""
Basic Usage Example
Demonstrates basic usage of the Transcription Platform SDK
"""

import os
import time
from transcription_platform import TranscriptionClient, TranscriptionError

def main():
    # Initialize client
    # Make sure to set TRANSCRIPTION_API_KEY environment variable
    # or pass api_key parameter
    client = TranscriptionClient()
    
    try:
        # Example 1: Create a transcript from URL
        print("Creating transcript from URL...")
        transcript = client.create_transcript(
            audio_url="https://example.com/sample-audio.mp3",
            language="en",
            enable_diarization=True,
            max_speakers=2,
            metadata={
                "project": "demo",
                "type": "interview"
            }
        )
        
        print(f"Transcript created with ID: {transcript.id}")
        print(f"Status: {transcript.status}")
        
        # Example 2: Poll for completion
        print("\nWaiting for transcript to complete...")
        while transcript.status in ['pending', 'processing']:
            time.sleep(5)
            transcript = client.get_transcript(transcript.id)
            print(f"Status: {transcript.status}")
        
        if transcript.is_complete:
            print(f"\nTranscript completed!")
            print(f"Duration: {transcript.duration:.1f} seconds")
            print(f"Word count: {transcript.word_count}")
            
            # Print first 500 characters
            print(f"\nTranscript preview:")
            print(transcript.text[:500] + "...")
            
            # Show speaker segments
            if transcript.segments:
                print(f"\nFirst 5 segments:")
                for segment in transcript.segments[:5]:
                    print(f"[{segment.speaker}] {segment.text}")
        
        elif transcript.is_failed:
            print(f"\nTranscript failed: {transcript.error}")
        
        # Example 3: List recent transcripts
        print("\n\nListing recent transcripts...")
        result = client.list_transcripts(per_page=5)
        
        print(f"Found {result['pagination']['total']} total transcripts")
        for t in result['data']:
            print(f"- {t.id}: {t.title or 'Untitled'} ({t.status})")
        
        # Example 4: Export transcript
        if transcript.is_complete:
            print("\n\nExporting transcript...")
            
            # Export as text
            text_export = client.export_transcript(transcript.id, format="txt")
            print(f"Text export length: {len(text_export)} characters")
            
            # Export as SRT
            srt_export = client.export_transcript(
                transcript.id, 
                format="srt",
                include_speakers=False
            )
            print(f"SRT export preview:")
            print(srt_export[:200] + "...")
        
        # Example 5: Get usage statistics
        print("\n\nChecking usage...")
        usage = client.get_usage()
        
        transcripts_usage = usage.get_usage('transcripts')
        print(f"Transcripts used: {transcripts_usage.get('current', 0)}")
        print(f"Transcripts remaining: {usage.get_remaining('transcripts')}")
        
        # Example 6: Webhook management
        print("\n\nCreating webhook...")
        webhook = client.create_webhook(
            name="Demo Webhook",
            url="https://example.com/webhook",
            events=["transcript.completed", "transcript.failed"]
        )
        
        print(f"Webhook created with ID: {webhook.id}")
        print(f"Secret: {webhook.secret}")
        print("Save this secret - it won't be shown again!")
        
        # List webhooks
        webhooks = client.list_webhooks()
        print(f"\nActive webhooks: {len(webhooks)}")
        
        # Clean up - delete the webhook
        client.delete_webhook(webhook.id)
        print("Webhook deleted")
        
    except TranscriptionError as e:
        print(f"\nError: {e}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled")

if __name__ == "__main__":
    main()