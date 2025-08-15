/**
 * Cross-Platform Mobile Authentication Service
 * Handles authentication for React Native mobile app
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { apiClient } from './cross_platform_api';

class MobileAuthService {
  constructor() {
    this.storageKey = '@transcription_app_auth';
    this.userKey = '@transcription_app_user';
  }

  // Load stored authentication data
  async loadStoredAuth() {
    try {
      const authData = await AsyncStorage.getItem(this.storageKey);
      const userData = await AsyncStorage.getItem(this.userKey);
      
      if (authData) {
        const parsedAuth = JSON.parse(authData);
        const parsedUser = userData ? JSON.parse(userData) : null;
        
        // Validate token expiration
        if (parsedAuth.token && parsedAuth.expiresAt) {
          const now = new Date().getTime();
          if (parsedAuth.expiresAt > now) {
            return {
              token: parsedAuth.token,
              user: parsedUser,
              isAuthenticated: true
            };
          } else {
            // Token expired, clear storage
            await this.clearAuth();
          }
        }
      }
      
      return { token: null, user: null, isAuthenticated: false };
    } catch (error) {
      console.error('Error loading stored auth:', error);
      return { token: null, user: null, isAuthenticated: false };
    }
  }

  // Save authentication data
  async saveAuth(token, user, expiresIn = 3600000) { // Default 1 hour
    try {
      const authData = {
        token,
        expiresAt: new Date().getTime() + expiresIn
      };
      
      await AsyncStorage.setItem(this.storageKey, JSON.stringify(authData));
      await AsyncStorage.setItem(this.userKey, JSON.stringify(user));
      
      return true;
    } catch (error) {
      console.error('Error saving auth data:', error);
      return false;
    }
  }

  // Clear authentication data
  async clearAuth() {
    try {
      await AsyncStorage.removeItem(this.storageKey);
      await AsyncStorage.removeItem(this.userKey);
      return true;
    } catch (error) {
      console.error('Error clearing auth data:', error);
      return false;
    }
  }

  // Login with email/password
  async login(email, password) {
    try {
      const response = await apiClient.post('/api/auth/login', {
        email,
        password
      });
      
      if (response.access_token) {
        await this.saveAuth(response.access_token, response.user);
        return { success: true, token: response.access_token, user: response.user };
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  // Login with OAuth provider
  async loginWithOAuth(provider) {
    try {
      // For mobile, we'll use deep linking or in-app browser
      const redirectUri = `${Platform.OS}://auth/callback`;
      
      // This would typically open an in-app browser or use a deep link
      // Implementation depends on the specific OAuth provider
      const authUrl = `/api/auth/${provider}?redirect_uri=${encodeURIComponent(redirectUri)}`;
      
      // In a real implementation, you would:
      // 1. Open an in-app browser or use deep linking
      // 2. Handle the callback
      // 3. Exchange the code for a token
      
      // For now, return a mock implementation
      const mockToken = 'mock_oauth_token_' + Date.now();
      const mockUser = { email: `${provider}_user@example.com`, name: `OAuth User` };
      
      await this.saveAuth(mockToken, mockUser);
      return { success: true, token: mockToken, user: mockUser };
    } catch (error) {
      console.error('OAuth login error:', error);
      throw error;
    }
  }

  // Register new user
  async register(userData) {
    try {
      const response = await apiClient.post('/api/auth/register', userData);
      
      if (response.access_token) {
        await this.saveAuth(response.access_token, response.user);
        return { success: true, token: response.access_token, user: response.user };
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }

  // Logout
  async logout() {
    try {
      // Try to call logout endpoint
      const storedAuth = await this.loadStoredAuth();
      if (storedAuth.token) {
        try {
          await apiClient.post('/api/auth/logout', {}, {
            headers: { Authorization: `Bearer ${storedAuth.token}` }
          });
        } catch (error) {
          console.warn('Logout endpoint call failed:', error);
          // Continue with local logout even if server call fails
        }
      }
      
      // Clear local storage
      await this.clearAuth();
      return true;
    } catch (error) {
      console.error('Logout error:', error);
      return false;
    }
  }

  // Refresh token
  async refreshToken() {
    try {
      const storedAuth = await this.loadStoredAuth();
      if (!storedAuth.token) {
        throw new Error('No token available for refresh');
      }
      
      const response = await apiClient.post('/api/auth/refresh', {
        token: storedAuth.token
      });
      
      if (response.access_token) {
        await this.saveAuth(response.access_token, storedAuth.user);
        return response.access_token;
      } else {
        throw new Error('Token refresh failed');
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      await this.logout(); // Logout if refresh fails
      throw error;
    }
  }

  // Check if user is authenticated
  async isAuthenticated() {
    const authData = await this.loadStoredAuth();
    return authData.isAuthenticated;
  }

  // Get current user
  async getCurrentUser() {
    const authData = await this.loadStoredAuth();
    return authData.user;
  }
}

// Create singleton instance
export const mobileAuthService = new MobileAuthService();

export default mobileAuthService;