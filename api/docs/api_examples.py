"""
API usage examples and code snippets for documentation
Provides practical examples in multiple programming languages
"""

from typing import Dict, List

# Python examples
PYTHON_EXAMPLES = {
    "authentication": """
import requests
import json

# API base URL
BASE_URL = "https://api.transcription.com"

# Register new user
def register_user(username, email, password):
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    return response.json()

# Login and get tokens
def login(username, password):
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "username": username,
            "password": password
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        return access_token, refresh_token
    else:
        raise Exception(f"Login failed: {response.text}")

# Use authenticated request
def get_transcripts(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/transcripts",
        headers=headers
    )
    
    return response.json()
""",
    
    "file_upload": """
import requests
import time

def upload_and_transcribe(file_path, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Upload file
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{BASE_URL}/api/transcription/upload",
            headers=headers,
            files=files
        )
    
    if response.status_code != 202:
        raise Exception(f"Upload failed: {response.text}")
    
    transcript_id = response.json()["transcript_id"]
    
    # Configure processing options
    process_response = requests.post(
        f"{BASE_URL}/api/transcription/process",
        headers=headers,
        json={
            "transcript_id": transcript_id,
            "language": "auto",
            "model": "large-v3",
            "enable_diarization": True,
            "enable_ner": True
        }
    )
    
    # Poll for status
    while True:
        status_response = requests.get(
            f"{BASE_URL}/api/transcripts/{transcript_id}/status",
            headers=headers
        )
        
        status_data = status_response.json()
        
        if status_data["status"] == "completed":
            return transcript_id
        elif status_data["status"] == "failed":
            raise Exception(f"Transcription failed: {status_data.get('error')}")
        
        print(f"Progress: {status_data.get('progress', 0)}%")
        time.sleep(5)
""",
    
    "websocket_client": """
import asyncio
import websockets
import json

async def connect_websocket(access_token):
    uri = f"ws://localhost:8000/ws?token={access_token}"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Subscribe to transcription updates
        await websocket.send(json.dumps({
            "event": "subscribe",
            "data": {
                "channels": ["transcription.updates", "notifications"]
            }
        }))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
            
            if data["event"] == "transcription.complete":
                transcript_id = data["data"]["transcript_id"]
                print(f"Transcription {transcript_id} completed!")

# Run WebSocket client
asyncio.run(connect_websocket("your_access_token"))
""",
    
    "search_example": """
def search_transcripts(query, access_token, filters=None):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "q": query,
        "page": 1,
        "per_page": 20
    }
    
    if filters:
        params.update(filters)
    
    response = requests.get(
        f"{BASE_URL}/api/search",
        headers=headers,
        params=params
    )
    
    results = response.json()
    
    # Process results
    for item in results["items"]:
        print(f"Transcript: {item['title']}")
        print(f"Score: {item['relevance_score']}")
        print(f"Snippet: {item['snippet']}")
        print("-" * 50)
    
    return results

# Example search with filters
results = search_transcripts(
    query="machine learning",
    access_token=token,
    filters={
        "language": "en",
        "date_from": "2024-01-01",
        "confidence_min": 0.8
    }
)
"""
}

