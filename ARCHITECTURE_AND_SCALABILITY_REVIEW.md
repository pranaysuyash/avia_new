# Architecture and Scalability Review

## 1. Executive Summary

The application currently operates as a **hybrid monolith**. The Streamlit frontend acts as both a user interface and a business logic orchestrator, with a developing but not fully enforced separation from a FastAPI backend. This is a natural evolution for a rapidly developed project.

To ensure future scalability and maintainability, the architecture needs to evolve towards a clear **decoupled, API-centric model**. The primary goal is to make the Streamlit application a pure, stateless client that communicates with a robust, asynchronous, and scalable FastAPI backend. This separation is the key to supporting more users, enabling new client types (e.g., a future JavaScript web app), and improving overall system resilience.

This document outlines the current state and provides a clear, actionable roadmap for this architectural evolution.

## 2. Current Architecture Analysis

-   **Frontend:** A single, large **Streamlit** application (`app.py`) serves as the primary user interface. Its major architectural challenge is that it directly imports and uses backend logic modules, tightly coupling the UI to the business logic.

-   **Backend:** There is a significant ambiguity in the backend strategy:
    1.  **Primary API (`api_launcher.py`):** A **FastAPI** application that appears to be the intended production backend. It uses modern practices like `uvicorn` and is designed to be the core of the system.
    2.  **Mock Server (`backend_server.py`):** Another FastAPI application that serves mock data, likely for developing a separate, more advanced frontend (`frontend-v2`).
    This duality creates confusion and splits development effort.

-   **Processing Model:** Long-running tasks like audio transcription are currently handled within the application's request-response cycle. As you scale, this will lead to request timeouts and a poor user experience. The application will not be able to handle multiple concurrent processing jobs efficiently.

-   **Database:** The use of `alembic.ini` and SQLAlchemy points to a robust relational database setup (likely PostgreSQL or similar), which is an excellent choice. However, it's not clear if all application data and state are consistently managed through this database.

## 3. Key Scalability Recommendations

To prepare the application for growth, I recommend focusing on four key areas:

### Recommendation 1: Unify and Decouple the Backend

You must commit to a single, unified backend architecture. The Streamlit app should be a **pure client** to the primary FastAPI backend.

-   **Action:** All business logic must be removed from the Streamlit application. The `app.py` file should not have any direct imports from your core logic. Instead, it should use an API client (like the one in `api_client.py`) to make HTTP requests to the FastAPI backend for all operations (e.g., uploading files, starting transcription, fetching results).
-   **Benefit:** This decoupling allows you to scale the frontend and backend independently. It also makes it possible to build new clients (like the `frontend-v2` you seem to be prototyping) on top of the same robust API without duplicating logic.

### Recommendation 2: Offload Long-Running Tasks with a Task Queue

Media processing is too slow for a standard HTTP request. You need to move this work to a background worker process using a task queue.

-   **Action:** Integrate a task queue like **ARQ (Asyncio and Redis Queue)** or **Celery**. ARQ is lightweight and a natural fit for FastAPI's `asyncio` model.
    -   The API endpoint for transcription should no longer perform the work directly. Instead, it should:
        1.  Add a "job" to the task queue.
        2.  Immediately return a `job_id` to the client.
    -   The Streamlit app will then use this `job_id` to poll another API endpoint (e.g., `/api/jobs/{job_id}/status`) to check the progress and retrieve the results when ready.
-   **Benefit:** This makes your API incredibly fast and responsive. It prevents request timeouts and allows you to scale the number of background workers independently to handle a high volume of processing jobs.

### Recommendation 3: Implement a Caching Layer

Transcription and analysis are expensive and time-consuming. You should not re-process the same file multiple times.

-   **Action:** Use a fast in-memory store like **Redis** for caching. Before starting a new processing job, calculate a hash (e.g., SHA-256) of the input file. Check if a result for this hash already exists in the cache. If it does, return the cached result immediately instead of starting a new job.
-   **Benefit:** Drastically reduces processing costs and provides an instantaneous experience for users who re-upload the same content.

### Recommendation 4: Embrace Asynchronous Operations

Your choice of FastAPI is excellent because it is built for asynchronous I/O. You should ensure this advantage is fully leveraged.

-   **Action:** Ensure that all I/O-bound operations in your FastAPI backend (database queries, calls to external APIs like OpenAI, file system access) use `async` and `await`.
-   **Benefit:** This allows a single server process to handle many concurrent connections, significantly increasing the throughput of your API.

## 4. Proposed Scalable Architecture

Here is a diagram of the target architecture:

```
+----------------+      +----------------+      +------------------------------------+
|                |      |                |      |      FastAPI Backend (Stateless)   |
|  Streamlit UI  |----->|  Load Balancer |----->| (run multiple instances for scale) |
| (Pure Client)  |      |                |      |                                    |
+----------------+      +----------------+      +------------------------------------+
                                                     |
                                                     | (HTTP Requests)
         +-------------------------------------------+-------------------------------------------+
         |                                           |                                           |
+--------v--------+                      +-----------v-----------+                      +----------v--------+
|                 |                      |                       |                      |                   |
| Task Queue      | (Jobs)               | Database              | (Read/Write)         | Cache             | (Cache Results)
| (e.g., Redis)   |--------------------->| (e.g., PostgreSQL)    |<--------------------->| (e.g., Redis)     |
|                 |                      |                       |                      |                   |
+-----------------+                      +-----------------------+                      +-------------------+
         ^
         | (Pulls Jobs)
+--------+--------+
|                 |
| Worker Processes| (Processes Jobs)
| (Independent)   |-----> (Calls to OpenAI, etc.)
|                 |
+-----------------+
```

## 5. Actionable Migration Plan

1.  **Consolidate the Backend:** Archive the mock `backend_server.py`. All future backend development should focus on the primary FastAPI application defined by `api_launcher.py`.
2.  **Refactor Streamlit:** Go through `app.py` and methodically replace every direct call to a backend module with an API call to your FastAPI server. This is the most critical step.
3.  **Integrate a Task Queue:**
    -   Add `arq` to your `pyproject.toml` (or requirements).
    -   Create a worker function that contains your core transcription/analysis logic.
    -   Modify your `/transcribe` API endpoint to enqueue a job for that worker function and return a job ID.
    -   Create a `/jobs/{job_id}/status` endpoint for polling.
4.  **Implement Caching:** Add Redis to your stack and implement the file hashing and cache-checking logic before enqueuing a new processing job.
