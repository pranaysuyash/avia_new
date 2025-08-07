/**
 * Desktop Internationalization Component
 * Enhanced i18n features for Electron app with native integration
 */

import React, { useState, useEffect, useCallback } from 'react';
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
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Chip,
  Paper,
  Tabs,
  Tab,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Language as LanguageIcon,
  Settings as SettingsIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Folder as FolderIcon,
  Sync as SyncIcon,
  Notifications as NotificationsIcon,
  Keyboard as KeyboardIcon,
  Palette as PaletteIcon,
  ExpandMore as ExpandMoreIcon,
  Flag as FlagIcon,
  Translate as TranslateIcon,
  AutoAwesome as AutoAwesomeIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkCheckIcon
} from '@mui/icons-material';

const { ipcRenderer } = window.require('electron');

interface LanguageInfo {
  code: string;
  name: string;
  native_name: string;
  direction: 'ltr' | 'rtl';
  flag: string;
}

interface LocaleSettings {
  language: string;
  region: string;
  timezone: string;
  dateFormat: string;
  timeFormat: string;
  numberFormat: string;
  currencyFormat: string;
  firstDayOfWeek: number;
}

interface TranslationPackage {
  name: string;
  version: string;
  language: string;
  size: string;
  lastUpdated: string;
  installed: boolean;
}

const InternationalizationDesktop: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [languages, setLanguages] = useState<LanguageInfo[]>([]);
  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [localeSettings, setLocaleSettings] = useState<LocaleSettings>({
    language: 'en',
    region: 'US',
    timezone: 'America/New_York',
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12h',
    numberFormat: 'US',
    currencyFormat: 'USD',
    firstDayOfWeek: 0
  });
  
  const [translationPackages, setTranslationPackages] = useState<TranslationPackage[]>([]);
  const [autoTranslationEnabled, setAutoTranslationEnabled] = useState(false);
  const [offlineModeEnabled, setOfflineModeEnabled] = useState(false);
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [downloadDialogOpen, setDownloadDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as any });

  // Initialize desktop-specific features
  useEffect(() => {
    initializeDesktopI18n();
    setupNativeIntegration();
    loadTranslationPackages();
  }, []);

  const initializeDesktopI18n = async () => {
    try {
      // Get system locale information
      const systemLocale = await ipcRenderer.invoke('get-system-locale');
      const userSettings = await ipcRenderer.invoke('get-user-i18n-settings');
      
      if (userSettings) {
        setLocaleSettings(userSettings);
        setCurrentLanguage(userSettings.language);
      } else {
        // Use system defaults
        setCurrentLanguage(systemLocale.language);
        setLocaleSettings({
          ...localeSettings,
          language: systemLocale.language,
          region: systemLocale.region,
          timezone: systemLocale.timezone
        });
      }

      // Load available languages
      const availableLanguages = await ipcRenderer.invoke('get-available-languages');
      setLanguages(availableLanguages);
    } catch (error) {
      console.error('Failed to initialize desktop i18n:', error);
      showSnackbar('Failed to initialize language settings', 'error');
    }
  };

  const setupNativeIntegration = () => {
    // Listen for system language changes
    ipcRenderer.on('system-locale-changed', (event, newLocale) => {
      if (autoTranslationEnabled) {
        setCurrentLanguage(newLocale.language);
        showSnackbar(`Language changed to ${newLocale.language}`, 'info');
      }
    });

    // Listen for translation updates
    ipcRenderer.on('translation-update-available', (event, packageInfo) => {
      showSnackbar(`Translation update available: ${packageInfo.name}`, 'info');
    });

    // Cleanup
    return () => {
      ipcRenderer.removeAllListeners('system-locale-changed');
      ipcRenderer.removeAllListeners('translation-update-available');
    };
  };

  const loadTranslationPackages = async () => {
    try {
      const packages = await ipcRenderer.invoke('get-translation-packages');
      setTranslationPackages(packages);
    } catch (error) {
      console.error('Failed to load translation packages:', error);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleLanguageChange = async (languageCode: string) => {
    try {
      setCurrentLanguage(languageCode);
      
      const newSettings = { ...localeSettings, language: languageCode };
      setLocaleSettings(newSettings);
      
      // Save to native storage
      await ipcRenderer.invoke('save-user-i18n-settings', newSettings);
      
      // Update application language
      await ipcRenderer.invoke('set-app-language', languageCode);
      
      // Show native notification
      await ipcRenderer.invoke('show-notification', {
        title: 'Language Changed',
        body: `Application language changed to ${languageCode.toUpperCase()}`,
        silent: true
      });
      
      showSnackbar('Language updated successfully', 'success');
    } catch (error) {
      console.error('Failed to change language:', error);
      showSnackbar('Failed to change language', 'error');
    }
  };

  const handleDownloadTranslationPack = async (packageName: string) => {
    try {
      setSyncInProgress(true);
      
      // Show progress in native taskbar (Windows/macOS)
      await ipcRenderer.invoke('set-progress-bar', { progress: 0 });
      
      const result = await ipcRenderer.invoke('download-translation-package', packageName);
      
      if (result.success) {
        await loadTranslationPackages();
        showSnackbar('Translation package downloaded successfully', 'success');
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('Download failed:', error);
      showSnackbar('Failed to download translation package', 'error');
    } finally {
      setSyncInProgress(false);
      await ipcRenderer.invoke('set-progress-bar', { progress: -1 }); // Hide progress
    }
  };

  const handleExportTranslations = async () => {
    try {
      const result = await ipcRenderer.invoke('show-save-dialog', {
        title: 'Export Translations',
        defaultPath: `translations_${currentLanguage}_${new Date().toISOString().split('T')[0]}.json`,
        filters: [
          { name: 'JSON Files', extensions: ['json'] },
          { name: 'CSV Files', extensions: ['csv'] }
        ]
      });
      
      if (result.filePath) {
        await ipcRenderer.invoke('export-translations', {
          language: currentLanguage,
          filePath: result.filePath
        });
        
        showSnackbar('Translations exported successfully', 'success');
      }
    } catch (error) {
      console.error('Export failed:', error);
      showSnackbar('Failed to export translations', 'error');
    }
  };

  const handleImportTranslations = async () => {
    try {
      const result = await ipcRenderer.invoke('show-open-dialog', {
        title: 'Import Translations',
        filters: [
          { name: 'JSON Files', extensions: ['json'] },
          { name: 'CSV Files', extensions: ['csv'] }
        ],
        properties: ['openFile']
      });
      
      if (result.filePaths && result.filePaths.length > 0) {
        const importResult = await ipcRenderer.invoke('import-translations', {
          filePath: result.filePaths[0],
          language: currentLanguage
        });
        
        if (importResult.success) {
          showSnackbar(`Imported ${importResult.count} translations`, 'success');
        } else {
          throw new Error(importResult.error);
        }
      }
    } catch (error) {
      console.error('Import failed:', error);
      showSnackbar('Failed to import translations', 'error');
    }
  };

  const handleSyncTranslations = async () => {
    try {
      setSyncInProgress(true);
      
      const result = await ipcRenderer.invoke('sync-translations');
      
      if (result.success) {
        await loadTranslationPackages();
        showSnackbar(`Synced ${result.updated} translations`, 'success');
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('Sync failed:', error);
      showSnackbar('Failed to sync translations', 'error');
    } finally {
      setSyncInProgress(false);
    }
  };

  const renderLanguageSettings = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Language Selection
            </Typography>
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Primary Language</InputLabel>
              <Select
                value={currentLanguage}
                label="Primary Language"
                onChange={(e) => handleLanguageChange(e.target.value)}
              >
                {languages.map(lang => (
                  <MenuItem key={lang.code} value={lang.code}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <span style={{ marginRight: 8 }}>{lang.flag}</span>
                      {lang.native_name} ({lang.name})
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <FormControlLabel
              control={
                <Switch
                  checked={autoTranslationEnabled}
                  onChange={(e) => setAutoTranslationEnabled(e.target.checked)}
                />
              }
              label="Auto-detect system language changes"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={offlineModeEnabled}
                  onChange={(e) => setOfflineModeEnabled(e.target.checked)}
                />
              }
              label="Enable offline translation mode"
            />
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Regional Settings
            </Typography>
            
            <TextField
              fullWidth
              label="Region"
              value={localeSettings.region}
              onChange={(e) => setLocaleSettings({ ...localeSettings, region: e.target.value })}
              sx={{ mb: 2 }}
            />
            
            <TextField
              fullWidth
              label="Timezone"
              value={localeSettings.timezone}
              onChange={(e) => setLocaleSettings({ ...localeSettings, timezone: e.target.value })}
              sx={{ mb: 2 }}
            />
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Date Format</InputLabel>
              <Select
                value={localeSettings.dateFormat}
                label="Date Format"
                onChange={(e) => setLocaleSettings({ ...localeSettings, dateFormat: e.target.value })}
              >
                <MenuItem value="MM/DD/YYYY">MM/DD/YYYY (US)</MenuItem>
                <MenuItem value="DD/MM/YYYY">DD/MM/YYYY (EU)</MenuItem>
                <MenuItem value="YYYY-MM-DD">YYYY-MM-DD (ISO)</MenuItem>
                <MenuItem value="DD.MM.YYYY">DD.MM.YYYY (DE)</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Time Format</InputLabel>
              <Select
                value={localeSettings.timeFormat}
                label="Time Format"
                onChange={(e) => setLocaleSettings({ ...localeSettings, timeFormat: e.target.value })}
              >
                <MenuItem value="12h">12-hour (AM/PM)</MenuItem>
                <MenuItem value="24h">24-hour</MenuItem>
              </Select>
            </FormControl>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Preview
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">Date</Typography>
                <Typography variant="body1">
                  {new Date().toLocaleDateString(currentLanguage)}
                </Typography>
              </Grid>
              
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">Time</Typography>
                <Typography variant="body1">
                  {new Date().toLocaleTimeString(currentLanguage)}
                </Typography>
              </Grid>
              
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">Number</Typography>
                <Typography variant="body1">
                  {(12345.67).toLocaleString(currentLanguage)}
                </Typography>
              </Grid>
              
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">Currency</Typography>
                <Typography variant="body1">
                  {(99.99).toLocaleString(currentLanguage, {
                    style: 'currency',
                    currency: localeSettings.currencyFormat
                  })}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderTranslationPackages = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">
          Translation Packages
        </Typography>
        
        <Box>
          <Button
            variant="outlined"
            startIcon={<SyncIcon />}
            onClick={handleSyncTranslations}
            disabled={syncInProgress}
            sx={{ mr: 1 }}
          >
            {syncInProgress ? 'Syncing...' : 'Sync'}
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => setDownloadDialogOpen(true)}
          >
            Download New
          </Button>
        </Box>
      </Box>
      
      {syncInProgress && <LinearProgress sx={{ mb: 2 }} />}
      
      <Grid container spacing={2}>
        {translationPackages.map((pkg, index) => (
          <Grid item xs={12} md={6} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography variant="subtitle1">
                      {pkg.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Language: {pkg.language.toUpperCase()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Version: {pkg.version}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Size: {pkg.size}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Updated: {pkg.lastUpdated}
                    </Typography>
                  </Box>
                  
                  <Box>
                    {pkg.installed ? (
                      <Chip label="Installed" color="success" size="small" />
                    ) : (
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleDownloadTranslationPack(pkg.name)}
                      >
                        Install
                      </Button>
                    )}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderAdvancedSettings = () => (
    <Box>
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>File Management</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<UploadIcon />}
                onClick={handleImportTranslations}
              >
                Import Translations
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={handleExportTranslations}
              >
                Export Translations
              </Button>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Cache Management</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Alert severity="info" sx={{ mb: 2 }}>
                Translation cache helps improve performance by storing frequently used translations locally.
              </Alert>
            </Grid>
            <Grid item xs={6}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<StorageIcon />}
                onClick={async () => {
                  try {
                    await ipcRenderer.invoke('clear-translation-cache');
                    showSnackbar('Translation cache cleared', 'success');
                  } catch (error) {
                    showSnackbar('Failed to clear cache', 'error');
                  }
                }}
              >
                Clear Cache
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<NetworkCheckIcon />}
                onClick={async () => {
                  try {
                    const stats = await ipcRenderer.invoke('get-cache-stats');
                    showSnackbar(`Cache size: ${stats.size}, Entries: ${stats.count}`, 'info');
                  } catch (error) {
                    showSnackbar('Failed to get cache stats', 'error');
                  }
                }}
              >
                View Cache Stats
              </Button>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Keyboard Shortcuts</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List dense>
            <ListItem>
              <ListItemText
                primary="Ctrl/Cmd + Shift + L"
                secondary="Quick language switch"
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Ctrl/Cmd + Shift + T"
                secondary="Toggle translation mode"
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Ctrl/Cmd + Shift + R"
                secondary="Reload translations"
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>
    </Box>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Internationalization Settings
      </Typography>
      
      <Tabs
        value={activeTab}
        onChange={(_, newValue) => setActiveTab(newValue)}
        sx={{ mb: 3 }}
      >
        <Tab icon={<LanguageIcon />} label="Language & Region" />
        <Tab icon={<DownloadIcon />} label="Translation Packages" />
        <Tab icon={<SettingsIcon />} label="Advanced" />
      </Tabs>
      
      {activeTab === 0 && renderLanguageSettings()}
      {activeTab === 1 && renderTranslationPackages()}
      {activeTab === 2 && renderAdvancedSettings()}
      
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

export default InternationalizationDesktop;