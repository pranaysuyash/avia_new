import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  Mic, 
  MicOff, 
  Play, 
  Pause, 
  Square,
  Settings, 
  Activity,
  Users,
  Clock,
  Zap,
  Wifi,
  WifiOff,
  Volume2,
  VolumeX
} from 'lucide-react';

interface TranscriptionSegment {
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
  is_final: boolean;
  speaker_id?: string;
  language?: string;
  engine?: string;
}

interface StreamingStats {
  total_audio_duration: number;
  total_processing_time: number;
  segments_processed: number;
  average_latency: number;
  confidence_scores: number[];
  error_count: number;
}

interface StreamingConfig {
  engine: string;
  language: string;
  sample_rate: number;
  chunk_duration: number;
  buffer_duration: number;
  overlap_duration: number;
  confidence_threshold: number;
  enable_vad: boolean;
  enable_speaker_diarization: boolean;
  streaming_mode: string;
}

interface EngineOption {
  value: string;
  label: string;
  description: string;
  supports_streaming: boolean;
  languages: string[];
}

const RealTimeTranscription: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [segments, setSegments] = useState<TranscriptionSegment[]>([]);
  const [currentSegment, setCurrentSegment] = useState<TranscriptionSegment | null>(null);
  const [stats, setStats] = useState<StreamingStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [engines, setEngines] = useState<EngineOption[]>([]);
  
  // Configuration state
  const [config, setConfig] = useState<StreamingConfig>({
    engine: 'whisper_api',
    language: 'en',
    sample_rate: 16000,
    chunk_duration: 1.0,
    buffer_duration: 5.0,
    overlap_duration: 0.5,
    confidence_threshold: 0.7,
    enable_vad: true,
    enable_speaker_diarization: false,
    streaming_mode: 'continuous'
  });
  
  // Audio state
  const [audioLevel, setAudioLevel] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  
  // Refs
  const websocketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Load available engines on component mount
  useEffect(() => {
    loadEngines();
    return () => {
      cleanup();
    };
  }, []);

  const loadEngines = async () => {
    try {
      const response = await fetch('/api/v1/realtime-transcription/engines');
      if (response.ok) {
        const data = await response.json();
        setEngines(data.data.engines);
      }
    } catch (error) {
      console.error('Failed to load engines:', error);
    }
  };

  const cleanup = () => {
    if (websocketRef.current) {
      websocketRef.current.close();
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  };

  const createSession = async () => {
    try {
      const response = await fetch('/api/v1/realtime-transcription/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          config: config,
          session_name: `Session ${new Date().toLocaleTimeString()}`
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create session');
      }

      const data = await response.json();
      setSessionId(data.data.session_id);
      return data.data.session_id;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create session');
      throw error;
    }
  };

  const connectWebSocket = (sessionId: string) => {
    const wsUrl = `ws://localhost:8000/api/v1/realtime-transcription/ws/${sessionId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'connected':
          console.log('Session connected:', message.session_id);
          break;
          
        case 'transcription':
          const segment = message.data as TranscriptionSegment;
          if (segment.is_final) {
            setSegments(prev => [...prev, segment]);
            setCurrentSegment(null);
          } else {
            setCurrentSegment(segment);
          }
          break;
          
        case 'stats':
          setStats(message.data as StreamingStats);
          break;
          
        case 'error':
          setError(message.message);
          break;
          
        default:
          console.log('Unknown message type:', message.type);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      setError('WebSocket connection error');
      console.error('WebSocket error:', error);
    };

    websocketRef.current = ws;
  };

  const startRecording = async () => {
    try {
      // Create session if not exists
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        currentSessionId = await createSession();
      }

      // Connect WebSocket
      if (!isConnected) {
        connectWebSocket(currentSessionId);
      }

      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: config.sample_rate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });

      streamRef.current = stream;

      // Setup audio context for visualization
      const audioContext = new AudioContext({ sampleRate: config.sample_rate });
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      source.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      // Setup media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && websocketRef.current?.readyState === WebSocket.OPEN) {
          // Convert blob to base64 and send
          const reader = new FileReader();
          reader.onload = () => {
            const base64Data = (reader.result as string).split(',')[1];
            websocketRef.current?.send(JSON.stringify({
              type: 'audio_data',
              data: base64Data
            }));
          };
          reader.readAsDataURL(event.data);
        }
      };

      mediaRecorder.start(config.chunk_duration * 1000); // Convert to milliseconds
      mediaRecorderRef.current = mediaRecorder;

      // Start audio level monitoring
      startAudioLevelMonitoring();

      setIsRecording(true);
      setError(null);

      // Send start recording signal
      websocketRef.current?.send(JSON.stringify({
        type: 'start_recording'
      }));

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to start recording');
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    // Send stop recording signal
    websocketRef.current?.send(JSON.stringify({
      type: 'stop_recording'
    }));

    setIsRecording(false);
    setAudioLevel(0);
  };

  const startAudioLevelMonitoring = () => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const updateAudioLevel = () => {
      if (!analyserRef.current) return;
      
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
      setAudioLevel(average / 255 * 100);
      
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    };
    
    updateAudioLevel();
  };

  const toggleMute = () => {
    if (streamRef.current) {
      streamRef.current.getAudioTracks().forEach(track => {
        track.enabled = isMuted;
      });
      setIsMuted(!isMuted);
    }
  };

  const clearTranscription = () => {
    setSegments([]);
    setCurrentSegment(null);
    setStats(null);
  };

  const exportTranscription = () => {
    const fullText = segments.map(segment => segment.text).join(' ');
    const exportData = {
      transcript: fullText,
      segments: segments,
      stats: stats,
      config: config,
      exported_at: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `realtime-transcript-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getFullTranscript = () => {
    const allText = segments.map(segment => segment.text).join(' ');
    if (currentSegment) {
      return allText + ' ' + currentSegment.text;
    }
    return allText;
  };

  const getAverageConfidence = () => {
    if (segments.length === 0) return 0;
    const total = segments.reduce((sum, segment) => sum + segment.confidence, 0);
    return total / segments.length;
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center space-x-2">
        <Activity className="h-6 w-6 text-red-600" />
        <h1 className="text-2xl font-bold">Real-Time Transcription</h1>
        <div className="flex items-center space-x-2 ml-auto">
          <div className={`flex items-center space-x-1 ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
            {isConnected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
            <span className="text-sm">{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Control Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Controls</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Recording Controls */}
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-4">
                <Button
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={!isConnected && !sessionId}
                  size="lg"
                  className={`${isRecording ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}`}
                >
                  {isRecording ? (
                    <>
                      <Square className="h-5 w-5 mr-2" />
                      Stop
                    </>
                  ) : (
                    <>
                      <Mic className="h-5 w-5 mr-2" />
                      Start
                    </>
                  )}
                </Button>

                <Button
                  onClick={toggleMute}
                  disabled={!isRecording}
                  variant="outline"
                  size="lg"
                >
                  {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                </Button>
              </div>

              {/* Audio Level Indicator */}
              <div className="space-y-2">
                <Label>Audio Level</Label>
                <div className="flex items-center space-x-2">
                  <Progress value={audioLevel} className="flex-1" />
                  <span className="text-sm text-gray-500">{Math.round(audioLevel)}%</span>
                </div>
              </div>
            </div>

            <Separator />

            {/* Configuration */}
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="basic">Basic</TabsTrigger>
                <TabsTrigger value="advanced">Advanced</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4">
                <div>
                  <Label htmlFor="engine">Engine</Label>
                  <Select 
                    value={config.engine} 
                    onValueChange={(value) => setConfig(prev => ({ ...prev, engine: value }))}
                    disabled={isRecording}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {engines.map(engine => (
                        <SelectItem key={engine.value} value={engine.value}>
                          {engine.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="language">Language</Label>
                  <Select 
                    value={config.language} 
                    onValueChange={(value) => setConfig(prev => ({ ...prev, language: value }))}
                    disabled={isRecording}
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
                      <SelectItem value="pt">Portuguese</SelectItem>
                      <SelectItem value="ru">Russian</SelectItem>
                      <SelectItem value="ja">Japanese</SelectItem>
                      <SelectItem value="ko">Korean</SelectItem>
                      <SelectItem value="zh">Chinese</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="streaming-mode">Streaming Mode</Label>
                  <Select 
                    value={config.streaming_mode} 
                    onValueChange={(value) => setConfig(prev => ({ ...prev, streaming_mode: value }))}
                    disabled={isRecording}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="continuous">Continuous</SelectItem>
                      <SelectItem value="push_to_talk">Push to Talk</SelectItem>
                      <SelectItem value="voice_activity">Voice Activity</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>

              <TabsContent value="advanced" className="space-y-4">
                <div>
                  <Label htmlFor="confidence-threshold">Confidence Threshold</Label>
                  <Input
                    id="confidence-threshold"
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.confidence_threshold}
                    onChange={(e) => setConfig(prev => ({ ...prev, confidence_threshold: parseFloat(e.target.value) }))}
                    disabled={isRecording}
                  />
                </div>

                <div>
                  <Label htmlFor="chunk-duration">Chunk Duration (seconds)</Label>
                  <Input
                    id="chunk-duration"
                    type="number"
                    min="0.1"
                    max="5"
                    step="0.1"
                    value={config.chunk_duration}
                    onChange={(e) => setConfig(prev => ({ ...prev, chunk_duration: parseFloat(e.target.value) }))}
                    disabled={isRecording}
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="enable-vad"
                    checked={config.enable_vad}
                    onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enable_vad: checked }))}
                    disabled={isRecording}
                  />
                  <Label htmlFor="enable-vad">Voice Activity Detection</Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="enable-speaker-diarization"
                    checked={config.enable_speaker_diarization}
                    onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enable_speaker_diarization: checked }))}
                    disabled={isRecording}
                  />
                  <Label htmlFor="enable-speaker-diarization">Speaker Diarization</Label>
                </div>
              </TabsContent>
            </Tabs>

            <Separator />

            {/* Action Buttons */}
            <div className="space-y-2">
              <Button onClick={clearTranscription} variant="outline" className="w-full">
                Clear Transcription
              </Button>
              <Button onClick={exportTranscription} variant="outline" className="w-full" disabled={segments.length === 0}>
                Export Transcript
              </Button>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Transcription Display */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Zap className="h-5 w-5" />
                <span>Live Transcription</span>
              </div>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <span>{segments.length} segments</span>
                <span>{getFullTranscript().split(' ').length} words</span>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Live Transcript */}
              <div className="min-h-[300px] max-h-[400px] overflow-y-auto p-4 bg-gray-50 rounded-lg">
                {segments.length === 0 && !currentSegment ? (
                  <div className="text-center text-gray-500 py-12">
                    <Mic className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Start recording to see live transcription</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {segments.map((segment, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        {segment.speaker_id && (
                          <Badge variant="secondary" className="text-xs">
                            {segment.speaker_id}
                          </Badge>
                        )}
                        <div className="flex-1">
                          <p className="text-gray-800">{segment.text}</p>
                          <div className="flex items-center space-x-2 text-xs text-gray-500 mt-1">
                            <span>{segment.start_time.toFixed(1)}s - {segment.end_time.toFixed(1)}s</span>
                            <span>•</span>
                            <span>{(segment.confidence * 100).toFixed(1)}% confidence</span>
                            {segment.engine && (
                              <>
                                <span>•</span>
                                <span>{segment.engine}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    {currentSegment && (
                      <div className="flex items-start space-x-2 opacity-70">
                        <Badge variant="outline" className="text-xs animate-pulse">
                          Live
                        </Badge>
                        <div className="flex-1">
                          <p className="text-gray-600 italic">{currentSegment.text}</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Statistics */}
              {stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-blue-50 rounded-lg">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {stats.segments_processed}
                    </div>
                    <div className="text-xs text-gray-500">Segments</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {stats.average_latency.toFixed(1)}ms
                    </div>
                    <div className="text-xs text-gray-500">Avg Latency</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {(getAverageConfidence() * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">Confidence</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {stats.total_audio_duration.toFixed(1)}s
                    </div>
                    <div className="text-xs text-gray-500">Duration</div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default RealTimeTranscription;