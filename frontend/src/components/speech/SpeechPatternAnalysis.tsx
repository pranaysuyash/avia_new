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
  BarChart3,
  Clock,
  MessageSquare,
  TrendingUp,
  TrendingDown,
  Volume2,
  Mic,
  Target,
  Award,
  BookOpen,
  RefreshCw,
  Download,
  Settings,
  Activity,
  Zap
} from 'lucide-react';

interface SpeechSegment {
  start_time: number;
  end_time: number;
  text: string;
  speaker_id?: string;
  confidence: number;
  duration: number;
  word_count: number;
  speech_rate: number;
  pause_count: number;
  filler_count: number;
}

interface PauseAnalysis {
  total_pause_time: number;
  pause_count: number;
  average_pause_duration: number;
  longest_pause_duration: number;
  pause_frequency: number;
  pause_locations: Array<{ start_time: number; duration: number }>;
  silence_ratio: number;
}

interface FillerWordAnalysis {
  total_filler_count: number;
  filler_frequency: number;
  filler_types: Record<string, number>;
  filler_locations: Array<{ word: string; start_time: number; confidence: number }>;
  filler_ratio: number;
}

interface SpeechRateAnalysis {
  average_speech_rate: number;
  speech_rate_variance: number;
  speech_rate_timeline: Array<{ time: number; rate: number }>;
  speaking_time: number;
  total_words: number;
  rate_classification: string;
}

interface ConfidenceAnalysis {
  overall_confidence: number;
  confidence_timeline: Array<{ time: number; confidence: number }>;
  hesitation_count: number;
  repetition_count: number;
  false_starts: number;
  confidence_classification: string;
}

interface CoachingSuggestions {
  overall_score: number;
  strengths: string[];
  areas_for_improvement: string[];
  specific_suggestions: Array<{ category: string; suggestion: string }>;
  practice_exercises: string[];
}

interface AnalysisResult {
  segments: SpeechSegment[];
  pause_analysis: PauseAnalysis;
  filler_analysis: FillerWordAnalysis;
  speech_rate_analysis: SpeechRateAnalysis;
  confidence_analysis: ConfidenceAnalysis;
  coaching_suggestions: CoachingSuggestions;
  overall_statistics: Record<string, any>;
  processing_time: number;
  total_duration: number;
  config_used: any;
}

interface AnalysisConfig {
  analysis_types: string[];
  language: string;
  speaker_detection: boolean;
  filler_word_detection: boolean;
  pause_analysis: boolean;
  speech_rate_analysis: boolean;
  confidence_analysis: boolean;
  coaching_suggestions: boolean;
  segment_duration: number;
  min_pause_duration: number;
  speech_rate_threshold: number;
}

