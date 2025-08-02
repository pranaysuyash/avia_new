import { useState, useEffect, useCallback, useRef } from 'react';
import io from 'socket.io-client';

const useWebSocket = (url, options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const messageHandlersRef = useRef(new Map());

  // Connection options
  const {
    autoConnect = true,
    reconnect = true,
    reconnectDelay = 5000,
    onConnect = () => {},
    onDisconnect = () => {},
    onError = () => {}
  } = options;

  // Connect to WebSocket server
  const connect = useCallback(() => {
    if (socketRef.current?.connected) return;

    try {
      socketRef.current = io(url, {
        transports: ['websocket'],
        autoConnect: false,
        reconnection: reconnect,
        reconnectionDelay: reconnectDelay
      });

      // Connection event handlers
      socketRef.current.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        onConnect();
      });

      socketRef.current.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        setIsConnected(false);
        onDisconnect(reason);

        // Auto-reconnect if enabled
        if (reconnect && reason !== 'io client disconnect') {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        }
      });

      socketRef.current.on('error', (error) => {
        console.error('WebSocket error:', error);
        onError(error);
      });

      // Message handler
      socketRef.current.onAny((event, data) => {
        const message = { event, data, timestamp: new Date().toISOString() };
        setLastMessage(message);

        // Call registered handlers
        const handlers = messageHandlersRef.current.get(event) || [];
        handlers.forEach(handler => handler(data));
      });

      socketRef.current.connect();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      onError(error);
    }
  }, [url, reconnect, reconnectDelay, onConnect, onDisconnect, onError]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  // Send message
  const sendMessage = useCallback((event, data) => {
    if (!socketRef.current?.connected) {
      console.warn('WebSocket not connected');
      return false;
    }

    socketRef.current.emit(event, data);
    return true;
  }, []);

  // Subscribe to specific events
  const subscribe = useCallback((event, handler) => {
    const handlers = messageHandlersRef.current.get(event) || [];
    handlers.push(handler);
    messageHandlersRef.current.set(event, handlers);

    // Return unsubscribe function
    return () => {
      const handlers = messageHandlersRef.current.get(event) || [];
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
        messageHandlersRef.current.set(event, handlers);
      }
    };
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    connect,
    disconnect,
    sendMessage,
    subscribe
  };
};

export default useWebSocket;