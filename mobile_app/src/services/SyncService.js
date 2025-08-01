import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-netinfo/netinfo';
import axios from 'axios';
import { Platform } from 'react-native';

class SyncService {
  constructor() {
    this.syncQueue = [];
    this.isOnline = true;
    this.lastSyncTime = null;
    this.syncInProgress = false;
    this.baseURL = __DEV__ 
      ? 'http://localhost:8000'
      : 'https://your-api-server.com';

    this.setupNetworkListener();
  }

  setupNetworkListener() {
    NetInfo.addEventListener(state => {
      const wasOnline = this.isOnline;
      this.isOnline = state.isConnected && state.isInternetReachable;
      
      if (!wasOnline && this.isOnline) {
        // Just came back online, trigger sync
        this.performFullSync();
      }
    });
  }

  async checkConnectivity() {
    const netInfo = await NetInfo.fetch();
    this.isOnline = netInfo.isConnected && netInfo.isInternetReachable;
    
    return {
      isConnected: this.isOnline,
      connectionType: netInfo.type,
      isWiFi: netInfo.type === 'wifi',
      isCellular: netInfo.type === 'cellular',
    };
  }

  async syncWithServer() {
    if (!this.isOnline || this.syncInProgress) {
      return { success: false, reason: 'offline_or_in_progress' };
    }

    this.syncInProgress = true;
    
    try {
      console.log('🔄 Starting sync with server...');
      
      // Get device info for sync
      const deviceInfo = await this.getDeviceInfo();
      const lastSync = await AsyncStorage.getItem('lastSyncTime');
      
      // Sync transcriptions
      await this.syncTranscriptions(lastSync);
      
      // Sync customizations (vocabularies, voice profiles, etc.)
      await this.syncCustomizations(lastSync);
      
      // Sync user settings
      await this.syncUserSettings(lastSync);
      
      // Update sync timestamp
      const now = new Date().toISOString();
      await AsyncStorage.setItem('lastSyncTime', now);
      this.lastSyncTime = now;
      
      console.log('✅ Sync completed successfully');
      
      return { 
        success: true, 
        syncTime: now,
        itemsSynced: this.syncQueue.length 
      };
      
    } catch (error) {
      console.error('❌ Sync failed:', error);
      return { 
        success: false, 
        error: error.message 
      };
    } finally {
      this.syncInProgress = false;
      this.syncQueue = [];
    }
  }

  async syncTranscriptions(lastSync) {
    try {
      // Upload pending transcriptions
      const pendingUploads = await AsyncStorage.getItem('pendingUploads');
      if (pendingUploads) {
        const uploads = JSON.parse(pendingUploads);
        
        for (const upload of uploads) {
          try {
            await this.uploadTranscription(upload);
            this.syncQueue.push({ type: 'transcription_upload', id: upload.id });
          } catch (error) {
            console.warn(`Failed to upload transcription ${upload.id}:`, error);
          }
        }
        
        // Clear successful uploads
        await AsyncStorage.removeItem('pendingUploads');
      }

      // Download new transcriptions from server
      const response = await axios.get(`${this.baseURL}/api/sync/transcriptions`, {
        params: { 
          since: lastSync,
          device_id: await this.getDeviceId()
        },
        headers: await this.getAuthHeaders()
      });

      const { transcriptions } = response.data;
      
      for (const transcription of transcriptions) {
        await this.cacheTranscription(transcription);
        this.syncQueue.push({ type: 'transcription_download', id: transcription.id });
      }

    } catch (error) {
      console.error('Transcription sync failed:', error);
      throw error;
    }
  }

