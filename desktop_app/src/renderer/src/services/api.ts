// Real API service that connects to actual backend
export interface DashboardStats {
  totalTranscriptions: number;
  hoursProcessed: number;
  entitiesFound: number;
  accuracyRate: number;
}

export interface TranscriptionItem {
  id: string;
  title: string;
  duration: number;
  status: 'completed' | 'processing' | 'failed';
  accuracy: number;
  createdAt: string;
  entities: string[];
  language: string;
}

export interface TranscriptionRequest {
  file: File;
  language?: string;
  detectCodeSwitching?: boolean;
  method?: 'basic' | 'advanced' | 'multilingual' | 'whisperx';
}

export interface TranscriptionResult {
  id: string;
  text: string;
  language: string;
  confidence: number;
  duration: number;
  entities: {
    [type: string]: string[];
  };
  segments: Array<{
    start: number;
    end: number;
    text: string;
    confidence: number;
  }>;
  created_at: string;
}

class ApiService {
  private baseUrl: string;
  
  constructor() {
    // Connect to the FastAPI backend that has real REST endpoints
    this.baseUrl = 'http://localhost:8000'; // Our FastAPI backend
  }

  // Check if backend is healthy
  async checkHealth(): Promise<{ status: 'healthy' | 'error'; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`);
      if (response.ok) {
        return { status: 'healthy', message: 'FastAPI backend connected' };
      } else {
        return { status: 'error', message: 'FastAPI backend not responding' };
      }
    } catch (error) {
      return { status: 'error', message: (error as Error).message };
    }
  }

  // Get real dashboard statistics
  async getDashboardStats(): Promise<DashboardStats> {
    try {
      // Since Streamlit doesn't have REST endpoints, we'll use localStorage as a simple database
      // In a real app, this would be a proper database call
      const transcriptions = this.getStoredTranscriptions();
      
      const stats: DashboardStats = {
        totalTranscriptions: transcriptions.length,
        hoursProcessed: transcriptions.reduce((total, t) => total + t.duration, 0) / 3600,
        entitiesFound: transcriptions.reduce((total, t) => total + t.entities.length, 0),
        accuracyRate: transcriptions.length > 0 
          ? transcriptions.reduce((total, t) => total + t.accuracy, 0) / transcriptions.length 
          : 0
      };

      return stats;
    } catch (error) {
      console.error('Failed to get stats:', error);
      // Return empty stats instead of dummy data
      return {
        totalTranscriptions: 0,
        hoursProcessed: 0,
        entitiesFound: 0,
        accuracyRate: 0
      };
    }
  }

  // Get recent transcriptions from storage
  async getRecentTranscriptions(): Promise<TranscriptionItem[]> {
    const transcriptions = this.getStoredTranscriptions();
    return transcriptions
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      .slice(0, 5); // Return last 5
  }

  // Process a file for transcription using FastAPI
  async transcribeFile(request: TranscriptionRequest): Promise<TranscriptionResult> {
    try {
      // Step 1: Upload file to FastAPI
      const formData = new FormData();
      formData.append('file', request.file);
      
      const uploadResponse = await fetch(`${this.baseUrl}/api/transcription/upload`, {
        method: 'POST',
        body: formData
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.statusText}`);
      }

      const uploadResult = await uploadResponse.json();
      const fileId = uploadResult.data.file_id;

      // Step 2: Start transcription process
      // Map frontend method to backend model
      const modelMap = {
        'basic': 'base',
        'advanced': 'medium',
        'multilingual': 'large',
        'whisperx': 'large'
      };
      
      const transcribeData = {
        use_api: false,
        language: request.language || 'auto',
        model: modelMap[request.method || 'basic'] || 'base',
        enable_diarization: request.method === 'whisperx',
        extract_entities: true
      };

      const transcribeResponse = await fetch(`${this.baseUrl}/api/transcription/process?file_id=${fileId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(transcribeData)
      });

      if (!transcribeResponse.ok) {
        throw new Error(`Transcription failed: ${transcribeResponse.statusText}`);
      }

      const transcriptionResult = await transcribeResponse.json();
      
      // Store the result for dashboard
      this.storeTranscription(transcriptionResult.data);
      
      return transcriptionResult.data;
    } catch (error) {
      throw new Error(`Transcription failed: ${(error as Error).message}`);
    }
  }

  // Helper methods for local storage (simulating database)
  private getStoredTranscriptions(): TranscriptionItem[] {
    const stored = localStorage.getItem('transcriptions');
    return stored ? JSON.parse(stored) : [];
  }

  private storeTranscription(result: TranscriptionResult): void {
    const transcriptions = this.getStoredTranscriptions();
    const newItem: TranscriptionItem = {
      id: result.id,
      title: `Transcription ${transcriptions.length + 1}`,
      duration: result.duration,
      status: 'completed',
      accuracy: result.confidence,
      createdAt: result.created_at,
      entities: Object.values(result.entities).flat(),
      language: result.language
    };
    
    transcriptions.push(newItem);
    localStorage.setItem('transcriptions', JSON.stringify(transcriptions));
  }

  private async simulateProcessing(): Promise<void> {
    // Simulate realistic processing time
    const processingTime = 2000 + Math.random() * 3000; // 2-5 seconds
    await new Promise(resolve => setTimeout(resolve, processingTime));
  }

  // HTTP methods for compatibility with existing code
  async get(url: string, options?: RequestInit): Promise<any> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      ...options,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  async post(url: string, data?: any, options?: RequestInit): Promise<any> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      ...options,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  async put(url: string, data?: any, options?: RequestInit): Promise<any> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      ...options,
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  async delete(url: string, options?: RequestInit): Promise<any> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      ...options,
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  async patch(url: string, data?: any, options?: RequestInit): Promise<any> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      ...options,
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }
}

export const apiService = new ApiService();
export const api = apiService; // Alias for compatibility