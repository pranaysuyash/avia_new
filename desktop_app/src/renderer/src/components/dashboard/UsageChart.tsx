import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService } from '../../services/api';

const UsageChart: React.FC = () => {
  const [data, setData] = useState([
    { day: 'Mon', hours: 0 },
    { day: 'Tue', hours: 0 },
    { day: 'Wed', hours: 0 },
    { day: 'Thu', hours: 0 },
    { day: 'Fri', hours: 0 },
    { day: 'Sat', hours: 0 },
    { day: 'Sun', hours: 0 },
  ]);
  const [loading, setLoading] = useState(true);
  const [totalHours, setTotalHours] = useState(0);

  useEffect(() => {
    loadUsageData();
  }, []);

  const loadUsageData = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/analytics/usage/weekly');
      if (response.ok) {
        const result = await response.json();
        if (result.data) {
          setData(result.data);
          setTotalHours(result.stats.total_hours);
        }
      }
    } catch (error) {
      console.error('Failed to load usage data:', error);
      // Keep default mock data if API fails
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700"
    >
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Weekly Usage
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Hours of audio processed this week
        </p>
      </div>
      
      <div className="p-6">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="day" 
                axisLine={false}
                tickLine={false}
                className="text-xs fill-gray-500"
              />
              <YAxis 
                axisLine={false}
                tickLine={false}
                className="text-xs fill-gray-500"
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                labelStyle={{ color: '#374151' }}
              />
              <Bar 
                dataKey="hours" 
                fill="#6366f1"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        <div className="mt-4 flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2">
            <div className="h-3 w-3 bg-indigo-500 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">Processing Hours</span>
          </div>
          <span className="font-medium text-gray-900 dark:text-white">
            {loading ? 'Loading...' : `${totalHours.toFixed(1)}h total`}
          </span>
        </div>
      </div>
    </motion.div>
  );
};

export default UsageChart;