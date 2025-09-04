# Audio Processing Refactoring Guide

This document provides a detailed, step-by-step guide for the development team to refactor the audio processing system and consolidate the functionality of `audio_preprocessing_system_fast.py` into `audio_preprocessing_system.py`.

---

## 1. Goal

The goal of this refactoring is to create a single, unified audio processing system that can be configured to run in either a "full" or a "fast" mode. This will eliminate code duplication, improve maintainability, and provide a more flexible API for audio preprocessing.

---

## 2. Refactoring Steps

### Step 1: Modify the `AudioPreprocessingConfig`

In `audio_preprocessing_system.py`, add a new `mode` parameter to the `AudioPreprocessingConfig` data class. This parameter will control which processing pipeline is used.

```python
from enum import Enum

class ProcessingMode(str, Enum):
    FULL = "full"
    FAST = "fast"

@dataclass
class AudioPreprocessingConfig:
    mode: ProcessingMode = ProcessingMode.FULL
    # ... existing parameters
```

### Step 2: Modify the `preprocess_audio` Method

In `audio_preprocessing_system.py`, modify the `preprocess_audio` method to check the `mode` parameter and execute the appropriate logic.

```python
class AudioPreprocessor:
    # ... existing code

    def preprocess_audio(self, audio_input, config: Optional[AudioPreprocessingConfig] = None) -> AudioPreprocessingResult:
        config = config or self.config

        if config.mode == ProcessingMode.FAST:
            return self._preprocess_audio_fast(audio_input, config)
        else:
            return self._preprocess_audio_full(audio_input, config)

    def _preprocess_audio_full(self, audio_input, config: AudioPreprocessingConfig) -> AudioPreprocessingResult:
        # ... existing logic from the original preprocess_audio method

    def _preprocess_audio_fast(self, audio_input, config: AudioPreprocessingConfig) -> AudioPreprocessingResult:
        # ... logic from audio_preprocessing_system_fast.py will go here
```

### Step 3: Integrate the "Fast" Mode Logic

Copy the logic from the `preprocess_audio` method in `audio_preprocessing_system_fast.py` into the new `_preprocess_audio_fast` method in `audio_preprocessing_system.py`. You will need to adapt the code to work with the data models and configuration from the main system.

### Step 4: Update Call Sites

Search the codebase for any code that imports and uses the `AudioPreprocessorFast` from `audio_preprocessing_system_fast.py`. Update these call sites to use the `AudioPreprocessor` from `audio_preprocessing_system.py` and pass the `mode='fast'` parameter in the `AudioPreprocessingConfig`.

### Step 5: Archive the Old Module

Once all the logic has been migrated and the call sites have been updated, move the `audio_preprocessing_system_fast.py` file to the `archive` directory.

```bash
mv audio_preprocessing_system_fast.py archive/
```

---

## 3. Verification

After the refactoring is complete, the development team should:

1.  **Run all existing tests** to ensure that the changes have not introduced any regressions.
2.  **Add new tests** for the `mode` parameter to ensure that both the "full" and "fast" modes are working correctly.
3.  **Perform manual testing** of the application to verify that the audio preprocessing is working as expected in both modes.
