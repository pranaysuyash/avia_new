import React, { useState, useEffect } from 'react';
import {
  Grid,
  Box,
  Container,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Avatar,
  Badge,
  Tooltip,
  Fab,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon
} from '@mui/material';
import {
  Dashboard,
  Upload,
  Mic,
  VideoCall,
  Analytics,
  Search,
  Settings,
  History,
  Folder,
  People,
  Notifications,
  Help,
  Add,
  AudioFile,
  VideoFile,
  Description,
  TrendingUp,
  Psychology,
  Compare,
  Timeline,
  CloudUpload,
  RecordVoiceOver
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

interface DashboardStats {
  totalTranscripts: number;
  totalDuration: number;
  recentActivity: number;
  processingQueue: number;
  storageUsed: number;
  storageLimit: number;
}

interface RecentTranscript {
  id: string;
  title: string;
  duration: number;
  createdAt: string;
  status: 'completed' | 'processing' | 'failed';
  type: 'audio' | 'video';
  confidence?: number;
}

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  action: () => void;
}

export const MainDashboard: React.FC = () => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [stats, setStats] = useState<DashboardStats>({
    totalTranscripts: 0,
    totalDuration: 0,
    recentActivity: 0,
    processingQueue: 0,
    storageUsed: 0,
    storageLimit: 1000
  });
  const [recentTranscripts, setRecentTranscripts] = useState<RecentTranscript[]>([]);
  const [loading, setLoading] = useState(true);

  const quickActions: QuickAction[] = [
    {
      id: 'upload-audio',
      label: 'Upload Audio',
      icon: <AudioFile />,
      color: theme.palette.primary.main,
      action: () => console.log('Upload audio')
    },
    {
      id: 'upload-video',
      label: 'Upload Video',
      icon: <VideoFile />,
      color: theme.palette.secondary.main,
      action: () => console.log('Upload video')
    },
    {
      id: 'record-audio',
      label: 'Record Audio',
      icon: <Mic />,
      color: theme.palette.error.main,
      action: () => console.log('Record audio')
    },
    {
      id: 'live-transcription',
      label: 'Live Transcription',
      icon: <RecordVoiceOver />,
      color: theme.palette.warning.main,
      action: () => console.log('Live transcription')
    }
  ];

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Simulate API calls
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setStats({
        totalTranscripts: 156,
        totalDuration: 2847, // minutes
        recentActivity: 12,
        processingQueue: 3,
        storageUsed: 750,
        storageLimit: 1000
      });

      setRecentTranscripts([
        {
          id: '1',
          title: 'Team Meeting - Q4 Planning',
          duration: 45,
          createdAt: '2024-01-15T10:30:00Z',
          status: 'completed',
          type: 'video',
          confidence: 0.94
        },
        {
          id: '2',
          title: 'Client Interview - Product Feedback',
          duration: 32,
          createdAt: '2024-01-15T09:15:00Z',
          status: 'processing',
          type: 'audio'
        },
        {
          id: '3',
          title: 'Podcast Episode 15',
          duration: 67,
          createdAt: '2024-01-14T16:45:00Z',
          status: 'completed',
          type: 'audio',
          confidence: 0.91
        },
        {
          id: '4',
          title: 'Training Session - New Features',
          duration: 89,
          createdAt: '2024-01-14T14:20:00Z',
          status: 'failed',
          type: 'video'
        }
      ]);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatFileSize = (mb: number): string => {
    if (mb >= 1000) {
      return `${(mb / 1000).toFixed(1)} GB`;
    }
    return `${mb} MB`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const renderStatsCards = () => (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Description color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="div">
                Total Transcripts
              </Typography>
            </Box>
            <Typography variant="h4" color="primary">
              {stats.totalTranscripts}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              +{stats.recentActivity} this week
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Timeline color="secondary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="div">
                Total Duration
              </Typography>
            </Box>
            <Typography variant="h4" color="secondary">
              {formatDuration(stats.totalDuration)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Content processed
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <CloudUpload color="warning" sx={{ mr: 1 }} />
              <Typography variant="h6" component="div">
                Processing Queue
              </Typography>
            </Box>
            <Typography variant="h4" color="warning.main">
              {stats.processingQueue}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Files in queue
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Folder color="info" sx={{ mr: 1 }} />
              <Typography variant="h6" component="div">
                Storage Used
              </Typography>
            </Box>
            <Typography variant="h4" color="info.main">
              {formatFileSize(stats.storageUsed)}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={(stats.storageUsed / stats.storageLimit) * 100}
              sx={{ mt: 1 }}
            />
            <Typography variant="body2" color="text.secondary">
              {formatFileSize(stats.storageLimit - stats.storageUsed)} remaining
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderQuickActions = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Grid container spacing={2}>
          {quickActions.map((action) => (
            <Grid item xs={12} sm={6} md={3} key={action.id}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={action.icon}
                onClick={action.action}
                sx={{
                  height: 60,
                  borderColor: action.color,
                  color: action.color,
                  '&:hover': {
                    borderColor: action.color,
                    backgroundColor: `${action.color}10`
                  }
                }}
              >
                {action.label}
              </Button>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );

  const renderRecentActivity = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Recent Transcripts
        </Typography>
        <List>
          {recentTranscripts.map((transcript, index) => (
            <React.Fragment key={transcript.id}>
              <ListItem
                sx={{
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: theme.palette.action.hover
                  }
                }}
              >
                <ListItemIcon>
                  <Avatar sx={{ bgcolor: getStatusColor(transcript.status) + '.main' }}>
                    {transcript.type === 'video' ? <VideoFile /> : <AudioFile />}
                  </Avatar>
                </ListItemIcon>
                <ListItemText
                  primary={transcript.title}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {formatDuration(transcript.duration)} • {new Date(transcript.createdAt).toLocaleDateString()}
                      </Typography>
                      {transcript.confidence && (
                        <Typography variant="body2" color="text.secondary">
                          Confidence: {(transcript.confidence * 100).toFixed(0)}%
                        </Typography>
                      )}
                    </Box>
                  }
                />
                <Chip
                  label={transcript.status}
                  color={getStatusColor(transcript.status) as any}
                  size="small"
                />
              </ListItem>
              {index < recentTranscripts.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Button variant="text" color="primary">
            View All Transcripts
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

  const renderAnalyticsPreview = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Analytics Overview
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <TrendingUp color="primary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6">Trending Up</Typography>
              <Typography variant="body2" color="text.secondary">
                Processing volume increased 23% this month
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <Psychology color="secondary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6">AI Insights</Typography>
              <Typography variant="body2" color="text.secondary">
                15 new topics discovered in recent content
              </Typography>
            </Box>
          </Grid>
        </Grid>
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Button variant="outlined" startIcon={<Analytics />}>
            View Full Analytics
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ py: 3 }}>
          <LinearProgress />
          <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
            Loading dashboard...
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center' }}>
            <Dashboard sx={{ mr: 2 }} />
            Dashboard
          </Typography>
          <Box>
            <IconButton color="primary">
              <Badge badgeContent={3} color="error">
                <Notifications />
              </Badge>
            </IconButton>
            <IconButton color="primary">
              <Settings />
            </IconButton>
          </Box>
        </Box>

        {/* Stats Cards */}
        {renderStatsCards()}

        {/* Quick Actions */}
        {renderQuickActions()}

        {/* Main Content */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            {renderRecentActivity()}
          </Grid>
          <Grid item xs={12} md={4}>
            {renderAnalyticsPreview()}
          </Grid>
        </Grid>

        {/* Floating Action Button */}
        <SpeedDial
          ariaLabel="Quick Actions"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          icon={<SpeedDialIcon />}
        >
          <SpeedDialAction
            icon={<Upload />}
            tooltipTitle="Upload File"
            onClick={() => console.log('Upload')}
          />
          <SpeedDialAction
            icon={<Mic />}
            tooltipTitle="Record Audio"
            onClick={() => console.log('Record')}
          />
          <SpeedDialAction
            icon={<Search />}
            tooltipTitle="Search"
            onClick={() => console.log('Search')}
          />
        </SpeedDial>
      </Box>
    </Container>
  );
};

export default MainDashboard;