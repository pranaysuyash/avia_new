import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import axios from 'axios';

interface User {
  id: number;
  email: string;
  name: string;
  role: string;
  tier?: string;
}

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

interface AuthContextType {
  user: User | null;
  tokens: AuthTokens | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Configure axios defaults
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
axios.defaults.baseURL = API_BASE_URL;

// Token storage utilities
const TOKEN_KEY = 'auth_tokens';
const USER_KEY = 'auth_user';

const saveTokens = (tokens: AuthTokens) => {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
};

const getTokens = (): AuthTokens | null => {
  const tokens = localStorage.getItem(TOKEN_KEY);
  return tokens ? JSON.parse(tokens) : null;
};

const removeTokens = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

const saveUser = (user: User) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

const getUser = (): User | null => {
  const user = localStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Setup axios interceptors for token management
  useEffect(() => {
    // Request interceptor to add token
    const requestInterceptor = axios.interceptors.request.use(
      (config) => {
        const tokens = getTokens();
        if (tokens?.accessToken) {
          config.headers.Authorization = `Bearer ${tokens.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle 401 and refresh token
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            await refreshAccessToken();
            const tokens = getTokens();
            if (tokens?.accessToken) {
              originalRequest.headers.Authorization = `Bearer ${tokens.accessToken}`;
            }
            return axios(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout user
            await logout();
            return Promise.reject(refreshError);
          }
        }
        
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.request.eject(requestInterceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedTokens = getTokens();
        const storedUser = getUser();
        
        if (storedTokens && storedUser) {
          setTokens(storedTokens);
          setUser(storedUser);
          
          // Verify token is still valid
          try {
            const response = await axios.get('/api/auth/me');
            setUser(response.data);
            saveUser(response.data);
          } catch (error) {
            // Token invalid, try refresh
            await refreshAccessToken();
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        removeTokens();
      } finally {
        setIsLoading(false);
      }
    };
    
    initAuth();
  }, []);

  const refreshAccessToken = useCallback(async () => {
    try {
      const currentTokens = getTokens();
      if (!currentTokens?.refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await axios.post('/api/auth/refresh', {
        refresh_token: currentTokens.refreshToken
      });
      
      const newTokens: AuthTokens = {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token || currentTokens.refreshToken,
        expiresIn: response.data.expires_in
      };
      
      setTokens(newTokens);
      saveTokens(newTokens);
      
      // Update user data if provided
      if (response.data.user) {
        setUser(response.data.user);
        saveUser(response.data.user);
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setError(null);
      setIsLoading(true);
      
      const response = await axios.post('/api/auth/login', {
        email,
        password
      });
      
      const tokens: AuthTokens = {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        expiresIn: response.data.expires_in
      };
      
      setTokens(tokens);
      setUser(response.data.user);
      saveTokens(tokens);
      saveUser(response.data.user);
      
      // Set up token refresh timer
      setupTokenRefreshTimer(tokens.expiresIn);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Login failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (email: string, password: string, name: string) => {
    try {
      setError(null);
      setIsLoading(true);
      
      const response = await axios.post('/api/auth/signup', {
        email,
        password,
        name
      });
      
      const tokens: AuthTokens = {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        expiresIn: response.data.expires_in
      };
      
      setTokens(tokens);
      setUser(response.data.user);
      saveTokens(tokens);
      saveUser(response.data.user);
      
      // Set up token refresh timer
      setupTokenRefreshTimer(tokens.expiresIn);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Signup failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Call logout endpoint if available
      if (tokens?.accessToken) {
        await axios.post('/api/auth/logout');
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setTokens(null);
      removeTokens();
      clearTokenRefreshTimer();
    }
  };

  // Token refresh timer
  let refreshTimer: NodeJS.Timeout | null = null;
  
  const setupTokenRefreshTimer = (expiresIn: number) => {
    clearTokenRefreshTimer();
    
    // Refresh token 5 minutes before expiry
    const refreshTime = (expiresIn - 300) * 1000;
    
    if (refreshTime > 0) {
      refreshTimer = setTimeout(async () => {
        try {
          await refreshAccessToken();
        } catch (error) {
          console.error('Auto token refresh failed:', error);
        }
      }, refreshTime);
    }
  };
  
  const clearTokenRefreshTimer = () => {
    if (refreshTimer) {
      clearTimeout(refreshTimer);
      refreshTimer = null;
    }
  };

  const value: AuthContextType = {
    user,
    tokens,
    login,
    logout,
    signup,
    refreshAccessToken,
    isAuthenticated: !!user && !!tokens,
    isLoading,
    error
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;