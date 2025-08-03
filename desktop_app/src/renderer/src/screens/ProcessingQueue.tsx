import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ClockIcon, CheckCircleIcon, XCircleIcon, PlayIcon, PauseIcon, TrashIcon } from '@heroicons/react/24/outline';

interface QueueItem {
  id: string;
  filename: string;
  file_size: number;
  status: string;
  progress: number;
  estimated_time?: number;
  created_at: string;
  error_message?: string;
}

interface QueueStats {
  total_items: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  cancelled: number;
  estimated_queue_time: number;
}

const ProcessingQueue: React.FC = () => {
  const [queueItems, setQueueItems] = useState<QueueItem[]>([]);
  const [stats, setStats] = useState<QueueStats>({
    total_items: 0, pending: 0, processing: 0, completed: 0, failed: 0, cancelled: 0, estimated_queue_time: 0
  });
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    loadQueueStatus();
    // Disable WebSocket for now as the API doesn't support it
    // setupWebSocket();
    
    // Set up polling instead
    const interval = setInterval(() => {
      loadQueueStatus();
    }, 5000); // Poll every 5 seconds
    
    return () => clearInterval(interval);
  }, []);

  const loadQueueStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/queue/status');
      if (response.ok) {
        const result = await response.json();
        setQueueItems(result.items || []);
        setStats(result.stats || {});
      }
    } catch (error) {
      console.error('Failed to load queue status:', error);
    } finally {
      setLoading(false);
    }
  };

  const setupWebSocket = () => {
    try {
      const ws = new WebSocket('ws://localhost:8000/api/queue/ws');
      
      ws.onopen = () => {
        setWsConnected(true);
        console.log('Queue WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'progress_update') {
          setQueueItems(prev => prev.map(item => 
            item.id === message.data.id ? { ...item, ...message.data } : item
          ));
        } else if (message.type === 'item_added') {
          setQueueItems(prev => [...prev, message.data]);
        }
      };
      
      ws.onclose = () => {
        setWsConnected(false);
        console.log('Queue WebSocket disconnected');
      };
    } catch (error) {
      console.error('WebSocket setup failed:', error);
    }
  };

  const cancelItem = async (queueId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/queue/${queueId}/cancel`, {
        method: 'POST'
      });
      if (response.ok) {
        setQueueItems(prev => prev.map(item => 
          item.id === queueId ? { ...item, status: 'cancelled' } : item
        ));
      }
    } catch (error) {
      console.error('Failed to cancel item:', error);
    }
  };

  const retryItem = async (queueId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/queue/${queueId}/retry`, {
        method: 'POST'
      });
      if (response.ok) {
        setQueueItems(prev => prev.map(item => 
          item.id === queueId ? { ...item, status: 'pending', progress: 0 } : item
        ));
      }
    } catch (error) {
      console.error('Failed to retry item:', error);
    }
  };

  const clearCompleted = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/queue/clear', {
        method: 'DELETE'
      });
      if (response.ok) {
        setQueueItems(prev => prev.filter(item => 
          !['completed', 'failed', 'cancelled'].includes(item.status)
        ));
      }
    } catch (error) {
      console.error('Failed to clear completed items:', error);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon className="h-5 w-5 text-emerald-500" />;
      case 'failed': return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'processing': return <div className="h-2 w-2 bg-amber-500 rounded-full animate-pulse"></div>;
      case 'cancelled': return <XCircleIcon className="h-5 w-5 text-gray-500" />;
      default: return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
            Processing Queue
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Monitor your transcription processing status
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`h-3 w-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-500">
            {wsConnected ? 'Live Updates' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Queue Stats */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">Total</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.total_items}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">Pending</div>
          <div className="text-2xl font-semibold text-amber-600">{stats.pending}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">Processing</div>
          <div className="text-2xl font-semibold text-blue-600">{stats.processing}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">Completed</div>
          <div className="text-2xl font-semibold text-emerald-600">{stats.completed}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">Failed</div>
          <div className="text-2xl font-semibold text-red-600">{stats.failed}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">Est. Time</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {formatTime(stats.estimated_queue_time)}
          </div>
        </div>
      </div>
      
      {/* Queue Actions */}
      <div className="flex justify-end">
        <button 
          onClick={clearCompleted}
          className="btn-secondary text-sm"
          disabled={stats.completed + stats.failed + stats.cancelled === 0}
        >
          <TrashIcon className="h-4 w-4 mr-2" />
          Clear Completed
        </button>
      </div>

      {/* Queue Items */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-500 dark:text-gray-400">Loading queue...</p>
          </div>
        ) : queueItems.length === 0 ? (
          <div className="p-8 text-center">
            <ClockIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">No items in queue</h3>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              Your processing queue is empty. Upload files to get started.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {queueItems.map((item) => (
              <div key={item.id} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {getStatusIcon(item.status)}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        {item.filename}
                      </h4>
                      <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500 dark:text-gray-400">
                        <span>{formatFileSize(item.file_size)}</span>
                        <span className="capitalize">{item.status}</span>
                        {item.estimated_time && (
                          <span>~{formatTime(item.estimated_time)} remaining</span>
                        )}
                      </div>
                      {item.error_message && (
                        <div className="text-xs text-red-600 mt-1">{item.error_message}</div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    {/* Progress Bar */}
                    {item.status === 'processing' && (
                      <div className="w-32">
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>Progress</span>
                          <span>{item.progress.toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${item.progress}%` }}
                          ></div>
                        </div>
                      </div>
                    )}
                    
                    {/* Action Buttons */}
                    <div className="flex space-x-2">
                      {item.status === 'failed' && (
                        <button 
                          onClick={() => retryItem(item.id)}
                          className="p-2 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                          title="Retry"
                        >
                          <PlayIcon className="h-4 w-4" />
                        </button>
                      )}
                      {(item.status === 'pending' || item.status === 'processing') && (
                        <button 
                          onClick={() => cancelItem(item.id)}
                          className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                          title="Cancel"
                        >
                          <PauseIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default ProcessingQueue;