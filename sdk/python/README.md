# Transcription Platform Python SDK

Official Python SDK for the Transcription Platform API.

## Installation

```bash
pip install transcription-platform
```

## Quick Start

```python
from transcription_platform import TranscriptionClient

# Initialize the client
client = TranscriptionClient(api_key="YOUR_API_KEY")

# Create a transcript from URL
transcript = client.create_transcript(
    audio_url="https://example.com/audio.mp3",
    language="en",
    enable_diarization=True
)

# Wait for completion and get results
import time
while not transcript.is_complete:
    time.sleep(5)
    transcript = client.get_transcript(transcript.id)
    
print(f"Transcript completed! Word count: {transcript.word_count}")
print(transcript.text)
```

## Authentication

You can provide your API key in several ways:

1. Pass it directly to the client:
```python
client = TranscriptionClient(api_key="YOUR_API_KEY")
```

2. Set it as an environment variable:
```bash
export TRANSCRIPTION_API_KEY="YOUR_API_KEY"
```

## Creating Transcripts

### From URL

```python
transcript = client.create_transcript(
    audio_url="https://example.com/audio.mp3",
    language="en",
    enable_diarization=True,
    max_speakers=3,
    webhook_url="https://your-app.com/webhook",
    metadata={"project": "interview", "episode": 42}
)
```

### From File Upload

```python
with open("audio.mp3", "rb") as f:
    transcript = client.create_transcript(
        audio_file=f,
        language="en",
        enable_diarization=True
    )
```

## Managing Transcripts

### List Transcripts

```python
# Get paginated list of transcripts
result = client.list_transcripts(
    page=1,
    per_page=20,
    status="completed",
    language="en"
)

for transcript in result['data']:
    print(f"{transcript.id}: {transcript.title}")
```

### Get Transcript Details

```python
transcript = client.get_transcript("tr_abc123")
print(f"Status: {transcript.status}")
print(f"Duration: {transcript.duration} seconds")

# Access speaker segments
for segment in transcript.segments:
    print(f"[{segment.speaker}] {segment.text}")
```

### Export Transcripts

```python
# Export as plain text
text = client.export_transcript(transcript.id, format="txt")

# Export as SRT subtitles
srt = client.export_transcript(
    transcript.id, 
    format="srt",
    include_speakers=False
)

# Export as JSON
data = client.export_transcript(transcript.id, format="json")
```

### Delete Transcript

```python
client.delete_transcript(transcript.id)
```

## Teams

```python
# List teams
teams = client.list_teams()

# Create a team
team = client.create_team(
    name="Research Team",
    description="Audio research and analysis"
)

# Get team details
team = client.get_team(team.id)
for member in team.members:
    print(f"{member.username} - {member.role}")
```

## Analytics

```python
# Get usage statistics
usage = client.get_usage(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

print(f"Transcripts created: {usage.get_usage('transcripts')['current']}")
print(f"Minutes processed: {usage.get_usage('minutes')['current']}")
print(f"Remaining transcript quota: {usage.get_remaining('transcripts')}")
```

## Webhooks

### Create Webhook

```python
webhook = client.create_webhook(
    name="Transcript Complete",
    url="https://your-app.com/webhook",
    events=["transcript.completed", "transcript.failed"]
)

print(f"Webhook created with secret: {webhook.secret}")
```

### Verify Webhook Signature

```python
# In your webhook handler
import json

def handle_webhook(request):
    payload = request.body
    signature = request.headers.get('X-Webhook-Signature')
    
    # Verify signature
    if not client.verify_webhook_signature(payload, signature, webhook_secret):
        return 401  # Unauthorized
    
    # Parse event
    event = json.loads(payload)
    
    if event['type'] == 'transcript.completed':
        transcript_id = event['data']['transcript_id']
        # Handle completed transcript
```

## Error Handling

```python
from transcription_platform import (
    TranscriptionError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError
)

try:
    transcript = client.get_transcript("invalid_id")
except NotFoundError:
    print("Transcript not found")
except RateLimitError as e:
    print(f"Rate limit hit. Retry after {e.retry_after} seconds")
except AuthenticationError:
    print("Invalid API key")
except TranscriptionError as e:
    print(f"API error: {e}")
```

## Advanced Usage

### Custom Timeout

```python
# Set custom timeout for long audio files
client = TranscriptionClient(
    api_key="YOUR_API_KEY",
    timeout=120  # 2 minutes
)
```

### Using a Different Base URL

```python
# For self-hosted or staging environments
client = TranscriptionClient(
    api_key="YOUR_API_KEY",
    base_url="https://api-staging.example.com/v1"
)
```

### Retry Configuration

```python
# Configure retry behavior
client = TranscriptionClient(
    api_key="YOUR_API_KEY",
    max_retries=5  # Retry failed requests up to 5 times
)
```

## Async Support

For async applications, use the async client (coming soon):

```python
from transcription_platform import AsyncTranscriptionClient

async def main():
    async with AsyncTranscriptionClient(api_key="YOUR_API_KEY") as client:
        transcript = await client.create_transcript(
            audio_url="https://example.com/audio.mp3"
        )
```

## Contributing

See [CONTRIBUTING.md](https://github.com/transcription-platform/python-sdk/blob/main/CONTRIBUTING.md) for information on how to contribute to this SDK.

## License

This SDK is distributed under the MIT license. See [LICENSE](https://github.com/transcription-platform/python-sdk/blob/main/LICENSE) for more information.