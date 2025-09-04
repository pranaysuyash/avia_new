# End-to-End Testing Guide

This document provides a step-by-step guide for setting up an end-to-end testing framework using `pytest-playwright` for the Streamlit application.

---

## 1. Goal

The goal is to establish a robust end-to-end testing environment that can simulate user interactions with the Streamlit application and verify its behavior, especially concerning authentication and authorization.

---

## 2. Recommended Framework: `pytest-playwright`

`pytest-playwright` is recommended for its ease of use with Python, its ability to interact with modern web applications, and its support for various browsers.

---

## 3. Setup Instructions

### Step 3.1: Install Dependencies

Ensure Python 3.8+ is installed. Then, install `pytest` and `pytest-playwright`:

```bash
pip install pytest pytest-playwright
playwright install  # Installs browser binaries (Chromium, Firefox, WebKit)
```

### Step 3.2: Project Structure

It is recommended to create a dedicated `e2e_tests` directory at the root of your project to house your end-to-end tests.

```
your_project/
├── app.py
├── requirements.txt
├── e2e_tests/
│   ├── conftest.py
│   └── test_authentication.py
└── ...
```

### Step 3.3: `conftest.py` (Pytest Fixtures)

Create a `conftest.py` file inside the `e2e_tests` directory. This file will contain fixtures that set up the test environment, such as launching the Streamlit application.

```python
import pytest
import subprocess
import time
import requests

@pytest.fixture(scope="session")
def streamlit_app_url():
    """Fixture to start and stop the Streamlit app for tests."""
    # Start Streamlit app in a subprocess
    # Ensure 'app.py' is the correct entry point for your Streamlit app
    process = subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for the Streamlit app to be ready
    url = "http://localhost:8501"
    retries = 10
    for i in range(retries):
        try:
            response = requests.get(f"{url}/_stcore/health", timeout=1)
            if response.status_code == 200:
                print(f"\nStreamlit app ready at {url}")
                break
        except requests.exceptions.ConnectionError:
            pass
        print(f"Waiting for Streamlit app... (attempt {i+1}/{retries})")
        time.sleep(2)
    else:
        process.terminate()
        raise RuntimeError("Streamlit app did not start in time.")

    yield url  # Provide the URL to tests

    # Teardown: Terminate the Streamlit app process
    print("\nShutting down Streamlit app...")
    process.terminate()
    process.wait()
    print("Streamlit app shut down.")

# You can add other fixtures here, e.g., for database setup/teardown
```

### Step 3.4: Writing Your First Test (`test_authentication.py`)

Create a test file, e.g., `test_authentication.py`, inside the `e2e_tests` directory. This file will contain your actual test cases.

```python
import pytest
from playwright.sync_api import Page, expect

def test_unauthenticated_redirect(page: Page, streamlit_app_url: str):
    """Test that an unauthenticated user is redirected to the login page."""
    page.goto(f"{streamlit_app_url}/protected_page") # Replace with an actual protected route
    expect(page).to_have_url(f"{streamlit_app_url}/login") # Replace with your actual login page URL
    expect(page.locator("text=Please log in")).to_be_visible()

def test_successful_login(page: Page, streamlit_app_url: str):
    """Test that a user can successfully log in."""
    page.goto(streamlit_app_url)
    
    # Assuming your login form has input fields with specific selectors
    page.fill("input[placeholder='Email']", "test@example.com")
    page.fill("input[placeholder='Password']", "testpassword")
    page.click("button:has-text('Log In')")
    
    # Wait for navigation or a success message
    expect(page).to_have_url(f"{streamlit_app_url}/") # Assuming root is the post-login page
    expect(page.locator("text=Welcome, testuser!")).to_be_visible()

# Add more tests for role-based access, logout, etc.
```

---

## 4. Running Your Tests

Navigate to your project's root directory in the terminal and run pytest, specifying the `e2e_tests` directory:

```bash
pytest e2e_tests/
```

---

## 5. Next Steps

Once the framework is set up, you can proceed with:

-   **Writing MVP Tests:** Implement the specific MVP tests for authentication as outlined in the `IMPROVEMENT_OPPORTUNITIES.md` document.
-   **Integrating into CI/CD:** Add the `pytest e2e_tests/` command to your CI/CD pipeline configuration.

```

## 6. Detailed MVP Test Cases for Authentication

This section provides a detailed breakdown of the Minimum Viable Product (MVP) end-to-end test cases for the authentication system. These tests are crucial for verifying the core security and access control mechanisms of the application.

### 6.1. Unauthenticated Access

-   **Scenario:** An unauthenticated user attempts to access a protected page.
-   **Steps:**
    1.  Open the application in a browser (ensure no active session).
    2.  Navigate directly to a known protected URL (e.g., `/my_transcripts`, `/admin_panel`).
-   **Expected Behavior:**
    -   The user is redirected to the login page.
    -   A clear message indicating the need to log in is displayed (e.g., "Please log in to access this page").
    -   The protected content is not displayed.

### 6.2. Successful Login and Logout

-   **Scenario:** A user with valid credentials successfully logs in and then logs out.
-   **Steps:**
    1.  Open the application in a browser.
    2.  Navigate to the login page.
    3.  Enter valid username/email and password.
    4.  Click the "Log In" button.
    5.  Verify successful redirection to the main application dashboard or a welcome page.
    6.  Verify the presence of a welcome message or user-specific content.
    7.  Click the "Logout" button (e.g., in the user menu or header).
-   **Expected Behavior:**
    -   Upon successful login, the user is redirected to the main application interface.
    -   The user's session is active, and protected content is accessible.
    -   Upon logout, the user is redirected back to the login page.
    -   The user's session is terminated, and protected content is no longer accessible.

### 6.3. Role-Based Access Control (RBAC)

-   **Scenario 1: Insufficient Permissions (User Role)**
    -   **Steps:**
        1.  Log in as a user with a standard "USER" role.
        2.  Attempt to navigate to an admin-only section (e.g., `/admin_panel`, `/user_management`).
    -   **Expected Behavior:**
        -   Access is denied.
        -   An appropriate error message is displayed (e.g., "Access Denied", "You do not have permission").
        -   The user is not redirected to the admin content.

-   **Scenario 2: Sufficient Permissions (Admin Role)**
    -   **Steps:**
        1.  Log in as a user with an "ADMIN" role.
        2.  Navigate to the admin-only section.
    -   **Expected Behavior:**
        -   Access is granted.
        -   The admin content is displayed correctly.

---

## 7. Integrating into CI/CD

Once the end-to-end tests are written and passing locally, they should be integrated into your Continuous Integration/Continuous Deployment (CI/CD) pipeline. This ensures that every code change is automatically validated against the critical user flows.

### Step 7.1: Add Playwright to CI/CD Environment

Ensure your CI/CD environment has `playwright` installed and its browser binaries are set up. Most CI/CD platforms have specific ways to do this (e.g., using a Docker image with Playwright pre-installed, or running `playwright install` as part of your build script).

### Step 7.2: Run Tests in CI/CD

Add the following command to your CI/CD pipeline script after your application has been deployed to a test environment (or started locally for testing):

```bash
pytest e2e_tests/
```

### Step 7.3: Configure Reporting

Configure your CI/CD system to collect and display the test results. `pytest` can generate various reports (e.g., JUnit XML, HTML) that can be integrated with CI/CD dashboards.

---

## 8. Next Steps

This guide provides the foundation for your end-to-end testing. The next steps involve actively implementing these tests and integrating them into your development workflow.

```