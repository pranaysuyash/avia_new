import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  Modal,
  StyleSheet,
  Alert,
  Dimensions,
  Platform,
  KeyboardAvoidingView,
  StatusBar,
  ActivityIndicator,
  FlatList
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  runOnJS
} from 'react-native-reanimated';
import { BlurView } from '@react-native-community/blur';
import LinearGradient from 'react-native-linear-gradient';

// Types for collaborative editing
interface User {
  user_id: string;
  username: string;
  email: string;
  avatar?: string;
  color: string;
  role: string;
  joined_at: string;
  last_seen: string;
  is_typing: boolean;
  cursor_position: number;
  selection_start?: number;
  selection_end?: number;
}

interface Comment {
  comment_id: string;
  user_id: string;
  username: string;
  content: string;
  position: number;
  selection_start: number;
  selection_end: number;
  timestamp: string;
  replies: Comment[];
  resolved: boolean;
  tags: string[];
}

interface Operation {
  operation_id: string;
  user_id: string;
  operation_type: 'insert' | 'delete' | 'replace' | 'cursor_move' | 'selection';
  position: number;
  content?: string;
  length?: number;
  timestamp: string;
  metadata?: Record<string, any>;
}

interface Document {
  document_id: string;
  content: string;
  version: number;
  created_at: string;
  updated_at: string;
  created_by: string;
  title: string;
  metadata?: Record<string, any>;
}

interface CollaborativeEditorProps {
  documentId: string;
  currentUser: User;
  onSave?: (content: string, version: number) => void;
  initialContent?: string;
  readOnly?: boolean;
}

const { width, height } = Dimensions.get('window');

