import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Modal,
  FlatList,
  RefreshControl,
  Dimensions,
  Animated,
  TextInput,
  Image,
  StatusBar,
  Platform,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient } from '../../services/api';
import { theme } from '../../theme';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LineChart, BarChart, PieChart } from 'react-native-chart-kit';
import { Rating } from 'react-native-ratings';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface MarketplaceItem {
  id: string;
  name: string;
  description: string;
  type: 'plugin' | 'extension' | 'template' | 'integration' | 'workflow' | 'theme' | 'model' | 'dataset';
  version: string;
  category: string;
  tags: string[];
  compatibility: 'stable' | 'beta' | 'alpha' | 'experimental';
  price: number;
  currency: string;
  developer_name: string;
  downloads: number;
  rating: number;
  review_count: number;
  created_at: string;
  repository_url?: string;
  documentation_url?: string;
  demo_url?: string;
  screenshots: string[];
  dependencies: string[];
  permissions: string[];
  verified: boolean;
}

interface Installation {
  id: string;
  item_id: string;
  version: string;
  status: 'not_installed' | 'installing' | 'installed' | 'updating' | 'failed';
  installed_at: string;
  auto_update: boolean;
}

interface Category {
  name: string;
  count: number;
  types: string[];
}

const typeIcons = {
  plugin: 'extension',
  extension: 'extension', 
  template: 'code',
  integration: 'integration-instructions',
  workflow: 'account-tree',
  theme: 'palette',
  model: 'psychology',
  dataset: 'dataset',
};

const typeColors = {
  plugin: '#2196F3',
  extension: '#4CAF50',
  template: '#FF9800',
  integration: '#9C27B0',
  workflow: '#F44336',
  theme: '#607D8B',
  model: '#795548',
  dataset: '#3F51B5',
};

const compatibilityColors = {
  stable: theme.colors.success,
  beta: theme.colors.warning,
  alpha: theme.colors.info,
  experimental: theme.colors.error,
};

