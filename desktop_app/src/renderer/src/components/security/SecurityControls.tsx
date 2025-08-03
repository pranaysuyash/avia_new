import React, { useState } from 'react';
import {
  Shield,
  Lock,
  Key,
  Smartphone,
  Globe,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  Download,
  Upload,
  RefreshCw,
  UserCheck,
  FileText,
  Activity,
  Settings,
  Ban,
  Unlock,
  ShieldCheck,
  ShieldAlert
} from 'lucide-react';

interface SecurityPolicy {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  lastModified: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface SecurityEvent {
  id: string;
  type: 'login_attempt' | 'permission_change' | 'data_access' | 'security_alert';
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  user?: string;
  ip?: string;
  timestamp: string;
}

interface IPRule {
  id: string;
  ip: string;
  type: 'whitelist' | 'blacklist';
  reason: string;
  addedBy: string;
  addedAt: string;
}

// Helper functions
const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return 'text-red-400';
    case 'warning': return 'text-yellow-400';
    case 'error': return 'text-orange-400';
    default: return 'text-blue-400';
  }
};

const getSeverityBadge = (severity: string) => {
  const colors = {
    critical: 'bg-red-900/50 text-red-400',
    warning: 'bg-yellow-900/50 text-yellow-400',
    error: 'bg-orange-900/50 text-orange-400',
    info: 'bg-blue-900/50 text-blue-400'
  };
  
  return (
    <span className={`px-2 py-1 text-xs rounded ${colors[severity as keyof typeof colors] || colors.info}`}>
      {severity}
    </span>
  );
};

