// API Service for connecting to the backend
import analytics from '../utils/analytics';
import { rateLimiters } from '../utils/rateLimiter';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  constructor() {
    this.token = localStorage.getItem('authToken');
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const startTime = Date.now();
    
    // Determine rate limiter based on endpoint
    let rateLimiter = rateLimiters.general;
    if (endpoint.includes('transcription')) {
      rateLimiter = rateLimiters.transcription;
    } else if (endpoint.includes('search')) {
      rateLimiter = rateLimiters.search;
    } else if (endpoint.includes('export')) {
      rateLimiter = rateLimiters.export;
    }
    
    // Check rate limit
    const rateCheck = rateLimiter.isAllowed();
    if (!rateCheck.allowed) {
      const waitTime = Math.ceil((rateCheck.resetTime - Date.now()) / 1000);
      const error = new Error(`Rate limit exceeded. Please wait ${waitTime} seconds.`);
      error.rateLimited = true;
      error.resetTime = rateCheck.resetTime;
      throw error;
    }
    
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
        ...options.headers,
      }
    };

    try {
      const response = await fetch(url, config);
      const duration = Date.now() - startTime;
      
      // Track API call
      analytics.trackAPICall(endpoint, options.method || 'GET', response.status, duration);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      const duration = Date.now() - startTime;
      
      // Track error
      if (!error.rateLimited) {
        analytics.trackAPICall(endpoint, options.method || 'GET', error.status || 500, duration);
      }
      
      console.error('API Request failed:', error);
      throw error;
    }
  }

  // Authentication
  async login(username, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    
    if (response.data?.access_token) {
      this.token = response.data.access_token;
      localStorage.setItem('authToken', this.token);
    }
    
    return response;
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.token = null;
      localStorage.removeItem('authToken');
    }
  }

  // Dashboard Stats
  async getDashboardStats() {
    try {
      // Try to get real stats from API
      const response = await this.request('/insights/dashboard-stats');
      return response.data;
    } catch (error) {
      // Return mock data if API fails
      console.warn('Using mock data for dashboard stats');
      return {
        totalTranscriptions: 1234,
        hoursProcessed: 842,
        entitiesFound: 5678,
        accuracyRate: 98.5
      };
    }
  }

  // Transcriptions
  async getTranscriptions(params = {}) {
    try {
      const queryString = new URLSearchParams(params).toString();
      const response = await this.request(`/transcription/list?${queryString}`);
      return response.data;
    } catch (error) {
      console.warn('Using mock data for transcriptions');
      return {
        items: [
          {
            id: 'sample-1',
            title: 'Product Team Meeting - Q1 Review',
            created_at: new Date().toISOString(),
            duration: 240,
            word_count: 5200
          }
        ],
        total: 1,
        page: 1,
        pageSize: 10
      };
    }
  }

  async uploadFile(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options.language) formData.append('language', options.language);
    if (options.speakerCount) formData.append('speaker_count', options.speakerCount);
    
    const response = await fetch(`${API_BASE_URL}/transcription/upload`, {
      method: 'POST',
      headers: {
        ...(this.token && { 'Authorization': `Bearer ${this.token}` })
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  }

  async processTranscription(fileId, options = {}) {
    const formData = new FormData();
    formData.append('file_id', fileId);
    formData.append('language', options.language || 'auto');
    formData.append('enable_diarization', options.enableDiarization || false);
    formData.append('extract_entities', options.extractEntities !== false);
    
    const response = await fetch(`${API_BASE_URL}/transcription/process`, {
      method: 'POST',
      headers: {
        ...(this.token && { 'Authorization': `Bearer ${this.token}` })
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Processing failed: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  }

  async generateInsights(transcriptId) {
    const formData = new FormData();
    formData.append('transcript_id', transcriptId);
    
    const response = await fetch(`${API_BASE_URL}/insights/generate`, {
      method: 'POST',
      headers: {
        ...(this.token && { 'Authorization': `Bearer ${this.token}` })
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Insights generation failed: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  }

  async transcribeFile(fileId, options = {}) {
    return await this.request(`/transcription/process`, {
      method: 'POST',
      body: JSON.stringify({
        file_id: fileId,
        use_api: false,
        language: options.language || 'auto',
        model: options.model || 'base',
        enable_diarization: options.enableDiarization || false,
        extract_entities: options.extractEntities !== false
      })
    });
  }

  async getTranscription(id) {
    try {
      return await this.request(`/transcription/status/${id}`);
    } catch (error) {
      // Return mock data for testing
      console.warn('Using mock data for transcription detail');
      return {
        data: {
          transcript_id: id,
          status: 'completed',
          result: {
            transcript_id: id,
            text: `Welcome everyone to our Q1 product review meeting. I'm Sarah Johnson, VP of Product, and I'll be leading today's discussion.

Let's start by reviewing our key achievements this quarter. Our team successfully launched the new dashboard feature, which has been adopted by 78% of our users within the first month. This exceeded our initial target of 60% adoption.

John Smith from the engineering team did an outstanding job leading the API refactoring project. The new architecture has improved response times by 40% and reduced server costs by 25%.

Moving on to our mobile app updates, we've seen great feedback from customers about the new user interface. The app store ratings have improved from 4.2 to 4.7 stars, and daily active users have increased by 35%.

For Q2, we need to focus on three main areas: improving our onboarding flow, implementing real-time collaboration features, and expanding our API capabilities for third-party integrations.

Let me hand it over to John to discuss the technical roadmap for these initiatives...`,
            language: 'en',
            duration: 240,
            word_count: 5200,
            confidence: 0.95,
            processing_time: 12.5,
            created_at: new Date().toISOString(),
            entities: [
              { text: "Q1", label: "DATE", start: 28, end: 30, confidence: 0.98 },
              { text: "Sarah Johnson", label: "PERSON", start: 54, end: 67, confidence: 0.99 },
              { text: "VP of Product", label: "TITLE", start: 69, end: 82, confidence: 0.95 },
              { text: "John Smith", label: "PERSON", start: 250, end: 260, confidence: 0.98 },
              { text: "Q2", label: "DATE", start: 550, end: 552, confidence: 0.98 }
            ],
            speakers: [
              {
                speaker_id: "SPEAKER_00",
                start_time: 0,
                end_time: 15,
                text: "Welcome everyone to our Q1 product review meeting. I'm Sarah Johnson, VP of Product, and I'll be leading today's discussion.",
                confidence: 0.95
              },
              {
                speaker_id: "SPEAKER_00",
                start_time: 15,
                end_time: 45,
                text: "Let's start by reviewing our key achievements this quarter. Our team successfully launched the new dashboard feature, which has been adopted by 78% of our users within the first month. This exceeded our initial target of 60% adoption.",
                confidence: 0.94
              },
              {
                speaker_id: "SPEAKER_01",
                start_time: 43,
                end_time: 48,
                text: "That's fantastic news, Sarah!",
                confidence: 0.92
              },
              {
                speaker_id: "SPEAKER_00",
                start_time: 48,
                end_time: 75,
                text: "Thank you, John. Speaking of achievements, John Smith from the engineering team did an outstanding job leading the API refactoring project. The new architecture has improved response times by 40% and reduced server costs by 25%.",
                confidence: 0.93
              },
              {
                speaker_id: "SPEAKER_01",
                start_time: 75,
                end_time: 95,
                text: "Thanks Sarah. The team worked really hard on this. We focused on optimizing the database queries and implementing better caching strategies.",
                confidence: 0.91
              },
              {
                speaker_id: "SPEAKER_00",
                start_time: 95,
                end_time: 120,
                text: "The mobile app updates have also been a success. We've seen great feedback from customers about the new user interface.",
                confidence: 0.94
              },
              {
                speaker_id: "SPEAKER_02",
                start_time: 118,
                end_time: 125,
                text: "The UI improvements are really impressive.",
                confidence: 0.90
              },
              {
                speaker_id: "SPEAKER_00",
                start_time: 125,
                end_time: 150,
                text: "Absolutely. The app store ratings have improved from 4.2 to 4.7 stars, and daily active users have increased by 35%.",
                confidence: 0.93
              },
              {
                speaker_id: "SPEAKER_02",
                start_time: 150,
                end_time: 170,
                text: "I'd like to highlight the accessibility features we added. They've made our app much more inclusive.",
                confidence: 0.91
              },
              {
                speaker_id: "SPEAKER_00",
                start_time: 170,
                end_time: 200,
                text: "That's a great point, Emily. For Q2, we need to focus on three main areas: improving our onboarding flow, implementing real-time collaboration features, and expanding our API capabilities.",
                confidence: 0.94
              },
              {
                speaker_id: "SPEAKER_01",
                start_time: 200,
                end_time: 220,
                text: "I have some ideas for the real-time collaboration. We could use WebSockets for instant updates.",
                confidence: 0.92
              },
              {
                speaker_id: "SPEAKER_02",
                start_time: 218,
                end_time: 225,
                text: "And we should consider offline support too.",
                confidence: 0.89
              },
              {
                speaker_id: "SPEAKER_00",
                start_time: 225,
                end_time: 240,
                text: "Excellent suggestions. Let's schedule a follow-up meeting to dive deeper into the technical implementation.",
                confidence: 0.93
              }
            ]
          }
        }
      };
    }
  }

  async deleteTranscription(id) {
    return await this.request(`/transcription/${id}`, {
      method: 'DELETE'
    });
  }

  // Search
  async search(query, filters = {}) {
    const params = {
      q: query,
      ...filters
    };
    
    const queryString = new URLSearchParams(params).toString();
    return await this.request(`/search?${queryString}`);
  }

  // Export
  async exportTranscription(id, format = 'pdf') {
    const response = await fetch(`${API_BASE_URL}/export/${id}?format=${format}`, {
      headers: {
        ...(this.token && { 'Authorization': `Bearer ${this.token}` })
      }
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status} ${response.statusText}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcription_${id}.${format}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }

  // Video Processing
  async uploadVideo(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/video/upload`, {
      method: 'POST',
      headers: {
        ...(this.token && { 'Authorization': `Bearer ${this.token}` })
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Video upload failed: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  }

  async analyzeVideo(fileId, options = {}) {
    return await this.request(`/video/analyze/${fileId}`, {
      method: 'POST',
      body: JSON.stringify({
        extract_frames: options.extractFrames !== false,
        detect_scenes: options.detectScenes !== false,
        generate_thumbnails: options.generateThumbnails !== false,
        keyframe_interval: options.keyframeInterval || 10.0,
        thumbnail_count: options.thumbnailCount || 5
      })
    });
  }

  async getVideoFrames(fileId, options = {}) {
    const params = new URLSearchParams();
    if (options.startTime) params.append('start_time', options.startTime);
    if (options.endTime) params.append('end_time', options.endTime);
    if (options.interval) params.append('interval', options.interval);
    
    return await this.request(`/video/frames/${fileId}?${params.toString()}`);
  }

  async getVideoScenes(fileId, minDuration = 1.0) {
    return await this.request(`/video/scenes/${fileId}?min_duration=${minDuration}`);
  }

  async getVideoThumbnails(fileId, count = 5) {
    return await this.request(`/video/thumbnails/${fileId}?count=${count}`);
  }

  // Batch Processing
  async processBatch(files, options = {}) {
    const formData = new FormData();
    
    // Add files
    files.forEach(file => {
      formData.append('files', file.file);
    });
    
    // Add options
    formData.append('language', options.language || 'auto');
    formData.append('model', options.model || 'base');
    formData.append('enable_diarization', options.enableDiarization || false);
    formData.append('extract_entities', options.extractEntities !== false);
    
    const response = await fetch(`${API_BASE_URL}/transcription/batch`, {
      method: 'POST',
      headers: {
        ...(this.token && { 'Authorization': `Bearer ${this.token}` })
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Batch processing failed: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  }

  async getBatchStatus(batchId) {
    return await this.request(`/transcription/batch/${batchId}/status`);
  }

  // Advanced Analytics
  async getAdvancedAnalytics() {
    try {
      const response = await this.request('/analytics/advanced');
      return response.data;
    } catch (error) {
      console.warn('Using mock data for advanced analytics');
      return {
        usage: {
          daily_uploads: [30, 45, 52, 38, 61, 49, 55],
          weekly_growth: 8.5,
          peak_hours: [9, 10, 14, 15, 16],
          top_formats: [
            { format: "WAV", count: 120, percentage: 40 },
            { format: "MP3", count: 90, percentage: 30 },
            { format: "MP4", count: 90, percentage: 30 }
          ]
        },
        performance: {
          avg_processing_time: 25.0,
          accuracy_by_format: { "WAV": 98.5, "MP3": 96.2, "MP4": 94.8 },
          error_rate: 1.8,
          success_rate: 98.2
        }
      };
    }
  }

  // Health Check
  async checkHealth() {
    try {
      const response = await fetch('http://localhost:8000/health');
      return await response.json();
    } catch (error) {
      return { status: 'error', message: error.message };
    }
  }
}

export default new ApiService();