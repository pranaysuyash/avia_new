import { useState, useEffect, useRef } from 'react';

interface WebSocketHookOptions {
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export const useWebSocket = (url: string, options: WebSocketHookOptions = {}) => {
  const [data, setData] = useState<any>(null);
  const [connectionStatus, setConnectionStatus] = useState<'Connecting' | 'Open' | 'Closing' | 'Closed'>('Closed');
  const [error, setError] = useState<Event | null>(null);
  
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnectAttempts = 5,
    reconnectInterval = 3000
  } = options;

  const connect = () => {
    try {
      // For demo purposes, simulate WebSocket connection
      // In production, this would be: new WebSocket(url)
      
      setConnectionStatus('Connecting');
      
      // Simulate connection delay
      setTimeout(() => {
        setConnectionStatus('Open');
        reconnectAttemptsRef.current = 0;
        
        // Simulate real-time data updates
        const interval = setInterval(() => {
          const mockData = {
            activities: [
              {
                id: Date.now(),
                user: 'John Smith',
                action: 'completed transcription of meeting_audio.mp4',
                timestamp: 'Just now',
                status: 'completed'
              },
              {
                id: Date.now() + 1,
                user: 'Sarah Johnson',
                action: 'started processing customer_call.wav',
                timestamp: '2 minutes ago',
                status: 'processing'
              }
            ],
            metrics: {
              activeConnections: Math.floor(Math.random() * 50) + 100,
              currentLoad: Math.floor(Math.random() * 30) + 60,
              processingQueue: Math.floor(Math.random() * 10) + 2
            }
          };
          
          setData(mockData);
          onMessage?.(mockData);
        }, 5000); // Update every 5 seconds
        
        onOpen?.();
        
        // Store interval for cleanup
        websocketRef.current = { close: () => clearInterval(interval) } as any;
      }, 1000);
      
    } catch (err) {
      console.error('WebSocket connection failed:', err);
      setError(err as Event);
      setConnectionStatus('Closed');
      onError?.(err as Event);
      
      // Attempt to reconnect
      if (reconnectAttemptsRef.current < reconnectAttempts) {
        reconnectAttemptsRef.current++;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval);
      }
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (websocketRef.current) {
      setConnectionStatus('Closing');
      websocketRef.current.close();
      websocketRef.current = null;
      setConnectionStatus('Closed');
      onClose?.();
    }
  };

  const sendMessage = (message: any) => {
    if (websocketRef.current && connectionStatus === 'Open') {
      // In production: websocketRef.current.send(JSON.stringify(message));
      console.log('Would send message:', message);
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [url]);

  return {
    data,
    connectionStatus,
    error,
    sendMessage,
    reconnect: connect,
    disconnect
  };
};
