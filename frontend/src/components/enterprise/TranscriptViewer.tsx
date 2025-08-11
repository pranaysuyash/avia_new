import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  AvatarGroup,
  Tooltip,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  TextField,
  Button,
  Divider,
  Alert,
  Badge,
  useTheme,
  alpha,
  Popover,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Comment as CommentIcon,
  Highlight as HighlightIcon,
  Task as TaskIcon,
  Lightbulb as LightbulbIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  Share as ShareIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  BarChart as ConfidenceIcon,
} from '@mui/icons-material';
import { useCollaboration } from '../../hooks/useCollaboration';
import { format } from 'date-fns';

interface Transcript {
  id: string;
  segments: TranscriptSegment[];
  entities: Record<string, Entity[]>;
  confidence: number;
  duration: number;
  wordCount: number;
  language: string;
  processingModel: string;
  speakers?: Speaker[];
}

interface TranscriptSegment {
  id: string;
  text: string;
  speaker?: Speaker;
  start: number;
  end: number;
  confidence: number;
  entities?: Entity[];
}

interface Speaker {
  id: string;
  label: string;
  color?: string;
}

interface Entity {
  text: string;
  type: string;
  confidence: number;
  start: number;
  end: number;
}

interface Annotation {
  id: string;
  segmentId: string;
  type: 'comment' | 'highlight' | 'action' | 'insight';
  text: string;
  author: string;
  timestamp: Date;
  position?: { start: number; end: number };
}

interface TranscriptViewerProps {
  transcript: Transcript;
  enableCollaboration?: boolean;
  enableAnnotations?: boolean;
  enableExport?: boolean;
  onSegmentClick?: (segment: TranscriptSegment) => void;
}

