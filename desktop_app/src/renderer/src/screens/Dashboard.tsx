import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  DocumentTextIcon,
  MicrophoneIcon,
  ClockIcon,
  ChartBarIcon,
  FolderOpenIcon,
  CloudArrowUpIcon,
  VideoCameraIcon
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import StatsCard from '../components/dashboard/StatsCard';
import RecentTranscriptions from '../components/dashboard/RecentTranscriptions';
import QuickActions from '../components/dashboard/QuickActions';
import UsageChart from '../components/dashboard/UsageChart';
import { apiService, DashboardStats } from '../services/api';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    totalTranscriptions: 0,
    hoursProcessed: 0,
    entitiesFound: 0,
    accuracyRate: 0
  });
  const [loading, setLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Check backend health
      const health = await apiService.checkHealth();
      setApiConnected(health.status === 'healthy');
      
      // Load real stats
      const dashboardStats = await apiService.getDashboardStats();
      setStats(dashboardStats);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setApiConnected(false);
    } finally {
      setLoading(false);
    }
  };

  const formatStatsForDisplay = (stats: DashboardStats) => [
    {
      title: 'Total Transcriptions',
      value: stats.totalTranscriptions.toString(),
      change: stats.totalTranscriptions > 0 ? '+' + stats.totalTranscriptions : '0',
      icon: DocumentTextIcon,
      color: 'indigo'
    },
    {
      title: 'Hours Processed',
      value: stats.hoursProcessed.toFixed(1),
      change: stats.hoursProcessed > 0 ? '+' + stats.hoursProcessed.toFixed(1) : '0',
      icon: ClockIcon,
      color: 'purple'
    },
    {
      title: 'Entities Found',
      value: stats.entitiesFound.toString(),
      change: stats.entitiesFound > 0 ? '+' + stats.entitiesFound : '0',
      icon: FolderOpenIcon,
      color: 'emerald'
    },
    {
      title: 'Accuracy Rate',
      value: stats.accuracyRate > 0 ? (stats.accuracyRate * 100).toFixed(1) + '%' : '0%',
      change: stats.accuracyRate > 0 ? '+' + (stats.accuracyRate * 100).toFixed(1) + '%' : '0%',
      icon: ChartBarIcon,
      color: 'amber'
    }
  ];

  const displayStats = formatStatsForDisplay(stats);

  const quickActions = [
    {
      title: 'Upload File',
      description: 'Process audio or video files',
      icon: CloudArrowUpIcon,
      action: () => navigate('/workspace'),
      color: 'bg-indigo-500'
    },
    {
      title: 'Record Audio',
      description: 'Start a new recording',
      icon: MicrophoneIcon,
      action: () => navigate('/workspace?mode=record'),
      color: 'bg-purple-500'
    },
    {
      title: 'Import Video',
      description: 'Extract audio from video',
      icon: VideoCameraIcon,
      action: () => navigate('/workspace?mode=video'),
      color: 'bg-emerald-500'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Welcome back! Here's what's happening with your transcriptions.
          </p>
        </div>
        
        {/* API Status Indicator */}
        <div className="flex items-center space-x-2">
          <div className={`h-3 w-3 rounded-full ${apiConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {apiConnected ? 'API Connected' : 'API Disconnected'}
          </span>
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-6 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ) : (
        /* Stats Grid - Real Data */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {displayStats.map((stat, index) => (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <StatsCard {...stat} />
            </motion.div>
          ))}
        </div>
      )}

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h2>
        <QuickActions actions={quickActions} />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Transcriptions */}
        <motion.div
          className="lg:col-span-2"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <RecentTranscriptions />
        </motion.div>

        {/* Usage Chart */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          <UsageChart />
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;