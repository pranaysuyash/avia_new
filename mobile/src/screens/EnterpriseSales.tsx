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
} from 'react-native';
import { Card, Button, Badge, SearchBar, FAB } from 'react-native-elements';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient, Lead } from '../services/apiClient';

const EnterpriseSales: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [pipeline, setPipeline] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [leadsData, pipelineData] = await Promise.all([
        apiClient.getLeads(),
        apiClient.getSalesPipeline(),
      ]);
      setLeads(leadsData);
      setPipeline(pipelineData);
    } catch (error) {
      Alert.alert('Error', 'Failed to load sales data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      new: '#3498db',
      contacted: '#f39c12',
      qualified: '#27ae60',
      proposal: '#e67e22',
      negotiation: '#9b59b6',
      closed_won: '#2ecc71',
      closed_lost: '#e74c3c',
    };
    return colors[status] || '#95a5a6';
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: '#95a5a6',
      medium: '#f39c12',
      high: '#e74c3c',
    };
    return colors[priority] || '#95a5a6';
  };

  const filteredLeads = leads.filter(lead => {
    const matchesSearch = lead.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      lead.contact_name?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = !selectedStatus || lead.status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  const renderPipelineCard = () => (
    <Card containerStyle={styles.pipelineCard}>
      <Text style={styles.cardTitle}>Sales Pipeline</Text>
      {pipeline && (
        <View style={styles.metricsContainer}>
          <View style={styles.metric}>
            <Text style={styles.metricValue}>{pipeline.total_leads}</Text>
            <Text style={styles.metricLabel}>Total Leads</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricValue}>${(pipeline.total_pipeline_value / 1000).toFixed(0)}k</Text>
            <Text style={styles.metricLabel}>Pipeline Value</Text>
          </View>
          <View style={styles.metric}>
            <Text style={styles.metricValue}>{pipeline.win_rate?.toFixed(1)}%</Text>
            <Text style={styles.metricLabel}>Win Rate</Text>
          </View>
        </View>
      )}
    </Card>
  );

  const renderLeadItem = ({ item }: { item: Lead }) => (
    <TouchableOpacity style={styles.leadItem} activeOpacity={0.7}>
      <View style={styles.leadHeader}>
        <View style={{ flex: 1 }}>
          <Text style={styles.leadCompany}>{item.company_name}</Text>
          {item.contact_name && (
            <Text style={styles.leadContact}>{item.contact_name}</Text>
          )}
        </View>
        <View style={styles.leadBadges}>
          <Badge
            value={item.status.replace('_', ' ')}
            badgeStyle={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) }]}
            textStyle={styles.badgeText}
          />
          <Badge
            value={item.priority}
            badgeStyle={[styles.priorityBadge, { backgroundColor: getPriorityColor(item.priority) }]}
            textStyle={styles.badgeText}
          />
        </View>
      </View>
      <View style={styles.leadFooter}>
        <View style={styles.scoreContainer}>
          <Icon name="trending-up" size={16} color="#666" />
          <Text style={styles.leadScore}>Score: {item.score}</Text>
        </View>
        <Text style={styles.leadDate}>
          {new Date(item.created_at).toLocaleDateString()}
        </Text>
      </View>
    </TouchableOpacity>
  );

  const statusFilters = [
    { label: 'All', value: null },
    { label: 'New', value: 'new' },
    { label: 'Contacted', value: 'contacted' },
    { label: 'Qualified', value: 'qualified' },
    { label: 'Proposal', value: 'proposal' },
  ];

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#3498db" />
        <Text style={styles.loadingText}>Loading sales data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        stickyHeaderIndices={[1]}
      >
        {renderPipelineCard()}
        
        <View style={styles.searchSection}>
          <SearchBar
            placeholder="Search leads..."
            onChangeText={setSearchQuery}
            value={searchQuery}
            platform="ios"
            containerStyle={styles.searchContainer}
            inputContainerStyle={styles.searchInput}
          />
          
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.filterContainer}
          >
            {statusFilters.map(filter => (
              <TouchableOpacity
                key={filter.value || 'all'}
                style={[
                  styles.filterChip,
                  selectedStatus === filter.value && styles.filterChipActive
                ]}
                onPress={() => setSelectedStatus(filter.value)}
              >
                <Text
                  style={[
                    styles.filterText,
                    selectedStatus === filter.value && styles.filterTextActive
                  ]}
                >
                  {filter.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        <FlatList
          data={filteredLeads}
          renderItem={renderLeadItem}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.leadsList}
          scrollEnabled={false}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Icon name="inbox" size={48} color="#bdc3c7" />
              <Text style={styles.emptyText}>No leads found</Text>
            </View>
          }
        />
      </ScrollView>

      <FAB
        title="Add Lead"
        placement="right"
        icon={{ name: 'add', color: 'white' }}
        color="#3498db"
        onPress={() => Alert.alert('Add Lead', 'Lead creation coming soon!')}
      />
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
  pipelineCard: {
    margin: 15,
    borderRadius: 10,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#2c3e50',
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  metric: {
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3498db',
  },
  metricLabel: {
    fontSize: 12,
    color: '#7f8c8d',
    marginTop: 5,
  },
  searchSection: {
    backgroundColor: 'white',
    paddingBottom: 10,
  },
  searchContainer: {
    backgroundColor: 'transparent',
    borderTopWidth: 0,
    borderBottomWidth: 0,
    paddingHorizontal: 10,
  },
  searchInput: {
    backgroundColor: '#f5f5f5',
  },
  filterContainer: {
    paddingHorizontal: 15,
    marginTop: 5,
  },
  filterChip: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#ecf0f1',
    marginRight: 10,
  },
  filterChipActive: {
    backgroundColor: '#3498db',
  },
  filterText: {
    color: '#7f8c8d',
    fontSize: 14,
  },
  filterTextActive: {
    color: 'white',
  },
  leadsList: {
    padding: 15,
  },
  leadItem: {
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
  leadHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  leadCompany: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  leadContact: {
    fontSize: 14,
    color: '#7f8c8d',
    marginTop: 2,
  },
  leadBadges: {
    flexDirection: 'row',
    gap: 5,
  },
  statusBadge: {
    borderRadius: 12,
    paddingHorizontal: 10,
    marginLeft: 5,
  },
  priorityBadge: {
    borderRadius: 12,
    paddingHorizontal: 10,
  },
  badgeText: {
    fontSize: 12,
    textTransform: 'capitalize',
  },
  leadFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  scoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  leadScore: {
    fontSize: 14,
    color: '#666',
  },
  leadDate: {
    fontSize: 12,
    color: '#95a5a6',
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

export default EnterpriseSales;