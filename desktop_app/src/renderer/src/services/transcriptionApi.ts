// API service to connect React frontend to Python backend
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
  speakers?: Array<{
    speaker: string;
    segments: Array<{
      start: number;
      end: number;
      text: string;
    }>;
  }>;
  segments?: Array<{
    start: number;
    end: number;
    text: string;
    confidence: number;
  }>;
}

export interface ProcessingStatus {
  id: string;
  status: 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  result?: TranscriptionResult;
  error?: string;
}

class TranscriptionAPI {
  private baseUrl = 'http://localhost:8001';
  
  async uploadAndTranscribe(request: TranscriptionRequest): Promise<string> {
    const formData = new FormData();
    formData.append('file', request.file);
    
    if (request.language) {
      formData.append('language', request.language);
    }
    
    if (request.detectCodeSwitching) {
      formData.append('detect_code_switching', 'true');
    }

    const response = await fetch(`${this.baseUrl}/api/transcription/upload`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Transcription failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result.data.file_id; // Return file ID for transcription
  }

  async getProcessingStatus(id: string): Promise<ProcessingStatus> {
    const response = await fetch(`${this.baseUrl}/api/transcription/status/${id}`);
    
    if (!response.ok) {
      throw new Error(`Failed to get status: ${response.statusText}`);
    }

    const result = await response.json();
    return result.data;
  }

  async getTranscriptionResult(id: string): Promise<TranscriptionResult> {
    const response = await fetch(`${this.baseUrl}/api/transcription/result/${id}`);
    
    if (!response.ok) {
      throw new Error(`Failed to get result: ${response.statusText}`);
    }

    const result = await response.json();
    return result.data;
  }

  async getSupportedLanguages(): Promise<Array<{
    code: string;
    name: string;
    has_ner: boolean;
    is_rtl: boolean;
  }>> {
    const response = await fetch(`${this.baseUrl}/api/transcription/languages`);
    
    if (!response.ok) {
      throw new Error(`Failed to get languages: ${response.statusText}`);
    }

    const result = await response.json();
    return result.data;
  }

  // Real transcription using the established API service
  async transcribeFile(request: TranscriptionRequest): Promise<TranscriptionResult> {
    // Import at top level instead of inside function
    const { apiService } = await import('./api');
    
    try {
      // Call the real transcription API that stores results and shows real data
      const result = await apiService.transcribeFile(request);
      
      // Convert the API result format to match TranscriptionResult interface
      return {
        id: result.id,
        text: result.text,
        language: result.language,
        confidence: result.confidence,
        duration: result.duration,
        entities: result.entities,
        segments: result.segments
      };
    } catch (error) {
      throw new Error(`Transcription failed: ${(error as Error).message}`);
    }
  }
}

export const transcriptionAPI = new TranscriptionAPI();