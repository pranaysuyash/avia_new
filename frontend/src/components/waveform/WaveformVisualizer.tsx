import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Slider,
  IconButton,
  Tooltip,
  LinearProgress,
  Chip,
  Menu,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  VolumeUp,
  VolumeDown,
  Fullscreen,
  Download,
  Settings,
  Timeline,
  GraphicEq,
} from '@mui/icons-material';

interface WaveformSegment {
  start: number;
  end: number;
  speaker?: string;
  text?: string;
  type?: 'speech' | 'silence' | 'music' | 'noise';
}

interface WaveformVisualizerProps {
  audioUrl: string;
  segments?: WaveformSegment[];
  transcriptSegments?: Array<{
    start: number;
    end: number;
    text: string;
    speaker?: string;
  }>;
  onTimeUpdate?: (currentTime: number) => void;
  onSegmentClick?: (segment: WaveformSegment) => void;
  height?: number;
  showControls?: boolean;
  showTimeline?: boolean;
  showSpeakers?: boolean;
}

const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  audioUrl,
  segments = [],
  transcriptSegments = [],
  onTimeUpdate,
  onSegmentClick,
  height = 200,
  showControls = true,
  showTimeline = true,
  showSpeakers = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const animationRef = useRef<number>();
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [waveformData, setWaveformData] = useState<number[]>([]);
  const [settingsAnchor, setSettingsAnchor] = useState<null | HTMLElement>(null);
  const [showSegments, setShowSegments] = useState(true);
  const [showTranscript, setShowTranscript] = useState(true);
  const [showSpeakersState, setShowSpeakersState] = useState(showSpeakers);
  const [error, setError] = useState<string | null>(null);

  // Generate waveform data from audio
  const generateWaveform = useCallback(async () => {
    if (!audioUrl) return;

    try {
      setIsLoading(true);
      setError(null);

      // Create audio context for waveform analysis
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // Fetch audio data
      const response = await fetch(audioUrl);
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      
      // Extract waveform data
      const channelData = audioBuffer.getChannelData(0);
      const samples = 1000; // Number of samples for visualization
      const blockSize = Math.floor(channelData.length / samples);
      const waveform: number[] = [];
      
      for (let i = 0; i < samples; i++) {
        let sum = 0;
        for (let j = 0; j < blockSize; j++) {
          sum += Math.abs(channelData[i * blockSize + j]);
        }
        waveform.push(sum / blockSize);
      }
      
      setWaveformData(waveform);
      setDuration(audioBuffer.duration);
      
    } catch (err) {
      console.error('Error generating waveform:', err);
      setError('Failed to generate waveform visualization');
    } finally {
      setIsLoading(false);
    }
  }, [audioUrl]);

  // Draw waveform on canvas
  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || waveformData.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height: canvasHeight } = canvas;
    const centerY = canvasHeight / 2;
    const barWidth = width / waveformData.length;

    // Clear canvas
    ctx.clearRect(0, 0, width, canvasHeight);

    // Draw waveform bars
    waveformData.forEach((amplitude, index) => {
      const barHeight = amplitude * centerY * 0.8;
      const x = index * barWidth;
      
      // Determine color based on current time and segments
      let color = '#3f51b5'; // Default blue
      const timeAtIndex = (index / waveformData.length) * duration;
      
      if (timeAtIndex <= currentTime) {
        color = '#4caf50'; // Green for played portion
      }
      
      // Color based on segments
      if (showSegments && segments.length > 0) {
        const segment = segments.find(s => timeAtIndex >= s.start && timeAtIndex <= s.end);
        if (segment) {
          switch (segment.type) {
            case 'speech':
              color = timeAtIndex <= currentTime ? '#2e7d32' : '#4caf50';
              break;
            case 'silence':
              color = timeAtIndex <= currentTime ? '#757575' : '#bdbdbd';
              break;
            case 'music':
              color = timeAtIndex <= currentTime ? '#7b1fa2' : '#9c27b0';
              break;
            case 'noise':
              color = timeAtIndex <= currentTime ? '#d32f2f' : '#f44336';
              break;
          }
        }
      }
      
      ctx.fillStyle = color;
      ctx.fillRect(x, centerY - barHeight / 2, barWidth - 1, barHeight);
    });

    // Draw current time indicator
    const progressX = (currentTime / duration) * width;
    ctx.strokeStyle = '#ff5722';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(progressX, 0);
    ctx.lineTo(progressX, canvasHeight);
    ctx.stroke();

    // Draw segment markers
    if (showSegments && segments.length > 0) {
      segments.forEach(segment => {
        const startX = (segment.start / duration) * width;
        const endX = (segment.end / duration) * width;
        
        // Draw segment boundary
        ctx.strokeStyle = '#ff9800';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(startX, 0);
        ctx.lineTo(startX, canvasHeight);
        ctx.stroke();
        
        // Draw speaker label if available
        if (showSpeakersState && segment.speaker) {
          ctx.fillStyle = '#333';
          ctx.font = '12px Arial';
          ctx.fillText(segment.speaker, startX + 5, 15);
        }
      });
      ctx.setLineDash([]); // Reset dash
    }

    // Draw transcript segments
    if (showTranscript && transcriptSegments.length > 0) {
      transcriptSegments.forEach((segment, index) => {
        const startX = (segment.start / duration) * width;
        const endX = (segment.end / duration) * width;
        
        // Highlight current transcript segment
        if (currentTime >= segment.start && currentTime <= segment.end) {
          ctx.fillStyle = 'rgba(255, 193, 7, 0.3)';
          ctx.fillRect(startX, 0, endX - startX, canvasHeight);
        }
      });
    }
  }, [waveformData, currentTime, duration, segments, transcriptSegments, showSegments, showTranscript, showSpeakersState]);

  // Handle canvas click for seeking
  const handleCanvasClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const audio = audioRef.current;
    if (!canvas || !audio || duration === 0) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const clickTime = (x / canvas.width) * duration;
    
    audio.currentTime = clickTime;
    setCurrentTime(clickTime);
    
    // Check if click is on a segment
    const clickedSegment = segments.find(s => clickTime >= s.start && clickTime <= s.end);
    if (clickedSegment && onSegmentClick) {
      onSegmentClick(clickedSegment);
    }
  }, [duration, segments, onSegmentClick]);

  // Audio event handlers
  const handlePlay = () => {
    const audio = audioRef.current;
    if (audio) {
      audio.play();
      setIsPlaying(true);
    }
  };

  const handlePause = () => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      setIsPlaying(false);
    }
  };

  const handleStop = () => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
      setIsPlaying(false);
      setCurrentTime(0);
    }
  };

  const handleTimeUpdate = () => {
    const audio = audioRef.current;
    if (audio) {
      setCurrentTime(audio.currentTime);
      onTimeUpdate?.(audio.currentTime);
    }
  };

  const handleVolumeChange = (event: Event, newValue: number | number[]) => {
    const audio = audioRef.current;
    const volumeValue = Array.isArray(newValue) ? newValue[0] : newValue;
    if (audio) {
      audio.volume = volumeValue;
      setVolume(volumeValue);
    }
  };

  const handleSeek = (event: Event, newValue: number | number[]) => {
    const audio = audioRef.current;
    const seekTime = Array.isArray(newValue) ? newValue[0] : newValue;
    if (audio) {
      audio.currentTime = seekTime;
      setCurrentTime(seekTime);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const downloadWaveform = () => {
    const canvas = canvasRef.current;
    if (canvas) {
      const link = document.createElement('a');
      link.download = 'waveform.png';
      link.href = canvas.toDataURL();
      link.click();
    }
  };

  // Initialize waveform when audio URL changes
  useEffect(() => {
    if (audioUrl) {
      generateWaveform();
    }
  }, [audioUrl, generateWaveform]);

  // Redraw waveform when data or state changes
  useEffect(() => {
    drawWaveform();
  }, [drawWaveform]);

  // Animation loop for smooth updates
  useEffect(() => {
    if (isPlaying) {
      const animate = () => {
        drawWaveform();
        animationRef.current = requestAnimationFrame(animate);
      };
      animationRef.current = requestAnimationFrame(animate);
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, drawWaveform]);

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" display="flex" alignItems="center">
            <GraphicEq sx={{ mr: 1 }} />
            Waveform Visualization
          </Typography>
          <Box>
            <IconButton onClick={(e) => setSettingsAnchor(e.currentTarget)}>
              <Settings />
            </IconButton>
            <IconButton onClick={downloadWaveform}>
              <Download />
            </IconButton>
          </Box>
        </Box>

        {isLoading && (
          <Box mb={2}>
            <LinearProgress />
            <Typography variant="body2" color="text.secondary" align="center" mt={1}>
              Generating waveform...
            </Typography>
          </Box>
        )}

        {/* Waveform Canvas */}
        <Box 
          sx={{ 
            border: '1px solid #e0e0e0', 
            borderRadius: 1, 
            mb: 2,
            cursor: 'pointer',
            '&:hover': {
              borderColor: '#3f51b5',
            }
          }}
        >
          <canvas
            ref={canvasRef}
            width={800}
            height={height}
            style={{ width: '100%', height: `${height}px`, display: 'block' }}
            onClick={handleCanvasClick}
          />
        </Box>

        {/* Timeline */}
        {showTimeline && duration > 0 && (
          <Box mb={2}>
            <Slider
              value={currentTime}
              max={duration}
              onChange={handleSeek}
              valueLabelDisplay="auto"
              valueLabelFormat={formatTime}
              sx={{ mb: 1 }}
            />
            <Box display="flex" justifyContent="space-between">
              <Typography variant="caption">{formatTime(currentTime)}</Typography>
              <Typography variant="caption">{formatTime(duration)}</Typography>
            </Box>
          </Box>
        )}

        {/* Audio Controls */}
        {showControls && (
          <Box display="flex" alignItems="center" gap={2}>
            <Box display="flex" alignItems="center" gap={1}>
              <IconButton onClick={isPlaying ? handlePause : handlePlay} color="primary">
                {isPlaying ? <Pause /> : <PlayArrow />}
              </IconButton>
              <IconButton onClick={handleStop}>
                <Stop />
              </IconButton>
            </Box>

            <Box display="flex" alignItems="center" gap={1} flex={1}>
              <VolumeDown />
              <Slider
                value={volume}
                max={1}
                step={0.1}
                onChange={handleVolumeChange}
                sx={{ width: 100 }}
              />
              <VolumeUp />
            </Box>

            <Typography variant="body2" color="text.secondary">
              {formatTime(currentTime)} / {formatTime(duration)}
            </Typography>
          </Box>
        )}

        {/* Segment Information */}
        {segments.length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              Audio Segments ({segments.length})
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {segments.slice(0, 10).map((segment, index) => (
                <Chip
                  key={index}
                  label={`${segment.speaker || segment.type || 'Segment'} (${formatTime(segment.start)})`}
                  size="small"
                  onClick={() => onSegmentClick?.(segment)}
                  color={currentTime >= segment.start && currentTime <= segment.end ? 'primary' : 'default'}
                />
              ))}
              {segments.length > 10 && (
                <Chip label={`+${segments.length - 10} more`} size="small" variant="outlined" />
              )}
            </Box>
          </Box>
        )}

        {/* Current Transcript */}
        {showTranscript && transcriptSegments.length > 0 && (
          <Box mt={2}>
            {(() => {
              const currentSegment = transcriptSegments.find(
                s => currentTime >= s.start && currentTime <= s.end
              );
              return currentSegment ? (
                <Card variant="outlined">
                  <CardContent sx={{ py: 1 }}>
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      {currentSegment.speaker && `${currentSegment.speaker}: `}
                      {formatTime(currentSegment.start)} - {formatTime(currentSegment.end)}
                    </Typography>
                    <Typography variant="body2">
                      {currentSegment.text}
                    </Typography>
                  </CardContent>
                </Card>
              ) : (
                <Typography variant="body2" color="text.secondary" align="center">
                  No transcript available for current time
                </Typography>
              );
            })()}
          </Box>
        )}

        {/* Hidden Audio Element */}
        <audio
          ref={audioRef}
          src={audioUrl}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={() => {
            const audio = audioRef.current;
            if (audio) {
              setDuration(audio.duration);
            }
          }}
          onEnded={() => setIsPlaying(false)}
        />

        {/* Settings Menu */}
        <Menu
          anchorEl={settingsAnchor}
          open={Boolean(settingsAnchor)}
          onClose={() => setSettingsAnchor(null)}
        >
          <MenuItem>
            <FormControlLabel
              control={
                <Switch
                  checked={showSegments}
                  onChange={(e) => setShowSegments(e.target.checked)}
                />
              }
              label="Show Segments"
            />
          </MenuItem>
          <MenuItem>
            <FormControlLabel
              control={
                <Switch
                  checked={showTranscript}
                  onChange={(e) => setShowTranscript(e.target.checked)}
                />
              }
              label="Show Transcript"
            />
          </MenuItem>
          <MenuItem>
            <FormControlLabel
              control={
                <Switch
                  checked={showSpeakersState}
                  onChange={(e) => setShowSpeakersState(e.target.checked)}
                />
              }
              label="Show Speakers"
            />
          </MenuItem>
        </Menu>
      </CardContent>
    </Card>
  );
};

export default WaveformVisualizer;