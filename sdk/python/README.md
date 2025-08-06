# Transcription API Python SDK

A comprehensive Python SDK for the Audio/Video Transcription Platform API. This SDK provides easy-to-use interfaces for transcription, analysis, team management, and more.

## Installation

```bash
pip install transcription-api
```

For async support:
```bash
pip install transcription-api[async]
```

## Quick Start

```python
from transcription_api import TranscriptionClient

# Initialize the client
client = TranscriptionClient(api_key="your_api_key_here")

# Upload and transcribe a file
with open("audio.mp3", "rb") as f:
    transcript = client.transcribe_file(f, title="My Recording")

# Wait for completion
transcript = client.wait_for_completion(transcript.id)

# Get the transcribed text
print(transcript.text)

# Get extracted entities
print(transcript.entities)
```

## Authentication

You can provide your API key in several ways:

1. **Direct initialization:**
```python
client = TranscriptionClient(api_key="your_api_key")
```

2. **Environment variable:**
```bash
export TRANSCRIPTION_API_KEY="your_api_key"
```
```python
client = TranscriptionClient()  # Will use env var
```

## Features

### File Transcription

```python
from transcription_api import TranscriptionClient, TranscriptionOptions

client = TranscriptionClient(api_key="your_api_key")

# Basic transcription
with open("audio.mp3", "rb") as f:
    transcript = client.transcribe_file(f)

# Advanced transcription with options
options = TranscriptionOptions(
    language="en",
    method="advanced",
    speaker_detection=True,
    sentiment_analysis=True
)

with open("meeting.mp4", "rb") as f:
    transcript = client.transcribe_file(f, title="Team Meeting", options=options)

# Wait for completion
completed_transcript = client.wait_for_completion(transcript.id)
```

### Team Management

```python
# Create a team
team = client.create_team("My Team", description="Team for project X")

# List teams
teams = client.list_teams()

# Invite a member
client.invite_team_member(team.id, "colleague@example.com", role="member")

# Transcribe to team workspace
options = TranscriptionOptions(team_id=team.id)
transcript = client.transcribe_file(file, options=options)
```

### Search and Discovery

```python
# List transcripts
transcripts = client.list_transcripts(limit=50)

# Filter by team
team_transcripts = client.list_transcripts(team_id=team.id)

# Get specific transcript
transcript = client.get_transcript("transcript_id")
```

### User Management

```python
# Get user profile
profile = client.get_profile()
print(f"User: {profile.name} ({profile.email})")

# Update profile
updated_profile = client.update_profile(name="New Name")
```

### API Key Management

```python
# Create API key
api_key = client.create_api_key("My App Key", expires_in_days=90)
print(f"New API key: {api_key['key']}")  # Only shown once!

# List API keys
keys = client.list_api_keys()

# Delete API key
client.delete_api_key(key_id)
```

## Async Support

For async operations, use the `AsyncTranscriptionClient`:

```python
import asyncio
from transcription_api import AsyncTranscriptionClient

async def main():
    client = AsyncTranscriptionClient(api_key="your_api_key")
    
    # Async transcription
    with open("audio.mp3", "rb") as f:
        transcript = await client.transcribe_file(f)
    
    # Async wait for completion
    completed = await client.wait_for_completion(transcript.id)
    print(completed.text)

asyncio.run(main())
```

## Error Handling

The SDK provides specific exception types for different error conditions:

```python
from transcription_api import (
    TranscriptionClient, 
    AuthenticationError, 
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError
)

client = TranscriptionClient(api_key="your_api_key")

try:
    transcript = client.get_transcript("invalid_id")
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Transcript not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ValidationError as e:
    print(f"Validation error: {e.message}")
except ServerError:
    print("Server error occurred")
```

## Configuration

### Custom Base URL

```python
client = TranscriptionClient(
    api_key="your_api_key",
    base_url="https://your-custom-domain.com/api/v1"
)
```

### Timeout and Retries

```python
client = TranscriptionClient(
    api_key="your_api_key",
    timeout=60,  # 60 seconds timeout
    max_retries=5  # Retry failed requests up to 5 times
)
```

## Models

The SDK includes comprehensive data models:

### Transcript

```python
transcript = client.get_transcript("transcript_id")

print(f"Title: {transcript.title}")
print(f"Status: {transcript.status}")
print(f"Duration: {transcript.duration} seconds")
print(f"Confidence: {transcript.confidence}")
print(f"Language: {transcript.language}")
print(f"Text: {transcript.text}")
print(f"Entities: {transcript.entities}")

# Check status
if transcript.is_completed:
    print("Transcription is ready!")
elif transcript.is_processing:
    print("Still processing...")
elif transcript.has_failed:
    print("Transcription failed")
```

### Team

```python
team = client.get_team(team_id)

print(f"Team: {team.name}")
print(f"Description: {team.description}")
print(f"Members: {team.member_count}")
print(f"Owner ID: {team.owner_id}")

for member in team.members:
    print(f"- {member.user_name} ({member.role})")
```

## Advanced Usage

### Webhook Handling

```python
from transcription_api import WebhookEvent

# In your webhook endpoint
def handle_webhook(request_body: str):
    event = WebhookEvent.from_dict(json.loads(request_body))
    
    if event.event_type == "transcription.completed":
        transcript_id = event.data["transcript_id"]
        print(f"Transcription {transcript_id} completed!")
```

### Batch Processing

```python
import os
from pathlib import Path

# Process multiple files
audio_files = Path("audio_files").glob("*.mp3")
transcripts = []

for audio_file in audio_files:
    with open(audio_file, "rb") as f:
        transcript = client.transcribe_file(f, title=audio_file.stem)
        transcripts.append(transcript)

# Wait for all to complete
completed_transcripts = []
for transcript in transcripts:
    completed = client.wait_for_completion(transcript.id)
    completed_transcripts.append(completed)
    print(f"Completed: {completed.title}")
```

### Usage Monitoring

```python
# Check usage stats
stats = client.get_usage_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"This month: {stats['current_month_requests']}")

# Health check
health = client.health_check()
print(f"API Status: {health['status']}")
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run tests with coverage
pytest --cov=transcription_api
```

### Code Formatting

```bash
# Format code
black transcription_api/

# Check formatting
flake8 transcription_api/

# Type checking
mypy transcription_api/
```

## Support

- **Documentation:** https://docs.transcriptionapi.com/sdk/python
- **API Reference:** https://docs.transcriptionapi.com/api
- **Issues:** https://github.com/transcription-api/python-sdk/issues
- **Email:** support@transcriptionapi.com

## License

This SDK is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Changelog

### v1.0.0
- Initial release
- Support for file transcription
- Team management
- User profile management
- API key management
- Async client support
- Comprehensive error handling
- Full type hints