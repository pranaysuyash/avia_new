/**
 * Advanced Search API client for React Native mobile platforms
 */

export interface SearchFilters {
  dateRange?: {
    start: Date | null;
    end: Date | null;
  };
  language?: string;
  speakers?: string[];
  tags?: string[];
  entityTypes?: string[];
  minConfidence?: number;
  hasEntities?: boolean;
  hasSpeakers?: boolean;
  hasTags?: boolean;
}

export interface SearchOptions {
  limit: number;
  offset: number;
  sortBy: 'relevance' | 'date_desc' | 'date_asc' | 'title';
  highlight: boolean;
  fuzzy: boolean;
  includeFacets: boolean;
}

export interface SearchRequest {
  query: string;
  filters: SearchFilters;
  options: SearchOptions;
}

export interface SearchResult {
  doc_id: string;
  title: string;
  content_snippet: string;
  title_snippet?: string;
  created_at: string;
  language?: string;
  confidence?: number;
  speakers?: string[];
  tags?: string[];
  entities?: Array<{
    text: string;
    label: string;
  }>;
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  results: SearchResult[];
  totalCount: number;
  searchTimeMs: number;
  facets: Record<string, Record<string, number>>;
  suggestions: string[];
  pageInfo: {
    currentPage: number;
    totalPages: number;
    perPage: number;
    totalResults: number;
    showingFrom: number;
    showingTo: number;
  };
}

export interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: SearchFilters;
  useCount: number;
  createdAt: string;
}

export interface SearchHistory {
  query: string;
  timestamp: string;
  resultCount: number;
  filters?: SearchFilters;
}

