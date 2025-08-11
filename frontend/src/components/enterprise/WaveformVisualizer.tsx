import React, { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import RegionsPlugin from 'wavesurfer.js/dist/plugin/wavesurfer.regions';
import TimelinePlugin from 'wavesurfer.js/dist/plugin/wavesurfer.timeline';
import SpectrogramPlugin from 'wavesurfer.js/dist/plugin/wavesurfer.spectrogram';
import {
  Box,
  Paper,
  IconButton,
  ToggleButtonGroup,
  ToggleButton,
  FormControlLabel,
  Switch,
  Chip,
  Divider,
  Tooltip,
  useTheme,
  alpha,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Replay5 as Replay5Icon,
  Forward5 as Forward5Icon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  GetApp as DownloadIcon,
  Fullscreen as FullscreenIcon,
} from '@mui/icons-material';

interface AudioRegion {
  start: number;
  end: number;
  color: string;
  label?: string;
  confidence?: number;
}

interface Speaker {
  id: string;
  label: string;
  segments: Array<{
    start: number;
    end: number;
    confidence: number;
  }>;
  color: string;
  duration: number;
}

interface WaveformVisualizerProps {
  audioUrl: string;
  peaks?: number[];
  regions?: AudioRegion[];
  speakers?: Speaker[];
  showSpectrogram?: boolean;
  height?: number;
  progress?: number;
  responsive?: boolean;
  onRegionClick?: (region: AudioRegion) => void;
  onTimeUpdate?: (time: number) => void;
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  audioUrl,
  peaks,
  regions = [],
  speakers = [],
  showSpectrogram: initialShowSpectrogram = false,
  height = 256,
  progress = 0,
  responsive = true,
  onRegionClick,
  onTimeUpdate,
}) => {
  const theme = useTheme();
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurfer = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [zoom, setZoom] = useState(100);
  const [showSpectrogram, setShowSpectrogram] = useState(initialShowSpectrogram);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const speakerColors = [
    theme.palette.error.main,
    theme.palette.info.main,
    theme.palette.success.main,
    theme.palette.warning.main,
    theme.palette.secondary.main,
  ];

  useEffect(() => {
    if (!waveformRef.current || !audioUrl) return;

    // Initialize WaveSurfer
    wavesurfer.current = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: theme.palette.primary.main,
      progressColor: alpha(theme.palette.primary.dark, 0.8),
      cursorColor: theme.palette.primary.dark,
      barWidth: 2,
      barRadius: 3,
      responsive,
      height,
      normalize: true,
      backend: 'WebAudio',
      plugins: [
        RegionsPlugin.create({
          regionsMinLength: 1,
          dragSelection: {
            slop: 5,
          },
        }),
        TimelinePlugin.create({
          container: '#wave-timeline',
          primaryFontColor: theme.palette.text.secondary,
          secondaryFontColor: theme.palette.text.disabled,
          primaryColor: theme.palette.divider,
          secondaryColor: alpha(theme.palette.divider, 0.5),
        }),
      ],
    });

    // Load audio
    if (peaks && peaks.length > 0) {
      wavesurfer.current.load(audioUrl, peaks);
    } else {
      wavesurfer.current.load(audioUrl);
    }

    // Event listeners
    wavesurfer.current.on('ready', () => {
      setDuration(wavesurfer.current!.getDuration());
      
      // Add regions
      regions.forEach(region => {
        wavesurfer.current!.addRegion({
          start: region.start,
          end: region.end,
          color: alpha(region.color, 0.3),
          drag: false,
          resize: false,
          data: region,
        });
      });

      // Add speaker regions
      speakers.forEach(speaker => {
        speaker.segments.forEach(segment => {
          wavesurfer.current!.addRegion({
            start: segment.start,
            end: segment.end,
            color: alpha(speaker.color || speakerColors[parseInt(speaker.id) % speakerColors.length], 0.2),
            drag: false,
            resize: false,
            data: {
              speaker: speaker.label,
              confidence: segment.confidence,
            },
          });
        });
      });
    });

    wavesurfer.current.on('audioprocess', (time) => {
      setCurrentTime(time);
      if (onTimeUpdate) {
        onTimeUpdate(time);
      }
    });

    wavesurfer.current.on('play', () => setIsPlaying(true));
    wavesurfer.current.on('pause', () => setIsPlaying(false));
    wavesurfer.current.on('finish', () => setIsPlaying(false));

    wavesurfer.current.on('region-click', (region, e) => {
      e.stopPropagation();
      if (onRegionClick && region.data) {
        onRegionClick(region.data);
      }
    });

    return () => {
      wavesurfer.current?.destroy();
    };
  }, [audioUrl, peaks, regions, speakers, height, responsive, theme]);

  useEffect(() => {
    if (wavesurfer.current) {
      wavesurfer.current.zoom(zoom);
    }
  }, [zoom]);

  const handlePlayPause = () => {
    if (wavesurfer.current) {
      wavesurfer.current.playPause();
    }
  };

  const handleStop = () => {
    if (wavesurfer.current) {
      wavesurfer.current.stop();
    }
  };

  const handleSkipBackward = () => {
    if (wavesurfer.current) {
      wavesurfer.current.skipBackward(5);
    }
  };

  const handleSkipForward = () => {
    if (wavesurfer.current) {
      wavesurfer.current.skipForward(5);
    }
  };

  const handleZoomChange = (event: React.MouseEvent<HTMLElement>, newZoom: number | null) => {
    if (newZoom !== null) {
      setZoom(newZoom);
    }
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const handleDownload = () => {
    if (wavesurfer.current) {
      const blob = wavesurfer.current.exportImage('image/png');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'waveform.png';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper 
        elevation={1} 
        sx={{ 
          p: 2, 
          bgcolor: theme.palette.background.default,
          borderRadius: 2,
        }}
      >
        {/* Waveform Controls */}
        <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Tooltip title={isPlaying ? 'Pause' : 'Play'}>
              <IconButton onClick={handlePlayPause} color="primary">
                {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Stop">
              <IconButton onClick={handleStop}>
                <StopIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Skip backward 5s">
              <IconButton onClick={handleSkipBackward}>
                <Replay5Icon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Skip forward 5s">
              <IconButton onClick={handleSkipForward}>
                <Forward5Icon />
              </IconButton>
            </Tooltip>
          </Box>

          <Divider orientation="vertical" flexItem />

          <ToggleButtonGroup 
            value={zoom} 
            exclusive 
            onChange={handleZoomChange}
            size="small"
          >
            <ToggleButton value={50}>
              <ZoomOutIcon fontSize="small" />
            </ToggleButton>
            <ToggleButton value={100}>100%</ToggleButton>
            <ToggleButton value={200}>
              <ZoomInIcon fontSize="small" />
            </ToggleButton>
          </ToggleButtonGroup>

          <Divider orientation="vertical" flexItem />

          <FormControlLabel
            control={
              <Switch
                checked={showSpectrogram}
                onChange={(e) => setShowSpectrogram(e.target.checked)}
                size="small"
              />
            }
            label="Spectrogram"
          />

          <Box sx={{ flexGrow: 1 }} />

          <Typography variant="body2" color="text.secondary">
            {formatTime(currentTime)} / {formatTime(duration)}
          </Typography>

          <Tooltip title="Download waveform">
            <IconButton onClick={handleDownload} size="small">
              <DownloadIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Fullscreen">
            <IconButton size="small">
              <FullscreenIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Main Waveform */}
        <Box 
          ref={waveformRef} 
          sx={{ 
            borderRadius: 1,
            overflow: 'hidden',
            bgcolor: alpha(theme.palette.primary.main, 0.02),
          }}
        />

        {/* Timeline */}
        <Box 
          id="wave-timeline" 
          sx={{ 
            mt: 1,
            height: 30,
          }}
        />

        {/* Spectrogram */}
        {showSpectrogram && (
          <Box 
            id="wave-spectrogram" 
            sx={{ 
              mt: 2,
              height: 128,
              borderRadius: 1,
              overflow: 'hidden',
            }}
          />
        )}

        {/* Speaker Labels */}
        {speakers.length > 0 && (
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {speakers.map((speaker, index) => (
              <Chip
                key={speaker.id}
                label={`${speaker.label}: ${formatTime(speaker.duration)}`}
                size="small"
                sx={{
                  bgcolor: alpha(
                    speaker.color || speakerColors[index % speakerColors.length],
                    0.2
                  ),
                  color: speaker.color || speakerColors[index % speakerColors.length],
                  fontWeight: 'medium',
                }}
              />
            ))}
          </Box>
        )}
      </Paper>
    </Box>
  );
};
