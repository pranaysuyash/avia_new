/**
 * Mobile App API Configuration
 * Handles API calls for React Native mobile platform
 */

import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Determine the base URL based on the platform
const getBaseURL = () => {
  // In development, use localhost
  // In production, use the deployed API URL
  if (__DEV__) {
    // Check if we're running on a simulator or physical device
    const isAndroidEmulator = Platform.OS === 'android' && 
      (Platform.constants.Brand === 'generic' || 
       Platform.constants.Model.includes('sdk') ||
       Platform.constants.Manufacturer.includes('Genymotion'));
       
    if (isAndroidEmulator) {
      // Android emulator needs to use 10.0.2.2 to reach host localhost
      return 'http://10.0.2.2:8000';
    } else if (Platform.OS === 'android') {
      // Physical Android device - need to use IP address of development machine
      // This should be configurable
      return 'http://192.168.1.100:8000'; // Replace with actual IP
    } else {
      // iOS simulator can use localhost
      return 'http://localhost:8000';
    }
  } else {
    // Production URL - replace with your actual API URL
    return 'https://yourdomain.com/api';
  }
};

// API Configuration
export const MOBILE_API_CONFIG = {
  BASE_URL: getBaseURL(),
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
};

// Mobile API Client
class MobileAPIClient {
  constructor() {
    this.baseURL = MOBILE_API_CONFIG.BASE_URL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  // Get authentication headers
  async getAuthHeaders() {
    const token = await AsyncStorage.getItem('auth_token');
    const apiKey = await AsyncStorage.getItem('api_key');
    
    const headers = { ...this.defaultHeaders };
    
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    } else if (apiKey) {
      headers['X-API-Key'] = apiKey;
      headers.Authorization = `ApiKey ${apiKey}`;
    }
    
    return headers;
  }

  // Enhanced fetch with retry logic and error handling
  async fetch(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      ...this.defaultHeaders,
      ...(await this.getAuthHeaders()),
      ...(options.headers || {}),
    };

    const config = {
      method: 'GET',
      headers,
      timeout: MOBILE_API_CONFIG.TIMEOUT,
      ...options,
    };

    // Handle file upload differently for mobile
    if (config.body instanceof FormData) {
      // Remove Content-Type header for FormData uploads
      // Let the browser set it automatically with boundary
      delete headers['Content-Type'];
    }

    // Retry logic
    let lastError;
    for (let attempt = 1; attempt <= MOBILE_API_CONFIG.RETRY_ATTEMPTS; attempt++) {
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
              ...(await this.getAuthHeaders()),
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
        if (attempt === MOBILE_API_CONFIG.RETRY_ATTEMPTS) {
          throw error;
        }
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, MOBILE_API_CONFIG.RETRY_DELAY * attempt));
      }
    }
    
    throw lastError;
  }

  // Fetch with timeout
  async _fetchWithTimeout(url, options) {
    const { timeout = MOBILE_API_CONFIG.TIMEOUT, ...fetchOptions } = options;
    
    // Use AbortController for timeout
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
      const refreshToken = await AsyncStorage.getItem('refresh_token');
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
        await AsyncStorage.setItem('auth_token', data.access_token);
        if (data.refresh_token) {
          await AsyncStorage.setItem('refresh_token', data.refresh_token);
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
    let body = data;
    
    // Handle different data types
    if (!(data instanceof FormData)) {
      body = JSON.stringify(data);
    }
    
    const response = await this.fetch(endpoint, {
      method: 'POST',
      body,
      ...options,
    });
    return response.json();
  }

  // PUT request
  async put(endpoint, data, options = {}) {
    let body = JSON.stringify(data);
    
    const response = await this.fetch(endpoint, {
      method: 'PUT',
      body,
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

  // File upload with progress (for mobile)
  async uploadFile(endpoint, fileUri, fileName, mimeType, onProgress) {
    try {
      // For mobile, we need to create a FormData object with the file URI
      const formData = new FormData();
      
      // Add file to form data
      formData.append('file', {
        uri: fileUri,
        type: mimeType,
        name: fileName,
      });
      
      // Create request options
      const options = {
        method: 'POST',
        body: formData,
        headers: {
          ...(await this.getAuthHeaders()),
          // Don't set Content-Type for FormData - let fetch handle it
        },
      };
      
      // For progress tracking, we might need to use a different approach on mobile
      // This is a simplified version - full implementation would require more complex networking
      
      const response = await this.fetch(endpoint, options);
      return await response.json();
      
    } catch (error) {
      console.error('File upload error:', error);
      throw error;
    }
  }
}

// Create singleton instance
export const mobileApiClient = new MobileAPIClient();

// Export convenience functions
export const mobileApi = {
  get: mobileApiClient.get.bind(mobileApiClient),
  post: mobileApiClient.post.bind(mobileApiClient),
  put: mobileApiClient.put.bind(mobileApiClient),
  delete: mobileApiClient.delete.bind(mobileApiClient),
  uploadFile: mobileApiClient.uploadFile.bind(mobileApiClient),
};

export default mobileApiClient;