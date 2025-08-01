import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Alert,
  Share,
  Dimensions,
  TextInput,
  Modal,
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';
import TranscriptionService from '../services/TranscriptionService';
import SyncService from '../services/SyncService';

const { width } = Dimensions.get('window');

export default function HistoryScreen({ navigation }) {
  const [transcriptions, setTranscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredTranscriptions, setFilteredTranscriptions] = useState([]);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [selectionMode, setSelectionMode] = useState(false);
  const [sortBy, setSortBy] = useState('date'); // 'date', 'name', 'duration'
  const [filterModalVisible, setFilterModalVisible] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);

  useEffect(() => {
    loadTranscriptions();
    loadSyncStatus();
  }, []);

  useEffect(() => {
    filterAndSortTranscriptions();
  }, [transcriptions, searchQuery, sortBy]);

  const loadTranscriptions = async () => {
    try {
      setLoading(true);
      const data = await TranscriptionService.getTranscriptionHistory(50, 0);
      setTranscriptions(data.transcriptions || []);
    } catch (error) {
      console.error('Failed to load transcriptions:', error);
      Alert.alert('Error', 'Failed to load transcription history');
    } finally {
      setLoading(false);
    }
  };

  const loadSyncStatus = async () => {
    try {
      const status = await SyncService.getSyncStatus();
      setSyncStatus(status);
    } catch (error) {
      console.warn('Failed to load sync status:', error);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadTranscriptions();
    await loadSyncStatus();
    setRefreshing(false);
  }, []);

  const filterAndSortTranscriptions = () => {
    let filtered = transcriptions;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = transcriptions.filter(item => 
        item.filename?.toLowerCase().includes(query) ||
        item.transcript?.toLowerCase().includes(query) ||
        item.created_at?.toLowerCase().includes(query)
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return (a.filename || '').localeCompare(b.filename || '');
        case 'duration':
          return (b.duration || 0) - (a.duration || 0);
        case 'date':
        default:
          return new Date(b.created_at) - new Date(a.created_at);
      }
    });

    setFilteredTranscriptions(filtered);
  };

  const handleItemPress = (item) => {
    if (selectionMode) {
      toggleSelection(item.id);
    } else {
      navigation.navigate('Transcription', { 
        transcriptionId: item.id,
        transcriptionData: item 
      });
    }
  };

  const handleItemLongPress = (item) => {
    if (!selectionMode) {
      setSelectionMode(true);
      setSelectedItems(new Set([item.id]));
    }
  };

  const toggleSelection = (id) => {
    const newSelection = new Set(selectedItems);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedItems(newSelection);

    if (newSelection.size === 0) {
      setSelectionMode(false);
    }
  };

  const selectAll = () => {
    if (selectedItems.size === filteredTranscriptions.length) {
      setSelectedItems(new Set());
      setSelectionMode(false);
    } else {
      setSelectedItems(new Set(filteredTranscriptions.map(item => item.id)));
    }
  };

  const deleteSelected = () => {
    Alert.alert(
      'Delete Transcriptions',
      `Delete ${selectedItems.size} selected transcription(s)?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: performDelete 
        }
      ]
    );
  };

  const performDelete = async () => {
    try {
      const deletePromises = Array.from(selectedItems).map(id =>
        TranscriptionService.deleteTranscription(id)
      );
      
      await Promise.all(deletePromises);
      
      setTranscriptions(prev => 
        prev.filter(item => !selectedItems.has(item.id))
      );
      
      setSelectedItems(new Set());
      setSelectionMode(false);
      
      Alert.alert('Success', `${selectedItems.size} transcription(s) deleted`);
    } catch (error) {
      console.error('Failed to delete transcriptions:', error);
      Alert.alert('Error', 'Failed to delete some transcriptions');
    }
  };

  const shareSelected = async () => {
    try {
      const selectedTranscriptions = filteredTranscriptions.filter(item => 
        selectedItems.has(item.id)
      );
      
      const shareText = selectedTranscriptions.map(item => 
        `${item.filename || 'Untitled'}\n${item.transcript || 'No transcript available'}\n---`
      ).join('\n\n');

      await Share.share({
        message: shareText,
        title: `${selectedItems.size} Transcription(s)`,
      });
    } catch (error) {
      console.error('Failed to share:', error);
      Alert.alert('Error', 'Failed to share transcriptions');
    }
  };

  const syncNow = async () => {
    try {
      const result = await SyncService.syncWithServer();
      if (result.success) {
        Alert.alert('Sync Complete', 'Transcriptions synced successfully');
        await loadTranscriptions();
        await loadSyncStatus();
      } else {
        Alert.alert('Sync Failed', result.error || 'Unknown error occurred');
      }
    } catch (error) {
      console.error('Sync failed:', error);
      Alert.alert('Sync Failed', 'Unable to sync with server');
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = now - date;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const renderTranscriptionItem = ({ item }) => {
    const isSelected = selectedItems.has(item.id);
    
    return (
      <TouchableOpacity
        style={[
          styles.transcriptionItem,
          isSelected && styles.selectedItem
        ]}
        onPress={() => handleItemPress(item)}
        onLongPress={() => handleItemLongPress(item)}
      >
        <View style={styles.itemHeader}>
          <View style={styles.itemInfo}>
            <Text style={styles.itemTitle} numberOfLines={1}>
              {item.filename || 'Untitled Recording'}
            </Text>
            <Text style={styles.itemDate}>{formatDate(item.created_at)}</Text>
          </View>
          <View style={styles.itemMeta}>
            <Text style={styles.itemDuration}>{formatDuration(item.duration)}</Text>
            {item.cached && (
              <MaterialIcons name="offline-pin" size={16} color="#4CAF50" />
            )}
            {selectionMode && (
              <MaterialIcons 
                name={isSelected ? "check-circle" : "radio-button-unchecked"} 
                size={24} 
                color={isSelected ? "#2196F3" : "#ccc"} 
              />
            )}
          </View>
        </View>
        
        {item.transcript && (
          <Text style={styles.itemPreview} numberOfLines={2}>
            {item.transcript}
          </Text>
        )}
        
        <View style={styles.itemFooter}>
          <View style={styles.itemTags}>
            {item.analysis_mode && (
              <Text style={styles.tag}>{item.analysis_mode}</Text>
            )}
            {item.speaker_count > 1 && (
              <Text style={styles.tag}>{item.speaker_count} speakers</Text>
            )}
          </View>
          <MaterialIcons name="chevron-right" size={20} color="#ccc" />
        </View>
      </TouchableOpacity>
    );
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.searchContainer}>
        <MaterialIcons name="search" size={20} color="#666" />
        <TextInput
          style={styles.searchInput}
          placeholder="Search transcriptions..."
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <MaterialIcons name="clear" size={20} color="#666" />
          </TouchableOpacity>
        )}
      </View>
      
      <View style={styles.headerActions}>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={() => setFilterModalVisible(true)}
        >
          <MaterialIcons name="sort" size={20} color="#666" />
        </TouchableOpacity>
        
        {syncStatus && (
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={syncNow}
          >
            <MaterialIcons 
              name={syncStatus.isOnline ? "cloud-done" : "cloud-off"} 
              size={20} 
              color={syncStatus.isOnline ? "#4CAF50" : "#ff9800"} 
            />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  const renderSelectionHeader = () => (
    <View style={styles.selectionHeader}>
      <TouchableOpacity 
        style={styles.selectionButton}
        onPress={() => {
          setSelectionMode(false);
          setSelectedItems(new Set());
        }}
      >
        <MaterialIcons name="close" size={24} color="#333" />
      </TouchableOpacity>
      
      <Text style={styles.selectionCount}>
        {selectedItems.size} selected
      </Text>
      
      <View style={styles.selectionActions}>
        <TouchableOpacity 
          style={styles.selectionButton}
          onPress={selectAll}
        >
          <MaterialIcons name="select-all" size={24} color="#333" />
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.selectionButton}
          onPress={shareSelected}
        >
          <MaterialIcons name="share" size={24} color="#333" />
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.selectionButton}
          onPress={deleteSelected}
        >
          <MaterialIcons name="delete" size={24} color="#f44336" />
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderFilterModal = () => (
    <Modal
      visible={filterModalVisible}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setFilterModalVisible(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Sort By</Text>
          
          {[
            { key: 'date', label: 'Date (Newest First)' },
            { key: 'name', label: 'Name (A-Z)' },
            { key: 'duration', label: 'Duration (Longest First)' }
          ].map(option => (
            <TouchableOpacity
              key={option.key}
              style={styles.modalOption}
              onPress={() => {
                setSortBy(option.key);
                setFilterModalVisible(false);
              }}
            >
              <Text style={styles.modalOptionText}>{option.label}</Text>
              {sortBy === option.key && (
                <MaterialIcons name="check" size={20} color="#2196F3" />
              )}
            </TouchableOpacity>
          ))}
          
          <TouchableOpacity
            style={styles.modalCloseButton}
            onPress={() => setFilterModalVisible(false)}
          >
            <Text style={styles.modalCloseText}>Close</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <MaterialIcons name="history" size={64} color="#ccc" />
      <Text style={styles.emptyTitle}>No Transcriptions Yet</Text>
      <Text style={styles.emptyText}>
        Your transcription history will appear here
      </Text>
      <TouchableOpacity 
        style={styles.emptyButton}
        onPress={() => navigation.navigate('Home')}
      >
        <Text style={styles.emptyButtonText}>Start Recording</Text>
      </TouchableOpacity>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <MaterialIcons name="history" size={48} color="#ccc" />
        <Text style={styles.loadingText}>Loading history...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {selectionMode ? renderSelectionHeader() : renderHeader()}
      
      <FlatList
        data={filteredTranscriptions}
        renderItem={renderTranscriptionItem}
        keyExtractor={item => item.id}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={["#2196F3"]}
          />
        }
        contentContainerStyle={filteredTranscriptions.length === 0 ? styles.emptyContent : null}
        ListEmptyComponent={renderEmpty}
        showsVerticalScrollIndicator={false}
      />
      
      {renderFilterModal()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    padding: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    paddingHorizontal: 12,
    marginBottom: 12,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    fontSize: 16,
  },
  headerActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  headerButton: {
    padding: 8,
    marginLeft: 12,
  },
  selectionHeader: {
    backgroundColor: '#e3f2fd',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    elevation: 2,
  },
  selectionButton: {
    padding: 8,
  },
  selectionCount: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  selectionActions: {
    flexDirection: 'row',
  },
  transcriptionItem: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginVertical: 4,
    borderRadius: 8,
    padding: 16,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
  },
  selectedItem: {
    backgroundColor: '#e3f2fd',
    borderColor: '#2196F3',
    borderWidth: 1,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  itemInfo: {
    flex: 1,
    marginRight: 12,
  },
  itemTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  itemDate: {
    fontSize: 12,
    color: '#666',
  },
  itemMeta: {
    alignItems: 'flex-end',
    gap: 4,
  },
  itemDuration: {
    fontSize: 12,
    color: '#666',
    fontFamily: 'monospace',
  },
  itemPreview: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 8,
  },
  itemFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  itemTags: {
    flexDirection: 'row',
    gap: 6,
  },
  tag: {
    fontSize: 10,
    color: '#2196F3',
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  emptyContent: {
    flex: 1,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  emptyButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 24,
  },
  emptyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },
  modalOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  modalOptionText: {
    fontSize: 16,
    color: '#333',
  },
  modalCloseButton: {
    marginTop: 16,
    padding: 12,
    alignItems: 'center',
  },
  modalCloseText: {
    fontSize: 16,
    color: '#2196F3',
    fontWeight: '600',
  },
});