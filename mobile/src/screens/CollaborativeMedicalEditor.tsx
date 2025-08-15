/**
 * Collaborative Medical Editor Screen for React Native
 * Touch-optimized multi-user editing with medical schema integration and mobile-specific features
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  TouchableHighlight,
  PanGestureHandler,
  TapGestureHandler,
  LongPressGestureHandler,
  GestureHandlerRootView,
  State,
  Alert,
  Modal,
  FlatList,
  Dimensions,
  Platform,
  Keyboard,
  KeyboardAvoidingView,
  StatusBar,
  Animated,
  Easing,
  PanResponder,
  Vibration,
  Share
} from 'react-native';
import {
  SafeAreaView,
  SafeAreaProvider,
  useSafeAreaInsets
} from 'react-native-safe-area-context';
import {
  Header,
  HeaderTitle,
  HeaderLeft,
  HeaderRight,
  HeaderButton
} from '@react-navigation/elements';
import NetInfo from '@react-native-netinfo/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNetInfo } from '@react-native-netinfo/netinfo';
import { useKeyboard } from '@react-native-community/hooks';
import { useColorScheme } from 'react-native-appearance';
import Svg, { Circle, Path, Text as SvgText } from 'react-native-svg';
import LinearGradient from 'react-native-linear-gradient';
import { BlurView } from '@react-native-blur/blur';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Haptics, HapticsImpactType } from 'expo-haptics';
import * as Speech from 'expo-speech';
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system';
import { Audio } from 'expo-av';

// Mobile collaboration services
import { MobileCollaborationEngine } from '../services/mobileCollaborationEngine';
import { TouchPresenceTracker } from '../services/touchPresenceTracker';
import { MobileMedicalValidator } from '../services/mobileMedicalValidator';
import { VoiceAnnotationService } from '../services/voiceAnnotationService';
import { OfflineCollaborationSync } from '../services/offlineCollaborationSync';
import { MobileNotificationManager } from '../services/mobileNotificationManager';

// Enhanced mobile styling
const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

const styles = {
  container: {
    flex: 1,
    backgroundColor: '#ffffff'
  },
  darkContainer: {
    flex: 1,
    backgroundColor: '#1a1a1a'
  },
  header: {
    height: 60,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#f8f9fa',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
    elevation: 2,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4
  },
  connectionIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8
  },
  userAvatars: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    marginLeft: -8,
    borderWidth: 2,
    borderColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center'
  },
  avatarText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold'
  },
  typingIndicator: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    backgroundColor: '#007AFF',
    borderRadius: 12,
    marginLeft: 8
  },
  typingText: {
    color: '#ffffff',
    fontSize: 12
  },
  editorContainer: {
    flex: 1,
    position: 'relative'
  },
  editor: {
    flex: 1,
    padding: 16,
    fontSize: 16,
    lineHeight: 24,
    textAlignVertical: 'top',
    backgroundColor: 'transparent'
  },
  darkEditor: {
    color: '#ffffff'
  },
  presenceCursor: {
    position: 'absolute',
    width: 2,
    height: 20,
    zIndex: 1000
  },
  selectionHighlight: {
    position: 'absolute',
    backgroundColor: 'rgba(0, 122, 255, 0.3)',
    zIndex: 999
  },
  annotationHighlight: {
    position: 'absolute',
    backgroundColor: 'rgba(255, 193, 7, 0.4)',
    zIndex: 998,
    borderRadius: 2
  },
  medicalTermHighlight: {
    position: 'absolute',
    backgroundColor: 'rgba(40, 167, 69, 0.3)',
    zIndex: 997,
    borderRadius: 2
  },
  bottomSheet: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    paddingBottom: 40,
    paddingHorizontal: 20,
    elevation: 10,
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.2,
    shadowRadius: 8
  },
  bottomSheetHandle: {
    width: 40,
    height: 4,
    backgroundColor: '#d1d5db',
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 20
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 4,
    marginBottom: 20
  },
  tab: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center'
  },
  activeTab: {
    backgroundColor: '#ffffff',
    elevation: 2,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280'
  },
  activeTabText: {
    color: '#007AFF'
  },
  userItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    marginBottom: 8
  },
  userInfo: {
    marginLeft: 12,
    flex: 1
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937'
  },
  userStatus: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2
  },
  userActions: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  actionButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#e5e7eb',
    marginLeft: 8
  },
  commentItem: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#007AFF'
  },
  commentText: {
    fontSize: 14,
    color: '#1f2937',
    marginBottom: 8
  },
  commentMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  commentAuthor: {
    fontSize: 12,
    color: '#6b7280'
  },
  commentTime: {
    fontSize: 12,
    color: '#9ca3af'
  },
  medicalValidation: {
    backgroundColor: '#f0f9ff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#bfdbfe'
  },
  validationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e40af',
    marginBottom: 12
  },
  validationMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12
  },
  metricItem: {
    alignItems: 'center'
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e40af'
  },
  metricLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4
  },
  validationError: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fef2f2',
    borderRadius: 6,
    padding: 8,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#ef4444'
  },
  errorIcon: {
    marginRight: 8
  },
  errorText: {
    flex: 1,
    fontSize: 14,
    color: '#dc2626'
  },
  floatingButtons: {
    position: 'absolute',
    right: 16,
    bottom: 100,
    alignItems: 'flex-end'
  },
  floatingButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    elevation: 6,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.3,
    shadowRadius: 4
  },
  smallFloatingButton: {
    width: 48,
    height: 48,
    borderRadius: 24
  },
  voiceRecordingButton: {
    backgroundColor: '#dc2626'
  },
  recordingAnimation: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(220, 38, 38, 0.2)',
    position: 'absolute',
    right: -22,
    bottom: -22
  },
  contextMenu: {
    position: 'absolute',
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 8,
    elevation: 8,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    minWidth: 200
  },
  contextMenuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 4
  },
  contextMenuText: {
    marginLeft: 12,
    fontSize: 16,
    color: '#1f2937'
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center'
  },
  loadingContent: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    minWidth: 200
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#1f2937'
  },
  offlineIndicator: {
    backgroundColor: '#f59e0b',
    paddingVertical: 4,
    paddingHorizontal: 16,
    alignItems: 'center'
  },
  offlineText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '500'
  },
  toolBar: {
    flexDirection: 'row',
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  toolButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    backgroundColor: '#e5e7eb'
  },
  toolButtonActive: {
    backgroundColor: '#007AFF'
  },
  toolButtonText: {
    marginLeft: 4,
    fontSize: 12,
    color: '#6b7280'
  },
  toolButtonTextActive: {
    color: '#ffffff'
  }
};

// Types
interface MobileUser {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'owner' | 'editor' | 'reviewer' | 'viewer' | 'medical_professional';
  color: string;
  isOnline: boolean;
  isTyping: boolean;
  cursor?: { x: number; y: number; line: number; column: number };
  selection?: { start: number; end: number };
  lastActivity: Date;
  deviceInfo: {
    platform: string;
    deviceType: string;
    hasVoiceCapabilities: boolean;
    supportsTouchGestures: boolean;
  };
}

interface MobileComment {
  id: string;
  userId: string;
  text: string;
  timestamp: Date;
  position: { line: number; column: number };
  resolved: boolean;
  replies: MobileComment[];
  voiceNote?: {
    uri: string;
    duration: number;
  };
  medicalPriority?: 'low' | 'medium' | 'high' | 'critical';
}

interface MobileAnnotation {
  id: string;
  userId: string;
  type: 'highlight' | 'medical_term' | 'correction' | 'note' | 'voice_note';
  text: string;
  note?: string;
  start: number;
  end: number;
  color: string;
  timestamp: Date;
  medicalContext?: {
    terminology: string;
    category: string;
    confidence: number;
  };
  voiceData?: {
    uri: string;
    transcription: string;
    duration: number;
  };
}

interface Props {
  documentId: string;
  initialContent?: string;
  readOnly?: boolean;
  enableMedicalValidation?: boolean;
  enableVoiceAnnotations?: boolean;
  currentUser: MobileUser;
  onSave?: (content: string) => void;
  onError?: (error: Error) => void;
  navigation: any;
}

const CollaborativeMedicalEditor: React.FC<Props> = ({
  documentId,
  initialContent = '',
  readOnly = false,
  enableMedicalValidation = true,
  enableVoiceAnnotations = true,
  currentUser,
  onSave,
  onError,
  navigation
}) => {
  // State management
  const [content, setContent] = useState(initialContent);
  const [users, setUsers] = useState<MobileUser[]>([currentUser]);
  const [comments, setComments] = useState<MobileComment[]>([]);
  const [annotations, setAnnotations] = useState<MobileAnnotation[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'syncing'>('connecting');
  const [showBottomSheet, setShowBottomSheet] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);
  const [isRecordingVoice, setIsRecordingVoice] = useState(false);
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 });
  const [selectedText, setSelectedText] = useState('');
  const [selectionRange, setSelectionRange] = useState({ start: 0, end: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const [medicalValidation, setMedicalValidation] = useState(null);
  const [offlineMode, setOfflineMode] = useState(false);
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  
  // Animations
  const bottomSheetAnim = useRef(new Animated.Value(0)).current;
  const recordingAnim = useRef(new Animated.Value(0)).current;
  const presencePulse = useRef(new Animated.Value(1)).current;
  
  // Refs
  const editorRef = useRef<TextInput>(null);
  const collaborationEngineRef = useRef<MobileCollaborationEngine | null>(null);
  const presenceTrackerRef = useRef<TouchPresenceTracker | null>(null);
  const medicalValidatorRef = useRef<MobileMedicalValidator | null>(null);
  const voiceServiceRef = useRef<VoiceAnnotationService | null>(null);
  const offlineSyncRef = useRef<OfflineCollaborationSync | null>(null);
  const notificationManagerRef = useRef<MobileNotificationManager | null>(null);
  
  // Hooks
  const insets = useSafeAreaInsets();
  const netInfo = useNetInfo();
  const keyboard = useKeyboard();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  
  // Memoized values
  const activeUsers = useMemo(() => users.filter(user => user.isOnline), [users]);
  const typingUsers = useMemo(() => users.filter(user => user.isTyping && user.id !== currentUser.id), [users, currentUser.id]);
  const unresolvedComments = useMemo(() => comments.filter(comment => !comment.resolved), [comments]);
  
  // Initialize mobile collaboration
  useEffect(() => {
    const initializeMobileCollaboration = async () => {
      try {
        setIsLoading(true);
        
        // Initialize mobile collaboration engine
        collaborationEngineRef.current = new MobileCollaborationEngine(documentId, currentUser);
        await collaborationEngineRef.current.initialize();
        
        // Initialize touch presence tracker
        presenceTrackerRef.current = new TouchPresenceTracker(documentId, currentUser);
        await presenceTrackerRef.current.initialize();
        
        // Initialize medical validator
        if (enableMedicalValidation) {
          medicalValidatorRef.current = new MobileMedicalValidator();
          await medicalValidatorRef.current.initialize();
        }
        
        // Initialize voice annotation service
        if (enableVoiceAnnotations) {
          voiceServiceRef.current = new VoiceAnnotationService(documentId, currentUser);
          await voiceServiceRef.current.initialize();
        }
        
        // Initialize offline sync
        offlineSyncRef.current = new OfflineCollaborationSync(documentId, currentUser);
        await offlineSyncRef.current.initialize();
        
        // Initialize notification manager
        notificationManagerRef.current = new MobileNotificationManager();
        await notificationManagerRef.current.initialize();
        
        // Set up event handlers
        setupMobileEventHandlers();
        
        setConnectionStatus('connected');
        setIsLoading(false);
        
        // Show success haptic
        Haptics.impactAsync(HapticsImpactType.Light);
      } catch (error) {
        console.error('Failed to initialize mobile collaboration:', error);
        setConnectionStatus('disconnected');
        setIsLoading(false);
        onError?.(error as Error);
        
        // Show error haptic
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      }
    };
    
    initializeMobileCollaboration();
    
    return () => {
      // Cleanup
      collaborationEngineRef.current?.cleanup();
      presenceTrackerRef.current?.cleanup();
      voiceServiceRef.current?.cleanup();
      offlineSyncRef.current?.cleanup();
      notificationManagerRef.current?.cleanup();
    };
  }, [documentId, currentUser, enableMedicalValidation, enableVoiceAnnotations, onError]);
  
  // Network status monitoring
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      const isConnected = state.isConnected && state.isInternetReachable;
      setOfflineMode(!isConnected);
      
      if (isConnected && offlineSyncRef.current) {
        // Sync offline changes when reconnected
        offlineSyncRef.current.syncOfflineChanges();
      }
    });
    
    return unsubscribe;
  }, []);
  
  // Keyboard handling
  useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener('keyboardDidShow', () => {
      setKeyboardVisible(true);
    });
    const keyboardDidHideListener = Keyboard.addListener('keyboardDidHide', () => {
      setKeyboardVisible(false);
    });
    
    return () => {
      keyboardDidHideListener.remove();
      keyboardDidShowListener.remove();
    };
  }, []);
  
  // Event handlers setup
  const setupMobileEventHandlers = useCallback(() => {
    if (!collaborationEngineRef.current || !presenceTrackerRef.current) return;
    
    // Content change events
    collaborationEngineRef.current.onContentChange((newContent) => {
      setContent(newContent);
      setConnectionStatus('connected');
    });
    
    // User presence events
    presenceTrackerRef.current.onUserJoin((user) => {
      setUsers(prev => [...prev.filter(u => u.id !== user.id), user]);
      notificationManagerRef.current?.showNotification(`${user.name} joined the session`);
      Haptics.impactAsync(HapticsImpactType.Light);
    });
    
    presenceTrackerRef.current.onUserLeave((userId) => {
      const user = users.find(u => u.id === userId);
      if (user) {
        notificationManagerRef.current?.showNotification(`${user.name} left the session`);
      }
      setUsers(prev => prev.filter(u => u.id !== userId));
    });
    
    // Touch activity events
    presenceTrackerRef.current.onTouchActivity((userId, activity) => {
      setUsers(prev => prev.map(user => 
        user.id === userId 
          ? { ...user, ...activity, lastActivity: new Date() }
          : user
      ));
    });
    
    // Medical validation events
    if (medicalValidatorRef.current) {
      medicalValidatorRef.current.onValidationComplete((validation) => {
        setMedicalValidation(validation);
        if (validation.errors.length > 0) {
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        }
      });
    }
    
    // Voice annotation events
    if (voiceServiceRef.current) {
      voiceServiceRef.current.onVoiceAnnotationAdded((annotation) => {
        setAnnotations(prev => [...prev, annotation]);
        Haptics.impactAsync(HapticsImpactType.Medium);
      });
    }
  }, [users]);
  
  // Content change handler
  const handleContentChange = useCallback((text: string) => {
    setContent(text);
    setConnectionStatus('syncing');
    
    // Apply changes through collaboration engine
    collaborationEngineRef.current?.applyChange(text);
    
    // Medical validation
    if (enableMedicalValidation && medicalValidatorRef.current) {
      medicalValidatorRef.current.validateContent(text);
    }
    
    // Auto-save offline if disconnected
    if (offlineMode && offlineSyncRef.current) {
      offlineSyncRef.current.saveOfflineChange(text);
    }
  }, [enableMedicalValidation, offlineMode]);
  
  // Selection change handler
  const handleSelectionChange = useCallback(({ nativeEvent }) => {
    const { selection } = nativeEvent;
    setSelectionRange(selection);
    
    // Update presence tracker with cursor position
    presenceTrackerRef.current?.updateCursorPosition(selection.start);
    
    // Extract selected text
    if (selection.start !== selection.end) {
      const selected = content.substring(selection.start, selection.end);
      setSelectedText(selected);
    } else {
      setSelectedText('');
    }
  }, [content]);
  
  // Long press handler for context menu
  const handleLongPress = useCallback((event) => {
    if (selectedText) {
      const { pageX, pageY } = event.nativeEvent;
      setContextMenuPosition({ x: pageX, y: pageY });
      setShowContextMenu(true);
      Haptics.impactAsync(HapticsImpactType.Medium);
    }
  }, [selectedText]);
  
  // Voice recording
  const handleStartVoiceRecording = useCallback(async () => {
    if (!enableVoiceAnnotations || !voiceServiceRef.current) return;
    
    try {
      setIsRecordingVoice(true);
      
      // Start recording animation
      Animated.loop(
        Animated.sequence([
          Animated.timing(recordingAnim, {
            toValue: 1,
            duration: 1000,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true
          }),
          Animated.timing(recordingAnim, {
            toValue: 0,
            duration: 1000,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true
          })
        ])
      ).start();
      
      await voiceServiceRef.current.startRecording();
      Haptics.impactAsync(HapticsImpactType.Heavy);
      
    } catch (error) {
      console.error('Failed to start voice recording:', error);
      setIsRecordingVoice(false);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }
  }, [enableVoiceAnnotations]);
  
  const handleStopVoiceRecording = useCallback(async () => {
    if (!isRecordingVoice || !voiceServiceRef.current) return;
    
    try {
      const voiceAnnotation = await voiceServiceRef.current.stopRecording();
      setIsRecordingVoice(false);
      recordingAnim.stopAnimation();
      recordingAnim.setValue(0);
      
      // Add voice annotation
      if (voiceAnnotation) {
        setAnnotations(prev => [...prev, voiceAnnotation]);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
      
    } catch (error) {
      console.error('Failed to stop voice recording:', error);
      setIsRecordingVoice(false);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }
  }, [isRecordingVoice]);
  
  // Add comment
  const handleAddComment = useCallback((text: string) => {
    const comment: MobileComment = {
      id: `comment_${Date.now()}`,
      userId: currentUser.id,
      text,
      timestamp: new Date(),
      position: { line: 0, column: selectionRange.start },
      resolved: false,
      replies: []
    };
    
    setComments(prev => [...prev, comment]);
    collaborationEngineRef.current?.addComment(comment);
    Haptics.impactAsync(HapticsImpactType.Light);
  }, [currentUser.id, selectionRange.start]);
  
  // Create annotation
  const handleCreateAnnotation = useCallback((type: string) => {
    if (!selectedText) return;
    
    const annotation: MobileAnnotation = {
      id: `annotation_${Date.now()}`,
      userId: currentUser.id,
      type: type as any,
      text: selectedText,
      start: selectionRange.start,
      end: selectionRange.end,
      color: currentUser.color,
      timestamp: new Date()
    };
    
    setAnnotations(prev => [...prev, annotation]);
    collaborationEngineRef.current?.addAnnotation(annotation);
    setShowContextMenu(false);
    Haptics.impactAsync(HapticsImpactType.Medium);
  }, [selectedText, selectionRange, currentUser]);
  
  // Save handler
  const handleSave = useCallback(() => {
    if (onSave) {
      onSave(content);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }
  }, [content, onSave]);
  
  // Bottom sheet animation
  const animateBottomSheet = useCallback((show: boolean) => {
    Animated.timing(bottomSheetAnim, {
      toValue: show ? 1 : 0,
      duration: 300,
      easing: Easing.out(Easing.ease),
      useNativeDriver: true
    }).start();
  }, [bottomSheetAnim]);
  
  useEffect(() => {
    animateBottomSheet(showBottomSheet);
  }, [showBottomSheet, animateBottomSheet]);

  return (
    <GestureHandlerRootView style={isDark ? styles.darkContainer : styles.container}>
      <SafeAreaProvider>
        <StatusBar 
          barStyle={isDark ? 'light-content' : 'dark-content'}
          backgroundColor={isDark ? '#1a1a1a' : '#ffffff'}
        />
        
        {/* Offline indicator */}
        {offlineMode && (
          <View style={styles.offlineIndicator}>
            <Text style={styles.offlineText}>
              Offline Mode - Changes will sync when reconnected
            </Text>
          </View>
        )}
        
        {/* Header */}
        <View style={[styles.header, isDark && { backgroundColor: '#2d2d2d', borderBottomColor: '#404040' }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            {/* Connection status */}
            <View style={[
              styles.connectionIndicator,
              {
                backgroundColor:
                  connectionStatus === 'connected' ? '#10b981' :
                  connectionStatus === 'connecting' ? '#f59e0b' :
                  connectionStatus === 'syncing' ? '#3b82f6' : '#ef4444'
              }
            ]} />
            
            {/* Active users */}
            <View style={styles.userAvatars}>
              {activeUsers.slice(0, 4).map((user, index) => (
                <Animated.View
                  key={user.id}
                  style={[
                    styles.avatar,
                    { 
                      backgroundColor: user.color,
                      zIndex: activeUsers.length - index,
                      transform: user.isTyping ? [{ scale: presencePulse }] : []
                    }
                  ]}
                >
                  <Text style={styles.avatarText}>
                    {user.name.charAt(0).toUpperCase()}
                  </Text>
                </Animated.View>
              ))}
              
              {activeUsers.length > 4 && (
                <View style={[styles.avatar, { backgroundColor: '#6b7280' }]}>
                  <Text style={styles.avatarText}>+{activeUsers.length - 4}</Text>
                </View>
              )}
            </View>
            
            {/* Typing indicator */}
            {typingUsers.length > 0 && (
              <View style={styles.typingIndicator}>
                <Text style={styles.typingText}>
                  {typingUsers.length === 1 
                    ? `${typingUsers[0].name} typing...`
                    : `${typingUsers.length} typing...`
                  }
                </Text>
              </View>
            )}
          </View>
          
          {/* Header actions */}
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <TouchableOpacity onPress={handleSave}>
              <Icon name="save" size={24} color="#007AFF" />
            </TouchableOpacity>
            
            <TouchableOpacity 
              onPress={() => setShowBottomSheet(true)}
              style={{ marginLeft: 16 }}
            >
              <Icon name="people" size={24} color="#007AFF" />
            </TouchableOpacity>
          </View>
        </View>
        
        {/* Main editor */}
        <KeyboardAvoidingView 
          style={{ flex: 1 }} 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.editorContainer}>
            <LongPressGestureHandler onHandlerStateChange={handleLongPress}>
              <TextInput
                ref={editorRef}
                style={[styles.editor, isDark && styles.darkEditor]}
                value={content}
                onChangeText={handleContentChange}
                onSelectionChange={handleSelectionChange}
                multiline
                placeholder={readOnly ? "Read-only mode" : "Start typing to collaborate..."}
                placeholderTextColor={isDark ? '#9ca3af' : '#6b7280'}
                editable={!readOnly}
                scrollEnabled
                textAlignVertical="top"
                selectionColor="#007AFF"
              />
            </LongPressGestureHandler>
            
            {/* Presence cursors and selections */}
            {users.filter(u => u.id !== currentUser.id).map(user => (
              <React.Fragment key={user.id}>
                {/* Cursor */}
                {user.cursor && (
                  <View
                    style={[
                      styles.presenceCursor,
                      {
                        backgroundColor: user.color,
                        left: user.cursor.x,
                        top: user.cursor.y
                      }
                    ]}
                  />
                )}
                
                {/* Selection */}
                {user.selection && (
                  <View
                    style={[
                      styles.selectionHighlight,
                      {
                        backgroundColor: user.color + '40',
                        // Position based on selection range
                      }
                    ]}
                  />
                )}
              </React.Fragment>
            ))}
            
            {/* Annotations */}
            {annotations.map(annotation => (
              <TouchableOpacity
                key={annotation.id}
                style={[
                  annotation.type === 'medical_term' 
                    ? styles.medicalTermHighlight 
                    : styles.annotationHighlight,
                  {
                    // Position based on annotation range
                  }
                ]}
                onPress={() => {
                  // Show annotation details
                }}
              />
            ))}
          </View>
        </KeyboardAvoidingView>
        
        {/* Floating action buttons */}
        {!keyboardVisible && (
          <View style={styles.floatingButtons}>
            {/* Voice recording button */}
            {enableVoiceAnnotations && (
              <TouchableOpacity
                style={[
                  styles.floatingButton,
                  styles.smallFloatingButton,
                  isRecordingVoice && styles.voiceRecordingButton
                ]}
                onPressIn={handleStartVoiceRecording}
                onPressOut={handleStopVoiceRecording}
              >
                {isRecordingVoice && (
                  <Animated.View
                    style={[
                      styles.recordingAnimation,
                      {
                        transform: [
                          {
                            scale: recordingAnim.interpolate({
                              inputRange: [0, 1],
                              outputRange: [1, 1.5]
                            })
                          }
                        ],
                        opacity: recordingAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: [0.3, 0.1]
                        })
                      }
                    ]}
                  />
                )}
                <Icon 
                  name={isRecordingVoice ? "stop" : "mic"} 
                  size={24} 
                  color="#ffffff" 
                />
              </TouchableOpacity>
            )}
            
            {/* Add comment button */}
            <TouchableOpacity
              style={[styles.floatingButton, styles.smallFloatingButton]}
              onPress={() => {
                // Show comment dialog
              }}
            >
              <Icon name="comment" size={24} color="#ffffff" />
            </TouchableOpacity>
            
            {/* Main collaboration button */}
            <TouchableOpacity
              style={styles.floatingButton}
              onPress={() => setShowBottomSheet(true)}
            >
              <Icon name="people" size={28} color="#ffffff" />
            </TouchableOpacity>
          </View>
        )}
        
        {/* Context menu */}
        {showContextMenu && (
          <TouchableOpacity
            style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
            onPress={() => setShowContextMenu(false)}
            activeOpacity={1}
          >
            <View
              style={[
                styles.contextMenu,
                {
                  left: contextMenuPosition.x - 100,
                  top: contextMenuPosition.y - 160
                }
              ]}
            >
              <TouchableOpacity
                style={styles.contextMenuItem}
                onPress={() => handleCreateAnnotation('highlight')}
              >
                <Icon name="highlight" size={20} color="#1f2937" />
                <Text style={styles.contextMenuText}>Highlight</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={styles.contextMenuItem}
                onPress={() => handleCreateAnnotation('medical_term')}
              >
                <Icon name="local-hospital" size={20} color="#1f2937" />
                <Text style={styles.contextMenuText}>Medical Term</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={styles.contextMenuItem}
                onPress={() => handleCreateAnnotation('correction')}
              >
                <Icon name="edit" size={20} color="#1f2937" />
                <Text style={styles.contextMenuText}>Correction</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={styles.contextMenuItem}
                onPress={() => {
                  Share.share({ message: selectedText });
                  setShowContextMenu(false);
                }}
              >
                <Icon name="share" size={20} color="#1f2937" />
                <Text style={styles.contextMenuText}>Share</Text>
              </TouchableOpacity>
            </View>
          </TouchableOpacity>
        )}
        
        {/* Bottom sheet */}
        {showBottomSheet && (
          <Animated.View
            style={[
              styles.bottomSheet,
              {
                transform: [
                  {
                    translateY: bottomSheetAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: [500, 0]
                    })
                  }
                ]
              }
            ]}
          >
            <TouchableOpacity
              style={styles.bottomSheetHandle}
              onPress={() => setShowBottomSheet(false)}
            />
            
            {/* Tab bar */}
            <View style={styles.tabBar}>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 0 && styles.activeTab]}
                onPress={() => setSelectedTab(0)}
              >
                <Text style={[styles.tabText, selectedTab === 0 && styles.activeTabText]}>
                  Users ({activeUsers.length})
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.tab, selectedTab === 1 && styles.activeTab]}
                onPress={() => setSelectedTab(1)}
              >
                <Text style={[styles.tabText, selectedTab === 1 && styles.activeTabText]}>
                  Comments ({unresolvedComments.length})
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.tab, selectedTab === 2 && styles.activeTab]}
                onPress={() => setSelectedTab(2)}
              >
                <Text style={[styles.tabText, selectedTab === 2 && styles.activeTabText]}>
                  Medical
                </Text>
              </TouchableOpacity>
            </View>
            
            <ScrollView style={{ flex: 1 }}>
              {/* Users tab */}
              {selectedTab === 0 && (
                <FlatList
                  data={users}
                  keyExtractor={(item) => item.id}
                  renderItem={({ item: user }) => (
                    <View style={styles.userItem}>
                      <View style={[styles.avatar, { backgroundColor: user.color }]}>
                        <Text style={styles.avatarText}>
                          {user.name.charAt(0).toUpperCase()}
                        </Text>
                      </View>
                      
                      <View style={styles.userInfo}>
                        <Text style={styles.userName}>{user.name}</Text>
                        <Text style={styles.userStatus}>
                          {user.role.replace('_', ' ').toUpperCase()} • {user.deviceInfo.platform}
                        </Text>
                        <Text style={styles.userStatus}>
                          {user.isOnline 
                            ? user.isTyping 
                              ? 'Typing...' 
                              : 'Online'
                            : `Last seen ${user.lastActivity.toLocaleTimeString()}`
                          }
                        </Text>
                      </View>
                      
                      <View style={styles.userActions}>
                        {user.deviceInfo.hasVoiceCapabilities && (
                          <TouchableOpacity style={styles.actionButton}>
                            <Icon name="mic" size={16} color="#6b7280" />
                          </TouchableOpacity>
                        )}
                        
                        <TouchableOpacity style={styles.actionButton}>
                          <Icon name="message" size={16} color="#6b7280" />
                        </TouchableOpacity>
                      </View>
                    </View>
                  )}
                  scrollEnabled={false}
                />
              )}
              
              {/* Comments tab */}
              {selectedTab === 1 && (
                <FlatList
                  data={comments}
                  keyExtractor={(item) => item.id}
                  renderItem={({ item: comment }) => (
                    <View style={styles.commentItem}>
                      <Text style={styles.commentText}>{comment.text}</Text>
                      <View style={styles.commentMeta}>
                        <Text style={styles.commentAuthor}>
                          {users.find(u => u.id === comment.userId)?.name || 'Unknown User'}
                        </Text>
                        <Text style={styles.commentTime}>
                          {comment.timestamp.toLocaleString()}
                        </Text>
                      </View>
                      
                      {comment.voiceNote && (
                        <TouchableOpacity
                          style={{ marginTop: 8, flexDirection: 'row', alignItems: 'center' }}
                          onPress={() => {
                            // Play voice note
                          }}
                        >
                          <Icon name="play-arrow" size={20} color="#007AFF" />
                          <Text style={{ marginLeft: 4, color: '#007AFF' }}>
                            Voice note ({Math.round(comment.voiceNote.duration)}s)
                          </Text>
                        </TouchableOpacity>
                      )}
                    </View>
                  )}
                  scrollEnabled={false}
                />
              )}
              
              {/* Medical validation tab */}
              {selectedTab === 2 && medicalValidation && (
                <View style={styles.medicalValidation}>
                  <Text style={styles.validationTitle}>Medical Validation</Text>
                  
                  <View style={styles.validationMetrics}>
                    <View style={styles.metricItem}>
                      <Text style={styles.metricValue}>
                        {Math.round(medicalValidation.accuracy * 100)}%
                      </Text>
                      <Text style={styles.metricLabel}>Accuracy</Text>
                    </View>
                    
                    <View style={styles.metricItem}>
                      <Text style={styles.metricValue}>
                        {Math.round(medicalValidation.completeness * 100)}%
                      </Text>
                      <Text style={styles.metricLabel}>Completeness</Text>
                    </View>
                    
                    <View style={styles.metricItem}>
                      <Text style={styles.metricValue}>
                        {medicalValidation.medicalTermCount}
                      </Text>
                      <Text style={styles.metricLabel}>Terms</Text>
                    </View>
                  </View>
                  
                  <FlatList
                    data={medicalValidation.errors}
                    keyExtractor={(item, index) => index.toString()}
                    renderItem={({ item: error }) => (
                      <View style={styles.validationError}>
                        <Icon 
                          name={error.severity === 'error' ? 'error' : 'warning'} 
                          size={20} 
                          color="#dc2626"
                          style={styles.errorIcon}
                        />
                        <Text style={styles.errorText}>{error.message}</Text>
                      </View>
                    )}
                    scrollEnabled={false}
                  />
                </View>
              )}
            </ScrollView>
          </Animated.View>
        )}
        
        {/* Loading overlay */}
        {isLoading && (
          <View style={styles.loadingOverlay}>
            <BlurView
              style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
              blurType="light"
              blurAmount={10}
            />
            <View style={styles.loadingContent}>
              <Icon name="sync" size={32} color="#007AFF" />
              <Text style={styles.loadingText}>Connecting to collaboration...</Text>
            </View>
          </View>
        )}
        
        {/* Toolbar */}
        {!showBottomSheet && !keyboardVisible && (
          <View style={styles.toolBar}>
            <TouchableOpacity 
              style={[styles.toolButton, isRecordingVoice && styles.toolButtonActive]}
              onPress={isRecordingVoice ? handleStopVoiceRecording : handleStartVoiceRecording}
            >
              <Icon 
                name={isRecordingVoice ? "stop" : "mic"} 
                size={16} 
                color={isRecordingVoice ? "#ffffff" : "#6b7280"} 
              />
              <Text style={[styles.toolButtonText, isRecordingVoice && styles.toolButtonTextActive]}>
                Voice
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.toolButton}>
              <Icon name="comment" size={16} color="#6b7280" />
              <Text style={styles.toolButtonText}>Comment</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.toolButton}>
              <Icon name="highlight" size={16} color="#6b7280" />
              <Text style={styles.toolButtonText}>Highlight</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.toolButton}>
              <Icon name="local-hospital" size={16} color="#6b7280" />
              <Text style={styles.toolButtonText}>Medical</Text>
            </TouchableOpacity>
          </View>
        )}
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
};

export default CollaborativeMedicalEditor;