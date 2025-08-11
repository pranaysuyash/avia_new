/**
 * User Engagement Analytics Component
 * Task 202: Advanced User Engagement Analytics
 * React component for displaying user behavior analytics and insights
 */

import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { 
  Activity, TrendingUp, Users, Clock, AlertCircle, 
  Target, BarChart2, PieChart as PieChartIcon, Filter,
  Calendar, RefreshCw, Download, Settings
} from 'lucide-react';

interface EngagementMetrics {
  totalUsers: number;
  activeUsers: number;
  totalEvents: number;
  avgSessionDuration: number;
  bounceRate: number;
  retentionRate: number;
}

interface UserBehavior {
  userId: string;
  engagementLevel: 'high' | 'medium' | 'low' | 'inactive';
  lastActivity: string;
  totalSessions: number;
  avgSessionDuration: number;
  preferredFeatures: string[];
}

interface ChurnPrediction {
  userId: string;
  churnProbability: number;
  riskLevel: 'high' | 'medium' | 'low';
  riskFactors: string[];
  recommendations: string[];
}

const UserEngagementAnalytics: React.FC = () => {
  const [activeView, setActiveView] = useState<string>('overview');
  const [dateRange, setDateRange] = useState<string>('7d');
  const [metrics, setMetrics] = useState<EngagementMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);

  // Mock data for charts
  const dailyActiveUsers = [
    { date: 'Mon', users: 1250 },
    { date: 'Tue', users: 1380 },
    { date: 'Wed', users: 1420 },
    { date: 'Thu', users: 1390 },
    { date: 'Fri', users: 1490 },
    { date: 'Sat', users: 1120 },
    { date: 'Sun', users: 980 },
  ];

  const engagementDistribution = [
    { name: 'High', value: 35, color: '#10b981' },
    { name: 'Medium', value: 45, color: '#3b82f6' },
    { name: 'Low', value: 15, color: '#f59e0b' },
    { name: 'Inactive', value: 5, color: '#ef4444' },
  ];

  const featureUsage = [
    { feature: 'Transcription', usage: 89, users: 1234 },
    { feature: 'Translation', usage: 67, users: 932 },
    { feature: 'Summary', usage: 78, users: 1087 },
    { feature: 'Search', usage: 92, users: 1280 },
    { feature: 'Export', usage: 45, users: 626 },
    { feature: 'Share', usage: 56, users: 779 },
  ];

  const sessionMetrics = [
    { hour: '00', sessions: 120 },
    { hour: '03', sessions: 80 },
    { hour: '06', sessions: 150 },
    { hour: '09', sessions: 380 },
    { hour: '12', sessions: 420 },
    { hour: '15', sessions: 390 },
    { hour: '18', sessions: 340 },
    { hour: '21', sessions: 280 },
  ];

  const churnRiskUsers = [
    { 
      name: 'John Doe', 
      risk: 85, 
      lastSeen: '7 days ago',
      sessions: 2,
      reason: 'Decreased activity'
    },
    { 
      name: 'Jane Smith', 
      risk: 72, 
      lastSeen: '5 days ago',
      sessions: 3,
      reason: 'Feature usage decline'
    },
    { 
      name: 'Bob Johnson', 
      risk: 68, 
      lastSeen: '4 days ago',
      sessions: 4,
      reason: 'Support tickets'
    },
  ];

  const behaviorPatterns = [
    { metric: 'Page Views', current: 85, previous: 72 },
    { metric: 'Session Time', current: 92, previous: 88 },
    { metric: 'Feature Usage', current: 78, previous: 71 },
    { metric: 'Engagement', current: 81, previous: 75 },
    { metric: 'Retention', current: 89, previous: 84 },
  ];

  useEffect(() => {
    fetchMetrics();
  }, [dateRange]);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      // In production, this would call the actual API
      const response = await fetch(`/api/v1/analytics/engagement/metrics?range=${dateRange}`);
      if (response.ok) {
        const data = await response.json();
        setMetrics(data.data.overview);
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      // Use mock data for demo
      setMetrics({
        totalUsers: 1432,
        activeUsers: 892,
        totalEvents: 45678,
        avgSessionDuration: 12.5,
        bounceRate: 23.4,
        retentionRate: 76.8,
      });
    } finally {
      setLoading(false);
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Users</p>
              <p className="text-2xl font-bold">{metrics?.totalUsers || 0}</p>
              <p className="text-xs text-green-600">↑ 12% from last period</p>
            </div>
            <Users className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Users</p>
              <p className="text-2xl font-bold">{metrics?.activeUsers || 0}</p>
              <p className="text-xs text-green-600">↑ 8% from last period</p>
            </div>
            <Activity className="h-8 w-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Session</p>
              <p className="text-2xl font-bold">{metrics?.avgSessionDuration || 0}m</p>
              <p className="text-xs text-green-600">↑ 5% from last period</p>
            </div>
            <Clock className="h-8 w-8 text-purple-500" />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Retention Rate</p>
              <p className="text-2xl font-bold">{metrics?.retentionRate || 0}%</p>
              <p className="text-xs text-green-600">↑ 3% from last period</p>
            </div>
            <Target className="h-8 w-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Daily Active Users Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Daily Active Users</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={dailyActiveUsers}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey="users" stroke="#3b82f6" fill="#93c5fd" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Engagement Distribution */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Engagement Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={engagementDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {engagementDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Session Distribution */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Session Distribution by Hour</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sessionMetrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="sessions" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  const renderBehaviorAnalysis = () => (
    <div className="space-y-6">
      {/* Behavior Patterns Radar Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">User Behavior Patterns</h3>
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={behaviorPatterns}>
            <PolarGrid />
            <PolarAngleAxis dataKey="metric" />
            <PolarRadiusAxis angle={90} domain={[0, 100]} />
            <Radar name="Current" dataKey="current" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
            <Radar name="Previous" dataKey="previous" stroke="#6b7280" fill="#6b7280" fillOpacity={0.3} />
            <Legend />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Feature Usage Analysis */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Feature Usage Analysis</h3>
        <div className="space-y-4">
          {featureUsage.map((feature) => (
            <div key={feature.feature} className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">{feature.feature}</span>
                  <span className="text-sm text-gray-600">{feature.users} users</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${feature.usage}%` }}
                  />
                </div>
              </div>
              <span className="ml-4 text-sm font-semibold">{feature.usage}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* User Journey Funnel */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">User Journey Funnel</h3>
        <div className="space-y-2">
          {[
            { stage: 'Sign Up', users: 1000, color: 'bg-blue-500' },
            { stage: 'First Upload', users: 850, color: 'bg-blue-400' },
            { stage: 'First Transcription', users: 720, color: 'bg-blue-300' },
            { stage: 'Regular Usage', users: 540, color: 'bg-green-400' },
            { stage: 'Power User', users: 180, color: 'bg-green-500' },
          ].map((stage, index) => (
            <div key={stage.stage} className="relative">
              <div className="flex items-center">
                <div 
                  className={`${stage.color} text-white px-4 py-2 rounded`}
                  style={{ width: `${(stage.users / 1000) * 100}%` }}
                >
                  <span className="font-medium">{stage.stage}</span>
                  <span className="ml-2 text-sm">({stage.users} users)</span>
                </div>
              </div>
              {index < 4 && (
                <div className="text-xs text-gray-500 mt-1 ml-4">
                  {Math.round((stage.users / 1000) * 100)}% conversion
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderChurnPrevention = () => (
    <div className="space-y-6">
      {/* At-Risk Users */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Users at Risk of Churning</h3>
          <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
            Export List
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Risk Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Seen
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sessions
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Risk Reason
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {churnRiskUsers.map((user) => (
                <tr key={user.name}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {user.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className={`text-sm font-medium ${
                        user.risk >= 80 ? 'text-red-600' : user.risk >= 60 ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {user.risk}%
                      </span>
                      <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            user.risk >= 80 ? 'bg-red-500' : user.risk >= 60 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${user.risk}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.lastSeen}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.sessions}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.reason}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button className="text-blue-600 hover:text-blue-900">
                      Contact
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Churn Prevention Recommendations */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Churn Prevention Strategies</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              title: 'Re-engagement Campaign',
              description: 'Send personalized emails to inactive users',
              impact: 'High',
              users: 234,
              color: 'bg-green-100 text-green-800',
            },
            {
              title: 'Feature Tutorial',
              description: 'Provide guided tours for underutilized features',
              impact: 'Medium',
              users: 156,
              color: 'bg-yellow-100 text-yellow-800',
            },
            {
              title: 'Customer Success Outreach',
              description: 'Personal consultation for at-risk accounts',
              impact: 'High',
              users: 89,
              color: 'bg-green-100 text-green-800',
            },
            {
              title: 'Incentive Program',
              description: 'Offer credits or discounts to encourage usage',
              impact: 'Medium',
              users: 123,
              color: 'bg-yellow-100 text-yellow-800',
            },
          ].map((strategy) => (
            <div key={strategy.title} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium">{strategy.title}</h4>
                <span className={`px-2 py-1 text-xs rounded-full ${strategy.color}`}>
                  {strategy.impact} Impact
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3">{strategy.description}</p>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">
                  Affects {strategy.users} users
                </span>
                <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                  Launch →
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <BarChart2 className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">User Engagement Analytics</h1>
            </div>
            <div className="flex items-center space-x-4">
              {/* Date Range Selector */}
              <select 
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
              </select>
              
              <button 
                onClick={fetchMetrics}
                className="p-2 text-gray-600 hover:text-gray-900"
              >
                <RefreshCw className="h-5 w-5" />
              </button>
              
              <button className="p-2 text-gray-600 hover:text-gray-900">
                <Download className="h-5 w-5" />
              </button>
              
              <button className="p-2 text-gray-600 hover:text-gray-900">
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
          
          {/* Navigation Tabs */}
          <div className="flex space-x-8 border-b">
            {[
              { id: 'overview', label: 'Overview', icon: Activity },
              { id: 'behavior', label: 'Behavior Analysis', icon: Users },
              { id: 'churn', label: 'Churn Prevention', icon: AlertCircle },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveView(tab.id)}
                className={`flex items-center space-x-2 py-3 px-1 border-b-2 transition-colors ${
                  activeView === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="h-5 w-5" />
                <span className="font-medium">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {activeView === 'overview' && renderOverview()}
            {activeView === 'behavior' && renderBehaviorAnalysis()}
            {activeView === 'churn' && renderChurnPrevention()}
          </>
        )}
      </div>
    </div>
  );
};

export default UserEngagementAnalytics;