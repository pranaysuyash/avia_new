import React, { useState } from 'react';
import {
  Key,
  Plus,
  Copy,
  Trash2,
  RefreshCw,
  Activity,
  Calendar,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface APIKey {
  id: string;
  name: string;
  key: string;
  createdAt: string;
  lastUsed: string;
  usage: number;
  limit: number;
  status: 'active' | 'inactive';
  permissions: string[];
}

export const APIManagement: React.FC = () => {
  const [apiKeys] = useState<APIKey[]>([
    {
      id: '1',
      name: 'Production API Key',
      key: 'sk_live_1234567890abcdef',
      createdAt: '2024-01-15',
      lastUsed: '2024-03-20',
      usage: 45234,
      limit: 100000,
      status: 'active',
      permissions: ['read', 'write', 'delete']
    },
    {
      id: '2',
      name: 'Development API Key',
      key: 'sk_test_abcdef1234567890',
      createdAt: '2024-02-01',
      lastUsed: '2024-03-19',
      usage: 12543,
      limit: 50000,
      status: 'active',
      permissions: ['read', 'write']
    }
  ]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyToClipboard = (key: string) => {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">API Management</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Create API Key
        </button>
      </div>

      {/* API Keys List */}
      <div className="space-y-4">
        {apiKeys.map(apiKey => (
          <div key={apiKey.id} className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold mb-1">{apiKey.name}</h3>
                <div className="flex items-center gap-4 text-sm text-gray-400">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    Created {apiKey.createdAt}
                  </span>
                  <span className="flex items-center gap-1">
                    <Activity className="w-4 h-4" />
                    Last used {apiKey.lastUsed}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {apiKey.status === 'active' ? (
                  <span className="flex items-center gap-1 px-2 py-1 bg-green-900/50 text-green-400 rounded-full text-sm">
                    <CheckCircle className="w-4 h-4" />
                    Active
                  </span>
                ) : (
                  <span className="flex items-center gap-1 px-2 py-1 bg-red-900/50 text-red-400 rounded-full text-sm">
                    <XCircle className="w-4 h-4" />
                    Inactive
                  </span>
                )}
              </div>
            </div>

            <div className="bg-gray-900 rounded p-3 mb-4">
              <div className="flex items-center justify-between">
                <code className="text-sm text-gray-300">{apiKey.key}</code>
                <button
                  onClick={() => copyToClipboard(apiKey.key)}
                  className="p-2 hover:bg-gray-800 rounded transition"
                >
                  {copiedKey === apiKey.key ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <div className="text-sm text-gray-400">Usage</div>
                <div className="text-lg font-semibold">
                  {apiKey.usage.toLocaleString()} / {apiKey.limit.toLocaleString()}
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${(apiKey.usage / apiKey.limit) * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-400">Rate Limit</div>
                <div className="text-lg font-semibold">100 req/min</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">Permissions</div>
                <div className="flex gap-2 mt-1">
                  {apiKey.permissions.map(perm => (
                    <span
                      key={perm}
                      className="px-2 py-1 bg-gray-700 rounded text-xs capitalize"
                    >
                      {perm}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button className="flex items-center gap-2 px-3 py-1 bg-gray-700 rounded hover:bg-gray-600 text-sm">
                <RefreshCw className="w-4 h-4" />
                Regenerate
              </button>
              <button className="flex items-center gap-2 px-3 py-1 bg-gray-700 rounded hover:bg-gray-600 text-sm">
                Edit Permissions
              </button>
              <button className="flex items-center gap-2 px-3 py-1 bg-red-900/50 text-red-400 rounded hover:bg-red-900/70 text-sm">
                <Trash2 className="w-4 h-4" />
                Revoke
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Create API Key Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Create New API Key</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Key Name</label>
                <input
                  type="text"
                  placeholder="e.g., Mobile App Key"
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Permissions</label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input type="checkbox" className="mr-2 rounded" defaultChecked />
                    <span className="text-sm">Read</span>
                  </label>
                  <label className="flex items-center">
                    <input type="checkbox" className="mr-2 rounded" defaultChecked />
                    <span className="text-sm">Write</span>
                  </label>
                  <label className="flex items-center">
                    <input type="checkbox" className="mr-2 rounded" />
                    <span className="text-sm">Delete</span>
                  </label>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Rate Limit</label>
                <select className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500">
                  <option>100 requests/minute</option>
                  <option>1000 requests/minute</option>
                  <option>10000 requests/minute</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button className="flex-1 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                Create Key
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default APIManagement;