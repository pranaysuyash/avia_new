# Transcription API JavaScript/TypeScript SDK

A comprehensive JavaScript/TypeScript SDK for the Audio/Video Transcription Platform API. This SDK provides easy-to-use interfaces for transcription, analysis, team management, and more.

## Installation

```bash
npm install @transcription-api/sdk
```

Or with yarn:
```bash
yarn add @transcription-api/sdk
```

## Quick Start

### JavaScript (ES6+)

```javascript
import { TranscriptionClient } from '@transcription-api/sdk';

// Initialize the client
const client = new TranscriptionClient({
  apiKey: 'your_api_key_here'
});

// Upload and transcribe a file
const fileInput = document.getElementById('audio-file');
const file = fileInput.files[0];

const transcript = await client.transcribeFile(file, {
  title: 'My Recording'
});

// Wait for completion
const completed = await client.waitForCompletion(transcript.id);
console.log(completed.text);
```

### TypeScript

```typescript
import { 
  TranscriptionClient, 
  Transcript, 
  TranscriptionOptions 
} from '@transcription-api/sdk';

const client = new TranscriptionClient({
  apiKey: 'your_api_key_here'
});

const options: TranscriptionOptions = {
  language: 'en',
  method: 'advanced',
  speakerDetection: true,
  sentimentAnalysis: true
};

const transcript: Transcript = await client.transcribeFile(file, {
  title: 'Team Meeting',
  transcriptionOptions: options
});
```

### Node.js

```javascript
const { TranscriptionClient } = require('@transcription-api/sdk');
const fs = require('fs');

const client = new TranscriptionClient({
  apiKey: process.env.TRANSCRIPTION_API_KEY
});

// Read file from filesystem
const fileBuffer = fs.readFileSync('audio.mp3');
const file = new Blob([fileBuffer], { type: 'audio/mpeg' });

const transcript = await client.transcribeFile(file, {
  title: 'Audio Recording'
});
```

## Authentication

You can provide your API key in several ways:

1. **Direct initialization:**
```javascript
const client = new TranscriptionClient({
  apiKey: 'your_api_key'
});
```

2. **Environment variable:**
```bash
export TRANSCRIPTION_API_KEY="your_api_key"
```
```javascript
const client = new TranscriptionClient({}); // Will use env var
```

## Features

### File Transcription

```javascript
import { TranscriptionClient } from '@transcription-api/sdk';

const client = new TranscriptionClient({ apiKey: 'your_api_key' });

// Basic transcription
const transcript = await client.transcribeFile(file);

// Advanced transcription with options
const transcript = await client.transcribeFile(file, {
  title: 'Team Meeting',
  transcriptionOptions: {
    language: 'en',
    method: 'advanced',
    speakerDetection: true,
    sentimentAnalysis: true,
    entityExtraction: true
  }
});

// Wait for completion with custom timeout
const completed = await client.waitForCompletion(transcript.id, {
  timeout: 600000, // 10 minutes
  pollInterval: 3000 // Check every 3 seconds
});
```

### Team Management

```javascript
// Create a team
const team = await client.createTeam('My Team', 'Team for project X');

// List teams
const teams = await client.listTeams();

// Get team details
const teamDetails = await client.getTeam(team.id);

// Invite a member
await client.inviteTeamMember(team.id, 'colleague@example.com', 'member');

// Transcribe to team workspace
const transcript = await client.transcribeFile(file, {
  transcriptionOptions: { teamId: team.id }
});
```

### Search and Discovery

```javascript
// List transcripts with pagination
const transcripts = await client.listTranscripts({
  skip: 0,
  limit: 50
});

// Filter by team
const teamTranscripts = await client.listTranscripts({
  teamId: team.id,
  limit: 20
});

// Search transcripts
const searchResults = await client.searchTranscripts('meeting notes', {
  limit: 10
});

// Get specific transcript
const transcript = await client.getTranscript('transcript_id');
```

### User Management

```javascript
// Get user profile
const profile = await client.getProfile();
console.log(`User: ${profile.name} (${profile.email})`);

// Update profile
const updatedProfile = await client.updateProfile('New Name');
```

### API Key Management

```javascript
// Create API key
const apiKey = await client.createApiKey('My App Key', 90); // expires in 90 days
console.log(`New API key: ${apiKey.key}`); // Only shown once!

// List API keys
const keys = await client.listApiKeys();

// Delete API key
await client.deleteApiKey(keyId);
```

## Advanced Features

### File Upload with Progress

```javascript
// Using presigned URLs for large files
const { uploadUrl, objectKey } = await client.getPresignedUploadUrl(
  file.name,
  file.type
);

// Upload directly to storage with progress tracking
const xhr = new XMLHttpRequest();
xhr.upload.addEventListener('progress', (event) => {
  if (event.lengthComputable) {
    const percentComplete = (event.loaded / event.total) * 100;
    console.log(`Upload progress: ${percentComplete}%`);
  }
});

xhr.open('PUT', uploadUrl);
xhr.send(file);
```

### Real-time Transcription

