import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  Avatar,
  Rating,
  Badge,
  Tab,
  Tabs,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Tooltip,
  Skeleton,
  Pagination,
  ToggleButton,
  ToggleButtonGroup,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  InputAdornment,
  Menu,
  Switch,
  FormControlLabel,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Snackbar,
  Drawer,
  TreeView,
  TreeItem,
  Breadcrumbs,
  Link,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Collapse,
  ButtonGroup,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Backdrop,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Stack,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
} from '@mui/material';
import {
  Store as StoreIcon,
  Search,
  FilterList,
  Sort,
  Download,
  Star,
  StarBorder,
  GetApp,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Info,
  Verified,
  TrendingUp,
  Category,
  Extension,
  Palette,
  IntegrationInstructions,
  AccountTree,
  ModelTraining,
  Dataset,
  Code,
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Settings,
  Share,
  Favorite,
  FavoriteBorder,
  ExpandMore,
  ExpandLess,
  Reviews,
  Security,
  UpdateDisabled,
  Update,
  DeleteForever,
  Launch,
  Preview,
  GitHub,
  Description,
  Visibility,
  MonetizationOn,
  Free,
  Payment,
  ShoppingCart,
  InstallDesktop,
  CloudDownload,
  Cancel,
  CheckBox,
  IndeterminateCheckBox,
  FolderOpen,
  History,
  NewReleases,
  LocalOffer,
  Sync,
  SyncDisabled,
  Schedule,
  Assessment,
  Build,
  BugReport,
  Feedback,
  RateReview,
  OpenInNew,
  CloudOff,
  CloudQueue,
  AutoAwesome,
  Inventory,
  Dashboard,
  ViewList,
  ViewModule,
  ViewQuilt,
  GridView,
  TableChart,
} from '@mui/icons-material';
import { apiClient } from '../../services/api';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut, Pie } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement
);

interface MarketplaceItem {
  id: string;
  name: string;
  description: string;
  type: 'plugin' | 'extension' | 'template' | 'integration' | 'workflow' | 'theme' | 'model' | 'dataset';
  version: string;
  category: string;
  tags: string[];
  compatibility: 'stable' | 'beta' | 'alpha' | 'experimental';
  supported_versions: string[];
  price: number;
  currency: string;
  license: string;
  status: string;
  developer_id: string;
  developer_name: string;
  downloads: number;
  rating: number;
  review_count: number;
  created_at: string;
  updated_at: string;
  repository_url?: string;
  documentation_url?: string;
  demo_url?: string;
  screenshots: string[];
  dependencies: string[];
  permissions: string[];
  verified: boolean;
  file_size?: number;
}

interface Installation {
  id: string;
  item_id: string;
  version: string;
  status: 'not_installed' | 'installing' | 'installed' | 'updating' | 'failed';
  installed_at: string;
  auto_update: boolean;
  usage_stats: Record<string, any>;
}

interface MarketplaceStats {
  total_items: number;
  total_downloads: number;
  total_developers: number;
  popular_categories: Record<string, number>;
  trending_items: string[];
  revenue_stats: Record<string, number>;
  by_type: Record<string, number>;
}

const typeIcons = {
  plugin: <Extension />,
  extension: <Extension />,
  template: <Code />,
  integration: <IntegrationInstructions />,
  workflow: <AccountTree />,
  theme: <Palette />,
  model: <ModelTraining />,
  dataset: <Dataset />,
};

const typeColors = {
  plugin: '#2196f3',
  extension: '#4caf50',
  template: '#ff9800',
  integration: '#9c27b0',
  workflow: '#f44336',
  theme: '#607d8b',
  model: '#795548',
  dataset: '#3f51b5',
};

const compatibilityColors = {
  stable: 'success',
  beta: 'warning',
  alpha: 'info',
  experimental: 'error',
} as const;

