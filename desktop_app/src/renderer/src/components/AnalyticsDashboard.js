import React, { useState, useEffect } from 'react';
import analytics from '../utils/analytics';
import { rateLimiters } from '../utils/rateLimiter';

const AnalyticsDashboard = ({ onClose }) => {
  const [stats, setStats] = useState(null);
  const [rateLimits, setRateLimits] = useState({});
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadStats();
    loadRateLimits();
    
    // Refresh every 5 seconds
    const interval = setInterval(() => {
      loadStats();
      loadRateLimits();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const loadStats = () => {
    setStats(analytics.getUsageStats());
  };

  const loadRateLimits = () => {
    const limits = {};
    Object.entries(rateLimiters).forEach(([key, limiter]) => {
      limits[key] = {
        remaining: limiter.getRemainingRequests(),
        max: limiter.maxRequests,
        window: limiter.windowMs / 1000 // Convert to seconds
      };
    });
    setRateLimits(limits);
  };

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
  };

  if (!stats) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6">
          <div className="spinner w-8 h-8 mx-auto"></div>
          <p className="text-gray-600 dark:text-gray-400 mt-2">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Analytics & Usage</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Tabs */}
          <div className="flex space-x-6 mt-4">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'overview'
                  ? 'text-primary-600 border-primary-600'
                  : 'text-gray-600 dark:text-gray-400 border-transparent hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('api')}
              className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'api'
                  ? 'text-primary-600 border-primary-600'
                  : 'text-gray-600 dark:text-gray-400 border-transparent hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              API Usage
            </button>
            <button
              onClick={() => setActiveTab('limits')}
              className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'limits'
                  ? 'text-primary-600 border-primary-600'
                  : 'text-gray-600 dark:text-gray-400 border-transparent hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              Rate Limits
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-8rem)]">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Session Info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Session Duration</h4>
                  <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                    {formatDuration(stats.session.duration)}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Total API Calls</h4>
                  <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                    {stats.apiUsage.totalRequests}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Success Rate</h4>
                  <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                    {stats.apiUsage.successRate}%
                  </p>
                </div>
              </div>

              {/* Usage by Type */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Usage by Type</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Transcriptions</p>
                        <p className="text-xl font-semibold text-gray-900 dark:text-white mt-1">
                          {stats.apiUsage.transcriptions}
                        </p>
                      </div>
                      <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Searches</p>
                        <p className="text-xl font-semibold text-gray-900 dark:text-white mt-1">
                          {stats.apiUsage.searches}
                        </p>
                      </div>
                      <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                        <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Exports</p>
                        <p className="text-xl font-semibold text-gray-900 dark:text-white mt-1">
                          {stats.apiUsage.exports}
                        </p>
                      </div>
                      <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                        <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Errors</p>
                        <p className="text-xl font-semibold text-gray-900 dark:text-white mt-1">
                          {stats.apiUsage.errors}
                        </p>
                      </div>
                      <div className="p-3 bg-red-100 dark:bg-red-900 rounded-lg">
                        <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => analytics.exportAnalytics()}
                  className="px-4 py-2 bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 rounded-lg"
                >
                  Export Analytics
                </button>
                <button
                  onClick={() => {
                    if (window.confirm('Are you sure you want to clear all analytics data?')) {
                      analytics.clearAnalytics();
                      loadStats();
                    }
                  }}
                  className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg"
                >
                  Clear Data
                </button>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="space-y-6">
              {/* Hourly Distribution */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  API Calls - Last 24 Hours
                </h3>
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                  <div className="flex items-end space-x-1" style={{ height: '200px' }}>
                    {stats.hourlyDistribution.map((count, hour) => {
                      const maxCount = Math.max(...stats.hourlyDistribution, 1);
                      const height = (count / maxCount) * 100;
                      
                      return (
                        <div
                          key={hour}
                          className="flex-1 bg-primary-500 hover:bg-primary-600 rounded-t cursor-pointer relative group"
                          style={{ height: `${height}%` }}
                        >
                          <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                            {hour}:00 - {count} calls
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mt-2">
                    <span>00:00</span>
                    <span>06:00</span>
                    <span>12:00</span>
                    <span>18:00</span>
                    <span>23:00</span>
                  </div>
                </div>
              </div>

              {/* Top Endpoints */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Top Endpoints</h3>
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {stats.topEndpoints.length === 0 ? (
                      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                        No endpoint data available
                      </div>
                    ) : (
                      stats.topEndpoints.map((endpoint, index) => (
                        <div key={index} className="p-4 flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {endpoint.endpoint}
                            </p>
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            {endpoint.count} calls
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Error Rates */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Error Rates</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Last Hour</h4>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white mt-2">
                      {stats.errorRate.lastHour}%
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Total</h4>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white mt-2">
                      {stats.errorRate.total}%
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'limits' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Rate Limits</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(rateLimits).map(([key, limit]) => (
                  <div key={key} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900 dark:text-white capitalize">{key}</h4>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {limit.window}s window
                      </span>
                    </div>
                    
                    <div className="mb-2">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600 dark:text-gray-400">Remaining</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {limit.remaining} / {limit.max}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all ${
                            limit.remaining / limit.max > 0.5 
                              ? 'bg-green-500' 
                              : limit.remaining / limit.max > 0.2 
                              ? 'bg-yellow-500' 
                              : 'bg-red-500'
                          }`}
                          style={{ width: `${(limit.remaining / limit.max) * 100}%` }}
                        />
                      </div>
                    </div>
                    
                    {limit.remaining === 0 && (
                      <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                        Rate limit exceeded. Please wait before making more requests.
                      </p>
                    )}
                  </div>
                ))}
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="ml-3">
                    <h4 className="text-sm font-medium text-blue-900 dark:text-blue-200">Rate Limiting Info</h4>
                    <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                      Rate limits help ensure fair usage and prevent API abuse. Limits reset automatically after the specified time window.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;