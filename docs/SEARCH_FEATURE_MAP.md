# Search Systems Feature Map

This document provides a detailed feature map of the two advanced search systems, `advanced_search_discovery.py` and `advanced_search_system.py`, to help guide the consolidation effort.

---

## Feature Comparison

| Feature                       | `advanced_search_discovery.py`                               | `advanced_search_system.py`                                  |
| ----------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| **Core Search Types**         | Text, Fuzzy, Voice, Boolean, Temporal, Speaker               | Semantic, Hybrid, Traditional, Fuzzy (via legacy import)     |
| **Data Storage**              | Self-contained SQLite database (`search.db`)                 | Relies on external services (`ComprehensiveSearchService`)   |
| **Search Indexing**           | Basic content indexing in SQLite                             | Not explicitly defined (likely handled by external services) |
| **Relevance Scoring**         | Basic scoring based on term matching and simple heuristics   | Advanced, configurable scoring (BM25, TF-IDF, Neural, Ensemble) |
| **Query Analysis**            | Simple boolean query parsing                                 | Advanced query analysis (entity extraction, intent detection) |
| **Semantic Understanding**      | No                                                           | Yes (via `SemanticSearchEngine` and embeddings)              |
| **Faceted Search**            | No                                                           | Yes (with hierarchical and range-based facets)               |
| **Result Diversification**    | No                                                           | Yes                                                          |
| **Search Alerts**             | Yes (with email, webhook, and in-app notifications)          | No                                                           |
| **Voice Search**              | Yes (via `speech_recognition` library)                       | No                                                           |
| **Data Models**               | `SearchQuery`, `SearchResult`, `SavedSearch`, `SearchAlert`    | `AdvancedSearchQuery`, `EnhancedSearchResult`, `AdvancedSearchResponse` |
| **Dependencies**              | `sqlite3`, `speech_recognition`, `fuzzywuzzy`                | `sentence_transformers`, `sklearn`, and other services       |

---

## Analysis and Recommendations

### Overlapping Features

-   **Fuzzy Search:** Both systems have fuzzy search capabilities. The implementation in `advanced_search_discovery.py` should be migrated or re-implemented in the new system.
-   **Boolean Search:** Both systems support boolean search. The more advanced parsing and execution logic should be consolidated into the new system.

### Unique Features to Migrate

The following features from `advanced_search_discovery.py` are valuable and should be migrated to `advanced_search_system.py`:

-   **Voice Search:** The ability to perform voice-based queries is a valuable user feature.
-   **Search Alerts:** The notification system for saved searches is a powerful feature that should be preserved.
-   **Saved Searches:** The functionality for saving and re-running searches should be integrated into the new system.

### Deprecation Plan

Once the valuable features from `advanced_search_discovery.py` have been migrated to `advanced_search_system.py`, the older file can be deprecated and archived. This will create a single, unified, and modern search system for the application.
