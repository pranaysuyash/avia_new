import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Chip,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Tabs,
  Tab,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Badge,
  Avatar,
  LinearProgress,
  Alert,
  Menu,
  MenuItem,
  Slider
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Download,
  Share,
  Edit,
  Search,
  Person,
  Business,
  LocationOn,
  Event,
  Psychology,
  ExpandMore,
  VolumeUp,
  VolumeOff,
  Speed,
  Bookmark,
  Comment,
  Visibility,
  VisibilityOff,
  ContentCopy,
  Print,
  Translate,
  Analytics,
  Timeline
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

interface TranscriptSegment {
  id: string;
  start: number;
  end: number;
  text: string;
  speaker?: string;
  confidence: number;
  words?: Array<{
    word: string;
    start: number;
    end: number;
    confidence: number;
  }>;
}

interface Entity {
  text: string;
  label: string;
  start: number;
  end: number;
  confidence: number;
  description?: string;
}

interface TranscriptionData {
  id: string;
  title: string;
  duration: number;
  language: string;
  confidence: number;
  segments: TranscriptSegment[];
  entities: Entity[];
  summary?: string;
  keyPoints?: string[];
  speakers?: Array<{
    id: string;
    name: string;
    segments: number;
    duration: number;
  }>;
  metadata: {
    createdAt: string;
    fileSize: number;
    processingTime: number;
    model: string;
  };
}

interface TranscriptionResultsProps {
  data: TranscriptionData;
  audioUrl?: string;
  onEdit?: (segmentId: string, newText: string) => void;
  onExport?: (format: string) => void;
  onShare?: () => void;
}

export const TranscriptionResults: React.FC<TranscriptionResultsProps> = ({
  data,
  audioUrl,
  onEdit,
  onExport,
  onShare
}) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [volume, setVolume] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);
  const [editingSegment, setEditingSegment] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [showTimestamps, setShowTimestamps] = useState(true);
  const [showConfidence, setShowConfidence] = useState(false);
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);
  const [highlightedEntities, setHighlightedEntities] = useState<string[]>([]);

  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.addEventListener('timeupdate', handleTimeUpdate);
      audioRef.current.addEventListener('ended', () => setIsPlaying(false));
    }

    return () => {
      if (audioRef.current) {
        audioRef.current.removeEventListener('timeupdate', handleTimeUpdate);
        audioRef.current.removeEventListener('ended', () => setIsPlaying(false));
      }
    };
  }, []);

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const togglePlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const seekTo = (time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const changePlaybackRate = (rate: number) => {
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
      setPlaybackRate(rate);
    }
  };

  const changeVolume = (newVolume: number) => {
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
      setVolume(newVolume);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getEntityColor = (label: string): string => {
    const colors: Record<string, string> = {
      'PERSON': theme.palette.primary.main,
      'ORG': theme.palette.secondary.main,
      'LOC': theme.palette.success.main,
      'DATE': theme.palette.warning.main,
      'TIME': theme.palette.info.main,
      'MONEY': theme.palette.error.main,
    };
    return colors[label] || theme.palette.grey[500];
  };

  const highlightText = (text: string, entities: Entity[]): React.ReactNode => {
    if (!entities.length) return text;

    let lastIndex = 0;
    const elements: React.ReactNode[] = [];

    entities
      .filter(entity => highlightedEntities.length === 0 || highlightedEntities.includes(entity.label))
      .sort((a, b) => a.start - b.start)
      .forEach((entity, index) => {
        // Add text before entity
        if (entity.start > lastIndex) {
          elements.push(text.slice(lastIndex, entity.start));
        }

        // Add highlighted entity
        elements.push(
          <Chip
            key={index}
            label={entity.text}
            size="small"
            sx={{
              backgroundColor: getEntityColor(entity.label) + '20',
              color: getEntityColor(entity.label),
              fontWeight: 'bold',
              mx: 0.5
            }}
          />
        );

        lastIndex = entity.end;
      });

    // Add remaining text
    if (lastIndex < text.length) {
      elements.push(text.slice(lastIndex));
    }

    return elements;
  };

  const filteredSegments = data.segments.filter(segment =>
    searchQuery === '' || segment.text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleEditSegment = (segmentId: string, text: string) => {
    setEditingSegment(segmentId);
    setEditText(text);
  };

  const saveEdit = () => {
    if (editingSegment && onEdit) {
      onEdit(editingSegment, editText);
    }
    setEditingSegment(null);
    setEditText('');
  };

  const renderAudioControls = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <IconButton onClick={togglePlayback} color="primary" size="large">
            {isPlaying ? <Pause /> : <PlayArrow />}
          </IconButton>
          
          <Box sx={{ flex: 1 }}>
            <Slider
              value={currentTime}
              max={data.duration}
              onChange={(_, value) => seekTo(value as number)}
              valueLabelDisplay="auto"
              valueLabelFormat={formatTime}
            />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
              <Typography variant="caption">{formatTime(currentTime)}</Typography>
              <Typography variant="caption">{formatTime(data.duration)}</Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Playback Speed">
              <Button
                variant="outlined"
                size="small"
                startIcon={<Speed />}
                onClick={(e) => {
                  const rates = [0.5, 0.75, 1, 1.25, 1.5, 2];
                  const currentIndex = rates.indexOf(playbackRate);
                  const nextRate = rates[(currentIndex + 1) % rates.length];
                  changePlaybackRate(nextRate);
                }}
              >
                {playbackRate}x
              </Button>
            </Tooltip>

            <Tooltip title="Volume">
              <Box sx={{ display: 'flex', alignItems: 'center', width: 100 }}>
                <IconButton size="small" onClick={() => changeVolume(volume === 0 ? 1 : 0)}>
                  {volume === 0 ? <VolumeOff /> : <VolumeUp />}
                </IconButton>
                <Slider
                  value={volume}
                  max={1}
                  step={0.1}
                  onChange={(_, value) => changeVolume(value as number)}
                  size="small"
                />
              </Box>
            </Tooltip>
          </Box>
        </Box>

        {audioUrl && (
          <audio ref={audioRef} src={audioUrl} preload="metadata" />
        )}
      </CardContent>
    </Card>
  );

  const renderTranscriptTab = () => (
    <Box>
      {/* Search and Controls */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField
          placeholder="Search transcript..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          size="small"
          sx={{ minWidth: 300 }}
        />
        
        <Button
          variant="outlined"
          startIcon={showTimestamps ? <Visibility /> : <VisibilityOff />}
          onClick={() => setShowTimestamps(!showTimestamps)}
          size="small"
        >
          Timestamps
        </Button>
        
        <Button
          variant="outlined"
          startIcon={<Analytics />}
          onClick={() => setShowConfidence(!showConfidence)}
          size="small"
        >
          Confidence
        </Button>
      </Box>

      {/* Transcript Segments */}
      <Paper sx={{ maxHeight: 600, overflow: 'auto' }}>
        <List>
          {filteredSegments.map((segment, index) => (
            <React.Fragment key={segment.id}>
              <ListItem
                sx={{
                  cursor: 'pointer',
                  backgroundColor: selectedSegment === segment.id ? 'action.selected' : 'transparent',
                  '&:hover': { backgroundColor: 'action.hover' }
                }}
                onClick={() => {
                  setSelectedSegment(segment.id);
                  seekTo(segment.start);
                }}
              >
                <ListItemIcon>
                  {segment.speaker && (
                    <Avatar sx={{ width: 32, height: 32, fontSize: 14 }}>
                      {segment.speaker.charAt(0)}
                    </Avatar>
                  )}
                </ListItemIcon>
                
                <ListItemText
                  primary={
                    <Box>
                      {showTimestamps && (
                        <Typography variant="caption" color="text.secondary" sx={{ mr: 2 }}>
                          {formatTime(segment.start)} - {formatTime(segment.end)}
                        </Typography>
                      )}
                      {segment.speaker && (
                        <Chip
                          label={segment.speaker}
                          size="small"
                          sx={{ mr: 1, mb: 1 }}
                        />
                      )}
                      {showConfidence && (
                        <Chip
                          label={`${(segment.confidence * 100).toFixed(0)}%`}
                          size="small"
                          color={segment.confidence > 0.8 ? 'success' : segment.confidence > 0.6 ? 'warning' : 'error'}
                          sx={{ mr: 1, mb: 1 }}
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    editingSegment === segment.id ? (
                      <Box sx={{ mt: 1 }}>
                        <TextField
                          fullWidth
                          multiline
                          value={editText}
                          onChange={(e) => setEditText(e.target.value)}
                          size="small"
                        />
                        <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                          <Button size="small" onClick={saveEdit}>Save</Button>
                          <Button size="small" onClick={() => setEditingSegment(null)}>Cancel</Button>
                        </Box>
                      </Box>
                    ) : (
                      <Typography variant="body1" sx={{ mt: 1 }}>
                        {highlightText(segment.text, data.entities.filter(e => 
                          e.start >= segment.start && e.end <= segment.end
                        ))}
                      </Typography>
                    )
                  }
                />
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditSegment(segment.id, segment.text);
                    }}
                  >
                    <Edit />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigator.clipboard.writeText(segment.text);
                    }}
                  >
                    <ContentCopy />
                  </IconButton>
                </Box>
              </ListItem>
              {index < filteredSegments.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </Paper>
    </Box>
  );

  const renderEntitiesTab = () => (
    <Box>
      {/* Entity Type Filter */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>Entity Types</Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {Array.from(new Set(data.entities.map(e => e.label))).map(label => (
            <Chip
              key={label}
              label={label}
              onClick={() => {
                setHighlightedEntities(prev =>
                  prev.includes(label)
                    ? prev.filter(l => l !== label)
                    : [...prev, label]
                );
              }}
              color={highlightedEntities.includes(label) ? 'primary' : 'default'}
              variant={highlightedEntities.includes(label) ? 'filled' : 'outlined'}
            />
          ))}
          <Button
            size="small"
            onClick={() => setHighlightedEntities([])}
            disabled={highlightedEntities.length === 0}
          >
            Clear All
          </Button>
        </Box>
      </Box>

      {/* Entities List */}
      <Grid container spacing={2}>
        {Array.from(new Set(data.entities.map(e => e.label))).map(label => {
          const entitiesOfType = data.entities.filter(e => e.label === label);
          const uniqueEntities = Array.from(new Set(entitiesOfType.map(e => e.text)))
            .map(text => entitiesOfType.find(e => e.text === text)!);

          return (
            <Grid item xs={12} md={6} key={label}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    {label === 'PERSON' && <Person sx={{ mr: 1 }} />}
                    {label === 'ORG' && <Business sx={{ mr: 1 }} />}
                    {label === 'LOC' && <LocationOn sx={{ mr: 1 }} />}
                    {label === 'DATE' && <Event sx={{ mr: 1 }} />}
                    {label}
                    <Badge badgeContent={uniqueEntities.length} color="primary" sx={{ ml: 1 }} />
                  </Typography>
                  
                  <List dense>
                    {uniqueEntities.slice(0, 10).map((entity, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemText
                          primary={entity.text}
                          secondary={`Confidence: ${(entity.confidence * 100).toFixed(0)}%`}
                        />
                      </ListItem>
                    ))}
                    {uniqueEntities.length > 10 && (
                      <ListItem sx={{ px: 0 }}>
                        <ListItemText
                          primary={`... and ${uniqueEntities.length - 10} more`}
                          sx={{ fontStyle: 'italic' }}
                        />
                      </ListItem>
                    )}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );

  const renderSummaryTab = () => (
    <Box>
      {data.summary && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Summary</Typography>
            <Typography variant="body1">{data.summary}</Typography>
          </CardContent>
        </Card>
      )}

      {data.keyPoints && data.keyPoints.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Key Points</Typography>
            <List>
              {data.keyPoints.map((point, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Psychology />
                  </ListItemIcon>
                  <ListItemText primary={point} />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {data.speakers && data.speakers.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Speaker Statistics</Typography>
            <Grid container spacing={2}>
              {data.speakers.map((speaker) => (
                <Grid item xs={12} sm={6} md={4} key={speaker.id}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Avatar sx={{ mx: 'auto', mb: 1 }}>{speaker.name.charAt(0)}</Avatar>
                    <Typography variant="subtitle1">{speaker.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {speaker.segments} segments
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {formatTime(speaker.duration)} speaking time
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  const renderMetadataTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>File Information</Typography>
            <List>
              <ListItem>
                <ListItemText primary="Title" secondary={data.title} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Duration" secondary={formatTime(data.duration)} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Language" secondary={data.language.toUpperCase()} />
              </ListItem>
              <ListItem>
                <ListItemText primary="File Size" secondary={`${(data.metadata.fileSize / 1024 / 1024).toFixed(2)} MB`} />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Processing Information</Typography>
            <List>
              <ListItem>
                <ListItemText primary="Overall Confidence" secondary={`${(data.confidence * 100).toFixed(1)}%`} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Processing Time" secondary={`${data.metadata.processingTime}s`} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Model Used" secondary={data.metadata.model} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Created At" secondary={new Date(data.metadata.createdAt).toLocaleString()} />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">{data.title}</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={(e) => setExportMenuAnchor(e.currentTarget)}
          >
            Export
          </Button>
          <Button
            variant="outlined"
            startIcon={<Share />}
            onClick={onShare}
          >
            Share
          </Button>
        </Box>
      </Box>

      {/* Audio Controls */}
      {audioUrl && renderAudioControls()}

      {/* Main Content Tabs */}
      <Paper>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Transcript" icon={<Timeline />} iconPosition="start" />
          <Tab label="Entities" icon={<Psychology />} iconPosition="start" />
          <Tab label="Summary" icon={<Analytics />} iconPosition="start" />
          <Tab label="Metadata" icon={<Event />} iconPosition="start" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && renderTranscriptTab()}
          {activeTab === 1 && renderEntitiesTab()}
          {activeTab === 2 && renderSummaryTab()}
          {activeTab === 3 && renderMetadataTab()}
        </Box>
      </Paper>

      {/* Export Menu */}
      <Menu
        anchorEl={exportMenuAnchor}
        open={Boolean(exportMenuAnchor)}
        onClose={() => setExportMenuAnchor(null)}
      >
        <MenuItem onClick={() => { onExport?.('txt'); setExportMenuAnchor(null); }}>
          Plain Text
        </MenuItem>
        <MenuItem onClick={() => { onExport?.('json'); setExportMenuAnchor(null); }}>
          JSON
        </MenuItem>
        <MenuItem onClick={() => { onExport?.('srt'); setExportMenuAnchor(null); }}>
          SRT Subtitles
        </MenuItem>
        <MenuItem onClick={() => { onExport?.('vtt'); setExportMenuAnchor(null); }}>
          VTT Subtitles
        </MenuItem>
        <MenuItem onClick={() => { onExport?.('docx'); setExportMenuAnchor(null); }}>
          Word Document
        </MenuItem>
        <MenuItem onClick={() => { onExport?.('pdf'); setExportMenuAnchor(null); }}>
          PDF
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default TranscriptionResults;