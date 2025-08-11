/**
 * Translation Manager Component
 * Admin interface for managing translations
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Chip,
  LinearProgress,
  Tabs,
  Tab,
  Alert,
  Snackbar,
  Tooltip,
  Fab,
  Menu,
  ListItemIcon,
  ListItemText,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Translate as TranslateIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  AutoAwesome as AutoAwesomeIcon,
  Language as LanguageIcon,
  Flag as FlagIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  ErrorOutline as ErrorIcon
} from '@mui/icons-material';
import { useI18n } from './InternationalizationProvider';
import apiService from '../../services/api';

interface Translation {
  key: string;
  value: string;
  namespace: string;
  language_code: string;
  is_approved?: boolean;
  created_at?: string;
  updated_at?: string;
}

interface TranslationStats {
  total_keys: number;
  languages: number;
  namespaces: number;
  completion_rate: Record<string, number>;
  recent_updates: Array<{
    key: string;
    language: string;
    updated_at: string;
    updated_by: string;
  }>;
}

interface MissingTranslation {
  key: string;
  namespace: string;
  english_value: string;
  priority: 'high' | 'medium' | 'low';
}

const TranslationManager: React.FC = () => {
  const { currentLanguage, languages, t } = useI18n();
  const [activeTab, setActiveTab] = useState(0);
  const [translations, setTranslations] = useState<Translation[]>([]);
  const [stats, setStats] = useState<TranslationStats | null>(null);
  const [missingTranslations, setMissingTranslations] = useState<MissingTranslation[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState(currentLanguage);
  const [selectedNamespace, setSelectedNamespace] = useState('general');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [editDialog, setEditDialog] = useState<{
    open: boolean;
    translation?: Translation;
    isNew?: boolean;
  }>({ open: false });
  const [bulkDialog, setBulkDialog] = useState(false);
  const [importDialog, setImportDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as any });
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  const namespaces = [
    'general', 'navigation', 'forms', 'errors', 'dashboard', 'transcription'
  ];

  useEffect(() => {
    loadData();
  }, [selectedLanguage, selectedNamespace]);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadStats(),
        loadMissingTranslations()
      ]);
    } catch (error) {
      console.error('Failed to load translation data:', error);
      showSnackbar('Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiService.get('/api/v1/i18n/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadMissingTranslations = async () => {
    try {
      const response = await apiService.get('/api/v1/i18n/missing', {
        params: {
          language_code: selectedLanguage,
          namespace: selectedNamespace
        }
      });
      setMissingTranslations(response.data.missing_translations);
    } catch (error) {
      console.error('Failed to load missing translations:', error);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleSaveTranslation = async (translation: Translation) => {
    try {
      await apiService.post('/api/v1/i18n/translate/set', translation);
      showSnackbar('Translation saved successfully', 'success');
      setEditDialog({ open: false });
      await loadData();
    } catch (error) {
      console.error('Failed to save translation:', error);
      showSnackbar('Failed to save translation', 'error');
    }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const response = await apiService.get(`/api/v1/i18n/export/${selectedLanguage}`, {
        params: { format, namespace: selectedNamespace },
        responseType: 'blob'
      });

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `translations_${selectedLanguage}_${selectedNamespace}.${format}`;
      link.click();
      window.URL.revokeObjectURL(url);

      showSnackbar('Export completed', 'success');
    } catch (error) {
      console.error('Export failed:', error);
      showSnackbar('Export failed', 'error');
    }
  };

  const handleImport = async (file: File, format: 'json' | 'csv') => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      await apiService.post(`/api/v1/i18n/import/${selectedLanguage}?format=${format}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      showSnackbar('Import completed successfully', 'success');
      setImportDialog(false);
      await loadData();
    } catch (error) {
      console.error('Import failed:', error);
      showSnackbar('Import failed', 'error');
    }
  };

  const handleBulkTranslate = async (texts: Record<string, string>, targetLanguage: string) => {
    try {
      const response = await apiService.post('/api/v1/i18n/translate/ai', {
        texts,
        target_language: targetLanguage,
        source_language: 'en'
      });

      // Save translated texts
      for (const [key, value] of Object.entries(response.data.translations)) {
        await apiService.post('/api/v1/i18n/translate/set', {
          key,
          language_code: targetLanguage,
          value,
          namespace: selectedNamespace
        });
      }

      showSnackbar('Bulk translation completed', 'success');
      setBulkDialog(false);
      await loadData();
    } catch (error) {
      console.error('Bulk translation failed:', error);
      showSnackbar('Bulk translation failed', 'error');
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high': return <ErrorIcon fontSize="small" />;
      case 'medium': return <WarningIcon fontSize="small" />;
      case 'low': return <CheckCircleIcon fontSize="small" />;
      default: return undefined;
    }
  };

  const renderStatsTab = () => (
    <Grid container spacing={3}>
      {/* Overview Cards */}
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Keys
            </Typography>
            <Typography variant="h4">
              {stats?.total_keys || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Languages
            </Typography>
            <Typography variant="h4">
              {stats?.languages || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Namespaces
            </Typography>
            <Typography variant="h4">
              {stats?.namespaces || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Completion Rate
            </Typography>
            <Typography variant="h4">
              {Math.round(Object.values(stats?.completion_rate || {}).reduce((a, b) => a + b, 0) / Object.keys(stats?.completion_rate || {}).length) || 0}%
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Completion Progress */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Translation Progress by Language
            </Typography>
            {Object.entries(stats?.completion_rate || {}).map(([lang, completion]) => {
              const langInfo = languages.find(l => l.code === lang);
              return (
                <Box key={lang} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Typography sx={{ minWidth: 120 }}>
                      {langInfo?.flag} {langInfo?.name || lang}
                    </Typography>
                    <Typography sx={{ ml: 2, color: 'text.secondary' }}>
                      {completion}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={completion}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              );
            })}
          </CardContent>
        </Card>
      </Grid>

      {/* Recent Updates */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Updates
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Key</TableCell>
                    <TableCell>Language</TableCell>
                    <TableCell>Updated At</TableCell>
                    <TableCell>Updated By</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(stats?.recent_updates || []).map((update, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <code>{update.key}</code>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={update.language.toUpperCase()}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(update.updated_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{update.updated_by}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderMissingTab = () => (
    <Box>
      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Language</InputLabel>
                <Select
                  value={selectedLanguage}
                  label="Language"
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                >
                  {languages.map(lang => (
                    <MenuItem key={lang.code} value={lang.code}>
                      {lang.flag} {lang.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Namespace</InputLabel>
                <Select
                  value={selectedNamespace}
                  label="Namespace"
                  onChange={(e) => setSelectedNamespace(e.target.value)}
                >
                  {namespaces.map(ns => (
                    <MenuItem key={ns} value={ns}>{ns}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Button
                variant="contained"
                startIcon={<AutoAwesomeIcon />}
                onClick={() => setBulkDialog(true)}
                disabled={missingTranslations.length === 0}
                fullWidth
              >
                Auto-Translate Missing
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Missing Translations Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Missing Translations ({missingTranslations.length})
          </Typography>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Priority</TableCell>
                  <TableCell>Key</TableCell>
                  <TableCell>Namespace</TableCell>
                  <TableCell>English Value</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {missingTranslations.map((missing, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Chip
                        icon={getPriorityIcon(missing.priority)}
                        label={missing.priority}
                        color={getPriorityColor(missing.priority) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <code>{missing.key}</code>
                    </TableCell>
                    <TableCell>
                      <Chip label={missing.namespace} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>{missing.english_value}</TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => setEditDialog({
                          open: true,
                          translation: {
                            key: missing.key,
                            value: '',
                            namespace: missing.namespace,
                            language_code: selectedLanguage
                          },
                          isNew: true
                        })}
                      >
                        <AddIcon />
                      </IconButton>
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

  const renderEditDialog = () => (
    <Dialog
      open={editDialog.open}
      onClose={() => setEditDialog({ open: false })}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        {editDialog.isNew ? 'Add Translation' : 'Edit Translation'}
      </DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Key"
              value={editDialog.translation?.key || ''}
              onChange={(e) => setEditDialog({
                ...editDialog,
                translation: { ...editDialog.translation!, key: e.target.value }
              })}
              disabled={!editDialog.isNew}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Language</InputLabel>
              <Select
                value={editDialog.translation?.language_code || ''}
                label="Language"
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  translation: { ...editDialog.translation!, language_code: e.target.value }
                })}
              >
                {languages.map(lang => (
                  <MenuItem key={lang.code} value={lang.code}>
                    {lang.flag} {lang.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Namespace</InputLabel>
              <Select
                value={editDialog.translation?.namespace || ''}
                label="Namespace"
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  translation: { ...editDialog.translation!, namespace: e.target.value }
                })}
              >
                {namespaces.map(ns => (
                  <MenuItem key={ns} value={ns}>{ns}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Translation Value"
              value={editDialog.translation?.value || ''}
              onChange={(e) => setEditDialog({
                ...editDialog,
                translation: { ...editDialog.translation!, value: e.target.value }
              })}
              helperText="Use {variable} or {{variable}} for variable substitution"
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setEditDialog({ open: false })}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={() => handleSaveTranslation(editDialog.translation!)}
          disabled={!editDialog.translation?.key || !editDialog.translation?.value}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Translation Manager
        </Typography>
        
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadData}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={() => setImportDialog(true)}
            sx={{ mr: 1 }}
          >
            Import
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={(e) => setMenuAnchor(e.currentTarget)}
          >
            Export
          </Button>
        </Box>
      </Box>

      {/* Loading */}
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onChange={(_, newValue) => setActiveTab(newValue)}
        sx={{ mb: 3 }}
      >
        <Tab label="Statistics" />
        <Tab label="Missing Translations" />
      </Tabs>

      {/* Tab Content */}
      {activeTab === 0 && renderStatsTab()}
      {activeTab === 1 && renderMissingTab()}

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add translation"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => setEditDialog({
          open: true,
          translation: {
            key: '',
            value: '',
            namespace: 'general',
            language_code: currentLanguage
          },
          isNew: true
        })}
      >
        <AddIcon />
      </Fab>

      {/* Dialogs */}
      {renderEditDialog()}

      {/* Export Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem onClick={() => { handleExport('json'); setMenuAnchor(null); }}>
          <ListItemIcon><DownloadIcon /></ListItemIcon>
          <ListItemText>Export JSON</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { handleExport('csv'); setMenuAnchor(null); }}>
          <ListItemIcon><DownloadIcon /></ListItemIcon>
          <ListItemText>Export CSV</ListItemText>
        </MenuItem>
      </Menu>

      {/* Snackbar */}
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

export default TranslationManager;