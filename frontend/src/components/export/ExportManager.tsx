import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  TextField,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
} from '@mui/material';
import {
  Download,
  Share,
  PictureAsPdf,
  Description,
  TableChart,
  Code,
  Language,
  Settings,
  Preview,
  CloudUpload,
  Link,
  Email,
  ExpandMore,
  Palette,
  Storefront,
} from '@mui/icons-material';

interface ExportConfig {
  format: string;
  includeMetadata: boolean;
  includeTimestamps: boolean;
  includeSpeakerInfo: boolean;
  includeEntities: boolean;
  includeInsights: boolean;
  includeVisualizations: boolean;
  customTemplate?: string;
  branding: {
    companyName?: string;
    logo?: string;
    colors?: {
      primary: string;
      secondary: string;
    };
  };
}

interface ShareConfig {
  platform: string;
  accessLevel: 'public' | 'private' | 'password';
  password?: string;
  expiresIn?: number;
  allowDownload: boolean;
  allowComments: boolean;
}

interface ExportManagerProps {
  transcriptData?: any;
  analysisResults?: any;
  onExportComplete?: (exportUrl: string) => void;
  onShareComplete?: (shareUrl: string) => void;
}

const EXPORT_FORMATS = [
  { value: 'pdf', label: 'PDF Document', icon: <PictureAsPdf />, description: 'Professional document format' },
  { value: 'docx', label: 'Word Document', icon: <Description />, description: 'Editable Microsoft Word format' },
  { value: 'json', label: 'JSON Data', icon: <Code />, description: 'Structured data format' },
  { value: 'csv', label: 'CSV Spreadsheet', icon: <TableChart />, description: 'Comma-separated values' },
  { value: 'txt', label: 'Plain Text', icon: <Description />, description: 'Simple text format' },
  { value: 'html', label: 'Web Page', icon: <Language />, description: 'Interactive HTML format' },
  { value: 'srt', label: 'Subtitles (SRT)', icon: <Language />, description: 'Video subtitle format' },
  { value: 'vtt', label: 'WebVTT', icon: <Language />, description: 'Web video text tracks' },
];

const SHARE_PLATFORMS = [
  { value: 'link', label: 'Share Link', icon: <Link />, description: 'Generate shareable link' },
  { value: 'email', label: 'Email', icon: <Email />, description: 'Send via email' },
  { value: 'cloud', label: 'Cloud Storage', icon: <CloudUpload />, description: 'Upload to cloud' },
];

