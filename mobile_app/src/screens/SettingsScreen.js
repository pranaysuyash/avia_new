import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Switch,
  Alert,
  TextInput,
  Modal,
  Dimensions,
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import SyncService from '../services/SyncService';
import OfflineManager from '../services/OfflineManager';

const { width } = Dimensions.get('window');

export default function SettingsScreen({ navigation }) {
  const [settings, setSettings] = useState({
    // Audio settings
    audioQuality: 'high',
    maxRecordingTime: 30,
    autoSave: true,
    backgroundRecording: false,
    
    // Transcription settings
    defaultAnalysisMode: 'advanced',
    autoTranscribe: true,
    speakerDiarization: true,
    timestampInterval: 5,
    
    // Sync settings
    autoSync: true,
    syncOnWifi: true,
    offlineMode: false,
    
    // UI settings
    theme: 'system',
    fontSize: 'medium',
    showTimestamps: true,
    compactMode: false,
    
    // Privacy settings
    dataRetention: 30,
    analyticsEnabled: false,
    crashReporting: true,
    
    // Notification settings
    transcriptionComplete: true,
    syncComplete: false,
    errorNotifications: true,
  });

  const [syncStatus, setSyncStatus] = useState(null);
  const [offlineStatus, setOfflineStatus] = useState(null);
  const [storageInfo, setStorageInfo] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalContent, setModalContent] = useState(null);
  const [tempValue, setTempValue] = useState('');

  useEffect(() => {
    loadSettings();
    loadStatus();
  }, []);

  const loadSettings = async () => {
    try {
      const storedSettings = await AsyncStorage.getItem('appSettings');
      if (storedSettings) {
        setSettings({ ...settings, ...JSON.parse(storedSettings) });
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const loadStatus = async () => {
    try {
      const [sync, offline] = await Promise.all([
        SyncService.getSyncStatus(),
        OfflineManager.getOfflineStatus()
      ]);
      
      setSyncStatus(sync);
      setOfflineStatus(offline);
      
      // Get storage info
      const storage = await OfflineManager.getOfflineStorageUsed();
      setStorageInfo({ used: storage });
    } catch (error) {
      console.warn('Failed to load status:', error);
    }
  };

  const updateSetting = async (key, value) => {
    try {
      const newSettings = { ...settings, [key]: value };
      setSettings(newSettings);
      await AsyncStorage.setItem('appSettings', JSON.stringify(newSettings));
      
      // Handle special settings
      if (key === 'offlineMode') {
        if (value) {
          const result = await OfflineManager.enableOfflineMode();
          if (!result.success) {
            Alert.alert('Error', result.error || 'Failed to enable offline mode');
            setSettings({ ...settings, [key]: false });
            return;
          }
        } else {
          await OfflineManager.disableOfflineMode();
        }
        await loadStatus();
      }
    } catch (error) {
      console.error('Failed to update setting:', error);
      Alert.alert('Error', 'Failed to save settings');
    }
  };

  const showValueModal = (title, currentValue, key, type = 'text') => {
    setModalContent({ title, key, type });
    setTempValue(currentValue.toString());
    setModalVisible(true);
  };

  const saveModalValue = () => {
    const { key, type } = modalContent;
    let value = tempValue;
    
    if (type === 'number') {
      value = parseInt(tempValue) || 0;
    }
    
    updateSetting(key, value);
    setModalVisible(false);
  };

  const clearAllData = () => {
    Alert.alert(
      'Clear All Data',
      'This will delete all transcriptions, recordings, and settings. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.clear();
              await OfflineManager.clearOfflineModels();
              Alert.alert('Success', 'All data has been cleared');
              navigation.reset({
                index: 0,
                routes: [{ name: 'Home' }],
              });
            } catch (error) {
              Alert.alert('Error', 'Failed to clear data');
            }
          }
        }
      ]
    );
  };

  const exportSettings = async () => {
    try {
      // This would implement settings export
      Alert.alert('Export Settings', 'Settings export feature coming soon');
    } catch (error) {
      Alert.alert('Error', 'Failed to export settings');
    }
  };

  const formatStorageSize = (bytes) => {
    if (!bytes) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const renderSection = (title, children) => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );

  const renderSettingItem = (title, subtitle, value, onPress, icon = null) => (
    <TouchableOpacity style={styles.settingItem} onPress={onPress}>
      <View style={styles.settingLeft}>
        {icon && <MaterialIcons name={icon} size={20} color="#666" style={styles.settingIcon} />}
        <View>
          <Text style={styles.settingTitle}>{title}</Text>
          {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
        </View>
      </View>
      <View style={styles.settingRight}>
        {typeof value === 'boolean' ? (
          <Switch
            value={value}
            onValueChange={onPress}
            trackColor={{ false: '#767577', true: '#2196F3' }}
            thumbColor={value ? '#fff' : '#f4f3f4'}
          />
        ) : (
          <View style={styles.settingValue}>
            <Text style={styles.settingValueText}>{value}</Text>
            <MaterialIcons name="chevron-right" size={20} color="#ccc" />
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  const renderStatusItem = (label, value, color = '#666') => (
    <View style={styles.statusItem}>
      <Text style={styles.statusLabel}>{label}</Text>
      <Text style={[styles.statusValue, { color }]}>{value}</Text>
    </View>
  );

  const renderModal = () => (
    <Modal
      visible={modalVisible}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setModalVisible(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>{modalContent?.title}</Text>
          
          <TextInput
            style={styles.modalInput}
            value={tempValue}
            onChangeText={setTempValue}
            keyboardType={modalContent?.type === 'number' ? 'numeric' : 'default'}
            placeholder="Enter value"
            autoFocus={true}
          />
          
          <View style={styles.modalButtons}>
            <TouchableOpacity
              style={[styles.modalButton, styles.modalCancelButton]}
              onPress={() => setModalVisible(false)}
            >
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.modalButton, styles.modalSaveButton]}
              onPress={saveModalValue}
            >
              <Text style={styles.modalSaveText}>Save</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Status Section */}
      {renderSection('Status', (
        <View style={styles.statusContainer}>
          {syncStatus && renderStatusItem(
            'Sync Status',
            syncStatus.isOnline ? 'Online' : 'Offline',
            syncStatus.isOnline ? '#4CAF50' : '#ff9800'
          )}
          {syncStatus?.lastSyncTime && renderStatusItem(
            'Last Sync',
            new Date(syncStatus.lastSyncTime).toLocaleString()
          )}
          {offlineStatus && renderStatusItem(
            'Offline Mode',
            offlineStatus.isOfflineMode ? 'Enabled' : 'Disabled',
            offlineStatus.isOfflineMode ? '#4CAF50' : '#666'
          )}
          {storageInfo && renderStatusItem(
            'Storage Used',
            formatStorageSize(storageInfo.used)
          )}
        </View>
      ))}

      {/* Audio Settings */}
      {renderSection('Audio', (
        <>
          {renderSettingItem(
            'Audio Quality',
            'Higher quality uses more storage',
            settings.audioQuality,
            () => {
              Alert.alert(
                'Audio Quality',
                'Choose recording quality:',
                [
                  { text: 'Low', onPress: () => updateSetting('audioQuality', 'low') },
                  { text: 'Medium', onPress: () => updateSetting('audioQuality', 'medium') },
                  { text: 'High', onPress: () => updateSetting('audioQuality', 'high') }
                ]
              );
            },
            'audiotrack'
          )}
          
          {renderSettingItem(
            'Max Recording Time',
            'Maximum recording length in minutes',
            `${settings.maxRecordingTime} min`,
            () => showValueModal('Max Recording Time (minutes)', settings.maxRecordingTime, 'maxRecordingTime', 'number'),
            'timer'
          )}
          
          {renderSettingItem(
            'Auto Save',
            'Automatically save recordings',
            settings.autoSave,
            () => updateSetting('autoSave', !settings.autoSave),
            'save'
          )}
          
          {renderSettingItem(
            'Background Recording',
            'Allow recording when app is in background',
            settings.backgroundRecording,
            () => updateSetting('backgroundRecording', !settings.backgroundRecording),
            'radio-button-checked'
          )}
        </>
      ))}

      {/* Transcription Settings */}
      {renderSection('Transcription', (
        <>
          {renderSettingItem(
            'Default Analysis Mode',
            'Processing level for new transcriptions',
            settings.defaultAnalysisMode,
            () => {
              Alert.alert(
                'Analysis Mode',
                'Choose default processing level:',
                [
                  { text: 'Basic', onPress: () => updateSetting('defaultAnalysisMode', 'basic') },
                  { text: 'Advanced', onPress: () => updateSetting('defaultAnalysisMode', 'advanced') },
                  { text: 'Complete', onPress: () => updateSetting('defaultAnalysisMode', 'complete') }
                ]
              );
            },
            'psychology'
          )}
          
          {renderSettingItem(
            'Auto Transcribe',
            'Start transcription automatically after recording',
            settings.autoTranscribe,
            () => updateSetting('autoTranscribe', !settings.autoTranscribe),
            'auto-awesome'
          )}
          
          {renderSettingItem(
            'Speaker Diarization',
            'Identify different speakers',
            settings.speakerDiarization,
            () => updateSetting('speakerDiarization', !settings.speakerDiarization),
            'people'
          )}
          
          {renderSettingItem(
            'Timestamp Interval',
            'Time between timestamps in seconds',
            `${settings.timestampInterval}s`,
            () => showValueModal('Timestamp Interval (seconds)', settings.timestampInterval, 'timestampInterval', 'number'),
            'schedule'
          )}
        </>
      ))}

      {/* Sync & Storage */}
      {renderSection('Sync & Storage', (
        <>
          {renderSettingItem(
            'Auto Sync',
            'Automatically sync data when online',
            settings.autoSync,
            () => updateSetting('autoSync', !settings.autoSync),
            'sync'
          )}
          
          {renderSettingItem(
            'Sync on WiFi Only',
            'Only sync when connected to WiFi',
            settings.syncOnWifi,
            () => updateSetting('syncOnWifi', !settings.syncOnWifi),
            'wifi'
          )}
          
          {renderSettingItem(
            'Offline Mode',
            'Enable offline transcription capabilities',
            settings.offlineMode,
            () => updateSetting('offlineMode', !settings.offlineMode),
            'cloud-off'
          )}
          
          {renderSettingItem(
            'Data Retention',
            'Days to keep transcriptions locally',
            `${settings.dataRetention} days`,
            () => showValueModal('Data Retention (days)', settings.dataRetention, 'dataRetention', 'number'),
            'delete-sweep'
          )}
        </>
      ))}

      {/* Appearance */}
      {renderSection('Appearance', (
        <>
          {renderSettingItem(
            'Theme',
            'App color scheme',
            settings.theme,
            () => {
              Alert.alert(
                'Theme',
                'Choose app theme:',
                [
                  { text: 'Light', onPress: () => updateSetting('theme', 'light') },
                  { text: 'Dark', onPress: () => updateSetting('theme', 'dark') },
                  { text: 'System', onPress: () => updateSetting('theme', 'system') }
                ]
              );
            },
            'palette'
          )}
          
          {renderSettingItem(
            'Font Size',
            'Text size in transcriptions',
            settings.fontSize,
            () => {
              Alert.alert(
                'Font Size',
                'Choose text size:',
                [
                  { text: 'Small', onPress: () => updateSetting('fontSize', 'small') },
                  { text: 'Medium', onPress: () => updateSetting('fontSize', 'medium') },
                  { text: 'Large', onPress: () => updateSetting('fontSize', 'large') }
                ]
              );
            },
            'text-fields'
          )}
          
          {renderSettingItem(
            'Show Timestamps',
            'Display timestamps in transcriptions by default',
            settings.showTimestamps,
            () => updateSetting('showTimestamps', !settings.showTimestamps),
            'access-time'
          )}
          
          {renderSettingItem(
            'Compact Mode',
            'Use compact layout for more content',
            settings.compactMode,
            () => updateSetting('compactMode', !settings.compactMode),
            'view-compact'
          )}
        </>
      ))}

      {/* Notifications */}
      {renderSection('Notifications', (
        <>
          {renderSettingItem(
            'Transcription Complete',
            'Notify when transcription finishes',
            settings.transcriptionComplete,
            () => updateSetting('transcriptionComplete', !settings.transcriptionComplete),
            'notifications'
          )}
          
          {renderSettingItem(
            'Sync Complete',
            'Notify when sync finishes',
            settings.syncComplete,
            () => updateSetting('syncComplete', !settings.syncComplete),
            'cloud-done'
          )}
          
          {renderSettingItem(
            'Error Notifications',
            'Show notifications for errors',
            settings.errorNotifications,
            () => updateSetting('errorNotifications', !settings.errorNotifications),
            'error'
          )}
        </>
      ))}

      {/* Privacy */}
      {renderSection('Privacy', (
        <>
          {renderSettingItem(
            'Analytics',
            'Help improve the app with usage data',
            settings.analyticsEnabled,
            () => updateSetting('analyticsEnabled', !settings.analyticsEnabled),
            'analytics'
          )}
          
          {renderSettingItem(
            'Crash Reporting',
            'Send crash reports to help fix bugs',
            settings.crashReporting,
            () => updateSetting('crashReporting', !settings.crashReporting),
            'bug-report'
          )}
        </>
      ))}

      {/* Actions */}
      {renderSection('Actions', (
        <>
          <TouchableOpacity style={styles.actionButton} onPress={exportSettings}>
            <MaterialIcons name="download" size={20} color="#2196F3" />
            <Text style={styles.actionButtonText}>Export Settings</Text>
            <MaterialIcons name="chevron-right" size={20} color="#ccc" />
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.actionButton} onPress={() => loadStatus()}>
            <MaterialIcons name="refresh" size={20} color="#2196F3" />
            <Text style={styles.actionButtonText}>Refresh Status</Text>
            <MaterialIcons name="chevron-right" size={20} color="#ccc" />
          </TouchableOpacity>
          
          <TouchableOpacity style={[styles.actionButton, styles.dangerButton]} onPress={clearAllData}>
            <MaterialIcons name="delete-forever" size={20} color="#f44336" />
            <Text style={[styles.actionButtonText, { color: '#f44336' }]}>Clear All Data</Text>
            <MaterialIcons name="chevron-right" size={20} color="#ccc" />
          </TouchableOpacity>
        </>
      ))}

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Transcription App v1.0.0
        </Text>
        <Text style={styles.footerSubtext}>
          © 2024 Your Company
        </Text>
      </View>

      {renderModal()}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  section: {
    backgroundColor: '#fff',
    marginBottom: 20,
    paddingTop: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLeft: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingIcon: {
    marginRight: 12,
  },
  settingTitle: {
    fontSize: 16,
    color: '#333',
    marginBottom: 2,
  },
  settingSubtitle: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
  settingRight: {
    alignItems: 'flex-end',
  },
  settingValue: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingValueText: {
    fontSize: 14,
    color: '#666',
    marginRight: 4,
  },
  statusContainer: {
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  statusItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  statusLabel: {
    fontSize: 14,
    color: '#666',
  },
  statusValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  dangerButton: {
    backgroundColor: '#fff5f5',
  },
  actionButtonText: {
    flex: 1,
    fontSize: 16,
    color: '#2196F3',
    marginLeft: 12,
  },
  footer: {
    alignItems: 'center',
    padding: 32,
  },
  footerText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  footerSubtext: {
    fontSize: 12,
    color: '#999',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    width: '100%',
    maxWidth: 300,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
    textAlign: 'center',
  },
  modalInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    marginBottom: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  modalCancelButton: {
    backgroundColor: '#f5f5f5',
  },
  modalSaveButton: {
    backgroundColor: '#2196F3',
  },
  modalCancelText: {
    fontSize: 16,
    color: '#666',
  },
  modalSaveText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
  },
});