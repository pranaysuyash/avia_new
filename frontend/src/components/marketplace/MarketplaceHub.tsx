import React, { useState, useEffect } from 'react';
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
} from '@mui/icons-material';
import { apiClient } from '../../services/api';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

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
}

interface Category {
  name: string;
  count: number;
  types: string[];
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

const compatibilityColors = {
  stable: 'success',
  beta: 'warning',
  alpha: 'info',
  experimental: 'error',
} as const;

const MarketplaceHub: React.FC = () => {
  const [items, setItems] = useState<MarketplaceItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [compatibilityFilter, setCompatibilityFilter] = useState('');
  const [priceFilter, setPriceFilter] = useState('');
  const [sortBy, setSortBy] = useState('downloads');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedItem, setSelectedItem] = useState<MarketplaceItem | null>(null);
  const [itemDetailsOpen, setItemDetailsOpen] = useState(false);
  const [installDialogOpen, setInstallDialogOpen] = useState(false);
  const [reviewsDialogOpen, setReviewsDialogOpen] = useState(false);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showOnlyInstalled, setShowOnlyInstalled] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  useEffect(() => {
    loadMarketplaceData();
    loadInstallations();
    loadFavorites();
  }, []);

  useEffect(() => {
    loadItems();
  }, [searchQuery, selectedCategory, selectedType, compatibilityFilter, priceFilter, sortBy, sortOrder, page]);

  const loadMarketplaceData = async () => {
    try {
      const [categoriesResponse] = await Promise.all([
        apiClient.get('/api/v1/marketplace/categories/'),
      ]);
      setCategories(categoriesResponse.data);
    } catch (error) {
      console.error('Failed to load marketplace data:', error);
    }
  };

  const loadItems = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (searchQuery) params.append('search', searchQuery);
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedType) params.append('type', selectedType);
      if (compatibilityFilter) params.append('compatibility', compatibilityFilter);
      if (priceFilter === 'free') params.append('free_only', 'true');
      params.append('sort_by', sortBy);
      params.append('sort_order', sortOrder);
      params.append('page', page.toString());
      params.append('limit', '12');

      const response = await apiClient.get(`/api/v1/marketplace/?${params}`);
      setItems(response.data);
      
      // Calculate total pages (mock calculation)
      setTotalPages(Math.ceil(100 / 12)); // Assuming 100 total items
    } catch (error) {
      console.error('Failed to load items:', error);
      setSnackbar({ open: true, message: 'Failed to load marketplace items', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const loadInstallations = async () => {
    try {
      const response = await apiClient.get('/api/v1/marketplace/installations/');
      setInstallations(response.data);
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

  const handleInstall = async (item: MarketplaceItem) => {
    try {
      await apiClient.post(`/api/v1/marketplace/${item.id}/install`, {
        item_id: item.id,
        auto_update: true,
      });
      
      setSnackbar({ open: true, message: `Installing ${item.name}...`, severity: 'success' });
      setInstallDialogOpen(false);
      
      // Refresh installations
      setTimeout(() => {
        loadInstallations();
      }, 1000);
    } catch (error) {
      setSnackbar({ open: true, message: `Failed to install ${item.name}`, severity: 'error' });
    }
  };

  const handleUninstall = async (installation: Installation) => {
    try {
      await apiClient.delete(`/api/v1/marketplace/installations/${installation.id}`);
      
      setSnackbar({ open: true, message: 'Item uninstalled successfully', severity: 'success' });
      loadInstallations();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to uninstall item', severity: 'error' });
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'installed': return 'success';
      case 'installing': case 'updating': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const renderItemCard = (item: MarketplaceItem) => {
    const installation = getInstallationStatus(item.id);
    const isFavorite = favorites.includes(item.id);
    const typeIcon = typeIcons[item.type] || <Extension />;

    return (
      <Grid item xs={12} sm={6} md={4} key={item.id}>
        <Card 
          sx={{ 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column',
            position: 'relative',
            '&:hover': { transform: 'translateY(-2px)', transition: 'transform 0.2s' }
          }}
        >
          {item.verified && (
            <Chip
              icon={<Verified />}
              label="Verified"
              color="primary"
              size="small"
              sx={{ position: 'absolute', top: 8, right: 8, zIndex: 1 }}
            />
          )}
          
          <CardContent sx={{ flexGrow: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                {typeIcon}
              </Avatar>
              <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                <Typography variant="h6" component="div" noWrap>
                  {item.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  by {item.developer_name}
                </Typography>
              </Box>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFavorite(item.id);
                }}
              >
                {isFavorite ? <Favorite color="error" /> : <FavoriteBorder />}
              </IconButton>
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: 40 }}>
              {item.description}
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Rating value={item.rating} readOnly size="small" precision={0.1} />
              <Typography variant="caption" sx={{ ml: 1 }}>
                ({item.review_count})
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Chip
                label={item.compatibility}
                color={compatibilityColors[item.compatibility]}
                size="small"
                sx={{ mr: 1 }}
              />
              <Chip
                label={item.category}
                variant="outlined"
                size="small"
                sx={{ mr: 1 }}
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

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Download sx={{ mr: 1, fontSize: 16 }} />
              <Typography variant="caption">
                {item.downloads.toLocaleString()} downloads
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
              {item.tags.slice(0, 3).map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              ))}
              {item.tags.length > 3 && (
                <Typography variant="caption" color="text.secondary">
                  +{item.tags.length - 3} more
                </Typography>
              )}
            </Box>

            {installation && (
              <Box sx={{ mb: 2 }}>
                <Chip
                  label={installation.status.replace('_', ' ').toUpperCase()}
                  color={getStatusColor(installation.status)}
                  size="small"
                  icon={installation.status === 'installed' ? <CheckCircle /> : <CircularProgress size={16} />}
                />
              </Box>
            )}
          </CardContent>

          <CardActions sx={{ justifyContent: 'space-between', p: 2 }}>
            <Button
              size="small"
              onClick={() => {
                setSelectedItem(item);
                setItemDetailsOpen(true);
              }}
            >
              View Details
            </Button>
            
            {installation?.status === 'installed' ? (
              <Button
                variant="outlined"
                size="small"
                color="error"
                startIcon={<DeleteForever />}
                onClick={() => handleUninstall(installation)}
              >
                Uninstall
              </Button>
            ) : installation?.status === 'installing' ? (
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
      </Grid>
    );
  };

  const renderItemList = (item: MarketplaceItem) => {
    const installation = getInstallationStatus(item.id);
    const isFavorite = favorites.includes(item.id);

    return (
      <Paper key={item.id} sx={{ mb: 2, p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Avatar sx={{ bgcolor: 'primary.main', mr: 2, width: 56, height: 56 }}>
            {typeIcons[item.type]}
          </Avatar>
          
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6" sx={{ mr: 2 }}>
                {item.name}
              </Typography>
              {item.verified && <Verified color="primary" sx={{ mr: 1 }} />}
              <Chip
                label={item.compatibility}
                color={compatibilityColors[item.compatibility]}
                size="small"
                sx={{ mr: 1 }}
              />
              {item.price > 0 ? (
                <Chip
                  label={`$${item.price}`}
                  color="secondary"
                  size="small"
                />
              ) : (
                <Chip
                  label="Free"
                  color="success"
                  size="small"
                />
              )}
            </Box>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {item.description}
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="caption">
                by {item.developer_name}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Rating value={item.rating} readOnly size="small" />
                <Typography variant="caption" sx={{ ml: 0.5 }}>
                  ({item.review_count})
                </Typography>
              </Box>
              <Typography variant="caption">
                {item.downloads.toLocaleString()} downloads
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              onClick={() => toggleFavorite(item.id)}
              color={isFavorite ? 'error' : 'default'}
            >
              {isFavorite ? <Favorite /> : <FavoriteBorder />}
            </IconButton>
            
            <Button
              variant="outlined"
              size="small"
              onClick={() => {
                setSelectedItem(item);
                setItemDetailsOpen(true);
              }}
            >
              Details
            </Button>

            {installation?.status === 'installed' ? (
              <Button
                variant="outlined"
                color="error"
                size="small"
                onClick={() => handleUninstall(installation)}
              >
                Uninstall
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
          </Box>
        </Box>
      </Paper>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <StoreIcon color="primary" />
        Marketplace
      </Typography>

      {/* Tabs */}
      <Tabs 
        value={selectedTab} 
        onChange={(_, newValue) => setSelectedTab(newValue)} 
        sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label="Browse" />
        <Tab label={`Installed (${installations.length})`} />
        <Tab label={`Favorites (${favorites.length})`} />
        <Tab label="Categories" />
      </Tabs>

      {/* Browse Tab */}
      {selectedTab === 0 && (
        <>
          {/* Search and Filters */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Search marketplace"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Search />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    label="Category"
                  >
                    <MenuItem value="">All Categories</MenuItem>
                    {categories.map((category) => (
                      <MenuItem key={category.name} value={category.name}>
                        {category.name} ({category.count})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Type</InputLabel>
                  <Select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    label="Type"
                  >
                    <MenuItem value="">All Types</MenuItem>
                    <MenuItem value="plugin">Plugins</MenuItem>
                    <MenuItem value="extension">Extensions</MenuItem>
                    <MenuItem value="template">Templates</MenuItem>
                    <MenuItem value="integration">Integrations</MenuItem>
                    <MenuItem value="workflow">Workflows</MenuItem>
                    <MenuItem value="theme">Themes</MenuItem>
                    <MenuItem value="model">Models</MenuItem>
                    <MenuItem value="dataset">Datasets</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Compatibility</InputLabel>
                  <Select
                    value={compatibilityFilter}
                    onChange={(e) => setCompatibilityFilter(e.target.value)}
                    label="Compatibility"
                  >
                    <MenuItem value="">All Levels</MenuItem>
                    <MenuItem value="stable">Stable</MenuItem>
                    <MenuItem value="beta">Beta</MenuItem>
                    <MenuItem value="alpha">Alpha</MenuItem>
                    <MenuItem value="experimental">Experimental</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Price</InputLabel>
                  <Select
                    value={priceFilter}
                    onChange={(e) => setPriceFilter(e.target.value)}
                    label="Price"
                  >
                    <MenuItem value="">All Items</MenuItem>
                    <MenuItem value="free">Free Only</MenuItem>
                    <MenuItem value="paid">Paid Only</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <FormControl size="small">
                  <InputLabel>Sort by</InputLabel>
                  <Select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    label="Sort by"
                  >
                    <MenuItem value="downloads">Downloads</MenuItem>
                    <MenuItem value="rating">Rating</MenuItem>
                    <MenuItem value="name">Name</MenuItem>
                    <MenuItem value="created_at">Date Added</MenuItem>
                    <MenuItem value="price">Price</MenuItem>
                  </Select>
                </FormControl>

                <ToggleButtonGroup
                  value={sortOrder}
                  exclusive
                  onChange={(_, value) => value && setSortOrder(value)}
                  size="small"
                >
                  <ToggleButton value="desc">Desc</ToggleButton>
                  <ToggleButton value="asc">Asc</ToggleButton>
                </ToggleButtonGroup>
              </Box>

              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={(_, value) => value && setViewMode(value)}
                size="small"
              >
                <ToggleButton value="grid">Grid</ToggleButton>
                <ToggleButton value="list">List</ToggleButton>
              </ToggleButtonGroup>
            </Box>
          </Paper>

          {/* Items Grid/List */}
          {loading ? (
            <Grid container spacing={3}>
              {[...Array(12)].map((_, index) => (
                <Grid item xs={12} sm={6} md={4} key={index}>
                  <Card>
                    <CardContent>
                      <Skeleton variant="rectangular" width={40} height={40} sx={{ mb: 2 }} />
                      <Skeleton width="80%" height={24} sx={{ mb: 1 }} />
                      <Skeleton width="60%" height={20} sx={{ mb: 2 }} />
                      <Skeleton width="100%" height={60} />
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : viewMode === 'grid' ? (
            <Grid container spacing={3}>
              {items.map(renderItemCard)}
            </Grid>
          ) : (
            <Box>
              {items.map(renderItemList)}
            </Box>
          )}

          {/* Pagination */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(_, newPage) => setPage(newPage)}
              color="primary"
            />
          </Box>
        </>
      )}

      {/* Installed Tab */}
      {selectedTab === 1 && (
        <Box>
          {installations.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Extension sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No items installed
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Browse the marketplace to find and install plugins, extensions, and more
              </Typography>
              <Button
                variant="contained"
                onClick={() => setSelectedTab(0)}
                startIcon={<StoreIcon />}
              >
                Browse Marketplace
              </Button>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {installations.map((installation) => {
                const item = items.find(i => i.id === installation.item_id);
                return item ? renderItemCard(item) : null;
              })}
            </Grid>
          )}
        </Box>
      )}

      {/* Favorites Tab */}
      {selectedTab === 2 && (
        <Box>
          {favorites.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Favorite sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No favorites yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Mark items as favorites to easily find them later
              </Typography>
              <Button
                variant="contained"
                onClick={() => setSelectedTab(0)}
                startIcon={<StoreIcon />}
              >
                Browse Marketplace
              </Button>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {items
                .filter(item => favorites.includes(item.id))
                .map(renderItemCard)}
            </Grid>
          )}
        </Box>
      )}

      {/* Categories Tab */}
      {selectedTab === 3 && (
        <Grid container spacing={3}>
          {categories.map((category) => (
            <Grid item xs={12} sm={6} md={4} key={category.name}>
              <Card sx={{ cursor: 'pointer' }} onClick={() => {
                setSelectedCategory(category.name);
                setSelectedTab(0);
              }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Category sx={{ mr: 2, fontSize: 40, color: 'primary.main' }} />
                    <Box>
                      <Typography variant="h6">
                        {category.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {category.count} items
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {category.types.map((type) => (
                      <Chip
                        key={type}
                        label={type}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Item Details Dialog */}
      <Dialog
        open={itemDetailsOpen}
        onClose={() => setItemDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedItem && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  {typeIcons[selectedItem.type]}
                </Avatar>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h5">
                    {selectedItem.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    by {selectedItem.developer_name}
                  </Typography>
                </Box>
                {selectedItem.verified && <Verified color="primary" />}
              </Box>
            </DialogTitle>
            
            <DialogContent>
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Rating value={selectedItem.rating} readOnly precision={0.1} />
                  <Typography variant="body2">
                    {selectedItem.rating} ({selectedItem.review_count} reviews)
                  </Typography>
                  <Divider orientation="vertical" flexItem />
                  <Typography variant="body2">
                    {selectedItem.downloads.toLocaleString()} downloads
                  </Typography>
                  <Divider orientation="vertical" flexItem />
                  <Typography variant="body2">
                    Version {selectedItem.version}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <Chip
                    label={selectedItem.compatibility}
                    color={compatibilityColors[selectedItem.compatibility]}
                    size="small"
                  />
                  <Chip
                    label={selectedItem.category}
                    variant="outlined"
                    size="small"
                  />
                  <Chip
                    label={selectedItem.license}
                    variant="outlined"
                    size="small"
                  />
                  {selectedItem.price > 0 ? (
                    <Chip
                      label={`$${selectedItem.price}`}
                      color="secondary"
                      size="small"
                    />
                  ) : (
                    <Chip
                      label="Free"
                      color="success"
                      size="small"
                    />
                  )}
                </Box>
              </Box>

              <Typography variant="body1" paragraph>
                {selectedItem.description}
              </Typography>

              {selectedItem.tags.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
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

              {selectedItem.permissions.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Required Permissions
                  </Typography>
                  <List dense>
                    {selectedItem.permissions.map((permission) => (
                      <ListItem key={permission}>
                        <ListItemIcon>
                          <Security fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={permission} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {selectedItem.dependencies.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Dependencies
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selectedItem.dependencies.map((dep) => (
                      <Chip
                        key={dep}
                        label={dep}
                        size="small"
                        color="info"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Box>
              )}

              <Box sx={{ display: 'flex', gap: 2 }}>
                {selectedItem.repository_url && (
                  <Button
                    startIcon={<GitHub />}
                    href={selectedItem.repository_url}
                    target="_blank"
                    rel="noopener"
                  >
                    Repository
                  </Button>
                )}
                {selectedItem.documentation_url && (
                  <Button
                    startIcon={<Description />}
                    href={selectedItem.documentation_url}
                    target="_blank"
                    rel="noopener"
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
                  >
                    Demo
                  </Button>
                )}
              </Box>
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
          </>
        )}
      </Dialog>

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
            <Alert severity="info" sx={{ mt: 2 }}>
              This item requires the following permissions:
              <List dense sx={{ mt: 1 }}>
                {selectedItem.permissions.map((permission) => (
                  <ListItem key={permission} sx={{ py: 0 }}>
                    <ListItemText primary={`• ${permission}`} />
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
            Install
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MarketplaceHub;