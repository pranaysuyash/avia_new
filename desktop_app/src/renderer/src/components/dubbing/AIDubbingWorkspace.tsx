import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  Drawer,
  AppBar,
  Toolbar,
  SpeedDial,
  SpeedDialIcon,
  SpeedDialAction,
  Timeline,
  TimelineItem,
  TimelineContent,
  TimelineSeparator,
  TimelineDot,
  TimelineConnector,
  Breadcrumbs,
  Link,
  Skeleton,
  Fade,
  Slide,
  Grow,
  ButtonGroup,
  ToggleButton,
  ToggleButtonGroup,
  Backdrop,
  Stack,
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
  Waveform,
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
  GraphicEq,
  MusicNote,
  Campaign,
  Transform,
  AutoAwesome,
  Preview,
  Close,
  Menu as MenuIcon,
  Dashboard,
  Analytics,
  Folder,
  FileCopy,
  ImportExport,
  Launch,
  Fullscreen,
  FullscreenExit,
  PictureInPicture,
  VolumeOff,
  VolumeDown,
  Loop,
  Shuffle,
  QueueMusic,
  Equalizer,
  Code,
  BugReport,
  Extension,
  CloudSync,
  Backup,
  Restore,
  Schedule,
  Timer,
  AccessTime,
  Today,
  Event,
  Notifications,
  NotificationsActive,
  LightMode,
  DarkMode,
  Contrast,
  Palette,
} from '@mui/icons-material';
import { Line, Bar, Doughnut, Radar } from 'react-chartjs-2';

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

interface DubbingProject {
  id: string;
  name: string;
  type: 'text_synthesis' | 'video_dubbing' | 'batch_processing' | 'voice_cloning';
  status: 'draft' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  progress: number;
  metadata: any;
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

const AIDubbingWorkspace: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [projects, setProjects] = useState<DubbingProject[]>([]);
  const [jobs, setJobs] = useState<DubbingJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  
  // Project state
  const [currentProject, setCurrentProject] = useState<DubbingProject | null>(null);
  const [projectName, setProjectName] = useState('');
  const [projectType, setProjectType] = useState<'text_synthesis' | 'video_dubbing' | 'batch_processing' | 'voice_cloning'>('text_synthesis');
  
