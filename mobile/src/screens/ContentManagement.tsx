/**
 * Content Management Screen - React Native
 * Task 203: Advanced Content Management and Organization System
 * Mobile app screen for managing transcribed content
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  TextInput,
  FlatList,
  Modal,
  SafeAreaView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import DocumentPicker from 'react-native-document-picker';

interface ContentItem {
  id: string;
  title: string;
  description?: string;
  contentType: string;
  status: string;
  quality: string;
  duration?: number;
  tags: Array<{ id: string; name: string; color: string }>;
  createdAt: string;
  accessLevel: string;
}

interface Collection {
  id: string;
  name: string;
  description?: string;
  itemsCount: number;
  accessLevel: string;
}

interface Tag {
  id: string;
  name: string;
  color: string;
  usageCount: number;
}

const ContentManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'all' | 'collections' | 'tags'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [contentItems, setContentItems] = useState<ContentItem[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  // Mock data
  const mockContent: ContentItem[] = [
    {
      id: '1',
      title: 'Team Meeting - Product Roadmap',
      description: 'Q4 product planning discussion',
      contentType: 'meeting',
      status: 'ready',
      quality: 'good',
      duration: 2730,
      tags: [
        { id: 't1', name: 'meeting', color: '#3b82f6' },
        { id: 't2', name: 'product', color: '#10b981' },
      ],
      createdAt: '2025-08-07T14:30:00Z',
      accessLevel: 'team',
    },
    {
      id: '2',
      title: 'Customer Interview - User Research',
      description: 'User feedback on new features',
      contentType: 'interview',
      status: 'ready',
      quality: 'excellent',
      duration: 1935,
      tags: [
        { id: 't3', name: 'interview', color: '#f59e0b' },
        { id: 't4', name: 'research', color: '#8b5cf6' },
      ],
      createdAt: '2025-08-07T11:20:00Z',
      accessLevel: 'private',
    },
  ];

  const mockCollections: Collection[] = [
    {
      id: 'col1',
      name: 'Customer Interviews',
      description: 'All customer research interviews',
      itemsCount: 23,
      accessLevel: 'team',
    },
    {
      id: 'col2',
      name: 'Product Planning',
      description: 'Product roadmap discussions',
      itemsCount: 16,
      accessLevel: 'private',
    },
  ];

  const mockTags: Tag[] = [
    { id: 't1', name: 'meeting', color: '#3b82f6', usageCount: 45 },
    { id: 't2', name: 'product', color: '#10b981', usageCount: 32 },
    { id: 't3', name: 'interview', color: '#f59e0b', usageCount: 28 },
    { id: 't4', name: 'research', color: '#8b5cf6', usageCount: 24 },
  ];

  useEffect(() => {
    setContentItems(mockContent);
    setCollections(mockCollections);
    setTags(mockTags);
  }, []);

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    setTimeout(() => {
      setRefreshing(false);
    }, 2000);
  }, []);

  const handleSearch = (text: string) => {
    setSearchQuery(text);
    // Implement search logic
  };

  const handleTagSelect = (tagId: string) => {
    setSelectedTags((prev) =>
      prev.includes(tagId) ? prev.filter((t) => t !== tagId) : [...prev, tagId]
    );
  };

  const handleUpload = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.audio, DocumentPicker.types.video],
      });
      // Handle file upload
      Alert.alert('Success', 'File uploaded successfully');
      setShowUploadModal(false);
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        Alert.alert('Error', 'Failed to upload file');
      }
    }
  };

  const handleDelete = (item: ContentItem) => {
    Alert.alert(
      'Delete Content',
      `Are you sure you want to delete "${item.title}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            setContentItems((prev) => prev.filter((i) => i.id !== item.id));
          },
        },
      ]
    );
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getQualityColor = (quality: string): string => {
    switch (quality) {
      case 'excellent':
        return '#10b981';
      case 'good':
        return '#3b82f6';
      case 'fair':
        return '#f59e0b';
      case 'poor':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const renderContentItem = ({ item }: { item: ContentItem }) => (
    <TouchableOpacity
      style={styles.contentCard}
      onPress={() => setSelectedContent(item)}
    >
      <View style={styles.contentHeader}>
        <Icon
          name={
            item.contentType === 'meeting'
              ? 'groups'
              : item.contentType === 'interview'
              ? 'person'
              : 'description'
          }
          size={24}
          color="#6b7280"
        />
        <View style={styles.contentInfo}>
          <Text style={styles.contentTitle} numberOfLines={1}>
            {item.title}
          </Text>
          <Text style={styles.contentDescription} numberOfLines={2}>
            {item.description}
          </Text>
        </View>
      </View>

      <View style={styles.contentTags}>
        {item.tags.slice(0, 3).map((tag) => (
          <View
            key={tag.id}
            style={[styles.tag, { backgroundColor: `${tag.color}20` }]}
          >
            <Text style={[styles.tagText, { color: tag.color }]}>{tag.name}</Text>
          </View>
        ))}
        {item.tags.length > 3 && (
          <Text style={styles.moreTagsText}>+{item.tags.length - 3}</Text>
        )}
      </View>

      <View style={styles.contentFooter}>
        <View style={styles.contentMeta}>
          <Icon name="access-time" size={14} color="#6b7280" />
          <Text style={styles.metaText}>{formatDuration(item.duration)}</Text>
        </View>
        <View
          style={[
            styles.qualityBadge,
            { backgroundColor: `${getQualityColor(item.quality)}20` },
          ]}
        >
          <Text style={[styles.qualityText, { color: getQualityColor(item.quality) }]}>
            {item.quality}
          </Text>
        </View>
        <TouchableOpacity
          style={styles.moreButton}
          onPress={() => {
            Alert.alert(
              'Actions',
              '',
              [
                { text: 'Share', onPress: () => {} },
                { text: 'Edit', onPress: () => {} },
                {
                  text: 'Delete',
                  style: 'destructive',
                  onPress: () => handleDelete(item),
                },
                { text: 'Cancel', style: 'cancel' },
              ],
              { cancelable: true }
            );
          }}
        >
          <Icon name="more-vert" size={20} color="#6b7280" />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  const renderCollection = ({ item }: { item: Collection }) => (
    <TouchableOpacity style={styles.collectionCard}>
      <Icon name="folder" size={32} color="#3b82f6" />
      <Text style={styles.collectionName}>{item.name}</Text>
      <Text style={styles.collectionDescription} numberOfLines={2}>
        {item.description}
      </Text>
      <View style={styles.collectionFooter}>
        <Text style={styles.collectionItems}>{item.itemsCount} items</Text>
        <View
          style={[
            styles.accessBadge,
            {
              backgroundColor:
                item.accessLevel === 'private' ? '#e5e7eb' : '#d1fae5',
            },
          ]}
        >
          <Text
            style={[
              styles.accessText,
              {
                color: item.accessLevel === 'private' ? '#6b7280' : '#10b981',
              },
            ]}
          >
            {item.accessLevel}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  const renderTag = ({ item }: { item: Tag }) => (
    <TouchableOpacity
      style={[
        styles.tagCard,
        selectedTags.includes(item.id) && styles.selectedTagCard,
      ]}
      onPress={() => handleTagSelect(item.id)}
    >
      <View style={[styles.tagIcon, { backgroundColor: `${item.color}20` }]}>
        <Icon name="label" size={16} color={item.color} />
      </View>
      <Text style={styles.tagName}>{item.name}</Text>
      <Text style={styles.tagCount}>{item.usageCount}</Text>
    </TouchableOpacity>
  );

  const renderUploadModal = () => (
    <Modal
      visible={showUploadModal}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setShowUploadModal(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Upload Content</Text>
            <TouchableOpacity onPress={() => setShowUploadModal(false)}>
              <Icon name="close" size={24} color="#6b7280" />
            </TouchableOpacity>
          </View>

          <TextInput
            style={styles.input}
            placeholder="Content Title"
            placeholderTextColor="#9ca3af"
          />

          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Description (optional)"
            placeholderTextColor="#9ca3af"
            multiline
            numberOfLines={3}
          />

          <TouchableOpacity style={styles.uploadButton} onPress={handleUpload}>
            <Icon name="cloud-upload" size={24} color="#fff" />
            <Text style={styles.uploadButtonText}>Choose File</Text>
          </TouchableOpacity>

          <View style={styles.modalActions}>
            <TouchableOpacity
              style={[styles.modalButton, styles.cancelButton]}
              onPress={() => setShowUploadModal(false)}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.modalButton, styles.submitButton]}>
              <Text style={styles.submitButtonText}>Upload</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Content Management</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setShowFilterModal(true)}
          >
            <Icon name="filter-list" size={24} color="#6b7280" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setShowUploadModal(true)}
          >
            <Icon name="add" size={24} color="#3b82f6" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Icon name="search" size={20} color="#9ca3af" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search content..."
          placeholderTextColor="#9ca3af"
          value={searchQuery}
          onChangeText={handleSearch}
        />
      </View>

      {/* Tabs */}
      <View style={styles.tabContainer}>
        {(['all', 'collections', 'tags'] as const).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab === 'all'
                ? 'All Content'
                : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
            {tab === 'all' && (
              <View style={styles.tabBadge}>
                <Text style={styles.tabBadgeText}>{contentItems.length}</Text>
              </View>
            )}
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
        </View>
      ) : (
        <>
          {activeTab === 'all' && (
            <FlatList
              data={contentItems}
              renderItem={renderContentItem}
              keyExtractor={(item) => item.id}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
              contentContainerStyle={styles.listContainer}
            />
          )}

          {activeTab === 'collections' && (
            <FlatList
              data={collections}
              renderItem={renderCollection}
              keyExtractor={(item) => item.id}
              numColumns={2}
              columnWrapperStyle={styles.collectionRow}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
              contentContainerStyle={styles.listContainer}
            />
          )}

          {activeTab === 'tags' && (
            <FlatList
              data={tags}
              renderItem={renderTag}
              keyExtractor={(item) => item.id}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
              contentContainerStyle={styles.listContainer}
            />
          )}
        </>
      )}

      {/* Upload Modal */}
      {renderUploadModal()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerButton: {
    marginLeft: 15,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  searchIcon: {
    marginRight: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#111827',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    marginRight: 25,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#3b82f6',
  },
  tabText: {
    fontSize: 14,
    color: '#6b7280',
  },
  activeTabText: {
    color: '#3b82f6',
    fontWeight: '600',
  },
  tabBadge: {
    marginLeft: 6,
    backgroundColor: '#e5e7eb',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  tabBadgeText: {
    fontSize: 12,
    color: '#6b7280',
    fontWeight: '600',
  },
  listContainer: {
    padding: 20,
  },
  contentCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.05,
    shadowRadius: 3.84,
    elevation: 5,
  },
  contentHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  contentInfo: {
    flex: 1,
    marginLeft: 10,
  },
  contentTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  contentDescription: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
  },
  contentTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 10,
  },
  tag: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 6,
    marginBottom: 6,
  },
  tagText: {
    fontSize: 12,
    fontWeight: '500',
  },
  moreTagsText: {
    fontSize: 12,
    color: '#6b7280',
    alignSelf: 'center',
  },
  contentFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  contentMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metaText: {
    fontSize: 12,
    color: '#6b7280',
    marginLeft: 4,
  },
  qualityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  qualityText: {
    fontSize: 12,
    fontWeight: '600',
  },
  moreButton: {
    padding: 4,
  },
  collectionCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    margin: 5,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.05,
    shadowRadius: 3.84,
    elevation: 5,
  },
  collectionRow: {
    justifyContent: 'space-between',
  },
  collectionName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginTop: 8,
    marginBottom: 4,
    textAlign: 'center',
  },
  collectionDescription: {
    fontSize: 12,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 8,
  },
  collectionFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
  },
  collectionItems: {
    fontSize: 12,
    color: '#6b7280',
  },
  accessBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  accessText: {
    fontSize: 10,
    fontWeight: '600',
  },
  tagCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  selectedTagCard: {
    borderWidth: 2,
    borderColor: '#3b82f6',
  },
  tagIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  tagName: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  tagCount: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 20,
    width: '90%',
    maxWidth: 400,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
  },
  input: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: '#111827',
    marginBottom: 15,
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  uploadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3b82f6',
    borderRadius: 8,
    paddingVertical: 12,
    marginBottom: 20,
  },
  uploadButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#e5e7eb',
    marginRight: 10,
  },
  submitButton: {
    backgroundColor: '#3b82f6',
    marginLeft: 10,
  },
  cancelButtonText: {
    color: '#6b7280',
    fontSize: 16,
    fontWeight: '600',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default ContentManagement;