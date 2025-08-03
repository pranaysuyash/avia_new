import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { DocumentTextIcon, ClockIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { apiService, TranscriptionItem } from '../../services/api';

const RecentTranscriptions: React.FC = () => {
  const [recentTranscriptions, setRecentTranscriptions] = useState<TranscriptionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecentTranscriptions();
  }, []);

  const loadRecentTranscriptions = async () => {
    try {
      setLoading(true);
      const transcriptions = await apiService.getRecentTranscriptions();
      setRecentTranscriptions(transcriptions);
    } catch (error) {
      console.error('Failed to load recent transcriptions:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatCreatedAt = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return `${Math.floor(diffInHours * 60)} minutes ago`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)} hours ago`;
    } else {
      return `${Math.floor(diffInHours / 24)} days ago`;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Recent Transcriptions
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Your latest processing activities
        </p>
      </div>
      
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {loading ? (
          /* Loading State */
          [1, 2, 3].map((i) => (
            <div key={i} className="p-6 animate-pulse">
              <div className="flex items-center space-x-4">
                <div className="h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-2"></div>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
                </div>
              </div>
            </div>
          ))
        ) : recentTranscriptions.length === 0 ? (
          /* Empty State */
          <div className="p-12 text-center">
            <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">No transcriptions yet</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Upload an audio file to get started
            </p>
          </div>
        ) : (
          /* Real Data */
          recentTranscriptions.map((transcription, index) => (
            <motion.div
              key={transcription.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-6 hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-indigo-100 dark:bg-indigo-900 rounded-lg">
                    <DocumentTextIcon className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                      {transcription.title}
                    </h4>
                    <div className="flex items-center space-x-4 mt-1">
                      <div className="flex items-center space-x-1">
                        <ClockIcon className="h-4 w-4 text-gray-400" />
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatDuration(transcription.duration)}
                        </span>
                      </div>
                      <span className="text-xs text-emerald-600 dark:text-emerald-400">
                        {(transcription.accuracy * 100).toFixed(1)}% accuracy
                      </span>
                      <span className="text-xs text-blue-600 dark:text-blue-400">
                        {transcription.language}
                      </span>
                    </div>
                    {transcription.entities.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {transcription.entities.slice(0, 3).map((entity, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded"
                          >
                            {entity}
                          </span>
                        ))}
                        {transcription.entities.length > 3 && (
                          <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded">
                            +{transcription.entities.length - 3} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-2">
                    {transcription.status === 'completed' ? (
                      <CheckCircleIcon className="h-5 w-5 text-emerald-500" />
                    ) : (
                      <div className="h-2 w-2 bg-amber-500 rounded-full animate-pulse"></div>
                    )}
                    <span className={`text-xs font-medium ${
                      transcription.status === 'completed' 
                        ? 'text-emerald-600 dark:text-emerald-400' 
                        : 'text-amber-600 dark:text-amber-400'
                    }`}>
                      {transcription.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {formatCreatedAt(transcription.createdAt)}
                  </p>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
};

export default RecentTranscriptions;