import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Chip,
  Badge,
  CircularProgress,
  LinearProgress,
  Tab,
  Tabs,
  Alert,
  Tooltip,
  useTheme
} from '@mui/material';
import {
  ConfirmationNumber as TicketIcon,
  Chat as ChatIcon,
  Help as HelpIcon,
  School as TutorialIcon,
  Forum as ForumIcon,
  Feedback as FeedbackIcon,
  Dashboard as DashboardIcon,
  TrendingUp as TrendingIcon,
  CheckCircle as ResolvedIcon,
  HourglassEmpty as PendingIcon,
  Star as StarIcon,
  AccessTime as TimeIcon,
  Person as PersonIcon,
  AttachMoney as BillingIcon,
  Code as APIIcon,
  BugReport as BugIcon,
  Lightbulb as FeatureIcon,
  NavigateNext as NavigateNextIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  BarElement
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  BarElement
);

interface DashboardMetrics {
  tickets: {
    total: number;
    open: number;
    resolved: number;
    avgResolutionTime: number;
    satisfactionScore: number;
  };
  chat: {
    totalSessions: number;
    activeNow: number;
    avgResponseTime: number;
  };
  articles: {
    total: number;
    views: number;
    helpfulPercentage: number;
  };
  forum: {
    posts: number;
    activeUsers: number;
    solvedPercentage: number;
  };
  feedback: {
    total: number;
    avgRating: number;
    featureRequests: number;
  };
}

interface QuickAction {
  title: string;
  icon: React.ReactNode;
  description: string;
  action: string;
  color: string;
}

const quickActions: QuickAction[] = [
  {
    title: 'Create Ticket',
    icon: <TicketIcon />,
    description: 'Get help from our support team',
    action: '/support/tickets/new',
    color: '#4CAF50'
  },
  {
    title: 'Live Chat',
    icon: <ChatIcon />,
    description: 'Chat with our AI assistant',
    action: '/support/chat',
    color: '#2196F3'
  },
  {
    title: 'Browse Help',
    icon: <HelpIcon />,
    description: 'Search our knowledge base',
    action: '/support/help',
    color: '#FF9800'
  },
  {
    title: 'Watch Tutorials',
    icon: <TutorialIcon />,
    description: 'Learn with video guides',
    action: '/support/tutorials',
    color: '#9C27B0'
  }
];

const SupportDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState(0);
  const [recentTickets, setRecentTickets] = useState<any[]>([]);
  const [trendingTopics, setTrendingTopics] = useState<any[]>([]);
  const navigate = useNavigate();
  const theme = useTheme();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Simulate API call with IPC
      const data = await window.electron.ipcRenderer.invoke('get-support-dashboard');
      setMetrics(data.metrics);
      setRecentTickets(data.recentTickets);
      setTrendingTopics(data.trendingTopics);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = (action: string) => {
    navigate(action);
  };

  const getTicketStatusColor = (status: string) => {
    switch (status) {
      case 'resolved':
        return 'success';
      case 'open':
        return 'error';
      case 'in_progress':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Chart data
  const ticketTrendData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'New Tickets',
        data: [12, 19, 15, 25, 22, 18, 20],
        borderColor: theme.palette.primary.main,
        backgroundColor: theme.palette.primary.light,
        tension: 0.4
      },
      {
        label: 'Resolved',
        data: [10, 15, 18, 20, 25, 15, 18],
        borderColor: theme.palette.success.main,
        backgroundColor: theme.palette.success.light,
        tension: 0.4
      }
    ]
  };

  const categoryDistributionData = {
    labels: ['Technical', 'Billing', 'Feature Request', 'Account', 'Other'],
    datasets: [
      {
        data: [35, 20, 25, 10, 10],
        backgroundColor: [
          '#FF6384',
          '#36A2EB',
          '#FFCE56',
          '#4BC0C0',
          '#9966FF'
        ]
      }
    ]
  };

  const satisfactionData = {
    labels: ['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied', 'Very Dissatisfied'],
    datasets: [
      {
        label: 'Customer Satisfaction',
        data: [45, 30, 15, 7, 3],
        backgroundColor: theme.palette.primary.main,
        borderColor: theme.palette.primary.dark,
        borderWidth: 1
      }
    ]
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Support Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Get help, track tickets, and explore our resources
        </Typography>
      </Box>

      {/* Quick Actions */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {quickActions.map((action, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card
              sx={{
                cursor: 'pointer',
                transition: 'all 0.3s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
              onClick={() => handleQuickAction(action.action)}
            >
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    mb: 2,
                    color: action.color
                  }}
                >
                  {action.icon}
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    {action.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {action.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Metrics Overview */}
      {metrics && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={2.4}>
            <Paper sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TicketIcon color="primary" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {metrics.tickets.open}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Open Tickets
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(metrics.tickets.resolved / metrics.tickets.total) * 100}
                sx={{ mt: 1 }}
              />
            </Paper>
          </Grid>

          <Grid item xs={12} md={2.4}>
            <Paper sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TimeIcon color="warning" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {metrics.tickets.avgResolutionTime}h
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Avg Resolution
              </Typography>
              <Chip
                label="Target: 24h"
                size="small"
                color={metrics.tickets.avgResolutionTime <= 24 ? 'success' : 'warning'}
                sx={{ mt: 1 }}
              />
            </Paper>
          </Grid>

          <Grid item xs={12} md={2.4}>
            <Paper sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <StarIcon color="warning" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {metrics.tickets.satisfactionScore}/5
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Satisfaction
              </Typography>
              <Box sx={{ display: 'flex', mt: 1 }}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <StarIcon
                    key={star}
                    fontSize="small"
                    color={star <= metrics.tickets.satisfactionScore ? 'warning' : 'disabled'}
                  />
                ))}
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} md={2.4}>
            <Paper sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ChatIcon color="info" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {metrics.chat.activeNow}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Active Chats
              </Typography>
              <Typography variant="caption" color="success.main" sx={{ mt: 1, display: 'block' }}>
                {metrics.chat.avgResponseTime}s avg response
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} md={2.4}>
            <Paper sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ForumIcon color="secondary" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {metrics.forum.posts}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Forum Posts
              </Typography>
              <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                {metrics.forum.solvedPercentage}% solved
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Main Content Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={selectedTab}
          onChange={(_, newValue) => setSelectedTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="Recent Activity" />
          <Tab label="Analytics" />
          <Tab label="Trending Topics" />
          <Tab label="Your History" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {selectedTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Recent Tickets
              </Typography>
              <List>
                {recentTickets.map((ticket) => (
                  <React.Fragment key={ticket.id}>
                    <ListItem>
                      <ListItemIcon>
                        <Badge
                          badgeContent={ticket.replies}
                          color="primary"
                          invisible={ticket.replies === 0}
                        >
                          <TicketIcon />
                        </Badge>
                      </ListItemIcon>
                      <ListItemText
                        primary={ticket.subject}
                        secondary={`${ticket.id} • ${ticket.category} • ${ticket.created}`}
                      />
                      <Chip
                        label={ticket.status}
                        size="small"
                        color={getTicketStatusColor(ticket.status) as any}
                      />
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
              <Button
                fullWidth
                variant="text"
                endIcon={<NavigateNextIcon />}
                onClick={() => navigate('/support/tickets')}
              >
                View All Tickets
              </Button>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Popular Help Articles
              </Typography>
              <List>
                {[
                  { title: 'Getting Started Guide', views: 1234, category: 'Basics' },
                  { title: 'Troubleshooting Audio Issues', views: 892, category: 'Technical' },
                  { title: 'Understanding Billing', views: 756, category: 'Billing' },
                  { title: 'API Integration Guide', views: 623, category: 'Developer' }
                ].map((article, index) => (
                  <ListItemButton key={index} onClick={() => navigate('/support/help')}>
                    <ListItemIcon>
                      <HelpIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={article.title}
                      secondary={`${article.views} views • ${article.category}`}
                    />
                  </ListItemButton>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )}

      {selectedTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Ticket Trends
              </Typography>
              <Line data={ticketTrendData} options={{ responsive: true }} />
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Category Distribution
              </Typography>
              <Doughnut data={categoryDistributionData} options={{ responsive: true }} />
            </Paper>
          </Grid>
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Customer Satisfaction
              </Typography>
              <Bar data={satisfactionData} options={{ responsive: true }} />
            </Paper>
          </Grid>
        </Grid>
      )}

      {selectedTab === 2 && (
        <Grid container spacing={3}>
          {trendingTopics.map((topic, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Chip
                      icon={<TrendingIcon />}
                      label={`#${index + 1}`}
                      color="primary"
                      size="small"
                    />
                    <Typography variant="caption" color="text.secondary">
                      {topic.mentions} mentions
                    </Typography>
                  </Box>
                  <Typography variant="h6" gutterBottom>
                    {topic.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {topic.description}
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Chip
                      label={topic.category}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    <Chip
                      label={`${topic.growth}% growth`}
                      size="small"
                      color={topic.growth > 0 ? 'success' : 'default'}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {selectedTab === 3 && (
        <Alert severity="info">
          Your support history will be displayed here. This feature is coming soon!
        </Alert>
      )}
    </Box>
  );
};

export default SupportDashboard;