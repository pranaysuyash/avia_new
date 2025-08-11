import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Collapse,
  Badge,
  Tooltip,
  Menu,
  MenuItem,
  InputAdornment
} from '@mui/material';
import {
  Send as SendIcon,
  Support as SupportIcon,
  Person as PersonIcon,
  AttachFile as AttachFileIcon,
  EmojiEmotions as EmojiIcon,
  MoreVert as MoreIcon,
  Article as ArticleIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Email as EmailIcon,
  CheckCircle as CheckCircleIcon,
  HourglassEmpty as WaitingIcon
} from '@mui/icons-material';
import { supportApi } from '../../services/supportApi';
import EmojiPicker from 'emoji-picker-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  message: string;
  timestamp: string;
  suggested_articles?: Array<{
    title: string;
    url: string;
  }>;
  attachments?: Array<{
    name: string;
    url: string;
  }>;
}

interface ChatSession {
  id: string;
  status: 'active' | 'waiting' | 'escalated' | 'closed';
  agent?: {
    name: string;
    avatar?: string;
    status: 'online' | 'away' | 'offline';
  };
  started_at: string;
  messages: ChatMessage[];
}

const LiveChat: React.FC = () => {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [suggestedArticlesOpen, setSuggestedArticlesOpen] = useState(true);
  const [attachments, setAttachments] = useState<File[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    startChatSession();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const startChatSession = async () => {
    setLoading(true);
    try {
      const response = await supportApi.startChatSession();
      setSession(response.data.session);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Error starting chat session:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() && attachments.length === 0) return;
    
    setSending(true);
    const messageToSend = inputMessage;
    setInputMessage('');
    
    // Add user message immediately for better UX
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      message: messageToSend,
      timestamp: new Date().toISOString(),
      attachments: attachments.map(f => ({ name: f.name, url: URL.createObjectURL(f) }))
    };
    
    setMessages(prev => [...prev, userMessage]);
    setAttachments([]);
    
    try {
      const formData = new FormData();
      formData.append('message', messageToSend);
      attachments.forEach(file => {
        formData.append('attachments', file);
      });
      
      const response = await supportApi.sendChatMessage(session!.id, formData);
      
      // Add AI response
      setMessages(prev => [...prev, response.data.message]);
      
      // Check if escalated
      if (response.data.escalated) {
        setSession(prev => prev ? { ...prev, status: 'escalated' } : null);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Remove the optimistic message on error
      setMessages(prev => prev.filter(m => m.id !== userMessage.id));
      setInputMessage(messageToSend);
    } finally {
      setSending(false);
    }
  };

  const handleEmojiClick = (emoji: any) => {
    setInputMessage(prev => prev + emoji.emoji);
    setShowEmojiPicker(false);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setAttachments(prev => [...prev, ...files]);
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const downloadTranscript = () => {
    const transcript = messages.map(m => 
      `[${new Date(m.timestamp).toLocaleString()}] ${m.role === 'user' ? 'You' : 'Support'}: ${m.message}`
    ).join('\n');
    
    const blob = new Blob([transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-transcript-${session?.id || 'unknown'}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const emailTranscript = async () => {
    try {
      await supportApi.emailChatTranscript(session!.id);
      // Show success message
    } catch (error) {
      console.error('Error emailing transcript:', error);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Badge
              overlap="circular"
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              variant="dot"
              color={session?.agent?.status === 'online' ? 'success' : 'default'}
            >
              <Avatar sx={{ bgcolor: 'primary.main' }}>
                <SupportIcon />
              </Avatar>
            </Badge>
            <Box>
              <Typography variant="h6">
                {session?.agent?.name || 'Support Assistant'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {session?.status === 'escalated' ? 'Connecting to agent...' : 
                 session?.agent ? `${session.agent.status}` : 'AI Assistant'}
              </Typography>
            </Box>
          </Box>
          
          <Box>
            <Tooltip title="New Chat">
              <IconButton onClick={startChatSession}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Email Transcript">
              <IconButton onClick={emailTranscript}>
                <EmailIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download Transcript">
              <IconButton onClick={downloadTranscript}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
              <MoreIcon />
            </IconButton>
          </Box>
        </Box>
      </Paper>

      {/* Status Alert */}
      {session?.status === 'escalated' && (
        <Alert severity="info" sx={{ borderRadius: 0 }}>
          Your chat has been escalated to a human agent. Please wait while we connect you...
        </Alert>
      )}

      {/* Messages Area */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2, bgcolor: 'background.default' }}>
        {messages.map((message, index) => (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
              mb: 2
            }}
          >
            <Box
              sx={{
                maxWidth: '70%',
                display: 'flex',
                flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                gap: 1
              }}
            >
              <Avatar sx={{ 
                bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                width: 32,
                height: 32
              }}>
                {message.role === 'user' ? <PersonIcon /> : <SupportIcon />}
              </Avatar>
              
              <Box>
                <Paper
                  sx={{
                    p: 2,
                    bgcolor: message.role === 'user' ? 'primary.main' : 'background.paper',
                    color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                    borderRadius: 2,
                    boxShadow: 1
                  }}
                >
                  <Typography variant="body2">{message.message}</Typography>
                  
                  {message.attachments && message.attachments.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      {message.attachments.map((att, i) => (
                        <Chip
                          key={i}
                          label={att.name}
                          size="small"
                          icon={<AttachFileIcon />}
                          sx={{ mr: 0.5, mb: 0.5 }}
                          onClick={() => window.open(att.url, '_blank')}
                        />
                      ))}
                    </Box>
                  )}
                </Paper>
                
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  {new Date(message.timestamp).toLocaleTimeString()}
                </Typography>
                
                {message.suggested_articles && message.suggested_articles.length > 0 && (
                  <Collapse in={suggestedArticlesOpen}>
                    <Card sx={{ mt: 1, bgcolor: 'background.default' }}>
                      <CardContent sx={{ p: 1.5 }}>
                        <Typography variant="caption" color="text.secondary" gutterBottom>
                          Related Articles:
                        </Typography>
                        <List dense sx={{ p: 0 }}>
                          {message.suggested_articles.map((article, i) => (
                            <ListItem
                              key={i}
                              button
                              sx={{ p: 0.5 }}
                              onClick={() => window.open(article.url, '_blank')}
                            >
                              <ListItemAvatar sx={{ minWidth: 32 }}>
                                <ArticleIcon fontSize="small" color="primary" />
                              </ListItemAvatar>
                              <ListItemText
                                primary={article.title}
                                primaryTypographyProps={{ variant: 'caption' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </CardContent>
                    </Card>
                  </Collapse>
                )}
              </Box>
            </Box>
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </Box>

      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <Box sx={{ p: 1, bgcolor: 'background.paper', borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {attachments.map((file, index) => (
              <Chip
                key={index}
                label={file.name}
                onDelete={() => removeAttachment(index)}
                icon={<AttachFileIcon />}
                size="small"
              />
            ))}
          </Box>
        </Box>
      )}

      {/* Input Area */}
      <Paper sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Type your message..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            disabled={sending || session?.status === 'closed'}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <IconButton
                    size="small"
                    onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                  >
                    <EmojiIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <AttachFileIcon />
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
          <IconButton
            color="primary"
            onClick={sendMessage}
            disabled={(!inputMessage.trim() && attachments.length === 0) || sending}
          >
            {sending ? <CircularProgress size={24} /> : <SendIcon />}
          </IconButton>
        </Box>
        
        <input
          ref={fileInputRef}
          type="file"
          hidden
          multiple
          onChange={handleFileSelect}
        />
        
        {showEmojiPicker && (
          <Box sx={{ position: 'absolute', bottom: 80, zIndex: 1000 }}>
            <EmojiPicker onEmojiClick={handleEmojiClick} />
          </Box>
        )}
      </Paper>

      {/* Options Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={() => {
          setSuggestedArticlesOpen(!suggestedArticlesOpen);
          setAnchorEl(null);
        }}>
          {suggestedArticlesOpen ? 'Hide' : 'Show'} Suggested Articles
        </MenuItem>
        <MenuItem onClick={() => {
          // End chat
          setAnchorEl(null);
        }}>
          End Chat
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default LiveChat;