export const SecurityControls: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'policies' | 'access' | 'monitoring' | 'compliance'>('overview');
  
  const [securityPolicies] = useState<SecurityPolicy[]>([
    {
      id: '1',
      name: 'Two-Factor Authentication',
      description: 'Require 2FA for all user accounts',
      enabled: true,
      lastModified: '2024-03-15',
      severity: 'high'
    },
    {
      id: '2',
      name: 'Password Complexity',
      description: 'Enforce strong password requirements',
      enabled: true,
      lastModified: '2024-03-10',
      severity: 'high'
    },
    {
      id: '3',
      name: 'Session Timeout',
      description: 'Auto-logout after 30 minutes of inactivity',
      enabled: true,
      lastModified: '2024-03-01',
      severity: 'medium'
    },
    {
      id: '4',
      name: 'IP Whitelisting',
      description: 'Restrict access to specific IP addresses',
      enabled: false,
      lastModified: '2024-02-28',
      severity: 'medium'
    }
  ]);

  const [recentEvents] = useState<SecurityEvent[]>([
    {
      id: '1',
      type: 'login_attempt',
      severity: 'warning',
      message: 'Failed login attempt from unknown location',
      user: 'john@example.com',
      ip: '192.168.1.100',
      timestamp: '2024-03-20 14:32:15'
    },
    {
      id: '2',
      type: 'permission_change',
      severity: 'info',
      message: 'User role updated from Member to Admin',
      user: 'admin@example.com',
      timestamp: '2024-03-20 13:15:42'
    },
    {
      id: '3',
      type: 'security_alert',
      severity: 'critical',
      message: 'Multiple failed login attempts detected',
      ip: '10.0.0.50',
      timestamp: '2024-03-20 12:45:00'
    }
  ]);

  const [ipRules] = useState<IPRule[]>([
    {
      id: '1',
      ip: '192.168.1.0/24',
      type: 'whitelist',
      reason: 'Office network',
      addedBy: 'admin@example.com',
      addedAt: '2024-01-15'
    },
    {
      id: '2',
      ip: '10.0.0.50',
      type: 'blacklist',
      reason: 'Suspicious activity detected',
      addedBy: 'security@example.com',
      addedAt: '2024-03-20'
    }
  ]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Shield },
    { id: 'policies', label: 'Security Policies', icon: FileText },
    { id: 'access', label: 'Access Control', icon: Lock },
    { id: 'monitoring', label: 'Monitoring', icon: Activity },
    { id: 'compliance', label: 'Compliance', icon: ShieldCheck }
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
      case 'info':
        return 'text-blue-500';
      case 'medium':
      case 'warning':
        return 'text-yellow-500';
      case 'high':
      case 'error':
        return 'text-orange-500';
      case 'critical':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getSeverityBadge = (severity: string) => {
    const color = getSeverityColor(severity);
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${
        severity === 'critical' || severity === 'high' ? 'bg-red-900/50' :
        severity === 'medium' || severity === 'warning' ? 'bg-yellow-900/50' :
        severity === 'error' ? 'bg-orange-900/50' :
        'bg-blue-900/50'
      } ${color}`}>
        {severity.toUpperCase()}
      </span>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold flex items-center gap-2">
              <Shield className="w-6 h-6 text-blue-500" />
              Security Controls
            </h1>
            <p className="text-gray-400 mt-1">Manage security settings and monitor threats</p>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            <Download className="w-4 h-4" />
            Export Security Report
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mt-6">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'hover:bg-gray-800 text-gray-400'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'overview' && <SecurityOverview events={recentEvents} />}
        {activeTab === 'policies' && <SecurityPolicies policies={securityPolicies} />}
        {activeTab === 'access' && <AccessControl ipRules={ipRules} />}
        {activeTab === 'monitoring' && <SecurityMonitoring />}
        {activeTab === 'compliance' && <ComplianceCenter />}
      </div>
    </div>
  );
};

// Overview Component
const SecurityOverview: React.FC<{ events: SecurityEvent[] }> = ({ events }) => {
  const securityScore = 85; // Example score

  return (
    <div className="p-6">
      {/* Security Score */}
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Security Health Score</h3>
        <div className="flex items-center gap-6">
          <div className="relative w-32 h-32">
            <svg className="w-32 h-32 transform -rotate-90">
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke="#374151"
                strokeWidth="12"
                fill="none"
              />
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke="#10b981"
                strokeWidth="12"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 56}`}
                strokeDashoffset={`${2 * Math.PI * 56 * (1 - securityScore / 100)}`}
                className="transition-all duration-1000"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-3xl font-bold">{securityScore}%</span>
            </div>
          </div>
          <div className="flex-1">
            <p className="text-gray-400 mb-2">Your security score is based on:</p>
            <ul className="space-y-1 text-sm">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Strong password policies enabled
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Two-factor authentication active
              </li>
              <li className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                3 security policies need review
              </li>
              <li className="flex items-center gap-2">
                <XCircle className="w-4 h-4 text-red-500" />
                IP whitelisting disabled
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <UserCheck className="w-8 h-8 text-green-500" />
            <span className="text-2xl font-bold">156</span>
          </div>
          <div className="text-sm text-gray-400">Secure Logins Today</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <ShieldAlert className="w-8 h-8 text-yellow-500" />
            <span className="text-2xl font-bold">12</span>
          </div>
          <div className="text-sm text-gray-400">Security Alerts</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Ban className="w-8 h-8 text-red-500" />
            <span className="text-2xl font-bold">3</span>
          </div>
          <div className="text-sm text-gray-400">Blocked IPs</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Key className="w-8 h-8 text-blue-500" />
            <span className="text-2xl font-bold">98%</span>
          </div>
          <div className="text-sm text-gray-400">Users with 2FA</div>
        </div>
      </div>

      {/* Recent Security Events */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Security Events</h3>
        <div className="space-y-3">
          {events.map(event => (
            <div key={event.id} className="flex items-start gap-3 p-3 bg-gray-900 rounded">
              <div className={`p-2 rounded ${
                event.severity === 'critical' ? 'bg-red-900/50' :
                event.severity === 'warning' ? 'bg-yellow-900/50' :
                event.severity === 'error' ? 'bg-orange-900/50' :
                'bg-blue-900/50'
              }`}>
                <AlertTriangle className={`w-4 h-4 ${getSeverityColor(event.severity)}`} />
              </div>
              <div className="flex-1">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium">{event.message}</p>
                    <div className="flex items-center gap-3 mt-1 text-sm text-gray-400">
                      {event.user && <span>User: {event.user}</span>}
                      {event.ip && <span>IP: {event.ip}</span>}
                      <span>{event.timestamp}</span>
                    </div>
                  </div>
                  {getSeverityBadge(event.severity)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Security Policies Component
const SecurityPolicies: React.FC<{ policies: SecurityPolicy[] }> = ({ policies }) => {
  return (
    <div className="p-6">
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold">Security Policies</h3>
        </div>
        <div className="divide-y divide-gray-700">
          {policies.map(policy => (
            <div key={policy.id} className="p-4 hover:bg-gray-700/50">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h4 className="font-medium">{policy.name}</h4>
                    {getSeverityBadge(policy.severity)}
                  </div>
                  <p className="text-sm text-gray-400 mb-2">{policy.description}</p>
                  <p className="text-xs text-gray-500">Last modified: {policy.lastModified}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={policy.enabled}
                    className="sr-only peer"
                    onChange={() => {}}
                  />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Access Control Component
const AccessControl: React.FC<{ ipRules: IPRule[] }> = ({ ipRules }) => {
  const [showAddIP, setShowAddIP] = useState(false);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">IP Access Rules</h3>
        <button
          onClick={() => setShowAddIP(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Add IP Rule
        </button>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Whitelisted IPs */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="font-medium mb-3 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Whitelisted IPs
          </h4>
          <div className="space-y-2">
            {ipRules.filter(rule => rule.type === 'whitelist').map(rule => (
              <div key={rule.id} className="p-3 bg-gray-900 rounded">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-mono text-sm">{rule.ip}</p>
                    <p className="text-xs text-gray-400 mt-1">{rule.reason}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Added by {rule.addedBy} on {rule.addedAt}
                    </p>
                  </div>
                  <button className="text-red-400 hover:text-red-300">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Blacklisted IPs */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="font-medium mb-3 flex items-center gap-2">
            <Ban className="w-5 h-5 text-red-500" />
            Blacklisted IPs
          </h4>
          <div className="space-y-2">
            {ipRules.filter(rule => rule.type === 'blacklist').map(rule => (
              <div key={rule.id} className="p-3 bg-gray-900 rounded">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-mono text-sm">{rule.ip}</p>
                    <p className="text-xs text-gray-400 mt-1">{rule.reason}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Added by {rule.addedBy} on {rule.addedAt}
                    </p>
                  </div>
                  <button className="text-red-400 hover:text-red-300">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Session Management */}
      <div className="mt-6 bg-gray-800 rounded-lg p-6">
        <h4 className="font-medium mb-4">Active Sessions</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gray-900 rounded">
            <div className="flex items-center gap-3">
              <Smartphone className="w-5 h-5 text-gray-400" />
              <div>
                <p className="font-medium">Chrome on MacOS</p>
                <p className="text-sm text-gray-400">192.168.1.100 • San Francisco, CA</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Active now</span>
              <button className="text-red-400 hover:text-red-300 text-sm">Revoke</button>
            </div>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-900 rounded">
            <div className="flex items-center gap-3">
              <Globe className="w-5 h-5 text-gray-400" />
              <div>
                <p className="font-medium">API Access</p>
                <p className="text-sm text-gray-400">Production Server • AWS us-west-2</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Last used 1h ago</span>
              <button className="text-red-400 hover:text-red-300 text-sm">Revoke</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Security Monitoring Component
const SecurityMonitoring: React.FC = () => {
  return (
    <div className="p-6">
      <div className="grid grid-cols-2 gap-6">
        {/* Real-time Threats */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-red-500" />
            Real-time Threat Detection
          </h3>
          <div className="space-y-3">
            <div className="p-3 bg-red-900/20 border border-red-700 rounded">
              <div className="flex items-start justify-between mb-1">
                <span className="font-medium text-red-400">Brute Force Attack Detected</span>
                <span className="text-xs text-gray-400">2 min ago</span>
              </div>
              <p className="text-sm text-gray-300">Multiple failed login attempts from IP 10.0.0.50</p>
              <div className="flex gap-2 mt-2">
                <button className="text-xs px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">
                  Block IP
                </button>
                <button className="text-xs px-2 py-1 bg-gray-700 text-white rounded hover:bg-gray-600">
                  View Details
                </button>
              </div>
            </div>
            <div className="p-3 bg-yellow-900/20 border border-yellow-700 rounded">
              <div className="flex items-start justify-between mb-1">
                <span className="font-medium text-yellow-400">Unusual Access Pattern</span>
                <span className="text-xs text-gray-400">15 min ago</span>
              </div>
              <p className="text-sm text-gray-300">User accessing data from new location</p>
            </div>
          </div>
        </div>

        {/* Security Metrics */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Security Metrics (24h)</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Login Success Rate</span>
                <span>94%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '94%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Blocked Threats</span>
                <span>23</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-red-500 h-2 rounded-full" style={{ width: '23%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Suspicious Activities</span>
                <span>7</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '7%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Compliance Center Component
const ComplianceCenter: React.FC = () => {
  const complianceItems = [
    { name: 'GDPR', status: 'compliant', lastAudit: '2024-02-15' },
    { name: 'HIPAA', status: 'compliant', lastAudit: '2024-01-20' },
    { name: 'SOC 2', status: 'in-progress', lastAudit: '2024-03-01' },
    { name: 'ISO 27001', status: 'non-compliant', lastAudit: '2023-12-10' }
  ];

  return (
    <div className="p-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Compliance Status</h3>
        <div className="space-y-4">
          {complianceItems.map(item => (
            <div key={item.name} className="flex items-center justify-between p-4 bg-gray-900 rounded">
              <div className="flex items-center gap-4">
                <div className={`p-2 rounded ${
                  item.status === 'compliant' ? 'bg-green-900/50' :
                  item.status === 'in-progress' ? 'bg-yellow-900/50' :
                  'bg-red-900/50'
                }`}>
                  {item.status === 'compliant' ? 
                    <CheckCircle className="w-5 h-5 text-green-500" /> :
                    item.status === 'in-progress' ?
                    <RefreshCw className="w-5 h-5 text-yellow-500" /> :
                    <XCircle className="w-5 h-5 text-red-500" />
                  }
                </div>
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-sm text-gray-400">Last audit: {item.lastAudit}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-2 py-1 text-xs rounded-full ${
                  item.status === 'compliant' ? 'bg-green-900/50 text-green-400' :
                  item.status === 'in-progress' ? 'bg-yellow-900/50 text-yellow-400' :
                  'bg-red-900/50 text-red-400'
                }`}>
                  {item.status.replace('-', ' ').toUpperCase()}
                </span>
                <button className="text-blue-400 hover:text-blue-300 text-sm">
                  View Report
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SecurityControls;

// Missing import
import { Plus, Trash2 } from 'lucide-react';