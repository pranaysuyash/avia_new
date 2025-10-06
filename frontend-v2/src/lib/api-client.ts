import { QueryClient } from '@tanstack/react-query';

// API Configuration - Connect to your existing FastAPI backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds

// API Client Class
class ApiClient {
  private baseURL: string;
  private timeout: number;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL, timeout: number = API_TIMEOUT) {
    this.baseURL = baseURL;
    this.timeout = timeout;
    this.loadToken();
  }

  get authToken(): string | null {
    return this.token;
  }

  // Token Management
  private loadToken(): void {
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken(): void {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  // HTTP Methods
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        ...options.headers,
      },
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        if (response.status === 401) {
          this.clearToken();
          window.location.href = '/login';
          throw new Error('Authentication required');
        }
        
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return response.text() as unknown as T;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError('Request timeout', 408);
      }
      
      throw new ApiError(
        error instanceof Error ? error.message : 'Network error',
        0
      );
    }
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(endpoint, this.baseURL);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    
    return this.request<T>(url.pathname + url.search);
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  // File Upload
  async uploadFile<T>(
    endpoint: string,
    file: File,
    additionalData?: Record<string, any>,
    onProgress?: (progress: number) => void
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append('file', file);
      
      if (additionalData) {
        Object.entries(additionalData).forEach(([key, value]) => {
          formData.append(key, String(value));
        });
      }

      const xhr = new XMLHttpRequest();
      
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
          } catch {
            resolve(xhr.responseText as unknown as T);
          }
        } else {
          reject(new ApiError(`Upload failed: ${xhr.statusText}`, xhr.status));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new ApiError('Upload failed', 0));
      });

      xhr.open('POST', `${this.baseURL}${endpoint}`);
      
      if (this.token) {
        xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
      }
      
      xhr.send(formData);
    });
  }
}

// Custom Error Class
export class ApiError extends Error {
  public status: number;
  public data?: any;

  constructor(
    message: string,
    status: number,
    data?: any
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

// API Client Instance
export const apiClient = new ApiClient();

// React Query Client Configuration
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (error instanceof ApiError && error.status === 401) {
          return false; // Don't retry auth errors
        }
        return failureCount < 3;
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
    },
    mutations: {
      retry: (failureCount, error) => {
        if (error instanceof ApiError && error.status < 500) {
          return false; // Don't retry client errors
        }
        return failureCount < 2;
      },
    },
  },
});

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// API Endpoints - Matching your existing FastAPI backend
export const API_ENDPOINTS = {
  // Authentication - Your existing endpoints
  AUTH: {
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout', 
    REFRESH: '/api/auth/refresh',
    PROFILE: '/api/users/profile', // Your actual endpoint
    REGISTER: '/api/auth/register',
  },
  
  // Health Check
  HEALTH: '/api/health',
  
  // Transcriptions - Your existing endpoints
  TRANSCRIPTIONS: {
    UPLOAD: '/api/transcriptions/upload',
    LIST: '/api/transcriptions',
    DETAILS: (id: string) => `/api/transcriptions/${id}`,
    DELETE: (id: string) => `/api/transcriptions/${id}`,
  },
  
  // Teams - Your existing endpoints
  TEAMS: {
    LIST: '/api/teams',
    CREATE: '/api/teams',
    DETAILS: (id: string) => `/api/teams/${id}`,
    MEMBERS: (id: string) => `/api/teams/${id}/members`,
    REMOVE_MEMBER: (teamId: string, userId: string) => `/api/teams/${teamId}/members/${userId}`,
  },
  
  // Storage - Your existing endpoints
  STORAGE: {
    PRESIGNED_UPLOAD: '/api/storage/presigned-upload',
    DOWNLOAD: (id: string) => `/api/storage/download/${id}`,
    STATS: '/api/storage/stats',
  },
  
  // User Management - Your existing endpoints
  USERS: {
    PROFILE: '/api/users/profile',
    API_KEYS: '/api/users/api-keys',
    DELETE_API_KEY: (id: string) => `/api/users/api-keys/${id}`,
  },
  
  // WebSocket endpoints
  WEBSOCKET: {
    SIGNALING: '/ws/signaling',
    ROOMS: '/api/v1/rooms',
    ROOM_INFO: (id: string) => `/api/v1/rooms/${id}`,
  },
} as const;