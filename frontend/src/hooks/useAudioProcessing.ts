import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface ProcessingOptions {
  enhance?: boolean;
  transcribe?: boolean;
  extractEntities?: boolean;
  generateSummary?: boolean;
  detectSpeakers?: boolean;
}

interface ProcessingResult {
  transcription?: string;
  entities?: Record<string, any[]>;
  sentiment?: any;
  keywords?: string[];
  summary?: string;
  speakers?: any[];
  confidence?: number;
  duration?: number;
}

export const useAudioProcessing = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const processAudio = useCallback(async (
    file: File,
    options: ProcessingOptions
  ): Promise<ProcessingResult> => {
    setIsProcessing(true);
    setProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    Object.entries(options).forEach(([key, value]) => {
      formData.append(key, String(value));
    });

    try {
      const response = await axios.post(
        `${API_BASE_URL}/audio/process`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              setProgress(percentCompleted);
            }
          },
        }
      );

      setIsProcessing(false);
      setProgress(100);
      return response.data;
    } catch (err: any) {
      setError(err.message || 'Processing failed');
      setIsProcessing(false);
      throw err;
    }
  }, []);

  const cancelProcessing = useCallback(() => {
    // Implement cancellation logic
    setIsProcessing(false);
    setProgress(0);
  }, []);

  return {
    processAudio,
    cancelProcessing,
    isProcessing,
    progress,
    error,
  };
};

// WebSocket Hook
export const useWebSocket = (endpoint: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [data, setData] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}${endpoint}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        setData(parsedData);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (event) => {
      setError('WebSocket error occurred');
      console.error('WebSocket error:', event);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [endpoint]);

  const send = useCallback((message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    }
  }, [socket]);

  return {
    data,
    send,
    isConnected,
    error,
  };
};

// Analytics Hook
export const useAnalytics = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_BASE_URL}/analytics/metrics`);
      setMetrics(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  const refetch = useCallback(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  return {
    metrics,
    loading,
    error,
    refetch,
  };
};

// Collaboration Hook
interface Collaborator {
  id: string;
  name: string;
  avatar?: string;
  isActive: boolean;
}

interface Annotation {
  id: string;
  segmentId: string;
  type: 'comment' | 'highlight' | 'action' | 'insight';
  text: string;
  author: string;
  timestamp: Date;
}

export const useCollaboration = (transcriptId: string) => {
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const { data, send } = useWebSocket(`/ws/collaboration/${transcriptId}`);

  useEffect(() => {
    if (data) {
      if (data.type === 'collaborators') {
        setCollaborators(data.collaborators);
      } else if (data.type === 'annotation') {
        setAnnotations(prev => [...prev, data.annotation]);
      }
    }
  }, [data]);

  const addAnnotation = useCallback((annotation: Omit<Annotation, 'id'>) => {
    const newAnnotation = {
      ...annotation,
      id: `annotation-${Date.now()}`,
    };
    
    send({
      type: 'add_annotation',
      annotation: newAnnotation,
    });

    setAnnotations(prev => [...prev, newAnnotation]);
  }, [send]);

  const updateAnnotation = useCallback((id: string, updates: Partial<Annotation>) => {
    send({
      type: 'update_annotation',
      id,
      updates,
    });

    setAnnotations(prev =>
      prev.map(ann => (ann.id === id ? { ...ann, ...updates } : ann))
    );
  }, [send]);

  const deleteAnnotation = useCallback((id: string) => {
    send({
      type: 'delete_annotation',
      id,
    });

    setAnnotations(prev => prev.filter(ann => ann.id !== id));
  }, [send]);

  return {
    collaborators,
    annotations,
    addAnnotation,
    updateAnnotation,
    deleteAnnotation,
  };
};

// Theme Hook
export const useEnterpriseTheme = () => {
  const [themeMode, setThemeMode] = useState<'light' | 'dark'>('light');
  const [brandConfig, setBrandConfig] = useState<any>(null);

  useEffect(() => {
    const savedTheme = localStorage.getItem('themeMode');
    if (savedTheme) {
      setThemeMode(savedTheme as 'light' | 'dark');
    }
  }, []);

  const toggleTheme = useCallback(() => {
    const newMode = themeMode === 'light' ? 'dark' : 'light';
    setThemeMode(newMode);
    localStorage.setItem('themeMode', newMode);
  }, [themeMode]);

  const updateBrandConfig = useCallback((config: any) => {
    setBrandConfig(config);
    localStorage.setItem('brandConfig', JSON.stringify(config));
  }, []);

  return {
    themeMode,
    toggleTheme,
    brandConfig,
    updateBrandConfig,
  };
};

// File Management Hook
export const useFileManagement = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});

  const uploadFile = useCallback(async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/files/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              setUploadProgress(prev => ({
                ...prev,
                [file.name]: percentCompleted,
              }));
            }
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error('Upload failed:', error);
      throw error;
    }
  }, []);

  const deleteFile = useCallback((fileId: string) => {
    // Implement file deletion
  }, []);

  return {
    files,
    uploadFile,
    deleteFile,
    uploadProgress,
  };
};
