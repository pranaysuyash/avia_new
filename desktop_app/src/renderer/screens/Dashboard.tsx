import React from 'react';
import { motion } from 'framer-motion';
import {
  DocumentTextIcon,
  MicrophoneIcon,
  ClockIcon,
  ChartBarIcon,
  ArrowUpIcon,
  FolderOpenIcon,
  CloudArrowUpIcon,
  VideoCameraIcon
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import StatsCard from '../components/dashboard/StatsCard';
import RecentTranscriptions from '../components/dashboard/RecentTranscriptions';
import QuickActions from '../components/dashboard/QuickActions';
import UsageChart from '../components/dashboard/UsageChart';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const stats = [
    {
      title: 'Total Transcriptions',
      value: '1,234',
      change: '+12%',
      icon: DocumentTextIcon,
      color: 'indigo'
    },
    {
      title: 'Hours Processed',
      value: '456.7',
      change: '+8%',
      icon: ClockIcon,
      color: 'purple'
    },
    {
      title: 'Active Projects',
      value: '23',
      change: '+3',
      icon: FolderOpenIcon,
      color: 'emerald'
    },
    {
      title: 'Accuracy Rate',
      value: '98.5%',
      change: '+0.5%',
      icon: ChartBarIcon,
      color: 'amber'
    }
  ];

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
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Welcome back! Here's what's happening with your transcriptions.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
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