const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
  documentId,
  currentUser,
  onSave,
  initialContent = '',
  readOnly = false
}) => {
  // State management
  const [document, setDocument] = useState<Document | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [content, setContent] = useState<string>(initialContent);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved');

  // UI state
  const [showUsers, setShowUsers] = useState(false);
  const [showComments, setShowComments] = useState(false);
  const [selectedText, setSelectedText] = useState<{start: number, end: number} | null>(null);
  const [commentModalVisible, setCommentModalVisible] = useState(false);
  const [newCommentText, setNewCommentText] = useState('');
  const [notification, setNotification] = useState<{message: string, type: 'success' | 'error' | 'info'} | null>(null);

  // Refs
  const textInputRef = useRef<TextInput>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const operationQueue = useRef<Operation[]>([]);

  // Animation values
  const headerAnimation = useSharedValue(1);
  const usersAnimation = useSharedValue(0);
  const commentsAnimation = useSharedValue(0);
  const notificationAnimation = useSharedValue(0);

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    const wsUrl = `ws://localhost:8000/api/v1/collaborate/${documentId}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      setIsConnected(true);
      setIsLoading(false);
      console.log('Connected to collaborative editing session');
      
      // Send user info
      ws.send(JSON.stringify({
        type: 'user_join',
        user: currentUser
      }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      console.log('Disconnected from collaborative editing session');
      
      // Try to reconnect after 3 seconds
      setTimeout(() => {
        if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
          connectWebSocket();
        }
      }, 3000);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      showNotification('Connection error occurred', 'error');
    };
    
    wsRef.current = ws;
  }, [documentId, currentUser]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'initial_state':
        setDocument(data.document);
        setUsers(data.users || []);
        setComments(data.comments || []);
        setContent(data.document.content || '');
        break;
        
      case 'user_joined':
        setUsers(prev => [...prev.filter(u => u.user_id !== data.user.user_id), data.user]);
        showNotification(`${data.user.username} joined the session`, 'info');
        break;
        
      case 'user_left':
        setUsers(prev => prev.filter(u => u.user_id !== data.user_id));
        showNotification(`${data.username} left the session`, 'info');
        break;
        
      case 'document_updated':
        applyOperation(data.operation);
        setDocument(prev => prev ? { ...prev, version: data.document_version } : null);
        break;
        
      case 'cursor_update':
        updateUserCursor(data.user_id, data.cursor_position, data.selection_start, data.selection_end);
        break;
        
      case 'user_typing':
        updateUserTypingStatus(data.user_id, true);
        break;
        
      case 'user_idle':
        updateUserTypingStatus(data.user_id, false);
        break;
        
      case 'comment_added':
        setComments(prev => [...prev, data.comment]);
        break;
        
      case 'comment_updated':
        setComments(prev => prev.map(c => 
          c.comment_id === data.comment_id 
            ? { ...c, resolved: data.resolved }
            : c
        ));
        break;
        
      case 'save_status':
        setSaveStatus(data.status === 'saved' ? 'saved' : 'saving');
        if (data.status === 'saved') {
          showNotification('Document auto-saved', 'success');
        }
        break;
        
      case 'error':
        showNotification(data.message, 'error');
        break;
    }
  }, []);

  // Show notification
  const showNotification = useCallback((message: string, type: 'success' | 'error' | 'info') => {
    setNotification({ message, type });
    notificationAnimation.value = withSpring(1, { damping: 15 });
    
    setTimeout(() => {
      notificationAnimation.value = withTiming(0);
      setTimeout(() => setNotification(null), 300);
    }, 3000);
  }, []);

  // Apply operation to content
  const applyOperation = useCallback((operation: Operation) => {
    setContent(prev => {
      switch (operation.operation_type) {
        case 'insert':
          return prev.slice(0, operation.position) + 
                 operation.content + 
                 prev.slice(operation.position);
                 
        case 'delete':
          return prev.slice(0, operation.position) + 
                 prev.slice(operation.position + (operation.length || 0));
                 
        case 'replace':
          return prev.slice(0, operation.position) + 
                 operation.content + 
                 prev.slice(operation.position + (operation.length || 0));
                 
        default:
          return prev;
      }
    });
  }, []);

  // Update user cursor position
  const updateUserCursor = useCallback((userId: string, position: number, selectionStart?: number, selectionEnd?: number) => {
    setUsers(prev => prev.map(user => 
      user.user_id === userId 
        ? { ...user, cursor_position: position, selection_start: selectionStart, selection_end: selectionEnd }
        : user
    ));
  }, []);

  // Update user typing status
  const updateUserTypingStatus = useCallback((userId: string, isTyping: boolean) => {
    setUsers(prev => prev.map(user => 
      user.user_id === userId 
        ? { ...user, is_typing: isTyping }
        : user
    ));
  }, []);

  // Send operation to server
  const sendOperation = useCallback((operation: Partial<Operation>) => {
    if (!wsRef.current || !isConnected) return;
    
    const fullOperation: Operation = {
      operation_id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      user_id: currentUser.user_id,
      timestamp: new Date().toISOString(),
      ...operation
    } as Operation;
    
    wsRef.current.send(JSON.stringify({
      type: 'operation',
      operation: fullOperation
    }));
  }, [isConnected, currentUser.user_id]);

  // Handle text changes
  const handleTextChange = useCallback((newContent: string) => {
    if (readOnly) return;
    
    const oldContent = content;
    
    // Find the change
    let changeStart = 0;
    let changeEnd = oldContent.length;
    
    // Find start of change
    while (changeStart < Math.min(oldContent.length, newContent.length) &&
           oldContent[changeStart] === newContent[changeStart]) {
      changeStart++;
    }
    
    // Find end of change
    while (changeEnd > changeStart && 
           changeStart < newContent.length &&
           oldContent[changeEnd - 1] === newContent[newContent.length - (oldContent.length - changeEnd + 1)]) {
      changeEnd--;
    }
    
    // Determine operation type
    if (newContent.length > oldContent.length) {
      // Insert operation
      const insertedText = newContent.slice(changeStart, changeStart + (newContent.length - oldContent.length));
      sendOperation({
        operation_type: 'insert',
        position: changeStart,
        content: insertedText
      });
    } else if (newContent.length < oldContent.length) {
      // Delete operation
      sendOperation({
        operation_type: 'delete',
        position: changeStart,
        length: oldContent.length - newContent.length
      });
    } else if (changeStart < changeEnd) {
      // Replace operation
      const replacedText = newContent.slice(changeStart, changeEnd);
      sendOperation({
        operation_type: 'replace',
        position: changeStart,
        content: replacedText,
        length: changeEnd - changeStart
      });
    }
    
    setContent(newContent);
    setSaveStatus('unsaved');
  }, [content, readOnly, sendOperation]);

  // Add comment
  const handleAddComment = useCallback(() => {
    if (!selectedText || !newCommentText.trim()) return;
    
    const commentData = {
      content: newCommentText,
      position: selectedText.start,
      selection_start: selectedText.start,
      selection_end: selectedText.end,
      tags: []
    };
    
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({
        type: 'add_comment',
        comment: commentData
      }));
    }
    
    setNewCommentText('');
    setCommentModalVisible(false);
    setSelectedText(null);
  }, [selectedText, newCommentText]);

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // Animated styles
  const headerAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: headerAnimation.value }],
    opacity: headerAnimation.value
  }));

  const notificationAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ 
      translateY: interpolate(notificationAnimation.value, [0, 1], [-100, 0])
    }],
    opacity: notificationAnimation.value
  }));

  const usersAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ 
      translateX: interpolate(usersAnimation.value, [0, 1], [width, 0])
    }]
  }));

  const commentsAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ 
      translateY: interpolate(commentsAnimation.value, [0, 1], [height, 0])
    }]
  }));

  // Toggle panels
  const toggleUsers = () => {
    usersAnimation.value = withSpring(showUsers ? 0 : 1);
    setShowUsers(!showUsers);
  };

  const toggleComments = () => {
    commentsAnimation.value = withSpring(showComments ? 0 : 1);
    setShowComments(!showComments);
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Connecting to collaborative session...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1F2937" />
      
      <KeyboardAvoidingView 
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header */}
        <Animated.View style={[styles.header, headerAnimatedStyle]}>
          <LinearGradient
            colors={['#667eea', '#764ba2']}
            style={styles.headerGradient}
          >
            <View style={styles.headerContent}>
              <View style={styles.titleSection}>
                <Text style={styles.title}>
                  {document?.title || 'Collaborative Document'}
                </Text>
                <View style={styles.statusRow}>
                  <View style={[styles.statusBadge, { 
                    backgroundColor: isConnected ? '#10B981' : '#F59E0B' 
                  }]}>
                    <Text style={styles.statusText}>
                      {isConnected ? 'Connected' : 'Disconnected'}
                    </Text>
                  </View>
                  <View style={[styles.statusBadge, { 
                    backgroundColor: saveStatus === 'saved' ? '#10B981' : '#F59E0B' 
                  }]}>
                    <Text style={styles.statusText}>
                      {saveStatus === 'saved' ? 'Saved' : saveStatus === 'saving' ? 'Saving...' : 'Unsaved'}
                    </Text>
                  </View>
                </View>
              </View>

              <View style={styles.headerActions}>
                <TouchableOpacity onPress={toggleUsers} style={styles.headerButton}>
                  <Text style={styles.headerButtonText}>👥 {users.length}</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={toggleComments} style={styles.headerButton}>
                  <Text style={styles.headerButtonText}>💬 {comments.filter(c => !c.resolved).length}</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* User Avatars */}
            <ScrollView horizontal style={styles.userAvatars} showsHorizontalScrollIndicator={false}>
              {users.slice(0, 5).map(user => (
                <View key={user.user_id} style={[styles.avatar, { borderColor: user.color }]}>
                  {user.is_typing && <View style={styles.typingIndicator} />}
                  <Text style={styles.avatarText}>
                    {user.username.charAt(0).toUpperCase()}
                  </Text>
                </View>
              ))}
              {users.length > 5 && (
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>+{users.length - 5}</Text>
                </View>
              )}
            </ScrollView>
          </LinearGradient>
        </Animated.View>

        {/* Main Editor */}
        <View style={styles.editorContainer}>
          <TextInput
            ref={textInputRef}
            style={styles.textEditor}
            value={content}
            onChangeText={handleTextChange}
            multiline
            textAlignVertical="top"
            placeholder="Start typing to collaborate in real-time..."
            placeholderTextColor="#9CA3AF"
            editable={!readOnly}
            onSelectionChange={(event) => {
              const { start, end } = event.nativeEvent.selection;
              if (start !== end) {
                setSelectedText({ start, end });
              } else {
                setSelectedText(null);
              }
            }}
          />

          {/* Comment Overlay */}
          {selectedText && (
            <TouchableOpacity 
              style={styles.commentButton}
              onPress={() => setCommentModalVisible(true)}
            >
              <Text style={styles.commentButtonText}>💬 Add Comment</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Users Panel */}
        {showUsers && (
          <Animated.View style={[styles.usersPanel, usersAnimatedStyle]}>
            <BlurView style={styles.panelBlur} blurType="dark" blurAmount={10}>
              <View style={styles.panelHeader}>
                <Text style={styles.panelTitle}>Collaborators ({users.length})</Text>
                <TouchableOpacity onPress={toggleUsers} style={styles.closeButton}>
                  <Text style={styles.closeButtonText}>×</Text>
                </TouchableOpacity>
              </View>
              <FlatList
                data={users}
                keyExtractor={(item) => item.user_id}
                renderItem={({ item: user }) => (
                  <View style={styles.userItem}>
                    <View style={[styles.userAvatar, { borderColor: user.color }]}>
                      <Text style={styles.userAvatarText}>
                        {user.username.charAt(0).toUpperCase()}
                      </Text>
                      {user.is_typing && <View style={styles.userTypingDot} />}
                    </View>
                    <View style={styles.userInfo}>
                      <Text style={styles.userName}>{user.username}</Text>
                      <Text style={styles.userRole}>{user.role} • {user.is_typing ? 'Typing...' : 'Active'}</Text>
                    </View>
                    {user.user_id === currentUser.user_id && (
                      <View style={styles.youBadge}>
                        <Text style={styles.youBadgeText}>You</Text>
                      </View>
                    )}
                  </View>
                )}
              />
            </BlurView>
          </Animated.View>
        )}

        {/* Comments Panel */}
        {showComments && (
          <Animated.View style={[styles.commentsPanel, commentsAnimatedStyle]}>
            <BlurView style={styles.panelBlur} blurType="dark" blurAmount={10}>
              <View style={styles.panelHeader}>
                <Text style={styles.panelTitle}>
                  Comments ({comments.filter(c => !c.resolved).length})
                </Text>
                <TouchableOpacity onPress={toggleComments} style={styles.closeButton}>
                  <Text style={styles.closeButtonText}>×</Text>
                </TouchableOpacity>
              </View>
              <FlatList
                data={comments.filter(comment => !comment.resolved)}
                keyExtractor={(item) => item.comment_id}
                renderItem={({ item: comment }) => (
                  <View style={styles.commentItem}>
                    <View style={styles.commentHeader}>
                      <Text style={styles.commentAuthor}>{comment.username}</Text>
                      <Text style={styles.commentTime}>
                        {new Date(comment.timestamp).toLocaleTimeString()}
                      </Text>
                    </View>
                    <Text style={styles.commentContent}>{comment.content}</Text>
                    <TouchableOpacity style={styles.resolveButton}>
                      <Text style={styles.resolveButtonText}>Resolve</Text>
                    </TouchableOpacity>
                  </View>
                )}
              />
            </BlurView>
          </Animated.View>
        )}

        {/* Comment Modal */}
        <Modal
          visible={commentModalVisible}
          animationType="slide"
          transparent
          onRequestClose={() => setCommentModalVisible(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.commentModal}>
              <Text style={styles.modalTitle}>Add Comment</Text>
              <TextInput
                style={styles.commentInput}
                value={newCommentText}
                onChangeText={setNewCommentText}
                multiline
                placeholder="Enter your comment..."
                placeholderTextColor="#9CA3AF"
                autoFocus
              />
              <View style={styles.modalButtons}>
                <TouchableOpacity 
                  style={[styles.modalButton, styles.cancelButton]}
                  onPress={() => setCommentModalVisible(false)}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[styles.modalButton, styles.addButton]}
                  onPress={handleAddComment}
                  disabled={!newCommentText.trim()}
                >
                  <Text style={styles.addButtonText}>Add Comment</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>

        {/* Notification */}
        {notification && (
          <Animated.View style={[styles.notification, notificationAnimatedStyle]}>
            <LinearGradient
              colors={
                notification.type === 'success' 
                  ? ['#10B981', '#059669'] 
                  : notification.type === 'error'
                  ? ['#EF4444', '#DC2626']
                  : ['#3B82F6', '#2563EB']
              }
              style={styles.notificationGradient}
            >
              <Text style={styles.notificationText}>{notification.message}</Text>
            </LinearGradient>
          </Animated.View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1F2937'
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1F2937'
  },
  loadingText: {
    color: '#FFFFFF',
    fontSize: 16,
    marginTop: 16,
    fontWeight: '500'
  },
  header: {
    backgroundColor: 'transparent'
  },
  headerGradient: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12
  },
  titleSection: {
    flex: 1
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8
  },
  statusRow: {
    flexDirection: 'row',
    gap: 8
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12
  },
  statusText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600'
  },
  headerActions: {
    flexDirection: 'row',
    gap: 8
  },
  headerButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16
  },
  headerButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600'
  },
  userAvatars: {
    flexDirection: 'row'
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderWidth: 2,
    borderColor: '#FFFFFF',
    marginRight: 8,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative'
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold'
  },
  typingIndicator: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#10B981'
  },
  editorContainer: {
    flex: 1,
    position: 'relative'
  },
  textEditor: {
    flex: 1,
    padding: 20,
    fontSize: 16,
    lineHeight: 24,
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace'
  },
  commentButton: {
    position: 'absolute',
    top: 20,
    right: 20,
    backgroundColor: '#3B82F6',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5
  },
  commentButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600'
  },
  usersPanel: {
    position: 'absolute',
    top: 120,
    right: 0,
    width: width * 0.8,
    height: height - 200,
    borderTopLeftRadius: 24,
    borderBottomLeftRadius: 24,
    overflow: 'hidden'
  },
  commentsPanel: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: height * 0.6,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    overflow: 'hidden'
  },
  panelBlur: {
    flex: 1
  },
  panelHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.2)'
  },
  panelTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF'
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center'
  },
  closeButtonText: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: 'bold'
  },
  userItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)'
  },
  userAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    position: 'relative'
  },
  userAvatarText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold'
  },
  userTypingDot: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#10B981'
  },
  userInfo: {
    flex: 1
  },
  userName: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2
  },
  userRole: {
    color: '#D1D5DB',
    fontSize: 14
  },
  youBadge: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12
  },
  youBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600'
  },
  commentItem: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)'
  },
  commentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  commentAuthor: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600'
  },
  commentTime: {
    color: '#D1D5DB',
    fontSize: 12
  },
  commentContent: {
    color: '#FFFFFF',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12
  },
  resolveButton: {
    alignSelf: 'flex-start',
    backgroundColor: '#10B981',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16
  },
  resolveButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600'
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center'
  },
  commentModal: {
    backgroundColor: '#374151',
    borderRadius: 24,
    padding: 24,
    width: width * 0.9,
    maxWidth: 400
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 16,
    textAlign: 'center'
  },
  commentInput: {
    backgroundColor: '#4B5563',
    borderRadius: 12,
    padding: 12,
    color: '#FFFFFF',
    fontSize: 16,
    minHeight: 100,
    textAlignVertical: 'top',
    marginBottom: 16
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center'
  },
  cancelButton: {
    backgroundColor: '#6B7280'
  },
  cancelButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600'
  },
  addButton: {
    backgroundColor: '#3B82F6'
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600'
  },
  notification: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 50 : 30,
    left: 20,
    right: 20,
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5
  },
  notificationGradient: {
    padding: 16,
    alignItems: 'center'
  },
  notificationText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center'
  }
});

export default CollaborativeEditor;