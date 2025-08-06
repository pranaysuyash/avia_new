import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  ScrollView,
  Text,
  TextInput,
  StyleSheet,
  Alert,
  TouchableOpacity,
  Dimensions,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
  FlatList,
  Platform,
  KeyboardAvoidingView,
  Keyboard,
  Image,
  Linking,
} from 'react-native';
import {
  Card,
  Button,
  IconButton,
  Chip,
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
  Provider as PaperProvider,
  DefaultTheme,
  DarkTheme,
  useTheme,
  Snackbar,
  TextInput as PaperTextInput,
  HelperText,
  FAB,
  Menu,
  AnimatedFAB,
} from 'react-native-paper';
import MaterialIcons from 'react-native-vector-icons/MaterialIcons';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import DocumentPicker from 'react-native-document-picker';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  withRepeat,
  interpolate,
  Easing,
  FadeIn,
  FadeOut,
  SlideInDown,
  SlideOutDown,
} from 'react-native-reanimated';
import { format, formatDistanceToNow, isToday, isYesterday } from 'date-fns';
import EmojiPicker from 'react-native-emoji-selector';
import Sound from 'react-native-sound';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface Agent {
  id: string;
  name: string;
  avatar?: string;
  status: 'online' | 'busy' | 'away' | 'offline';
  department: string;
  rating: number;
}

interface ChatMessage {
  id: string;
  type: 'text' | 'image' | 'file' | 'system';
  content: string;
  sender: 'user' | 'agent' | 'system';
  senderName?: string;
  timestamp: string;
  status: 'sending' | 'sent' | 'delivered' | 'read' | 'failed';
  attachments?: Attachment[];
  metadata?: any;
}

interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
}

interface QuickReply {
  id: string;
  text: string;
  action?: string;
}

interface ChatSession {
  id: string;
  status: 'waiting' | 'connected' | 'ended';
  agent?: Agent;
  startTime: string;
  endTime?: string;
  rating?: number;
  transcript?: ChatMessage[];
}

