import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Person,
  PersonAdd,
  Edit,
  Delete,
  PlayArrow,
  Timeline,
  VoiceChat,
  Settings,
  Download,
  Refresh,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

interface SpeakerSegment {
  start: number;
  end: number;
  speaker: string;
  confidence: number;
  text?: string;
  embedding?: number[];
}

interface SpeakerProfile {
  id: string;
  name: string;
  color: string;
  totalDuration: number;
  segmentCount: number;
  averageConfidence: number;
  voiceCharacteristics?: {
    pitch: number;
    energy: number;
    spectralCentroid: number;
  };
}

interface DiarizationResult {
  speakers: SpeakerProfile[];
  segments: SpeakerSegment[];
  totalDuration: number;
  confidence: number;
  method: string;
}

interface SpeakerDiarizationProps {
  audioUrl?: string;
  transcriptData?: any;
  onSpeakerUpdate?: (speakers: SpeakerProfile[]) => void;
  onSegmentClick?: (segment: SpeakerSegment) => void;
}

const SPEAKER_COLORS = [
  '#3f51b5', '#f44336', '#4caf50', '#ff9800', 
  '#9c27b0', '#00bcd4', '#795548', '#607d8b',
  '#e91e63', '#8bc34a', '#ffc107', '#673ab7'
];

const SpeakerDiarization: React.FC<SpeakerDiarizationProps> = ({
  audioUrl,
  transcriptData,
  onSpeakerUpdate,
  onSegmentClick,
}) => {
  const [diarizationResult, setDiarizationResult] = useState<DiarizationResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedSpeaker, setSelectedSpeaker] = useState<SpeakerProfile | null>(null);
  const [newSpeakerName, setNewSpeakerName] = useState('');
  const [diarizationMethod, setDiarizationMethod] = useState('whisperx');
  const [minSpeakers, setMinSpeakers] = useState(2);
  const [maxSpeakers, setMaxSpeakers] = useState(10);

  const processDiarization = async () => {
    if (!audioUrl) {
      setError('No audio URL provided');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch('/api/speaker-diarization/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio_url: audioUrl,
          method: diarizationMethod,
          min_speakers: minSpeakers,
          max_speakers: maxSpeakers,
          transcript_data: transcriptData,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process speaker diarization');
      }

      const result = await response.json();
      setDiarizationResult(result);
      onSpeakerUpdate?.(result.speakers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Diarization failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const updateSpeakerName = async (speakerId: string, newName: string) => {
    if (!diarizationResult) return;

    try {
      const response = await fetch('/api/speaker-diarization/update-speaker', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          speaker_id: speakerId,
          new_name: newName,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update speaker name');
      }

      // Update local state
      const updatedResult = {
        ...diarizationResult,
        speakers: diarizationResult.speakers.map(speaker =>
          speaker.id === speakerId ? { ...speaker, name: newName } : speaker
        ),
        segments: diarizationResult.segments.map(segment =>
          segment.speaker === speakerId ? { ...segment, speaker: newName } : segment
        ),
      };

      setDiarizationResult(updatedResult);
      onSpeakerUpdate?.(updatedResult.speakers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update speaker');
    }
  };

  const mergeSpeakers = async (speaker1Id: string, speaker2Id: string) => {
    if (!diarizationResult) return;

    try {
      const response = await fetch('/api/speaker-diarization/merge-speakers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          speaker1_id: speaker1Id,
          speaker2_id: speaker2Id,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to merge speakers');
      }

      const result = await response.json();
      setDiarizationResult(result);
      onSpeakerUpdate?.(result.speakers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to merge speakers');
    }
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

  const getSpeakerStats = () => {
    if (!diarizationResult) return [];

    return diarizationResult.speakers.map(speaker => ({
      name: speaker.name,
      duration: speaker.totalDuration,
      percentage: (speaker.totalDuration / diarizationResult.totalDuration) * 100,
      segments: speaker.segmentCount,
      color: speaker.color,
    }));
  };

  const handleEditSpeaker = (speaker: SpeakerProfile) => {
    setSelectedSpeaker(speaker);
    setNewSpeakerName(speaker.name);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = () => {
    if (selectedSpeaker && newSpeakerName.trim()) {
      updateSpeakerName(selectedSpeaker.id, newSpeakerName.trim());
      setEditDialogOpen(false);
      setSelectedSpeaker(null);
      setNewSpeakerName('');
    }
  };

  const exportDiarization = () => {
    if (!diarizationResult) return;

    const exportData = {
      speakers: diarizationResult.speakers,
      segments: diarizationResult.segments,
      metadata: {
        totalDuration: diarizationResult.totalDuration,
        confidence: diarizationResult.confidence,
        method: diarizationResult.method,
        exportedAt: new Date().toISOString(),
      },
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `speaker-diarization-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    if (audioUrl && !diarizationResult && !isProcessing) {
      processDiarization();
    }
  }, [audioUrl]);

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Speaker Diarization Failed</Typography>
        <Typography>{error}</Typography>
        <Button onClick={processDiarization} sx={{ mt: 1 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" display="flex" alignItems="center">
          <VoiceChat sx={{ mr: 1 }} />
          Speaker Diarization
        </Typography>
        <Box>
          <Button
            startIcon={<Refresh />}
            onClick={processDiarization}
            disabled={isProcessing}
            sx={{ mr: 1 }}
          >
            Reprocess
          </Button>
          {diarizationResult && (
            <Button
              startIcon={<Download />}
              onClick={exportDiarization}
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
              <VoiceChat sx={{ mr: 1 }} />
              <Typography variant="h6">Processing Speaker Diarization...</Typography>
            </Box>
            <LinearProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Analyzing audio for speaker identification using {diarizationMethod}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Configuration */}
      {!diarizationResult && !isProcessing && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Diarization Settings
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Method</InputLabel>
                  <Select
                    value={diarizationMethod}
                    onChange={(e) => setDiarizationMethod(e.target.value)}
                  >
                    <MenuItem value="whisperx">WhisperX (Recommended)</MenuItem>
                    <MenuItem value="pyannote">PyAnnote</MenuItem>
                    <MenuItem value="resemblyzer">Resemblyzer</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Min Speakers"
                  type="number"
                  value={minSpeakers}
                  onChange={(e) => setMinSpeakers(parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 20 }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Max Speakers"
                  type="number"
                  value={maxSpeakers}
                  onChange={(e) => setMaxSpeakers(parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 20 }}
                />
              </Grid>
            </Grid>
            <Button
              variant="contained"
              onClick={processDiarization}
              sx={{ mt: 2 }}
              disabled={!audioUrl}
            >
              Start Diarization
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {diarizationResult && (
        <>
          {/* Overview Stats */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Speakers Detected
                  </Typography>
                  <Typography variant="h4">
                    {diarizationResult.speakers.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Total Duration
                  </Typography>
                  <Typography variant="h4">
                    {formatDuration(diarizationResult.totalDuration)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Segments
                  </Typography>
                  <Typography variant="h4">
                    {diarizationResult.segments.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Confidence
                  </Typography>
                  <Typography variant="h4">
                    {(diarizationResult.confidence * 100).toFixed(1)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Speaker Statistics */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Speaking Time Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={getSpeakerStats()}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="duration"
                        nameKey="name"
                      >
                        {getSpeakerStats().map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <RechartsTooltip
                        formatter={(value: number) => [formatDuration(value), 'Duration']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Segment Count by Speaker
                  </Typography>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={getSpeakerStats()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <RechartsTooltip />
                      <Bar dataKey="segments" fill="#3f51b5" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Speaker Profiles */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Speaker Profiles
              </Typography>
              <List>
                {diarizationResult.speakers.map((speaker, index) => (
                  <React.Fragment key={speaker.id}>
                    <ListItem>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: speaker.color }}>
                          <Person />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="subtitle1">
                              {speaker.name}
                            </Typography>
                            <Chip
                              label={`${(speaker.totalDuration / diarizationResult.totalDuration * 100).toFixed(1)}%`}
                              size="small"
                              color="primary"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Duration: {formatDuration(speaker.totalDuration)} • 
                              Segments: {speaker.segmentCount} • 
                              Confidence: {(speaker.averageConfidence * 100).toFixed(1)}%
                            </Typography>
                            {speaker.voiceCharacteristics && (
                              <Box sx={{ mt: 1 }}>
                                <Chip label={`Pitch: ${speaker.voiceCharacteristics.pitch.toFixed(1)}Hz`} size="small" sx={{ mr: 0.5 }} />
                                <Chip label={`Energy: ${speaker.voiceCharacteristics.energy.toFixed(2)}`} size="small" sx={{ mr: 0.5 }} />
                              </Box>
                            )}
                          </Box>
                        }
                      />
                      <Box>
                        <IconButton onClick={() => handleEditSpeaker(speaker)}>
                          <Edit />
                        </IconButton>
                      </Box>
                    </ListItem>
                    {index < diarizationResult.speakers.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Speaker Timeline */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Speaker Timeline
              </Typography>
              <Box sx={{ height: 100, position: 'relative', border: '1px solid #e0e0e0', borderRadius: 1 }}>
                {diarizationResult.segments.map((segment, index) => {
                  const speaker = diarizationResult.speakers.find(s => s.name === segment.speaker);
                  const left = (segment.start / diarizationResult.totalDuration) * 100;
                  const width = ((segment.end - segment.start) / diarizationResult.totalDuration) * 100;
                  
                  return (
                    <Tooltip
                      key={index}
                      title={`${segment.speaker}: ${formatTime(segment.start)} - ${formatTime(segment.end)}`}
                    >
                      <Box
                        sx={{
                          position: 'absolute',
                          left: `${left}%`,
                          width: `${width}%`,
                          height: '100%',
                          backgroundColor: speaker?.color || '#gray',
                          cursor: 'pointer',
                          '&:hover': {
                            opacity: 0.8,
                          },
                        }}
                        onClick={() => onSegmentClick?.(segment)}
                      />
                    </Tooltip>
                  );
                })}
              </Box>
              <Box display="flex" justifyContent="space-between" mt={1}>
                <Typography variant="caption">0:00</Typography>
                <Typography variant="caption">
                  {formatTime(diarizationResult.totalDuration)}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </>
      )}

      {/* Edit Speaker Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)}>
        <DialogTitle>Edit Speaker</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Speaker Name"
            fullWidth
            variant="outlined"
            value={newSpeakerName}
            onChange={(e) => setNewSpeakerName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SpeakerDiarization;