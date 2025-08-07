import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Modal,
  Alert,
  Vibration,
  Share,
  Dimensions,
  StatusBar,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Haptics from 'expo-haptics';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';

// Mobile theme colors
const theme = {
  primary: '#3B82F6',
  secondary: '#10B981',
  error: '#EF4444',
  warning: '#F59E0B',
  background: '#F8FAFC',
  surface: '#FFFFFF',
  text: '#1F2937',
  textSecondary: '#6B7280',
  border: '#E5E7EB',
};

// Types and interfaces
interface Operation {
  operation_id: string;
  type: 'insert' | 'delete' | 'retain' | 'format' | 'annotation';
  position: number;
  length?: number;
  content?: string;
  attributes?: Record<string, any>;
  user_id: number;
  timestamp: string;
}

interface CollaborativeUser {
  user_id: number;
  username: string;
  full_name?: string;
  email?: string;
  cursor_position?: number;
  last_seen: string;
  status: 'active' | 'idle' | 'typing';
  color: string;
  is_mobile?: boolean;
  platform?: string;
}

interface DocumentState {
  document_id: string;
  content: string;
  version: number;
  last_modified: string;
  active_users: Record<string, CollaborativeUser>;
  cursors: Record<string, number>;
  annotations: Array<{
    id: string;
    type: string;
    start: number;
    end: number;
    content?: string;
    attributes?: Record<string, any>;
    user_id: number;
    created_at: string;
  }>;
}

interface CollaborativeEditorProps {
  documentId: string;
  initialContent?: string;
  sessionId?: string;
  readOnly?: boolean;
  onContentChange?: (content: string) => void;
  onSave?: (content: string) => void;
}

const USER_COLORS = [
  '#3B82F6', '#EF4444', '#10B981', '#F59E0B', 
  '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'
];

// Haptic feedback helper
const triggerHaptic = (type: 'light' | 'medium' | 'heavy' = 'light') => {
  if (Platform.OS === 'ios') {
    if (type === 'light') Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    else if (type === 'medium') Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    else Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
  } else {
    Vibration.vibrate(50);
  }
};

// Push notification helper
const scheduleNotification = async (title: string, body: string) => {
  await Notifications.scheduleNotificationAsync({
    content: {
      title,
      body,
      sound: true,
    },
    trigger: { seconds: 1 },
  });
};

