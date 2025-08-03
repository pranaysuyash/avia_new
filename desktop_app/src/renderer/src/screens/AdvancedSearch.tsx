import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  BookmarkIcon,
  ClockIcon,
  InformationCircleIcon,
  XMarkIcon,
  CheckIcon,
  DocumentTextIcon,
  UserIcon,
  BuildingOfficeIcon,
  TagIcon,
  LanguageIcon,
  CalendarIcon,
  AdjustmentsHorizontalIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid';

interface SearchResult {
  id: string;
  title: string;
  snippet: string;
  relevance_score: number;
  matched_fields: string[];
  speakers: string[];
  language: string;
  duration: number;
  created_at: string;
  entities: string[];
  topics: string[];
  tags: string[];
  view_count: number;
}

interface SearchSuggestion {
  type: 'term' | 'field' | 'operator' | 'filter';
  value: string;
  display: string;
}

interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: any;
  created_at: string;
  notification_enabled: boolean;
  last_run: string;
  new_results: number;
}

const AdvancedSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState<any[]>([]);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [operators, setOperators] = useState<any>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Filters state
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    languages: [] as string[],
    speakers: [] as string[],
    duration_min: '',
    duration_max: '',
    entities: [] as string[],
    topics: [] as string[],
    tags: [] as string[]
  });

  // Quick date filters
  const quickDateFilters = [
    { label: 'Today', value: 'today' },
    { label: 'Yesterday', value: 'yesterday' },
    { label: 'Last 7 days', value: 'last-7-days' },
    { label: 'Last 30 days', value: 'last-30-days' },
    { label: 'This week', value: 'this-week' },
    { label: 'This month', value: 'this-month' }
  ];

  // Available languages
  const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'nl', name: 'Dutch' },
    { code: 'ru', name: 'Russian' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
    { code: 'zh', name: 'Chinese' }
  ];

  useEffect(() => {
    loadOperators();
    loadSearchHistory();
    loadSavedSearches();
  }, []);

  useEffect(() => {
    if (query.length > 0) {
      loadSuggestions();
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [query]);

  const loadOperators = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/search/operators');
      if (response.ok) {
        const result = await response.json();
        setOperators(result.data);
      }
    } catch (error) {
      console.error('Failed to load operators:', error);
    }
  };

  const loadSuggestions = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/search/suggestions?q=${encodeURIComponent(query)}`);
      if (response.ok) {
        const result = await response.json();
        setSuggestions(result.data.suggestions);
        setShowSuggestions(true);
      }
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };

  const loadSearchHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/search/history');
      if (response.ok) {
        const result = await response.json();
        setSearchHistory(result.data.history);
      }
    } catch (error) {
      console.error('Failed to load search history:', error);
    }
  };

  const loadSavedSearches = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/search/saved');
      if (response.ok) {
        const result = await response.json();
        setSavedSearches(result.data.saved_searches);
      }
    } catch (error) {
      console.error('Failed to load saved searches:', error);
    }
  };

  const performSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setShowSuggestions(false);
    
    try {
      const response = await fetch('http://localhost:8000/api/search/advanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          filters: {
            ...filters,
            duration_min: filters.duration_min ? parseInt(filters.duration_min) : null,
            duration_max: filters.duration_max ? parseInt(filters.duration_max) : null
          },
          limit: 50,
          offset: 0
        })
      });

      if (response.ok) {
        const result = await response.json();
        setResults(result.data.results);
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.value);
    setShowSuggestions(false);
    searchInputRef.current?.focus();
  };

  const handleQuickDateFilter = (value: string) => {
    const newQuery = query.includes('date:') 
      ? query.replace(/date:\S+/, `date:${value}`)
      : `${query} date:${value}`.trim();
    setQuery(newQuery);
  };

  const saveSearch = async () => {
    const name = prompt('Enter a name for this saved search:');
    if (!name) return;

    try {
      const response = await fetch('http://localhost:8000/api/search/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          query,
          filters,
          notification_enabled: false
        })
      });

      if (response.ok) {
        loadSavedSearches();
      }
    } catch (error) {
      console.error('Failed to save search:', error);
    }
  };

  const loadSavedSearch = (savedSearch: SavedSearch) => {
    setQuery(savedSearch.query);
    setFilters(savedSearch.filters || {});
    performSearch();
  };

  const renderSearchBar = () => (
    <div className="relative">
      <div className="flex items-center space-x-3">
        <div className="flex-1 relative">
          <input
            ref={searchInputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && performSearch()}
            placeholder="Search with operators: AND, OR, NOT, quotes for phrases, * for wildcards..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <MagnifyingGlassIcon className="absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
          
          {/* Suggestions Dropdown */}
          <AnimatePresence>
            {showSuggestions && suggestions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute z-10 mt-1 w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 max-h-64 overflow-y-auto"
              >
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="w-full px-4 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center justify-between"
                  >
                    <span className="text-sm text-gray-900 dark:text-white">
                      {suggestion.display}
                    </span>
                    <span className="text-xs text-gray-500 capitalize">
                      {suggestion.type}
                    </span>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <button
          onClick={performSearch}
          disabled={loading}
          className="btn-primary px-6 py-3"
        >
          {loading ? (
            <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
          ) : (
            'Search'
          )}
        </button>

        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`p-3 rounded-lg border ${
            showFilters 
              ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-500' 
              : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600'
          } hover:bg-gray-50 dark:hover:bg-gray-700`}
        >
          <FunnelIcon className="h-5 w-5" />
        </button>

        <button
          onClick={saveSearch}
          className="p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          <BookmarkIcon className="h-5 w-5" />
        </button>

        <button
          onClick={() => setShowHelp(!showHelp)}
          className="p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          <InformationCircleIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Quick Date Filters */}
      <div className="mt-3 flex items-center space-x-2">
        <span className="text-sm text-gray-500">Quick filters:</span>
        {quickDateFilters.map((filter) => (
          <button
            key={filter.value}
            onClick={() => handleQuickDateFilter(filter.value)}
            className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-full"
          >
            {filter.label}
          </button>
        ))}
      </div>
    </div>
  );

  const renderFilters = () => (
    <AnimatePresence>
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
        >
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Advanced Filters
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Date Range
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => setFilters({...filters, date_from: e.target.value})}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
                <span>to</span>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => setFilters({...filters, date_to: e.target.value})}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </div>

            {/* Duration Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Duration (seconds)
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={filters.duration_min}
                  onChange={(e) => setFilters({...filters, duration_min: e.target.value})}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
                <span>-</span>
                <input
                  type="number"
                  placeholder="Max"
                  value={filters.duration_max}
                  onChange={(e) => setFilters({...filters, duration_max: e.target.value})}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </div>

            {/* Languages */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Languages
              </label>
              <select
                multiple
                value={filters.languages}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions, option => option.value);
                  setFilters({...filters, languages: selected});
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                size={3}
              >
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Speakers */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Speakers
              </label>
              <input
                type="text"
                placeholder="Enter speaker names..."
                value={filters.speakers.join(', ')}
                onChange={(e) => setFilters({
                  ...filters, 
                  speakers: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>

            {/* Topics */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Topics
              </label>
              <input
                type="text"
                placeholder="Enter topics..."
                value={filters.topics.join(', ')}
                onChange={(e) => setFilters({
                  ...filters, 
                  topics: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tags
              </label>
              <input
                type="text"
                placeholder="Enter tags..."
                value={filters.tags.join(', ')}
                onChange={(e) => setFilters({
                  ...filters, 
                  tags: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>
          </div>

          <div className="mt-4 flex justify-end space-x-3">
            <button
              onClick={() => setFilters({
                date_from: '',
                date_to: '',
                languages: [],
                speakers: [],
                duration_min: '',
                duration_max: '',
                entities: [],
                topics: [],
                tags: []
              })}
              className="btn-secondary text-sm"
            >
              Clear Filters
            </button>
            <button
              onClick={performSearch}
              className="btn-primary text-sm"
            >
              Apply Filters
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  const renderHelp = () => (
    <AnimatePresence>
      {showHelp && operators && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="mt-4 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800"
        >
          <div className="flex items-start justify-between mb-4">
            <h3 className="text-lg font-medium text-blue-900 dark:text-blue-100">
              Search Help
            </h3>
            <button
              onClick={() => setShowHelp(false)}
              className="text-blue-600 hover:text-blue-800"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Operators */}
            <div>
              <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-3">
                Operators
              </h4>
              <div className="space-y-2">
                {operators.operators.map((op: any) => (
                  <div key={op.operator} className="text-sm">
                    <span className="font-mono bg-blue-100 dark:bg-blue-800 px-2 py-1 rounded">
                      {op.operator}
                    </span>
                    <span className="text-blue-700 dark:text-blue-300 ml-2">
                      {op.description}
                    </span>
                    <div className="text-xs text-blue-600 dark:text-blue-400 mt-1 ml-8">
                      Example: {op.example}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Field Searches */}
            <div>
              <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-3">
                Field Searches
              </h4>
              <div className="space-y-2">
                {operators.fields.slice(0, 6).map((field: any) => (
                  <div key={field.field} className="text-sm">
                    <span className="font-mono bg-blue-100 dark:bg-blue-800 px-2 py-1 rounded">
                      {field.field}:
                    </span>
                    <span className="text-blue-700 dark:text-blue-300 ml-2">
                      {field.description}
                    </span>
                    <div className="text-xs text-blue-600 dark:text-blue-400 mt-1 ml-8">
                      Example: {field.example}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Examples */}
          <div className="mt-6">
            <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-3">
              Example Searches
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {operators.examples.map((example: any, index: number) => (
                <div key={index} className="text-sm">
                  <code className="block bg-blue-100 dark:bg-blue-800 p-2 rounded mb-1">
                    {example.query}
                  </code>
                  <p className="text-blue-700 dark:text-blue-300 text-xs">
                    {example.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Tips */}
          <div className="mt-6">
            <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
              Tips
            </h4>
            <ul className="list-disc list-inside text-sm text-blue-700 dark:text-blue-300 space-y-1">
              {operators.tips.map((tip: string, index: number) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  const renderResults = () => (
    <div className="mt-6 space-y-4">
      {results.map((result) => (
        <motion.div
          key={result.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
                {result.title}
              </h3>
              
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {result.snippet}
              </p>

              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span className="flex items-center">
                  <UserIcon className="h-3 w-3 mr-1" />
                  {result.speakers.join(', ')}
                </span>
                <span className="flex items-center">
                  <CalendarIcon className="h-3 w-3 mr-1" />
                  {new Date(result.created_at).toLocaleDateString()}
                </span>
                <span className="flex items-center">
                  <ClockIcon className="h-3 w-3 mr-1" />
                  {Math.floor(result.duration / 60)}min
                </span>
                <span className="flex items-center">
                  <LanguageIcon className="h-3 w-3 mr-1" />
                  {result.language.toUpperCase()}
                </span>
              </div>

              <div className="mt-3 flex flex-wrap gap-1">
                {result.topics.map((topic, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-200 rounded"
                  >
                    {topic}
                  </span>
                ))}
                {result.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="text-right ml-4">
              <div className="text-2xl font-bold text-indigo-600">
                {(result.relevance_score * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-500">relevance</div>
              <div className="mt-2 text-xs text-gray-500">
                {result.view_count} views
              </div>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              <span>Matched in:</span>
              {result.matched_fields.map((field, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded"
                >
                  {field}
                </span>
              ))}
            </div>

            <button className="btn-primary text-xs py-1 px-3">
              View Transcript
            </button>
          </div>
        </motion.div>
      ))}
    </div>
  );

  const renderSidebar = () => (
    <div className="w-80 space-y-6">
      {/* Search History */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
          Recent Searches
        </h3>
        <div className="space-y-2">
          {searchHistory.slice(0, 5).map((item) => (
            <button
              key={item.id}
              onClick={() => setQuery(item.query)}
              className="w-full text-left p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded"
            >
              <div className="text-sm text-gray-900 dark:text-white">
                {item.query}
              </div>
              <div className="text-xs text-gray-500">
                {item.result_count} results • {new Date(item.timestamp).toLocaleDateString()}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Saved Searches */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
          Saved Searches
        </h3>
        <div className="space-y-2">
          {savedSearches.map((saved) => (
            <button
              key={saved.id}
              onClick={() => loadSavedSearch(saved)}
              className="w-full text-left p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-900 dark:text-white">
                  {saved.name}
                </span>
                {saved.notification_enabled && (
                  <BookmarkSolidIcon className="h-4 w-4 text-indigo-600" />
                )}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {saved.query.substring(0, 50)}...
              </div>
              {saved.new_results > 0 && (
                <div className="mt-1">
                  <span className="px-2 py-1 text-xs bg-indigo-100 text-indigo-800 rounded">
                    {saved.new_results} new
                  </span>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Popular Entities */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
          Popular Entities
        </h3>
        <div className="flex flex-wrap gap-2">
          {['Google', 'OpenAI', 'Python', 'TensorFlow', 'MIT', 'Stanford'].map((entity) => (
            <button
              key={entity}
              onClick={() => setQuery(`entity:${entity}`)}
              className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-full"
            >
              {entity}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex space-x-6"
    >
      <div className="flex-1">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
            Advanced Search
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Use operators and filters to find exactly what you're looking for
          </p>
        </div>

        {renderSearchBar()}
        {renderFilters()}
        {renderHelp()}

        {/* Results Summary */}
        {results.length > 0 && !loading && (
          <div className="mt-6 flex items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Found {results.length} results for "{query}"
            </p>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Sort by:</span>
              <select className="text-sm border border-gray-300 rounded px-2 py-1">
                <option>Relevance</option>
                <option>Date (Newest)</option>
                <option>Date (Oldest)</option>
                <option>Duration</option>
                <option>Views</option>
              </select>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-gray-500">Searching...</p>
            </div>
          </div>
        )}

        {/* No Results */}
        {!loading && query && results.length === 0 && (
          <div className="mt-8 text-center">
            <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No results found for "{query}"</p>
            <p className="text-sm text-gray-400 mt-2">
              Try using different keywords or adjusting your filters
            </p>
          </div>
        )}

        {/* Results */}
        {!loading && results.length > 0 && renderResults()}
      </div>

      {/* Sidebar */}
      {renderSidebar()}
    </motion.div>
  );
};

export default AdvancedSearch;