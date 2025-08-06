import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  color: string;
}

interface Cursor {
  userId: string;
  x: number;
  y: number;
  timestamp: number;
}

interface Selection {
  userId: string;
  start: number;
  end: number;
  timestamp: number;
}

interface Comment {
  id: string;
  userId: string;
  text: string;
  timestamp: string;
  resolved: boolean;
  replies?: Comment[];
  position?: {
    start: number;
    end: number;
  };
}

interface CollaborationContextType {
  // Connection
  isConnected: boolean;
  connectionError: string | null;
  
  // Users
  activeUsers: User[];
  currentUser: User | null;
  
  // Cursors and selections
  cursors: Map<string, Cursor>;
  selections: Map<string, Selection>;
  
  // Comments
  comments: Comment[];
  
  // Actions
  joinSession: (sessionId: string, user: User) => void;
  leaveSession: () => void;
  updateCursor: (position: { x: number; y: number }) => void;
  updateSelection: (selection: { start: number; end: number }) => void;
  addComment: (comment: Omit<Comment, 'id' | 'userId' | 'timestamp'>) => void;
  resolveComment: (commentId: string) => void;
  replyToComment: (commentId: string, text: string) => void;
  
  // Real-time editing
  sendChange: (change: any) => void;
  onReceiveChange: (callback: (change: any) => void) => void;
}

const CollaborationContext = createContext<CollaborationContextType | null>(null);

export const useCollaboration = () => {
  const context = useContext(CollaborationContext);
  if (!context) {
    throw new Error('useCollaboration must be used within a CollaborationProvider');
  }
  return context;
};

interface CollaborationProviderProps {
  children: React.ReactNode;
  serverUrl?: string;
}

