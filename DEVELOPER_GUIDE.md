# Developer Guide

This guide provides information for developers who want to contribute to the Audio/Video Transcription & Analysis Platform.

## Table of Contents

- [Project Structure](#project-structure)
- [Development Environment](#development-environment)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Running the Application](#running-the-application)
  - [Web Application](#web-application)
  - [API Server](#api-server)
  - [Desktop Application](#desktop-application)
  - [Mobile Application](#mobile-application)
- [Testing](#testing)
- [Contributing](#contributing)

## Project Structure

The project is a monorepo containing the web application, API server, desktop application, and mobile application.

-   `api/`: The FastAPI backend application.
    -   `main.py`: The main application file.
    -   `endpoints/`: API endpoints.
    -   `models/`: Database models.
    -   `schemas/`: Pydantic schemas.
-   `auth/`: Authentication services.
-   `database/`: Database models and migrations.
-   `desktop_app/`: The Electron-based desktop application.
-   `mobile/`: The React Native mobile application.
-   `tests/`: Backend and integration tests.
-   `*.py`: The Streamlit frontend application.

## Development Environment

### Prerequisites

-   Python 3.9+
-   Node.js 16+
-   Docker
-   Docker Compose

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd video-ner
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

4.  **Set up the database:**
    ```bash
    docker-compose up -d db
    ```

5.  **Run database migrations:**
    ```bash
    alembic upgrade head
    ```

## Running the Application

### Web Application

To run the Streamlit web application, use the following command:

```bash
streamlit run app.py
```

### API Server

To run the FastAPI API server, use the following command:

```bash
fastapi dev api/main.py
```

### Desktop Application

To run the Electron desktop application, use the following commands:

```bash
cd desktop_app
npm install
npm start
```

### Mobile Application

To run the React Native mobile application, use the following commands:

```bash
cd mobile
npm install
npm start
```

Then, scan the QR code with the Expo Go app on your mobile device.

## Testing

To run the backend tests, use `pytest`:

```bash
pytest
```

To run the frontend tests, use `jest`:

```bash
cd mobile
npm test
```

## Contributing

We welcome contributions to the project! Please follow these steps to contribute:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with a descriptive commit message.
4.  Push your changes to your fork.
5.  Create a pull request to the `main` branch of the original repository.
