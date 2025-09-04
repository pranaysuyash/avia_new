# Technical Debt Backlog

This document tracks the technical debt in the codebase. Each item in the backlog includes a description of the debt, its severity, the estimated effort to fix it, and a recommendation for how to address it.

---

## High Severity

### TD-001: Duplicated Search Functionality

-   **Description:** The `advanced_search_discovery.py` and `advanced_search_system.py` modules contain duplicated and overlapping functionality for advanced search. This increases the maintenance overhead and creates confusion about which module to use.
-   **Location:** `advanced_search_discovery.py`, `advanced_search_system.py`
-   **Severity:** High
-   **Effort:** Medium
-   **Recommendation:** Consolidate the two modules into a single, unified search system, as outlined in the Refactoring Roadmap.

### TD-002: Lack of End-to-End Tests for Authentication

-   **Description:** The authentication system lacks end-to-end tests, which creates a significant security risk. There is no automated verification that the UI correctly enforces authentication and authorization rules.
-   **Location:** `app.py`
-   **Severity:** High
-   **Effort:** Medium
-   **Recommendation:** Add end-to-end tests for the authentication system using a framework like `pytest-playwright` or `selenium`, as outlined in the Refactoring Roadmap.

---

## Medium Severity

### TD-003: Duplicated Audio Preprocessing Logic

-   **Description:** The `audio_preprocessing_system.py` and `audio_preprocessing_system_fast.py` modules contain duplicated logic for audio preprocessing. This makes the code harder to maintain and evolve.
-   **Location:** `audio_preprocessing_system.py`, `audio_preprocessing_system_fast.py`
-   **Severity:** Medium
-   **Effort:** Medium
-   **Recommendation:** Refactor the two modules into a single, configurable module, as outlined in the Refactoring Roadmap.

### TD-004: God Object Application File

-   **Description:** The `app.py` file is a "God Object" that has too many responsibilities. This makes the application difficult to understand, maintain, and test.
-   **Location:** `app.py`
-   **Severity:** Medium
-   **Effort:** High
-   **Recommendation:** Decompose the `app.py` file into smaller, more manageable modules, as outlined in the Architectural Review.

---

## Low Severity

### TD-005: Lack of Documentation in Complex Modules

-   **Description:** Complex modules like `advanced_content_analysis.py` lack sufficient documentation, making them difficult for new developers to understand.
-   **Location:** `advanced_content_analysis.py`
-   **Severity:** Low
-   **Effort:** Low
-   **Recommendation:** Add a module-level docstring and inline comments to explain the complex logic, as outlined in the Refactoring Roadmap.

### TD-006: Obsolete Application Entry Points

-   **Description:** The `app_with_auth.py` and `app_refactored.py` files are obsolete entry points to the application. They are not used and clutter the codebase.
-   **Location:** `app_with_auth.py`, `app_refactored.py`
-   **Severity:** Low
-   **Effort:** Low
-   **Recommendation:** Archive these files to a separate `archive` directory, as outlined in the Refactoring Roadmap.