export const CollaborationProvider: React.FC<CollaborationProviderProps> = ({ 
  children, 
  serverUrl = process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8001' 
}) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [activeUsers, setActiveUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [cursors, setCursors] = useState<Map<string, Cursor>>(new Map());
  const [selections, setSelections] = useState<Map<string, Selection>>(new Map());
  const [comments, setComments] = useState<Comment[]>([]);
  const changeCallbacks = useRef<((change: any) => void)[]>([]);
  const currentSessionId = useRef<string | null>(null);

  // Cleanup inactive cursors/selections
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const timeout = 5000; // 5 seconds

      setCursors(prev => {
        const updated = new Map(prev);
        updated.forEach((cursor, userId) => {
          if (now - cursor.timestamp > timeout) {
            updated.delete(userId);
          }
        });
        return updated;
      });

      setSelections(prev => {
        const updated = new Map(prev);
        updated.forEach((selection, userId) => {
          if (now - selection.timestamp > timeout) {
            updated.delete(userId);
          }
        });
        return updated;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const joinSession = useCallback((sessionId: string, user: User) => {
    if (socket?.connected) {
      socket.disconnect();
    }

    const newSocket = io(serverUrl, {
      transports: ['websocket'],
      auth: {
        sessionId,
        user
      }
    });

    newSocket.on('connect', () => {
      setIsConnected(true);
      setConnectionError(null);
      setCurrentUser(user);
      currentSessionId.current = sessionId;
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
    });

    newSocket.on('connect_error', (error) => {
      setConnectionError(error.message);
      setIsConnected(false);
    });

    // User events
    newSocket.on('users:update', (users: User[]) => {
      setActiveUsers(users);
    });

    newSocket.on('user:joined', (user: User) => {
      setActiveUsers(prev => [...prev, user]);
    });

    newSocket.on('user:left', (userId: string) => {
      setActiveUsers(prev => prev.filter(u => u.id !== userId));
      setCursors(prev => {
        const updated = new Map(prev);
        updated.delete(userId);
        return updated;
      });
      setSelections(prev => {
        const updated = new Map(prev);
        updated.delete(userId);
        return updated;
      });
    });

    // Cursor events
    newSocket.on('cursor:update', ({ userId, position }: { userId: string; position: { x: number; y: number } }) => {
      setCursors(prev => {
        const updated = new Map(prev);
        updated.set(userId, { userId, ...position, timestamp: Date.now() });
        return updated;
      });
    });

    // Selection events
    newSocket.on('selection:update', ({ userId, selection }: { userId: string; selection: { start: number; end: number } }) => {
      setSelections(prev => {
        const updated = new Map(prev);
        updated.set(userId, { userId, ...selection, timestamp: Date.now() });
        return updated;
      });
    });

    // Comment events
    newSocket.on('comment:added', (comment: Comment) => {
      setComments(prev => [...prev, comment]);
    });

    newSocket.on('comment:resolved', (commentId: string) => {
      setComments(prev => prev.map(c => 
        c.id === commentId ? { ...c, resolved: true } : c
      ));
    });

    newSocket.on('comment:reply', ({ commentId, reply }: { commentId: string; reply: Comment }) => {
      setComments(prev => prev.map(c => 
        c.id === commentId 
          ? { ...c, replies: [...(c.replies || []), reply] }
          : c
      ));
    });

    // Content change events
    newSocket.on('content:change', (change: any) => {
      changeCallbacks.current.forEach(callback => callback(change));
    });

    setSocket(newSocket);
  }, [serverUrl]);

  const leaveSession = useCallback(() => {
    if (socket) {
      socket.disconnect();
      setSocket(null);
      setIsConnected(false);
      setActiveUsers([]);
      setCurrentUser(null);
      setCursors(new Map());
      setSelections(new Map());
      setComments([]);
      currentSessionId.current = null;
    }
  }, [socket]);

  const updateCursor = useCallback((position: { x: number; y: number }) => {
    if (socket && isConnected) {
      socket.emit('cursor:move', position);
    }
  }, [socket, isConnected]);

  const updateSelection = useCallback((selection: { start: number; end: number }) => {
    if (socket && isConnected) {
      socket.emit('selection:change', selection);
    }
  }, [socket, isConnected]);

  const addComment = useCallback((comment: Omit<Comment, 'id' | 'userId' | 'timestamp'>) => {
    if (socket && isConnected && currentUser) {
      const newComment: Comment = {
        ...comment,
        id: `comment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        userId: currentUser.id,
        timestamp: new Date().toISOString(),
        resolved: false
      };
      socket.emit('comment:add', newComment);
    }
  }, [socket, isConnected, currentUser]);

  const resolveComment = useCallback((commentId: string) => {
    if (socket && isConnected) {
      socket.emit('comment:resolve', commentId);
    }
  }, [socket, isConnected]);

  const replyToComment = useCallback((commentId: string, text: string) => {
    if (socket && isConnected && currentUser) {
      const reply: Comment = {
        id: `reply_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        userId: currentUser.id,
        text,
        timestamp: new Date().toISOString(),
        resolved: false
      };
      socket.emit('comment:reply', { commentId, reply });
    }
  }, [socket, isConnected, currentUser]);

  const sendChange = useCallback((change: any) => {
    if (socket && isConnected) {
      socket.emit('content:change', change);
    }
  }, [socket, isConnected]);

  const onReceiveChange = useCallback((callback: (change: any) => void) => {
    changeCallbacks.current.push(callback);
    return () => {
      changeCallbacks.current = changeCallbacks.current.filter(cb => cb !== callback);
    };
  }, []);

  const value: CollaborationContextType = {
    isConnected,
    connectionError,
    activeUsers,
    currentUser,
    cursors,
    selections,
    comments,
    joinSession,
    leaveSession,
    updateCursor,
    updateSelection,
    addComment,
    resolveComment,
    replyToComment,
    sendChange,
    onReceiveChange
  };

  return (
    <CollaborationContext.Provider value={value}>
      {children}
    </CollaborationContext.Provider>
  );
};

export default CollaborationProvider;