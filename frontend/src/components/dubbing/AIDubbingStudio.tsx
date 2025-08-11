import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  Avatar,
  Slider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Tabs,
  Tab,
  LinearProgress,
  Badge,
  Tooltip,
  Menu,
  Switch,
  FormControlLabel,
  RadioGroup,
  Radio,
  Rating,
  Snackbar,
} from '@mui/material';
import {
  RecordVoiceOver,
  VolumeUp,
  Mic,
  MicOff,
  PlayArrow,
  Pause,
  Stop,
  Upload,
  Download,
  Settings,
  Language,
  Translate,
  MovieCreation,
  AudioFile,
  VideoFile,
  Speed,
  Tune,
  GraphicEq,
  Save,
  Share,
  History,
  Star,
  StarBorder,
  PersonAdd,
  Group,
  ExpandMore,
  Add,
  Remove,
  Edit,
  Delete,
  Refresh,
  CloudUpload,
  GetApp,
  Visibility,
  VisibilityOff,
  Cancel,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Info,
  Headset,
  MusicNote,
  Campaign,
  Transform,
  AutoAwesome,
  Preview,
} from '@mui/icons-material';
import apiService from '../../services/api';
import { Line, Bar } from 'react-chartjs-2';

interface VoiceProfile {
  id: string;
  name: string;
  language: string;
  country: string;
  gender: string;
  age_range: string;
  style: string;
  accent?: string;
  sample_url?: string;
  description?: string;
  premium: boolean;
}

interface DubbingJob {
  id: string;
  type: string;
  status: string;
  progress: number;
  created_at: string;
  result_url?: string;
  metadata?: any;
}

interface Language {
  code: string;
  name: string;
  native_name: string;
  voice_count: number;
  premium_voices: number;
  popular: boolean;
}

