import React, { useState } from 'react';
import {
  Shield,
  Users,
  Database,
  Activity,
  Settings,
  AlertCircle,
  BarChart3,
  Server,
  Key,
  FileText,
  Bell,
  Package,
  Zap,
  HardDrive,
  Globe,
  Lock
} from 'lucide-react';
import SystemMetrics from './SystemMetrics';
import UserManagement from './UserManagement';
import DatabaseManagement from './DatabaseManagement';
import AuditLogs from './AuditLogs';
import SystemSettings from './SystemSettings';
import APIManagement from './APIManagement';

type AdminSection = 
  | 'overview'
  | 'users'
  | 'database'
  | 'metrics'
  | 'audit'
  | 'api'
  | 'settings';

interface SystemStats {
  totalUsers: number;
  activeUsers: number;
  totalTranscriptions: number;
  storageUsed: number;
  apiCalls: number;
  systemHealth: 'healthy' | 'warning' | 'critical';
}

export const AdminPanel: React.FC = () => {
  const [activeSection, setActiveSection] = useState<AdminSection>('overview');
  const [systemStats] = useState<SystemStats>({
    totalUsers: 1245,
    activeUsers: 342,
    totalTranscriptions: 45678,
    storageUsed: 2.4, // TB
    apiCalls: 1234567,
    systemHealth: 'healthy'
  });

  const menuItems = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'users', label: 'User Management', icon: Users },
    { id: 'database', label: 'Database', icon: Database },
    { id: 'metrics', label: 'System Metrics', icon: Activity },
    { id: 'audit', label: 'Audit Logs', icon: FileText },
    { id: 'api', label: 'API Management', icon: Key },
    { id: 'settings', label: 'System Settings', icon: Settings }
  ];

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy':
        return 'text-green-500';
      case 'warning':
        return 'text-yellow-500';
      case 'critical':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const renderContent = () => {
    switch (activeSection) {
      case 'overview':
        return <AdminOverview stats={systemStats} />;
      case 'users':
        return <UserManagement />;
      case 'database':
        return <DatabaseManagement />;
      case 'metrics':
        return <SystemMetrics />;
      case 'audit':
        return <AuditLogs />;
      case 'api':
        return <APIManagement />;
      case 'settings':
        return <SystemSettings />;
      default:
        return <AdminOverview stats={systemStats} />;
    }
  };

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 border-r border-gray-700">
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-blue-500" />
            <h1 className="text-xl font-semibold">Admin Panel</h1>
          </div>
          <p className="text-sm text-gray-400 mt-1">System Administration</p>
        </div>

        <nav className="p-4">
          <ul className="space-y-2">
            {menuItems.map(item => (
              <li key={item.id}>
                <button
                  onClick={() => setActiveSection(item.id as AdminSection)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition ${
                    activeSection === item.id
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-700 text-gray-300'
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* System Health */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">System Health</span>
            <span className={`text-sm font-medium ${getHealthColor(systemStats.systemHealth)}`}>
              {systemStats.systemHealth.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        {renderContent()}
      </div>
    </div>
  );
};

interface AdminOverviewProps {
  stats: SystemStats;
}

const AdminOverview: React.FC<AdminOverviewProps> = ({ stats }) => {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-semibold mb-6">System Overview</h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={Users}
          label="Total Users"
          value={stats.totalUsers.toLocaleString()}
          change="+12%"
          positive
        />
        <StatCard
          icon={Activity}
          label="Active Users"
          value={stats.activeUsers.toLocaleString()}
          subtext="Last 24 hours"
        />
        <StatCard
          icon={FileText}
          label="Transcriptions"
          value={stats.totalTranscriptions.toLocaleString()}
          change="+23%"
          positive
        />
        <StatCard
          icon={HardDrive}
          label="Storage Used"
          value={`${stats.storageUsed} TB`}
          subtext="of 10 TB"
        />
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-4 gap-4">
          <QuickActionCard
            icon={Bell}
            label="Send Announcement"
            description="Notify all users"
            onClick={() => {}}
          />
          <QuickActionCard
            icon={Package}
            label="System Backup"
            description="Create backup now"
            onClick={() => {}}
          />
          <QuickActionCard
            icon={Zap}
            label="Clear Cache"
            description="Free up memory"
            onClick={() => {}}
          />
          <QuickActionCard
            icon={Lock}
            label="Security Scan"
            description="Run security audit"
            onClick={() => {}}
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Recent System Events</h3>
          <div className="space-y-3">
            <EventItem
              type="info"
              message="Database backup completed successfully"
              time="5 minutes ago"
            />
            <EventItem
              type="warning"
              message="High API usage detected from IP 192.168.1.1"
              time="1 hour ago"
            />
            <EventItem
              type="success"
              message="System update installed successfully"
              time="3 hours ago"
            />
            <EventItem
              type="error"
              message="Failed login attempt from unknown location"
              time="5 hours ago"
            />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">API Usage</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Transcription API</span>
                <span>78%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '78%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Search API</span>
                <span>45%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '45%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Analytics API</span>
                <span>32%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-purple-500 h-2 rounded-full" style={{ width: '32%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

interface StatCardProps {
  icon: React.FC<{ className?: string }>;
  label: string;
  value: string;
  change?: string;
  positive?: boolean;
  subtext?: string;
}

const StatCard: React.FC<StatCardProps> = ({ icon: Icon, label, value, change, positive, subtext }) => (
  <div className="bg-gray-800 rounded-lg p-6">
    <div className="flex items-start justify-between mb-4">
      <div className={`p-2 rounded-lg ${positive ? 'bg-green-900/50' : 'bg-gray-700'}`}>
        <Icon className={`w-6 h-6 ${positive ? 'text-green-500' : 'text-gray-400'}`} />
      </div>
      {change && (
        <span className={`text-sm font-medium ${positive ? 'text-green-500' : 'text-red-500'}`}>
          {change}
        </span>
      )}
    </div>
    <div className="text-2xl font-bold mb-1">{value}</div>
    <div className="text-sm text-gray-400">{label}</div>
    {subtext && <div className="text-xs text-gray-500 mt-1">{subtext}</div>}
  </div>
);

interface QuickActionCardProps {
  icon: React.FC<{ className?: string }>;
  label: string;
  description: string;
  onClick: () => void;
}

const QuickActionCard: React.FC<QuickActionCardProps> = ({ icon: Icon, label, description, onClick }) => (
  <button
    onClick={onClick}
    className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700 transition text-left"
  >
    <Icon className="w-8 h-8 text-blue-500 mb-2" />
    <div className="font-medium">{label}</div>
    <div className="text-xs text-gray-400">{description}</div>
  </button>
);

interface EventItemProps {
  type: 'info' | 'warning' | 'success' | 'error';
  message: string;
  time: string;
}

const EventItem: React.FC<EventItemProps> = ({ type, message, time }) => {
  const getTypeColor = () => {
    switch (type) {
      case 'info':
        return 'text-blue-500 bg-blue-900/20';
      case 'warning':
        return 'text-yellow-500 bg-yellow-900/20';
      case 'success':
        return 'text-green-500 bg-green-900/20';
      case 'error':
        return 'text-red-500 bg-red-900/20';
    }
  };

  return (
    <div className="flex items-start gap-3">
      <div className={`p-1 rounded ${getTypeColor()}`}>
        <AlertCircle className="w-4 h-4" />
      </div>
      <div className="flex-1">
        <p className="text-sm">{message}</p>
        <p className="text-xs text-gray-500 mt-1">{time}</p>
      </div>
    </div>
  );
};

export default AdminPanel;