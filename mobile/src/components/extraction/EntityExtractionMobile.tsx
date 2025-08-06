import React, { useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  ActivityIndicator,
  Alert,
  Platform,
  Dimensions,
  Modal,
  FlatList,
  Share,
} from 'react-native';
import {
  launchImageLibrary,
  launchCamera,
  ImagePickerResponse,
} from 'react-native-image-picker';
import Slider from '@react-native-community/slider';
import { Picker } from '@react-native-picker/picker';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient } from '../../services/api';
import { theme } from '../../theme';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface Entity {
  id: string;
  type: string;
  label: string;
  confidence: number;
  bbox: number[];
  attributes: Record<string, any>;
}

interface Relationship {
  source: string;
  target: string;
  type: string;
  confidence: number;
}

interface ExtractionConfig {
  confidence_threshold: number;
  max_entities: number;
  entity_types: string[];
}

interface ExtractionResults {
  task_id: string;
  status: string;
  entities: Entity[];
  entity_count: number;
  relationships: Relationship[];
  visualization_url?: string;
  processing_time?: number;
  timestamp?: string;
}

const EntityExtractionMobile: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<any>(null);
  const [extracting, setExtracting] = useState(false);
  const [results, setResults] = useState<ExtractionResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'entities' | 'relationships'>('entities');
  const [filterType, setFilterType] = useState<string>('all');
  const [showSettings, setShowSettings] = useState(false);
  const [showImageModal, setShowImageModal] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [extractionConfig, setExtractionConfig] = useState<ExtractionConfig>({
    confidence_threshold: 0.5,
    max_entities: 100,
    entity_types: ['all'],
  });

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const pickImage = (source: 'camera' | 'gallery') => {
    const options = {
      mediaType: 'photo' as const,
      includeBase64: true,
      maxWidth: 2048,
      maxHeight: 2048,
      quality: 0.8,
    };

    const callback = (response: ImagePickerResponse) => {
      if (response.didCancel || response.errorMessage) {
        return;
      }

      if (response.assets && response.assets[0]) {
        const asset = response.assets[0];
        setSelectedImage(asset.uri || null);
        setImageFile({
          uri: asset.uri,
          type: asset.type,
          name: asset.fileName || 'image.jpg',
          base64: asset.base64,
        });
        setResults(null);
        setError(null);
      }
    };

    if (source === 'camera') {
      launchCamera(options, callback);
    } else {
      launchImageLibrary(options, callback);
    }
  };

  const extractEntities = async () => {
    if (!imageFile || !imageFile.base64) return;

    try {
      setExtracting(true);
      setError(null);

      const response = await apiClient.post('/api/v1/entity-extraction/extract', {
        image_data: imageFile.base64,
        extraction_config: extractionConfig,
        include_visualization: false, // Mobile doesn't need visualization
        output_format: 'json',
      });

      const taskId = response.data.task_id;
      pollForResults(taskId);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Extraction failed');
      setExtracting(false);
    }
  };

  const pollForResults = (taskId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await apiClient.get(`/api/v1/entity-extraction/status/${taskId}`);
        const data = response.data;

        if (data.status === 'completed' && data.result) {
          setResults(data.result);
          setExtracting(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        } else if (data.status === 'failed') {
          setError(data.message || 'Extraction failed');
          setExtracting(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        }
      } catch (err) {
        setError('Failed to get extraction status');
        setExtracting(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
      }
    }, 1000);
  };

  const resetExtraction = () => {
    setSelectedImage(null);
    setImageFile(null);
    setResults(null);
    setError(null);
    setExtracting(false);
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
  };

  const shareResults = async () => {
    if (!results) return;

    try {
      const message = `Entity Extraction Results:\n\n` +
        `Total Entities: ${results.entity_count}\n` +
        `Entity Types: ${[...new Set(results.entities.map(e => e.type))].join(', ')}\n` +
        `Processing Time: ${results.processing_time?.toFixed(2)}s`;

      await Share.share({
        message,
        title: 'Entity Extraction Results',
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to share results');
    }
  };

  const getEntityColor = (type: string): string => {
    const colors: Record<string, string> = {
      person: '#2196F3',
      object: '#4CAF50',
      text: '#FF9800',
      logo: '#9C27B0',
      location: '#F44336',
      default: '#757575',
    };
    return colors[type.toLowerCase()] || colors.default;
  };

  const filteredEntities = results?.entities.filter(entity => 
    filterType === 'all' || entity.type === filterType
  ) || [];

  const entityTypes = [...new Set(results?.entities.map(e => e.type) || [])];

  const renderEntity = ({ item }: { item: Entity }) => (
    <TouchableOpacity
      style={styles.entityItem}
      onPress={() => setSelectedEntity(item)}
    >
      <View style={styles.entityHeader}>
        <View
          style={[
            styles.entityTypeChip,
            { backgroundColor: getEntityColor(item.type) }
          ]}
        >
          <Text style={styles.entityTypeText}>{item.type}</Text>
        </View>
        <Text style={styles.entityLabel}>{item.label}</Text>
      </View>
      <Text style={styles.entityConfidence}>
        Confidence: {(item.confidence * 100).toFixed(1)}%
      </Text>
    </TouchableOpacity>
  );

  const renderRelationship = ({ item }: { item: Relationship }) => (
    <View style={styles.relationshipItem}>
      <View style={styles.relationshipFlow}>
        <Text style={styles.relationshipEntity}>{item.source}</Text>
        <Icon name="arrow-forward" size={16} color={theme.colors.primary} />
        <Text style={styles.relationshipType}>{item.type}</Text>
        <Icon name="arrow-forward" size={16} color={theme.colors.primary} />
        <Text style={styles.relationshipEntity}>{item.target}</Text>
      </View>
      <Text style={styles.relationshipConfidence}>
        Confidence: {(item.confidence * 100).toFixed(1)}%
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Entity Extraction</Text>
          <TouchableOpacity
            onPress={() => setShowSettings(true)}
            style={styles.settingsButton}
          >
            <Icon name="settings" size={24} color={theme.colors.text} />
          </TouchableOpacity>
        </View>

        {/* Image Selection */}
        {!selectedImage ? (
          <View style={styles.imageSelector}>
            <Icon name="image" size={64} color={theme.colors.textSecondary} />
            <Text style={styles.imageSelectorText}>
              Select an image to extract entities
            </Text>
            <View style={styles.imageButtonsRow}>
              <TouchableOpacity
                style={styles.imageButton}
                onPress={() => pickImage('camera')}
              >
                <Icon name="camera-alt" size={24} color={theme.colors.primary} />
                <Text style={styles.imageButtonText}>Camera</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.imageButton}
                onPress={() => pickImage('gallery')}
              >
                <Icon name="photo-library" size={24} color={theme.colors.primary} />
                <Text style={styles.imageButtonText}>Gallery</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <TouchableOpacity
            onPress={() => setShowImageModal(true)}
            style={styles.selectedImageContainer}
          >
            <Image source={{ uri: selectedImage }} style={styles.selectedImage} />
            <TouchableOpacity
              style={styles.removeImageButton}
              onPress={resetExtraction}
            >
              <Icon name="close" size={20} color="#fff" />
            </TouchableOpacity>
          </TouchableOpacity>
        )}

        {/* Action Buttons */}
        {selectedImage && !results && (
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={[styles.extractButton, extracting && styles.extractingButton]}
              onPress={extractEntities}
              disabled={extracting}
            >
              {extracting ? (
                <>
                  <ActivityIndicator color="#fff" size="small" />
                  <Text style={styles.extractButtonText}>Extracting...</Text>
                </>
              ) : (
                <>
                  <Icon name="label" size={20} color="#fff" />
                  <Text style={styles.extractButtonText}>Extract Entities</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        )}

        {/* Error Message */}
        {error && (
          <View style={styles.errorContainer}>
            <Icon name="error" size={20} color={theme.colors.error} />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Results */}
        {results && (
          <>
            {/* Stats */}
            <View style={styles.statsContainer}>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{results.entity_count}</Text>
                <Text style={styles.statLabel}>Entities</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{results.relationships?.length || 0}</Text>
                <Text style={styles.statLabel}>Relations</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{entityTypes.length}</Text>
                <Text style={styles.statLabel}>Types</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{results.processing_time?.toFixed(1)}s</Text>
                <Text style={styles.statLabel}>Time</Text>
              </View>
            </View>

            {/* Tabs */}
            <View style={styles.tabs}>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'entities' && styles.activeTab]}
                onPress={() => setSelectedTab('entities')}
              >
                <Text style={[styles.tabText, selectedTab === 'entities' && styles.activeTabText]}>
                  Entities
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'relationships' && styles.activeTab]}
                onPress={() => setSelectedTab('relationships')}
              >
                <Text style={[styles.tabText, selectedTab === 'relationships' && styles.activeTabText]}>
                  Relationships
                </Text>
              </TouchableOpacity>
            </View>

            {/* Filter */}
            {selectedTab === 'entities' && (
              <View style={styles.filterContainer}>
                <Picker
                  selectedValue={filterType}
                  onValueChange={setFilterType}
                  style={styles.filterPicker}
                >
                  <Picker.Item label="All Types" value="all" />
                  {entityTypes.map(type => (
                    <Picker.Item key={type} label={type} value={type} />
                  ))}
                </Picker>
              </View>
            )}

            {/* Results List */}
            <View style={styles.resultsList}>
              {selectedTab === 'entities' ? (
                <FlatList
                  data={filteredEntities}
                  renderItem={renderEntity}
                  keyExtractor={(item) => item.id}
                  scrollEnabled={false}
                  ItemSeparatorComponent={() => <View style={styles.separator} />}
                  ListEmptyComponent={
                    <Text style={styles.emptyText}>No entities found</Text>
                  }
                />
              ) : (
                <FlatList
                  data={results.relationships || []}
                  renderItem={renderRelationship}
                  keyExtractor={(_, index) => index.toString()}
                  scrollEnabled={false}
                  ItemSeparatorComponent={() => <View style={styles.separator} />}
                  ListEmptyComponent={
                    <Text style={styles.emptyText}>No relationships found</Text>
                  }
                />
              )}
            </View>

            {/* Action Buttons */}
            <View style={styles.resultActions}>
              <TouchableOpacity style={styles.actionButton} onPress={shareResults}>
                <Icon name="share" size={20} color={theme.colors.primary} />
                <Text style={styles.actionButtonText}>Share</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.actionButton} onPress={resetExtraction}>
                <Icon name="refresh" size={20} color={theme.colors.primary} />
                <Text style={styles.actionButtonText}>New Image</Text>
              </TouchableOpacity>
            </View>
          </>
        )}
      </ScrollView>

      {/* Settings Modal */}
      <Modal
        visible={showSettings}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowSettings(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Extraction Settings</Text>
              <TouchableOpacity onPress={() => setShowSettings(false)}>
                <Icon name="close" size={24} color={theme.colors.text} />
              </TouchableOpacity>
            </View>

            <View style={styles.settingItem}>
              <Text style={styles.settingLabel}>
                Confidence Threshold: {extractionConfig.confidence_threshold}
              </Text>
              <Slider
                style={styles.slider}
                minimumValue={0}
                maximumValue={1}
                step={0.1}
                value={extractionConfig.confidence_threshold}
                onValueChange={(value) =>
                  setExtractionConfig({ ...extractionConfig, confidence_threshold: value })
                }
                minimumTrackTintColor={theme.colors.primary}
                maximumTrackTintColor={theme.colors.border}
              />
            </View>

            <View style={styles.settingItem}>
              <Text style={styles.settingLabel}>Max Entities</Text>
              <View style={styles.maxEntitiesButtons}>
                {[50, 100, 200, 500].map((value) => (
                  <TouchableOpacity
                    key={value}
                    style={[
                      styles.maxEntitiesButton,
                      extractionConfig.max_entities === value && styles.maxEntitiesButtonActive,
                    ]}
                    onPress={() =>
                      setExtractionConfig({ ...extractionConfig, max_entities: value })
                    }
                  >
                    <Text
                      style={[
                        styles.maxEntitiesButtonText,
                        extractionConfig.max_entities === value && styles.maxEntitiesButtonTextActive,
                      ]}
                    >
                      {value}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <TouchableOpacity
              style={styles.saveSettingsButton}
              onPress={() => setShowSettings(false)}
            >
              <Text style={styles.saveSettingsButtonText}>Save Settings</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Image Preview Modal */}
      <Modal
        visible={showImageModal}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowImageModal(false)}
      >
        <TouchableOpacity
          style={styles.imageModalOverlay}
          activeOpacity={1}
          onPress={() => setShowImageModal(false)}
        >
          <Image
            source={{ uri: selectedImage! }}
            style={styles.fullScreenImage}
            resizeMode="contain"
          />
        </TouchableOpacity>
      </Modal>

      {/* Entity Details Modal */}
      <Modal
        visible={!!selectedEntity}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setSelectedEntity(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Entity Details</Text>
              <TouchableOpacity onPress={() => setSelectedEntity(null)}>
                <Icon name="close" size={24} color={theme.colors.text} />
              </TouchableOpacity>
            </View>

            {selectedEntity && (
              <View style={styles.entityDetails}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Type:</Text>
                  <View
                    style={[
                      styles.entityTypeChip,
                      { backgroundColor: getEntityColor(selectedEntity.type) }
                    ]}
                  >
                    <Text style={styles.entityTypeText}>{selectedEntity.type}</Text>
                  </View>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Label:</Text>
                  <Text style={styles.detailValue}>{selectedEntity.label}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Confidence:</Text>
                  <Text style={styles.detailValue}>
                    {(selectedEntity.confidence * 100).toFixed(1)}%
                  </Text>
                </View>
                {selectedEntity.bbox && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>Position:</Text>
                    <Text style={styles.detailValue}>
                      [{selectedEntity.bbox.map(v => v.toFixed(0)).join(', ')}]
                    </Text>
                  </View>
                )}
                {selectedEntity.attributes && Object.keys(selectedEntity.attributes).length > 0 && (
                  <View style={styles.attributesSection}>
                    <Text style={styles.detailLabel}>Attributes:</Text>
                    <View style={styles.attributesBox}>
                      <Text style={styles.attributesText}>
                        {JSON.stringify(selectedEntity.attributes, null, 2)}
                      </Text>
                    </View>
                  </View>
                )}
              </View>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  settingsButton: {
    padding: 8,
  },
  imageSelector: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
    margin: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: theme.colors.border,
    borderStyle: 'dashed',
  },
  imageSelectorText: {
    fontSize: 16,
    color: theme.colors.textSecondary,
    marginTop: 16,
    marginBottom: 24,
  },
  imageButtonsRow: {
    flexDirection: 'row',
    gap: 16,
  },
  imageButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: theme.colors.primary,
  },
  imageButtonText: {
    fontSize: 16,
    color: theme.colors.primary,
    fontWeight: '500',
  },
  selectedImageContainer: {
    margin: 16,
    borderRadius: 12,
    overflow: 'hidden',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  selectedImage: {
    width: '100%',
    height: 250,
    resizeMode: 'cover',
  },
  removeImageButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderRadius: 20,
    padding: 8,
  },
  actionButtons: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  extractButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: theme.colors.primary,
    paddingVertical: 16,
    borderRadius: 8,
  },
  extractingButton: {
    opacity: 0.7,
  },
  extractButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    margin: 16,
    padding: 12,
    backgroundColor: theme.colors.errorBackground,
    borderRadius: 8,
  },
  errorText: {
    flex: 1,
    color: theme.colors.error,
    fontSize: 14,
  },
  statsContainer: {
    flexDirection: 'row',
    margin: 16,
    gap: 8,
  },
  statBox: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  statLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  tabs: {
    flexDirection: 'row',
    marginHorizontal: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
    padding: 4,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 6,
  },
  activeTab: {
    backgroundColor: theme.colors.primary,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.textSecondary,
  },
  activeTabText: {
    color: '#fff',
  },
  filterContainer: {
    margin: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
    overflow: 'hidden',
  },
  filterPicker: {
    height: 50,
  },
  resultsList: {
    margin: 16,
  },
  entityItem: {
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
  },
  entityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  entityTypeChip: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  entityTypeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '500',
  },
  entityLabel: {
    flex: 1,
    fontSize: 16,
    fontWeight: '500',
    color: theme.colors.text,
  },
  entityConfidence: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  relationshipItem: {
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
  },
  relationshipFlow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
    flexWrap: 'wrap',
  },
  relationshipEntity: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.text,
  },
  relationshipType: {
    fontSize: 14,
    color: theme.colors.primary,
  },
  relationshipConfidence: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  separator: {
    height: 8,
  },
  emptyText: {
    textAlign: 'center',
    color: theme.colors.textSecondary,
    fontSize: 14,
    padding: 32,
  },
  resultActions: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    margin: 16,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: theme.colors.primary,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.primary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: theme.colors.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: screenHeight * 0.8,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  settingItem: {
    marginBottom: 24,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: theme.colors.text,
    marginBottom: 12,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  maxEntitiesButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  maxEntitiesButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  maxEntitiesButtonActive: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  maxEntitiesButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.text,
  },
  maxEntitiesButtonTextActive: {
    color: '#fff',
  },
  saveSettingsButton: {
    backgroundColor: theme.colors.primary,
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
  },
  saveSettingsButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  imageModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  fullScreenImage: {
    width: screenWidth,
    height: screenHeight,
  },
  entityDetails: {
    gap: 16,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  detailLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.textSecondary,
    minWidth: 80,
  },
  detailValue: {
    flex: 1,
    fontSize: 14,
    color: theme.colors.text,
  },
  attributesSection: {
    marginTop: 8,
  },
  attributesBox: {
    marginTop: 8,
    padding: 12,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
  },
  attributesText: {
    fontSize: 12,
    color: theme.colors.text,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
});

export default EntityExtractionMobile;