import React, { useState } from 'react';
import {
  Database,
  HardDrive,
  Download,
  Upload,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  Trash2,
  Archive
} from 'lucide-react';

export const DatabaseManagement: React.FC = () => {
  const [backups] = useState([
    {
      id: '1',
      name: 'backup_2024_03_20_full.sql',
      type: 'full',
      size: '2.4 GB',
      created: '2024-03-20 03:00:00',
      status: 'completed'
    },
    {
      id: '2',
      name: 'backup_2024_03_19_incremental.sql',
      type: 'incremental',
      size: '156 MB',
      created: '2024-03-19 15:00:00',
      status: 'completed'
    }
  ]);

  const [isBackingUp, setIsBackingUp] = useState(false);

  const handleBackup = async () => {
    setIsBackingUp(true);
    // Simulate backup
    setTimeout(() => setIsBackingUp(false), 3000);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-semibold mb-6">Database Management</h2>

      {/* Database Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Database className="w-8 h-8 text-blue-500" />
            <span className="text-xs text-green-500">Healthy</span>
          </div>
          <div className="text-2xl font-bold">PostgreSQL</div>
          <div className="text-sm text-gray-400">v14.5</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <HardDrive className="w-8 h-8 text-purple-500 mb-2" />
          <div className="text-2xl font-bold">45.2 GB</div>
          <div className="text-sm text-gray-400">Database Size</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <Archive className="w-8 h-8 text-green-500 mb-2" />
          <div className="text-2xl font-bold">12</div>
          <div className="text-sm text-gray-400">Total Backups</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <Clock className="w-8 h-8 text-yellow-500 mb-2" />
          <div className="text-2xl font-bold">3h ago</div>
          <div className="text-sm text-gray-400">Last Backup</div>
        </div>
      </div>

      {/* Actions */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold mb-4">Database Actions</h3>
        <div className="grid grid-cols-4 gap-4">
          <button
            onClick={handleBackup}
            disabled={isBackingUp}
            className="flex flex-col items-center gap-2 p-4 bg-gray-700 rounded hover:bg-gray-600 disabled:opacity-50"
          >
            {isBackingUp ? (
              <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
            ) : (
              <Download className="w-8 h-8 text-blue-500" />
            )}
            <span>Create Backup</span>
          </button>
          <button className="flex flex-col items-center gap-2 p-4 bg-gray-700 rounded hover:bg-gray-600">
            <Upload className="w-8 h-8 text-green-500" />
            <span>Restore</span>
          </button>
          <button className="flex flex-col items-center gap-2 p-4 bg-gray-700 rounded hover:bg-gray-600">
            <RefreshCw className="w-8 h-8 text-yellow-500" />
            <span>Optimize</span>
          </button>
          <button className="flex flex-col items-center gap-2 p-4 bg-gray-700 rounded hover:bg-gray-600">
            <Trash2 className="w-8 h-8 text-red-500" />
            <span>Clean Up</span>
          </button>
        </div>
      </div>

      {/* Backup History */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold">Backup History</h3>
        </div>
        <table className="w-full">
          <thead className="bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Backup Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Size
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {backups.map(backup => (
              <tr key={backup.id} className="hover:bg-gray-700/50">
                <td className="px-6 py-4 text-sm">{backup.name}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    backup.type === 'full' 
                      ? 'bg-blue-900/50 text-blue-400 border border-blue-700'
                      : 'bg-gray-900/50 text-gray-400 border border-gray-700'
                  }`}>
                    {backup.type}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm">{backup.size}</td>
                <td className="px-6 py-4 text-sm text-gray-400">{backup.created}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm text-green-500">Completed</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-right">
                  <button className="text-blue-400 hover:text-blue-300 mr-3">
                    Download
                  </button>
                  <button className="text-red-400 hover:text-red-300">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DatabaseManagement;