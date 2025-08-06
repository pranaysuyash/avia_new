# Audio/Video Transcription & Analysis Platform

This is a comprehensive, enterprise-ready platform for transcribing, analyzing, and collaborating on audio and video content. It provides a rich set of features for individuals and teams, from basic transcription to advanced AI-powered content insights.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multi-Modal Transcription**: Transcribe audio and video files (MP3, WAV, MP4, M4A).
- **Advanced Analysis**: Named Entity Recognition (NER), sentiment analysis, and more.
- **Speaker Diarization**: Identify and separate different speakers in the audio.
- **Multi-Language Support**: Transcribe and analyze content in over 50 languages.
- **Collaboration Tools**: Team workspaces, real-time annotations, and version control.
- **Enterprise-Ready**: Secure, scalable, and extensible with a full-featured REST API.
- **Desktop and Mobile Apps**: Access the platform from anywhere.

For a full list of features, see the [User Guide](USER_GUIDE.md).

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: Streamlit, React (for desktop and mobile apps)
- **Database**: PostgreSQL
- **AI/ML**: OpenAI, spaCy, Pyannote
- **Deployment**: Docker, Docker Compose

## Quick Start

The easiest way to get the application running is with Docker.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd video-ner
    ```

2.  **Create a `.env` file:**
    ```bash
    cp .env.example .env
    ```
    Fill in the required API keys in the `.env` file. See the [Configuration](#configuration) section for more details.

3.  **Run the application:**
    ```bash
    docker-compose up --build
    ```

4.  **Access the application:**
    - **Web App**: `http://localhost:8501`
    - **API Docs**: `http://localhost:8000/docs`

## Configuration

The application is configured using environment variables. Create a `.env` file in the root of the project and add the following:

```
# Required API Keys
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Database
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=videoner
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

See the `env.example` file for a full list of available configuration options.

## Project Structure

The project is organized into the following directories:

-   `api/`: The FastAPI backend application.
-   `auth/`: Authentication services.
-   `database/`: Database models and migrations.
-   `desktop_app/`: The Electron-based desktop application.
-   `mobile/`: The React Native mobile application.
-   `tests/`: Backend and integration tests.
-   `*.py`: The Streamlit frontend application.

For a more detailed explanation of the project structure, see the [Developer Guide](DEVELOPER_GUIDE.md).

## Testing

To run the backend tests, use `pytest`:

```bash
pytest
```

## Contributing

We welcome contributions to the project! Please see the [Developer Guide](DEVELOPER_GUIDE.md) for more information on how to get started.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