  // Text synthesis state
  const [text, setText] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('en-US');
  const [selectedVoice, setSelectedVoice] = useState('');
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);
  const [volume, setVolume] = useState(1.0);
  const [audioFormat, setAudioFormat] = useState('mp3');
  const [quality, setQuality] = useState('high');
  
  // Video dubbing state
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [voiceMapping, setVoiceMapping] = useState<Record<string, string>>({});
  const [dubbingMode, setDubbingMode] = useState('full_replacement');
  const [preserveBackground, setPreserveBackground] = useState(true);
  const [syncLipMovement, setSyncLipMovement] = useState(false);
  const [backgroundMusicVolume, setBackgroundMusicVolume] = useState(0.3);
  
  // Batch processing state
  const [batchFiles, setBatchFiles] = useState<File[]>([]);
  const [batchSettings, setBatchSettings] = useState({});
  
  // Voice cloning state
  const [cloneName, setCloneName] = useState('');
  const [cloneDescription, setCloneDescription] = useState('');
  const [cloneGender, setCloneGender] = useState('female');
  const [cloneAudioFiles, setCloneAudioFiles] = useState<File[]>([]);
  
  // UI state
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [analyticsDialogOpen, setAnalyticsDialogOpen] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'timeline'>('grid');
  const [darkMode, setDarkMode] = useState(false);
  const [autoSave, setAutoSave] = useState(true);
  const [notifications, setNotifications] = useState(true);
  
  const [snackbar, setSnackbar] = useState<{ 
    open: boolean; 
    message: string; 
    severity: 'success' | 'error' | 'warning' | 'info' 
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadWorkspaceData();
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  // Auto-save functionality
  useEffect(() => {
    if (autoSave && currentProject) {
      const timer = setTimeout(() => {
        saveProject();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [text, selectedVoice, speed, pitch, volume, autoSave, currentProject]);

  const loadWorkspaceData = async () => {
    try {
      setLoading(true);
      // Mock API calls - replace with actual API calls
      const mockVoices: VoiceProfile[] = [
        {
          id: 'voice_en_us_sarah',
          name: 'Sarah',
          language: 'en-US',
          country: 'United States',
          gender: 'female',
          age_range: '20-30',
          style: 'natural',
          description: 'Clear, professional female voice',
          premium: false
        },
        {
          id: 'voice_en_us_john',
          name: 'John',
          language: 'en-US',
          country: 'United States',
          gender: 'male',
          age_range: '30-40',
          style: 'professional',
          description: 'Deep, authoritative male voice',
          premium: true
        },
      ];

      const mockProjects: DubbingProject[] = [
        {
          id: 'project_1',
          name: 'Marketing Video Dubbing',
          type: 'video_dubbing',
          status: 'completed',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          progress: 100,
          metadata: { language: 'es-ES', duration: 120 }
        },
        {
          id: 'project_2',
          name: 'Product Demo Voice-over',
          type: 'text_synthesis',
          status: 'processing',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          progress: 65,
          metadata: { voice: 'Sarah', words: 450 }
        },
      ];

      setVoices(mockVoices);
      setProjects(mockProjects);
    } catch (error) {
      console.error('Failed to load workspace data:', error);
      setSnackbar({ open: true, message: 'Failed to load workspace data', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const loadJobs = async () => {
    try {
      // Mock job updates
      const mockJobs: DubbingJob[] = [
        {
          id: 'job_1',
          type: 'text_synthesis',
          status: 'processing',
          progress: 75,
          created_at: new Date().toISOString(),
        },
      ];
      setJobs(mockJobs);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    }
  };

  const createProject = () => {
    if (!projectName.trim()) {
      setSnackbar({ open: true, message: 'Please enter a project name', severity: 'warning' });
      return;
    }

    const newProject: DubbingProject = {
      id: `project_${Date.now()}`,
      name: projectName,
      type: projectType,
      status: 'draft',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      progress: 0,
      metadata: {}
    };

    setProjects(prev => [newProject, ...prev]);
    setCurrentProject(newProject);
    setProjectName('');
    setProjectDialogOpen(false);
    setSnackbar({ open: true, message: 'Project created successfully', severity: 'success' });
  };

  const saveProject = useCallback(async () => {
    if (!currentProject) return;

    try {
      // Mock save operation
      const updatedProject = {
        ...currentProject,
        updated_at: new Date().toISOString(),
        metadata: {
          ...currentProject.metadata,
          text: text,
          voice: selectedVoice,
          settings: { speed, pitch, volume, quality }
        }
      };

      setProjects(prev => prev.map(p => p.id === currentProject.id ? updatedProject : p));
      setCurrentProject(updatedProject);
    } catch (error) {
      console.error('Failed to save project:', error);
    }
  }, [currentProject, text, selectedVoice, speed, pitch, volume, quality]);

  const handleTextSynthesis = async () => {
    if (!text.trim() || !selectedVoice) {
      setSnackbar({ open: true, message: 'Please fill in all required fields', severity: 'warning' });
      return;
    }

    try {
      setLoading(true);
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      setSnackbar({ open: true, message: 'Speech synthesis started successfully', severity: 'success' });
      loadJobs();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to start speech synthesis', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleVideoDubbing = async () => {
    if (!videoFile || Object.keys(voiceMapping).length === 0) {
      setSnackbar({ open: true, message: 'Please upload a video and configure voice mapping', severity: 'warning' });
      return;
    }

    try {
      setLoading(true);
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      setSnackbar({ open: true, message: 'Video dubbing started successfully', severity: 'success' });
      loadJobs();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to start video dubbing', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleBatchProcessing = async () => {
    if (batchFiles.length === 0) {
      setSnackbar({ open: true, message: 'Please select files to process', severity: 'warning' });
      return;
    }

    try {
      setLoading(true);
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      setSnackbar({ open: true, message: 'Batch processing started successfully', severity: 'success' });
      loadJobs();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to start batch processing', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceCloning = async () => {
    if (!cloneName.trim() || cloneAudioFiles.length === 0) {
      setSnackbar({ open: true, message: 'Please fill in all required fields', severity: 'warning' });
      return;
    }

    try {
      setLoading(true);
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 5000));
      setSnackbar({ open: true, message: 'Voice cloning started successfully', severity: 'success' });
      loadJobs();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to start voice cloning', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const toggleFullscreen = () => {
    setFullscreen(!fullscreen);
    if (!fullscreen) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  };

  const exportProject = () => {
    if (!currentProject) return;
    
    const projectData = {
      project: currentProject,
      settings: { speed, pitch, volume, quality },
      content: text,
      voice: selectedVoice,
      exported_at: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(projectData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentProject.name}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const importProject = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const projectData = JSON.parse(e.target?.result as string);
        const importedProject = {
          ...projectData.project,
          id: `project_${Date.now()}`,
          name: `${projectData.project.name} (Imported)`
        };
        
        setProjects(prev => [importedProject, ...prev]);
        setCurrentProject(importedProject);
        setText(projectData.content || '');
        setSelectedVoice(projectData.voice || '');
        setSpeed(projectData.settings?.speed || 1.0);
        setPitch(projectData.settings?.pitch || 1.0);
        setVolume(projectData.settings?.volume || 1.0);
        setQuality(projectData.settings?.quality || 'high');
        
        setSnackbar({ open: true, message: 'Project imported successfully', severity: 'success' });
      } catch (error) {
        setSnackbar({ open: true, message: 'Failed to import project', severity: 'error' });
      }
    };
    reader.readAsText(file);
  };

  const renderProjectCard = (project: DubbingProject) => (
    <Card 
      key={project.id}
      sx={{ 
        cursor: 'pointer',
        border: currentProject?.id === project.id ? 2 : 0,
        borderColor: 'primary.main',
        '&:hover': { transform: 'translateY(-2px)', transition: 'transform 0.2s' }
      }}
      onClick={() => setCurrentProject(project)}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
            {project.type === 'text_synthesis' && <RecordVoiceOver />}
            {project.type === 'video_dubbing' && <MovieCreation />}
            {project.type === 'batch_processing' && <QueueMusic />}
            {project.type === 'voice_cloning' && <PersonAdd />}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6">{project.name}</Typography>
            <Typography variant="body2" color="text.secondary">
              {project.type.replace('_', ' ').toUpperCase()}
            </Typography>
          </Box>
          <Chip 
            label={project.status.toUpperCase()} 
            color={project.status === 'completed' ? 'success' : project.status === 'processing' ? 'warning' : 'default'}
            size="small"
          />
        </Box>
        
        {project.status === 'processing' && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress variant="determinate" value={project.progress} />
            <Typography variant="caption" color="text.secondary">
              {project.progress}% complete
            </Typography>
          </Box>
        )}
        
        <Typography variant="body2" color="text.secondary">
          Updated: {new Date(project.updated_at).toLocaleDateString()}
        </Typography>
      </CardContent>
    </Card>
  );

  const renderTimelineView = () => (
    <Timeline position="alternate">
      {projects.map((project, index) => (
        <TimelineItem key={project.id}>
          <TimelineSeparator>
            <TimelineDot 
              color={project.status === 'completed' ? 'success' : project.status === 'processing' ? 'warning' : 'primary'}
            >
              {project.type === 'text_synthesis' && <RecordVoiceOver />}
              {project.type === 'video_dubbing' && <MovieCreation />}
              {project.type === 'batch_processing' && <QueueMusic />}
              {project.type === 'voice_cloning' && <PersonAdd />}
            </TimelineDot>
            {index < projects.length - 1 && <TimelineConnector />}
          </TimelineSeparator>
          <TimelineContent>
            <Card 
              sx={{ 
                cursor: 'pointer',
                border: currentProject?.id === project.id ? 2 : 0,
                borderColor: 'primary.main'
              }}
              onClick={() => setCurrentProject(project)}
            >
              <CardContent>
                <Typography variant="h6">{project.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {new Date(project.created_at).toLocaleDateString()}
                </Typography>
                {project.status === 'processing' && (
                  <LinearProgress variant="determinate" value={project.progress} sx={{ mt: 1 }} />
                )}
              </CardContent>
            </Card>
          </TimelineContent>
        </TimelineItem>
      ))}
    </Timeline>
  );

  const speedDialActions = [
    { icon: <Add />, name: 'New Project', action: () => setProjectDialogOpen(true) },
    { icon: <Upload />, name: 'Import Project', action: () => fileInputRef.current?.click() },
    { icon: <Analytics />, name: 'Analytics', action: () => setAnalyticsDialogOpen(true) },
    { icon: <Settings />, name: 'Settings', action: () => setSettingsDialogOpen(true) },
    { icon: <Backup />, name: 'Backup Projects', action: exportProject },
    { icon: fullscreen ? <FullscreenExit /> : <Fullscreen />, name: 'Toggle Fullscreen', action: toggleFullscreen },
  ];

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Hidden file input for import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        style={{ display: 'none' }}
        onChange={importProject}
      />

      {/* Sidebar */}
      <Drawer
        variant="persistent"
        anchor="left"
        open={drawerOpen}
        sx={{
          width: 300,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 300,
            boxSizing: 'border-box',
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            AI Dubbing Workspace
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(_, value) => value && setViewMode(value)}
              size="small"
            >
              <ToggleButton value="grid">Grid</ToggleButton>
              <ToggleButton value="list">List</ToggleButton>
              <ToggleButton value="timeline">Timeline</ToggleButton>
            </ToggleButtonGroup>
          </Box>

          <Typography variant="subtitle1" gutterBottom>
            Recent Projects
          </Typography>
          
          <List>
            {projects.slice(0, 5).map((project) => (
              <ListItem 
                key={project.id} 
                button 
                selected={currentProject?.id === project.id}
                onClick={() => setCurrentProject(project)}
              >
                <ListItemIcon>
                  {project.type === 'text_synthesis' && <RecordVoiceOver />}
                  {project.type === 'video_dubbing' && <MovieCreation />}
                  {project.type === 'batch_processing' && <QueueMusic />}
                  {project.type === 'voice_cloning' && <PersonAdd />}
                </ListItemIcon>
                <ListItemText
                  primary={project.name}
                  secondary={project.type.replace('_', ' ')}
                />
                <ListItemSecondaryAction>
                  <Chip 
                    label={project.status} 
                    size="small" 
                    color={project.status === 'completed' ? 'success' : 'default'}
                  />
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Top App Bar */}
        <AppBar position="static" color="default" elevation={1}>
          <Toolbar>
            <IconButton
              edge="start"
              onClick={() => setDrawerOpen(!drawerOpen)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              {currentProject ? currentProject.name : 'AI Dubbing Workspace'}
            </Typography>

            <Box sx={{ display: 'flex', gap: 1 }}>
              {currentProject && (
                <>
                  <Button size="small" startIcon={<Save />} onClick={saveProject}>
                    Save
                  </Button>
                  <Button size="small" startIcon={<Download />} onClick={exportProject}>
                    Export
                  </Button>
                </>
              )}
              
              <IconButton onClick={() => setNotifications(!notifications)}>
                {notifications ? <NotificationsActive /> : <Notifications />}
              </IconButton>
              
              <IconButton onClick={() => setDarkMode(!darkMode)}>
                {darkMode ? <LightMode /> : <DarkMode />}
              </IconButton>
            </Box>
          </Toolbar>
        </AppBar>

        {/* Main Content Area */}
        <Box sx={{ flexGrow: 1, p: 3, overflow: 'auto' }}>
          {!currentProject ? (
            /* Project Overview */
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4">
                  Your Dubbing Projects
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => setProjectDialogOpen(true)}
                >
                  New Project
                </Button>
              </Box>

              {viewMode === 'timeline' ? renderTimelineView() : (
                <Grid container spacing={3}>
                  {projects.map((project) => (
                    <Grid item xs={12} sm={6} md={4} key={project.id}>
                      {renderProjectCard(project)}
                    </Grid>
                  ))}
                </Grid>
              )}
            </Box>
          ) : (
            /* Project Workspace */
            <Box>
              <Breadcrumbs sx={{ mb: 3 }}>
                <Link color="inherit" href="#" onClick={() => setCurrentProject(null)}>
                  Projects
                </Link>
                <Typography color="text.primary">{currentProject.name}</Typography>
              </Breadcrumbs>

              {/* Project-specific tabs */}
              <Tabs 
                value={selectedTab} 
                onChange={(_, newValue) => setSelectedTab(newValue)} 
                sx={{ mb: 3 }}
              >
                {currentProject.type === 'text_synthesis' && (
                  <Tab label="Text to Speech" icon={<RecordVoiceOver />} />
                )}
                {currentProject.type === 'video_dubbing' && (
                  <Tab label="Video Dubbing" icon={<MovieCreation />} />
                )}
                {currentProject.type === 'batch_processing' && (
                  <Tab label="Batch Processing" icon={<QueueMusic />} />
                )}
                {currentProject.type === 'voice_cloning' && (
                  <Tab label="Voice Cloning" icon={<PersonAdd />} />
                )}
                <Tab label="Preview" icon={<Preview />} />
                <Tab label="Export" icon={<GetApp />} />
              </Tabs>

              {/* Text to Speech Workspace */}
              {currentProject.type === 'text_synthesis' && selectedTab === 0 && (
                <Grid container spacing={3}>
                  <Grid item xs={12} lg={8}>
                    <Paper sx={{ p: 3, height: 'fit-content' }}>
                      <Typography variant="h6" gutterBottom>
                        Text Content
                      </Typography>
                      
                      <TextField
                        fullWidth
                        multiline
                        rows={8}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Enter your text here..."
                        variant="outlined"
                        sx={{ mb: 2 }}
                      />
                      
                      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                        <Chip label={`${text.length} characters`} variant="outlined" />
                        <Chip label={`~${Math.ceil(text.length / 5)} words`} variant="outlined" />
                        <Chip label={`~${Math.ceil(text.length * 0.08)}s duration`} variant="outlined" />
                      </Box>
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={12} lg={4}>
                    <Stack spacing={2}>
                      {/* Voice Selection */}
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                          Voice Settings
                        </Typography>
                        
                        <FormControl fullWidth sx={{ mb: 2 }}>
                          <InputLabel>Voice</InputLabel>
                          <Select
                            value={selectedVoice}
                            onChange={(e) => setSelectedVoice(e.target.value)}
                            label="Voice"
                          >
                            {voices.map((voice) => (
                              <MenuItem key={voice.id} value={voice.id}>
                                {voice.name} ({voice.gender}, {voice.language})
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>

                        <Typography gutterBottom>Speed: {speed}x</Typography>
                        <Slider
                          value={speed}
                          onChange={(_, value) => setSpeed(value as number)}
                          min={0.5}
                          max={2.0}
                          step={0.1}
                          sx={{ mb: 2 }}
                        />

                        <Typography gutterBottom>Pitch: {pitch}x</Typography>
                        <Slider
                          value={pitch}
                          onChange={(_, value) => setPitch(value as number)}
                          min={0.5}
                          max={2.0}
                          step={0.1}
                          sx={{ mb: 2 }}
                        />

                        <Typography gutterBottom>Volume: {volume}x</Typography>
                        <Slider
                          value={volume}
                          onChange={(_, value) => setVolume(value as number)}
                          min={0.1}
                          max={2.0}
                          step={0.1}
                          sx={{ mb: 2 }}
                        />
                      </Paper>

                      {/* Quality Settings */}
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                          Output Settings
                        </Typography>
                        
                        <FormControl fullWidth sx={{ mb: 2 }}>
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

                        <FormControl fullWidth>
                          <InputLabel>Format</InputLabel>
                          <Select
                            value={audioFormat}
                            onChange={(e) => setAudioFormat(e.target.value)}
                            label="Format"
                          >
                            <MenuItem value="mp3">MP3</MenuItem>
                            <MenuItem value="wav">WAV</MenuItem>
                            <MenuItem value="flac">FLAC</MenuItem>
                            <MenuItem value="ogg">OGG</MenuItem>
                          </Select>
                        </FormControl>
                      </Paper>

                      {/* Action Buttons */}
                      <ButtonGroup variant="contained" fullWidth>
                        <Button
                          onClick={handleTextSynthesis}
                          disabled={loading || !text.trim() || !selectedVoice}
                          startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
                        >
                          Generate
                        </Button>
                        <Button onClick={() => setPreviewDialogOpen(true)}>
                          Preview
                        </Button>
                      </ButtonGroup>
                    </Stack>
                  </Grid>
                </Grid>
              )}

              {/* Other project type workspaces would go here */}
            </Box>
          )}
        </Box>
      </Box>

      {/* Speed Dial */}
      <SpeedDial
        ariaLabel="Dubbing Actions"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        icon={<SpeedDialIcon />}
      >
        {speedDialActions.map((action) => (
          <SpeedDialAction
            key={action.name}
            icon={action.icon}
            tooltipTitle={action.name}
            onClick={action.action}
          />
        ))}
      </SpeedDial>

      {/* Project Creation Dialog */}
      <Dialog
        open={projectDialogOpen}
        onClose={() => setProjectDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Project Name"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="Enter project name"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Project Type</InputLabel>
                <Select
                  value={projectType}
                  onChange={(e) => setProjectType(e.target.value as any)}
                  label="Project Type"
                >
                  <MenuItem value="text_synthesis">Text to Speech</MenuItem>
                  <MenuItem value="video_dubbing">Video Dubbing</MenuItem>
                  <MenuItem value="batch_processing">Batch Processing</MenuItem>
                  <MenuItem value="voice_cloning">Voice Cloning</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProjectDialogOpen(false)}>Cancel</Button>
          <Button onClick={createProject} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog
        open={settingsDialogOpen}
        onClose={() => setSettingsDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Workspace Settings</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={autoSave}
                    onChange={(e) => setAutoSave(e.target.checked)}
                  />
                }
                label="Auto-save projects"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={notifications}
                    onChange={(e) => setNotifications(e.target.checked)}
                  />
                }
                label="Show notifications"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={darkMode}
                    onChange={(e) => setDarkMode(e.target.checked)}
                  />
                }
                label="Dark mode"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
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

export default AIDubbingWorkspace;