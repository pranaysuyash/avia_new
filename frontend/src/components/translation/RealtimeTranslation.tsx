import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  IconButton,
  Chip,
  Alert,
  LinearProgress,
  Divider,
  Grid,
  Switch,
  FormControlLabel,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Tab,
  Tabs,
  Paper,
} from '@mui/material';
import {
  Translate,
  Language,
  SwapHoriz,
  ContentCopy,
  Download,
  PlayArrow,
  Pause,
  Settings,
  Cached,
  Speed,
  CompareArrows,
  Subtitles,
  CloudUpload,
} from '@mui/icons-material';
import apiService from '../../services/api';

interface TranslationSegment {
  text: string;
  start_time: number;
  end_time: number;
  speaker?: string;
  confidence: number;
}

interface TranslationResult {
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
  provider: string;
  confidence: number;
  processing_time: number;
  cached: boolean;
}

interface SupportedLanguage {
  code: string;
  name: string;
}

interface RealtimeTranslationProps {
  transcript?: TranslationSegment[];
  onTranslationComplete?: (translated: TranslationSegment[]) => void;
  enableStreaming?: boolean;
  defaultTargetLanguage?: string;
}

const RealtimeTranslation: React.FC<RealtimeTranslationProps> = ({
  transcript,
  onTranslationComplete,
  enableStreaming = false,
  defaultTargetLanguage = 'es',
}) => {
  const [sourceLanguage, setSourceLanguage] = useState<string>('auto');
  const [targetLanguage, setTargetLanguage] = useState<string>(defaultTargetLanguage);
  const [supportedLanguages, setSupportedLanguages] = useState<SupportedLanguage[]>([]);
  const [translationProvider, setTranslationProvider] = useState<string>('google');
  const [isTranslating, setIsTranslating] = useState(false);
  const [translatedSegments, setTranslatedSegments] = useState<TranslationSegment[]>([]);
  const [selectedSegment, setSelectedSegment] = useState<number>(-1);
  const [textToTranslate, setTextToTranslate] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [translationStats, setTranslationStats] = useState({
    totalSegments: 0,
    translatedSegments: 0,
    cacheHits: 0,
    averageTime: 0,
  });
  const [tabValue, setTabValue] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [autoTranslate, setAutoTranslate] = useState(false);
  const [preserveFormatting, setPreserveFormatting] = useState(true);
  const [batchSize, setBatchSize] = useState(10);
  const [streamingEnabled, setStreamingEnabled] = useState(enableStreaming);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    fetchSupportedLanguages();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (autoTranslate && transcript && transcript.length > 0) {
      handleTranslateTranscript();
    }
  }, [transcript, autoTranslate]);

  const fetchSupportedLanguages = async () => {
    try {
      const response = await apiService.get('/api/translation/supported-languages');
      setSupportedLanguages(response.data.languages);
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
  };

  const handleTranslateText = async () => {
    if (!textToTranslate) return;

    setIsTranslating(true);
    try {
      const response = await apiService.post('/api/translation/translate', {
        text: textToTranslate,
        target_language: targetLanguage,
        source_language: sourceLanguage,
        provider: translationProvider,
        preserve_formatting: preserveFormatting,
      });

      const result: TranslationResult = response.data;
      setTranslatedText(result.translated_text);

      // Update stats
      setTranslationStats(prev => ({
        ...prev,
        cacheHits: prev.cacheHits + (result.cached ? 1 : 0),
        averageTime: (prev.averageTime + result.processing_time) / 2,
      }));
    } catch (error) {
      console.error('Translation error:', error);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleTranslateTranscript = async () => {
    if (!transcript || transcript.length === 0) return;

    setIsTranslating(true);
    setTranslationStats(prev => ({ ...prev, totalSegments: transcript.length }));

    try {
      const response = await apiService.post('/api/translation/translate-transcript', {
        segments: transcript,
        target_language: targetLanguage,
        source_language: sourceLanguage,
        provider: translationProvider,
      });

      const translated = response.data.translated_segments;
      setTranslatedSegments(translated);
      setTranslationStats(prev => ({
        ...prev,
        translatedSegments: translated.length,
      }));

      if (onTranslationComplete) {
        onTranslationComplete(translated);
      }
    } catch (error) {
      console.error('Transcript translation error:', error);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleBatchTranslate = async () => {
    if (!transcript || transcript.length === 0) return;

    setIsTranslating(true);
    const texts = transcript.map(seg => seg.text);
    const targetLanguages = [targetLanguage]; // Can be extended to multiple languages

    try {
      const response = await apiService.post('/api/translation/batch-translate', {
        texts,
        target_languages: targetLanguages,
        source_language: sourceLanguage,
        provider: translationProvider,
      });

      const translations = response.data.translations[targetLanguage];
      const translated = transcript.map((seg, idx) => ({
        ...seg,
        text: translations[idx],
      }));

      setTranslatedSegments(translated);
      if (onTranslationComplete) {
        onTranslationComplete(translated);
      }
    } catch (error) {
      console.error('Batch translation error:', error);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleStreamTranslation = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(
      `ws://localhost:8000/api/translation/stream?target_language=${targetLanguage}&source_language=${sourceLanguage}`
    );

    ws.onopen = () => {
      console.log('Translation stream connected');
      setStreamingEnabled(true);
    };

    ws.onmessage = (event) => {
      if (event.data === 'TRANSLATION_COMPLETE') {
        setStreamingEnabled(false);
        ws.close();
      } else if (event.data.startsWith('ERROR:')) {
        console.error('Stream error:', event.data);
        setStreamingEnabled(false);
      } else {
        setTranslatedText(prev => prev + event.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStreamingEnabled(false);
    };

    ws.onclose = () => {
      setStreamingEnabled(false);
    };

    wsRef.current = ws;
  };

  const handleSendStreamText = (text: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(text);
    }
  };

  const handleExportTranslation = () => {
    if (!translatedSegments || translatedSegments.length === 0) return;

    const srtContent = translatedSegments
      .map((seg, idx) => {
        const startTime = formatTime(seg.start_time);
        const endTime = formatTime(seg.end_time);
        return `${idx + 1}\n${startTime} --> ${endTime}\n${seg.text}\n`;
      })
      .join('\n');

    const blob = new Blob([srtContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translation_${targetLanguage}.srt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const millis = Math.floor((seconds % 1) * 1000);
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')},${String(millis).padStart(3, '0')}`;
  };

  const handleCopyTranslation = () => {
    const text = translatedSegments.map(seg => seg.text).join('\n');
    navigator.clipboard.writeText(text);
  };

  const handleSwapLanguages = () => {
    if (sourceLanguage !== 'auto') {
      const temp = sourceLanguage;
      setSourceLanguage(targetLanguage);
      setTargetLanguage(temp);
    }
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <Translate sx={{ mr: 1 }} />
          <Typography variant="h5">Real-time Translation</Typography>
          <Box sx={{ flexGrow: 1 }} />
          <IconButton onClick={() => setShowSettings(true)}>
            <Settings />
          </IconButton>
        </Box>

        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
          <Tab label="Text Translation" />
          <Tab label="Transcript Translation" />
          <Tab label="Streaming Translation" />
        </Tabs>

        {tabValue === 0 && (
          <Box>
            <Grid container spacing={2} alignItems="center" mb={2}>
              <Grid item xs={5}>
                <FormControl fullWidth size="small">
                  <InputLabel>Source Language</InputLabel>
                  <Select
                    value={sourceLanguage}
                    onChange={(e) => setSourceLanguage(e.target.value)}
                    label="Source Language"
                  >
                    <MenuItem value="auto">Auto-detect</MenuItem>
                    {supportedLanguages.map((lang) => (
                      <MenuItem key={lang.code} value={lang.code}>
                        {lang.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={2} display="flex" justifyContent="center">
                <IconButton onClick={handleSwapLanguages} disabled={sourceLanguage === 'auto'}>
                  <SwapHoriz />
                </IconButton>
              </Grid>
              <Grid item xs={5}>
                <FormControl fullWidth size="small">
                  <InputLabel>Target Language</InputLabel>
                  <Select
                    value={targetLanguage}
                    onChange={(e) => setTargetLanguage(e.target.value)}
                    label="Target Language"
                  >
                    {supportedLanguages.map((lang) => (
                      <MenuItem key={lang.code} value={lang.code}>
                        {lang.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  variant="outlined"
                  placeholder="Enter text to translate..."
                  value={textToTranslate}
                  onChange={(e) => setTextToTranslate(e.target.value)}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  variant="outlined"
                  placeholder="Translation will appear here..."
                  value={translatedText}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
            </Grid>

            <Box display="flex" justifyContent="center" mt={2}>
              <Button
                variant="contained"
                startIcon={<Translate />}
                onClick={handleTranslateText}
                disabled={isTranslating || !textToTranslate}
              >
                Translate
              </Button>
              <IconButton onClick={() => navigator.clipboard.writeText(translatedText)} disabled={!translatedText}>
                <ContentCopy />
              </IconButton>
            </Box>
          </Box>
        )}

        {tabValue === 1 && (
          <Box>
            {transcript && transcript.length > 0 ? (
              <>
                <Box display="flex" alignItems="center" mb={2}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={autoTranslate}
                        onChange={(e) => setAutoTranslate(e.target.checked)}
                      />
                    }
                    label="Auto-translate new segments"
                  />
                  <Box sx={{ flexGrow: 1 }} />
                  <Chip
                    label={`${translationStats.translatedSegments}/${translationStats.totalSegments} segments`}
                    color="primary"
                    variant="outlined"
                  />
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Paper elevation={1} sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Original Transcript
                      </Typography>
                      <List dense>
                        {transcript.map((seg, idx) => (
                          <ListItem
                            key={idx}
                            button
                            selected={selectedSegment === idx}
                            onClick={() => setSelectedSegment(idx)}
                          >
                            <ListItemText
                              primary={seg.text}
                              secondary={`${seg.speaker || 'Unknown'} | ${seg.start_time.toFixed(1)}s - ${seg.end_time.toFixed(1)}s`}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Paper>
                  </Grid>
                  <Grid item xs={6}>
                    <Paper elevation={1} sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Translated Transcript
                      </Typography>
                      <List dense>
                        {translatedSegments.map((seg, idx) => (
                          <ListItem key={idx}>
                            <ListItemText
                              primary={seg.text}
                              secondary={`${seg.speaker || 'Unknown'} | ${seg.start_time.toFixed(1)}s - ${seg.end_time.toFixed(1)}s`}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Paper>
                  </Grid>
                </Grid>

                <Box display="flex" justifyContent="center" gap={2} mt={2}>
                  <Button
                    variant="contained"
                    startIcon={<Translate />}
                    onClick={handleTranslateTranscript}
                    disabled={isTranslating}
                  >
                    Translate Transcript
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Speed />}
                    onClick={handleBatchTranslate}
                    disabled={isTranslating}
                  >
                    Batch Translate
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Download />}
                    onClick={handleExportTranslation}
                    disabled={translatedSegments.length === 0}
                  >
                    Export SRT
                  </Button>
                  <IconButton onClick={handleCopyTranslation} disabled={translatedSegments.length === 0}>
                    <ContentCopy />
                  </IconButton>
                </Box>
              </>
            ) : (
              <Alert severity="info">
                No transcript available. Upload or transcribe content first.
              </Alert>
            )}
          </Box>
        )}

        {tabValue === 2 && (
          <Box>
            <Alert severity="info" sx={{ mb: 2 }}>
              Streaming translation provides real-time translation as you type or speak.
            </Alert>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  variant="outlined"
                  placeholder="Type or paste text for streaming translation..."
                  onChange={(e) => {
                    if (streamingEnabled) {
                      handleSendStreamText(e.target.value);
                    }
                  }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  variant="outlined"
                  placeholder="Streaming translation will appear here..."
                  value={translatedText}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
            </Grid>

            <Box display="flex" justifyContent="center" mt={2}>
              <Button
                variant="contained"
                startIcon={streamingEnabled ? <Pause /> : <PlayArrow />}
                onClick={streamingEnabled ? () => wsRef.current?.close() : handleStreamTranslation}
                color={streamingEnabled ? 'secondary' : 'primary'}
              >
                {streamingEnabled ? 'Stop Streaming' : 'Start Streaming'}
              </Button>
            </Box>
          </Box>
        )}

        {isTranslating && <LinearProgress sx={{ mt: 2 }} />}

        {translationStats.averageTime > 0 && (
          <Box display="flex" justifyContent="space-between" mt={2}>
            <Chip
              icon={<Cached />}
              label={`Cache hits: ${translationStats.cacheHits}`}
              size="small"
              variant="outlined"
            />
            <Chip
              icon={<Speed />}
              label={`Avg time: ${translationStats.averageTime.toFixed(2)}s`}
              size="small"
              variant="outlined"
            />
          </Box>
        )}

        {/* Settings Dialog */}
        <Dialog open={showSettings} onClose={() => setShowSettings(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Translation Settings</DialogTitle>
          <DialogContent>
            <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
              <InputLabel>Translation Provider</InputLabel>
              <Select
                value={translationProvider}
                onChange={(e) => setTranslationProvider(e.target.value)}
                label="Translation Provider"
              >
                <MenuItem value="google">Google Translate</MenuItem>
                <MenuItem value="microsoft">Microsoft Translator</MenuItem>
                <MenuItem value="openai">OpenAI GPT</MenuItem>
                <MenuItem value="deepl">DeepL</MenuItem>
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Switch
                  checked={preserveFormatting}
                  onChange={(e) => setPreserveFormatting(e.target.checked)}
                />
              }
              label="Preserve formatting"
            />

            <TextField
              fullWidth
              type="number"
              label="Batch Size"
              value={batchSize}
              onChange={(e) => setBatchSize(parseInt(e.target.value))}
              sx={{ mt: 2 }}
              InputProps={{ inputProps: { min: 1, max: 50 } }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowSettings(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default RealtimeTranslation;