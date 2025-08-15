import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Chip,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Search as SearchIcon,
  Link as LinkIcon,
  AccountTree as GraphIcon,
  Psychology as AIIcon,
  Language as LanguageIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Place as PlaceIcon,
  Event as EventIcon,
  AttachMoney as MoneyIcon,
  Percent as PercentIcon,
  Help as HelpIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Styled components
const StyledCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  transition: 'all 0.3s ease',
  '&:hover': {
    boxShadow: theme.shadows[4],
    transform: 'translateY(-2px)'
  }
}));

const EntityChip = styled(Chip)(({ theme, entitytype }) => {
  const getColor = (type: string) => {
    const colors = {
      PERSON: theme.palette.primary.main,
      ORG: theme.palette.secondary.main,
      GPE: theme.palette.success.main,
      PRODUCT: theme.palette.warning.main,
      EVENT: theme.palette.info.main,
      DATE: theme.palette.error.main,
      MONEY: '#4caf50',
      PERCENT: '#ff9800',
      CONCEPT: '#9c27b0',
      UNKNOWN: theme.palette.grey[500]
    };
    return colors[type] || theme.palette.grey[500];
  };

  return {
    backgroundColor: getColor(entitytype),
    color: theme.palette.getContrastText(getColor(entitytype)),
    margin: theme.spacing(0.5),
    '&:hover': {
      backgroundColor: getColor(entitytype),
      opacity: 0.8
    }
  };
});

const ConfidenceBar = styled(LinearProgress)(({ theme, confidence }) => ({
  height: 8,
  borderRadius: 4,
  backgroundColor: theme.palette.grey[200],
  '& .MuiLinearProgress-bar': {
    backgroundColor: confidence > 0.8 ? '#4caf50' : 
                    confidence > 0.5 ? '#ff9800' : '#f44336'
  }
}));

// Types
interface Entity {
  text: string;
  entity_type: string;
  confidence: number;
  provider: string;
  canonical_id: string;
  aliases: string[];
  properties: Record<string, any>;
  knowledge_links: any[];
}

interface UnifiedEntity {
  canonical_id: string;
  canonical_name: string;
  entity_type: string;
  aliases: string[];
  providers: string[];
  confidence_scores: Record<string, number>;
  overall_confidence: number;
  knowledge_links: any[];
  source_entities: number;
}

interface ExtractionResult {
  success: boolean;
  text: string;
  context?: string;
  total_entities: number;
  entity_links: number;
  knowledge_links: number;
  extraction_results: Record<string, any>;
  unified_entities: UnifiedEntity[];
  processing_time_ms: number;
  timestamp: string;
}

interface SearchResult {
  entity: Entity;
  links: any[];
}

interface SystemStats {
  success: boolean;
  total_entities: number;
  total_links: number;
  entities_by_provider: Record<string, number>;
  entities_by_type: Record<string, number>;
  knowledge_graph_nodes: number;
  knowledge_graph_edges: number;
  active_extractors: string[];
  active_knowledge_linkers: string[];
}