const MarketplaceBrowser: React.FC = () => {
  const [items, setItems] = useState<MarketplaceItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<MarketplaceItem[]>([]);
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [stats, setStats] = useState<MarketplaceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [compatibilityFilter, setCompatibilityFilter] = useState('');
  const [priceFilter, setPriceFilter] = useState('');
  const [sortBy, setSortBy] = useState('downloads');
  const [sortOrder, setSortOrder] = useState('desc');
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'table' | 'cards'>('cards');
  const [selectedItem, setSelectedItem] = useState<MarketplaceItem | null>(null);
  const [itemDetailsOpen, setItemDetailsOpen] = useState(false);
  const [installDialogOpen, setInstallDialogOpen] = useState(false);
  const [reviewsDialogOpen, setReviewsDialogOpen] = useState(false);
  const [filtersDrawerOpen, setFiltersDrawerOpen] = useState(false);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [installQueue, setInstallQueue] = useState<string[]>([]);
  const [updateAvailable, setUpdateAvailable] = useState<string[]>([]);
  const [speedDialOpen, setSpeedDialOpen] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(12);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const searchTimeout = useRef<NodeJS.Timeout>();

  useEffect(() => {
    loadMarketplaceData();
    loadInstallations();
    loadFavorites();
    loadStats();
  }, []);

  useEffect(() => {
    filterAndSortItems();
  }, [
    items,
    searchQuery,
    selectedCategory,
    selectedType,
    compatibilityFilter,
    priceFilter,
    sortBy,
    sortOrder,
  ]);

  const loadMarketplaceData = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/marketplace/');
      setItems(response.data);
    } catch (error) {
      console.error('Failed to load marketplace data:', error);
      setSnackbar({
        open: true,
        message: 'Failed to load marketplace items',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadInstallations = async () => {
    try {
      const response = await apiClient.get('/api/v1/marketplace/installations/');
      setInstallations(response.data);

      // Check for updates
      const updatesAvailable = response.data
        .filter((installation: Installation) => {
          const item = items.find(i => i.id === installation.item_id);
          return item && item.version !== installation.version;
        })
        .map((installation: Installation) => installation.item_id);
      
      setUpdateAvailable(updatesAvailable);
    } catch (error) {
      console.error('Failed to load installations:', error);
    }
  };

  const loadFavorites = async () => {
    try {
      const saved = localStorage.getItem('marketplace_favorites');
      if (saved) {
        setFavorites(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Failed to load favorites:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiClient.get('/api/v1/marketplace/stats/');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load marketplace stats:', error);
    }
  };

  const filterAndSortItems = () => {
    let filtered = [...items];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        item =>
          item.name.toLowerCase().includes(query) ||
          item.description.toLowerCase().includes(query) ||
          item.developer_name.toLowerCase().includes(query) ||
          item.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    // Category filter
    if (selectedCategory) {
      filtered = filtered.filter(item => item.category === selectedCategory);
    }

    // Type filter
    if (selectedType) {
      filtered = filtered.filter(item => item.type === selectedType);
    }

    // Compatibility filter
    if (compatibilityFilter) {
      filtered = filtered.filter(item => item.compatibility === compatibilityFilter);
    }

    // Price filter
    if (priceFilter === 'free') {
      filtered = filtered.filter(item => item.price === 0);
    } else if (priceFilter === 'paid') {
      filtered = filtered.filter(item => item.price > 0);
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'downloads':
          comparison = a.downloads - b.downloads;
          break;
        case 'rating':
          comparison = a.rating - b.rating;
          break;
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'price':
          comparison = a.price - b.price;
          break;
        default:
          comparison = 0;
      }

      return sortOrder === 'desc' ? -comparison : comparison;
    });

    setFilteredItems(filtered);
  };

  const handleInstall = async (item: MarketplaceItem) => {
    try {
      setInstallQueue([...installQueue, item.id]);
      
      await apiClient.post(`/api/v1/marketplace/${item.id}/install`, {
        item_id: item.id,
        auto_update: true,
      });
      
      setSnackbar({
        open: true,
        message: `Installing ${item.name}...`,
        severity: 'info',
      });
      
      setInstallDialogOpen(false);
      
      // Simulate installation progress
      setTimeout(() => {
        setInstallQueue(prev => prev.filter(id => id !== item.id));
        loadInstallations();
        setSnackbar({
          open: true,
          message: `${item.name} installed successfully!`,
          severity: 'success',
        });
      }, 3000);
    } catch (error) {
      setInstallQueue(prev => prev.filter(id => id !== item.id));
      setSnackbar({
        open: true,
        message: `Failed to install ${item.name}`,
        severity: 'error',
      });
    }
  };

  const handleUninstall = async (installation: Installation) => {
    try {
      await apiClient.delete(`/api/v1/marketplace/installations/${installation.id}`);
      
      setSnackbar({
        open: true,
        message: 'Item uninstalled successfully',
        severity: 'success',
      });
      
      loadInstallations();
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to uninstall item',
        severity: 'error',
      });
    }
  };

  const toggleFavorite = (itemId: string) => {
    const newFavorites = favorites.includes(itemId)
      ? favorites.filter(id => id !== itemId)
      : [...favorites, itemId];
    
    setFavorites(newFavorites);
    localStorage.setItem('marketplace_favorites', JSON.stringify(newFavorites));
  };

  const getInstallationStatus = (itemId: string): Installation | null => {
    return installations.find(inst => inst.item_id === itemId) || null;
  };

  const renderItemCard = (item: MarketplaceItem) => {
    const installation = getInstallationStatus(item.id);
    const isFavorite = favorites.includes(item.id);
    const isInstalling = installQueue.includes(item.id);
    const hasUpdate = updateAvailable.includes(item.id);

    return (
      <Card
        key={item.id}
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
          transition: 'all 0.2s',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: 4,
          },
        }}
      >
        <Box sx={{ position: 'relative' }}>
          {item.verified && (
            <Chip
              icon={<Verified />}
              label="Verified"
              color="primary"
              size="small"
              sx={{ position: 'absolute', top: 8, right: 8, zIndex: 1 }}
            />
          )}
          
          {hasUpdate && (
            <Chip
              icon={<NewReleases />}
              label="Update"
              color="warning"
              size="small"
              sx={{ position: 'absolute', top: 8, left: 8, zIndex: 1 }}
            />
          )}

          <CardContent sx={{ flexGrow: 1, pb: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Avatar
                sx={{
                  bgcolor: typeColors[item.type],
                  mr: 2,
                  width: 48,
                  height: 48,
                }}
              >
                {typeIcons[item.type]}
              </Avatar>
              <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                <Typography variant="h6" component="div" noWrap sx={{ fontWeight: 600 }}>
                  {item.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  by {item.developer_name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  v{item.version} • {item.type}
                </Typography>
              </Box>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFavorite(item.id);
                }}
                color={isFavorite ? 'error' : 'default'}
              >
                {isFavorite ? <Favorite /> : <FavoriteBorder />}
              </IconButton>
            </Box>

            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                mb: 2,
                height: 40,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
              }}
            >
              {item.description}
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Rating value={item.rating} readOnly size="small" precision={0.1} />
              <Typography variant="caption" sx={{ ml: 1 }}>
                {item.rating} ({item.review_count})
              </Typography>
              <Box sx={{ flexGrow: 1 }} />
              <Typography variant="caption">
                <Download sx={{ fontSize: 14, mr: 0.5 }} />
                {item.downloads.toLocaleString()}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
              <Chip
                label={item.compatibility}
                color={compatibilityColors[item.compatibility]}
                size="small"
              />
              <Chip
                label={item.category}
                variant="outlined"
                size="small"
              />
              {item.price > 0 ? (
                <Chip
                  icon={<MonetizationOn />}
                  label={`$${item.price}`}
                  color="secondary"
                  size="small"
                />
              ) : (
                <Chip
                  icon={<Free />}
                  label="Free"
                  color="success"
                  size="small"
                />
              )}
            </Box>

            {installation && (
              <Box sx={{ mb: 2 }}>
                <Chip
                  label={installation.status.replace('_', ' ').toUpperCase()}
                  color={installation.status === 'installed' ? 'success' : 'warning'}
                  size="small"
                  icon={
                    installation.status === 'installed' ? (
                      <CheckCircle />
                    ) : (
                      <CircularProgress size={16} />
                    )
                  }
                />
              </Box>
            )}

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {item.tags.slice(0, 2).map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              ))}
              {item.tags.length > 2 && (
                <Typography variant="caption" color="text.secondary">
                  +{item.tags.length - 2}
                </Typography>
              )}
            </Box>
          </CardContent>
        </Box>

        <CardActions sx={{ p: 2, pt: 0, gap: 1 }}>
          <Button
            size="small"
            onClick={() => {
              setSelectedItem(item);
              setItemDetailsOpen(true);
            }}
            startIcon={<Visibility />}
          >
            Details
          </Button>
          
          <Box sx={{ flexGrow: 1 }} />
          
          {installation?.status === 'installed' ? (
            <ButtonGroup size="small" variant="outlined">
              {hasUpdate && (
                <Button
                  color="warning"
                  startIcon={<Update />}
                  onClick={() => {
                    setSelectedItem(item);
                    setInstallDialogOpen(true);
                  }}
                >
                  Update
                </Button>
              )}
              <Button
                color="error"
                startIcon={<DeleteForever />}
                onClick={() => handleUninstall(installation)}
              >
                Remove
              </Button>
            </ButtonGroup>
          ) : isInstalling ? (
            <Button
              variant="outlined"
              size="small"
              disabled
              startIcon={<CircularProgress size={16} />}
            >
              Installing...
            </Button>
          ) : (
            <Button
              variant="contained"
              size="small"
              startIcon={<GetApp />}
              onClick={() => {
                setSelectedItem(item);
                setInstallDialogOpen(true);
              }}
            >
              Install
            </Button>
          )}
        </CardActions>
      </Card>
    );
  };

  const renderTableView = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Item</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Rating</TableCell>
            <TableCell>Downloads</TableCell>
            <TableCell>Price</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {filteredItems
            .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
            .map((item) => {
              const installation = getInstallationStatus(item.id);
              const isFavorite = favorites.includes(item.id);
              const hasUpdate = updateAvailable.includes(item.id);

              return (
                <TableRow key={item.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar
                        sx={{ bgcolor: typeColors[item.type], mr: 2, width: 32, height: 32 }}
                      >
                        {typeIcons[item.type]}
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                          {item.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {item.developer_name} • v{item.version}
                        </Typography>
                      </Box>
                      {item.verified && <Verified color="primary" sx={{ ml: 1 }} />}
                      {hasUpdate && <NewReleases color="warning" sx={{ ml: 1 }} />}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={item.type}
                      size="small"
                      sx={{ bgcolor: typeColors[item.type], color: 'white' }}
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Rating value={item.rating} readOnly size="small" />
                      <Typography variant="caption" sx={{ ml: 1 }}>
                        ({item.review_count})
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{item.downloads.toLocaleString()}</TableCell>
                  <TableCell>
                    {item.price > 0 ? `$${item.price}` : 'Free'}
                  </TableCell>
                  <TableCell>
                    {installation ? (
                      <Chip
                        label={installation.status}
                        color={installation.status === 'installed' ? 'success' : 'warning'}
                        size="small"
                      />
                    ) : (
                      <Chip label="Not installed" variant="outlined" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <IconButton
                        size="small"
                        onClick={() => toggleFavorite(item.id)}
                        color={isFavorite ? 'error' : 'default'}
                      >
                        {isFavorite ? <Favorite /> : <FavoriteBorder />}
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedItem(item);
                          setItemDetailsOpen(true);
                        }}
                      >
                        <Visibility />
                      </IconButton>
                      {installation?.status === 'installed' ? (
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleUninstall(installation)}
                        >
                          <DeleteForever />
                        </IconButton>
                      ) : (
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => {
                            setSelectedItem(item);
                            setInstallDialogOpen(true);
                          }}
                        >
                          <GetApp />
                        </IconButton>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
        </TableBody>
      </Table>
      <TablePagination
        rowsPerPageOptions={[12, 24, 48, 96]}
        component="div"
        count={filteredItems.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
        onRowsPerPageChange={(event) => {
          setRowsPerPage(parseInt(event.target.value, 10));
          setPage(0);
        }}
      />
    </TableContainer>
  );

  const renderStatsTab = () => {
    if (!stats) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      );
    }

    const categoryData = {
      labels: Object.keys(stats.popular_categories),
      datasets: [{
        data: Object.values(stats.popular_categories),
        backgroundColor: [
          '#FF6384',
          '#36A2EB',
          '#FFCE56',
          '#4BC0C0',
          '#9966FF',
          '#FF9F40',
        ],
      }],
    };

    const typeData = {
      labels: Object.keys(stats.by_type),
      datasets: [{
        data: Object.values(stats.by_type),
        backgroundColor: Object.keys(stats.by_type).map(type => typeColors[type] || '#ccc'),
      }],
    };

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Marketplace Overview
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.main', color: 'white' }}>
                  <Typography variant="h3">{stats.total_items}</Typography>
                  <Typography variant="body2">Total Items</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.main', color: 'white' }}>
                  <Typography variant="h3">{stats.total_downloads.toLocaleString()}</Typography>
                  <Typography variant="body2">Downloads</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.main', color: 'white' }}>
                  <Typography variant="h3">{stats.total_developers}</Typography>
                  <Typography variant="body2">Developers</Typography>
                </Paper>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Revenue Stats
            </Typography>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Total Revenue
              </Typography>
              <Typography variant="h4" color="success.main">
                ${stats.revenue_stats.total_revenue?.toFixed(2) || '0.00'}
              </Typography>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Monthly Revenue
              </Typography>
              <Typography variant="h5">
                ${stats.revenue_stats.monthly_revenue?.toFixed(2) || '0.00'}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Average Price
              </Typography>
              <Typography variant="h5">
                ${stats.revenue_stats.average_price?.toFixed(2) || '0.00'}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Popular Categories
            </Typography>
            <Box sx={{ height: 300 }}>
              <Doughnut data={categoryData} options={{ maintainAspectRatio: false }} />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Items by Type
            </Typography>
            <Box sx={{ height: 300 }}>
              <Pie data={typeData} options={{ maintainAspectRatio: false }} />
            </Box>
          </Paper>
        </Grid>
      </Grid>
    );
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <StoreIcon color="primary" />
            Marketplace Browser
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Badge badgeContent={installQueue.length} color="warning">
              <IconButton onClick={() => console.log('Show install queue')}>
                <CloudDownload />
              </IconButton>
            </Badge>
            <Badge badgeContent={updateAvailable.length} color="error">
              <IconButton onClick={() => console.log('Show updates')}>
                <Update />
              </IconButton>
            </Badge>
            <IconButton onClick={() => setFiltersDrawerOpen(true)}>
              <FilterList />
            </IconButton>
            <IconButton onClick={loadMarketplaceData}>
              <Refresh />
            </IconButton>
          </Box>
        </Box>

        {/* Quick Search */}
        <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="Search marketplace..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              if (searchTimeout.current) {
                clearTimeout(searchTimeout.current);
              }
              searchTimeout.current = setTimeout(() => {
                filterAndSortItems();
              }, 300);
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 300 }}
          />
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Sort by</InputLabel>
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              label="Sort by"
            >
              <MenuItem value="downloads">Downloads</MenuItem>
              <MenuItem value="rating">Rating</MenuItem>
              <MenuItem value="name">Name</MenuItem>
              <MenuItem value="created_at">Date</MenuItem>
              <MenuItem value="price">Price</MenuItem>
            </Select>
          </FormControl>

          <ToggleButtonGroup
            value={sortOrder}
            exclusive
            onChange={(_, value) => value && setSortOrder(value)}
            size="small"
          >
            <ToggleButton value="desc">↓</ToggleButton>
            <ToggleButton value="asc">↑</ToggleButton>
          </ToggleButtonGroup>

          <Box sx={{ flexGrow: 1 }} />

          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(_, value) => value && setViewMode(value)}
            size="small"
          >
            <ToggleButton value="cards">
              <ViewModule />
            </ToggleButton>
            <ToggleButton value="grid">
              <GridView />
            </ToggleButton>
            <ToggleButton value="list">
              <ViewList />
            </ToggleButton>
            <ToggleButton value="table">
              <TableChart />
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Paper>

      {/* Tabs */}
      <Tabs
        value={selectedTab}
        onChange={(_, newValue) => setSelectedTab(newValue)}
        sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
      >
        <Tab 
          label={`Browse (${filteredItems.length})`} 
          icon={<StoreIcon />} 
          iconPosition="start"
        />
        <Tab 
          label={`Installed (${installations.length})`} 
          icon={<CheckCircle />} 
          iconPosition="start"
        />
        <Tab 
          label={`Favorites (${favorites.length})`} 
          icon={<Favorite />} 
          iconPosition="start"
        />
        <Tab 
          label="Statistics" 
          icon={<Assessment />} 
          iconPosition="start"
        />
      </Tabs>

      {/* Content */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', px: 2 }}>
        {selectedTab === 0 && (
          <>
            {loading ? (
              <Grid container spacing={2}>
                {[...Array(12)].map((_, index) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={index}>
                    <Skeleton variant="rectangular" height={300} />
                  </Grid>
                ))}
              </Grid>
            ) : viewMode === 'table' ? (
              renderTableView()
            ) : (
              <Grid 
                container 
                spacing={2}
                sx={{ 
                  '& .MuiGrid-item': {
                    transition: 'all 0.3s ease',
                  }
                }}
              >
                {filteredItems
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((item) => (
                    <Grid 
                      item 
                      xs={12} 
                      sm={viewMode === 'cards' ? 6 : 12} 
                      md={viewMode === 'cards' ? 4 : viewMode === 'grid' ? 6 : 12} 
                      lg={viewMode === 'cards' ? 3 : viewMode === 'grid' ? 4 : 12}
                      key={item.id}
                    >
                      {renderItemCard(item)}
                    </Grid>
                  ))}
              </Grid>
            )}
          </>
        )}

        {selectedTab === 1 && (
          <Grid container spacing={2}>
            {installations.map((installation) => {
              const item = items.find(i => i.id === installation.item_id);
              return item ? (
                <Grid item xs={12} sm={6} md={4} lg={3} key={installation.id}>
                  {renderItemCard(item)}
                </Grid>
              ) : null;
            })}
          </Grid>
        )}

        {selectedTab === 2 && (
          <Grid container spacing={2}>
            {items
              .filter(item => favorites.includes(item.id))
              .map((item) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={item.id}>
                  {renderItemCard(item)}
                </Grid>
              ))}
          </Grid>
        )}

        {selectedTab === 3 && renderStatsTab()}
      </Box>

      {/* Filters Drawer */}
      <Drawer
        anchor="right"
        open={filtersDrawerOpen}
        onClose={() => setFiltersDrawerOpen(false)}
        sx={{ '& .MuiDrawer-paper': { width: 320, p: 2 } }}
      >
        <Typography variant="h6" gutterBottom>
          Filters
        </Typography>
        
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Category</InputLabel>
          <Select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            label="Category"
          >
            <MenuItem value="">All Categories</MenuItem>
            {stats && Object.keys(stats.popular_categories).map((category) => (
              <MenuItem key={category} value={category}>
                {category} ({stats.popular_categories[category]})
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Type</InputLabel>
          <Select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            label="Type"
          >
            <MenuItem value="">All Types</MenuItem>
            {Object.keys(typeIcons).map((type) => (
              <MenuItem key={type} value={type}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {typeIcons[type]}
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Compatibility</InputLabel>
          <Select
            value={compatibilityFilter}
            onChange={(e) => setCompatibilityFilter(e.target.value)}
            label="Compatibility"
          >
            <MenuItem value="">All Levels</MenuItem>
            <MenuItem value="stable">
              <Chip label="Stable" color="success" size="small" sx={{ mr: 1 }} />
              Stable
            </MenuItem>
            <MenuItem value="beta">
              <Chip label="Beta" color="warning" size="small" sx={{ mr: 1 }} />
              Beta
            </MenuItem>
            <MenuItem value="alpha">
              <Chip label="Alpha" color="info" size="small" sx={{ mr: 1 }} />
              Alpha
            </MenuItem>
            <MenuItem value="experimental">
              <Chip label="Experimental" color="error" size="small" sx={{ mr: 1 }} />
              Experimental
            </MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Price</InputLabel>
          <Select
            value={priceFilter}
            onChange={(e) => setPriceFilter(e.target.value)}
            label="Price"
          >
            <MenuItem value="">All Items</MenuItem>
            <MenuItem value="free">
              <Free sx={{ mr: 1, color: 'success.main' }} />
              Free Only
            </MenuItem>
            <MenuItem value="paid">
              <MonetizationOn sx={{ mr: 1, color: 'warning.main' }} />
              Paid Only
            </MenuItem>
          </Select>
        </FormControl>

        <Button
          fullWidth
          variant="outlined"
          onClick={() => {
            setSelectedCategory('');
            setSelectedType('');
            setCompatibilityFilter('');
            setPriceFilter('');
            setSearchQuery('');
          }}
        >
          Clear All Filters
        </Button>
      </Drawer>

      {/* Speed Dial for Quick Actions */}
      <SpeedDial
        ariaLabel="Quick Actions"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        icon={<SpeedDialIcon />}
        open={speedDialOpen}
        onClose={() => setSpeedDialOpen(false)}
        onOpen={() => setSpeedDialOpen(true)}
      >
        <SpeedDialAction
          icon={<Refresh />}
          tooltipTitle="Refresh"
          onClick={() => {
            setSpeedDialOpen(false);
            loadMarketplaceData();
          }}
        />
        <SpeedDialAction
          icon={<Update />}
          tooltipTitle="Check Updates"
          onClick={() => {
            setSpeedDialOpen(false);
            loadInstallations();
          }}
        />
        <SpeedDialAction
          icon={<Assessment />}
          tooltipTitle="Statistics"
          onClick={() => {
            setSpeedDialOpen(false);
            setSelectedTab(3);
          }}
        />
      </SpeedDial>

      {/* Item Details Dialog */}
      {selectedItem && (
        <Dialog
          open={itemDetailsOpen}
          onClose={() => setItemDetailsOpen(false)}
          maxWidth="lg"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: typeColors[selectedItem.type], width: 56, height: 56 }}>
                {typeIcons[selectedItem.type]}
              </Avatar>
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h4">
                  {selectedItem.name}
                </Typography>
                <Typography variant="subtitle1" color="text.secondary">
                  by {selectedItem.developer_name}
                </Typography>
              </Box>
              {selectedItem.verified && <Verified color="primary" fontSize="large" />}
            </Box>
          </DialogTitle>
          
          <DialogContent>
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Rating value={selectedItem.rating} readOnly precision={0.1} />
                  <Typography variant="body1" sx={{ ml: 1 }}>
                    {selectedItem.rating} ({selectedItem.review_count} reviews)
                  </Typography>
                </Box>
                <Typography variant="body1">
                  <Download sx={{ fontSize: 16, mr: 0.5 }} />
                  {selectedItem.downloads.toLocaleString()} downloads
                </Typography>
                <Typography variant="body1">
                  Version {selectedItem.version}
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
                <Chip
                  label={selectedItem.compatibility}
                  color={compatibilityColors[selectedItem.compatibility]}
                />
                <Chip
                  label={selectedItem.category}
                  variant="outlined"
                />
                <Chip
                  label={selectedItem.license}
                  variant="outlined"
                />
                {selectedItem.price > 0 ? (
                  <Chip
                    icon={<MonetizationOn />}
                    label={`$${selectedItem.price}`}
                    color="secondary"
                  />
                ) : (
                  <Chip
                    icon={<Free />}
                    label="Free"
                    color="success"
                  />
                )}
              </Box>
            </Box>

            <Typography variant="h6" gutterBottom>
              Description
            </Typography>
            <Typography variant="body1" paragraph>
              {selectedItem.description}
            </Typography>

            {selectedItem.screenshots.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Screenshots
                </Typography>
                <ImageList sx={{ width: '100%', height: 200 }} cols={3} rowHeight={150}>
                  {selectedItem.screenshots.map((screenshot, index) => (
                    <ImageListItem key={index}>
                      <img
                        src={screenshot}
                        alt={`Screenshot ${index + 1}`}
                        loading="lazy"
                        style={{ objectFit: 'cover' }}
                      />
                    </ImageListItem>
                  ))}
                </ImageList>
              </Box>
            )}

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                {selectedItem.tags.length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Tags
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selectedItem.tags.map((tag) => (
                        <Chip
                          key={tag}
                          label={tag}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {selectedItem.dependencies.length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Dependencies
                    </Typography>
                    <List dense>
                      {selectedItem.dependencies.map((dep) => (
                        <ListItem key={dep}>
                          <ListItemIcon>
                            <Extension fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary={dep} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </Grid>

              <Grid item xs={12} md={6}>
                {selectedItem.permissions.length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Required Permissions
                    </Typography>
                    <List dense>
                      {selectedItem.permissions.map((permission) => (
                        <ListItem key={permission}>
                          <ListItemIcon>
                            <Security fontSize="small" color="warning" />
                          </ListItemIcon>
                          <ListItemText primary={permission} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {selectedItem.repository_url && (
                    <Button
                      startIcon={<GitHub />}
                      href={selectedItem.repository_url}
                      target="_blank"
                      rel="noopener"
                      variant="outlined"
                    >
                      View Repository
                    </Button>
                  )}
                  {selectedItem.documentation_url && (
                    <Button
                      startIcon={<Description />}
                      href={selectedItem.documentation_url}
                      target="_blank"
                      rel="noopener"
                      variant="outlined"
                    >
                      Documentation
                    </Button>
                  )}
                  {selectedItem.demo_url && (
                    <Button
                      startIcon={<Preview />}
                      href={selectedItem.demo_url}
                      target="_blank"
                      rel="noopener"
                      variant="outlined"
                    >
                      View Demo
                    </Button>
                  )}
                </Box>
              </Grid>
            </Grid>
          </DialogContent>

          <DialogActions>
            <Button onClick={() => setItemDetailsOpen(false)}>
              Close
            </Button>
            <Button
              onClick={() => setReviewsDialogOpen(true)}
              startIcon={<Reviews />}
            >
              Reviews
            </Button>
            <Button
              onClick={() => toggleFavorite(selectedItem.id)}
              startIcon={favorites.includes(selectedItem.id) ? <Favorite /> : <FavoriteBorder />}
              color={favorites.includes(selectedItem.id) ? 'error' : 'default'}
            >
              {favorites.includes(selectedItem.id) ? 'Remove Favorite' : 'Add Favorite'}
            </Button>
            <Button
              variant="contained"
              startIcon={<GetApp />}
              onClick={() => {
                setItemDetailsOpen(false);
                setInstallDialogOpen(true);
              }}
            >
              Install
            </Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Install Dialog */}
      <Dialog
        open={installDialogOpen}
        onClose={() => setInstallDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Install {selectedItem?.name}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            This will install {selectedItem?.name} version {selectedItem?.version}.
          </Typography>
          
          {selectedItem?.permissions && selectedItem.permissions.length > 0 && (
            <Alert severity="warning" sx={{ mt: 2, mb: 2 }}>
              This item requires the following permissions:
              <List dense sx={{ mt: 1 }}>
                {selectedItem.permissions.map((permission) => (
                  <ListItem key={permission} sx={{ py: 0 }}>
                    <ListItemIcon>
                      <Security fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={permission} />
                  </ListItem>
                ))}
              </List>
            </Alert>
          )}

          <FormControlLabel
            control={<Switch defaultChecked />}
            label="Enable automatic updates"
            sx={{ mt: 2 }}
          />

          <FormControlLabel
            control={<Switch defaultChecked />}
            label="Start after installation"
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInstallDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={() => selectedItem && handleInstall(selectedItem)}
            startIcon={<GetApp />}
          >
            Install Now
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MarketplaceBrowser;