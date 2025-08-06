import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
  Platform
} from 'react-native';
import {
  Card,
  Badge,
  Icon,
  Avatar,
  ListItem,
  SearchBar,
  Header,
  Divider,
  Button
} from 'react-native-elements';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { LineChart, PieChart } from 'react-native-chart-kit';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');

interface Metrics {
  tickets: {
    open: number;
    resolved: number;
    avgResolutionTime: number;
    satisfactionScore: number;
  };
  articles: {
    total: number;
    views: number;
  };
  chat: {
    sessions: number;
    avgResponseTime: number;
  };
}

interface QuickAction {
  title: string;
  icon: string;
  color: string;
  screen: string;
  description: string;
}

const quickActions: QuickAction[] = [
  {
    title: 'New Ticket',
    icon: 'confirmation-number',
    color: '#4CAF50',
    screen: 'CreateTicket',
    description: 'Get help from support'
  },
  {
    title: 'Live Chat',
    icon: 'chat',
    color: '#2196F3',
    screen: 'LiveChat',
    description: 'Chat with AI assistant'
  },
  {
    title: 'Help Center',
    icon: 'help',
    color: '#FF9800',
    screen: 'HelpCenter',
    description: 'Browse articles'
  },
  {
    title: 'Tutorials',
    icon: 'school',
    color: '#9C27B0',
    screen: 'Tutorials',
    description: 'Video guides'
  }
];

