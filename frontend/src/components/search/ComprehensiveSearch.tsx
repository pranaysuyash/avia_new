import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Label } from '../ui/label';
import { Checkbox } from '../ui/checkbox';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '../ui/collapsible';
import {
  Search,
  Filter,
  Clock,
  FileText,
  User,
  Database,
  Download,
  Sparkles,
  ChevronDown,
  ChevronRight,
  X,
  Loader2,
  TrendingUp,
  BarChart3,
  RefreshCw,
} from 'lucide-react';
import { format } from 'date-fns';

// Types and interfaces
interface SearchFilter {
  field: string;
  operator: string;
  value: any;
  case_sensitive?: boolean;
}

interface SearchResult {
  id: string;
  type: string;
  title: string;
  content: string;
  highlighted_content: string;
  metadata: Record<string, any>;
  score: number;
  created_at: string;
  updated_at: string;
}

interface SearchResponse {
  results: SearchResult[];
  total_count: number;
  query: string;
  search_time_ms: number;
  facets: Record<string, Record<string, number>>;
  suggestions: string[];
  filters_applied: SearchFilter[];
  page: number;
  per_page: number;
  has_more: boolean;
}

interface SearchAnalytics {
  total_searches: number;
  unique_queries: number;
  avg_search_time_ms: number;
  avg_results_count: number;
  popular_queries: { query: string; count: number }[];
  search_types: Record<string, number>;
  search_scopes: Record<string, number>;
  daily_stats: Record<string, Record<string, number>>;
}

interface ComprehensiveSearchProps {
  className?: string;
}

