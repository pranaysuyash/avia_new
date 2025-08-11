import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Divider,
  IconButton,
  Tooltip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Psychology,
  Assignment,
  TrendingUp,
  Topic,
  Schedule,
  Person,
  Priority,
  Sentiment,
  ExpandMore,
  Download,
  Share,
  Insights,
  Analytics,
  SmartToy,
} from '@mui/icons-material';
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

interface ActionItem {
  id: string;
  text: string;
  assignee?: string;
  due_date?: string;
  priority: 'high' | 'medium' | 'low';
  context: string;
  timestamp: number;
  confidence: number;
  status: string;
}

interface SentimentPoint {
  timestamp: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  score: number;
  confidence: number;
  text_segment: string;
  keywords: string[];
}

interface TopicCluster {
  id: string;
  name: string;
  keywords: string[];
  segments: string[];
  timestamps: number[];
  confidence: number;
  summary: string;
}

interface MeetingMinutes {
  title: string;
  date: string;
  duration: number;
  participants: string[];
  agenda_items: string[];
  key_decisions: string[];
  action_items: ActionItem[];
  next_steps: string[];
  summary: string;
  topics_discussed: string[];
}

interface ContentSummary {
  executive_summary: string;
  key_points: string[];
  main_topics: string[];
  sentiment_overview: string;
  duration: number;
  word_count: number;
  speaker_insights: Record<string, any>;
  confidence_score: number;
}

interface AnalysisResults {
  content_type: string;
  analysis_timestamp: string;
  transcript_stats: {
    total_segments: number;
    total_duration: number;
    word_count: number;
    speaking_rate: number;
  };
  summary: ContentSummary;
  action_items: ActionItem[];
  sentiment_analysis: SentimentPoint[];
  topic_clusters: TopicCluster[];
  meeting_minutes?: MeetingMinutes;
  content_categories: {
    content_themes: string[];
    discussion_type: string;
    formality_level: string;
    technical_level: string;
    emotional_tone: string;
  };
  key_insights: {
    summary_insights: string[];
    action_insights: string[];
    sentiment_insights: string[];
    topic_insights: string[];
    overall_assessment: Record<string, string>;
  };
}

interface AIContentInsightsProps {
  transcriptData?: any;
  onAnalysisComplete?: (results: AnalysisResults) => void;
}

