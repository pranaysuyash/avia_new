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
  Download,
  Settings,
  BarChart3,
  Zap,
  Volume2,
  VolumeX,
  Sliders,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Waveform,
  Filter,
  Maximize
} from 'lucide-react';

interface AudioQualityMetrics {
  overall_quality_score: number;
  snr_db: number;
  thd_percent: number;
  dynamic_range_db: number;
  peak_level_db: number;
  rms_level_db: number;
  spectral_centroid: number;
  spectral_rolloff: number;
  zero_crossing_rate: number;
  silence_ratio: number;
  clipping_detected: boolean;
  noise_level_db: number;
  frequency_response_score: number;
  stereo_balance?: number;
}

interface EnhancementResult {
  original_metrics: AudioQualityMetrics;
  enhanced_metrics: AudioQualityMetrics;
  improvement_score: number;
  processing_time: number;
  file_size_original: number;
  file_size_enhanced: number;
  enhancements_applied: string[];
  recommendations: string[];
  config_used: any;
}

interface EnhancementConfig {
  enable_noise_reduction: boolean;
  enable_normalization: boolean;
  enable_compression: boolean;
  enable_eq: boolean;
  enable_repair: boolean;
  target_sample_rate: number;
  target_bit_depth: number;
  noise_reduction_strength: number;
  normalization_target: number;
  compression_ratio: number;
  high_pass_freq: number;
  low_pass_freq: number;
}con
st AudioEnhancement: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<EnhancementResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [presets, setPresets] = useState<any[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  
  // Configuration state
  const [config, setConfig] = useState<EnhancementConfig>({
    enable_noise_reduction: true,
    enable_normalization: true,
    enable_compression: false,
    enable_eq: false,
    enable_repair: true,
    target_sample_rate: 16000,
    target_bit_depth: 16,
    noise_reduction_strength: 0.7,
    normalization_target: -20.0,
    compression_ratio: 2.0,
    high_pass_freq: 80.0,
    low_pass_freq: 8000.0
  });
  
  // Audio playback
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadPresets();
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

  const loadPresets = async () => {
    try {
      const response = await fetch('/api/v1/audio-enhancement/presets');
      if (response.ok) {
        const data = await response.json();
        setPresets(data.data.presets);
      }
    } catch (error) {
      console.error('Failed to load presets:', error);
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

  const handlePresetChange = (presetName: string) => {
    const preset = presets.find(p => p.name === presetName);
    if (preset) {
      setConfig(preset.config);
      setSelectedPreset(presetName);
    }
  };

  const handleEnhance = async () => {
    if (!selectedFile) {
      setError('Please select an audio file');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('audio_file', selectedFile);
      formData.append('config', JSON.stringify(config));
      formData.append('return_enhanced_file', 'true');

      const response = await fetch('/api/v1/audio-enhancement/enhance', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to enhance audio');
      }

      const data = await response.json();
      setResult(data.data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsProcessing(false);
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

  const getQualityColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  };  re
turn (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Audio Enhancement Pipeline
        </h1>
        <p className="text-gray-600">
          Enhance audio quality with noise reduction, normalization, and advanced processing
        </p>
      </div>

      <Tabs defaultValue="enhance" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="enhance">
            <Zap className="w-4 h-4 mr-2" />
            Enhance
          </TabsTrigger>
          <TabsTrigger value="analyze">
            <BarChart3 className="w-4 h-4 mr-2" />
            Analyze
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="enhance" className="space-y-6">
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

              {/* Preset Selection */}
              <div>
                <Label htmlFor="preset">Enhancement Preset</Label>
                <Select value={selectedPreset} onValueChange={handlePresetChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a preset or configure manually" />
                  </SelectTrigger>
                  <SelectContent>
                    {presets.map(preset => (
                      <SelectItem key={preset.name} value={preset.name}>
                        {preset.name} - {preset.description}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button
                onClick={handleEnhance}
                disabled={!selectedFile || isProcessing}
                className="w-full"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Enhancing Audio...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" />
                    Enhance Audio
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Results */}
          {result && (
            <div className="space-y-6">
              {/* Enhancement Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    Enhancement Complete
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-green-600">
                        {result.improvement_score.toFixed(1)}%
                      </p>
                      <p className="text-sm text-gray-500">Improvement</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-blue-600">
                        {result.processing_time.toFixed(2)}s
                      </p>
                      <p className="text-sm text-gray-500">Processing Time</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-purple-600">
                        {result.enhancements_applied.length}
                      </p>
                      <p className="text-sm text-gray-500">Enhancements Applied</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-orange-600">
                        {((result.file_size_enhanced / result.file_size_original) * 100).toFixed(0)}%
                      </p>
                      <p className="text-sm text-gray-500">Size Ratio</p>
                    </div>
                  </div>

                  <Separator className="my-4" />

                  <div className="space-y-3">
                    <h4 className="font-medium">Enhancements Applied:</h4>
                    <div className="flex flex-wrap gap-2">
                      {result.enhancements_applied.map((enhancement, index) => (
                        <Badge key={index} variant="secondary">
                          {enhancement}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {result.recommendations.length > 0 && (
                    <div className="space-y-3 mt-4">
                      <h4 className="font-medium">Recommendations:</h4>
                      <div className="space-y-2">
                        {result.recommendations.map((recommendation, index) => (
                          <div key={index} className="flex items-start gap-2">
                            <AlertCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-gray-700">{recommendation}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Quality Comparison */}
              <Card>
                <CardHeader>
                  <CardTitle>Quality Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium mb-3 text-red-600">Original Audio</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Overall Quality</span>
                          <div className="flex items-center gap-2">
                            <span className={`font-medium ${getQualityColor(result.original_metrics.overall_quality_score)}`}>
                              {result.original_metrics.overall_quality_score.toFixed(1)}%
                            </span>
                            <Badge variant="outline" className={getQualityColor(result.original_metrics.overall_quality_score)}>
                              {getQualityLabel(result.original_metrics.overall_quality_score)}
                            </Badge>
                          </div>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">SNR</span>
                          <span className="font-medium">{result.original_metrics.snr_db.toFixed(1)} dB</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Dynamic Range</span>
                          <span className="font-medium">{result.original_metrics.dynamic_range_db.toFixed(1)} dB</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Peak Level</span>
                          <span className="font-medium">{result.original_metrics.peak_level_db.toFixed(1)} dB</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Noise Level</span>
                          <span className="font-medium">{result.original_metrics.noise_level_db.toFixed(1)} dB</span>
                        </div>
                        {result.original_metrics.clipping_detected && (
                          <div className="flex items-center gap-2 text-red-600">
                            <AlertCircle className="w-4 h-4" />
                            <span className="text-sm">Clipping Detected</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-3 text-green-600">Enhanced Audio</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Overall Quality</span>
                          <div className="flex items-center gap-2">
                            <span className={`font-medium ${getQualityColor(result.enhanced_metrics.overall_quality_score)}`}>
                              {result.enhanced_metrics.overall_quality_score.toFixed(1)}%
                            </span>
                            <Badge variant="outline" className={getQualityColor(result.enhanced_metrics.overall_quality_score)}>
                              {getQualityLabel(result.enhanced_metrics.overall_quality_score)}
                            </Badge>
                            <TrendingUp className="w-4 h-4 text-green-500" />
                          </div>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">SNR</span>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{result.enhanced_metrics.snr_db.toFixed(1)} dB</span>
                            {result.enhanced_metrics.snr_db > result.original_metrics.snr_db && (
                              <TrendingUp className="w-4 h-4 text-green-500" />
                            )}
                          </div>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Dynamic Range</span>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{result.enhanced_metrics.dynamic_range_db.toFixed(1)} dB</span>
                            {result.enhanced_metrics.dynamic_range_db > result.original_metrics.dynamic_range_db && (
                              <TrendingUp className="w-4 h-4 text-green-500" />
                            )}
                          </div>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Peak Level</span>
                          <span className="font-medium">{result.enhanced_metrics.peak_level_db.toFixed(1)} dB</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Noise Level</span>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{result.enhanced_metrics.noise_level_db.toFixed(1)} dB</span>
                            {result.enhanced_metrics.noise_level_db < result.original_metrics.noise_level_db && (
                              <TrendingUp className="w-4 h-4 text-green-500" />
                            )}
                          </div>
                        </div>
                        {!result.enhanced_metrics.clipping_detected && result.original_metrics.clipping_detected && (
                          <div className="flex items-center gap-2 text-green-600">
                            <CheckCircle className="w-4 h-4" />
                            <span className="text-sm">Clipping Resolved</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>        <Ta
bsContent value="analyze" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Audio Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Waveform className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">
                  Upload and enhance an audio file to see detailed analysis
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Enhancement Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="font-semibold">Processing Options</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="noise-reduction">Noise Reduction</Label>
                    <Switch
                      id="noise-reduction"
                      checked={config.enable_noise_reduction}
                      onCheckedChange={(checked) => setConfig({...config, enable_noise_reduction: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="normalization">Normalization</Label>
                    <Switch
                      id="normalization"
                      checked={config.enable_normalization}
                      onCheckedChange={(checked) => setConfig({...config, enable_normalization: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="compression">Dynamic Compression</Label>
                    <Switch
                      id="compression"
                      checked={config.enable_compression}
                      onCheckedChange={(checked) => setConfig({...config, enable_compression: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="eq">Equalization</Label>
                    <Switch
                      id="eq"
                      checked={config.enable_eq}
                      onCheckedChange={(checked) => setConfig({...config, enable_eq: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="repair">Audio Repair</Label>
                    <Switch
                      id="repair"
                      checked={config.enable_repair}
                      onCheckedChange={(checked) => setConfig({...config, enable_repair: checked})}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="font-semibold">Audio Parameters</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="sample-rate">Target Sample Rate</Label>
                    <Select 
                      value={config.target_sample_rate.toString()} 
                      onValueChange={(value) => setConfig({...config, target_sample_rate: parseInt(value)})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="8000">8 kHz (Phone)</SelectItem>
                        <SelectItem value="16000">16 kHz (Voice)</SelectItem>
                        <SelectItem value="22050">22.05 kHz</SelectItem>
                        <SelectItem value="44100">44.1 kHz (CD)</SelectItem>
                        <SelectItem value="48000">48 kHz (Professional)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="bit-depth">Target Bit Depth</Label>
                    <Select 
                      value={config.target_bit_depth.toString()} 
                      onValueChange={(value) => setConfig({...config, target_bit_depth: parseInt(value)})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="16">16-bit</SelectItem>
                        <SelectItem value="24">24-bit</SelectItem>
                        <SelectItem value="32">32-bit</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="font-semibold">Processing Strength</h3>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="noise-strength">
                      Noise Reduction Strength: {config.noise_reduction_strength.toFixed(1)}
                    </Label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={config.noise_reduction_strength}
                      onChange={(e) => setConfig({...config, noise_reduction_strength: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                      disabled={!config.enable_noise_reduction}
                    />
                  </div>

                  <div>
                    <Label htmlFor="normalization-target">
                      Normalization Target: {config.normalization_target.toFixed(1)} dB
                    </Label>
                    <input
                      type="range"
                      min="-60"
                      max="0"
                      step="1"
                      value={config.normalization_target}
                      onChange={(e) => setConfig({...config, normalization_target: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                      disabled={!config.enable_normalization}
                    />
                  </div>

                  <div>
                    <Label htmlFor="compression-ratio">
                      Compression Ratio: {config.compression_ratio.toFixed(1)}:1
                    </Label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      step="0.1"
                      value={config.compression_ratio}
                      onChange={(e) => setConfig({...config, compression_ratio: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                      disabled={!config.enable_compression}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="font-semibold">Frequency Filtering</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="high-pass">
                      High-pass Filter: {config.high_pass_freq.toFixed(0)} Hz
                    </Label>
                    <input
                      type="range"
                      min="20"
                      max="1000"
                      step="10"
                      value={config.high_pass_freq}
                      onChange={(e) => setConfig({...config, high_pass_freq: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                      disabled={!config.enable_eq}
                    />
                  </div>

                  <div>
                    <Label htmlFor="low-pass">
                      Low-pass Filter: {config.low_pass_freq.toFixed(0)} Hz
                    </Label>
                    <input
                      type="range"
                      min="1000"
                      max="20000"
                      step="100"
                      value={config.low_pass_freq}
                      onChange={(e) => setConfig({...config, low_pass_freq: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                      disabled={!config.enable_eq}
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

export default AudioEnhancement;