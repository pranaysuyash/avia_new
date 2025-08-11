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
  Settings, 
  Activity,
  Volume2,
  VolumeX,
  Download,
  RefreshCw,
  Zap,
  Target,
  TrendingUp,
  Clock
} from 'lucide-react';

interface VADSegment {
  start_time: number;
  end_time: number;
  duration: number;
  is_speech: boolean;
  confidence: number;
  method: string;
  features?: Record<string, number>;
}

interface AudioQualityMetrics {
  snr_db: number;
  thd_percent: number;
  dynamic_range_db: number;
  spectral_centroid_hz: number;
  spectral_rolloff_hz: number;
  zero_crossing_rate: number;
  mfcc_features: number[];
  energy_entropy: number;
  spectral_entropy: number;
}

interface VADResult {
  segments: VADSegment[];
  total_duration: number;
  speech_duration: number;
  silence_duration: number;
  speech_ratio: number;
  quality_score: number;
  method_used: string;
  processing_time: number;
  audio_quality?: AudioQualityMetrics;
}

interface VADConfig {
  method: string;
  mode: number;
  frame_duration_ms: number;
  sample_rate: number;
  min_speech_duration: number;
  min_silence_duration: number;
  energy_threshold: number;
  enable_preprocessing: boolean;
  enable_postprocessing: boolean;
}

interface MethodOption {
  value: string;
  label: string;
  description: string;
  supports_modes: boolean;
  recommended_for: string[];
}

