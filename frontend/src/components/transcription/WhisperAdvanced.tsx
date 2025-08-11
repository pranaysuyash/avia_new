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
import { Textarea } from '../ui/textarea';
import { 
  Upload, 
  Play, 
  Pause,
  Download,
  Settings,
  Mic,
  Globe,
  Brain,
  Zap,
  FileText,
  BarChart3,
  Clock,
  Volume2,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Copy,
  Edit,
  Sliders,
  Users,
  Languages,
  Waveform,
  TrendingUp,
  FileAudio,
  Layers
} from 'lucide-react';

interface TranscriptionResult {
  text: string;
  language?: string;
  language_confidence?: number;
  segments: Array<{
    id: number;
    start: number;
    end: number;
    text: string;
    confidence?: number;
    speaker_id?: string;
  }>;
  words?: Array<{
    word: string;
    start: number;
    end: number;
    confidence: number;
  }>;
  confidence_analysis?: {
    overall_confidence: number;
    preprocessing_quality: number;
    quality_improvement: number;
  };
  processing_time: number;
  model_used: string;
  config_used: any;
}

interface LanguageDetectionResult {
  detected_language: string;
  confidence: number;
  alternative_languages: Array<{[key: string]: number}>;
  language_segments?: Array<any>;
}

interface BatchTranscriptionResult {
  results: Array<{
    index: number;
    filename: string;
    status: 'success' | 'error';
    result?: any;
    error?: string;
  }>;
  summary: {
    total_files: number;
    successful: number;
    failed: number;
    total_words: number;
    average_processing_time: number;
    total_processing_time: number;
  };
  total_processing_time: number;
}

interface WhisperConfig {
  model: string;
  language?: string;
  prompt?: string;
  response_format: string;
  temperature: number;
  enable_language_detection: boolean;
  enable_confidence_analysis: boolean;
  enable_custom_vocabulary: boolean;
  confidence_threshold: number;
  chunk_length_s: number;
  enable_word_timestamps: boolean;
  enable_speaker_detection: boolean;
}

interface CustomVocabularyConfig {
  vocabulary_terms: string[];
  domain_specific_terms: string[];
  proper_nouns: string[];
  technical_terms: string[];
  boost_factor: number;
}

interface PromptConfig {
  context_prompt?: string;
  style_prompt?: string;
  domain_prompt?: string;
  format_prompt?: string;
}