const LiveChatMobile: React.FC = () => {
  const theme = useTheme();
  const [chatSession, setChatSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [agentTyping, setAgentTyping] = useState(false);
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');
  
  // UI state
  const [emojiPickerVisible, setEmojiPickerVisible] = useState(false);
  const [attachmentMenuVisible, setAttachmentMenuVisible] = useState(false);
  const [chatInfoVisible, setChatInfoVisible] = useState(false);
  const [ratingDialogVisible, setRatingDialogVisible] = useState(false);
  const [quickRepliesVisible, setQuickRepliesVisible] = useState(true);
  const [snackbarVisible, setSnackbarVisible] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [sessionRating, setSessionRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  
  // Quick replies
  const [quickReplies, setQuickReplies] = useState<QuickReply[]>([
    { id: '1', text: 'Hello, I need help' },
    { id: '2', text: 'Technical issue' },
    { id: '3', text: 'Billing question' },
    { id: '4', text: 'Feature request' },
  ]);
  
  // Animation values
  const typingDot1 = useSharedValue(0);
  const typingDot2 = useSharedValue(0);
  const typingDot3 = useSharedValue(0);
  const fabExtended = useSharedValue(true);
  const messageScale = useSharedValue(1);
  
  // Refs
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  const soundRef = useRef<Sound | null>(null);

  useEffect(() => {
    // Initialize sound
    Sound.setCategory('Playback');
    
    return () => {
      if (soundRef.current) {
        soundRef.current.release();
      }
      if (chatSession && chatSession.status === 'connected') {
        endChat();
      }
    };
  }, []);

  useEffect(() => {
    // Animate typing indicator
    if (agentTyping) {
      typingDot1.value = withRepeat(
        withTiming(1, { duration: 600, easing: Easing.ease }),
        -1,
        true
      );
      typingDot2.value = withRepeat(
        withTiming(1, { duration: 600, easing: Easing.ease }, () => {
          typingDot2.value = withDelay(200, withTiming(0));
        }),
        -1,
        true
      );
      typingDot3.value = withRepeat(
        withTiming(1, { duration: 600, easing: Easing.ease }, () => {
          typingDot3.value = withDelay(400, withTiming(0));
        }),
        -1,
        true
      );
    } else {
      typingDot1.value = 0;
      typingDot2.value = 0;
      typingDot3.value = 0;
    }
  }, [agentTyping]);

  const startChat = async () => {
    try {
      setLoading(true);
      setConnectionStatus('connecting');
      
      // Simulate connection delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Create chat session
      const newSession: ChatSession = {
        id: `chat_${Date.now()}`,
        status: 'waiting',
        startTime: new Date().toISOString(),
      };
      
      setChatSession(newSession);
      setConnectionStatus('connected');
      
      // Add system message
      addMessage({
        id: `msg_${Date.now()}`,
        type: 'system',
        content: 'Connecting you to an agent...',
        sender: 'system',
        timestamp: new Date().toISOString(),
        status: 'sent',
      });
      
      // Simulate agent connection
      setTimeout(() => {
        const agent: Agent = {
          id: 'agent_1',
          name: 'Sarah Johnson',
          status: 'online',
          department: 'Technical Support',
          rating: 4.8,
        };
        
        setChatSession(prev => prev ? { ...prev, status: 'connected', agent } : null);
        
        addMessage({
          id: `msg_${Date.now()}`,
          type: 'text',
          content: 'Hello! I\'m Sarah from technical support. How can I help you today?',
          sender: 'agent',
          senderName: agent.name,
          timestamp: new Date().toISOString(),
          status: 'sent',
        });
        
        playNotificationSound();
      }, 3000);
    } catch (error) {
      Alert.alert('Error', 'Failed to start chat session');
      setConnectionStatus('disconnected');
    } finally {
      setLoading(false);
    }
  };

  const endChat = async () => {
    if (!chatSession) return;
    
    Alert.alert(
      'End Chat',
      'Are you sure you want to end this chat?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'End Chat',
          style: 'destructive',
          onPress: async () => {
            setChatSession(prev => prev ? { ...prev, status: 'ended', endTime: new Date().toISOString() } : null);
            setConnectionStatus('disconnected');
            setRatingDialogVisible(true);
          },
        },
      ]
    );
  };

  const sendMessage = async () => {
    if (!inputText.trim() || !chatSession || chatSession.status !== 'connected') return;
    
    const newMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      type: 'text',
      content: inputText.trim(),
      sender: 'user',
      timestamp: new Date().toISOString(),
      status: 'sending',
    };
    
    addMessage(newMessage);
    setInputText('');
    setQuickRepliesVisible(false);
    
    // Simulate message delivery
    setTimeout(() => {
      updateMessageStatus(newMessage.id, 'sent');
      setTimeout(() => {
        updateMessageStatus(newMessage.id, 'delivered');
        simulateAgentResponse();
      }, 500);
    }, 300);
  };

  const simulateAgentResponse = () => {
    setAgentTyping(true);
    
    setTimeout(() => {
      setAgentTyping(false);
      
      const responses = [
        'I understand your concern. Let me help you with that.',
        'Could you provide more details about the issue?',
        'I\'ve checked your account and found the issue. Let me fix that for you.',
        'That\'s a great question! Here\'s what I recommend...',
        'I\'m looking into this for you. One moment please.',
      ];
      
      const response = responses[Math.floor(Math.random() * responses.length)];
      
      addMessage({
        id: `msg_${Date.now()}`,
        type: 'text',
        content: response,
        sender: 'agent',
        senderName: chatSession?.agent?.name,
        timestamp: new Date().toISOString(),
        status: 'sent',
      });
      
      playNotificationSound();
      
      // Update quick replies based on context
      if (Math.random() > 0.5) {
        setQuickReplies([
          { id: '5', text: 'Yes, that helps' },
          { id: '6', text: 'I need more information' },
          { id: '7', text: 'Can you show me how?' },
          { id: '8', text: 'Thank you!' },
        ]);
        setQuickRepliesVisible(true);
      }
    }, 2000 + Math.random() * 2000);
  };

  const addMessage = (message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
    
    // Animate new message
    messageScale.value = 0.8;
    messageScale.value = withSpring(1);
    
    // Scroll to bottom
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const updateMessageStatus = (messageId: string, status: ChatMessage['status']) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, status } : msg
    ));
  };

  const sendQuickReply = (reply: QuickReply) => {
    setInputText(reply.text);
    setTimeout(() => sendMessage(), 100);
  };

  const pickImage = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.images],
        allowMultiSelection: false,
      });
      
      if (result && result.length > 0) {
        const file = result[0];
        const attachment: Attachment = {
          id: `att_${Date.now()}`,
          name: file.name || 'Image',
          type: file.type || 'image',
          size: file.size || 0,
          url: file.uri,
        };
        
        const newMessage: ChatMessage = {
          id: `msg_${Date.now()}`,
          type: 'image',
          content: 'Sent an image',
          sender: 'user',
          timestamp: new Date().toISOString(),
          status: 'sending',
          attachments: [attachment],
        };
        
        addMessage(newMessage);
        setAttachmentMenuVisible(false);
        
        // Simulate upload
        setTimeout(() => {
          updateMessageStatus(newMessage.id, 'sent');
        }, 1000);
      }
    } catch (error) {
      if (!DocumentPicker.isCancel(error)) {
        Alert.alert('Error', 'Failed to pick image');
      }
    }
  };

  const pickFile = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.allFiles],
        allowMultiSelection: false,
      });
      
      if (result && result.length > 0) {
        const file = result[0];
        const attachment: Attachment = {
          id: `att_${Date.now()}`,
          name: file.name || 'File',
          type: file.type || 'file',
          size: file.size || 0,
          url: file.uri,
        };
        
        const newMessage: ChatMessage = {
          id: `msg_${Date.now()}`,
          type: 'file',
          content: `Sent a file: ${file.name}`,
          sender: 'user',
          timestamp: new Date().toISOString(),
          status: 'sending',
          attachments: [attachment],
        };
        
        addMessage(newMessage);
        setAttachmentMenuVisible(false);
        
        // Simulate upload
        setTimeout(() => {
          updateMessageStatus(newMessage.id, 'sent');
        }, 1500);
      }
    } catch (error) {
      if (!DocumentPicker.isCancel(error)) {
        Alert.alert('Error', 'Failed to pick file');
      }
    }
  };

  const playNotificationSound = () => {
    try {
      soundRef.current = new Sound('notification.mp3', Sound.MAIN_BUNDLE, (error) => {
        if (!error) {
          soundRef.current?.play();
        }
      });
    } catch (error) {
      console.log('Failed to play sound');
    }
  };

  const submitRating = () => {
    if (sessionRating === 0) {
      Alert.alert('Rating Required', 'Please rate your chat experience');
      return;
    }
    
    // Submit rating
    showSnackbar('Thank you for your feedback!');
    setRatingDialogVisible(false);
    
    // Reset chat
    setChatSession(null);
    setMessages([]);
    setSessionRating(0);
    setFeedbackText('');
  };

  const showSnackbar = (message: string) => {
    setSnackbarMessage(message);
    setSnackbarVisible(true);
  };

  const formatMessageTime = (timestamp: string) => {
    const date = new Date(timestamp);
    
    if (isToday(date)) {
      return format(date, 'h:mm a');
    } else if (isYesterday(date)) {
      return `Yesterday ${format(date, 'h:mm a')}`;
    } else {
      return format(date, 'MMM dd, h:mm a');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getStatusIcon = (status: ChatMessage['status']) => {
    switch (status) {
      case 'sending': return 'schedule';
      case 'sent': return 'check';
      case 'delivered': return 'done';
      case 'read': return 'done-all';
      case 'failed': return 'error';
      default: return 'check';
    }
  };

  const typingDot1Style = useAnimatedStyle(() => ({
    opacity: typingDot1.value,
    transform: [{ translateY: interpolate(typingDot1.value, [0, 1], [0, -5]) }],
  }));

  const typingDot2Style = useAnimatedStyle(() => ({
    opacity: typingDot2.value,
    transform: [{ translateY: interpolate(typingDot2.value, [0, 1], [0, -5]) }],
  }));

  const typingDot3Style = useAnimatedStyle(() => ({
    opacity: typingDot3.value,
    transform: [{ translateY: interpolate(typingDot3.value, [0, 1], [0, -5]) }],
  }));

  const renderMessage = ({ item }: { item: ChatMessage }) => {
    const isUser = item.sender === 'user';
    const isSystem = item.sender === 'system';
    
    if (isSystem) {
      return (
        <Animated.View 
          entering={FadeIn} 
          style={styles.systemMessageContainer}
        >
          <View style={styles.systemMessage}>
            <MaterialIcons name="info" size={16} color={theme.colors.onSurfaceVariant} />
            <Caption style={{ marginLeft: 8 }}>{item.content}</Caption>
          </View>
        </Animated.View>
      );
    }
    
    return (
      <Animated.View 
        entering={SlideInDown.springify()} 
        style={[
          styles.messageContainer,
          isUser && styles.userMessageContainer,
        ]}
      >
        {!isUser && chatSession?.agent && (
          <Avatar.Text 
            size={32} 
            label={chatSession.agent.name.charAt(0)} 
            style={styles.agentAvatar}
          />
        )}
        
        <View style={styles.messageContent}>
          <Surface 
            style={[
              styles.messageBubble,
              isUser ? styles.userMessageBubble : styles.agentMessageBubble,
            ]} 
            elevation={1}
          >
            {!isUser && item.senderName && (
              <Text style={[styles.senderName, { color: theme.colors.primary }]}>
                {item.senderName}
              </Text>
            )}
            
            {item.type === 'text' && (
              <Text style={[
                styles.messageText,
                { color: isUser ? '#fff' : theme.colors.onSurface }
              ]}>
                {item.content}
              </Text>
            )}
            
            {item.type === 'image' && item.attachments?.[0] && (
              <TouchableOpacity onPress={() => {}}>
                <Image
                  source={{ uri: item.attachments[0].url }}
                  style={styles.messageImage}
                  resizeMode="cover"
                />
              </TouchableOpacity>
            )}
            
            {item.type === 'file' && item.attachments?.[0] && (
              <TouchableOpacity 
                style={styles.fileAttachment}
                onPress={() => {}}
              >
                <MaterialIcons name="attach-file" size={24} color={theme.colors.primary} />
                <View style={{ marginLeft: 8, flex: 1 }}>
                  <Text style={[styles.fileName, { color: theme.colors.onSurface }]} numberOfLines={1}>
                    {item.attachments[0].name}
                  </Text>
                  <Caption>{formatFileSize(item.attachments[0].size)}</Caption>
                </View>
              </TouchableOpacity>
            )}
            
            <View style={styles.messageFooter}>
              <Caption style={{ color: isUser ? 'rgba(255,255,255,0.7)' : theme.colors.onSurfaceVariant }}>
                {formatMessageTime(item.timestamp)}
              </Caption>
              {isUser && (
                <MaterialIcons 
                  name={getStatusIcon(item.status)} 
                  size={16} 
                  color={isUser ? 'rgba(255,255,255,0.7)' : theme.colors.onSurfaceVariant}
                  style={{ marginLeft: 4 }}
                />
              )}
            </View>
          </Surface>
        </View>
      </Animated.View>
    );
  };

  const renderTypingIndicator = () => {
    if (!agentTyping) return null;
    
    return (
      <Animated.View entering={FadeIn} exiting={FadeOut} style={styles.typingContainer}>
        {chatSession?.agent && (
          <Avatar.Text 
            size={32} 
            label={chatSession.agent.name.charAt(0)} 
            style={styles.agentAvatar}
          />
        )}
        <Surface style={styles.typingBubble} elevation={1}>
          <View style={styles.typingDots}>
            <Animated.View style={[styles.typingDot, typingDot1Style]} />
            <Animated.View style={[styles.typingDot, typingDot2Style]} />
            <Animated.View style={[styles.typingDot, typingDot3Style]} />
          </View>
        </Surface>
      </Animated.View>
    );
  };

  const renderQuickReplies = () => {
    if (!quickRepliesVisible || messages.length === 0) return null;
    
    return (
      <Animated.View entering={SlideInDown} exiting={SlideOutDown} style={styles.quickRepliesContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {quickReplies.map((reply) => (
            <Chip
              key={reply.id}
              mode="outlined"
              onPress={() => sendQuickReply(reply)}
              style={styles.quickReplyChip}
            >
              {reply.text}
            </Chip>
          ))}
        </ScrollView>
      </Animated.View>
    );
  };

  const renderChatInfo = () => {
    if (!chatSession?.agent) return null;
    
    return (
      <Portal>
        <Dialog visible={chatInfoVisible} onDismiss={() => setChatInfoVisible(false)}>
          <Dialog.Title>Chat Information</Dialog.Title>
          <Dialog.Content>
            <View style={styles.agentInfo}>
              <Avatar.Text 
                size={64} 
                label={chatSession.agent.name.charAt(0)} 
                style={{ backgroundColor: theme.colors.primary }}
              />
              <View style={{ marginLeft: 16, flex: 1 }}>
                <Title>{chatSession.agent.name}</Title>
                <Caption>{chatSession.agent.department}</Caption>
                <View style={styles.agentRating}>
                  <MaterialIcons name="star" size={16} color="#FFB800" />
                  <Text style={{ marginLeft: 4, color: theme.colors.onSurface }}>
                    {chatSession.agent.rating}
                  </Text>
                </View>
              </View>
            </View>
            
            <Divider style={{ marginVertical: 16 }} />
            
            <View style={styles.chatStats}>
              <View style={styles.statItem}>
                <MaterialIcons name="schedule" size={20} color={theme.colors.onSurfaceVariant} />
                <Caption style={{ marginLeft: 8 }}>
                  Started {formatDistanceToNow(new Date(chatSession.startTime), { addSuffix: true })}
                </Caption>
              </View>
              <View style={styles.statItem}>
                <MaterialIcons name="chat" size={20} color={theme.colors.onSurfaceVariant} />
                <Caption style={{ marginLeft: 8 }}>
                  {messages.filter(m => m.sender !== 'system').length} messages
                </Caption>
              </View>
            </View>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setChatInfoVisible(false)}>Close</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    );
  };

  const renderRatingDialog = () => (
    <Portal>
      <Dialog visible={ratingDialogVisible} onDismiss={() => {}}>
        <Dialog.Title>Rate Your Experience</Dialog.Title>
        <Dialog.Content>
          <Paragraph>How was your chat experience?</Paragraph>
          
          <View style={styles.ratingStars}>
            {[1, 2, 3, 4, 5].map((rating) => (
              <TouchableOpacity
                key={rating}
                onPress={() => setSessionRating(rating)}
              >
                <MaterialIcons
                  name="star"
                  size={40}
                  color={rating <= sessionRating ? '#FFB800' : '#E0E0E0'}
                  style={{ marginHorizontal: 4 }}
                />
              </TouchableOpacity>
            ))}
          </View>
          
          <PaperTextInput
            label="Additional feedback (optional)"
            value={feedbackText}
            onChangeText={setFeedbackText}
            mode="outlined"
            multiline
            numberOfLines={3}
            style={{ marginTop: 16 }}
          />
        </Dialog.Content>
        <Dialog.Actions>
          <Button onPress={() => setRatingDialogVisible(false)}>Skip</Button>
          <Button mode="contained" onPress={submitRating}>Submit</Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );

  if (!chatSession) {
    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
        <PaperProvider>
          <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
            <View style={styles.welcomeContainer}>
              <MaterialCommunityIcons 
                name="chat-processing" 
                size={64} 
                color={theme.colors.primary} 
              />
              
              <Title style={{ marginTop: 24, textAlign: 'center' }}>
                Welcome to Live Chat Support
              </Title>
              
              <Paragraph style={{ marginTop: 8, textAlign: 'center', paddingHorizontal: 32 }}>
                Connect with our support team for instant help with your questions
              </Paragraph>
              
              <View style={styles.features}>
                <View style={styles.featureItem}>
                  <MaterialIcons name="access-time" size={24} color={theme.colors.primary} />
                  <Caption style={{ marginTop: 4 }}>Average wait: 30s</Caption>
                </View>
                <View style={styles.featureItem}>
                  <MaterialIcons name="support-agent" size={24} color={theme.colors.primary} />
                  <Caption style={{ marginTop: 4 }}>Expert agents</Caption>
                </View>
                <View style={styles.featureItem}>
                  <MaterialIcons name="security" size={24} color={theme.colors.primary} />
                  <Caption style={{ marginTop: 4 }}>Secure chat</Caption>
                </View>
              </View>
              
              <Button
                mode="contained"
                onPress={startChat}
                loading={loading}
                style={styles.startChatButton}
                icon="chat"
              >
                Start Live Chat
              </Button>
              
              <Caption style={{ marginTop: 16 }}>
                Available Mon-Fri, 9 AM - 6 PM EST
              </Caption>
            </View>
          </SafeAreaView>
        </PaperProvider>
      </GestureHandlerRootView>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PaperProvider>
        <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={{ flex: 1 }}
            keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 25}
          >
            {/* Header */}
            <Surface style={styles.header} elevation={2}>
              <View style={styles.headerContent}>
                <View style={styles.headerLeft}>
                  {chatSession.agent && (
                    <>
                      <Avatar.Text 
                        size={40} 
                        label={chatSession.agent.name.charAt(0)} 
                      />
                      <View style={{ marginLeft: 12 }}>
                        <Text style={[styles.agentName, { color: theme.colors.onSurface }]}>
                          {chatSession.agent.name}
                        </Text>
                        <View style={styles.agentStatus}>
                          <View style={[
                            styles.statusDot, 
                            { backgroundColor: connectionStatus === 'connected' ? '#4CAF50' : '#757575' }
                          ]} />
                          <Caption style={{ marginLeft: 4 }}>
                            {connectionStatus === 'connected' ? 'Online' : 'Connecting...'}
                          </Caption>
                        </View>
                      </View>
                    </>
                  )}
                </View>
                
                <View style={styles.headerActions}>
                  <IconButton
                    icon="information"
                    onPress={() => setChatInfoVisible(true)}
                  />
                  <IconButton
                    icon="close"
                    onPress={endChat}
                  />
                </View>
              </View>
            </Surface>
            
            {/* Messages */}
            <FlatList
              ref={flatListRef}
              data={messages}
              renderItem={renderMessage}
              keyExtractor={(item) => item.id}
              contentContainerStyle={styles.messagesList}
              onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
              ListFooterComponent={renderTypingIndicator}
            />
            
            {/* Quick Replies */}
            {renderQuickReplies()}
            
            {/* Input Area */}
            <Surface style={styles.inputContainer} elevation={2}>
              <View style={styles.inputRow}>
                <Menu
                  visible={attachmentMenuVisible}
                  onDismiss={() => setAttachmentMenuVisible(false)}
                  anchor={
                    <IconButton
                      icon="attachment"
                      onPress={() => setAttachmentMenuVisible(true)}
                    />
                  }
                >
                  <Menu.Item
                    onPress={pickImage}
                    title="Send Image"
                    icon="image"
                  />
                  <Menu.Item
                    onPress={pickFile}
                    title="Send File"
                    icon="file"
                  />
                </Menu>
                
                <TextInput
                  ref={inputRef}
                  style={[styles.textInput, { color: theme.colors.onSurface }]}
                  value={inputText}
                  onChangeText={setInputText}
                  placeholder="Type a message..."
                  placeholderTextColor={theme.colors.onSurfaceVariant}
                  multiline
                  maxLength={1000}
                  onFocus={() => {
                    setQuickRepliesVisible(false);
                    fabExtended.value = false;
                  }}
                  onBlur={() => {
                    fabExtended.value = true;
                  }}
                />
                
                <IconButton
                  icon="emoticon-happy-outline"
                  onPress={() => setEmojiPickerVisible(true)}
                />
                
                <IconButton
                  icon="send"
                  onPress={sendMessage}
                  disabled={!inputText.trim()}
                />
              </View>
              
              {inputText.length > 900 && (
                <Caption style={{ alignSelf: 'flex-end', marginRight: 16, marginTop: -8 }}>
                  {inputText.length}/1000
                </Caption>
              )}
            </Surface>
            
            {/* Emoji Picker */}
            <Modal
              visible={emojiPickerVisible}
              onRequestClose={() => setEmojiPickerVisible(false)}
              animationType="slide"
            >
              <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.background }}>
                <View style={styles.emojiHeader}>
                  <Title>Select Emoji</Title>
                  <IconButton
                    icon="close"
                    onPress={() => setEmojiPickerVisible(false)}
                  />
                </View>
                <EmojiPicker
                  onEmojiSelected={(emoji: string) => {
                    setInputText(prev => prev + emoji);
                    setEmojiPickerVisible(false);
                  }}
                  showSearchBar={false}
                  showHistory={false}
                  showSectionTitles={true}
                  columns={8}
                />
              </SafeAreaView>
            </Modal>
          </KeyboardAvoidingView>
          
          {/* Dialogs */}
          {renderChatInfo()}
          {renderRatingDialog()}
          
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
  welcomeContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  features: {
    flexDirection: 'row',
    marginTop: 32,
    marginBottom: 32,
  },
  featureItem: {
    alignItems: 'center',
    marginHorizontal: 16,
  },
  startChatButton: {
    paddingHorizontal: 32,
    paddingVertical: 8,
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  agentName: {
    fontSize: 16,
    fontWeight: '500',
  },
  agentStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  headerActions: {
    flexDirection: 'row',
  },
  messagesList: {
    padding: 16,
    paddingBottom: 8,
  },
  messageContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-end',
  },
  userMessageContainer: {
    justifyContent: 'flex-end',
  },
  agentAvatar: {
    marginRight: 8,
  },
  messageContent: {
    maxWidth: '80%',
  },
  messageBubble: {
    padding: 12,
    borderRadius: 16,
  },
  userMessageBubble: {
    backgroundColor: '#2196F3',
    borderBottomRightRadius: 4,
  },
  agentMessageBubble: {
    backgroundColor: '#f5f5f5',
    borderBottomLeftRadius: 4,
  },
  senderName: {
    fontSize: 12,
    fontWeight: '500',
    marginBottom: 4,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  messageImage: {
    width: 200,
    height: 200,
    borderRadius: 8,
    marginBottom: 8,
  },
  fileAttachment: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    backgroundColor: 'rgba(0,0,0,0.05)',
    borderRadius: 8,
    marginBottom: 8,
  },
  fileName: {
    fontSize: 14,
    fontWeight: '500',
  },
  messageFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  systemMessageContainer: {
    alignItems: 'center',
    marginVertical: 16,
  },
  systemMessage: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: 'rgba(0,0,0,0.05)',
    borderRadius: 16,
  },
  typingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  typingBubble: {
    padding: 12,
    borderRadius: 16,
    backgroundColor: '#f5f5f5',
    borderBottomLeftRadius: 4,
  },
  typingDots: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#757575',
    marginHorizontal: 2,
  },
  quickRepliesContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  quickReplyChip: {
    marginRight: 8,
  },
  inputContainer: {
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingVertical: 8,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    maxHeight: 100,
    paddingHorizontal: 8,
    paddingVertical: 8,
  },
  agentInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  agentRating: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  chatStats: {
    gap: 12,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingStars: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginVertical: 24,
  },
  emojiHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
});

export default LiveChatMobile;