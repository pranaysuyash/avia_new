/**
 * Cross-Platform WebSocket Connection Handler
 * Handles real-time communication for web, desktop, and mobile platforms
 */

import { Platform } from 'react-native'; // For mobile detection
import { io } from 'socket.io-client';

// Determine WebSocket URL based on platform
const getWebSocketURL = () => {
  // Check if we're in a browser environment
  if (typeof window !== 'undefined' && window.location) {
    // Browser environment
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // Development URLs
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      // Try common development ports
      if (port === '3000') {
        // React dev server - WebSocket likely on 8000
        return 'ws://localhost:8000';
      } else if (port === '8000') {
        // API server directly
        return 'ws://localhost:8000';
      } else {
        // Fallback
        return 'ws://localhost:8000';
      }
    }
    
    // Production URLs - convert HTTP to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
  }
  
  // Non-browser environment (Node.js, React Native, Electron main process)
  if (typeof process !== 'undefined' && process.env) {
    // Check for environment variables
    if (import.meta.env.VITE_WS_URL) {
      return import.meta.env.VITE_WS_URL;
    }
    
    if (process.env.EXPO_PUBLIC_WS_URL) {
      return process.env.EXPO_PUBLIC_WS_URL;
    }
    
    // Electron main process
    if (process.type === 'browser') {
      return 'ws://localhost:8000';
    }
    
    // React Native
    if (process.env.NODE_ENV === 'development') {
      // Check if we're on Android emulator
      if (Platform && Platform.OS === 'android') {
        const isAndroidEmulator = Platform.constants && 
          (Platform.constants.Brand === 'generic' || 
           Platform.constants.Model.includes('sdk') ||
           Platform.constants.Manufacturer.includes('Genymotion'));
           
        if (isAndroidEmulator) {
          return 'ws://10.0.2.2:8000'; // Android emulator needs 10.0.2.2 to reach host
        } else {
          return 'ws://192.168.1.100:8000'; // Replace with actual development machine IP
        }
      } else {
        return 'ws://localhost:8000';
      }
    }
  }
  
  // Fallback to localhost
  return 'ws://localhost:8000';
};

// WebSocket Configuration
export const WEBSOCKET_CONFIG = {
  URL: getWebSocketURL(),
  RECONNECT_ATTEMPTS: 5,
  RECONNECT_DELAY: 1000,
  RECONNECT_DELAY_MAX: 30000,
  TIMEOUT: 20000,
  AUTO_CONNECT: true,
  TRANSPORTS: ['websocket', 'polling'],
};

// Cross-Platform WebSocket Manager
class CrossPlatformWebSocketManager {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.listeners = new Map();
    this.reconnectTimer = null;
  }

  // Initialize WebSocket connection
  initialize(token = null) {
    try {
      // Close existing connection if any
      this.disconnect();
      
      // Create socket.io client
      this.socket = io(WEBSOCKET_CONFIG.URL, {
        transports: WEBSOCKET_CONFIG.TRANSPORTS,
        timeout: WEBSOCKET_CONFIG.TIMEOUT,
        reconnection: true,
        reconnectionAttempts: WEBSOCKET_CONFIG.RECONNECT_ATTEMPTS,
        reconnectionDelay: WEBSOCKET_CONFIG.RECONNECT_DELAY,
        reconnectionDelayMax: WEBSOCKET_CONFIG.RECONNECT_DELAY_MAX,
        autoConnect: WEBSOCKET_CONFIG.AUTO_CONNECT,
        query: token ? { token } : {},
        // Add authentication headers if available
        extraHeaders: token ? {
          'Authorization': `Bearer ${token}`,
        } : {},
      });
      
      // Attach event listeners
      this._attachEventListeners();
      
      // Attempt connection
      if (WEBSOCKET_CONFIG.AUTO_CONNECT) {
        this.connect();
      }
      
      console.log(`WebSocket initialized with URL: ${WEBSOCKET_CONFIG.URL}`);
      
    } catch (error) {
      console.error('WebSocket initialization error:', error);
    }
  }

  // Attach event listeners
  _attachEventListeners() {
    if (!this.socket) return;
    
    // Connection events
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this._emitEvent('connect');
    });
    
    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.isConnected = false;
      this._emitEvent('disconnect', reason);
      
      // Handle reconnection
      if (reason === 'io server disconnect') {
        // Server intentionally disconnected - don't reconnect automatically
        console.log('Server intentionally disconnected WebSocket');
      } else {
        // Try to reconnect
        this._scheduleReconnect();
      }
    });
    
    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.isConnected = false;
      this._emitEvent('connect_error', error);
      this._scheduleReconnect();
    });
    
    this.socket.on('connect_timeout', (timeout) => {
      console.warn('WebSocket connection timeout:', timeout);
      this.isConnected = false;
      this._emitEvent('connect_timeout', timeout);
      this._scheduleReconnect();
    });
    
    this.socket.on('reconnect', (attempt) => {
      console.log('WebSocket reconnected after', attempt, 'attempts');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this._emitEvent('reconnect', attempt);
    });
    
    this.socket.on('reconnect_attempt', (attempt) => {
      console.log('WebSocket reconnect attempt:', attempt);
      this.reconnectAttempts = attempt;
      this._emitEvent('reconnect_attempt', attempt);
    });
    
    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket failed to reconnect after maximum attempts');
      this.isConnected = false;
      this.reconnectAttempts = 0;
      this._emitEvent('reconnect_failed');
    });
    
    this.socket.on('reconnect_error', (error) => {
      console.error('WebSocket reconnect error:', error);
      this._emitEvent('reconnect_error', error);
    });
  }

  // Schedule reconnection
  _scheduleReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    
    if (this.reconnectAttempts < WEBSOCKET_CONFIG.RECONNECT_ATTEMPTS) {
      const delay = Math.min(
        WEBSOCKET_CONFIG.RECONNECT_DELAY * Math.pow(2, this.reconnectAttempts),
        WEBSOCKET_CONFIG.RECONNECT_DELAY_MAX
      );
      
      this.reconnectTimer = setTimeout(() => {
        console.log('Attempting WebSocket reconnection...');
        this.connect();
      }, delay);
    }
  }

  // Connect to WebSocket
  connect(token = null) {
    if (!this.socket) {
      this.initialize(token);
      return;
    }
    
    try {
      if (token) {
        // Update authentication
        this.socket.auth = { token };
        this.socket.query = { token };
      }
      
      this.socket.connect();
    } catch (error) {
      console.error('WebSocket connect error:', error);
    }
  }

  // Disconnect from WebSocket
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    
    this.isConnected = false;
    this.reconnectAttempts = 0;
  }

  // Emit event to server
  emit(event, data) {
    if (!this.socket) {
      console.warn('WebSocket not initialized');
      return false;
    }
    
    if (!this.isConnected) {
      console.warn('WebSocket not connected');
      return false;
    }
    
    try {
      this.socket.emit(event, data);
      return true;
    } catch (error) {
      console.error('WebSocket emit error:', error);
      return false;
    }
  }

  // Listen for events from server
  on(event, callback) {
    if (!this.socket) {
      console.warn('WebSocket not initialized');
      return false;
    }
    
    // Store listener for cleanup
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
    
    // Attach to socket
    this.socket.on(event, callback);
    return true;
  }

  // Remove event listener
  off(event, callback) {
    if (!this.socket) return;
    
    // Remove from our storage
    if (this.listeners.has(event)) {
      const listeners = this.listeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
    
    // Remove from socket
    this.socket.off(event, callback);
  }

  // Remove all listeners for an event
  offAll(event) {
    if (!this.socket) return;
    
    // Remove from our storage
    if (this.listeners.has(event)) {
      this.listeners.delete(event);
    }
    
    // Remove all listeners from socket
    this.socket.off(event);
  }

  // Emit event to local listeners (internal use)
  _emitEvent(event, data = null) {
    // Emit to local listeners
    if (this.listeners.has(event)) {
      const listeners = this.listeners.get(event);
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  }

  // Get connection status
  getStatus() {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      url: WEBSOCKET_CONFIG.URL,
    };
  }
}

// Create singleton instance
export const websocketManager = new CrossPlatformWebSocketManager();

// Export convenience functions
export const ws = {
  connect: websocketManager.connect.bind(websocketManager),
  disconnect: websocketManager.disconnect.bind(websocketManager),
  emit: websocketManager.emit.bind(websocketManager),
  on: websocketManager.on.bind(websocketManager),
  off: websocketManager.off.bind(websocketManager),
  offAll: websocketManager.offAll.bind(websocketManager),
  getStatus: websocketManager.getStatus.bind(websocketManager),
};

export default websocketManager;