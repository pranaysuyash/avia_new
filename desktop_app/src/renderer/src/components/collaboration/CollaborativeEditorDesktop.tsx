import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Avatar,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction,
  Badge,
  Tooltip,
  CircularProgress,
  Fade,
  Slide,
  Alert,
  Snackbar,
  Paper,
  Divider,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent
} from '@mui/material';
import {
  Edit as EditIcon,
  Comment as CommentIcon,
  People as PeopleIcon,
  Save as SaveIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Share as ShareIcon,
  Undo as UndoIcon,
  Redo as RedoIcon,
  MoreVert as MoreVertIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  PersonAdd as PersonAddIcon,
  Close as CloseIcon,
  Send as SendIcon,
  Reply as ReplyIcon,
  Done as DoneIcon,
  DoneAll as DoneAllIcon,
  Sync as SyncIcon,
  CloudSync as CloudSyncIcon,
  Group as GroupIcon,
  Timeline as TimelineIcon,
  Code as CodeIcon,
  TextFields as TextFieldsIcon,
  FormatBold as FormatBoldIcon,
  FormatItalic as FormatItalicIcon,
  FormatUnderlined as FormatUnderlinedIcon,
  FormatColorText as FormatColorTextIcon,
  ExpandMore as ExpandMoreIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  PictureInPicture as PictureInPictureIcon,
  Notifications as NotificationsIcon,
  NotificationsOff as NotificationsOffIcon
} from '@mui/icons-material';
import { styled, alpha, useTheme } from '@mui/material/styles';
import { Resizable } from 're-resizable';
import CodeMirror from '@uiw/react-codemirror';
import { markdown } from '@codemirror/lang-markdown';
import { javascript } from '@codemirror/lang-javascript';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import { vsCodeKeymap } from '@codemirror/keymap';

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

// Styled components
const EditorContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100vh',
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  overflow: 'hidden',
  position: 'relative'
}));

const HeaderBar = styled(Paper)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing(2, 3),
  background: alpha(theme.palette.background.paper, 0.95),
  backdropFilter: 'blur(20px)',
  borderBottom: `1px solid ${alpha(theme.palette.divider, 0.12)}`,
  zIndex: 100
}));

const MainContent = styled(Box)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  overflow: 'hidden'
}));

const EditorPane = styled(Box)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  background: theme.palette.background.paper,
  position: 'relative'
}));

const SidePanel = styled(Drawer)(({ theme }) => ({
  '& .MuiDrawer-paper': {
    width: 400,
    background: alpha(theme.palette.background.paper, 0.95),
    backdropFilter: 'blur(20px)',
    borderLeft: `1px solid ${alpha(theme.palette.divider, 0.12)}`
  }
}));

const UserCursorOverlay = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'color' && prop !== 'position'
})<{ color: string; position: number }>(({ theme, color, position }) => ({
  position: 'absolute',
  width: '2px',
  height: '24px',
  background: color,
  left: `${position}px`,
  top: '0',
  zIndex: 10,
  pointerEvents: 'none',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: '-4px',
    left: '-4px',
    width: '10px',
    height: '10px',
    background: color,
    borderRadius: '50%',
    border: `2px solid ${theme.palette.background.paper}`
  }
}));

const CommentThread = styled(Paper)(({ theme }) => ({
  position: 'absolute',
  right: 420,
  minWidth: 300,
  maxWidth: 400,
  background: alpha(theme.palette.background.paper, 0.98),
  backdropFilter: 'blur(20px)',
  border: `1px solid ${alpha(theme.palette.divider, 0.12)}`,
  borderRadius: theme.spacing(2),
  boxShadow: theme.shadows[8],
  zIndex: 50
}));

const TypingIndicator = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  padding: theme.spacing(1, 2),
  background: alpha(theme.palette.info.main, 0.1),
  borderRadius: theme.spacing(2),
  '& .typing-dots': {
    display: 'flex',
    gap: 2,
    '& div': {
      width: 4,
      height: 4,
      borderRadius: '50%',
      background: theme.palette.info.main,
      animation: 'typing-bounce 1.4s infinite ease-in-out',
      '&:nth-of-type(1)': { animationDelay: '-0.32s' },
      '&:nth-of-type(2)': { animationDelay: '-0.16s' }
    }
  },
  '@keyframes typing-bounce': {
    '0%, 80%, 100%': { transform: 'scale(0)' },
    '40%': { transform: 'scale(1)' }
  }
}));

