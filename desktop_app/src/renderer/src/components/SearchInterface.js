import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { exportToPDF, exportToTXT } from '../utils/exportUtils';
// Simple debounce implementation
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

const SearchInterface = ({ toast }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    dateRange: 'all',
    language: 'all',
    hasEntities: false,
    sortBy: 'relevance'
  });
  const [selectedResult, setSelectedResult] = useState(null);

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce(async (query, currentFilters) => {
      if (!query.trim()) {
        setSearchResults([]);
        return;
      }

      setLoading(true);
      try {
        const response = await api.search(query, currentFilters);
        setSearchResults(response.data.results || []);
        toast.success(`Found ${response.data.total_count} results`);
      } catch (error) {
        toast.error('Search failed: ' + error.message);
        setSearchResults([]);
      } finally {
        setLoading(false);
      }
    }, 500),
    [toast]
  );

  useEffect(() => {
    debouncedSearch(searchQuery, filters);
  }, [searchQuery, filters, debouncedSearch]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const highlightText = (text, query) => {
    if (!query) return text;
    
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) => 
      part.toLowerCase() === query.toLowerCase() ? 
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-800">{part}</mark> : 
        part
    );
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const handleQuickExport = (result, format) => {
    try {
      toast.info(`Exporting as ${format.toUpperCase()}...`);
      
      // Convert search result to transcription format for export
      const transcriptionData = {
        title: result.title || `Transcription ${result.transcript_id}`,
        text: result.full_text || result.snippet,
        created_at: result.created_at,
        duration: result.duration,
        word_count: result.word_count,
        language: result.language,
        entities: result.entities || [],
        summary: result.snippet
      };
      
      if (format === 'pdf') {
        exportToPDF(transcriptionData);
      } else if (format === 'txt') {
        exportToTXT(transcriptionData);
      }
      
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Export failed: ' + error.message);
    }
  };

  return (
    <div className="h-full flex">
      {/* Search Panel */}
      <div className="w-1/3 border-r border-gray-200 dark:border-gray-700 p-4 overflow-y-auto">
        {/* Search Input */}
        <div className="mb-4">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search transcriptions..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
            />
            <svg className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            {loading && (
              <div className="absolute right-3 top-3">
                <div className="spinner w-5 h-5"></div>
              </div>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="mb-4 space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Date Range
            </label>
            <select
              value={filters.dateRange}
              onChange={(e) => handleFilterChange('dateRange', e.target.value)}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="year">This Year</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Language
            </label>
            <select
              value={filters.language}
              onChange={(e) => handleFilterChange('language', e.target.value)}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="all">All Languages</option>
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Sort By
            </label>
            <select
              value={filters.sortBy}
              onChange={(e) => handleFilterChange('sortBy', e.target.value)}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="relevance">Relevance</option>
              <option value="date">Date</option>
              <option value="duration">Duration</option>
              <option value="word_count">Word Count</option>
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="hasEntities"
              checked={filters.hasEntities}
              onChange={(e) => handleFilterChange('hasEntities', e.target.checked)}
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
            <label htmlFor="hasEntities" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Has Named Entities
            </label>
          </div>
        </div>

        {/* Search Results */}
        <div className="space-y-2">
          {searchResults.map((result) => (
            <div
              key={result.transcript_id}
              onClick={() => setSelectedResult(result)}
              className={`p-3 rounded-lg cursor-pointer transition-colors ${
                selectedResult?.transcript_id === result.transcript_id
                  ? 'bg-primary-100 dark:bg-primary-900 border-primary-500'
                  : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'
              } border border-gray-200 dark:border-gray-700`}
            >
              <h4 className="font-medium text-sm text-gray-900 dark:text-white mb-1">
                {result.title || `Transcription ${result.transcript_id}`}
              </h4>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                {formatDate(result.created_at)} • {Math.round(result.duration / 60)} min • {result.word_count} words
              </p>
              <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
                {highlightText(result.snippet, searchQuery)}
              </p>
              {result.entities && result.entities.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {result.entities.slice(0, 3).map((entity, idx) => (
                    <span key={idx} className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                      {entity.text}
                    </span>
                  ))}
                  {result.entities.length > 3 && (
                    <span className="text-xs text-gray-500">+{result.entities.length - 3} more</span>
                  )}
                </div>
              )}
            </div>
          ))}
          
          {searchQuery && !loading && searchResults.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No results found for "{searchQuery}"
            </div>
          )}
        </div>
      </div>

      {/* Result Detail Panel */}
      <div className="flex-1 p-6 overflow-y-auto">
        {selectedResult ? (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                {selectedResult.title || `Transcription ${selectedResult.transcript_id}`}
              </h2>
              <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                <span>{formatDate(selectedResult.created_at)}</span>
                <span>•</span>
                <span>{Math.round(selectedResult.duration / 60)} minutes</span>
                <span>•</span>
                <span>{selectedResult.word_count} words</span>
                <span>•</span>
                <span>{selectedResult.language?.toUpperCase()}</span>
              </div>
            </div>

            {/* Full Transcript */}
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">Transcript</h3>
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {selectedResult.full_text ? 
                    highlightText(selectedResult.full_text, searchQuery) : 
                    selectedResult.snippet
                  }
                </p>
              </div>
            </div>

            {/* Entities */}
            {selectedResult.entities && selectedResult.entities.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">Named Entities</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedResult.entities.map((entity, idx) => (
                    <div key={idx} className="px-3 py-1.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-lg">
                      <span className="font-medium">{entity.text}</span>
                      <span className="text-xs ml-1 opacity-75">({entity.label})</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-3">
              <button className="px-4 py-2 bg-primary-600 text-white hover:bg-primary-700 rounded-lg">
                View Full Details
              </button>
              <div className="relative group">
                <button className="px-4 py-2 bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 rounded-lg">
                  Export
                </button>
                <div className="absolute left-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                  <button
                    onClick={() => handleQuickExport(selectedResult, 'pdf')}
                    className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    Export as PDF
                  </button>
                  <button
                    onClick={() => handleQuickExport(selectedResult, 'txt')}
                    className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    Export as Text
                  </button>
                </div>
              </div>
              <button className="px-4 py-2 bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 rounded-lg">
                Edit
              </button>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <p>Search for transcriptions to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchInterface;