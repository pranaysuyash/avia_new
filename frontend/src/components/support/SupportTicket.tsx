import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Avatar,
  Divider,
  Alert,
  CircularProgress,
  Tab,
  Tabs,
  Paper,
  Grid,
  Badge,
  Tooltip,
  Rating
} from '@mui/material';
import {
  Add as AddIcon,
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  CheckCircle as CheckCircleIcon,
  HourglassEmpty,
  Error as ErrorIcon,
  Info as InfoIcon,
  Person as PersonIcon,
  Support as SupportIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Upload as UploadIcon
} from '@mui/icons-material';
import { supportApi } from '../../services/supportApi';

interface Ticket {
  id: string;
  subject: string;
  description: string;
  status: 'open' | 'in_progress' | 'waiting_customer' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  assigned_to?: string;
  tags: string[];
  attachments: Array<{ name: string; url: string; size: number }>;
  conversation: Array<{
    type: 'customer' | 'agent' | 'system';
    message: string;
    timestamp: string;
    attachments?: Array<{ name: string; url: string }>;
  }>;
  satisfaction_rating?: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ticket-tabpanel-${index}`}
      aria-labelledby={`ticket-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const SupportTicket: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    subject: '',
    description: '',
    category: 'technical',
    priority: 'medium',
    attachments: [] as File[]
  });
  
  // Reply state
  const [replyText, setReplyText] = useState('');
  const [replying, setReplying] = useState(false);

  useEffect(() => {
    fetchTickets();
  }, []);

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const response = await supportApi.getMyTickets();
      setTickets(response.data);
    } catch (error) {
      console.error('Error fetching tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTicket = async () => {
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('subject', formData.subject);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('category', formData.category);
      formDataToSend.append('priority', formData.priority);
      
      formData.attachments.forEach(file => {
        formDataToSend.append('attachments', file);
      });

      await supportApi.createTicket(formDataToSend);
      setCreateDialogOpen(false);
      setFormData({
        subject: '',
        description: '',
        category: 'technical',
        priority: 'medium',
        attachments: []
      });
      fetchTickets();
    } catch (error) {
      console.error('Error creating ticket:', error);
    }
  };

  const handleReply = async () => {
    if (!selectedTicket || !replyText.trim()) return;
    
    setReplying(true);
    try {
      await supportApi.addTicketReply(selectedTicket.id, {
        message: replyText,
        is_agent: false
      });
      setReplyText('');
      fetchTickets();
    } catch (error) {
      console.error('Error sending reply:', error);
    } finally {
      setReplying(false);
    }
  };

  const handleRateTicket = async (rating: number) => {
    if (!selectedTicket) return;
    
    try {
      await supportApi.rateTicket(selectedTicket.id, rating);
      fetchTickets();
    } catch (error) {
      console.error('Error rating ticket:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open':
        return <ErrorIcon color="error" />;
      case 'in_progress':
        return <HourglassEmpty color="warning" />;
      case 'waiting_customer':
        return <InfoIcon color="info" />;
      case 'resolved':
      case 'closed':
        return <CheckCircleIcon color="success" />;
      default:
        return <InfoIcon />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  const filterTicketsByStatus = (status?: string) => {
    if (!status) return tickets;
    return tickets.filter(ticket => ticket.status === status);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Support Tickets</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Ticket
        </Button>
      </Box>

      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label={`All (${tickets.length})`} />
          <Tab label={`Open (${filterTicketsByStatus('open').length})`} />
          <Tab label={`In Progress (${filterTicketsByStatus('in_progress').length})`} />
          <Tab label={`Resolved (${filterTicketsByStatus('resolved').length})`} />
        </Tabs>
      </Paper>

      <TabPanel value={tabValue} index={0}>
        <TicketList 
          tickets={tickets}
          onSelectTicket={(ticket) => {
            setSelectedTicket(ticket);
            setDetailDialogOpen(true);
          }}
        />
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        <TicketList 
          tickets={filterTicketsByStatus('open')}
          onSelectTicket={(ticket) => {
            setSelectedTicket(ticket);
            setDetailDialogOpen(true);
          }}
        />
      </TabPanel>
      <TabPanel value={tabValue} index={2}>
        <TicketList 
          tickets={filterTicketsByStatus('in_progress')}
          onSelectTicket={(ticket) => {
            setSelectedTicket(ticket);
            setDetailDialogOpen(true);
          }}
        />
      </TabPanel>
      <TabPanel value={tabValue} index={3}>
        <TicketList 
          tickets={filterTicketsByStatus('resolved')}
          onSelectTicket={(ticket) => {
            setSelectedTicket(ticket);
            setDetailDialogOpen(true);
          }}
        />
      </TabPanel>

      {/* Create Ticket Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create Support Ticket</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Subject"
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  label="Category"
                >
                  <MenuItem value="technical">Technical Issue</MenuItem>
                  <MenuItem value="billing">Billing</MenuItem>
                  <MenuItem value="feature_request">Feature Request</MenuItem>
                  <MenuItem value="account">Account</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  label="Priority"
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="urgent">Urgent</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="outlined"
                component="label"
                startIcon={<UploadIcon />}
              >
                Attach Files
                <input
                  type="file"
                  hidden
                  multiple
                  onChange={(e) => {
                    const files = Array.from(e.target.files || []);
                    setFormData({ ...formData, attachments: files });
                  }}
                />
              </Button>
              {formData.attachments.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  {formData.attachments.map((file, index) => (
                    <Chip
                      key={index}
                      label={file.name}
                      onDelete={() => {
                        const newAttachments = [...formData.attachments];
                        newAttachments.splice(index, 1);
                        setFormData({ ...formData, attachments: newAttachments });
                      }}
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                </Box>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateTicket}
            variant="contained"
            disabled={!formData.subject || !formData.description}
          >
            Create Ticket
          </Button>
        </DialogActions>
      </Dialog>

      {/* Ticket Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">{selectedTicket?.id} - {selectedTicket?.subject}</Typography>
            <IconButton onClick={() => setDetailDialogOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedTicket && (
            <>
              <Box sx={{ mb: 2 }}>
                <Grid container spacing={2}>
                  <Grid item xs={4}>
                    <Typography variant="caption">Status</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getStatusIcon(selectedTicket.status)}
                      <Typography>{selectedTicket.status.replace('_', ' ')}</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="caption">Priority</Typography>
                    <Box>
                      <Chip
                        label={selectedTicket.priority}
                        color={getPriorityColor(selectedTicket.priority) as any}
                        size="small"
                      />
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="caption">Category</Typography>
                    <Typography>{selectedTicket.category}</Typography>
                  </Grid>
                </Grid>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Conversation */}
              <Box sx={{ maxHeight: 400, overflow: 'auto', mb: 2 }}>
                {selectedTicket.conversation.map((msg, index) => (
                  <Box
                    key={index}
                    sx={{
                      mb: 2,
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 1
                    }}
                  >
                    <Avatar sx={{ bgcolor: msg.type === 'customer' ? 'primary.main' : 'secondary.main' }}>
                      {msg.type === 'customer' ? <PersonIcon /> : <SupportIcon />}
                    </Avatar>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        {msg.type === 'customer' ? 'You' : msg.type === 'agent' ? 'Support' : 'System'} • 
                        {new Date(msg.timestamp).toLocaleString()}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 0.5 }}>
                        {msg.message}
                      </Typography>
                      {msg.attachments && msg.attachments.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          {msg.attachments.map((att, i) => (
                            <Chip
                              key={i}
                              icon={<AttachFileIcon />}
                              label={att.name}
                              size="small"
                              sx={{ mr: 1 }}
                            />
                          ))}
                        </Box>
                      )}
                    </Box>
                  </Box>
                ))}
              </Box>

              {/* Reply Box */}
              {selectedTicket.status !== 'resolved' && selectedTicket.status !== 'closed' && (
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <TextField
                    fullWidth
                    multiline
                    rows={2}
                    placeholder="Type your reply..."
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                  />
                  <Button
                    variant="contained"
                    endIcon={<SendIcon />}
                    onClick={handleReply}
                    disabled={!replyText.trim() || replying}
                  >
                    Send
                  </Button>
                </Box>
              )}

              {/* Rating */}
              {selectedTicket.status === 'resolved' && !selectedTicket.satisfaction_rating && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                  <Typography variant="body2" gutterBottom>
                    How satisfied are you with the resolution?
                  </Typography>
                  <Rating
                    value={0}
                    onChange={(_, value) => value && handleRateTicket(value)}
                  />
                </Box>
              )}

              {selectedTicket.satisfaction_rating && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    Your rating: <Rating value={selectedTicket.satisfaction_rating} readOnly size="small" />
                  </Typography>
                </Box>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

// Ticket List Component
const TicketList: React.FC<{
  tickets: Ticket[];
  onSelectTicket: (ticket: Ticket) => void;
}> = ({ tickets, onSelectTicket }) => {
  if (tickets.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body1" color="text.secondary">
          No tickets found
        </Typography>
      </Box>
    );
  }

  return (
    <List>
      {tickets.map((ticket) => (
        <React.Fragment key={ticket.id}>
          <ListItem
            button
            onClick={() => onSelectTicket(ticket)}
            sx={{
              '&:hover': {
                bgcolor: 'action.hover'
              }
            }}
          >
            <ListItemIcon>
              {getStatusIcon(ticket.status)}
            </ListItemIcon>
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body1">{ticket.subject}</Typography>
                  <Chip
                    label={ticket.priority}
                    color={getPriorityColor(ticket.priority) as any}
                    size="small"
                  />
                  {ticket.tags.map((tag, index) => (
                    <Chip key={index} label={tag} size="small" variant="outlined" />
                  ))}
                </Box>
              }
              secondary={
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    {ticket.id} • {ticket.category} • Created {new Date(ticket.created_at).toLocaleDateString()}
                  </Typography>
                </Box>
              }
            />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {ticket.conversation.length > 1 && (
                <Badge badgeContent={ticket.conversation.length - 1} color="primary">
                  <Typography variant="caption">replies</Typography>
                </Badge>
              )}
              {ticket.satisfaction_rating && (
                <Rating value={ticket.satisfaction_rating} readOnly size="small" />
              )}
            </Box>
          </ListItem>
          <Divider />
        </React.Fragment>
      ))}
    </List>
  );
};

function getStatusIcon(status: string) {
  switch (status) {
    case 'open':
      return <ErrorIcon color="error" />;
    case 'in_progress':
      return <HourglassEmpty color="warning" />;
    case 'waiting_customer':
      return <InfoIcon color="info" />;
    case 'resolved':
    case 'closed':
      return <CheckCircleIcon color="success" />;
    default:
      return <InfoIcon />;
  }
}

function getPriorityColor(priority: string) {
  switch (priority) {
    case 'urgent':
      return 'error';
    case 'high':
      return 'warning';
    case 'medium':
      return 'info';
    case 'low':
      return 'default';
    default:
      return 'default';
  }
}

export default SupportTicket;