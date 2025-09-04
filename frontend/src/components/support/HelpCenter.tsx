import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Button,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  Divider,
  Rating,
  CircularProgress,
  Alert,
  Breadcrumbs,
  Link,
  Container,
  Tooltip,
  Badge
} from '@mui/material';
import {
  Search as SearchIcon,
  Article as ArticleIcon,
  ExpandMore as ExpandMoreIcon,
  Category as CategoryIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Visibility as ViewIcon,
  AccessTime as TimeIcon,
  LocalOffer as TagIcon,
  QuestionAnswer as FAQIcon,
  VideoLibrary as VideoIcon,
  School as TutorialIcon,
  Forum as ForumIcon,
  Lightbulb as TipIcon,
  NavigateNext as NavigateNextIcon
} from '@mui/icons-material';
import { supportApi } from '../../services/supportApi';
import ReactMarkdown from 'react-markdown';

interface HelpArticle {
  id: string;
  title: string;
  slug: string;
  content: string;
  category: string;
  tags: string[];
  views: number;
  helpful_count: number;
  not_helpful_count: number;
  created_at: string;
  updated_at: string;
  author: string;
  related_articles: string[];
  reading_time: number;
}

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: string;
  helpful_count: number;
  views: number;
}

interface Category {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  articleCount: number;
}

const categories: Category[] = [
  {
    id: 'getting_started',
    name: 'Getting Started',
    icon: <TutorialIcon />,
    description: 'Learn the basics and get up and running',
    articleCount: 0
  },
  {
    id: 'transcription',
    name: 'Transcription',
    icon: <ArticleIcon />,
    description: 'Everything about audio and video transcription',
    articleCount: 0
  },
  {
    id: 'features',
    name: 'Features',
    icon: <TipIcon />,
    description: 'Explore all available features',
    articleCount: 0
  },
  {
    id: 'billing',
    name: 'Billing',
    icon: <CategoryIcon />,
    description: 'Pricing, subscriptions, and payments',
    articleCount: 0
  },
  {
    id: 'technical',
    name: 'Technical',
    icon: <CategoryIcon />,
    description: 'Technical guides and troubleshooting',
    articleCount: 0
  },
  {
    id: 'api',
    name: 'API',
    icon: <CategoryIcon />,
    description: 'API documentation and integration',
    articleCount: 0
  }
];

const HelpCenter: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [articles, setArticles] = useState<HelpArticle[]>([]);
  const [faqItems, setFaqItems] = useState<FAQItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<HelpArticle | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [popularArticles, setPopularArticles] = useState<HelpArticle[]>([]);

  useEffect(() => {
    fetchHelpContent();
  }, []);

  const fetchHelpContent = async () => {
    setLoading(true);
    try {
      const [articlesRes, faqRes] = await Promise.all([
        supportApi.getHelpArticles(),
        supportApi.getFAQs()
      ]);
      
      setArticles(articlesRes.data);
      setFaqItems(faqRes.data);
      
      // Set popular articles (top 5 by views)
      const popular = [...articlesRes.data]
        .sort((a, b) => b.views - a.views)
        .slice(0, 5);
      setPopularArticles(popular);
    } catch (error) {
      console.error('Error fetching help content:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchArticles = async () => {
    if (!searchQuery.trim()) {
      fetchHelpContent();
      return;
    }
    
    setLoading(true);
    try {
      const response = await supportApi.searchHelpArticles(searchQuery, selectedCategory);
      setArticles(response.data);
    } catch (error) {
      console.error('Error searching articles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleArticleFeedback = async (articleId: string, helpful: boolean) => {
    try {
      await supportApi.rateHelpArticle(articleId, helpful);
      // Update local state
      setArticles(prev => prev.map(article => {
        if (article.id === articleId) {
          return {
            ...article,
            helpful_count: helpful ? article.helpful_count + 1 : article.helpful_count,
            not_helpful_count: !helpful ? article.not_helpful_count + 1 : article.not_helpful_count
          };
        }
        return article;
      }));
    } catch (error) {
      console.error('Error rating article:', error);
    }
  };

  const getFilteredArticles = () => {
    let filtered = articles;
    
    if (selectedCategory) {
      filtered = filtered.filter(article => article.category === selectedCategory);
    }
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(article =>
        article.title.toLowerCase().includes(query) ||
        article.content.toLowerCase().includes(query) ||
        article.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }
    
    return filtered;
  };

  const getFilteredFAQs = () => {
    let filtered = faqItems;
    
    if (selectedCategory) {
      filtered = filtered.filter(faq => faq.category === selectedCategory);
    }
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(faq =>
        faq.question.toLowerCase().includes(query) ||
        faq.answer.toLowerCase().includes(query)
      );
    }
    
    return filtered;
  };

  if (loading && articles.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" gutterBottom>
          How can we help?
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Search our knowledge base or browse categories below
        </Typography>
        <Button
          variant="outlined"
          size="small"
          onClick={async () => {
            try {
              const u = new URL(window.location.href);
              await navigator.clipboard.writeText(u.toString());
              // eslint-disable-next-line @typescript-eslint/no-var-requires
              const { logUxEvent } = require('../../components/shared/uxTelemetry');
              try { logUxEvent('share_view_copied', { page: 'help_center' }); } catch {}
            } catch {}
          }}
          sx={{ mt: 1 }}
        >
          Share
        </Button>
        
        {/* Search Bar */}
        <Paper sx={{ p: 1, maxWidth: 600, mx: 'auto' }}>
          <TextField
            fullWidth
            placeholder="Search for articles, tutorials, or FAQs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                searchArticles();
              }
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: searchQuery && (
                <InputAdornment position="end">
                  <IconButton size="small" onClick={() => setSearchQuery('')}>
                    ×
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
        </Paper>
      </Box>

      {/* Categories */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {categories.map((category) => (
          <Grid item xs={12} sm={6} md={4} key={category.id}>
            <Card
              sx={{
                cursor: 'pointer',
                '&:hover': { boxShadow: 3 },
                border: selectedCategory === category.id ? 2 : 0,
                borderColor: 'primary.main'
              }}
              onClick={() => setSelectedCategory(
                selectedCategory === category.id ? null : category.id
              )}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  {category.icon}
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    {category.name}
                  </Typography>
                  <Badge
                    badgeContent={
                      articles.filter(a => a.category === category.id).length
                    }
                    color="primary"
                    sx={{ ml: 'auto' }}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {category.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Left Sidebar - Popular Articles */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Popular Articles
            </Typography>
            <List dense>
              {popularArticles.map((article) => (
                <ListItem
                  key={article.id}
                  button
                  onClick={() => setSelectedArticle(article)}
                >
                  <ListItemIcon>
                    <ArticleIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={article.title}
                    secondary={`${article.views} views`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Links
            </Typography>
            <List dense>
              <ListItem button>
                <ListItemIcon>
                  <VideoIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="Video Tutorials" />
              </ListItem>
              <ListItem button>
                <ListItemIcon>
                  <ForumIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="Community Forum" />
              </ListItem>
              <ListItem button>
                <ListItemIcon>
                  <FAQIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="Contact Support" />
              </ListItem>
            </List>
          </Paper>
        </Grid>

        {/* Main Content Area */}
        <Grid item xs={12} md={9}>
          {selectedArticle ? (
            // Article View
            <Paper sx={{ p: 3 }}>
              <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} sx={{ mb: 2 }}>
                <Link
                  color="inherit"
                  href="#"
                  onClick={() => setSelectedArticle(null)}
                >
                  Help Center
                </Link>
                <Typography color="text.primary">{selectedArticle.category}</Typography>
                <Typography color="text.primary">{selectedArticle.title}</Typography>
              </Breadcrumbs>

              <Typography variant="h4" gutterBottom>
                {selectedArticle.title}
              </Typography>

              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <Chip
                  icon={<CategoryIcon />}
                  label={selectedArticle.category}
                  size="small"
                />
                <Chip
                  icon={<TimeIcon />}
                  label={`${selectedArticle.reading_time || 5} min read`}
                  size="small"
                />
                <Chip
                  icon={<ViewIcon />}
                  label={`${selectedArticle.views} views`}
                  size="small"
                />
              </Box>

              <Divider sx={{ mb: 3 }} />

              <ReactMarkdown>{selectedArticle.content}</ReactMarkdown>

              <Divider sx={{ my: 3 }} />

              {/* Article Feedback */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2">Was this article helpful?</Typography>
                <Button
                  startIcon={<ThumbUpIcon />}
                  onClick={() => handleArticleFeedback(selectedArticle.id, true)}
                >
                  Yes ({selectedArticle.helpful_count})
                </Button>
                <Button
                  startIcon={<ThumbDownIcon />}
                  onClick={() => handleArticleFeedback(selectedArticle.id, false)}
                >
                  No ({selectedArticle.not_helpful_count})
                </Button>
              </Box>

              {/* Tags */}
              {selectedArticle.tags.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" gutterBottom>
                    Tags:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedArticle.tags.map((tag, index) => (
                      <Chip
                        key={index}
                        label={tag}
                        size="small"
                        icon={<TagIcon />}
                        onClick={() => setSearchQuery(tag)}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Related Articles */}
              {selectedArticle.related_articles.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Related Articles
                  </Typography>
                  <List>
                    {selectedArticle.related_articles.map((relatedId) => {
                      const related = articles.find(a => a.id === relatedId);
                      if (!related) return null;
                      return (
                        <ListItem
                          key={related.id}
                          button
                          onClick={() => setSelectedArticle(related)}
                        >
                          <ListItemIcon>
                            <ArticleIcon />
                          </ListItemIcon>
                          <ListItemText primary={related.title} />
                        </ListItem>
                      );
                    })}
                  </List>
                </Box>
              )}
            </Paper>
          ) : (
            // Articles and FAQ List
            <Box>
              <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
                <Tab label={`Articles (${getFilteredArticles().length})`} />
                <Tab label={`FAQ (${getFilteredFAQs().length})`} />
              </Tabs>

              {tabValue === 0 && (
                // Articles Tab
                <Box sx={{ mt: 3 }}>
                  {getFilteredArticles().length === 0 ? (
                    <Alert severity="info">
                      No articles found. Try different search terms or browse categories.
                    </Alert>
                  ) : (
                    <Grid container spacing={2}>
                      {getFilteredArticles().map((article) => (
                        <Grid item xs={12} key={article.id}>
                          <Card
                            sx={{
                              cursor: 'pointer',
                              '&:hover': { boxShadow: 2 }
                            }}
                            onClick={() => setSelectedArticle(article)}
                          >
                            <CardContent>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Box sx={{ flex: 1 }}>
                                  <Typography variant="h6" gutterBottom>
                                    {article.title}
                                  </Typography>
                                  <Typography
                                    variant="body2"
                                    color="text.secondary"
                                    sx={{
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      display: '-webkit-box',
                                      WebkitLineClamp: 2,
                                      WebkitBoxOrient: 'vertical'
                                    }}
                                  >
                                    {article.content.substring(0, 200)}...
                                  </Typography>
                                  <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                                    <Chip
                                      label={article.category}
                                      size="small"
                                      variant="outlined"
                                    />
                                    {article.tags.slice(0, 2).map((tag, index) => (
                                      <Chip
                                        key={index}
                                        label={tag}
                                        size="small"
                                        variant="outlined"
                                      />
                                    ))}
                                  </Box>
                                </Box>
                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                                  <Typography variant="caption" color="text.secondary">
                                    {article.views} views
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {new Date(article.updated_at).toLocaleDateString()}
                                  </Typography>
                                </Box>
                              </Box>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  )}
                </Box>
              )}

              {tabValue === 1 && (
                // FAQ Tab
                <Box sx={{ mt: 3 }}>
                  {getFilteredFAQs().length === 0 ? (
                    <Alert severity="info">
                      No FAQs found. Try different search terms or browse categories.
                    </Alert>
                  ) : (
                    getFilteredFAQs().map((faq) => (
                      <Accordion key={faq.id} sx={{ mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', pr: 2 }}>
                            <FAQIcon sx={{ mr: 2, color: 'primary.main' }} />
                            <Typography sx={{ flex: 1 }}>{faq.question}</Typography>
                            <Chip
                              label={faq.category}
                              size="small"
                              sx={{ ml: 2 }}
                            />
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Typography variant="body2" color="text.secondary">
                            {faq.answer}
                          </Typography>
                          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Typography variant="caption" color="text.secondary">
                              Was this helpful?
                            </Typography>
                            <IconButton size="small">
                              <ThumbUpIcon fontSize="small" />
                            </IconButton>
                            <IconButton size="small">
                              <ThumbDownIcon fontSize="small" />
                            </IconButton>
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                              {faq.views} views
                            </Typography>
                          </Box>
                        </AccordionDetails>
                      </Accordion>
                    ))
                  )}
                </Box>
              )}
            </Box>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default HelpCenter;