const AIDubbingStudio: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [jobs, setJobs] = useState<DubbingJob[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Text synthesis state
  const [text, setText] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('');
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);
  const [volume, setVolume] = useState(1.0);
  const [audioFormat, setAudioFormat] = useState('mp3');
  const [quality, setQuality] = useState('standard');
  
  // Video dubbing state
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [voiceMapping, setVoiceMapping] = useState<Record<string, string>>({});
  const [dubbingMode, setDubbingMode] = useState('full_replacement');
  const [preserveBackground, setPreserveBackground] = useState(true);
  const [syncLipMovement, setSyncLipMovement] = useState(false);
  const [backgroundMusicVolume, setBackgroundMusicVolume] = useState(0.3);
  
  // Voice cloning state
  const [cloneName, setCloneName] = useState('');
  const [cloneDescription, setCloneDescription] = useState('');
  const [cloneGender, setCloneGender] = useState('female');
  const [cloneAudioFile, setCloneAudioFile] = useState<File | null>(null);
  
  // UI state
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [voiceCloneDialogOpen, setVoiceCloneDialogOpen] = useState(false);
  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    loadInitialData();
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [voicesResponse, languagesResponse, jobsResponse] = await Promise.all([
        apiService.get('/api/v1/ai_dubbing/voices'),
        apiService.get('/api/v1/ai_dubbing/languages'),
        apiService.get('/api/v1/ai_dubbing/jobs?limit=20'),
      ]);
      
      setVoices(voicesResponse.data);
      setLanguages(languagesResponse.data.languages);
      setJobs(jobsResponse.data);
    } catch (error) {
      console.error('Failed to load dubbing data:', error);
      setSnackbar({ open: true, message: 'Failed to load dubbing data', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const loadJobs = async () => {
    try {
      const response = await apiService.get('/api/v1/ai_dubbing/jobs?limit=20');
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    }
  };

  const handleTextSynthesis = async () => {
    if (!text.trim() || !selectedLanguage || !selectedVoice) {
      setSnackbar({ open: true, message: 'Please fill in all required fields', severity: 'error' });
      return;
    }

    try {
      setLoading(true);
      const response = await apiService.post('/api/v1/ai_dubbing/synthesize', {
        text: text.trim(),
        language: selectedLanguage,
        voice_id: selectedVoice,
        speed,
        pitch,
        volume,
        format: audioFormat,
        quality,
      });

      setSnackbar({ open: true, message: 'Speech synthesis started successfully', severity: 'success' });
      setText('');
      loadJobs();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to start speech synthesis', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleVideoDubbing = async () => {
    if (!videoFile || !selectedLanguage || Object.keys(voiceMapping).length === 0) {
      setSnackbar({ open: true, message: 'Please upload a video and configure voice mapping', severity: 'error' });
      return;
    }

    try {
      setLoading(true);
      
      // Upload video file first
      const formData = new FormData();
      formData.append('file', videoFile);
      
      const uploadResponse = await apiService.post('/api/v1/files/upload', formData);
      const videoFileId = uploadResponse.data.file_id;

      const response = await apiService.post('/api/v1/ai_dubbing/video/dub', {
        video_file_id: videoFileId,
        target_language: selectedLanguage,
        voice_mapping: voiceMapping,
        mode: dubbingMode,
        preserve_background_audio: preserveBackground,
        sync_lip_movement: syncLipMovement,
        background_music_volume: backgroundMusicVolume,
        quality,
      });

      setSnackbar({ open: true, message: 'Video dubbing started successfully', severity: 'success' });
      setVideoFile(null);
      setVoiceMapping({});
      loadJobs();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to start video dubbing', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceCloning = async () => {
    if (!cloneName.trim() || !selectedLanguage || !cloneGender || !cloneAudioFile) {
      setSnackbar({ open: true, message: 'Please fill in all required fields', severity: 'error' });
      return;
    }

    try {
      setLoading(true);
      
      // Start cloning process
      const cloneResponse = await apiService.post('/api/v1/ai_dubbing/voice/clone/start', {
        name: cloneName,
        description: cloneDescription,
        language: selectedLanguage,
        gender: cloneGender,
      });

      const cloneId = cloneResponse.data.clone_id;
      
      // Upload training audio
      const formData = new FormData();
      formData.append('audio_file', cloneAudioFile);
      
      await apiService.post(`/api/v1/ai_dubbing/voice/clone/${cloneId}/upload`, formData);

      setSnackbar({ open: true, message: 'Voice cloning started successfully', severity: 'success' });
      setVoiceCloneDialogOpen(false);
      setCloneName('');
      setCloneDescription('');
      setCloneAudioFile(null);
      loadJobs();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to start voice cloning', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const playVoiceSample = async (voiceId: string, sampleUrl?: string) => {
    if (currentlyPlaying === voiceId) {
      audioRef.current?.pause();
      setCurrentlyPlaying(null);
      return;
    }

    if (sampleUrl && audioRef.current) {
      audioRef.current.src = sampleUrl;
      audioRef.current.play();
      setCurrentlyPlaying(voiceId);
      
      audioRef.current.onended = () => setCurrentlyPlaying(null);
    }
  };

  const getJobStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      case 'cancelled': return 'default';
      default: return 'info';
    }
  };

  const getJobStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle />;
      case 'processing': return <CircularProgress size={20} />;
      case 'failed': return <ErrorIcon />;
      case 'cancelled': return <Cancel />;
      default: return <Info />;
    }
  };

  const renderVoiceSelector = () => {
    const filteredVoices = voices.filter(voice => 
      !selectedLanguage || voice.language === selectedLanguage
    );

    return (
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Select Voice Profile
        </Typography>
        <Grid container spacing={2}>
          {filteredVoices.map((voice) => (
            <Grid item xs={12} sm={6} md={4} key={voice.id}>
              <Card 
                sx={{ 
                  cursor: 'pointer',
                  border: selectedVoice === voice.id ? 2 : 0,
                  borderColor: 'primary.main',
                  '&:hover': { transform: 'translateY(-2px)', transition: 'transform 0.2s' }
                }}
                onClick={() => setSelectedVoice(voice.id)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                      <RecordVoiceOver />
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {voice.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {voice.country}
                      </Typography>
                    </Box>
                    {voice.premium && (
                      <Chip label="Premium" color="secondary" size="small" />
                    )}
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    {voice.description}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Chip label={voice.gender} size="small" variant="outlined" />
                      <Chip label={voice.style} size="small" variant="outlined" />
                    </Box>
                    
                    {voice.sample_url && (
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          playVoiceSample(voice.id, voice.sample_url);
                        }}
                        color={currentlyPlaying === voice.id ? 'secondary' : 'default'}
                      >
                        {currentlyPlaying === voice.id ? <Pause /> : <PlayArrow />}
                      </IconButton>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <RecordVoiceOver color="primary" />
        AI Dubbing Studio
      </Typography>

      <audio ref={audioRef} style={{ display: 'none' }} />

      {/* Main Tabs */}
      <Tabs 
        value={selectedTab} 
        onChange={(_, newValue) => setSelectedTab(newValue)} 
        sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label="Text to Speech" icon={<AudioFile />} />
        <Tab label="Video Dubbing" icon={<VideoFile />} />
        <Tab label="Voice Cloning" icon={<PersonAdd />} />
        <Tab label="Job History" icon={<History />} />
      </Tabs>

      {/* Text to Speech Tab */}
      {selectedTab === 0 && (
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Convert Text to Speech
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Enter text to convert to speech"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Type or paste your text here..."
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    label="Language"
                  >
                    {languages.map((lang) => (
                      <MenuItem key={lang.code} value={lang.code}>
                        {lang.name} ({lang.voice_count} voices)
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Audio Format</InputLabel>
                  <Select
                    value={audioFormat}
                    onChange={(e) => setAudioFormat(e.target.value)}
                    label="Audio Format"
                  >
                    <MenuItem value="mp3">MP3</MenuItem>
                    <MenuItem value="wav">WAV</MenuItem>
                    <MenuItem value="flac">FLAC</MenuItem>
                    <MenuItem value="ogg">OGG</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
            
            <Accordion sx={{ mt: 2 }}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Advanced Settings</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={4}>
                    <Typography gutterBottom>Speed: {speed}x</Typography>
                    <Slider
                      value={speed}
                      onChange={(_, value) => setSpeed(value as number)}
                      min={0.5}
                      max={2.0}
                      step={0.1}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={4}>
                    <Typography gutterBottom>Pitch: {pitch}x</Typography>
                    <Slider
                      value={pitch}
                      onChange={(_, value) => setPitch(value as number)}
                      min={0.5}
                      max={2.0}
                      step={0.1}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={4}>
                    <Typography gutterBottom>Volume: {volume}x</Typography>
                    <Slider
                      value={volume}
                      onChange={(_, value) => setVolume(value as number)}
                      min={0.1}
                      max={2.0}
                      step={0.1}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Quality</InputLabel>
                      <Select
                        value={quality}
                        onChange={(e) => setQuality(e.target.value)}
                        label="Quality"
                      >
                        <MenuItem value="standard">Standard</MenuItem>
                        <MenuItem value="high">High</MenuItem>
                        <MenuItem value="premium">Premium</MenuItem>
                        <MenuItem value="studio">Studio</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Paper>

          {selectedLanguage && renderVoiceSelector()}

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              onClick={handleTextSynthesis}
              disabled={loading || !text.trim() || !selectedVoice}
              startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
            >
              Generate Speech
            </Button>
          </Box>
        </Box>
      )}

      {/* Video Dubbing Tab */}
      {selectedTab === 1 && (
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Video Dubbing Configuration
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Box
                  sx={{
                    border: '2px dashed',
                    borderColor: 'divider',
                    p: 4,
                    textAlign: 'center',
                    cursor: 'pointer',
                    '&:hover': { borderColor: 'primary.main' }
                  }}
                  onClick={() => document.getElementById('video-upload')?.click()}
                >
                  <input
                    id="video-upload"
                    type="file"
                    accept="video/*"
                    style={{ display: 'none' }}
                    onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
                  />
                  
                  {videoFile ? (
                    <Box>
                      <VideoFile sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                      <Typography variant="h6">{videoFile.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {(videoFile.size / (1024 * 1024)).toFixed(2)} MB
                      </Typography>
                    </Box>
                  ) : (
                    <Box>
                      <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                      <Typography variant="h6">Upload Video File</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Click to select a video file for dubbing
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Target Language</InputLabel>
                  <Select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    label="Target Language"
                  >
                    {languages.map((lang) => (
                      <MenuItem key={lang.code} value={lang.code}>
                        {lang.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Dubbing Mode</InputLabel>
                  <Select
                    value={dubbingMode}
                    onChange={(e) => setDubbingMode(e.target.value)}
                    label="Dubbing Mode"
                  >
                    <MenuItem value="full_replacement">Full Voice Replacement</MenuItem>
                    <MenuItem value="voice_over">Voice Over</MenuItem>
                    <MenuItem value="subtitle_sync">Subtitle Synchronized</MenuItem>
                    <MenuItem value="background_music">With Background Music</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
            
            <Accordion sx={{ mt: 2 }}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Audio Settings</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={preserveBackground}
                          onChange={(e) => setPreserveBackground(e.target.checked)}
                        />
                      }
                      label="Preserve Background Audio"
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={syncLipMovement}
                          onChange={(e) => setSyncLipMovement(e.target.checked)}
                        />
                      }
                      label="Sync Lip Movement (AI)"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Typography gutterBottom>
                      Background Music Volume: {(backgroundMusicVolume * 100).toFixed(0)}%
                    </Typography>
                    <Slider
                      value={backgroundMusicVolume}
                      onChange={(_, value) => setBackgroundMusicVolume(value as number)}
                      min={0}
                      max={1}
                      step={0.1}
                      marks
                      valueLabelDisplay="auto"
                      valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Paper>

          {videoFile && selectedLanguage && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Voice Mapping Configuration
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Map detected speakers to voice profiles
              </Typography>
              
              {/* Mock speaker detection */}
              <List>
                {['Speaker 1 (Male)', 'Speaker 2 (Female)', 'Narrator'].map((speaker, index) => (
                  <ListItem key={speaker}>
                    <ListItemIcon>
                      <Headset />
                    </ListItemIcon>
                    <ListItemText primary={speaker} />
                    <ListItemSecondaryAction>
                      <FormControl size="small" sx={{ minWidth: 120 }}>
                        <Select
                          value={voiceMapping[speaker] || ''}
                          onChange={(e) => setVoiceMapping({
                            ...voiceMapping,
                            [speaker]: e.target.value
                          })}
                          displayEmpty
                        >
                          <MenuItem value="">Select Voice</MenuItem>
                          {voices
                            .filter(voice => !selectedLanguage || voice.language === selectedLanguage)
                            .map((voice) => (
                              <MenuItem key={voice.id} value={voice.id}>
                                {voice.name} ({voice.gender})
                              </MenuItem>
                            ))}
                        </Select>
                      </FormControl>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              onClick={handleVideoDubbing}
              disabled={loading || !videoFile || Object.keys(voiceMapping).length === 0}
              startIcon={loading ? <CircularProgress size={20} /> : <MovieCreation />}
            >
              Start Video Dubbing
            </Button>
          </Box>
        </Box>
      )}

      {/* Voice Cloning Tab */}
      {selectedTab === 2 && (
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Create Custom Voice Clone
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Upload audio samples to create a personalized voice profile
            </Typography>
            
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setVoiceCloneDialogOpen(true)}
            >
              Start Voice Cloning
            </Button>
          </Paper>
          
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Your Custom Voices
            </Typography>
            
            {/* Mock custom voices list */}
            <List>
              <ListItem>
                <ListItemIcon>
                  <Avatar sx={{ bgcolor: 'secondary.main' }}>
                    <PersonAdd />
                  </Avatar>
                </ListItemIcon>
                <ListItemText
                  primary="My Voice Clone"
                  secondary="Created 2 days ago • English (US) • Female"
                />
                <ListItemSecondaryAction>
                  <Chip label="Training" color="warning" size="small" />
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </Paper>
        </Box>
      )}

      {/* Job History Tab */}
      {selectedTab === 3 && (
        <Box>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Dubbing Job History
            </Typography>
            
            <List>
              {jobs.map((job) => (
                <ListItem key={job.id} divider>
                  <ListItemIcon>
                    {getJobStatusIcon(job.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={`${job.type.replace('_', ' ').toUpperCase()} Job`}
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Created: {new Date(job.created_at).toLocaleString()}
                        </Typography>
                        {job.status === 'processing' && (
                          <LinearProgress 
                            variant="determinate" 
                            value={job.progress} 
                            sx={{ mt: 1, width: '200px' }}
                          />
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <Chip 
                        label={job.status.toUpperCase()} 
                        color={getJobStatusColor(job.status)} 
                        size="small" 
                      />
                      {job.result_url && job.status === 'completed' && (
                        <IconButton size="small" href={job.result_url} download>
                          <GetApp />
                        </IconButton>
                      )}
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      )}

      {/* Voice Clone Dialog */}
      <Dialog
        open={voiceCloneDialogOpen}
        onClose={() => setVoiceCloneDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create Voice Clone</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Voice Name"
                value={cloneName}
                onChange={(e) => setCloneName(e.target.value)}
                placeholder="Enter a name for your voice clone"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Description (Optional)"
                value={cloneDescription}
                onChange={(e) => setCloneDescription(e.target.value)}
                placeholder="Describe the voice characteristics"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Language</InputLabel>
                <Select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  label="Language"
                >
                  {languages.map((lang) => (
                    <MenuItem key={lang.code} value={lang.code}>
                      {lang.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Gender</InputLabel>
                <Select
                  value={cloneGender}
                  onChange={(e) => setCloneGender(e.target.value)}
                  label="Gender"
                >
                  <MenuItem value="female">Female</MenuItem>
                  <MenuItem value="male">Male</MenuItem>
                  <MenuItem value="neutral">Neutral</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <Box
                sx={{
                  border: '2px dashed',
                  borderColor: 'divider',
                  p: 3,
                  textAlign: 'center',
                  cursor: 'pointer',
                  '&:hover': { borderColor: 'primary.main' }
                }}
                onClick={() => document.getElementById('clone-audio-upload')?.click()}
              >
                <input
                  id="clone-audio-upload"
                  type="file"
                  accept="audio/*"
                  style={{ display: 'none' }}
                  onChange={(e) => setCloneAudioFile(e.target.files?.[0] || null)}
                />
                
                {cloneAudioFile ? (
                  <Box>
                    <AudioFile sx={{ fontSize: 36, color: 'primary.main', mb: 1 }} />
                    <Typography variant="subtitle1">{cloneAudioFile.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {(cloneAudioFile.size / (1024 * 1024)).toFixed(2)} MB
                    </Typography>
                  </Box>
                ) : (
                  <Box>
                    <Mic sx={{ fontSize: 36, color: 'text.secondary', mb: 1 }} />
                    <Typography variant="subtitle1">Upload Training Audio</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Minimum 5 minutes • Clear speech • Minimal background noise
                    </Typography>
                  </Box>
                )}
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVoiceCloneDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleVoiceCloning}
            disabled={loading || !cloneName.trim() || !cloneAudioFile}
            startIcon={loading ? <CircularProgress size={20} /> : <PersonAdd />}
          >
            Start Cloning
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AIDubbingStudio;