export const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
  documentId,
  initialContent = '',
  sessionId,
  readOnly = false,
  onContentChange,
  onSave
}) => {
  // State
  const [content, setContent] = useState(initialContent);
  const [documentState, setDocumentState] = useState<DocumentState | null>(null);
  const [collaborativeUsers, setCollaborativeUsers] = useState<Record<number, CollaborativeUser>>({});
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(sessionId || null);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [pendingOperations, setPendingOperations] = useState<Operation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showCollaborators, setShowCollaborators] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [isLandscape, setIsLandscape] = useState(false);

  // Refs
  const textInputRef = useRef<TextInput>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const operationQueueRef = useRef<Operation[]>([]);
  const typingTimeoutRef = useRef<NodeJS.Timeout>();
  const saveTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // Screen dimensions
  const screenData = Dimensions.get('window');
  
  // Get user color
  const getUserColor = useCallback((userId: number): string => {
    return USER_COLORS[userId % USER_COLORS.length];
  }, []);

  // Mobile-specific notification
  const showMobileNotification = useCallback(async (title: string, message: string) => {
    if (!notifications) return;

    if (Device.isDevice) {
      await scheduleNotification(title, message);
    } else {
      Alert.alert(title, message);
    }
    triggerHaptic('light');
  }, [notifications]);

  // Mobile-specific file sharing
  const shareDocument = useCallback(async () => {
    try {
      const fileUri = `${FileSystem.documentDirectory}document_${documentId}.txt`;
      await FileSystem.writeAsStringAsync(fileUri, content);
      
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(fileUri);
        triggerHaptic('medium');
      } else {
        await Share.share({
          message: content,
          title: `Document ${documentId}`,
        });
      }
    } catch (err) {
      console.error('Share failed:', err);
      Alert.alert('Share Failed', 'Could not share document');
    }
  }, [content, documentId]);

  // Handle orientation changes
  useEffect(() => {
    const subscription = Dimensions.addEventListener('change', ({ window }) => {
      setIsLandscape(window.width > window.height);
    });

    return () => subscription?.remove();
  }, []);

  // Initialize collaborative session
  const initializeSession = useCallback(async () => {
    try {
      setError(null);
      
      if (!currentSessionId) {
        // Create new session with mobile metadata
        const response = await fetch('/api/v1/collaboration/sessions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            document_id: documentId,
            initial_content: content,
            settings: {
              conflict_resolution: 'merge_changes',
              auto_save_interval: 30,
              max_participants: 10,
              platform_info: {
                platform: 'mobile',
                client: 'react-native',
                os: Platform.OS,
                version: Platform.Version?.toString() || '1.0.0'
              }
            }
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to create collaboration session');
        }

        const sessionData = await response.json();
        setCurrentSessionId(sessionData.session_id);
      } else {
        // Join existing session
        const response = await fetch(`/api/v1/collaboration/sessions/${currentSessionId}/join`, {
          method: 'POST',
        });

        if (!response.ok) {
          throw new Error('Failed to join collaboration session');
        }
      }

      // Load document state
      await loadDocumentState();
      
      // Connect WebSocket
      await connectWebSocket();

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize session');
      console.error('Session initialization error:', err);
    }
  }, [documentId, content, currentSessionId]);

  // Load document state
  const loadDocumentState = useCallback(async () => {
    try {
      const response = await fetch(`/api/v1/collaboration/documents/${documentId}/state`);
      if (response.ok) {
        const state: DocumentState = await response.json();
        setDocumentState(state);
        setContent(state.content);
        
        // Convert active users to collaborative users with platform info
        const users: Record<number, CollaborativeUser> = {};
        Object.entries(state.active_users).forEach(([userIdStr, userData]) => {
          const userId = parseInt(userIdStr);
          users[userId] = {
            ...userData,
            user_id: userId,
            status: 'active',
            color: getUserColor(userId),
            cursor_position: state.cursors[userIdStr] || 0,
            is_mobile: userData.platform === 'mobile',
            platform: userData.platform || 'unknown'
          } as CollaborativeUser;
        });
        setCollaborativeUsers(users);
      }
    } catch (err) {
      console.error('Failed to load document state:', err);
    }
  }, [documentId, getUserColor]);

  // Connect WebSocket with mobile-specific reconnection
  const connectWebSocket = useCallback(async () => {
    if (!currentSessionId) return;

    try {
      setConnectionStatus('connecting');
      
      const token = btoa(JSON.stringify({
        user_id: 1, // Would get from auth context
        username: 'mobile_user',
        platform: 'mobile'
      }));

      const wsUrl = `ws://localhost:8000/api/v1/collaboration/ws/${currentSessionId}?token=${token}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnectionStatus('connected');
        setError(null);
        
        // Clear any pending reconnect
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        
        showMobileNotification('Connected', 'Real-time collaboration enabled');
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('WebSocket message parse error:', err);
        }
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        showMobileNotification('Disconnected', 'Attempting to reconnect...');
        
        // Auto-reconnect with exponential backoff
        const baseDelay = 1000;
        const maxDelay = 30000;
        const currentDelay = Math.min(baseDelay * Math.pow(2, 1), maxDelay);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          if (websocketRef.current === ws) {
            connectWebSocket();
          }
        }, currentDelay);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error');
        setConnectionStatus('disconnected');
      };

      websocketRef.current = ws;

    } catch (err) {
      console.error('WebSocket connection error:', err);
      setConnectionStatus('disconnected');
    }
  }, [currentSessionId, showMobileNotification]);

  // Handle WebSocket messages with mobile notifications
  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'connection_confirmed':
        console.log('WebSocket connection confirmed');
        break;

      case 'operation_applied':
        applyRemoteOperations(message.operations);
        triggerHaptic('light');
        break;

      case 'cursor_update':
        if (message.user_id !== 1) { // Not current user
          setCollaborativeUsers(prev => ({
            ...prev,
            [message.user_id]: {
              ...prev[message.user_id],
              cursor_position: message.position,
              status: 'active',
              last_seen: message.timestamp
            }
          }));
        }
        break;

      case 'user_joined':
        const newUser = {
          user_id: message.user_id,
          username: message.username,
          status: 'active' as const,
          color: getUserColor(message.user_id),
          cursor_position: 0,
          last_seen: message.timestamp,
          is_mobile: message.platform === 'mobile',
          platform: message.platform || 'unknown'
        };
        
        setCollaborativeUsers(prev => ({
          ...prev,
          [message.user_id]: newUser
        }));
        
        showMobileNotification(
          'User Joined', 
          `${message.username} joined from ${message.platform || 'unknown'} device`
        );
        break;

      case 'user_left':
        setCollaborativeUsers(prev => {
          const updated = { ...prev };
          const leftUser = updated[message.user_id];
          delete updated[message.user_id];
          
          if (leftUser) {
            showMobileNotification('User Left', `${leftUser.username} left the session`);
          }
          
          return updated;
        });
        break;

      case 'presence_update':
        setCollaborativeUsers(prev => ({
          ...prev,
          [message.user_id]: {
            ...prev[message.user_id],
            status: message.status,
            last_seen: message.timestamp
          }
        }));
        break;

      case 'operation_ack':
        setPendingOperations(prev => 
          prev.filter(op => op.operation_id !== message.operation_id)
        );
        break;

      case 'operation_error':
        console.error('Operation error:', message.error);
        setError(`Operation failed: ${message.error}`);
        showMobileNotification('Sync Error', message.error);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [getUserColor, showMobileNotification]);

  // Apply remote operations to content
  const applyRemoteOperations = useCallback((operations: Operation[]) => {
    setContent(prevContent => {
      let newContent = prevContent;
      
      for (const op of operations) {
        if (op.type === 'insert') {
          newContent = newContent.slice(0, op.position) + 
                      op.content + 
                      newContent.slice(op.position);
        } else if (op.type === 'delete') {
          const start = op.position;
          const end = op.position + (op.length || 0);
          newContent = newContent.slice(0, start) + newContent.slice(end);
        }
      }
      
      return newContent;
    });

    // Update document version if provided
    if (operations.length > 0) {
      setDocumentState(prev => prev ? {
        ...prev,
        version: prev.version + 1,
        content: content // Will be updated in next render
      } : null);
    }
  }, [content]);

  // Send operation through WebSocket
  const sendOperation = useCallback((operation: Partial<Operation>) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN && !readOnly) {
      const fullOperation: Operation = {
        operation_id: `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: operation.type || 'insert',
        position: operation.position || 0,
        length: operation.length || 0,
        content: operation.content || '',
        attributes: operation.attributes || {},
        user_id: 1, // Would get from auth context
        timestamp: new Date().toISOString()
      };

      // Add to pending operations
      setPendingOperations(prev => [...prev, fullOperation]);

      // Send via WebSocket
      websocketRef.current.send(JSON.stringify({
        type: 'operation',
        document_id: documentId,
        operation: fullOperation
      }));
    }
  }, [documentId, readOnly]);

  // Handle text input changes
  const handleContentChange = useCallback((newContent: string) => {
    const oldContent = content;
    const newPos = cursorPosition; // Mobile doesn't have selectionStart like web

    // Calculate operation
    if (newContent.length > oldContent.length) {
      // Insert operation
      const insertPos = newPos;
      const insertedText = newContent.slice(insertPos, insertPos + (newContent.length - oldContent.length));
      
      sendOperation({
        type: 'insert',
        position: insertPos,
        content: insertedText
      });
    } else if (newContent.length < oldContent.length) {
      // Delete operation
      const deleteLength = oldContent.length - newContent.length;
      const deletePos = Math.max(0, newPos - deleteLength);
      
      sendOperation({
        type: 'delete',
        position: deletePos,
        length: deleteLength
      });
    }

    setContent(newContent);
    setHasUnsavedChanges(true);
    setIsTyping(true);

    // Clear typing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set typing indicator timeout
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      sendPresenceUpdate('active');
    }, 1000);

    // Send typing presence
    sendPresenceUpdate('typing');

    // Auto-save timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    saveTimeoutRef.current = setTimeout(() => {
      handleSave();
    }, 5000); // Auto-save after 5 seconds of inactivity

    // Notify parent component
    if (onContentChange) {
      onContentChange(newContent);
    }
  }, [content, cursorPosition, sendOperation, onContentChange]);

  // Send presence update
  const sendPresenceUpdate = useCallback((status: 'active' | 'idle' | 'typing') => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({
        type: 'presence_update',
        status
      }));
    }
  }, []);

  // Handle save with mobile integration
  const handleSave = useCallback(async () => {
    if (!hasUnsavedChanges) return;

    try {
      if (onSave) {
        await onSave(content);
      }
      
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
      triggerHaptic('medium');
      showMobileNotification('Saved', 'Document saved successfully');
    } catch (err) {
      console.error('Save failed:', err);
      setError('Save failed');
      showMobileNotification('Save Failed', 'Could not save document');
    }
  }, [content, hasUnsavedChanges, onSave, showMobileNotification]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  // Auto-save on content change
  useEffect(() => {
    if (hasUnsavedChanges && saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
      saveTimeoutRef.current = setTimeout(handleSave, 5000);
    }
  }, [hasUnsavedChanges, handleSave]);

  const getConnectionIcon = () => {
    switch (connectionStatus) {
      case 'connected': return 'wifi';
      case 'connecting': return 'time';
      default: return 'wifi-off';
    }
  };

  const getConnectionColor = () => {
    switch (connectionStatus) {
      case 'connected': return theme.secondary;
      case 'connecting': return theme.warning;
      default: return theme.error;
    }
  };

  const getPlatformIcon = (platform?: string) => {
    switch (platform) {
      case 'desktop':
        return 'desktop';
      case 'mobile':
        return 'phone-portrait';
      case 'web':
        return 'globe';
      default:
        return 'laptop';
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.background }}>
      <StatusBar barStyle="dark-content" backgroundColor={theme.background} />
      
      {/* Header */}
      <View style={{
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingVertical: 12,
        backgroundColor: theme.surface,
        borderBottomWidth: 1,
        borderBottomColor: theme.border,
      }}>
        <View style={{ flex: 1 }}>
          <Text style={{
            fontSize: 18,
            fontWeight: '600',
            color: theme.text,
            marginBottom: 2,
          }}>
            Collaborative Editor
          </Text>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Ionicons 
              name={getConnectionIcon() as any} 
              size={14} 
              color={getConnectionColor()} 
            />
            <Text style={{
              fontSize: 12,
              color: theme.textSecondary,
              marginLeft: 4,
            }}>
              {connectionStatus === 'connected' ? 'Connected' :
               connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
            </Text>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          {hasUnsavedChanges && (
            <View style={{
              paddingHorizontal: 8,
              paddingVertical: 4,
              backgroundColor: theme.warning,
              borderRadius: 12,
            }}>
              <Text style={{
                fontSize: 10,
                color: 'white',
                fontWeight: '600',
              }}>
                Unsaved
              </Text>
            </View>
          )}

          {lastSaved && !hasUnsavedChanges && (
            <View style={{
              paddingHorizontal: 8,
              paddingVertical: 4,
              backgroundColor: theme.secondary,
              borderRadius: 12,
            }}>
              <Text style={{
                fontSize: 10,
                color: 'white',
                fontWeight: '600',
              }}>
                Saved {format(lastSaved, 'HH:mm')}
              </Text>
            </View>
          )}

          <TouchableOpacity
            onPress={() => setShowCollaborators(true)}
            style={{ padding: 4 }}
          >
            <View style={{ position: 'relative' }}>
              <Ionicons name="people" size={24} color={theme.primary} />
              {Object.keys(collaborativeUsers).length > 0 && (
                <View style={{
                  position: 'absolute',
                  top: -4,
                  right: -4,
                  width: 16,
                  height: 16,
                  backgroundColor: theme.error,
                  borderRadius: 8,
                  justifyContent: 'center',
                  alignItems: 'center',
                }}>
                  <Text style={{
                    fontSize: 10,
                    color: 'white',
                    fontWeight: '600',
                  }}>
                    {Object.keys(collaborativeUsers).length}
                  </Text>
                </View>
              )}
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={shareDocument}
            style={{ padding: 4 }}
          >
            <Ionicons name="share" size={24} color={theme.primary} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Error Alert */}
      {error && (
        <View style={{
          margin: 16,
          padding: 12,
          backgroundColor: theme.error + '20',
          borderRadius: 8,
          borderLeftWidth: 4,
          borderLeftColor: theme.error,
        }}>
          <Text style={{
            color: theme.error,
            fontSize: 14,
            fontWeight: '500',
          }}>
            {error}
          </Text>
        </View>
      )}

      {/* Main Editor */}
      <View style={{ flex: 1, margin: 16 }}>
        <View style={{
          flex: 1,
          backgroundColor: theme.surface,
          borderRadius: 12,
          borderWidth: 1,
          borderColor: theme.border,
          position: 'relative',
        }}>
          <TextInput
            ref={textInputRef}
            value={content}
            onChangeText={handleContentChange}
            onSelectionChange={(e) => setCursorPosition(e.nativeEvent.selection.start)}
            placeholder={readOnly ? "Content is read-only" : "Start typing to collaborate..."}
            placeholderTextColor={theme.textSecondary}
            editable={!readOnly}
            multiline
            textAlignVertical="top"
            style={{
              flex: 1,
              padding: 16,
              fontSize: 16,
              color: theme.text,
              fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
              lineHeight: 24,
            }}
          />

          {/* Pending operations indicator */}
          {pendingOperations.length > 0 && (
            <View style={{
              position: 'absolute',
              top: 12,
              right: 12,
              paddingHorizontal: 8,
              paddingVertical: 4,
              backgroundColor: theme.warning,
              borderRadius: 12,
              flexDirection: 'row',
              alignItems: 'center',
            }}>
              <Ionicons name="time" size={12} color="white" />
              <Text style={{
                fontSize: 10,
                color: 'white',
                fontWeight: '600',
                marginLeft: 4,
              }}>
                {pendingOperations.length} pending
              </Text>
            </View>
          )}
        </View>

        {/* Document Info */}
        {documentState && (
          <View style={{
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: 8,
            paddingHorizontal: 4,
          }}>
            <Text style={{
              fontSize: 12,
              color: theme.textSecondary,
            }}>
              Version: {documentState.version} • 
              Last modified: {format(new Date(documentState.last_modified), 'MMM dd, HH:mm')}
            </Text>
            <Text style={{
              fontSize: 12,
              color: theme.textSecondary,
            }}>
              {content.length} chars • {content.split('\n').length} lines
            </Text>
          </View>
        )}
      </View>

      {/* Floating Action Button */}
      <TouchableOpacity
        onPress={handleSave}
        disabled={!hasUnsavedChanges}
        style={{
          position: 'absolute',
          bottom: 24,
          right: 24,
          width: 56,
          height: 56,
          borderRadius: 28,
          backgroundColor: hasUnsavedChanges ? theme.primary : theme.textSecondary,
          justifyContent: 'center',
          alignItems: 'center',
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.25,
          shadowRadius: 4,
          elevation: 5,
        }}
      >
        <Ionicons name="save" size={24} color="white" />
      </TouchableOpacity>

      {/* Collaborators Modal */}
      <Modal
        visible={showCollaborators}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowCollaborators(false)}
      >
        <SafeAreaView style={{ flex: 1, backgroundColor: theme.background }}>
          <View style={{
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingHorizontal: 16,
            paddingVertical: 12,
            borderBottomWidth: 1,
            borderBottomColor: theme.border,
          }}>
            <Text style={{
              fontSize: 18,
              fontWeight: '600',
              color: theme.text,
            }}>
              Collaborators ({Object.keys(collaborativeUsers).length})
            </Text>
            <TouchableOpacity
              onPress={() => setShowCollaborators(false)}
              style={{ padding: 4 }}
            >
              <Ionicons name="close" size={24} color={theme.text} />
            </TouchableOpacity>
          </View>

          <ScrollView style={{ flex: 1, padding: 16 }}>
            {Object.values(collaborativeUsers).map((user) => (
              <View
                key={user.user_id}
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  paddingVertical: 12,
                  paddingHorizontal: 16,
                  backgroundColor: theme.surface,
                  borderRadius: 12,
                  marginBottom: 8,
                  borderWidth: 2,
                  borderColor: user.color + '40',
                }}
              >
                <View style={{
                  width: 40,
                  height: 40,
                  borderRadius: 20,
                  backgroundColor: user.color + '20',
                  justifyContent: 'center',
                  alignItems: 'center',
                  marginRight: 12,
                  position: 'relative',
                }}>
                  <Text style={{
                    fontSize: 16,
                    fontWeight: '600',
                    color: user.color,
                  }}>
                    {user.username.substring(0, 2).toUpperCase()}
                  </Text>
                  
                  {/* Platform indicator */}
                  <View style={{
                    position: 'absolute',
                    bottom: -2,
                    right: -2,
                    width: 16,
                    height: 16,
                    borderRadius: 8,
                    backgroundColor: theme.surface,
                    justifyContent: 'center',
                    alignItems: 'center',
                    borderWidth: 1,
                    borderColor: theme.border,
                  }}>
                    <Ionicons 
                      name={getPlatformIcon(user.platform) as any} 
                      size={10} 
                      color={theme.textSecondary} 
                    />
                  </View>
                  
                  {/* Status indicator */}
                  <View style={{
                    position: 'absolute',
                    top: -2,
                    right: -2,
                    width: 12,
                    height: 12,
                    borderRadius: 6,
                    backgroundColor: user.status === 'typing' ? theme.secondary :
                                    user.status === 'active' ? theme.secondary : theme.textSecondary,
                    borderWidth: 2,
                    borderColor: theme.surface,
                  }} />
                </View>

                <View style={{ flex: 1 }}>
                  <Text style={{
                    fontSize: 16,
                    fontWeight: '500',
                    color: theme.text,
                    marginBottom: 2,
                  }}>
                    {user.full_name || user.username}
                    {user.is_mobile && ' 📱'}
                  </Text>
                  <Text style={{
                    fontSize: 12,
                    color: theme.textSecondary,
                  }}>
                    {user.status === 'typing' ? 'Typing...' : 
                     user.status === 'active' ? 'Active' : 'Idle'} • 
                    Position {user.cursor_position}
                  </Text>
                </View>

                <View style={{
                  width: 16,
                  height: 16,
                  borderRadius: 8,
                  backgroundColor: user.color,
                }} />
              </View>
            ))}

            {Object.keys(collaborativeUsers).length === 0 && (
              <View style={{
                alignItems: 'center',
                justifyContent: 'center',
                paddingVertical: 40,
              }}>
                <Ionicons name="people-outline" size={48} color={theme.textSecondary} />
                <Text style={{
                  fontSize: 16,
                  color: theme.textSecondary,
                  marginTop: 8,
                }}>
                  No other collaborators
                </Text>
                <Text style={{
                  fontSize: 14,
                  color: theme.textSecondary,
                  textAlign: 'center',
                  marginTop: 4,
                  lineHeight: 20,
                }}>
                  Share this document to collaborate in real-time
                </Text>
              </View>
            )}
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
};

export default CollaborativeEditor;