import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, API_ENDPOINTS } from '@/lib/api-client';
import { useDevelopmentMode, mockUser } from './useDevelopmentMode';

// Types
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  initials: string;
  role: 'admin' | 'user' | 'viewer';
  teamId?: string;
  preferences: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    notifications: boolean;
  };
  subscription: {
    plan: 'free' | 'pro' | 'enterprise';
    status: 'active' | 'inactive' | 'trial';
    expiresAt?: string;
  };
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  user: User;
  token: string;
  refreshToken: string;
}

// Custom hook for authentication
export function useAuth() {
  const queryClient = useQueryClient();
  const { isDevelopmentMode, isChecking } = useDevelopmentMode();

  // Get current user
  const {
    data: user,
    isLoading: isLoadingUser,
    error: userError,
  } = useQuery({
    queryKey: ['auth', 'user'],
    queryFn: async (): Promise<User> => {
      if (isDevelopmentMode) {
        // Return mock user in development mode
        return mockUser;
      }
      const response = await apiClient.get<{ user: User }>(API_ENDPOINTS.AUTH.PROFILE);
      return response.user;
    },
    enabled: isDevelopmentMode || !!apiClient.authToken,
    retry: false,
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginCredentials): Promise<LoginResponse> => {
      const response = await apiClient.post<LoginResponse>(
        API_ENDPOINTS.AUTH.LOGIN,
        credentials
      );
      return response;
    },
    onSuccess: (data) => {
      // Store token
      apiClient.setToken(data.token);
      
      // Store refresh token
      localStorage.setItem('refresh_token', data.refreshToken);
      
      // Update user data in cache
      queryClient.setQueryData(['auth', 'user'], data.user);
      
      // Invalidate and refetch related queries
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (error) => {
      console.error('Login failed:', error);
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: async (): Promise<void> => {
      try {
        await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
      } catch (error) {
        // Continue with logout even if API call fails
        console.warn('Logout API call failed:', error);
      }
    },
    onSuccess: () => {
      // Clear tokens
      apiClient.clearToken();
      localStorage.removeItem('refresh_token');
      
      // Clear all cached data
      queryClient.clear();
      
      // Redirect to login
      window.location.href = '/login';
    },
  });

  // Refresh token mutation
  const refreshTokenMutation = useMutation({
    mutationFn: async (): Promise<{ token: string }> => {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await apiClient.post<{ token: string }>(
        API_ENDPOINTS.AUTH.REFRESH,
        { refreshToken }
      );
      return response;
    },
    onSuccess: (data) => {
      apiClient.setToken(data.token);
      // Retry the failed request that triggered the refresh
      queryClient.invalidateQueries({ queryKey: ['auth', 'user'] });
    },
    onError: () => {
      // Refresh failed, redirect to login
      logoutMutation.mutate();
    },
  });

  // Update user profile
  const updateProfileMutation = useMutation({
    mutationFn: async (updates: Partial<User>): Promise<User> => {
      const response = await apiClient.patch<{ user: User }>(
        API_ENDPOINTS.USERS.PROFILE,
        updates
      );
      return response.user;
    },
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(['auth', 'user'], updatedUser);
    },
  });

  // Helper functions
  const login = (credentials: LoginCredentials) => {
    return loginMutation.mutateAsync(credentials);
  };

  const logout = () => {
    logoutMutation.mutate();
  };

  const updateProfile = (updates: Partial<User>) => {
    return updateProfileMutation.mutateAsync(updates);
  };

  const refreshToken = () => {
    return refreshTokenMutation.mutateAsync();
  };

  // Check if user is authenticated
  const isAuthenticated = isDevelopmentMode ? !!user : (!!user && !!apiClient.authToken);

  // Check user permissions
  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    
    // Admin has all permissions
    if (user.role === 'admin') return true;
    
    // Define role-based permissions
    const permissions = {
      admin: ['*'],
      user: [
        'media.upload',
        'media.view',
        'jobs.create',
        'jobs.view',
        'transcription.create',
        'transcription.view',
        'profile.update',
      ],
      viewer: [
        'media.view',
        'jobs.view',
        'transcription.view',
      ],
    };
    
    const userPermissions = permissions[user.role] || [];
    return userPermissions.includes('*') || userPermissions.includes(permission);
  };

  // Check subscription status
  const hasActiveSubscription = (): boolean => {
    if (!user) return false;
    return user.subscription.status === 'active' || user.subscription.status === 'trial';
  };

  const canAccessFeature = (feature: string): boolean => {
    if (!user || !hasActiveSubscription()) return false;
    
    const featureAccess = {
      free: ['basic_transcription', 'basic_upload'],
      pro: [
        'basic_transcription',
        'basic_upload',
        'advanced_transcription',
        'real_time_transcription',
        'ai_summarization',
        'voice_profiling',
      ],
      enterprise: ['*'], // All features
    };
    
    const planFeatures = featureAccess[user.subscription.plan] || [];
    return planFeatures.includes('*') || planFeatures.includes(feature);
  };

  return {
    // State
    user,
    isAuthenticated,
    isLoading: isLoadingUser || isChecking,
    error: userError,
    isDevelopmentMode,
    
    // Actions
    login,
    logout,
    updateProfile,
    refreshToken,
    
    // Mutation states
    isLoggingIn: loginMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
    isUpdatingProfile: updateProfileMutation.isPending,
    
    // Errors
    loginError: loginMutation.error,
    logoutError: logoutMutation.error,
    updateProfileError: updateProfileMutation.error,
    
    // Permissions
    hasPermission,
    hasActiveSubscription,
    canAccessFeature,
  };
}

// Hook for protected routes
export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (!isLoading && !isAuthenticated) {
    window.location.href = '/login';
  }
  
  return { isAuthenticated, isLoading };
}

// Generate user initials from name
export function generateInitials(name: string): string {
  return name
    .split(' ')
    .map(part => part.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('');
}