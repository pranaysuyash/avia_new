# Task: Frame OCR Indexing System Implementation

## Task Overview
Implement a Frame OCR Indexing System to enable search within video content that lacks transcripts by extracting text from video frames.

## Intent Analysis
- **Problem**: Videos without transcripts (archival footage, third-party content) are not searchable
- **User Impact**: High - Enables search in previously unsearchable content
- **Business Impact**: High - Differentiates platform, unlocks value in existing media assets
- **Technical Effort**: Medium - Uses proven tech with clear integration points
- **Strategic Importance**: High - Supports visual enrichment and search initiatives

## Subtasks

### 1. Frame Extraction Component
**Files**: New files to be created
**Requirements**:
- Extract keyframes from videos using scene-change detection or time intervals
- Support configurable extraction rates (e.g., every N seconds or scene changes)
- Handle various video formats supported by FFmpeg
- Store extracted frames temporarily for OCR processing
- Implement batch processing for efficiency

### 2. OCR Processing Component
**Files**: New files to be created or extend existing OCR functionality
**Requirements**:
- Integrate with existing OCR endpoint (`api/endpoints/ocr.py`)
- Add preprocessing (grayscale, threshold) for better OCR accuracy
- Support multiple languages
- Extract text with bounding box coordinates and confidence scores
- Handle various text orientations and fonts

### 3. Text Normalization and Indexing Component
**Files**: New files to be created
**Requirements**:
- Normalize extracted text (remove noise, standardize formatting)
- Extract timecodes for each text segment
- Index OCR results into existing search infrastructure
- Support phrase matching and fuzzy search
- Handle duplicate or overlapping text detections

### 4. API Endpoints
**Files**: New files to be created in `api/endpoints/`
**Requirements**:
- Endpoint to trigger OCR processing for a video
- Endpoint to check OCR job status
- Endpoint to query OCR results
- Endpoint to manage OCR processing queue
- Integrate with existing search endpoints

### 5. UI Components
**Files**: New or modified files in UI directories
**Requirements**:
- UI for triggering OCR processing
- Display OCR results in search results with timecode jumps
- Admin dashboard for monitoring OCR jobs
- Progress indicators for ongoing processing

## Technical Implementation Details

### Pipeline Architecture
1. **Trigger**: User requests OCR processing for a video
2. **Frame Extraction**: Extract keyframes (scene-change or interval-based)
3. **OCR Processing**: Process each frame with OCR engine
4. **Text Processing**: Normalize and organize extracted text with timecodes
5. **Indexing**: Index text into search system
6. **Storage**: Store OCR results for future queries
7. **Notification**: Notify user when processing is complete

### Integration Points
- **Frame Extraction**: Use FFmpeg utilities (similar to `advanced_timestamping_system.py`)
- **OCR Engine**: Reuse `api/endpoints/ocr.py` service with enhancements
- **Indexing**: Extend existing search index (`search/`, `semantic_search/`)
- **Storage**: Use existing storage manager (`cloud_storage/`)
- **API**: New endpoints or extension of existing OCR endpoints

### Data Schema
**OCR Results Storage**:
- `video_id`: Identifier for the source video
- `timestamp`: Timecode in video where text appears
- `text`: Extracted text content
- `bounding_box`: Coordinates of text in frame
- `confidence`: OCR confidence score
- `language`: Detected language
- `processed_at`: Timestamp when processed

## Acceptance Criteria
1. Successfully extract text from video frames with >80% accuracy for clear text
2. Correctly associate extracted text with timecodes (±0.5s accuracy)
3. Index OCR results into search system and make them searchable
4. Provide API endpoints for triggering and querying OCR processing
5. Implement UI components for user interaction
6. Handle various video formats and text orientations
7. Include error handling and retry mechanisms
8. Log processing metrics (time, cost, accuracy)
9. Implement rate limiting and resource controls
10. Support privacy features (redact faces/regions if required)

## Implementation Notes
- Start with POC on sample video to measure accuracy and latency
- Define schema for OCR results storage
- Implement batch job processing with idempotency
- Add cost and latency logging
- Include controls: per-team toggle, max frame rate caps, queue limits, retries
- Support internationalization: detect language, choose appropriate OCR model
- Implement privacy features: redact faces/regions before OCR, store only needed text
- Create comprehensive test suite including edge cases
- Document API and usage patterns