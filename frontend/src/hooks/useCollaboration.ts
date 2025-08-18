/**
 * React Hook for Real-time Collaboration
 * Manages WebRTC connections and collaborative features
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { WebRTCService } from '../services/webrtc/WebRTCService';
import { trackFunnelEvent } from '../utils/posthog';

interface Collaborator {
  userId: string;
  userName: string;
  cursorColor: string;
  cursor?: { x: number; y: number };
  selection?: { start: number; end: number };
  isActive: boolean;
}

interface CollaborationState {
  isConnected: boolean;
  collaborators: Map<string, Collaborator>;
  error: Error | null;
}

interface UseCollaborationOptions {
  roomId: string;
  userId: string;
  userName: string;
  signalingServerUrl?: string;
  iceServers?: RTCIceServer[];
  onMessage?: (message: any) => void;
}

export function useCollaboration(options: UseCollaborationOptions) {
  const {
    roomId,
    userId,
    userName,
    signalingServerUrl = import.meta.env.VITE_SIGNALING_SERVER || 'wss://localhost:8080',
    iceServers = [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
    ],
    onMessage,
  } = options;

  const [state, setState] = useState<CollaborationState>({
    isConnected: false,
    collaborators: new Map(),
    error: null,
  });

  const webrtcRef = useRef<WebRTCService | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // Initialize WebRTC service
  useEffect(() => {
    const webrtc = new WebRTCService(
      { iceServers, signalingServerUrl },
      userId,
      userName
    );

    // Set up event handlers
    webrtc.on('connected', () => {
      setState(prev => ({ ...prev, isConnected: true, error: null }));
      reconnectAttemptsRef.current = 0;
      trackFunnelEvent('COLLABORATION_STARTED', { roomId });
    });

    webrtc.on('disconnected', () => {
      setState(prev => ({ ...prev, isConnected: false }));
      handleReconnect();
    });

    webrtc.on('error', (error) => {
      setState(prev => ({ ...prev, error }));
      console.error('WebRTC error:', error);
    });

    webrtc.on('peer-connected', (metadata) => {
      setState(prev => {
        const collaborators = new Map(prev.collaborators);
        collaborators.set(metadata.userId, {
          ...metadata,
          isActive: true,
        });
        return { ...prev, collaborators };
      });
    });

    webrtc.on('peer-left', ({ userId }) => {
      setState(prev => {
        const collaborators = new Map(prev.collaborators);
        collaborators.delete(userId);
        return { ...prev, collaborators };
      });
    });

    webrtc.on('message', (message) => {
      handleCollaborationMessage(message);
      onMessage?.(message);
    });

    webrtcRef.current = webrtc;

    // Join room
    webrtc.joinRoom(roomId).catch(error => {
      console.error('Failed to join room:', error);
      setState(prev => ({ ...prev, error }));
    });

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      webrtc.leaveRoom();
      webrtc.removeAllListeners();
    };
  }, [roomId, userId, userName, signalingServerUrl, iceServers, onMessage]);

  // Handle collaboration messages
  const handleCollaborationMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'cursor':
        setState(prev => {
          const collaborators = new Map(prev.collaborators);
          const collaborator = collaborators.get(message.userId);
          if (collaborator) {
            collaborator.cursor = message.data;
            collaborators.set(message.userId, { ...collaborator });
          }
          return { ...prev, collaborators };
        });
        break;

      case 'selection':
        setState(prev => {
          const collaborators = new Map(prev.collaborators);
          const collaborator = collaborators.get(message.userId);
          if (collaborator) {
            collaborator.selection = message.data;
            collaborators.set(message.userId, { ...collaborator });
          }
          return { ...prev, collaborators };
        });
        break;

      case 'presence':
        setState(prev => {
          const collaborators = new Map(prev.collaborators);
          const collaborator = collaborators.get(message.userId);
          if (collaborator) {
            collaborator.isActive = message.data.isActive;
            collaborators.set(message.userId, { ...collaborator });
          }
          return { ...prev, collaborators };
        });
        break;
    }
  }, []);

  // Handle reconnection
  const handleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= 5) {
      setState(prev => ({
        ...prev,
        error: new Error('Failed to reconnect after 5 attempts'),
      }));
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
    reconnectAttemptsRef.current++;

    reconnectTimeoutRef.current = setTimeout(() => {
      if (webrtcRef.current) {
        webrtcRef.current.joinRoom(roomId).catch(error => {
          console.error('Reconnection failed:', error);
          handleReconnect();
        });
      }
    }, delay);
  }, [roomId]);

  // Send cursor position
  const sendCursor = useCallback((x: number, y: number) => {
    if (webrtcRef.current && state.isConnected) {
      webrtcRef.current.broadcast({
        type: 'cursor',
        userId,
        data: { x, y },
        timestamp: Date.now(),
      });
    }
  }, [userId, state.isConnected]);

  // Send selection
  const sendSelection = useCallback((start: number, end: number) => {
    if (webrtcRef.current && state.isConnected) {
      webrtcRef.current.broadcast({
        type: 'selection',
        userId,
        data: { start, end },
        timestamp: Date.now(),
      });
    }
  }, [userId, state.isConnected]);

  // Send edit
  const sendEdit = useCallback((edit: any) => {
    if (webrtcRef.current && state.isConnected) {
      webrtcRef.current.broadcast({
        type: 'edit',
        userId,
        data: edit,
        timestamp: Date.now(),
      });
    }
  }, [userId, state.isConnected]);

  // Send presence update
  const sendPresence = useCallback((isActive: boolean) => {
    if (webrtcRef.current && state.isConnected) {
      webrtcRef.current.broadcast({
        type: 'presence',
        userId,
        data: { isActive },
        timestamp: Date.now(),
      });
    }
  }, [userId, state.isConnected]);

  // Sync full document state
  const syncDocument = useCallback((document: any) => {
    if (webrtcRef.current && state.isConnected) {
      webrtcRef.current.broadcast({
        type: 'sync',
        userId,
        data: { document },
        timestamp: Date.now(),
      });
    }
  }, [userId, state.isConnected]);

  return {
    isConnected: state.isConnected,
    collaborators: Array.from(state.collaborators.values()),
    error: state.error,
    sendCursor,
    sendSelection,
    sendEdit,
    sendPresence,
    syncDocument,
  };
}