/**
 * Cross-Platform API Configuration
 * Handles API calls for web, desktop, and mobile platforms
 */

// Determine the base URL based on the platform
const getBaseURL = () => {
  // Check if we're in a browser environment
  if (typeof window !== 'undefined' && window.location) {
    // Browser environment
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // Development URLs
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      // Try common development ports
      if (port === '3000') {
        // React dev server - API likely on 8000
        return 'http://localhost:8000';
      } else if (port === '8000') {
        // API server directly
        return 'http://localhost:8000';
      } else {
        // Fallback
        return 'http://localhost:8000';
      }
    }
    
    // Production URLs
    return window.location.origin;
  }
  
  // Non-browser environment (Node.js, React Native, Electron main process)
  if (typeof process !== 'undefined' && process.env) {
    // Check for environment variables
    if (process.env.REACT_APP_API_URL) {
      return process.env.REACT_APP_API_URL;
    }
    
    if (process.env.EXPO_PUBLIC_API_URL) {
      return process.env.EXPO_PUBLIC_API_URL;
    }
    
    // Electron main process
    if (process.type === 'browser') {
      return 'http://localhost:8000';
    }
    
    // React Native
    if (process.env.NODE_ENV === 'development') {
      return 'http://localhost:8000';
    }
  }
  
  // Fallback to localhost
  return 'http://localhost:8000';
};

// Determine WebSocket URL
const getWebSocketURL = () => {
  const baseURL = getBaseURL();
  
  // Convert HTTP to WS
  if (baseURL.startsWith('https://')) {
    return baseURL.replace('https://', 'wss://') + '/ws';
  } else {
    return baseURL.replace('http://', 'ws://') + '/ws';
  }
};

// API Configuration
export const API_CONFIG = {
  BASE_URL: getBaseURL(),
  WEBSOCKET_URL: getWebSocketURL(),
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
};

// Platform Detection
export const PLATFORM = {
  isWeb: typeof window !== 'undefined' && !window.process,
  isElectron: typeof window !== 'undefined' && !!window.process && window.process.type === 'renderer',
  isReactNative: typeof navigator !== 'undefined' && navigator.product === 'ReactNative',
  isNode: typeof process !== 'undefined' && process.versions && process.versions.node,
};

// Enhanced API Client
class APIClient {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.websocketURL = API_CONFIG.WEBSOCKET_URL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  // Get authentication headers
  getAuthHeaders() {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');
    const apiKey = localStorage.getItem('api_key');
    
    const headers = { ...this.defaultHeaders };
    
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    } else if (apiKey) {
      headers['X-API-Key'] = apiKey;
      headers.Authorization = `ApiKey ${apiKey}`;
    } else if (PLATFORM.isElectron) {
      // Electron desktop app - use demo key
      headers['X-API-Key'] = 'demo-desktop-key';
    }
    
    return headers;
  }

  // Enhanced fetch with retry logic and error handling
  async fetch(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      ...this.defaultHeaders,
      ...this.getAuthHeaders(),
      ...(options.headers || {}),
    };

    const config = {
      method: 'GET',
      headers,
      timeout: API_CONFIG.TIMEOUT,
      ...options,
    };

    // Retry logic
    let lastError;
    for (let attempt = 1; attempt <= API_CONFIG.RETRY_ATTEMPTS; attempt++) {
      try {
        const response = await this._fetchWithTimeout(url, config);
        
        // Handle different response statuses
        if (response.ok) {
          return response;
        }
        
        // Special handling for authentication errors
        if (response.status === 401) {
          // Try to refresh token
          const refreshed = await this._refreshToken();
          if (refreshed) {
            // Retry with new token
            config.headers = {
              ...config.headers,
              ...this.getAuthHeaders(),
            };
            continue; // Retry the request
          }
        }
        
        // Throw error for non-ok responses
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        
      } catch (error) {
        lastError = error;
        
        // Don't retry on client errors (4xx) except 401
        if (error.message && error.message.includes('4') && !error.message.includes('401')) {
          throw error;
        }
        
        // Don't retry on the last attempt
        if (attempt === API_CONFIG.RETRY_ATTEMPTS) {
          throw error;
        }
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, API_CONFIG.RETRY_DELAY * attempt));
      }
    }
    
    throw lastError;
  }

  // Fetch with timeout
  async _fetchWithTimeout(url, options) {
    const { timeout = API_CONFIG.TIMEOUT, ...fetchOptions } = options;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }

  // Token refresh
  async _refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        return false;
      }
      
      const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('auth_token', data.access_token);
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
        }
        return true;
      }
    } catch (error) {
      console.warn('Token refresh failed:', error);
    }
    
    return false;
  }

  // GET request
  async get(endpoint, options = {}) {
    const response = await this.fetch(endpoint, {
      method: 'GET',
      ...options,
    });
    return response.json();
  }

  // POST request
  async post(endpoint, data, options = {}) {
    const response = await this.fetch(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      ...options,
    });
    return response.json();
  }

  // PUT request
  async put(endpoint, data, options = {}) {
    const response = await this.fetch(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
      ...options,
    });
    return response.json();
  }

  // DELETE request
  async delete(endpoint, options = {}) {
    const response = await this.fetch(endpoint, {
      method: 'DELETE',
      ...options,
    });
    return response.json();
  }

  // File upload with progress
  async uploadFile(endpoint, file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    
    return new Promise((resolve, reject) => {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            resolve(xhr.responseText);
          }
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('POST', `${this.baseURL}${endpoint}`);
      
      // Add auth headers
      const authHeaders = this.getAuthHeaders();
      Object.keys(authHeaders).forEach(key => {
        xhr.setRequestHeader(key, authHeaders[key]);
      });

      xhr.send(formData);
    });
  }
}

// Create singleton instance
export const apiClient = new APIClient();

// Export convenience functions
export const api = {
  get: apiClient.get.bind(apiClient),
  post: apiClient.post.bind(apiClient),
  put: apiClient.put.bind(apiClient),
  delete: apiClient.delete.bind(apiClient),
  uploadFile: apiClient.uploadFile.bind(apiClient),
};

export default apiClient;