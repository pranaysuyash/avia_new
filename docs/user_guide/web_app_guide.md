# Web Application User Guide

This guide provides a detailed walkthrough of the web application's features and how to use them.

## Table of Contents

- [Getting Started](#getting-started)
  - [Uploading Files](#uploading-files)
  - [Recording Audio](#recording-audio)
- [Analysis Modes](#analysis-modes)
  - [Basic Mode](#basic-mode)
  - [Advanced Mode](#advanced-mode)
  - [Advanced+ (Speaker Diarization)](#advanced-speaker-diarization)
  - [Multi-Language Mode](#multi-language-mode)
- [Features](#features)
  - [Admin Panel](#admin-panel)
  - [Batch Processing](#batch-processing)
  - [Search](#search)
  - [Video Processing](#video-processing)
  - [Content Insights](#content-insights)
  - [Real-time Collaboration](#real-time-collaboration)
  - [AI Model Customization](#ai-model-customization)
  - [Analytics Dashboard](#analytics-dashboard)
  - [Export & Sharing](#export--sharing)

## Getting Started

### Uploading Files

You can upload audio or video files in MP3, WAV, MP4, or M4A format. The maximum file size is 100MB.

1.  Click the **Browse files** button or drag and drop a file into the upload area.
2.  Once the file is uploaded, you will see information about the file, such as its size and duration.

### Recording Audio

You can also record audio directly in the application.

1.  Click the **Record Audio** button to start recording.
2.  Click the **Stop** button when you are finished.
3.  The recorded audio will be available for processing.

## Analysis Modes

The application offers several analysis modes to suit your needs.

### Basic Mode

-   **Fast, local processing** using spaCy.
-   **Works offline**.
-   Extracts basic entities such as names, organizations, dates, and locations.
-   No API keys required.

### Advanced Mode

-   **AI-powered analysis** with OpenAI's GPT models.
-   Provides **content summaries and insights**.
-   Better context understanding.
-   Requires an OpenAI API key.

### Advanced+ (Speaker Diarization)

-   All the features of Advanced Mode, plus:
-   **Speaker identification and separation**.
-   **Multi-language detection and support**.
-   Interactive transcript with timestamps.
-   Confidence scoring and quality analysis.
-   Advanced export options (SRT, VTT, CSV).
-   Requires an OpenAI API key.

### Multi-Language Mode

-   **Automatic language detection** for over 50 languages.
-   **Real-time language switching detection**.
-   Multi-language entity extraction.
-   Translation capabilities.
-   Code-switching analysis.
-   Requires an OpenAI API key.

## Features

### Admin Panel

The admin panel provides tools for content generation and testing.

-   **Script Generation**: Create realistic scripts from text prompts.
-   **Text-to-Speech**: Convert scripts to natural-sounding audio using ElevenLabs.
-   **Pipeline Testing**: Test generated content through the analysis pipeline.

### Batch Processing

Process multiple files at once with the batch processing feature.

-   Upload multiple files and select the desired analysis mode.
-   The application will process the files in parallel and provide a summary of the results.

### Search

The advanced search feature allows you to search across all your transcribed content.

-   **Full-text search** with filters and facets.
-   **Save searches** for later use.
-   **Semantic search** to find content based on meaning, not just keywords.

### Video Processing

The video processing tools allow you to analyze video content.

-   **Frame extraction** to capture still images from the video.
-   **Object detection** to identify objects in the video.

### Content Insights

AI-powered content insights provide a deeper understanding of your content.

-   **Emotion detection** to analyze the emotional tone of the content.
-   **Bias analysis** to identify potential biases in the content.
-   **Complexity scoring** to assess the complexity of the content.
-   **Plagiarism checking** to identify potential plagiarism.

### Real-time Collaboration

Collaborate with your team in real-time.

-   **Live editing** of transcripts.
-   **Timestamped comments** to provide feedback.
-   **Version control** to track changes and restore previous versions.

### AI Model Customization

Customize the AI models to suit your needs.

-   **Custom vocabularies** to improve transcription accuracy.
-   **Voice profiles** to improve speaker diarization.
-   **Custom entity types** to extract the information that is most important to you.

### Analytics Dashboard

The analytics dashboard provides insights into your usage of the platform.

-   **Usage metrics** to track your usage of the platform.
-   **Team insights** to see how your team is using the platform.

### Export & Sharing

Export your transcripts and analysis results in a variety of formats.

-   **PDF, DOCX, CSV, and more**.
-   **Share transcripts** with your team or with external collaborators.
