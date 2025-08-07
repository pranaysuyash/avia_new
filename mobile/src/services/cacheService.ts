/**
 * Cache Service - React Native Mobile Version
 * Unified service for interacting with Redis cache across all platforms
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export interface CacheStats {
  connected: boolean;
  uptime_seconds: number;
  memory: {
    used_bytes: number;
    used_human: string;
    peak_bytes: number;
    peak_human: string;
    rss_bytes: number;
    fragmentation_ratio: number;
  };
  stats: {
    total_requests: number;
    hits: number;
    misses: number;
    hit_rate: number;
    evicted_keys: number;
    expired_keys: number;
    ops_per_sec: number;
  };
  clients: {
    connected: number;
    blocked: number;
    max_clients: number;
  };
  keyspace: {
    total_keys: number;
    databases: Record<string, {
      count: number;
      sample_keys: string[];
    }>;
  };
}

export interface TranscriptionCacheRequest {
  file_key: string;
  language?: string;
  prompt?: string;
  temperature?: number;
  use_cache?: boolean;
}

export interface TranscriptionCacheResponse {
  transcript_id: string;
  text: string;
  segments: Array<{
    id: number;
    start: number;
    end: number;
    text: string;
    confidence?: number;
  }>;
  language: string;
  duration: number;
  cached: boolean;
  created_at: string;
}

export class CacheService {
  private baseUrl: string;
  private authToken: string | null = null;

  constructor(baseUrl: string = 'http://localhost:8000/api') {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
  }

  /**
   * Set authentication token
   */
  async setAuthToken(token: string): Promise<void> {
    this.authToken = token;
    // Store token in AsyncStorage for persistence
    try {
      await AsyncStorage.setItem('@cache_service_token', token);
    } catch (error) {
      console.warn('Failed to store auth token:', error);
    }
  }

  /**
   * Load authentication token from storage
   */
  async loadAuthToken(): Promise<string | null> {
    if (this.authToken) {
      return this.authToken;
    }

    try {
      const token = await AsyncStorage.getItem('@cache_service_token');
      if (token) {
        this.authToken = token;
      }
      return token;
    } catch (error) {
      console.warn('Failed to load auth token:', error);
      return null;
    }
  }

  /**
   * Clear authentication token
   */
  async clearAuthToken(): Promise<void> {
    this.authToken = null;
    try {
      await AsyncStorage.removeItem('@cache_service_token');
    } catch (error) {
      console.warn('Failed to clear auth token:', error);
    }
  }

  /**
   * Get request headers
   */
  private async getHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    const token = await this.loadAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  /**
   * Handle API response
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorText = await response.text();
        errorMessage += `: ${errorText}`;
      } catch {
        errorMessage += ': Unknown error';
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<CacheStats> {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.baseUrl}/v1/transcription/cached/cache-stats`, {
      method: 'GET',
      headers,
    });

    return this.handleResponse<CacheStats>(response);
  }

  /**
   * Transcribe file with caching
   */
  async transcribeWithCache(request: TranscriptionCacheRequest): Promise<TranscriptionCacheResponse> {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.baseUrl}/v1/transcription/cached/transcribe`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    return this.handleResponse<TranscriptionCacheResponse>(response);
  }

  /**
   * Invalidate user's cache
   */
  async invalidateUserCache(): Promise<{ success: boolean; message: string }> {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.baseUrl}/v1/transcription/cached/invalidate-cache`, {
      method: 'POST',
      headers,
    });

    return this.handleResponse<{ success: boolean; message: string }>(response);
  }

  /**
   * Warm cache with specific transcripts
   */
  async warmCache(transcriptIds: string[] = []): Promise<{ success: boolean; message: string }> {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.baseUrl}/v1/transcription/cached/warm-cache`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ transcript_ids: transcriptIds }),
    });

    return this.handleResponse<{ success: boolean; message: string }>(response);
  }

  /**
   * Get user's cached transcripts
   */
  async getUserTranscripts(limit: number = 50, offset: number = 0): Promise<any[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    const headers = await this.getHeaders();
    const response = await fetch(`${this.baseUrl}/v1/transcription/cached/transcripts?${params}`, {
      method: 'GET',
      headers,
    });

    return this.handleResponse<any[]>(response);
  }

  /**
   * Calculate cache efficiency metrics
   */
  calculateEfficiency(stats: CacheStats): {
    hitRate: number;
    missRate: number;
    efficiency: 'excellent' | 'good' | 'fair' | 'poor';
    memoryUtilization: number;
    recommendations: string[];
  } {
    const hitRate = stats.stats.hit_rate;
    const missRate = 100 - hitRate;
    const memoryUtilization = (stats.memory.used_bytes / stats.memory.peak_bytes) * 100;

    let efficiency: 'excellent' | 'good' | 'fair' | 'poor';
    const recommendations: string[] = [];

    if (hitRate >= 90) {
      efficiency = 'excellent';
    } else if (hitRate >= 70) {
      efficiency = 'good';
    } else if (hitRate >= 50) {
      efficiency = 'fair';
      recommendations.push('Consider warming cache with frequently accessed transcripts');
    } else {
      efficiency = 'poor';
      recommendations.push('Cache hit rate is low - review caching strategy');
      recommendations.push('Consider increasing cache TTL for transcriptions');
    }

    if (stats.stats.evicted_keys > stats.keyspace.total_keys * 0.1) {
      recommendations.push('High eviction rate - consider increasing memory allocation');
    }

    if (stats.memory.fragmentation_ratio > 1.5) {
      recommendations.push('Memory fragmentation is high - consider restarting Redis');
    }

    if (stats.clients.connected > stats.clients.max_clients * 0.8) {
      recommendations.push('Approaching client connection limit');
    }

    return {
      hitRate,
      missRate,
      efficiency,
      memoryUtilization: Math.max(0, memoryUtilization),
      recommendations,
    };
  }

  /**
   * Export cache statistics
   */
  exportCacheStats(stats: CacheStats): string {
    const analysis = this.calculateEfficiency(stats);
    
    const report = {
      timestamp: new Date().toISOString(),
      platform: 'react-native',
      connection: {
        status: stats.connected ? 'Connected' : 'Disconnected',
        uptime: `${Math.floor(stats.uptime_seconds / 3600)}h ${Math.floor((stats.uptime_seconds % 3600) / 60)}m`,
      },
      performance: {
        hit_rate: `${stats.stats.hit_rate.toFixed(2)}%`,
        total_requests: stats.stats.total_requests,
        hits: stats.stats.hits,
        misses: stats.stats.misses,
        ops_per_second: stats.stats.ops_per_sec,
        efficiency: analysis.efficiency,
      },
      memory: {
        used: stats.memory.used_human,
        peak: stats.memory.peak_human,
        rss: `${Math.round(stats.memory.rss_bytes / (1024 * 1024))}MB`,
        fragmentation_ratio: stats.memory.fragmentation_ratio,
        utilization: `${analysis.memoryUtilization.toFixed(1)}%`,
      },
      keyspace: {
        total_keys: stats.keyspace.total_keys,
        evicted_keys: stats.stats.evicted_keys,
        expired_keys: stats.stats.expired_keys,
        databases: stats.keyspace.databases,
      },
      clients: {
        connected: stats.clients.connected,
        blocked: stats.clients.blocked,
        max_clients: stats.clients.max_clients,
      },
      recommendations: analysis.recommendations,
    };

    return JSON.stringify(report, null, 2);
  }

  /**
   * Cache historical stats locally (mobile specific)
   */
  async cacheStatsHistory(stats: CacheStats): Promise<void> {
    try {
      const timestamp = Date.now();
      const historyKey = `@cache_stats_history_${timestamp}`;
      const historyValue = JSON.stringify({
        timestamp,
        stats,
      });

      await AsyncStorage.setItem(historyKey, historyValue);

      // Keep only last 24 hours of data
      const cutoff = timestamp - 24 * 60 * 60 * 1000;
      const allKeys = await AsyncStorage.getAllKeys();
      const historyKeys = allKeys.filter(key => key.startsWith('@cache_stats_history_'));
      
      for (const key of historyKeys) {
        const keyTimestamp = parseInt(key.split('_').pop() || '0');
        if (keyTimestamp < cutoff) {
          await AsyncStorage.removeItem(key);
        }
      }
    } catch (error) {
      console.warn('Failed to cache stats history:', error);
    }
  }

  /**
   * Get cached stats history (mobile specific)
   */
  async getCachedStatsHistory(): Promise<Array<{ timestamp: number; stats: CacheStats }>> {
    try {
      const allKeys = await AsyncStorage.getAllKeys();
      const historyKeys = allKeys.filter(key => key.startsWith('@cache_stats_history_'));
      
      const history = [];
      for (const key of historyKeys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          const parsed = JSON.parse(value);
          history.push(parsed);
        }
      }

      return history.sort((a, b) => a.timestamp - b.timestamp);
    } catch (error) {
      console.warn('Failed to get cached stats history:', error);
      return [];
    }
  }
}

// Default instance
export const cacheService = new CacheService();

// Utility functions
export const formatBytes = (bytes: number): string => {
  const sizes = ['B', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 B';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
};

export const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
};

export const getCacheHealthColor = (hitRate: number): string => {
  if (hitRate >= 90) return '#10B981'; // green
  if (hitRate >= 70) return '#F59E0B'; // yellow
  if (hitRate >= 50) return '#EF4444'; // red
  return '#6B7280'; // gray
};

export const getCacheHealthStatus = (hitRate: number): string => {
  if (hitRate >= 90) return 'Excellent';
  if (hitRate >= 70) return 'Good';
  if (hitRate >= 50) return 'Fair';
  return 'Poor';
};