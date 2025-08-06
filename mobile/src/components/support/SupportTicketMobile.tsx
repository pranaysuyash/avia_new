import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  ScrollView,
  Text,
  TextInput,
  StyleSheet,
  Alert,
  Modal,
  TouchableOpacity,
  Dimensions,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
  FlatList,
  Platform,
  KeyboardAvoidingView,
  Keyboard,
  RefreshControl,
  Image,
} from 'react-native';
import {
  Card,
  Button,
  IconButton,
  ProgressBar,
  Chip,
  FAB,
  Portal,
  Dialog,
  Paragraph,
  Title,
  Subheading,
  Caption,
  Surface,
  Divider,
  List,
  Avatar,
  Badge,
  Menu,
  Provider as PaperProvider,
  DefaultTheme,
  DarkTheme,
  useTheme,
  Snackbar,
  Searchbar,
  RadioButton,
  TextInput as PaperTextInput,
  HelperText,
} from 'react-native-paper';
import MaterialIcons from 'react-native-vector-icons/MaterialIcons';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import DocumentPicker from 'react-native-document-picker';
import RNFS from 'react-native-fs';
import { GestureHandlerRootView, Swipeable } from 'react-native-gesture-handler';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  interpolate,
  runOnJS,
} from 'react-native-reanimated';
import { format, formatDistanceToNow } from 'date-fns';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface Ticket {
  id: string;
  subject: string;
  description: string;
  status: 'open' | 'in_progress' | 'waiting' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: string;
  created_at: string;
  updated_at: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  assigned_to?: string;
  assigned_name?: string;
  tags: string[];
  attachments: Attachment[];
  messages: Message[];
  satisfaction_rating?: number;
}

interface Message {
  id: string;
  ticket_id: string;
  sender_type: 'customer' | 'agent' | 'system';
  sender_name: string;
  content: string;
  created_at: string;
  attachments: Attachment[];
  is_internal: boolean;
}

interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
}

interface Category {
  id: string;
  name: string;
  icon: string;
  color: string;
}

const categories: Category[] = [
  { id: 'technical', name: 'Technical Issue', icon: 'bug-report', color: '#F44336' },
  { id: 'billing', name: 'Billing', icon: 'credit-card', color: '#4CAF50' },
  { id: 'feature', name: 'Feature Request', icon: 'lightbulb', color: '#FF9800' },
  { id: 'account', name: 'Account', icon: 'account-circle', color: '#2196F3' },
  { id: 'general', name: 'General Inquiry', icon: 'help', color: '#9C27B0' },
];

