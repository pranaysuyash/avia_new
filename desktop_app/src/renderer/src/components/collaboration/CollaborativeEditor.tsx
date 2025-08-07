import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
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
  FolderOpen,
  Bell,
  Download,
} from 'lucide-react';
import { format } from 'date-fns';

// Desktop-specific imports
declare global {
  interface Window {
    electronAPI: {
      saveDialog: (options: any) => Promise<{ filePath?: string; canceled: boolean }>;
      showNotification: (title: string, body: string) => void;
      openExternal: (url: string) => void;
      getAppVersion: () => Promise<string>;
      onAppUpdate: (callback: (info: any) => void) => void;
      showContextMenu: (options: any) => Promise<string>;
    };
  }
}

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
  is_desktop?: boolean;
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
  const [isMinimized, setIsMinimized] = useState(false);
  const [notifications, setNotifications] = useState(true);

  // Refs
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const operationQueueRef = useRef<Operation[]>([]);
  const typingTimeoutRef = useRef<NodeJS.Timeout>();
  const saveTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // Get user color
  const getUserColor = useCallback((userId: number): string => {
    return USER_COLORS[userId % USER_COLORS.length];
  }, []);

  // Desktop-specific notification
  const showDesktopNotification = useCallback((title: string, message: string) => {
    if (notifications && window.electronAPI) {
      window.electronAPI.showNotification(title, message);
    }
  }, [notifications]);

  // Desktop-specific file saving
  const saveToDesktop = useCallback(async () => {
    if (!window.electronAPI) return false;

    try {
      const result = await window.electronAPI.saveDialog({
        title: 'Save Document',
        defaultPath: `document_${documentId}.txt`,
        filters: [
          { name: 'Text Files', extensions: ['txt'] },
          { name: 'All Files', extensions: ['*'] }
        ]
      });

      if (!result.canceled && result.filePath) {
        // In a real implementation, you'd save the content to the file
        // For now, we'll just trigger the regular save
        if (onSave) {
          await onSave(content);
        }
        showDesktopNotification('Document Saved', `Document saved to ${result.filePath}`);
        return true;
      }
    } catch (err) {
      console.error('Desktop save failed:', err);
      showDesktopNotification('Save Failed', 'Could not save document');
    }
    return false;
  }, [content, documentId, onSave, showDesktopNotification]);

  // Context menu for desktop
  const showContextMenu = useCallback(async (event: React.MouseEvent) => {
    if (!window.electronAPI) return;

    event.preventDefault();
    
    try {
      const result = await window.electronAPI.showContextMenu({
        items: [
          { label: 'Copy', role: 'copy' },
          { label: 'Cut', role: 'cut' },
          { label: 'Paste', role: 'paste' },
          { type: 'separator' },
          { label: 'Select All', accelerator: 'CmdOrCtrl+A' },
          { type: 'separator' },
          { label: 'Save Document', click: 'save' },
          { label: 'Export as PDF', click: 'export-pdf' }
        ]
      });

      if (result === 'save') {
        await saveToDesktop();
      } else if (result === 'export-pdf') {
        // Handle PDF export
        showDesktopNotification('Export', 'PDF export feature coming soon');
      }
    } catch (err) {
      console.error('Context menu error:', err);
    }
  }, [saveToDesktop, showDesktopNotification]);

  // Initialize collaborative session
  const initializeSession = useCallback(async () => {
    try {
      setError(null);
      
      if (!currentSessionId) {
        // Create new session with desktop metadata
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
                platform: 'desktop',
                client: 'electron',
                version: await window.electronAPI?.getAppVersion?.() || '1.0.0'
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
            is_desktop: userData.platform === 'desktop',
            platform: userData.platform || 'unknown'
          } as CollaborativeUser;
        });
        setCollaborativeUsers(users);
      }
    } catch (err) {
      console.error('Failed to load document state:', err);
    }
  }, [documentId, getUserColor]);

  // Connect WebSocket with desktop-specific reconnection
  const connectWebSocket = useCallback(async () => {
    if (!currentSessionId) return;

    try {
      setConnectionStatus('connecting');
      
      const token = btoa(JSON.stringify({
        user_id: 1, // Would get from auth context
        username: 'desktop_user',
        platform: 'desktop'
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
        
        showDesktopNotification('Connected', 'Real-time collaboration enabled');
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
        showDesktopNotification('Disconnected', 'Attempting to reconnect...');
        
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
  }, [currentSessionId, showDesktopNotification]);

  // Handle WebSocket messages with desktop notifications
  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'connection_confirmed':
        console.log('WebSocket connection confirmed');
        break;

      case 'operation_applied':
        applyRemoteOperations(message.operations);
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
          is_desktop: message.platform === 'desktop',
          platform: message.platform || 'unknown'
        };
        
        setCollaborativeUsers(prev => ({
          ...prev,
          [message.user_id]: newUser
        }));
        
        showDesktopNotification(
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
            showDesktopNotification('User Left', `${leftUser.username} left the session`);
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
        showDesktopNotification('Sync Error', message.error);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [getUserColor, showDesktopNotification]);

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

  // Handle save with desktop integration
  const handleSave = useCallback(async () => {
    if (!hasUnsavedChanges) return;

    try {
      if (onSave) {
        await onSave(content);
      }
      
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
      showDesktopNotification('Saved', 'Document saved successfully');
    } catch (err) {
      console.error('Save failed:', err);
      setError('Save failed');
      showDesktopNotification('Save Failed', 'Could not save document');
    }
  }, [content, hasUnsavedChanges, onSave, showDesktopNotification]);

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

  const getPlatformIcon = (platform?: string) => {
    switch (platform) {
      case 'desktop':
        return '🖥️';
      case 'mobile':
        return '📱';
      case 'web':
        return '🌐';
      default:
        return '💻';
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
                  Collaborative Editor (Desktop)
                </CardTitle>
                <CardDescription>
                  Real-time collaborative editing with desktop integration
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

                {/* Desktop Action Buttons */}
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
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={saveToDesktop}
                  >
                    <FolderOpen className="h-4 w-4 mr-2" />
                    Save As...
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setNotifications(!notifications)}
                  >
                    <Bell className={`h-4 w-4 ${notifications ? 'text-blue-500' : 'text-gray-400'}`} />
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
                      
                      {/* Platform indicator */}
                      <div 
                        className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white bg-white flex items-center justify-center text-xs"
                        title={`Platform: ${user.platform}`}
                      >
                        {getPlatformIcon(user.platform)}
                      </div>
                      
                      {/* Status indicator */}
                      <div 
                        className={`absolute top-0 right-0 w-3 h-3 rounded-full border-2 border-white ${
                          user.status === 'typing' ? 'bg-green-500 animate-pulse' :
                          user.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                        }`}
                      />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">
                        {user.full_name || user.username}
                        {user.is_desktop && ' 🖥️'}
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
                    onContextMenu={showContextMenu}
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
                            className="absolute -top-6 -left-1 px-2 py-1 text-xs rounded text-white whitespace-nowrap flex items-center gap-1"
                            style={{ backgroundColor: user.color }}
                          >
                            {getPlatformIcon(user.platform)}
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