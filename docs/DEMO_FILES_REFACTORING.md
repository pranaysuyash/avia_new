# Demo Files Refactoring

This document outlines the process and results of refactoring the `demo_` files in the codebase, following the "Intent-First" philosophy.

---

## 1. Intent

The goal of this refactoring was to address the large number of `demo_` files in the codebase. These files cluttered the project, increased maintenance overhead, and their purpose was often unclear. The intent was to evaluate each file, preserve the valuable ones as examples or tests, and remove the obsolete ones.

---

## 2. Actions Taken

### 2.1. Inventory

An inventory of all `demo_` files was created. A total of 128 demo files were identified.

### 2.2. Categorization and Evaluation

The demo files were categorized into three groups:

-   **Core Functionality Demos:** These files demonstrate the usage of core modules like NER, STT, and TTS. They were deemed valuable as usage examples.
-   **API Demos:** These files demonstrate the usage of the API endpoints. They were deemed valuable as a basis for integration tests.
-   **UI and Feature Demos:** These files demonstrate specific features or UI components that are likely obsolete and have been integrated into the main application.

### 2.3. Execution

-   An `examples` directory was created.
-   The "Core Functionality Demos" were moved to the `examples` directory.
-   The remaining `demo_` files, which fall into the "API Demos" and "UI and Feature Demos" categories, have been left in the root directory for now, with the recommendations outlined below.

---

## 3. Recommendations

### 3.1. Convert API Demos to Integration Tests

The following files should be reviewed by the development team and converted into formal integration tests. Once the tests are created, the original demo files should be deleted.

-   `demo_api_platform_comprehensive.py`
-   `demo_media_api.py`
-   `demo_ner_advanced_api.py`
-   `demo_ner_basic_api.py`
-   `demo_stt_api.py`
-   `demo_tts_api.py`

### 3.2. Delete Obsolete UI and Feature Demos

The remaining `demo_` files are likely obsolete and should be deleted. The development team should perform a final review to ensure that no valuable code is lost before deleting them.

---

## 4. Next Steps

-   The development team should review the recommendations in this document and create tasks in their backlog to address them.
-   Once the recommendations have been implemented, this document can be archived.
