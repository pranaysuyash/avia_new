# Project Structure Review

## 1. Executive Summary

The current project structure is the single most significant challenge to the application's maintainability, scalability, and overall development velocity. The root directory is a flat collection of over 200 files, which creates high cognitive overhead and makes it difficult to understand the relationships between different parts of the application.

This document provides a detailed recommendation for migrating to a standard, scalable Python project structure. Adopting this structure will:

-   **Improve Maintainability:** Make it easier to find and modify code.
-   **Clarify Architecture:** Clearly separate the different components of your application (API, UI, core logic).
-   **Enhance Scalability:** Provide a solid foundation for future growth, whether that involves adding new features or scaling existing ones.
-   **Simplify Onboarding:** Make it easier for any future collaborators (or your future self) to understand the codebase.

## 2. Current State Analysis

-   **Flat Hierarchy:** All files, regardless of function (API, UI, configuration, business logic, documentation), reside in the root directory.
-   **Monolithic UI:** The `app.py` Streamlit application is a single, massive file containing logic for UI rendering, state management, and business process orchestration.
-   **Ambiguous Backend:** The presence of both a mock `backend_server.py` and a real `api_launcher.py` creates confusion about the true backend service.
-   **Implicit Structure:** The only hint of structure is the `api/` directory implied by the `api_launcher.py` script.

## 3. Proposed Project Structure

I recommend reorganizing the project into a standard "source" layout, which is common for modern Python applications. This structure clearly separates application code from other project files like tests, scripts, and documentation.

```
/Users/pranay/Projects/LLM/video/ner/
├── .env
├── .gitignore
├── alembic.ini
├── pyproject.toml         # <-- New: Replaces requirements.txt for better dependency management
├── README.md
│
├── scripts/               # <-- New: For utility and helper scripts
│   └── launcher.py        # <-- Unified launcher for API or UI
│
├── src/                   # <-- New: Main source code directory
│   ├── __init__.py
│   │
│   ├── api/               # The FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py        # The entry point for your FastAPI app (from api/api_main.py)
│   │   ├── dependencies.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── transcription.py
│   │   │   └── analysis.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── media.py
│   │
│   ├── app/               # The Streamlit application
│   │   ├── __init__.py
│   │   ├── main.py        # The refactored entry point for your Streamlit app
│   │   ├── pages/         # <-- New: For multi-page Streamlit structure
│   │   │   ├── 1_Transcription.py
│   │   │   └── 2_Admin_Panel.py
│   │   └── components/    # <-- New: For reusable UI components
│   │       ├── __init__.py
│   │       ├── sidebar.py
│   │       └── results_display.py
│   │
│   ├── core/              # <-- New: Shared business logic and configuration
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── media_processor.py
│   │   ├── transcription.py
│   │   ├── analysis.py
│   │   └── database.py
│   │
│   └── services/          # <-- New: For third-party API clients
│       ├── __init__.py
│       ├── openai_client.py
│       └── elevenlabs_client.py
│
├── tests/                 # For all application tests
│   ├── __init__.py
│   ├── test_api.py
│   └── test_core_logic.py
│
└── temp/                  # For temporary file storage
```

## 4. Explanation of the New Structure

-   **`pyproject.toml`**: This file is the modern standard for Python project configuration. It will define project metadata, dependencies (replacing `api_requirements.txt`), and tool configurations (like `pytest` or `flake8`). It provides a single source of truth for your project setup.
-   **`scripts/`**: A dedicated place for runnable scripts that are not part of the main application, like your API launcher.
-   **`src/`**: The "source" directory. Placing all your application code here prevents common import problems and clearly separates it from other project files.
-   **`src/api/`**: This directory will house your entire FastAPI application.
    -   `routers/`: Splits your API endpoints into logical groups (e.g., one file for transcription endpoints, another for analysis).
    -   `schemas/`: Contains your Pydantic models for request and response validation.
-   **`src/app/`**: This will house your Streamlit application.
    -   `pages/`: Streamlit has native support for multi-page apps. By placing files here, you can break down your massive `app.py` into logical pages (e.g., "Transcription", "Admin Panel").
    -   `components/`: For reusable Streamlit UI functions (e.g., a function to render the sidebar or display results).
-   **`src/core/`**: This is the heart of your application. It contains the core business logic that is independent of any framework. Your media processing, transcription logic, and analysis functions would live here. This allows you to share logic between your API and potentially other interfaces in the future.
-   **`src/services/`**: A dedicated place for clients that interact with external APIs like OpenAI or ElevenLabs. This isolates third-party dependencies.
-   **`tests/`**: All your tests go here, mirroring the structure of the `src` directory.

## 5. Actionable Migration Plan

As a solo developer, you can perform this migration incrementally:

1.  **Create the New Directories:** Start by creating the new folder structure (`src`, `src/api`, `src/app`, `src/core`, `scripts`, `tests`).
2.  **Move Core Logic:** Identify pure business logic functions in `app.py` and other root-level files (e.g., functions related to media processing, transcription, NER) and move them into the appropriate files within `src/core/`.
3.  **Refactor the Streamlit App:**
    *   Move `app.py` to `src/app/main.py`.
    *   Start extracting logical sections of the UI into separate files in `src/app/pages/`. For example, the code that renders the "Admin Panel" can go into `src/app/pages/2_Admin_Panel.py`.
    *   Extract reusable UI functions (like `display_api_status`) into `src/app/components/`.
4.  **Consolidate the Backend:**
    *   Decide which backend is the future. Assuming it's the "real" API, move the relevant code from the implied `api/` directory into the new `src/api/` structure.
    *   Retire or archive the `backend_server.py` mock server, or move it to a `prototypes/` directory if you still need it for `frontend-v2` experiments.
5.  **Update Imports:** This is the most tedious part. As you move files, you will need to fix all the import statements. With the `src` layout, your imports will become more explicit, e.g., `from src.core.config import Config` or `from src.services.openai_client import transcribe`.
6.  **Adopt `pyproject.toml`:** Create a `pyproject.toml` file and transfer your dependencies from `api_requirements.txt`. You can then install dependencies with `pip install .` from the project root.

This is a significant undertaking, but the payoff in clarity and development speed will be immense. I am ready to guide you through these steps.
