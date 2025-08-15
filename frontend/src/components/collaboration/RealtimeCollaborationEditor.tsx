/**
 * Real-time Collaboration Editor Component
 * Multi-user editing with presence awareness, operational transforms, and medical schema integration
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  AvatarGroup,
  Chip,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Badge,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction,
  Divider,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  LinearProgress,
  Grid,
  Tabs,
  Tab,
  Popper,
  ClickAwayListener,
  Grow
} from '@mui/material';
import {
  Edit as EditIcon,
  People as PeopleIcon,
  Comment as CommentIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  PersonAdd as PersonAddIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
  Share as ShareIcon,
  Save as SaveIcon,
  Sync as SyncIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Close as CloseIcon,
  MoreVert as MoreVertIcon,
  VolumeUp as VolumeUpIcon,
  VolumeOff as VolumeOffIcon,
  Notifications as NotificationsIcon,
  NotificationsOff as NotificationsOffIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { WebSocketManager } from '../../services/websocketManager';
import { CollaborationEngine } from '../../services/collaborationEngine';
import { MedicalSchemaIntegrator } from '../../services/medicalSchemaIntegrator';
import { PresenceTracker } from '../../services/presenceTracker';
import { AnnotationEngine } from '../../services/annotationEngine';

// Enhanced styling for collaboration features
const CollaborationContainer = styled(Paper)(({ theme }) => ({
  minHeight: '600px',
  display: 'flex',
  flexDirection: 'column',
  position: 'relative',
  backgroundColor: theme.palette.background.paper,
  boxShadow: theme.shadows[8],
  borderRadius: theme.spacing(2),
  overflow: 'hidden'
}));

const EditorHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(1.5, 2),
  borderBottom: `1px solid ${theme.palette.divider}`,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  backgroundColor: theme.palette.background.default
}));

const EditorContent = styled(Box)(({ theme }) => ({
  flex: 1,
  position: 'relative',
  overflow: 'hidden',
  backgroundColor: theme.palette.background.paper
}));

const PresenceIndicator = styled(Box)(({ theme, color }) => ({
  position: 'absolute',
  width: '12px',
  height: '12px',
  borderRadius: '50%',
  backgroundColor: color || theme.palette.primary.main,
  border: `2px solid ${theme.palette.background.paper}`,
  boxShadow: theme.shadows[2],
  zIndex: 1000
}));

const CollaborationSidebar = styled(Box)(({ theme }) => ({
  width: '320px',
  borderLeft: `1px solid ${theme.palette.divider}`,
  backgroundColor: theme.palette.background.default,
  display: 'flex',
  flexDirection: 'column'
}));

const AnnotationPopover = styled(Paper)(({ theme }) => ({
  maxWidth: '300px',
  padding: theme.spacing(2),
  backgroundColor: theme.palette.background.paper,
  border: `1px solid ${theme.palette.divider}`,
  boxShadow: theme.shadows[8]
}));

const StatusIndicator = styled(Box)(({ theme, status }) => {
  const colors = {
    connected: theme.palette.success.main,
    connecting: theme.palette.warning.main,
    disconnected: theme.palette.error.main,
    syncing: theme.palette.info.main
  };
  
  return {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: colors[status] || colors.disconnected,
    marginRight: theme.spacing(1),
    animation: status === 'syncing' ? 'pulse 1.5s infinite' : 'none',
    '@keyframes pulse': {
      '0%': { opacity: 1 },
      '50%': { opacity: 0.5 },
      '100%': { opacity: 1 }
    }
  };
});

// Types
interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'owner' | 'editor' | 'reviewer' | 'viewer' | 'medical_professional';
  color: string;
  isOnline: boolean;
  isTyping: boolean;
  cursor?: { line: number; column: number };
  selection?: { start: number; end: number };
  lastActivity: Date;
  permissions: {
    canEdit: boolean;
    canComment: boolean;
    canShare: boolean;
    canManageUsers: boolean;
    requiresMedicalReview: boolean;
  };
}

interface Comment {
  id: string;
  userId: string;
  text: string;
  timestamp: Date;
  position: { line: number; column: number };
  resolved: boolean;
  replies: Comment[];
  medicalPriority?: 'low' | 'medium' | 'high' | 'critical';
  requiresReview?: boolean;
}

interface Annotation {
  id: string;
  userId: string;
  type: 'highlight' | 'medical_term' | 'correction' | 'note' | 'warning';
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
    requiresValidation: boolean;
  };
}

interface Props {
  documentId: string;
  initialContent?: string;
  readOnly?: boolean;
  enableMedicalValidation?: boolean;
  onSave?: (content: string) => void;
  onError?: (error: Error) => void;
  currentUser: User;
}

const RealtimeCollaborationEditor: React.FC<Props> = ({
  documentId,
  initialContent = '',
  readOnly = false,
  enableMedicalValidation = true,
  onSave,
  onError,
  currentUser
}) => {
  // State management
  const [content, setContent] = useState(initialContent);
  const [users, setUsers] = useState<User[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'syncing'>('connecting');
  const [isLocked, setIsLocked] = useState(false);
  const [lockHolder, setLockHolder] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [selectedTab, setSelectedTab] = useState(0);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);
  
  // Dialog states
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [showHistoryDialog, setShowHistoryDialog] = useState(false);
  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [commentPosition, setCommentPosition] = useState<{ line: number; column: number } | null>(null);
  
  // Menu states
  const [userMenuAnchor, setUserMenuAnchor] = useState<HTMLElement | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  
  // Notification state
  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'warning' | 'info'; message: string } | null>(null);
  
  // Refs
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const wsManagerRef = useRef<WebSocketManager | null>(null);
  const collaborationEngineRef = useRef<CollaborationEngine | null>(null);
  const medicalIntegratorRef = useRef<MedicalSchemaIntegrator | null>(null);
  const presenceTrackerRef = useRef<PresenceTracker | null>(null);
  const annotationEngineRef = useRef<AnnotationEngine | null>(null);
  
  // Memoized values
  const activeUsers = useMemo(() => users.filter(user => user.isOnline), [users]);
  const typingUsers = useMemo(() => users.filter(user => user.isTyping && user.id !== currentUser.id), [users, currentUser.id]);
  const unresolvedComments = useMemo(() => comments.filter(comment => !comment.resolved), [comments]);
  const medicalAnnotations = useMemo(() => annotations.filter(ann => ann.type === 'medical_term'), [annotations]);
  const canEdit = useMemo(() => {
    return !readOnly && 
           currentUser.permissions.canEdit && 
           (!isLocked || lockHolder === currentUser.id);
  }, [readOnly, currentUser.permissions.canEdit, isLocked, lockHolder, currentUser.id]);
  
  // Initialize collaboration systems
  useEffect(() => {
    const initializeCollaboration = async () => {
      try {
        // Initialize WebSocket connection
        wsManagerRef.current = new WebSocketManager(`ws://localhost:8000/api/v1/collaboration/ws`);
        await wsManagerRef.current.connect();
        
        // Initialize collaboration engine
        collaborationEngineRef.current = new CollaborationEngine(documentId, currentUser);
        await collaborationEngineRef.current.initialize(wsManagerRef.current);
        
        // Initialize medical schema integrator
        if (enableMedicalValidation) {
          medicalIntegratorRef.current = new MedicalSchemaIntegrator();
          await medicalIntegratorRef.current.initialize();
        }
        
        // Initialize presence tracker
        presenceTrackerRef.current = new PresenceTracker(documentId, currentUser);
        await presenceTrackerRef.current.initialize(wsManagerRef.current);
        
        // Initialize annotation engine
        annotationEngineRef.current = new AnnotationEngine(documentId, currentUser);
        await annotationEngineRef.current.initialize(wsManagerRef.current);
        
        // Set up event handlers
        setupEventHandlers();
        
        setConnectionStatus('connected');
        showNotification('success', 'Connected to collaboration session');
      } catch (error) {
        console.error('Failed to initialize collaboration:', error);
        setConnectionStatus('disconnected');
        showNotification('error', 'Failed to connect to collaboration session');
        onError?.(error as Error);
      }
    };
    
    initializeCollaboration();
    
    return () => {
      // Cleanup
      wsManagerRef.current?.disconnect();
      collaborationEngineRef.current?.cleanup();
      presenceTrackerRef.current?.cleanup();
      annotationEngineRef.current?.cleanup();
    };
  }, [documentId, currentUser, enableMedicalValidation, onError]);
  
  // Event handlers setup
  const setupEventHandlers = useCallback(() => {
    if (!collaborationEngineRef.current || !presenceTrackerRef.current || !annotationEngineRef.current) return;
    
    // Content change events
    collaborationEngineRef.current.onContentChange((newContent) => {
      setContent(newContent);
      setConnectionStatus('connected');
    });
    
    // User presence events
    presenceTrackerRef.current.onUserJoin((user) => {
      setUsers(prev => [...prev.filter(u => u.id !== user.id), user]);
      if (notificationsEnabled) {
        showNotification('info', `${user.name} joined the session`);
      }
    });
    
    presenceTrackerRef.current.onUserLeave((userId) => {
      setUsers(prev => prev.filter(u => u.id !== userId));
    });
    
    presenceTrackerRef.current.onUserActivity((userId, activity) => {
      setUsers(prev => prev.map(user => 
        user.id === userId 
          ? { ...user, ...activity, lastActivity: new Date() }
          : user
      ));
    });
    
    // Comment events
    annotationEngineRef.current.onCommentAdded((comment) => {
      setComments(prev => [...prev, comment]);
      if (comment.userId !== currentUser.id && notificationsEnabled) {
        showNotification('info', `New comment from ${users.find(u => u.id === comment.userId)?.name || 'User'}`);
      }
    });
    
    annotationEngineRef.current.onCommentResolved((commentId) => {
      setComments(prev => prev.map(comment => 
        comment.id === commentId ? { ...comment, resolved: true } : comment
      ));
    });
    
    // Annotation events
    annotationEngineRef.current.onAnnotationAdded((annotation) => {
      setAnnotations(prev => [...prev, annotation]);
      if (annotation.medicalContext?.requiresValidation && annotation.userId !== currentUser.id) {
        showNotification('warning', 'New medical annotation requires validation');
      }
    });
    
    // Lock events
    collaborationEngineRef.current.onLockChanged((locked, holderId) => {
      setIsLocked(locked);
      setLockHolder(holderId);
      if (locked && holderId !== currentUser.id) {
        const holderName = users.find(u => u.id === holderId)?.name || 'Another user';
        showNotification('warning', `Document locked by ${holderName}`);
      }
    });
    
    // Connection status events
    wsManagerRef.current?.onConnectionChange((status) => {
      setConnectionStatus(status);
      if (status === 'disconnected') {
        showNotification('error', 'Connection lost. Attempting to reconnect...');
      } else if (status === 'connected') {
        showNotification('success', 'Reconnected to session');
      }
    });
  }, [currentUser, users, notificationsEnabled]);
  
  // Content change handler
  const handleContentChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (!canEdit) return;
    
    const newContent = event.target.value;
    setContent(newContent);
    setConnectionStatus('syncing');
    
    // Apply operational transform and send changes
    collaborationEngineRef.current?.applyChange(newContent);
    
    // Track cursor position
    const cursorPosition = event.target.selectionStart;
    presenceTrackerRef.current?.updateCursorPosition(cursorPosition);
    
    // Medical validation
    if (enableMedicalValidation && medicalIntegratorRef.current) {
      medicalIntegratorRef.current.validateContent(newContent).then(validation => {
        if (validation.hasErrors) {
          showNotification('warning', `${validation.errors.length} medical validation issues found`);
        }
      });
    }
  }, [canEdit, enableMedicalValidation]);
  
  // Lock management
  const handleToggleLock = useCallback(() => {
    if (isLocked && lockHolder === currentUser.id) {
      collaborationEngineRef.current?.releaseLock();
    } else if (!isLocked) {
      collaborationEngineRef.current?.acquireLock();
    }
  }, [isLocked, lockHolder, currentUser.id]);
  
  // Comment management
  const handleAddComment = useCallback((text: string, position: { line: number; column: number }) => {
    const comment: Comment = {
      id: `comment_${Date.now()}`,
      userId: currentUser.id,
      text,
      timestamp: new Date(),
      position,
      resolved: false,
      replies: []
    };
    
    annotationEngineRef.current?.addComment(comment);
    setShowCommentDialog(false);
    setCommentPosition(null);
  }, [currentUser.id]);
  
  const handleResolveComment = useCallback((commentId: string) => {
    annotationEngineRef.current?.resolveComment(commentId);
  }, []);
  
  // Annotation management
  const handleCreateAnnotation = useCallback((type: string, start: number, end: number, note?: string) => {
    const selectedText = content.substring(start, end);
    const annotation: Annotation = {
      id: `annotation_${Date.now()}`,
      userId: currentUser.id,
      type: type as any,
      text: selectedText,
      note,
      start,
      end,
      color: currentUser.color,
      timestamp: new Date()
    };
    
    // Add medical context if it's a medical term
    if (type === 'medical_term' && medicalIntegratorRef.current) {
      medicalIntegratorRef.current.analyzeMedicalTerm(selectedText).then(analysis => {
        annotation.medicalContext = {
          terminology: analysis.terminology,
          category: analysis.category,
          confidence: analysis.confidence,
          requiresValidation: analysis.confidence < 0.8
        };
        annotationEngineRef.current?.addAnnotation(annotation);
      });
    } else {
      annotationEngineRef.current?.addAnnotation(annotation);
    }
  }, [content, currentUser]);
  
  // Save handler
  const handleSave = useCallback(() => {
    if (onSave) {
      onSave(content);
      showNotification('success', 'Document saved successfully');
    }
  }, [content, onSave]);
  
  // Notification helper
  const showNotification = useCallback((type: 'success' | 'error' | 'warning' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  }, []);
  
  // User menu handlers
  const handleUserMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>, userId: string) => {
    setUserMenuAnchor(event.currentTarget);
    setSelectedUserId(userId);
  }, []);
  
  const handleUserMenuClose = useCallback(() => {
    setUserMenuAnchor(null);
    setSelectedUserId(null);
  }, []);

  return (
    <CollaborationContainer>
      {/* Header */}
      <EditorHeader>
        <Box display="flex" alignItems="center" gap={1}>
          <StatusIndicator status={connectionStatus} />
          <Typography variant="h6" sx={{ mr: 2 }}>
            Real-time Collaboration
          </Typography>
          
          {/* Active users */}
          <AvatarGroup max={5} sx={{ mr: 2 }}>
            {activeUsers.map(user => (
              <Tooltip key={user.id} title={`${user.name} (${user.role})`}>
                <Badge
                  overlap="circular"
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  badgeContent={user.isTyping ? <EditIcon fontSize="small" /> : null}
                >
                  <Avatar
                    sx={{ 
                      bgcolor: user.color,
                      width: 32,
                      height: 32,
                      fontSize: '0.875rem',
                      cursor: 'pointer'
                    }}
                    onClick={(e) => handleUserMenuOpen(e, user.id)}
                  >
                    {user.name.charAt(0).toUpperCase()}
                  </Avatar>
                </Badge>
              </Tooltip>
            ))}
          </AvatarGroup>
          
          {/* Typing indicators */}
          {typingUsers.length > 0 && (
            <Chip
              size="small"
              icon={<EditIcon />}
              label={`${typingUsers.map(u => u.name).join(', ')} typing...`}
              color="primary"
              variant="outlined"
            />
          )}
        </Box>
        
        <Box display="flex" alignItems="center" gap={1}>
          {/* Lock status */}
          {isLocked && (
            <Chip
              size="small"
              icon={<LockIcon />}
              label={lockHolder === currentUser.id ? 'Locked by you' : `Locked by ${users.find(u => u.id === lockHolder)?.name || 'User'}`}
              color={lockHolder === currentUser.id ? 'success' : 'warning'}
              variant="filled"
            />
          )}
          
          {/* Control buttons */}
          <Tooltip title={isLocked ? 'Release lock' : 'Acquire lock'}>
            <IconButton onClick={handleToggleLock} disabled={isLocked && lockHolder !== currentUser.id}>
              {isLocked ? <LockIcon /> : <LockOpenIcon />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Save document">
            <IconButton onClick={handleSave} disabled={!canEdit}>
              <SaveIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Invite users">
            <IconButton onClick={() => setShowInviteDialog(true)}>
              <PersonAddIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Settings">
            <IconButton onClick={() => setShowSettingsDialog(true)}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={showSidebar ? 'Hide sidebar' : 'Show sidebar'}>
            <IconButton onClick={() => setShowSidebar(!showSidebar)}>
              {showSidebar ? <VisibilityOffIcon /> : <VisibilityIcon />}
            </IconButton>
          </Tooltip>
        </Box>
      </EditorHeader>
      
      {/* Main content area */}
      <Box display="flex" flex={1}>
        {/* Editor */}
        <EditorContent>
          <Box position="relative" height="100%">
            <TextField
              ref={editorRef}
              multiline
              fullWidth
              value={content}
              onChange={handleContentChange}
              disabled={!canEdit}
              placeholder={canEdit ? "Start typing to collaborate..." : "Read-only mode"}
              variant="outlined"
              InputProps={{
                sx: {
                  height: '100%',
                  '& .MuiInputBase-input': {
                    height: '100% !important',
                    overflow: 'auto !important'
                  }
                }
              }}
              sx={{
                height: '100%',
                '& .MuiOutlinedInput-root': {
                  height: '100%'
                }
              }}
            />
            
            {/* Presence indicators for other users */}
            {users.filter(u => u.id !== currentUser.id && u.cursor).map(user => (
              <PresenceIndicator
                key={user.id}
                color={user.color}
                style={{
                  top: `${(user.cursor?.line || 0) * 20}px`,
                  left: `${(user.cursor?.column || 0) * 8}px`
                }}
              />
            ))}
          </Box>
        </EditorContent>
        
        {/* Collaboration sidebar */}
        {showSidebar && (
          <CollaborationSidebar>
            <Tabs
              value={selectedTab}
              onChange={(_, newValue) => setSelectedTab(newValue)}
              variant="fullWidth"
            >
              <Tab label={`Users (${activeUsers.length})`} icon={<PeopleIcon />} />
              <Tab label={`Comments (${unresolvedComments.length})`} icon={<CommentIcon />} />
              <Tab label="History" icon={<HistoryIcon />} />
            </Tabs>
            
            <Box flex={1} overflow="auto" p={1}>
              {/* Users tab */}
              {selectedTab === 0 && (
                <List>
                  {users.map(user => (
                    <ListItem key={user.id}>
                      <ListItemAvatar>
                        <Badge
                          overlap="circular"
                          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                          badgeContent={
                            <Box
                              sx={{
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                backgroundColor: user.isOnline ? 'success.main' : 'grey.400',
                                border: '2px solid white'
                              }}
                            />
                          }
                        >
                          <Avatar sx={{ bgcolor: user.color }}>
                            {user.name.charAt(0).toUpperCase()}
                          </Avatar>
                        </Badge>
                      </ListItemAvatar>
                      <ListItemText
                        primary={user.name}
                        secondary={
                          <Box>
                            <Typography variant="caption" display="block">
                              {user.role.replace('_', ' ').toUpperCase()}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {user.isOnline 
                                ? user.isTyping 
                                  ? 'Typing...' 
                                  : 'Online'
                                : `Last seen ${user.lastActivity.toLocaleTimeString()}`
                              }
                            </Typography>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton edge="end" onClick={(e) => handleUserMenuOpen(e, user.id)}>
                          <MoreVertIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
              
              {/* Comments tab */}
              {selectedTab === 1 && (
                <Box>
                  <Button
                    fullWidth
                    startIcon={<CommentIcon />}
                    onClick={() => setShowCommentDialog(true)}
                    sx={{ mb: 2 }}
                  >
                    Add Comment
                  </Button>
                  <List>
                    {comments.map(comment => (
                      <ListItem key={comment.id}>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: users.find(u => u.id === comment.userId)?.color || '#ccc' }}>
                            {users.find(u => u.id === comment.userId)?.name.charAt(0).toUpperCase() || '?'}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={comment.text}
                          secondary={
                            <Box>
                              <Typography variant="caption" display="block">
                                {users.find(u => u.id === comment.userId)?.name || 'Unknown User'}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                {comment.timestamp.toLocaleString()}
                              </Typography>
                              {comment.medicalPriority && (
                                <Chip
                                  size="small"
                                  label={comment.medicalPriority}
                                  color={comment.medicalPriority === 'critical' ? 'error' : 'warning'}
                                  sx={{ ml: 1 }}
                                />
                              )}
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          {!comment.resolved && (
                            <IconButton
                              edge="end"
                              onClick={() => handleResolveComment(comment.id)}
                            >
                              <CheckCircleIcon />
                            </IconButton>
                          )}
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
              
              {/* History tab */}
              {selectedTab === 2 && (
                <Box p={2}>
                  <Typography variant="body2" color="textSecondary">
                    Document history and version control coming soon...
                  </Typography>
                </Box>
              )}
            </Box>
          </CollaborationSidebar>
        )}
      </Box>
      
      {/* Progress indicator for syncing */}
      {connectionStatus === 'syncing' && (
        <LinearProgress 
          sx={{ 
            position: 'absolute', 
            bottom: 0, 
            left: 0, 
            right: 0 
          }} 
        />
      )}
      
      {/* User menu */}
      <Menu
        anchorEl={userMenuAnchor}
        open={Boolean(userMenuAnchor)}
        onClose={handleUserMenuClose}
      >
        <MenuItem onClick={handleUserMenuClose}>View Profile</MenuItem>
        <MenuItem onClick={handleUserMenuClose}>Send Message</MenuItem>
        <MenuItem onClick={handleUserMenuClose}>Share Screen</MenuItem>
      </Menu>
      
      {/* Notifications */}
      <Snackbar
        open={Boolean(notification)}
        autoHideDuration={5000}
        onClose={() => setNotification(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setNotification(null)}
          severity={notification?.type}
          sx={{ width: '100%' }}
        >
          {notification?.message}
        </Alert>
      </Snackbar>
    </CollaborationContainer>
  );
};

export default RealtimeCollaborationEditor;