# Sample Test Data

This directory contains sample audio files and transcripts for testing the transcription system.

## Sample Files Available

### Audio Files
Located in `audio/` directory:

1. **business_meeting.wav** (2:30)
   - Multiple speakers discussing quarterly results
   - Good for testing speaker diarization
   - Contains business terminology and numbers

2. **technical_interview.wav** (1:45) 
   - Job interview scenario with technical questions
   - Clear single speaker initially
   - Tests technical vocabulary recognition

3. **educational_lecture.wav** (3:15)
   - University lecture on computer science
   - Academic terminology and concepts
   - Longer content for testing processing

4. **customer_service.wav** (2:00)
   - Customer support call scenario
   - Problem-solution conversation flow
   - Tests service industry vocabulary

5. **medical_consultation.wav** (3:00)
   - Doctor-patient consultation
   - Medical terminology and procedures
   - Tests healthcare domain vocabulary

### Transcript Data
Pre-generated transcripts with segments, timing, and entities available in `sample_transcripts.json`.

Each sample includes:
- Full transcript text
- Segmented transcript with timing
- Speaker identification
- Confidence scores
- Named entity extraction
- Domain-specific vocabulary

## Using Sample Files

### In the Main App
1. Look for "🎬 Try Sample Files" section
2. Click "📁 Use" next to any sample
3. The file will be automatically loaded
4. Click "Process Audio" to see results

### For Testing
Use these files to test:
- Transcription accuracy
- Speaker diarization
- Entity extraction
- Export functionality
- Search features
- Edit capabilities

## File Formats Supported

The system supports various input formats:
- **Audio**: MP3, WAV, M4A, AAC, OGG
- **Video**: MP4, AVI, MOV, WMV, MKV

## Expected Processing Times

- Small files (< 2 minutes): 30-60 seconds
- Medium files (2-5 minutes): 1-3 minutes  
- Large files (5-10 minutes): 3-8 minutes

Processing time depends on:
- File length and quality
- Processing mode (Basic vs Advanced)
- System resources available
- Network connectivity (for AI features)

## Quality Tips

For best transcription results:
- Use clear audio with minimal background noise
- Ensure good volume levels (not too quiet/loud)
- Single speaker per segment when possible
- Avoid overlapping conversations
- Use high-quality audio formats when available

## Troubleshooting

If sample files don't load:
1. Check file permissions
2. Verify audio codecs are available
3. Try a different sample file
4. Check browser console for errors
5. Refresh the page and try again

## Adding Custom Samples

To add your own sample files:
1. Place audio/video files in `audio/` directory
2. Update `sample_transcripts.json` with metadata
3. Add entry to sample list in `user_onboarding.py`
4. Test with the onboarding system

## Privacy Note

These sample files are for demonstration purposes only and contain no real personal information. They may be processed through AI services for transcription and analysis.