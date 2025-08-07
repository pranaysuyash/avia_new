import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Avatar, AvatarImage, AvatarFallback } from '../ui/avatar';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';
import {
  Users,
  Share,
  Settings,
  Save,
  Undo,
  Redo,
  MessageSquare,
  Eye,
  Edit3,
  Wifi,
  WifiOff,
  Clock,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';
import { format } from 'date-fns';

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
  className?: string;
  readOnly?: boolean;
  onContentChange?: (content: string) => void;
  onSave?: (content: string) => void;
}

const USER_COLORS = [
  '#3B82F6', '#EF4444', '#10B981', '#F59E0B', 
  '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'
];

export const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
  documentId,
  initialContent = '',
  sessionId,
  className,
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

  // Refs
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const operationQueueRef = useRef<Operation[]>([]);
  const typingTimeoutRef = useRef<NodeJS.Timeout>();
  const saveTimeoutRef = useRef<NodeJS.Timeout>();

  // Get user color
  const getUserColor = useCallback((userId: number): string => {
    return USER_COLORS[userId % USER_COLORS.length];
  }, []);

  // Initialize collaborative session
  const initializeSession = useCallback(async () => {
    try {
      setError(null);
      
      if (!currentSessionId) {
        // Create new session
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
              max_participants: 10
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
        
        // Convert active users to collaborative users with colors
        const users: Record<number, CollaborativeUser> = {};
        Object.entries(state.active_users).forEach(([userIdStr, userData]) => {
          const userId = parseInt(userIdStr);
          users[userId] = {
            ...userData,
            user_id: userId,
            status: 'active',
            color: getUserColor(userId),
            cursor_position: state.cursors[userIdStr] || 0
          } as CollaborativeUser;
        });
        setCollaborativeUsers(users);
      }
    } catch (err) {
      console.error('Failed to load document state:', err);
    }
  }, [documentId, getUserColor]);

  // Connect WebSocket
  const connectWebSocket = useCallback(async () => {
    if (!currentSessionId) return;

    try {
      setConnectionStatus('connecting');
      
      // Create authentication token (simplified)
      const token = btoa(JSON.stringify({
        user_id: 1, // Would get from auth context
        username: 'current_user'
      }));

      const wsUrl = `ws://localhost:8000/api/v1/collaboration/ws/${currentSessionId}?token=${token}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnectionStatus('connected');
        setError(null);
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
        
        // Auto-reconnect after 3 seconds
        setTimeout(() => {
          if (websocketRef.current === ws) {
            connectWebSocket();
          }
        }, 3000);
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
  }, [currentSessionId]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'connection_confirmed':
        console.log('WebSocket connection confirmed');
        break;

      case 'operation_applied':
        // Apply remote operation to content
        applyRemoteOperations(message.operations);
        break;

      case 'cursor_update':
        // Update remote user cursor position
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
        // Add new user to collaborators
        setCollaborativeUsers(prev => ({
          ...prev,
          [message.user_id]: {
            user_id: message.user_id,
            username: message.username,
            status: 'active',
            color: getUserColor(message.user_id),
            cursor_position: 0,
            last_seen: message.timestamp
          }
        }));
        break;

      case 'user_left':
        // Remove user from collaborators
        setCollaborativeUsers(prev => {
          const updated = { ...prev };
          delete updated[message.user_id];
          return updated;
        });
        break;

      case 'presence_update':
        // Update user presence status
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
        // Remove acknowledged operation from pending queue
        setPendingOperations(prev => 
          prev.filter(op => op.operation_id !== message.operation_id)
        );
        break;

      case 'operation_error':
        console.error('Operation error:', message.error);
        setError(`Operation failed: ${message.error}`);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [getUserColor]);

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
    const newPos = editorRef.current?.selectionStart || 0;
    const oldPos = cursorPosition;

    // Calculate operation
    if (newContent.length > oldContent.length) {
      // Insert operation
      const insertPos = newPos - (newContent.length - oldContent.length);
      const insertedText = newContent.slice(insertPos, newPos);
      
      sendOperation({
        type: 'insert',
        position: insertPos,
        content: insertedText
      });
    } else if (newContent.length < oldContent.length) {
      // Delete operation
      const deleteLength = oldContent.length - newContent.length;
      const deletePos = Math.min(oldPos, newPos);
      
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

  // Handle cursor position changes
  const handleCursorChange = useCallback(() => {
    const newPosition = editorRef.current?.selectionStart || 0;
    if (newPosition !== cursorPosition) {
      setCursorPosition(newPosition);
      
      // Send cursor update via WebSocket
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        websocketRef.current.send(JSON.stringify({
          type: 'cursor_update',
          document_id: documentId,
          position: newPosition
        }));
      }
    }
  }, [cursorPosition, documentId]);

  // Send presence update
  const sendPresenceUpdate = useCallback((status: 'active' | 'idle' | 'typing') => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({
        type: 'presence_update',
        status
      }));
    }
  }, []);

  // Handle save
  const handleSave = useCallback(async () => {
    if (!hasUnsavedChanges) return;

    try {
      if (onSave) {
        await onSave(content);
      }
      
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
    } catch (err) {
      console.error('Save failed:', err);
      setError('Save failed');
    }
  }, [content, hasUnsavedChanges, onSave]);

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
      case 'connected': return <Wifi className="h-4 w-4 text-green-500" />;
      case 'connecting': return <Clock className="h-4 w-4 text-yellow-500 animate-pulse" />;
      default: return <WifiOff className="h-4 w-4 text-red-500" />;
    }
  };

  const getConnectionText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      default: return 'Disconnected';
    }
  };

  return (
    <TooltipProvider>
      <div className={`space-y-4 ${className}`}>
        {/* Header */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Edit3 className="h-5 w-5" />
                  Collaborative Editor
                </CardTitle>
                <CardDescription>
                  Real-time collaborative editing with operational transforms
                </CardDescription>
              </div>
              
              <div className="flex items-center gap-3">
                {/* Connection Status */}
                <div className="flex items-center gap-2">
                  {getConnectionIcon()}
                  <span className="text-sm text-muted-foreground">
                    {getConnectionText()}
                  </span>
                </div>

                {/* Save Status */}
                {hasUnsavedChanges ? (
                  <Badge variant="outline" className="text-orange-600">
                    Unsaved changes
                  </Badge>
                ) : lastSaved ? (
                  <Badge variant="outline" className="text-green-600">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Saved {format(lastSaved, 'HH:mm')}
                  </Badge>
                ) : null}

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSave}
                    disabled={!hasUnsavedChanges}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </Button>
                  
                  <Button variant="outline" size="sm">
                    <Share className="h-4 w-4 mr-2" />
                    Share
                  </Button>
                </div>
              </div>
            </div>
          </CardHeader>
        </Card>

        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Collaborators Sidebar */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Collaborators ({Object.keys(collaborativeUsers).length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {Object.values(collaborativeUsers).map((user) => (
                  <div key={user.user_id} className="flex items-center gap-3">
                    <div className="relative">
                      <Avatar className="h-8 w-8" style={{ borderColor: user.color, borderWidth: '2px' }}>
                        <AvatarImage src={`/avatars/${user.username}.png`} />
                        <AvatarFallback style={{ backgroundColor: user.color + '20' }}>
                          {user.username.substring(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      
                      {/* Status indicator */}
                      <div 
                        className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white ${
                          user.status === 'typing' ? 'bg-green-500 animate-pulse' :
                          user.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                        }`}
                      />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">
                        {user.full_name || user.username}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {user.status === 'typing' ? 'Typing...' : 
                         user.status === 'active' ? 'Active' : 'Idle'}
                      </div>
                    </div>
                    
                    <Tooltip>
                      <TooltipTrigger>
                        <div 
                          className="w-4 h-4 rounded-full border"
                          style={{ backgroundColor: user.color }}
                        />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Cursor at position {user.cursor_position}</p>
                      </TooltipContent>
                    </Tooltip>
                  </div>
                ))}
                
                {Object.keys(collaborativeUsers).length === 0 && (
                  <div className="text-center text-muted-foreground text-sm py-4">
                    No other collaborators
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Main Editor */}
          <div className="lg:col-span-3">
            <Card>
              <CardContent className="p-0">
                <div className="relative">
                  <textarea
                    ref={editorRef}
                    value={content}
                    onChange={(e) => handleContentChange(e.target.value)}
                    onSelect={handleCursorChange}
                    onKeyUp={handleCursorChange}
                    onClick={handleCursorChange}
                    placeholder={readOnly ? "Content is read-only" : "Start typing to collaborate..."}
                    readOnly={readOnly}
                    className="w-full h-96 p-4 border-0 resize-none focus:outline-none focus:ring-0 font-mono text-sm"
                    style={{
                      background: 'transparent',
                      lineHeight: '1.5'
                    }}
                  />
                  
                  {/* Cursor indicators for other users */}
                  <div className="absolute inset-0 pointer-events-none">
                    {Object.values(collaborativeUsers).map((user) => {
                      if (user.user_id === 1 || !user.cursor_position) return null; // Skip current user
                      
                      // Calculate cursor position (simplified)
                      const lines = content.substring(0, user.cursor_position).split('\n');
                      const lineNumber = lines.length - 1;
                      const columnNumber = lines[lines.length - 1].length;
                      
                      return (
                        <div
                          key={user.user_id}
                          className="absolute w-px h-5 pointer-events-none animate-pulse"
                          style={{
                            backgroundColor: user.color,
                            left: `${4 + columnNumber * 8.4}px`, // Approximation
                            top: `${16 + lineNumber * 21}px`, // Line height approximation
                          }}
                        >
                          <div 
                            className="absolute -top-6 -left-1 px-2 py-1 text-xs rounded text-white whitespace-nowrap"
                            style={{ backgroundColor: user.color }}
                          >
                            {user.username}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* Pending operations indicator */}
                  {pendingOperations.length > 0 && (
                    <div className="absolute top-2 right-2">
                      <Badge variant="outline" className="text-orange-600">
                        <Clock className="h-3 w-3 mr-1 animate-spin" />
                        {pendingOperations.length} pending
                      </Badge>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
            
            {/* Document Info */}
            {documentState && (
              <div className="mt-4 text-xs text-muted-foreground flex justify-between items-center">
                <span>
                  Version: {documentState.version} • 
                  Last modified: {format(new Date(documentState.last_modified), 'MMM dd, yyyy HH:mm')}
                </span>
                <span>
                  {content.length} characters • {content.split('\n').length} lines
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default CollaborativeEditor;