const ExportManager: React.FC<ExportManagerProps> = ({
  transcriptData,
  analysisResults,
  onExportComplete,
  onShareComplete,
}) => {
  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    format: 'pdf',
    includeMetadata: true,
    includeTimestamps: true,
    includeSpeakerInfo: true,
    includeEntities: true,
    includeInsights: true,
    includeVisualizations: false,
    branding: {
      companyName: '',
      colors: {
        primary: '#3f51b5',
        secondary: '#f50057',
      },
    },
  });

  const [shareConfig, setShareConfig] = useState<ShareConfig>({
    platform: 'link',
    accessLevel: 'private',
    expiresIn: 7,
    allowDownload: true,
    allowComments: false,
  });

  const [isExporting, setIsExporting] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState<string>('');
  const [brandingDialogOpen, setBrandingDialogOpen] = useState(false);

  const handleExport = async () => {
    if (!transcriptData) {
      setError('No transcript data available for export');
      return;
    }

    setIsExporting(true);
    setError(null);

    try {
      const response = await fetch('/api/export/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript_data: transcriptData,
          analysis_results: analysisResults,
          config: exportConfig,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate export');
      }

      const result = await response.json();
      
      if (exportConfig.format === 'html') {
        // For HTML exports, open in new tab
        window.open(result.url, '_blank');
      } else {
        // For file downloads, trigger download
        const link = document.createElement('a');
        link.href = result.url;
        link.download = result.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }

      onExportComplete?.(result.url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  const handleShare = async () => {
    if (!transcriptData) {
      setError('No transcript data available for sharing');
      return;
    }

    setIsSharing(true);
    setError(null);

    try {
      const response = await fetch('/api/export/share', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript_data: transcriptData,
          analysis_results: analysisResults,
          export_config: exportConfig,
          share_config: shareConfig,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create share link');
      }

      const result = await response.json();
      
      if (shareConfig.platform === 'email') {
        // Open email client
        const subject = encodeURIComponent('Shared Transcript Analysis');
        const body = encodeURIComponent(`View the shared transcript analysis: ${result.shareUrl}`);
        window.open(`mailto:?subject=${subject}&body=${body}`);
      } else {
        // Copy to clipboard
        navigator.clipboard.writeText(result.shareUrl);
      }

      onShareComplete?.(result.shareUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sharing failed');
    } finally {
      setIsSharing(false);
    }
  };

  const handlePreview = async () => {
    if (!transcriptData) return;

    try {
      const response = await fetch('/api/export/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript_data: transcriptData,
          analysis_results: analysisResults,
          config: exportConfig,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate preview');
      }

      const result = await response.json();
      setPreviewContent(result.preview);
      setPreviewDialogOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Preview failed');
    }
  };

  const getFormatInfo = (format: string) => {
    return EXPORT_FORMATS.find(f => f.value === format);
  };

  const getPlatformInfo = (platform: string) => {
    return SHARE_PLATFORMS.find(p => p.value === platform);
  };

  const getEstimatedSize = () => {
    if (!transcriptData) return 'Unknown';
    
    const baseSize = JSON.stringify(transcriptData).length;
    let multiplier = 1;
    
    switch (exportConfig.format) {
      case 'pdf': multiplier = 3; break;
      case 'docx': multiplier = 2.5; break;
      case 'html': multiplier = 2; break;
      case 'json': multiplier = 1; break;
      case 'csv': multiplier = 0.5; break;
      case 'txt': multiplier = 0.3; break;
      default: multiplier = 1;
    }
    
    if (exportConfig.includeVisualizations) multiplier *= 2;
    if (exportConfig.includeInsights) multiplier *= 1.5;
    
    const estimatedBytes = baseSize * multiplier;
    
    if (estimatedBytes < 1024) return `${estimatedBytes.toFixed(0)} B`;
    if (estimatedBytes < 1024 * 1024) return `${(estimatedBytes / 1024).toFixed(1)} KB`;
    return `${(estimatedBytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Box>
      {/* Header */}
      <Typography variant="h5" gutterBottom display="flex" alignItems="center">
        <Download sx={{ mr: 1 }} />
        Export & Share
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Export Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom display="flex" alignItems="center">
                <Download sx={{ mr: 1 }} />
                Export Configuration
              </Typography>

              {/* Format Selection */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Export Format</InputLabel>
                <Select
                  value={exportConfig.format}
                  onChange={(e) => setExportConfig({ ...exportConfig, format: e.target.value })}
                >
                  {EXPORT_FORMATS.map((format) => (
                    <MenuItem key={format.value} value={format.value}>
                      <Box display="flex" alignItems="center">
                        {format.icon}
                        <Box sx={{ ml: 1 }}>
                          <Typography variant="body1">{format.label}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {format.description}
                          </Typography>
                        </Box>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Content Options */}
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                Include Content
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={exportConfig.includeMetadata}
                    onChange={(e) => setExportConfig({ ...exportConfig, includeMetadata: e.target.checked })}
                  />
                }
                label="Metadata & Statistics"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={exportConfig.includeTimestamps}
                    onChange={(e) => setExportConfig({ ...exportConfig, includeTimestamps: e.target.checked })}
                  />
                }
                label="Timestamps"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={exportConfig.includeSpeakerInfo}
                    onChange={(e) => setExportConfig({ ...exportConfig, includeSpeakerInfo: e.target.checked })}
                  />
                }
                label="Speaker Information"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={exportConfig.includeEntities}
                    onChange={(e) => setExportConfig({ ...exportConfig, includeEntities: e.target.checked })}
                  />
                }
                label="Extracted Entities"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={exportConfig.includeInsights}
                    onChange={(e) => setExportConfig({ ...exportConfig, includeInsights: e.target.checked })}
                  />
                }
                label="AI Insights"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={exportConfig.includeVisualizations}
                    onChange={(e) => setExportConfig({ ...exportConfig, includeVisualizations: e.target.checked })}
                  />
                }
                label="Charts & Visualizations"
              />

              {/* Branding */}
              <Box sx={{ mt: 2 }}>
                <Button
                  startIcon={<Palette />}
                  onClick={() => setBrandingDialogOpen(true)}
                  variant="outlined"
                  size="small"
                >
                  Customize Branding
                </Button>
              </Box>

              {/* Export Info */}
              <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Export Summary
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Format: {getFormatInfo(exportConfig.format)?.label}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Estimated Size: {getEstimatedSize()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Content Sections: {[
                    exportConfig.includeMetadata && 'Metadata',
                    exportConfig.includeTimestamps && 'Timestamps',
                    exportConfig.includeSpeakerInfo && 'Speakers',
                    exportConfig.includeEntities && 'Entities',
                    exportConfig.includeInsights && 'Insights',
                    exportConfig.includeVisualizations && 'Charts',
                  ].filter(Boolean).length}
                </Typography>
              </Box>

              {/* Export Actions */}
              <Box sx={{ mt: 3, display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  onClick={handleExport}
                  disabled={isExporting || !transcriptData}
                  startIcon={<Download />}
                >
                  {isExporting ? 'Exporting...' : 'Export'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={handlePreview}
                  disabled={!transcriptData}
                  startIcon={<Preview />}
                >
                  Preview
                </Button>
              </Box>

              {isExporting && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Generating {getFormatInfo(exportConfig.format)?.label}...
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Share Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom display="flex" alignItems="center">
                <Share sx={{ mr: 1 }} />
                Share Configuration
              </Typography>

              {/* Platform Selection */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Share Platform</InputLabel>
                <Select
                  value={shareConfig.platform}
                  onChange={(e) => setShareConfig({ ...shareConfig, platform: e.target.value })}
                >
                  {SHARE_PLATFORMS.map((platform) => (
                    <MenuItem key={platform.value} value={platform.value}>
                      <Box display="flex" alignItems="center">
                        {platform.icon}
                        <Box sx={{ ml: 1 }}>
                          <Typography variant="body1">{platform.label}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {platform.description}
                          </Typography>
                        </Box>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Access Control */}
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                Access Control
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Access Level</InputLabel>
                <Select
                  value={shareConfig.accessLevel}
                  onChange={(e) => setShareConfig({ ...shareConfig, accessLevel: e.target.value as any })}
                >
                  <MenuItem value="public">Public - Anyone with link</MenuItem>
                  <MenuItem value="private">Private - Invite only</MenuItem>
                  <MenuItem value="password">Password Protected</MenuItem>
                </Select>
              </FormControl>

              {shareConfig.accessLevel === 'password' && (
                <TextField
                  fullWidth
                  label="Password"
                  type="password"
                  value={shareConfig.password || ''}
                  onChange={(e) => setShareConfig({ ...shareConfig, password: e.target.value })}
                  sx={{ mb: 2 }}
                />
              )}

              <TextField
                fullWidth
                label="Expires In (days)"
                type="number"
                value={shareConfig.expiresIn}
                onChange={(e) => setShareConfig({ ...shareConfig, expiresIn: parseInt(e.target.value) })}
                sx={{ mb: 2 }}
                inputProps={{ min: 1, max: 365 }}
              />

              {/* Permissions */}
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                Permissions
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={shareConfig.allowDownload}
                    onChange={(e) => setShareConfig({ ...shareConfig, allowDownload: e.target.checked })}
                  />
                }
                label="Allow Download"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={shareConfig.allowComments}
                    onChange={(e) => setShareConfig({ ...shareConfig, allowComments: e.target.checked })}
                  />
                }
                label="Allow Comments"
              />

              {/* Share Info */}
              <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Share Summary
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Platform: {getPlatformInfo(shareConfig.platform)?.label}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Access: {shareConfig.accessLevel.charAt(0).toUpperCase() + shareConfig.accessLevel.slice(1)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Expires: {shareConfig.expiresIn} days
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Permissions: {[
                    shareConfig.allowDownload && 'Download',
                    shareConfig.allowComments && 'Comments',
                  ].filter(Boolean).join(', ') || 'View only'}
                </Typography>
              </Box>

              {/* Share Actions */}
              <Box sx={{ mt: 3 }}>
                <Button
                  variant="contained"
                  onClick={handleShare}
                  disabled={isSharing || !transcriptData}
                  startIcon={<Share />}
                  fullWidth
                >
                  {isSharing ? 'Creating Share Link...' : 'Create Share Link'}
                </Button>
              </Box>

              {isSharing && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Creating shareable link...
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Exports */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Exports & Shares
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Your recent export and share history will appear here.
          </Typography>
        </CardContent>
      </Card>

      {/* Preview Dialog */}
      <Dialog open={previewDialogOpen} onClose={() => setPreviewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Export Preview</DialogTitle>
        <DialogContent>
          <Box
            sx={{
              border: '1px solid #e0e0e0',
              borderRadius: 1,
              p: 2,
              bgcolor: 'grey.50',
              maxHeight: 400,
              overflow: 'auto',
            }}
          >
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
              {previewContent}
            </pre>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>Close</Button>
          <Button onClick={handleExport} variant="contained">
            Export This
          </Button>
        </DialogActions>
      </Dialog>

      {/* Branding Dialog */}
      <Dialog open={brandingDialogOpen} onClose={() => setBrandingDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Customize Branding</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Company Name"
            value={exportConfig.branding.companyName || ''}
            onChange={(e) => setExportConfig({
              ...exportConfig,
              branding: { ...exportConfig.branding, companyName: e.target.value }
            })}
            sx={{ mb: 2, mt: 1 }}
          />
          
          <Typography variant="subtitle2" gutterBottom>
            Brand Colors
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Primary Color"
                type="color"
                value={exportConfig.branding.colors?.primary || '#3f51b5'}
                onChange={(e) => setExportConfig({
                  ...exportConfig,
                  branding: {
                    ...exportConfig.branding,
                    colors: { 
                      primary: e.target.value,
                      secondary: exportConfig.branding.colors?.secondary || '#f50057'
                    }
                  }
                })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Secondary Color"
                type="color"
                value={exportConfig.branding.colors?.secondary || '#f50057'}
                onChange={(e) => setExportConfig({
                  ...exportConfig,
                  branding: {
                    ...exportConfig.branding,
                    colors: { 
                      primary: exportConfig.branding.colors?.primary || '#3f51b5',
                      secondary: e.target.value
                    }
                  }
                })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBrandingDialogOpen(false)}>Cancel</Button>
          <Button onClick={() => setBrandingDialogOpen(false)} variant="contained">
            Apply
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExportManager;