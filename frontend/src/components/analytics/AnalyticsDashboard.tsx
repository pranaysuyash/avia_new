import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Paper,
  Card,
  CardContent,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  TrendingUp,
  Analytics,
  Compare,
  Search,
  ExpandMore,
  Download,
  Refresh,
  FilterList,
  Timeline,
  Topic,
  Psychology
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

interface AnalyticsDashboardProps {
  className?: string;
}

interface TrendData {
  time_bucket: string;
  keywords?: Array<{
    keyword: string;
    score: number;
    frequency: number;
    growth_rate?: number;
  }>;
  topics?: Array<{
    topic_id: string;
    weight: number;
    keywords: string[];
  }>;
  entities?: Array<{
    entity: string;
    count: number;
  }>;
  sentiment?: {
    average_sentiment: number;
    sentiment_distribution: {
      positive: number;
      neutral: number;
      negative: number;
    };
  };
}

interface TopicModel {
  topics: Array<{
    topic_id: string;
    keywords: string[];
    weight: number;
    description: string;
  }>;
  coherence_score: number;
  num_topics: number;
}

interface ComparisonResult {
  source_a: string;
  source_b: string;
  similarities: {
    keyword_similarity: number;
    length_similarity: number;
    entity_similarity: number;
    overall_similarity: number;
  };
  common_themes: string[];
  unique_themes: {
    source_a_unique: string[];
    source_b_unique: string[];
  };
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ className }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Trend Analysis State
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [trendPeriod, setTrendPeriod] = useState('30d');
  const [analysisType, setAnalysisType] = useState('keywords');
  const [trendFilters, setTrendFilters] = useState({
    language: 'all',
    speakers: '',
    tags: '',
    minConfidence: 0
  });

  // Topic Modeling State
  const [topicModel, setTopicModel] = useState<TopicModel | null>(null);
  const [numTopics, setNumTopics] = useState(5);
  const [topicMethod, setTopicMethod] = useState('keyword_clustering');
  const [selectedTranscripts, setSelectedTranscripts] = useState<string[]>([]);

  // Comparative Analysis State
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [sourceA, setSourceA] = useState('');
  const [sourceB, setSourceB] = useState('');
  const [comparisonType, setComparisonType] = useState('comprehensive');

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const analyzeTrends = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/analytics/trends', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          time_period: trendPeriod,
          analysis_type: analysisType,
          filters: trendFilters
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze trends');
      }

      const result = await response.json();
      setTrendData(result.trends || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const extractTopics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/analytics/topics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript_ids: selectedTranscripts.length > 0 ? selectedTranscripts : null,
          num_topics: numTopics,
          method: topicMethod
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to extract topics');
      }

      const result = await response.json();
      setTopicModel(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const compareSources = async () => {
    if (!sourceA || !sourceB) {
      setError('Please specify both sources for comparison');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/analytics/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_a: sourceA,
          source_b: sourceB,
          comparison_type: comparisonType
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to compare sources');
      }

      const result = await response.json();
      setComparisonResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const exportResults = (data: any, filename: string) => {
    const jsonData = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const renderTrendAnalysis = () => (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TrendingUp />
        Trend Analysis
      </Typography>
      
      {/* Configuration Panel */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3 }}>
          <Box>
            <FormControl fullWidth>
              <InputLabel>Time Period</InputLabel>
              <Select
                value={trendPeriod}
                onChange={(e) => setTrendPeriod(e.target.value)}
                label="Time Period"
              >
                <MenuItem value="7d">Last 7 days</MenuItem>
                <MenuItem value="30d">Last 30 days</MenuItem>
                <MenuItem value="90d">Last 90 days</MenuItem>
                <MenuItem value="1y">Last year</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <Box>
            <FormControl fullWidth>
              <InputLabel>Analysis Type</InputLabel>
              <Select
                value={analysisType}
                onChange={(e) => setAnalysisType(e.target.value)}
                label="Analysis Type"
              >
                <MenuItem value="keywords">Keywords</MenuItem>
                <MenuItem value="topics">Topics</MenuItem>
                <MenuItem value="entities">Entities</MenuItem>
                <MenuItem value="sentiment">Sentiment</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <Box>
            <Button
              variant="contained"
              onClick={analyzeTrends}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <Analytics />}
              fullWidth
              sx={{ height: '56px' }}
            >
              Analyze Trends
            </Button>
          </Box>
          
          <Box>
            <Button
              variant="outlined"
              onClick={() => exportResults(trendData, 'trend_analysis')}
              disabled={trendData.length === 0}
              startIcon={<Download />}
              fullWidth
              sx={{ height: '56px' }}
            >
              Export Results
            </Button>
          </Box>
        </Box>

        {/* Advanced Filters */}
        <Accordion sx={{ mt: 2 }}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FilterList />
              Advanced Filters
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
              <Box>
                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={trendFilters.language}
                    onChange={(e) => setTrendFilters({...trendFilters, language: e.target.value})}
                    label="Language"
                  >
                    <MenuItem value="all">All Languages</MenuItem>
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Spanish</MenuItem>
                    <MenuItem value="fr">French</MenuItem>
                  </Select>
                </FormControl>
              </Box>
              
              <Box>
                <TextField
                  fullWidth
                  label="Speakers"
                  placeholder="John, Mary, Speaker 1"
                  value={trendFilters.speakers}
                  onChange={(e) => setTrendFilters({...trendFilters, speakers: e.target.value})}
                />
              </Box>
              
              <Box>
                <TextField
                  fullWidth
                  label="Tags"
                  placeholder="meeting, review, important"
                  value={trendFilters.tags}
                  onChange={(e) => setTrendFilters({...trendFilters, tags: e.target.value})}
                />
              </Box>
              
              <Box>
                <TextField
                  fullWidth
                  type="number"
                  label="Min Confidence"
                  inputProps={{ min: 0, max: 1, step: 0.1 }}
                  value={trendFilters.minConfidence}
                  onChange={(e) => setTrendFilters({...trendFilters, minConfidence: parseFloat(e.target.value)})}
                />
              </Box>
            </Box>
          </AccordionDetails>
        </Accordion>
      </Paper>

      {/* Results Display */}
      {trendData.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Trend Results ({trendData.length} time periods)
          </Typography>
          
          {analysisType === 'keywords' && (
            <Box>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time_bucket" />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  {trendData[0]?.keywords?.slice(0, 5).map((_, index) => (
                    <Line
                      key={index}
                      type="monotone"
                      dataKey={`keywords[${index}].score`}
                      stroke={COLORS[index % COLORS.length]}
                      strokeWidth={2}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
              
              {/* Growth Rate Chart */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>Top Growing Keywords</Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trendData.slice(-1)[0]?.keywords?.filter(k => k.growth_rate).slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="keyword" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="growth_rate" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </Box>
          )}
          
          {analysisType === 'sentiment' && (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time_bucket" />
                <YAxis domain={[-1, 1]} />
                <RechartsTooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="sentiment.average_sentiment"
                  stroke="#8884d8"
                  strokeWidth={3}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Paper>
      )}
    </Box>
  );

  const renderTopicModeling = () => (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Topic />
        Topic Modeling
      </Typography>
      
      {/* Configuration Panel */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3 }}>
          <Box>
            <TextField
              fullWidth
              type="number"
              label="Number of Topics"
              inputProps={{ min: 2, max: 20 }}
              value={numTopics}
              onChange={(e) => setNumTopics(parseInt(e.target.value))}
            />
          </Box>
          
          <Box>
            <FormControl fullWidth>
              <InputLabel>Method</InputLabel>
              <Select
                value={topicMethod}
                onChange={(e) => setTopicMethod(e.target.value)}
                label="Method"
              >
                <MenuItem value="keyword_clustering">Keyword Clustering</MenuItem>
                <MenuItem value="semantic_clustering">Semantic Clustering</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <Box>
            <Button
              variant="contained"
              onClick={extractTopics}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <Psychology />}
              fullWidth
              sx={{ height: '56px' }}
            >
              Extract Topics
            </Button>
          </Box>
          
          <Box>
            <Button
              variant="outlined"
              onClick={() => exportResults(topicModel, 'topic_model')}
              disabled={!topicModel}
              startIcon={<Download />}
              fullWidth
              sx={{ height: '56px' }}
            >
              Export Topics
            </Button>
          </Box>
        </Box>

        {/* Transcript Selection */}
        <Accordion sx={{ mt: 2 }}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography>Transcript Selection (Optional)</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Transcript IDs (one per line)"
              placeholder="transcript_1&#10;transcript_2&#10;transcript_3"
              value={selectedTranscripts.join('\n')}
              onChange={(e) => setSelectedTranscripts(e.target.value.split('\n').filter(id => id.trim()))}
            />
          </AccordionDetails>
        </Accordion>
      </Paper>

      {/* Results Display */}
      {topicModel && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3 }}>
            <Box>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Model Statistics</Typography>
                  <Typography>Topics: {topicModel.num_topics}</Typography>
                  <Typography>Coherence: {topicModel.coherence_score.toFixed(3)}</Typography>
                </CardContent>
              </Card>
            </Box>
            
            <Box>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topicModel.topics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="topic_id" />
                  <YAxis />
                  <RechartsTooltip />
                  <Bar dataKey="weight" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Box>

          {/* Topic Details */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>Topic Details</Typography>
            {topicModel.topics.map((topic, index) => (
              <Accordion key={topic.topic_id}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography>
                    {topic.topic_id}: {topic.description}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>Keywords:</Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {topic.keywords.map((keyword, idx) => (
                          <Chip key={idx} label={keyword} size="small" />
                        ))}
                      </Box>
                    </Box>
                    <Box>
                      <Typography variant="subtitle2">Weight: {topic.weight.toFixed(3)}</Typography>
                    </Box>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        </Paper>
      )}
    </Box>
  );

  const renderComparativeAnalysis = () => (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Compare />
        Comparative Analysis
      </Typography>
      
      {/* Configuration Panel */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3 }}>
          <Box>
            <TextField
              fullWidth
              label="Source A"
              placeholder="transcript_id or collection_name"
              value={sourceA}
              onChange={(e) => setSourceA(e.target.value)}
            />
          </Box>
          
          <Box>
            <TextField
              fullWidth
              label="Source B"
              placeholder="transcript_id or collection_name"
              value={sourceB}
              onChange={(e) => setSourceB(e.target.value)}
            />
          </Box>
          
          <Box>
            <FormControl fullWidth>
              <InputLabel>Comparison Type</InputLabel>
              <Select
                value={comparisonType}
                onChange={(e) => setComparisonType(e.target.value)}
                label="Comparison Type"
              >
                <MenuItem value="comprehensive">Comprehensive</MenuItem>
                <MenuItem value="keywords">Keywords Only</MenuItem>
                <MenuItem value="topics">Topics Only</MenuItem>
                <MenuItem value="sentiment">Sentiment Only</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Button
              variant="contained"
              onClick={compareSources}
              disabled={loading || !sourceA || !sourceB}
              startIcon={loading ? <CircularProgress size={20} /> : <Compare />}
              fullWidth
            >
              Compare Sources
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Results Display */}
      {comparisonResult && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Comparison: {comparisonResult.source_a} vs {comparisonResult.source_b}
          </Typography>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3 }}>
            {/* Similarity Metrics */}
            <Box>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Similarity Metrics</Typography>
                  {Object.entries(comparisonResult.similarities).map(([metric, value]) => (
                    <Box key={metric} sx={{ mb: 1 }}>
                      <Typography variant="body2">
                        {metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                          sx={{
                            width: '100%',
                            height: 8,
                            bgcolor: 'grey.300',
                            borderRadius: 1,
                            overflow: 'hidden'
                          }}
                        >
                          <Box
                            sx={{
                              width: `${value * 100}%`,
                              height: '100%',
                              bgcolor: value > 0.7 ? 'success.main' : value > 0.4 ? 'warning.main' : 'error.main'
                            }}
                          />
                        </Box>
                        <Typography variant="body2" sx={{ minWidth: 40 }}>
                          {(value * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Box>
            
            {/* Radar Chart */}
            <Box>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={Object.entries(comparisonResult.similarities).map(([key, value]) => ({
                  metric: key.replace('_', ' '),
                  value: value
                }))}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" />
                  <PolarRadiusAxis domain={[0, 1]} />
                  <Radar
                    name="Similarity"
                    dataKey="value"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.6}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </Box>
          </Box>

          {/* Common Themes */}
          {comparisonResult.common_themes.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>Common Themes</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {comparisonResult.common_themes.map((theme, index) => (
                  <Chip key={index} label={theme} color="primary" />
                ))}
              </Box>
            </Box>
          )}

          {/* Unique Themes */}
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3, mt: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Unique to {comparisonResult.source_a}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {comparisonResult.unique_themes.source_a_unique.map((theme, index) => (
                  <Chip key={index} label={theme} color="secondary" variant="outlined" />
                ))}
              </Box>
            </Box>
            
            <Box>
              <Typography variant="h6" gutterBottom>
                Unique to {comparisonResult.source_b}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {comparisonResult.unique_themes.source_b_unique.map((theme, index) => (
                  <Chip key={index} label={theme} color="info" variant="outlined" />
                ))}
              </Box>
            </Box>
          </Box>

          {/* Export Button */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Button
              variant="outlined"
              onClick={() => exportResults(comparisonResult, 'comparison_analysis')}
              startIcon={<Download />}
            >
              Export Comparison Results
            </Button>
          </Box>
        </Paper>
      )}
    </Box>
  );

  const renderSearchAnalytics = () => (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Search />
        Search Analytics
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        Search analytics coming soon! This will show popular search terms, success rates, and user behavior patterns.
      </Alert>
      
      {/* Placeholder Charts */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3 }}>
        <Box>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Popular Search Terms</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { term: 'meeting', frequency: 45 },
                { term: 'project', frequency: 32 },
                { term: 'discussion', frequency: 28 },
                { term: 'presentation', frequency: 21 },
                { term: 'interview', frequency: 18 }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="term" />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="frequency" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Box>
        
        <Box>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Search Success Rates</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { term: 'meeting', success_rate: 0.89 },
                { term: 'project', success_rate: 0.76 },
                { term: 'discussion', success_rate: 0.82 },
                { term: 'presentation', success_rate: 0.91 },
                { term: 'interview', success_rate: 0.73 }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="term" />
                <YAxis domain={[0, 1]} />
                <RechartsTooltip />
                <Bar dataKey="success_rate" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Box>
      </Box>
    </Box>
  );

  return (
    <Container maxWidth="xl" className={className}>
      <Box sx={{ py: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Analytics />
          Advanced Analytics Dashboard
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Paper sx={{ width: '100%' }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab
              label="Trend Analysis"
              icon={<TrendingUp />}
              iconPosition="start"
            />
            <Tab
              label="Topic Modeling"
              icon={<Topic />}
              iconPosition="start"
            />
            <Tab
              label="Comparative Analysis"
              icon={<Compare />}
              iconPosition="start"
            />
            <Tab
              label="Search Analytics"
              icon={<Search />}
              iconPosition="start"
            />
          </Tabs>

          <Box sx={{ p: 3 }}>
            {activeTab === 0 && renderTrendAnalysis()}
            {activeTab === 1 && renderTopicModeling()}
            {activeTab === 2 && renderComparativeAnalysis()}
            {activeTab === 3 && renderSearchAnalytics()}
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default AnalyticsDashboard;