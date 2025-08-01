import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-netinfo/netinfo';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import { Alert } from 'react-native';

class OfflineManager {
  constructor() {
    this.isOfflineMode = false;
    this.offlineCapabilities = {
      basicTranscription: false,
      voiceRecognition: false,
      textProcessing: true,
      fileStorage: true,
    };
    this.offlineQueue = [];
    this.maxOfflineStorage = 500 * 1024 * 1024; // 500MB
    this.offlineModels = {};
    
    this.initializeOfflineMode();
  }

  async initializeOfflineMode() {
    try {
      // Check if offline mode was previously enabled
      const offlineEnabled = await AsyncStorage.getItem('offlineMode');
      if (offlineEnabled === 'true') {
        await this.enableOfflineMode();
      }
      
      // Monitor network connectivity
      this.setupNetworkMonitoring();
      
      // Load offline queue
      await this.loadOfflineQueue();
      
    } catch (error) {
      console.error('Failed to initialize offline mode:', error);
    }
  }

  setupNetworkMonitoring() {
    NetInfo.addEventListener(state => {
      const wasOffline = !state.isConnected || !state.isInternetReachable;
      
      if (wasOffline && !this.isOfflineMode) {
        // Went offline
        this.handleNetworkDisconnected();
      } else if (!wasOffline && this.isOfflineMode) {
        // Came back online
        this.handleNetworkReconnected();
      }
    });
  }

