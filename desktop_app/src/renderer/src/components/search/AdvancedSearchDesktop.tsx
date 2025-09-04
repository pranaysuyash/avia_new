/**
 * Advanced Search Interface - Task 133 Electron Desktop Implementation
 * Comprehensive search interface with semantic search, faceted search, and advanced analytics
 */

import React, { useState, useEffect, useCallback } from 'react';
import { logUxEvent } from '../../services/uxTelemetry';
import {
  Search,
  Filter,
  Settings,
  BarChart3,
  Brain,
  Zap,
  Clock,
  Star,
  TrendingUp,
  BookOpen,
  Sliders,
  ChevronDown,
  ChevronRight,
  X,
  RefreshCw,
  Download,
  Share2,
  Bookmark,
  Eye,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  History,
  Layers,
  Cpu,
  Database
} from 'lucide-react';

// Types (same as React implementation but adapted for Electron)
interface SearchQuery {
  query: string;
  strategy: 'hybrid' | 'semantic_only' | 'traditional_only' | 'fuzzy_enhanced' | 'neural_ranking';
  relevanceModel: 'bm25' | 'tfidf' | 'neural' | 'hybrid_ensemble';
  searchType: 'full_text' | 'semantic' | 'fuzzy' | 'regex' | 'exact';
  scope: 'all' | 'transcripts' | 'users' | 'content' | 'metadata';
  filters: SearchFilter[];
  facets: string[];
  sortOrder: 'relevance' | 'date_desc' | 'date_asc' | 'title_asc' | 'title_desc';
  limit: number;
  offset: number;
  boostFactors: Record<string, number>;
  diversifyResults: boolean;
  explainRanking: boolean;
  semanticThreshold: number;
}

interface SearchFilter {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'contains' | 'in' | 'not_in';
  value: any;
  caseSensitive?: boolean;
}

interface SearchResult {
  id: string;
  type: string;
  title: string;
  content: string;
  highlightedContent: string;
  score: number;
  semanticScore?: number;
  traditionalScore?: number;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  explanation?: SearchExplanation;
  similarResults: string[];
  contentCategories: string[];
  extractedEntities: Entity[];
  filePath?: string; // Desktop-specific: local file path
  thumbnailPath?: string; // Desktop-specific: thumbnail for videos
}

interface SearchExplanation {
  totalScore: number;
  scoreComponents: Record<string, number>;
  matchingTerms: string[];
  boostApplied: Record<string, number>;
  penaltiesApplied: Record<string, number>;
  rankingModel: string;
}

interface Entity {
  type: string;
  value: string;
  confidence: number;
}

interface FacetValue {
  value: string;
  count: number;
  selected: boolean;
}

interface Facet {
  type: 'categorical' | 'range' | 'date_hierarchy';
  displayName: string;
  values?: FacetValue[];
  ranges?: RangeValue[];
  hierarchy?: Record<string, Record<string, number>>;
  totalItems: number;
}

interface RangeValue {
  label: string;
  min?: number;
  max?: number;
  count: number;
  selected: boolean;
}

interface SearchResponse {
  results: SearchResult[];
  totalCount: number;
  query: string;
  searchTimeMs: number;
  facets: Record<string, Facet>;
  facetRanges: Record<string, any>;
  querySuggestions: string[];
  relatedQueries: string[];
  searchTips: string[];
  queryInterpretation: string;
  searchAnalytics: Record<string, any>;
  performanceMetrics: Record<string, any>;
  filtersApplied: SearchFilter[];
  page: number;
  perPage: number;
  hasMore: boolean;
  resultClusters: Record<string, string[]>;
  indexStats?: {
    totalDocuments: number;
    lastUpdated: string;
    indexSize: string;
  };
}

function getQP(key: string): string | null {
  try { const url = new URL(window.location.href); return url.searchParams.get(key); } catch { return null; }
}
function setQP(key: string, val: string | null) {
  try { const url = new URL(window.location.href); if (!val) url.searchParams.delete(key); else url.searchParams.set(key, val); window.history.replaceState({}, '', url.toString()); } catch {}
}