const WhisperAdvanced: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [result, setResult] = useState<TranscriptionResult | null>(null);
  const [batchResult, setBatchResult] = useState<BatchTranscriptionResult | null>(null);
  const [languageResult, setLanguageResult] = useState<LanguageDetectionResult | null>(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isDetectingLanguage, setIsDetectingLanguage] = useState(false);
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [presets, setPresets] = useState<any[]>([]);
  const [models, setModels] = useState<any>(null);
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [processingMode, setProcessingMode] = useState<'single' | 'batch' | 'language'>('single');
  
  // Configuration state
  const [config, setConfig] = useState<WhisperConfig>({
    model: 'whisper-1',
    language: undefined,
    prompt: undefined,
    response_format: 'json',
    temperature: 0.0,
    enable_language_detection: true,
    enable_confidence_analysis: true,
    enable_custom_vocabulary: false,
    confidence_threshold: 0.8,
    chunk_length_s: 30,
    enable_word_timestamps: true,
    enable_speaker_detection: false
  });
  
  // Custom vocabulary state
  const [vocabularyConfig, setVocabularyConfig] = useState<CustomVocabularyConfig>({
    vocabulary_terms: [],
    domain_specific_terms: [],
    proper_nouns: [],
    technical_terms: [],
    boost_factor: 1.5
  });
  
  // Prompt configuration state
  const [promptConfig, setPromptConfig] = useState<PromptConfig>({
    context_prompt: '',
    style_prompt: '',
    domain_prompt: '',
    format_prompt: ''
  });
  
  // Audio playback
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Text input for vocabulary
  const [vocabularyInput, setVocabularyInput] = useState('');
  const [domainTermsInput, setDomainTermsInput] = useState('');
  const [properNounsInput, setProperNounsInput] = useState('');
  const [technicalTermsInput, setTechnicalTermsInput] = useState('');

  useEffect(() => {
    loadPresets();
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

  const loadPresets = async () => {
    try {
      const response = await fetch('/api/v1/whisper-advanced/presets');
      if (response.ok) {
        const data = await response.json();
        setPresets(data.data.presets);
      }
    } catch (error) {
      console.error('Failed to load presets:', error);
    }
  };

  const loadModels = async () => {
    try {
      const response = await fetch('/api/v1/whisper-advanced/models');
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
      // Check file size (25MB limit)
      if (file.size > 25 * 1024 * 1024) {
        setError('File size exceeds 25MB limit for Whisper API');
        return;
      }
      
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

  const updateVocabularyConfig = () => {
    setVocabularyConfig({
      vocabulary_terms: vocabularyInput.split(',').map(s => s.trim()).filter(s => s),
      domain_specific_terms: domainTermsInput.split(',').map(s => s.trim()).filter(s => s),
      proper_nouns: properNounsInput.split(',').map(s => s.trim()).filter(s => s),
      technical_terms: technicalTermsInput.split(',').map(s => s.trim()).filter(s => s),
      boost_factor: vocabularyConfig.boost_factor
    });
  };

  const handleTranscribe = async () => {
    if (!selectedFile) {
      setError('Please select an audio file');
      return;
    }

    setIsTranscribing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('audio_file', selectedFile);
      formData.append('config', JSON.stringify(config));
      
      if (config.enable_custom_vocabulary) {
        updateVocabularyConfig();
        formData.append('custom_vocabulary', JSON.stringify(vocabularyConfig));
      }
      
      // Add prompt configuration if any prompts are provided
      const hasPrompts = Object.values(promptConfig).some(prompt => prompt && prompt.trim());
      if (hasPrompts) {
        formData.append('prompt_config', JSON.stringify(promptConfig));
      }

      const response = await fetch('/api/v1/whisper-advanced/transcribe', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to transcribe audio');
      }

      const data = await response.json();
      setResult(data.data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleLanguageDetection = async () => {
    if (!selectedFile) {
      setError('Please select an audio file');
      return;
    }

    setIsDetectingLanguage(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('audio_file', selectedFile);

      const response = await fetch('/api/v1/whisper-advanced/detect-language', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to detect language');
      }

      const data = await response.json();
      setLanguageResult(data.data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsDetectingLanguage(false);
    }
  };

  const handleBatchTranscribe = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select audio files for batch processing');
      return;
    }

    setIsBatchProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });
      formData.append('config', JSON.stringify(config));

      const response = await fetch('/api/v1/whisper-advanced/batch-transcribe', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process batch transcription');
      }

      const data = await response.json();
      setBatchResult(data.data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsBatchProcessing(false);
    }
  };

  const handleMultipleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length > 10) {
      setError('Maximum 10 files allowed for batch processing');
      return;
    }
    
    // Check total size
    const totalSize = files.reduce((sum, file) => sum + file.size, 0);
    if (totalSize > 250 * 1024 * 1024) { // 250MB total limit
      setError('Total file size exceeds 250MB limit');
      return;
    }
    
    setSelectedFiles(files);
    setBatchResult(null);
    setError(null);
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

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.9) return 'High';
    if (confidence >= 0.7) return 'Medium';
    return 'Low';
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-6 w-6" />
            Whisper Advanced Integration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={processingMode} onValueChange={(value) => setProcessingMode(value as any)}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="single" className="flex items-center gap-2">
                <FileAudio className="h-4 w-4" />
                Single File
              </TabsTrigger>
              <TabsTrigger value="batch" className="flex items-center gap-2">
                <Layers className="h-4 w-4" />
                Batch Processing
              </TabsTrigger>
              <TabsTrigger value="language" className="flex items-center gap-2">
                <Languages className="h-4 w-4" />
                Language Detection
              </TabsTrigger>
            </TabsList>

            {/* Single File Processing */}
            <TabsContent value="single" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* File Upload */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Upload className="h-5 w-5" />
                      Audio Upload
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="audio/*"
                        onChange={handleFileSelect}
                        className="hidden"
                      />
                      <Button
                        onClick={() => fileInputRef.current?.click()}
                        variant="outline"
                        className="mb-2"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Select Audio File
                      </Button>
                      <p className="text-sm text-gray-500">
                        Supports MP3, WAV, M4A, FLAC (max 25MB)
                      </p>
                    </div>
                    
                    {selectedFile && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="font-medium">{selectedFile.name}</p>
                        <p className="text-sm text-gray-500">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                        {selectedFile && (
                          <audio
                            ref={audioRef}
                            src={URL.createObjectURL(selectedFile)}
                            className="w-full mt-2"
                            controls
                          />
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Configuration */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Settings className="h-5 w-5" />
                      Configuration
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>Preset Configuration</Label>
                      <Select value={selectedPreset} onValueChange={handlePresetChange}>
                        <SelectTrigger>
                          <SelectValue placeholder="Choose a preset" />
                        </SelectTrigger>
                        <SelectContent>
                          {presets.map((preset) => (
                            <SelectItem key={preset.name} value={preset.name}>
                              {preset.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Model</Label>
                        <Select
                          value={config.model}
                          onValueChange={(value) => setConfig({...config, model: value})}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="whisper-1">Whisper v1</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Language</Label>
                        <Select
                          value={config.language || 'auto'}
                          onValueChange={(value) => setConfig({...config, language: value === 'auto' ? undefined : value})}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="auto">Auto-detect</SelectItem>
                            <SelectItem value="en">English</SelectItem>
                            <SelectItem value="es">Spanish</SelectItem>
                            <SelectItem value="fr">French</SelectItem>
                            <SelectItem value="de">German</SelectItem>
                            <SelectItem value="it">Italian</SelectItem>
                            <SelectItem value="pt">Portuguese</SelectItem>
                            <SelectItem value="ru">Russian</SelectItem>
                            <SelectItem value="ja">Japanese</SelectItem>
                            <SelectItem value="ko">Korean</SelectItem>
                            <SelectItem value="zh">Chinese</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div>
                      <Label>Temperature: {config.temperature}</Label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={config.temperature}
                        onChange={(e) => setConfig({...config, temperature: parseFloat(e.target.value)})}
                        className="w-full"
                      />
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Language Detection</Label>
                        <Switch
                          checked={config.enable_language_detection}
                          onCheckedChange={(checked) => setConfig({...config, enable_language_detection: checked})}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Confidence Analysis</Label>
                        <Switch
                          checked={config.enable_confidence_analysis}
                          onCheckedChange={(checked) => setConfig({...config, enable_confidence_analysis: checked})}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Word Timestamps</Label>
                        <Switch
                          checked={config.enable_word_timestamps}
                          onCheckedChange={(checked) => setConfig({...config, enable_word_timestamps: checked})}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Speaker Detection</Label>
                        <Switch
                          checked={config.enable_speaker_detection}
                          onCheckedChange={(checked) => setConfig({...config, enable_speaker_detection: checked})}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Custom Vocabulary</Label>
                        <Switch
                          checked={config.enable_custom_vocabulary}
                          onCheckedChange={(checked) => setConfig({...config, enable_custom_vocabulary: checked})}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Custom Vocabulary */}
              {config.enable_custom_vocabulary && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Custom Vocabulary
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label>General Terms</Label>
                        <Textarea
                          placeholder="Enter terms separated by commas"
                          value={vocabularyInput}
                          onChange={(e) => setVocabularyInput(e.target.value)}
                        />
                      </div>
                      <div>
                        <Label>Domain-Specific Terms</Label>
                        <Textarea
                          placeholder="Enter domain terms separated by commas"
                          value={domainTermsInput}
                          onChange={(e) => setDomainTermsInput(e.target.value)}
                        />
                      </div>
                      <div>
                        <Label>Proper Nouns</Label>
                        <Textarea
                          placeholder="Enter proper nouns separated by commas"
                          value={properNounsInput}
                          onChange={(e) => setProperNounsInput(e.target.value)}
                        />
                      </div>
                      <div>
                        <Label>Technical Terms</Label>
                        <Textarea
                          placeholder="Enter technical terms separated by commas"
                          value={technicalTermsInput}
                          onChange={(e) => setTechnicalTermsInput(e.target.value)}
                        />
                      </div>
                    </div>
                    <div>
                      <Label>Boost Factor: {vocabularyConfig.boost_factor}</Label>
                      <input
                        type="range"
                        min="1"
                        max="3"
                        step="0.1"
                        value={vocabularyConfig.boost_factor}
                        onChange={(e) => setVocabularyConfig({...vocabularyConfig, boost_factor: parseFloat(e.target.value)})}
                        className="w-full"
                      />
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Prompt Configuration */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Edit className="h-5 w-5" />
                    Prompt Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Context Prompt</Label>
                      <Textarea
                        placeholder="Provide context for better transcription"
                        value={promptConfig.context_prompt || ''}
                        onChange={(e) => setPromptConfig({...promptConfig, context_prompt: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label>Style Prompt</Label>
                      <Textarea
                        placeholder="Specify transcription style preferences"
                        value={promptConfig.style_prompt || ''}
                        onChange={(e) => setPromptConfig({...promptConfig, style_prompt: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label>Domain Prompt</Label>
                      <Textarea
                        placeholder="Specify domain or subject matter"
                        value={promptConfig.domain_prompt || ''}
                        onChange={(e) => setPromptConfig({...promptConfig, domain_prompt: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label>Format Prompt</Label>
                      <Textarea
                        placeholder="Specify output format preferences"
                        value={promptConfig.format_prompt || ''}
                        onChange={(e) => setPromptConfig({...promptConfig, format_prompt: e.target.value})}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <Button
                  onClick={handleTranscribe}
                  disabled={!selectedFile || isTranscribing}
                  className="flex-1"
                >
                  {isTranscribing ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Transcribing...
                    </>
                  ) : (
                    <>
                      <Mic className="h-4 w-4 mr-2" />
                      Transcribe Audio
                    </>
                  )}
                </Button>
              </div>

              {/* Results */}
              {result && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      Transcription Results
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <div className="text-sm text-blue-600">Processing Time</div>
                        <div className="font-semibold">{result.processing_time.toFixed(2)}s</div>
                      </div>
                      {result.language && (
                        <div className="bg-green-50 p-3 rounded-lg">
                          <div className="text-sm text-green-600">Language</div>
                          <div className="font-semibold">
                            {result.language}
                            {result.language_confidence && (
                              <span className="text-sm ml-1">
                                ({(result.language_confidence * 100).toFixed(1)}%)
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                      {result.confidence_analysis && (
                        <div className="bg-purple-50 p-3 rounded-lg">
                          <div className="text-sm text-purple-600">Overall Confidence</div>
                          <div className="font-semibold">
                            {(result.confidence_analysis.overall_confidence * 100).toFixed(1)}%
                          </div>
                        </div>
                      )}
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <Label>Transcription Text</Label>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(result.text)}
                        >
                          <Copy className="h-4 w-4 mr-1" />
                          Copy
                        </Button>
                      </div>
                      <Textarea
                        value={result.text}
                        readOnly
                        className="min-h-[200px]"
                      />
                    </div>

                    {result.segments && result.segments.length > 0 && (
                      <div>
                        <Label>Segments</Label>
                        <div className="max-h-60 overflow-y-auto space-y-2">
                          {result.segments.map((segment) => (
                            <div key={segment.id} className="bg-gray-50 p-3 rounded-lg">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm text-gray-500">
                                  {formatTime(segment.start)} - {formatTime(segment.end)}
                                </span>
                                {segment.confidence && (
                                  <Badge variant={segment.confidence > 0.8 ? 'default' : 'secondary'}>
                                    {(segment.confidence * 100).toFixed(1)}%
                                  </Badge>
                                )}
                                {segment.speaker_id && (
                                  <Badge variant="outline">
                                    <Users className="h-3 w-3 mr-1" />
                                    {segment.speaker_id}
                                  </Badge>
                                )}
                              </div>
                              <p className="text-sm">{segment.text}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {result.confidence_analysis && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-medium mb-2">Quality Analysis</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">Overall Confidence:</span>
                            <span className="ml-2 font-medium">
                              {(result.confidence_analysis.overall_confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Preprocessing Quality:</span>
                            <span className="ml-2 font-medium">
                              {(result.confidence_analysis.preprocessing_quality * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Quality Improvement:</span>
                            <span className="ml-2 font-medium">
                              {(result.confidence_analysis.quality_improvement * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Batch Processing */}
            <TabsContent value="batch" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Layers className="h-5 w-5" />
                    Batch Processing
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <input
                      type="file"
                      accept="audio/*"
                      multiple
                      onChange={handleMultipleFileSelect}
                      className="hidden"
                      id="batch-file-input"
                    />
                    <Button
                      onClick={() => document.getElementById('batch-file-input')?.click()}
                      variant="outline"
                      className="mb-2"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      Select Multiple Audio Files
                    </Button>
                    <p className="text-sm text-gray-500">
                      Select up to 10 audio files (max 250MB total)
                    </p>
                  </div>

                  {selectedFiles.length > 0 && (
                    <div className="space-y-2">
                      <Label>Selected Files ({selectedFiles.length})</Label>
                      <div className="max-h-40 overflow-y-auto space-y-1">
                        {selectedFiles.map((file, index) => (
                          <div key={index} className="bg-gray-50 p-2 rounded flex justify-between items-center">
                            <span className="text-sm">{file.name}</span>
                            <span className="text-xs text-gray-500">
                              {(file.size / 1024 / 1024).toFixed(2)} MB
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <Button
                    onClick={handleBatchTranscribe}
                    disabled={selectedFiles.length === 0 || isBatchProcessing}
                    className="w-full"
                  >
                    {isBatchProcessing ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Processing Batch...
                      </>
                    ) : (
                      <>
                        <Layers className="h-4 w-4 mr-2" />
                        Process Batch
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {batchResult && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5" />
                      Batch Results
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-blue-50 p-3 rounded-lg text-center">
                        <div className="text-2xl font-bold text-blue-600">{batchResult.summary.total_files}</div>
                        <div className="text-sm text-blue-600">Total Files</div>
                      </div>
                      <div className="bg-green-50 p-3 rounded-lg text-center">
                        <div className="text-2xl font-bold text-green-600">{batchResult.summary.successful}</div>
                        <div className="text-sm text-green-600">Successful</div>
                      </div>
                      <div className="bg-red-50 p-3 rounded-lg text-center">
                        <div className="text-2xl font-bold text-red-600">{batchResult.summary.failed}</div>
                        <div className="text-sm text-red-600">Failed</div>
                      </div>
                      <div className="bg-purple-50 p-3 rounded-lg text-center">
                        <div className="text-2xl font-bold text-purple-600">{batchResult.summary.total_words}</div>
                        <div className="text-sm text-purple-600">Total Words</div>
                      </div>
                    </div>

                    <div>
                      <Label>Processing Results</Label>
                      <div className="max-h-60 overflow-y-auto space-y-2">
                        {batchResult.results.map((result, index) => (
                          <div key={index} className="bg-gray-50 p-3 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">{result.filename}</span>
                              <Badge variant={result.status === 'success' ? 'default' : 'destructive'}>
                                {result.status}
                              </Badge>
                            </div>
                            {result.status === 'success' && result.result && (
                              <div className="text-sm space-y-1">
                                <div>Language: {result.result.language}</div>
                                <div>Words: {result.result.word_count}</div>
                                <div>Processing Time: {result.result.processing_time.toFixed(2)}s</div>
                                <div>Confidence: {(result.result.confidence_score * 100).toFixed(1)}%</div>
                              </div>
                            )}
                            {result.status === 'error' && (
                              <div className="text-sm text-red-600">{result.error}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Language Detection */}
            <TabsContent value="language" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Languages className="h-5 w-5" />
                    Language Detection
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <input
                      type="file"
                      accept="audio/*"
                      onChange={handleFileSelect}
                      className="hidden"
                      id="language-file-input"
                    />
                    <Button
                      onClick={() => document.getElementById('language-file-input')?.click()}
                      variant="outline"
                      className="mb-2"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      Select Audio File
                    </Button>
                    <p className="text-sm text-gray-500">
                      Upload audio to detect language
                    </p>
                  </div>

                  {selectedFile && (
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-sm text-gray-500">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  )}

                  <Button
                    onClick={handleLanguageDetection}
                    disabled={!selectedFile || isDetectingLanguage}
                    className="w-full"
                  >
                    {isDetectingLanguage ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Detecting Language...
                      </>
                    ) : (
                      <>
                        <Globe className="h-4 w-4 mr-2" />
                        Detect Language
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {languageResult && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      Language Detection Results
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-lg font-semibold text-green-800">
                        Detected Language: {languageResult.detected_language.toUpperCase()}
                      </div>
                      <div className="text-green-600">
                        Confidence: {(languageResult.confidence * 100).toFixed(1)}%
                      </div>
                    </div>

                    {languageResult.alternative_languages && languageResult.alternative_languages.length > 0 && (
                      <div>
                        <Label>Alternative Languages</Label>
                        <div className="space-y-2">
                          {languageResult.alternative_languages.slice(0, 5).map((langObj, index) => {
                            const [lang, confidence] = Object.entries(langObj)[0];
                            return (
                              <div key={index} className="flex justify-between items-center bg-gray-50 p-2 rounded">
                                <span className="font-medium">{lang.toUpperCase()}</span>
                                <span className="text-sm text-gray-600">
                                  {(confidence * 100).toFixed(1)}%
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>

          {error && (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                {error}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default WhisperAdvanced;