class SearchAPI {
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
   * Execute advanced search
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search/advanced', {
      method: 'POST',
      body: JSON.stringify({
        ...request,
        mobile: true, // Flag for mobile-optimized response
      }),
    });
  }

  /**
   * Execute quick search (mobile-optimized)
   */
  async quickSearch(
    query: string,
    limit: number = 10
  ): Promise<{
    results: SearchResult[];
    totalCount: number;
    searchTimeMs: number;
  }> {
    return this.request('/search/quick', {
      method: 'POST',
      body: JSON.stringify({
        query,
        limit,
        mobile: true,
      }),
    });
  }

  /**
   * Get search suggestions for autocomplete
   */
  async getSuggestions(partialQuery: string): Promise<string[]> {
    return this.request<string[]>(`/search/suggestions?q=${encodeURIComponent(partialQuery)}&mobile=true`);
  }

  /**
   * Save a search for later use
   */
  async saveSearch(name: string, query: string, filters: SearchFilters): Promise<SavedSearch> {
    return this.request<SavedSearch>('/search/save', {
      method: 'POST',
      body: JSON.stringify({ name, query, filters }),
    });
  }

  /**
   * Get saved searches
   */
  async getSavedSearches(): Promise<SavedSearch[]> {
    return this.request<SavedSearch[]>('/search/saved');
  }

  /**
   * Delete a saved search
   */
  async deleteSavedSearch(searchId: string): Promise<void> {
    return this.request(`/search/saved/${searchId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Get search history
   */
  async getSearchHistory(limit: number = 20): Promise<SearchHistory[]> {
    return this.request<SearchHistory[]>(`/search/history?limit=${limit}`);
  }

  /**
   * Clear search history
   */
  async clearSearchHistory(): Promise<void> {
    return this.request('/search/history', {
      method: 'DELETE',
    });
  }

  /**
   * Export search results (mobile-optimized)
   */
  async exportResults(
    results: SearchResponse,
    format: 'json' | 'csv' = 'json'
  ): Promise<string> {
    const response = await this.request<{ data: string }>('/search/export', {
      method: 'POST',
      body: JSON.stringify({
        results,
        format,
        mobile: true,
      }),
    });

    return response.data;
  }

  /**
   * Get search analytics (mobile summary)
   */
  async getSearchAnalytics(timeRange: string = '30d'): Promise<{
    popularTerms: Array<{ term: string; frequency: number; successRate: number }>;
    searchVolume: Array<{ date: string; count: number }>;
    averageResponseTime: number;
    totalSearches: number;
  }> {
    return this.request(`/search/analytics?timeRange=${timeRange}&mobile=true`);
  }

  /**
   * Perform semantic search
   */
  async semanticSearch(
    query: string,
    limit: number = 10,
    minSimilarity: number = 0.7
  ): Promise<Array<{
    transcript_id: string;
    title: string;
    content_snippet: string;
    similarity_score: number;
    matching_chunks: Array<{
      text: string;
      start_pos: number;
      end_pos: number;
      similarity: number;
    }>;
  }>> {
    return this.request('/search/semantic', {
      method: 'POST',
      body: JSON.stringify({
        query,
        limit,
        min_similarity: minSimilarity,
        mobile: true,
      }),
    });
  }

  /**
   * Find similar transcripts
   */
  async findSimilar(
    transcriptId: string,
    limit: number = 5,
    minSimilarity: number = 0.6
  ): Promise<Array<{
    transcript_id: string;
    title: string;
    similarity_score: number;
    common_themes: string[];
  }>> {
    return this.request(`/search/similar/${transcriptId}?limit=${limit}&minSimilarity=${minSimilarity}&mobile=true`);
  }

  /**
   * Get content recommendations
   */
  async getRecommendations(
    userHistory: string[],
    limit: number = 10
  ): Promise<Array<{
    transcript_id: string;
    title: string;
    recommendation_score: number;
    reason: string;
  }>> {
    return this.request('/search/recommendations', {
      method: 'POST',
      body: JSON.stringify({
        user_history: userHistory,
        limit,
        mobile: true,
      }),
    });
  }

  /**
   * Get recent searches for mobile quick access
   */
  async getRecentSearches(limit: number = 5): Promise<string[]> {
    const history = await this.getSearchHistory(limit);
    return history.map(h => h.query);
  }

  /**
   * Get popular searches for mobile discovery
   */
  async getPopularSearches(limit: number = 10): Promise<Array<{
    query: string;
    frequency: number;
    successRate: number;
  }>> {
    return this.request(`/search/popular?limit=${limit}&mobile=true`);
  }

  /**
   * Check search service health
   */
  async healthCheck(): Promise<{ status: 'healthy' | 'degraded' | 'down'; message?: string }> {
    try {
      return await this.request('/search/health');
    } catch (error) {
      return { status: 'down', message: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  /**
   * Get search filters suggestions based on current query
   */
  async getFilterSuggestions(query: string): Promise<{
    languages: string[];
    speakers: string[];
    tags: string[];
    entityTypes: string[];
    dateRanges: Array<{ label: string; start: string; end: string }>;
  }> {
    return this.request(`/search/filter-suggestions?q=${encodeURIComponent(query)}`);
  }
}

// Create singleton instance
export const searchAPI = new SearchAPI();

// Export individual methods for convenience
export const {
  search,
  quickSearch,
  getSuggestions,
  saveSearch,
  getSavedSearches,
  deleteSavedSearch,
  getSearchHistory,
  clearSearchHistory,
  exportResults,
  getSearchAnalytics,
  semanticSearch,
  findSimilar,
  getRecommendations,
  getRecentSearches,
  getPopularSearches,
  healthCheck,
  getFilterSuggestions,
} = searchAPI;

// Mobile-specific utilities
export const SearchUtils = {
  /**
   * Highlight search terms in text for mobile display
   */
  highlightText: (text: string, searchTerms: string[]): string => {
    let highlightedText = text;
    searchTerms.forEach(term => {
      const regex = new RegExp(`(${term})`, 'gi');
      highlightedText = highlightedText.replace(regex, '**$1**');
    });
    return highlightedText;
  },

  /**
   * Truncate search results for mobile display
   */
  truncateSnippet: (snippet: string, maxLength: number = 150): string => {
    if (snippet.length <= maxLength) {
      return snippet;
    }
    return `${snippet.substring(0, maxLength)}...`;
  },

  /**
   * Format search time for mobile display
   */
  formatSearchTime: (timeMs: number): string => {
    if (timeMs < 1000) {
      return `${timeMs}ms`;
    }
    return `${(timeMs / 1000).toFixed(1)}s`;
  },

  /**
   * Get icon for entity type
   */
  getEntityIcon: (entityType: string): string => {
    const iconMap: Record<string, string> = {
      'PERSON': 'person',
      'ORG': 'business',
      'LOC': 'place',
      'DATE': 'event',
      'TIME': 'schedule',
      'MONEY': 'attach-money',
      'PERCENT': 'percent',
      'PRODUCT': 'inventory',
    };
    return iconMap[entityType] || 'label';
  },

  /**
   * Get color for confidence level
   */
  getConfidenceColor: (confidence: number): string => {
    if (confidence >= 0.8) return '#4CAF50'; // Green
    if (confidence >= 0.6) return '#FF9800'; // Orange
    return '#F44336'; // Red
  },

  /**
   * Format result count for mobile display
   */
  formatResultCount: (count: number): string => {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`;
    }
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count.toString();
  },

  /**
   * Parse search query for mobile suggestions
   */
  parseSearchQuery: (query: string): {
    terms: string[];
    filters: string[];
    phrases: string[];
  } => {
    const terms: string[] = [];
    const filters: string[] = [];
    const phrases: string[] = [];

    // Extract quoted phrases
    const phraseMatches = query.match(/"([^"]+)"/g);
    if (phraseMatches) {
      phraseMatches.forEach(match => {
        phrases.push(match.replace(/"/g, ''));
        query = query.replace(match, '');
      });
    }

    // Extract filters (key:value)
    const filterMatches = query.match(/\w+:\w+/g);
    if (filterMatches) {
      filterMatches.forEach(match => {
        filters.push(match);
        query = query.replace(match, '');
      });
    }

    // Extract remaining terms
    const remainingTerms = query.trim().split(/\s+/).filter(term => term.length > 0);
    terms.push(...remainingTerms);

    return { terms, filters, phrases };
  },

  /**
   * Build search query from components
   */
  buildSearchQuery: (components: {
    terms?: string[];
    filters?: string[];
    phrases?: string[];
  }): string => {
    const parts: string[] = [];

    if (components.terms) {
      parts.push(...components.terms);
    }

    if (components.phrases) {
      parts.push(...components.phrases.map(phrase => `"${phrase}"`));
    }

    if (components.filters) {
      parts.push(...components.filters);
    }

    return parts.join(' ');
  },
};