  async handleNetworkDisconnected() {
    console.log('📴 Network disconnected - switching to offline mode');
    
    // Check if offline capabilities are available
    const hasOfflineCapabilities = await this.checkOfflineCapabilities();
    
    if (hasOfflineCapabilities) {
      this.isOfflineMode = true;
      Alert.alert(
        'Offline Mode',
        'Network disconnected. You can continue using basic features offline.',
        [{ text: 'OK' }]
      );
    } else {
      Alert.alert(
        'Network Required',
        'No network connection. Some features may not be available.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Enable Offline Mode', onPress: () => this.promptEnableOfflineMode() }
        ]
      );
    }
  }

  async handleNetworkReconnected() {
    console.log('🌐 Network reconnected - syncing offline data');
    
    this.isOfflineMode = false;
    
    // Process offline queue
    await this.processOfflineQueue();
    
    Alert.alert(
      'Back Online',
      'Network connection restored. Syncing your offline data.',
      [{ text: 'OK' }]
    );
  }

  async enableOfflineMode() {
    try {
      console.log('⚡ Enabling offline mode...');
      
      // Set offline mode flag
      this.isOfflineMode = true;
      await AsyncStorage.setItem('offlineMode', 'true');
      
      // Initialize offline storage
      await this.setupOfflineStorage();
      
      // Download basic models (if available)
      await this.downloadOfflineModels();
      
      // Update capabilities
      await this.updateOfflineCapabilities();
      
      console.log('✅ Offline mode enabled');
      return { success: true };
      
    } catch (error) {
      console.error('Failed to enable offline mode:', error);
      return { success: false, error: error.message };
    }
  }

  async disableOfflineMode() {
    try {
      console.log('📱 Disabling offline mode...');
      
      this.isOfflineMode = false;
      await AsyncStorage.setItem('offlineMode', 'false');
      
      // Clear offline models to save space
      await this.clearOfflineModels();
      
      console.log('✅ Offline mode disabled');
      return { success: true };
      
    } catch (error) {
      console.error('Failed to disable offline mode:', error);
      return { success: false, error: error.message };
    }
  }

  async setupOfflineStorage() {
    try {
      const offlineDir = `${FileSystem.documentDirectory}offline/`;
      
      // Create offline storage directories
      const directories = ['audio', 'transcripts', 'models', 'cache'];
      
      for (const dir of directories) {
        const dirPath = `${offlineDir}${dir}/`;
        const dirInfo = await FileSystem.getInfoAsync(dirPath);
        
        if (!dirInfo.exists) {
          await FileSystem.makeDirectoryAsync(dirPath, { intermediates: true });
        }
      }
      
      console.log('📁 Offline storage setup complete');
      
    } catch (error) {
      console.error('Failed to setup offline storage:', error);
      throw error;
    }
  }

  async downloadOfflineModels() {
    // In a real implementation, this would download lightweight
    // speech recognition or transcription models for offline use
    console.log('📥 Downloading offline models...');
    
    try {
      // Mock offline model download
      const models = {
        basicTranscription: {
          name: 'Basic Transcription Model',
          size: 50 * 1024 * 1024, // 50MB
          url: 'https://example.com/basic-model.bin',
          capabilities: ['speech-to-text', 'basic-language-detection']
        },
        textProcessing: {
          name: 'Text Processing Model',
          size: 10 * 1024 * 1024, // 10MB
          url: 'https://example.com/text-model.bin',
          capabilities: ['text-analysis', 'keyword-extraction']
        }
      };
      
      // Check available storage
      const availableStorage = await this.getAvailableStorage();
      const requiredStorage = Object.values(models).reduce((sum, model) => sum + model.size, 0);
      
      if (availableStorage < requiredStorage) {
        throw new Error('Insufficient storage for offline models');
      }
      
      // In a real app, download and store models
      // For now, just mark as available
      this.offlineModels = models;
      await AsyncStorage.setItem('offlineModels', JSON.stringify(models));
      
      console.log('✅ Offline models ready');
      
    } catch (error) {
      console.warn('Failed to download offline models:', error);
      // Continue without offline models
    }
  }

  async updateOfflineCapabilities() {
    try {
      // Check what offline capabilities are actually available
      const capabilities = {
        basicTranscription: !!this.offlineModels.basicTranscription,
        voiceRecognition: false, // Requires special implementation
        textProcessing: !!this.offlineModels.textProcessing,
        fileStorage: true,
        audioPlayback: true,
        recordingAnalysis: true,
      };
      
      this.offlineCapabilities = capabilities;
      await AsyncStorage.setItem('offlineCapabilities', JSON.stringify(capabilities));
      
      console.log('🔄 Offline capabilities updated:', capabilities);
      
    } catch (error) {
      console.error('Failed to update offline capabilities:', error);
    }
  }

  async checkOfflineCapabilities() {
    try {
      const stored = await AsyncStorage.getItem('offlineCapabilities');
      if (stored) {
        this.offlineCapabilities = JSON.parse(stored);
      }
      
      // Check if we have basic offline functionality
      return this.offlineCapabilities.textProcessing || 
             this.offlineCapabilities.fileStorage ||
             this.offlineCapabilities.basicTranscription;
             
    } catch (error) {
      console.error('Failed to check offline capabilities:', error);
      return false;
    }
  }

  async processOffline(operation, data) {
    if (!this.isOfflineMode) {
      throw new Error('Not in offline mode');
    }
    
    console.log('⚡ Processing offline operation:', operation);
    
    switch (operation) {
      case 'transcribe_audio':
        return await this.offlineTranscribeAudio(data);
      
      case 'analyze_text':
        return await this.offlineAnalyzeText(data);
      
      case 'store_recording':
        return await this.offlineStoreRecording(data);
      
      case 'process_recording':
        return await this.offlineProcessRecording(data);
      
      default:
        throw new Error(`Unsupported offline operation: ${operation}`);
    }
  }

  async offlineTranscribeAudio(audioData) {
    try {
      // In a real implementation, this would use local speech recognition
      console.log('🎙️ Offline audio transcription (simulated)');
      
      // For now, return a placeholder result
      const result = {
        transcript: '[Offline transcription - full processing available when online]',
        confidence: 0.8,
        duration: audioData.duration || 0,
        segments: [{
          text: '[Offline transcription - full processing available when online]',
          start_time: 0,
          end_time: audioData.duration || 0,
          confidence: 0.8
        }],
        processed_offline: true,
        requires_online_processing: true
      };
      
      // Queue for full processing when online
      await this.queueForOnlineProcessing('full_transcription', audioData, result);
      
      return result;
      
    } catch (error) {
      console.error('Offline transcription failed:', error);
      throw error;
    }
  }

  async offlineAnalyzeText(textData) {
    try {
      console.log('📝 Offline text analysis');
      
      // Basic text processing that can be done offline
      const text = textData.text || '';
      const words = text.split(/\s+/).filter(word => word.length > 0);
      const sentences = text.split(/[.!?]+/).filter(sent => sent.trim().length > 0);
      
      // Simple keyword extraction
      const keywords = this.extractKeywords(text);
      
      // Basic stats
      const stats = {
        word_count: words.length,
        sentence_count: sentences.length,
        character_count: text.length,
        average_word_length: words.reduce((sum, word) => sum + word.length, 0) / words.length || 0,
        reading_time: Math.ceil(words.length / 200) // Assume 200 WPM
      };
      
      return {
        keywords,
        stats,
        processed_offline: true,
        full_analysis_pending: true
      };
      
    } catch (error) {
      console.error('Offline text analysis failed:', error);
      throw error;
    }
  }

  async offlineStoreRecording(recordingData) {
    try {
      console.log('💾 Storing recording offline');
      
      const { uri, filename, metadata } = recordingData;
      const offlineDir = `${FileSystem.documentDirectory}offline/audio/`;
      const newFilename = filename || `recording_${Date.now()}.m4a`;
      const newPath = `${offlineDir}${newFilename}`;
      
      // Copy file to offline storage
      await FileSystem.copyAsync({
        from: uri,
        to: newPath
      });
      
      // Store metadata
      const recordingInfo = {
        id: `offline_${Date.now()}`,
        filename: newFilename,
        path: newPath,
        size: metadata?.size || 0,
        duration: metadata?.duration || 0,
        created_at: new Date().toISOString(),
        stored_offline: true,
        sync_pending: true
      };
      
      // Add to offline recordings index
      const offlineRecordings = await this.getOfflineRecordings();
      offlineRecordings.push(recordingInfo);
      await AsyncStorage.setItem('offlineRecordings', JSON.stringify(offlineRecordings));
      
      // Queue for sync when online
      await this.queueForOnlineProcessing('sync_recording', recordingInfo);
      
      return recordingInfo;
      
    } catch (error) {
      console.error('Failed to store recording offline:', error);
      throw error;
    }
  }

  async offlineProcessRecording(recordingData) {
    try {
      console.log('🔄 Processing recording offline');
      
      // Basic processing that can be done offline
      const { path, metadata } = recordingData;
      
      // Get audio file info
      const fileInfo = await FileSystem.getInfoAsync(path);
      
      if (!fileInfo.exists) {
        throw new Error('Recording file not found');
      }
      
      // Basic audio analysis (duration, size, etc.)
      const analysis = {
        file_size: fileInfo.size,
        estimated_duration: metadata?.duration || 0,
        format: path.split('.').pop()?.toLowerCase() || 'unknown',
        processed_at: new Date().toISOString(),
        processing_type: 'offline_basic'
      };
      
      // If we have offline transcription capability, use it
      if (this.offlineCapabilities.basicTranscription) {
        const transcription = await this.offlineTranscribeAudio({
          path,
          duration: analysis.estimated_duration
        });
        analysis.transcription = transcription;
      }
      
      return analysis;
      
    } catch (error) {
      console.error('Offline recording processing failed:', error);
      throw error;
    }
  }

  extractKeywords(text) {
    // Simple keyword extraction
    const words = text.toLowerCase()
      .replace(/[^\w\s]/g, '')
      .split(/\s+/)
      .filter(word => word.length > 3);
    
    // Count word frequency
    const frequency = {};
    words.forEach(word => {
      frequency[word] = (frequency[word] || 0) + 1;
    });
    
    // Get top keywords
    return Object.entries(frequency)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([word, count]) => ({ word, count }));
  }

  async queueForOnlineProcessing(operation, data, partialResult = null) {
    try {
      const queueItem = {
        id: `queue_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        operation,
        data,
        partial_result: partialResult,
        created_at: new Date().toISOString(),
        attempts: 0,
        max_attempts: 3
      };
      
      this.offlineQueue.push(queueItem);
      await this.saveOfflineQueue();
      
      console.log('📝 Queued for online processing:', operation);
      
    } catch (error) {
      console.error('Failed to queue for online processing:', error);
    }
  }

  async processOfflineQueue() {
    if (this.offlineQueue.length === 0) {
      console.log('📭 No offline queue items to process');
      return;
    }
    
    console.log(`🔄 Processing ${this.offlineQueue.length} offline queue items`);
    
    const results = {
      processed: 0,
      failed: 0,
      errors: []
    };
    
    for (const item of [...this.offlineQueue]) {
      try {
        await this.processQueueItem(item);
        
        // Remove from queue on success
        this.offlineQueue = this.offlineQueue.filter(qi => qi.id !== item.id);
        results.processed++;
        
      } catch (error) {
        console.error(`Failed to process queue item ${item.id}:`, error);
        
        item.attempts++;
        item.last_error = error.message;
        
        if (item.attempts >= item.max_attempts) {
          // Remove failed items after max attempts
          this.offlineQueue = this.offlineQueue.filter(qi => qi.id !== item.id);
          results.failed++;
          results.errors.push({
            operation: item.operation,
            error: error.message
          });
        }
      }
    }
    
    await this.saveOfflineQueue();
    
    console.log('✅ Offline queue processing complete:', results);
    return results;
  }

  async processQueueItem(item) {
    switch (item.operation) {
      case 'full_transcription':
        // Re-process audio with full online capabilities
        return await this.processFullTranscription(item.data);
      
      case 'sync_recording':
        // Sync recording to server
        return await this.syncRecording(item.data);
      
      default:
        console.warn(`Unknown queue operation: ${item.operation}`);
    }
  }

  async processFullTranscription(audioData) {
    // This would use the full online transcription service
    console.log('🔄 Processing full transcription online');
    // Implementation would depend on the main TranscriptionService
  }

  async syncRecording(recordingInfo) {
    // This would sync the recording to the server
    console.log('🔄 Syncing recording to server');
    // Implementation would depend on the SyncService
  }

  async getOfflineRecordings() {
    try {
      const stored = await AsyncStorage.getItem('offlineRecordings');
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('Failed to get offline recordings:', error);
      return [];
    }
  }

  async loadOfflineQueue() {
    try {
      const stored = await AsyncStorage.getItem('offlineQueue');
      this.offlineQueue = stored ? JSON.parse(stored) : [];
      console.log(`📋 Loaded ${this.offlineQueue.length} offline queue items`);
    } catch (error) {
      console.error('Failed to load offline queue:', error);
      this.offlineQueue = [];
    }
  }

  async saveOfflineQueue() {
    try {
      await AsyncStorage.setItem('offlineQueue', JSON.stringify(this.offlineQueue));
    } catch (error) {
      console.error('Failed to save offline queue:', error);
    }
  }

  async getAvailableStorage() {
    try {
      const freeSpace = await FileSystem.getFreeDiskStorageAsync();
      return freeSpace;
    } catch (error) {
      console.warn('Could not get available storage:', error);
      return this.maxOfflineStorage; // Return default
    }
  }

  async clearOfflineModels() {
    try {
      const modelsDir = `${FileSystem.documentDirectory}offline/models/`;
      const modelsInfo = await FileSystem.getInfoAsync(modelsDir);
      
      if (modelsInfo.exists) {
        await FileSystem.deleteAsync(modelsDir, { idempotent: true });
        await FileSystem.makeDirectoryAsync(modelsDir, { intermediates: true });
      }
      
      this.offlineModels = {};
      await AsyncStorage.removeItem('offlineModels');
      
      console.log('🗑️ Offline models cleared');
      
    } catch (error) {
      console.error('Failed to clear offline models:', error);
    }
  }

  async getOfflineStatus() {
    return {
      isOfflineMode: this.isOfflineMode,
      capabilities: this.offlineCapabilities,
      queueSize: this.offlineQueue.length,
      modelsAvailable: Object.keys(this.offlineModels).length,
      storageUsed: await this.getOfflineStorageUsed()
    };
  }

  async getOfflineStorageUsed() {
    try {
      const offlineDir = `${FileSystem.documentDirectory}offline/`;
      const dirInfo = await FileSystem.getInfoAsync(offlineDir);
      
      if (!dirInfo.exists) {
        return 0;
      }
      
      // This would require recursive directory size calculation
      // For now, return estimate based on stored recordings
      const recordings = await this.getOfflineRecordings();
      return recordings.reduce((sum, rec) => sum + (rec.size || 0), 0);
      
    } catch (error) {
      console.warn('Could not calculate offline storage used:', error);
      return 0;
    }
  }

  async promptEnableOfflineMode() {
    Alert.alert(
      'Enable Offline Mode',
      'Download models for offline transcription? This will use about 60MB of storage.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Enable', 
          onPress: async () => {
            const result = await this.enableOfflineMode();
            if (result.success) {
              Alert.alert('Success', 'Offline mode enabled. You can now use basic features without internet.');
            } else {
              Alert.alert('Error', result.error || 'Failed to enable offline mode');
            }
          }
        }
      ]
    );
  }
}

export default new OfflineManager();