# JavaScript/TypeScript examples
JAVASCRIPT_EXAMPLES = {
    "authentication": """
// Using fetch API
const API_BASE = 'https://api.transcription.com';

// Register new user
async function registerUser(username, email, password) {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username,
      email,
      password
    })
  });
  
  if (!response.ok) {
    throw new Error(`Registration failed: ${response.statusText}`);
  }
  
  return response.json();
}

// Login and store tokens
async function login(username, password) {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username,
      password
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store tokens securely
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    // Set up automatic token refresh
    scheduleTokenRefresh(data.expires_in);
    
    return data;
  } else {
    throw new Error(data.error || 'Login failed');
  }
}

// Authenticated API call
async function getTranscripts() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`${API_BASE}/api/transcripts`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.status === 401) {
    // Token expired, try to refresh
    await refreshAccessToken();
    return getTranscripts(); // Retry
  }
  
  return response.json();
}
""",
    
    "file_upload": """
// File upload with progress tracking
async function uploadFile(file, onProgress) {
  const token = localStorage.getItem('access_token');
  const formData = new FormData();
  formData.append('file', file);
  
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    // Track upload progress
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        const percentComplete = (e.loaded / e.total) * 100;
        onProgress(percentComplete);
      }
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status === 202) {
        const response = JSON.parse(xhr.responseText);
        resolve(response);
      } else {
        reject(new Error(`Upload failed: ${xhr.statusText}`));
      }
    });
    
    xhr.addEventListener('error', () => {
      reject(new Error('Upload failed'));
    });
    
    xhr.open('POST', `${API_BASE}/api/transcription/upload`);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.send(formData);
  });
}

// Process transcription with options
async function processTranscription(transcriptId, options = {}) {
  const token = localStorage.getItem('access_token');
  
  const defaultOptions = {
    language: 'auto',
    model: 'large-v3',
    enable_diarization: true,
    enable_ner: true
  };
  
  const response = await fetch(`${API_BASE}/api/transcription/process`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      transcript_id: transcriptId,
      ...defaultOptions,
      ...options
    })
  });
  
  return response.json();
}
""",
    
    "websocket_client": """
// WebSocket connection with reconnection logic
class TranscriptionWebSocket {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.listeners = new Map();
  }
  
  connect() {
    const wsUrl = `wss://api.transcription.com/ws?token=${this.token}`;
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      
      // Subscribe to events
      this.send({
        event: 'subscribe',
        data: {
          channels: ['transcription.updates', 'notifications']
        }
      });
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.reconnect();
    };
  }
  
  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      
      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }
  
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
  
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }
  
  handleMessage(data) {
    const listeners = this.listeners.get(data.event) || [];
    listeners.forEach(callback => callback(data.data));
  }
}

// Usage
const ws = new TranscriptionWebSocket(accessToken);
ws.connect();

ws.on('transcription.progress', (data) => {
  console.log(`Progress: ${data.progress}%`);
});

ws.on('transcription.complete', (data) => {
  console.log('Transcription completed!', data);
});
"""
}

# cURL examples
CURL_EXAMPLES = {
    "authentication": """
# Register new user
curl -X POST https://api.transcription.com/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'

# Login
curl -X POST https://api.transcription.com/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }'

# Save the access token
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIs..."
""",
    
    "file_upload": """
# Upload audio file
curl -X POST https://api.transcription.com/api/transcription/upload \\
  -H "Authorization: Bearer $ACCESS_TOKEN" \\
  -F "file=@/path/to/audio.mp3"

# Process with options
curl -X POST https://api.transcription.com/api/transcription/process \\
  -H "Authorization: Bearer $ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "transcript_id": 456,
    "language": "en",
    "model": "large-v3",
    "enable_diarization": true,
    "enable_ner": true
  }'

# Check status
curl -X GET https://api.transcription.com/api/transcripts/456/status \\
  -H "Authorization: Bearer $ACCESS_TOKEN"
""",
    
    "search": """
# Basic search
curl -X GET "https://api.transcription.com/api/search?q=machine%20learning" \\
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Search with filters
curl -X GET "https://api.transcription.com/api/search" \\
  -G \\
  -H "Authorization: Bearer $ACCESS_TOKEN" \\
  --data-urlencode "q=artificial intelligence" \\
  --data-urlencode "language=en" \\
  --data-urlencode "date_from=2024-01-01" \\
  --data-urlencode "confidence_min=0.8"
""",
    
    "export": """
# Export as SRT
curl -X GET "https://api.transcription.com/api/transcripts/456/export?format=srt" \\
  -H "Authorization: Bearer $ACCESS_TOKEN" \\
  -o transcript.srt

# Export as PDF with options
curl -X GET "https://api.transcription.com/api/transcripts/456/export" \\
  -G \\
  -H "Authorization: Bearer $ACCESS_TOKEN" \\
  --data-urlencode "format=pdf" \\
  --data-urlencode "include_timestamps=true" \\
  --data-urlencode "include_speakers=true" \\
  -o transcript.pdf
"""
}

