/**
 * Mobile API client for Hybrid Summarization endpoints
 */

export interface SummarizationRequest {
  text: string;
  summary_type?: string;
  length?: string;
  style?: string;
  query?: string;
  max_sentences?: number;
  max_words?: number;
  focus_keywords?: string[];
  exclude_keywords?: string[];
  preserve_structure?: boolean;
  include_quotes?: boolean;
  language?: string;
  user_preferences?: Record<string, any>;
}

export interface SummaryResult {
  summary: string;
  summary_type: string;
  length: string;
  style: string;
  word_count: number;
  sentence_count: number;
  compression_ratio: number;
  quality_score: number;
  key_points: string[];
  extracted_sentences: string[];
  confidence_score: number;
  processing_time: number;
  metadata: Record<string, any>;
  created_at: string;
}

export interface SummaryOptions {
  summary_types: Array<{value: string, label: string, description: string}>;
  lengths: Array<{value: string, label: string, description: string}>;
  styles: Array<{value: string, label: string, description: string}>;
}

export interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}

class HybridSummarizationAPI {
  private baseUrl = '/api/v1/hybrid-summarization';

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${url}`, error);
      throw error;
    }
  }

  /**
   * Create a single document summary
   */
  async createSummary(request: SummarizationRequest): Promise<SummaryResult> {
    const response = await this.request<SummaryResult>('/summarize', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    return response.data;
  }

  /**
   * Get available summary types, lengths, and styles
   */
  async getSummaryOptions(): Promise<SummaryOptions> {
    const response = await this.request<SummaryOptions>('/types');
    return response.data;
  }

  /**
   * Health check for the summarization service
   */
  async healthCheck(): Promise<{
    status: string;
    components: Record<string, string>;
    test_result: {
      processing_time: number;
      quality_score: number;
    };
  }> {
    const response = await this.request<{
      status: string;
      components: Record<string, string>;
      test_result: {
        processing_time: number;
        quality_score: number;
      };
    }>('/health');
    return response.data;
  }
}

// Export singleton instance
export const hybridSummarizationAPI = new HybridSummarizationAPI();

// Export utility functions
export const summarizationUtils = {
  /**
   * Calculate estimated reading time for text
   */
  calculateReadingTime(text: string, wordsPerMinute: number = 200): number {
    const wordCount = text.split(/\s+/).filter(w => w.length > 0).length;
    return Math.ceil(wordCount / wordsPerMinute);
  },

  /**
   * Get compression ratio description
   */
  getCompressionDescription(ratio: number): string {
    if (ratio < 2) return 'Minimal compression';
    if (ratio < 5) return 'Light compression';
    if (ratio < 10) return 'Moderate compression';
    if (ratio < 20) return 'High compression';
    return 'Very high compression';
  },

  /**
   * Get quality score description
   */
  getQualityDescription(score: number): string {
    if (score >= 0.9) return 'Excellent';
    if (score >= 0.8) return 'Very Good';
    if (score >= 0.7) return 'Good';
    if (score >= 0.6) return 'Fair';
    return 'Needs Improvement';
  },

  /**
   * Format processing time
   */
  formatProcessingTime(seconds: number): string {
    if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  },

  /**
   * Validate summarization request
   */
  validateRequest(request: SummarizationRequest): string[] {
    const errors: string[] = [];

    if (!request.text || request.text.trim().length < 10) {
      errors.push('Text must be at least 10 characters long');
    }

    if (request.max_sentences && (request.max_sentences < 1 || request.max_sentences > 50)) {
      errors.push('Max sentences must be between 1 and 50');
    }

    if (request.max_words && (request.max_words < 10 || request.max_words > 1000)) {
      errors.push('Max words must be between 10 and 1000');
    }

    if (request.summary_type === 'query_focused' && !request.query?.trim()) {
      errors.push('Query is required for query-focused summarization');
    }

    return errors;
  }
};

export default hybridSummarizationAPI;