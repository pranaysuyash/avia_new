import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  IconButton,
  Badge,
  Popover,
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
  Settings,
  MarkEmailRead,
  Delete,
  Close,
  Refresh,
  DoneAll,
  NotificationImportant,
} from '@mui/icons-material';
import apiService from '../../services/api';
import { formatDistanceToNow } from 'date-fns';

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
}

interface NotificationStats {
  total: number;
  unread: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  last_7_days: Array<{ date: string; count: number }>;
}

const NotificationCenter: React.FC = () => {
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [tabValue, setTabValue] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
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
  });
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadNotifications();
    loadPreferences();
    connectWebSocket();

    // Poll for new notifications every 30 seconds
    const interval = setInterval(() => {
      loadUnreadCount();
    }, 30000);

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
    
    // Show browser notification if enabled
    if (preferences.push_enabled && 'Notification' in window && Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/icon.png',
      });
    }
  };

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await apiService.get('/api/v1/notifications/', {
        params: { limit: 50 },
      });
      setNotifications(response.data);
    } catch (err) {
      setError('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const response = await apiService.get('/api/v1/notifications/unread-count');
      setUnreadCount(response.data.unread_count);
    } catch (err) {
      console.error('Failed to load unread count:', err);
    }
  };

  const loadPreferences = async () => {
    try {
      const response = await apiService.get('/api/v1/notifications/preferences');
      setPreferences(response.data);
    } catch (err) {
      console.error('Failed to load preferences:', err);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiService.get('/api/v1/notifications/stats');
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await apiService.put(`/api/v1/notifications/${notificationId}/read`, {});
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
      await apiService.put('/api/v1/notifications/mark-all-read', {});
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
      setSnackbar({ open: true, message: 'All notifications marked as read', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to mark all as read', severity: 'error' });
    }
  };

  const deleteNotification = async (notificationId: string) => {
    try {
      await apiService.delete(`/api/v1/notifications/${notificationId}`);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      loadUnreadCount();
    } catch (err) {
      console.error('Failed to delete notification:', err);
    }
  };

  const clearAll = async () => {
    try {
      await apiService.delete('/api/v1/notifications/clear-all');
      setNotifications([]);
      setUnreadCount(0);
      setSnackbar({ open: true, message: 'All notifications cleared', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to clear notifications', severity: 'error' });
    }
  };

  const updatePreferences = async () => {
    try {
      await apiService.put('/api/v1/notifications/preferences', preferences);
      setSnackbar({ open: true, message: 'Preferences updated', severity: 'success' });
      setShowSettings(false);
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to update preferences', severity: 'error' });
    }
  };

  const sendTestNotification = async () => {
    try {
      await apiService.post('/api/v1/notifications/test', {});
      setSnackbar({ open: true, message: 'Test notification sent', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to send test notification', severity: 'error' });
    }
  };

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    if (tabValue === 1) {
      loadStats();
    }
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

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
        return <Settings color="action" />;
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

  const filteredNotifications = notifications.filter(n => {
    if (tabValue === 0) return true; // All
    if (tabValue === 1) return !n.read; // Unread
    return false;
  });

  return (
    <>
      <Tooltip title="Notifications">
        <IconButton onClick={handleClick} color="inherit">
          <Badge badgeContent={unreadCount} color="error">
            {unreadCount > 0 ? <NotificationsActive /> : <NotificationsIcon />}
          </Badge>
        </IconButton>
      </Tooltip>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: { width: 400, maxHeight: 600 },
        }}
      >
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Notifications</Typography>
            <Box>
              <IconButton size="small" onClick={loadNotifications}>
                <Refresh />
              </IconButton>
              <IconButton size="small" onClick={() => setShowSettings(true)}>
                <Settings />
              </IconButton>
              <IconButton size="small" onClick={handleClose}>
                <Close />
              </IconButton>
            </Box>
          </Box>

          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mt: 1 }}>
            <Tab label="All" />
            <Tab label={`Unread (${unreadCount})`} />
            <Tab label="Stats" />
          </Tabs>
        </Box>

        {tabValue < 2 && (
          <>
            {filteredNotifications.length > 0 && (
              <Box sx={{ px: 2, py: 1, borderBottom: 1, borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Button size="small" startIcon={<DoneAll />} onClick={markAllAsRead}>
                    Mark all as read
                  </Button>
                  <Button size="small" color="error" onClick={clearAll}>
                    Clear all
                  </Button>
                </Box>
              </Box>
            )}

            <List sx={{ maxHeight: 400, overflow: 'auto' }}>
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
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <NotificationsNone sx={{ fontSize: 48, color: 'text.secondary' }} />
                  <Typography color="textSecondary">
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
          </>
        )}

        {tabValue === 2 && stats && (
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Notification Statistics
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="textSecondary">
                Total: {stats.total} | Unread: {stats.unread}
              </Typography>
            </Box>

            <Typography variant="subtitle2" gutterBottom>
              By Type
            </Typography>
            <Box sx={{ mb: 2 }}>
              {Object.entries(stats.by_type).map(([type, count]) => (
                <Chip
                  key={type}
                  label={`${type}: ${count}`}
                  size="small"
                  sx={{ m: 0.5 }}
                />
              ))}
            </Box>

            <Typography variant="subtitle2" gutterBottom>
              By Priority
            </Typography>
            <Box sx={{ mb: 2 }}>
              {Object.entries(stats.by_priority).map(([priority, count]) => (
                <Chip
                  key={priority}
                  label={`${priority}: ${count}`}
                  size="small"
                  color={getPriorityColor(priority)}
                  sx={{ m: 0.5 }}
                />
              ))}
            </Box>

            <Button variant="outlined" fullWidth onClick={sendTestNotification}>
              Send Test Notification
            </Button>
          </Box>
        )}
      </Popover>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onClose={() => setShowSettings(false)} maxWidth="sm" fullWidth>
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
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Delivery Channels
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.email_enabled}
                  onChange={(e) => setPreferences({ ...preferences, email_enabled: e.target.checked })}
                />
              }
              label="Email Notifications"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.sms_enabled}
                  onChange={(e) => setPreferences({ ...preferences, sms_enabled: e.target.checked })}
                />
              }
              label="SMS Notifications"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.push_enabled}
                  onChange={(e) => setPreferences({ ...preferences, push_enabled: e.target.checked })}
                />
              }
              label="Push Notifications"
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
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Notification Types
            </Typography>
            {Object.entries(preferences.notification_types).map(([type, enabled]) => (
              <FormControlLabel
                key={type}
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
                label={type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
              />
            ))}
          </Box>

          <Box sx={{ mb: 3 }}>
            <FormControl fullWidth>
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
          </Box>

          <Box>
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
                />
                <TextField
                  label="End Time"
                  type="time"
                  value={preferences.quiet_hours_end || '08:00'}
                  onChange={(e) => setPreferences({ ...preferences, quiet_hours_end: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
              </Box>
            )}
          </Box>
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