// Transcript Segment Component
const TranscriptSegment: React.FC<{
  segment: TranscriptSegment;
  annotations: Annotation[];
  searchQuery: string;
  highlightedEntities: Set<string>;
  onTextSelect: () => void;
  onClick?: () => void;
  renderHighlightedText: (text: string, entities?: Entity[]) => React.ReactNode;
  getConfidenceColor: (confidence: number) => string;
  formatTimestamp: (seconds: number) => string;
  speakerColors: string[];
  theme: any;
}> = ({
  segment,
  annotations,
  onTextSelect,
  onClick,
  renderHighlightedText,
  getConfidenceColor,
  formatTimestamp,
  speakerColors,
  theme,
}) => {
  const segmentRef = useRef<HTMLDivElement>(null);

  return (
    <Box
      ref={segmentRef}
      sx={{
        mb: 3,
        position: 'relative',
        p: 2,
        borderRadius: 1,
        transition: 'all 0.2s',
        '&:hover': {
          bgcolor: alpha(theme.palette.primary.main, 0.02),
        },
        cursor: onClick ? 'pointer' : 'default',
      }}
      onMouseUp={onTextSelect}
      onClick={onClick}
    >
      {/* Speaker and Timestamp */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        {segment.speaker && (
          <>
            <Avatar
              sx={{
                width: 28,
                height: 28,
                mr: 1,
                bgcolor: segment.speaker.color || speakerColors[parseInt(segment.speaker.id) % speakerColors.length],
                fontSize: '0.875rem',
              }}
            >
              {segment.speaker.label[0]}
            </Avatar>
            <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 'medium' }}>
              {segment.speaker.label}
            </Typography>
          </>
        )}
        <Typography variant="caption" color="text.secondary" sx={{ ml: segment.speaker ? 2 : 0 }}>
          {formatTimestamp(segment.start)} - {formatTimestamp(segment.end)}
        </Typography>

        {/* Confidence Indicator */}
        <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
          <Tooltip title={`Confidence: ${(segment.confidence * 100).toFixed(1)}%`}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <ConfidenceIcon sx={{ fontSize: 16, mr: 0.5, color: getConfidenceColor(segment.confidence) }} />
              <Typography variant="caption" sx={{ color: getConfidenceColor(segment.confidence) }}>
                {(segment.confidence * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Tooltip>
        </Box>
      </Box>

      {/* Transcript Text */}
      <Typography
        variant="body1"
        paragraph
        sx={{
          lineHeight: 1.8,
          mb: annotations.length > 0 ? 2 : 0,
        }}
      >
        {renderHighlightedText(segment.text, segment.entities)}
      </Typography>

      {/* Annotations */}
      {annotations.length > 0 && (
        <Box sx={{ mt: 2, pl: 2, borderLeft: `3px solid ${theme.palette.divider}` }}>
          {annotations.map((annotation) => (
            <AnnotationDisplay
              key={annotation.id}
              annotation={annotation}
              theme={theme}
            />
          ))}
        </Box>
      )}
    </Box>
  );
};

// Annotation Display Component
const AnnotationDisplay: React.FC<{
  annotation: Annotation;
  theme: any;
}> = ({ annotation, theme }) => {
  const getAnnotationIcon = () => {
    switch (annotation.type) {
      case 'comment':
        return <CommentIcon fontSize="small" />;
      case 'highlight':
        return <HighlightIcon fontSize="small" />;
      case 'action':
        return <TaskIcon fontSize="small" />;
      case 'insight':
        return <LightbulbIcon fontSize="small" />;
      default:
        return <CommentIcon fontSize="small" />;
    }
  };

  const getAnnotationColor = () => {
    switch (annotation.type) {
      case 'comment':
        return theme.palette.info.main;
      case 'highlight':
        return theme.palette.warning.main;
      case 'action':
        return theme.palette.error.main;
      case 'insight':
        return theme.palette.success.main;
      default:
        return theme.palette.grey[500];
    }
  };

  return (
    <Box
      sx={{
        mb: 1.5,
        p: 1.5,
        bgcolor: alpha(getAnnotationColor(), 0.05),
        borderRadius: 1,
        border: `1px solid ${alpha(getAnnotationColor(), 0.2)}`,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
        <Box sx={{ color: getAnnotationColor(), mt: 0.5 }}>
          {getAnnotationIcon()}
        </Box>
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Typography variant="caption" fontWeight="medium">
              {annotation.author}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {format(new Date(annotation.timestamp), 'MMM d, h:mm a')}
            </Typography>
          </Box>
          <Typography variant="body2">{annotation.text}</Typography>
        </Box>
      </Box>
    </Box>
  );
};

export const TranscriptViewer: React.FC<TranscriptViewerProps> = ({
  transcript,
  enableCollaboration = true,
  enableAnnotations = true,
  enableExport = true,
  onSegmentClick,
}) => {
  const theme = useTheme();
  const {
    collaborators,
    annotations,
    addAnnotation,
    updateAnnotation,
    deleteAnnotation,
  } = useCollaboration(transcript.id);

  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedEntities, setHighlightedEntities] = useState<Set<string>>(new Set());
  const [selectedText, setSelectedText] = useState<{
    text: string;
    segmentId: string;
    position: { x: number; y: number };
  } | null>(null);
  const [annotationMenuAnchor, setAnnotationMenuAnchor] = useState<null | HTMLElement>(null);

  const speakerColors = [
    theme.palette.error.main,
    theme.palette.info.main,
    theme.palette.success.main,
    theme.palette.warning.main,
    theme.palette.secondary.main,
  ];

  const toggleEntityHighlight = (entityType: string) => {
    const newHighlighted = new Set(highlightedEntities);
    if (newHighlighted.has(entityType)) {
      newHighlighted.delete(entityType);
    } else {
      newHighlighted.add(entityType);
    }
    setHighlightedEntities(newHighlighted);
  };

  const handleTextSelection = (segmentId: string) => {
    const selection = window.getSelection();
    if (!selection || selection.toString().trim() === '') return;

    const text = selection.toString();
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    setSelectedText({
      text,
      segmentId,
      position: { x: rect.x + rect.width / 2, y: rect.y },
    });
    setAnnotationMenuAnchor(document.body);
  };

  const handleAnnotate = (type: 'comment' | 'highlight' | 'action' | 'insight') => {
    if (!selectedText) return;

    addAnnotation({
      segmentId: selectedText.segmentId,
      type,
      text: selectedText.text,
      author: 'Current User',
      timestamp: new Date(),
    });

    setSelectedText(null);
    setAnnotationMenuAnchor(null);
  };

  const handleExport = (format: string) => {
    console.log('Exporting as', format);
  };

  const formatTimestamp = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    }
    return `${minutes}m ${secs}s`;
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.9) return theme.palette.success.main;
    if (confidence >= 0.7) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const renderHighlightedText = (text: string, entities: Entity[] = []) => {
    let processedText = text;
    const highlights: Array<{ start: number; end: number; type: string; text: string }> = [];

    highlightedEntities.forEach(entityType => {
      entities
        .filter(e => e.type === entityType)
        .forEach(entity => {
          const index = processedText.toLowerCase().indexOf(entity.text.toLowerCase());
          if (index !== -1) {
            highlights.push({
              start: index,
              end: index + entity.text.length,
              type: entityType,
              text: entity.text,
            });
          }
        });
    });

    if (searchQuery) {
      const searchIndex = processedText.toLowerCase().indexOf(searchQuery.toLowerCase());
      if (searchIndex !== -1) {
        highlights.push({
          start: searchIndex,
          end: searchIndex + searchQuery.length,
          type: 'search',
          text: searchQuery,
        });
      }
    }

    highlights.sort((a, b) => a.start - b.start);

    if (highlights.length === 0) return <span>{text}</span>;

    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    highlights.forEach((highlight, index) => {
      if (highlight.start > lastIndex) {
        elements.push(
          <span key={`text-${index}`}>{text.substring(lastIndex, highlight.start)}</span>
        );
      }

      const highlightStyle = {
        backgroundColor:
          highlight.type === 'search'
            ? alpha(theme.palette.warning.main, 0.3)
            : alpha(getEntityColor(highlight.type), 0.2),
        padding: '2px 4px',
        borderRadius: '4px',
        fontWeight: highlight.type === 'search' ? 'bold' : 'normal',
      };

      elements.push(
        <span key={`highlight-${index}`} style={highlightStyle}>
          {text.substring(highlight.start, highlight.end)}
        </span>
      );

      lastIndex = highlight.end;
    });

    if (lastIndex < text.length) {
      elements.push(<span key="text-end">{text.substring(lastIndex)}</span>);
    }

    return <>{elements}</>;
  };

  const getEntityColor = (type: string): string => {
    const colors: Record<string, string> = {
      person: theme.palette.primary.main,
      organization: theme.palette.secondary.main,
      location: theme.palette.success.main,
      date: theme.palette.warning.main,
      other: theme.palette.info.main,
    };
    return colors[type.toLowerCase()] || theme.palette.grey[500];
  };

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header with Collaboration Info */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          bgcolor: theme.palette.grey[50],
        }}
      >
        <Typography variant="h6" fontWeight="medium">
          Transcript Analysis
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {enableCollaboration && (
            <AvatarGroup max={4} sx={{ mr: 2 }}>
              {collaborators?.map((user: any) => (
                <Tooltip key={user.id} title={`${user.name} ${user.isActive ? '(Active)' : ''}`}>
                  <Badge
                    overlap="circular"
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                    variant="dot"
                    sx={{
                      '& .MuiBadge-badge': {
                        backgroundColor: user.isActive ? '#44b700' : 'transparent',
                        color: '#44b700',
                      },
                    }}
                  >
                    <Avatar
                      src={user.avatar}
                      sx={{
                        width: 32,
                        height: 32,
                        border: `2px solid ${theme.palette.background.paper}`,
                      }}
                    >
                      {user.name?.charAt(0)}
                    </Avatar>
                  </Badge>
                </Tooltip>
              ))}
            </AvatarGroup>
          )}

          <TextField
            size="small"
            placeholder="Search transcript..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
            sx={{ width: 200 }}
          />

          {enableExport && (
            <>
              <IconButton size="small" onClick={() => handleExport('pdf')}>
                <DownloadIcon />
              </IconButton>
              <IconButton size="small" onClick={() => window.print()}>
                <PrintIcon />
              </IconButton>
              <IconButton size="small">
                <ShareIcon />
              </IconButton>
            </>
          )}
        </Box>
      </Box>

      {/* Entity Filter Bar */}
      <Box sx={{ p: 2, bgcolor: 'grey.50', display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Typography variant="body2" sx={{ mr: 2, display: 'flex', alignItems: 'center' }}>
          Filter Entities:
        </Typography>
        {Object.entries(transcript.entities).map(([type, entities]) => (
          <Chip
            key={type}
            label={`${type} (${entities.length})`}
            size="small"
            color={highlightedEntities.has(type) ? 'primary' : 'default'}
            onClick={() => toggleEntityHighlight(type)}
            sx={{
              textTransform: 'capitalize',
              bgcolor: highlightedEntities.has(type)
                ? alpha(getEntityColor(type), 0.2)
                : 'default',
              color: highlightedEntities.has(type) ? getEntityColor(type) : 'inherit',
              border: `1px solid ${
                highlightedEntities.has(type) ? getEntityColor(type) : theme.palette.divider
              }`,
            }}
          />
        ))}
      </Box>

      {/* Main Transcript Content */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 3,
          position: 'relative',
        }}
      >
        {transcript.segments.map((segment) => (
          <TranscriptSegment
            key={segment.id}
            segment={segment}
            annotations={annotations?.filter((a: Annotation) => a.segmentId === segment.id) || []}
            searchQuery={searchQuery}
            highlightedEntities={highlightedEntities}
            onTextSelect={() => handleTextSelection(segment.id)}
            onClick={() => onSegmentClick?.(segment)}
            renderHighlightedText={renderHighlightedText}
            getConfidenceColor={getConfidenceColor}
            formatTimestamp={formatTimestamp}
            speakerColors={speakerColors}
            theme={theme}
          />
        ))}
      </Box>

      {/* Floating Annotation Menu */}
      <Popover
        open={Boolean(annotationMenuAnchor) && Boolean(selectedText)}
        anchorEl={annotationMenuAnchor}
        onClose={() => {
          setAnnotationMenuAnchor(null);
          setSelectedText(null);
        }}
        anchorReference="anchorPosition"
        anchorPosition={
          selectedText
            ? { top: selectedText.position.y - 50, left: selectedText.position.x }
            : undefined
        }
      >
        <Box sx={{ p: 1, display: 'flex', gap: 0.5 }}>
          <Tooltip title="Add Comment">
            <IconButton size="small" onClick={() => handleAnnotate('comment')}>
              <CommentIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Highlight">
            <IconButton size="small" onClick={() => handleAnnotate('highlight')}>
              <HighlightIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Create Action Item">
            <IconButton size="small" onClick={() => handleAnnotate('action')}>
              <TaskIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Mark as Insight">
            <IconButton size="small" onClick={() => handleAnnotate('insight')}>
              <LightbulbIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Popover>

      {/* Footer with Metadata */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          display: 'flex',
          justifyContent: 'space-between',
          bgcolor: 'grey.50',
        }}
      >
        <Box sx={{ display: 'flex', gap: 3 }}>
          <Typography variant="body2" color="text.secondary">
            Confidence: {(transcript.confidence * 100).toFixed(1)}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Duration: {formatDuration(transcript.duration)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Words: {transcript.wordCount}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            size="small"
            label={transcript.language}
            color="primary"
            variant="outlined"
          />
          <Chip
            size="small"
            label={transcript.processingModel}
            color="secondary"
            variant="outlined"
          />
        </Box>
      </Box>
    </Paper>
  );
};