/**
 * User Engagement Analytics Component - Electron
 * Task 202: Advanced User Engagement Analytics
 * Desktop app component for user behavior analytics
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  Treemap, Sankey
} from 'recharts';
import './UserEngagementAnalytics.css';

const { ipcRenderer } = window.require('electron');

interface AnalyticsData {
  metrics: {
    totalUsers: number;
    activeUsers: number;
    avgSessionDuration: number;
    bounceRate: number;
    retentionRate: number;
    conversionRate: number;
  };
  dailyActiveUsers: Array<{ date: string; users: number }>;
  engagementDistribution: Array<{ name: string; value: number; color: string }>;
  userJourneyFunnel: Array<{ stage: string; users: number; conversion: number }>;
  featureUsage: Array<{ feature: string; usage: number; trend: number }>;
  churnRiskUsers: Array<{
    id: string;
    name: string;
    email: string;
    riskScore: number;
    lastActivity: string;
    predictedChurnDate: string;
    factors: string[];
  }>;
}

const UserEngagementAnalytics: React.FC = () => {
  const [activeView, setActiveView] = useState<'overview' | 'behavior' | 'journey' | 'churn' | 'realtime'>('overview');
  const [dateRange, setDateRange] = useState<string>('7d');
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedMetric, setSelectedMetric] = useState<string>('users');
  const [realtimeData, setRealtimeData] = useState<any[]>([]);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'csv' | 'json'>('pdf');

  // Initialize IPC listeners
  useEffect(() => {
    // Listen for analytics updates
    ipcRenderer.on('analytics-update', (event, data) => {
      setAnalyticsData(data);
    });

    // Listen for realtime data
    ipcRenderer.on('realtime-analytics', (event, data) => {
      setRealtimeData(prev => [...prev.slice(-59), data]);
    });

    // Request initial data
    fetchAnalytics();

    return () => {
      ipcRenderer.removeAllListeners('analytics-update');
      ipcRenderer.removeAllListeners('realtime-analytics');
    };
  }, []);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ipcRenderer.invoke('fetch-analytics', { dateRange });
      setAnalyticsData(data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      // Use mock data for demo
      setAnalyticsData(getMockData());
    } finally {
      setLoading(false);
    }
  }, [dateRange]);

  const getMockData = (): AnalyticsData => ({
    metrics: {
      totalUsers: 15432,
      activeUsers: 8921,
      avgSessionDuration: 14.7,
      bounceRate: 21.3,
      retentionRate: 78.5,
      conversionRate: 34.2,
    },
    dailyActiveUsers: [
      { date: '2025-08-01', users: 1250 },
      { date: '2025-08-02', users: 1380 },
      { date: '2025-08-03', users: 1420 },
      { date: '2025-08-04', users: 1390 },
      { date: '2025-08-05', users: 1490 },
      { date: '2025-08-06', users: 1120 },
      { date: '2025-08-07', users: 980 },
    ],
    engagementDistribution: [
      { name: 'Highly Engaged', value: 35, color: '#10b981' },
      { name: 'Moderately Engaged', value: 45, color: '#3b82f6' },
      { name: 'Low Engagement', value: 15, color: '#f59e0b' },
      { name: 'At Risk', value: 5, color: '#ef4444' },
    ],
    userJourneyFunnel: [
      { stage: 'Sign Up', users: 10000, conversion: 100 },
      { stage: 'First Upload', users: 8500, conversion: 85 },
      { stage: 'First Transcription', users: 7200, conversion: 72 },
      { stage: 'Regular Usage', users: 5400, conversion: 54 },
      { stage: 'Power User', users: 1800, conversion: 18 },
    ],
    featureUsage: [
      { feature: 'Transcription', usage: 89, trend: 5 },
      { feature: 'Translation', usage: 67, trend: -3 },
      { feature: 'Summary', usage: 78, trend: 12 },
      { feature: 'Search', usage: 92, trend: 8 },
      { feature: 'Export', usage: 45, trend: -2 },
      { feature: 'Share', usage: 56, trend: 15 },
    ],
    churnRiskUsers: [
      {
        id: '1',
        name: 'John Doe',
        email: 'john@example.com',
        riskScore: 85,
        lastActivity: '2025-08-01',
        predictedChurnDate: '2025-08-15',
        factors: ['Decreased usage', 'Support tickets', 'Failed payments'],
      },
      {
        id: '2',
        name: 'Jane Smith',
        email: 'jane@example.com',
        riskScore: 72,
        lastActivity: '2025-08-03',
        predictedChurnDate: '2025-08-20',
        factors: ['Feature abandonment', 'Session decline'],
      },
    ],
  });

  const handleExport = () => {
    ipcRenderer.send('export-analytics', {
      format: exportFormat,
      data: analyticsData,
      dateRange,
    });
  };

  const handleUserIntervention = (userId: string) => {
    ipcRenderer.send('trigger-intervention', { userId });
  };

  const renderOverview = () => {
    if (!analyticsData) return null;

    return (
      <div className="analytics-overview">
        {/* Key Metrics */}
        <div className="metrics-grid">
          <div className="metric-card primary">
            <div className="metric-icon">👥</div>
            <div className="metric-content">
              <div className="metric-value">{analyticsData.metrics.totalUsers.toLocaleString()}</div>
              <div className="metric-label">Total Users</div>
              <div className="metric-change positive">↑ 12.5%</div>
            </div>
          </div>
          <div className="metric-card success">
            <div className="metric-icon">📈</div>
            <div className="metric-content">
              <div className="metric-value">{analyticsData.metrics.activeUsers.toLocaleString()}</div>
              <div className="metric-label">Active Users</div>
              <div className="metric-change positive">↑ 8.3%</div>
            </div>
          </div>
          <div className="metric-card info">
            <div className="metric-icon">⏱️</div>
            <div className="metric-content">
              <div className="metric-value">{analyticsData.metrics.avgSessionDuration} min</div>
              <div className="metric-label">Avg Session</div>
              <div className="metric-change positive">↑ 5.2%</div>
            </div>
          </div>
          <div className="metric-card warning">
            <div className="metric-icon">🎯</div>
            <div className="metric-content">
              <div className="metric-value">{analyticsData.metrics.retentionRate}%</div>
              <div className="metric-label">Retention Rate</div>
              <div className="metric-change positive">↑ 3.1%</div>
            </div>
          </div>
        </div>

        {/* Daily Active Users Chart */}
        <div className="chart-container">
          <div className="chart-header">
            <h3>Daily Active Users Trend</h3>
            <div className="chart-controls">
              <button className="chart-btn" onClick={() => setSelectedMetric('users')}>Users</button>
              <button className="chart-btn" onClick={() => setSelectedMetric('sessions')}>Sessions</button>
              <button className="chart-btn" onClick={() => setSelectedMetric('events')}>Events</button>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={analyticsData.dailyActiveUsers}>
              <defs>
                <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="users" stroke="#3b82f6" fillOpacity={1} fill="url(#colorUsers)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="charts-row">
          {/* Engagement Distribution */}
          <div className="chart-container half">
            <h3>Engagement Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analyticsData.engagementDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {analyticsData.engagementDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Feature Usage */}
          <div className="chart-container half">
            <h3>Feature Usage Analysis</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analyticsData.featureUsage} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="feature" type="category" />
                <Tooltip />
                <Bar dataKey="usage" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };

  const renderUserJourney = () => {
    if (!analyticsData) return null;

    return (
      <div className="user-journey">
        <div className="chart-container">
          <h3>User Journey Funnel</h3>
          <div className="funnel-chart">
            {analyticsData.userJourneyFunnel.map((stage, index) => (
              <div key={stage.stage} className="funnel-stage">
                <div 
                  className="funnel-bar"
                  style={{
                    width: `${stage.conversion}%`,
                    backgroundColor: `hsl(${220 - index * 20}, 70%, 50%)`,
                  }}
                >
                  <div className="funnel-content">
                    <span className="funnel-stage-name">{stage.stage}</span>
                    <span className="funnel-users">{stage.users.toLocaleString()} users</span>
                  </div>
                </div>
                {index < analyticsData.userJourneyFunnel.length - 1 && (
                  <div className="funnel-conversion">
                    {stage.conversion}% conversion
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* User Flow Sankey Diagram would go here */}
        <div className="chart-container">
          <h3>User Flow Patterns</h3>
          <div className="flow-diagram">
            {/* Placeholder for Sankey diagram */}
            <p>User flow visualization showing navigation patterns</p>
          </div>
        </div>
      </div>
    );
  };

  const renderChurnAnalysis = () => {
    if (!analyticsData) return null;

    return (
      <div className="churn-analysis">
        <div className="churn-header">
          <h2>Churn Risk Analysis</h2>
          <button className="export-btn" onClick={handleExport}>
            Export Report
          </button>
        </div>

        <div className="churn-summary">
          <div className="summary-card danger">
            <div className="summary-value">{analyticsData.churnRiskUsers.filter(u => u.riskScore >= 80).length}</div>
            <div className="summary-label">High Risk Users</div>
          </div>
          <div className="summary-card warning">
            <div className="summary-value">{analyticsData.churnRiskUsers.filter(u => u.riskScore >= 60 && u.riskScore < 80).length}</div>
            <div className="summary-label">Medium Risk Users</div>
          </div>
          <div className="summary-card success">
            <div className="summary-value">{analyticsData.churnRiskUsers.filter(u => u.riskScore < 60).length}</div>
            <div className="summary-label">Low Risk Users</div>
          </div>
        </div>

        <div className="churn-users-table">
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Risk Score</th>
                <th>Last Activity</th>
                <th>Predicted Churn</th>
                <th>Risk Factors</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {analyticsData.churnRiskUsers.map(user => (
                <tr key={user.id}>
                  <td>
                    <div className="user-info">
                      <div className="user-name">{user.name}</div>
                      <div className="user-email">{user.email}</div>
                    </div>
                  </td>
                  <td>
                    <div className={`risk-score ${user.riskScore >= 80 ? 'high' : user.riskScore >= 60 ? 'medium' : 'low'}`}>
                      {user.riskScore}%
                    </div>
                  </td>
                  <td>{new Date(user.lastActivity).toLocaleDateString()}</td>
                  <td>{new Date(user.predictedChurnDate).toLocaleDateString()}</td>
                  <td>
                    <div className="risk-factors">
                      {user.factors.map((factor, idx) => (
                        <span key={idx} className="risk-factor">{factor}</span>
                      ))}
                    </div>
                  </td>
                  <td>
                    <button 
                      className="action-btn"
                      onClick={() => handleUserIntervention(user.id)}
                    >
                      Intervene
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

  const renderRealtime = () => {
    return (
      <div className="realtime-analytics">
        <div className="realtime-header">
          <h2>Real-time Analytics</h2>
          <div className="realtime-status">
            <span className="status-indicator active"></span>
            <span>Live</span>
          </div>
        </div>

        <div className="realtime-metrics">
          <div className="realtime-metric">
            <div className="metric-realtime-value">142</div>
            <div className="metric-label">Active Now</div>
          </div>
          <div className="realtime-metric">
            <div className="metric-realtime-value">23</div>
            <div className="metric-label">New Sessions</div>
          </div>
          <div className="realtime-metric">
            <div className="metric-realtime-value">567</div>
            <div className="metric-label">Events/Min</div>
          </div>
        </div>

        <div className="chart-container">
          <h3>Live Activity Stream</h3>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={realtimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="activeUsers" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="events" stroke="#10b981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="activity-feed">
          <h3>Recent Activity</h3>
          <div className="activity-list">
            {/* Activity feed items would be rendered here */}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="user-engagement-analytics">
      <div className="analytics-header">
        <h1>User Engagement Analytics</h1>
        <div className="header-controls">
          <select 
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="date-range-select"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="1y">Last Year</option>
          </select>
          <button className="refresh-btn" onClick={fetchAnalytics}>🔄 Refresh</button>
          <button className="export-btn" onClick={handleExport}>📥 Export</button>
        </div>
      </div>

      <div className="analytics-nav">
        <button 
          className={`nav-btn ${activeView === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveView('overview')}
        >
          Overview
        </button>
        <button 
          className={`nav-btn ${activeView === 'behavior' ? 'active' : ''}`}
          onClick={() => setActiveView('behavior')}
        >
          Behavior
        </button>
        <button 
          className={`nav-btn ${activeView === 'journey' ? 'active' : ''}`}
          onClick={() => setActiveView('journey')}
        >
          User Journey
        </button>
        <button 
          className={`nav-btn ${activeView === 'churn' ? 'active' : ''}`}
          onClick={() => setActiveView('churn')}
        >
          Churn Analysis
        </button>
        <button 
          className={`nav-btn ${activeView === 'realtime' ? 'active' : ''}`}
          onClick={() => setActiveView('realtime')}
        >
          Real-time
        </button>
      </div>

      <div className="analytics-content">
        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading analytics data...</p>
          </div>
        ) : (
          <>
            {activeView === 'overview' && renderOverview()}
            {activeView === 'journey' && renderUserJourney()}
            {activeView === 'churn' && renderChurnAnalysis()}
            {activeView === 'realtime' && renderRealtime()}
          </>
        )}
      </div>
    </div>
  );
};

export default UserEngagementAnalytics;