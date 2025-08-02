/**
 * Advanced Search API client for web/desktop platforms
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
   * Execute advanced search
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search/advanced', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get search suggestions for autocomplete
   */
  async getSuggestions(partialQuery: string): Promise<string[]> {
    return this.request<string[]>(`/search/suggestions?q=${encodeURIComponent(partialQuery)}`);
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
   * Export search results
   */
  async exportResults(
    results: SearchResponse,
    format: 'json' | 'csv' = 'json'
  ): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/search/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        results,
        format,
      }),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * Get search analytics
   */
  async getSearchAnalytics(timeRange: string = '30d'): Promise<{
    popularTerms: Array<{ term: string; frequency: number; successRate: number }>;
    searchVolume: Array<{ date: string; count: number }>;
    averageResponseTime: number;
    totalSearches: number;
  }> {
    return this.request(`/search/analytics?timeRange=${timeRange}`);
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
    return this.request(`/search/similar/${transcriptId}?limit=${limit}&minSimilarity=${minSimilarity}`);
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
      }),
    });
  }
}

// Create singleton instance
export const searchAPI = new SearchAPI();

// Export individual methods for convenience
export const {
  search,
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
} = searchAPI;