```javascript
// WebSocket connection for real-time transcription
const ws = new WebSocket('wss://api.transcriptionplatform.com/ws/realtime');

ws.onopen = () => {
  // Send authentication
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_jwt_token'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'transcription') {
    console.log('Real-time text:', data.text);
    console.log('Is final:', data.isFinal);
  }
};

// Send audio chunks
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        ws.send(event.data);
      }
    };
    mediaRecorder.start(1000); // Send chunks every second
  });
```

### GraphQL Support

```javascript
// Use GraphQL for flexible queries
const query = `
  query GetTranscripts($first: Int, $filter: TranscriptFilter) {
    transcripts(first: $first, filter: $filter) {
      edges {
        id
        title
        status
        duration
        entities
      }
      pageInfo {
        hasNextPage
        totalCount
      }
    }
  }
`;

const variables = {
  first: 10,
  filter: {
    language: 'en',
    dateFrom: '2024-01-01T00:00:00Z'
  }
};

const response = await client.graphql({ query, variables });
console.log(response.data.transcripts);
```

## Error Handling

The SDK provides specific exception types for different error conditions:

```javascript
import {
  TranscriptionClient,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  NotFoundError,
  ServerError,
  TimeoutError
} from '@transcription-api/sdk';

const client = new TranscriptionClient({ apiKey: 'your_api_key' });

try {
  const transcript = await client.getTranscript('invalid_id');
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof NotFoundError) {
    console.error('Transcript not found');
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited. Retry after ${error.retryAfter} seconds`);
  } else if (error instanceof ValidationError) {
    console.error('Validation error:', error.errors);
  } else if (error instanceof TimeoutError) {
    console.error('Request timed out');
  } else if (error instanceof ServerError) {
    console.error('Server error occurred');
  } else {
    console.error('Unknown error:', error.message);
  }
}
```

## Configuration

### Custom Base URL

```javascript
const client = new TranscriptionClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://your-custom-domain.com/api/v1'
});
```

### Timeout and Retries

```javascript
const client = new TranscriptionClient({
  apiKey: 'your_api_key',
  timeout: 60000, // 60 seconds timeout
  maxRetries: 5   // Retry failed requests up to 5 times
});
```

## TypeScript Support

The SDK is written in TypeScript and provides comprehensive type definitions:

```typescript
import { 
  TranscriptionClient, 
  Transcript, 
  TranscriptStatus,
  Team,
  User,
  TranscriptionOptions,
  ListResponse
} from '@transcription-api/sdk';

// All types are fully typed
const client = new TranscriptionClient({ apiKey: 'key' });

const transcript: Transcript = await client.getTranscript('id');
const status: TranscriptStatus = transcript.status; // 'processing' | 'completed' | 'failed' | 'queued'

const teams: Team[] = await client.listTeams();
const transcripts: ListResponse<Transcript> = await client.listTranscripts();
```

## Browser Support

The SDK works in all modern browsers and supports:

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

For older browsers, you may need polyfills for:
- `fetch` API
- `Promise`
- `FormData`

## Node.js Support

Requires Node.js 14+ with support for:
- ES2020 features
- `fetch` API (Node.js 18+) or polyfill

## React Integration

```jsx
import React, { useState } from 'react';
import { TranscriptionClient } from '@transcription-api/sdk';

const client = new TranscriptionClient({ apiKey: 'your_api_key' });

function TranscriptionUpload() {
  const [transcript, setTranscript] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    try {
      const newTranscript = await client.transcribeFile(file, {
        title: file.name
      });
      
      const completed = await client.waitForCompletion(newTranscript.id);
      setTranscript(completed);
    } catch (error) {
      console.error('Transcription failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input type="file" onChange={handleFileUpload} accept="audio/*,video/*" />
      {loading && <p>Processing...</p>}
      {transcript && (
        <div>
          <h3>{transcript.title}</h3>
          <p>{transcript.text}</p>
        </div>
      )}
    </div>
  );
}
```

## Vue.js Integration

```vue
<template>
  <div>
    <input type="file" @change="handleFileUpload" accept="audio/*,video/*" />
    <div v-if="loading">Processing...</div>
    <div v-if="transcript">
      <h3>{{ transcript.title }}</h3>
      <p>{{ transcript.text }}</p>
    </div>
  </div>
</template>

<script>
import { TranscriptionClient } from '@transcription-api/sdk';

const client = new TranscriptionClient({ apiKey: 'your_api_key' });

export default {
  data() {
    return {
      transcript: null,
      loading: false
    };
  },
  methods: {
    async handleFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      this.loading = true;
      try {
        const newTranscript = await client.transcribeFile(file, {
          title: file.name
        });
        
        const completed = await client.waitForCompletion(newTranscript.id);
        this.transcript = completed;
      } catch (error) {
        console.error('Transcription failed:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/transcription-api/javascript-sdk.git
cd javascript-sdk

# Install dependencies
npm install

# Build the SDK
npm run build

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

### Code Quality

```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Type check
npm run type-check
```

## Support

- **Documentation:** https://docs.transcriptionapi.com/sdk/javascript
- **API Reference:** https://docs.transcriptionapi.com/api
- **Issues:** https://github.com/transcription-api/javascript-sdk/issues
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
- GraphQL support
- Real-time transcription
- Comprehensive error handling
- Full TypeScript support
- Browser and Node.js compatibility