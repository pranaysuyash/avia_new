/**
 * React Query hooks for API interactions
 */

import { useQuery, useMutation, useQueryClient, useInfiniteQuery, UseQueryOptions, UseMutationOptions, QueryClient } from '@tanstack/react-query';
import axios, { AxiosError } from 'axios';
import { useAuth } from '../contexts/AuthContext';

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Types
interface Transcription {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  content?: string;
  entities?: any;
  created_at: string;
  updated_at: string;
}

interface UploadResponse {
  id: string;
  message: string;
}

interface SearchResult {
  id: string;
  title: string;
  snippet: string;
  score: number;
}

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Query Keys
export const queryKeys = {
  transcriptions: ['transcriptions'] as const,
  transcription: (id: string) => ['transcription', id] as const,
  search: (query: string) => ['search', query] as const,
  analytics: ['analytics'] as const,
  user: ['user'] as const,
};

// Transcription Hooks
export const useTranscriptions = (options?: UseQueryOptions<Transcription[], AxiosError>) => {
  const { tokens } = useAuth();
  
  return useQuery<Transcription[], AxiosError>({
    queryKey: queryKeys.transcriptions,
    queryFn: async () => {
      const response = await apiClient.get('/api/transcriptions', {
        headers: {
          Authorization: tokens?.accessToken ? `Bearer ${tokens.accessToken}` : '',
        },
      });
      return response.data;
    },
    ...options,
  });
};

export const useTranscription = (id: string, options?: UseQueryOptions<Transcription, AxiosError>) => {
  const { tokens } = useAuth();
  
  return useQuery<Transcription, AxiosError>({
    queryKey: queryKeys.transcription(id),
    queryFn: async () => {
      const response = await apiClient.get(`/api/transcriptions/${id}`, {
        headers: {
          Authorization: tokens?.accessToken ? `Bearer ${tokens.accessToken}` : '',
        },
      });
      return response.data;
    },
    enabled: !!id,
    ...options,
  });
};

export const useUploadTranscription = (
  options?: UseMutationOptions<UploadResponse, AxiosError, FormData>
) => {
  const queryClient = useQueryClient();
  const { tokens } = useAuth();
  
  return useMutation<UploadResponse, AxiosError, FormData>({
    mutationFn: async (formData: FormData) => {
      const response = await apiClient.post('/api/transcriptions/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: tokens?.accessToken ? `Bearer ${tokens.accessToken}` : '',
        },
      });
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch transcriptions list
      queryClient.invalidateQueries({ queryKey: queryKeys.transcriptions });
    },
    ...options,
  });
};

export const useDeleteTranscription = (
  options?: UseMutationOptions<void, AxiosError, string>
) => {
  const queryClient = useQueryClient();
  const { tokens } = useAuth();
  
  return useMutation<void, AxiosError, string>({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/api/transcriptions/${id}`, {
        headers: {
          Authorization: tokens?.accessToken ? `Bearer ${tokens.accessToken}` : '',
        },
      });
    },
    onSuccess: (_, id) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: queryKeys.transcription(id) });
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: queryKeys.transcriptions });
    },
    ...options,
  });
};

// Search Hooks
export const useSearch = (
  query: string,
  options?: UseQueryOptions<SearchResult[], AxiosError>
) => {
  const { tokens } = useAuth();
  
  return useQuery<SearchResult[], AxiosError>({
    queryKey: queryKeys.search(query),
    queryFn: async () => {
      const response = await apiClient.get('/api/search', {
        params: { q: query },
        headers: {
          Authorization: tokens?.accessToken ? `Bearer ${tokens.accessToken}` : '',
        },
      });
      return response.data;
    },
    enabled: !!query && query.length > 2,
    staleTime: 60 * 1000, // Cache search results for 1 minute
    ...options,
  });
};

// Analytics Hooks
export const useAnalytics = (options?: UseQueryOptions<any, AxiosError>) => {
  const { tokens } = useAuth();
  
  return useQuery<any, AxiosError>({
    queryKey: queryKeys.analytics,
    queryFn: async () => {
      const response = await apiClient.get('/api/analytics/overview', {
        headers: {
          Authorization: tokens?.accessToken ? `Bearer ${tokens.accessToken}` : '',
        },
      });
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    ...options,
  });
};

// Optimistic Updates Example
export const useUpdateTranscription = (
  options?: UseMutationOptions<Transcription, AxiosError, { id: string; data: Partial<Transcription> }>
) => {
  const queryClient = useQueryClient();
  const { tokens } = useAuth();
  
  return useMutation<Transcription, AxiosError, { id: string; data: Partial<Transcription> }>({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.patch(`/api/transcriptions/${id}`, data, {
        headers: {
          Authorization: tokens?.accessToken ? `Bearer ${tokens.accessToken}` : '',
        },
      });
      return response.data;
    },
    onMutate: async ({ id, data }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.transcription(id) });
      
      // Snapshot the previous value
      const previousTranscription = queryClient.getQueryData(queryKeys.transcription(id));
      
      // Optimistically update to the new value
      queryClient.setQueryData(queryKeys.transcription(id), (old: any) => ({
        ...old,
        ...data,
      }));
      
      // Return a context object with the snapshotted value
      return { previousTranscription };
    },
    onError: (err, { id }, context: any) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousTranscription) {
        queryClient.setQueryData(queryKeys.transcription(id), context.previousTranscription);
      }
    },
    onSettled: (_, __, { id }) => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ queryKey: queryKeys.transcription(id) });
    },
    ...options,
  });
};

// Infinite Query Example for Pagination
export const useInfiniteTranscriptions = () => {
  const { tokens } = useAuth();
  
  return useInfiniteQuery({
    queryKey: ['transcriptions', 'infinite'],
    queryFn: async ({ pageParam }) => {
      const response = await apiClient.get('/api/transcriptions', {
        params: {
          offset: pageParam,
          limit: 20,
        },
        headers: {
          Authorization: tokens?.accessToken ? `Bearer ${tokens.accessToken}` : '',
        },
      });
      return response.data;
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage: any, pages: any[]) => {
      // Return the next offset or undefined if no more pages
      return lastPage.hasMore ? pages.length * 20 : undefined;
    },
  });
};

// Prefetch utility
export const prefetchTranscription = async (queryClient: QueryClient, id: string, token?: string) => {
  await queryClient.prefetchQuery({
    queryKey: queryKeys.transcription(id),
    queryFn: async () => {
      const response = await apiClient.get(`/api/transcriptions/${id}`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
        },
      });
      return response.data;
    },
    staleTime: 10 * 1000,
  });
};