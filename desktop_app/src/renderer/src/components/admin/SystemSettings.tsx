import React, { useState } from 'react';
import {
  Settings,
  Globe,
  Mail,
  Shield,
  Database,
  Bell,
  Key,
  Save,
  RefreshCw,
  AlertCircle
} from 'lucide-react';

interface SystemConfig {
  general: {
    siteName: string;
    siteUrl: string;
    adminEmail: string;
    timezone: string;
    language: string;
  };
  email: {
    smtpHost: string;
    smtpPort: number;
    smtpUser: string;
    smtpSecure: boolean;
    fromEmail: string;
    fromName: string;
  };
  security: {
    passwordMinLength: number;
    sessionTimeout: number;
    maxLoginAttempts: number;
    enable2FA: boolean;
    forceHttps: boolean;
  };
  storage: {
    provider: 'local' | 's3' | 'gcs';
    maxFileSize: number;
    allowedFormats: string[];
  };
  api: {
    rateLimit: number;
    apiVersion: string;
    enableWebhooks: boolean;
    corsOrigins: string[];
  };
}

export const SystemSettings: React.FC = () => {
  const [config, setConfig] = useState<SystemConfig>({
    general: {
      siteName: 'Transcription Platform',
      siteUrl: 'https://transcribe.example.com',
      adminEmail: 'admin@example.com',
      timezone: 'UTC',
      language: 'en'
    },
    email: {
      smtpHost: 'smtp.gmail.com',
      smtpPort: 587,
      smtpUser: 'noreply@example.com',
      smtpSecure: true,
      fromEmail: 'noreply@example.com',
      fromName: 'Transcription Platform'
    },
    security: {
      passwordMinLength: 8,
      sessionTimeout: 3600,
      maxLoginAttempts: 5,
      enable2FA: true,
      forceHttps: true
    },
    storage: {
      provider: 's3',
      maxFileSize: 500, // MB
      allowedFormats: ['mp3', 'wav', 'mp4', 'mov']
    },
    api: {
      rateLimit: 100,
      apiVersion: 'v1',
      enableWebhooks: true,
      corsOrigins: ['https://app.example.com']
    }
  });

  const [activeTab, setActiveTab] = useState<keyof SystemConfig>('general');
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    // Simulate save
    setTimeout(() => {
      setIsSaving(false);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    }, 1000);
  };

  const tabs = [
    { id: 'general', label: 'General', icon: Globe },
    { id: 'email', label: 'Email', icon: Mail },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'storage', label: 'Storage', icon: Database },
    { id: 'api', label: 'API', icon: Key }
  ];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">System Settings</h2>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600">
            <RefreshCw className="w-4 h-4" />
            Reset to Defaults
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {showSuccess && (
        <div className="mb-4 p-4 bg-green-900/50 border border-green-700 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-green-500" />
          <span className="text-green-400">Settings saved successfully!</span>
        </div>
      )}

      <div className="flex gap-6">
        {/* Tabs */}
        <div className="w-48">
          <nav className="space-y-1">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as keyof SystemConfig)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'hover:bg-gray-800 text-gray-300'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 bg-gray-800 rounded-lg p-6">
          {activeTab === 'general' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold mb-4">General Settings</h3>
              <div>
                <label className="block text-sm font-medium mb-2">Site Name</label>
                <input
                  type="text"
                  value={config.general.siteName}
                  onChange={(e) => setConfig({
                    ...config,
                    general: { ...config.general, siteName: e.target.value }
                  })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Site URL</label>
                <input
                  type="url"
                  value={config.general.siteUrl}
                  onChange={(e) => setConfig({
                    ...config,
                    general: { ...config.general, siteUrl: e.target.value }
                  })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Admin Email</label>
                <input
                  type="email"
                  value={config.general.adminEmail}
                  onChange={(e) => setConfig({
                    ...config,
                    general: { ...config.general, adminEmail: e.target.value }
                  })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Timezone</label>
                  <select
                    value={config.general.timezone}
                    onChange={(e) => setConfig({
                      ...config,
                      general: { ...config.general, timezone: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">Eastern Time</option>
                    <option value="America/Los_Angeles">Pacific Time</option>
                    <option value="Europe/London">London</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Language</label>
                  <select
                    value={config.general.language}
                    onChange={(e) => setConfig({
                      ...config,
                      general: { ...config.general, language: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'email' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold mb-4">Email Settings</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">SMTP Host</label>
                  <input
                    type="text"
                    value={config.email.smtpHost}
                    onChange={(e) => setConfig({
                      ...config,
                      email: { ...config.email, smtpHost: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">SMTP Port</label>
                  <input
                    type="number"
                    value={config.email.smtpPort}
                    onChange={(e) => setConfig({
                      ...config,
                      email: { ...config.email, smtpPort: parseInt(e.target.value) }
                    })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="smtp-secure"
                  checked={config.email.smtpSecure}
                  onChange={(e) => setConfig({
                    ...config,
                    email: { ...config.email, smtpSecure: e.target.checked }
                  })}
                  className="rounded"
                />
                <label htmlFor="smtp-secure" className="text-sm">Use secure connection (TLS/SSL)</label>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold mb-4">Security Settings</h3>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Minimum Password Length
                </label>
                <input
                  type="number"
                  value={config.security.passwordMinLength}
                  onChange={(e) => setConfig({
                    ...config,
                    security: { ...config.security, passwordMinLength: parseInt(e.target.value) }
                  })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Session Timeout (seconds)
                </label>
                <input
                  type="number"
                  value={config.security.sessionTimeout}
                  onChange={(e) => setConfig({
                    ...config,
                    security: { ...config.security, sessionTimeout: parseInt(e.target.value) }
                  })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="space-y-3">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.security.enable2FA}
                    onChange={(e) => setConfig({
                      ...config,
                      security: { ...config.security, enable2FA: e.target.checked }
                    })}
                    className="rounded"
                  />
                  <span className="text-sm">Enable Two-Factor Authentication</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.security.forceHttps}
                    onChange={(e) => setConfig({
                      ...config,
                      security: { ...config.security, forceHttps: e.target.checked }
                    })}
                    className="rounded"
                  />
                  <span className="text-sm">Force HTTPS Connections</span>
                </label>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;