  async syncCustomizations(lastSync) {
    try {
      // Upload local customizations
      const localCustomizations = await AsyncStorage.getItem('localCustomizations');
      if (localCustomizations) {
        const customizations = JSON.parse(localCustomizations);
        
        const response = await axios.post(
          `${this.baseURL}/api/sync/customizations`,
          {
            customizations,
            device_id: await this.getDeviceId(),
            platform: Platform.OS
          },
          { headers: await this.getAuthHeaders() }
        );

        // Clear uploaded customizations
        await AsyncStorage.removeItem('localCustomizations');
        this.syncQueue.push({ type: 'customizations_upload', count: customizations.length });
      }

      // Download server customizations
      const response = await axios.get(`${this.baseURL}/api/sync/customizations`, {
        params: { 
          since: lastSync,
          device_id: await this.getDeviceId()
        },
        headers: await this.getAuthHeaders()
      });

      const { vocabularies, voiceProfiles, entityTypes } = response.data;
      
      // Store downloaded customizations
      if (vocabularies?.length > 0) {
        await AsyncStorage.setItem('syncedVocabularies', JSON.stringify(vocabularies));
        this.syncQueue.push({ type: 'vocabularies_download', count: vocabularies.length });
      }
      
      if (voiceProfiles?.length > 0) {
        await AsyncStorage.setItem('syncedVoiceProfiles', JSON.stringify(voiceProfiles));
        this.syncQueue.push({ type: 'voice_profiles_download', count: voiceProfiles.length });
      }
      
      if (entityTypes?.length > 0) {
        await AsyncStorage.setItem('syncedEntityTypes', JSON.stringify(entityTypes));
        this.syncQueue.push({ type: 'entity_types_download', count: entityTypes.length });
      }

    } catch (error) {
      console.error('Customizations sync failed:', error);
      throw error;
    }
  }

  async syncUserSettings(lastSync) {
    try {
      // Get local settings
      const localSettings = await AsyncStorage.getItem('userSettings');
      
      if (localSettings) {
        const settings = JSON.parse(localSettings);
        
        // Upload settings if modified since last sync
        if (!lastSync || new Date(settings.modified_at) > new Date(lastSync)) {
          await axios.post(
            `${this.baseURL}/api/sync/settings`,
            {
              settings,
              device_id: await this.getDeviceId()
            },
            { headers: await this.getAuthHeaders() }
          );
          
          this.syncQueue.push({ type: 'settings_upload' });
        }
      }

      // Download server settings
      const response = await axios.get(`${this.baseURL}/api/sync/settings`, {
        params: { 
          since: lastSync,
          device_id: await this.getDeviceId()
        },
        headers: await this.getAuthHeaders()
      });

      const { settings } = response.data;
      
      if (settings) {
        await AsyncStorage.setItem('syncedUserSettings', JSON.stringify(settings));
        this.syncQueue.push({ type: 'settings_download' });
      }

    } catch (error) {
      console.error('Settings sync failed:', error);
      throw error;
    }
  }

  async performFullSync() {
    if (!this.isOnline) {
      console.log('📴 Offline - skipping sync');
      return;
    }

    console.log('🔄 Performing full sync...');
    return await this.syncWithServer();
  }

  async queueForSync(item) {
    try {
      const queue = await AsyncStorage.getItem('syncQueue');
      const currentQueue = queue ? JSON.parse(queue) : [];
      
      currentQueue.push({
        ...item,
        queued_at: new Date().toISOString(),
        id: Date.now().toString()
      });
      
      await AsyncStorage.setItem('syncQueue', JSON.stringify(currentQueue));
      
      // Try to sync if online
      if (this.isOnline) {
        setTimeout(() => this.performFullSync(), 1000);
      }
      
    } catch (error) {
      console.error('Failed to queue item for sync:', error);
    }
  }

  async uploadTranscription(transcription) {
    const formData = new FormData();
    formData.append('transcription', JSON.stringify(transcription));
    formData.append('device_id', await this.getDeviceId());
    
    if (transcription.audio_file) {
      formData.append('audio_file', {
        uri: transcription.audio_file,
        type: 'audio/wav',
        name: 'transcription.wav'
      });
    }

    const response = await axios.post(
      `${this.baseURL}/api/sync/upload-transcription`,
      formData,
      {
        headers: {
          ...await this.getAuthHeaders(),
          'Content-Type': 'multipart/form-data'
        }
      }
    );

    return response.data;
  }

  async cacheTranscription(transcription) {
    const cacheKey = `transcription_${transcription.id}`;
    const cacheData = {
      ...transcription,
      cached_at: new Date().toISOString(),
      synced: true
    };

    await AsyncStorage.setItem(cacheKey, JSON.stringify(cacheData));
    
    // Update cache index
    const index = await AsyncStorage.getItem('transcription_cache_index');
    const cacheIndex = index ? JSON.parse(index) : [];
    
    if (!cacheIndex.includes(cacheKey)) {
      cacheIndex.push(cacheKey);
      await AsyncStorage.setItem('transcription_cache_index', JSON.stringify(cacheIndex));
    }
  }