const AdvancedSearchDesktop: React.FC = () => {
  // State management
  const [searchQuery, setSearchQuery] = useState<SearchQuery>({
    query: '',
    strategy: 'hybrid',
    relevanceModel: 'hybrid_ensemble',
    searchType: 'full_text',
    scope: 'all',
    filters: [],
    facets: ['content_type', 'duration', 'file_format'],
    sortOrder: 'relevance',
    limit: 20,
    offset: 0,
    boostFactors: { title: 2.0, content: 1.0, metadata: 0.5 },
    diversifyResults: true,
    explainRanking: false,
    semanticThreshold: 0.7
  });

  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'search' | 'analytics' | 'settings' | 'help' | 'index'>('search');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [searchHistory, setSearchHistory] = useState<Array<{ 
    query: string; 
    timestamp: Date; 
    resultsCount: number;
    strategy: string;
  }>>([]);

  // Desktop-specific state
  const [indexingStatus, setIndexingStatus] = useState<'idle' | 'indexing' | 'complete' | 'error'>('idle');
  const [indexStats, setIndexStats] = useState<{
    totalFiles: number;
    indexedFiles: number;
    lastIndexed: Date | null;
  }>({ totalFiles: 0, indexedFiles: 0, lastIndexed: null });

  // Search suggestions state
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Desktop-specific: Communication with main process
  useEffect(() => {
    // Listen for search results from main process
    window.electronAPI?.onSearchResults?.((results: SearchResponse) => {
      setSearchResults(results);
      setLoading(false);
    });

    // Listen for indexing updates
    window.electronAPI?.onIndexingUpdate?.((update: { status: string; progress?: number }) => {
      setIndexingStatus(update.status as any);
    });

    return () => {
      window.electronAPI?.removeAllListeners?.('search-results');
      window.electronAPI?.removeAllListeners?.('indexing-update');
    };
  }, []);

  // Initialize state from deep-link
  useEffect(() => {
    const q = getQP('q');
    const strat = getQP('strategy');
    const scope = getQP('scope');
    const sort = getQP('sort');
    const tab = getQP('tab') as any;
    const adv = getQP('adv') === '1';
    setSearchQuery(prev => ({
      ...prev,
      query: q ?? prev.query,
      strategy: (strat as any) || prev.strategy,
      scope: (scope as any) || prev.scope,
      sortOrder: (sort as any) || prev.sortOrder,
    }));
    if (tab && ['search','analytics','settings','help','index'].includes(tab)) setActiveTab(tab);
    setShowAdvanced(adv);
  }, []);

  // Sync state to URL on changes
  useEffect(() => { setQP('q', searchQuery.query || null); }, [searchQuery.query]);
  useEffect(() => { setQP('strategy', searchQuery.strategy); }, [searchQuery.strategy]);
  useEffect(() => { setQP('scope', searchQuery.scope); }, [searchQuery.scope]);
  useEffect(() => { setQP('sort', searchQuery.sortOrder); }, [searchQuery.sortOrder]);
  useEffect(() => { setQP('tab', activeTab); }, [activeTab]);
  useEffect(() => { setQP('adv', showAdvanced ? '1' : null); }, [showAdvanced]);

  // Perform search using Electron's main process
  const performSearch = useCallback(async () => {
    if (!searchQuery.query.trim()) return;

    setLoading(true);
    try { logUxEvent('search_executed', { q: searchQuery.query, strategy: searchQuery.strategy, scope: searchQuery.scope, sort: searchQuery.sortOrder }); } catch {}
    try {
      // Send search request to main process
      await window.electronAPI?.performAdvancedSearch?.(searchQuery);

      // Add to search history
      setSearchHistory(prev => [
        {
          query: searchQuery.query,
          timestamp: new Date(),
          resultsCount: 0, // Will be updated when results arrive
          strategy: searchQuery.strategy
        },
        ...prev.slice(0, 9) // Keep last 10
      ]);
    } catch (error) {
      console.error('Search error:', error);
      setLoading(false);
    }
  }, [searchQuery]);

  // Get search suggestions
  const getSearchSuggestions = useCallback(async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const suggestions = await window.electronAPI?.getSearchSuggestions?.(query);
      setSuggestions(suggestions || []);
    } catch (error) {
      console.error('Error getting suggestions:', error);
    }
  }, []);

  // Handle search input change
  const handleSearchInputChange = (value: string) => {
    setSearchQuery(prev => ({ ...prev, query: value }));
    getSearchSuggestions(value);
    setShowSuggestions(true);
  };

  // Desktop-specific: Start indexing
  const startIndexing = async () => {
    try {
      await window.electronAPI?.startIndexing?.();
      setIndexingStatus('indexing');
    } catch (error) {
      console.error('Error starting indexing:', error);
      setIndexingStatus('error');
    }
  };

  // Desktop-specific: Open file location
  const openFileLocation = async (filePath: string) => {
    try {
      await window.electronAPI?.showInFolder?.(filePath);
    } catch (error) {
      console.error('Error opening file location:', error);
    }
  };

  // Desktop-specific: Export search results
  const exportResults = async () => {
    if (!searchResults) return;

    try {
      await window.electronAPI?.exportSearchResults?.(searchResults, searchQuery);
    } catch (error) {
      console.error('Error exporting results:', error);
    }
  };

  // Filter management
  const addFilter = (field: string, operator: string, value: any) => {
    const newFilter: SearchFilter = { field, operator, value };
    setSearchQuery(prev => ({
      ...prev,
      filters: [...prev.filters, newFilter]
    }));
  };

  const removeFilter = (index: number) => {
    setSearchQuery(prev => ({
      ...prev,
      filters: prev.filters.filter((_, i) => i !== index)
    }));
  };

  // Render search interface
  const renderSearchInterface = () => (
    <div className="flex-1 p-6 space-y-6 overflow-auto">
      {/* Search Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center space-x-4 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={searchQuery.query}
              onChange={(e) => handleSearchInputChange(e.target.value)}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              placeholder="Search transcripts, videos, audio files..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && performSearch()}
            />
            
            {/* Search suggestions */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-50 mt-1">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setSearchQuery(prev => ({ ...prev, query: suggestion }));
                      setShowSuggestions(false);
                    }}
                    className="w-full text-left px-4 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                  >
                    <Search className="inline w-4 h-4 mr-2 text-gray-400" />
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <button
            onClick={performSearch}
            disabled={loading || !searchQuery.query.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {loading ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Search className="w-5 h-5" />
            )}
            <span>Search</span>
          </button>

          {/* Desktop-specific: Export button */}
          {searchResults && (
            <button
              onClick={exportResults}
              className="px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center space-x-2"
            >
              <Download className="w-5 h-5" />
              <span>Export</span>
            </button>
          )}
          <button
            onClick={async () => { try { const href = window.location.href; await navigator.clipboard.writeText(href); logUxEvent('share_view_copied', { href }); } catch {} }}
            className="px-4 py-3 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 flex items-center space-x-2"
            title="Copy shareable link"
          >
            <Share2 className="w-5 h-5" />
            <span>Share</span>
          </button>
        </div>

        {/* Advanced options toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center space-x-2 text-blue-600 hover:text-blue-700"
        >
          {showAdvanced ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          <span>Advanced Options</span>
        </button>

        {/* Advanced search options */}
        {showAdvanced && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Search Strategy */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Brain className="inline w-4 h-4 mr-1" />
                  Search Strategy
                </label>
                <select
                  value={searchQuery.strategy}
                  onChange={(e) => setSearchQuery(prev => ({ 
                    ...prev, 
                    strategy: e.target.value as any 
                  }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="hybrid">🔄 Hybrid</option>
                  <option value="semantic_only">🧠 Semantic Only</option>
                  <option value="traditional_only">📝 Traditional Only</option>
                  <option value="fuzzy_enhanced">🔤 Fuzzy Enhanced</option>
                  <option value="neural_ranking">🤖 Neural Ranking</option>
                </select>
              </div>

              {/* Relevance Model */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Star className="inline w-4 h-4 mr-1" />
                  Relevance Model
                </label>
                <select
                  value={searchQuery.relevanceModel}
                  onChange={(e) => setSearchQuery(prev => ({ 
                    ...prev, 
                    relevanceModel: e.target.value as any 
                  }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="bm25">📊 BM25</option>
                  <option value="tfidf">📈 TF-IDF</option>
                  <option value="neural">🧠 Neural</option>
                  <option value="hybrid_ensemble">🎯 Hybrid Ensemble</option>
                </select>
              </div>

              {/* Search Scope */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Filter className="inline w-4 h-4 mr-1" />
                  Search Scope
                </label>
                <select
                  value={searchQuery.scope}
                  onChange={(e) => setSearchQuery(prev => ({ 
                    ...prev, 
                    scope: e.target.value as any 
                  }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">🌐 All Content</option>
                  <option value="transcripts">📄 Transcripts</option>
                  <option value="users">👥 Users</option>
                  <option value="content">📁 Content</option>
                  <option value="metadata">📋 Metadata</option>
                </select>
              </div>
            </div>

            {/* Additional options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={searchQuery.diversifyResults}
                    onChange={(e) => setSearchQuery(prev => ({ 
                      ...prev, 
                      diversifyResults: e.target.checked 
                    }))}
                    className="rounded"
                  />
                  <span className="text-sm">🎭 Diversify Results</span>
                </label>
                
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={searchQuery.explainRanking}
                    onChange={(e) => setSearchQuery(prev => ({ 
                      ...prev, 
                      explainRanking: e.target.checked 
                    }))}
                    className="rounded"
                  />
                  <span className="text-sm">📖 Explain Ranking</span>
                </label>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  🎯 Semantic Similarity Threshold: {searchQuery.semanticThreshold}
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  value={searchQuery.semanticThreshold}
                  onChange={(e) => setSearchQuery(prev => ({ 
                    ...prev, 
                    semanticThreshold: parseFloat(e.target.value) 
                  }))}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}

        {/* Active filters */}
        {searchQuery.filters.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="text-sm text-gray-600">Active filters:</span>
            {searchQuery.filters.map((filter, index) => (
              <div
                key={index}
                className="flex items-center space-x-2 bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
              >
                <span>{filter.field} {filter.operator} {filter.value}</span>
                <button
                  onClick={() => removeFilter(index)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Search Results */}
      {searchResults && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Facets Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                <Filter className="w-5 h-5 mr-2" />
                Filter Results
              </h3>
              
              {Object.entries(searchResults.facets).map(([facetName, facet]) => (
                <div key={facetName} className="mb-6">
                  <h4 className="font-medium text-gray-800 mb-2">{facet.displayName}</h4>
                  
                  {facet.type === 'categorical' && facet.values && (
                    <div className="space-y-2">
                      {facet.values.map((value, index) => (
                        <label key={index} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={value.selected}
                            onChange={() => {
                              if (!value.selected) {
                                addFilter(facetName, 'eq', value.value);
                              }
                            }}
                            className="rounded"
                          />
                          <span className="text-sm">
                            {value.value} ({value.count})
                          </span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Results */}
          <div className="lg:col-span-3">
            {/* Results header */}
            <div className="bg-white rounded-lg shadow-sm border p-4 mb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className="text-gray-600">
                    Found <span className="font-semibold">{searchResults.totalCount}</span> results
                  </span>
                  <span className="text-gray-500">
                    in <span className="font-semibold">{searchResults.searchTimeMs.toFixed(1)}ms</span>
                  </span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <select
                    value={searchQuery.sortOrder}
                    onChange={(e) => setSearchQuery(prev => ({ 
                      ...prev, 
                      sortOrder: e.target.value as any 
                    }))}
                    className="p-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="relevance">⭐ Relevance</option>
                    <option value="date_desc">📅 Newest First</option>
                    <option value="date_asc">📅 Oldest First</option>
                    <option value="title_asc">🔤 Title A-Z</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Result items */}
            <div className="space-y-4">
              {searchResults.results.map((result) => (
                <div
                  key={result.id}
                  className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {result.title}
                      </h3>
                      <div className="flex items-center space-x-3 text-sm text-gray-600 mb-2">
                        <span className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          {Math.floor(result.metadata.duration / 60)}m
                        </span>
                        <span className="flex items-center">
                          <Star className="w-4 h-4 mr-1" />
                          {result.score.toFixed(2)}
                        </span>
                        <span>{result.type}</span>
                        {result.filePath && (
                          <button
                            onClick={() => openFileLocation(result.filePath!)}
                            className="text-blue-600 hover:text-blue-700 text-xs underline"
                          >
                            📁 Show in Folder
                          </button>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setSelectedResult(result)}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="View details"
                      >
                        <Eye className="w-5 h-5" />
                      </button>
                      <button
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Bookmark"
                      >
                        <Bookmark className="w-5 h-5" />
                      </button>
                      <button
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Share"
                      >
                        <Share2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                  
                  <div
                    className="text-gray-700 mb-4"
                    dangerouslySetInnerHTML={{ __html: result.highlightedContent }}
                  />
                  
                  {/* Desktop-specific: Thumbnail */}
                  {result.thumbnailPath && (
                    <div className="mb-4">
                      <img
                        src={result.thumbnailPath}
                        alt="Thumbnail"
                        className="w-32 h-20 object-cover rounded"
                      />
                    </div>
                  )}
                  
                  {/* Metadata */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {result.contentCategories.map((category, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                      >
                        {category}
                      </span>
                    ))}
                  </div>
                  
                  {/* Ranking explanation */}
                  {searchQuery.explainRanking && result.explanation && (
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg text-sm">
                      <strong>Ranking Explanation:</strong>
                      <div className="mt-2 space-y-1">
                        <div>Model: {result.explanation.rankingModel}</div>
                        <div>Total Score: {result.explanation.totalScore.toFixed(3)}</div>
                        <div>Matching Terms: {result.explanation.matchingTerms.join(', ')}</div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // Render indexing management
  const renderIndexManagement = () => (
    <div className="flex-1 p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Database className="w-6 h-6 mr-2" />
          Search Index Management
        </h2>
        
        {/* Index status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{indexStats.totalFiles}</div>
            <div className="text-sm text-gray-600">Total Files</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{indexStats.indexedFiles}</div>
            <div className="text-sm text-gray-600">Indexed Files</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">
              {indexingStatus === 'indexing' ? 'Indexing...' : indexingStatus}
            </div>
            <div className="text-sm text-gray-600">Status</div>
          </div>
        </div>
        
        {/* Index actions */}
        <div className="flex space-x-4">
          <button
            onClick={startIndexing}
            disabled={indexingStatus === 'indexing'}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
          >
            <Cpu className="w-5 h-5" />
            <span>Start Indexing</span>
          </button>
          
          <button
            onClick={() => window.electronAPI?.clearIndex?.()}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2"
          >
            <X className="w-5 h-5" />
            <span>Clear Index</span>
          </button>
        </div>
        
        {indexStats.lastIndexed && (
          <p className="mt-4 text-sm text-gray-600">
            Last indexed: {indexStats.lastIndexed.toLocaleString()}
          </p>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b flex-shrink-0">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Search className="w-8 h-8 text-blue-600" />
              <h1 className="text-xl font-semibold text-gray-900">
                Advanced Search & Discovery
              </h1>
            </div>
            
            {/* Tab navigation */}
            <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
              {[
                { id: 'search', label: 'Search', icon: Search },
                { id: 'analytics', label: 'Analytics', icon: BarChart3 },
                { id: 'index', label: 'Index', icon: Database },
                { id: 'settings', label: 'Settings', icon: Settings },
                { id: 'help', label: 'Help', icon: BookOpen }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'search' && renderSearchInterface()}
        {activeTab === 'index' && renderIndexManagement()}
        {activeTab === 'analytics' && (
          <div className="flex-1 p-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <BarChart3 className="w-6 h-6 mr-2" />
                Search Analytics
              </h2>
              <div className="space-y-4">
                {searchHistory.map((entry, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <div className="font-medium">{entry.query}</div>
                      <div className="text-sm text-gray-600">
                        {entry.timestamp.toLocaleString()} • {entry.strategy} • {entry.resultsCount} results
                      </div>
                    </div>
                    <button
                      onClick={() => setSearchQuery(prev => ({ 
                        ...prev, 
                        query: entry.query,
                        strategy: entry.strategy as any
                      }))}
                      className="text-blue-600 hover:text-blue-700 text-sm"
                    >
                      Search Again
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        {activeTab === 'settings' && (
          <div className="flex-1 p-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Search Settings
              </h2>
              <p className="text-gray-600">
                Configure search preferences, performance settings, and advanced options.
              </p>
            </div>
          </div>
        )}
        {activeTab === 'help' && (
          <div className="flex-1 p-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Search Help & Documentation
              </h2>
              <div className="prose max-w-none">
                <p>Learn how to use the advanced search features effectively:</p>
                <ul>
                  <li><strong>Basic Search:</strong> Simply type your query and hit search</li>
                  <li><strong>Boolean Search:</strong> Use AND, OR, NOT operators</li>
                  <li><strong>Semantic Search:</strong> Enable for concept-based matching</li>
                  <li><strong>Faceted Search:</strong> Use filters to narrow results</li>
                  <li><strong>File Location:</strong> Click "Show in Folder" to navigate to files</li>
                  <li><strong>Export Results:</strong> Use the Export button to save search results</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Result detail modal */}
      {selectedResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-screen overflow-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">{selectedResult.title}</h2>
                <button
                  onClick={() => setSelectedResult(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Content</h3>
                  <div className="text-gray-700">{selectedResult.content}</div>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Metadata</h3>
                  <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto">
                    {JSON.stringify(selectedResult.metadata, null, 2)}
                  </pre>
                </div>
                
                {selectedResult.extractedEntities.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Extracted Entities</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedResult.extractedEntities.map((entity, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded"
                        >
                          {entity.type}: {entity.value} ({(entity.confidence * 100).toFixed(0)}%)
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {selectedResult.filePath && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">File Location</h3>
                    <div className="flex items-center space-x-2">
                      <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                        {selectedResult.filePath}
                      </code>
                      <button
                        onClick={() => openFileLocation(selectedResult.filePath!)}
                        className="text-blue-600 hover:text-blue-700 text-sm"
                      >
                        Open in Finder
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedSearchDesktop;