# SDK examples
SDK_EXAMPLES = {
    "python_sdk": """
# Install SDK
pip install transcription-api-sdk

# Usage
from transcription_sdk import TranscriptionClient

# Initialize client
client = TranscriptionClient(
    api_key="your_api_key",
    # or use access_token="your_jwt_token"
)

# Upload and transcribe
transcript = client.transcribe_file(
    "path/to/audio.mp3",
    language="auto",
    model="large-v3",
    enable_diarization=True,
    enable_ner=True
)

# Wait for completion
transcript.wait_until_complete(callback=lambda p: print(f"Progress: {p}%"))

# Get results
print(transcript.text)
print(f"Duration: {transcript.duration} seconds")
print(f"Speakers: {transcript.speakers}")

# Search transcripts
results = client.search(
    query="machine learning",
    language="en",
    date_from="2024-01-01"
)

for result in results:
    print(f"{result.title}: {result.snippet}")
""",
    
    "node_sdk": """
// Install SDK
npm install @transcription-api/sdk

// Usage
const { TranscriptionClient } = require('@transcription-api/sdk');

// Initialize client
const client = new TranscriptionClient({
  apiKey: process.env.TRANSCRIPTION_API_KEY
});

// Async upload and transcribe
async function transcribeFile() {
  try {
    // Upload file
    const transcript = await client.transcribeFile({
      filePath: './audio.mp3',
      options: {
        language: 'auto',
        model: 'large-v3',
        enableDiarization: true,
        enableNER: true
      }
    });
    
    // Monitor progress
    transcript.on('progress', (progress) => {
      console.log(`Progress: ${progress}%`);
    });
    
    // Wait for completion
    await transcript.waitUntilComplete();
    
    // Get results
    console.log('Text:', transcript.text);
    console.log('Entities:', transcript.entities);
    
    // Export
    await transcript.exportTo('./output.srt', 'srt');
    
  } catch (error) {
    console.error('Transcription failed:', error);
  }
}

// Real-time WebSocket monitoring
client.ws.on('transcription.complete', (data) => {
  console.log('Transcription completed:', data.transcriptId);
});
"""
}

# Error handling examples
ERROR_HANDLING_EXAMPLES = {
    "python": """
import requests
from typing import Optional
import time

class APIError(Exception):
    def __init__(self, status_code, message, retry_after=None):
        self.status_code = status_code
        self.message = message
        self.retry_after = retry_after
        super().__init__(f"API Error {status_code}: {message}")

def api_request_with_retry(method, url, max_retries=3, **kwargs):
    headers = kwargs.get('headers', {})
    
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                if attempt < max_retries - 1:
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    raise APIError(429, "Rate limit exceeded", retry_after)
            
            # Handle other errors
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Request failed, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise
    
    raise Exception("Max retries exceeded")

# Usage with error handling
try:
    response = api_request_with_retry(
        'POST',
        f"{BASE_URL}/api/transcription/process",
        headers={'Authorization': f'Bearer {token}'},
        json={'transcript_id': 123}
    )
    result = response.json()
except APIError as e:
    if e.status_code == 429:
        print(f"Rate limited. Try again in {e.retry_after} seconds")
    elif e.status_code == 401:
        print("Authentication failed. Please login again.")
    else:
        print(f"API error: {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
""",
    
    "javascript": """
// Comprehensive error handling
class APIClient {
  constructor(baseURL, accessToken) {
    this.baseURL = baseURL;
    this.accessToken = accessToken;
    this.maxRetries = 3;
  }
  
  async request(method, endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        const response = await fetch(url, {
          method,
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json',
            ...options.headers
          },
          ...options
        });
        
        // Handle different status codes
        if (response.ok) {
          return await response.json();
        }
        
        const errorData = await response.json().catch(() => ({}));
        
        switch (response.status) {
          case 401:
            // Try to refresh token
            await this.refreshToken();
            continue; // Retry request
            
          case 429:
            // Rate limited
            const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
            if (attempt < this.maxRetries - 1) {
              console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
              await this.sleep(retryAfter * 1000);
              continue;
            }
            throw new Error(`Rate limit exceeded. Retry after ${retryAfter} seconds`);
            
          case 422:
            // Validation error
            throw new ValidationError(errorData.detail || 'Validation failed');
            
          default:
            throw new Error(errorData.error || `Request failed: ${response.statusText}`);
        }
        
      } catch (error) {
        if (attempt === this.maxRetries - 1) {
          throw error;
        }
        
        // Network error - exponential backoff
        const waitTime = Math.min(1000 * Math.pow(2, attempt), 30000);
        console.log(`Network error, retrying in ${waitTime}ms...`);
        await this.sleep(waitTime);
      }
    }
  }
  
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  async refreshToken() {
    // Implement token refresh logic
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
      localStorage.setItem('access_token', data.access_token);
    } else {
      throw new Error('Token refresh failed');
    }
  }
}

// Custom error classes
class ValidationError extends Error {
  constructor(details) {
    super('Validation Error');
    this.name = 'ValidationError';
    this.details = details;
  }
}
"""
}

def get_all_examples() -> Dict[str, Dict[str, str]]:
    """Get all code examples organized by language"""
    return {
        "python": PYTHON_EXAMPLES,
        "javascript": JAVASCRIPT_EXAMPLES,
        "curl": CURL_EXAMPLES,
        "sdk": SDK_EXAMPLES,
        "error_handling": ERROR_HANDLING_EXAMPLES
    }