const SpeechPatternAnalysis: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [transcriptText, setTranscriptText] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisTypes, setAnalysisTypes] = useState<any>(null);
  
  // Configuration state
  const [config, setConfig] = useState<AnalysisConfig>({
    analysis_types: ['all'],
    language: 'en',
    speaker_detection: true,
    filler_word_detection: true,
    pause_analysis: true,
    speech_rate_analysis: true,
    confidence_analysis: true,
    coaching_suggestions: true,
    segment_duration: 5.0,
    min_pause_duration: 0.3,
    speech_rate_threshold: 150.0
  });
  
  // Audio playback
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load available analysis types on component mount
  useEffect(() => {
    loadAnalysisTypes();
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

  const loadAnalysisTypes = async () => {
    try {
      const response = await fetch('/api/v1/speech-pattern/analysis-types');
      if (response.ok) {
        const data = await response.json();
        setAnalysisTypes(data.data);
      }
    } catch (error) {
      console.error('Failed to load analysis types:', error);
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
      
      formData.append('include_coaching', 'true');

      const response = await fetch('/api/v1/speech-pattern/analyze', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze speech patterns');
      }

      const data = await response.json();
      setResult(data.data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsAnalyzing(false);
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

  const getRateClassificationColor = (classification: string) => {
    switch (classification.toLowerCase()) {
      case 'too slow':
        return 'bg-blue-100 text-blue-800';
      case 'optimal':
        return 'bg-green-100 text-green-800';
      case 'too fast':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getConfidenceClassificationColor = (classification: string) => {
    switch (classification.toLowerCase()) {
      case 'high':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Speech Pattern Analysis
        </h1>
        <p className="text-gray-600">
          Analyze speaking patterns, pace, pauses, and get personalized coaching suggestions
        </p>
      </div>

      <Tabs defaultValue="analysis" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="analysis">
            <Mic className="w-4 h-4 mr-2" />
            Analysis
          </TabsTrigger>
          <TabsTrigger value="coaching">
            <Target className="w-4 h-4 mr-2" />
            Coaching
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="analysis" className="space-y-6">
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
                  placeholder="Paste transcript text here for more accurate analysis..."
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
                    Analyzing Speech Patterns...
                  </>
                ) : (
                  <>
                    <Activity className="w-4 h-4 mr-2" />
                    Analyze Speech Patterns
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Results */}
          {result && (
            <div className="space-y-6">
              {/* Overall Statistics */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    Overall Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-blue-600">{result.segments.length}</p>
                      <p className="text-sm text-gray-500">Speech Segments</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-green-600">
                        {result.speech_rate_analysis.average_speech_rate.toFixed(0)} WPM
                      </p>
                      <p className="text-sm text-gray-500">Average Speech Rate</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-purple-600">
                        {result.pause_analysis.pause_count}
                      </p>
                      <p className="text-sm text-gray-500">Total Pauses</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-orange-600">
                        {result.filler_analysis.total_filler_count}
                      </p>
                      <p className="text-sm text-gray-500">Filler Words</p>
                    </div>
                  </div>

                  <Separator className="my-4" />

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <Badge className={getRateClassificationColor(result.speech_rate_analysis.rate_classification)}>
                        {result.speech_rate_analysis.rate_classification}
                      </Badge>
                      <p className="text-sm text-gray-500 mt-1">Speech Rate</p>
                    </div>
                    <div className="text-center">
                      <Badge className={getConfidenceClassificationColor(result.confidence_analysis.confidence_classification)}>
                        {result.confidence_analysis.confidence_classification}
                      </Badge>
                      <p className="text-sm text-gray-500 mt-1">Confidence Level</p>
                    </div>
                    <div className="text-center">
                      <p className={`text-2xl font-bold ${getScoreColor(result.coaching_suggestions.overall_score)}`}>
                        {result.coaching_suggestions.overall_score.toFixed(0)}%
                      </p>
                      <p className="text-sm text-gray-500">Overall Score</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Detailed Analysis */}
              <Tabs defaultValue="speech-rate" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="speech-rate">Speech Rate</TabsTrigger>
                  <TabsTrigger value="pauses">Pauses</TabsTrigger>
                  <TabsTrigger value="fillers">Fillers</TabsTrigger>
                  <TabsTrigger value="confidence">Confidence</TabsTrigger>
                </TabsList>

                <TabsContent value="speech-rate" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="w-5 h-5" />
                        Speech Rate Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-blue-600">
                            {result.speech_rate_analysis.average_speech_rate.toFixed(0)}
                          </p>
                          <p className="text-sm text-gray-500">Words Per Minute</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-green-600">
                            {result.speech_rate_analysis.total_words}
                          </p>
                          <p className="text-sm text-gray-500">Total Words</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-purple-600">
                            {result.speech_rate_analysis.speaking_time.toFixed(1)}s
                          </p>
                          <p className="text-sm text-gray-500">Speaking Time</p>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium mb-2">Speech Rate Timeline</h4>
                        <div className="h-32 bg-gray-50 rounded-lg flex items-center justify-center">
                          <p className="text-gray-500">Speech rate timeline chart would be rendered here</p>
                        </div>
                      </div>

                      <div className="p-4 bg-blue-50 rounded-lg">
                        <p className="text-sm text-blue-800">
                          <strong>Classification:</strong> {result.speech_rate_analysis.rate_classification}
                        </p>
                        <p className="text-sm text-blue-700 mt-1">
                          Optimal speech rate is typically between 140-160 words per minute for clear communication.
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="pauses" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Clock className="w-5 h-5" />
                        Pause Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-blue-600">
                            {result.pause_analysis.pause_count}
                          </p>
                          <p className="text-sm text-gray-500">Total Pauses</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-green-600">
                            {result.pause_analysis.average_pause_duration.toFixed(2)}s
                          </p>
                          <p className="text-sm text-gray-500">Average Duration</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-purple-600">
                            {result.pause_analysis.longest_pause_duration.toFixed(2)}s
                          </p>
                          <p className="text-sm text-gray-500">Longest Pause</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-orange-600">
                            {(result.pause_analysis.silence_ratio * 100).toFixed(1)}%
                          </p>
                          <p className="text-sm text-gray-500">Silence Ratio</p>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium mb-2">Pause Locations</h4>
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {result.pause_analysis.pause_locations.slice(0, 10).map((pause, index) => (
                            <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                              <span className="text-sm">Pause {index + 1}</span>
                              <span className="text-sm text-gray-500">
                                {formatTime(pause.start_time)} ({pause.duration.toFixed(2)}s)
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="p-4 bg-green-50 rounded-lg">
                        <p className="text-sm text-green-800">
                          <strong>Pause Frequency:</strong> {result.pause_analysis.pause_frequency.toFixed(2)} pauses per minute
                        </p>
                        <p className="text-sm text-green-700 mt-1">
                          Strategic pauses can improve clarity and give listeners time to process information.
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="fillers" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <MessageSquare className="w-5 h-5" />
                        Filler Word Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-red-600">
                            {result.filler_analysis.total_filler_count}
                          </p>
                          <p className="text-sm text-gray-500">Total Fillers</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-orange-600">
                            {result.filler_analysis.filler_frequency.toFixed(1)}
                          </p>
                          <p className="text-sm text-gray-500">Per Minute</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-purple-600">
                            {(result.filler_analysis.filler_ratio * 100).toFixed(1)}%
                          </p>
                          <p className="text-sm text-gray-500">Filler Ratio</p>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium mb-2">Filler Word Types</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                          {Object.entries(result.filler_analysis.filler_types).map(([word, count]) => (
                            <div key={word} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                              <span className="text-sm font-medium">"{word}"</span>
                              <Badge variant="outline">{count}</Badge>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium mb-2">Recent Filler Locations</h4>
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {result.filler_analysis.filler_locations.slice(0, 10).map((filler, index) => (
                            <div key={index} className="flex justify-between items-center p-2 bg-red-50 rounded">
                              <span className="text-sm font-medium">"{filler.word}"</span>
                              <span className="text-sm text-gray-500">
                                {formatTime(filler.start_time)} ({(filler.confidence * 100).toFixed(0)}%)
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="p-4 bg-red-50 rounded-lg">
                        <p className="text-sm text-red-800">
                          <strong>Recommendation:</strong> Try to reduce filler words for clearer communication
                        </p>
                        <p className="text-sm text-red-700 mt-1">
                          Practice pausing silently instead of using filler words like "um", "uh", or "like".
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="confidence" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Zap className="w-5 h-5" />
                        Confidence Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-green-600">
                            {(result.confidence_analysis.overall_confidence * 100).toFixed(0)}%
                          </p>
                          <p className="text-sm text-gray-500">Overall Confidence</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-yellow-600">
                            {result.confidence_analysis.hesitation_count}
                          </p>
                          <p className="text-sm text-gray-500">Hesitations</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-red-600">
                            {result.confidence_analysis.repetition_count}
                          </p>
                          <p className="text-sm text-gray-500">Repetitions</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-purple-600">
                            {result.confidence_analysis.false_starts}
                          </p>
                          <p className="text-sm text-gray-500">False Starts</p>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium mb-2">Confidence Timeline</h4>
                        <div className="h-32 bg-gray-50 rounded-lg flex items-center justify-center">
                          <p className="text-gray-500">Confidence timeline chart would be rendered here</p>
                        </div>
                      </div>

                      <div className="p-4 bg-green-50 rounded-lg">
                        <p className="text-sm text-green-800">
                          <strong>Classification:</strong> {result.confidence_analysis.confidence_classification} Confidence
                        </p>
                        <p className="text-sm text-green-700 mt-1">
                          Confident speakers typically have fewer hesitations and false starts.
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </TabsContent>

        <TabsContent value="coaching" className="space-y-6">
          {result && (
            <div className="space-y-6">
              {/* Overall Score */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Award className="w-5 h-5" />
                    Speaking Performance Score
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className={`text-6xl font-bold ${getScoreColor(result.coaching_suggestions.overall_score)} mb-2`}>
                      {result.coaching_suggestions.overall_score.toFixed(0)}%
                    </div>
                    <Progress 
                      value={result.coaching_suggestions.overall_score} 
                      className="w-full max-w-md mx-auto mb-4" 
                    />
                    <p className="text-gray-600">
                      Based on speech rate, pause management, filler usage, and confidence indicators
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Strengths and Areas for Improvement */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-green-600">
                      <TrendingUp className="w-5 h-5" />
                      Strengths
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {result.coaching_suggestions.strengths.map((strength, index) => (
                        <div key={index} className="flex items-start gap-2">
                          <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                          <p className="text-sm text-gray-700">{strength}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-orange-600">
                      <Target className="w-5 h-5" />
                      Areas for Improvement
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {result.coaching_suggestions.areas_for_improvement.map((area, index) => (
                        <div key={index} className="flex items-start gap-2">
                          <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0" />
                          <p className="text-sm text-gray-700">{area}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Specific Suggestions */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="w-5 h-5" />
                    Specific Suggestions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {result.coaching_suggestions.specific_suggestions.map((suggestion, index) => (
                      <div key={index} className="p-4 border rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline">{suggestion.category}</Badge>
                        </div>
                        <p className="text-sm text-gray-700">{suggestion.suggestion}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Practice Exercises */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    Recommended Practice Exercises
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {result.coaching_suggestions.practice_exercises.map((exercise, index) => (
                      <div key={index} className="p-4 bg-blue-50 rounded-lg">
                        <div className="flex items-start gap-2">
                          <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                            {index + 1}
                          </div>
                          <p className="text-sm text-blue-800">{exercise}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {!result && (
            <Card>
              <CardContent className="text-center py-12">
                <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">
                  Upload and analyze an audio file to receive personalized coaching suggestions
                </p>
              </CardContent>
            </Card>
          )}
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

                  <div>
                    <Label htmlFor="segment-duration">
                      Segment Duration: {config.segment_duration}s
                    </Label>
                    <input
                      type="range"
                      min="1"
                      max="30"
                      step="1"
                      value={config.segment_duration}
                      onChange={(e) => setConfig({...config, segment_duration: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="min-pause-duration">
                      Min Pause Duration: {config.min_pause_duration}s
                    </Label>
                    <input
                      type="range"
                      min="0.1"
                      max="2"
                      step="0.1"
                      value={config.min_pause_duration}
                      onChange={(e) => setConfig({...config, min_pause_duration: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="speech-rate-threshold">
                      Speech Rate Threshold: {config.speech_rate_threshold} WPM
                    </Label>
                    <input
                      type="range"
                      min="50"
                      max="300"
                      step="10"
                      value={config.speech_rate_threshold}
                      onChange={(e) => setConfig({...config, speech_rate_threshold: parseFloat(e.target.value)})}
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
                    <Label htmlFor="speaker-detection">Speaker Detection</Label>
                    <Switch
                      id="speaker-detection"
                      checked={config.speaker_detection}
                      onCheckedChange={(checked) => setConfig({...config, speaker_detection: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="filler-detection">Filler Word Detection</Label>
                    <Switch
                      id="filler-detection"
                      checked={config.filler_word_detection}
                      onCheckedChange={(checked) => setConfig({...config, filler_word_detection: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="pause-analysis">Pause Analysis</Label>
                    <Switch
                      id="pause-analysis"
                      checked={config.pause_analysis}
                      onCheckedChange={(checked) => setConfig({...config, pause_analysis: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="speech-rate-analysis">Speech Rate Analysis</Label>
                    <Switch
                      id="speech-rate-analysis"
                      checked={config.speech_rate_analysis}
                      onCheckedChange={(checked) => setConfig({...config, speech_rate_analysis: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="confidence-analysis">Confidence Analysis</Label>
                    <Switch
                      id="confidence-analysis"
                      checked={config.confidence_analysis}
                      onCheckedChange={(checked) => setConfig({...config, confidence_analysis: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="coaching-suggestions">Coaching Suggestions</Label>
                    <Switch
                      id="coaching-suggestions"
                      checked={config.coaching_suggestions}
                      onCheckedChange={(checked) => setConfig({...config, coaching_suggestions: checked})}
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

export default SpeechPatternAnalysis;