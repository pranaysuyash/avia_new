import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Separator } from '../ui/separator';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Upload, 
  Play, 
  Pause,
  Heart,
  Smile,
  Frown,
  Meh,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Download,
  RefreshCw,
  Zap,
  Brain,
  MessageCircle,
  Volume2,
  FileText,
  Settings,
  Activity
} from 'lucide-react';

interface EmotionResult {
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

interface SentimentResult {
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

interface AnalysisResult {
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

interface EmotionConfig {
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

const EmotionSentimentDetection: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [transcriptText, setTranscriptText] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<any>(null);
  
  // Configuration state
  const [config, setConfig] = useState<EmotionConfig>({
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
  });
  
  // Audio playback
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Text analysis
  const [textInput, setTextInput] = useState('');
  const [textSentiments, setTextSentiments] = useState<SentimentResult[]>([]);

  // Load available models on component mount
  useEffect(() => {
    loadModels();
  }, []);

  // Audio playback time update
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration);

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', () => setIsPlaying(false));

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', () => setIsPlaying(false));
    };
  }, [selectedFile]);

  const loadModels = async () => {
    try {
      const response = await fetch('/api/v1/emotion-sentiment/models');
      if (response.ok) {
        const data = await response.json();
        setModels(data.data);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select an audio file');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('audio_file', selectedFile);
      formData.append('config', JSON.stringify(config));
      
      if (transcriptText) {
        formData.append('transcript_text', transcriptText);
      }
      
      formData.append('include_timeline', 'true');
      formData.append('include_statistics', 'true');

      const response = await fetch('/api/v1/emotion-sentiment/analyze', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze emotion and sentiment');
      }

      const data = await response.json();
      setResult(data.data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const analyzeTextSentiment = async () => {
    if (!textInput.trim()) {
      setError('Please enter text to analyze');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('text', textInput);
      formData.append('language', config.language);
      formData.append('model_type', config.model_type);

      const response = await fetch('/api/v1/emotion-sentiment/analyze-text', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze text sentiment');
      }

      const data = await response.json();
      setTextSentiments(data.data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    }
  };

  const togglePlayback = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getEmotionIcon = (emotion: string) => {
    switch (emotion.toLowerCase()) {
      case 'joy':
      case 'happy':
      case 'positive':
        return <Smile className="w-4 h-4" />;
      case 'sadness':
      case 'sad':
      case 'negative':
        return <Frown className="w-4 h-4" />;
      case 'anger':
      case 'angry':
        return <Zap className="w-4 h-4 text-red-500" />;
      case 'fear':
      case 'fearful':
        return <Heart className="w-4 h-4 text-purple-500" />;
      default:
        return <Meh className="w-4 h-4" />;
    }
  };

  const getSentimentIcon = (polarity: string) => {
    switch (polarity.toLowerCase()) {
      case 'positive':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'negative':
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <Meh className="w-4 h-4 text-gray-500" />;
    }
  };

  const getEmotionColor = (emotion: string) => {
    switch (emotion.toLowerCase()) {
      case 'joy':
      case 'happy':
        return 'bg-yellow-100 text-yellow-800';
      case 'sadness':
      case 'sad':
        return 'bg-blue-100 text-blue-800';
      case 'anger':
      case 'angry':
        return 'bg-red-100 text-red-800';
      case 'fear':
      case 'fearful':
        return 'bg-purple-100 text-purple-800';
      case 'surprise':
      case 'surprised':
        return 'bg-orange-100 text-orange-800';
      case 'disgust':
      case 'disgusted':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSentimentColor = (polarity: string) => {
    switch (polarity.toLowerCase()) {
      case 'positive':
        return 'bg-green-100 text-green-800';
      case 'negative':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Emotion & Sentiment Detection
        </h1>
        <p className="text-gray-600">
          Analyze emotions from voice characteristics and sentiment from text content
        </p>
      </div>

      <Tabs defaultValue="audio-analysis" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="audio-analysis">
            <Volume2 className="w-4 h-4 mr-2" />
            Audio Analysis
          </TabsTrigger>
          <TabsTrigger value="text-analysis">
            <FileText className="w-4 h-4 mr-2" />
            Text Analysis
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="audio-analysis" className="space-y-6">
          {/* File Upload */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Audio File Upload
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="audio-file">Select Audio File</Label>
                <Input
                  id="audio-file"
                  type="file"
                  accept="audio/*"
                  onChange={handleFileSelect}
                  ref={fileInputRef}
                  className="mt-1"
                />
              </div>

              {selectedFile && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-sm text-gray-500">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={togglePlayback}
                      disabled={!selectedFile}
                    >
                      {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </Button>
                  </div>

                  <audio
                    ref={audioRef}
                    src={selectedFile ? URL.createObjectURL(selectedFile) : undefined}
                    className="hidden"
                  />

                  {duration > 0 && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm text-gray-500">
                        <span>{formatTime(currentTime)}</span>
                        <span>{formatTime(duration)}</span>
                      </div>
                      <Progress value={(currentTime / duration) * 100} className="w-full" />
                    </div>
                  )}
                </div>
              )}

              <div>
                <Label htmlFor="transcript">Optional Transcript (for enhanced analysis)</Label>
                <textarea
                  id="transcript"
                  value={transcriptText}
                  onChange={(e) => setTranscriptText(e.target.value)}
                  placeholder="Paste transcript text here for more accurate sentiment analysis..."
                  className="w-full mt-1 p-3 border border-gray-300 rounded-md resize-none"
                  rows={4}
                />
              </div>

              <Button
                onClick={handleAnalyze}
                disabled={!selectedFile || isAnalyzing}
                className="w-full"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Brain className="w-4 h-4 mr-2" />
                    Analyze Emotion & Sentiment
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Results */}
          {result && (
            <div className="space-y-6">
              {/* Overall Results */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    Overall Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <h3 className="font-semibold text-lg">Primary Emotion</h3>
                      <div className="flex items-center gap-3">
                        {getEmotionIcon(result.overall_emotion)}
                        <Badge className={getEmotionColor(result.overall_emotion)}>
                          {result.overall_emotion}
                        </Badge>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <h3 className="font-semibold text-lg">Overall Sentiment</h3>
                      <div className="flex items-center gap-3">
                        {getSentimentIcon(result.overall_sentiment)}
                        <Badge className={getSentimentColor(result.overall_sentiment)}>
                          {result.overall_sentiment}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <Separator className="my-4" />

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-blue-600">{result.emotions.length}</p>
                      <p className="text-sm text-gray-500">Emotion Segments</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-green-600">{result.sentiments.length}</p>
                      <p className="text-sm text-gray-500">Sentiment Segments</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-purple-600">
                        {result.processing_time.toFixed(2)}s
                      </p>
                      <p className="text-sm text-gray-500">Processing Time</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-orange-600">
                        {result.total_duration.toFixed(1)}s
                      </p>
                      <p className="text-sm text-gray-500">Audio Duration</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Detailed Results */}
              <Tabs defaultValue="emotions" className="w-full">
                <TabsList>
                  <TabsTrigger value="emotions">Emotions</TabsTrigger>
                  <TabsTrigger value="sentiments">Sentiments</TabsTrigger>
                  <TabsTrigger value="timeline">Timeline</TabsTrigger>
                  <TabsTrigger value="statistics">Statistics</TabsTrigger>
                </TabsList>

                <TabsContent value="emotions" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Emotion Analysis Results</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {result.emotions.map((emotion, index) => (
                          <div key={index} className="p-4 border rounded-lg">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-3">
                                {getEmotionIcon(emotion.primary_emotion)}
                                <Badge className={getEmotionColor(emotion.primary_emotion)}>
                                  {emotion.primary_emotion}
                                </Badge>
                                <span className="text-sm text-gray-500">
                                  {formatTime(emotion.timestamp)} - {formatTime(emotion.timestamp + emotion.duration)}
                                </span>
                              </div>
                              <div className="text-right">
                                <p className="text-sm font-medium">
                                  Confidence: {(emotion.confidence * 100).toFixed(1)}%
                                </p>
                                <p className="text-sm text-gray-500">
                                  Intensity: {(emotion.intensity * 100).toFixed(1)}%
                                </p>
                              </div>
                            </div>
                            
                            <div className="space-y-2">
                              <p className="text-sm font-medium">Emotion Scores:</p>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                {Object.entries(emotion.emotion_scores).map(([emotionType, score]) => (
                                  <div key={emotionType} className="text-center">
                                    <p className="text-xs text-gray-500 capitalize">{emotionType}</p>
                                    <Progress value={score * 100} className="h-2" />
                                    <p className="text-xs font-medium">{(score * 100).toFixed(1)}%</p>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {emotion.text_content && (
                              <div className="mt-3 p-2 bg-gray-50 rounded">
                                <p className="text-sm text-gray-700">{emotion.text_content}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="sentiments" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Sentiment Analysis Results</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {result.sentiments.map((sentiment, index) => (
                          <div key={index} className="p-4 border rounded-lg">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-3">
                                {getSentimentIcon(sentiment.polarity)}
                                <Badge className={getSentimentColor(sentiment.polarity)}>
                                  {sentiment.polarity}
                                </Badge>
                                <span className="text-sm text-gray-500">
                                  {formatTime(sentiment.timestamp)} - {formatTime(sentiment.timestamp + sentiment.duration)}
                                </span>
                              </div>
                              <div className="text-right">
                                <p className="text-sm font-medium">
                                  Score: {sentiment.sentiment_score.toFixed(2)}
                                </p>
                                <p className="text-sm text-gray-500">
                                  Confidence: {(sentiment.confidence * 100).toFixed(1)}%
                                </p>
                              </div>
                            </div>

                            <div className="space-y-2">
                              <div className="flex items-center gap-4">
                                <div className="flex-1">
                                  <p className="text-sm text-gray-500">Sentiment Score</p>
                                  <Progress 
                                    value={((sentiment.sentiment_score + 1) / 2) * 100} 
                                    className="h-2"
                                  />
                                </div>
                                <div className="flex-1">
                                  <p className="text-sm text-gray-500">Subjectivity</p>
                                  <Progress value={sentiment.subjectivity * 100} className="h-2" />
                                </div>
                              </div>
                            </div>

                            {sentiment.keywords.length > 0 && (
                              <div className="mt-3">
                                <p className="text-sm font-medium mb-2">Keywords:</p>
                                <div className="flex flex-wrap gap-1">
                                  {sentiment.keywords.map((keyword, idx) => (
                                    <Badge key={idx} variant="outline" className="text-xs">
                                      {keyword}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {sentiment.text_content && (
                              <div className="mt-3 p-2 bg-gray-50 rounded">
                                <p className="text-sm text-gray-700">{sentiment.text_content}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="timeline" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Emotional Timeline</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                          <p className="text-gray-500">Timeline visualization would be rendered here</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="statistics" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Analysis Statistics</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {Object.entries(result.statistics).map(([key, value]) => (
                          <div key={key} className="p-4 bg-gray-50 rounded-lg">
                            <p className="font-medium capitalize">{key.replace(/_/g, ' ')}</p>
                            <p className="text-2xl font-bold text-blue-600">
                              {typeof value === 'number' ? value.toFixed(2) : String(value)}
                            </p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </TabsContent>

        <TabsContent value="text-analysis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageCircle className="w-5 h-5" />
                Text Sentiment Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="text-input">Enter Text to Analyze</Label>
                <textarea
                  id="text-input"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Enter text for sentiment analysis..."
                  className="w-full mt-1 p-3 border border-gray-300 rounded-md resize-none"
                  rows={6}
                />
              </div>

              <Button
                onClick={analyzeTextSentiment}
                disabled={!textInput.trim()}
                className="w-full"
              >
                <Brain className="w-4 h-4 mr-2" />
                Analyze Text Sentiment
              </Button>

              {textSentiments.length > 0 && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-lg">Text Sentiment Results</h3>
                  {textSentiments.map((sentiment, index) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          {getSentimentIcon(sentiment.polarity)}
                          <Badge className={getSentimentColor(sentiment.polarity)}>
                            {sentiment.polarity}
                          </Badge>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium">
                            Score: {sentiment.sentiment_score.toFixed(2)}
                          </p>
                          <p className="text-sm text-gray-500">
                            Confidence: {(sentiment.confidence * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center gap-4">
                          <div className="flex-1">
                            <p className="text-sm text-gray-500">Sentiment Score</p>
                            <Progress 
                              value={((sentiment.sentiment_score + 1) / 2) * 100} 
                              className="h-2"
                            />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm text-gray-500">Subjectivity</p>
                            <Progress value={sentiment.subjectivity * 100} className="h-2" />
                          </div>
                        </div>
                      </div>

                      {sentiment.keywords.length > 0 && (
                        <div className="mt-3">
                          <p className="text-sm font-medium mb-2">Keywords:</p>
                          <div className="flex flex-wrap gap-1">
                            {sentiment.keywords.map((keyword, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {keyword}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Analysis Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="detection-mode">Detection Mode</Label>
                    <Select
                      value={config.detection_mode}
                      onValueChange={(value) => setConfig({...config, detection_mode: value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="emotion">Emotion Only</SelectItem>
                        <SelectItem value="sentiment">Sentiment Only</SelectItem>
                        <SelectItem value="both">Both</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="model-type">Model Type</Label>
                    <Select
                      value={config.model_type}
                      onValueChange={(value) => setConfig({...config, model_type: value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="transformer">Transformer</SelectItem>
                        <SelectItem value="cnn">CNN</SelectItem>
                        <SelectItem value="svm">SVM</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="language">Language</Label>
                    <Select
                      value={config.language}
                      onValueChange={(value) => setConfig({...config, language: value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="es">Spanish</SelectItem>
                        <SelectItem value="fr">French</SelectItem>
                        <SelectItem value="de">German</SelectItem>
                        <SelectItem value="it">Italian</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="confidence-threshold">
                      Confidence Threshold: {config.confidence_threshold}
                    </Label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={config.confidence_threshold}
                      onChange={(e) => setConfig({...config, confidence_threshold: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="segment-duration">
                      Segment Duration: {config.segment_duration}s
                    </Label>
                    <input
                      type="range"
                      min="0.5"
                      max="10"
                      step="0.5"
                      value={config.segment_duration}
                      onChange={(e) => setConfig({...config, segment_duration: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="overlap-duration">
                      Overlap Duration: {config.overlap_duration}s
                    </Label>
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="0.1"
                      value={config.overlap_duration}
                      onChange={(e) => setConfig({...config, overlap_duration: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="font-semibold">Analysis Options</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="enable-audio">Enable Audio Analysis</Label>
                    <Switch
                      id="enable-audio"
                      checked={config.enable_audio_analysis}
                      onCheckedChange={(checked) => setConfig({...config, enable_audio_analysis: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="enable-text">Enable Text Analysis</Label>
                    <Switch
                      id="enable-text"
                      checked={config.enable_text_analysis}
                      onCheckedChange={(checked) => setConfig({...config, enable_text_analysis: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="enable-temporal">Enable Temporal Analysis</Label>
                    <Switch
                      id="enable-temporal"
                      checked={config.enable_temporal_analysis}
                      onCheckedChange={(checked) => setConfig({...config, enable_temporal_analysis: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="enable-speaker">Enable Speaker Emotion</Label>
                    <Switch
                      id="enable-speaker"
                      checked={config.enable_speaker_emotion}
                      onCheckedChange={(checked) => setConfig({...config, enable_speaker_emotion: checked})}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default EmotionSentimentDetection;