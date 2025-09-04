# Search System Migration Plan

This document outlines the migration plan for consolidating the features of `advanced_search_discovery.py` into `advanced_search_system.py`.

---

## 1. Goal

The goal of this migration is to create a single, unified search system that combines the modern architecture of `advanced_search_system.py` with the valuable, user-facing features of `advanced_search_discovery.py`. This will result in a more powerful, maintainable, and feature-rich search experience for users.

---

## 2. Features to Migrate

The following features have been identified for migration:

1.  **Voice Search**
2.  **Saved Searches**
3.  **Search Alerts**

---

## 3. Migration Strategy

### 3.1. Voice Search

**Current Implementation:** The `VoiceSearchEngine` class in `advanced_search_discovery.py` uses the `speech_recognition` library to capture and transcribe voice queries.

**Proposed Integration:**

1.  **Move the `VoiceSearchEngine`:** Move the `VoiceSearchEngine` class from `advanced_search_discovery.py` to a new file, `voice_search.py`, in the `search` directory. This will make it a reusable component.
2.  **Add a `voice_search` Method:** Add a new `voice_search` method to the `AdvancedSearchSystem` class in `advanced_search_system.py`. This method will:
    -   Instantiate the `VoiceSearchEngine`.
    -   Call the `listen_for_query` method to capture and transcribe the user's voice query.
    -   Pass the transcribed query to the existing `search` method of the `AdvancedSearchSystem`.
3.  **Update the UI:** The UI will need to be updated to include a button or other control to initiate a voice search. This control will call the new `voice_search` method.

### 3.2. Saved Searches

**Current Implementation:** The `advanced_search_discovery.py` file includes a `SavedSearch` data model and methods for saving and running searches.

**Proposed Integration:**

1.  **Create a `SavedSearch` Model:** Create a new `SavedSearch` data model in `advanced_search_system.py`, similar to the one in the older file. This model should be adapted to work with the new `AdvancedSearchQuery` data model.
2.  **Add `save_search` and `run_saved_search` Methods:** Add new methods to the `AdvancedSearchSystem` class for saving and running searches. The `save_search` method will take a search query and a name, and the `run_saved_search` method will take a saved search ID.
3.  **Database Integration:** The saved searches should be stored in the main application database, not the separate `search.db` SQLite database used by the older system.

### 3.3. Search Alerts

**Current Implementation:** The `SearchAlertSystem` in `advanced_search_discovery.py` provides a system for creating and managing search alerts.

**Proposed Integration:**

1.  **Integrate the `SearchAlertSystem`:** The `SearchAlertSystem` can be moved to a new file, `search_alerts.py`, in the `search` directory. It will need to be adapted to work with the new `SavedSearch` model and the main application's notification system.
2.  **Add Alert Management Methods:** Add methods to the `AdvancedSearchSystem` class for creating, updating, and deleting search alerts.
3.  **Triggering Alerts:** The `SearchAlertSystem` will need to be triggered periodically to check for new content that matches the saved search criteria. This can be done using a background job or a scheduled task.

---

## 4. Deprecation Plan

Once all the valuable features have been migrated from `advanced_search_discovery.py` to the new system, the old file can be safely archived. This will leave a single, unified, and powerful search system that is easier to maintain and extend.
