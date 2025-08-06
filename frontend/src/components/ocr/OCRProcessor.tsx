/**
 * OCR Processor Component for React/Electron
 * Handles image and document OCR processing with drag-and-drop interface
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  CloudUpload,
  Description,
  Image as ImageIcon,
  Download,
  Delete,
  Visibility,
  Settings,
  Analytics,
  ExpandMore,
  ContentCopy,
  CheckCircle,
  Error as ErrorIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-toastify';

// Types
interface OCRResult {
  text: string;
  confidence: number;
  language: string;
  processing_time: number;
  word_count: number;
  line_count: number;
  bounding_boxes: BoundingBox[];
  metadata: Record<string, any>;
}

interface BoundingBox {
  text: string;
  confidence: number;
  bbox: [number, number, number, number];
}

interface DocumentResult {
  filename: string;
  total_pages: number;
  pages: DocumentPage[];
  combined_text: string;
  processing_time: number;
  metadata: Record<string, any>;
}

interface DocumentPage {
  page_number: number;
  text: string;
  confidence: number;
  tables?: any[];
}

interface ProcessingJob {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  result?: OCRResult | DocumentResult;
  error?: string;
  timestamp: Date;
}

interface Language {
  code: string;
  name: string;
}

const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'zh', name: 'Chinese (Simplified)' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'auto', name: 'Auto-detect' }
];

const OCRProcessor: React.FC = () => {
  // State management
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('en');
  const [extractTables, setExtractTables] = useState<boolean>(true);
  const [enhanceContrast, setEnhanceContrast] = useState<boolean>(true);
  const [denoiseImage, setDenoiseImage] = useState<boolean>(true);
  const [deskewImage, setDeskewImage] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<number>(0);
  const [previewDialog, setPreviewDialog] = useState<{
    open: boolean;
    job?: ProcessingJob;
  }>({ open: false });
  const [settingsDialog, setSettingsDialog] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Drag and drop configuration
  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach(file => {
      if (isValidFileType(file)) {
        addProcessingJob(file);
      } else {
        toast.error(`Unsupported file type: ${file.name}`);
      }
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'],
      'application/pdf': ['.pdf']
    },
    multiple: true
  });

  // File validation
  const isValidFileType = (file: File): boolean => {
    const validTypes = [
      'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp',
      'application/pdf'
    ];
    return validTypes.includes(file.type);
  };

  // Add processing job
  const addProcessingJob = (file: File) => {
    const job: ProcessingJob = {
      id: `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      filename: file.name,
      status: 'pending',
      progress: 0,
      timestamp: new Date()
    };

    setJobs(prev => [...prev, job]);
    processFile(job, file);
  };

  // Process file with OCR
  const processFile = async (job: ProcessingJob, file: File) => {
    try {
      // Update job status
      setJobs(prev => prev.map(j => 
        j.id === job.id ? { ...j, status: 'processing', progress: 10 } : j
      ));

      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', file);
      formData.append('language', selectedLanguage);
      formData.append('extract_tables', extractTables.toString());
      formData.append('enhance_contrast', enhanceContrast.toString());
      formData.append('denoise_image', denoiseImage.toString());
      formData.append('deskew_image', deskewImage.toString());

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setJobs(prev => prev.map(j => 
          j.id === job.id && j.progress < 90 
            ? { ...j, progress: j.progress + 10 } 
            : j
        ));
      }, 500);

      // Make API call to backend
      const response = await fetch('/api/ocr/process', {
        method: 'POST',
        body: formData
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      // Update job with result
      setJobs(prev => prev.map(j => 
        j.id === job.id 
          ? { 
              ...j, 
              status: 'completed', 
              progress: 100, 
              result: result.data 
            } 
          : j
      ));

      toast.success(`OCR completed for ${file.name}`);

    } catch (error) {
      console.error('OCR processing error:', error);
      
      setJobs(prev => prev.map(j => 
        j.id === job.id 
          ? { 
              ...j, 
              status: 'error', 
              progress: 0, 
              error: error instanceof Error ? error.message : 'Unknown error'
            } 
          : j
      ));

      toast.error(`OCR failed for ${file.name}`);
    }
  };

  // Handle file input change
  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      Array.from(files).forEach(file => {
        if (isValidFileType(file)) {
          addProcessingJob(file);
        } else {
          toast.error(`Unsupported file type: ${file.name}`);
        }
      });
    }
  };

  // Download result as text
  const downloadResult = (job: ProcessingJob) => {
    if (!job.result) return;

    const text = 'text' in job.result ? job.result.text : job.result.combined_text;
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${job.filename.split('.')[0]}_extracted.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Copy result to clipboard
  const copyToClipboard = async (job: ProcessingJob) => {
    if (!job.result) return;

    const text = 'text' in job.result ? job.result.text : job.result.combined_text;
    try {
      await navigator.clipboard.writeText(text);
      toast.success('Text copied to clipboard');
    } catch (error) {
      toast.error('Failed to copy text');
    }
  };

  // Delete job
  const deleteJob = (jobId: string) => {
    setJobs(prev => prev.filter(j => j.id !== jobId));
  };

  // Clear all jobs
  const clearAllJobs = () => {
    setJobs([]);
  };

  // Get job statistics
  const getJobStats = () => {
    const total = jobs.length;
    const completed = jobs.filter(j => j.status === 'completed').length;
    const processing = jobs.filter(j => j.status === 'processing').length;
    const errors = jobs.filter(j => j.status === 'error').length;
    
    return { total, completed, processing, errors };
  };

  // Render upload area
  const renderUploadArea = () => (
    <Paper
      {...getRootProps()}
      sx={{
        p: 4,
        textAlign: 'center',
        border: '2px dashed',
        borderColor: isDragActive ? 'primary.main' : 'grey.300',
        backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        '&:hover': {
          borderColor: 'primary.main',
          backgroundColor: 'action.hover'
        }
      }}
    >
      <input {...getInputProps()} />
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        multiple
        accept=".jpg,.jpeg,.png,.tiff,.tif,.bmp,.pdf"
        style={{ display: 'none' }}
      />
      
      <CloudUpload sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
      
      <Typography variant="h6" gutterBottom>
        {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
      </Typography>
      
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Supported formats: JPG, PNG, TIFF, BMP, PDF
      </Typography>
      
      <Button
        variant="outlined"
        onClick={() => fileInputRef.current?.click()}
        sx={{ mt: 2 }}
      >
        Browse Files
      </Button>
    </Paper>
  );

  // Render processing options
  const renderProcessingOptions = () => (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Processing Options
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Language</InputLabel>
              <Select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                label="Language"
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <MenuItem key={lang.code} value={lang.code}>
                    {lang.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={extractTables}
                    onChange={(e) => setExtractTables(e.target.checked)}
                  />
                }
                label="Extract Tables"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={enhanceContrast}
                    onChange={(e) => setEnhanceContrast(e.target.checked)}
                  />
                }
                label="Enhance Contrast"
              />
            </Box>
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={denoiseImage}
                    onChange={(e) => setDenoiseImage(e.target.checked)}
                  />
                }
                label="Denoise Image"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={deskewImage}
                    onChange={(e) => setDeskewImage(e.target.checked)}
                  />
                }
                label="Auto-correct Skew"
              />
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

  // Render job list
  const renderJobList = () => {
    const stats = getJobStats();
    
    return (
      <Box>
        {/* Statistics */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4">{stats.total}</Typography>
                <Typography variant="body2">Total</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">{stats.completed}</Typography>
                <Typography variant="body2">Completed</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">{stats.processing}</Typography>
                <Typography variant="body2">Processing</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="error.main">{stats.errors}</Typography>
                <Typography variant="body2">Errors</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Job list */}
        {jobs.length === 0 ? (
          <Alert severity="info">
            No files processed yet. Upload some files to get started.
          </Alert>
        ) : (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">Processing Queue</Typography>
              <Button
                variant="outlined"
                color="error"
                onClick={clearAllJobs}
                disabled={jobs.length === 0}
              >
                Clear All
              </Button>
            </Box>
            
            {jobs.map((job) => (
              <Accordion key={job.id}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                      {job.filename.toLowerCase().endsWith('.pdf') ? (
                        <Description sx={{ mr: 1 }} />
                      ) : (
                        <ImageIcon sx={{ mr: 1 }} />
                      )}
                      <Typography>{job.filename}</Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {job.status === 'completed' && (
                        <Chip
                          icon={<CheckCircle />}
                          label="Completed"
                          color="success"
                          size="small"
                        />
                      )}
                      {job.status === 'processing' && (
                        <Chip
                          label="Processing"
                          color="warning"
                          size="small"
                        />
                      )}
                      {job.status === 'error' && (
                        <Chip
                          icon={<ErrorIcon />}
                          label="Error"
                          color="error"
                          size="small"
                        />
                      )}
                      {job.status === 'pending' && (
                        <Chip
                          label="Pending"
                          color="default"
                          size="small"
                        />
                      )}
                    </Box>
                  </Box>
                </AccordionSummary>
                
                <AccordionDetails>
                  {job.status === 'processing' && (
                    <Box sx={{ mb: 2 }}>
                      <LinearProgress
                        variant="determinate"
                        value={job.progress}
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        Processing... {job.progress}%
                      </Typography>
                    </Box>
                  )}
                  
                  {job.status === 'error' && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                      {job.error}
                    </Alert>
                  )}
                  
                  {job.status === 'completed' && job.result && (
                    <Box>
                      <Grid container spacing={2} sx={{ mb: 2 }}>
                        <Grid item xs={3}>
                          <Typography variant="body2" color="text.secondary">
                            Confidence
                          </Typography>
                          <Typography variant="h6">
                            {'confidence' in job.result 
                              ? `${(job.result.confidence * 100).toFixed(1)}%`
                              : 'N/A'
                            }
                          </Typography>
                        </Grid>
                        <Grid item xs={3}>
                          <Typography variant="body2" color="text.secondary">
                            Words
                          </Typography>
                          <Typography variant="h6">
                            {'word_count' in job.result 
                              ? job.result.word_count.toLocaleString()
                              : job.result.combined_text.split(' ').length.toLocaleString()
                            }
                          </Typography>
                        </Grid>
                        <Grid item xs={3}>
                          <Typography variant="body2" color="text.secondary">
                            Processing Time
                          </Typography>
                          <Typography variant="h6">
                            {job.result.processing_time.toFixed(2)}s
                          </Typography>
                        </Grid>
                        <Grid item xs={3}>
                          <Typography variant="body2" color="text.secondary">
                            Language
                          </Typography>
                          <Typography variant="h6">
                            {'language' in job.result 
                              ? job.result.language.toUpperCase()
                              : 'N/A'
                            }
                          </Typography>
                        </Grid>
                      </Grid>
                      
                      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                        <Button
                          variant="outlined"
                          startIcon={<Visibility />}
                          onClick={() => setPreviewDialog({ open: true, job })}
                        >
                          Preview
                        </Button>
                        <Button
                          variant="outlined"
                          startIcon={<Download />}
                          onClick={() => downloadResult(job)}
                        >
                          Download
                        </Button>
                        <Button
                          variant="outlined"
                          startIcon={<ContentCopy />}
                          onClick={() => copyToClipboard(job)}
                        >
                          Copy
                        </Button>
                        <Button
                          variant="outlined"
                          color="error"
                          startIcon={<Delete />}
                          onClick={() => deleteJob(job.id)}
                        >
                          Delete
                        </Button>
                      </Box>
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}
      </Box>
    );
  };

  // Render preview dialog
  const renderPreviewDialog = () => (
    <Dialog
      open={previewDialog.open}
      onClose={() => setPreviewDialog({ open: false })}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        Text Preview - {previewDialog.job?.filename}
      </DialogTitle>
      <DialogContent>
        {previewDialog.job?.result && (
          <Box
            component="pre"
            sx={{
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              backgroundColor: 'grey.100',
              p: 2,
              borderRadius: 1,
              maxHeight: '400px',
              overflow: 'auto'
            }}
          >
            {'text' in previewDialog.job.result 
              ? previewDialog.job.result.text 
              : previewDialog.job.result.combined_text
            }
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setPreviewDialog({ open: false })}>
          Close
        </Button>
        {previewDialog.job && (
          <>
            <Button
              onClick={() => copyToClipboard(previewDialog.job!)}
              startIcon={<ContentCopy />}
            >
              Copy
            </Button>
            <Button
              onClick={() => downloadResult(previewDialog.job!)}
              startIcon={<Download />}
              variant="contained"
            >
              Download
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        📄 OCR Document Processing
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Extract text from images and PDF documents using advanced OCR technology
      </Typography>

      <Tabs
        value={activeTab}
        onChange={(_, newValue) => setActiveTab(newValue)}
        sx={{ mb: 3 }}
      >
        <Tab label="Upload & Process" />
        <Tab label="Results" />
        <Tab label="Analytics" />
      </Tabs>

      {activeTab === 0 && (
        <Box>
          {renderProcessingOptions()}
          {renderUploadArea()}
        </Box>
      )}

      {activeTab === 1 && renderJobList()}

      {activeTab === 2 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Processing Analytics
          </Typography>
          <Alert severity="info">
            Analytics dashboard coming soon...
          </Alert>
        </Box>
      )}

      {renderPreviewDialog()}
    </Box>
  );
};

export default OCRProcessor;