export const ComprehensiveSearch: React.FC<ComprehensiveSearchProps> = ({ className }) => {
  // State
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('full_text');
  const [searchScope, setSearchScope] = useState('all');
  const [sortOrder, setSortOrder] = useState('relevance');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTime, setSearchTime] = useState(0);
  const [facets, setFacets] = useState<Record<string, Record<string, number>>>({});
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [filters, setFilters] = useState<SearchFilter[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  // UI state
  const [showFilters, setShowFilters] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<string[]>([]);
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [analytics, setAnalytics] = useState<SearchAnalytics | null>(null);

  // Refs
  const searchInputRef = useRef<HTMLInputElement>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout>();

  // Auto-complete functionality
  const fetchAutocomplete = useCallback(async (prefix: string) => {
    if (prefix.length < 2) {
      setAutocompleteSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`/api/v1/search/suggestions?prefix=${encodeURIComponent(prefix)}`);
      if (response.ok) {
        const data = await response.json();
        setAutocompleteSuggestions(data.suggestions || []);
      }
    } catch (err) {
      console.error('Autocomplete fetch error:', err);
    }
  }, []);

  const handleInputChange = (value: string) => {
    setQuery(value);
    
    // Debounced autocomplete
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }
    
    debounceTimeoutRef.current = setTimeout(() => {
      fetchAutocomplete(value);
      setShowAutocomplete(value.length >= 2);
    }, 300);
  };

  // Search functionality
  const performSearch = async (resetPage = true) => {
    if (!query.trim()) {
      return;
    }

    setLoading(true);
    setError(null);
    
    if (resetPage) {
      setPage(1);
    }

    try {
      const searchRequest = {
        query,
        search_type: searchType,
        scope: searchScope,
        filters,
        sort_order: sortOrder,
        limit: 20,
        offset: resetPage ? 0 : (page - 1) * 20,
        highlight: true,
        facets: ['language', 'duration', 'created_month', 'type']
      };

      const response = await fetch('/api/v1/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchRequest),
      });

      if (!response.ok) {
        throw new Error('Search request failed');
      }

      const data: SearchResponse = await response.json();
      
      if (resetPage) {
        setResults(data.results);
      } else {
        setResults(prev => [...prev, ...data.results]);
      }
      
      setTotalCount(data.total_count);
      setSearchTime(data.search_time_ms);
      setFacets(data.facets);
      setSuggestions(data.suggestions);
      setHasMore(data.has_more);
      setShowAutocomplete(false);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  // Track search result clicks
  const trackClick = async (resultId: string) => {
    try {
      await fetch('/api/v1/search/click', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          result_id: resultId
        }),
      });
    } catch (err) {
      console.error('Click tracking failed:', err);
    }
  };

  // Load analytics
  const loadAnalytics = async () => {
    try {
      const response = await fetch('/api/v1/search/analytics?days=30');
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error('Analytics fetch error:', err);
    }
  };

  // Export search results
  const exportResults = async (format: 'json' | 'csv') => {
    try {
      const response = await fetch(
        `/api/v1/search/export?query=${encodeURIComponent(query)}&format_type=${format}&max_results=1000`
      );
      
      if (!response.ok) {
        throw new Error('Export failed');
      }

      const data = await response.json();
      
      if (format === 'csv') {
        // Download CSV
        const blob = new Blob([data.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `search_results_${Date.now()}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // Download JSON
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `search_results_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }

      setShowExportDialog(false);
    } catch (err) {
      setError('Export failed');
    }
  };

  // Filter management
  const addFilter = (field: string, operator: string, value: any) => {
    const newFilter: SearchFilter = { field, operator, value };
    setFilters(prev => [...prev, newFilter]);
  };

  const removeFilter = (index: number) => {
    setFilters(prev => prev.filter((_, i) => i !== index));
  };

  const clearAllFilters = () => {
    setFilters([]);
  };

  // Handle suggestion selection
  const selectSuggestion = (suggestion: string) => {
    setQuery(suggestion);
    setShowAutocomplete(false);
    // Auto-search when suggestion is selected
    setTimeout(() => performSearch(), 100);
  };

  // Load analytics on component mount
  useEffect(() => {
    loadAnalytics();
  }, []);

  // Perform search when filters change
  useEffect(() => {
    if (query.trim()) {
      performSearch();
    }
  }, [filters, searchType, searchScope, sortOrder]);

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'transcript':
        return <FileText className="h-4 w-4" />;
      case 'user':
        return <User className="h-4 w-4" />;
      case 'cached_content':
        return <Database className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'transcript':
        return 'bg-blue-100 text-blue-800';
      case 'user':
        return 'bg-green-100 text-green-800';
      case 'cached_content':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Comprehensive Search
          </CardTitle>
          <CardDescription>
            Search across transcripts, users, and content with advanced filtering and analytics
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Search Bar and Controls */}
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            {/* Main Search Input */}
            <div className="relative">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    ref={searchInputRef}
                    placeholder="Search transcripts, users, content..."
                    value={query}
                    onChange={(e) => handleInputChange(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        performSearch();
                      } else if (e.key === 'Escape') {
                        setShowAutocomplete(false);
                      }
                    }}
                    className="pl-10"
                  />
                  
                  {/* Autocomplete Suggestions */}
                  {showAutocomplete && autocompleteSuggestions.length > 0 && (
                    <div className="absolute top-full left-0 right-0 z-50 mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto">
                      {autocompleteSuggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                          onClick={() => selectSuggestion(suggestion)}
                        >
                          <div className="flex items-center gap-2">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            {suggestion}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                
                <Button onClick={() => performSearch()} disabled={loading || !query.trim()}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                  Search
                </Button>
              </div>

              {/* Search Type and Scope Controls */}
              <div className="flex gap-2 mt-3">
                <Select value={searchType} onValueChange={setSearchType}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="full_text">Full Text</SelectItem>
                    <SelectItem value="exact">Exact Match</SelectItem>
                    <SelectItem value="fuzzy">Fuzzy</SelectItem>
                    <SelectItem value="regex">Regex</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={searchScope} onValueChange={setSearchScope}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="transcripts">Transcripts</SelectItem>
                    <SelectItem value="users">Users</SelectItem>
                    <SelectItem value="content">Content</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={sortOrder} onValueChange={setSortOrder}>
                  <SelectTrigger className="w-36">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="relevance">Relevance</SelectItem>
                    <SelectItem value="date_desc">Newest</SelectItem>
                    <SelectItem value="date_asc">Oldest</SelectItem>
                    <SelectItem value="title_asc">Title A-Z</SelectItem>
                  </SelectContent>
                </Select>

                <Button
                  variant="outline"
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center gap-1"
                >
                  <Filter className="h-4 w-4" />
                  Filters
                  {filters.length > 0 && (
                    <Badge variant="secondary" className="ml-1">
                      {filters.length}
                    </Badge>
                  )}
                </Button>

                <Button
                  variant="outline"
                  onClick={() => setShowAnalytics(!showAnalytics)}
                >
                  <BarChart3 className="h-4 w-4" />
                </Button>

                {results.length > 0 && (
                  <Button
                    variant="outline"
                    onClick={() => setShowExportDialog(true)}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                )}
              </div>

              {/* Active Filters */}
              {filters.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {filters.map((filter, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      {filter.field} {filter.operator} {String(filter.value)}
                      <button
                        onClick={() => removeFilter(index)}
                        className="ml-1 hover:bg-gray-300 rounded"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                  <Button variant="ghost" size="sm" onClick={clearAllFilters}>
                    Clear all
                  </Button>
                </div>
              )}

              {/* Search Suggestions */}
              {suggestions.length > 0 && !loading && query && (
                <div className="mt-3">
                  <div className="text-sm text-muted-foreground mb-2">Did you mean:</div>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => selectSuggestion(suggestion)}
                        className="text-sm px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Results Summary */}
      {(results.length > 0 || loading) && (
        <div className="flex justify-between items-center text-sm text-muted-foreground">
          <span>
            {loading ? 'Searching...' : `${totalCount} results found in ${searchTime.toFixed(0)}ms`}
          </span>
          {!loading && (
            <Button variant="ghost" size="sm" onClick={() => performSearch()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Facets Sidebar */}
        {Object.keys(facets).length > 0 && (
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Refine Results</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(facets).map(([facetName, facetValues]) => (
                  <Collapsible key={facetName}>
                    <CollapsibleTrigger className="flex items-center justify-between w-full text-sm font-medium">
                      <span className="capitalize">{facetName.replace('_', ' ')}</span>
                      <ChevronDown className="h-4 w-4" />
                    </CollapsibleTrigger>
                    <CollapsibleContent className="space-y-2 mt-2">
                      {Object.entries(facetValues)
                        .sort(([, a], [, b]) => b - a)
                        .slice(0, 8)
                        .map(([value, count]) => (
                          <button
                            key={value}
                            onClick={() => addFilter(facetName, 'eq', value)}
                            className="flex justify-between w-full text-sm py-1 px-2 hover:bg-gray-100 rounded"
                          >
                            <span>{value}</span>
                            <span className="text-muted-foreground">({count})</span>
                          </button>
                        ))
                      }
                    </CollapsibleContent>
                  </Collapsible>
                ))}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Results */}
        <div className={Object.keys(facets).length > 0 ? "lg:col-span-3" : "lg:col-span-4"}>
          <div className="space-y-4">
            {results.map((result) => (
              <Card
                key={result.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => trackClick(result.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getResultIcon(result.type)}
                      <Badge variant="outline" className={getTypeColor(result.type)}>
                        {result.type}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        Score: {result.score.toFixed(2)}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {format(new Date(result.created_at), 'MMM dd, yyyy')}
                    </div>
                  </div>

                  <h3 className="font-medium text-lg mb-2">{result.title}</h3>
                  
                  <div
                    className="text-sm text-muted-foreground mb-3"
                    dangerouslySetInnerHTML={{ __html: result.highlighted_content }}
                  />

                  {/* Metadata */}
                  {Object.keys(result.metadata).length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(result.metadata)
                        .filter(([key, value]) => value !== null && value !== undefined && value !== "")
                        .slice(0, 5)
                        .map(([key, value]) => (
                          <Badge key={key} variant="outline" className="text-xs">
                            {key}: {String(value)}
                          </Badge>
                        ))
                      }
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}

            {loading && (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            )}

            {hasMore && !loading && (
              <div className="flex justify-center">
                <Button
                  variant="outline"
                  onClick={() => {
                    setPage(prev => prev + 1);
                    performSearch(false);
                  }}
                >
                  Load More Results
                </Button>
              </div>
            )}

            {results.length === 0 && !loading && query && (
              <Card>
                <CardContent className="p-8 text-center">
                  <Search className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No results found</h3>
                  <p className="text-muted-foreground mb-4">
                    Try adjusting your search terms or filters
                  </p>
                  {suggestions.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Suggestions:</p>
                      <div className="flex flex-wrap gap-2 justify-center">
                        {suggestions.map((suggestion, index) => (
                          <Button
                            key={index}
                            variant="outline"
                            size="sm"
                            onClick={() => selectSuggestion(suggestion)}
                          >
                            {suggestion}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Analytics Modal */}
      <Dialog open={showAnalytics} onOpenChange={setShowAnalytics}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Search Analytics</DialogTitle>
            <DialogDescription>
              Your search patterns and popular queries from the last 30 days
            </DialogDescription>
          </DialogHeader>

          {analytics && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-500">{analytics.total_searches}</div>
                  <div className="text-xs text-muted-foreground">Total Searches</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-500">{analytics.unique_queries}</div>
                  <div className="text-xs text-muted-foreground">Unique Queries</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-500">
                    {analytics.avg_search_time_ms.toFixed(0)}ms
                  </div>
                  <div className="text-xs text-muted-foreground">Avg Search Time</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-500">
                    {analytics.avg_results_count.toFixed(1)}
                  </div>
                  <div className="text-xs text-muted-foreground">Avg Results</div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2">Popular Queries</h4>
                  <div className="space-y-1">
                    {analytics.popular_queries.slice(0, 5).map(({ query, count }, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span>{query}</span>
                        <span className="text-muted-foreground">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Search Types</h4>
                  <div className="space-y-1">
                    {Object.entries(analytics.search_types).map(([type, count]) => (
                      <div key={type} className="flex justify-between text-sm">
                        <span className="capitalize">{type.replace('_', ' ')}</span>
                        <span className="text-muted-foreground">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button onClick={() => setShowAnalytics(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={showExportDialog} onOpenChange={setShowExportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Export Search Results</DialogTitle>
            <DialogDescription>
              Export your search results in JSON or CSV format
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label>Export Format</Label>
              <div className="flex gap-4 mt-2">
                <Button
                  variant="outline"
                  onClick={() => exportResults('json')}
                  className="flex-1"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  JSON
                </Button>
                <Button
                  variant="outline"
                  onClick={() => exportResults('csv')}
                  className="flex-1"
                >
                  <Download className="h-4 w-4 mr-2" />
                  CSV
                </Button>
              </div>
            </div>

            <div className="text-sm text-muted-foreground">
              Export will include up to 1,000 results for query: "{query}"
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowExportDialog(false)}>
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ComprehensiveSearch;