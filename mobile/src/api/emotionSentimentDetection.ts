import { ApiResponse } from './types';

export interface EmotionResult {
  timestamp: number;
  duration: number;
  primary_emotion: string;
  emotion_scores: Record<string, number>;
  confidence: number;
  intensity: number;
  speaker_id?: string;
  audio_features?: Record<string, number>;
  text_content?: string;
}

export interface SentimentResult {
  timestamp: number;
  duration: number;
  polarity: string;
  sentiment_score: number;
  confidence: number;
  subjectivity: number;
  speaker_id?: string;
  text_content?: string;
  keywords: string[];
}

export interface EmotionSentimentAnalysisResult {
  emotions: EmotionResult[];
  sentiments: SentimentResult[];
  overall_emotion: string;
  overall_sentiment: string;
  emotion_timeline: any[];
  sentiment_timeline: any[];
  statistics: Record<string, any>;
  processing_time: number;
  total_duration: number;
  config_used: any;
}

export interface EmotionConfig {
  detection_mode: string;
  model_type: string;
  language: string;
  confidence_threshold: number;
  enable_audio_analysis: boolean;
  enable_text_analysis: boolean;
  enable_temporal_analysis: boolean;
  segment_duration: number;
  overlap_duration: number;
  enable_speaker_emotion: boolean;
}

export interface ModelsResponse {
  emotion_models: Array<{
    value: string;
    label: string;
    description: string;
    emotions: string[];
  }>;
  sentiment_models: Array<{
    value: string;
    label: string;
    description: string;
    polarities: string[];
  }>;
  detection_modes: Array<{
    value: string;
    label: string;
    description: string;
  }>;
  supported_languages: Array<{
    code: string;
    name: string;
  }>;
}

class EmotionSentimentDetectionAPI {
  private baseUrl = '/api/v1/emotion-sentiment';

  /**
   * Analyze emotion and sentiment from audio file
   */
  async analyzeAudioFile(
    audioFile: {
      uri: string;
      type: string;
      name: string;
    },
    config: EmotionConfig,
    transcriptText?: string,
    includeTimeline: boolean = true,
    includeStatistics: boolean = true
  ): Promise<ApiResponse<EmotionSentimentAnalysisResult>> {
    const formData = new FormData();
    
    formData.append('audio_file', {
      uri: audioFile.uri,
      type: audioFile.type,
      name: audioFile.name,
    } as any);
    
    formData.append('config', JSON.stringify(config));
    
    if (transcriptText) {
      formData.append('transcript_text', transcriptText);
    }
    
    formData.append('include_timeline', includeTimeline.toString());
    formData.append('include_statistics', includeStatistics.toString());

    const response = await fetch(`${this.baseUrl}/analyze`, {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to analyze emotion and sentiment');
    }

    return response.json();
  }

  /**
   * Analyze sentiment from text only
   */
  async analyzeTextSentiment(
    text: string,
    language: string = 'en',
    modelType: string = 'transformer'
  ): Promise<ApiResponse<SentimentResult[]>> {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('language', language);
    formData.append('model_type', modelType);

    const response = await fetch(`${this.baseUrl}/analyze-text`, {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to analyze text sentiment');
    }

    return response.json();
  }

  /**
   * Get available models and configurations
   */
  async getAvailableModels(): Promise<ApiResponse<ModelsResponse>> {
    const response = await fetch(`${this.baseUrl}/models`);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch available models');
    }

    return response.json();
  }

  /**
   * Health check for the emotion/sentiment detection service
   */
  async healthCheck(): Promise<ApiResponse<{
    status: string;
    components: Record<string, string>;
    supported_models: number;
    supported_languages: number;
  }>> {
    const response = await fetch(`${this.baseUrl}/health`);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Health check failed');
    }

    return response.json();
  }

  /**
   * Create default emotion configuration
   */
  createDefaultConfig(): EmotionConfig {
    return {
      detection_mode: 'both',
      model_type: 'transformer',
      language: 'en',
      confidence_threshold: 0.5,
      enable_audio_analysis: true,
      enable_text_analysis: true,
      enable_temporal_analysis: true,
      segment_duration: 2.0,
      overlap_duration: 0.5,
      enable_speaker_emotion: true
    };
  }

