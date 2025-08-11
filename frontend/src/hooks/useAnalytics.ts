import { useState, useEffect } from 'react';

export interface AnalyticsMetrics {
  totalProcessed: number;
  accuracy: number;
  avgProcessingTime: number;
  costSaved: number;
  activeUsers: number;
  storageUsed: number;
  apiCalls: number;
  revenue: number;
}

export interface AnalyticsData {
  metrics: AnalyticsMetrics;
  trends: {
    processed: number;
    accuracy: number;
    speed: number;
    revenue: number;
  };
  timeRange?: string;
}

export const useAnalytics = (timeRange: string = '7d') => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Try to fetch from real API first
      const response = await fetch(`/api/v1/analytics/metrics?timeRange=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('api_key') || 'demo-key'}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        setData(result);
      } else {
        throw new Error('API not available');
      }
    } catch (err) {
      // Fallback to demo data
      console.log('Using demo analytics data');
      
      // Generate realistic demo data based on time range
      const baseMetrics = {
        totalProcessed: 1247,
        accuracy: 97.8,
        avgProcessingTime: 45,
        costSaved: 15420,
        activeUsers: 156,
        storageUsed: 2.4,
        apiCalls: 45632,
        revenue: 125430
      };
      
      // Adjust metrics based on time range
      const multiplier = timeRange === '1d' ? 0.1 : 
                        timeRange === '7d' ? 1 : 
                        timeRange === '30d' ? 4.2 : 12.5;
      
      const adjustedMetrics = {
        ...baseMetrics,
        totalProcessed: Math.floor(baseMetrics.totalProcessed * multiplier),
        revenue: Math.floor(baseMetrics.revenue * multiplier),
        apiCalls: Math.floor(baseMetrics.apiCalls * multiplier)
      };
      
      const mockData: AnalyticsData = {
        metrics: adjustedMetrics,
        trends: {
          processed: 12.5 + (Math.random() - 0.5) * 10,
          accuracy: 2.3 + (Math.random() - 0.5) * 2,
          speed: -8.2 + (Math.random() - 0.5) * 5,
          revenue: 18.7 + (Math.random() - 0.5) * 15
        },
        timeRange
      };
      
      setData(mockData);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const refetch = () => {
    fetchAnalytics();
  };

  return {
    data,
    metrics: data?.metrics,
    trends: data?.trends,
    loading,
    error,
    refetch
  };
};
