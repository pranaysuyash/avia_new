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
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../ui/dialog';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
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
import {
  Shield,
  Download,
  Upload,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  HardDrive,
  Settings,
  Trash2,
  Play,
  Pause,
  Eye,
} from 'lucide-react';

interface BackupInfo {
  backup_id: string;
  status: string;
  size?: number;
  components: string[];
  location?: string;
  s3_location?: string;
  created_at: string;
  duration?: number;
  error?: string;
}

interface BackupStatus {
  scheduler_running: boolean;
  next_daily?: string;
  recent_backups: number;
  last_backup?: any;
  success_rate: number;
  configuration: {
    daily_hour: number;
    weekly_day: string;
    monthly_day: number;
    notify_on_success: boolean;
    notify_on_failure: boolean;
  };
}

interface BackupManagerProps {
  className?: string;
}

export const BackupManager: React.FC<BackupManagerProps> = ({ className }) => {
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [status, setStatus] = useState<BackupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [selectedBackupType, setSelectedBackupType] = useState<string>('manual');
  const [includeFiles, setIncludeFiles] = useState(true);
  const [compress, setCompress] = useState(true);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState<BackupInfo | null>(null);
  const [restoreConfirm, setRestoreConfirm] = useState(false);

  const fetchBackups = async () => {
    try {
      const response = await fetch('/api/v1/backup/list');
      if (!response.ok) throw new Error('Failed to fetch backups');
      const data = await response.json();
      setBackups(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/v1/backup/status');
      if (!response.ok) throw new Error('Failed to fetch status');
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const refreshData = async () => {
    setLoading(true);
    await Promise.all([fetchBackups(), fetchStatus()]);
    setLoading(false);
  };

  useEffect(() => {
    refreshData();
    
    // Set up auto-refresh
    const interval = setInterval(refreshData, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, []);

  const createBackup = async () => {
    setCreating(true);
    try {
      const response = await fetch('/api/v1/backup/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          backup_type: selectedBackupType,
          include_files: includeFiles,
          compress: compress,
        }),
      });

      if (!response.ok) throw new Error('Failed to create backup');

      const result = await response.json();
      
      // Refresh data to show new backup
      await refreshData();
      
      // Reset form
      setSelectedBackupType('manual');
      setIncludeFiles(true);
      setCompress(true);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create backup');
    } finally {
      setCreating(false);
    }
  };

  const createComprehensiveBackup = async () => {
    setCreating(true);
    try {
      const response = await fetch('/api/v1/backup/create-comprehensive', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to create comprehensive backup');

      await refreshData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create comprehensive backup');
    } finally {
      setCreating(false);
    }
  };

  const toggleScheduler = async () => {
    if (!status) return;

    try {
      const endpoint = status.scheduler_running ? 'stop' : 'start';
      const response = await fetch(`/api/v1/backup/scheduler/${endpoint}`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error(`Failed to ${endpoint} scheduler`);

      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle scheduler');
    }
  };

  const restoreBackup = async () => {
    if (!selectedBackup || !restoreConfirm) return;

    try {
      const response = await fetch('/api/v1/backup/restore', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          backup_id: selectedBackup.backup_id,
          confirm: true,
        }),
      });

      if (!response.ok) throw new Error('Failed to restore backup');

      setShowRestoreDialog(false);
      setSelectedBackup(null);
      setRestoreConfirm(false);
      
      // Refresh data
      await refreshData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to restore backup');
    }
  };

  const cleanupBackups = async () => {
    try {
      const response = await fetch('/api/v1/backup/cleanup', {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to cleanup backups');

      await refreshData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cleanup backups');
    }
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Backup Manager
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" />
            Loading backup data...
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
              Backup Manager
            </div>
            <Button onClick={refreshData} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Manage automated backups and restore system data
          </CardDescription>
        </CardHeader>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Status Cards */}
      {status && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Scheduler Status</p>
                  <p className="text-2xl font-bold">
                    {status.scheduler_running ? 'Running' : 'Stopped'}
                  </p>
                </div>
                <div className={`h-3 w-3 rounded-full ${
                  status.scheduler_running ? 'bg-green-500' : 'bg-red-500'
                }`} />
              </div>
              <Button
                onClick={toggleScheduler}
                variant="outline"
                size="sm"
                className="mt-2 w-full"
              >
                {status.scheduler_running ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" />
                    Stop
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Start
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Success Rate</p>
                  <p className="text-2xl font-bold">
                    {(status.success_rate * 100).toFixed(1)}%
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
              <Progress value={status.success_rate * 100} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Recent Backups</p>
                  <p className="text-2xl font-bold">{status.recent_backups}</p>
                </div>
                <Database className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Next Backup</p>
                  <p className="text-lg font-medium">
                    {status.next_daily ? 
                      new Date(status.next_daily).toLocaleTimeString() : 
                      'Not scheduled'
                    }
                  </p>
                </div>
                <Clock className="h-8 w-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create Backup Section */}
      <Card>
        <CardHeader>
          <CardTitle>Create New Backup</CardTitle>
          <CardDescription>
            Create a backup of your system data and files
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Backup Type</Label>
              <Select value={selectedBackupType} onValueChange={setSelectedBackupType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="manual">Manual</SelectItem>
                  <SelectItem value="full">Full System</SelectItem>
                  <SelectItem value="incremental">Incremental</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Options</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="include-files"
                    checked={includeFiles}
                    onCheckedChange={setIncludeFiles}
                  />
                  <Label htmlFor="include-files">Include user files</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="compress"
                    checked={compress}
                    onCheckedChange={setCompress}
                  />
                  <Label htmlFor="compress">Compress archive</Label>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Actions</Label>
              <div className="space-y-2">
                <Button
                  onClick={createBackup}
                  disabled={creating}
                  className="w-full"
                >
                  {creating ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" />
                      Create Backup
                    </>
                  )}
                </Button>
                <Button
                  onClick={createComprehensiveBackup}
                  disabled={creating}
                  variant="outline"
                  className="w-full"
                >
                  <Database className="h-4 w-4 mr-2" />
                  Comprehensive
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Backup List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Available Backups</CardTitle>
              <CardDescription>
                List of all available backup archives
              </CardDescription>
            </div>
            <Button onClick={cleanupBackups} variant="outline" size="sm">
              <Trash2 className="h-4 w-4 mr-2" />
              Cleanup Old
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Backup ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Components</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {backups.map((backup) => (
                <TableRow key={backup.backup_id}>
                  <TableCell className="font-mono text-sm">
                    {backup.backup_id}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        backup.status === 'completed' 
                          ? 'default' 
                          : backup.status === 'failed'
                          ? 'destructive'
                          : 'secondary'
                      }
                    >
                      {backup.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {backup.components.map((component) => (
                        <Badge key={component} variant="outline" className="text-xs">
                          {component}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    {backup.size ? formatFileSize(backup.size) : 'N/A'}
                  </TableCell>
                  <TableCell>
                    {new Date(backup.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    {backup.duration ? formatDuration(backup.duration) : 'N/A'}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button
                        onClick={() => {
                          setSelectedBackup(backup);
                          setShowRestoreDialog(true);
                        }}
                        variant="outline"
                        size="sm"
                        disabled={backup.status !== 'completed'}
                      >
                        <Upload className="h-4 w-4 mr-1" />
                        Restore
                      </Button>
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {backups.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No backups available. Create your first backup above.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Restore Dialog */}
      <Dialog open={showRestoreDialog} onOpenChange={setShowRestoreDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Restore Backup
            </DialogTitle>
            <DialogDescription>
              This is a destructive operation that will overwrite existing data.
            </DialogDescription>
          </DialogHeader>

          {selectedBackup && (
            <div className="space-y-4">
              <div className="bg-muted p-4 rounded">
                <h4 className="font-semibold">Backup Details</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  ID: {selectedBackup.backup_id}
                </p>
                <p className="text-sm text-muted-foreground">
                  Created: {new Date(selectedBackup.created_at).toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">
                  Components: {selectedBackup.components.join(', ')}
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="restore-confirm"
                  checked={restoreConfirm}
                  onCheckedChange={setRestoreConfirm}
                />
                <Label htmlFor="restore-confirm" className="text-sm">
                  I understand this will overwrite existing data
                </Label>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowRestoreDialog(false);
                setSelectedBackup(null);
                setRestoreConfirm(false);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={restoreBackup}
              disabled={!restoreConfirm}
              variant="destructive"
            >
              <Upload className="h-4 w-4 mr-2" />
              Restore Backup
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BackupManager;