const CrossProviderEntityLinking: React.FC = () => {
  // State
  const [activeTab, setActiveTab] = useState(0);
  const [text, setText] = useState('');
  const [context, setContext] = useState('');
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [includeKnowledgeLinks, setIncludeKnowledgeLinks] = useState(true);
  const [extractionResult, setExtractionResult] = useState<ExtractionResult | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchEntityType, setSearchEntityType] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [availableProviders, setAvailableProviders] = useState<any[]>([]);
  const [entityTypes, setEntityTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<UnifiedEntity | null>(null);
  const [entityGraphDialog, setEntityGraphDialog] = useState(false);
  const [entityGraph, setEntityGraph] = useState<any>(null);

  // Sample texts for demo
  const sampleTexts = [
    {
      title: "Technology News",
      text: "Apple Inc. announced that Tim Cook will present the new iPhone at their Cupertino headquarters. The event will be streamed live on September 15th, 2024.",
      context: "technology news article"
    },
    {
      title: "Business Report",
      text: "Microsoft Corporation reported quarterly earnings of $2.1 billion. CEO Satya Nadella praised the Azure cloud platform's 50% growth in Seattle.",
      context: "business financial report"
    },
    {
      title: "Medical Research",
      text: "Dr. Sarah Johnson from Johns Hopkins University published research on COVID-19 treatments. The study was funded by the National Institutes of Health.",
      context: "medical research publication"
    }
  ];

  // Load initial data
  useEffect(() => {
    loadProviders();
    loadEntityTypes();
    loadSystemStats();
  }, []);

  const loadProviders = async () => {
    try {
      const response = await fetch('/api/v1/entity-linking/providers');
      const data = await response.json();
      if (data.success) {
        setAvailableProviders([...data.entity_extractors, ...data.knowledge_linkers]);
      }
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const loadEntityTypes = async () => {
    try {
      const response = await fetch('/api/v1/entity-linking/entity-types');
      const data = await response.json();
      if (data.success) {
        setEntityTypes(data.entity_types);
      }
    } catch (error) {
      console.error('Failed to load entity types:', error);
    }
  };

  const loadSystemStats = async () => {
    try {
      const response = await fetch('/api/v1/entity-linking/stats');
      const data = await response.json();
      if (data.success) {
        setSystemStats(data);
      }
    } catch (error) {
      console.error('Failed to load system stats:', error);
    }
  };

  const handleExtractEntities = async () => {
    if (!text.trim()) {
      setError('Please enter text to analyze');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/entity-linking/extract', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          context: context || undefined,
          providers: selectedProviders.length > 0 ? selectedProviders : undefined,
          include_knowledge_links: includeKnowledgeLinks
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setExtractionResult(data);
      } else {
        setError('Entity extraction failed');
      }
    } catch (error) {
      setError(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchEntities = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/entity-linking/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          entity_type: searchEntityType || undefined,
          limit: 20,
          include_links: true
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setSearchResults(data.results);
      } else {
        setError('Entity search failed');
      }
    } catch (error) {
      setError(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleViewEntityGraph = async (entityId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/entity-linking/graph', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity_id: entityId,
          depth: 2
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setEntityGraph(data);
        setEntityGraphDialog(true);
      } else {
        setError('Failed to load entity graph');
      }
    } catch (error) {
      setError(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getEntityIcon = (entityType: string) => {
    const icons = {
      PERSON: <PersonIcon />,
      ORG: <BusinessIcon />,
      GPE: <PlaceIcon />,
      PRODUCT: <BusinessIcon />,
      EVENT: <EventIcon />,
      DATE: <EventIcon />,
      MONEY: <MoneyIcon />,
      PERCENT: <PercentIcon />,
      CONCEPT: <AIIcon />,
      UNKNOWN: <HelpIcon />
    };
    return icons[entityType] || <HelpIcon />;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'success';
    if (confidence > 0.5) return 'warning';
    return 'error';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence > 0.8) return 'High';
    if (confidence > 0.5) return 'Medium';
    if (confidence > 0.2) return 'Low';
    return 'Very Low';
  };

  const loadSampleText = (sample: any) => {
    setText(sample.text);
    setContext(sample.context);
  };

  const renderExtractionResults = () => {
    if (!extractionResult) return null;

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Extraction Results
        </Typography>
        
        {/* Summary */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {extractionResult.total_entities}
              </Typography>
              <Typography variant="body2">Total Entities</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="secondary">
                {extractionResult.entity_links}
              </Typography>
              <Typography variant="body2">Entity Links</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">
                {extractionResult.knowledge_links}
              </Typography>
              <Typography variant="body2">Knowledge Links</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {Math.round(extractionResult.processing_time_ms)}ms
              </Typography>
              <Typography variant="body2">Processing Time</Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Provider Results */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">Results by Provider</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              {Object.entries(extractionResult.extraction_results).map(([provider, result]: [string, any]) => (
                <Grid item xs={12} sm={6} md={4} key={provider}>
                  <StyledCard>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {provider.toUpperCase()}
                      </Typography>
                      {result.error ? (
                        <Alert severity="error">{result.error}</Alert>
                      ) : (
                        <>
                          <Typography variant="body2" color="text.secondary">
                            {result.count} entities found
                          </Typography>
                          <Box sx={{ mt: 1 }}>
                            {result.entities?.slice(0, 3).map((entity: any, index: number) => (
                              <EntityChip
                                key={index}
                                label={entity.text}
                                entitytype={entity.entity_type}
                                size="small"
                              />
                            ))}
                          </Box>
                        </>
                      )}
                    </CardContent>
                  </StyledCard>
                </Grid>
              ))}
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Unified Entities */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">Unified Entities</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              {extractionResult.unified_entities.map((entity, index) => (
                <Grid item xs={12} sm={6} md={4} key={index}>
                  <StyledCard>
                    <CardContent>
                      <Box display="flex" alignItems="center" mb={1}>
                        {getEntityIcon(entity.entity_type)}
                        <Typography variant="h6" sx={{ ml: 1 }}>
                          {entity.canonical_name}
                        </Typography>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {entity.entity_type}
                      </Typography>
                      
                      <Box mb={2}>
                        <Typography variant="body2" gutterBottom>
                          Confidence: {getConfidenceLabel(entity.overall_confidence)}
                        </Typography>
                        <ConfidenceBar
                          variant="determinate"
                          value={entity.overall_confidence * 100}
                          confidence={entity.overall_confidence}
                        />
                      </Box>

                      <Typography variant="body2" gutterBottom>
                        Providers: {entity.providers.join(', ')}
                      </Typography>
                      
                      <Typography variant="body2" gutterBottom>
                        Sources: {entity.source_entities} entities
                      </Typography>

                      {entity.aliases.length > 0 && (
                        <Box mt={1}>
                          <Typography variant="body2" gutterBottom>
                            Aliases:
                          </Typography>
                          <Box>
                            {entity.aliases.slice(0, 3).map((alias, aliasIndex) => (
                              <Chip
                                key={aliasIndex}
                                label={alias}
                                size="small"
                                variant="outlined"
                                sx={{ mr: 0.5, mb: 0.5 }}
                              />
                            ))}
                          </Box>
                        </Box>
                      )}

                      <Box mt={2} display="flex" gap={1}>
                        <Tooltip title="View Knowledge Graph">
                          <IconButton
                            size="small"
                            onClick={() => handleViewEntityGraph(entity.canonical_id)}
                          >
                            <GraphIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => setSelectedEntity(entity)}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </CardContent>
                  </StyledCard>
                </Grid>
              ))}
            </Grid>
          </AccordionDetails>
        </Accordion>
      </Box>
    );
  };

  const renderSearchResults = () => {
    return (
      <Box>
        {searchResults.length > 0 && (
          <Typography variant="h6" gutterBottom>
            Search Results ({searchResults.length})
          </Typography>
        )}
        
        <Grid container spacing={2}>
          {searchResults.map((result, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <StyledCard>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    {getEntityIcon(result.entity.entity_type)}
                    <Typography variant="h6" sx={{ ml: 1 }}>
                      {result.entity.text}
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {result.entity.entity_type} • {result.entity.provider}
                  </Typography>
                  
                  <Box mb={2}>
                    <Typography variant="body2" gutterBottom>
                      Confidence: {getConfidenceLabel(result.entity.confidence)}
                    </Typography>
                    <ConfidenceBar
                      variant="determinate"
                      value={result.entity.confidence * 100}
                      confidence={result.entity.confidence}
                    />
                  </Box>

                  {result.entity.aliases.length > 0 && (
                    <Box mt={1}>
                      <Typography variant="body2" gutterBottom>
                        Aliases:
                      </Typography>
                      <Box>
                        {result.entity.aliases.slice(0, 2).map((alias, aliasIndex) => (
                          <Chip
                            key={aliasIndex}
                            label={alias}
                            size="small"
                            variant="outlined"
                            sx={{ mr: 0.5, mb: 0.5 }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}

                  {result.links.length > 0 && (
                    <Typography variant="body2" color="text.secondary">
                      {result.links.length} connections
                    </Typography>
                  )}

                  <Box mt={2} display="flex" gap={1}>
                    <Tooltip title="View Knowledge Graph">
                      <IconButton
                        size="small"
                        onClick={() => handleViewEntityGraph(result.entity.canonical_id)}
                      >
                        <GraphIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </CardContent>
              </StyledCard>
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  };

  const renderSystemStats = () => {
    if (!systemStats) return null;

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          System Statistics
        </Typography>
        
        <Grid container spacing={3}>
          {/* Overview */}
          <Grid item xs={12} md={6}>
            <StyledCard>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Overview
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Total Entities"
                      secondary={systemStats.total_entities.toLocaleString()}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Total Links"
                      secondary={systemStats.total_links.toLocaleString()}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Knowledge Graph Nodes"
                      secondary={systemStats.knowledge_graph_nodes.toLocaleString()}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Knowledge Graph Edges"
                      secondary={systemStats.knowledge_graph_edges.toLocaleString()}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </StyledCard>
          </Grid>

          {/* Entities by Provider */}
          <Grid item xs={12} md={6}>
            <StyledCard>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Entities by Provider
                </Typography>
                <List>
                  {Object.entries(systemStats.entities_by_provider).map(([provider, count]) => (
                    <ListItem key={provider}>
                      <ListItemText
                        primary={provider.toUpperCase()}
                        secondary={count.toLocaleString()}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </StyledCard>
          </Grid>

          {/* Entities by Type */}
          <Grid item xs={12} md={6}>
            <StyledCard>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Entities by Type
                </Typography>
                <List>
                  {Object.entries(systemStats.entities_by_type).map(([type, count]) => (
                    <ListItem key={type}>
                      <ListItemIcon>
                        {getEntityIcon(type)}
                      </ListItemIcon>
                      <ListItemText
                        primary={type}
                        secondary={count.toLocaleString()}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </StyledCard>
          </Grid>

          {/* Active Providers */}
          <Grid item xs={12} md={6}>
            <StyledCard>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Active Providers
                </Typography>
                <Typography variant="subtitle2" gutterBottom>
                  Entity Extractors:
                </Typography>
                <Box mb={2}>
                  {systemStats.active_extractors.map((extractor, index) => (
                    <Chip
                      key={index}
                      label={extractor}
                      color="primary"
                      size="small"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </Box>
                <Typography variant="subtitle2" gutterBottom>
                  Knowledge Linkers:
                </Typography>
                <Box>
                  {systemStats.active_knowledge_linkers.map((linker, index) => (
                    <Chip
                      key={index}
                      label={linker}
                      color="secondary"
                      size="small"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </Box>
              </CardContent>
            </StyledCard>
          </Grid>
        </Grid>
      </Box>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Cross-Provider Entity Linking
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Extract, link, and analyze entities across multiple AI providers and knowledge bases.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Entity Extraction" />
        <Tab label="Entity Search" />
        <Tab label="System Statistics" />
      </Tabs>

      {/* Entity Extraction Tab */}
      {activeTab === 0 && (
        <Box>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <StyledCard>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Text Analysis
                  </Typography>
                  
                  <TextField
                    fullWidth
                    multiline
                    rows={6}
                    label="Text to analyze"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Enter text to extract entities from..."
                    sx={{ mb: 2 }}
                  />
                  
                  <TextField
                    fullWidth
                    label="Context (optional)"
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    placeholder="Additional context for better extraction..."
                    sx={{ mb: 2 }}
                  />

                  <Box display="flex" gap={2} alignItems="center" mb={2}>
                    <FormControl sx={{ minWidth: 200 }}>
                      <InputLabel>Providers</InputLabel>
                      <Select
                        multiple
                        value={selectedProviders}
                        onChange={(e) => setSelectedProviders(e.target.value as string[])}
                        renderValue={(selected) => selected.join(', ')}
                      >
                        {availableProviders
                          .filter(p => p.type !== 'knowledge_base')
                          .map((provider) => (
                          <MenuItem key={provider.name} value={provider.name}>
                            {provider.name.toUpperCase()}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>

                    <FormControlLabel
                      control={
                        <Switch
                          checked={includeKnowledgeLinks}
                          onChange={(e) => setIncludeKnowledgeLinks(e.target.checked)}
                        />
                      }
                      label="Include Knowledge Links"
                    />
                  </Box>

                  <Button
                    variant="contained"
                    onClick={handleExtractEntities}
                    disabled={loading || !text.trim()}
                    startIcon={loading ? <CircularProgress size={20} /> : <AIIcon />}
                    sx={{ mr: 1 }}
                  >
                    {loading ? 'Analyzing...' : 'Extract Entities'}
                  </Button>

                  <Button
                    variant="outlined"
                    onClick={loadSystemStats}
                    startIcon={<RefreshIcon />}
                  >
                    Refresh Stats
                  </Button>
                </CardContent>
              </StyledCard>
            </Grid>

            <Grid item xs={12} md={4}>
              <StyledCard>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Sample Texts
                  </Typography>
                  {sampleTexts.map((sample, index) => (
                    <Box key={index} mb={2}>
                      <Typography variant="subtitle2" gutterBottom>
                        {sample.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        {sample.text.substring(0, 100)}...
                      </Typography>
                      <Button
                        size="small"
                        onClick={() => loadSampleText(sample)}
                      >
                        Load Sample
                      </Button>
                      <Divider sx={{ mt: 1 }} />
                    </Box>
                  ))}
                </CardContent>
              </StyledCard>
            </Grid>
          </Grid>

          {renderExtractionResults()}
        </Box>
      )}

      {/* Entity Search Tab */}
      {activeTab === 1 && (
        <Box>
          <StyledCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Entity Search
              </Typography>
              
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Search query"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search for entities..."
                    onKeyPress={(e) => e.key === 'Enter' && handleSearchEntities()}
                  />
                </Grid>
                
                <Grid item xs={12} sm={3}>
                  <FormControl fullWidth>
                    <InputLabel>Entity Type</InputLabel>
                    <Select
                      value={searchEntityType}
                      onChange={(e) => setSearchEntityType(e.target.value)}
                    >
                      <MenuItem value="">All Types</MenuItem>
                      {entityTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          {type.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={3}>
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={handleSearchEntities}
                    disabled={loading || !searchQuery.trim()}
                    startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
                  >
                    {loading ? 'Searching...' : 'Search'}
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </StyledCard>

          {renderSearchResults()}
        </Box>
      )}

      {/* System Statistics Tab */}
      {activeTab === 2 && renderSystemStats()}

      {/* Entity Graph Dialog */}
      <Dialog
        open={entityGraphDialog}
        onClose={() => setEntityGraphDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Entity Knowledge Graph
        </DialogTitle>
        <DialogContent>
          {entityGraph && (
            <Box>
              <Typography variant="body1" gutterBottom>
                Graph centered on: <strong>{entityGraph.center_entity}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Depth: {entityGraph.depth} | Nodes: {entityGraph.node_count} | Edges: {entityGraph.edge_count}
              </Typography>
              
              <Box mt={2}>
                <Typography variant="h6" gutterBottom>
                  Connected Entities
                </Typography>
                <Grid container spacing={1}>
                  {entityGraph.nodes.map((node: any, index: number) => (
                    <Grid item key={index}>
                      <Chip
                        label={node.data.name || node.id}
                        size="small"
                        color={node.id === entityGraph.center_entity ? 'primary' : 'default'}
                      />
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEntityGraphDialog(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Entity Details Dialog */}
      <Dialog
        open={!!selectedEntity}
        onClose={() => setSelectedEntity(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Entity Details
        </DialogTitle>
        <DialogContent>
          {selectedEntity && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedEntity.canonical_name}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Type: {selectedEntity.entity_type}
              </Typography>
              <Typography variant="body2" gutterBottom>
                Overall Confidence: {(selectedEntity.overall_confidence * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2" gutterBottom>
                Source Entities: {selectedEntity.source_entities}
              </Typography>
              
              <Box mt={2}>
                <Typography variant="subtitle2" gutterBottom>
                  Providers:
                </Typography>
                {selectedEntity.providers.map((provider, index) => (
                  <Chip
                    key={index}
                    label={provider}
                    size="small"
                    sx={{ mr: 0.5, mb: 0.5 }}
                  />
                ))}
              </Box>

              {selectedEntity.aliases.length > 0 && (
                <Box mt={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Aliases:
                  </Typography>
                  {selectedEntity.aliases.map((alias, index) => (
                    <Chip
                      key={index}
                      label={alias}
                      size="small"
                      variant="outlined"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </Box>
              )}

              {selectedEntity.knowledge_links.length > 0 && (
                <Box mt={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Knowledge Links: {selectedEntity.knowledge_links.length}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedEntity(null)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CrossProviderEntityLinking;