const SupportTicketMobile: React.FC = () => {
  const theme = useTheme();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<'all' | 'open' | 'closed'>('all');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'priority'>('newest');
  
  // Create ticket form state
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('general');
  const [selectedPriority, setSelectedPriority] = useState<'low' | 'medium' | 'high' | 'urgent'>('medium');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  
  // Reply state
  const [replyText, setReplyText] = useState('');
  const [replyModalVisible, setReplyModalVisible] = useState(false);
  const [isInternalNote, setIsInternalNote] = useState(false);
  
  // UI state
  const [filterMenuVisible, setFilterMenuVisible] = useState(false);
  const [sortMenuVisible, setSortMenuVisible] = useState(false);
  const [ticketDetailsVisible, setTicketDetailsVisible] = useState(false);
  const [snackbarVisible, setSnackbarVisible] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  
  // Animation values
  const ticketScale = useSharedValue(1);
  const fabScale = useSharedValue(1);
  const keyboardHeight = useSharedValue(0);
  
  // Refs
  const scrollViewRef = useRef<ScrollView>(null);
  const replyInputRef = useRef<TextInput>(null);

  useEffect(() => {
    loadTickets();
    
    const keyboardWillShow = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow',
      (e) => {
        keyboardHeight.value = withSpring(e.endCoordinates.height);
      }
    );
    
    const keyboardWillHide = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide',
      () => {
        keyboardHeight.value = withSpring(0);
      }
    );
    
    return () => {
      keyboardWillShow.remove();
      keyboardWillHide.remove();
    };
  }, []);

  const loadTickets = async () => {
    try {
      setLoading(true);
      
      // Mock tickets data
      const mockTickets: Ticket[] = [
        {
          id: 'ticket_1',
          subject: 'Cannot export video in 4K resolution',
          description: 'When I try to export my video in 4K, the app crashes...',
          status: 'open',
          priority: 'high',
          category: 'technical',
          created_at: new Date(Date.now() - 3600000).toISOString(),
          updated_at: new Date(Date.now() - 1800000).toISOString(),
          customer_id: 'user_123',
          customer_name: 'John Doe',
          customer_email: 'john.doe@example.com',
          tags: ['export', 'crash', '4k'],
          attachments: [],
          messages: [
            {
              id: 'msg_1',
              ticket_id: 'ticket_1',
              sender_type: 'customer',
              sender_name: 'John Doe',
              content: 'When I try to export my video in 4K, the app crashes. This happens every time I select the 4K option.',
              created_at: new Date(Date.now() - 3600000).toISOString(),
              attachments: [],
              is_internal: false,
            },
          ],
        },
        {
          id: 'ticket_2',
          subject: 'Billing issue - duplicate charge',
          description: 'I was charged twice for my subscription...',
          status: 'in_progress',
          priority: 'urgent',
          category: 'billing',
          created_at: new Date(Date.now() - 7200000).toISOString(),
          updated_at: new Date(Date.now() - 3600000).toISOString(),
          customer_id: 'user_456',
          customer_name: 'Jane Smith',
          customer_email: 'jane.smith@example.com',
          assigned_to: 'agent_1',
          assigned_name: 'Support Agent',
          tags: ['billing', 'refund'],
          attachments: [],
          messages: [
            {
              id: 'msg_2',
              ticket_id: 'ticket_2',
              sender_type: 'customer',
              sender_name: 'Jane Smith',
              content: 'I was charged twice for my subscription this month. Please refund the duplicate charge.',
              created_at: new Date(Date.now() - 7200000).toISOString(),
              attachments: [],
              is_internal: false,
            },
            {
              id: 'msg_3',
              ticket_id: 'ticket_2',
              sender_type: 'agent',
              sender_name: 'Support Agent',
              content: 'I apologize for the inconvenience. I\'m looking into this issue and will process your refund shortly.',
              created_at: new Date(Date.now() - 3600000).toISOString(),
              attachments: [],
              is_internal: false,
            },
          ],
        },
        {
          id: 'ticket_3',
          subject: 'Feature request - Dark mode',
          description: 'It would be great to have a dark mode option...',
          status: 'resolved',
          priority: 'low',
          category: 'feature',
          created_at: new Date(Date.now() - 86400000).toISOString(),
          updated_at: new Date(Date.now() - 43200000).toISOString(),
          customer_id: 'user_789',
          customer_name: 'Bob Johnson',
          customer_email: 'bob.johnson@example.com',
          tags: ['feature-request', 'ui'],
          attachments: [],
          messages: [],
          satisfaction_rating: 5,
        },
      ];
      
      setTickets(mockTickets);
    } catch (error) {
      Alert.alert('Error', 'Failed to load tickets');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadTickets();
    setRefreshing(false);
  };

  const createTicket = async () => {
    if (!subject.trim() || !description.trim()) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }
    
    try {
      setLoading(true);
      
      // Mock ticket creation
      const newTicket: Ticket = {
        id: `ticket_${Date.now()}`,
        subject: subject.trim(),
        description: description.trim(),
        status: 'open',
        priority: selectedPriority,
        category: selectedCategory,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        customer_id: 'current_user',
        customer_name: 'Current User',
        customer_email: 'user@example.com',
        tags: [],
        attachments: attachments,
        messages: [
          {
            id: `msg_${Date.now()}`,
            ticket_id: `ticket_${Date.now()}`,
            sender_type: 'customer',
            sender_name: 'Current User',
            content: description.trim(),
            created_at: new Date().toISOString(),
            attachments: attachments,
            is_internal: false,
          },
        ],
      };
      
      setTickets([newTicket, ...tickets]);
      setCreateModalVisible(false);
      resetCreateForm();
      showSnackbar('Ticket created successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to create ticket');
    } finally {
      setLoading(false);
    }
  };

  const sendReply = async () => {
    if (!replyText.trim() || !selectedTicket) return;
    
    try {
      setLoading(true);
      
      // Mock reply
      const newMessage: Message = {
        id: `msg_${Date.now()}`,
        ticket_id: selectedTicket.id,
        sender_type: 'customer',
        sender_name: 'Current User',
        content: replyText.trim(),
        created_at: new Date().toISOString(),
        attachments: [],
        is_internal: isInternalNote,
      };
      
      // Update ticket with new message
      const updatedTicket = {
        ...selectedTicket,
        messages: [...selectedTicket.messages, newMessage],
        updated_at: new Date().toISOString(),
      };
      
      setSelectedTicket(updatedTicket);
      setTickets(tickets.map(t => t.id === selectedTicket.id ? updatedTicket : t));
      
      setReplyText('');
      setReplyModalVisible(false);
      showSnackbar('Reply sent successfully');
      
      // Scroll to bottom to show new message
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    } catch (error) {
      Alert.alert('Error', 'Failed to send reply');
    } finally {
      setLoading(false);
    }
  };

  const updateTicketStatus = async (ticketId: string, newStatus: Ticket['status']) => {
    try {
      setTickets(tickets.map(t => 
        t.id === ticketId 
          ? { ...t, status: newStatus, updated_at: new Date().toISOString() }
          : t
      ));
      
      if (selectedTicket?.id === ticketId) {
        setSelectedTicket({ ...selectedTicket, status: newStatus });
      }
      
      showSnackbar(`Ticket status updated to ${newStatus}`);
    } catch (error) {
      Alert.alert('Error', 'Failed to update ticket status');
    }
  };

  const pickAttachments = async () => {
    try {
      const results = await DocumentPicker.pick({
        type: [DocumentPicker.types.allFiles],
        allowMultiSelection: true,
      });
      
      const newAttachments: Attachment[] = results.map((file) => ({
        id: `attachment_${Date.now()}_${Math.random()}`,
        name: file.name || 'Unknown',
        type: file.type || 'unknown',
        size: file.size || 0,
        url: file.uri,
      }));
      
      setAttachments([...attachments, ...newAttachments]);
    } catch (error) {
      if (!DocumentPicker.isCancel(error)) {
        Alert.alert('Error', 'Failed to pick attachments');
      }
    }
  };

  const removeAttachment = (attachmentId: string) => {
    setAttachments(attachments.filter(a => a.id !== attachmentId));
  };

  const resetCreateForm = () => {
    setSubject('');
    setDescription('');
    setSelectedCategory('general');
    setSelectedPriority('medium');
    setAttachments([]);
  };

  const showSnackbar = (message: string) => {
    setSnackbarMessage(message);
    setSnackbarVisible(true);
  };

  const getStatusColor = (status: Ticket['status']) => {
    switch (status) {
      case 'open': return '#2196F3';
      case 'in_progress': return '#FF9800';
      case 'waiting': return '#9C27B0';
      case 'resolved': return '#4CAF50';
      case 'closed': return '#757575';
      default: return theme.colors.primary;
    }
  };

  const getStatusIcon = (status: Ticket['status']) => {
    switch (status) {
      case 'open': return 'radio-button-unchecked';
      case 'in_progress': return 'pending';
      case 'waiting': return 'hourglass-empty';
      case 'resolved': return 'check-circle';
      case 'closed': return 'lock';
      default: return 'help';
    }
  };

  const getPriorityColor = (priority: Ticket['priority']) => {
    switch (priority) {
      case 'low': return '#4CAF50';
      case 'medium': return '#FF9800';
      case 'high': return '#F44336';
      case 'urgent': return '#D32F2F';
      default: return theme.colors.primary;
    }
  };

  const getPriorityIcon = (priority: Ticket['priority']) => {
    switch (priority) {
      case 'low': return 'arrow-downward';
      case 'medium': return 'remove';
      case 'high': return 'arrow-upward';
      case 'urgent': return 'priority-high';
      default: return 'help';
    }
  };

  const getFilteredTickets = () => {
    let filtered = tickets;
    
    // Apply status filter
    if (filter === 'open') {
      filtered = filtered.filter(t => ['open', 'in_progress', 'waiting'].includes(t.status));
    } else if (filter === 'closed') {
      filtered = filtered.filter(t => ['resolved', 'closed'].includes(t.status));
    }
    
    // Apply search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(t => 
        t.subject.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query) ||
        t.customer_name.toLowerCase().includes(query) ||
        t.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'oldest':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'priority':
          const priorityOrder = { urgent: 0, high: 1, medium: 2, low: 3 };
          return priorityOrder[a.priority] - priorityOrder[b.priority];
        default:
          return 0;
      }
    });
    
    return filtered;
  };

  const renderTicketItem = ({ item }: { item: Ticket }) => {
    const category = categories.find(c => c.id === item.category);
    
    const rightSwipeActions = () => (
      <TouchableOpacity
        style={[styles.swipeAction, { backgroundColor: '#4CAF50' }]}
        onPress={() => updateTicketStatus(item.id, 'resolved')}
      >
        <MaterialIcons name="check" size={24} color="#fff" />
        <Text style={styles.swipeActionText}>Resolve</Text>
      </TouchableOpacity>
    );
    
    const leftSwipeActions = () => (
      <TouchableOpacity
        style={[styles.swipeAction, { backgroundColor: '#F44336' }]}
        onPress={() => updateTicketStatus(item.id, 'closed')}
      >
        <MaterialIcons name="close" size={24} color="#fff" />
        <Text style={styles.swipeActionText}>Close</Text>
      </TouchableOpacity>
    );
    
    return (
      <Swipeable
        renderRightActions={item.status !== 'resolved' && item.status !== 'closed' ? rightSwipeActions : undefined}
        renderLeftActions={item.status !== 'closed' ? leftSwipeActions : undefined}
      >
        <TouchableOpacity
          onPress={() => {
            setSelectedTicket(item);
            setTicketDetailsVisible(true);
          }}
        >
          <Surface style={styles.ticketCard} elevation={1}>
            <View style={styles.ticketHeader}>
              <View style={styles.ticketStatus}>
                <MaterialIcons 
                  name={getStatusIcon(item.status)} 
                  size={20} 
                  color={getStatusColor(item.status)} 
                />
                <Caption style={{ color: getStatusColor(item.status), marginLeft: 4 }}>
                  {item.status.replace('_', ' ').toUpperCase()}
                </Caption>
              </View>
              
              <View style={styles.ticketPriority}>
                <MaterialIcons 
                  name={getPriorityIcon(item.priority)} 
                  size={16} 
                  color={getPriorityColor(item.priority)} 
                />
                <Caption style={{ color: getPriorityColor(item.priority), marginLeft: 2 }}>
                  {item.priority.toUpperCase()}
                </Caption>
              </View>
            </View>
            
            <Text style={[styles.ticketSubject, { color: theme.colors.onSurface }]} numberOfLines={2}>
              {item.subject}
            </Text>
            
            <View style={styles.ticketMeta}>
              <View style={styles.ticketCategory}>
                <MaterialIcons 
                  name={category?.icon || 'help'} 
                  size={16} 
                  color={category?.color || theme.colors.primary} 
                />
                <Caption style={{ marginLeft: 4 }}>{category?.name}</Caption>
              </View>
              
              <Caption>{formatDistanceToNow(new Date(item.updated_at), { addSuffix: true })}</Caption>
            </View>
            
            {item.tags.length > 0 && (
              <View style={styles.ticketTags}>
                {item.tags.slice(0, 3).map((tag) => (
                  <Chip key={tag} mode="outlined" compact textStyle={{ fontSize: 10 }}>
                    {tag}
                  </Chip>
                ))}
                {item.tags.length > 3 && (
                  <Caption>+{item.tags.length - 3} more</Caption>
                )}
              </View>
            )}
            
            {item.assigned_to && (
              <View style={styles.ticketAssignee}>
                <Avatar.Text size={24} label={item.assigned_name?.charAt(0) || 'A'} />
                <Caption style={{ marginLeft: 8 }}>Assigned to {item.assigned_name}</Caption>
              </View>
            )}
          </Surface>
        </TouchableOpacity>
      </Swipeable>
    );
  };

  const renderTicketDetails = () => {
    if (!selectedTicket) return null;
    
    const category = categories.find(c => c.id === selectedTicket.category);
    
    return (
      <Modal
        visible={ticketDetailsVisible}
        onRequestClose={() => setTicketDetailsVisible(false)}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.colors.background }]}>
          {/* Header */}
          <Surface style={styles.detailsHeader} elevation={2}>
            <View style={styles.detailsHeaderContent}>
              <IconButton
                icon="arrow-back"
                onPress={() => setTicketDetailsVisible(false)}
              />
              <View style={styles.detailsHeaderInfo}>
                <Text style={[styles.ticketId, { color: theme.colors.onSurfaceVariant }]}>
                  #{selectedTicket.id}
                </Text>
                <View style={styles.ticketStatus}>
                  <MaterialIcons 
                    name={getStatusIcon(selectedTicket.status)} 
                    size={16} 
                    color={getStatusColor(selectedTicket.status)} 
                  />
                  <Caption style={{ color: getStatusColor(selectedTicket.status), marginLeft: 2 }}>
                    {selectedTicket.status.replace('_', ' ').toUpperCase()}
                  </Caption>
                </View>
              </View>
              <Menu
                visible={false}
                onDismiss={() => {}}
                anchor={
                  <IconButton icon="dots-vertical" onPress={() => {}} />
                }
              >
                <Menu.Item onPress={() => {}} title="Change Status" />
                <Menu.Item onPress={() => {}} title="Assign Agent" />
                <Menu.Item onPress={() => {}} title="Add Tags" />
              </Menu>
            </View>
          </Surface>
          
          {/* Content */}
          <ScrollView
            ref={scrollViewRef}
            style={styles.detailsContent}
            contentContainerStyle={{ paddingBottom: 80 }}
          >
            {/* Ticket Info */}
            <Surface style={styles.detailsSection} elevation={1}>
              <Title>{selectedTicket.subject}</Title>
              
              <View style={styles.detailsInfo}>
                <View style={styles.detailsInfoRow}>
                  <MaterialIcons name="person" size={20} color={theme.colors.onSurfaceVariant} />
                  <View style={{ marginLeft: 12, flex: 1 }}>
                    <Text style={{ color: theme.colors.onSurface }}>{selectedTicket.customer_name}</Text>
                    <Caption>{selectedTicket.customer_email}</Caption>
                  </View>
                </View>
                
                <View style={styles.detailsInfoRow}>
                  <MaterialIcons 
                    name={category?.icon || 'help'} 
                    size={20} 
                    color={category?.color || theme.colors.primary} 
                  />
                  <Text style={{ marginLeft: 12, color: theme.colors.onSurface }}>
                    {category?.name}
                  </Text>
                </View>
                
                <View style={styles.detailsInfoRow}>
                  <MaterialIcons 
                    name={getPriorityIcon(selectedTicket.priority)} 
                    size={20} 
                    color={getPriorityColor(selectedTicket.priority)} 
                  />
                  <Text style={{ marginLeft: 12, color: theme.colors.onSurface }}>
                    {selectedTicket.priority.charAt(0).toUpperCase() + selectedTicket.priority.slice(1)} Priority
                  </Text>
                </View>
                
                <View style={styles.detailsInfoRow}>
                  <MaterialIcons name="access-time" size={20} color={theme.colors.onSurfaceVariant} />
                  <View style={{ marginLeft: 12 }}>
                    <Text style={{ color: theme.colors.onSurface }}>
                      Created {format(new Date(selectedTicket.created_at), 'MMM dd, yyyy h:mm a')}
                    </Text>
                    <Caption>
                      Updated {formatDistanceToNow(new Date(selectedTicket.updated_at), { addSuffix: true })}
                    </Caption>
                  </View>
                </View>
              </View>
            </Surface>
            
            {/* Messages */}
            <Surface style={styles.detailsSection} elevation={1}>
              <Subheading style={{ marginBottom: 16 }}>Conversation</Subheading>
              
              {selectedTicket.messages.map((message) => (
                <View 
                  key={message.id} 
                  style={[
                    styles.messageItem,
                    message.sender_type === 'customer' && styles.customerMessage,
                    message.is_internal && styles.internalMessage,
                  ]}
                >
                  <View style={styles.messageHeader}>
                    <Avatar.Text 
                      size={32} 
                      label={message.sender_name.charAt(0)} 
                      style={{ 
                        backgroundColor: message.sender_type === 'customer' 
                          ? theme.colors.primary 
                          : theme.colors.secondary 
                      }}
                    />
                    <View style={{ marginLeft: 12, flex: 1 }}>
                      <Text style={[styles.messageSender, { color: theme.colors.onSurface }]}>
                        {message.sender_name}
                      </Text>
                      <Caption>
                        {format(new Date(message.created_at), 'MMM dd, h:mm a')}
                        {message.is_internal && ' • Internal Note'}
                      </Caption>
                    </View>
                  </View>
                  
                  <Text style={[styles.messageContent, { color: theme.colors.onSurface }]}>
                    {message.content}
                  </Text>
                  
                  {message.attachments.length > 0 && (
                    <View style={styles.messageAttachments}>
                      {message.attachments.map((attachment) => (
                        <Chip 
                          key={attachment.id} 
                          mode="outlined" 
                          icon="attachment"
                          compact
                          textStyle={{ fontSize: 12 }}
                        >
                          {attachment.name}
                        </Chip>
                      ))}
                    </View>
                  )}
                </View>
              ))}
            </Surface>
            
            {/* Satisfaction Rating (if resolved) */}
            {selectedTicket.status === 'resolved' && selectedTicket.satisfaction_rating && (
              <Surface style={styles.detailsSection} elevation={1}>
                <Subheading>Customer Satisfaction</Subheading>
                <View style={styles.satisfactionRating}>
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <MaterialIcons
                      key={rating}
                      name="star"
                      size={32}
                      color={rating <= selectedTicket.satisfaction_rating! ? '#FFB800' : '#E0E0E0'}
                    />
                  ))}
                </View>
              </Surface>
            )}
          </ScrollView>
          
          {/* Reply Button */}
          <FAB
            style={[styles.replyFab, { backgroundColor: theme.colors.primary }]}
            icon="reply"
            onPress={() => setReplyModalVisible(true)}
          />
        </SafeAreaView>
      </Modal>
    );
  };

  const renderCreateModal = () => (
    <Modal
      visible={createModalVisible}
      onRequestClose={() => setCreateModalVisible(false)}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.colors.background }]}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={{ flex: 1 }}
        >
          <Surface style={styles.modalHeader} elevation={2}>
            <Title>Create New Ticket</Title>
            <IconButton
              icon="close"
              onPress={() => setCreateModalVisible(false)}
            />
          </Surface>
          
          <ScrollView style={styles.modalContent}>
            <PaperTextInput
              label="Subject"
              value={subject}
              onChangeText={setSubject}
              mode="outlined"
              style={styles.input}
            />
            
            <PaperTextInput
              label="Description"
              value={description}
              onChangeText={setDescription}
              mode="outlined"
              multiline
              numberOfLines={6}
              style={styles.input}
            />
            
            <View style={styles.formSection}>
              <Subheading style={{ marginBottom: 8 }}>Category</Subheading>
              <View style={styles.categoryGrid}>
                {categories.map((category) => (
                  <TouchableOpacity
                    key={category.id}
                    style={[
                      styles.categoryItem,
                      selectedCategory === category.id && styles.selectedCategoryItem,
                      { borderColor: selectedCategory === category.id ? category.color : '#E0E0E0' }
                    ]}
                    onPress={() => setSelectedCategory(category.id)}
                  >
                    <MaterialIcons 
                      name={category.icon} 
                      size={24} 
                      color={selectedCategory === category.id ? category.color : theme.colors.onSurfaceVariant} 
                    />
                    <Caption>{category.name}</Caption>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
            
            <View style={styles.formSection}>
              <Subheading style={{ marginBottom: 8 }}>Priority</Subheading>
              <RadioButton.Group
                onValueChange={(value) => setSelectedPriority(value as Ticket['priority'])}
                value={selectedPriority}
              >
                <View style={styles.priorityOptions}>
                  {(['low', 'medium', 'high', 'urgent'] as const).map((priority) => (
                    <TouchableOpacity
                      key={priority}
                      style={styles.priorityOption}
                      onPress={() => setSelectedPriority(priority)}
                    >
                      <RadioButton value={priority} />
                      <MaterialIcons 
                        name={getPriorityIcon(priority)} 
                        size={20} 
                        color={getPriorityColor(priority)} 
                      />
                      <Text style={{ marginLeft: 8, color: theme.colors.onSurface }}>
                        {priority.charAt(0).toUpperCase() + priority.slice(1)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </RadioButton.Group>
            </View>
            
            <View style={styles.formSection}>
              <Subheading style={{ marginBottom: 8 }}>Attachments</Subheading>
              <Button
                mode="outlined"
                icon="attachment"
                onPress={pickAttachments}
                style={{ marginBottom: 8 }}
              >
                Add Attachments
              </Button>
              
              {attachments.map((attachment) => (
                <Chip
                  key={attachment.id}
                  mode="outlined"
                  onClose={() => removeAttachment(attachment.id)}
                  style={{ marginBottom: 4 }}
                >
                  {attachment.name}
                </Chip>
              ))}
            </View>
          </ScrollView>
          
          <Surface style={styles.modalFooter} elevation={2}>
            <Button
              mode="contained"
              onPress={createTicket}
              loading={loading}
              disabled={loading || !subject.trim() || !description.trim()}
              style={styles.modalButton}
            >
              Create Ticket
            </Button>
          </Surface>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </Modal>
  );

  const renderReplyModal = () => (
    <Modal
      visible={replyModalVisible}
      onRequestClose={() => setReplyModalVisible(false)}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.colors.background }]}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={{ flex: 1 }}
        >
          <Surface style={styles.modalHeader} elevation={2}>
            <Title>Reply to Ticket</Title>
            <IconButton
              icon="close"
              onPress={() => setReplyModalVisible(false)}
            />
          </Surface>
          
          <ScrollView style={styles.modalContent}>
            <PaperTextInput
              ref={replyInputRef}
              label="Your Reply"
              value={replyText}
              onChangeText={setReplyText}
              mode="outlined"
              multiline
              numberOfLines={8}
              style={styles.input}
            />
            
            <View style={styles.replyOptions}>
              <List.Item
                title="Internal Note"
                description="Only visible to support agents"
                right={() => (
                  <Switch
                    value={isInternalNote}
                    onValueChange={setIsInternalNote}
                  />
                )}
              />
            </View>
          </ScrollView>
          
          <Surface style={styles.modalFooter} elevation={2}>
            <Button
              mode="contained"
              onPress={sendReply}
              loading={loading}
              disabled={loading || !replyText.trim()}
              style={styles.modalButton}
              icon="send"
            >
              Send Reply
            </Button>
          </Surface>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </Modal>
  );

  const fabAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: fabScale.value }],
  }));

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PaperProvider>
        <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
          {/* Header */}
          <Surface style={styles.header} elevation={2}>
            <Title>Support Tickets</Title>
            <View style={styles.headerActions}>
              <Menu
                visible={filterMenuVisible}
                onDismiss={() => setFilterMenuVisible(false)}
                anchor={
                  <IconButton
                    icon="filter-list"
                    onPress={() => setFilterMenuVisible(true)}
                  />
                }
              >
                <Menu.Item
                  onPress={() => {
                    setFilter('all');
                    setFilterMenuVisible(false);
                  }}
                  title="All Tickets"
                  icon={filter === 'all' ? 'check' : undefined}
                />
                <Menu.Item
                  onPress={() => {
                    setFilter('open');
                    setFilterMenuVisible(false);
                  }}
                  title="Open Tickets"
                  icon={filter === 'open' ? 'check' : undefined}
                />
                <Menu.Item
                  onPress={() => {
                    setFilter('closed');
                    setFilterMenuVisible(false);
                  }}
                  title="Closed Tickets"
                  icon={filter === 'closed' ? 'check' : undefined}
                />
              </Menu>
              
              <Menu
                visible={sortMenuVisible}
                onDismiss={() => setSortMenuVisible(false)}
                anchor={
                  <IconButton
                    icon="sort"
                    onPress={() => setSortMenuVisible(true)}
                  />
                }
              >
                <Menu.Item
                  onPress={() => {
                    setSortBy('newest');
                    setSortMenuVisible(false);
                  }}
                  title="Newest First"
                  icon={sortBy === 'newest' ? 'check' : undefined}
                />
                <Menu.Item
                  onPress={() => {
                    setSortBy('oldest');
                    setSortMenuVisible(false);
                  }}
                  title="Oldest First"
                  icon={sortBy === 'oldest' ? 'check' : undefined}
                />
                <Menu.Item
                  onPress={() => {
                    setSortBy('priority');
                    setSortMenuVisible(false);
                  }}
                  title="By Priority"
                  icon={sortBy === 'priority' ? 'check' : undefined}
                />
              </Menu>
            </View>
          </Surface>
          
          {/* Search Bar */}
          <View style={styles.searchContainer}>
            <Searchbar
              placeholder="Search tickets..."
              onChangeText={setSearchQuery}
              value={searchQuery}
              style={styles.searchBar}
            />
          </View>
          
          {/* Statistics */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.statsContainer}>
            <Surface style={styles.statCard} elevation={1}>
              <Text style={[styles.statValue, { color: theme.colors.primary }]}>
                {tickets.filter(t => t.status === 'open').length}
              </Text>
              <Caption>Open</Caption>
            </Surface>
            
            <Surface style={styles.statCard} elevation={1}>
              <Text style={[styles.statValue, { color: '#FF9800' }]}>
                {tickets.filter(t => t.status === 'in_progress').length}
              </Text>
              <Caption>In Progress</Caption>
            </Surface>
            
            <Surface style={styles.statCard} elevation={1}>
              <Text style={[styles.statValue, { color: '#4CAF50' }]}>
                {tickets.filter(t => t.status === 'resolved').length}
              </Text>
              <Caption>Resolved</Caption>
            </Surface>
            
            <Surface style={styles.statCard} elevation={1}>
              <Text style={[styles.statValue, { color: '#757575' }]}>
                {tickets.filter(t => t.status === 'closed').length}
              </Text>
              <Caption>Closed</Caption>
            </Surface>
          </ScrollView>
          
          {/* Tickets List */}
          <FlatList
            data={getFilteredTickets()}
            renderItem={renderTicketItem}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.ticketsList}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                colors={[theme.colors.primary]}
              />
            }
            ListEmptyComponent={
              <View style={styles.emptyState}>
                <MaterialIcons name="confirmation-number" size={64} color={theme.colors.onSurfaceVariant} />
                <Subheading style={{ color: theme.colors.onSurfaceVariant, marginTop: 16 }}>
                  No tickets found
                </Subheading>
                <Caption>Create a new ticket to get support</Caption>
              </View>
            }
          />
          
          {/* FAB */}
          <Animated.View style={fabAnimatedStyle}>
            <FAB
              style={[styles.fab, { backgroundColor: theme.colors.primary }]}
              icon="plus"
              onPress={() => setCreateModalVisible(true)}
              onPressIn={() => {
                fabScale.value = withSpring(0.9);
              }}
              onPressOut={() => {
                fabScale.value = withSpring(1);
              }}
            />
          </Animated.View>
          
          {/* Modals */}
          {renderTicketDetails()}
          {renderCreateModal()}
          {renderReplyModal()}
          
          {/* Snackbar */}
          <Snackbar
            visible={snackbarVisible}
            onDismiss={() => setSnackbarVisible(false)}
            duration={3000}
          >
            {snackbarMessage}
          </Snackbar>
        </SafeAreaView>
      </PaperProvider>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  headerActions: {
    flexDirection: 'row',
  },
  searchContainer: {
    padding: 16,
    paddingTop: 8,
  },
  searchBar: {
    elevation: 0,
  },
  statsContainer: {
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  statCard: {
    padding: 16,
    marginRight: 12,
    borderRadius: 8,
    alignItems: 'center',
    minWidth: 80,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  ticketsList: {
    padding: 16,
    paddingTop: 8,
  },
  ticketCard: {
    padding: 16,
    marginBottom: 12,
    borderRadius: 8,
  },
  ticketHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  ticketStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ticketPriority: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ticketSubject: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  ticketMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  ticketCategory: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ticketTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginBottom: 8,
  },
  ticketAssignee: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 100,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  modalFooter: {
    padding: 16,
  },
  modalButton: {
    paddingVertical: 4,
  },
  input: {
    marginBottom: 16,
  },
  formSection: {
    marginBottom: 24,
  },
  categoryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  categoryItem: {
    padding: 12,
    borderWidth: 2,
    borderRadius: 8,
    alignItems: 'center',
    width: (screenWidth - 48) / 3,
  },
  selectedCategoryItem: {
    backgroundColor: 'rgba(33, 150, 243, 0.1)',
  },
  priorityOptions: {
    gap: 8,
  },
  priorityOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
  },
  detailsHeader: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  detailsHeaderContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  detailsHeaderInfo: {
    flex: 1,
    marginLeft: 8,
  },
  ticketId: {
    fontSize: 12,
  },
  detailsContent: {
    flex: 1,
  },
  detailsSection: {
    padding: 16,
    margin: 16,
    marginBottom: 8,
    borderRadius: 8,
  },
  detailsInfo: {
    marginTop: 16,
    gap: 12,
  },
  detailsInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  messageItem: {
    marginBottom: 16,
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  customerMessage: {
    backgroundColor: '#e3f2fd',
  },
  internalMessage: {
    backgroundColor: '#fff3e0',
    borderWidth: 1,
    borderColor: '#ffb74d',
    borderStyle: 'dashed',
  },
  messageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  messageSender: {
    fontWeight: '500',
  },
  messageContent: {
    marginTop: 8,
    lineHeight: 20,
  },
  messageAttachments: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: 8,
  },
  satisfactionRating: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 16,
  },
  replyFab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
  replyOptions: {
    marginTop: 16,
  },
  swipeAction: {
    justifyContent: 'center',
    alignItems: 'center',
    width: 80,
    height: '100%',
  },
  swipeActionText: {
    color: '#fff',
    fontSize: 12,
    marginTop: 4,
  },
});

export default SupportTicketMobile;