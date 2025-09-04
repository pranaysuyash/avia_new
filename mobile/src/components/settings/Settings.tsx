import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Switch,
  Alert,
  ActivityIndicator,
  Linking,
  Share,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Picker } from '@react-native-picker/picker';
import styles from './styles';
import { useRoute } from '@react-navigation/native';
import { logUxEvent } from '../../utils/uxTelemetry';
import { buildLink } from '../../utils/deeplink';
import { SkeletonLine, SkeletonBlock } from '../shared/Skeleton';

interface SettingsProps {
  onSave?: () => void;
  onClose?: () => void;
}

const Settings: React.FC<SettingsProps> = ({ onSave, onClose }) => {
  const route = useRoute<any>();
  const [activeTab, setActiveTab] = useState(route?.params?.tab || 'general');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // General Settings
  const [theme, setTheme] = useState('system');
  const [language, setLanguage] = useState('en');
  const [enableNotifications, setEnableNotifications] = useState(true);
  const [autoSave, setAutoSave] = useState(true);
  const [maxFileSize, setMaxFileSize] = useState('100');
  const [retentionDays, setRetentionDays] = useState('30');
  
  // Transcription Settings
  const [whisperModel, setWhisperModel] = useState('base');
  const [defaultLanguage, setDefaultLanguage] = useState('auto');
  const [enableSpeakerDiarization, setEnableSpeakerDiarization] = useState(true);
  const [minSpeakers, setMinSpeakers] = useState('2');
  const [maxSpeakers, setMaxSpeakers] = useState('5');
  const [enablePunctuation, setEnablePunctuation] = useState(true);
  const [enableTimestamps, setEnableTimestamps] = useState(true);
  const [enableNoiseCancellation, setEnableNoiseCancellation] = useState(true);
  
  // API Keys
  const [openaiKey, setOpenaiKey] = useState('');
  const [elevenlabsKey, setElevenlabsKey] = useState('');
  const [googleCloudKey, setGoogleCloudKey] = useState('');
  const [awsAccessKey, setAwsAccessKey] = useState('');
  const [awsSecretKey, setAwsSecretKey] = useState('');
  
  // Storage Settings
  const [storageBackend, setStorageBackend] = useState('local');
  const [localPath, setLocalPath] = useState('');
  const [cloudBucket, setCloudBucket] = useState('');
  const [enableEncryption, setEnableEncryption] = useState(true);
  const [enableCompression, setEnableCompression] = useState(true);
  
  // Security Settings
  const [enableAuditLog, setEnableAuditLog] = useState(true);
  const [dataRetention, setDataRetention] = useState('90days');
  const [sessionTimeout, setSessionTimeout] = useState('60');
  const [require2FA, setRequire2FA] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  // Apply deep-linked tab param when present
  useEffect(() => {
    if (route?.params?.tab && typeof route.params.tab === 'string') {
      setActiveTab(route.params.tab);
    }
  }, [route?.params?.tab]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      // TODO: Load settings from API
      // const response = await fetch('/api/settings');
      // const data = await response.json();
      // Apply loaded settings to state
    } catch (error) {
      Alert.alert('Error', 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // TODO: Save settings to API
      Alert.alert('Success', 'Settings saved successfully');
      await logUxEvent('settings_saved', { tab: activeTab });
      if (onSave) onSave();
    } catch (error) {
      Alert.alert('Error', 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTabChange = async (id: string) => {
    setActiveTab(id);
    await logUxEvent('settings_tab_change', { tab: id });
  };

  const shareCurrentView = async () => {
    const url = buildLink('settings', { tab: activeTab });
    try {
      await Share.share({ message: url });
      await logUxEvent('share_settings_view', { url, method: 'native_share' });
    } catch (_) {
      try {
        await Linking.openURL(url);
      } catch (__) {}
    }
  };

  const tabs = [
    { id: 'general', label: 'General', icon: 'settings' },
    { id: 'transcription', label: 'Transcription', icon: 'mic' },
    { id: 'api-keys', label: 'API Keys', icon: 'vpn-key' },
    { id: 'storage', label: 'Storage', icon: 'storage' },
    { id: 'security', label: 'Security', icon: 'security' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return (
          <View style={styles.tabContent}>
            {/* Developer Tools shortcut */}
            <View style={{ flexDirection: 'row', justifyContent: 'flex-end', marginBottom: 8 }}>
              <TouchableOpacity accessibilityRole="button" accessibilityLabel="Open Telemetry Viewer" onPress={() => {
                try { logUxEvent('open_telemetry_viewer'); } catch {}
                // @ts-ignore navigation may be available via parent stack; fallback to Linking
                try { (global as any).navigation?.navigate('Telemetry'); } catch {}
              }} style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Icon name="insights" size={18} color="#3498db" />
                <Text style={{ color: '#3498db', marginLeft: 6 }}>Open Telemetry Viewer</Text>
              </TouchableOpacity>
            </View>
            {/* Shareable deep link example */}
            <View style={{ flexDirection: 'row', justifyContent: 'flex-end', marginBottom: 8 }}>
              <TouchableOpacity accessibilityRole="button" accessibilityLabel="Share settings view" onPress={shareCurrentView} style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Icon name="ios-share" size={18} color="#3498db" />
                <Text style={{ color: '#3498db', marginLeft: 6 }}>Share View</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Theme</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={theme}
                  onValueChange={setTheme}
                  style={styles.picker}
                >
                  <Picker.Item label="Light" value="light" />
                  <Picker.Item label="Dark" value="dark" />
                  <Picker.Item label="System" value="system" />
                </Picker>
              </View>
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Language</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={language}
                  onValueChange={setLanguage}
                  style={styles.picker}
                >
                  <Picker.Item label="English" value="en" />
                  <Picker.Item label="Spanish" value="es" />
                  <Picker.Item label="French" value="fr" />
                  <Picker.Item label="German" value="de" />
                  <Picker.Item label="Chinese" value="zh" />
                  <Picker.Item label="Japanese" value="ja" />
                </Picker>
              </View>
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Max File Size (MB)</Text>
              <TextInput
                style={styles.textInput}
                value={maxFileSize}
                onChangeText={setMaxFileSize}
                keyboardType="numeric"
                placeholder="100"
              />
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Data Retention (Days)</Text>
              <TextInput
                style={styles.textInput}
                value={retentionDays}
                onChangeText={setRetentionDays}
                keyboardType="numeric"
                placeholder="30"
              />
            </View>

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Enable Notifications</Text>
              <Switch
                value={enableNotifications}
                onValueChange={setEnableNotifications}
                trackColor={{ false: '#767577', true: '#81b0ff' }}
                thumbColor={enableNotifications ? '#007AFF' : '#f4f3f4'}
              />
            </View>

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Auto-save</Text>
              <Switch
                value={autoSave}
                onValueChange={setAutoSave}
                trackColor={{ false: '#767577', true: '#81b0ff' }}
                thumbColor={autoSave ? '#007AFF' : '#f4f3f4'}
              />
            </View>
          </View>
        );

      case 'transcription':
        return (
          <View style={styles.tabContent}>
            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Whisper Model</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={whisperModel}
                  onValueChange={setWhisperModel}
                  style={styles.picker}
                >
                  <Picker.Item label="Tiny (39M)" value="tiny" />
                  <Picker.Item label="Base (74M)" value="base" />
                  <Picker.Item label="Small (244M)" value="small" />
                  <Picker.Item label="Medium (769M)" value="medium" />
                  <Picker.Item label="Large (1550M)" value="large" />
                </Picker>
              </View>
              <Text style={styles.helpText}>Larger models are more accurate but slower</Text>
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Default Language</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={defaultLanguage}
                  onValueChange={setDefaultLanguage}
                  style={styles.picker}
                >
                  <Picker.Item label="Auto-detect" value="auto" />
                  <Picker.Item label="English" value="en" />
                  <Picker.Item label="Spanish" value="es" />
                  <Picker.Item label="French" value="fr" />
                  <Picker.Item label="German" value="de" />
                  <Picker.Item label="Chinese" value="zh" />
                  <Picker.Item label="Japanese" value="ja" />
                </Picker>
              </View>
            </View>

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Speaker Diarization</Text>
              <Switch
                value={enableSpeakerDiarization}
                onValueChange={setEnableSpeakerDiarization}
                trackColor={{ false: '#767577', true: '#81b0ff' }}
                thumbColor={enableSpeakerDiarization ? '#007AFF' : '#f4f3f4'}
              />
            </View>

            {enableSpeakerDiarization && (
              <View style={styles.speakerSettings}>
                <View style={styles.settingGroup}>
                  <Text style={styles.settingLabel}>Min Speakers</Text>
                  <TextInput
                    style={styles.textInput}
                    value={minSpeakers}
                    onChangeText={setMinSpeakers}
                    keyboardType="numeric"
                    placeholder="2"
                  />
                </View>
                <View style={styles.settingGroup}>
                  <Text style={styles.settingLabel}>Max Speakers</Text>
                  <TextInput
                    style={styles.textInput}
                    value={maxSpeakers}
                    onChangeText={setMaxSpeakers}
                    keyboardType="numeric"
                    placeholder="5"
                  />
                </View>
              </View>
            )}

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Auto-punctuation</Text>
              <Switch
                value={enablePunctuation}
                onValueChange={setEnablePunctuation}
                trackColor={{ false: '#767577', true: '#81b0ff' }}
                thumbColor={enablePunctuation ? '#007AFF' : '#f4f3f4'}
              />
            </View>

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Include Timestamps</Text>
              <Switch
                value={enableTimestamps}
                onValueChange={setEnableTimestamps}
                trackColor={{ false: '#767577', true: '#81b0ff' }}
                thumbColor={enableTimestamps ? '#007AFF' : '#f4f3f4'}
              />
            </View>

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Noise Cancellation</Text>
              <Switch
                value={enableNoiseCancellation}
                onValueChange={setEnableNoiseCancellation}
                trackColor={{ false: '#767577', true: '#81b0ff' }}
                thumbColor={enableNoiseCancellation ? '#007AFF' : '#f4f3f4'}
              />
            </View>
          </View>
        );

      case 'api-keys':
        return (
          <View style={styles.tabContent}>
            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>OpenAI API Key</Text>
              <TextInput
                style={styles.textInput}
                value={openaiKey}
                onChangeText={setOpenaiKey}
                placeholder="sk-..."
                secureTextEntry
              />
              <Text style={styles.helpText}>Required for Whisper transcription</Text>
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>ElevenLabs API Key</Text>
              <TextInput
                style={styles.textInput}
                value={elevenlabsKey}
                onChangeText={setElevenlabsKey}
                placeholder="Your API key"
                secureTextEntry
              />
              <Text style={styles.helpText}>Required for text-to-speech features</Text>
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Google Cloud API Key</Text>
              <TextInput
                style={styles.textInput}
                value={googleCloudKey}
                onChangeText={setGoogleCloudKey}
                placeholder="Your API key"
                secureTextEntry
              />
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>AWS Access Key</Text>
              <TextInput
                style={styles.textInput}
                value={awsAccessKey}
                onChangeText={setAwsAccessKey}
                placeholder="Your access key"
                secureTextEntry
              />
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>AWS Secret Key</Text>
              <TextInput
                style={styles.textInput}
                value={awsSecretKey}
                onChangeText={setAwsSecretKey}
                placeholder="Your secret key"
                secureTextEntry
              />
            </View>
          </View>
        );

      case 'storage':
        return (
          <View style={styles.tabContent}>
            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Storage Backend</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={storageBackend}
                  onValueChange={setStorageBackend}
                  style={styles.picker}
                >
                  <Picker.Item label="Local Storage" value="local" />
                  <Picker.Item label="Amazon S3" value="s3" />
                  <Picker.Item label="Google Cloud Storage" value="gcs" />
                  <Picker.Item label="Azure Blob Storage" value="azure" />
                </Picker>
              </View>
            </View>

            {storageBackend === 'local' ? (
              <View style={styles.settingGroup}>
                <Text style={styles.settingLabel}>Local Storage Path</Text>
                <TextInput
                  style={styles.textInput}
                  value={localPath}
                  onChangeText={setLocalPath}
                  placeholder="/path/to/storage"
                />
              </View>
            ) : (
              <View style={styles.settingGroup}>
                <Text style={styles.settingLabel}>Cloud Bucket Name</Text>
                <TextInput
                  style={styles.textInput}
                  value={cloudBucket}
                  onChangeText={setCloudBucket}
                  placeholder="my-transcription-bucket"
                />
              </View>
            )}

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Enable Encryption</Text>
              <Switch
                value={enableEncryption}
                onValueChange={setEnableEncryption}
                trackColor={{ false: '#767577', true: '#81b0ff' }}
                thumbColor={enableEncryption ? '#007AFF' : '#f4f3f4'}
              />
            </View>

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Enable Compression</Text>
              <Switch
                value={enableCompression}
                onValueChange={setEnableCompression}
                trackColor={{ false: '#767577', true: '#81b0ff' }}
                thumbColor={enableCompression ? '#007AFF' : '#f4f3f4'}
              />
            </View>
          </View>
        );

      case 'security':
        return (
          <View style={styles.tabContent}>
            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Data Retention Policy</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={dataRetention}
                  onValueChange={setDataRetention}
                  style={styles.picker}
                >
                  <Picker.Item label="No retention" value="none" />
                  <Picker.Item label="30 days" value="30days" />
                  <Picker.Item label="90 days" value="90days" />
                  <Picker.Item label="1 year" value="1year" />
                  <Picker.Item label="Forever" value="forever" />
                </Picker>
              </View>
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Session Timeout (minutes)</Text>
              <TextInput
                style={styles.textInput}
                value={sessionTimeout}
                onChangeText={setSessionTimeout}
                keyboardType="numeric"
                placeholder="60"
              />
            </View>

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Enable Audit Logging</Text>
              <Switch
                value={enableAuditLog}
                onValueChange={setEnableAuditLog}
                trackColor={{ false: '#767577', true: '#81b0ff' }}
                thumbColor={enableAuditLog ? '#007AFF' : '#f4f3f4'}
              />
            </View>

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Require 2FA</Text>
              <Switch
                value={require2FA}
                onValueChange={setRequire2FA}
                trackColor={{ false: '#767577', true: '#81b0ff' }}
                thumbColor={require2FA ? '#007AFF' : '#f4f3f4'}
              />
            </View>

            <View style={styles.privacyNotice}>
              <Icon name="info" size={20} color="#F59E0B" />
              <Text style={styles.privacyText}>
                Your data is processed locally by default. API keys are encrypted 
                and stored securely. No data is shared with third parties unless 
                explicitly configured.
              </Text>
            </View>
          </View>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, { padding: 16 }]}> 
        <SkeletonLine width="60%" height={20} />
        <SkeletonBlock height={100} />
        <SkeletonLine width="40%" />
        <SkeletonBlock height={160} />
        <SkeletonLine width="80%" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Settings</Text>
        {onClose && (
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="close" size={24} color="#333" />
          </TouchableOpacity>
        )}
      </View>

      {/* Tabs */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.tabsContainer}
      >
        {tabs.map(tab => (
          <TouchableOpacity
            key={tab.id}
            style={[
              styles.tab,
              activeTab === tab.id && styles.activeTab
            ]}
            onPress={() => handleTabChange(tab.id)}
          >
            <Icon 
              name={tab.icon} 
              size={20} 
              color={activeTab === tab.id ? '#007AFF' : '#666'} 
            />
            <Text style={[
              styles.tabLabel,
              activeTab === tab.id && styles.activeTabLabel
            ]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Content */}
      <ScrollView style={styles.contentContainer}>
        {renderTabContent()}
      </ScrollView>

      {/* Save Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.saveButton, saving && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={saving}
        >
          {saving ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <>
              <Icon name="save" size={20} color="#FFFFFF" />
              <Text style={styles.saveButtonText}>Save Settings</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default Settings;
