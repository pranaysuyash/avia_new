import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Switch,
  FormControlLabel,
  Grid,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  AutoFixHigh,
  Timeline,
  Edit,
  Add,
  Delete,
  PlayArrow,
  Settings,
  Download,
  Refresh,
  ContentCut,
  MergeType,
  Splitscreen,
} from '@mui/icons-material';
import { Timeline as TimelineChart, TimelineItem, TimelineSeparator, TimelineConnector, TimelineContent, TimelineDot } from '@mui/lab';

interface Segment {
  id: string;
  start: number;
  end: number;
  text: string;
  type: 'semantic' | 'speaker' | 'time' | 'silence' | 'manual';
  confidence: number;
  speaker?: string;
  topic?: string;
  keywords?: string[];
  summary?: string;
}

interface ChunkingSettings {
  method: 'semantic' | 'speaker' | 'time' | 'silence' | 'hybrid';
  minSegmentLength: number;
  maxSegmentLength: number;
  mergeSimilar: boolean;
  enableSilenceRefinement: boolean;
  preserveManualChapters: boolean;
  semanticThreshold: number;
  silenceThreshold: number;
}

interface IntelligentChunkingProps {
  transcriptData?: any;
  audioUrl?: string;
  onSegmentsUpdate?: (segments: Segment[]) => void;
  onSegmentSelect?: (segment: Segment) => void;
}

const IntelligentChunking: React.FC<IntelligentChunkingProps> = ({
  transcriptData,
  audioUrl,
  onSegmentsUpdate,
  onSegmentSelect,
}) => {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<ChunkingSettings>({
    method: 'hybrid',
    minSegmentLength: 30,
    maxSegmentLength: 300,
    mergeSimilar: true,
    enableSilenceRefinement: true,
    preserveManualChapters: true,
    semanticThreshold: 0.7,
    silenceThreshold: 1.0,
  });
  const [selectedSegment, setSelectedSegment] = useState<Segment | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [newSegmentText, setNewSegmentText] = useState('');
  const [manualChapters, setManualChapters] = useState<Array<{ time: number; title: string }>>([]);
  const [addChapterDialogOpen, setAddChapterDialogOpen] = useState(false);
  const [newChapterTime, setNewChapterTime] = useState(0);
  const [newChapterTitle, setNewChapterTitle] = useState('');

  const processSegmentation = async () => {
    if (!transcriptData) {
      setError('No transcript data provided');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch('/api/segmentation/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript_data: transcriptData,
          audio_url: audioUrl,
          settings: settings,
          manual_chapters: manualChapters,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process segmentation');
      }

      const result = await response.json();
      setSegments(result.segments);
      onSegmentsUpdate?.(result.segments);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Segmentation failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const mergeSegments = async (segment1Id: string, segment2Id: string) => {
    try {
      const response = await fetch('/api/segmentation/merge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment1_id: segment1Id,
          segment2_id: segment2Id,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to merge segments');
      }

      const result = await response.json();
      setSegments(result.segments);
      onSegmentsUpdate?.(result.segments);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to merge segments');
    }
  };

  const splitSegment = async (segmentId: string, splitTime: number) => {
    try {
      const response = await fetch('/api/segmentation/split', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment_id: segmentId,
          split_time: splitTime,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to split segment');
      }

      const result = await response.json();
      setSegments(result.segments);
      onSegmentsUpdate?.(result.segments);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to split segment');
    }
  };

  const updateSegment = async (segmentId: string, updates: Partial<Segment>) => {
    try {
      const response = await fetch('/api/segmentation/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment_id: segmentId,
          updates: updates,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update segment');
      }

      const result = await response.json();
      setSegments(result.segments);
      onSegmentsUpdate?.(result.segments);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update segment');
    }
  };

  const addManualChapter = () => {
    if (newChapterTitle.trim() && newChapterTime >= 0) {
      const newChapter = { time: newChapterTime, title: newChapterTitle.trim() };
      setManualChapters([...manualChapters, newChapter].sort((a, b) => a.time - b.time));
      setAddChapterDialogOpen(false);
      setNewChapterTime(0);
      setNewChapterTitle('');
    }
  };

  const removeManualChapter = (index: number) => {
    setManualChapters(manualChapters.filter((_, i) => i !== index));
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  const getSegmentTypeColor = (type: string) => {
    switch (type) {
      case 'semantic': return '#3f51b5';
      case 'speaker': return '#4caf50';
      case 'time': return '#ff9800';
      case 'silence': return '#9e9e9e';
      case 'manual': return '#e91e63';
      default: return '#757575';
    }
  };

  const getSegmentTypeIcon = (type: string) => {
    switch (type) {
      case 'semantic': return <AutoFixHigh />;
      case 'speaker': return <PlayArrow />;
      case 'time': return <Timeline />;
      case 'silence': return <ContentCut />;
      case 'manual': return <Edit />;
      default: return <Splitscreen />;
    }
  };

  const handleEditSegment = (segment: Segment) => {
    setSelectedSegment(segment);
    setNewSegmentText(segment.text);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = () => {
    if (selectedSegment && newSegmentText.trim()) {
      updateSegment(selectedSegment.id, { text: newSegmentText.trim() });
      setEditDialogOpen(false);
      setSelectedSegment(null);
      setNewSegmentText('');
    }
  };

  const exportSegments = () => {
    const exportData = {
      segments: segments,
      settings: settings,
      manual_chapters: manualChapters,
      metadata: {
        total_segments: segments.length,
        total_duration: segments.length > 0 ? Math.max(...segments.map(s => s.end)) : 0,
        exported_at: new Date().toISOString(),
      },
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `segments-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getSegmentStats = () => {
    const typeStats = segments.reduce((acc, segment) => {
      acc[segment.type] = (acc[segment.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const avgDuration = segments.length > 0 
      ? segments.reduce((sum, s) => sum + (s.end - s.start), 0) / segments.length 
      : 0;

    const avgConfidence = segments.length > 0
      ? segments.reduce((sum, s) => sum + s.confidence, 0) / segments.length
      : 0;

    return { typeStats, avgDuration, avgConfidence };
  };

  useEffect(() => {
    if (transcriptData && segments.length === 0 && !isProcessing) {
      processSegmentation();
    }
  }, [transcriptData]);

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Segmentation Failed</Typography>
        <Typography>{error}</Typography>
        <Button onClick={processSegmentation} sx={{ mt: 1 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  const stats = getSegmentStats();

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" display="flex" alignItems="center">
          <Splitscreen sx={{ mr: 1 }} />
          Intelligent Chunking
        </Typography>
        <Box>
          <Button
            startIcon={<Refresh />}
            onClick={processSegmentation}
            disabled={isProcessing}
            sx={{ mr: 1 }}
          >
            Reprocess
          </Button>
          {segments.length > 0 && (
            <Button
              startIcon={<Download />}
              onClick={exportSegments}
              variant="outlined"
            >
              Export
            </Button>
          )}
        </Box>
      </Box>

      {/* Processing Status */}
      {isProcessing && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <AutoFixHigh sx={{ mr: 1 }} />
              <Typography variant="h6">Processing Intelligent Segmentation...</Typography>
            </Box>
            <LinearProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Analyzing content using {settings.method} method
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Settings */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Segmentation Settings
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Method</InputLabel>
                <Select
                  value={settings.method}
                  onChange={(e) => setSettings({ ...settings, method: e.target.value as any })}
                >
                  <MenuItem value="semantic">Semantic</MenuItem>
                  <MenuItem value="speaker">Speaker-based</MenuItem>
                  <MenuItem value="time">Time-based</MenuItem>
                  <MenuItem value="silence">Silence-based</MenuItem>
                  <MenuItem value="hybrid">Hybrid (Recommended)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Min Length (seconds)"
                type="number"
                value={settings.minSegmentLength}
                onChange={(e) => setSettings({ ...settings, minSegmentLength: parseInt(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Max Length (seconds)"
                type="number"
                value={settings.maxSegmentLength}
                onChange={(e) => setSettings({ ...settings, maxSegmentLength: parseInt(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Semantic Threshold"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.1 }}
                value={settings.semanticThreshold}
                onChange={(e) => setSettings({ ...settings, semanticThreshold: parseFloat(e.target.value) })}
              />
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.mergeSimilar}
                  onChange={(e) => setSettings({ ...settings, mergeSimilar: e.target.checked })}
                />
              }
              label="Merge Similar Segments"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableSilenceRefinement}
                  onChange={(e) => setSettings({ ...settings, enableSilenceRefinement: e.target.checked })}
                />
              }
              label="Enable Silence Refinement"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={settings.preserveManualChapters}
                  onChange={(e) => setSettings({ ...settings, preserveManualChapters: e.target.checked })}
                />
              }
              label="Preserve Manual Chapters"
            />
          </Box>
        </CardContent>
      </Card>

      {/* Manual Chapters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Manual Chapters</Typography>
            <Button
              startIcon={<Add />}
              onClick={() => setAddChapterDialogOpen(true)}
              size="small"
            >
              Add Chapter
            </Button>
          </Box>
          
          {manualChapters.length > 0 ? (
            <List dense>
              {manualChapters.map((chapter, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Edit />
                  </ListItemIcon>
                  <ListItemText
                    primary={chapter.title}
                    secondary={`Time: ${formatTime(chapter.time)}`}
                  />
                  <IconButton onClick={() => removeManualChapter(index)} size="small">
                    <Delete />
                  </IconButton>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No manual chapters added
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Segment Statistics */}
      {segments.length > 0 && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Segments
                </Typography>
                <Typography variant="h4">
                  {segments.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Avg Duration
                </Typography>
                <Typography variant="h4">
                  {formatDuration(stats.avgDuration)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Avg Confidence
                </Typography>
                <Typography variant="h4">
                  {(stats.avgConfidence * 100).toFixed(1)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Method Used
                </Typography>
                <Typography variant="h6">
                  {settings.method.charAt(0).toUpperCase() + settings.method.slice(1)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Segment Type Distribution */}
      {segments.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Segment Types
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {Object.entries(stats.typeStats).map(([type, count]) => (
                <Chip
                  key={type}
                  icon={getSegmentTypeIcon(type)}
                  label={`${type.charAt(0).toUpperCase() + type.slice(1)}: ${count}`}
                  sx={{ backgroundColor: getSegmentTypeColor(type), color: 'white' }}
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Segments List */}
      {segments.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Segments ({segments.length})
            </Typography>
            
            <List>
              {segments.map((segment, index) => (
                <React.Fragment key={segment.id}>
                  <ListItem>
                    <ListItemIcon>
                      <Box
                        sx={{
                          width: 40,
                          height: 40,
                          borderRadius: '50%',
                          backgroundColor: getSegmentTypeColor(segment.type),
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                        }}
                      >
                        {getSegmentTypeIcon(segment.type)}
                      </Box>
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="subtitle1">
                            Segment {index + 1}
                          </Typography>
                          <Chip
                            label={segment.type}
                            size="small"
                            sx={{ backgroundColor: getSegmentTypeColor(segment.type), color: 'white' }}
                          />
                          <Chip
                            label={`${(segment.confidence * 100).toFixed(1)}%`}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {formatTime(segment.start)} - {formatTime(segment.end)} 
                            ({formatDuration(segment.end - segment.start)})
                            {segment.speaker && ` • Speaker: ${segment.speaker}`}
                            {segment.topic && ` • Topic: ${segment.topic}`}
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 1 }}>
                            {segment.text.length > 150 
                              ? `${segment.text.substring(0, 150)}...` 
                              : segment.text}
                          </Typography>
                          {segment.keywords && segment.keywords.length > 0 && (
                            <Box sx={{ mt: 1 }}>
                              {segment.keywords.slice(0, 5).map((keyword, idx) => (
                                <Chip
                                  key={idx}
                                  label={keyword}
                                  size="small"
                                  variant="outlined"
                                  sx={{ mr: 0.5, mb: 0.5 }}
                                />
                              ))}
                            </Box>
                          )}
                        </Box>
                      }
                    />
                    <Box>
                      <IconButton onClick={() => handleEditSegment(segment)}>
                        <Edit />
                      </IconButton>
                      <IconButton onClick={() => onSegmentSelect?.(segment)}>
                        <PlayArrow />
                      </IconButton>
                    </Box>
                  </ListItem>
                  {index < segments.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Edit Segment Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Segment</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Segment Text"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={newSegmentText}
            onChange={(e) => setNewSegmentText(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Chapter Dialog */}
      <Dialog open={addChapterDialogOpen} onClose={() => setAddChapterDialogOpen(false)}>
        <DialogTitle>Add Manual Chapter</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Chapter Title"
            fullWidth
            variant="outlined"
            value={newChapterTitle}
            onChange={(e) => setNewChapterTitle(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Time (seconds)"
            type="number"
            fullWidth
            variant="outlined"
            value={newChapterTime}
            onChange={(e) => setNewChapterTime(parseFloat(e.target.value))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddChapterDialogOpen(false)}>Cancel</Button>
          <Button onClick={addManualChapter} variant="contained">
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default IntelligentChunking;