const MarketplaceStore: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false);
  const [items, setItems] = useState<MarketplaceItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<MarketplaceItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'browse' | 'installed' | 'favorites' | 'stats'>('browse');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [sortBy, setSortBy] = useState('downloads');
  const [showFilters, setShowFilters] = useState(false);
  const [showSortModal, setShowSortModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState<MarketplaceItem | null>(null);
  const [itemDetailsModal, setItemDetailsModal] = useState(false);
  const [installModal, setInstallModal] = useState(false);
  const [reviewsModal, setReviewsModal] = useState(false);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [installQueue, setInstallQueue] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  
  const slideAnim = useRef(new Animated.Value(screenHeight)).current;
  const searchTimeout = useRef<NodeJS.Timeout>();

  useEffect(() => {
    loadMarketplaceData();
    loadInstallations();
    loadFavorites();
  }, []);

  useEffect(() => {
    filterItems();
  }, [items, searchQuery, selectedCategory, selectedType, sortBy]);

  const loadMarketplaceData = async () => {
    try {
      setLoading(true);
      const [itemsResponse, categoriesResponse] = await Promise.all([
        apiClient.get('/api/v1/marketplace/'),
        apiClient.get('/api/v1/marketplace/categories/'),
      ]);
      
      setItems(itemsResponse.data);
      setCategories(categoriesResponse.data);
    } catch (error) {
      console.error('Failed to load marketplace data:', error);
      Alert.alert('Error', 'Failed to load marketplace');
    } finally {
      setLoading(false);
    }
  };

  const loadInstallations = async () => {
    try {
      const response = await apiClient.get('/api/v1/marketplace/installations/');
      setInstallations(response.data);
    } catch (error) {
      console.error('Failed to load installations:', error);
    }
  };

  const loadFavorites = async () => {
    try {
      const saved = await AsyncStorage.getItem('marketplace_favorites');
      if (saved) {
        setFavorites(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Failed to load favorites:', error);
    }
  };

  const saveFavorites = async (newFavorites: string[]) => {
    try {
      await AsyncStorage.setItem('marketplace_favorites', JSON.stringify(newFavorites));
      setFavorites(newFavorites);
    } catch (error) {
      console.error('Failed to save favorites:', error);
    }
  };

  const filterItems = () => {
    let filtered = [...items];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        item =>
          item.name.toLowerCase().includes(query) ||
          item.description.toLowerCase().includes(query) ||
          item.developer_name.toLowerCase().includes(query) ||
          item.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    if (selectedCategory) {
      filtered = filtered.filter(item => item.category === selectedCategory);
    }

    if (selectedType) {
      filtered = filtered.filter(item => item.type === selectedType);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'downloads':
          return b.downloads - a.downloads;
        case 'rating':
          return b.rating - a.rating;
        case 'name':
          return a.name.localeCompare(b.name);
        case 'price':
          return a.price - b.price;
        case 'newest':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        default:
          return 0;
      }
    });

    setFilteredItems(filtered);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadMarketplaceData();
    await loadInstallations();
    setRefreshing(false);
  };

  const handleInstall = async (item: MarketplaceItem) => {
    try {
      setInstallQueue([...installQueue, item.id]);
      
      await apiClient.post(`/api/v1/marketplace/${item.id}/install`, {
        item_id: item.id,
        auto_update: true,
      });
      
      Alert.alert('Success', `Installing ${item.name}...`);
      setInstallModal(false);
      
      // Simulate installation
      setTimeout(() => {
        setInstallQueue(prev => prev.filter(id => id !== item.id));
        loadInstallations();
        Alert.alert('Success', `${item.name} installed successfully!`);
      }, 3000);
    } catch (error) {
      setInstallQueue(prev => prev.filter(id => id !== item.id));
      Alert.alert('Error', `Failed to install ${item.name}`);
    }
  };

  const handleUninstall = (installation: Installation) => {
    Alert.alert(
      'Uninstall',
      'Are you sure you want to uninstall this item?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Uninstall',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiClient.delete(`/api/v1/marketplace/installations/${installation.id}`);
              Alert.alert('Success', 'Item uninstalled successfully');
              loadInstallations();
            } catch (error) {
              Alert.alert('Error', 'Failed to uninstall item');
            }
          },
        },
      ]
    );
  };

  const toggleFavorite = async (itemId: string) => {
    const newFavorites = favorites.includes(itemId)
      ? favorites.filter(id => id !== itemId)
      : [...favorites, itemId];
    
    await saveFavorites(newFavorites);
  };

  const getInstallationStatus = (itemId: string): Installation | null => {
    return installations.find(inst => inst.item_id === itemId) || null;
  };

  const getCompatibilityIcon = (compatibility: string) => {
    switch (compatibility) {
      case 'stable': return 'verified';
      case 'beta': return 'science';
      case 'alpha': return 'bug-report';
      case 'experimental': return 'warning';
      default: return 'help';
    }
  };

  const renderItemCard = ({ item }: { item: MarketplaceItem }) => {
    const installation = getInstallationStatus(item.id);
    const isFavorite = favorites.includes(item.id);
    const isInstalling = installQueue.includes(item.id);

    return (
      <TouchableOpacity
        style={styles.itemCard}
        onPress={() => {
          setSelectedItem(item);
          setItemDetailsModal(true);
        }}
        activeOpacity={0.8}
      >
        <View style={styles.cardHeader}>
          <View style={[styles.typeIcon, { backgroundColor: typeColors[item.type] + '20' }]}>
            <Icon name={typeIcons[item.type]} size={24} color={typeColors[item.type]} />
          </View>
          <View style={styles.itemInfo}>
            <Text style={styles.itemName} numberOfLines={1}>{item.name}</Text>
            <Text style={styles.developer} numberOfLines={1}>by {item.developer_name}</Text>
            <View style={styles.versionRow}>
              <Text style={styles.version}>v{item.version}</Text>
              <View style={styles.typeChip}>
                <Text style={[styles.typeText, { color: typeColors[item.type] }]}>
                  {item.type}
                </Text>
              </View>
            </View>
          </View>
          <TouchableOpacity
            style={styles.favoriteButton}
            onPress={() => toggleFavorite(item.id)}
          >
            <Icon 
              name={isFavorite ? 'favorite' : 'favorite-border'} 
              size={20} 
              color={isFavorite ? theme.colors.error : theme.colors.textSecondary}
            />
          </TouchableOpacity>
        </View>

        <Text style={styles.description} numberOfLines={2}>
          {item.description}
        </Text>

        <View style={styles.ratingRow}>
          <View style={styles.rating}>
            <Rating
              readonly
              startingValue={item.rating}
              imageSize={14}
              style={{ alignItems: 'flex-start' }}
            />
            <Text style={styles.ratingText}>
              {item.rating} ({item.review_count})
            </Text>
          </View>
          <View style={styles.downloads}>
            <Icon name="download" size={14} color={theme.colors.textSecondary} />
            <Text style={styles.downloadText}>
              {item.downloads.toLocaleString()}
            </Text>
          </View>
        </View>

        <View style={styles.cardFooter}>
          <View style={styles.badges}>
            <View style={[styles.compatibilityBadge, { backgroundColor: compatibilityColors[item.compatibility] + '20' }]}>
              <Icon 
                name={getCompatibilityIcon(item.compatibility)} 
                size={12} 
                color={compatibilityColors[item.compatibility]} 
              />
              <Text style={[styles.compatibilityText, { color: compatibilityColors[item.compatibility] }]}>
                {item.compatibility}
              </Text>
            </View>
            {item.verified && (
              <View style={styles.verifiedBadge}>
                <Icon name="verified" size={12} color={theme.colors.primary} />
                <Text style={styles.verifiedText}>Verified</Text>
              </View>
            )}
            <View style={styles.priceBadge}>
              <Text style={[styles.priceText, { color: item.price > 0 ? theme.colors.secondary : theme.colors.success }]}>
                {item.price > 0 ? `$${item.price}` : 'Free'}
              </Text>
            </View>
          </View>

          {installation?.status === 'installed' ? (
            <TouchableOpacity
              style={styles.installedButton}
              onPress={() => handleUninstall(installation)}
            >
              <Icon name="check-circle" size={16} color={theme.colors.success} />
              <Text style={styles.installedText}>Installed</Text>
            </TouchableOpacity>
          ) : isInstalling ? (
            <View style={styles.installingButton}>
              <ActivityIndicator size={16} color={theme.colors.primary} />
              <Text style={styles.installingText}>Installing...</Text>
            </View>
          ) : (
            <TouchableOpacity
              style={styles.installButton}
              onPress={() => {
                setSelectedItem(item);
                setInstallModal(true);
              }}
            >
              <Icon name="get-app" size={16} color="#fff" />
              <Text style={styles.installText}>Install</Text>
            </TouchableOpacity>
          )}
        </View>

        {item.tags.length > 0 && (
          <View style={styles.tagRow}>
            {item.tags.slice(0, 3).map((tag) => (
              <View key={tag} style={styles.tag}>
                <Text style={styles.tagText}>#{tag}</Text>
              </View>
            ))}
            {item.tags.length > 3 && (
              <Text style={styles.moreTagsText}>+{item.tags.length - 3}</Text>
            )}
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderFilterModal = () => (
    <Modal
      visible={showFilters}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setShowFilters(false)}
    >
      <View style={styles.modalContainer}>
        <View style={styles.filterModal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Filters</Text>
            <TouchableOpacity onPress={() => setShowFilters(false)}>
              <Icon name="close" size={24} color={theme.colors.text} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.filterContent}>
            <View style={styles.filterSection}>
              <Text style={styles.filterSectionTitle}>Category</Text>
              <TouchableOpacity
                style={[styles.filterOption, !selectedCategory && styles.activeFilterOption]}
                onPress={() => {
                  setSelectedCategory('');
                  setShowFilters(false);
                }}
              >
                <Text style={[styles.filterOptionText, !selectedCategory && styles.activeFilterText]}>
                  All Categories
                </Text>
              </TouchableOpacity>
              {categories.map((category) => (
                <TouchableOpacity
                  key={category.name}
                  style={[styles.filterOption, selectedCategory === category.name && styles.activeFilterOption]}
                  onPress={() => {
                    setSelectedCategory(category.name);
                    setShowFilters(false);
                  }}
                >
                  <Text style={[styles.filterOptionText, selectedCategory === category.name && styles.activeFilterText]}>
                    {category.name} ({category.count})
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.filterSection}>
              <Text style={styles.filterSectionTitle}>Type</Text>
              <TouchableOpacity
                style={[styles.filterOption, !selectedType && styles.activeFilterOption]}
                onPress={() => {
                  setSelectedType('');
                  setShowFilters(false);
                }}
              >
                <Text style={[styles.filterOptionText, !selectedType && styles.activeFilterText]}>
                  All Types
                </Text>
              </TouchableOpacity>
              {Object.keys(typeIcons).map((type) => (
                <TouchableOpacity
                  key={type}
                  style={[styles.filterOption, selectedType === type && styles.activeFilterOption]}
                  onPress={() => {
                    setSelectedType(type);
                    setShowFilters(false);
                  }}
                >
                  <View style={styles.typeFilterRow}>
                    <Icon name={typeIcons[type]} size={20} color={typeColors[type]} />
                    <Text style={[styles.filterOptionText, selectedType === type && styles.activeFilterText]}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity
              style={styles.clearFiltersButton}
              onPress={() => {
                setSelectedCategory('');
                setSelectedType('');
                setSearchQuery('');
                setShowFilters(false);
              }}
            >
              <Text style={styles.clearFiltersText}>Clear All Filters</Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );

  const renderSortModal = () => (
    <Modal
      visible={showSortModal}
      animationType="fade"
      transparent={true}
      onRequestClose={() => setShowSortModal(false)}
    >
      <View style={styles.modalContainer}>
        <View style={styles.sortModal}>
          <Text style={styles.modalTitle}>Sort By</Text>
          {[
            { key: 'downloads', label: 'Most Downloaded', icon: 'trending-down' },
            { key: 'rating', label: 'Highest Rated', icon: 'star' },
            { key: 'name', label: 'Name A-Z', icon: 'sort-by-alpha' },
            { key: 'price', label: 'Price Low-High', icon: 'attach-money' },
            { key: 'newest', label: 'Newest First', icon: 'new-releases' },
          ].map((option) => (
            <TouchableOpacity
              key={option.key}
              style={[styles.sortOption, sortBy === option.key && styles.activeSortOption]}
              onPress={() => {
                setSortBy(option.key);
                setShowSortModal(false);
              }}
            >
              <Icon name={option.icon} size={20} color={sortBy === option.key ? theme.colors.primary : theme.colors.text} />
              <Text style={[styles.sortOptionText, sortBy === option.key && styles.activeSortText]}>
                {option.label}
              </Text>
              {sortBy === option.key && (
                <Icon name="check" size={20} color={theme.colors.primary} />
              )}
            </TouchableOpacity>
          ))}
        </View>
      </View>
    </Modal>
  );

  const renderTabContent = () => {
    switch (selectedTab) {
      case 'browse':
        return (
          <FlatList
            data={filteredItems}
            renderItem={renderItemCard}
            keyExtractor={item => item.id}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                colors={[theme.colors.primary]}
              />
            }
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.itemsList}
            ListEmptyComponent={
              loading ? (
                <View style={styles.centerContainer}>
                  <ActivityIndicator size="large" color={theme.colors.primary} />
                </View>
              ) : (
                <View style={styles.centerContainer}>
                  <Icon name="store" size={64} color={theme.colors.textSecondary} />
                  <Text style={styles.emptyText}>No items found</Text>
                  <Text style={styles.emptySubtext}>Try adjusting your filters</Text>
                </View>
              )
            }
          />
        );

      case 'installed':
        const installedItems = items.filter(item => 
          installations.some(inst => inst.item_id === item.id)
        );
        return (
          <FlatList
            data={installedItems}
            renderItem={renderItemCard}
            keyExtractor={item => item.id}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                colors={[theme.colors.primary]}
              />
            }
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.itemsList}
            ListEmptyComponent={
              <View style={styles.centerContainer}>
                <Icon name="get-app" size={64} color={theme.colors.textSecondary} />
                <Text style={styles.emptyText}>No installed items</Text>
                <Text style={styles.emptySubtext}>Browse the store to install items</Text>
              </View>
            }
          />
        );

      case 'favorites':
        const favoriteItems = items.filter(item => favorites.includes(item.id));
        return (
          <FlatList
            data={favoriteItems}
            renderItem={renderItemCard}
            keyExtractor={item => item.id}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                colors={[theme.colors.primary]}
              />
            }
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.itemsList}
            ListEmptyComponent={
              <View style={styles.centerContainer}>
                <Icon name="favorite" size={64} color={theme.colors.textSecondary} />
                <Text style={styles.emptyText}>No favorites yet</Text>
                <Text style={styles.emptySubtext}>Tap the heart icon to favorite items</Text>
              </View>
            }
          />
        );

      case 'stats':
        return (
          <ScrollView 
            style={styles.statsContainer}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                colors={[theme.colors.primary]}
              />
            }
          >
            <View style={styles.statsCard}>
              <Text style={styles.statsTitle}>Marketplace Overview</Text>
              <View style={styles.statsGrid}>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{items.length}</Text>
                  <Text style={styles.statLabel}>Total Items</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{installations.length}</Text>
                  <Text style={styles.statLabel}>Installed</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{favorites.length}</Text>
                  <Text style={styles.statLabel}>Favorites</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{categories.length}</Text>
                  <Text style={styles.statLabel}>Categories</Text>
                </View>
              </View>
            </View>

            <View style={styles.statsCard}>
              <Text style={styles.statsTitle}>Popular Categories</Text>
              {categories.slice(0, 5).map((category) => (
                <View key={category.name} style={styles.categoryItem}>
                  <Text style={styles.categoryName}>{category.name}</Text>
                  <Text style={styles.categoryCount}>{category.count} items</Text>
                </View>
              ))}
            </View>
          </ScrollView>
        );

      default:
        return null;
    }
  };

  return (
    <>
      {/* Main Button */}
      <TouchableOpacity
        style={styles.mainButton}
        onPress={() => setModalVisible(true)}
        activeOpacity={0.8}
      >
        <View style={styles.buttonContent}>
          <Icon name="store" size={24} color={theme.colors.primary} />
          <View style={styles.buttonText}>
            <Text style={styles.buttonLabel}>Marketplace</Text>
            <Text style={styles.buttonSubtitle}>
              {installations.length} installed • {favorites.length} favorites
            </Text>
          </View>
        </View>
        <Icon name="chevron-right" size={24} color={theme.colors.textSecondary} />
      </TouchableOpacity>

      {/* Main Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={false}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.container}>
          <StatusBar backgroundColor={theme.colors.background} barStyle="dark-content" />
          
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => setModalVisible(false)}
            >
              <Icon name="arrow-back" size={24} color={theme.colors.text} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Marketplace</Text>
            <View style={styles.headerActions}>
              <TouchableOpacity
                style={styles.headerButton}
                onPress={() => setShowSortModal(true)}
              >
                <Icon name="sort" size={24} color={theme.colors.text} />
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.headerButton}
                onPress={() => setShowFilters(true)}
              >
                <Icon name="filter-list" size={24} color={theme.colors.text} />
              </TouchableOpacity>
            </View>
          </View>

          {/* Search */}
          <View style={styles.searchContainer}>
            <View style={styles.searchBox}>
              <Icon name="search" size={20} color={theme.colors.textSecondary} />
              <TextInput
                style={styles.searchInput}
                placeholder="Search marketplace..."
                value={searchQuery}
                onChangeText={(text) => {
                  setSearchQuery(text);
                  if (searchTimeout.current) {
                    clearTimeout(searchTimeout.current);
                  }
                  searchTimeout.current = setTimeout(() => {
                    filterItems();
                  }, 300);
                }}
                placeholderTextColor={theme.colors.textSecondary}
              />
              {searchQuery.length > 0 && (
                <TouchableOpacity onPress={() => setSearchQuery('')}>
                  <Icon name="clear" size={20} color={theme.colors.textSecondary} />
                </TouchableOpacity>
              )}
            </View>
          </View>

          {/* Tabs */}
          <View style={styles.tabContainer}>
            {[
              { key: 'browse', label: 'Browse', icon: 'store' },
              { key: 'installed', label: 'Installed', icon: 'get-app' },
              { key: 'favorites', label: 'Favorites', icon: 'favorite' },
              { key: 'stats', label: 'Stats', icon: 'assessment' },
            ].map((tab) => (
              <TouchableOpacity
                key={tab.key}
                style={[styles.tab, selectedTab === tab.key && styles.activeTab]}
                onPress={() => setSelectedTab(tab.key as any)}
              >
                <Icon 
                  name={tab.icon} 
                  size={20} 
                  color={selectedTab === tab.key ? theme.colors.primary : theme.colors.textSecondary} 
                />
                <Text style={[
                  styles.tabText, 
                  selectedTab === tab.key && styles.activeTabText
                ]}>
                  {tab.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Content */}
          <View style={styles.content}>
            {renderTabContent()}
          </View>
        </View>

        {renderFilterModal()}
        {renderSortModal()}
      </Modal>

      {/* Item Details Modal */}
      {selectedItem && (
        <Modal
          visible={itemDetailsModal}
          animationType="slide"
          transparent={true}
          onRequestClose={() => setItemDetailsModal(false)}
        >
          <View style={styles.modalContainer}>
            <View style={styles.itemDetailsModal}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>{selectedItem.name}</Text>
                <TouchableOpacity onPress={() => setItemDetailsModal(false)}>
                  <Icon name="close" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>

              <ScrollView style={styles.itemDetailsContent}>
                <View style={styles.itemDetailsHeader}>
                  <View style={[styles.itemDetailsIcon, { backgroundColor: typeColors[selectedItem.type] + '20' }]}>
                    <Icon name={typeIcons[selectedItem.type]} size={32} color={typeColors[selectedItem.type]} />
                  </View>
                  <View style={styles.itemDetailsInfo}>
                    <Text style={styles.itemDetailsName}>{selectedItem.name}</Text>
                    <Text style={styles.itemDetailsDeveloper}>by {selectedItem.developer_name}</Text>
                    <Text style={styles.itemDetailsVersion}>Version {selectedItem.version}</Text>
                  </View>
                </View>

                <View style={styles.itemDetailsRating}>
                  <Rating
                    readonly
                    startingValue={selectedItem.rating}
                    imageSize={16}
                    style={{ alignItems: 'flex-start' }}
                  />
                  <Text style={styles.itemDetailsRatingText}>
                    {selectedItem.rating} ({selectedItem.review_count} reviews)
                  </Text>
                  <Text style={styles.itemDetailsDownloads}>
                    {selectedItem.downloads.toLocaleString()} downloads
                  </Text>
                </View>

                <Text style={styles.itemDetailsDescription}>
                  {selectedItem.description}
                </Text>

                <View style={styles.itemDetailsBadges}>
                  <View style={[styles.detailsBadge, { backgroundColor: compatibilityColors[selectedItem.compatibility] + '20' }]}>
                    <Icon name={getCompatibilityIcon(selectedItem.compatibility)} size={14} color={compatibilityColors[selectedItem.compatibility]} />
                    <Text style={[styles.detailsBadgeText, { color: compatibilityColors[selectedItem.compatibility] }]}>
                      {selectedItem.compatibility}
                    </Text>
                  </View>
                  <View style={styles.detailsBadge}>
                    <Text style={styles.detailsBadgeText}>{selectedItem.category}</Text>
                  </View>
                  {selectedItem.verified && (
                    <View style={[styles.detailsBadge, { backgroundColor: theme.colors.primary + '20' }]}>
                      <Icon name="verified" size={14} color={theme.colors.primary} />
                      <Text style={[styles.detailsBadgeText, { color: theme.colors.primary }]}>Verified</Text>
                    </View>
                  )}
                </View>

                {selectedItem.tags.length > 0 && (
                  <View style={styles.itemDetailsTags}>
                    <Text style={styles.detailsSectionTitle}>Tags</Text>
                    <View style={styles.tagsContainer}>
                      {selectedItem.tags.map((tag) => (
                        <View key={tag} style={styles.detailsTag}>
                          <Text style={styles.detailsTagText}>#{tag}</Text>
                        </View>
                      ))}
                    </View>
                  </View>
                )}

                {selectedItem.permissions.length > 0 && (
                  <View style={styles.detailsSection}>
                    <Text style={styles.detailsSectionTitle}>Required Permissions</Text>
                    {selectedItem.permissions.map((permission) => (
                      <View key={permission} style={styles.permissionItem}>
                        <Icon name="security" size={16} color={theme.colors.warning} />
                        <Text style={styles.permissionText}>{permission}</Text>
                      </View>
                    ))}
                  </View>
                )}
              </ScrollView>

              <View style={styles.itemDetailsActions}>
                <TouchableOpacity
                  style={styles.favoriteActionButton}
                  onPress={() => toggleFavorite(selectedItem.id)}
                >
                  <Icon 
                    name={favorites.includes(selectedItem.id) ? 'favorite' : 'favorite-border'} 
                    size={20} 
                    color={favorites.includes(selectedItem.id) ? theme.colors.error : theme.colors.textSecondary}
                  />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.installActionButton}
                  onPress={() => {
                    setItemDetailsModal(false);
                    setInstallModal(true);
                  }}
                >
                  <Text style={styles.installActionText}>Install</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      )}

      {/* Install Modal */}
      {selectedItem && (
        <Modal
          visible={installModal}
          animationType="fade"
          transparent={true}
          onRequestClose={() => setInstallModal(false)}
        >
          <View style={styles.modalContainer}>
            <View style={styles.installModalContent}>
              <Text style={styles.installModalTitle}>
                Install {selectedItem.name}
              </Text>
              <Text style={styles.installModalText}>
                This will install {selectedItem.name} version {selectedItem.version}.
              </Text>
              
              {selectedItem.permissions.length > 0 && (
                <View style={styles.installPermissions}>
                  <Text style={styles.installPermissionsTitle}>Required Permissions:</Text>
                  {selectedItem.permissions.map((permission) => (
                    <Text key={permission} style={styles.installPermissionItem}>
                      • {permission}
                    </Text>
                  ))}
                </View>
              )}

              <View style={styles.installModalActions}>
                <TouchableOpacity
                  style={styles.installCancelButton}
                  onPress={() => setInstallModal(false)}
                >
                  <Text style={styles.installCancelText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.installConfirmButton}
                  onPress={() => handleInstall(selectedItem)}
                >
                  <Text style={styles.installConfirmText}>Install</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      )}
    </>
  );
};

const styles = StyleSheet.create({
  mainButton: {
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  buttonText: {
    marginLeft: 12,
    flex: 1,
  },
  buttonLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
  },
  buttonSubtitle: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
    flex: 1,
    textAlign: 'center',
  },
  headerActions: {
    flexDirection: 'row',
  },
  headerButton: {
    padding: 8,
    marginLeft: 8,
  },
  searchContainer: {
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: theme.colors.text,
    marginLeft: 8,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: theme.colors.primary,
  },
  tabText: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginLeft: 4,
    fontWeight: '500',
  },
  activeTabText: {
    color: theme.colors.primary,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  itemsList: {
    padding: 16,
  },
  itemCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  typeIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 2,
  },
  developer: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginBottom: 4,
  },
  versionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  version: {
    fontSize: 11,
    color: theme.colors.textSecondary,
  },
  typeChip: {
    backgroundColor: theme.colors.background,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  typeText: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  favoriteButton: {
    padding: 8,
  },
  description: {
    fontSize: 13,
    color: theme.colors.textSecondary,
    lineHeight: 18,
    marginBottom: 12,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  rating: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingText: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginLeft: 4,
  },
  downloads: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  downloadText: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginLeft: 4,
  },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  badges: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
  },
  compatibilityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    gap: 2,
  },
  compatibilityText: {
    fontSize: 10,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.primary + '20',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    gap: 2,
  },
  verifiedText: {
    fontSize: 10,
    fontWeight: '500',
    color: theme.colors.primary,
  },
  priceBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    backgroundColor: theme.colors.background,
  },
  priceText: {
    fontSize: 11,
    fontWeight: '600',
  },
  installButton: {
    backgroundColor: theme.colors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    gap: 4,
  },
  installText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  installedButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    gap: 4,
    backgroundColor: theme.colors.success + '20',
  },
  installedText: {
    color: theme.colors.success,
    fontSize: 12,
    fontWeight: '600',
  },
  installingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    gap: 4,
    backgroundColor: theme.colors.background,
  },
  installingText: {
    color: theme.colors.primary,
    fontSize: 12,
    fontWeight: '600',
  },
  tagRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tag: {
    backgroundColor: theme.colors.background,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  tagText: {
    fontSize: 10,
    color: theme.colors.textSecondary,
  },
  moreTagsText: {
    fontSize: 10,
    color: theme.colors.textSecondary,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 16,
    color: theme.colors.textSecondary,
    marginTop: 16,
    fontWeight: '500',
  },
  emptySubtext: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  statsContainer: {
    flex: 1,
    padding: 16,
  },
  statsCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  statItem: {
    width: '50%',
    alignItems: 'center',
    paddingVertical: 12,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.primary,
  },
  statLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  categoryItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  categoryName: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.text,
  },
  categoryCount: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  filterModal: {
    backgroundColor: theme.colors.background,
    borderRadius: 16,
    width: screenWidth - 32,
    maxHeight: screenHeight * 0.8,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
  },
  filterContent: {
    flex: 1,
    padding: 20,
  },
  filterSection: {
    marginBottom: 24,
  },
  filterSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 12,
  },
  filterOption: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 4,
  },
  activeFilterOption: {
    backgroundColor: theme.colors.primary + '20',
  },
  filterOptionText: {
    fontSize: 14,
    color: theme.colors.text,
  },
  activeFilterText: {
    color: theme.colors.primary,
    fontWeight: '600',
  },
  typeFilterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  clearFiltersButton: {
    backgroundColor: theme.colors.error + '20',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  clearFiltersText: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.error,
  },
  sortModal: {
    backgroundColor: theme.colors.background,
    borderRadius: 16,
    padding: 20,
    minWidth: 250,
  },
  sortOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginVertical: 2,
  },
  activeSortOption: {
    backgroundColor: theme.colors.primary + '20',
  },
  sortOptionText: {
    fontSize: 14,
    color: theme.colors.text,
    marginLeft: 12,
    flex: 1,
  },
  activeSortText: {
    color: theme.colors.primary,
    fontWeight: '600',
  },
  itemDetailsModal: {
    backgroundColor: theme.colors.background,
    borderRadius: 16,
    width: screenWidth - 32,
    maxHeight: screenHeight * 0.9,
  },
  itemDetailsContent: {
    flex: 1,
    padding: 20,
  },
  itemDetailsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  itemDetailsIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  itemDetailsInfo: {
    flex: 1,
  },
  itemDetailsName: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
  },
  itemDetailsDeveloper: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  itemDetailsVersion: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  itemDetailsRating: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
  },
  itemDetailsRatingText: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  itemDetailsDownloads: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  itemDetailsDescription: {
    fontSize: 14,
    color: theme.colors.text,
    lineHeight: 20,
    marginBottom: 16,
  },
  itemDetailsBadges: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 16,
  },
  detailsBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: theme.colors.background,
    gap: 4,
  },
  detailsBadgeText: {
    fontSize: 12,
    color: theme.colors.text,
    fontWeight: '500',
  },
  itemDetailsTags: {
    marginBottom: 16,
  },
  detailsSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 8,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  detailsTag: {
    backgroundColor: theme.colors.background,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  detailsTagText: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  detailsSection: {
    marginBottom: 16,
  },
  permissionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
    gap: 8,
  },
  permissionText: {
    fontSize: 12,
    color: theme.colors.text,
    flex: 1,
  },
  itemDetailsActions: {
    flexDirection: 'row',
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
    gap: 12,
  },
  favoriteActionButton: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: theme.colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  installActionButton: {
    flex: 1,
    backgroundColor: theme.colors.primary,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  installActionText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  installModalContent: {
    backgroundColor: theme.colors.background,
    borderRadius: 16,
    padding: 20,
    minWidth: 280,
    maxWidth: screenWidth - 64,
  },
  installModalTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 12,
  },
  installModalText: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    lineHeight: 20,
    marginBottom: 16,
  },
  installPermissions: {
    backgroundColor: theme.colors.warning + '10',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  installPermissionsTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: theme.colors.warning,
    marginBottom: 8,
  },
  installPermissionItem: {
    fontSize: 12,
    color: theme.colors.warning,
    marginBottom: 2,
  },
  installModalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  installCancelButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    backgroundColor: theme.colors.background,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  installCancelText: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
  },
  installConfirmButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    backgroundColor: theme.colors.primary,
  },
  installConfirmText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
});

export default MarketplaceStore;