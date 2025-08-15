import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Modal,
  FlatList,
  Dimensions,
  Switch
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import Icon from 'react-native-vector-icons/MaterialIcons';

const { width } = Dimensions.get('window');

// Types
interface Entity {
  text: string;
  entity_type: string;
  confidence: number;
  provider: string;
  canonical_id: string;
  aliases: string[];
  properties: Record<string, any>;
  knowledge_links: any[];
}

interface UnifiedEntity {
  canonical_id: string;
  canonical_name: string;
  entity_type: string;
  aliases: string[];
  providers: string[];
  confidence_scores: Record<string, number>;
  overall_confidence: number;
  knowledge_links: any[];
  source_entities: number;
}

interface ExtractionResult {
  success: boolean;
  text: string;
  context?: string;
  total_entities: number;
  entity_links: number;
  knowledge_links: number;
  extraction_results: Record<string, any>;
  unified_entities: UnifiedEntity[];
  processing_time_ms: number;
  timestamp: string;
}

interface SearchResult {
  entity: Entity;
  links: any[];
}

interface SystemStats {
  success: boolean;
  total_entities: number;
  total_links: number;
  entities_by_provider: Record<string, number>;
  entities_by_type: Record<string, number>;
  knowledge_graph_nodes: number;
  knowledge_graph_edges: number;
  active_extractors: string[];
  active_knowledge_linkers: string[];
}

