/**
 * AI Assistant Desktop Component
 * Desktop-optimized AI writing assistant with native features
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  IconButton,
  Chip,
  Card,
  CardContent,
  Popper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  Switch,
  FormControlLabel,
  Stack,
  Badge,
  Fade,
  Grow,
  Collapse,
  Menu,
  MenuItem,
  Tab,
  Tabs,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  ClickAwayListener,
  Drawer,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Slider,
  Select,
  FormControl,
  InputLabel,
  Backdrop,
} from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  Lightbulb as LightbulbIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Psychology as PsychologyIcon,
  Translate as TranslateIcon,
  Summarize as SummarizeIcon,
  FormatQuote as FormatQuoteIcon,
  TipsAndUpdates as TipsAndUpdatesIcon,
  Speed as SpeedIcon,
  Grammar as GrammarIcon,
  Style as StyleIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  ContentCopy as ContentCopyIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  KeyboardArrowRight as KeyboardArrowRightIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Keyboard as KeyboardIcon,
  History as HistoryIcon,
  BookmarkIcon,
  FolderOpenIcon,
  SaveAsIcon,
  NotificationsIcon,
  ShortcutIcon,
  PaletteIcon,
  TextFieldsIcon,
  SpellcheckIcon,
  TranslateIcon as TranslationIcon,
  VolumeUpIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { aiSuggestionsAPI } from '../../services/api';
import { debounce } from 'lodash';

const { ipcRenderer } = window.require('electron');

// Types
interface AISettings {
  autoCompleteEnabled: boolean;
  grammarCheckEnabled: boolean;
  styleCheckEnabled: boolean;
  smartReplyEnabled: boolean;
  voiceTypingEnabled: boolean;
  suggestionDelay: number;
  suggestionConfidence: number;
  theme: 'light' | 'dark' | 'auto';
  fontSize: number;
  shortcuts: Record<string, string>;
  dictationLanguage: string;
  translationTargets: string[];
}

interface WritingTemplate {
  id: string;
  name: string;
  content: string;
  category: string;
  variables: string[];
}

interface AIAssistantDesktopProps {
  value: string;
  onChange: (value: string) => void;
  context?: 'transcript' | 'email' | 'document' | 'chat' | 'note';
  placeholder?: string;
  multiline?: boolean;
  rows?: number;
  maxRows?: number;
  onFocus?: () => void;
  onBlur?: () => void;
  disabled?: boolean;
  fullWidth?: boolean;
  variant?: 'standard' | 'outlined' | 'filled';
  label?: string;
  helperText?: string;
  error?: boolean;
}

const AIAssistantDesktop: React.FC<AIAssistantDesktopProps> = ({
  value,
  onChange,
  context = 'document',
  placeholder = 'Start typing or use voice dictation...',
  multiline = true,
  rows = 6,
  maxRows = 30,
  onFocus,
  onBlur,
  disabled = false,
  fullWidth = true,
  variant = 'outlined',
  label,
  helperText,
  error = false,
}) => {
  const { user } = useAuth();
  const [settings, setSettings] = useState<AISettings>({
    autoCompleteEnabled: true,
    grammarCheckEnabled: true,
    styleCheckEnabled: true,
    smartReplyEnabled: true,
    voiceTypingEnabled: false,
    suggestionDelay: 500,
    suggestionConfidence: 0.7,
    theme: 'auto',
    fontSize: 14,
    shortcuts: {
      'autocomplete': 'Tab',
      'grammar': 'Ctrl+G',
      'style': 'Ctrl+S',
      'voice': 'Ctrl+D',
    },
    dictationLanguage: 'en-US',
    translationTargets: ['es', 'fr', 'de'],
  });
  
  const [completions, setCompletions] = useState<any[]>([]);
  const [showCompletions, setShowCompletions] = useState(false);
  const [selectedCompletionIndex, setSelectedCompletionIndex] = useState(-1);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [templates, setTemplates] = useState<WritingTemplate[]>([]);
  const [writingHistory, setWritingHistory] = useState<string[]>([]);
  const [pinnedSuggestions, setPinnedSuggestions] = useState<any[]>([]);
  const [floatingToolbar, setFloatingToolbar] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as any });
  const textFieldRef = useRef<HTMLTextAreaElement | HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Load settings and templates from native storage
  useEffect(() => {
    loadDesktopSettings();
    loadTemplates();
    loadWritingHistory();
    setupKeyboardShortcuts();
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const loadDesktopSettings = async () => {
    try {
      const savedSettings = await ipcRenderer.invoke('get-ai-settings');
      if (savedSettings) {
        setSettings({ ...settings, ...savedSettings });
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const loadedTemplates = await ipcRenderer.invoke('get-writing-templates');
      setTemplates(loadedTemplates || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const loadWritingHistory = async () => {
    try {
      const history = await ipcRenderer.invoke('get-writing-history');
      setWritingHistory(history || []);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const setupKeyboardShortcuts = () => {
    const handleShortcut = (event: KeyboardEvent) => {
      // Grammar check shortcut
      if (event.ctrlKey && event.key === 'g') {
        event.preventDefault();
        checkGrammar();
      }
      // Style check shortcut
      else if (event.ctrlKey && event.key === 's' && !event.shiftKey) {
        event.preventDefault();
        checkStyle();
      }
      // Voice dictation shortcut
      else if (event.ctrlKey && event.key === 'd') {
        event.preventDefault();
        toggleVoiceDictation();
      }
      // Save to history shortcut
      else if (event.ctrlKey && event.shiftKey && event.key === 'h') {
        event.preventDefault();
        saveToHistory();
      }
    };

    document.addEventListener('keydown', handleShortcut);
    return () => document.removeEventListener('keydown', handleShortcut);
  };

  // Enhanced WebSocket with desktop features
  useEffect(() => {
    if (settings.autoCompleteEnabled && user?.token) {
      const ws = new WebSocket(
        `${process.env.REACT_APP_WS_URL}/api/v1/ai-suggestions/ws/autocomplete?token=${user.token}`
      );

      ws.onopen = () => {
        setWsConnected(true);
        // Notify user
        ipcRenderer.invoke('show-notification', {
          title: 'AI Assistant',
          body: 'Connected to AI suggestion service',
        });
      };

      ws.onclose = () => {
        setWsConnected(false);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.completions) {
          setCompletions(
            data.completions.map((text: string, index: number) => ({
              text,
              confidence: data.confidence_scores[index],
              source: 'ai',
            }))
          );
          
          // Add history-based completions
          const historyCompletions = getHistoryCompletions(value);
          if (historyCompletions.length > 0) {
            setCompletions(prev => [...historyCompletions, ...prev]);
          }
          
          setShowCompletions(true);
        }
      };

      wsRef.current = ws;

      return () => {
        ws.close();
      };
    }
  }, [settings.autoCompleteEnabled, user?.token]);

  // Voice dictation setup
  const setupVoiceDictation = () => {
    if ('webkitSpeechRecognition' in window) {
      const recognition = new (window as any).webkitSpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = settings.dictationLanguage;

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript) {
          const newValue = value + (value ? ' ' : '') + finalTranscript;
          onChange(newValue);
        }
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        showSnackbar('Voice dictation error', 'error');
      };

      recognitionRef.current = recognition;
    }
  };

  const toggleVoiceDictation = () => {
    if (!recognitionRef.current) {
      setupVoiceDictation();
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      recognitionRef.current?.start();
      setIsListening(true);
      showSnackbar('Voice dictation started', 'info');
    }
  };

  // Get completions from writing history
  const getHistoryCompletions = (text: string): any[] => {
    if (!text || text.length < 3) return [];
    
    const matches = writingHistory
      .filter(h => h.toLowerCase().startsWith(text.toLowerCase()))
      .slice(0, 3)
      .map(h => ({
        text: h.substring(text.length),
        confidence: 0.9,
        source: 'history',
      }));
    
    return matches;
  };

  // Enhanced grammar check with desktop notifications
  const checkGrammar = async () => {
    if (!value) return;
    
    try {
      const response = await aiSuggestionsAPI.checkGrammar(value);
      
      if (response.corrections.length === 0) {
        showSnackbar('No grammar errors found!', 'success');
        
        // Desktop notification
        ipcRenderer.invoke('show-notification', {
          title: 'Grammar Check',
          body: 'Your writing looks perfect!',
        });
      } else {
        setSuggestions(response.corrections.map((c: any, i: number) => ({
          id: `grammar_${i}`,
          type: 'grammar_correction',
          text: c.corrected_text,
          confidence: 1.0,
          metadata: c,
        })));
        setShowSuggestions(true);
        
        // Desktop notification
        ipcRenderer.invoke('show-notification', {
          title: 'Grammar Check',
          body: `Found ${response.corrections.length} suggestions`,
        });
      }
    } catch (error) {
      console.error('Failed to check grammar:', error);
      showSnackbar('Failed to check grammar', 'error');
    }
  };

  // Style check
  const checkStyle = async () => {
    if (!value) return;
    
    try {
      const response = await aiSuggestionsAPI.getContentSuggestions({
        content: value,
        context,
        suggestion_types: ['style_improvement'],
      });
      
      setSuggestions(response.suggestions);
      setShowSuggestions(true);
    } catch (error) {
      console.error('Failed to check style:', error);
    }
  };

  // Save to writing history
  const saveToHistory = async () => {
    if (!value) return;
    
    const newHistory = [value, ...writingHistory.slice(0, 99)];
    setWritingHistory(newHistory);
    
    // Save to native storage
    await ipcRenderer.invoke('save-writing-history', newHistory);
    showSnackbar('Saved to history', 'success');
  };

  // Apply template
  const applyTemplate = (template: WritingTemplate) => {
    let content = template.content;
    
    // Replace variables
    template.variables.forEach(variable => {
      const placeholder = `{{${variable}}}`;
      const value = prompt(`Enter value for ${variable}:`);
      if (value) {
        content = content.replace(new RegExp(placeholder, 'g'), value);
      }
    });
    
    onChange(content);
    setShowTemplates(false);
    showSnackbar('Template applied', 'success');
  };

  // Export content
  const exportContent = async (format: 'txt' | 'md' | 'docx' | 'pdf') => {
    try {
      const filePath = await ipcRenderer.invoke('show-save-dialog', {
        defaultPath: `document_${Date.now()}.${format}`,
        filters: [
          { name: format.toUpperCase(), extensions: [format] },
        ],
      });
      
      if (filePath) {
        await ipcRenderer.invoke('export-content', {
          content: value,
          format,
          path: filePath,
        });
        
        showSnackbar(`Exported as ${format.toUpperCase()}`, 'success');
      }
    } catch (error) {
      console.error('Failed to export:', error);
      showSnackbar('Export failed', 'error');
    }
  };

  // Text-to-speech
  const speakText = (text: string) => {
    ipcRenderer.invoke('text-to-speech', { text, language: settings.dictationLanguage });
  };

  // Translate text
  const translateText = async (targetLang: string) => {
    if (!selectedText && !value) return;
    
    const textToTranslate = selectedText || value;
    
    try {
      // In production, use translation API
      showSnackbar(`Translating to ${targetLang}...`, 'info');
      
      // Mock translation
      setTimeout(() => {
        showSnackbar('Translation complete', 'success');
      }, 1000);
    } catch (error) {
      console.error('Translation failed:', error);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  // Enhanced floating toolbar
  const renderFloatingToolbar = () => {
    if (!floatingToolbar || !selectedText) return null;
    
    return (
      <Paper
        elevation={8}
        sx={{
          position: 'fixed',
          top: '50%',
          right: 20,
          transform: 'translateY(-50%)',
          p: 1,
          zIndex: 1500,
          borderRadius: 2,
        }}
      >
        <Stack spacing={1}>
          <Tooltip title="Grammar Check">
            <IconButton size="small" onClick={checkGrammar}>
              <SpellcheckIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Style Check">
            <IconButton size="small" onClick={checkStyle}>
              <StyleIcon />
            </IconButton>
          </Tooltip>
          
          <Divider />
          
          <Tooltip title="Translate">
            <IconButton size="small" onClick={() => translateText('es')}>
              <TranslationIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Speak">
            <IconButton size="small" onClick={() => speakText(selectedText)}>
              <VolumeUpIcon />
            </IconButton>
          </Tooltip>
          
          <Divider />
          
          <Tooltip title="Copy">
            <IconButton
              size="small"
              onClick={() => {
                navigator.clipboard.writeText(selectedText);
                showSnackbar('Copied to clipboard', 'success');
              }}
            >
              <ContentCopyIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Paper>
    );
  };

  // Settings dialog
  const renderSettingsDialog = () => (
    <Dialog
      open={showSettings}
      onClose={() => setShowSettings(false)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>AI Assistant Settings</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 2 }}>
          <Box>
            <Typography variant="h6" gutterBottom>Features</Typography>
            <Stack spacing={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoCompleteEnabled}
                    onChange={(e) => setSettings({ ...settings, autoCompleteEnabled: e.target.checked })}
                  />
                }
                label="Auto-completion"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.grammarCheckEnabled}
                    onChange={(e) => setSettings({ ...settings, grammarCheckEnabled: e.target.checked })}
                  />
                }
                label="Grammar checking"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.styleCheckEnabled}
                    onChange={(e) => setSettings({ ...settings, styleCheckEnabled: e.target.checked })}
                  />
                }
                label="Style suggestions"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.voiceTypingEnabled}
                    onChange={(e) => setSettings({ ...settings, voiceTypingEnabled: e.target.checked })}
                  />
                }
                label="Voice typing"
              />
            </Stack>
          </Box>
          
          <Box>
            <Typography variant="h6" gutterBottom>Performance</Typography>
            <Box>
              <Typography gutterBottom>Suggestion Delay: {settings.suggestionDelay}ms</Typography>
              <Slider
                value={settings.suggestionDelay}
                onChange={(_, value) => setSettings({ ...settings, suggestionDelay: value as number })}
                min={100}
                max={2000}
                step={100}
                marks
              />
            </Box>
            <Box sx={{ mt: 2 }}>
              <Typography gutterBottom>
                Minimum Confidence: {Math.round(settings.suggestionConfidence * 100)}%
              </Typography>
              <Slider
                value={settings.suggestionConfidence}
                onChange={(_, value) => setSettings({ ...settings, suggestionConfidence: value as number })}
                min={0.5}
                max={1.0}
                step={0.1}
                marks
              />
            </Box>
          </Box>
          
          <Box>
            <Typography variant="h6" gutterBottom>Appearance</Typography>
            <Stack spacing={2}>
              <FormControl fullWidth>
                <InputLabel>Theme</InputLabel>
                <Select
                  value={settings.theme}
                  onChange={(e) => setSettings({ ...settings, theme: e.target.value as any })}
                  label="Theme"
                >
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="dark">Dark</MenuItem>
                  <MenuItem value="auto">Auto</MenuItem>
                </Select>
              </FormControl>
              
              <Box>
                <Typography gutterBottom>Font Size: {settings.fontSize}px</Typography>
                <Slider
                  value={settings.fontSize}
                  onChange={(_, value) => setSettings({ ...settings, fontSize: value as number })}
                  min={12}
                  max={24}
                  step={1}
                  marks
                />
              </Box>
            </Stack>
          </Box>
          
          <Box>
            <Typography variant="h6" gutterBottom>Voice & Language</Typography>
            <FormControl fullWidth>
              <InputLabel>Dictation Language</InputLabel>
              <Select
                value={settings.dictationLanguage}
                onChange={(e) => setSettings({ ...settings, dictationLanguage: e.target.value })}
                label="Dictation Language"
              >
                <MenuItem value="en-US">English (US)</MenuItem>
                <MenuItem value="en-GB">English (UK)</MenuItem>
                <MenuItem value="es-ES">Spanish</MenuItem>
                <MenuItem value="fr-FR">French</MenuItem>
                <MenuItem value="de-DE">German</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowSettings(false)}>Cancel</Button>
        <Button
          variant="contained"
          onClick={async () => {
            await ipcRenderer.invoke('save-ai-settings', settings);
            setShowSettings(false);
            showSnackbar('Settings saved', 'success');
          }}
        >
          Save Settings
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box sx={{ position: 'relative' }}>
      {/* Main text field with enhanced features */}
      <TextField
        ref={textFieldRef}
        value={value}
        onChange={(e) => {
          const newValue = e.target.value;
          onChange(newValue);
          
          // Check for selected text
          const start = e.target.selectionStart || 0;
          const end = e.target.selectionEnd || 0;
          if (start !== end) {
            setSelectedText(newValue.substring(start, end));
            setFloatingToolbar(true);
          } else {
            setSelectedText('');
            setFloatingToolbar(false);
          }
        }}
        placeholder={placeholder}
        multiline={multiline}
        rows={rows}
        maxRows={maxRows}
        disabled={disabled}
        fullWidth={fullWidth}
        variant={variant}
        label={label}
        helperText={helperText}
        error={error}
        InputProps={{
          style: { fontSize: settings.fontSize },
          endAdornment: (
            <Stack direction="row" spacing={1} alignItems="center">
              {isListening && (
                <CircularProgress size={20} />
              )}
              {wsConnected && (
                <Tooltip title="AI Connected">
                  <Badge color="success" variant="dot">
                    <AutoAwesomeIcon fontSize="small" color="primary" />
                  </Badge>
                </Tooltip>
              )}
            </Stack>
          ),
        }}
      />
      
      {/* Enhanced toolbar */}
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Stack direction="row" spacing={1}>
          <Tooltip title="Voice Dictation (Ctrl+D)">
            <IconButton
              onClick={toggleVoiceDictation}
              color={isListening ? 'error' : 'default'}
            >
              {isListening ? <MicOffIcon /> : <MicIcon />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Templates">
            <IconButton onClick={() => setShowTemplates(true)}>
              <TextFieldsIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Writing History">
            <IconButton onClick={() => {/* Show history dialog */}}>
              <HistoryIcon />
            </IconButton>
          </Tooltip>
          
          <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
          
          <Tooltip title="Check Grammar (Ctrl+G)">
            <IconButton onClick={checkGrammar} disabled={!value}>
              <SpellcheckIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Check Style (Ctrl+S)">
            <IconButton onClick={checkStyle} disabled={!value}>
              <StyleIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Summarize">
            <IconButton
              onClick={async () => {
                if (value.length < 50) {
                  showSnackbar('Content too short to summarize', 'warning');
                  return;
                }
                // Implement summarization
              }}
              disabled={!value || value.length < 50}
            >
              <SummarizeIcon />
            </IconButton>
          </Tooltip>
          
          <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
          
          <Tooltip title="Export">
            <IconButton
              onClick={(e) => {
                // Show export menu
              }}
              disabled={!value}
            >
              <SaveAsIcon />
            </IconButton>
          </Tooltip>
        </Stack>
        
        <IconButton onClick={() => setShowSettings(true)}>
          <SettingsIcon />
        </IconButton>
      </Box>
      
      {/* Speed Dial for quick actions */}
      <SpeedDial
        ariaLabel="AI Assistant Actions"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        icon={<SpeedDialIcon />}
      >
        <SpeedDialAction
          icon={<SaveAsIcon />}
          tooltipTitle="Export as PDF"
          onClick={() => exportContent('pdf')}
        />
        <SpeedDialAction
          icon={<TranslationIcon />}
          tooltipTitle="Translate"
          onClick={() => translateText('es')}
        />
        <SpeedDialAction
          icon={<VolumeUpIcon />}
          tooltipTitle="Read Aloud"
          onClick={() => speakText(value)}
        />
        <SpeedDialAction
          icon={<BookmarkIcon />}
          tooltipTitle="Save to History"
          onClick={saveToHistory}
        />
      </SpeedDial>
      
      {/* Render floating toolbar */}
      {renderFloatingToolbar()}
      
      {/* Settings dialog */}
      {renderSettingsDialog()}
      
      {/* Templates dialog */}
      <Dialog
        open={showTemplates}
        onClose={() => setShowTemplates(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Writing Templates</DialogTitle>
        <DialogContent>
          <List>
            {templates.map((template) => (
              <ListItem
                key={template.id}
                button
                onClick={() => applyTemplate(template)}
              >
                <ListItemText
                  primary={template.name}
                  secondary={template.category}
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTemplates(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
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

export default AIAssistantDesktop;