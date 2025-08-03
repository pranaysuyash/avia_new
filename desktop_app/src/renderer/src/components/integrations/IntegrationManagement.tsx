import React, { useState } from 'react';
import {
  Plug,
  Plus,
  Settings,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  MoreVertical,
  RefreshCw,
  Trash2,
  Key,
  Link,
  Unlink,
  Activity,
  Code,
  Globe
} from 'lucide-react';

interface Integration {
  id: string;
  name: string;
  description: string;
  category: 'productivity' | 'storage' | 'communication' | 'analytics' | 'development';
  icon: string;
  status: 'connected' | 'disconnected' | 'error';
  lastSync?: string;
  config?: {
    apiKey?: string;
    webhookUrl?: string;
    clientId?: string;
  };
  features: string[];
  usage?: {
    events: number;
    lastEvent?: string;
  };
}

export const IntegrationManagement: React.FC = () => {
  const [integrations] = useState<Integration[]>([
    {
      id: 'slack',
      name: 'Slack',
      description: 'Get notifications and share transcriptions in Slack channels',
      category: 'communication',
      icon: '💬',
      status: 'connected',
      lastSync: '2024-03-20 14:30:00',
      features: ['Notifications', 'Share transcriptions', 'Commands'],
      usage: {
        events: 1234,
        lastEvent: '5 minutes ago'
      }
    },
    {
      id: 'google-drive',
      name: 'Google Drive',
      description: 'Automatically backup transcriptions to Google Drive',
      category: 'storage',
      icon: '📁',
      status: 'connected',
      lastSync: '2024-03-20 12:00:00',
      features: ['Auto backup', 'Folder sync', 'Share links'],
      usage: {
        events: 456,
        lastEvent: '2 hours ago'
      }
    },
    {
      id: 'zapier',
      name: 'Zapier',
      description: 'Connect with 5000+ apps through Zapier automation',
      category: 'productivity',
      icon: '⚡',
      status: 'disconnected',
      features: ['Automation', 'Workflows', 'Triggers'],
      usage: {
        events: 0
      }
    },
    {
      id: 'notion',
      name: 'Notion',
      description: 'Create notes and documents from transcriptions',
      category: 'productivity',
      icon: '📝',
      status: 'disconnected',
      features: ['Create pages', 'Sync content', 'Templates']
    },
    {
      id: 'github',
      name: 'GitHub',
      description: 'Create issues and PRs from transcription insights',
      category: 'development',
      icon: '🐙',
      status: 'error',
      lastSync: '2024-03-19 10:00:00',
      features: ['Create issues', 'PR comments', 'Webhooks'],
      usage: {
        events: 89,
        lastEvent: 'Connection failed'
      }
    },
    {
      id: 'mixpanel',
      name: 'Mixpanel',
      description: 'Track transcription analytics and user behavior',
      category: 'analytics',
      icon: '📊',
      status: 'connected',
      features: ['Event tracking', 'User analytics', 'Custom events'],
      usage: {
        events: 5678,
        lastEvent: '1 minute ago'
      }
    }
  ]);

  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [showConfigModal, setShowConfigModal] = useState(false);

  const categories = [
    { id: 'all', label: 'All', icon: Globe },
    { id: 'productivity', label: 'Productivity', icon: Activity },
    { id: 'storage', label: 'Storage', icon: HardDrive },
    { id: 'communication', label: 'Communication', icon: MessageSquare },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'development', label: 'Development', icon: Code }
  ];

  const filteredIntegrations = filterCategory === 'all' 
    ? integrations 
    : integrations.filter(i => i.category === filterCategory);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'text-green-500';
      case 'disconnected':
        return 'text-gray-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-green-900/50 text-green-400 rounded-full text-xs">
            <CheckCircle className="w-3 h-3" />
            Connected
          </span>
        );
      case 'disconnected':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-gray-900/50 text-gray-400 rounded-full text-xs">
            <Unlink className="w-3 h-3" />
            Disconnected
          </span>
        );
      case 'error':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-red-900/50 text-red-400 rounded-full text-xs">
            <AlertCircle className="w-3 h-3" />
            Error
          </span>
        );
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-semibold flex items-center gap-2">
              <Plug className="w-6 h-6" />
              Integrations
            </h1>
            <p className="text-gray-400 mt-1">Connect your favorite tools and services</p>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            <Plus className="w-4 h-4" />
            Browse Marketplace
          </button>
        </div>

        {/* Category Filters */}
        <div className="flex gap-2">
          {categories.map(category => (
            <button
              key={category.id}
              onClick={() => setFilterCategory(category.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition ${
                filterCategory === category.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              <category.icon className="w-4 h-4" />
              <span className="text-sm">{category.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Integrations Grid */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-3 gap-4">
          {filteredIntegrations.map(integration => (
            <div
              key={integration.id}
              className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700/50 transition cursor-pointer"
              onClick={() => setSelectedIntegration(integration)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="text-3xl">{integration.icon}</div>
                  <div>
                    <h3 className="font-semibold">{integration.name}</h3>
                    <p className="text-xs text-gray-400 capitalize">{integration.category}</p>
                  </div>
                </div>
                {getStatusBadge(integration.status)}
              </div>

              <p className="text-sm text-gray-400 mb-3">{integration.description}</p>

              <div className="flex flex-wrap gap-2 mb-3">
                {integration.features.slice(0, 3).map((feature, idx) => (
                  <span key={idx} className="text-xs px-2 py-1 bg-gray-700 rounded">
                    {feature}
                  </span>
                ))}
              </div>

              {integration.usage && integration.status === 'connected' && (
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>{integration.usage.events} events</span>
                  <span>{integration.usage.lastEvent}</span>
                </div>
              )}

              <div className="flex gap-2 mt-3">
                {integration.status === 'connected' ? (
                  <>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedIntegration(integration);
                        setShowConfigModal(true);
                      }}
                      className="flex-1 py-1.5 bg-gray-700 text-sm rounded hover:bg-gray-600"
                    >
                      Configure
                    </button>
                    <button className="px-3 py-1.5 bg-gray-700 rounded hover:bg-gray-600">
                      <RefreshCw className="w-4 h-4" />
                    </button>
                  </>
                ) : (
                  <button className="flex-1 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                    Connect
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Integration Details Modal */}
      {selectedIntegration && !showConfigModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="text-4xl">{selectedIntegration.icon}</div>
                <div>
                  <h2 className="text-xl font-semibold">{selectedIntegration.name}</h2>
                  <p className="text-sm text-gray-400">{selectedIntegration.description}</p>
                </div>
              </div>
              {getStatusBadge(selectedIntegration.status)}
            </div>

            {/* Integration Info */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-medium mb-2">Features</h3>
                <ul className="space-y-1">
                  {selectedIntegration.features.map((feature, idx) => (
                    <li key={idx} className="text-sm text-gray-400 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              {selectedIntegration.usage && (
                <div className="bg-gray-800 rounded-lg p-4">
                  <h3 className="font-medium mb-2">Usage Statistics</h3>
                  <dl className="space-y-2">
                    <div>
                      <dt className="text-xs text-gray-400">Total Events</dt>
                      <dd className="text-lg font-semibold">{selectedIntegration.usage.events.toLocaleString()}</dd>
                    </div>
                    {selectedIntegration.lastSync && (
                      <div>
                        <dt className="text-xs text-gray-400">Last Sync</dt>
                        <dd className="text-sm">{selectedIntegration.lastSync}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              {selectedIntegration.status === 'connected' ? (
                <>
                  <button
                    onClick={() => setShowConfigModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    <Settings className="w-4 h-4" />
                    Configure
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600">
                    <RefreshCw className="w-4 h-4" />
                    Sync Now
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 bg-red-900/50 text-red-400 rounded hover:bg-red-900/70">
                    <Unlink className="w-4 h-4" />
                    Disconnect
                  </button>
                </>
              ) : (
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                  <Link className="w-4 h-4" />
                  Connect {selectedIntegration.name}
                </button>
              )}
              <button
                onClick={() => setSelectedIntegration(null)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Configuration Modal */}
      {showConfigModal && selectedIntegration && (
        <IntegrationConfigModal
          integration={selectedIntegration}
          onClose={() => {
            setShowConfigModal(false);
            setSelectedIntegration(null);
          }}
        />
      )}
    </div>
  );
};

interface IntegrationConfigModalProps {
  integration: Integration;
  onClose: () => void;
}

const IntegrationConfigModal: React.FC<IntegrationConfigModalProps> = ({ integration, onClose }) => {
  const [config, setConfig] = useState({
    apiKey: integration.config?.apiKey || '',
    webhookUrl: integration.config?.webhookUrl || '',
    clientId: integration.config?.clientId || '',
    enableNotifications: true,
    syncFrequency: 'realtime',
    allowedEvents: ['transcription.created', 'transcription.completed']
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-lg p-6 max-w-lg w-full">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Configure {integration.name}
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">API Key</label>
            <div className="relative">
              <input
                type="password"
                value={config.apiKey}
                onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                className="w-full px-3 py-2 pr-10 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
              />
              <Key className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Webhook URL</label>
            <input
              type="url"
              value={config.webhookUrl}
              onChange={(e) => setConfig({ ...config, webhookUrl: e.target.value })}
              placeholder="https://your-webhook-url.com/webhook"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Sync Frequency</label>
            <select
              value={config.syncFrequency}
              onChange={(e) => setConfig({ ...config, syncFrequency: e.target.value })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
            >
              <option value="realtime">Real-time</option>
              <option value="5min">Every 5 minutes</option>
              <option value="15min">Every 15 minutes</option>
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Enabled Events</label>
            <div className="space-y-2">
              {['transcription.created', 'transcription.completed', 'transcription.deleted', 'user.joined'].map(event => (
                <label key={event} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.allowedEvents.includes(event)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setConfig({ ...config, allowedEvents: [...config.allowedEvents, event] });
                      } else {
                        setConfig({ ...config, allowedEvents: config.allowedEvents.filter(e => e !== event) });
                      }
                    }}
                    className="mr-2 rounded"
                  />
                  <span className="text-sm">{event}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="notifications"
              checked={config.enableNotifications}
              onChange={(e) => setConfig({ ...config, enableNotifications: e.target.checked })}
              className="mr-2 rounded"
            />
            <label htmlFor="notifications" className="text-sm">Enable notifications</label>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button className="flex-1 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Save Configuration
          </button>
          <button onClick={onClose} className="flex-1 py-2 bg-gray-700 text-white rounded hover:bg-gray-600">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default IntegrationManagement;

// Missing imports
import { HardDrive, MessageSquare, BarChart3 } from 'lucide-react';