  async getDeviceInfo() {
    return {
      platform: Platform.OS,
      version: Platform.Version,
      device_id: await this.getDeviceId(),
      app_version: '1.0.0', // Should be dynamic
      sync_version: '1.0'
    };
  }

  async getDeviceId() {
    let deviceId = await AsyncStorage.getItem('deviceId');
    
    if (!deviceId) {
      // Generate unique device ID
      deviceId = `${Platform.OS}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      await AsyncStorage.setItem('deviceId', deviceId);
    }
    
    return deviceId;
  }

  async getAuthHeaders() {
    const token = await AsyncStorage.getItem('authToken');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async getSyncStatus() {
    const lastSync = await AsyncStorage.getItem('lastSyncTime');
    const pendingItems = await AsyncStorage.getItem('syncQueue');
    const pendingCount = pendingItems ? JSON.parse(pendingItems).length : 0;
    
    return {
      lastSyncTime: lastSync,
      isOnline: this.isOnline,
      syncInProgress: this.syncInProgress,
      pendingItems: pendingCount,
      canSync: this.isOnline && !this.syncInProgress
    };
  }

  async clearSyncData() {
    const keys = [
      'lastSyncTime',
      'syncQueue',
      'pendingUploads',
      'localCustomizations',
      'syncedVocabularies',
      'syncedVoiceProfiles',
      'syncedEntityTypes',
      'syncedUserSettings'
    ];
    
    await AsyncStorage.multiRemove(keys);
    this.lastSyncTime = null;
    this.syncQueue = [];
  }

  // Cross-platform data sharing
  async exportSyncData() {
    try {
      const syncData = {
        transcriptions: await this.getTranscriptionData(),
        customizations: await this.getCustomizationData(),
        settings: await this.getUserSettings(),
        exported_at: new Date().toISOString(),
        device_info: await this.getDeviceInfo()
      };

      return JSON.stringify(syncData, null, 2);
      
    } catch (error) {
      console.error('Failed to export sync data:', error);
      throw error;
    }
  }

  async importSyncData(syncDataString) {
    try {
      const syncData = JSON.parse(syncDataString);
      
      // Validate data structure
      if (!syncData.exported_at || !syncData.device_info) {
        throw new Error('Invalid sync data format');
      }

      // Import transcriptions
      if (syncData.transcriptions) {
        for (const transcription of syncData.transcriptions) {
          await this.cacheTranscription(transcription);
        }
      }

      // Import customizations
      if (syncData.customizations) {
        await AsyncStorage.setItem('importedCustomizations', JSON.stringify(syncData.customizations));
      }

      // Import settings
      if (syncData.settings) {
        await AsyncStorage.setItem('importedSettings', JSON.stringify(syncData.settings));
      }

      console.log('✅ Sync data imported successfully');
      return { success: true, imported_at: new Date().toISOString() };
      
    } catch (error) {
      console.error('Failed to import sync data:', error);
      throw error;
    }
  }

  async getTranscriptionData() {
    const index = await AsyncStorage.getItem('transcription_cache_index');
    if (!index) return [];

    const transcriptions = [];
    const keys = JSON.parse(index);

    for (const key of keys) {
      const data = await AsyncStorage.getItem(key);
      if (data) {
        transcriptions.push(JSON.parse(data));
      }
    }

    return transcriptions;
  }

  async getCustomizationData() {
    const customizations = {};
    
    const vocabularies = await AsyncStorage.getItem('syncedVocabularies');
    if (vocabularies) {
      customizations.vocabularies = JSON.parse(vocabularies);
    }

    const voiceProfiles = await AsyncStorage.getItem('syncedVoiceProfiles');
    if (voiceProfiles) {
      customizations.voiceProfiles = JSON.parse(voiceProfiles);
    }

    const entityTypes = await AsyncStorage.getItem('syncedEntityTypes');
    if (entityTypes) {
      customizations.entityTypes = JSON.parse(entityTypes);
    }

    return customizations;
  }

  async getUserSettings() {
    const settings = await AsyncStorage.getItem('syncedUserSettings');
    return settings ? JSON.parse(settings) : null;
  }
}

export default new SyncService();