const VoiceActivityDetection: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<VADResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [methods, setMethods] = useState<MethodOption[]>([]);
  const [batchResults, setBatchResults] = useState<any[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  
  // Configuration state
  const [config, setConfig] = useState<VADConfig>({
    method: 'webrtc',
    mode: 2,
    frame_duration_ms: 30,
    sample_rate: 16000,
    min_speech_duration: 0.1,
    min_silence_duration: 0.1,
    energy_threshold: 0.01,
    enable_preprocessing: true,
    enable_postprocessing: true
  });
  
  // Analysis options
  const [includeQualityMetrics, setIncludeQualityMetrics] = useState(true);
  const [includeFeatures, setIncludeFeatures] = useState(false);
  
  // Audio playback
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load available methods on component mount
  useEffect(() => {
    loadMethods();
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

  const loadMethods = async () => {
    try {
      const response = await fetch('/api/v1/voice-activity-detection/methods');
      if (response.ok) {
        const data = await response.json();
        setMethods(data.data.methods);
      }
    } catch (error) {
      console.error('Failed to load methods:', error);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setResult(null);
      setError(null);
      setBatchResults([]);
      setShowComparison(false);
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
      formData.append('file', selectedFile);

      const requestBody = {
        config: config,
        include_quality_metrics: includeQualityMetrics,
        include_features: includeFeatures
      };

      formData.append('request', JSON.stringify(requestBody));

      const response = await fetch('/api/v1/voice-activity-detection/analyze', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze voice activity');
      }

      const data = await response.json();
      setResult(data.data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleBatchAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select an audio file');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Create multiple configurations for comparison
      const configs = [
        { ...config, method: 'webrtc' },
        { ...config, method: 'energy_based' },
        { ...config, method: 'spectral_centroid' },
        { ...config, method: 'ensemble' }
      ];

      const requestBody = {
        configs: configs,
        include_comparison: true
      };

      formData.append('request', JSON.stringify(requestBody));

      const response = await fetch('/api/v1/voice-activity-detection/batch-analyze', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to perform batch analysis');
      }

      const data = await response.json();
      setBatchResults(data.data.results);
      setShowComparison(true);
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

  const handleSeek = (time: number) => {
    const audio = audioRef.current;
    if (audio) {
      audio.currentTime = time;
      setCurrentTime(time);
    }
  };

  const exportResults = () => {
    if (!result) return;
    
    const exportData = {
      analysis_results: result,
      configuration: config,
      file_info: {
        name: selectedFile?.name,
        size: selectedFile?.size,
        type: selectedFile?.type
      },
      exported_at: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vad-analysis-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSegmentColor = (segment: VADSegment) => {
    if (segment.is_speech) {
      return segment.confidence > 0.8 ? '#10B981' : '#F59E0B';
    }
    return '#6B7280';
  };

  const renderWaveform = () => {
    if (!result) return null;

    const totalWidth = 800;
    const segmentWidth = totalWidth / result.segments.length;

    return (
      <div className="relative">
        <div className="flex h-16 bg-gray-100 rounded-lg overflow-hidden">
          {result.segments.map((segment, index) => (
            <div
              key={index}
              className="flex-shrink-0 cursor-pointer hover:opacity-80 transition-opacity"
              style={{
                width: `${segmentWidth}px`,
                backgroundColor: getSegmentColor(segment),
                opacity: segment.confidence
              }}
              onClick={() => handleSeek(segment.start_time)}
              title={`${segment.is_speech ? 'Speech' : 'Silence'} - ${segment.confidence.toFixed(2)} confidence`}
            />
          ))}
        </div>
        
        {/* Playback position indicator */}
        {duration > 0 && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-red-500 pointer-events-none"
            style={{
              left: `${(currentTime / duration) * totalWidth}px`
            }}
          />
        )}
      </div>
    );
  };

  const renderSegmentsList = () => {
    if (!result) return null;

    return (
      <div className="max-h-64 overflow-y-auto space-y-2">
        {result.segments.map((segment, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg border cursor-pointer hover:bg-gray-50 ${
              segment.is_speech ? 'border-green-200 bg-green-50' : 'border-gray-200'
            }`}
            onClick={() => handleSeek(segment.start_time)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {segment.is_speech ? (
                  <Volume2 className="h-4 w-4 text-green-600" />
                ) : (
                  <VolumeX className="h-4 w-4 text-gray-400" />
                )}
                <span className="font-medium">
                  {segment.is_speech ? 'Speech' : 'Silence'}
                </span>
                <Badge variant={segment.is_speech ? 'default' : 'secondary'}>
                  {(segment.confidence * 100).toFixed(1)}%
                </Badge>
              </div>
              <div className="text-sm text-gray-500">
                {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
              </div>
            </div>
            <div className="text-xs text-gray-400 mt-1">
              Duration: {segment.duration.toFixed(2)}s
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderBatchComparison = () => {
    if (!showComparison || batchResults.length === 0) return null;

    const successfulResults = batchResults.filter(r => r.status === 'success');

    return (
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Method Comparison</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {successfulResults.map((result, index) => (
                <div key={index} className="p-4 border rounded-lg">
                  <h4 className="font-medium mb-2">{result.result.method_used}</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Speech Ratio:</span>
                      <span>{(result.result.speech_ratio * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Quality:</span>
                      <span>{(result.result.quality_score * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Time:</span>
                      <span>{result.result.processing_time.toFixed(2)}s</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Segments:</span>
                      <span>{result.result.segments.length}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center space-x-2">
        <Activity className="h-6 w-6 text-blue-600" />
        <h1 className="text-2xl font-bold">Voice Activity Detection</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Configuration</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* File Upload */}
            <div className="space-y-2">
              <Label>Audio File</Label>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                  className="flex-1"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  {selectedFile ? selectedFile.name : 'Select File'}
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </div>

            {/* Audio Player */}
            {selectedFile && (
              <div className="space-y-2">
                <audio
                  ref={audioRef}
                  src={URL.createObjectURL(selectedFile)}
                  className="hidden"
                />
                <div className="flex items-center space-x-2">
                  <Button
                    onClick={togglePlayback}
                    variant="outline"
                    size="sm"
                  >
                    {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                  <div className="flex-1 text-sm text-gray-500">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </div>
                </div>
                {duration > 0 && (
                  <Progress value={(currentTime / duration) * 100} className="h-2" />
                )}
              </div>
            )}

            <Separator />

            {/* VAD Configuration */}
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="basic">Basic</TabsTrigger>
                <TabsTrigger value="advanced">Advanced</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4">
                <div>
                  <Label htmlFor="method">Detection Method</Label>
                  <Select 
                    value={config.method} 
                    onValueChange={(value) => setConfig(prev => ({ ...prev, method: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {methods.map(method => (
                        <SelectItem key={method.value} value={method.value}>
                          {method.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {methods.find(m => m.value === config.method) && (
                    <p className="text-xs text-gray-500 mt-1">
                      {methods.find(m => m.value === config.method)?.description}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="mode">Aggressiveness Mode</Label>
                  <Select 
                    value={config.mode.toString()} 
                    onValueChange={(value) => setConfig(prev => ({ ...prev, mode: parseInt(value) }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">Quality (Most Aggressive)</SelectItem>
                      <SelectItem value="1">Low Bitrate</SelectItem>
                      <SelectItem value="2">Normal (Balanced)</SelectItem>
                      <SelectItem value="3">Very Aggressive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="sample-rate">Sample Rate (Hz)</Label>
                  <Select 
                    value={config.sample_rate.toString()} 
                    onValueChange={(value) => setConfig(prev => ({ ...prev, sample_rate: parseInt(value) }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="8000">8000 Hz</SelectItem>
                      <SelectItem value="16000">16000 Hz</SelectItem>
                      <SelectItem value="32000">32000 Hz</SelectItem>
                      <SelectItem value="48000">48000 Hz</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>

              <TabsContent value="advanced" className="space-y-4">
                <div>
                  <Label htmlFor="frame-duration">Frame Duration (ms)</Label>
                  <Input
                    id="frame-duration"
                    type="number"
                    min="10"
                    max="100"
                    value={config.frame_duration_ms}
                    onChange={(e) => setConfig(prev => ({ ...prev, frame_duration_ms: parseInt(e.target.value) }))}
                  />
                </div>

                <div>
                  <Label htmlFor="min-speech">Min Speech Duration (s)</Label>
                  <Input
                    id="min-speech"
                    type="number"
                    min="0.01"
                    max="5"
                    step="0.01"
                    value={config.min_speech_duration}
                    onChange={(e) => setConfig(prev => ({ ...prev, min_speech_duration: parseFloat(e.target.value) }))}
                  />
                </div>

                <div>
                  <Label htmlFor="min-silence">Min Silence Duration (s)</Label>
                  <Input
                    id="min-silence"
                    type="number"
                    min="0.01"
                    max="5"
                    step="0.01"
                    value={config.min_silence_duration}
                    onChange={(e) => setConfig(prev => ({ ...prev, min_silence_duration: parseFloat(e.target.value) }))}
                  />
                </div>

                <div>
                  <Label htmlFor="energy-threshold">Energy Threshold</Label>
                  <Input
                    id="energy-threshold"
                    type="number"
                    min="0"
                    max="1"
                    step="0.001"
                    value={config.energy_threshold}
                    onChange={(e) => setConfig(prev => ({ ...prev, energy_threshold: parseFloat(e.target.value) }))}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="preprocessing"
                      checked={config.enable_preprocessing}
                      onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enable_preprocessing: checked }))}
                    />
                    <Label htmlFor="preprocessing">Enable Preprocessing</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="postprocessing"
                      checked={config.enable_postprocessing}
                      onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enable_postprocessing: checked }))}
                    />
                    <Label htmlFor="postprocessing">Enable Postprocessing</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="quality-metrics"
                      checked={includeQualityMetrics}
                      onCheckedChange={setIncludeQualityMetrics}
                    />
                    <Label htmlFor="quality-metrics">Include Quality Metrics</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="features"
                      checked={includeFeatures}
                      onCheckedChange={setIncludeFeatures}
                    />
                    <Label htmlFor="features">Include Detailed Features</Label>
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <Separator />

            {/* Action Buttons */}
            <div className="space-y-2">
              <Button 
                onClick={handleAnalyze} 
                disabled={!selectedFile || isAnalyzing}
                className="w-full"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Analyze Voice Activity
                  </>
                )}
              </Button>

              <Button 
                onClick={handleBatchAnalyze} 
                disabled={!selectedFile || isAnalyzing}
                variant="outline"
                className="w-full"
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                Compare Methods
              </Button>

              {result && (
                <Button onClick={exportResults} variant="outline" className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Export Results
                </Button>
              )}
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Results Panel */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Target className="h-5 w-5" />
                <span>Analysis Results</span>
              </div>
              {result && (
                <Badge variant="outline">
                  {result.method_used}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-6">
                {/* Summary Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {(result.speech_ratio * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-500">Speech Ratio</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {(result.quality_score * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-500">Quality Score</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {result.segments.length}
                    </div>
                    <div className="text-sm text-gray-500">Segments</div>
                  </div>
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {result.processing_time.toFixed(2)}s
                    </div>
                    <div className="text-sm text-gray-500">Processing Time</div>
                  </div>
                </div>

                {/* Waveform Visualization */}
                <div className="space-y-2">
                  <h3 className="font-semibold">Voice Activity Timeline</h3>
                  {renderWaveform()}
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <div className="flex items-center space-x-1">
                      <div className="w-3 h-3 bg-green-500 rounded"></div>
                      <span>Speech</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <div className="w-3 h-3 bg-gray-400 rounded"></div>
                      <span>Silence</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                      <span>Low Confidence</span>
                    </div>
                  </div>
                </div>

                {/* Duration Breakdown */}
                <div className="space-y-2">
                  <h3 className="font-semibold">Duration Breakdown</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span>Total Duration:</span>
                      <span>{formatTime(result.total_duration)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Speech Duration:</span>
                      <span className="text-green-600">{formatTime(result.speech_duration)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Silence Duration:</span>
                      <span className="text-gray-500">{formatTime(result.silence_duration)}</span>
                    </div>
                  </div>
                </div>

                {/* Audio Quality Metrics */}
                {result.audio_quality && (
                  <div className="space-y-2">
                    <h3 className="font-semibold">Audio Quality Metrics</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex justify-between">
                        <span>SNR:</span>
                        <span>{result.audio_quality.snr_db.toFixed(1)} dB</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Dynamic Range:</span>
                        <span>{result.audio_quality.dynamic_range_db.toFixed(1)} dB</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Spectral Centroid:</span>
                        <span>{result.audio_quality.spectral_centroid_hz.toFixed(0)} Hz</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Zero Crossing Rate:</span>
                        <span>{result.audio_quality.zero_crossing_rate.toFixed(3)}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Segments List */}
                <div className="space-y-2">
                  <h3 className="font-semibold">Detected Segments</h3>
                  {renderSegmentsList()}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Upload an audio file and click "Analyze Voice Activity" to see results</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Batch Comparison Results */}
      {renderBatchComparison()}
    </div>
  );
};

export default VoiceActivityDetection;