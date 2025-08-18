/**
 * AI Assistant Component
 * Provides AI-powered writing assistance with auto-completion and suggestions
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
  ListItemButton,
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
  Spellcheck as GrammarIcon,
  Style as StyleIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  ContentCopy as ContentCopyIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  KeyboardArrowRight as KeyboardArrowRightIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import apiService from '../../services/api';

const aiSuggestionsAPI = {
  analyzeGrammar: (text: string) => apiService.post('/api/v1/ai/grammar', { text }),
  getSummary: (text: string) => apiService.post('/api/v1/ai/summary', { text }),
  extractKeyPoints: (text: string) => apiService.post('/api/v1/ai/keypoints', { text }),
  generateQuestions: (text: string) => apiService.post('/api/v1/ai/questions', { text }),
  suggestCorrections: (text: string) => apiService.post('/api/v1/ai/corrections', { text }),
  rewriteText: (text: string, style: string) => apiService.post('/api/v1/ai/rewrite', { text, style }),
  factCheck: (text: string) => apiService.post('/api/v1/ai/factcheck', { text }),
  getAutoCompletions: (params: any) => apiService.post('/api/v1/ai/autocomplete', params),
  getContentSuggestions: (params: any) => apiService.post('/api/v1/ai/suggestions', params),
  submitFeedback: (params: any) => apiService.post('/api/v1/ai/feedback', params),
  getSmartReplies: (params: any) => apiService.post('/api/v1/ai/smart-replies', params),
  checkGrammar: (text: string) => apiService.post('/api/v1/ai/check-grammar', { text }),
  summarize: (text: string, level: string) => apiService.post('/api/v1/ai/summarize', { text, level })
};
import { debounce } from 'lodash';

// Types
interface AutoCompletion {
  text: string;
  confidence: number;
}

interface Suggestion {
  id: string;
  type: string;
  text: string;
  confidence: number;
  metadata: any;
}

interface SmartReply {
  text: string;
  tone: string;
  context: string;
}

interface AIAssistantProps {
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

const AIAssistant: React.FC<AIAssistantProps> = ({
  value,
  onChange,
  context = 'document',
  placeholder = 'Start typing...',
  multiline = true,
  rows = 4,
  maxRows = 20,
  onFocus,
  onBlur,
  disabled = false,
  fullWidth = true,
  variant = 'outlined',
  label,
  helperText,
  error = false,
}) => {
  const { user, tokens } = useAuth();
  const [completions, setCompletions] = useState<AutoCompletion[]>([]);
  const [showCompletions, setShowCompletions] = useState(false);
  const [selectedCompletionIndex, setSelectedCompletionIndex] = useState(-1);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingCompletions, setLoadingCompletions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [smartReplies, setSmartReplies] = useState<SmartReply[]>([]);
  const [showSmartReplies, setShowSmartReplies] = useState(false);
  const [grammarErrors, setGrammarErrors] = useState<any[]>([]);
  const [showGrammarCheck, setShowGrammarCheck] = useState(false);
  const [autoCompleteEnabled, setAutoCompleteEnabled] = useState(true);
  const [suggestionsPanelOpen, setSuggestionsPanelOpen] = useState(false);
  const [selectedSuggestionType, setSelectedSuggestionType] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as any });
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [cursorPosition, setCursorPosition] = useState(0);
  const textFieldRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement>(null);
  const completionTimeoutRef = useRef<NodeJS.Timeout>();
  const suggestionTimeoutRef = useRef<NodeJS.Timeout>();

  // WebSocket for real-time completions
  const wsRef = useRef<WebSocket | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Initialize WebSocket connection
  useEffect(() => {
    if (autoCompleteEnabled && tokens?.accessToken) {
      const ws = new WebSocket(
        `${import.meta.env.VITE_WS_URL}/api/v1/ai-suggestions/ws/autocomplete?token=${tokens.accessToken}`
      );

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onclose = () => {
        setWsConnected(false);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.completions) {
          setCompletions(
            data.completions.map((text: string, index: number) => ({
              text,
              confidence: data.confidence_scores[index],
            }))
          );
          setShowCompletions(true);
          setLoadingCompletions(false);
        }
      };

      wsRef.current = ws;

      return () => {
        ws.close();
      };
    }
  }, [autoCompleteEnabled, tokens?.accessToken]);

  // Debounced auto-completion
  const getAutoCompletions = useMemo(
    () =>
      debounce(async (text: string, position: number) => {
        if (!text || text.length < 3 || !autoCompleteEnabled) {
          setCompletions([]);
          setShowCompletions(false);
          return;
        }

        // Get text up to cursor position
        const partialText = text.substring(0, position);
        const lastWord = partialText.split(/\s+/).pop() || '';

        if (lastWord.length < 2) {
          setCompletions([]);
          setShowCompletions(false);
          return;
        }

        setLoadingCompletions(true);

        try {
          if (wsConnected && wsRef.current) {
            // Use WebSocket for real-time completions
            wsRef.current.send(
              JSON.stringify({
                text: partialText,
                context,
                max_completions: 5,
              })
            );
          } else {
            // Fallback to REST API
            const response = await aiSuggestionsAPI.getAutoCompletions({
              text: partialText,
              context,
              max_completions: 5,
            });

            setCompletions(
              response.completions.map((text: string, index: number) => ({
                text,
                confidence: response.confidence_scores[index],
              }))
            );
            setShowCompletions(true);
            setLoadingCompletions(false);
          }
        } catch (error) {
          console.error('Failed to get completions:', error);
          setLoadingCompletions(false);
        }
      }, 300),
    [autoCompleteEnabled, context, wsConnected]
  );

  // Debounced content suggestions
  const getContentSuggestions = useMemo(
    () =>
      debounce(async (content: string) => {
        if (!content || content.length < 20) {
          setSuggestions([]);
          return;
        }

        setLoadingSuggestions(true);

        try {
          const response = await aiSuggestionsAPI.getContentSuggestions({
            content,
            context,
          });

          setSuggestions(response.suggestions);
          setLoadingSuggestions(false);
        } catch (error) {
          console.error('Failed to get suggestions:', error);
          setLoadingSuggestions(false);
        }
      }, 1000),
    [context]
  );

  // Handle text change
  const handleTextChange = (event: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    const newValue = event.target.value;
    const newPosition = event.target.selectionEnd || 0;
    
    onChange(newValue);
    setCursorPosition(newPosition);
    
    // Clear previous timeouts
    if (completionTimeoutRef.current) {
      clearTimeout(completionTimeoutRef.current);
    }
    if (suggestionTimeoutRef.current) {
      clearTimeout(suggestionTimeoutRef.current);
    }
    
    // Get auto-completions
    getAutoCompletions(newValue, newPosition);
    
    // Get content suggestions after longer delay
    suggestionTimeoutRef.current = setTimeout(() => {
      getContentSuggestions(newValue);
    }, 2000);
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (showCompletions && completions.length > 0) {
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setSelectedCompletionIndex((prev) =>
            prev < completions.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          event.preventDefault();
          setSelectedCompletionIndex((prev) =>
            prev > 0 ? prev - 1 : completions.length - 1
          );
          break;
        case 'Tab':
        case 'Enter':
          if (selectedCompletionIndex >= 0) {
            event.preventDefault();
            applyCompletion(completions[selectedCompletionIndex]);
          }
          break;
        case 'Escape':
          event.preventDefault();
          setShowCompletions(false);
          setSelectedCompletionIndex(-1);
          break;
      }
    }
  };

  // Apply completion
  const applyCompletion = (completion: AutoCompletion) => {
    const beforeCursor = value.substring(0, cursorPosition);
    const afterCursor = value.substring(cursorPosition);
    const newValue = beforeCursor + completion.text + afterCursor;
    
    onChange(newValue);
    setShowCompletions(false);
    setSelectedCompletionIndex(-1);
    
    // Move cursor to end of completion
    setTimeout(() => {
      if (inputRef.current) {
        const newPosition = cursorPosition + completion.text.length;
        inputRef.current.setSelectionRange(newPosition, newPosition);
        inputRef.current.focus();
      }
    }, 0);
    
    // Send feedback
    showSnackbar('Completion applied', 'success');
  };

  // Apply suggestion
  const applySuggestion = async (suggestion: Suggestion) => {
    onChange(suggestion.text);
    
    // Send feedback
    try {
      await aiSuggestionsAPI.submitFeedback({
        suggestion_id: suggestion.id,
        accepted: true,
        context,
      });
      showSnackbar('Suggestion applied', 'success');
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
    
    setShowSuggestions(false);
    setSuggestionsPanelOpen(false);
  };

  // Reject suggestion
  const rejectSuggestion = async (suggestion: Suggestion) => {
    try {
      await aiSuggestionsAPI.submitFeedback({
        suggestion_id: suggestion.id,
        accepted: false,
        context,
      });
      
      // Remove from current suggestions
      setSuggestions((prev) => prev.filter((s) => s.id !== suggestion.id));
      showSnackbar('Feedback recorded', 'info');
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  // Get smart replies
  const getSmartReplies = async () => {
    if (!value || value.length < 10) return;
    
    try {
      const response = await aiSuggestionsAPI.getSmartReplies({
        message: value,
        context,
        max_replies: 3,
      });
      
      setSmartReplies(
        response.replies.map((text: string, index: number) => ({
          text,
          tone: response.tones[index],
          context: response.contexts[index],
        }))
      );
      setShowSmartReplies(true);
    } catch (error) {
      console.error('Failed to get smart replies:', error);
    }
  };

  // Check grammar
  const checkGrammar = async () => {
    if (!value) return;
    
    try {
      const response = await aiSuggestionsAPI.checkGrammar(value);
      setGrammarErrors(response.corrections);
      setShowGrammarCheck(true);
      
      if (response.corrections.length === 0) {
        showSnackbar('No grammar errors found!', 'success');
      }
    } catch (error) {
      console.error('Failed to check grammar:', error);
      showSnackbar('Failed to check grammar', 'error');
    }
  };

  // Summarize content
  const summarizeContent = async () => {
    if (!value || value.length < 50) {
      showSnackbar('Content too short to summarize', 'warning');
      return;
    }
    
    try {
      const response = await aiSuggestionsAPI.summarize(value, 'medium');
      
      // Show summary in dialog
      setSuggestions([
        {
          id: 'summary',
          type: 'summarization',
          text: response.summary,
          confidence: 1.0,
          metadata: {
            keywords: response.keywords,
            word_count: response.word_count,
            summary_word_count: response.summary_word_count,
          },
        },
      ]);
      setSelectedSuggestionType('summarization');
      setSuggestionsPanelOpen(true);
    } catch (error) {
      console.error('Failed to summarize:', error);
      showSnackbar('Failed to generate summary', 'error');
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  // Render completions dropdown
  const renderCompletions = () => {
    if (!showCompletions || completions.length === 0) return null;
    
    const rect = textFieldRef.current?.getBoundingClientRect();
    if (!rect) return null;
    
    return (
      <Popper
        open={showCompletions}
        anchorEl={textFieldRef.current}
        placement="bottom-start"
        style={{ zIndex: 1300 }}
      >
        <ClickAwayListener onClickAway={() => setShowCompletions(false)}>
          <Paper elevation={3} sx={{ mt: 1, maxWidth: 400 }}>
            {loadingCompletions ? (
              <Box sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
                <CircularProgress size={16} sx={{ mr: 1 }} />
                <Typography variant="body2">Getting suggestions...</Typography>
              </Box>
            ) : (
              <List dense>
                {completions.map((completion, index) => (
                  <ListItem key={index} disablePadding>
                    <ListItemButton
                      selected={index === selectedCompletionIndex}
                      onClick={() => applyCompletion(completion)}
                      sx={{
                        '&:hover': { backgroundColor: 'action.hover' },
                        '&.Mui-selected': { backgroundColor: 'action.selected' },
                      }}
                    >
                      <ListItemIcon>
                        <AutoAwesomeIcon
                          fontSize="small"
                          sx={{
                            color: completion.confidence > 0.8 ? 'success.main' : 'text.secondary',
                          }}
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={completion.text}
                        secondary={`${Math.round(completion.confidence * 100)}% confidence`}
                      />
                    </ListItemButton>
                    <ListItemSecondaryAction>
                      <Typography variant="caption" color="text.secondary">
                        Tab
                      </Typography>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </ClickAwayListener>
      </Popper>
    );
  };

  // Render suggestions panel
  const renderSuggestionsPanel = () => {
    const suggestionTypes = [
      { type: 'grammar_correction', label: 'Grammar', icon: <GrammarIcon /> },
      { type: 'style_improvement', label: 'Style', icon: <StyleIcon /> },
      { type: 'summarization', label: 'Summary', icon: <SummarizeIcon /> },
      { type: 'smart_reply', label: 'Replies', icon: <FormatQuoteIcon /> },
    ];
    
    const filteredSuggestions = selectedSuggestionType
      ? suggestions.filter((s) => s.type === selectedSuggestionType)
      : suggestions;
    
    return (
      <Collapse in={suggestionsPanelOpen}>
        <Paper sx={{ mt: 2, p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              <TipsAndUpdatesIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              AI Suggestions
            </Typography>
            <IconButton onClick={() => setSuggestionsPanelOpen(false)} size="small">
              <CancelIcon />
            </IconButton>
          </Box>
          
          <Tabs
            value={selectedSuggestionType || false}
            onChange={(_, type) => setSelectedSuggestionType(type)}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ mb: 2 }}
          >
            <Tab label="All" value={false} />
            {suggestionTypes.map(({ type, label, icon }) => (
              <Tab
                key={type}
                label={label}
                value={type}
                icon={icon}
                iconPosition="start"
              />
            ))}
          </Tabs>
          
          {loadingSuggestions ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CircularProgress />
              <Typography variant="body2" sx={{ mt: 2 }}>
                Analyzing content...
              </Typography>
            </Box>
          ) : filteredSuggestions.length === 0 ? (
            <Alert severity="info">No suggestions available for this content.</Alert>
          ) : (
            <Stack spacing={2}>
              {filteredSuggestions.map((suggestion) => (
                <Card key={suggestion.id} variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Chip
                        label={suggestion.type.replace(/_/g, ' ')}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Typography variant="caption" color="text.secondary">
                        {Math.round(suggestion.confidence * 100)}% confidence
                      </Typography>
                    </Box>
                    
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {suggestion.text}
                    </Typography>
                    
                    {suggestion.metadata && (
                      <Box sx={{ mb: 2 }}>
                        {suggestion.metadata.reason && (
                          <Typography variant="caption" color="text.secondary">
                            Reason: {suggestion.metadata.reason}
                          </Typography>
                        )}
                        {suggestion.metadata.keywords && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                              Keywords:
                            </Typography>
                            <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                              {suggestion.metadata.keywords.map((keyword: string) => (
                                <Chip key={keyword} label={keyword} size="small" />
                              ))}
                            </Stack>
                          </Box>
                        )}
                      </Box>
                    )}
                    
                    <Stack direction="row" spacing={1}>
                      <Button
                        variant="contained"
                        size="small"
                        startIcon={<CheckCircleIcon />}
                        onClick={() => applySuggestion(suggestion)}
                      >
                        Apply
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<ContentCopyIcon />}
                        onClick={() => {
                          navigator.clipboard.writeText(suggestion.text);
                          showSnackbar('Copied to clipboard', 'success');
                        }}
                      >
                        Copy
                      </Button>
                      <IconButton
                        size="small"
                        onClick={() => rejectSuggestion(suggestion)}
                        color="error"
                      >
                        <ThumbDownIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </CardContent>
                </Card>
              ))}
            </Stack>
          )}
        </Paper>
      </Collapse>
    );
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <TextField
          ref={textFieldRef}
          inputRef={inputRef}
          value={value}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          onFocus={onFocus}
          onBlur={onBlur}
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
            endAdornment: (
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {wsConnected && (
                  <Tooltip title="AI Assistant Connected">
                    <Badge color="success" variant="dot">
                      <AutoAwesomeIcon fontSize="small" color="primary" />
                    </Badge>
                  </Tooltip>
                )}
              </Box>
            ),
          }}
        />
      </Box>
      
      {/* AI Assistant Toolbar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
        <Stack direction="row" spacing={1}>
          <Tooltip title="Get Suggestions">
            <IconButton
              size="small"
              onClick={() => {
                getContentSuggestions(value);
                setSuggestionsPanelOpen(true);
              }}
              disabled={!value || value.length < 20}
            >
              <LightbulbIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Check Grammar">
            <IconButton
              size="small"
              onClick={checkGrammar}
              disabled={!value}
            >
              <GrammarIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Summarize">
            <IconButton
              size="small"
              onClick={summarizeContent}
              disabled={!value || value.length < 50}
            >
              <SummarizeIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Smart Replies">
            <IconButton
              size="small"
              onClick={getSmartReplies}
              disabled={!value || context !== 'chat'}
            >
              <FormatQuoteIcon />
            </IconButton>
          </Tooltip>
        </Stack>
        
        <FormControlLabel
          control={
            <Switch
              checked={autoCompleteEnabled}
              onChange={(e) => setAutoCompleteEnabled(e.target.checked)}
              size="small"
            />
          }
          label="Auto-complete"
          labelPlacement="start"
          sx={{ ml: 'auto' }}
        />
      </Box>
      
      {/* Render dropdowns and panels */}
      {renderCompletions()}
      {renderSuggestionsPanel()}
      
      {/* Grammar check results */}
      <Dialog
        open={showGrammarCheck}
        onClose={() => setShowGrammarCheck(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Grammar Check Results</DialogTitle>
        <DialogContent>
          {grammarErrors.length === 0 ? (
            <Alert severity="success" sx={{ mt: 2 }}>
              No grammar errors found! Your writing looks great.
            </Alert>
          ) : (
            <Stack spacing={2} sx={{ mt: 2 }}>
              {grammarErrors.map((error, index) => (
                <Card key={index} variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2" color="error">
                        {error.error}
                      </Typography>
                      <KeyboardArrowRightIcon sx={{ mx: 1 }} />
                      <Typography variant="body2" color="success.main">
                        {error.correction}
                      </Typography>
                    </Box>
                    {error.reason && (
                      <Typography variant="caption" color="text.secondary">
                        {error.reason}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowGrammarCheck(false)}>Close</Button>
          {grammarErrors.length > 0 && (
            <Button
              variant="contained"
              onClick={() => {
                // Apply all corrections
                let correctedText = value;
                grammarErrors.forEach((error) => {
                  correctedText = correctedText.replace(error.error, error.correction);
                });
                onChange(correctedText);
                setShowGrammarCheck(false);
                showSnackbar('Grammar corrections applied', 'success');
              }}
            >
              Apply All Corrections
            </Button>
          )}
        </DialogActions>
      </Dialog>
      
      {/* Smart replies dialog */}
      <Dialog
        open={showSmartReplies}
        onClose={() => setShowSmartReplies(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Smart Reply Suggestions</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 2 }}>
            {smartReplies.map((reply, index) => (
              <Card
                key={index}
                variant="outlined"
                sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                onClick={() => {
                  onChange(reply.text);
                  setShowSmartReplies(false);
                  showSnackbar('Reply selected', 'success');
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Chip label={reply.tone} size="small" variant="outlined" />
                    <Chip label={reply.context} size="small" color="primary" variant="outlined" />
                  </Box>
                  <Typography variant="body2">{reply.text}</Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSmartReplies(false)}>Cancel</Button>
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

export default AIAssistant;