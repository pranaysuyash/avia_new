import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { DocumentTextIcon, TrashIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';

interface HistoryItem {
  id: string;
  title: string;
  filename: string;
  duration: number;
  status: string;
  accuracy: number;
  created_at: string;
  language: string;
  entities_count: number;
}

const History: React.FC = () => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total_items: 0, completed: 0, processing: 0, failed: 0 });
  const navigate = useNavigate();

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8001/api/transcriptions?limit=50', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const result = await response.json();
        // Transform the data to match the expected format
        const transcriptions = result.data || [];
        setHistory(transcriptions.map((item: any) => ({
          id: item.id,
          title: item.title || 'Untitled',
          filename: item.filename || 'unknown.mp3',
          duration: item.duration || 0,
          status: item.status || 'completed',
          accuracy: item.accuracy || 0.95,
          created_at: item.created_at || new Date().toISOString(),
          language: item.language || 'en',
          entities_count: item.entities_count || 0
        })));
        
        // Calculate stats from the data
        const completed = transcriptions.filter((t: any) => t.status === 'completed').length;
        const processing = transcriptions.filter((t: any) => t.status === 'processing').length;
        const failed = transcriptions.filter((t: any) => t.status === 'failed').length;
        
        setStats({
          total_items: transcriptions.length,
          completed,
          processing,
          failed
        });
      }
    } catch (error) {
      console.error('Failed to load history:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteItem = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8001/api/transcriptions/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        setHistory(prev => prev.filter(item => item.id !== id));
      }
    } catch (error) {
      console.error('Failed to delete item:', error);
    }
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toFixed(0).padStart(2, '0')}`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Transcription History
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          View and manage your past transcriptions
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">Total</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.total_items}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">Completed</div>
          <div className="text-2xl font-semibold text-emerald-600">{stats.completed}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">Processing</div>
          <div className="text-2xl font-semibold text-amber-600">{stats.processing}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">Failed</div>
          <div className="text-2xl font-semibold text-red-600">{stats.failed}</div>
        </div>
      </div>
      
      {/* History List */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-500 dark:text-gray-400">Loading history...</p>
          </div>
        ) : history.length === 0 ? (
          <div className="p-8 text-center">
            <DocumentTextIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">No transcriptions yet</h3>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              Your transcription history will appear here once you start processing files.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {history.map((item) => (
              <div key={item.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer transition-colors">
                <div className="flex items-center justify-between">
                  <div 
                    className="flex items-center space-x-4 flex-1"
                    onClick={() => navigate(`/workspace?id=${item.id}`)}
                  >
                    <div className="p-2 bg-indigo-100 dark:bg-indigo-900 rounded-lg">
                      <DocumentTextIcon className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                        {item.title}
                      </h4>
                      <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500 dark:text-gray-400">
                        <span>{item.filename}</span>
                        <span>{formatDuration(item.duration)}</span>
                        <span>{item.language}</span>
                        <span>{item.entities_count} entities</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className={`text-xs font-medium ${
                        item.status === 'completed' ? 'text-emerald-600' :
                        item.status === 'processing' ? 'text-amber-600' : 'text-red-600'
                      }`}>
                        {item.status}
                      </div>
                      {item.status === 'completed' && (
                        <div className="text-xs text-gray-500">
                          {(item.accuracy * 100).toFixed(1)}% accuracy
                        </div>
                      )}
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(item.created_at)}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <button className="p-2 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
                        <ArrowDownTrayIcon className="h-4 w-4" />
                      </button>
                      <button 
                        onClick={() => deleteItem(item.id)}
                        className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
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

export default History;