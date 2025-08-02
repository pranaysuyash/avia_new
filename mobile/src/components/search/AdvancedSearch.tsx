import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  ActivityIndicator,
  Alert,
  Modal,
  FlatList,
  Switch,
  Dimensions,
  RefreshControl
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { SafeAreaView } from 'react-native-safe-area-context';
import DateTimePicker from '@react-native-community/datetimepicker';

const { width: screenWidth } = Dimensions.get('window');

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
    fuzzy: false
  });
  
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  const [showFilters, setShowFilters] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState<'start' | 'end' | null>(null);
  const [showSavedSearches, setShowSavedSearches] = useState(false);
  
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [searchHistory, setSearchHistory] = useState<Array<{
    query: string;
    timestamp: string;
    resultCount: number;
  }>>([]);

  const languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'ru', 'ja', 'ko', 'zh'];
  const entityTypes = ['PERSON', 'ORG', 'LOC', 'DATE', 'TIME', 'MONEY', 'PERCENT', 'PRODUCT'];

  const executeSearch = useCallback(async (searchQuery?: string, searchFilters?: SearchFilters, searchOptions?: SearchOptions) => {
    const finalQuery = searchQuery ?? query;
    const finalFilters = searchFilters ?? filters;
    const finalOptions = searchOptions ?? options;
    
    if (!finalQuery.trim()) {
      Alert.alert('Error', 'Please enter a search query');
      return;
    }

    setLoading(true);

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

    } catch (error) {
      Alert.alert('Error', 'Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [query, filters, options]);

  const handleQuickFilter = (filterType: string) => {
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

  const loadMoreResults = () => {
    if (!searchResults || searchResults.pageInfo.currentPage >= searchResults.pageInfo.totalPages) {
      return;
    }

    const newOptions = {
      ...options,
      offset: options.offset + options.limit
    };
    setOptions(newOptions);
    executeSearch(query, filters, newOptions);
  };

  const clearFilters = () => {
    setFilters({});
    setOptions({
      ...options,
      offset: 0
    });
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await executeSearch();
    setRefreshing(false);
  };

  const renderSearchInterface = () => (
    <View style={styles.searchContainer}>
      <View style={styles.searchInputContainer}>
        <Icon name="search" size={20} color="#666" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search transcripts..."
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={() => executeSearch()}
          returnKeyType="search"
        />
        {query.length > 0 && (
          <TouchableOpacity onPress={() => setQuery('')} style={styles.clearButton}>
            <Icon name="clear" size={20} color="#666" />
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.searchActions}>
        <TouchableOpacity
          style={[styles.searchButton, (!query.trim() || loading) && styles.disabledButton]}
          onPress={() => executeSearch()}
          disabled={!query.trim() || loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <>
              <Icon name="search" size={18} color="#fff" />
              <Text style={styles.searchButtonText}>Search</Text>
            </>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => setShowFilters(true)}
        >
          <Icon name="filter-list" size={18} color="#007AFF" />
          <Text style={styles.filterButtonText}>Filters</Text>
          {Object.keys(filters).length > 0 && (
            <View style={styles.filterBadge}>
              <Text style={styles.filterBadgeText}>{Object.keys(filters).length}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Quick Filters */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.quickFilters}>
        <TouchableOpacity
          style={styles.quickFilterChip}
          onPress={() => handleQuickFilter('today')}
        >
          <Icon name="today" size={16} color="#007AFF" />
          <Text style={styles.quickFilterText}>Today</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.quickFilterChip}
          onPress={() => handleQuickFilter('week')}
        >
          <Icon name="date-range" size={16} color="#007AFF" />
          <Text style={styles.quickFilterText}>This Week</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.quickFilterChip}
          onPress={() => handleQuickFilter('has_speakers')}
        >
          <Icon name="people" size={16} color="#007AFF" />
          <Text style={styles.quickFilterText}>With Speakers</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.quickFilterChip}
          onPress={() => handleQuickFilter('has_tags')}
        >
          <Icon name="local-offer" size={16} color="#007AFF" />
          <Text style={styles.quickFilterText}>Tagged</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.quickFilterChip}
          onPress={() => handleQuickFilter('has_entities')}
        >
          <Icon name="psychology" size={16} color="#007AFF" />
          <Text style={styles.quickFilterText}>With Entities</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );

  const renderSearchResults = () => {
    if (!searchResults) return null;

    return (
      <View style={styles.resultsContainer}>
        {/* Results Summary */}
        <View style={styles.resultsSummary}>
          <Text style={styles.resultsText}>
            {searchResults.totalCount > 0 
              ? `Found ${searchResults.totalCount} results in ${searchResults.searchTimeMs.toFixed(0)}ms`
              : 'No results found'
            }
          </Text>
          
          <TouchableOpacity
            style={styles.savedSearchButton}
            onPress={() => setShowSavedSearches(true)}
          >
            <Icon name="bookmark" size={18} color="#007AFF" />
          </TouchableOpacity>
        </View>

        {/* No Results - Show Suggestions */}
        {searchResults.totalCount === 0 && searchResults.suggestions.length > 0 && (
          <View style={styles.suggestionsContainer}>
            <Text style={styles.suggestionsTitle}>Try these searches:</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {searchResults.suggestions.map((suggestion, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.suggestionChip}
                  onPress={() => {
                    setQuery(suggestion);
                    executeSearch(suggestion, filters, options);
                  }}
                >
                  <Text style={styles.suggestionText}>{suggestion}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Facets */}
        {searchResults.facets && Object.keys(searchResults.facets).length > 0 && (
          <View style={styles.facetsContainer}>
            <Text style={styles.facetsTitle}>Filter by:</Text>
            {Object.entries(searchResults.facets).map(([facetType, facetValues]) => (
              <View key={facetType} style={styles.facetGroup}>
                <Text style={styles.facetGroupTitle}>
                  {facetType.replace('_', ' ').toUpperCase()}
                </Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  {Object.entries(facetValues).slice(0, 10).map(([value, count]) => (
                    <TouchableOpacity
                      key={value}
                      style={styles.facetChip}
                      onPress={() => handleFacetClick(facetType, value)}
                    >
                      <Text style={styles.facetChipText}>{value} ({count})</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            ))}
          </View>
        )}

        {/* Results List */}
        <FlatList
          data={searchResults.results}
          keyExtractor={(item) => item.doc_id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.resultItem}
              onPress={() => {
                // Navigate to transcript viewer
                // navigation.navigate('TranscriptViewer', { transcriptId: item.doc_id });
              }}
            >
              <Text style={styles.resultTitle}>{item.title}</Text>
              
              {item.title_snippet && item.title_snippet.includes('<mark>') && (
                <Text style={styles.titleMatch}>
                  Title match: {item.title_snippet.replace(/<\/?mark>/g, '')}
                </Text>
              )}
              
              {item.content_snippet && (
                <Text style={styles.resultSnippet}>
                  {item.content_snippet.replace(/<\/?mark>/g, '')}
                </Text>
              )}
              
              {/* Metadata */}
              <View style={styles.resultMetadata}>
                {item.created_at && (
                  <View style={styles.metadataChip}>
                    <Icon name="schedule" size={12} color="#666" />
                    <Text style={styles.metadataText}>
                      {new Date(item.created_at).toLocaleDateString()}
                    </Text>
                  </View>
                )}
                
                {item.language && (
                  <View style={styles.metadataChip}>
                    <Icon name="language" size={12} color="#666" />
                    <Text style={styles.metadataText}>{item.language.toUpperCase()}</Text>
                  </View>
                )}
                
                {item.confidence && (
                  <View style={styles.metadataChip}>
                    <Icon name="verified" size={12} color="#666" />
                    <Text style={styles.metadataText}>
                      {(item.confidence * 100).toFixed(0)}%
                    </Text>
                  </View>
                )}
                
                {item.speakers && item.speakers.length > 0 && (
                  <View style={styles.metadataChip}>
                    <Icon name="people" size={12} color="#666" />
                    <Text style={styles.metadataText}>
                      {item.speakers.length} speakers
                    </Text>
                  </View>
                )}
                
                {item.tags && item.tags.length > 0 && (
                  <View style={styles.metadataChip}>
                    <Icon name="local-offer" size={12} color="#666" />
                    <Text style={styles.metadataText}>
                      {item.tags.slice(0, 2).join(', ')}
                    </Text>
                  </View>
                )}
              </View>
              
              <View style={styles.resultActions}>
                <Icon name="chevron-right" size={20} color="#ccc" />
              </View>
            </TouchableOpacity>
          )}
          onEndReached={loadMoreResults}
          onEndReachedThreshold={0.1}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListFooterComponent={
            searchResults.pageInfo.currentPage < searchResults.pageInfo.totalPages ? (
              <View style={styles.loadingMore}>
                <ActivityIndicator color="#007AFF" />
                <Text style={styles.loadingMoreText}>Loading more results...</Text>
              </View>
            ) : null
          }
        />
      </View>
    );
  };

  const renderFiltersModal = () => (
    <Modal
      visible={showFilters}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <SafeAreaView style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={() => setShowFilters(false)}>
            <Icon name="close" size={24} color="#007AFF" />
          </TouchableOpacity>
          <Text style={styles.modalTitle}>Advanced Filters</Text>
          <TouchableOpacity onPress={clearFilters}>
            <Text style={styles.clearFiltersText}>Clear All</Text>
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.modalContent}>
          {/* Date Range */}
          <View style={styles.filterSection}>
            <Text style={styles.filterSectionTitle}>Date Range</Text>
            
            <TouchableOpacity
              style={styles.dateButton}
              onPress={() => setShowDatePicker('start')}
            >
              <Icon name="event" size={20} color="#007AFF" />
              <Text style={styles.dateButtonText}>
                Start: {filters.dateRange?.start?.toLocaleDateString() || 'Any'}
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.dateButton}
              onPress={() => setShowDatePicker('end')}
            >
              <Icon name="event" size={20} color="#007AFF" />
              <Text style={styles.dateButtonText}>
                End: {filters.dateRange?.end?.toLocaleDateString() || 'Any'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Language */}
          <View style={styles.filterSection}>
            <Text style={styles.filterSectionTitle}>Language</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={filters.language || ''}
                onValueChange={(value) => setFilters({ ...filters, language: value || undefined })}
              >
                <Picker.Item label="Any Language" value="" />
                {languages.map(lang => (
                  <Picker.Item key={lang} label={lang.toUpperCase()} value={lang} />
                ))}
              </Picker>
            </View>
          </View>

          {/* Confidence */}
          <View style={styles.filterSection}>
            <Text style={styles.filterSectionTitle}>
              Minimum Confidence: {((filters.minConfidence || 0) * 100).toFixed(0)}%
            </Text>
            <View style={styles.sliderContainer}>
              {/* Note: React Native doesn't have a built-in slider, you'd need to install @react-native-community/slider */}
              <Text style={styles.sliderNote}>
                Confidence filter: {((filters.minConfidence || 0) * 100).toFixed(0)}%
              </Text>
            </View>
          </View>

          {/* Entity Types */}
          <View style={styles.filterSection}>
            <Text style={styles.filterSectionTitle}>Entity Types</Text>
            <View style={styles.checkboxContainer}>
              {entityTypes.map(type => (
                <TouchableOpacity
                  key={type}
                  style={styles.checkboxItem}
                  onPress={() => {
                    const current = filters.entityTypes || [];
                    const updated = current.includes(type)
                      ? current.filter(t => t !== type)
                      : [...current, type];
                    setFilters({ ...filters, entityTypes: updated });
                  }}
                >
                  <Icon
                    name={filters.entityTypes?.includes(type) ? 'check-box' : 'check-box-outline-blank'}
                    size={20}
                    color="#007AFF"
                  />
                  <Text style={styles.checkboxLabel}>{type}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Search Options */}
          <View style={styles.filterSection}>
            <Text style={styles.filterSectionTitle}>Search Options</Text>
            
            <View style={styles.switchItem}>
              <Text style={styles.switchLabel}>Highlight matches</Text>
              <Switch
                value={options.highlight}
                onValueChange={(value) => setOptions({ ...options, highlight: value })}
              />
            </View>
            
            <View style={styles.switchItem}>
              <Text style={styles.switchLabel}>Fuzzy matching</Text>
              <Switch
                value={options.fuzzy}
                onValueChange={(value) => setOptions({ ...options, fuzzy: value })}
              />
            </View>

            <Text style={styles.filterSectionTitle}>Sort By</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={options.sortBy}
                onValueChange={(value) => setOptions({ ...options, sortBy: value as any })}
              >
                <Picker.Item label="Relevance" value="relevance" />
                <Picker.Item label="Date (newest)" value="date_desc" />
                <Picker.Item label="Date (oldest)" value="date_asc" />
                <Picker.Item label="Title" value="title" />
              </Picker>
            </View>
          </View>
        </ScrollView>

        <View style={styles.modalFooter}>
          <TouchableOpacity
            style={styles.applyFiltersButton}
            onPress={() => {
              setShowFilters(false);
              executeSearch();
            }}
          >
            <Text style={styles.applyFiltersText}>Apply Filters</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>

      {/* Date Picker */}
      {showDatePicker && (
        <DateTimePicker
          value={
            showDatePicker === 'start' 
              ? filters.dateRange?.start || new Date()
              : filters.dateRange?.end || new Date()
          }
          mode="date"
          display="default"
          onChange={(event, selectedDate) => {
            setShowDatePicker(null);
            if (selectedDate) {
              const newDateRange = { ...filters.dateRange };
              if (showDatePicker === 'start') {
                newDateRange.start = selectedDate;
              } else {
                newDateRange.end = selectedDate;
              }
              setFilters({ ...filters, dateRange: newDateRange });
            }
          }}
        />
      )}
    </Modal>
  );

  const renderSavedSearchesModal = () => (
    <Modal
      visible={showSavedSearches}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <SafeAreaView style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={() => setShowSavedSearches(false)}>
            <Icon name="close" size={24} color="#007AFF" />
          </TouchableOpacity>
          <Text style={styles.modalTitle}>Saved Searches</Text>
          <View style={{ width: 24 }} />
        </View>
        
        <ScrollView style={styles.modalContent}>
          {/* Saved Searches */}
          <View style={styles.savedSection}>
            <Text style={styles.savedSectionTitle}>Saved Searches</Text>
            {savedSearches.length > 0 ? (
              savedSearches.map((savedSearch) => (
                <TouchableOpacity
                  key={savedSearch.id}
                  style={styles.savedSearchItem}
                  onPress={() => {
                    setQuery(savedSearch.query);
                    setFilters(savedSearch.filters);
                    setShowSavedSearches(false);
                    executeSearch(savedSearch.query, savedSearch.filters, options);
                  }}
                >
                  <View style={styles.savedSearchContent}>
                    <Text style={styles.savedSearchName}>{savedSearch.name}</Text>
                    <Text style={styles.savedSearchQuery}>{savedSearch.query}</Text>
                    <Text style={styles.savedSearchMeta}>
                      Used {savedSearch.useCount} times
                    </Text>
                  </View>
                  <Icon name="chevron-right" size={20} color="#ccc" />
                </TouchableOpacity>
              ))
            ) : (
              <Text style={styles.emptyText}>No saved searches yet</Text>
            )}
          </View>

          {/* Search History */}
          <View style={styles.savedSection}>
            <Text style={styles.savedSectionTitle}>Recent Searches</Text>
            {searchHistory.length > 0 ? (
              searchHistory.map((historyItem, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.savedSearchItem}
                  onPress={() => {
                    setQuery(historyItem.query);
                    setShowSavedSearches(false);
                    executeSearch(historyItem.query, filters, options);
                  }}
                >
                  <View style={styles.savedSearchContent}>
                    <Text style={styles.savedSearchQuery}>
                      {historyItem.query.length > 50 
                        ? `${historyItem.query.substring(0, 50)}...` 
                        : historyItem.query
                      }
                    </Text>
                    <Text style={styles.savedSearchMeta}>
                      {historyItem.resultCount} results
                    </Text>
                  </View>
                  <Icon name="history" size={20} color="#ccc" />
                </TouchableOpacity>
              ))
            ) : (
              <Text style={styles.emptyText}>No recent searches</Text>
            )}
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Advanced Search</Text>
      </View>
      
      <ScrollView style={styles.content}>
        {renderSearchInterface()}
        {renderSearchResults()}
      </ScrollView>

      {renderFiltersModal()}
      {renderSavedSearchesModal()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  content: {
    flex: 1,
  },
  searchContainer: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
    borderRadius: 12,
    paddingHorizontal: 15,
    marginBottom: 15,
  },
  searchIcon: {
    marginRight: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 15,
    color: '#333',
  },
  clearButton: {
    padding: 5,
  },
  searchActions: {
    flexDirection: 'row',
    marginBottom: 15,
  },
  searchButton: {
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    flex: 1,
    marginRight: 10,
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 5,
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#007AFF',
    position: 'relative',
  },
  filterButtonText: {
    color: '#007AFF',
    fontSize: 16,
    marginLeft: 5,
  },
  filterBadge: {
    position: 'absolute',
    top: -5,
    right: -5,
    backgroundColor: '#FF3B30',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  filterBadgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  quickFilters: {
    flexDirection: 'row',
  },
  quickFilterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f0f8ff',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 10,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  quickFilterText: {
    color: '#007AFF',
    fontSize: 14,
    marginLeft: 5,
  },
  resultsContainer: {
    flex: 1,
  },
  resultsSummary: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  resultsText: {
    fontSize: 16,
    color: '#333',
  },
  savedSearchButton: {
    padding: 5,
  },
  suggestionsContainer: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  suggestionsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  suggestionChip: {
    backgroundColor: '#f0f8ff',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 10,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  suggestionText: {
    color: '#007AFF',
    fontSize: 14,
  },
  facetsContainer: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  facetsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  facetGroup: {
    marginBottom: 15,
  },
  facetGroupTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
  },
  facetChip: {
    backgroundColor: '#f8f8f8',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  facetChipText: {
    fontSize: 12,
    color: '#333',
  },
  resultItem: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 1,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  titleMatch: {
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
    marginBottom: 5,
  },
  resultSnippet: {
    fontSize: 16,
    color: '#333',
    lineHeight: 22,
    marginBottom: 10,
  },
  resultMetadata: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 10,
  },
  metadataChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
    marginBottom: 4,
  },
  metadataText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  resultActions: {
    alignItems: 'flex-end',
  },
  loadingMore: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
  },
  loadingMoreText: {
    marginLeft: 10,
    fontSize: 16,
    color: '#666',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  clearFiltersText: {
    fontSize: 16,
    color: '#FF3B30',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  filterSection: {
    marginBottom: 30,
  },
  filterSectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
  dateButtonText: {
    fontSize: 16,
    color: '#333',
    marginLeft: 10,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: '#f8f8f8',
  },
  sliderContainer: {
    paddingVertical: 10,
  },
  sliderNote: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  checkboxContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  checkboxItem: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '50%',
    paddingVertical: 8,
  },
  checkboxLabel: {
    fontSize: 16,
    color: '#333',
    marginLeft: 8,
  },
  switchItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  switchLabel: {
    fontSize: 16,
    color: '#333',
  },
  modalFooter: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  applyFiltersButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  applyFiltersText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  savedSection: {
    marginBottom: 30,
  },
  savedSectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  savedSearchItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
  savedSearchContent: {
    flex: 1,
  },
  savedSearchName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 2,
  },
  savedSearchQuery: {
    fontSize: 14,
    color: '#666',
    marginBottom: 2,
  },
  savedSearchMeta: {
    fontSize: 12,
    color: '#999',
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
});

export default AdvancedSearch;