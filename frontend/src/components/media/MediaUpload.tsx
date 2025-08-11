import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  IconButton,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Switch,
  FormControlLabel,
  Divider
} from '@mui/material';
import {
  CloudUpload,
  AudioFile,
  VideoFile,
  Delete,
  PlayArrow,
  Pause,
  Settings,
  Info,
  CheckCircle,
  Error,
  Warning,
  Mic,
  Stop,
  Refresh
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: 'audio' | 'video';
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  duration?: number;
  error?: string;
  preview?: string;
}

interface ProcessingOptions {
  language: string;
  analysisMode: 'basic' | 'advanced' | 'advanced_plus';
  enableSpeakerDiarization: boolean;
  enableStructuredAnalysis: boolean;
  customPrompt?: string;
  outputFormat: 'json' | 'text' | 'srt' | 'vtt';
}

export const MediaUpload: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [processingOptions, setProcessingOptions] = useState<ProcessingOptions>({
    language: 'auto',
    analysisMode: 'advanced',
    enableSpeakerDiarization: true,
    enableStructuredAnalysis: false,
    outputFormat: 'json'
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const supportedFormats = {
    audio: ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'],
    video: ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv']
  };

  const maxFileSize = 500 * 1024 * 1024; // 500MB

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // Handle rejected files
    rejectedFiles.forEach(({ file, errors }) => {
      errors.forEach((error: any) => {
        console.error(`File ${file.name}: ${error.message}`);
      });
    });

    // Process accepted files
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: file.size,
      type: file.type.startsWith('video/') ? 'video' : 'audio',
      status: 'pending',
      progress: 0,
      preview: file.type.startsWith('video/') ? URL.createObjectURL(file) : undefined
    }));

    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': supportedFormats.audio,
      'video/*': supportedFormats.video
    },
    maxSize: maxFileSize,
    multiple: true
  });

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(file => file.id !== id));
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], `recording-${Date.now()}.wav`, {
          type: 'audio/wav'
        });

        const newFile: UploadedFile = {
          id: Math.random().toString(36).substr(2, 9),
          file: audioFile,
          name: audioFile.name,
          size: audioFile.size,
          type: 'audio',
          status: 'pending',
          progress: 0
        };

        setFiles(prev => [...prev, newFile]);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      recordingIntervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Failed to start recording. Please check microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
    }
  };

  const processFiles = async () => {
    const pendingFiles = files.filter(file => file.status === 'pending');
    
    for (const file of pendingFiles) {
      await processFile(file);
    }
  };

  const processFile = async (file: UploadedFile) => {
    // Update status to uploading
    setFiles(prev => prev.map(f => 
      f.id === file.id ? { ...f, status: 'uploading' } : f
    ));

    try {
      // Simulate file upload with progress
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setFiles(prev => prev.map(f => 
          f.id === file.id ? { ...f, progress } : f
        ));
      }

      // Update status to processing
      setFiles(prev => prev.map(f => 
        f.id === file.id ? { ...f, status: 'processing', progress: 0 } : f
      ));

      // Simulate processing
      const formData = new FormData();
      formData.append('file', file.file);
      formData.append('options', JSON.stringify(processingOptions));

      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Update status to completed
      setFiles(prev => prev.map(f => 
        f.id === file.id ? { 
          ...f, 
          status: 'completed', 
          progress: 100,
          duration: Math.floor(Math.random() * 300) + 60 // Mock duration
        } : f
      ));

    } catch (error) {
      setFiles(prev => prev.map(f => 
        f.id === file.id ? { 
          ...f, 
          status: 'error', 
          error: 'Processing failed. Please try again.'
        } : f
      ));
    }
  };

  const retryFile = (file: UploadedFile) => {
    setFiles(prev => prev.map(f => 
      f.id === file.id ? { ...f, status: 'pending', progress: 0, error: undefined } : f
    ));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle color="success" />;
      case 'error': return <Error color="error" />;
      case 'processing': case 'uploading': return <Warning color="warning" />;
      default: return <Info color="info" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'error': return 'error';
      case 'processing': case 'uploading': return 'warning';
      default: return 'info';
    }
  };

  const renderDropzone = () => (
    <Paper
      {...getRootProps()}
      sx={{
        p: 4,
        textAlign: 'center',
        cursor: 'pointer',
        border: '2px dashed',
        borderColor: isDragActive ? 'primary.main' : 'grey.300',
        backgroundColor: isDragActive ? 'primary.50' : 'grey.50',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          borderColor: 'primary.main',
          backgroundColor: 'primary.50'
        }
      }}
    >
      <input {...getInputProps()} />
      <CloudUpload sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
      <Typography variant="h6" gutterBottom>
        {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        or click to select files
      </Typography>
      <Typography variant="caption" color="text.secondary">
        Supported formats: {[...supportedFormats.audio, ...supportedFormats.video].join(', ')}
      </Typography>
      <br />
      <Typography variant="caption" color="text.secondary">
        Maximum file size: {formatFileSize(maxFileSize)}
      </Typography>
    </Paper>
  );

  const renderRecordingControls = () => (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Audio Recording
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {!isRecording ? (
            <Button
              variant="contained"
              startIcon={<Mic />}
              onClick={startRecording}
              color="error"
            >
              Start Recording
            </Button>
          ) : (
            <>
              <Button
                variant="contained"
                startIcon={<Stop />}
                onClick={stopRecording}
                color="primary"
              >
                Stop Recording
              </Button>
              <Typography variant="body1">
                Recording: {formatTime(recordingTime)}
              </Typography>
            </>
          )}
        </Box>
      </CardContent>
    </Card>
  );

  const renderFileList = () => (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Uploaded Files ({files.length})
          </Typography>
          <Box>
            <IconButton onClick={() => setShowSettings(true)}>
              <Settings />
            </IconButton>
            <Button
              variant="contained"
              onClick={processFiles}
              disabled={files.filter(f => f.status === 'pending').length === 0}
              sx={{ ml: 1 }}
            >
              Process Files
            </Button>
          </Box>
        </Box>

        <List>
          {files.map((file, index) => (
            <React.Fragment key={file.id}>
              <ListItem>
                <ListItemIcon>
                  {file.type === 'video' ? <VideoFile /> : <AudioFile />}
                </ListItemIcon>
                <ListItemText
                  primary={file.name}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {formatFileSize(file.size)}
                        {file.duration && ` • ${formatTime(file.duration)}`}
                      </Typography>
                      {file.error && (
                        <Typography variant="body2" color="error">
                          {file.error}
                        </Typography>
                      )}
                      {(file.status === 'uploading' || file.status === 'processing') && (
                        <LinearProgress
                          variant="determinate"
                          value={file.progress}
                          sx={{ mt: 1 }}
                        />
                      )}
                    </Box>
                  }
                />
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label={file.status}
                    color={getStatusColor(file.status) as any}
                    size="small"
                    icon={getStatusIcon(file.status)}
                  />
                  {file.status === 'error' && (
                    <IconButton onClick={() => retryFile(file)} size="small">
                      <Refresh />
                    </IconButton>
                  )}
                  <IconButton onClick={() => removeFile(file.id)} size="small">
                    <Delete />
                  </IconButton>
                </Box>
              </ListItem>
              {index < files.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>

        {files.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
            No files uploaded yet
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  const renderSettingsDialog = () => (
    <Dialog open={showSettings} onClose={() => setShowSettings(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Processing Settings</DialogTitle>
      <DialogContent>
        <Grid container spacing={3} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Language</InputLabel>
              <Select
                value={processingOptions.language}
                onChange={(e) => setProcessingOptions(prev => ({ ...prev, language: e.target.value }))}
                label="Language"
              >
                <MenuItem value="auto">Auto-detect</MenuItem>
                <MenuItem value="en">English</MenuItem>
                <MenuItem value="es">Spanish</MenuItem>
                <MenuItem value="fr">French</MenuItem>
                <MenuItem value="de">German</MenuItem>
                <MenuItem value="it">Italian</MenuItem>
                <MenuItem value="pt">Portuguese</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Analysis Mode</InputLabel>
              <Select
                value={processingOptions.analysisMode}
                onChange={(e) => setProcessingOptions(prev => ({ ...prev, analysisMode: e.target.value as any }))}
                label="Analysis Mode"
              >
                <MenuItem value="basic">Basic (spaCy)</MenuItem>
                <MenuItem value="advanced">Advanced (OpenAI)</MenuItem>
                <MenuItem value="advanced_plus">Advanced+ (Speaker Diarization)</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Output Format</InputLabel>
              <Select
                value={processingOptions.outputFormat}
                onChange={(e) => setProcessingOptions(prev => ({ ...prev, outputFormat: e.target.value as any }))}
                label="Output Format"
              >
                <MenuItem value="json">JSON</MenuItem>
                <MenuItem value="text">Plain Text</MenuItem>
                <MenuItem value="srt">SRT Subtitles</MenuItem>
                <MenuItem value="vtt">VTT Subtitles</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={processingOptions.enableSpeakerDiarization}
                  onChange={(e) => setProcessingOptions(prev => ({ ...prev, enableSpeakerDiarization: e.target.checked }))}
                />
              }
              label="Enable Speaker Diarization"
            />
          </Grid>

          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={processingOptions.enableStructuredAnalysis}
                  onChange={(e) => setProcessingOptions(prev => ({ ...prev, enableStructuredAnalysis: e.target.checked }))}
                />
              }
              label="Enable Structured Analysis"
            />
          </Grid>

          {processingOptions.enableStructuredAnalysis && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Custom Analysis Prompt"
                value={processingOptions.customPrompt || ''}
                onChange={(e) => setProcessingOptions(prev => ({ ...prev, customPrompt: e.target.value }))}
                placeholder="Enter custom instructions for structured analysis..."
              />
            </Grid>
          )}
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowSettings(false)}>Cancel</Button>
        <Button onClick={() => setShowSettings(false)} variant="contained">Save Settings</Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Media Upload & Processing
      </Typography>

      {renderDropzone()}
      {renderRecordingControls()}
      {renderFileList()}
      {renderSettingsDialog()}

      {files.some(f => f.status === 'processing') && (
        <Alert severity="info" sx={{ mt: 2 }}>
          Processing files... This may take a few minutes depending on file size and selected options.
        </Alert>
      )}
    </Box>
  );
};

export default MediaUpload;