const CrossProviderEntityLinkingMobile: React.FC = () => {
  // State
  const [activeTab, setActiveTab] = useState(0);
  const [text, setText] = useState('');
  const [context, setContext] = useState('');
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [includeKnowledgeLinks, setIncludeKnowledgeLinks] = useState(true);
  const [extractionResult, setExtractionResult] = useState<ExtractionResult | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchEntityType, setSearchEntityType] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [availableProviders, setAvailableProviders] = useState<any[]>([]);
  const [entityTypes, setEntityTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<UnifiedEntity | null>(null);
  const [entityDetailsModal, setEntityDetailsModal] = useState(false);
  const [providerSelectionModal, setProviderSelectionModal] = useState(false);

  // Sample texts for demo
  const sampleTexts = [
    {
      title: "Technology News",
      text: "Apple Inc. announced that Tim Cook will present the new iPhone at their Cupertino headquarters. The event will be streamed live on September 15th, 2024.",
      context: "technology news article"
    },
    {
      title: "Business Report",
      text: "Microsoft Corporation reported quarterly earnings of $2.1 billion. CEO Satya Nadella praised the Azure cloud platform's 50% growth in Seattle.",
      context: "business financial report"
    },
    {
      title: "Medical Research",
      text: "Dr. Sarah Johnson from Johns Hopkins University published research on COVID-19 treatments. The study was funded by the National Institutes of Health.",
      context: "medical research publication"
    }
  ];

  // Load initial data
  useEffect(() => {
    loadProviders();
    loadEntityTypes();
    loadSystemStats();
  }, []);

  const loadProviders = async () => {
    try {
      const response = await fetch('/api/v1/entity-linking/providers');
      const data = await response.json();
      if (data.success) {
        setAvailableProviders([...data.entity_extractors, ...data.knowledge_linkers]);
      }
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const loadEntityTypes = async () => {
    try {
      const response = await fetch('/api/v1/entity-linking/entity-types');
      const data = await response.json();
      if (data.success) {
        setEntityTypes(data.entity_types);
      }
    } catch (error) {
      console.error('Failed to load entity types:', error);
    }
  };

  const loadSystemStats = async () => {
    try {
      const response = await fetch('/api/v1/entity-linking/stats');
      const data = await response.json();
      if (data.success) {
        setSystemStats(data);
      }
    } catch (error) {
      console.error('Failed to load system stats:', error);
    }
  };

  const handleExtractEntities = async () => {
    if (!text.trim()) {
      Alert.alert('Error', 'Please enter text to analyze');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/entity-linking/extract', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          context: context || undefined,
          providers: selectedProviders.length > 0 ? selectedProviders : undefined,
          include_knowledge_links: includeKnowledgeLinks
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setExtractionResult(data);
        Alert.alert('Success', `Found ${data.total_entities} entities with ${data.entity_links} links`);
      } else {
        setError('Entity extraction failed');
        Alert.alert('Error', 'Entity extraction failed');
      }
    } catch (error) {
      const errorMessage = `Error: ${error.message}`;
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchEntities = async () => {
    if (!searchQuery.trim()) {
      Alert.alert('Error', 'Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/entity-linking/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          entity_type: searchEntityType || undefined,
          limit: 20,
          include_links: true
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setSearchResults(data.results);
        Alert.alert('Success', `Found ${data.results.length} entities`);
      } else {
        setError('Entity search failed');
        Alert.alert('Error', 'Entity search failed');
      }
    } catch (error) {
      const errorMessage = `Error: ${error.message}`;
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getEntityIcon = (entityType: string) => {
    const icons = {
      PERSON: 'person',
      ORG: 'business',
      GPE: 'place',
      PRODUCT: 'shopping-cart',
      EVENT: 'event',
      DATE: 'date-range',
      MONEY: 'attach-money',
      PERCENT: 'percent',
      CONCEPT: 'psychology',
      UNKNOWN: 'help'
    };
    return icons[entityType] || 'help';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return '#4caf50';
    if (confidence > 0.5) return '#ff9800';
    return '#f44336';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence > 0.8) return 'High';
    if (confidence > 0.5) return 'Medium';
    if (confidence > 0.2) return 'Low';
    return 'Very Low';
  };

  const loadSampleText = (sample: any) => {
    setText(sample.text);
    setContext(sample.context);
  };

  const toggleProvider = (providerName: string) => {
    setSelectedProviders(prev => 
      prev.includes(providerName)
        ? prev.filter(p => p !== providerName)
        : [...prev, providerName]
    );
  };

  const renderTabBar = () => (
    <View style={styles.tabBar}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 0 && styles.activeTab]}
        onPress={() => setActiveTab(0)}
      >
        <Text style={[styles.tabText, activeTab === 0 && styles.activeTabText]}>
          Extract
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 1 && styles.activeTab]}
        onPress={() => setActiveTab(1)}
      >
        <Text style={[styles.tabText, activeTab === 1 && styles.activeTabText]}>
          Search
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 2 && styles.activeTab]}
        onPress={() => setActiveTab(2)}
      >
        <Text style={[styles.tabText, activeTab === 2 && styles.activeTabText]}>
          Stats
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderEntityCard = (entity: UnifiedEntity, index: number) => (
    <TouchableOpacity
      key={index}
      style={styles.entityCard}
      onPress={() => {
        setSelectedEntity(entity);
        setEntityDetailsModal(true);
      }}
    >
      <View style={styles.entityHeader}>
        <Icon
          name={getEntityIcon(entity.entity_type)}
          size={24}
          color="#2196F3"
          style={styles.entityIcon}
        />
        <Text style={styles.entityName} numberOfLines={1}>
          {entity.canonical_name}
        </Text>
      </View>
      
      <Text style={styles.entityType}>{entity.entity_type}</Text>
      
      <View style={styles.confidenceContainer}>
        <Text style={styles.confidenceLabel}>
          {getConfidenceLabel(entity.overall_confidence)}
        </Text>
        <View style={styles.confidenceBar}>
          <View
            style={[
              styles.confidenceProgress,
              {
                width: `${entity.overall_confidence * 100}%`,
                backgroundColor: getConfidenceColor(entity.overall_confidence)
              }
            ]}
          />
        </View>
      </View>

      <Text style={styles.entityMeta}>
        Providers: {entity.providers.join(', ')}
      </Text>
      
      <Text style={styles.entityMeta}>
        Sources: {entity.source_entities} entities
      </Text>

      {entity.aliases.length > 0 && (
        <View style={styles.aliasContainer}>
          <Text style={styles.aliasLabel}>Aliases:</Text>
          <Text style={styles.aliasText} numberOfLines={2}>
            {entity.aliases.slice(0, 3).join(', ')}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );

  const renderSearchResultCard = (result: SearchResult, index: number) => (
    <TouchableOpacity key={index} style={styles.entityCard}>
      <View style={styles.entityHeader}>
        <Icon
          name={getEntityIcon(result.entity.entity_type)}
          size={24}
          color="#2196F3"
          style={styles.entityIcon}
        />
        <Text style={styles.entityName} numberOfLines={1}>
          {result.entity.text}
        </Text>
      </View>
      
      <Text style={styles.entityType}>
        {result.entity.entity_type} • {result.entity.provider}
      </Text>
      
      <View style={styles.confidenceContainer}>
        <Text style={styles.confidenceLabel}>
          {getConfidenceLabel(result.entity.confidence)}
        </Text>
        <View style={styles.confidenceBar}>
          <View
            style={[
              styles.confidenceProgress,
              {
                width: `${result.entity.confidence * 100}%`,
                backgroundColor: getConfidenceColor(result.entity.confidence)
              }
            ]}
          />
        </View>
      </View>

      {result.entity.aliases.length > 0 && (
        <View style={styles.aliasContainer}>
          <Text style={styles.aliasLabel}>Aliases:</Text>
          <Text style={styles.aliasText} numberOfLines={1}>
            {result.entity.aliases.slice(0, 2).join(', ')}
          </Text>
        </View>
      )}

      {result.links.length > 0 && (
        <Text style={styles.entityMeta}>
          {result.links.length} connections
        </Text>
      )}
    </TouchableOpacity>
  );

  const renderExtractionTab = () => (
    <ScrollView style={styles.tabContent}>
      {/* Text Input */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Text Analysis</Text>
        
        <TextInput
          style={styles.textArea}
          multiline
          numberOfLines={6}
          placeholder="Enter text to extract entities from..."
          value={text}
          onChangeText={setText}
        />
        
        <TextInput
          style={styles.textInput}
          placeholder="Context (optional)"
          value={context}
          onChangeText={setContext}
        />

        <View style={styles.settingsRow}>
          <TouchableOpacity
            style={styles.providerButton}
            onPress={() => setProviderSelectionModal(true)}
          >
            <Text style={styles.providerButtonText}>
              Providers ({selectedProviders.length})
            </Text>
            <Icon name="arrow-drop-down" size={24} color="#666" />
          </TouchableOpacity>

          <View style={styles.switchContainer}>
            <Text style={styles.switchLabel}>Knowledge Links</Text>
            <Switch
              value={includeKnowledgeLinks}
              onValueChange={setIncludeKnowledgeLinks}
            />
          </View>
        </View>

        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={handleExtractEntities}
          disabled={loading || !text.trim()}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Icon name="psychology" size={20} color="#fff" />
              <Text style={styles.buttonText}>Extract Entities</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* Sample Texts */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Sample Texts</Text>
        {sampleTexts.map((sample, index) => (
          <TouchableOpacity
            key={index}
            style={styles.sampleCard}
            onPress={() => loadSampleText(sample)}
          >
            <Text style={styles.sampleTitle}>{sample.title}</Text>
            <Text style={styles.sampleText} numberOfLines={2}>
              {sample.text}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Results */}
      {extractionResult && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Results</Text>
          
          {/* Summary */}
          <View style={styles.summaryContainer}>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryNumber}>{extractionResult.total_entities}</Text>
              <Text style={styles.summaryLabel}>Entities</Text>
            </View>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryNumber}>{extractionResult.entity_links}</Text>
              <Text style={styles.summaryLabel}>Links</Text>
            </View>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryNumber}>{extractionResult.knowledge_links}</Text>
              <Text style={styles.summaryLabel}>Knowledge</Text>
            </View>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryNumber}>{Math.round(extractionResult.processing_time_ms)}ms</Text>
              <Text style={styles.summaryLabel}>Time</Text>
            </View>
          </View>

          {/* Unified Entities */}
          <Text style={styles.subsectionTitle}>Unified Entities</Text>
          {extractionResult.unified_entities.map((entity, index) => 
            renderEntityCard(entity, index)
          )}
        </View>
      )}
    </ScrollView>
  );

  const renderSearchTab = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Entity Search</Text>
        
        <TextInput
          style={styles.textInput}
          placeholder="Search for entities..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          onSubmitEditing={handleSearchEntities}
        />

        <View style={styles.pickerContainer}>
          <Text style={styles.pickerLabel}>Entity Type:</Text>
          <Picker
            selectedValue={searchEntityType}
            onValueChange={setSearchEntityType}
            style={styles.picker}
          >
            <Picker.Item label="All Types" value="" />
            {entityTypes.map((type) => (
              <Picker.Item key={type.value} label={type.name} value={type.value} />
            ))}
          </Picker>
        </View>

        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={handleSearchEntities}
          disabled={loading || !searchQuery.trim()}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Icon name="search" size={20} color="#fff" />
              <Text style={styles.buttonText}>Search</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Search Results ({searchResults.length})
          </Text>
          {searchResults.map((result, index) => 
            renderSearchResultCard(result, index)
          )}
        </View>
      )}
    </ScrollView>
  );

  const renderStatsTab = () => (
    <ScrollView style={styles.tabContent}>
      {systemStats && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>System Statistics</Text>
          
          {/* Overview */}
          <View style={styles.statsCard}>
            <Text style={styles.statsCardTitle}>Overview</Text>
            <View style={styles.statsRow}>
              <Text style={styles.statsLabel}>Total Entities:</Text>
              <Text style={styles.statsValue}>{systemStats.total_entities.toLocaleString()}</Text>
            </View>
            <View style={styles.statsRow}>
              <Text style={styles.statsLabel}>Total Links:</Text>
              <Text style={styles.statsValue}>{systemStats.total_links.toLocaleString()}</Text>
            </View>
            <View style={styles.statsRow}>
              <Text style={styles.statsLabel}>Graph Nodes:</Text>
              <Text style={styles.statsValue}>{systemStats.knowledge_graph_nodes.toLocaleString()}</Text>
            </View>
            <View style={styles.statsRow}>
              <Text style={styles.statsLabel}>Graph Edges:</Text>
              <Text style={styles.statsValue}>{systemStats.knowledge_graph_edges.toLocaleString()}</Text>
            </View>
          </View>

          {/* Entities by Provider */}
          <View style={styles.statsCard}>
            <Text style={styles.statsCardTitle}>Entities by Provider</Text>
            {Object.entries(systemStats.entities_by_provider).map(([provider, count]) => (
              <View key={provider} style={styles.statsRow}>
                <Text style={styles.statsLabel}>{provider.toUpperCase()}:</Text>
                <Text style={styles.statsValue}>{count.toLocaleString()}</Text>
              </View>
            ))}
          </View>

          {/* Entities by Type */}
          <View style={styles.statsCard}>
            <Text style={styles.statsCardTitle}>Entities by Type</Text>
            {Object.entries(systemStats.entities_by_type).map(([type, count]) => (
              <View key={type} style={styles.statsRow}>
                <Icon
                  name={getEntityIcon(type)}
                  size={16}
                  color="#666"
                  style={styles.statsIcon}
                />
                <Text style={styles.statsLabel}>{type}:</Text>
                <Text style={styles.statsValue}>{count.toLocaleString()}</Text>
              </View>
            ))}
          </View>

          {/* Active Providers */}
          <View style={styles.statsCard}>
            <Text style={styles.statsCardTitle}>Active Providers</Text>
            <Text style={styles.statsSubtitle}>Entity Extractors:</Text>
            <View style={styles.chipContainer}>
              {systemStats.active_extractors.map((extractor, index) => (
                <View key={index} style={[styles.chip, styles.primaryChip]}>
                  <Text style={styles.chipText}>{extractor}</Text>
                </View>
              ))}
            </View>
            <Text style={styles.statsSubtitle}>Knowledge Linkers:</Text>
            <View style={styles.chipContainer}>
              {systemStats.active_knowledge_linkers.map((linker, index) => (
                <View key={index} style={[styles.chip, styles.secondaryChip]}>
                  <Text style={styles.chipText}>{linker}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>
      )}
    </ScrollView>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Entity Linking</Text>
        <Text style={styles.subtitle}>
          Extract and link entities across providers
        </Text>
      </View>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={() => setError(null)}>
            <Icon name="close" size={20} color="#f44336" />
          </TouchableOpacity>
        </View>
      )}

      {renderTabBar()}

      {activeTab === 0 && renderExtractionTab()}
      {activeTab === 1 && renderSearchTab()}
      {activeTab === 2 && renderStatsTab()}

      {/* Provider Selection Modal */}
      <Modal
        visible={providerSelectionModal}
        animationType="slide"
        transparent={true}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Providers</Text>
              <TouchableOpacity onPress={() => setProviderSelectionModal(false)}>
                <Icon name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.modalBody}>
              {availableProviders
                .filter(p => p.type !== 'knowledge_base')
                .map((provider) => (
                <TouchableOpacity
                  key={provider.name}
                  style={styles.providerOption}
                  onPress={() => toggleProvider(provider.name)}
                >
                  <Text style={styles.providerName}>{provider.name.toUpperCase()}</Text>
                  <Icon
                    name={selectedProviders.includes(provider.name) ? 'check-box' : 'check-box-outline-blank'}
                    size={24}
                    color={selectedProviders.includes(provider.name) ? '#2196F3' : '#666'}
                  />
                </TouchableOpacity>
              ))}
            </ScrollView>
            
            <TouchableOpacity
              style={[styles.button, styles.primaryButton]}
              onPress={() => setProviderSelectionModal(false)}
            >
              <Text style={styles.buttonText}>Done</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Entity Details Modal */}
      <Modal
        visible={entityDetailsModal}
        animationType="slide"
        transparent={true}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Entity Details</Text>
              <TouchableOpacity onPress={() => setEntityDetailsModal(false)}>
                <Icon name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>
            
            {selectedEntity && (
              <ScrollView style={styles.modalBody}>
                <Text style={styles.entityDetailName}>{selectedEntity.canonical_name}</Text>
                <Text style={styles.entityDetailType}>Type: {selectedEntity.entity_type}</Text>
                <Text style={styles.entityDetailMeta}>
                  Overall Confidence: {(selectedEntity.overall_confidence * 100).toFixed(1)}%
                </Text>
                <Text style={styles.entityDetailMeta}>
                  Source Entities: {selectedEntity.source_entities}
                </Text>
                
                <Text style={styles.entityDetailSection}>Providers:</Text>
                <View style={styles.chipContainer}>
                  {selectedEntity.providers.map((provider, index) => (
                    <View key={index} style={[styles.chip, styles.primaryChip]}>
                      <Text style={styles.chipText}>{provider}</Text>
                    </View>
                  ))}
                </View>

                {selectedEntity.aliases.length > 0 && (
                  <>
                    <Text style={styles.entityDetailSection}>Aliases:</Text>
                    <View style={styles.chipContainer}>
                      {selectedEntity.aliases.map((alias, index) => (
                        <View key={index} style={[styles.chip, styles.outlineChip]}>
                          <Text style={styles.chipText}>{alias}</Text>
                        </View>
                      ))}
                    </View>
                  </>
                )}

                {selectedEntity.knowledge_links.length > 0 && (
                  <Text style={styles.entityDetailMeta}>
                    Knowledge Links: {selectedEntity.knowledge_links.length}
                  </Text>
                )}
              </ScrollView>
            )}
            
            <TouchableOpacity
              style={[styles.button, styles.primaryButton]}
              onPress={() => setEntityDetailsModal(false)}
            >
              <Text style={styles.buttonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    padding: 20,
    paddingTop: 40,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    padding: 12,
    margin: 16,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  errorText: {
    color: '#f44336',
    flex: 1,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#2196F3',
  },
  tabText: {
    fontSize: 16,
    color: '#666',
  },
  activeTabText: {
    color: '#2196F3',
    fontWeight: 'bold',
  },
  tabContent: {
    flex: 1,
  },
  section: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 8,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  subsectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
    marginBottom: 12,
  },
  textArea: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    textAlignVertical: 'top',
    marginBottom: 12,
    minHeight: 120,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
  },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  providerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    flex: 1,
    marginRight: 12,
  },
  providerButtonText: {
    flex: 1,
    fontSize: 16,
    color: '#333',
  },
  switchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  switchLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 8,
    marginBottom: 8,
  },
  primaryButton: {
    backgroundColor: '#2196F3',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  sampleCard: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  sampleTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  sampleText: {
    fontSize: 14,
    color: '#666',
  },
  summaryContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
    padding: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
  },
  summaryItem: {
    alignItems: 'center',
  },
  summaryNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  entityCard: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  entityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  entityIcon: {
    marginRight: 8,
  },
  entityName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  entityType: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  confidenceContainer: {
    marginBottom: 8,
  },
  confidenceLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  confidenceBar: {
    height: 6,
    backgroundColor: '#e0e0e0',
    borderRadius: 3,
    overflow: 'hidden',
  },
  confidenceProgress: {
    height: '100%',
    borderRadius: 3,
  },
  entityMeta: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  aliasContainer: {
    marginTop: 8,
  },
  aliasLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  aliasText: {
    fontSize: 12,
    color: '#333',
  },
  pickerContainer: {
    marginBottom: 12,
  },
  pickerLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  picker: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
  },
  statsCard: {
    backgroundColor: '#f8f9fa',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  statsCardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  statsIcon: {
    marginRight: 8,
  },
  statsLabel: {
    flex: 1,
    fontSize: 14,
    color: '#666',
  },
  statsValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  statsSubtitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 12,
    marginBottom: 8,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 8,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  primaryChip: {
    backgroundColor: '#2196F3',
  },
  secondaryChip: {
    backgroundColor: '#ff9800',
  },
  outlineChip: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  chipText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: 'bold',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    width: width * 0.9,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  modalBody: {
    maxHeight: 400,
  },
  providerOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  providerName: {
    fontSize: 16,
    color: '#333',
  },
  entityDetailName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  entityDetailType: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  entityDetailMeta: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  entityDetailSection: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
});

export default CrossProviderEntityLinkingMobile;