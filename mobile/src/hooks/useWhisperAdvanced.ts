/**
 * useWhisperAdvanced - React Native hook for Whisper Advanced Integration
 * Provides state management, offline support, and mobile-optimized functionality
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { Alert, AppState, AppStateStatus } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-netinfo/netinfo';
import BackgroundJob from 'react-native-background-job';
import whisperAPI, { 
  WhisperConfig, 
  TranscriptionResult, 
  LanguageDetectionResult 
} from '../api/whisperAdvanced';

// Types
interface UseWhisperAdvancedState {
  // Processing states
  isTranscribing: boolean;
  isDetectingLanguage: boolean;
  isRecording: boolean;
  isPlaying: boolean;
  
  // Data states
  result: TranscriptionResult | null;
  languageResult: LanguageDetectionResult | null;
  error: string | null;
  progress: number;
  
  // Configuration
  config: WhisperConfig;
  
  // Network and app state
  isOnline: boolean;
  isAppActive: boolean;
  
  // File management
  selectedFile: any;
  recordingTime: number;
  playbackTime: number;
  
  // Cache and offline
  cachedResults: TranscriptionResult[];
  offlineQueueSize: number;
}

interface UseWhisperAdvancedActions {
  // Transcription actions
  transcribeAudio: (file: any, customConfig?: Partial<WhisperConfig>) => Promise<void>;
  detectLanguage: (file: any) => Promise<void>;
  batchTranscribe: (files: any[]) => Promise<void>;
  
  // Recording actions
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  
  // Playback actions
  playAudio: (file: any) => Promise<void>;
  pauseAudio: () => Promise<void>;
  seekAudio: (position: number) => Promise<void>;
  
  // File management
  selectFile: (file: any) => void;
  clearFile: () => void;
  
  // Configuration
  updateConfig: (newConfig: Partial<WhisperConfig>) => Promise<void>;
  resetConfig: () => Promise<void>;
  loadPreset: (presetName: string) => Promise<void>;
  
  // Error handling
  clearError: () => void;
  retryLastOperation: () => Promise<void>;
  
  // Cache management
  clearCache: () => Promise<void>;
  loadCachedResults: () => Promise<void>;
  exportResult: (result: TranscriptionResult, format: string) => Promise<string>;
  
  // Offline support
  processOfflineQueue: () => Promise<void>;
  getOfflineQueueStatus: () => Promise<number>;
}

const DEFAULT_CONFIG: WhisperConfig = {
  model: 'whisper-1',
  language: undefined,
  temperature: 0.0,
  enable_language_detection: true,
  enable_confidence_analysis: true,
  enable_word_timestamps: true,
  enable_speaker_detection: false,
  confidence_threshold: 0.8,
};

const STORAGE_KEYS = {
  CONFIG: 'whisper_config',
  LAST_OPERATION: 'whisper_last_operation',
  PREFERENCES: 'whisper_preferences',
};

export const useWhisperAdvanced = (): [UseWhisperAdvancedState, UseWhisperAdvancedActions] => {
  // State management
  const [state, setState] = useState<UseWhisperAdvancedState>({
    isTranscribing: false,
    isDetectingLanguage: false,
    isRecording: false,
    isPlaying: false,
    result: null,
    languageResult: null,
    error: null,
    progress: 0,
    config: DEFAULT_CONFIG,
    isOnline: true,
    isAppActive: true,
    selectedFile: null,
    recordingTime: 0,
    playbackTime: 0,
    cachedResults: [],
    offlineQueueSize: 0,
  });

  // Refs for cleanup and persistence
  const lastOperationRef = useRef<any>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const playbackTimerRef = useRef<NodeJS.Timeout | null>(null);
  const appStateRef = useRef<AppStateStatus>('active');

  // Update state helper
  const updateState = useCallback((updates: Partial<UseWhisperAdvancedState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Initialize hook
  useEffect(() => {
    initializeHook();
    setupNetworkListener();
    setupAppStateListener();
    
    return cleanup;
  }, []);

  // Auto-save configuration changes
  useEffect(() => {
    saveConfig(state.config);
  }, [state.config]);

  // Background processing when app becomes active
  useEffect(() => {
    if (state.isAppActive && state.isOnline) {
      processOfflineQueue();
    }
  }, [state.isAppActive, state.isOnline]);

  // Initialize hook with saved data
  const initializeHook = async () => {
    try {
      // Load saved configuration
      const savedConfig = await AsyncStorage.getItem(STORAGE_KEYS.CONFIG);
      if (savedConfig) {
        const config = JSON.parse(savedConfig);
        updateState({ config: { ...DEFAULT_CONFIG, ...config } });
      }

      // Load cached results
      await loadCachedResults();
      
      // Check offline queue size
      const queueSize = await getOfflineQueueStatus();
      updateState({ offlineQueueSize: queueSize });

      // Check network status
      const netInfo = await NetInfo.fetch();
      updateState({ isOnline: netInfo.isConnected ?? false });

    } catch (error) {
      console.error('Failed to initialize hook:', error);
    }
  };

  // Setup network status listener
  const setupNetworkListener = () => {
    const unsubscribe = NetInfo.addEventListener(state => {
      const isOnline = state.isConnected ?? false;
      updateState({ isOnline });
      
      if (isOnline) {
        // Process offline queue when coming back online
        processOfflineQueue();
      }
    });

    return unsubscribe;
  };

  // Setup app state listener
  const setupAppStateListener = () => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      const isAppActive = nextAppState === 'active';
      updateState({ isAppActive });
      appStateRef.current = nextAppState;

      if (nextAppState === 'background') {
        // Start background processing if needed
        startBackgroundProcessing();
      } else if (nextAppState === 'active') {
        // Stop background processing
        stopBackgroundProcessing();
      }
    };

    AppState.addEventListener('change', handleAppStateChange);
    
    return () => {
      AppState.removeEventListener('change', handleAppStateChange);
    };
  };

  // Cleanup function
  const cleanup = () => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }
    if (playbackTimerRef.current) {
      clearInterval(playbackTimerRef.current);
    }
    stopBackgroundProcessing();
  };

  // Background processing
  const startBackgroundProcessing = () => {
    if (state.offlineQueueSize > 0) {
      BackgroundJob.start({
        jobKey: 'whisperProcessing',
        period: 30000, // Check every 30 seconds
      });
    }
  };

  const stopBackgroundProcessing = () => {
    BackgroundJob.stop({
      jobKey: 'whisperProcessing',
    });
  };

  // Save configuration
  const saveConfig = async (config: WhisperConfig) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.CONFIG, JSON.stringify(config));
    } catch (error) {
      console.error('Failed to save config:', error);
    }
  };

  // Save last operation for retry
  const saveLastOperation = async (operation: any) => {
    try {
      lastOperationRef.current = operation;
      await AsyncStorage.setItem(STORAGE_KEYS.LAST_OPERATION, JSON.stringify(operation));
    } catch (error) {
      console.error('Failed to save last operation:', error);
    }
  };

  // Actions implementation
  const actions: UseWhisperAdvancedActions = {
    // Transcription actions
    transcribeAudio: async (file: any, customConfig?: Partial<WhisperConfig>) => {
      const finalConfig = { ...state.config, ...customConfig };
      
      updateState({ 
        isTranscribing: true, 
        error: null, 
        progress: 0,
        selectedFile: file 
      });

      await saveLastOperation({
        type: 'transcribe',
        file,
        config: finalConfig,
      });

      try {
        const result = await whisperAPI.transcribeAudio(
          file,
          finalConfig,
          undefined,
          undefined,
          (progress) => updateState({ progress })
        );

        updateState({ 
          result, 
          isTranscribing: false, 
          progress: 100 
        });

        // Show success notification
        Alert.alert('Success', 'Transcription completed successfully');

      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Transcription failed';
        updateState({ 
          error: errorMessage, 
          isTranscribing: false, 
          progress: 0 
        });

        // Show error alert with retry option
        Alert.alert(
          'Transcription Failed',
          errorMessage,
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Retry', onPress: () => actions.retryLastOperation() },
          ]
        );
      }
    },

    detectLanguage: async (file: any) => {
      updateState({ 
        isDetectingLanguage: true, 
        error: null,
        selectedFile: file 
      });

      await saveLastOperation({
        type: 'detectLanguage',
        file,
      });

      try {
        const result = await whisperAPI.detectLanguage(
          file,
          (progress) => updateState({ progress })
        );

        updateState({ 
          languageResult: result, 
          isDetectingLanguage: false 
        });

      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Language detection failed';
        updateState({ 
          error: errorMessage, 
          isDetectingLanguage: false 
        });

        Alert.alert('Detection Failed', errorMessage);
      }
    },

    batchTranscribe: async (files: any[]) => {
      if (files.length === 0) {
        Alert.alert('No Files', 'Please select files to transcribe');
        return;
      }

      if (files.length > 10) {
        Alert.alert('Too Many Files', 'Maximum 10 files allowed for batch processing');
        return;
      }

      updateState({ 
        isTranscribing: true, 
        error: null, 
        progress: 0 
      });

      try {
        const result = await whisperAPI.batchTranscribe(
          files,
          state.config,
          (progress) => updateState({ progress })
        );

        updateState({ 
          isTranscribing: false, 
          progress: 100 
        });

        Alert.alert(
          'Batch Complete',
          `Processed ${result.summary.successful}/${result.summary.total_files} files successfully`
        );

      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Batch processing failed';
        updateState({ 
          error: errorMessage, 
          isTranscribing: false 
        });

        Alert.alert('Batch Failed', errorMessage);
      }
    },

    // Recording actions
    startRecording: async () => {
      updateState({ 
        isRecording: true, 
        recordingTime: 0, 
        error: null 
      });

      recordingTimerRef.current = setInterval(() => {
        updateState(prev => ({ 
          ...prev, 
          recordingTime: prev.recordingTime + 1 
        }));
      }, 1000);
    },

    stopRecording: async () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }

      updateState({ isRecording: false });
    },

    // Playback actions
    playAudio: async (file: any) => {
      updateState({ 
        isPlaying: true, 
        playbackTime: 0,
        selectedFile: file 
      });

      playbackTimerRef.current = setInterval(() => {
        updateState(prev => ({ 
          ...prev, 
          playbackTime: prev.playbackTime + 1 
        }));
      }, 1000);
    },

    pauseAudio: async () => {
      if (playbackTimerRef.current) {
        clearInterval(playbackTimerRef.current);
      }

      updateState({ isPlaying: false });
    },

    seekAudio: async (position: number) => {
      updateState({ playbackTime: position });
    },

    // File management
    selectFile: (file: any) => {
      updateState({ 
        selectedFile: file, 
        error: null,
        result: null,
        languageResult: null 
      });
    },

    clearFile: () => {
      updateState({ 
        selectedFile: null,
        result: null,
        languageResult: null,
        error: null 
      });
    },

    // Configuration
    updateConfig: async (newConfig: Partial<WhisperConfig>) => {
      const updatedConfig = { ...state.config, ...newConfig };
      updateState({ config: updatedConfig });
    },

    resetConfig: async () => {
      updateState({ config: DEFAULT_CONFIG });
    },

    loadPreset: async (presetName: string) => {
      try {
        const presets = await whisperAPI.getPresets();
        const preset = presets.presets.find((p: any) => p.name === presetName);
        
        if (preset) {
          updateState({ config: { ...DEFAULT_CONFIG, ...preset.config } });
        }
      } catch (error) {
        console.error('Failed to load preset:', error);
      }
    },

    // Error handling
    clearError: () => {
      updateState({ error: null });
    },

    retryLastOperation: async () => {
      const lastOp = lastOperationRef.current;
      if (!lastOp) return;

      switch (lastOp.type) {
        case 'transcribe':
          await actions.transcribeAudio(lastOp.file, lastOp.config);
          break;
        case 'detectLanguage':
          await actions.detectLanguage(lastOp.file);
          break;
        default:
          console.warn('Unknown operation type for retry:', lastOp.type);
      }
    },

    // Cache management
    clearCache: async () => {
      try {
        await whisperAPI.clearCache();
        updateState({ cachedResults: [] });
        Alert.alert('Cache Cleared', 'All cached data has been removed');
      } catch (error) {
        console.error('Failed to clear cache:', error);
      }
    },

    loadCachedResults: async () => {
      try {
        const cached = await whisperAPI.getCachedTranscriptions();
        updateState({ cachedResults: cached });
      } catch (error) {
        console.error('Failed to load cached results:', error);
      }
    },

    exportResult: async (result: TranscriptionResult, format: string) => {
      try {
        return await whisperAPI.exportTranscription(result, format as any);
      } catch (error) {
        console.error('Failed to export result:', error);
        throw error;
      }
    },

    // Offline support
    processOfflineQueue: async () => {
      try {
        await whisperAPI.processOfflineQueue();
        const queueSize = await getOfflineQueueStatus();
        updateState({ offlineQueueSize: queueSize });
      } catch (error) {
        console.error('Failed to process offline queue:', error);
      }
    },

    getOfflineQueueStatus: async () => {
      return await getOfflineQueueStatus();
    },
  };

  // Helper function for offline queue status
  const getOfflineQueueStatus = async (): Promise<number> => {
    try {
      // This would need to be implemented in the API
      return 0; // Placeholder
    } catch (error) {
      console.error('Failed to get offline queue status:', error);
      return 0;
    }
  };

  const loadCachedResults = async () => {
    try {
      const cached = await whisperAPI.getCachedTranscriptions();
      updateState({ cachedResults: cached });
    } catch (error) {
      console.error('Failed to load cached results:', error);
    }
  };

  const processOfflineQueue = async () => {
    try {
      await whisperAPI.processOfflineQueue();
      const queueSize = await getOfflineQueueStatus();
      updateState({ offlineQueueSize: queueSize });
    } catch (error) {
      console.error('Failed to process offline queue:', error);
    }
  };

  return [state, actions];
};

export default useWhisperAdvanced;