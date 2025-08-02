/**
 * Analytics API client for React Native mobile platforms
 */

export interface TrendAnalysisRequest {
  time_period: '7d' | '30d' | '90d' | '1y';
  analysis_type: 'keywords' | 'topics' | 'entities' | 'sentiment';
  filters?: {
    language?: string;
    speakers?: string[];
    tags?: string[];
    min_confidence?: number;
  };
}

export interface TrendAnalysisResponse {
  time_period: string;
  analysis_type: string;
  total_transcripts: number;
  trends: Array<{
    time_bucket: string;
    transcript_count: number;
    keywords?: Array<{
      keyword: string;
      score: number;
      frequency: number;
      growth_rate?: number;
    }>;
    topics?: Array<{
      topic_id: string;
      weight: number;
      keywords: string[];
    }>;
    entities?: Array<{
      entity: string;
      count: number;
    }>;
    sentiment?: {
      average_sentiment: number;
      sentiment_distribution: {
        positive: number;
        neutral: number;
        negative: number;
      };
    };
  }>;
  metadata: {
    analyzed_at: string;
    transcript_count: number;
  };
}

export interface TopicExtractionRequest {
  transcript_ids?: string[];
  num_topics: number;
  method: 'keyword_clustering' | 'semantic_clustering';
}

export interface TopicExtractionResponse {
  topics: Array<{
    topic_id: string;
    keywords: string[];
    weight: number;
    description: string;
  }>;
  topic_distribution: Record<string, number>;
  coherence_score: number;
  num_topics: number;
  metadata: {
    method: string;
    transcript_count: number;
    analyzed_at: string;
  };
}

export interface ComparisonRequest {
  source_a: string;
  source_b: string;
  comparison_type: 'comprehensive' | 'keywords' | 'topics' | 'sentiment';
}

export interface ComparisonResponse {
  source_a: string;
  source_b: string;
  similarities: {
    keyword_similarity: number;
    length_similarity: number;
    entity_similarity: number;
    overall_similarity: number;
  };
  differences: {
    length_difference: number;
    length_ratio: number;
    unique_keywords_a: string[];
    unique_keywords_b: string[];
    metadata_differences: Record<string, any>;
  };
  common_themes: string[];
  unique_themes: {
    source_a_unique: string[];
    source_b_unique: string[];
  };
  metadata: {
    comparison_type: string;
    analyzed_at: string;
  };
}

class AnalyticsAPI {
  private baseURL: string;

  constructor(baseURL: string = 'https://your-api-domain.com/api') {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network request failed');
    }
  }

  /**
   * Analyze trends across transcripts
   */
  async analyzeTrends(request: TrendAnalysisRequest): Promise<TrendAnalysisResponse> {
    return this.request<TrendAnalysisResponse>('/analytics/trends', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Extract topics from transcripts
   */
  async extractTopics(request: TopicExtractionRequest): Promise<TopicExtractionResponse> {
    return this.request<TopicExtractionResponse>('/analytics/topics', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Compare two sources
   */
  async compareSources(request: ComparisonRequest): Promise<ComparisonResponse> {
    return this.request<ComparisonResponse>('/analytics/compare', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get analytics statistics
   */
  async getStats(): Promise<{
    analytics_enabled: boolean;
    supported_analyses: string[];
    trend_periods: string[];
    analysis_types: string[];
  }> {
    return this.request('/analytics/stats');
  }

  /**
   * Export analysis results (mobile-optimized)
   */
  async exportResults(
    type: 'trends' | 'topics' | 'comparison',
    data: any,
    format: 'json' | 'csv' = 'json'
  ): Promise<string> {
    const response = await this.request<{ data: string }>('/analytics/export', {
      method: 'POST',
      body: JSON.stringify({
        type,
        data,
        format,
        mobile: true, // Flag for mobile-optimized response
      }),
    });

    return response.data;
  }

  /**
   * Get trending keywords for mobile dashboard
   */
  async getTrendingKeywords(timeRange: string = '7d'): Promise<Array<{
    keyword: string;
    score: number;
    growth_rate: number;
    frequency: number;
  }>> {
    return this.request(`/analytics/trending-keywords?timeRange=${timeRange}`);
  }

  /**
   * Get quick analytics summary for mobile
   */
  async getQuickSummary(): Promise<{
    total_transcripts: number;
    recent_activity: number;
    top_keywords: string[];
    sentiment_trend: 'positive' | 'neutral' | 'negative';
    processing_time_avg: number;
  }> {
    return this.request('/analytics/quick-summary');
  }

  /**
   * Check analytics service health
   */
  async healthCheck(): Promise<{ status: 'healthy' | 'degraded' | 'down'; message?: string }> {
    try {
      return await this.request('/analytics/health');
    } catch (error) {
      return { status: 'down', message: error instanceof Error ? error.message : 'Unknown error' };
    }
  }
}

// Create singleton instance
export const analyticsAPI = new AnalyticsAPI();

// Export individual methods for convenience
export const {
  analyzeTrends,
  extractTopics,
  compareSources,
  getStats,
  exportResults,
  getTrendingKeywords,
  getQuickSummary,
  healthCheck,
} = analyticsAPI;

// Mobile-specific utilities
export const AnalyticsUtils = {
  /**
   * Format large numbers for mobile display
   */
  formatNumber: (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  },

  /**
   * Format time duration for mobile display
   */
  formatDuration: (ms: number): string => {
    if (ms < 1000) {
      return `${ms}ms`;
    }
    if (ms < 60000) {
      return `${(ms / 1000).toFixed(1)}s`;
    }
    return `${(ms / 60000).toFixed(1)}m`;
  },

  /**
   * Truncate text for mobile display
   */
  truncateText: (text: string, maxLength: number = 50): string => {
    if (text.length <= maxLength) {
      return text;
    }
    return `${text.substring(0, maxLength)}...`;
  },

  /**
   * Get color for sentiment score
   */
  getSentimentColor: (score: number): string => {
    if (score > 0.1) return '#4CAF50'; // Green for positive
    if (score < -0.1) return '#F44336'; // Red for negative
    return '#FF9800'; // Orange for neutral
  },

  /**
   * Get color for confidence score
   */
  getConfidenceColor: (confidence: number): string => {
    if (confidence >= 0.8) return '#4CAF50'; // Green for high confidence
    if (confidence >= 0.6) return '#FF9800'; // Orange for medium confidence
    return '#F44336'; // Red for low confidence
  },

  /**
   * Format percentage for display
   */
  formatPercentage: (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  },

  /**
   * Get relative time string
   */
  getRelativeTime: (timestamp: string): string => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  },
};