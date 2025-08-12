import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { Mic, MicOff, Play, Pause, Stop, Download, Settings } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';

interface TranscriptionSegment {
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
  is_final: boolean;
  speaker_id?: string;
  language?: string;
}

interface StreamConfig {
  language: string;
  engine: string;
  mode: string;
  speaker_diarization: boolean;
  sample_rate: number;
  vad_aggressiveness: number;
}

export const RealtimeTranscription: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string>('');
  const [segments, setSegments] = useState<TranscriptionSegment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [duration, setDuration] = useState(0);
  const [statistics, setStatistics] = useState<any>(null);
  
  const [config, setConfig] = useState<StreamConfig>({
    language: 'auto',
    engine: 'FASTER_WHISPER',
    mode: 'VAD_BASED',
    speaker_diarization: false,
    sample_rate: 16000,
    vad_aggressiveness: 2
  });

  const wsRef = useRef<WebSocket | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef<Date | null>(null);

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  useEffect(() => {
    if (isRecording && !isPaused) {
      const updateDuration = () => {
        if (startTimeRef.current) {
          const elapsed = (Date.now() - startTimeRef.current.getTime()) / 1000;
          setDuration(elapsed);
        }
        animationRef.current = requestAnimationFrame(updateDuration);
      };
      updateDuration();
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }
  }, [isRecording, isPaused]);

  const startRecording = async () => {
    try {
      setError(null);
      
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: config.sample_rate,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      mediaStreamRef.current = stream;
      
      // Create audio context
      audioContextRef.current = new AudioContext({ sampleRate: config.sample_rate });
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      // Create processor for audio level monitoring
      processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      
      processorRef.current.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        
        // Calculate audio level
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
          sum += Math.abs(inputData[i]);
        }
        const average = sum / inputData.length;
        setAudioLevel(Math.min(100, average * 500));
        
        // Send audio to WebSocket
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          const int16Array = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            int16Array[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
          }
          wsRef.current.send(int16Array.buffer);
        }
      };
      
      source.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);
      
      // Create session
      const response = await fetch('/api/v1/streaming/session/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      const sessionData = await response.json();
      setSessionId(sessionData.session_id);
      
      // Connect WebSocket
      const ws = new WebSocket(`ws://localhost:8000/api/v1/streaming/ws/${sessionData.session_id}`);
      
      ws.onopen = () => {
        ws.send(JSON.stringify(config));
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'transcription':
            const segment = data.segment;
            setSegments(prev => [...prev, segment]);
            if (segment.is_final) {
              setTranscript(prev => prev + ' ' + segment.text);
            }
            break;
            
          case 'session_started':
            console.log('Session started:', data);
            break;
            
          case 'error':
            setError(data.message);
            break;
            
          case 'session_ended':
            setStatistics(data.statistics);
            break;
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error occurred');
      };
      
      ws.onclose = () => {
        console.log('WebSocket closed');
      };
      
      wsRef.current = ws;
      
      setIsRecording(true);
      startTimeRef.current = new Date();
      
    } catch (err: any) {
      setError(err.message || 'Failed to start recording');
    }
  };

  const stopRecording = async () => {
    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    // Close audio context
    if (audioContextRef.current) {
      await audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // Close WebSocket
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'stop' }));
      }
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Stop session
    if (sessionId) {
      try {
        const response = await fetch(`/api/v1/streaming/session/${sessionId}/stop`, {
          method: 'POST'
        });
        const result = await response.json();
        setStatistics(result.statistics);
      } catch (err) {
        console.error('Failed to stop session:', err);
      }
    }
    
    setIsRecording(false);
    setIsPaused(false);
    setAudioLevel(0);
  };

  const togglePause = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ 
        type: isPaused ? 'resume' : 'pause' 
      }));
    }
    setIsPaused(!isPaused);
  };

  const downloadTranscript = () => {
    const content = segments.map(seg => 
      `[${seg.start_time.toFixed(2)} - ${seg.end_time.toFixed(2)}] ${seg.text}`
    ).join('\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript_${sessionId || 'session'}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Real-time Transcription</span>
            <div className="flex items-center gap-2">
              {isRecording && (
                <Badge variant={isPaused ? "secondary" : "destructive"}>
                  {isPaused ? 'Paused' : 'Recording'}
                </Badge>
              )}
              <span className="text-sm text-gray-500">
                {formatDuration(duration)}
              </span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Configuration */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="language">Language</Label>
              <Select 
                value={config.language} 
                onValueChange={(value) => setConfig(prev => ({ ...prev, language: value }))}
                disabled={isRecording}
              >
                <SelectTrigger id="language">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Auto-detect</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                  <SelectItem value="zh">Chinese</SelectItem>
                  <SelectItem value="ja">Japanese</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="engine">Engine</Label>
              <Select 
                value={config.engine} 
                onValueChange={(value) => setConfig(prev => ({ ...prev, engine: value }))}
                disabled={isRecording}
              >
                <SelectTrigger id="engine">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="FASTER_WHISPER">Faster Whisper</SelectItem>
                  <SelectItem value="WHISPER_LOCAL">Whisper Local</SelectItem>
                  <SelectItem value="WHISPER_API">Whisper API</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="mode">Mode</Label>
              <Select 
                value={config.mode} 
                onValueChange={(value) => setConfig(prev => ({ ...prev, mode: value }))}
                disabled={isRecording}
              >
                <SelectTrigger id="mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="VAD_BASED">VAD Based</SelectItem>
                  <SelectItem value="CONTINUOUS">Continuous</SelectItem>
                  <SelectItem value="FIXED_DURATION">Fixed Duration</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="diarization"
                checked={config.speaker_diarization}
                onCheckedChange={(checked) => 
                  setConfig(prev => ({ ...prev, speaker_diarization: checked }))
                }
                disabled={isRecording}
              />
              <Label htmlFor="diarization">Speaker Diarization</Label>
            </div>
          </div>

          {/* Audio Level Indicator */}
          {isRecording && (
            <div className="space-y-2">
              <Label>Audio Level</Label>
              <Progress value={audioLevel} className="h-2" />
            </div>
          )}

          {/* Controls */}
          <div className="flex justify-center gap-4">
            {!isRecording ? (
              <Button 
                onClick={startRecording}
                size="lg"
                className="flex items-center gap-2"
              >
                <Mic className="h-5 w-5" />
                Start Recording
              </Button>
            ) : (
              <>
                <Button 
                  onClick={togglePause}
                  size="lg"
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  {isPaused ? (
                    <>
                      <Play className="h-5 w-5" />
                      Resume
                    </>
                  ) : (
                    <>
                      <Pause className="h-5 w-5" />
                      Pause
                    </>
                  )}
                </Button>
                <Button 
                  onClick={stopRecording}
                  size="lg"
                  variant="destructive"
                  className="flex items-center gap-2"
                >
                  <Stop className="h-5 w-5" />
                  Stop
                </Button>
              </>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Live Transcript */}
          {(transcript || segments.length > 0) && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Transcript</h3>
                <Button 
                  onClick={downloadTranscript}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Download
                </Button>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
                {segments.map((segment, index) => (
                  <div 
                    key={index} 
                    className={`mb-2 p-2 rounded ${
                      segment.is_final ? 'bg-white dark:bg-gray-800' : 'bg-blue-50 dark:bg-blue-900'
                    }`}
                  >
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>
                        {segment.start_time.toFixed(2)}s - {segment.end_time.toFixed(2)}s
                      </span>
                      {segment.speaker_id && (
                        <Badge variant="outline" className="text-xs">
                          Speaker {segment.speaker_id}
                        </Badge>
                      )}
                      <span>
                        Confidence: {(segment.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-sm">{segment.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Statistics */}
          {statistics && (
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-3">Session Statistics</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Duration:</span>
                  <p className="font-medium">{statistics.duration?.toFixed(2)}s</p>
                </div>
                <div>
                  <span className="text-gray-500">Audio Duration:</span>
                  <p className="font-medium">{statistics.audio_duration?.toFixed(2)}s</p>
                </div>
                <div>
                  <span className="text-gray-500">Segments:</span>
                  <p className="font-medium">{statistics.segment_count}</p>
                </div>
                <div>
                  <span className="text-gray-500">Word Count:</span>
                  <p className="font-medium">{statistics.word_count}</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};