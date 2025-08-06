# API Reference

This document provides a detailed reference for the Audio/Video Transcription & Analysis Platform API.

## Authentication

All API endpoints require authentication. The API uses JWT tokens for authentication. To obtain a token, you must first log in with your username and password.

### POST /auth/login

Authenticates a user and returns a JWT token.

**Request Body:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Login successful",
  "token": "string",
  "user_id": "string",
  "expires_at": "2025-08-06T15:41:00.000Z"
}
```

### POST /auth/register

Registers a new user. This endpoint is only accessible to admin users.

**Request Body:**

```json
{
  "user_id": "string",
  "password": "string",
  "role": "string"
}
```

**Response:**

```json
{
  "user_id": "string",
  "role": "string",
  "created_at": "2025-08-06T15:41:00.000Z",
  "last_login": null,
  "active": true
}
```

### POST /auth/logout

Logs out the current user.

**Response:**

```json
{
  "user_id": "string"
}
```

### POST /auth/api-key

Generates a new API key for the current user.

**Request Body:**

```json
{
  "description": "string"
}
```

**Response:**

```json
{
  "success": true,
  "message": "API key generated successfully",
  "api_key": "string",
  "description": "string",
  "created_at": "2025-08-06T15:41:00.000Z"
}
```

### GET /auth/api-keys

Lists the current user's API keys.

**Response:**

```json
{
  "api_keys": [
    {
      "key_id": "string",
      "description": "string",
      "created_at": "2025-08-06T15:41:00.000Z"
    }
  ],
  "count": 1
}
```

### DELETE /auth/api-key/{key_id}

Revokes an API key.

**Response:**

```json
{
  "key_id": "string"
}
```

### GET /auth/me

Gets the current user's information.

**Response:**

```json
{
  "user_id": "string",
  "role": "string",
  "created_at": "2025-08-06T15:41:00.000Z",
  "last_login": "2025-08-06T15:41:00.000Z",
  "active": true
}
```

### PUT /auth/password

Changes the current user's password.

**Request Body:**

```json
{
  "old_password": "string",
  "new_password": "string"
}
```

**Response:**

```json
{
  "user_id": "string"
}
```

### GET /auth/verify

Verifies the current user's authentication token.

**Response:**

```json
{
  "user_id": "string",
  "valid": true,
  "timestamp": "2025-08-06T15:41:00.000Z"
}
```

## Transcription

These endpoints are used to transcribe audio and video files.

### POST /transcription/upload

Uploads an audio or video file for transcription.

**Request Body:**

-   `file`: The audio or video file to upload.

**Response:**

```json
{
  "file_id": "string",
  "file_name": "string",
  "file_size": 0,
  "content_type": "string"
}
```

### POST /transcription/process

Processes an uploaded file for transcription.

**Request Body:**

```json
{
  "file_id": "string",
  "language": "string",
  "use_api": false,
  "extract_entities": true,
  "enable_diarization": true
}
```

**Response:**

```json
{
  "transcript_id": "string",
  "text": "string",
  "language": "string",
  "duration": 0,
  "word_count": 0,
  "entities": [],
  "speakers": [],
  "confidence": 0,
  "processing_time": 0,
  "created_at": "2025-08-06T15:41:00.000Z"
}
```

### GET /transcription/status/{transcript_id}

Gets the status of a transcription.

**Response:**

```json
{
  "transcript_id": "string",
  "status": "string",
  "result": {}
}
```

### GET /transcription/history

Gets the user's transcription history.

**Query Parameters:**

-   `limit`: The maximum number of results to return.
-   `offset`: The number of results to skip.

**Response:**

```json
{
  "transcriptions": [],
  "total_count": 0,
  "page": 0,
  "per_page": 0
}
```

### GET /transcription/list

Lists the user's transcriptions.

**Query Parameters:**

-   `limit`: The maximum number of results to return.
-   `offset`: The number of results to skip.

**Response:**

```json
{
  "items": [],
  "total": 0,
  "page": 0,
  "pageSize": 0
}
```

### DELETE /transcription/{transcript_id}

Deletes a transcription.

**Response:**

```json
{
  "transcript_id": "string"
}
```

### GET /transcription/supported-formats

Gets the supported audio and video formats.

**Response:**

```json
{
  "audio_formats": [],
  "video_formats": [],
  "max_file_size_mb": 0,
  "supported_languages": [],
  "whisper_models": []
}
```

### POST /transcription/batch

Processes multiple files for transcription in a batch.

**Request Body:**

-   `files`: A list of audio or video files to upload.
-   `language`: The language of the audio.
-   `model`: The transcription model to use.
-   `enable_diarization`: Whether to enable speaker diarization.
-   `extract_entities`: Whether to extract entities.

**Response:**

```json
{
  "batch_id": "string",
  "total_files": 0,
  "completed": 0,
  "failed": 0,
  "results": []
}
```

### GET /transcription/batch/{batch_id}/status

Gets the status of a batch transcription.

**Response:**

```json
{
  "batch_id": "string",
  "total_files": 0,
  "transcriptions": []
}
```

### GET /transcription/models

Gets the available transcription models.

**Response:**

```json
{
  "whisper_models": [],
  "api_models": []
}
```