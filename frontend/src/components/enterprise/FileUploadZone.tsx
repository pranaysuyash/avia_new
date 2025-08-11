import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  LinearProgress,
  Chip,
  useTheme,
  alpha,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

interface FileUploadZoneProps {
  onFileSelect: (files: File[]) => void;
  accept?: string;
  maxSize?: number;
  multiple?: boolean;
  dragDropEnabled?: boolean;
}

export const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onFileSelect,
  accept = 'audio/*,video/*',
  maxSize = 5000000000, // 5GB
  multiple = true,
  dragDropEnabled = true,
}) => {
  const theme = useTheme();
  const [uploadedFiles, setUploadedFiles] = React.useState<File[]>([]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setUploadedFiles(acceptedFiles);
      onFileSelect(acceptedFiles);
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: accept.split(',').reduce((acc, curr) => {
      acc[curr.trim()] = [];
      return acc;
    }, {} as Record<string, string[]>),
    maxSize,
    multiple,
    disabled: !dragDropEnabled,
  });

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const removeFile = (index: number) => {
    const newFiles = [...uploadedFiles];
    newFiles.splice(index, 1);
    setUploadedFiles(newFiles);
    onFileSelect(newFiles);
  };

  return (
    <Box>
      <Paper
        {...getRootProps()}
        sx={{
          p: 3,
          border: '2px dashed',
          borderColor: isDragActive
            ? theme.palette.primary.main
            : isDragReject
            ? theme.palette.error.main
            : theme.palette.divider,
          borderRadius: 2,
          bgcolor: isDragActive
            ? alpha(theme.palette.primary.main, 0.05)
            : isDragReject
            ? alpha(theme.palette.error.main, 0.05)
            : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.2s',
          '&:hover': {
            borderColor: theme.palette.primary.main,
            bgcolor: alpha(theme.palette.primary.main, 0.02),
          },
        }}
      >
        <input {...getInputProps()} />
        <Box sx={{ textAlign: 'center' }}>
          <CloudUploadIcon
            sx={{
              fontSize: 48,
              color: isDragActive
                ? theme.palette.primary.main
                : theme.palette.text.secondary,
              mb: 2,
            }}
          />
          <Typography variant="h6" gutterBottom>
            {isDragActive
              ? 'Drop files here'
              : 'Drag & drop files here'}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            or click to browse
          </Typography>
          <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
            Supported formats: Audio (MP3, WAV, M4A) • Video (MP4, MOV)
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Max file size: {formatFileSize(maxSize)}
          </Typography>
        </Box>
      </Paper>

      {uploadedFiles.length > 0 && (
        <List sx={{ mt: 2 }}>
          {uploadedFiles.map((file, index) => (
            <ListItem
              key={index}
              sx={{
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 1,
                mb: 1,
              }}
              secondaryAction={
                <IconButton edge="end" onClick={() => removeFile(index)}>
                  <DeleteIcon />
                </IconButton>
              }
            >
              <ListItemIcon>
                <FileIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary={file.name}
                secondary={formatFileSize(file.size)}
              />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
};

// ProcessingOptions Component
interface ProcessingOptionsProps {
  options: {
    enhance: boolean;
    transcribe: boolean;
    extractEntities: boolean;
    generateSummary: boolean;
    detectSpeakers: boolean;
  };
  onChange: (options: any) => void;
}

export const ProcessingOptions: React.FC<ProcessingOptionsProps> = ({
  options,
  onChange,
}) => {
  const theme = useTheme();

  const handleToggle = (key: string) => {
    onChange({
      ...options,
      [key]: !options[key as keyof typeof options],
    });
  };

  const optionsList = [
    { key: 'enhance', label: 'Audio Enhancement', description: 'Reduce noise and improve clarity' },
    { key: 'transcribe', label: 'Transcription', description: 'Convert speech to text' },
    { key: 'extractEntities', label: 'Entity Extraction', description: 'Identify people, places, dates' },
    { key: 'generateSummary', label: 'Generate Summary', description: 'Create AI-powered summary' },
    { key: 'detectSpeakers', label: 'Speaker Detection', description: 'Identify different speakers' },
  ];

  return (
    <Box>
      {optionsList.map((option) => (
        <Paper
          key={option.key}
          sx={{
            p: 1.5,
            mb: 1,
            cursor: 'pointer',
            border: `1px solid ${
              options[option.key as keyof typeof options]
                ? theme.palette.primary.main
                : theme.palette.divider
            }`,
            bgcolor: options[option.key as keyof typeof options]
              ? alpha(theme.palette.primary.main, 0.05)
              : 'background.paper',
            transition: 'all 0.2s',
            '&:hover': {
              borderColor: theme.palette.primary.main,
            },
          }}
          onClick={() => handleToggle(option.key)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="body2" fontWeight="medium">
                {option.label}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {option.description}
              </Typography>
            </Box>
            {options[option.key as keyof typeof options] && (
              <CheckCircleIcon color="primary" fontSize="small" />
            )}
          </Box>
        </Paper>
      ))}
    </Box>
  );
};

// ProcessingMetrics Component
interface ProcessingMetricsProps {
  metrics: any;
  compact?: boolean;
}

export const ProcessingMetrics: React.FC<ProcessingMetricsProps> = ({
  metrics,
  compact = false,
}) => {
  const theme = useTheme();

  if (!metrics) return null;

  if (compact) {
    return (
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Box>
          <Typography variant="caption" sx={{ opacity: 0.8 }}>
            Processing
          </Typography>
          <Typography variant="h6" sx={{ color: 'white' }}>
            {metrics.filesProcessed || 0} files
          </Typography>
        </Box>
        <Box>
          <Typography variant="caption" sx={{ opacity: 0.8 }}>
            Time
          </Typography>
          <Typography variant="h6" sx={{ color: 'white' }}>
            {metrics.processingTime || '0'}s
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Processing Metrics
      </Typography>
      {/* Add detailed metrics display */}
    </Box>
  );
};

// QualityAssessment Component
export const QualityAssessment: React.FC<{ quality: any }> = ({ quality }) => {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Quality Assessment
      </Typography>
      {/* Add quality assessment display */}
    </Box>
  );
};

// ResultsSummary Component
interface ResultsSummaryProps {
  transcription?: string;
  entities?: any;
  sentiment?: any;
  keywords?: string[];
  summary?: string;
}

export const ResultsSummary: React.FC<ResultsSummaryProps> = ({
  transcription,
  entities,
  sentiment,
  keywords,
  summary,
}) => {
  const theme = useTheme();

  return (
    <Box>
      {summary && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom color="primary">
            Summary
          </Typography>
          <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
            {summary}
          </Typography>
        </Box>
      )}

      {entities && Object.keys(entities).length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom color="primary">
            Entities Detected
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {Object.entries(entities).map(([type, items]: [string, any]) => (
              <Chip
                key={type}
                label={`${type}: ${items.length}`}
                size="small"
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      )}

      {keywords && keywords.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom color="primary">
            Keywords
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {keywords.map((keyword, index) => (
              <Chip key={index} label={keyword} size="small" />
            ))}
          </Box>
        </Box>
      )}

      {sentiment && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom color="primary">
            Sentiment
          </Typography>
          <Chip
            label={sentiment.label}
            color={sentiment.score > 0 ? 'success' : sentiment.score < 0 ? 'error' : 'default'}
            size="small"
          />
        </Box>
      )}
    </Box>
  );
};

// ExportOptions Component
interface ExportOptionsProps {
  results: any;
  formats: string[];
  onExport: (format: string) => void;
}

export const ExportOptions: React.FC<ExportOptionsProps> = ({
  results,
  formats,
  onExport,
}) => {
  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Export Options
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {formats.map((format) => (
          <Chip
            key={format}
            label={`Export as ${format}`}
            onClick={() => onExport(format)}
            clickable
            variant="outlined"
            size="small"
          />
        ))}
      </Box>
    </Box>
  );
};
