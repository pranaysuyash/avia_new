import React, { useState } from 'react';
import {
  Users,
  Search,
  Filter,
  UserPlus,
  MoreVertical,
  Shield,
  Ban,
  Check,
  X,
  Mail,
  Calendar,
  Activity,
  CreditCard
} from 'lucide-react';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'developer';
  status: 'active' | 'suspended' | 'pending';
  plan: 'free' | 'pro' | 'enterprise';
  createdAt: string;
  lastActive: string;
  usage: {
    transcriptions: number;
    storage: number; // MB
    apiCalls: number;
  };
}

export const UserManagement: React.FC = () => {
  const [users] = useState<User[]>([
    {
      id: '1',
      name: 'John Doe',
      email: 'john@example.com',
      role: 'admin',
      status: 'active',
      plan: 'enterprise',
      createdAt: '2024-01-15',
      lastActive: '2024-03-20',
      usage: { transcriptions: 234, storage: 1024, apiCalls: 5432 }
    },
    // Add more mock users...
  ]);

  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-900/50 text-green-400 border-green-700';
      case 'suspended':
        return 'bg-red-900/50 text-red-400 border-red-700';
      case 'pending':
        return 'bg-yellow-900/50 text-yellow-400 border-yellow-700';
      default:
        return 'bg-gray-900/50 text-gray-400 border-gray-700';
    }
  };

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case 'free':
        return 'text-gray-400';
      case 'pro':
        return 'text-blue-400';
      case 'enterprise':
        return 'text-purple-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">User Management</h2>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          <UserPlus className="w-4 h-4" />
          Add User
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
            placeholder="Search users..."
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
          />
        </div>
        <select
          value={filterRole}
          onChange={(e) => setFilterRole(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
        >
          <option value="all">All Roles</option>
          <option value="admin">Admin</option>
          <option value="user">User</option>
          <option value="developer">Developer</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="pending">Pending</option>
        </select>
      </div>

      {/* Users Table */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Role & Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Plan
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Usage
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Activity
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {users.map(user => (
              <tr key={user.id} className="hover:bg-gray-700/50">
                <td className="px-6 py-4">
                  <div>
                    <div className="text-sm font-medium">{user.name}</div>
                    <div className="text-sm text-gray-400">{user.email}</div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    {user.role === 'admin' && <Shield className="w-4 h-4 text-blue-500" />}
                    <span className="text-sm capitalize">{user.role}</span>
                  </div>
                  <span className={`inline-block mt-1 px-2 py-1 text-xs rounded-full border ${getStatusColor(user.status)}`}>
                    {user.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`text-sm font-medium ${getPlanColor(user.plan)}`}>
                    {user.plan.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm">
                    <div>{user.usage.transcriptions} transcriptions</div>
                    <div className="text-gray-400">{(user.usage.storage / 1024).toFixed(1)} GB</div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-gray-400" />
                      {new Date(user.createdAt).toLocaleDateString()}
                    </div>
                    <div className="flex items-center gap-1 text-gray-400">
                      <Activity className="w-3 h-3" />
                      {new Date(user.lastActive).toLocaleDateString()}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => setSelectedUser(user)}
                    className="text-gray-400 hover:text-white"
                  >
                    <MoreVertical className="w-5 h-5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* User Actions Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">User Actions</h3>
            <div className="space-y-3">
              <button className="w-full flex items-center gap-3 p-3 hover:bg-gray-800 rounded transition">
                <Mail className="w-5 h-5" />
                <span>Send Email</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 hover:bg-gray-800 rounded transition">
                <CreditCard className="w-5 h-5" />
                <span>Change Plan</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 hover:bg-gray-800 rounded transition">
                <Shield className="w-5 h-5" />
                <span>Change Role</span>
              </button>
              {selectedUser.status === 'active' ? (
                <button className="w-full flex items-center gap-3 p-3 hover:bg-red-900/20 text-red-400 rounded transition">
                  <Ban className="w-5 h-5" />
                  <span>Suspend User</span>
                </button>
              ) : (
                <button className="w-full flex items-center gap-3 p-3 hover:bg-green-900/20 text-green-400 rounded transition">
                  <Check className="w-5 h-5" />
                  <span>Activate User</span>
                </button>
              )}
            </div>
            <button
              onClick={() => setSelectedUser(null)}
              className="mt-4 w-full py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;