import React, { useState } from 'react';
import {
  FileText,
  Search,
  Filter,
  Download,
  User,
  Shield,
  Key,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';

interface AuditLog {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  resource: string;
  ip: string;
  status: 'success' | 'failure' | 'warning';
  details?: string;
}

export const AuditLogs: React.FC = () => {
  const [logs] = useState<AuditLog[]>([
    {
      id: '1',
      timestamp: '2024-03-20 14:32:15',
      user: 'admin@example.com',
      action: 'user.login',
      resource: 'Authentication',
      ip: '192.168.1.100',
      status: 'success'
    },
    {
      id: '2',
      timestamp: '2024-03-20 14:28:42',
      user: 'john@example.com',
      action: 'transcription.delete',
      resource: 'Transcription #4521',
      ip: '10.0.0.25',
      status: 'success',
      details: 'Deleted transcription "Meeting Recording"'
    },
    {
      id: '3',
      timestamp: '2024-03-20 14:15:33',
      user: 'system',
      action: 'backup.failed',
      resource: 'Database',
      ip: 'localhost',
      status: 'failure',
      details: 'Insufficient disk space'
    }
  ]);

  const [searchQuery, setSearchQuery] = useState('');
  const [filterAction, setFilterAction] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [dateRange, setDateRange] = useState('24h');

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failure':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return null;
    }
  };

  const getActionIcon = (action: string) => {
    if (action.includes('user')) return <User className="w-4 h-4" />;
    if (action.includes('auth')) return <Shield className="w-4 h-4" />;
    if (action.includes('api')) return <Key className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">Audit Logs</h2>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          <Download className="w-4 h-4" />
          Export Logs
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search logs..."
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
          />
        </div>
        <select
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
        >
          <option value="all">All Actions</option>
          <option value="user">User Actions</option>
          <option value="auth">Authentication</option>
          <option value="api">API Access</option>
          <option value="system">System Events</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
        >
          <option value="all">All Status</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
          <option value="warning">Warning</option>
        </select>
        <select
          value={dateRange}
          onChange={(e) => setDateRange(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
        >
          <option value="1h">Last Hour</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </div>

      {/* Logs Table */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Timestamp
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Action
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Resource
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                IP Address
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {logs.map(log => (
              <tr key={log.id} className="hover:bg-gray-700/50">
                <td className="px-6 py-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    {log.timestamp}
                  </div>
                </td>
                <td className="px-6 py-4 text-sm">{log.user}</td>
                <td className="px-6 py-4 text-sm">
                  <div className="flex items-center gap-2">
                    {getActionIcon(log.action)}
                    <span>{log.action}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm">{log.resource}</td>
                <td className="px-6 py-4 text-sm text-gray-400">{log.ip}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(log.status)}
                    <span className={`text-sm ${
                      log.status === 'success' ? 'text-green-500' :
                      log.status === 'failure' ? 'text-red-500' :
                      'text-yellow-500'
                    }`}>
                      {log.status}
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AuditLogs;