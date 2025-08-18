const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiService = {
  async fetch(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  },

  async post(endpoint: string, data: any, options: RequestInit = {}) {
    const isFormData = data instanceof FormData;
    const requestOptions: RequestInit = {
      method: 'POST',
      ...options,
      body: isFormData ? data : JSON.stringify(data),
    };
    
    if (isFormData) {
      // Remove Content-Type header for FormData so browser can set it with boundary
      const headers = { ...requestOptions.headers };
      delete (headers as any)['Content-Type'];
      requestOptions.headers = headers;
    }
    
    return this.fetch(endpoint, requestOptions);
  },

  async get(endpoint: string, options?: { params?: Record<string, any>, responseType?: string }) {
    let url = endpoint;
    if (options?.params) {
      const queryString = new URLSearchParams(options.params).toString();
      url = `${endpoint}${endpoint.includes('?') ? '&' : '?'}${queryString}`;
    }
    
    if (options?.responseType === 'blob') {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }
      
      return { data: await response.blob() };
    }
    
    return this.fetch(url);
  },

  async put(endpoint: string, data: any, options: RequestInit = {}) {
    return this.fetch(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
      ...options,
    });
  },

  async delete(endpoint: string) {
    return this.fetch(endpoint, {
      method: 'DELETE',
    });
  },
};

// Analytics API
export const analyticsAPI = {
  async getMetrics(period: string = '30d') {
    return apiService.get(`/api/analytics/metrics?period=${period}`);
  },
  
  async getUsageStats() {
    return apiService.get('/api/analytics/usage');
  },
  
  async getPerformanceData() {
    return apiService.get('/api/analytics/performance');
  },
  
  async getReportTypes() {
    return apiService.get('/api/analytics/report-types');
  },
  
  async generateReport(params: any) {
    return apiService.post('/api/analytics/generate-report', params);
  },
  
  async exportReport(params: any) {
    return apiService.post('/api/analytics/export', params);
  },
  
  async getCustomReports() {
    return apiService.get('/api/analytics/custom-reports');
  },
  
  async generateAnalytics(params: any) {
    return apiService.post('/api/analytics/generate', params);
  },
  
  async exportAnalytics(type: string, params: any) {
    return apiService.post(`/api/analytics/export/${type}`, params);
  },
  
  async getRealtimeMetric(metric: string) {
    return apiService.get(`/api/analytics/realtime/${metric}`);
  }
};

// Cache API
export const cacheAPI = {
  async getMetrics() {
    return apiService.get('/api/cache/metrics');
  },
  
  async clearCache(key?: string) {
    return apiService.post('/api/cache/clear', { key });
  }
};

// Collaboration API  
export const collaborationAPI = {
  async joinRoom(roomId: string) {
    return apiService.post('/api/collaboration/join', { roomId });
  },
  
  async leaveRoom(roomId: string) {
    return apiService.post('/api/collaboration/leave', { roomId });
  }
};

export default apiService;