const AIContentInsights: React.FC<AIContentInsightsProps> = ({
  transcriptData,
  onAnalysisComplete,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeContent = useCallback(async () => {
    if (!transcriptData) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await fetch('/api/ai-insights/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript_data: transcriptData,
          content_type: 'meeting',
          enable_openai: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze content');
      }

      const results = await response.json();
      setAnalysisResults(results);
      onAnalysisComplete?.(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  }, [transcriptData, onAnalysisComplete]);

  useEffect(() => {
    if (transcriptData && !analysisResults && !isAnalyzing) {
      analyzeContent();
    }
  }, [transcriptData, analysisResults, isAnalyzing, analyzeContent]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#f44336';
      case 'medium': return '#ff9800';
      case 'low': return '#4caf50';
      default: return '#757575';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '#4caf50';
      case 'negative': return '#f44336';
      case 'neutral': return '#ff9800';
      default: return '#757575';
    }
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const exportResults = (format: 'json' | 'csv') => {
    if (!analysisResults) return;

    let content: string;
    let filename: string;
    let mimeType: string;

    if (format === 'json') {
      content = JSON.stringify(analysisResults, null, 2);
      filename = `ai-insights-${Date.now()}.json`;
      mimeType = 'application/json';
    } else {
      // Convert to CSV format
      const csvData = analysisResults.action_items.map(item => ({
        text: item.text,
        assignee: item.assignee || '',
        priority: item.priority,
        due_date: item.due_date || '',
        confidence: item.confidence.toFixed(2),
      }));
      
      const headers = Object.keys(csvData[0] || {}).join(',');
      const rows = csvData.map(row => Object.values(row).join(','));
      content = [headers, ...rows].join('\n');
      filename = `action-items-${Date.now()}.csv`;
      mimeType = 'text/csv';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isAnalyzing) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" p={4}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Analyzing content with AI...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          This may take a few moments
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Analysis Failed</Typography>
        <Typography>{error}</Typography>
        <Button onClick={analyzeContent} sx={{ mt: 1 }}>
          Retry Analysis
        </Button>
      </Alert>
    );
  }

  if (!analysisResults) {
    return (
      <Box p={4} textAlign="center">
        <SmartToy sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          Upload a transcript to begin AI analysis
        </Typography>
      </Box>
    );
  }

  const renderOverviewTab = () => (
    <Box>
      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Duration
              </Typography>
              <Typography variant="h4">
                {formatTime(analysisResults.transcript_stats.total_duration)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Word Count
              </Typography>
              <Typography variant="h4">
                {analysisResults.transcript_stats.word_count.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Action Items
              </Typography>
              <Typography variant="h4">
                {analysisResults.action_items.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Topics
              </Typography>
              <Typography variant="h4">
                {analysisResults.topic_clusters.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Executive Summary */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <Insights sx={{ mr: 1, verticalAlign: 'middle' }} />
            Executive Summary
          </Typography>
          <Typography variant="body1" paragraph>
            {analysisResults.summary.executive_summary}
          </Typography>
          
          {analysisResults.summary.key_points.length > 0 && (
            <>
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                Key Points:
              </Typography>
              <List dense>
                {analysisResults.summary.key_points.map((point, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={`${index + 1}. ${point}`} />
                  </ListItem>
                ))}
              </List>
            </>
          )}
        </CardContent>
      </Card>

      {/* Content Classification */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Content Classification
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2">Discussion Type:</Typography>
              <Chip 
                label={analysisResults.content_categories.discussion_type} 
                color="primary" 
                sx={{ mb: 1 }}
              />
              <Typography variant="subtitle2">Formality Level:</Typography>
              <Chip 
                label={analysisResults.content_categories.formality_level} 
                color="secondary"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2">Technical Level:</Typography>
              <Chip 
                label={analysisResults.content_categories.technical_level} 
                color="info" 
                sx={{ mb: 1 }}
              />
              <Typography variant="subtitle2">Emotional Tone:</Typography>
              <Chip 
                label={analysisResults.content_categories.emotional_tone} 
                color="success"
              />
            </Grid>
          </Grid>
          
          {analysisResults.content_categories.content_themes.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2">Main Themes:</Typography>
              <Box sx={{ mt: 1 }}>
                {analysisResults.content_categories.content_themes.map((theme, index) => (
                  <Chip key={index} label={theme} sx={{ mr: 1, mb: 1 }} />
                ))}
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Key Insights */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Key Insights
          </Typography>
          {Object.entries(analysisResults.key_insights).map(([category, insights]) => {
            if (category === 'overall_assessment' || !Array.isArray(insights) || insights.length === 0) {
              return null;
            }
            
            return (
              <Accordion key={category}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="subtitle1">
                    {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {insights.map((insight, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={insight} />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </CardContent>
      </Card>
    </Box>
  );

  const renderActionItemsTab = () => {
    const priorityCounts = analysisResults.action_items.reduce(
      (acc, item) => {
        acc[item.priority] = (acc[item.priority] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );

    const priorityData = Object.entries(priorityCounts).map(([priority, count]) => ({
      name: priority.charAt(0).toUpperCase() + priority.slice(1),
      value: count,
      color: getPriorityColor(priority),
    }));

    return (
      <Box>
        {/* Priority Distribution */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Action Items by Priority
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={priorityData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                    >
                      {priorityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Grid>
              <Grid item xs={12} md={6}>
                <Grid container spacing={2}>
                  {priorityData.map((item) => (
                    <Grid item xs={4} key={item.name}>
                      <Card variant="outlined">
                        <CardContent sx={{ textAlign: 'center', py: 2 }}>
                          <Typography variant="h4" sx={{ color: item.color }}>
                            {item.value}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {item.name}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Action Items List */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Action Items ({analysisResults.action_items.length})
              </Typography>
              <Button
                startIcon={<Download />}
                onClick={() => exportResults('csv')}
                size="small"
              >
                Export CSV
              </Button>
            </Box>
            
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Action Item</TableCell>
                    <TableCell>Assignee</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Due Date</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Time</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {analysisResults.action_items.map((item, index) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <Typography variant="body2">{item.text}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {item.context.substring(0, 100)}...
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {item.assignee ? (
                          <Chip
                            icon={<Person />}
                            label={item.assignee}
                            size="small"
                            variant="outlined"
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Unassigned
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={item.priority}
                          size="small"
                          sx={{
                            backgroundColor: getPriorityColor(item.priority),
                            color: 'white',
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        {item.due_date || (
                          <Typography variant="body2" color="text.secondary">
                            Not specified
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <LinearProgress
                          variant="determinate"
                          value={item.confidence * 100}
                          sx={{ width: 60 }}
                        />
                        <Typography variant="caption">
                          {(item.confidence * 100).toFixed(0)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatTime(item.timestamp)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Box>
    );
  };

  const renderSentimentTab = () => {
    const sentimentCounts = analysisResults.sentiment_analysis.reduce(
      (acc, point) => {
        acc[point.sentiment] = (acc[point.sentiment] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );

    const sentimentData = Object.entries(sentimentCounts).map(([sentiment, count]) => ({
      name: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
      value: count,
      color: getSentimentColor(sentiment),
    }));

    const timelineData = analysisResults.sentiment_analysis.map((point, index) => ({
      time: formatTime(point.timestamp),
      score: point.score,
      sentiment: point.sentiment,
      index,
    }));

    return (
      <Box>
        {/* Sentiment Overview */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Sentiment Distribution
                </Typography>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={sentimentData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                    >
                      {sentimentData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Grid container spacing={2}>
              {sentimentData.map((item) => (
                <Grid item xs={4} key={item.name}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center', py: 2 }}>
                      <Typography variant="h4" sx={{ color: item.color }}>
                        {item.value}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {item.name}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Grid>
        </Grid>

        {/* Sentiment Timeline */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Sentiment Timeline
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="index" 
                  tickFormatter={(value) => timelineData[value]?.time || ''}
                />
                <YAxis domain={[-1, 1]} />
                <RechartsTooltip 
                  labelFormatter={(value) => `Time: ${timelineData[value]?.time}`}
                  formatter={(value: number) => [value.toFixed(2), 'Sentiment Score']}
                />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Detailed Sentiment Segments */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Sentiment Details
            </Typography>
            <List>
              {analysisResults.sentiment_analysis.slice(0, 10).map((point, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemIcon>
                      <Sentiment sx={{ color: getSentimentColor(point.sentiment) }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body1">
                            {point.text_segment}
                          </Typography>
                          <Chip
                            label={point.sentiment}
                            size="small"
                            sx={{
                              backgroundColor: getSentimentColor(point.sentiment),
                              color: 'white',
                            }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption">
                            Time: {formatTime(point.timestamp)} | 
                            Score: {point.score.toFixed(2)} | 
                            Confidence: {(point.confidence * 100).toFixed(0)}%
                          </Typography>
                          {point.keywords.length > 0 && (
                            <Box sx={{ mt: 1 }}>
                              {point.keywords.map((keyword, idx) => (
                                <Chip
                                  key={idx}
                                  label={keyword}
                                  size="small"
                                  variant="outlined"
                                  sx={{ mr: 0.5, mb: 0.5 }}
                                />
                              ))}
                            </Box>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < analysisResults.sentiment_analysis.slice(0, 10).length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      </Box>
    );
  };

  const renderTopicsTab = () => (
    <Box>
      {/* Topics Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Topic Confidence Scores
          </Typography>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={analysisResults.topic_clusters}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <RechartsTooltip />
              <Bar dataKey="confidence" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Topic Details */}
      <Grid container spacing={3}>
        {analysisResults.topic_clusters.map((topic, index) => (
          <Grid item xs={12} md={6} key={topic.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <Topic sx={{ mr: 1, verticalAlign: 'middle' }} />
                  {topic.name}
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Confidence: {(topic.confidence * 100).toFixed(1)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={topic.confidence * 100}
                    sx={{ mb: 2 }}
                  />
                </Box>

                <Typography variant="subtitle2" gutterBottom>
                  Keywords:
                </Typography>
                <Box sx={{ mb: 2 }}>
                  {topic.keywords.map((keyword, idx) => (
                    <Chip
                      key={idx}
                      label={keyword}
                      size="small"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </Box>

                <Typography variant="subtitle2" gutterBottom>
                  Summary:
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {topic.summary || 'No summary available'}
                </Typography>

                <Typography variant="caption" color="text.secondary">
                  {topic.segments.length} segments | 
                  Time range: {formatTime(Math.min(...topic.timestamps))} - {formatTime(Math.max(...topic.timestamps))}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderMeetingMinutesTab = () => {
    if (!analysisResults.meeting_minutes) {
      return (
        <Alert severity="info">
          Meeting minutes are only available for meeting-type content.
        </Alert>
      );
    }

    const minutes = analysisResults.meeting_minutes;

    return (
      <Box>
        {/* Meeting Header */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h4" gutterBottom>
              {minutes.title}
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle1">
                  <Schedule sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Date: {minutes.date}
                </Typography>
                <Typography variant="subtitle1">
                  Duration: {formatTime(minutes.duration)}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                {minutes.participants.length > 0 && (
                  <>
                    <Typography variant="subtitle1" gutterBottom>
                      Participants:
                    </Typography>
                    <Box>
                      {minutes.participants.map((participant, index) => (
                        <Chip
                          key={index}
                          icon={<Person />}
                          label={participant}
                          size="small"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                    </Box>
                  </>
                )}
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Meeting Content */}
        <Grid container spacing={3}>
          {/* Summary */}
          {minutes.summary && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Summary
                  </Typography>
                  <Typography variant="body1">
                    {minutes.summary}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Agenda Items */}
          {minutes.agenda_items.length > 0 && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Agenda Items
                  </Typography>
                  <List>
                    {minutes.agenda_items.map((item, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={`${index + 1}. ${item}`} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Key Decisions */}
          {minutes.key_decisions.length > 0 && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Key Decisions
                  </Typography>
                  <List>
                    {minutes.key_decisions.map((decision, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={`${index + 1}. ${decision}`} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Action Items */}
          {minutes.action_items.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Action Items
                  </Typography>
                  <List>
                    {minutes.action_items.map((item, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Assignment sx={{ color: getPriorityColor(item.priority) }} />
                        </ListItemIcon>
                        <ListItemText
                          primary={item.text}
                          secondary={
                            <Box>
                              {item.assignee && (
                                <Typography variant="caption">
                                  Assigned to: {item.assignee}
                                </Typography>
                              )}
                              {item.due_date && (
                                <Typography variant="caption" sx={{ ml: 2 }}>
                                  Due: {item.due_date}
                                </Typography>
                              )}
                              <Chip
                                label={item.priority}
                                size="small"
                                sx={{
                                  ml: 1,
                                  backgroundColor: getPriorityColor(item.priority),
                                  color: 'white',
                                }}
                              />
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Next Steps */}
          {minutes.next_steps.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Next Steps
                  </Typography>
                  <List>
                    {minutes.next_steps.map((step, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={`${index + 1}. ${step}`} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </Box>
    );
  };

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="Action Items" />
          <Tab label="Sentiment" />
          <Tab label="Topics" />
          <Tab label="Meeting Minutes" />
        </Tabs>
      </Box>

      <Box sx={{ mt: 2 }}>
        {activeTab === 0 && renderOverviewTab()}
        {activeTab === 1 && renderActionItemsTab()}
        {activeTab === 2 && renderSentimentTab()}
        {activeTab === 3 && renderTopicsTab()}
        {activeTab === 4 && renderMeetingMinutesTab()}
      </Box>

      {/* Export Actions */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button
          startIcon={<Download />}
          onClick={() => exportResults('json')}
          variant="outlined"
        >
          Export JSON
        </Button>
        <Button
          startIcon={<Share />}
          variant="outlined"
        >
          Share Results
        </Button>
      </Box>
    </Box>
  );
};

export default AIContentInsights;