export default function SupportScreen() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [recentTickets, setRecentTickets] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const navigation = useNavigation();

  useEffect(() => {
    fetchSupportData();
  }, []);

  const fetchSupportData = async () => {
    try {
      // Simulate API call
      setTimeout(() => {
        setMetrics({
          tickets: {
            open: 3,
            resolved: 24,
            avgResolutionTime: 18.5,
            satisfactionScore: 4.6
          },
          articles: {
            total: 156,
            views: 12543
          },
          chat: {
            sessions: 89,
            avgResponseTime: 1.2
          }
        });
        
        setRecentTickets([
          {
            id: 'TICKET-001',
            subject: 'Audio not processing',
            status: 'open',
            created: '2 hours ago',
            priority: 'high'
          },
          {
            id: 'TICKET-002',
            subject: 'Billing question',
            status: 'resolved',
            created: 'Yesterday',
            priority: 'medium'
          }
        ]);
        
        setLoading(false);
        setRefreshing(false);
      }, 1000);
    } catch (error) {
      console.error('Error fetching support data:', error);
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchSupportData();
  };

  const handleQuickAction = (action: QuickAction) => {
    navigation.navigate(action.screen as any);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return '#f44336';
      case 'in_progress':
        return '#ff9800';
      case 'resolved':
        return '#4caf50';
      default:
        return '#9e9e9e';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return '#f44336';
      case 'medium':
        return '#ff9800';
      case 'low':
        return '#4caf50';
      default:
        return '#9e9e9e';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <Header
        centerComponent={{ text: 'Support Center', style: styles.headerTitle }}
        rightComponent={
          <TouchableOpacity onPress={() => navigation.navigate('Notifications' as any)}>
            <Badge value="3" status="error" containerStyle={{ position: 'absolute', top: -4, right: -4 }} />
            <Icon name="notifications" color="#fff" />
          </TouchableOpacity>
        }
        backgroundColor="#2196F3"
      />

      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Search Bar */}
        <SearchBar
          placeholder="Search for help..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          platform={Platform.OS === 'ios' ? 'ios' : 'android'}
          containerStyle={styles.searchContainer}
          inputContainerStyle={styles.searchInputContainer}
        />

        {/* Quick Actions */}
        <View style={styles.quickActionsContainer}>
          <Text style={styles.sectionTitle}>How can we help?</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {quickActions.map((action, index) => (
              <TouchableOpacity
                key={index}
                style={styles.actionCard}
                onPress={() => handleQuickAction(action)}
              >
                <LinearGradient
                  colors={[action.color, action.color + 'DD']}
                  style={styles.actionGradient}
                >
                  <Icon
                    name={action.icon}
                    color="#fff"
                    size={32}
                    style={styles.actionIcon}
                  />
                  <Text style={styles.actionTitle}>{action.title}</Text>
                  <Text style={styles.actionDescription}>{action.description}</Text>
                </LinearGradient>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Metrics Overview */}
        {metrics && (
          <View style={styles.metricsContainer}>
            <Text style={styles.sectionTitle}>Support Overview</Text>
            
            <View style={styles.metricsGrid}>
              <Card containerStyle={styles.metricCard}>
                <View style={styles.metricContent}>
                  <Icon name="confirmation-number" color="#4CAF50" size={24} />
                  <Text style={styles.metricValue}>{metrics.tickets.open}</Text>
                  <Text style={styles.metricLabel}>Open Tickets</Text>
                </View>
              </Card>

              <Card containerStyle={styles.metricCard}>
                <View style={styles.metricContent}>
                  <Icon name="timer" color="#FF9800" size={24} />
                  <Text style={styles.metricValue}>{metrics.tickets.avgResolutionTime}h</Text>
                  <Text style={styles.metricLabel}>Avg Resolution</Text>
                </View>
              </Card>

              <Card containerStyle={styles.metricCard}>
                <View style={styles.metricContent}>
                  <Icon name="star" color="#FFC107" size={24} />
                  <Text style={styles.metricValue}>{metrics.tickets.satisfactionScore}</Text>
                  <Text style={styles.metricLabel}>Satisfaction</Text>
                </View>
              </Card>

              <Card containerStyle={styles.metricCard}>
                <View style={styles.metricContent}>
                  <Icon name="chat" color="#2196F3" size={24} />
                  <Text style={styles.metricValue}>{metrics.chat.sessions}</Text>
                  <Text style={styles.metricLabel}>Chat Sessions</Text>
                </View>
              </Card>
            </View>
          </View>
        )}

        {/* Recent Tickets */}
        <View style={styles.ticketsContainer}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recent Tickets</Text>
            <TouchableOpacity onPress={() => navigation.navigate('MyTickets' as any)}>
              <Text style={styles.viewAllText}>View All</Text>
            </TouchableOpacity>
          </View>

          {recentTickets.map((ticket, index) => (
            <ListItem
              key={ticket.id}
              bottomDivider
              onPress={() => navigation.navigate('TicketDetail', { ticketId: ticket.id } as any)}
            >
              <View style={[styles.statusIndicator, { backgroundColor: getStatusColor(ticket.status) }]} />
              <ListItem.Content>
                <ListItem.Title style={styles.ticketSubject}>{ticket.subject}</ListItem.Title>
                <View style={styles.ticketMeta}>
                  <Text style={styles.ticketId}>{ticket.id}</Text>
                  <Text style={styles.ticketTime}>{ticket.created}</Text>
                  <Badge
                    value={ticket.priority}
                    badgeStyle={{ backgroundColor: getPriorityColor(ticket.priority) }}
                  />
                </View>
              </ListItem.Content>
              <ListItem.Chevron />
            </ListItem>
          ))}
        </View>

        {/* Knowledge Base Stats */}
        <View style={styles.statsContainer}>
          <Text style={styles.sectionTitle}>Knowledge Base</Text>
          <Card containerStyle={styles.statsCard}>
            <LineChart
              data={{
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                  data: [20, 45, 28, 80, 99, 43, 50]
                }]
              }}
              width={width - 60}
              height={200}
              chartConfig={{
                backgroundColor: '#ffffff',
                backgroundGradientFrom: '#ffffff',
                backgroundGradientTo: '#ffffff',
                decimalPlaces: 0,
                color: (opacity = 1) => `rgba(33, 150, 243, ${opacity})`,
                labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                style: {
                  borderRadius: 16
                }
              }}
              style={{
                marginVertical: 8,
                borderRadius: 16
              }}
            />
            <Text style={styles.chartLabel}>Article Views This Week</Text>
          </Card>
        </View>

        {/* Quick Links */}
        <View style={styles.quickLinksContainer}>
          <Text style={styles.sectionTitle}>Quick Links</Text>
          
          <TouchableOpacity
            style={styles.quickLink}
            onPress={() => navigation.navigate('FAQ' as any)}
          >
            <Icon name="question-answer" color="#2196F3" />
            <Text style={styles.quickLinkText}>Frequently Asked Questions</Text>
            <Icon name="chevron-right" color="#999" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickLink}
            onPress={() => navigation.navigate('ContactSupport' as any)}
          >
            <Icon name="email" color="#2196F3" />
            <Text style={styles.quickLinkText}>Contact Support</Text>
            <Icon name="chevron-right" color="#999" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickLink}
            onPress={() => navigation.navigate('Feedback' as any)}
          >
            <Icon name="feedback" color="#2196F3" />
            <Text style={styles.quickLinkText}>Send Feedback</Text>
            <Icon name="chevron-right" color="#999" />
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5'
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center'
  },
  headerTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold'
  },
  searchContainer: {
    backgroundColor: 'transparent',
    borderTopWidth: 0,
    borderBottomWidth: 0,
    paddingHorizontal: 16,
    paddingTop: 16
  },
  searchInputContainer: {
    backgroundColor: '#fff',
    borderRadius: 8
  },
  quickActionsContainer: {
    paddingVertical: 16
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    paddingHorizontal: 16,
    marginBottom: 12
  },
  actionCard: {
    marginLeft: 16,
    marginRight: 8
  },
  actionGradient: {
    width: 120,
    height: 140,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center'
  },
  actionIcon: {
    marginBottom: 8
  },
  actionTitle: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
    marginBottom: 4
  },
  actionDescription: {
    color: '#fff',
    fontSize: 11,
    textAlign: 'center',
    opacity: 0.9
  },
  metricsContainer: {
    paddingVertical: 16
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 8
  },
  metricCard: {
    width: (width - 48) / 2,
    margin: 8,
    borderRadius: 8,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4
  },
  metricContent: {
    alignItems: 'center',
    padding: 8
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 8
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4
  },
  ticketsContainer: {
    paddingVertical: 16,
    backgroundColor: '#fff',
    marginTop: 8
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 8
  },
  viewAllText: {
    color: '#2196F3',
    fontSize: 14
  },
  statusIndicator: {
    width: 8,
    height: '100%',
    marginRight: 8
  },
  ticketSubject: {
    fontWeight: 'bold'
  },
  ticketMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4
  },
  ticketId: {
    fontSize: 12,
    color: '#666',
    marginRight: 12
  },
  ticketTime: {
    fontSize: 12,
    color: '#666',
    marginRight: 12
  },
  statsContainer: {
    paddingVertical: 16
  },
  statsCard: {
    borderRadius: 8,
    marginHorizontal: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4
  },
  chartLabel: {
    textAlign: 'center',
    marginTop: 8,
    color: '#666'
  },
  quickLinksContainer: {
    paddingVertical: 16,
    backgroundColor: '#fff',
    marginTop: 8,
    marginBottom: 24
  },
  quickLink: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0'
  },
  quickLinkText: {
    flex: 1,
    marginLeft: 16,
    fontSize: 16
  }
});