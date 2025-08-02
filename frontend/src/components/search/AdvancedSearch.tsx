import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Badge,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondary,
  CircularProgress,
  Alert,
  Autocomplete,
  Slider,
  Switch
} from '@mui/material';
import {
  Search,
  FilterList,
  ExpandMore,
  Clear,
  Save,
  History,
  Download,
  Visibility,
  AccessTime,
  Person,
  Language,
  Tag,
  Confidence,
  TrendingUp,
  Psychology,
  VolumeUp
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

interface SearchResult {
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

interface SearchFilters {
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

interface SearchOptions {
  limit: number;
  offset: number;
  sortBy: 'relevance' | 'date_desc' | 'date_asc' | 'title';
  highlight: boolean;
  fuzzy: boolean;
  includeFacets: boolean;
}

interface SearchResponse {
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

interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: SearchFilters;
  useCount: number;
  createdAt: string;
}

export const AdvancedSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({});
  const [options, setOptions] = useState<SearchOptions>({
    limit: 25,
    offset: 0,
    sortBy: 'relevance',
    highlight: true,
    fuzzy: false,
    includeFacets: true
  });
  
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [searchHistory, setSearchHistory] = useState<Array<{
    query: string;
    timestamp: string;
    resultCount: number;
  }>>([]);
  
  const [showFilters, setShowFilters] = useState(false);
  const [saveSearchName, setSaveSearchName] = useState('');
  
  // Available options for filters
  const languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'ru', 'ja', 'ko', 'zh'];
  const entityTypes = ['PERSON', 'ORG', 'LOC', 'DATE', 'TIME', 'MONEY', 'PERCENT', 'PRODUCT'];
  const sortOptions = [
    { value: 'relevance', label: 'Relevance' },
    { value: 'date_desc', label: 'Date (newest)' },
    { value: 'date_asc', label: 'Date (oldest)' },
    { value: 'title', label: 'Title' }
  ];

  const executeSearch = useCallback(async (searchQuery?: string, searchFilters?: SearchFilters, searchOptions?: SearchOptions) => {
    const finalQuery = searchQuery ?? query;
    const finalFilters = searchFilters ?? filters;
    const finalOptions = searchOptions ?? options;
    
    if (!finalQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/search/advanced', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: finalQuery,
          filters: finalFilters,
          options: finalOptions
        }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const result: SearchResponse = await response.json();
      setSearchResults(result);
      
      // Add to search history
      setSearchHistory(prev => [{
        query: finalQuery,
        timestamp: new Date().toISOString(),
        resultCount: result.totalCount
      }, ...prev.slice(0, 9)]);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [query, filters, options]);

  const handleQuickFilter = (filterType: string, value: any) => {
    const newFilters = { ...filters };
    
    switch (filterType) {
      case 'today':
        newFilters.dateRange = {
          start: new Date(),
          end: new Date()
        };
        break;
      case 'week':
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        newFilters.dateRange = {
          start: weekAgo,
          end: new Date()
        };
        break;
      case 'has_speakers':
        newFilters.hasSpeakers = true;
        break;
      case 'has_tags':
        newFilters.hasTags = true;
        break;
      case 'has_entities':
        newFilters.hasEntities = true;
        break;
    }
    
    setFilters(newFilters);
    executeSearch(query, newFilters, options);
  };

  const handleFacetClick = (facetType: string, facetValue: string) => {
    const newFilters = { ...filters };
    
    switch (facetType) {
      case 'language':
        newFilters.language = facetValue;
        break;
      case 'speakers':
        newFilters.speakers = [...(newFilters.speakers || []), facetValue];
        break;
      case 'tags':
        newFilters.tags = [...(newFilters.tags || []), facetValue];
        break;
      case 'entity_types':
        newFilters.entityTypes = [...(newFilters.entityTypes || []), facetValue];
        break;
    }
    
    setFilters(newFilters);
    executeSearch(query, newFilters, options);
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    const newOptions = {
      ...options,
      offset: (page - 1) * options.limit
    };
    setOptions(newOptions);
    executeSearch(query, filters, newOptions);
  };

  const saveCurrentSearch = async () => {
    if (!saveSearchName.trim()) {
      setError('Please enter a name for the saved search');
      return;
    }

    try {
      const response = await fetch('/api/search/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: saveSearchName,
          query,
          filters
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save search');
      }

      const savedSearch = await response.json();
      setSavedSearches(prev => [savedSearch, ...prev]);
      setSaveSearchName('');
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save search');
    }
  };

  const loadSavedSearch = (savedSearch: SavedSearch) => {
    setQuery(savedSearch.query);
    setFilters(savedSearch.filters);
    executeSearch(savedSearch.query, savedSearch.filters, options);
  };

  const exportResults = () => {
    if (!searchResults) return;
    
    const exportData = {
      query,
      filters,
      totalResults: searchResults.totalCount,
      searchTime: searchResults.searchTimeMs,
      results: searchResults.results,
      exportedAt: new Date().toISOString()
    };
    
    const jsonData = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `search_results_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearFilters = () => {
    setFilters({});
    setOptions({
      ...options,
      offset: 0
    });
  };

  const renderSearchInterface = () => (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} md={8}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search transcripts... Use quotes for exact phrases, - for exclusions, + for required terms"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && executeSearch()}
            InputProps={{
              startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              endAdornment: query && (
                <IconButton onClick={() => setQuery('')} size="small">
                  <Clear />
                </IconButton>
              )
            }}
          />
        </Grid>
        
        <Grid item xs={12} md={2}>
          <Button
            fullWidth
            variant="contained"
            onClick={() => executeSearch()}
            disabled={loading || !query.trim()}
            startIcon={loading ? <CircularProgress size={20} /> : <Search />}
            sx={{ height: '56px' }}
          >
            Search
          </Button>
        </Grid>
        
        <Grid item xs={12} md={2}>
          <Button
            fullWidth
            variant="outlined"
            onClick={() => setShowFilters(!showFilters)}
            startIcon={<FilterList />}
            sx={{ height: '56px' }}
          >
            Filters
            {Object.keys(filters).length > 0 && (
              <Badge badgeContent={Object.keys(filters).length} color="primary" sx={{ ml: 1 }} />
            )}
          </Button>
        </Grid>
      </Grid>

      {/* Quick Filters */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="subtitle2" gutterBottom>Quick Filters:</Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip
            label="Today"
            onClick={() => handleQuickFilter('today', null)}
            icon={<AccessTime />}
            variant="outlined"
            size="small"
          />
          <Chip
            label="This Week"
            onClick={() => handleQuickFilter('week', null)}
            icon={<AccessTime />}
            variant="outlined"
            size="small"
          />
          <Chip
            label="With Speakers"
            onClick={() => handleQuickFilter('has_speakers', null)}
            icon={<Person />}
            variant="outlined"
            size="small"
          />
          <Chip
            label="Tagged"
            onClick={() => handleQuickFilter('has_tags', null)}
            icon={<Tag />}
            variant="outlined"
            size="small"
          />
          <Chip
            label="With Entities"
            onClick={() => handleQuickFilter('has_entities', null)}
            icon={<Psychology />}
            variant="outlined"
            size="small"
          />
        </Box>
      </Box>
    </Paper>
  );

  const renderAdvancedFilters = () => (
    showFilters && (
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Advanced Filters</Typography>
          <Button onClick={clearFilters} startIcon={<Clear />} size="small">
            Clear All
          </Button>
        </Box>
        
        <Grid container spacing={3}>
          {/* Date Range */}
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>Date Range</Typography>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <DatePicker
                    label="Start Date"
                    value={filters.dateRange?.start || null}
                    onChange={(date) => setFilters({
                      ...filters,
                      dateRange: { ...filters.dateRange, start: date }
                    })}
                    slotProps={{ textField: { size: 'small', fullWidth: true } }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <DatePicker
                    label="End Date"
                    value={filters.dateRange?.end || null}
                    onChange={(date) => setFilters({
                      ...filters,
                      dateRange: { ...filters.dateRange, end: date }
                    })}
                    slotProps={{ textField: { size: 'small', fullWidth: true } }}
                  />
                </Grid>
              </Grid>
            </LocalizationProvider>
          </Grid>

          {/* Language */}
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Language</InputLabel>
              <Select
                value={filters.language || ''}
                onChange={(e) => setFilters({ ...filters, language: e.target.value })}
                label="Language"
              >
                <MenuItem value="">Any</MenuItem>
                {languages.map(lang => (
                  <MenuItem key={lang} value={lang}>{lang.toUpperCase()}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Confidence */}
          <Grid item xs={12} md={3}>
            <Typography variant="subtitle2" gutterBottom>
              Minimum Confidence: {filters.minConfidence || 0}
            </Typography>
            <Slider
              value={filters.minConfidence || 0}
              onChange={(_, value) => setFilters({ ...filters, minConfidence: value as number })}
              min={0}
              max={1}
              step={0.1}
              marks
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
            />
          </Grid>

          {/* Speakers */}
          <Grid item xs={12} md={6}>
            <Autocomplete
              multiple
              options={[]} // Would be populated from API
              freeSolo
              value={filters.speakers || []}
              onChange={(_, value) => setFilters({ ...filters, speakers: value })}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip variant="outlined" label={option} {...getTagProps({ index })} />
                ))
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Speakers"
                  placeholder="Enter speaker names"
                  size="small"
                />
              )}
            />
          </Grid>

          {/* Tags */}
          <Grid item xs={12} md={6}>
            <Autocomplete
              multiple
              options={[]} // Would be populated from API
              freeSolo
              value={filters.tags || []}
              onChange={(_, value) => setFilters({ ...filters, tags: value })}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip variant="outlined" label={option} {...getTagProps({ index })} />
                ))
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Tags"
                  placeholder="Enter tags"
                  size="small"
                />
              )}
            />
          </Grid>

          {/* Entity Types */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>Entity Types</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {entityTypes.map(type => (
                <FormControlLabel
                  key={type}
                  control={
                    <Checkbox
                      checked={filters.entityTypes?.includes(type) || false}
                      onChange={(e) => {
                        const current = filters.entityTypes || [];
                        const updated = e.target.checked
                          ? [...current, type]
                          : current.filter(t => t !== type);
                        setFilters({ ...filters, entityTypes: updated });
                      }}
                      size="small"
                    />
                  }
                  label={type}
                />
              ))}
            </Box>
          </Grid>
        </Grid>
      </Paper>
    )
  );

  const renderSearchOptions = () => (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Results per page</InputLabel>
            <Select
              value={options.limit}
              onChange={(e) => setOptions({ ...options, limit: e.target.value as number, offset: 0 })}
              label="Results per page"
            >
              <MenuItem value={10}>10</MenuItem>
              <MenuItem value={25}>25</MenuItem>
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Sort by</InputLabel>
            <Select
              value={options.sortBy}
              onChange={(e) => setOptions({ ...options, sortBy: e.target.value as any })}
              label="Sort by"
            >
              {sortOptions.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={3}>
          <FormControlLabel
            control={
              <Switch
                checked={options.highlight}
                onChange={(e) => setOptions({ ...options, highlight: e.target.checked })}
              />
            }
            label="Highlight matches"
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <FormControlLabel
            control={
              <Switch
                checked={options.fuzzy}
                onChange={(e) => setOptions({ ...options, fuzzy: e.target.checked })}
              />
            }
            label="Fuzzy matching"
          />
        </Grid>
      </Grid>
    </Paper>
  );

  const renderSearchResults = () => {
    if (!searchResults) return null;

    return (
      <Box>
        {/* Results Summary */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Grid container justifyContent="space-between" alignItems="center">
            <Grid item>
              {searchResults.totalCount > 0 ? (
                <Typography>
                  Found <strong>{searchResults.totalCount}</strong> results 
                  (showing {searchResults.pageInfo.showingFrom}-{searchResults.pageInfo.showingTo}) 
                  in {searchResults.searchTimeMs.toFixed(0)}ms
                </Typography>
              ) : (
                <Typography>No results found</Typography>
              )}
            </Grid>
            
            <Grid item>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  size="small"
                  placeholder="Save search as..."
                  value={saveSearchName}
                  onChange={(e) => setSaveSearchName(e.target.value)}
                  sx={{ width: 200 }}
                />
                <Button
                  onClick={saveCurrentSearch}
                  disabled={!saveSearchName.trim()}
                  startIcon={<Save />}
                  size="small"
                >
                  Save
                </Button>
                <Button
                  onClick={exportResults}
                  startIcon={<Download />}
                  size="small"
                >
                  Export
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Paper>

        {/* No Results - Show Suggestions */}
        {searchResults.totalCount === 0 && searchResults.suggestions.length > 0 && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>Try these searches:</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {searchResults.suggestions.map((suggestion, index) => (
                <Chip
                  key={index}
                  label={suggestion}
                  onClick={() => {
                    setQuery(suggestion);
                    executeSearch(suggestion, filters, options);
                  }}
                  variant="outlined"
                />
              ))}
            </Box>
          </Paper>
        )}

        {/* Facets */}
        {searchResults.facets && Object.keys(searchResults.facets).length > 0 && (
          <Paper sx={{ p: 2, mb: 3 }}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Filter by facets</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  {Object.entries(searchResults.facets).map(([facetType, facetValues]) => (
                    <Grid item xs={12} md={3} key={facetType}>
                      <Typography variant="subtitle2" gutterBottom>
                        {facetType.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                        {Object.entries(facetValues).slice(0, 10).map(([value, count]) => (
                          <Chip
                            key={value}
                            label={`${value} (${count})`}
                            onClick={() => handleFacetClick(facetType, value)}
                            variant="outlined"
                            size="small"
                            sx={{ justifyContent: 'flex-start' }}
                          />
                        ))}
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Paper>
        )}

        {/* Results List */}
        {searchResults.results.map((result, index) => (
          <Card key={result.doc_id} sx={{ mb: 2 }}>
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={9}>
                  <Typography variant="h6" gutterBottom>
                    {result.title}
                  </Typography>
                  
                  {result.title_snippet && result.title_snippet.includes('<mark>') && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      dangerouslySetInnerHTML={{ __html: `Title match: ${result.title_snippet}` }}
                      sx={{ mb: 1 }}
                    />
                  )}
                  
                  {result.content_snippet && (
                    <Typography
                      variant="body2"
                      dangerouslySetInnerHTML={{ __html: result.content_snippet }}
                      sx={{ mb: 2 }}
                    />
                  )}
                  
                  {/* Metadata Tags */}
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {result.created_at && (
                      <Chip
                        icon={<AccessTime />}
                        label={new Date(result.created_at).toLocaleDateString()}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    
                    {result.language && (
                      <Chip
                        icon={<Language />}
                        label={result.language.toUpperCase()}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    
                    {result.confidence && (
                      <Chip
                        icon={<Confidence />}
                        label={`${(result.confidence * 100).toFixed(0)}%`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    
                    {result.speakers && result.speakers.length > 0 && (
                      <Chip
                        icon={<Person />}
                        label={`${result.speakers.length} speakers`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    
                    {result.tags && result.tags.length > 0 && (
                      <Chip
                        icon={<Tag />}
                        label={result.tags.slice(0, 3).join(', ')}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    
                    {result.entities && result.entities.length > 0 && (
                      <Chip
                        icon={<Psychology />}
                        label={`${result.entities.length} entities`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={3} sx={{ textAlign: 'right' }}>
                  <Button
                    variant="outlined"
                    startIcon={<Visibility />}
                    onClick={() => {
                      // Navigate to transcript viewer
                      window.location.href = `/transcript/${result.doc_id}`;
                    }}
                  >
                    View
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        ))}

        {/* Pagination */}
        {searchResults.pageInfo.totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Pagination
              count={searchResults.pageInfo.totalPages}
              page={searchResults.pageInfo.currentPage}
              onChange={handlePageChange}
              color="primary"
              size="large"
            />
          </Box>
        )}
      </Box>
    );
  };

  const renderSidebar = () => (
    <Box>
      {/* Saved Searches */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Save />
          Saved Searches
        </Typography>
        
        {savedSearches.length > 0 ? (
          <List dense>
            {savedSearches.map((savedSearch) => (
              <ListItem
                key={savedSearch.id}
                button
                onClick={() => loadSavedSearch(savedSearch)}
              >
                <ListItemText
                  primary={savedSearch.name}
                  secondary={`Used ${savedSearch.useCount} times`}
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No saved searches yet
          </Typography>
        )}
      </Paper>

      {/* Search History */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <History />
          Recent Searches
        </Typography>
        
        {searchHistory.length > 0 ? (
          <List dense>
            {searchHistory.map((historyItem, index) => (
              <ListItem
                key={index}
                button
                onClick={() => {
                  setQuery(historyItem.query);
                  executeSearch(historyItem.query, filters, options);
                }}
              >
                <ListItemText
                  primary={historyItem.query.length > 30 
                    ? `${historyItem.query.substring(0, 30)}...` 
                    : historyItem.query
                  }
                  secondary={`${historyItem.resultCount} results`}
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No recent searches
          </Typography>
        )}
      </Paper>
    </Box>
  );

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Search />
          Advanced Search
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12} md={9}>
            {renderSearchInterface()}
            {renderAdvancedFilters()}
            {renderSearchOptions()}
            {renderSearchResults()}
          </Grid>
          
          <Grid item xs={12} md={3}>
            {renderSidebar()}
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default AdvancedSearch;