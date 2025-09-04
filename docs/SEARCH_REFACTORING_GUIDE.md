# Search System Refactoring Guide

This document provides a detailed, step-by-step guide for the development team to refactor the search system and consolidate the functionality of `advanced_search_discovery.py` into `advanced_search_system.py`.

---

## Step 1: Prepare the New `AdvancedSearchSystem`

1.  **Create New Data Models:**
    -   In `advanced_search_system.py`, define new `SavedSearch` and `SearchAlert` data models. These should be based on the existing models in `advanced_search_discovery.py`, but adapted to use the new `AdvancedSearchQuery` data model.

2.  **Add New Methods:**
    -   In the `AdvancedSearchSystem` class, add placeholder methods for the features to be migrated:
        -   `voice_search(self) -> AdvancedSearchResponse`
        -   `save_search(self, query: AdvancedSearchQuery, name: str, description: str) -> SavedSearch`
        -   `get_saved_search(self, search_id: str) -> SavedSearch`
        -   `run_saved_search(self, search_id: str) -> AdvancedSearchResponse`
        -   `create_alert(self, saved_search_id: str, conditions: dict) -> SearchAlert`
        -   `get_alert(self, alert_id: str) -> SearchAlert`

---

## Step 2: Migrate the `VoiceSearchEngine`

1.  **Create `voice_search.py`:**
    -   Create a new file, `search/voice_search.py`.
    -   Move the `VoiceSearchEngine` class from `advanced_search_discovery.py` into this new file.

2.  **Integrate into `AdvancedSearchSystem`:**
    -   In `advanced_search_system.py`, import the `VoiceSearchEngine`.
    -   Implement the `voice_search` method. This method should instantiate the `VoiceSearchEngine`, capture the user's voice query, and then pass the transcribed text to the existing `search` method.

---

## Step 3: Migrate Saved Searches and Search Alerts

1.  **Create `search_alerts.py`:**
    -   Create a new file, `search/search_alerts.py`.
    -   Move the `SearchAlertSystem` class from `advanced_search_discovery.py` into this new file.

2.  **Adapt `SearchAlertSystem`:**
    -   Modify the `SearchAlertSystem` to work with the new `SavedSearch` data model and the main application database.

3.  **Implement Saved Search and Alert Methods:**
    -   Implement the placeholder methods for saved searches and alerts in the `AdvancedSearchSystem` class. These methods will interact with the database to store and retrieve saved searches and alerts.

4.  **Integrate Alert Triggering:**
    -   Set up a background job or a scheduled task to periodically run the `SearchAlertSystem.check_alerts` method.

---

## Step 4: Update All Call Sites

1.  **Identify Call Sites:**
    -   Search the entire codebase for any code that imports and uses the `AdvancedSearchEngine` from `advanced_search_discovery.py`.

2.  **Update Imports:**
    -   Change the imports to use the `AdvancedSearchSystem` from `advanced_search_system.py`.

3.  **Update Method Calls:**
    -   Update the method calls to use the new methods of the `AdvancedSearchSystem`.

---

## Step 5: Archive the Old Search System

1.  **Move the File:**
    -   Once all the features have been migrated and all call sites have been updated, move the `advanced_search_discovery.py` file to the `archive` directory.

2.  **Verify Functionality:**
    -   Run all tests and perform manual testing to ensure that the new, unified search system is working correctly.