interface CollaborativeEditorDesktopProps {
  documentId: string;
  currentUser: User;
  onSave?: (content: string, version: number) => void;
  initialContent?: string;
  readOnly?: boolean;
  language?: string;
}

const CollaborativeEditorDesktop: React.FC<CollaborativeEditorDesktopProps> = ({
  documentId,
  currentUser,
  onSave,
  initialContent = '',
  readOnly = false,
  language = 'markdown'
}) => {
  const theme = useTheme();
  
  // State management
  const [document, setDocument] = useState<Document | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [content, setContent] = useState<string>(initialContent);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved');
  
  // UI state
  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [activePanel, setActivePanel] = useState<'users' | 'comments' | 'history'>('users');
  const [selectedText, setSelectedText] = useState<{start: number, end: number} | null>(null);
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [newCommentText, setNewCommentText] = useState('');
  const [menuAnchor, setMenuAnchor] = useState<HTMLElement | null>(null);
  const [notification, setNotification] = useState<{message: string, type: 'success' | 'error' | 'info'} | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showCursors, setShowCursors] = useState(true);
  const [enableNotifications, setEnableNotifications] = useState(true);
  const [autoSave, setAutoSave] = useState(true);

  // Advanced features
  const [versionHistory, setVersionHistory] = useState<any[]>([]);
  const [operationHistory, setOperationHistory] = useState<Operation[]>([]);
  const [activeCommentThread, setActiveCommentThread] = useState<string | null>(null);

  // Refs
  const editorRef = useRef<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const operationQueue = useRef<Operation[]>([]);

  // WebSocket connection with enhanced desktop features
  const connectWebSocket = useCallback(() => {
    const wsUrl = `ws://localhost:8000/api/v1/collaborate/${documentId}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      setIsConnected(true);
      setIsLoading(false);
      console.log('🔗 Connected to collaborative editing session');
      
      // Send enhanced user info for desktop
      ws.send(JSON.stringify({
        type: 'user_join',
        user: {
          ...currentUser,
          capabilities: ['desktop', 'advanced_editing', 'version_history', 'bulk_operations'],
          client_info: {
            platform: 'electron',
            version: '1.0.0',
            features: ['syntax_highlighting', 'advanced_search', 'multi_cursor']
          }
        }
      }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      console.log('🔌 Disconnected from collaborative editing session');
      
      // Desktop-specific reconnection with backoff
      setTimeout(() => {
        if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
          connectWebSocket();
        }
      }, 5000);
    };
    
    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setNotification({ message: 'Connection error - attempting to reconnect', type: 'error' });
    };
    
    wsRef.current = ws;
  }, [documentId, currentUser]);

  // Enhanced WebSocket message handling
  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'initial_state':
        setDocument(data.document);
        setUsers(data.users || []);
        setComments(data.comments || []);
        setContent(data.document.content || '');
        setVersionHistory(data.version_history || []);
        break;
        
      case 'user_joined':
        setUsers(prev => [...prev.filter(u => u.user_id !== data.user.user_id), data.user]);
        if (enableNotifications) {
          setNotification({ message: `👋 ${data.user.username} joined the session`, type: 'info' });
        }
        break;
        
      case 'user_left':
        setUsers(prev => prev.filter(u => u.user_id !== data.user_id));
        if (enableNotifications) {
          setNotification({ message: `👋 ${data.username} left the session`, type: 'info' });
        }
        break;
        
      case 'document_updated':
        applyOperation(data.operation);
        setDocument(prev => prev ? { ...prev, version: data.document_version } : null);
        setOperationHistory(prev => [...prev, data.operation]);
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
        if (enableNotifications) {
          setNotification({ message: `💬 New comment from ${data.comment.username}`, type: 'info' });
        }
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
        if (data.status === 'saved' && enableNotifications) {
          setNotification({ message: '💾 Document auto-saved', type: 'success' });
        }
        break;
        
      case 'version_created':
        setVersionHistory(prev => [data.version, ...prev]);
        break;
        
      case 'error':
        setNotification({ message: `❌ ${data.message}`, type: 'error' });
        break;
    }
  }, [enableNotifications]);

  // Apply operation to content with CodeMirror integration
  const applyOperation = useCallback((operation: Operation) => {
    if (editorRef.current && editorRef.current.view) {
      const view = editorRef.current.view;
      const doc = view.state.doc;
      
      let changes;
      switch (operation.operation_type) {
        case 'insert':
          changes = { from: operation.position, insert: operation.content };
          break;
        case 'delete':
          changes = { 
            from: operation.position, 
            to: operation.position + (operation.length || 0), 
            insert: '' 
          };
          break;
        case 'replace':
          changes = { 
            from: operation.position, 
            to: operation.position + (operation.length || 0), 
            insert: operation.content 
          };
          break;
        default:
          return;
      }
      
      view.dispatch({ changes });
    } else {
      // Fallback for basic text editing
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
    }
  }, []);

  // Enhanced user management
  const updateUserCursor = useCallback((userId: string, position: number, selectionStart?: number, selectionEnd?: number) => {
    setUsers(prev => prev.map(user => 
      user.user_id === userId 
        ? { ...user, cursor_position: position, selection_start: selectionStart, selection_end: selectionEnd }
        : user
    ));
  }, []);

  const updateUserTypingStatus = useCallback((userId: string, isTyping: boolean) => {
    setUsers(prev => prev.map(user => 
      user.user_id === userId 
        ? { ...user, is_typing: isTyping }
        : user
    ));
  }, []);

  // Send operation to server with desktop-specific metadata
  const sendOperation = useCallback((operation: Partial<Operation>) => {
    if (!wsRef.current || !isConnected) return;
    
    const fullOperation: Operation = {
      operation_id: `desktop_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      user_id: currentUser.user_id,
      timestamp: new Date().toISOString(),
      metadata: {
        client: 'desktop',
        language,
        editor_type: 'codemirror',
        ...operation.metadata
      },
      ...operation
    } as Operation;
    
    wsRef.current.send(JSON.stringify({
      type: 'operation',
      operation: fullOperation
    }));
  }, [isConnected, currentUser.user_id, language]);

  // CodeMirror change handler
  const handleEditorChange = useCallback((value: string, viewUpdate: any) => {
    if (readOnly) return;
    
    const oldContent = content;
    if (value === oldContent) return;
    
    // Extract changes from CodeMirror ViewUpdate
    if (viewUpdate.changes) {
      viewUpdate.changes.iterChanges((fromA: number, toA: number, fromB: number, toB: number, inserted: any) => {
        if (fromA === toA && inserted.length > 0) {
          // Insert operation
          sendOperation({
            operation_type: 'insert',
            position: fromA,
            content: inserted.toString()
          });
        } else if (inserted.length === 0 && fromA < toA) {
          // Delete operation
          sendOperation({
            operation_type: 'delete',
            position: fromA,
            length: toA - fromA
          });
        } else if (inserted.length > 0 && fromA < toA) {
          // Replace operation
          sendOperation({
            operation_type: 'replace',
            position: fromA,
            content: inserted.toString(),
            length: toA - fromA
          });
        }
      });
    }
    
    setContent(value);
    setSaveStatus('unsaved');
  }, [content, readOnly, sendOperation]);

  // Get CodeMirror language extension
  const getLanguageExtension = () => {
    switch (language) {
      case 'javascript':
        return javascript();
      case 'python':
        return python();
      case 'markdown':
      default:
        return markdown();
    }
  };

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // Auto-save functionality
  useEffect(() => {
    if (!autoSave || saveStatus !== 'unsaved') return;
    
    const timer = setTimeout(() => {
      if (onSave && document) {
        onSave(content, document.version);
        setSaveStatus('saving');
      }
    }, 2000);
    
    return () => clearTimeout(timer);
  }, [content, autoSave, saveStatus, onSave, document]);

  // Render user cursors for CodeMirror
  const renderUserCursors = useMemo(() => {
    if (!showCursors) return null;
    
    return users
      .filter(user => user.user_id !== currentUser.user_id)
      .map(user => (
        <UserCursorOverlay
          key={user.user_id}
          color={user.color}
          position={user.cursor_position}
        />
      ));
  }, [users, currentUser.user_id, showCursors]);

  // Render typing indicators
  const renderTypingIndicators = useMemo(() => {
    const typingUsers = users.filter(user => user.is_typing && user.user_id !== currentUser.user_id);
    
    if (typingUsers.length === 0) return null;
    
    return (
      <TypingIndicator>
        <Typography variant="body2" color="info.main">
          {typingUsers.map(user => user.username).join(', ')} 
          {typingUsers.length === 1 ? ' is typing' : ' are typing'}
        </Typography>
        <Box className="typing-dots">
          <div />
          <div />
          <div />
        </Box>
      </TypingIndicator>
    );
  }, [users, currentUser.user_id]);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Connecting to collaborative session...
        </Typography>
      </Box>
    );
  }

  return (
    <EditorContainer>
      {/* Enhanced Header Bar */}
      <HeaderBar elevation={0}>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h6" fontWeight="bold" color="primary">
            {document?.title || 'Collaborative Document'}
          </Typography>
          
          <Box display="flex" gap={1}>
            <Chip
              icon={isConnected ? <CheckCircleIcon /> : <WarningIcon />}
              label={isConnected ? 'Connected' : 'Disconnected'}
              color={isConnected ? 'success' : 'warning'}
              size="small"
              variant="outlined"
            />
            <Chip
              icon={<CloudSyncIcon />}
              label={saveStatus === 'saved' ? 'Saved' : saveStatus === 'saving' ? 'Saving...' : 'Unsaved'}
              color={saveStatus === 'saved' ? 'success' : 'warning'}
              size="small"
              variant="outlined"
            />
            <Chip
              label={`v${document?.version || 1}`}
              size="small"
              variant="outlined"
            />
          </Box>
        </Box>

        <Box display="flex" alignItems="center" gap={1}>
          {/* User avatars with enhanced info */}
          <Box display="flex" marginRight={2}>
            {users.slice(0, 4).map(user => (
              <Tooltip 
                key={user.user_id} 
                title={
                  <Box>
                    <Typography variant="subtitle2">{user.username}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {user.role} • {user.is_typing ? 'Typing...' : 'Active'}
                    </Typography>
                    <Typography variant="caption">
                      Joined: {new Date(user.joined_at).toLocaleTimeString()}
                    </Typography>
                  </Box>
                }
              >
                <Badge
                  color="success"
                  variant="dot"
                  invisible={!user.is_typing}
                  sx={{ marginRight: -1 }}
                >
                  <Avatar
                    sx={{
                      width: 36,
                      height: 36,
                      border: `3px solid ${user.color}`,
                      fontSize: '14px'
                    }}
                    src={user.avatar}
                  >
                    {user.username.charAt(0).toUpperCase()}
                  </Avatar>
                </Badge>
              </Tooltip>
            ))}
            {users.length > 4 && (
              <Tooltip title={`${users.length - 4} more collaborators`}>
                <Avatar sx={{ width: 36, height: 36, fontSize: '14px' }}>
                  +{users.length - 4}
                </Avatar>
              </Tooltip>
            )}
          </Box>

          <Tooltip title="Show Panels">
            <IconButton 
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              color={rightPanelOpen ? 'primary' : 'default'}
            >
              <PeopleIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}>
            <IconButton onClick={() => setIsFullscreen(!isFullscreen)}>
              {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Share Document">
            <IconButton>
              <ShareIcon />
            </IconButton>
          </Tooltip>

          <IconButton onClick={(e) => setMenuAnchor(e.currentTarget)}>
            <MoreVertIcon />
          </IconButton>
        </Box>
      </HeaderBar>

      <MainContent>
        {/* Main Editor Pane */}
        <EditorPane>
          {renderUserCursors}
          
          {/* CodeMirror Editor with desktop-specific extensions */}
          <Box flex={1} position="relative">
            <CodeMirror
              ref={editorRef}
              value={content}
              height="100%"
              theme={theme.palette.mode === 'dark' ? oneDark : undefined}
              extensions={[
                getLanguageExtension(),
                vsCodeKeymap
              ]}
              onChange={handleEditorChange}
              editable={!readOnly}
              placeholder="Start typing to collaborate in real-time..."
            />
          </Box>
          
          {/* Typing Indicators */}
          {renderTypingIndicators && (
            <Box position="absolute" bottom={16} left={16}>
              {renderTypingIndicators}
            </Box>
          )}
        </EditorPane>

        {/* Enhanced Side Panel */}
        <SidePanel
          anchor="right"
          open={rightPanelOpen}
          onClose={() => setRightPanelOpen(false)}
          variant="persistent"
        >
          <Box height="100%" display="flex" flexDirection="column">
            <Box p={2} borderBottom={1} borderColor="divider">
              <Tabs
                value={activePanel}
                onChange={(_, newValue) => setActivePanel(newValue)}
                variant="fullWidth"
              >
                <Tab 
                  icon={<GroupIcon />} 
                  label={`Users (${users.length})`} 
                  value="users" 
                />
                <Tab 
                  icon={<CommentIcon />} 
                  label={`Comments (${comments.filter(c => !c.resolved).length})`} 
                  value="comments" 
                />
                <Tab 
                  icon={<TimelineIcon />} 
                  label="History" 
                  value="history" 
                />
              </Tabs>
            </Box>

            {/* Users Panel */}
            {activePanel === 'users' && (
              <Box flex={1} overflow="auto">
                <Box p={2}>
                  <Button
                    startIcon={<PersonAddIcon />}
                    variant="outlined"
                    fullWidth
                    sx={{ mb: 2 }}
                  >
                    Invite Collaborators
                  </Button>
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={showCursors}
                        onChange={(e) => setShowCursors(e.target.checked)}
                      />
                    }
                    label="Show Cursors"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={enableNotifications}
                        onChange={(e) => setEnableNotifications(e.target.checked)}
                      />
                    }
                    label="Notifications"
                  />
                </Box>

                <List>
                  {users.map(user => (
                    <ListItem key={user.user_id}>
                      <ListItemAvatar>
                        <Badge
                          color="success"
                          variant="dot"
                          invisible={!user.is_typing}
                        >
                          <Avatar
                            sx={{ 
                              border: `2px solid ${user.color}`,
                              width: 48,
                              height: 48
                            }}
                            src={user.avatar}
                          >
                            {user.username.charAt(0).toUpperCase()}
                          </Avatar>
                        </Badge>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="body1">
                              {user.username}
                            </Typography>
                            {user.user_id === currentUser.user_id && (
                              <Chip label="You" size="small" color="primary" />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {user.role} • {user.is_typing ? 'Typing...' : 'Active'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Joined: {new Date(user.joined_at).toLocaleTimeString()}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {/* Comments Panel */}
            {activePanel === 'comments' && (
              <Box flex={1} overflow="auto">
                <Box p={2}>
                  <Button
                    startIcon={<CommentIcon />}
                    variant="outlined"
                    fullWidth
                    onClick={() => setCommentDialogOpen(true)}
                    disabled={!selectedText}
                  >
                    Add Comment
                  </Button>
                </Box>

                <List>
                  {comments
                    .filter(comment => !comment.resolved)
                    .map(comment => (
                      <Accordion key={comment.comment_id}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Box display="flex" alignItems="center" width="100%">
                            <Avatar sx={{ width: 32, height: 32, mr: 2 }}>
                              {comment.username.charAt(0).toUpperCase()}
                            </Avatar>
                            <Box flex={1}>
                              <Typography variant="body2" fontWeight="bold">
                                {comment.username}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {new Date(comment.timestamp).toLocaleString()}
                              </Typography>
                            </Box>
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Typography variant="body2" gutterBottom>
                            {comment.content}
                          </Typography>
                          <Box display="flex" gap={1} mt={1}>
                            <Button size="small" startIcon={<ReplyIcon />}>
                              Reply
                            </Button>
                            <Button 
                              size="small" 
                              startIcon={<DoneIcon />}
                              onClick={() => {
                                if (wsRef.current) {
                                  wsRef.current.send(JSON.stringify({
                                    type: 'resolve_comment',
                                    comment_id: comment.comment_id
                                  }));
                                }
                              }}
                            >
                              Resolve
                            </Button>
                          </Box>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                </List>
              </Box>
            )}

            {/* History Panel */}
            {activePanel === 'history' && (
              <Box flex={1} overflow="auto" p={2}>
                <Timeline>
                  {operationHistory.slice(-20).reverse().map((operation, index) => {
                    const user = users.find(u => u.user_id === operation.user_id);
                    return (
                      <TimelineItem key={operation.operation_id}>
                        <TimelineOppositeContent color="text.secondary">
                          {new Date(operation.timestamp).toLocaleTimeString()}
                        </TimelineOppositeContent>
                        <TimelineSeparator>
                          <TimelineDot color={
                            operation.operation_type === 'insert' ? 'success' : 
                            operation.operation_type === 'delete' ? 'error' : 'primary'
                          }>
                            {operation.operation_type === 'insert' ? '+' : 
                             operation.operation_type === 'delete' ? '-' : '~'}
                          </TimelineDot>
                          {index < operationHistory.length - 1 && <TimelineConnector />}
                        </TimelineSeparator>
                        <TimelineContent>
                          <Typography variant="body2">
                            <strong>{user?.username || 'Unknown'}</strong> {operation.operation_type}ed text
                          </Typography>
                          {operation.content && (
                            <Typography variant="caption" color="text.secondary">
                              "{operation.content.substring(0, 50)}..."
                            </Typography>
                          )}
                        </TimelineContent>
                      </TimelineItem>
                    );
                  })}
                </Timeline>
              </Box>
            )}
          </Box>
        </SidePanel>
      </MainContent>

      {/* Speed Dial for quick actions */}
      <SpeedDial
        ariaLabel="Quick Actions"
        sx={{ position: 'absolute', bottom: 24, right: rightPanelOpen ? 440 : 24 }}
        icon={<SpeedDialIcon />}
      >
        <SpeedDialAction
          icon={<SaveIcon />}
          tooltipTitle="Save Document"
          onClick={() => onSave && document && onSave(content, document.version)}
        />
        <SpeedDialAction
          icon={<CommentIcon />}
          tooltipTitle="Add Comment"
          onClick={() => setCommentDialogOpen(true)}
        />
        <SpeedDialAction
          icon={<ShareIcon />}
          tooltipTitle="Share"
        />
        <SpeedDialAction
          icon={<HistoryIcon />}
          tooltipTitle="Version History"
          onClick={() => setActivePanel('history')}
        />
      </SpeedDial>

      {/* Comment Dialog */}
      <Dialog 
        open={commentDialogOpen} 
        onClose={() => setCommentDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Comment</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Comment"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={newCommentText}
            onChange={(e) => setNewCommentText(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommentDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => {
              if (selectedText && newCommentText.trim() && wsRef.current) {
                wsRef.current.send(JSON.stringify({
                  type: 'add_comment',
                  comment: {
                    content: newCommentText,
                    position: selectedText.start,
                    selection_start: selectedText.start,
                    selection_end: selectedText.end,
                    tags: []
                  }
                }));
                setNewCommentText('');
                setCommentDialogOpen(false);
                setSelectedText(null);
              }
            }}
            variant="contained"
            disabled={!newCommentText.trim()}
            startIcon={<SendIcon />}
          >
            Add Comment
          </Button>
        </DialogActions>
      </Dialog>

      {/* Settings Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem>
          <FormControlLabel
            control={
              <Switch
                checked={autoSave}
                onChange={(e) => setAutoSave(e.target.checked)}
              />
            }
            label="Auto Save"
          />
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <UndoIcon sx={{ mr: 1 }} />
          Undo
        </MenuItem>
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <RedoIcon sx={{ mr: 1 }} />
          Redo
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <SettingsIcon sx={{ mr: 1 }} />
          Preferences
        </MenuItem>
      </Menu>

      {/* Notifications */}
      <Snackbar
        open={Boolean(notification)}
        autoHideDuration={4000}
        onClose={() => setNotification(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          severity={notification?.type || 'info'}
          onClose={() => setNotification(null)}
          variant="filled"
        >
          {notification?.message}
        </Alert>
      </Snackbar>
    </EditorContainer>
  );
};

export default CollaborativeEditorDesktop;