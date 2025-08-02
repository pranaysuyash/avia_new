import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Slider,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  Tooltip,
  Badge,
  Divider,
  Menu,
  MenuList,
  MenuItem as MenuItemComponent
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  VolumeUp,
  VolumeOff,
  Fullscreen,
  FullscreenExit,
  Speed,
  Subtitles,
  VideoSettings,
  Download,
  Share,
  Timeline,
  PhotoCamera,
  Movie,
  Analytics,
  Visibility,
  VisibilityOff,
  Bookmark,
  Edit,
  Delete,
  Add,
  Search,
  FilterList,
  ViewModule,
  ViewList
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

interface VideoFrame {
  timestamp: number;
  frameNumber: number;
  imagePath?: string;
  width: number;
  height: number;
  sceneId?: number;
  motionScore: number;
  brightness: number;
}

interface SceneSegment {
  sceneId: number;
  startTime: number;
  endTime: number;
  startFrame: number;
  endFrame: number;
  duration: number;
  keyframes: VideoFrame[];
}

interface VideoAnalysis {
  videoPath: string;
  duration: number;
  fps: number;
  totalFrames: number;
  width: number;
  height: number;
  scenes: SceneSegment[];
  keyframes: VideoFrame[];
  metadata: Record<string, any>;
}

interface Subtitle {
  id: string;
  startTime: number;
  endTime: number;
  text: string;
  speaker?: string;
}

interface VideoProcessorProps {
  videoUrl: string;
  videoAnalysis?: VideoAnalysis;
  subtitles?: Subtitle[];
  onGenerateSubtitles?: (format: 'srt' | 'vtt') => void;
  onExtractFrames?: (options: FrameExtractionOptions) => void;
  onDetectScenes?: () => void;
  onExportVideo?: (options: ExportOptions) => void;
}

interface FrameExtractionOptions {
  interval: number; // seconds
  quality: 'low' | 'medium' | 'high';
  format: 'jpg' | 'png';
  maxFrames: number;
}

interface ExportOptions {
  format: 'mp4' | 'webm' | 'avi';
  quality: 'low' | 'medium' | 'high';
  includeSubtitles: boolean;
  startTime?: number;
  endTime?: number;
}

