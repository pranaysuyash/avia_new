import React, { useState, useEffect } from 'react';
import { logUxEvent } from '../services/uxTelemetry';
import { motion } from 'framer-motion';
import { CheckIcon, XMarkIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

interface UserPreferences {
  language: string;
  theme: string;
  timezone: string;
  date_format: string;
  time_format: string;
  notifications_enabled: boolean;
  email_notifications: boolean;
  auto_save: boolean;
  default_transcription_language: string;
  audio_quality: string;
  max_file_size_mb: number;
  retention_days: number;
}

interface TranscriptionSettings {
  default_language: string;
  detect_code_switching: boolean;
  confidence_threshold: number;
  speaker_diarization: boolean;
  noise_reduction: boolean;
  auto_punctuation: boolean;
  profanity_filter: boolean;
  model_preference: string;
  whisper_model: 'tiny' | 'base' | 'small' | 'medium' | 'large';
  enable_timestamps: boolean;
  chunk_size_seconds: number;
  min_speakers: number;
  max_speakers: number;
}

interface ApiKeys {
  openai_api_key: string;
  elevenlabs_api_key: string;
  google_cloud_api_key: string;
  aws_access_key: string;
  aws_secret_key: string;
  azure_api_key: string;
  anthropic_api_key: string;
}

interface StorageSettings {
  storage_backend: 'local' | 's3' | 'gcs' | 'azure';
  local_storage_path: string;
  cloud_bucket_name: string;
  enable_encryption: boolean;
  enable_auto_delete: boolean;
  compression_enabled: boolean;
}

interface SecuritySettings {
  enable_audit_log: boolean;
  data_retention_policy: 'none' | '30days' | '90days' | '1year' | 'forever';
  allow_anonymous_usage: boolean;
  require_2fa: boolean;
  session_timeout_minutes: number;
  ip_whitelist: string[];
}

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState(() => {
    try { const url = new URL(window.location.href); return url.searchParams.get('settings_tab') || 'general'; } catch {}
    return 'general';
  });
  
  const [userPrefs, setUserPrefs] = useState<UserPreferences>({
    language: 'en',
    theme: 'light',
    timezone: 'UTC',
    date_format: 'YYYY-MM-DD',
    time_format: '24h',
    notifications_enabled: true,
    email_notifications: true,
    auto_save: true,
    default_transcription_language: 'auto',
    audio_quality: 'high',
    max_file_size_mb: 100,
    retention_days: 30
  });

  const [transcriptionSettings, setTranscriptionSettings] = useState<TranscriptionSettings>({
    default_language: 'auto',
    detect_code_switching: false,
    confidence_threshold: 0.8,
    speaker_diarization: false,
    noise_reduction: true,
    auto_punctuation: true,
    profanity_filter: false,
    model_preference: 'balanced',
    whisper_model: 'base',
    enable_timestamps: true,
    chunk_size_seconds: 30,
    min_speakers: 2,
    max_speakers: 5
  });

  const [apiKeys, setApiKeys] = useState<ApiKeys>({
    openai_api_key: '',
    elevenlabs_api_key: '',
    google_cloud_api_key: '',
    aws_access_key: '',
    aws_secret_key: '',
    azure_api_key: '',
    anthropic_api_key: ''
  });

  const [storageSettings, setStorageSettings] = useState<StorageSettings>({
    storage_backend: 'local',
    local_storage_path: '',
    cloud_bucket_name: '',
    enable_encryption: true,
    enable_auto_delete: false,
    compression_enabled: true
  });

  const [securitySettings, setSecuritySettings] = useState<SecuritySettings>({
    enable_audit_log: true,
    data_retention_policy: '90days',
    allow_anonymous_usage: false,
    require_2fa: false,
    session_timeout_minutes: 60,
    ip_whitelist: []
  });

  const [supportedLanguages, setSupportedLanguages] = useState<any[]>([]);
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  useEffect(() => {
    loadSettings();
    loadLanguages();
    loadModels();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      
      // Load user preferences
      const userResponse = await fetch('http://localhost:8001/api/settings/user');
      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUserPrefs(userData);
      }
      
      // Load transcription settings
      const transcriptionResponse = await fetch('http://localhost:8001/api/settings/transcription');
      if (transcriptionResponse.ok) {
        const transcriptionData = await transcriptionResponse.json();
        setTranscriptionSettings(transcriptionData);
      }
      
      // Load API keys
      const apiKeysResponse = await fetch('http://localhost:8001/api/settings/api-keys');
      if (apiKeysResponse.ok) {
        const apiKeysData = await apiKeysResponse.json();
        setApiKeys(apiKeysData);
      }
      
      // Load storage settings
      const storageResponse = await fetch('http://localhost:8001/api/settings/storage');
      if (storageResponse.ok) {
        const storageData = await storageResponse.json();
        setStorageSettings(storageData);
      }
      
      // Load security settings
      const securityResponse = await fetch('http://localhost:8001/api/settings/security');
      if (securityResponse.ok) {
        const securityData = await securityResponse.json();
        setSecuritySettings(securityData);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadLanguages = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/settings/languages');
      if (response.ok) {
        const result = await response.json();
        setSupportedLanguages(result.data || []);
      }
    } catch (error) {
      console.error('Failed to load languages:', error);
    }
  };

  const loadModels = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/settings/models');
      if (response.ok) {
        const result = await response.json();
        setAvailableModels(result.data || []);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  // Deep-link active tab to URL
  useEffect(() => {
    try { const url = new URL(window.location.href); url.searchParams.set('settings_tab', activeTab); window.history.replaceState({}, '', url.toString()); } catch {}
  }, [activeTab]);

  const saveUserPreferences = async () => {
    try {
      setSaving(true);
      const response = await fetch('http://localhost:8001/api/settings/user', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userPrefs)
      });
      
      if (response.ok) {
        setSaveStatus('success');
        setTimeout(() => setSaveStatus('idle'), 2000);
      } else {
        setSaveStatus('error');
      }
    } catch (error) {
      console.error('Failed to save user preferences:', error);
      setSaveStatus('error');
    } finally {
      setSaving(false);
    }
  };

  const saveTranscriptionSettings = async () => {
    try {
      setSaving(true);
      const response = await fetch('http://localhost:8001/api/settings/transcription', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(transcriptionSettings)
      });
      
      if (response.ok) {
        setSaveStatus('success');
        setTimeout(() => setSaveStatus('idle'), 2000);
      } else {
        setSaveStatus('error');
      }
    } catch (error) {
      console.error('Failed to save transcription settings:', error);
      setSaveStatus('error');
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/settings/reset', {
        method: 'POST'
      });
      
      if (response.ok) {
        loadSettings(); // Reload settings
        setSaveStatus('success');
      }
    } catch (error) {
      console.error('Failed to reset settings:', error);
      setSaveStatus('error');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  const tabs = [
    { id: 'general', label: 'General' },
    { id: 'transcription', label: 'Transcription' },
    { id: 'api-keys', label: 'API Keys' },
    { id: 'storage', label: 'Storage' },
    { id: 'security', label: 'Security' }
  ];

  const saveAllSettings = async () => {
    setSaving(true);
    try {
      const promises = [];
      
      if (activeTab === 'general') {
        promises.push(saveUserPreferences());
      } else if (activeTab === 'transcription') {
        promises.push(saveTranscriptionSettings());
      } else if (activeTab === 'api-keys') {
        promises.push(
          fetch('http://localhost:8001/api/settings/api-keys', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(apiKeys)
          })
        );
      } else if (activeTab === 'storage') {
        promises.push(
          fetch('http://localhost:8001/api/settings/storage', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(storageSettings)
          })
        );
      } else if (activeTab === 'security') {
        promises.push(
          fetch('http://localhost:8001/api/settings/security', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(securitySettings)
          })
        );
      }
      
      await Promise.all(promises);
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveStatus('error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
              Settings
            </h1>
            <button
              onClick={async () => { try { const href = window.location.href; await navigator.clipboard.writeText(href); logUxEvent('share_settings_view', { href }); } catch {} }}
              className="px-3 py-1 text-sm rounded-md bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
              title="Copy shareable link"
            >
              Share
            </button>
          </div>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Configure your application preferences
          </p>
        </div>
        
        {/* Save Status */}
        <div className="flex items-center space-x-2">
          {saveStatus === 'success' && (
            <div className="flex items-center text-emerald-600">
              <CheckIcon className="h-5 w-5 mr-1" />
              <span className="text-sm">Saved</span>
            </div>
          )}
          {saveStatus === 'error' && (
            <div className="flex items-center text-red-600">
              <XMarkIcon className="h-5 w-5 mr-1" />
              <span className="text-sm">Error</span>
            </div>
          )}
          <button 
            onClick={resetToDefaults}
            className="btn-secondary text-sm"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Reset to Defaults
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        {activeTab === 'general' && (
          <>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
              General Preferences
            </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Theme */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Theme
            </label>
            <select 
              value={userPrefs.theme}
              onChange={(e) => setUserPrefs(prev => ({ ...prev, theme: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto</option>
            </select>
          </div>

          {/* Language */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Interface Language
            </label>
            <select 
              value={userPrefs.language}
              onChange={(e) => setUserPrefs(prev => ({ ...prev, language: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
            </select>
          </div>

          {/* Max File Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Max File Size (MB)
            </label>
            <input 
              type="number"
              min="1"
              max="1000"
              value={userPrefs.max_file_size_mb}
              onChange={(e) => setUserPrefs(prev => ({ ...prev, max_file_size_mb: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>

          {/* Retention Days */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Data Retention (Days)
            </label>
            <input 
              type="number"
              min="1"
              max="365"
              value={userPrefs.retention_days}
              onChange={(e) => setUserPrefs(prev => ({ ...prev, retention_days: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
        </div>

        {/* Toggles */}
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700 dark:text-gray-300">Enable Notifications</span>
            <input 
              type="checkbox"
              checked={userPrefs.notifications_enabled}
              onChange={(e) => setUserPrefs(prev => ({ ...prev, notifications_enabled: e.target.checked }))}
              className="rounded"
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700 dark:text-gray-300">Auto-save Work</span>
            <input 
              type="checkbox"
              checked={userPrefs.auto_save}
              onChange={(e) => setUserPrefs(prev => ({ ...prev, auto_save: e.target.checked }))}
              className="rounded"
            />
          </div>
        </div>

        </>
        )}

        {activeTab === 'transcription' && (
          <>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
              Transcription Settings
            </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Default Language */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Default Language
            </label>
            <select 
              value={transcriptionSettings.default_language}
              onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, default_language: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              {supportedLanguages.map(lang => (
                <option key={lang.code} value={lang.code}>{lang.name}</option>
              ))}
            </select>
          </div>

          {/* Model Preference */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Model Preference
            </label>
            <select 
              value={transcriptionSettings.model_preference}
              onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, model_preference: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="fast">Fast (Lower accuracy)</option>
              <option value="balanced">Balanced</option>
              <option value="accurate">Accurate (Slower)</option>
            </select>
          </div>

          {/* Confidence Threshold */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Confidence Threshold: {transcriptionSettings.confidence_threshold}
            </label>
            <input 
              type="range"
              min="0.1"
              max="1"
              step="0.1"
              value={transcriptionSettings.confidence_threshold}
              onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, confidence_threshold: parseFloat(e.target.value) }))}
              className="w-full"
            />
          </div>
          
          {/* Whisper Model */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Whisper Model
            </label>
            <select 
              value={transcriptionSettings.whisper_model}
              onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, whisper_model: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="tiny">Tiny (39M parameters)</option>
              <option value="base">Base (74M parameters)</option>
              <option value="small">Small (244M parameters)</option>
              <option value="medium">Medium (769M parameters)</option>
              <option value="large">Large (1550M parameters)</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">Larger models are more accurate but slower</p>
          </div>
          
          {/* Chunk Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Chunk Size (seconds)
            </label>
            <input 
              type="number"
              min="10"
              max="300"
              step="10"
              value={transcriptionSettings.chunk_size_seconds}
              onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, chunk_size_seconds: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          
          {/* Speaker Range */}
          {transcriptionSettings.speaker_diarization && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Min Speakers
                </label>
                <input 
                  type="number"
                  min="1"
                  max="10"
                  value={transcriptionSettings.min_speakers}
                  onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, min_speakers: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Max Speakers
                </label>
                <input 
                  type="number"
                  min="1"
                  max="20"
                  value={transcriptionSettings.max_speakers}
                  onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, max_speakers: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </>
          )}
        </div>

        {/* Feature Toggles */}
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700 dark:text-gray-300">Detect Code-Switching</span>
            <input 
              type="checkbox"
              checked={transcriptionSettings.detect_code_switching}
              onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, detect_code_switching: e.target.checked }))}
              className="rounded"
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700 dark:text-gray-300">Speaker Diarization</span>
            <input 
              type="checkbox"
              checked={transcriptionSettings.speaker_diarization}
              onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, speaker_diarization: e.target.checked }))}
              className="rounded"
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700 dark:text-gray-300">Noise Reduction</span>
            <input 
              type="checkbox"
              checked={transcriptionSettings.noise_reduction}
              onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, noise_reduction: e.target.checked }))}
              className="rounded"
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700 dark:text-gray-300">Auto Punctuation</span>
            <input 
              type="checkbox"
              checked={transcriptionSettings.auto_punctuation}
              onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, auto_punctuation: e.target.checked }))}
              className="rounded"
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700 dark:text-gray-300">Profanity Filter</span>
            <input 
              type="checkbox"
              checked={transcriptionSettings.profanity_filter}
              onChange={(e) => setTranscriptionSettings(prev => ({ ...prev, profanity_filter: e.target.checked }))}
              className="rounded"
            />
          </div>
        </div>

          </>
        )}

        {activeTab === 'api-keys' && (
          <>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
              API Keys
            </h3>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  OpenAI API Key
                </label>
                <input 
                  type="password"
                  value={apiKeys.openai_api_key}
                  onChange={(e) => setApiKeys(prev => ({ ...prev, openai_api_key: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="sk-..."
                />
                <p className="text-xs text-gray-500 mt-1">Required for Whisper transcription</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  ElevenLabs API Key
                </label>
                <input 
                  type="password"
                  value={apiKeys.elevenlabs_api_key}
                  onChange={(e) => setApiKeys(prev => ({ ...prev, elevenlabs_api_key: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="Your API key"
                />
                <p className="text-xs text-gray-500 mt-1">Required for text-to-speech features</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Google Cloud API Key
                </label>
                <input 
                  type="password"
                  value={apiKeys.google_cloud_api_key}
                  onChange={(e) => setApiKeys(prev => ({ ...prev, google_cloud_api_key: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="Your API key"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  AWS Access Key
                </label>
                <input 
                  type="password"
                  value={apiKeys.aws_access_key}
                  onChange={(e) => setApiKeys(prev => ({ ...prev, aws_access_key: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="Your access key"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  AWS Secret Key
                </label>
                <input 
                  type="password"
                  value={apiKeys.aws_secret_key}
                  onChange={(e) => setApiKeys(prev => ({ ...prev, aws_secret_key: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="Your secret key"
                />
              </div>
            </div>
          </>
        )}

        {activeTab === 'storage' && (
          <>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
              Storage Settings
            </h3>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Storage Backend
                </label>
                <select 
                  value={storageSettings.storage_backend}
                  onChange={(e) => setStorageSettings(prev => ({ ...prev, storage_backend: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="local">Local Storage</option>
                  <option value="s3">Amazon S3</option>
                  <option value="gcs">Google Cloud Storage</option>
                  <option value="azure">Azure Blob Storage</option>
                </select>
              </div>
              
              {storageSettings.storage_backend === 'local' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Local Storage Path
                  </label>
                  <input 
                    type="text"
                    value={storageSettings.local_storage_path}
                    onChange={(e) => setStorageSettings(prev => ({ ...prev, local_storage_path: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    placeholder="/path/to/storage"
                  />
                </div>
              )}
              
              {storageSettings.storage_backend !== 'local' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Cloud Bucket Name
                  </label>
                  <input 
                    type="text"
                    value={storageSettings.cloud_bucket_name}
                    onChange={(e) => setStorageSettings(prev => ({ ...prev, cloud_bucket_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    placeholder="my-transcription-bucket"
                  />
                </div>
              )}
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">Enable Encryption</span>
                  <input 
                    type="checkbox"
                    checked={storageSettings.enable_encryption}
                    onChange={(e) => setStorageSettings(prev => ({ ...prev, enable_encryption: e.target.checked }))}
                    className="rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">Auto-delete Old Files</span>
                  <input 
                    type="checkbox"
                    checked={storageSettings.enable_auto_delete}
                    onChange={(e) => setStorageSettings(prev => ({ ...prev, enable_auto_delete: e.target.checked }))}
                    className="rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">Enable Compression</span>
                  <input 
                    type="checkbox"
                    checked={storageSettings.compression_enabled}
                    onChange={(e) => setStorageSettings(prev => ({ ...prev, compression_enabled: e.target.checked }))}
                    className="rounded"
                  />
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'security' && (
          <>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
              Security Settings
            </h3>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Data Retention Policy
                </label>
                <select 
                  value={securitySettings.data_retention_policy}
                  onChange={(e) => setSecuritySettings(prev => ({ ...prev, data_retention_policy: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="none">No retention</option>
                  <option value="30days">30 days</option>
                  <option value="90days">90 days</option>
                  <option value="1year">1 year</option>
                  <option value="forever">Forever</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Session Timeout (minutes)
                </label>
                <input 
                  type="number"
                  min="5"
                  max="1440"
                  value={securitySettings.session_timeout_minutes}
                  onChange={(e) => setSecuritySettings(prev => ({ ...prev, session_timeout_minutes: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">Enable Audit Logging</span>
                  <input 
                    type="checkbox"
                    checked={securitySettings.enable_audit_log}
                    onChange={(e) => setSecuritySettings(prev => ({ ...prev, enable_audit_log: e.target.checked }))}
                    className="rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">Require Two-Factor Authentication</span>
                  <input 
                    type="checkbox"
                    checked={securitySettings.require_2fa}
                    onChange={(e) => setSecuritySettings(prev => ({ ...prev, require_2fa: e.target.checked }))}
                    className="rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">Allow Anonymous Usage Analytics</span>
                  <input 
                    type="checkbox"
                    checked={securitySettings.allow_anonymous_usage}
                    onChange={(e) => setSecuritySettings(prev => ({ ...prev, allow_anonymous_usage: e.target.checked }))}
                    className="rounded"
                  />
                </div>
              </div>
              
              <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  <strong>Privacy Notice:</strong> Your data is processed locally by default. 
                  API keys are encrypted and stored securely. No data is shared with third parties 
                  unless explicitly configured.
                </p>
              </div>
            </div>
          </>
        )}
        
        <div className="mt-6 flex justify-end">
          <button 
            onClick={saveAllSettings}
            disabled={saving}
            className="btn-primary"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default Settings;
