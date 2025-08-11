import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Checkbox } from '../ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Progress } from '../ui/progress';
import {
  Shield,
  Download,
  Trash2,
  FileText,
  CheckCircle,
  AlertTriangle,
  Clock,
  Eye,
  RefreshCw,
  Lock,
  Unlock,
  Settings,
  Info,
  ExternalLink,
} from 'lucide-react';

interface ConsentRecord {
  id: string;
  purpose: string;
  consent_status: string;
  consent_version: string;
  given_at?: string;
  withdrawn_at?: string;
}

interface ExportRequest {
  request_id: string;
  status: string;
  requested_at: string;
  export_type: string;
  format_type?: string;
  expires_at: string;
  download_url?: string;
  file_size?: number;
}

interface ProcessingRecord {
  id: string;
  processing_purpose: string;
  lawful_basis: string;
  data_categories: string[];
  recipients: string[];
  retention_period?: number;
  created_at: string;
}

interface PrivacyDashboardData {
  user_id: number;
  data_categories: string[];
  active_consents: number;
  processing_activities: number;
  export_requests: number;
  last_export?: string;
  data_retention_info: Record<string, number>;
  privacy_rights: Record<string, string>;
}

interface GDPRPrivacyDashboardProps {
  className?: string;
}

export const GDPRPrivacyDashboard: React.FC<GDPRPrivacyDashboardProps> = ({ className }) => {
  // State
  const [dashboardData, setDashboardData] = useState<PrivacyDashboardData | null>(null);
  const [consents, setConsents] = useState<ConsentRecord[]>([]);
  const [exports, setExports] = useState<ExportRequest[]>([]);
  const [processingRecords, setProcessingRecords] = useState<ProcessingRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showConsentDialog, setShowConsentDialog] = useState(false);
  const [showDeletionDialog, setShowDeletionDialog] = useState(false);
  const [showRightsDialog, setShowRightsDialog] = useState(false);

  // Form states
  const [exportForm, setExportForm] = useState({
    export_type: 'full_export',
    format_type: 'json'
  });

  const [consentForm, setConsentForm] = useState({
    purpose: '',
    consent_text: '',
    consent_version: '1.0'
  });

  const [deletionConfirm, setDeletionConfirm] = useState({
    confirmation: false,
    reason: '',
    understanding: false
  });

  // Fetch data functions
  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/v1/gdpr/dashboard');
      if (!response.ok) throw new Error('Failed to fetch dashboard data');
      const data = await response.json();
      setDashboardData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchConsents = async () => {
    try {
      const response = await fetch('/api/v1/gdpr/consent/list');
      if (!response.ok) throw new Error('Failed to fetch consents');
      const data = await response.json();
      setConsents(data);
    } catch (err) {
      console.error('Failed to fetch consents:', err);
    }
  };

  const fetchExports = async () => {
    try {
      const response = await fetch('/api/v1/gdpr/export/list');
      if (!response.ok) throw new Error('Failed to fetch exports');
      const data = await response.json();
      setExports(data);
    } catch (err) {
      console.error('Failed to fetch exports:', err);
    }
  };

  const refreshData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchDashboardData(),
        fetchConsents(),
        fetchExports()
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  // Action functions
  const requestDataExport = async () => {
    try {
      const response = await fetch('/api/v1/gdpr/export/request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportForm),
      });

      if (!response.ok) throw new Error('Failed to request export');

      const result = await response.json();
      alert(`Export request created: ${result.request_id}\nStatus: ${result.status}`);
      
      setShowExportDialog(false);
      await fetchExports();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request export');
    }
  };

  const recordConsent = async () => {
    try {
      const response = await fetch('/api/v1/gdpr/consent/record', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(consentForm),
      });

      if (!response.ok) throw new Error('Failed to record consent');

      const result = await response.json();
      alert(`Consent recorded: ${result.consent_id}`);
      
      setShowConsentDialog(false);
      setConsentForm({ purpose: '', consent_text: '', consent_version: '1.0' });
      await fetchConsents();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record consent');
    }
  };

  const withdrawConsent = async (consentId: string) => {
    if (!confirm('Are you sure you want to withdraw this consent?')) return;

    try {
      const response = await fetch(`/api/v1/gdpr/consent/withdraw/${consentId}`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to withdraw consent');

      alert('Consent withdrawn successfully');
      await fetchConsents();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to withdraw consent');
    }
  };

  const requestDataDeletion = async () => {
    if (!deletionConfirm.confirmation || !deletionConfirm.understanding) {
      alert('Please confirm both checkboxes to proceed with data deletion.');
      return;
    }

    try {
      const response = await fetch('/api/v1/gdpr/delete/request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          confirmation: deletionConfirm.confirmation,
          reason: deletionConfirm.reason
        }),
      });

      if (!response.ok) throw new Error('Failed to request data deletion');

      const result = await response.json();
      alert(`Data deletion ${result.status}. This action cannot be undone.`);
      
      if (result.status === 'completed') {
        // Redirect to logout or home page as user data is deleted
        window.location.href = '/';
      }
      
      setShowDeletionDialog(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request deletion');
    }
  };

  const downloadExport = async (exportRequest: ExportRequest) => {
    if (!exportRequest.download_url) return;

    try {
      // The download URL should include the verification token
      const token = 'verification_token_here'; // Would be stored with the export request
      const downloadUrl = `${exportRequest.download_url}?token=${token}`;
      
      // Create download link
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `gdpr_export_${exportRequest.request_id}.${exportRequest.format_type || 'json'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      setError('Failed to download export file');
    }
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'given':
        return 'default';
      case 'processing':
      case 'pending':
        return 'secondary';
      case 'failed':
        return 'destructive';
      case 'withdrawn':
        return 'outline';
      default:
        return 'outline';
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Privacy Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" />
            Loading privacy data...
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              GDPR Privacy Dashboard
            </div>
            <div className="flex gap-2">
              <Button onClick={() => setShowRightsDialog(true)} variant="outline" size="sm">
                <Info className="h-4 w-4 mr-2" />
                Your Rights
              </Button>
              <Button onClick={refreshData} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Manage your personal data and privacy settings in compliance with GDPR
          </CardDescription>
        </CardHeader>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Dashboard Overview */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Data Categories</p>
                  <p className="text-2xl font-bold">{dashboardData.data_categories.length}</p>
                </div>
                <FileText className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Active Consents</p>
                  <p className="text-2xl font-bold">{dashboardData.active_consents}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Processing Activities</p>
                  <p className="text-2xl font-bold">{dashboardData.processing_activities}</p>
                </div>
                <Settings className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Export Requests</p>
                  <p className="text-2xl font-bold">{dashboardData.export_requests}</p>
                </div>
                <Download className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="exports" className="space-y-4">
        <TabsList>
          <TabsTrigger value="exports">Data Exports</TabsTrigger>
          <TabsTrigger value="consents">Consent Management</TabsTrigger>
          <TabsTrigger value="processing">Processing Activities</TabsTrigger>
          <TabsTrigger value="settings">Privacy Settings</TabsTrigger>
        </TabsList>

        {/* Data Exports Tab */}
        <TabsContent value="exports">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Data Export Requests</CardTitle>
                  <CardDescription>
                    Download your personal data (GDPR Article 20 - Right to Data Portability)
                  </CardDescription>
                </div>
                <Button onClick={() => setShowExportDialog(true)}>
                  <Download className="h-4 w-4 mr-2" />
                  Request Export
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {exports.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Request ID</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Requested</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Expires</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {exports.map((exportReq) => (
                      <TableRow key={exportReq.request_id}>
                        <TableCell className="font-mono text-sm">
                          {exportReq.request_id.slice(0, 8)}...
                        </TableCell>
                        <TableCell>{exportReq.export_type}</TableCell>
                        <TableCell>
                          <Badge variant={getStatusColor(exportReq.status)}>
                            {exportReq.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {new Date(exportReq.requested_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          {exportReq.file_size ? formatFileSize(exportReq.file_size) : 'N/A'}
                        </TableCell>
                        <TableCell>
                          {new Date(exportReq.expires_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          {exportReq.status === 'completed' && exportReq.download_url ? (
                            <Button
                              onClick={() => downloadExport(exportReq)}
                              size="sm"
                              variant="outline"
                            >
                              <Download className="h-4 w-4 mr-1" />
                              Download
                            </Button>
                          ) : (
                            <Badge variant="secondary">
                              {exportReq.status === 'processing' ? (
                                <>
                                  <Clock className="h-3 w-3 mr-1" />
                                  Processing
                                </>
                              ) : (
                                exportReq.status
                              )}
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No export requests yet. Request your data export to get started.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Consent Management Tab */}
        <TabsContent value="consents">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Consent Management</CardTitle>
                  <CardDescription>
                    Manage your consent preferences (GDPR Article 7)
                  </CardDescription>
                </div>
                <Button onClick={() => setShowConsentDialog(true)}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Record Consent
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {consents.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Purpose</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Given At</TableHead>
                      <TableHead>Withdrawn At</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {consents.map((consent) => (
                      <TableRow key={consent.id}>
                        <TableCell className="font-medium">{consent.purpose}</TableCell>
                        <TableCell>
                          <Badge variant={getStatusColor(consent.consent_status)}>
                            {consent.consent_status}
                          </Badge>
                        </TableCell>
                        <TableCell>{consent.consent_version}</TableCell>
                        <TableCell>
                          {consent.given_at ? 
                            new Date(consent.given_at).toLocaleString() : 
                            'N/A'
                          }
                        </TableCell>
                        <TableCell>
                          {consent.withdrawn_at ? 
                            new Date(consent.withdrawn_at).toLocaleString() : 
                            'N/A'
                          }
                        </TableCell>
                        <TableCell>
                          {consent.consent_status === 'given' ? (
                            <Button
                              onClick={() => withdrawConsent(consent.id)}
                              size="sm"
                              variant="outline"
                            >
                              <Unlock className="h-4 w-4 mr-1" />
                              Withdraw
                            </Button>
                          ) : (
                            <Badge variant="secondary">Withdrawn</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No consent records found. 
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Processing Activities Tab */}
        <TabsContent value="processing">
          <Card>
            <CardHeader>
              <CardTitle>Data Processing Activities</CardTitle>
              <CardDescription>
                Overview of how your data is processed (GDPR Article 30)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    This shows how your personal data is being processed by our system,
                    including the legal basis and retention periods.
                  </AlertDescription>
                </Alert>
                
                {dashboardData && (
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-semibold mb-2">Data Categories We Process:</h4>
                      <div className="flex flex-wrap gap-2">
                        {dashboardData.data_categories.map((category) => (
                          <Badge key={category} variant="outline">
                            {category.replace('_', ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-2">Retention Periods:</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {Object.entries(dashboardData.data_retention_info).map(([category, days]) => (
                          <div key={category} className="flex justify-between items-center p-2 bg-muted rounded">
                            <span className="capitalize">{category.replace('_', ' ')}</span>
                            <span className="text-sm text-muted-foreground">{days} days</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Privacy Settings Tab */}
        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Privacy Settings</CardTitle>
              <CardDescription>
                Configure your privacy preferences and data handling options
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Danger Zone */}
                <div className="border border-red-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-red-800 mb-2">Danger Zone</h3>
                  <p className="text-sm text-red-600 mb-4">
                    Permanently delete all your data. This action cannot be undone.
                  </p>
                  <Button 
                    onClick={() => setShowDeletionDialog(true)}
                    variant="destructive"
                    size="sm"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete All Data
                  </Button>
                </div>

                {/* Privacy Rights Information */}
                <div className="bg-muted p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">Your Privacy Rights</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                    {dashboardData?.privacy_rights && Object.entries(dashboardData.privacy_rights).map(([right, article]) => (
                      <div key={right} className="flex justify-between">
                        <span className="capitalize">{right.replace('_', ' ')}</span>
                        <span className="text-muted-foreground">{article}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Export Request Dialog */}
      <Dialog open={showExportDialog} onOpenChange={setShowExportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request Data Export</DialogTitle>
            <DialogDescription>
              Export your personal data in compliance with GDPR Article 20
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="export_type">Export Type</Label>
              <Select
                value={exportForm.export_type}
                onChange={(e) => setExportForm({ ...exportForm, export_type: e.target.value })}
              >
                <option value="full_export">Full Export (All Data)</option>
                <option value="transcripts_only">Transcripts Only</option>
                <option value="analytics_only">Analytics Only</option>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="format_type">Format</Label>
              <Select
                value={exportForm.format_type}
                onChange={(e) => setExportForm({ ...exportForm, format_type: e.target.value })}
              >
                <option value="json">JSON</option>
                <option value="csv">CSV (ZIP)</option>
                <option value="xml">XML</option>
              </Select>
            </div>

            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Your export will be available for download for 30 days after completion.
                We'll process your request within 72 hours.
              </AlertDescription>
            </Alert>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowExportDialog(false)}>
              Cancel
            </Button>
            <Button onClick={requestDataExport}>
              Request Export
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Consent Recording Dialog */}
      <Dialog open={showConsentDialog} onOpenChange={setShowConsentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Consent</DialogTitle>
            <DialogDescription>
              Record your consent for specific data processing purposes
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="purpose">Purpose</Label>
              <Input
                id="purpose"
                value={consentForm.purpose}
                onChange={(e) => setConsentForm({ ...consentForm, purpose: e.target.value })}
                placeholder="e.g., Marketing communications"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="consent_text">Consent Text</Label>
              <Textarea
                id="consent_text"
                value={consentForm.consent_text}
                onChange={(e) => setConsentForm({ ...consentForm, consent_text: e.target.value })}
                placeholder="Full consent text that user agrees to..."
                rows={4}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="consent_version">Version</Label>
              <Input
                id="consent_version"
                value={consentForm.consent_version}
                onChange={(e) => setConsentForm({ ...consentForm, consent_version: e.target.value })}
                placeholder="1.0"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConsentDialog(false)}>
              Cancel
            </Button>
            <Button onClick={recordConsent}>
              Record Consent
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Data Deletion Dialog */}
      <Dialog open={showDeletionDialog} onOpenChange={setShowDeletionDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              Delete All Data
            </DialogTitle>
            <DialogDescription>
              This will permanently delete ALL your data. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>WARNING:</strong> This will delete your account, transcripts, settings,
                and all associated data. You will not be able to recover this information.
              </AlertDescription>
            </Alert>

            <div className="space-y-2">
              <Label htmlFor="reason">Reason for deletion (optional)</Label>
              <Textarea
                id="reason"
                value={deletionConfirm.reason}
                onChange={(e) => setDeletionConfirm({ ...deletionConfirm, reason: e.target.value })}
                placeholder="Please tell us why you're deleting your data..."
                rows={3}
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="confirm_deletion"
                  checked={deletionConfirm.confirmation}
                  onCheckedChange={(checked) => setDeletionConfirm({ 
                    ...deletionConfirm, 
                    confirmation: checked as boolean 
                  })}
                />
                <Label htmlFor="confirm_deletion" className="text-sm">
                  I understand that this will permanently delete all my data
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="understand_irreversible"
                  checked={deletionConfirm.understanding}
                  onCheckedChange={(checked) => setDeletionConfirm({ 
                    ...deletionConfirm, 
                    understanding: checked as boolean 
                  })}
                />
                <Label htmlFor="understand_irreversible" className="text-sm">
                  I understand this action cannot be undone
                </Label>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeletionDialog(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={requestDataDeletion}
              disabled={!deletionConfirm.confirmation || !deletionConfirm.understanding}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete All Data
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rights Information Dialog */}
      <Dialog open={showRightsDialog} onOpenChange={setShowRightsDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Your Privacy Rights Under GDPR</DialogTitle>
            <DialogDescription>
              Learn about your rights and how to exercise them
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 max-h-96 overflow-y-auto">
            <div className="space-y-3">
              <div className="p-3 border rounded">
                <h4 className="font-semibold">Right to Access (Article 15)</h4>
                <p className="text-sm text-muted-foreground">
                  You can request information about your personal data we process
                </p>
              </div>

              <div className="p-3 border rounded">
                <h4 className="font-semibold">Right to Rectification (Article 16)</h4>
                <p className="text-sm text-muted-foreground">
                  You can request correction of inaccurate personal data
                </p>
              </div>

              <div className="p-3 border rounded">
                <h4 className="font-semibold">Right to Erasure (Article 17)</h4>
                <p className="text-sm text-muted-foreground">
                  You can request deletion of your personal data ("right to be forgotten")
                </p>
              </div>

              <div className="p-3 border rounded">
                <h4 className="font-semibold">Right to Data Portability (Article 20)</h4>
                <p className="text-sm text-muted-foreground">
                  You can request your data in a structured, machine-readable format
                </p>
              </div>

              <div className="p-3 border rounded">
                <h4 className="font-semibold">Right to Object (Article 21)</h4>
                <p className="text-sm text-muted-foreground">
                  You can object to certain types of data processing
                </p>
              </div>
            </div>

            <div className="mt-4 p-3 bg-muted rounded">
              <h4 className="font-semibold mb-2">Contact Information</h4>
              <div className="text-sm space-y-1">
                <p>Privacy Officer: privacy@example.com</p>
                <p>Data Protection Officer: dpo@example.com</p>
                <p>Phone: +1-555-PRIVACY</p>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRightsDialog(false)}>
              Close
            </Button>
            <Button onClick={() => window.open('https://gdpr.eu/', '_blank')}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Learn More
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GDPRPrivacyDashboard;