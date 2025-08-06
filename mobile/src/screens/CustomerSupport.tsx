import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  FlatList,
  Alert,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Card, Button, Badge, SearchBar, FAB, ListItem, Avatar } from 'react-native-elements';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient, SupportTicket } from '../services/apiClient';

const CustomerSupport: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'tickets' | 'knowledge' | 'chat'>('tickets');
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [knowledgeArticles, setKnowledgeArticles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const ticketsData = await apiClient.getTickets();
      setTickets(ticketsData);
    } catch (error) {
      Alert.alert('Error', 'Failed to load support data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const searchKnowledgeBase = async () => {
    if (!searchQuery) return;
    try {
      const results = await apiClient.searchKnowledgeBase(searchQuery);
      setKnowledgeArticles(results);
    } catch (error) {
      Alert.alert('Error', 'Failed to search knowledge base');
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      new: '#3498db',
      open: '#2ecc71',
      in_progress: '#f39c12',
      waiting_customer: '#e67e22',
      resolved: '#27ae60',
      closed: '#95a5a6',
    };
    return colors[status] || '#95a5a6';
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: '#95a5a6',
      medium: '#3498db',
      high: '#f39c12',
      critical: '#e74c3c',
    };
    return colors[priority] || '#95a5a6';
  };

  const renderTicketItem = ({ item }: { item: SupportTicket }) => (
    <TouchableOpacity 
      style={styles.ticketItem} 
      activeOpacity={0.7}
      onPress={() => setSelectedTicket(item)}
    >
      <View style={styles.ticketHeader}>
        <View style={{ flex: 1 }}>
          <Text style={styles.ticketNumber}>{item.ticket_number}</Text>
          <Text style={styles.ticketSubject} numberOfLines={1}>{item.subject}</Text>
        </View>
        <View style={styles.ticketBadges}>
          <Badge
            value={item.priority}
            badgeStyle={[styles.priorityBadge, { backgroundColor: getPriorityColor(item.priority) }]}
            textStyle={styles.badgeText}
          />
        </View>
      </View>
      <Text style={styles.ticketDescription} numberOfLines={2}>
        {item.description}
      </Text>
      <View style={styles.ticketFooter}>
        <Badge
          value={item.status.replace('_', ' ')}
          badgeStyle={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) }]}
          textStyle={styles.badgeText}
        />
        <Text style={styles.ticketDate}>
          {new Date(item.created_at).toLocaleDateString()}
        </Text>
      </View>
    </TouchableOpacity>
  );

  const renderKnowledgeItem = ({ item }: { item: any }) => (
    <ListItem
      bottomDivider
      onPress={() => Alert.alert(item.title, item.content)}
      containerStyle={styles.knowledgeItem}
    >
      <ListItem.Content>
        <ListItem.Title style={styles.knowledgeTitle}>{item.title}</ListItem.Title>
        <ListItem.Subtitle style={styles.knowledgeExcerpt}>
          {item.excerpt}
        </ListItem.Subtitle>
        <View style={styles.knowledgeFooter}>
          <View style={styles.knowledgeStats}>
            <Icon name="visibility" size={14} color="#95a5a6" />
            <Text style={styles.statText}>{item.view_count}</Text>
          </View>
          <View style={styles.knowledgeStats}>
            <Icon name="thumb-up" size={14} color="#95a5a6" />
            <Text style={styles.statText}>{item.helpful_count}</Text>
          </View>
          <Badge value={item.category} textStyle={styles.categoryBadgeText} />
        </View>
      </ListItem.Content>
    </ListItem>
  );

  const renderTickets = () => (
    <FlatList
      data={tickets}
      renderItem={renderTicketItem}
      keyExtractor={item => item.id}
      contentContainerStyle={styles.ticketsList}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }
      ListEmptyComponent={
        <View style={styles.emptyContainer}>
          <Icon name="inbox" size={48} color="#bdc3c7" />
          <Text style={styles.emptyText}>No tickets found</Text>
        </View>
      }
    />
  );

  const renderKnowledgeBase = () => (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.knowledgeContainer}
    >
      <SearchBar
        placeholder="Search knowledge base..."
        onChangeText={setSearchQuery}
        onSubmitEditing={searchKnowledgeBase}
        value={searchQuery}
        platform="ios"
        containerStyle={styles.searchContainer}
        inputContainerStyle={styles.searchInput}
      />
      
      <FlatList
        data={knowledgeArticles}
        renderItem={renderKnowledgeItem}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.knowledgeList}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Icon name="search" size={48} color="#bdc3c7" />
            <Text style={styles.emptyText}>Search for help articles</Text>
          </View>
        }
      />
    </KeyboardAvoidingView>
  );

  const renderLiveChat = () => (
    <View style={styles.chatContainer}>
      <View style={styles.chatEmptyState}>
        <Icon name="chat" size={64} color="#bdc3c7" />
        <Text style={styles.chatEmptyTitle}>Live Chat</Text>
        <Text style={styles.chatEmptyText}>
          Connect with our support team instantly
        </Text>
        <Button
          title="Start Chat"
          buttonStyle={styles.startChatButton}
          onPress={() => Alert.alert('Live Chat', 'Chat feature coming soon!')}
        />
      </View>
    </View>
  );

  const renderTabs = () => (
    <View style={styles.tabContainer}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'tickets' && styles.activeTab]}
        onPress={() => setActiveTab('tickets')}
      >
        <Icon 
          name="confirmation-number" 
          size={20} 
          color={activeTab === 'tickets' ? '#3498db' : '#95a5a6'} 
        />
        <Text style={[styles.tabText, activeTab === 'tickets' && styles.activeTabText]}>
          Tickets
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, activeTab === 'knowledge' && styles.activeTab]}
        onPress={() => setActiveTab('knowledge')}
      >
        <Icon 
          name="library-books" 
          size={20} 
          color={activeTab === 'knowledge' ? '#3498db' : '#95a5a6'} 
        />
        <Text style={[styles.tabText, activeTab === 'knowledge' && styles.activeTabText]}>
          Knowledge
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, activeTab === 'chat' && styles.activeTab]}
        onPress={() => setActiveTab('chat')}
      >
        <Icon 
          name="chat" 
          size={20} 
          color={activeTab === 'chat' ? '#3498db' : '#95a5a6'} 
        />
        <Text style={[styles.tabText, activeTab === 'chat' && styles.activeTabText]}>
          Live Chat
        </Text>
      </TouchableOpacity>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#3498db" />
        <Text style={styles.loadingText}>Loading support data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {renderTabs()}
      
      {activeTab === 'tickets' && renderTickets()}
      {activeTab === 'knowledge' && renderKnowledgeBase()}
      {activeTab === 'chat' && renderLiveChat()}
      
      {activeTab === 'tickets' && (
        <FAB
          title="New Ticket"
          placement="right"
          icon={{ name: 'add', color: 'white' }}
          color="#3498db"
          onPress={() => Alert.alert('New Ticket', 'Ticket creation coming soon!')}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'white',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    gap: 5,
  },
  activeTab: {
    borderBottomWidth: 3,
    borderBottomColor: '#3498db',
  },
  tabText: {
    fontSize: 14,
    color: '#95a5a6',
  },
  activeTabText: {
    color: '#3498db',
    fontWeight: '600',
  },
  ticketsList: {
    padding: 15,
  },
  ticketItem: {
    backgroundColor: 'white',
    padding: 15,
    marginBottom: 10,
    borderRadius: 10,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  ticketHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  ticketNumber: {
    fontSize: 12,
    color: '#3498db',
    fontWeight: 'bold',
  },
  ticketSubject: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginTop: 2,
  },
  ticketBadges: {
    flexDirection: 'row',
  },
  ticketDescription: {
    fontSize: 14,
    color: '#7f8c8d',
    marginBottom: 10,
  },
  ticketFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusBadge: {
    borderRadius: 12,
    paddingHorizontal: 10,
  },
  priorityBadge: {
    borderRadius: 12,
    paddingHorizontal: 10,
  },
  badgeText: {
    fontSize: 12,
    textTransform: 'capitalize',
  },
  ticketDate: {
    fontSize: 12,
    color: '#95a5a6',
  },
  knowledgeContainer: {
    flex: 1,
  },
  searchContainer: {
    backgroundColor: 'white',
    borderTopWidth: 0,
    borderBottomWidth: 0,
    paddingHorizontal: 10,
  },
  searchInput: {
    backgroundColor: '#f5f5f5',
  },
  knowledgeList: {
    paddingBottom: 20,
  },
  knowledgeItem: {
    backgroundColor: 'white',
    marginHorizontal: 15,
    marginVertical: 5,
    borderRadius: 10,
    elevation: 1,
  },
  knowledgeTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  knowledgeExcerpt: {
    fontSize: 14,
    color: '#7f8c8d',
    marginTop: 5,
  },
  knowledgeFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
    gap: 15,
  },
  knowledgeStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  statText: {
    fontSize: 12,
    color: '#95a5a6',
  },
  categoryBadgeText: {
    fontSize: 12,
  },
  chatContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  chatEmptyState: {
    alignItems: 'center',
  },
  chatEmptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginTop: 20,
  },
  chatEmptyText: {
    fontSize: 16,
    color: '#7f8c8d',
    marginTop: 10,
    textAlign: 'center',
  },
  startChatButton: {
    marginTop: 20,
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 25,
    backgroundColor: '#3498db',
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#95a5a6',
    marginTop: 10,
  },
});

export default CustomerSupport;