  /**
   * Validate emotion configuration
   */
  validateConfig(config: EmotionConfig): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!['emotion', 'sentiment', 'both'].includes(config.detection_mode)) {
      errors.push('Invalid detection mode');
    }

    if (!['transformer', 'cnn', 'svm'].includes(config.model_type)) {
      errors.push('Invalid model type');
    }

    if (config.confidence_threshold < 0 || config.confidence_threshold > 1) {
      errors.push('Confidence threshold must be between 0 and 1');
    }

    if (config.segment_duration < 0.5 || config.segment_duration > 10) {
      errors.push('Segment duration must be between 0.5 and 10 seconds');
    }

    if (config.overlap_duration < 0 || config.overlap_duration > 2) {
      errors.push('Overlap duration must be between 0 and 2 seconds');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Format emotion results for display
   */
  formatEmotionResult(emotion: EmotionResult): {
    displayText: string;
    timeRange: string;
    confidenceText: string;
    intensityText: string;
  } {
    const timeRange = `${this.formatTime(emotion.timestamp)} - ${this.formatTime(emotion.timestamp + emotion.duration)}`;
    const confidenceText = `${(emotion.confidence * 100).toFixed(1)}%`;
    const intensityText = `${(emotion.intensity * 100).toFixed(1)}%`;
    
    return {
      displayText: emotion.primary_emotion.charAt(0).toUpperCase() + emotion.primary_emotion.slice(1),
      timeRange,
      confidenceText,
      intensityText
    };
  }

  /**
   * Format sentiment results for display
   */
  formatSentimentResult(sentiment: SentimentResult): {
    displayText: string;
    timeRange: string;
    scoreText: string;
    confidenceText: string;
    subjectivityText: string;
  } {
    const timeRange = `${this.formatTime(sentiment.timestamp)} - ${this.formatTime(sentiment.timestamp + sentiment.duration)}`;
    const scoreText = sentiment.sentiment_score.toFixed(2);
    const confidenceText = `${(sentiment.confidence * 100).toFixed(1)}%`;
    const subjectivityText = `${(sentiment.subjectivity * 100).toFixed(1)}%`;
    
    return {
      displayText: sentiment.polarity.charAt(0).toUpperCase() + sentiment.polarity.slice(1),
      timeRange,
      scoreText,
      confidenceText,
      subjectivityText
    };
  }

  /**
   * Format time in seconds to MM:SS format
   */
  private formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  /**
   * Get emotion color for UI display
   */
  getEmotionColor(emotion: string): string {
    switch (emotion.toLowerCase()) {
      case 'joy':
      case 'happy':
        return '#FCD34D';
      case 'sadness':
      case 'sad':
        return '#60A5FA';
      case 'anger':
      case 'angry':
        return '#F87171';
      case 'fear':
      case 'fearful':
        return '#A78BFA';
      case 'surprise':
      case 'surprised':
        return '#FB923C';
      case 'disgust':
      case 'disgusted':
        return '#34D399';
      default:
        return '#9CA3AF';
    }
  }

  /**
   * Get sentiment color for UI display
   */
  getSentimentColor(polarity: string): string {
    switch (polarity.toLowerCase()) {
      case 'positive':
        return '#10B981';
      case 'negative':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  }

  /**
   * Export analysis results to various formats
   */
  exportResults(
    result: EmotionSentimentAnalysisResult,
    format: 'json' | 'csv' | 'txt' = 'json'
  ): string {
    switch (format) {
      case 'json':
        return JSON.stringify(result, null, 2);
      
      case 'csv':
        let csv = 'Type,Timestamp,Duration,Value,Confidence,Additional\n';
        
        result.emotions.forEach(emotion => {
          csv += `Emotion,${emotion.timestamp},${emotion.duration},${emotion.primary_emotion},${emotion.confidence},${emotion.intensity}\n`;
        });
        
        result.sentiments.forEach(sentiment => {
          csv += `Sentiment,${sentiment.timestamp},${sentiment.duration},${sentiment.polarity},${sentiment.confidence},${sentiment.sentiment_score}\n`;
        });
        
        return csv;
      
      case 'txt':
        let txt = 'Emotion and Sentiment Analysis Results\n';
        txt += '=====================================\n\n';
        txt += `Overall Emotion: ${result.overall_emotion}\n`;
        txt += `Overall Sentiment: ${result.overall_sentiment}\n`;
        txt += `Processing Time: ${result.processing_time.toFixed(2)}s\n`;
        txt += `Total Duration: ${result.total_duration.toFixed(1)}s\n\n`;
        
        txt += 'Emotions:\n';
        result.emotions.forEach((emotion, index) => {
          txt += `${index + 1}. ${emotion.primary_emotion} (${this.formatTime(emotion.timestamp)} - ${this.formatTime(emotion.timestamp + emotion.duration)}) - Confidence: ${(emotion.confidence * 100).toFixed(1)}%\n`;
        });
        
        txt += '\nSentiments:\n';
        result.sentiments.forEach((sentiment, index) => {
          txt += `${index + 1}. ${sentiment.polarity} (${this.formatTime(sentiment.timestamp)} - ${this.formatTime(sentiment.timestamp + sentiment.duration)}) - Score: ${sentiment.sentiment_score.toFixed(2)}\n`;
        });
        
        return txt;
      
      default:
        return JSON.stringify(result, null, 2);
    }
  }
}

export const emotionSentimentDetectionAPI = new EmotionSentimentDetectionAPI();