export const VideoProcessor: React.FC<VideoProcessorProps> = ({
  videoUrl,
  videoAnalysis,
  subtitles = [],
  onGenerateSubtitles,
  onExtractFrames,
  onDetectScenes,
  onExportVideo
}) => {
  const theme = useTheme();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSubtitles, setShowSubtitles] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedScene, setSelectedScene] = useState<number | null>(null);
  const [frameExtractionDialog, setFrameExtractionDialog] = useState(false);
  const [exportDialog, setExportDialog] = useState(false);
  const [frameOptions, setFrameOptions] = useState<FrameExtractionOptions>({
    interval: 5,
    quality: 'medium',
    format: 'jpg',
    maxFrames: 100
  });
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'mp4',
    quality: 'medium',
    includeSubtitles: true
  });
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [settingsAnchor, setSettingsAnchor] = useState<null | HTMLElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => setCurrentTime(video.currentTime);
    const handleDurationChange = () => setDuration(video.duration);
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('durationchange', handleDurationChange);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('durationchange', handleDurationChange);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
    };
  }, []);

  const togglePlayback = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
  };

  const seekTo = (time: number) => {
    const video = videoRef.current;
    if (!video) return;

    video.currentTime = time;
    setCurrentTime(time);
  };

  const changeVolume = (newVolume: number) => {
    const video = videoRef.current;
    if (!video) return;

    video.volume = newVolume;
    setVolume(newVolume);
  };

  const changePlaybackRate = (rate: number) => {
    const video = videoRef.current;
    if (!video) return;

    video.playbackRate = rate;
    setPlaybackRate(rate);
  };

  const toggleFullscreen = () => {
    const video = videoRef.current;
    if (!video) return;

    if (!isFullscreen) {
      video.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getCurrentSubtitle = (): Subtitle | null => {
    return subtitles.find(sub => 
      currentTime >= sub.startTime && currentTime <= sub.endTime
    ) || null;
  };

  const jumpToScene = (scene: SceneSegment) => {
    seekTo(scene.startTime);
    setSelectedScene(scene.sceneId);
  };

  const renderVideoPlayer = () => (
    <Paper sx={{ position: 'relative', mb: 3 }}>
      <Box sx={{ position: 'relative', backgroundColor: 'black' }}>
        <video
          ref={videoRef}
          src={videoUrl}
          style={{
            width: '100%',
            height: 'auto',
            maxHeight: '60vh',
            display: 'block'
          }}
          onLoadedMetadata={() => {
            if (videoRef.current) {
              setDuration(videoRef.current.duration);
            }
          }}
        />

        {/* Subtitle Overlay */}
        {showSubtitles && (
          <Box
            sx={{
              position: 'absolute',
              bottom: 60,
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              color: 'white',
              padding: '8px 16px',
              borderRadius: 1,
              maxWidth: '80%',
              textAlign: 'center',
              display: getCurrentSubtitle() ? 'block' : 'none'
            }}
          >
            <Typography variant="body1">
              {getCurrentSubtitle()?.text}
            </Typography>
            {getCurrentSubtitle()?.speaker && (
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                {getCurrentSubtitle()?.speaker}
              </Typography>
            )}
          </Box>
        )}

        {/* Video Controls */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            background: 'linear-gradient(transparent, rgba(0,0,0,0.8))',
            p: 2
          }}
        >
          {/* Progress Bar */}
          <Slider
            value={currentTime}
            max={duration}
            onChange={(_, value) => seekTo(value as number)}
            sx={{
              mb: 1,
              '& .MuiSlider-thumb': { color: 'white' },
              '& .MuiSlider-track': { color: 'white' },
              '& .MuiSlider-rail': { color: 'rgba(255,255,255,0.3)' }
            }}
          />

          {/* Control Buttons */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton onClick={togglePlayback} sx={{ color: 'white' }}>
              {isPlaying ? <Pause /> : <PlayArrow />}
            </IconButton>

            <Typography variant="body2" sx={{ color: 'white', minWidth: 80 }}>
              {formatTime(currentTime)} / {formatTime(duration)}
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', mx: 2 }}>
              <IconButton
                onClick={() => changeVolume(volume === 0 ? 1 : 0)}
                sx={{ color: 'white' }}
              >
                {volume === 0 ? <VolumeOff /> : <VolumeUp />}
              </IconButton>
              <Slider
                value={volume}
                max={1}
                step={0.1}
                onChange={(_, value) => changeVolume(value as number)}
                sx={{ width: 100, mx: 1 }}
              />
            </Box>

            <Button
              variant="text"
              onClick={(e) => {
                const rates = [0.5, 0.75, 1, 1.25, 1.5, 2];
                const currentIndex = rates.indexOf(playbackRate);
                const nextRate = rates[(currentIndex + 1) % rates.length];
                changePlaybackRate(nextRate);
              }}
              sx={{ color: 'white', minWidth: 60 }}
            >
              {playbackRate}x
            </Button>

            <IconButton
              onClick={() => setShowSubtitles(!showSubtitles)}
              sx={{ color: showSubtitles ? 'primary.main' : 'white' }}
            >
              <Subtitles />
            </IconButton>

            <IconButton
              onClick={(e) => setSettingsAnchor(e.currentTarget)}
              sx={{ color: 'white' }}
            >
              <VideoSettings />
            </IconButton>

            <Box sx={{ flexGrow: 1 }} />

            <IconButton onClick={toggleFullscreen} sx={{ color: 'white' }}>
              {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
            </IconButton>
          </Box>
        </Box>
      </Box>
    </Paper>
  );

  const renderSceneAnalysis = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Scene Analysis</Typography>
        <Box>
          <IconButton
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
          >
            {viewMode === 'grid' ? <ViewList /> : <ViewModule />}
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<Movie />}
            onClick={onDetectScenes}
            disabled={!videoAnalysis}
          >
            Detect Scenes
          </Button>
        </Box>
      </Box>

      {videoAnalysis?.scenes.length ? (
        viewMode === 'grid' ? (
          <Grid container spacing={2}>
            {videoAnalysis.scenes.map((scene) => (
              <Grid item xs={12} sm={6} md={4} key={scene.sceneId}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    border: selectedScene === scene.sceneId ? 2 : 0,
                    borderColor: 'primary.main',
                    '&:hover': { elevation: 4 }
                  }}
                  onClick={() => jumpToScene(scene)}
                >
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Scene {scene.sceneId}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {formatTime(scene.startTime)} - {formatTime(scene.endTime)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Duration: {formatTime(scene.duration)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Frames: {scene.startFrame} - {scene.endFrame}
                    </Typography>
                    {scene.keyframes.length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Chip
                          label={`${scene.keyframes.length} keyframes`}
                          size="small"
                          color="primary"
                        />
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : (
          <List>
            {videoAnalysis.scenes.map((scene, index) => (
              <React.Fragment key={scene.sceneId}>
                <ListItem
                  button
                  onClick={() => jumpToScene(scene)}
                  selected={selectedScene === scene.sceneId}
                >
                  <ListItemIcon>
                    <Movie />
                  </ListItemIcon>
                  <ListItemText
                    primary={`Scene ${scene.sceneId}`}
                    secondary={
                      <Box>
                        <Typography variant="body2">
                          {formatTime(scene.startTime)} - {formatTime(scene.endTime)} 
                          ({formatTime(scene.duration)})
                        </Typography>
                        <Typography variant="caption">
                          Frames: {scene.startFrame} - {scene.endFrame}
                        </Typography>
                      </Box>
                    }
                  />
                  <Box>
                    <Chip
                      label={`${scene.keyframes.length} keyframes`}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </ListItem>
                {index < videoAnalysis.scenes.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )
      ) : (
        <Alert severity="info">
          No scenes detected. Click "Detect Scenes" to analyze video structure.
        </Alert>
      )}
    </Box>
  );

  const renderFrameExtraction = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Frame Extraction</Typography>
        <Button
          variant="contained"
          startIcon={<PhotoCamera />}
          onClick={() => setFrameExtractionDialog(true)}
        >
          Extract Frames
        </Button>
      </Box>

      {videoAnalysis?.keyframes.length ? (
        <Grid container spacing={2}>
          {videoAnalysis.keyframes.map((frame, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card>
                <Box
                  sx={{
                    height: 120,
                    backgroundColor: 'grey.200',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  {frame.imagePath ? (
                    <img
                      src={frame.imagePath}
                      alt={`Frame ${frame.frameNumber}`}
                      style={{
                        maxWidth: '100%',
                        maxHeight: '100%',
                        objectFit: 'contain'
                      }}
                    />
                  ) : (
                    <PhotoCamera sx={{ fontSize: 40, color: 'grey.500' }} />
                  )}
                </Box>
                <CardContent sx={{ p: 1 }}>
                  <Typography variant="caption" display="block">
                    Frame {frame.frameNumber}
                  </Typography>
                  <Typography variant="caption" display="block">
                    {formatTime(frame.timestamp)}
                  </Typography>
                  <Typography variant="caption" display="block">
                    {frame.width}x{frame.height}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Alert severity="info">
          No frames extracted yet. Use the "Extract Frames" button to generate keyframes.
        </Alert>
      )}
    </Box>
  );

  const renderSubtitles = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Subtitles</Typography>
        <Box>
          <Button
            variant="outlined"
            onClick={() => onGenerateSubtitles?.('srt')}
            sx={{ mr: 1 }}
          >
            Generate SRT
          </Button>
          <Button
            variant="outlined"
            onClick={() => onGenerateSubtitles?.('vtt')}
          >
            Generate VTT
          </Button>
        </Box>
      </Box>

      {subtitles.length > 0 ? (
        <List sx={{ maxHeight: 400, overflow: 'auto' }}>
          {subtitles.map((subtitle, index) => (
            <React.Fragment key={subtitle.id}>
              <ListItem
                button
                onClick={() => seekTo(subtitle.startTime)}
                sx={{
                  backgroundColor: 
                    currentTime >= subtitle.startTime && currentTime <= subtitle.endTime
                      ? 'action.selected'
                      : 'transparent'
                }}
              >
                <ListItemText
                  primary={subtitle.text}
                  secondary={
                    <Box>
                      <Typography variant="caption">
                        {formatTime(subtitle.startTime)} - {formatTime(subtitle.endTime)}
                      </Typography>
                      {subtitle.speaker && (
                        <Chip
                          label={subtitle.speaker}
                          size="small"
                          sx={{ ml: 1 }}
                        />
                      )}
                    </Box>
                  }
                />
              </ListItem>
              {index < subtitles.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      ) : (
        <Alert severity="info">
          No subtitles available. Generate subtitles from the transcript to enable synchronized playback.
        </Alert>
      )}
    </Box>
  );

  const renderVideoInfo = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Video Information</Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="Duration" secondary={formatTime(duration)} />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Resolution" 
                  secondary={videoAnalysis ? `${videoAnalysis.width}x${videoAnalysis.height}` : 'Loading...'} 
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Frame Rate" 
                  secondary={videoAnalysis ? `${videoAnalysis.fps.toFixed(2)} fps` : 'Loading...'} 
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Total Frames" 
                  secondary={videoAnalysis?.totalFrames.toLocaleString() || 'Loading...'} 
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Analysis Statistics</Typography>
            <List dense>
              <ListItem>
                <ListItemText 
                  primary="Scenes Detected" 
                  secondary={videoAnalysis?.scenes.length || 0} 
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Keyframes Extracted" 
                  secondary={videoAnalysis?.keyframes.length || 0} 
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Subtitles" 
                  secondary={subtitles.length} 
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="File Size" 
                  secondary={videoAnalysis?.metadata?.fileSize ? 
                    `${(videoAnalysis.metadata.fileSize / 1024 / 1024).toFixed(2)} MB` : 
                    'Unknown'
                  } 
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <Box>
      {/* Video Player */}
      {renderVideoPlayer()}

      {/* Main Content Tabs */}
      <Paper>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Scenes" icon={<Movie />} iconPosition="start" />
          <Tab label="Frames" icon={<PhotoCamera />} iconPosition="start" />
          <Tab label="Subtitles" icon={<Subtitles />} iconPosition="start" />
          <Tab label="Info" icon={<Analytics />} iconPosition="start" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && renderSceneAnalysis()}
          {activeTab === 1 && renderFrameExtraction()}
          {activeTab === 2 && renderSubtitles()}
          {activeTab === 3 && renderVideoInfo()}
        </Box>
      </Paper>

      {/* Frame Extraction Dialog */}
      <Dialog
        open={frameExtractionDialog}
        onClose={() => setFrameExtractionDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Extract Frames</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="number"
                label="Interval (seconds)"
                value={frameOptions.interval}
                onChange={(e) => setFrameOptions({
                  ...frameOptions,
                  interval: parseInt(e.target.value) || 5
                })}
              />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Quality</InputLabel>
                <Select
                  value={frameOptions.quality}
                  onChange={(e) => setFrameOptions({
                    ...frameOptions,
                    quality: e.target.value as any
                  })}
                  label="Quality"
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Format</InputLabel>
                <Select
                  value={frameOptions.format}
                  onChange={(e) => setFrameOptions({
                    ...frameOptions,
                    format: e.target.value as any
                  })}
                  label="Format"
                >
                  <MenuItem value="jpg">JPEG</MenuItem>
                  <MenuItem value="png">PNG</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="number"
                label="Max Frames"
                value={frameOptions.maxFrames}
                onChange={(e) => setFrameOptions({
                  ...frameOptions,
                  maxFrames: parseInt(e.target.value) || 100
                })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFrameExtractionDialog(false)}>Cancel</Button>
          <Button
            onClick={() => {
              onExtractFrames?.(frameOptions);
              setFrameExtractionDialog(false);
            }}
            variant="contained"
          >
            Extract Frames
          </Button>
        </DialogActions>
      </Dialog>

      {/* Settings Menu */}
      <Menu
        anchorEl={settingsAnchor}
        open={Boolean(settingsAnchor)}
        onClose={() => setSettingsAnchor(null)}
      >
        <MenuItemComponent onClick={() => setExportDialog(true)}>
          <Download sx={{ mr: 1 }} />
          Export Video
        </MenuItemComponent>
        <MenuItemComponent>
          <Share sx={{ mr: 1 }} />
          Share
        </MenuItemComponent>
      </Menu>

      {/* Export Dialog */}
      <Dialog
        open={exportDialog}
        onClose={() => setExportDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Export Video</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Format</InputLabel>
                <Select
                  value={exportOptions.format}
                  onChange={(e) => setExportOptions({
                    ...exportOptions,
                    format: e.target.value as any
                  })}
                  label="Format"
                >
                  <MenuItem value="mp4">MP4</MenuItem>
                  <MenuItem value="webm">WebM</MenuItem>
                  <MenuItem value="avi">AVI</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Quality</InputLabel>
                <Select
                  value={exportOptions.quality}
                  onChange={(e) => setExportOptions({
                    ...exportOptions,
                    quality: e.target.value as any
                  })}
                  label="Quality"
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={exportOptions.includeSubtitles}
                    onChange={(e) => setExportOptions({
                      ...exportOptions,
                      includeSubtitles: e.target.checked
                    })}
                  />
                }
                label="Include Subtitles"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialog(false)}>Cancel</Button>
          <Button
            onClick={() => {
              onExportVideo?.(exportOptions);
              setExportDialog(false);
            }}
            variant="contained"
          >
            Export
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default VideoProcessor;