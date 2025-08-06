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
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Tabs,
  Tab,
  Badge,
  Tooltip,
  Menu,
  Switch,
  FormControlLabel,
  Slider,
  Snackbar,
  Drawer,
  AppBar,
  Toolbar,
  SpeedDial,
  SpeedDialIcon,
  SpeedDialAction,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ToggleButton,
  ToggleButtonGroup,
  Backdrop,
  Fade,
  Zoom,
  Grow,
  Collapse,
} from '@mui/material';
import {
  CloudUpload,
  Image as ImageIcon,
  PictureAsPdf,
  Description,
  TextFields,
  Scanner,
  Search,
  FilterList,
  Settings,
  Language,
  Translate,
  Code,
  TableChart,
  FormatListBulleted,
  Download,
  Save,
  Share,
  History,
  Refresh,
  Delete,
  Edit,
  ContentCopy,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Info,
  ExpandMore,
  ChevronRight,
  Folder,
  FolderOpen,
  InsertDriveFile,
  PhotoCamera,
  CameraAlt,
  Crop,
  RotateLeft,
  RotateRight,
  ZoomIn,
  ZoomOut,
  Fullscreen,
  FullscreenExit,
  Brightness6,
  Contrast,
  Tune,
  AutoFixHigh,
  FindInPage,
  SelectAll,
  HighlightAlt,
  CropFree,
  Straighten,
  CompareArrows,
  ViewColumn,
  ViewStream,
  Dashboard,
  Analytics,
  Speed,
  Memory,
  Storage,
  CloudSync,
  Backup,
  RestorePage,
  PlayArrow,
  Pause,
  Stop,
  SkipNext,
  Queue,
  Assignment,
  AssignmentTurnedIn,
  BatchPrediction,
  ModelTraining,
  Psychology,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { HotKeys } from 'react-hotkeys';
import { Line, Bar, Doughnut, Scatter } from 'react-chartjs-2';
import Tesseract from 'tesseract.js';
import * as pdfjsLib from 'pdfjs-dist';
import { fabric } from 'fabric';

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

interface OCRDocument {
  id: string;
  name: string;
  type: 'image' | 'pdf' | 'scan';
  path: string;
  size: number;
  pages?: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  result?: OCRResult;
  thumbnail?: string;
  metadata?: DocumentMetadata;
  createdAt: Date;
  processedAt?: Date;
}

interface OCRResult {
  text: string;
  confidence: number;
  language: string;
  blocks: TextBlock[];
  tables?: TableData[];
  metadata?: ResultMetadata;
  processingTime: number;
}

interface TextBlock {
  id: string;
  text: string;
  confidence: number;
  bbox: BoundingBox;
  words: Word[];
  type: 'paragraph' | 'heading' | 'list' | 'table' | 'other';
}

interface Word {
  text: string;
  confidence: number;
  bbox: BoundingBox;
}

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface TableData {
  rows: string[][];
  confidence: number;
  bbox: BoundingBox;
}

interface DocumentMetadata {
  width: number;
  height: number;
  dpi: number;
  colorSpace: string;
  format: string;
}

interface ResultMetadata {
  wordsCount: number;
  charactersCount: number;
  linesCount: number;
  averageConfidence: number;
  languages: string[];
}

interface ProcessingSettings {
  language: string[];
  enhanceImage: boolean;
  deskew: boolean;
  removeNoise: boolean;
  binarize: boolean;
  preserveLayout: boolean;
  detectTables: boolean;
  detectColumns: boolean;
  outputFormat: 'text' | 'json' | 'pdf' | 'docx';
  confidenceThreshold: number;
  batchMode: boolean;
  autoRotate: boolean;
  pageSegmentationMode: string;
}

interface ProcessingStats {
  totalDocuments: number;
  processedDocuments: number;
  failedDocuments: number;
  totalPages: number;
  averageConfidence: number;
  averageProcessingTime: number;
  successRate: number;
}

const keyMap = {
  UPLOAD: 'ctrl+o',
  PROCESS: 'ctrl+p',
  SAVE: 'ctrl+s',
  EXPORT: 'ctrl+e',
  DELETE: 'delete',
  SELECT_ALL: 'ctrl+a',
  COPY: 'ctrl+c',
  ZOOM_IN: 'ctrl+plus',
  ZOOM_OUT: 'ctrl+minus',
  TOGGLE_FULLSCREEN: 'f11',
};

const OCRProcessorDesktop: React.FC = () => {
  const [documents, setDocuments] = useState<OCRDocument[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [currentDocument, setCurrentDocument] = useState<OCRDocument | null>(null);
  const [processing, setProcessing] = useState(false);
  const [processingQueue, setProcessingQueue] = useState<string[]>([]);
  const [selectedTab, setSelectedTab] = useState(0);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'details'>('grid');
  const [settings, setSettings] = useState<ProcessingSettings>({
    language: ['eng'],
    enhanceImage: true,
    deskew: true,
    removeNoise: true,
    binarize: false,
    preserveLayout: true,
    detectTables: true,
    detectColumns: true,
    outputFormat: 'text',
    confidenceThreshold: 60,
    batchMode: false,
    autoRotate: true,
    pageSegmentationMode: '3',
  });

  const [drawerOpen, setDrawerOpen] = useState(true);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [resultsDialogOpen, setResultsDialogOpen] = useState(false);
  const [statsDialogOpen, setStatsDialogOpen] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [zoom, setZoom] = useState(100);
  const [selectedText, setSelectedText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterLanguage, setFilterLanguage] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'warning' | 'info' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricCanvasRef = useRef<fabric.Canvas | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const workerRef = useRef<Tesseract.Worker | null>(null);

  useEffect(() => {
    initializeOCRWorker();
    initializeFabricCanvas();

    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
      }
      if (fabricCanvasRef.current) {
        fabricCanvasRef.current.dispose();
      }
    };
  }, []);

  const initializeOCRWorker = async () => {
    try {
      const worker = await Tesseract.createWorker({
        logger: (m) => {
          if (m.status === 'recognizing text') {
            const progress = Math.round(m.progress * 100);
            updateDocumentProgress(m.workerId || '', progress);
          }
        },
      });

      await worker.loadLanguage('eng+fra+deu+spa');
      await worker.initialize('eng');
      workerRef.current = worker;
    } catch (error) {
      console.error('Failed to initialize OCR worker:', error);
      showSnackbar('Failed to initialize OCR engine', 'error');
    }
  };

  const initializeFabricCanvas = () => {
    if (canvasRef.current) {
      fabricCanvasRef.current = new fabric.Canvas(canvasRef.current, {
        selection: true,
        preserveObjectStacking: true,
      });
    }
  };

  const updateDocumentProgress = (docId: string, progress: number) => {
    setDocuments(prev => prev.map(doc =>
      doc.id === docId ? { ...doc, progress } : doc
    ));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'],
      'application/pdf': ['.pdf'],
    },
    onDrop: handleFileDrop,
    multiple: true,
  });

  async function handleFileDrop(acceptedFiles: File[]) {
    const newDocuments: OCRDocument[] = [];

    for (const file of acceptedFiles) {
      const id = `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const type = file.type.startsWith('image/') ? 'image' : 'pdf';
      
      // Create thumbnail for images
      let thumbnail: string | undefined;
      if (type === 'image') {
        thumbnail = await createImageThumbnail(file);
      }

      const document: OCRDocument = {
        id,
        name: file.name,
        type,
        path: URL.createObjectURL(file),
        size: file.size,
        status: 'pending',
        progress: 0,
        thumbnail,
        createdAt: new Date(),
      };

      // Get PDF page count
      if (type === 'pdf') {
        const pageCount = await getPDFPageCount(file);
        document.pages = pageCount;
      }

      newDocuments.push(document);
    }

    setDocuments(prev => [...prev, ...newDocuments]);
    showSnackbar(`Added ${newDocuments.length} document(s) to queue`, 'success');
  }

  const createImageThumbnail = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');
          if (!ctx) return;

          const maxSize = 200;
          const scale = Math.min(maxSize / img.width, maxSize / img.height);
          canvas.width = img.width * scale;
          canvas.height = img.height * scale;

          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          resolve(canvas.toDataURL('image/jpeg', 0.8));
        };
        img.src = e.target?.result as string;
      };
      reader.readAsDataURL(file);
    });
  };

  const getPDFPageCount = async (file: File): Promise<number> => {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
    return pdf.numPages;
  };

  const processDocuments = async () => {
    const documentsToProcess = selectedDocuments.length > 0
      ? documents.filter(doc => selectedDocuments.includes(doc.id))
      : documents.filter(doc => doc.status === 'pending');

    if (documentsToProcess.length === 0) {
      showSnackbar('No documents to process', 'warning');
      return;
    }

    setProcessing(true);
    setProcessingQueue(documentsToProcess.map(doc => doc.id));

    for (const document of documentsToProcess) {
      try {
        await processDocument(document);
      } catch (error) {
        console.error(`Failed to process ${document.name}:`, error);
        updateDocumentStatus(document.id, 'failed');
      }
    }

    setProcessing(false);
    setProcessingQueue([]);
    showSnackbar('Processing completed', 'success');
  };

  const processDocument = async (document: OCRDocument) => {
    updateDocumentStatus(document.id, 'processing');
    const startTime = Date.now();

    try {
      let result: OCRResult;
      
      if (document.type === 'pdf') {
        result = await processPDF(document);
      } else {
        result = await processImage(document);
      }

      result.processingTime = Date.now() - startTime;

      setDocuments(prev => prev.map(doc =>
        doc.id === document.id
          ? {
              ...doc,
              status: 'completed',
              progress: 100,
              result,
              processedAt: new Date(),
            }
          : doc
      ));
    } catch (error) {
      throw error;
    }
  };

  const processImage = async (document: OCRDocument): Promise<OCRResult> => {
    if (!workerRef.current) {
      throw new Error('OCR worker not initialized');
    }

    // Load and preprocess image if needed
    let imageData = document.path;
    if (settings.enhanceImage) {
      imageData = await enhanceImage(document.path);
    }

    // Set OCR parameters
    await workerRef.current.setParameters({
      tessedit_pageseg_mode: settings.pageSegmentationMode,
      preserve_interword_spaces: '1',
    });

    // Perform OCR
    const { data } = await workerRef.current.recognize(imageData);

    // Process results
    const blocks = processTextBlocks(data);
    const tables = settings.detectTables ? detectTables(blocks) : undefined;

    return {
      text: data.text,
      confidence: data.confidence,
      language: data.language || 'eng',
      blocks,
      tables,
      metadata: {
        wordsCount: data.words.length,
        charactersCount: data.text.length,
        linesCount: data.lines.length,
        averageConfidence: data.confidence,
        languages: [data.language || 'eng'],
      },
      processingTime: 0,
    };
  };

  const processPDF = async (document: OCRDocument): Promise<OCRResult> => {
    const arrayBuffer = await fetch(document.path).then(res => res.arrayBuffer());
    const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
    
    const results: OCRResult[] = [];
    
    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
      const page = await pdf.getPage(pageNum);
      const viewport = page.getViewport({ scale: 2.0 });
      
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      if (!context) continue;
      
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      
      await page.render({
        canvasContext: context,
        viewport: viewport,
      }).promise;
      
      const imageData = canvas.toDataURL('image/png');
      const pageResult = await processImage({
        ...document,
        path: imageData,
      });
      
      results.push(pageResult);
      
      // Update progress
      const progress = (pageNum / pdf.numPages) * 100;
      updateDocumentProgress(document.id, progress);
    }
    
    // Combine results from all pages
    return combineOCRResults(results);
  };

  const enhanceImage = async (imagePath: string): Promise<string> => {
    // Image enhancement logic (placeholder)
    // In real implementation, use image processing libraries
    return imagePath;
  };

  const processTextBlocks = (data: any): TextBlock[] => {
    const blocks: TextBlock[] = [];
    
    data.blocks.forEach((block: any, blockIndex: number) => {
      const words: Word[] = [];
      let blockText = '';
      
      block.paragraphs.forEach((paragraph: any) => {
        paragraph.words.forEach((word: any) => {
          const wordText = word.symbols.map((s: any) => s.text).join('');
          words.push({
            text: wordText,
            confidence: word.confidence,
            bbox: {
              x: word.bbox.x0,
              y: word.bbox.y0,
              width: word.bbox.x1 - word.bbox.x0,
              height: word.bbox.y1 - word.bbox.y0,
            },
          });
          blockText += wordText + ' ';
        });
      });
      
      blocks.push({
        id: `block_${blockIndex}`,
        text: blockText.trim(),
        confidence: block.confidence,
        bbox: {
          x: block.bbox.x0,
          y: block.bbox.y0,
          width: block.bbox.x1 - block.bbox.x0,
          height: block.bbox.y1 - block.bbox.y0,
        },
        words,
        type: detectBlockType(blockText),
      });
    });
    
    return blocks;
  };

  const detectBlockType = (text: string): TextBlock['type'] => {
    // Simple heuristics for block type detection
    if (text.length < 50 && /^[A-Z]/.test(text)) return 'heading';
    if (/^\d+\./.test(text) || /^[•\-\*]/.test(text)) return 'list';
    if (/\t/.test(text) || /\|/.test(text)) return 'table';
    return 'paragraph';
  };

  const detectTables = (blocks: TextBlock[]): TableData[] => {
    // Table detection logic (placeholder)
    return [];
  };

  const combineOCRResults = (results: OCRResult[]): OCRResult => {
    const combinedText = results.map(r => r.text).join('\n\n');
    const allBlocks = results.flatMap(r => r.blocks);
    const allTables = results.flatMap(r => r.tables || []);
    const avgConfidence = results.reduce((sum, r) => sum + r.confidence, 0) / results.length;
    
    return {
      text: combinedText,
      confidence: avgConfidence,
      language: results[0].language,
      blocks: allBlocks,
      tables: allTables.length > 0 ? allTables : undefined,
      metadata: {
        wordsCount: results.reduce((sum, r) => sum + (r.metadata?.wordsCount || 0), 0),
        charactersCount: combinedText.length,
        linesCount: combinedText.split('\n').length,
        averageConfidence: avgConfidence,
        languages: [...new Set(results.flatMap(r => r.metadata?.languages || []))],
      },
      processingTime: 0,
    };
  };

  const updateDocumentStatus = (docId: string, status: OCRDocument['status']) => {
    setDocuments(prev => prev.map(doc =>
      doc.id === docId ? { ...doc, status } : doc
    ));
  };

  const exportResults = async () => {
    const completedDocs = documents.filter(doc => doc.status === 'completed' && doc.result);
    
    if (completedDocs.length === 0) {
      showSnackbar('No completed documents to export', 'warning');
      return;
    }
    
    // Export logic based on format
    switch (settings.outputFormat) {
      case 'text':
        exportAsText(completedDocs);
        break;
      case 'json':
        exportAsJSON(completedDocs);
        break;
      case 'pdf':
        exportAsPDF(completedDocs);
        break;
      case 'docx':
        exportAsDocx(completedDocs);
        break;
    }
  };

  const exportAsText = (docs: OCRDocument[]) => {
    const content = docs.map(doc => 
      `=== ${doc.name} ===\n\n${doc.result?.text || ''}\n\n`
    ).join('\n');
    
    downloadFile(content, 'ocr-results.txt', 'text/plain');
  };

  const exportAsJSON = (docs: OCRDocument[]) => {
    const data = docs.map(doc => ({
      document: doc.name,
      result: doc.result,
      metadata: doc.metadata,
      processedAt: doc.processedAt,
    }));
    
    downloadFile(JSON.stringify(data, null, 2), 'ocr-results.json', 'application/json');
  };

  const exportAsPDF = async (docs: OCRDocument[]) => {
    // PDF export logic (placeholder)
    showSnackbar('PDF export not implemented', 'info');
  };

  const exportAsDocx = async (docs: OCRDocument[]) => {
    // DOCX export logic (placeholder)
    showSnackbar('DOCX export not implemented', 'info');
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    showSnackbar('Export completed', 'success');
  };

  const deleteDocuments = () => {
    const toDelete = selectedDocuments.length > 0 ? selectedDocuments : [currentDocument?.id].filter(Boolean);
    
    setDocuments(prev => prev.filter(doc => !toDelete.includes(doc.id)));
    setSelectedDocuments([]);
    setCurrentDocument(null);
    showSnackbar(`Deleted ${toDelete.length} document(s)`, 'success');
  };

  const calculateStats = (): ProcessingStats => {
    const completed = documents.filter(doc => doc.status === 'completed');
    const failed = documents.filter(doc => doc.status === 'failed');
    
    return {
      totalDocuments: documents.length,
      processedDocuments: completed.length,
      failedDocuments: failed.length,
      totalPages: documents.reduce((sum, doc) => sum + (doc.pages || 1), 0),
      averageConfidence: completed.reduce((sum, doc) => sum + (doc.result?.confidence || 0), 0) / (completed.length || 1),
      averageProcessingTime: completed.reduce((sum, doc) => sum + (doc.result?.processingTime || 0), 0) / (completed.length || 1),
      successRate: (completed.length / (documents.length || 1)) * 100,
    };
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info' = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handlers = {
    UPLOAD: () => fileInputRef.current?.click(),
    PROCESS: () => processDocuments(),
    SAVE: () => exportResults(),
    DELETE: () => deleteDocuments(),
    SELECT_ALL: () => setSelectedDocuments(documents.map(d => d.id)),
    ZOOM_IN: () => setZoom(prev => Math.min(prev + 10, 200)),
    ZOOM_OUT: () => setZoom(prev => Math.max(prev - 10, 50)),
    TOGGLE_FULLSCREEN: () => setFullscreen(prev => !prev),
  };

  const speedDialActions = [
    { icon: <CloudUpload />, name: 'Upload Files', action: () => fileInputRef.current?.click() },
    { icon: <PhotoCamera />, name: 'Scan Document', action: () => {} },
    { icon: <BatchPrediction />, name: 'Batch Process', action: () => processDocuments() },
    { icon: <Settings />, name: 'Settings', action: () => setSettingsDialogOpen(true) },
    { icon: <Analytics />, name: 'Statistics', action: () => setStatsDialogOpen(true) },
  ];

  return (
    <HotKeys keyMap={keyMap} handlers={handlers}>
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,.pdf"
          style={{ display: 'none' }}
          onChange={(e) => e.target.files && handleFileDrop(Array.from(e.target.files))}
        />

        {/* Sidebar */}
        <Drawer
          variant="persistent"
          anchor="left"
          open={drawerOpen}
          sx={{
            width: drawerOpen ? 280 : 0,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 280,
              boxSizing: 'border-box',
            },
          }}
        >
          <Toolbar>
            <Typography variant="h6" noWrap component="div">
              OCR Processor
            </Typography>
          </Toolbar>
          <Divider />
          
          {/* Document List */}
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Documents ({documents.length})
            </Typography>
            
            <List dense>
              {documents.map((doc) => (
                <ListItem
                  key={doc.id}
                  button
                  selected={currentDocument?.id === doc.id}
                  onClick={() => setCurrentDocument(doc)}
                >
                  <ListItemIcon>
                    {doc.type === 'pdf' ? <PictureAsPdf /> : <ImageIcon />}
                  </ListItemIcon>
                  <ListItemText
                    primary={doc.name}
                    secondary={
                      <Box>
                        <Chip
                          label={doc.status}
                          size="small"
                          color={
                            doc.status === 'completed' ? 'success' :
                            doc.status === 'processing' ? 'warning' :
                            doc.status === 'failed' ? 'error' : 'default'
                          }
                        />
                        {doc.status === 'processing' && (
                          <LinearProgress
                            variant="determinate"
                            value={doc.progress}
                            sx={{ mt: 0.5 }}
                          />
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedDocuments([doc.id]);
                        deleteDocuments();
                      }}
                    >
                      <Delete />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Box>
          
          {/* Processing Stats */}
          <Box sx={{ p: 2, mt: 'auto' }}>
            <Paper elevation={2} sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Quick Stats
              </Typography>
              <Box>
                <Typography variant="caption" display="block">
                  Processed: {documents.filter(d => d.status === 'completed').length}
                </Typography>
                <Typography variant="caption" display="block">
                  Failed: {documents.filter(d => d.status === 'failed').length}
                </Typography>
                <Typography variant="caption" display="block">
                  Pending: {documents.filter(d => d.status === 'pending').length}
                </Typography>
              </Box>
            </Paper>
          </Box>
        </Drawer>

        {/* Main Content */}
        <Box component="main" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          {/* App Bar */}
          <AppBar position="static" color="default" elevation={1}>
            <Toolbar>
              <IconButton
                edge="start"
                onClick={() => setDrawerOpen(!drawerOpen)}
                sx={{ mr: 2 }}
              >
                <Menu />
              </IconButton>
              
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                {currentDocument ? currentDocument.name : 'Desktop OCR Processor'}
              </Typography>
              
              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={(_, value) => value && setViewMode(value)}
                size="small"
                sx={{ mr: 2 }}
              >
                <ToggleButton value="grid">
                  <Dashboard />
                </ToggleButton>
                <ToggleButton value="list">
                  <ViewStream />
                </ToggleButton>
                <ToggleButton value="details">
                  <ViewColumn />
                </ToggleButton>
              </ToggleButtonGroup>
              
              <IconButton onClick={() => setFullscreen(!fullscreen)}>
                {fullscreen ? <FullscreenExit /> : <Fullscreen />}
              </IconButton>
            </Toolbar>
          </AppBar>

          {/* Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={selectedTab} onChange={(_, value) => setSelectedTab(value)}>
              <Tab label="Documents" icon={<Folder />} />
              <Tab label="Preview" icon={<FindInPage />} />
              <Tab label="Results" icon={<TextFields />} />
              <Tab label="Settings" icon={<Settings />} />
            </Tabs>
          </Box>

          {/* Tab Content */}
          <Box sx={{ flexGrow: 1, overflow: 'auto', p: 3 }}>
            {selectedTab === 0 && (
              /* Documents Tab */
              <Box>
                {/* Drop Zone */}
                <Paper
                  {...getRootProps()}
                  sx={{
                    p: 4,
                    mb: 3,
                    textAlign: 'center',
                    cursor: 'pointer',
                    backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
                    border: '2px dashed',
                    borderColor: isDragActive ? 'primary.main' : 'divider',
                  }}
                >
                  <input {...getInputProps()} />
                  <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    or click to select files (Images, PDFs)
                  </Typography>
                  <Button variant="contained" sx={{ mt: 2 }}>
                    Browse Files
                  </Button>
                </Paper>

                {/* Document Grid/List */}
                {viewMode === 'grid' ? (
                  <Grid container spacing={2}>
                    {documents.map((doc) => (
                      <Grid item xs={12} sm={6} md={4} lg={3} key={doc.id}>
                        <Card
                          sx={{
                            cursor: 'pointer',
                            border: selectedDocuments.includes(doc.id) ? 2 : 0,
                            borderColor: 'primary.main',
                          }}
                          onClick={() => setCurrentDocument(doc)}
                        >
                          <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                              {doc.type === 'pdf' ? (
                                <PictureAsPdf sx={{ mr: 1 }} />
                              ) : (
                                <ImageIcon sx={{ mr: 1 }} />
                              )}
                              <Typography variant="subtitle2" noWrap>
                                {doc.name}
                              </Typography>
                            </Box>
                            
                            {doc.thumbnail && (
                              <Box
                                component="img"
                                src={doc.thumbnail}
                                sx={{
                                  width: '100%',
                                  height: 150,
                                  objectFit: 'cover',
                                  mb: 1,
                                  borderRadius: 1,
                                }}
                              />
                            )}
                            
                            <Chip
                              label={doc.status}
                              size="small"
                              color={
                                doc.status === 'completed' ? 'success' :
                                doc.status === 'processing' ? 'warning' :
                                doc.status === 'failed' ? 'error' : 'default'
                              }
                              sx={{ mb: 1 }}
                            />
                            
                            {doc.status === 'processing' && (
                              <LinearProgress
                                variant="determinate"
                                value={doc.progress}
                              />
                            )}
                            
                            {doc.result && (
                              <Typography variant="caption" display="block">
                                Confidence: {Math.round(doc.result.confidence)}%
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                ) : (
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Name</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Confidence</TableCell>
                          <TableCell>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {documents.map((doc) => (
                          <TableRow
                            key={doc.id}
                            hover
                            selected={selectedDocuments.includes(doc.id)}
                            onClick={() => setCurrentDocument(doc)}
                          >
                            <TableCell>{doc.name}</TableCell>
                            <TableCell>{doc.type.toUpperCase()}</TableCell>
                            <TableCell>
                              <Chip
                                label={doc.status}
                                size="small"
                                color={
                                  doc.status === 'completed' ? 'success' :
                                  doc.status === 'processing' ? 'warning' :
                                  doc.status === 'failed' ? 'error' : 'default'
                                }
                              />
                            </TableCell>
                            <TableCell>
                              {doc.result ? `${Math.round(doc.result.confidence)}%` : '-'}
                            </TableCell>
                            <TableCell>
                              <IconButton size="small">
                                <Delete />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Box>
            )}

            {selectedTab === 1 && currentDocument && (
              /* Preview Tab */
              <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <IconButton onClick={() => setZoom(prev => Math.max(prev - 10, 50))}>
                    <ZoomOut />
                  </IconButton>
                  <Typography>{zoom}%</Typography>
                  <IconButton onClick={() => setZoom(prev => Math.min(prev + 10, 200))}>
                    <ZoomIn />
                  </IconButton>
                  <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
                  <IconButton>
                    <RotateLeft />
                  </IconButton>
                  <IconButton>
                    <RotateRight />
                  </IconButton>
                  <IconButton>
                    <Crop />
                  </IconButton>
                  <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
                  <IconButton>
                    <AutoFixHigh />
                  </IconButton>
                  <IconButton>
                    <Brightness6 />
                  </IconButton>
                  <IconButton>
                    <Contrast />
                  </IconButton>
                </Box>
                
                <Paper
                  sx={{
                    flexGrow: 1,
                    overflow: 'auto',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    backgroundColor: 'grey.100',
                  }}
                >
                  <canvas
                    ref={canvasRef}
                    style={{
                      maxWidth: '100%',
                      maxHeight: '100%',
                      transform: `scale(${zoom / 100})`,
                    }}
                  />
                </Paper>
              </Box>
            )}

            {selectedTab === 2 && currentDocument?.result && (
              /* Results Tab */
              <Box>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        Extracted Text
                      </Typography>
                      <TextField
                        multiline
                        fullWidth
                        value={currentDocument.result.text}
                        InputProps={{
                          readOnly: true,
                        }}
                        sx={{ mb: 2 }}
                        minRows={10}
                        maxRows={20}
                      />
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                          startIcon={<ContentCopy />}
                          onClick={() => {
                            navigator.clipboard.writeText(currentDocument.result!.text);
                            showSnackbar('Text copied to clipboard', 'success');
                          }}
                        >
                          Copy
                        </Button>
                        <Button startIcon={<Edit />}>
                          Edit
                        </Button>
                        <Button startIcon={<Translate />}>
                          Translate
                        </Button>
                      </Box>
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3, mb: 2 }}>
                      <Typography variant="h6" gutterBottom>
                        Analysis
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemText
                            primary="Confidence"
                            secondary={`${Math.round(currentDocument.result.confidence)}%`}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Language"
                            secondary={currentDocument.result.language}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Words"
                            secondary={currentDocument.result.metadata?.wordsCount}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Characters"
                            secondary={currentDocument.result.metadata?.charactersCount}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Processing Time"
                            secondary={`${(currentDocument.result.processingTime / 1000).toFixed(2)}s`}
                          />
                        </ListItem>
                      </List>
                    </Paper>
                    
                    {currentDocument.result.tables && currentDocument.result.tables.length > 0 && (
                      <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                          Detected Tables
                        </Typography>
                        <Typography variant="body2">
                          {currentDocument.result.tables.length} table(s) found
                        </Typography>
                      </Paper>
                    )}
                  </Grid>
                </Grid>
              </Box>
            )}

            {selectedTab === 3 && (
              /* Settings Tab */
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      OCR Settings
                    </Typography>
                    
                    <FormControl fullWidth sx={{ mb: 2 }}>
                      <InputLabel>Languages</InputLabel>
                      <Select
                        multiple
                        value={settings.language}
                        onChange={(e) => setSettings({ ...settings, language: e.target.value as string[] })}
                      >
                        <MenuItem value="eng">English</MenuItem>
                        <MenuItem value="fra">French</MenuItem>
                        <MenuItem value="deu">German</MenuItem>
                        <MenuItem value="spa">Spanish</MenuItem>
                        <MenuItem value="ita">Italian</MenuItem>
                        <MenuItem value="por">Portuguese</MenuItem>
                      </Select>
                    </FormControl>
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.preserveLayout}
                          onChange={(e) => setSettings({ ...settings, preserveLayout: e.target.checked })}
                        />
                      }
                      label="Preserve Layout"
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.detectTables}
                          onChange={(e) => setSettings({ ...settings, detectTables: e.target.checked })}
                        />
                      }
                      label="Detect Tables"
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.detectColumns}
                          onChange={(e) => setSettings({ ...settings, detectColumns: e.target.checked })}
                        />
                      }
                      label="Detect Columns"
                    />
                    
                    <Typography gutterBottom sx={{ mt: 2 }}>
                      Confidence Threshold: {settings.confidenceThreshold}%
                    </Typography>
                    <Slider
                      value={settings.confidenceThreshold}
                      onChange={(_, value) => setSettings({ ...settings, confidenceThreshold: value as number })}
                      min={0}
                      max={100}
                      marks
                      step={10}
                    />
                  </Paper>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Image Enhancement
                    </Typography>
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.enhanceImage}
                          onChange={(e) => setSettings({ ...settings, enhanceImage: e.target.checked })}
                        />
                      }
                      label="Auto Enhance"
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.deskew}
                          onChange={(e) => setSettings({ ...settings, deskew: e.target.checked })}
                        />
                      }
                      label="Auto Deskew"
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.removeNoise}
                          onChange={(e) => setSettings({ ...settings, removeNoise: e.target.checked })}
                        />
                      }
                      label="Remove Noise"
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.binarize}
                          onChange={(e) => setSettings({ ...settings, binarize: e.target.checked })}
                        />
                      }
                      label="Binarize"
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.autoRotate}
                          onChange={(e) => setSettings({ ...settings, autoRotate: e.target.checked })}
                        />
                      }
                      label="Auto Rotate"
                    />
                  </Paper>
                </Grid>
                
                <Grid item xs={12}>
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Output Settings
                    </Typography>
                    
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                          <InputLabel>Output Format</InputLabel>
                          <Select
                            value={settings.outputFormat}
                            onChange={(e) => setSettings({ ...settings, outputFormat: e.target.value as any })}
                          >
                            <MenuItem value="text">Plain Text</MenuItem>
                            <MenuItem value="json">JSON</MenuItem>
                            <MenuItem value="pdf">PDF</MenuItem>
                            <MenuItem value="docx">DOCX</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                      
                      <Grid item xs={12} sm={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={settings.batchMode}
                              onChange={(e) => setSettings({ ...settings, batchMode: e.target.checked })}
                            />
                          }
                          label="Batch Processing Mode"
                        />
                      </Grid>
                    </Grid>
                  </Paper>
                </Grid>
              </Grid>
            )}
          </Box>

          {/* Bottom Action Bar */}
          <Paper
            elevation={3}
            sx={{
              p: 2,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={processDocuments}
                disabled={processing || documents.length === 0}
              >
                Process{selectedDocuments.length > 0 && ` (${selectedDocuments.length})`}
              </Button>
              <Button
                variant="outlined"
                startIcon={<SelectAll />}
                onClick={() => setSelectedDocuments(documents.map(d => d.id))}
              >
                Select All
              </Button>
              <Button
                variant="outlined"
                startIcon={<Download />}
                onClick={exportResults}
                disabled={documents.filter(d => d.status === 'completed').length === 0}
              >
                Export
              </Button>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {processing && (
                <>
                  <CircularProgress size={20} />
                  <Typography variant="body2">
                    Processing {processingQueue.length} document(s)...
                  </Typography>
                </>
              )}
            </Box>
          </Paper>
        </Box>

        {/* Speed Dial */}
        <SpeedDial
          ariaLabel="OCR Actions"
          sx={{ position: 'fixed', bottom: 80, right: 16 }}
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

        {/* Statistics Dialog */}
        <Dialog
          open={statsDialogOpen}
          onClose={() => setStatsDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>Processing Statistics</DialogTitle>
          <DialogContent>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {calculateStats().totalDocuments}
                  </Typography>
                  <Typography variant="body2">Total Documents</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {calculateStats().processedDocuments}
                  </Typography>
                  <Typography variant="body2">Processed</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="error.main">
                    {calculateStats().failedDocuments}
                  </Typography>
                  <Typography variant="body2">Failed</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="info.main">
                    {Math.round(calculateStats().averageConfidence)}%
                  </Typography>
                  <Typography variant="body2">Avg Confidence</Typography>
                </Paper>
              </Grid>
            </Grid>
            
            {/* Charts */}
            <Grid container spacing={3} sx={{ mt: 2 }}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Processing Status
                  </Typography>
                  <Doughnut
                    data={{
                      labels: ['Completed', 'Failed', 'Pending', 'Processing'],
                      datasets: [{
                        data: [
                          documents.filter(d => d.status === 'completed').length,
                          documents.filter(d => d.status === 'failed').length,
                          documents.filter(d => d.status === 'pending').length,
                          documents.filter(d => d.status === 'processing').length,
                        ],
                        backgroundColor: ['#4caf50', '#f44336', '#ff9800', '#2196f3'],
                      }],
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                    }}
                    height={200}
                  />
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Confidence Distribution
                  </Typography>
                  <Bar
                    data={{
                      labels: ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'],
                      datasets: [{
                        label: 'Documents',
                        data: [
                          documents.filter(d => d.result && d.result.confidence < 20).length,
                          documents.filter(d => d.result && d.result.confidence >= 20 && d.result.confidence < 40).length,
                          documents.filter(d => d.result && d.result.confidence >= 40 && d.result.confidence < 60).length,
                          documents.filter(d => d.result && d.result.confidence >= 60 && d.result.confidence < 80).length,
                          documents.filter(d => d.result && d.result.confidence >= 80).length,
                        ],
                        backgroundColor: '#2196f3',
                      }],
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                    }}
                    height={200}
                  />
                </Paper>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setStatsDialogOpen(false)}>Close</Button>
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
    </HotKeys>
  );
};

export default OCRProcessorDesktop;