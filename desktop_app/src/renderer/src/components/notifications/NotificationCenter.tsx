import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  IconButton,
  Badge,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Typography,
  Button,
  Divider,
  Chip,
  Alert,
  CircularProgress,
  Tab,
  Tabs,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
  Snackbar,
  Paper,
  Menu,
  Checkbox,
  FormGroup,
  Grid,
  Avatar,
  ToggleButton,
  ToggleButtonGroup,
  Backdrop,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  NotificationsNone,
  NotificationsActive,
  Info,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Assignment,
  Security,
  Group,
  System,
  MarkEmailRead,
  Delete,
  Settings,
  Close,
  Refresh,
  DoneAll,
  NotificationImportant,
  FilterList,
  Sort,
  Archive,
  Unarchive,
  VolumeOff,
  VolumeUp,
  Palette,
  DarkMode,
  LightMode,
  MoreVert,
  Schedule,
  Email,
  Sms,
  PhoneAndroid,
  Computer,
} from '@mui/icons-material';
import { apiClient } from '../../services/api';
import { formatDistanceToNow, format } from 'date-fns';
import { Line } from 'react-chartjs-2';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'task_update' | 'system' | 'collaboration' | 'security';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  data?: Record<string, any>;
  action_url?: string;
  action_text?: string;
  read: boolean;
  read_at?: string;
  created_at: string;
  expires_at?: string;
  archived?: boolean;
}

interface NotificationPreferences {
  email_enabled: boolean;
  sms_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  notification_types: Record<string, boolean>;
  priority_threshold: string;
  desktop_notifications: boolean;
  sound_enabled: boolean;
  theme: 'light' | 'dark' | 'auto';
}

interface NotificationStats {
  total: number;
  unread: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  last_7_days: Array<{ date: string; count: number }>;
}

const NotificationCenter: React.FC = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [tabValue, setTabValue] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [selectedNotifications, setSelectedNotifications] = useState<string[]>([]);
  const [filterType, setFilterType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'priority'>('date');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    email_enabled: true,
    sms_enabled: false,
    push_enabled: true,
    in_app_enabled: true,
    quiet_hours_enabled: false,
    notification_types: {
      info: true,
      success: true,
      warning: true,
      error: true,
      task_update: true,
      system: true,
      collaboration: true,
      security: true,
    },
    priority_threshold: 'low',
    desktop_notifications: true,
    sound_enabled: true,
    theme: 'auto',
  });
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement>(new Audio('/notification.mp3'));

  useEffect(() => {
    loadNotifications();
    loadPreferences();
    connectWebSocket();
    requestNotificationPermission();

    // Poll for new notifications every 30 seconds
    const interval = setInterval(() => {
      loadUnreadCount();
    }, 30000);

    // Set up desktop notification handler
    if ('Notification' in window) {
      Notification.requestPermission();
    }

    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  };

  const connectWebSocket = () => {
    try {
      // Get auth token from localStorage or context
      const token = localStorage.getItem('auth_token') || 'dummy_token';
      const wsUrl = `ws://localhost:8000/api/v1/notifications/ws?token=${token}`;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Connected to notification service');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'notification') {
          handleNewNotification(data.data);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current.onclose = () => {
        console.log('Disconnected from notification service');
        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

  const handleNewNotification = (notification: any) => {
    // Add to notifications list
    setNotifications(prev => [notification, ...prev]);
    setUnreadCount(prev => prev + 1);
    
    // Play sound if enabled
    if (preferences.sound_enabled) {
      audioRef.current.play().catch(e => console.error('Failed to play sound:', e));
    }
    
    // Show desktop notification if enabled
    if (preferences.desktop_notifications && 'Notification' in window && Notification.permission === 'granted') {
      const notif = new Notification(notification.title, {
        body: notification.message,
        icon: '/icon.png',
        tag: notification.id,
        requireInteraction: notification.priority === 'urgent',
      });

      notif.onclick = () => {
        window.focus();
        if (notification.action_url) {
          window.location.href = notification.action_url;
        }
        setDrawerOpen(true);
      };
    }
  };

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/notifications/', {
        params: { limit: 100 },
      });
      setNotifications(response.data);
      loadUnreadCount();
    } catch (err) {
      setError('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const response = await apiClient.get('/api/v1/notifications/unread-count');
      setUnreadCount(response.data.unread_count);
    } catch (err) {
      console.error('Failed to load unread count:', err);
    }
  };

  const loadPreferences = async () => {
    try {
      const response = await apiClient.get('/api/v1/notifications/preferences');
      setPreferences({ ...preferences, ...response.data });
    } catch (err) {
      console.error('Failed to load preferences:', err);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiClient.get('/api/v1/notifications/stats');
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await apiClient.put(`/api/v1/notifications/${notificationId}/read`);
      setNotifications(prev =>
        prev.map(n => (n.id === notificationId ? { ...n, read: true } : n))
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await apiClient.put('/api/v1/notifications/mark-all-read');
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
      setSnackbar({ open: true, message: 'All notifications marked as read', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to mark all as read', severity: 'error' });
    }
  };

  const deleteNotification = async (notificationId: string) => {
    try {
      await apiClient.delete(`/api/v1/notifications/${notificationId}`);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      loadUnreadCount();
    } catch (err) {
      console.error('Failed to delete notification:', err);
    }
  };

  const deleteSelected = async () => {
    try {
      await Promise.all(selectedNotifications.map(id => apiClient.delete(`/api/v1/notifications/${id}`)));
      setNotifications(prev => prev.filter(n => !selectedNotifications.includes(n.id)));
      setSelectedNotifications([]);
      loadUnreadCount();
      setSnackbar({ open: true, message: `Deleted ${selectedNotifications.length} notifications`, severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to delete notifications', severity: 'error' });
    }
  };

  const archiveNotification = (notificationId: string) => {
    setNotifications(prev =>
      prev.map(n => (n.id === notificationId ? { ...n, archived: true } : n))
    );
  };

  const unarchiveNotification = (notificationId: string) => {
    setNotifications(prev =>
      prev.map(n => (n.id === notificationId ? { ...n, archived: false } : n))
    );
  };

  const clearAll = async () => {
    try {
      await apiClient.delete('/api/v1/notifications/clear-all');
      setNotifications([]);
      setUnreadCount(0);
      setSnackbar({ open: true, message: 'All notifications cleared', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to clear notifications', severity: 'error' });
    }
  };

  const updatePreferences = async () => {
    try {
      await apiClient.put('/api/v1/notifications/preferences', preferences);
      setSnackbar({ open: true, message: 'Preferences updated', severity: 'success' });
      setShowSettings(false);
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to update preferences', severity: 'error' });
    }
  };

  const sendTestNotification = async () => {
    try {
      await apiClient.post('/api/v1/notifications/test');
      setSnackbar({ open: true, message: 'Test notification sent', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to send test notification', severity: 'error' });
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'info':
        return <Info color="info" />;
      case 'success':
        return <CheckCircle color="success" />;
      case 'warning':
        return <Warning color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'task_update':
        return <Assignment color="primary" />;
      case 'system':
        return <System color="action" />;
      case 'collaboration':
        return <Group color="primary" />;
      case 'security':
        return <Security color="error" />;
      default:
        return <NotificationsNone />;
    }
  };

  const getPriorityColor = (priority: string): 'default' | 'primary' | 'secondary' | 'error' => {
    switch (priority) {
      case 'low':
        return 'default';
      case 'medium':
        return 'primary';
      case 'high':
        return 'secondary';
      case 'urgent':
        return 'error';
      default:
        return 'default';
    }
  };

  const filteredNotifications = notifications
    .filter(n => {
      if (showArchived) return n.archived;
      if (n.archived) return false;
      if (tabValue === 0) return true; // All
      if (tabValue === 1) return !n.read; // Unread
      if (tabValue === 2) return filterType === 'all' || n.type === filterType;
      return false;
    })
    .sort((a, b) => {
      if (sortBy === 'priority') {
        const priorityOrder = { urgent: 0, high: 1, medium: 2, low: 3 };
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      }
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

  const statsChartData = stats ? {
    labels: stats.last_7_days.map(d => format(new Date(d.date), 'MMM dd')),
    datasets: [{
      label: 'Notifications',
      data: stats.last_7_days.map(d => d.count),
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
      tension: 0.1,
    }],
  } : null;

  return (
    <>
      <Tooltip title="Notifications">
        <IconButton onClick={() => setDrawerOpen(true)} color="inherit">
          <Badge badgeContent={unreadCount} color="error">
            {unreadCount > 0 ? <NotificationsActive /> : <NotificationsIcon />}
          </Badge>
        </IconButton>
      </Tooltip>

      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{
          sx: { width: 450 },
        }}
      >
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          {/* Header */}
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <NotificationsIcon />
                Notifications
                {unreadCount > 0 && (
                  <Chip label={unreadCount} color="error" size="small" />
                )}
              </Typography>
              <Box>
                <IconButton size="small" onClick={loadNotifications}>
                  <Refresh />
                </IconButton>
                <IconButton size="small" onClick={() => setShowSettings(true)}>
                  <Settings />
                </IconButton>
                <IconButton size="small" onClick={() => setDrawerOpen(false)}>
                  <Close />
                </IconButton>
              </Box>
            </Box>

            <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} variant="fullWidth">
              <Tab label="All" />
              <Tab label={`Unread (${unreadCount})`} />
              <Tab label="Filtered" />
              <Tab label="Stats" />
            </Tabs>
          </Box>

          {/* Action Bar */}
          {tabValue < 3 && (
            <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center', gap: 1 }}>
              {selectedNotifications.length > 0 ? (
                <>
                  <Typography variant="body2" sx={{ flex: 1 }}>
                    {selectedNotifications.length} selected
                  </Typography>
                  <Button size="small" onClick={() => setSelectedNotifications([])}>
                    Clear
                  </Button>
                  <Button size="small" color="error" onClick={deleteSelected}>
                    Delete
                  </Button>
                </>
              ) : (
                <>
                  <ToggleButtonGroup
                    value={sortBy}
                    exclusive
                    onChange={(_, value) => value && setSortBy(value)}
                    size="small"
                  >
                    <ToggleButton value="date">
                      <Schedule fontSize="small" />
                    </ToggleButton>
                    <ToggleButton value="priority">
                      <NotificationImportant fontSize="small" />
                    </ToggleButton>
                  </ToggleButtonGroup>
                  <Box sx={{ flex: 1 }} />
                  <Button size="small" startIcon={<DoneAll />} onClick={markAllAsRead}>
                    Mark all read
                  </Button>
                  <IconButton size="small" onClick={(e) => setAnchorEl(e.currentTarget)}>
                    <MoreVert />
                  </IconButton>
                </>
              )}
            </Box>
          )}

          {/* Filter Bar (for Filtered tab) */}
          {tabValue === 2 && (
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <FormControl fullWidth size="small">
                <InputLabel>Filter by Type</InputLabel>
                <Select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  label="Filter by Type"
                  startAdornment={<FilterList sx={{ mr: 1, color: 'action.active' }} />}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="info">Info</MenuItem>
                  <MenuItem value="success">Success</MenuItem>
                  <MenuItem value="warning">Warning</MenuItem>
                  <MenuItem value="error">Error</MenuItem>
                  <MenuItem value="task_update">Task Update</MenuItem>
                  <MenuItem value="system">System</MenuItem>
                  <MenuItem value="collaboration">Collaboration</MenuItem>
                  <MenuItem value="security">Security</MenuItem>
                </Select>
              </FormControl>
            </Box>
          )}

          {/* Content */}
          {tabValue < 3 ? (
            <List sx={{ flex: 1, overflow: 'auto', p: 0 }}>
              {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              )}

              {error && (
                <Alert severity="error" sx={{ m: 2 }}>
                  {error}
                </Alert>
              )}

              {!loading && filteredNotifications.length === 0 && (
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <NotificationsNone sx={{ fontSize: 64, color: 'text.secondary' }} />
                  <Typography color="textSecondary" sx={{ mt: 2 }}>
                    {tabValue === 1 ? 'No unread notifications' : 'No notifications'}
                  </Typography>
                </Box>
              )}

              {filteredNotifications.map((notification) => (
                <React.Fragment key={notification.id}>
                  <ListItem
                    sx={{
                      opacity: notification.read ? 0.7 : 1,
                      backgroundColor: notification.read ? 'transparent' : 'action.hover',
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: 'action.hover',
                      },
                    }}
                    onClick={() => {
                      if (!notification.read) {
                        markAsRead(notification.id);
                      }
                      if (notification.action_url) {
                        window.location.href = notification.action_url;
                      }
                    }}
                  >
                    {selectedNotifications.length > 0 && (
                      <Checkbox
                        checked={selectedNotifications.includes(notification.id)}
                        onChange={(e) => {
                          e.stopPropagation();
                          if (e.target.checked) {
                            setSelectedNotifications([...selectedNotifications, notification.id]);
                          } else {
                            setSelectedNotifications(selectedNotifications.filter(id => id !== notification.id));
                          }
                        }}
                        onClick={(e) => e.stopPropagation()}
                      />
                    )}
                    <ListItemIcon>{getIcon(notification.type)}</ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle2">{notification.title}</Typography>
                          {notification.priority === 'urgent' && (
                            <NotificationImportant color="error" fontSize="small" />
                          )}
                          <Chip
                            label={notification.priority}
                            size="small"
                            color={getPriorityColor(notification.priority)}
                          />
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography variant="body2" color="textSecondary" sx={{ mb: 0.5 }}>
                            {notification.message}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                          </Typography>
                        </>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (notification.archived) {
                            unarchiveNotification(notification.id);
                          } else {
                            archiveNotification(notification.id);
                          }
                        }}
                      >
                        {notification.archived ? <Unarchive /> : <Archive />}
                      </IconButton>
                      <IconButton
                        edge="end"
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteNotification(notification.id);
                        }}
                      >
                        <Delete />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          ) : (
            // Stats Tab
            <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
              {!stats ? (
                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                  <CircularProgress />
                </Box>
              ) : (
                <>
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={6}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4">{stats.total}</Typography>
                        <Typography variant="body2" color="textSecondary">
                          Total Notifications
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={6}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="error">
                          {stats.unread}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Unread
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>

                  <Typography variant="subtitle2" gutterBottom>
                    Last 7 Days
                  </Typography>
                  <Paper sx={{ p: 2, mb: 3 }}>
                    {statsChartData && (
                      <Line data={statsChartData} options={{ maintainAspectRatio: false }} height={200} />
                    )}
                  </Paper>

                  <Typography variant="subtitle2" gutterBottom>
                    By Type
                  </Typography>
                  <Box sx={{ mb: 3 }}>
                    {Object.entries(stats.by_type).map(([type, count]) => (
                      <Chip
                        key={type}
                        icon={getIcon(type)}
                        label={`${type}: ${count}`}
                        sx={{ m: 0.5 }}
                      />
                    ))}
                  </Box>

                  <Typography variant="subtitle2" gutterBottom>
                    By Priority
                  </Typography>
                  <Box sx={{ mb: 3 }}>
                    {Object.entries(stats.by_priority).map(([priority, count]) => (
                      <Chip
                        key={priority}
                        label={`${priority}: ${count}`}
                        color={getPriorityColor(priority)}
                        sx={{ m: 0.5 }}
                      />
                    ))}
                  </Box>

                  <Button variant="outlined" fullWidth onClick={sendTestNotification}>
                    Send Test Notification
                  </Button>
                </>
              )}
            </Box>
          )}

          {/* Footer */}
          {showArchived && (
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              <Button
                fullWidth
                startIcon={<Unarchive />}
                onClick={() => setShowArchived(false)}
              >
                Back to Notifications
              </Button>
            </Box>
          )}
        </Box>

        {/* More Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
        >
          <MenuItem onClick={() => { setShowArchived(!showArchived); setAnchorEl(null); }}>
            {showArchived ? 'Show Active' : 'Show Archived'}
          </MenuItem>
          <MenuItem onClick={() => { clearAll(); setAnchorEl(null); }}>
            Clear All
          </MenuItem>
        </Menu>
      </Drawer>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onClose={() => setShowSettings(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Notification Settings
          <IconButton
            onClick={() => setShowSettings(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={3}>
            {/* Delivery Channels */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Email />
                Delivery Channels
              </Typography>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.email_enabled}
                      onChange={(e) => setPreferences({ ...preferences, email_enabled: e.target.checked })}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Email fontSize="small" />
                      Email Notifications
                    </Box>
                  }
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.sms_enabled}
                      onChange={(e) => setPreferences({ ...preferences, sms_enabled: e.target.checked })}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Sms fontSize="small" />
                      SMS Notifications
                    </Box>
                  }
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.push_enabled}
                      onChange={(e) => setPreferences({ ...preferences, push_enabled: e.target.checked })}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PhoneAndroid fontSize="small" />
                      Push Notifications
                    </Box>
                  }
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.desktop_notifications}
                      onChange={(e) => setPreferences({ ...preferences, desktop_notifications: e.target.checked })}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Computer fontSize="small" />
                      Desktop Notifications
                    </Box>
                  }
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.in_app_enabled}
                      onChange={(e) => setPreferences({ ...preferences, in_app_enabled: e.target.checked })}
                    />
                  }
                  label="In-App Notifications"
                />
              </FormGroup>
            </Grid>

            {/* Preferences */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Settings />
                Preferences
              </Typography>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.sound_enabled}
                      onChange={(e) => setPreferences({ ...preferences, sound_enabled: e.target.checked })}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {preferences.sound_enabled ? <VolumeUp fontSize="small" /> : <VolumeOff fontSize="small" />}
                      Sound Effects
                    </Box>
                  }
                />
                <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
                  <InputLabel>Minimum Priority</InputLabel>
                  <Select
                    value={preferences.priority_threshold}
                    onChange={(e) => setPreferences({ ...preferences, priority_threshold: e.target.value })}
                    label="Minimum Priority"
                  >
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="urgent">Urgent Only</MenuItem>
                  </Select>
                </FormControl>
                <FormControl fullWidth>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={preferences.theme}
                    onChange={(e) => setPreferences({ ...preferences, theme: e.target.value as any })}
                    label="Theme"
                  >
                    <MenuItem value="light">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LightMode fontSize="small" />
                        Light
                      </Box>
                    </MenuItem>
                    <MenuItem value="dark">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <DarkMode fontSize="small" />
                        Dark
                      </Box>
                    </MenuItem>
                    <MenuItem value="auto">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Palette fontSize="small" />
                        Auto
                      </Box>
                    </MenuItem>
                  </Select>
                </FormControl>
              </FormGroup>
            </Grid>

            {/* Notification Types */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Notification Types
              </Typography>
              <Paper sx={{ p: 2 }}>
                <Grid container spacing={2}>
                  {Object.entries(preferences.notification_types).map(([type, enabled]) => (
                    <Grid item xs={6} sm={4} md={3} key={type}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={enabled}
                            onChange={(e) =>
                              setPreferences({
                                ...preferences,
                                notification_types: {
                                  ...preferences.notification_types,
                                  [type]: e.target.checked,
                                },
                              })
                            }
                          />
                        }
                        label={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            {getIcon(type)}
                            <Typography variant="body2">
                              {type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
                            </Typography>
                          </Box>
                        }
                      />
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            </Grid>

            {/* Quiet Hours */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Schedule />
                Quiet Hours
              </Typography>
              <Paper sx={{ p: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.quiet_hours_enabled}
                      onChange={(e) => setPreferences({ ...preferences, quiet_hours_enabled: e.target.checked })}
                    />
                  }
                  label="Enable Quiet Hours"
                />
                {preferences.quiet_hours_enabled && (
                  <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                    <TextField
                      label="Start Time"
                      type="time"
                      value={preferences.quiet_hours_start || '22:00'}
                      onChange={(e) => setPreferences({ ...preferences, quiet_hours_start: e.target.value })}
                      InputLabelProps={{ shrink: true }}
                      fullWidth
                    />
                    <TextField
                      label="End Time"
                      type="time"
                      value={preferences.quiet_hours_end || '08:00'}
                      onChange={(e) => setPreferences({ ...preferences, quiet_hours_end: e.target.value })}
                      InputLabelProps={{ shrink: true }}
                      fullWidth
                    />
                  </Box>
                )}
              </Paper>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSettings(false)}>Cancel</Button>
          <Button onClick={updatePreferences} variant="contained">
            Save Settings
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        message={snackbar.message}
      />
    </>
  );
};

export default NotificationCenter;