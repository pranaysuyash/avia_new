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
  TextField, 
  Button, 
  Popover, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemAvatar, 
  Badge, 
  Tooltip, 
  CircularProgress,
  Fade,
  Zoom,
  Alert,
  Snackbar
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
  Close as CloseIcon
} from '@mui/icons-material';
import { styled, alpha } from '@mui/material/styles';

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
  height: '100%',
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  borderRadius: theme.spacing(2),
  overflow: 'hidden',
  position: 'relative'
}));

const EditorHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing(2),
  background: 'rgba(255, 255, 255, 0.95)',
  backdropFilter: 'blur(10px)',
  borderBottom: '1px solid rgba(255, 255, 255, 0.2)'
}));

const EditorContent = styled(Box)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  background: theme.palette.background.paper
}));

const EditorTextArea = styled('textarea')(({ theme }) => ({
  flex: 1,
  border: 'none',
  outline: 'none',
  padding: theme.spacing(3),
  fontSize: '16px',
  lineHeight: '1.6',
  fontFamily: '"Fira Code", "Monaco", "Consolas", monospace',
  background: theme.palette.background.paper,
  color: theme.palette.text.primary,
  resize: 'none',
  '&::selection': {
    background: alpha(theme.palette.primary.main, 0.3)
  }
}));

const UsersSidebar = styled(Box)(({ theme }) => ({
  width: '300px',
  background: theme.palette.background.paper,
  borderLeft: `1px solid ${theme.palette.divider}`,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden'
}));

const UserCursor = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'color' && prop !== 'position'
})<{ color: string; position: number }>(({ theme, color, position }) => ({
  position: 'absolute',
  width: '2px',
  height: '20px',
  background: color,
  left: `${position}px`,
  top: '0',
  zIndex: 10,
  animation: 'blink 1s infinite',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: '-8px',
    left: '-3px',
    width: '8px',
    height: '8px',
    background: color,
    borderRadius: '50%'
  },
  '@keyframes blink': {
    '0%, 50%': { opacity: 1 },
    '51%, 100%': { opacity: 0.3 }
  }
}));

const CommentBubble = styled(Box)<{ color: string }>(({ theme, color }) => ({
  position: 'absolute',
  padding: theme.spacing(1, 2),
  background: color,
  color: theme.palette.common.white,
  borderRadius: theme.spacing(2),
  fontSize: '14px',
  maxWidth: '200px',
  boxShadow: theme.shadows[4],
  zIndex: 20,
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: '-8px',
    left: '16px',
    width: 0,
    height: 0,
    border: '8px solid transparent',
    borderTopColor: color
  }
}));

interface RealTimeCollaborativeEditorProps {
  documentId: string;
  currentUser: User;
  onSave?: (content: string, version: number) => void;
  initialContent?: string;
  readOnly?: boolean;
}

const RealTimeCollaborativeEditor: React.FC<RealTimeCollaborativeEditorProps> = ({
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
  const [showUsers, setShowUsers] = useState(true);
  const [showComments, setShowComments] = useState(true);
  const [selectedText, setSelectedText] = useState<{start: number, end: number} | null>(null);
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [newCommentText, setNewCommentText] = useState('');
  const [menuAnchor, setMenuAnchor] = useState<HTMLElement | null>(null);
  const [notification, setNotification] = useState<{message: string, type: 'success' | 'error' | 'info'} | null>(null);

  // Refs
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const operationQueue = useRef<Operation[]>([]);
  const cursorPositions = useRef<Map<string, {x: number, y: number}>>(new Map());

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
      setNotification({ message: 'Connection error occurred', type: 'error' });
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
        setNotification({ message: `${data.user.username} joined the session`, type: 'info' });
        break;
        
      case 'user_left':
        setUsers(prev => prev.filter(u => u.user_id !== data.user_id));
        setNotification({ message: `${data.username} left the session`, type: 'info' });
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
          setNotification({ message: 'Document auto-saved', type: 'success' });
        }
        break;
        
      case 'error':
        setNotification({ message: data.message, type: 'error' });
        break;
    }
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
  const handleTextChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (readOnly) return;
    
    const newContent = event.target.value;
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

  // Handle cursor movement
  const handleCursorMove = useCallback(() => {
    if (!textAreaRef.current || !isConnected) return;
    
    const textarea = textAreaRef.current;
    const cursorPosition = textarea.selectionStart;
    const selectionStart = textarea.selectionStart;
    const selectionEnd = textarea.selectionEnd;
    
    // Send cursor update
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({
        type: 'cursor_update',
        cursor_position: cursorPosition,
        selection_start: selectionStart !== selectionEnd ? selectionStart : undefined,
        selection_end: selectionStart !== selectionEnd ? selectionEnd : undefined
      }));
    }
  }, [isConnected]);

  // Handle text selection for comments
  const handleTextSelection = useCallback(() => {
    if (!textAreaRef.current) return;
    
    const textarea = textAreaRef.current;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    
    if (start !== end) {
      setSelectedText({ start, end });
    } else {
      setSelectedText(null);
    }
  }, []);

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
    setCommentDialogOpen(false);
    setSelectedText(null);
  }, [selectedText, newCommentText]);

  // Resolve comment
  const handleResolveComment = useCallback((commentId: string) => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({
        type: 'resolve_comment',
        comment_id: commentId
      }));
    }
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // Typing indicator
  useEffect(() => {
    const timer = setTimeout(() => {
      if (wsRef.current && isConnected) {
        wsRef.current.send(JSON.stringify({
          type: 'typing_status',
          is_typing: false
        }));
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [content, isConnected]);

  // Render user avatars with cursors
  const renderUserCursors = useMemo(() => {
    return users
      .filter(user => user.user_id !== currentUser.user_id)
      .map(user => (
        <UserCursor
          key={user.user_id}
          color={user.color}
          position={user.cursor_position}
        />
      ));
  }, [users, currentUser.user_id]);

  // Render comments on text
  const renderComments = useMemo(() => {
    return comments
      .filter(comment => !comment.resolved)
      .map(comment => (
        <CommentBubble
          key={comment.comment_id}
          color={users.find(u => u.user_id === comment.user_id)?.color || '#2196f3'}
          sx={{
            top: `${Math.min(comment.position * 0.5, 300)}px`,
            right: '320px'
          }}
        >
          <Typography variant="body2" fontWeight="bold">
            {comment.username}
          </Typography>
          <Typography variant="body2">
            {comment.content}
          </Typography>
          <Typography variant="caption" color="rgba(255,255,255,0.8)">
            {new Date(comment.timestamp).toLocaleTimeString()}
          </Typography>
        </CommentBubble>
      ));
  }, [comments, users]);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <EditorContainer>
      <EditorHeader>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h6" fontWeight="bold">
            {document?.title || 'Collaborative Document'}
          </Typography>
          <Chip
            icon={isConnected ? <CheckCircleIcon /> : <WarningIcon />}
            label={isConnected ? 'Connected' : 'Disconnected'}
            color={isConnected ? 'success' : 'warning'}
            size="small"
          />
          <Chip
            icon={<SaveIcon />}
            label={saveStatus === 'saved' ? 'Saved' : saveStatus === 'saving' ? 'Saving...' : 'Unsaved'}
            color={saveStatus === 'saved' ? 'success' : 'warning'}
            size="small"
          />
        </Box>

        <Box display="flex" alignItems="center" gap={1}>
          {/* User avatars */}
          <Box display="flex" marginRight={2}>
            {users.slice(0, 3).map(user => (
              <Tooltip key={user.user_id} title={`${user.username} (${user.role})`}>
                <Badge
                  color="success"
                  variant="dot"
                  invisible={!user.is_typing}
                  sx={{ marginRight: -1 }}
                >
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      border: `2px solid ${user.color}`,
                      fontSize: '14px'
                    }}
                    src={user.avatar}
                  >
                    {user.username.charAt(0).toUpperCase()}
                  </Avatar>
                </Badge>
              </Tooltip>
            ))}
            {users.length > 3 && (
              <Avatar sx={{ width: 32, height: 32, fontSize: '14px' }}>
                +{users.length - 3}
              </Avatar>
            )}
          </Box>

          <Tooltip title="Add Comment">
            <IconButton 
              onClick={() => selectedText && setCommentDialogOpen(true)}
              disabled={!selectedText}
            >
              <CommentIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Toggle Users Panel">
            <IconButton onClick={() => setShowUsers(!showUsers)}>
              {showUsers ? <VisibilityIcon /> : <VisibilityOffIcon />}
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
      </EditorHeader>

      <EditorContent>
        <Box flex={1} position="relative">
          {renderUserCursors}
          {renderComments}
          
          <EditorTextArea
            ref={textAreaRef}
            value={content}
            onChange={handleTextChange}
            onSelect={handleTextSelection}
            onMouseUp={handleCursorMove}
            onKeyUp={handleCursorMove}
            placeholder="Start typing to collaborate in real-time..."
            readOnly={readOnly}
          />
        </Box>

        {showUsers && (
          <Fade in={showUsers}>
            <UsersSidebar>
              <Box p={2} borderBottom={1} borderColor="divider">
                <Typography variant="h6" gutterBottom>
                  Collaborators ({users.length})
                </Typography>
                <Button
                  startIcon={<PersonAddIcon />}
                  variant="outlined"
                  size="small"
                  fullWidth
                >
                  Invite Others
                </Button>
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
                            width: 40,
                            height: 40
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
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>

              {showComments && (
                <>
                  <Box p={2} borderTop={1} borderColor="divider">
                    <Typography variant="h6" gutterBottom>
                      Comments ({comments.filter(c => !c.resolved).length})
                    </Typography>
                  </Box>

                  <List>
                    {comments
                      .filter(comment => !comment.resolved)
                      .map(comment => (
                        <ListItem key={comment.comment_id}>
                          <ListItemAvatar>
                            <Avatar sx={{ width: 32, height: 32 }}>
                              {comment.username.charAt(0).toUpperCase()}
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText
                            primary={comment.content}
                            secondary={
                              <Box>
                                <Typography variant="caption" color="text.secondary">
                                  {comment.username} • {new Date(comment.timestamp).toLocaleTimeString()}
                                </Typography>
                                <Box mt={1}>
                                  <Button
                                    size="small"
                                    onClick={() => handleResolveComment(comment.comment_id)}
                                  >
                                    Resolve
                                  </Button>
                                </Box>
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                  </List>
                </>
              )}
            </UsersSidebar>
          </Fade>
        )}
      </EditorContent>

      {/* Comment Dialog */}
      <Dialog open={commentDialogOpen} onClose={() => setCommentDialogOpen(false)}>
        <DialogTitle>Add Comment</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Comment"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newCommentText}
            onChange={(e) => setNewCommentText(e.target.value)}
          />
          <Box mt={2} display="flex" gap={1} justifyContent="flex-end">
            <Button onClick={() => setCommentDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAddComment}
              variant="contained"
              disabled={!newCommentText.trim()}
            >
              Add Comment
            </Button>
          </Box>
        </DialogContent>
      </Dialog>

      {/* Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <UndoIcon sx={{ mr: 1 }} />
          Undo
        </MenuItem>
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <RedoIcon sx={{ mr: 1 }} />
          Redo
        </MenuItem>
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <HistoryIcon sx={{ mr: 1 }} />
          Version History
        </MenuItem>
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <SettingsIcon sx={{ mr: 1 }} />
          Settings
        </MenuItem>
      </Menu>

      {/* Notifications */}
      <Snackbar
        open={Boolean(notification)}
        autoHideDuration={4000}
        onClose={() => setNotification(null)}
      >
        <Alert
          severity={notification?.type || 'info'}
          onClose={() => setNotification(null)}
        >
          {notification?.message}
        </Alert>
      </Snackbar>
    </EditorContainer>
  );
};

export default RealTimeCollaborativeEditor;