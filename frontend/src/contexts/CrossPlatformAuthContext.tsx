/**
 * Cross-Platform Authentication Context
 * Handles authentication for web, desktop (Electron), and mobile platforms
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiClient, PLATFORM } from '../utils/cross_platform_api';

// Create context
const AuthContext = createContext();

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Load user from storage on mount
  useEffect(() => {
    const loadStoredAuth = async () => {
      try {
        // Check different storage locations based on platform
        let storedToken = null;
        let storedUser = null;
        
        if (PLATFORM.isWeb) {
          storedToken = localStorage.getItem('auth_token') || localStorage.getItem('access_token');
          storedUser = localStorage.getItem('user');
        } else if (PLATFORM.isElectron) {
          // Electron can use localStorage but also has access to Node.js
          storedToken = localStorage.getItem('auth_token') || localStorage.getItem('access_token');
          storedUser = localStorage.getItem('user');
          
          // Fallback to file-based storage for desktop
          if (!storedToken) {
            try {
              const { ipcRenderer } = window.require('electron');
              const desktopAuth = await ipcRenderer.invoke('get-desktop-auth');
              if (desktopAuth && desktopAuth.token) {
                storedToken = desktopAuth.token;
                storedUser = desktopAuth.user;
              }
            } catch (error) {
              console.debug('Electron IPC not available for auth:', error);
            }
          }
        } else if (PLATFORM.isReactNative) {
          // React Native uses AsyncStorage
          try {
            const AsyncStorage = require('@react-native-async-storage/async-storage').default;
            storedToken = await AsyncStorage.getItem('auth_token');
            storedUser = await AsyncStorage.getItem('user');
          } catch (error) {
            console.debug('AsyncStorage not available:', error);
          }
        }
        
        // Validate and set user
        if (storedToken) {
          setToken(storedToken);
          
          // Decode JWT to get user info (without verification for client-side)
          try {
            const payload = JSON.parse(atob(storedToken.split('.')[1]));
            if (payload.exp && payload.exp * 1000 > Date.now()) {
              // Token is valid
              setUser(storedUser ? JSON.parse(storedUser) : payload);
              setIsAuthenticated(true);
            } else {
              // Token expired
              await logout();
            }
          } catch (error) {
            console.debug('Failed to decode token:', error);
            // Even if we can't decode, keep the token for server validation
            if (storedUser) {
              setUser(JSON.parse(storedUser));
              setIsAuthenticated(true);
            }
          }
        }
      } catch (error) {
        console.error('Error loading stored auth:', error);
      } finally {
        setLoading(false);
      }
    };

    loadStoredAuth();
  }, []);

  // Save auth data to storage
  const saveAuthData = useCallback(async (token, userData) => {
    try {
      if (PLATFORM.isWeb || PLATFORM.isElectron) {
        if (token) localStorage.setItem('auth_token', token);
        if (userData) localStorage.setItem('user', JSON.stringify(userData));
      } else if (PLATFORM.isReactNative) {
        const AsyncStorage = require('@react-native-async-storage/async-storage').default;
        if (token) await AsyncStorage.setItem('auth_token', token);
        if (userData) await AsyncStorage.setItem('user', JSON.stringify(userData));
      }
      
      // Save to Electron secure storage if available
      if (PLATFORM.isElectron) {
        try {
          const { ipcRenderer } = window.require('electron');
          await ipcRenderer.invoke('save-desktop-auth', { token, user: userData });
        } catch (error) {
          console.debug('Electron secure storage not available:', error);
        }
      }
    } catch (error) {
      console.error('Error saving auth data:', error);
    }
  }, []);

  // Login function
  const login = useCallback(async (credentials) => {
    try {
      setLoading(true);
      
      // Determine login endpoint based on credentials type
      let endpoint = '/api/auth/login';
      if (credentials.provider) {
        // OAuth login
        endpoint = `/api/auth/${credentials.provider}/callback`;
      } else if (credentials.apiKey) {
        // API key authentication
        endpoint = '/api/auth/api-key';
      }
      
      const response = await apiClient.post(endpoint, credentials);
      
      if (response.access_token) {
        setToken(response.access_token);
        setUser(response.user || { email: credentials.email });
        setIsAuthenticated(true);
        
        // Save auth data
        await saveAuthData(response.access_token, response.user || { email: credentials.email });
        
        return { success: true, user: response.user };
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Login error:', error);
      
      // Handle different error types
      if (error.message && error.message.includes('401')) {
        throw new Error('Invalid credentials');
      } else if (error.message && error.message.includes('network')) {
        throw new Error('Network error - please check your connection');
      } else {
        throw new Error('Login failed - please try again');
      }
    } finally {
      setLoading(false);
    }
  }, [saveAuthData]);

  // Logout function
  const logout = useCallback(async () => {
    try {
      setLoading(true);
      
      // Call logout endpoint if token exists
      if (token) {
        try {
          await apiClient.post('/api/auth/logout', {}, {
            headers: { Authorization: `Bearer ${token}` }
          });
        } catch (error) {
          console.debug('Logout endpoint call failed:', error);
          // Continue with local logout even if server call fails
        }
      }
      
      // Clear local storage
      if (PLATFORM.isWeb || PLATFORM.isElectron) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
      } else if (PLATFORM.isReactNative) {
        try {
          const AsyncStorage = require('@react-native-async-storage/async-storage').default;
          await AsyncStorage.multiRemove(['auth_token', 'access_token', 'refresh_token', 'user']);
        } catch (error) {
          console.debug('AsyncStorage clear failed:', error);
        }
      }
      
      // Clear Electron secure storage
      if (PLATFORM.isElectron) {
        try {
          const { ipcRenderer } = window.require('electron');
          await ipcRenderer.invoke('clear-desktop-auth');
        } catch (error) {
          console.debug('Electron secure storage clear failed:', error);
        }
      }
      
      // Reset state
      setUser(null);
      setToken(null);
      setIsAuthenticated(false);
      
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Register function
  const register = useCallback(async (userData) => {
    try {
      setLoading(true);
      
      const response = await apiClient.post('/api/auth/register', userData);
      
      if (response.access_token) {
        setToken(response.access_token);
        setUser(response.user);
        setIsAuthenticated(true);
        
        // Save auth data
        await saveAuthData(response.access_token, response.user);
        
        return { success: true, user: response.user };
      } else {
        return { success: false, error: 'Registration failed' };
      }
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [saveAuthData]);

  // Refresh token
  const refreshToken = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await apiClient.post('/api/auth/refresh', {
        refresh_token: refreshToken
      });
      
      if (response.access_token) {
        setToken(response.access_token);
        await saveAuthData(response.access_token, user);
        return response.access_token;
      } else {
        throw new Error('Token refresh failed');
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      await logout(); // Logout if refresh fails
      throw error;
    }
  }, [user, logout, saveAuthData]);

  // Expose values
  const value = {
    user,
    token,
    isAuthenticated,
    loading,
    login,
    logout,
    register,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

export default AuthContext;