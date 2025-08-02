/**
 * Analytics API client for web/desktop platforms
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

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
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
   * Export analysis results
   */
  async exportResults(
    type: 'trends' | 'topics' | 'comparison',
    data: any,
    format: 'json' | 'csv' = 'json'
  ): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/analytics/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type,
        data,
        format,
      }),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
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
} = analyticsAPI;