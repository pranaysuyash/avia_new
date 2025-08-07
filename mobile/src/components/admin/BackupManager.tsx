import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Alert,
  RefreshControl,
  Modal,
  Switch,
  Share,
  StyleSheet,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  Shield,
  Download,
  Upload,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Trash2,
  Play,
  Pause,
  Eye,
  Settings,
  Share as ShareIcon,
} from 'lucide-react-native';

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
  baseUrl?: string;
  authToken?: string;
}

const BackupManager: React.FC<BackupManagerProps> = ({
  baseUrl = 'http://localhost:8000',
  authToken,
}) => {
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [status, setStatus] = useState<BackupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [selectedBackupType, setSelectedBackupType] = useState<string>('manual');
  const [includeFiles, setIncludeFiles] = useState(true);
  const [compress, setCompress] = useState(true);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState<BackupInfo | null>(null);
  const [restoreConfirm, setRestoreConfirm] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Get auth headers
  const getHeaders = useCallback(async () => {
    const headers: any = {
      'Content-Type': 'application/json',
    };

    // Try to get token from props or AsyncStorage
    let token = authToken;
    if (!token) {
      try {
        token = await AsyncStorage.getItem('@auth_token');
      } catch (err) {
        console.warn('Failed to load auth token:', err);
      }
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }, [authToken]);

  const fetchBackups = async () => {
    try {
      const headers = await getHeaders();
      const response = await fetch(`${baseUrl}/api/v1/backup/list`, {
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch backups: ${response.status}`);
      }
      
      const data = await response.json();
      setBackups(data);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Failed to fetch backups:', message);
    }
  };

  const fetchStatus = async () => {
    try {
      const headers = await getHeaders();
      const response = await fetch(`${baseUrl}/api/v1/backup/status`, {
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch status: ${response.status}`);
      }
      
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Failed to fetch status:', message);
    }
  };

  const refreshData = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([fetchBackups(), fetchStatus()]);
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshData();

    // Set up auto-refresh
    const interval = setInterval(refreshData, 60000); // 1 minute for mobile
    return () => clearInterval(interval);
  }, [refreshData]);

  const createBackup = async () => {
    setCreating(true);
    try {
      const headers = await getHeaders();
      const response = await fetch(`${baseUrl}/api/v1/backup/create`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          backup_type: selectedBackupType,
          include_files: includeFiles,
          compress: compress,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create backup: ${response.status}`);
      }

      const result = await response.json();
      
      Alert.alert(
        'Backup Created',
        `Backup ${result.backup_id} created successfully`,
        [{ text: 'OK' }]
      );
      
      // Refresh data and reset form
      await refreshData();
      setSelectedBackupType('manual');
      setIncludeFiles(true);
      setCompress(true);
      setShowCreateModal(false);
      
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create backup';
      setError(message);
      Alert.alert('Error', message);
    } finally {
      setCreating(false);
    }
  };

  const createComprehensiveBackup = async () => {
    setCreating(true);
    try {
      const headers = await getHeaders();
      const response = await fetch(`${baseUrl}/api/v1/backup/create-comprehensive`, {
        method: 'POST',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to create comprehensive backup: ${response.status}`);
      }

      const result = await response.json();
      
      Alert.alert(
        'Comprehensive Backup Created',
        `Comprehensive backup ${result.backup_id} created successfully`,
        [{ text: 'OK' }]
      );

      await refreshData();
      setShowCreateModal(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create comprehensive backup';
      setError(message);
      Alert.alert('Error', message);
    } finally {
      setCreating(false);
    }
  };

  const toggleScheduler = async () => {
    if (!status) return;

    try {
      const endpoint = status.scheduler_running ? 'stop' : 'start';
      const headers = await getHeaders();
      const response = await fetch(`${baseUrl}/api/v1/backup/scheduler/${endpoint}`, {
        method: 'POST',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to ${endpoint} scheduler: ${response.status}`);
      }

      await fetchStatus();
      
      Alert.alert(
        'Scheduler Updated',
        `Backup scheduler ${status.scheduler_running ? 'stopped' : 'started'}`,
        [{ text: 'OK' }]
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to toggle scheduler';
      setError(message);
      Alert.alert('Error', message);
    }
  };

  const restoreBackup = async () => {
    if (!selectedBackup || !restoreConfirm) return;

    try {
      const headers = await getHeaders();
      const response = await fetch(`${baseUrl}/api/v1/backup/restore`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          backup_id: selectedBackup.backup_id,
          confirm: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to restore backup: ${response.status}`);
      }

      setShowRestoreModal(false);
      setSelectedBackup(null);
      setRestoreConfirm(false);
      
      Alert.alert(
        'Backup Restored',
        `Backup ${selectedBackup.backup_id} restored successfully`,
        [{ text: 'OK' }]
      );
      
      await refreshData();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to restore backup';
      setError(message);
      Alert.alert('Error', message);
    }
  };

  const cleanupBackups = async () => {
    Alert.alert(
      'Cleanup Backups',
      'Are you sure you want to remove old backups?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Cleanup',
          style: 'destructive',
          onPress: async () => {
            try {
              const headers = await getHeaders();
              const response = await fetch(`${baseUrl}/api/v1/backup/cleanup`, {
                method: 'POST',
                headers,
              });

              if (!response.ok) {
                throw new Error(`Failed to cleanup backups: ${response.status}`);
              }

              const result = await response.json();
              
              Alert.alert(
                'Cleanup Completed',
                `${result.removed_count} old backups removed`,
                [{ text: 'OK' }]
              );

              await refreshData();
            } catch (err) {
              const message = err instanceof Error ? err.message : 'Failed to cleanup backups';
              setError(message);
              Alert.alert('Error', message);
            }
          },
        },
      ]
    );
  };

  const shareBackupList = async () => {
    const reportData = {
      timestamp: new Date().toISOString(),
      platform: 'react-native',
      backups: backups.map(backup => ({
        id: backup.backup_id,
        created: backup.created_at,
        status: backup.status,
        size: backup.size,
        components: backup.components,
      })),
      status: status ? {
        scheduler_running: status.scheduler_running,
        recent_backups: status.recent_backups,
        success_rate: status.success_rate,
      } : null,
    };

    try {
      await Share.share({
        message: `Backup Report\n${JSON.stringify(reportData, null, 2)}`,
        title: 'Backup Status Report',
      });
    } catch (err) {
      Alert.alert('Error', 'Failed to share backup report');
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10B981'; // green
      case 'failed':
        return '#EF4444'; // red
      default:
        return '#6B7280'; // gray
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <RefreshCw color="#666" size={24} />
          <Text style={styles.loadingText}>Loading backup data...</Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={refreshData} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <View style={styles.headerTitle}>
            <Shield color="#2563EB" size={24} />
            <Text style={styles.title}>Backup Manager</Text>
          </View>
          <TouchableOpacity onPress={shareBackupList} style={styles.shareButton}>
            <ShareIcon color="#666" size={20} />
          </TouchableOpacity>
        </View>
        <Text style={styles.subtitle}>
          Manage automated backups from your mobile device
        </Text>
      </View>

      {/* Error Alert */}
      {error && (
        <View style={styles.errorContainer}>
          <AlertTriangle color="#EF4444" size={20} />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity
            onPress={() => setError(null)}
            style={styles.errorClose}
          >
            <Text style={styles.errorCloseText}>×</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Status Cards */}
      {status && (
        <View style={styles.statusGrid}>
          <View style={styles.statusCard}>
            <Text style={styles.statusLabel}>Scheduler</Text>
            <View style={styles.statusValue}>
              <Text style={styles.statusValueText}>
                {status.scheduler_running ? 'Running' : 'Stopped'}
              </Text>
              <View
                style={[
                  styles.statusIndicator,
                  {
                    backgroundColor: status.scheduler_running ? '#10B981' : '#EF4444',
                  },
                ]}
              />
            </View>
            <TouchableOpacity onPress={toggleScheduler} style={styles.statusButton}>
              {status.scheduler_running ? (
                <Pause color="#666" size={16} />
              ) : (
                <Play color="#666" size={16} />
              )}
              <Text style={styles.statusButtonText}>
                {status.scheduler_running ? 'Stop' : 'Start'}
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.statusCard}>
            <Text style={styles.statusLabel}>Success Rate</Text>
            <Text style={styles.statusValue}>
              {(status.success_rate * 100).toFixed(1)}%
            </Text>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${status.success_rate * 100}%` },
                ]}
              />
            </View>
          </View>

          <View style={styles.statusCard}>
            <Text style={styles.statusLabel}>Recent Backups</Text>
            <Text style={styles.statusValue}>{status.recent_backups}</Text>
            <Database color="#3B82F6" size={24} style={styles.statusIcon} />
          </View>

          <View style={styles.statusCard}>
            <Text style={styles.statusLabel}>Next Backup</Text>
            <Text style={styles.statusValue}>
              {status.next_daily
                ? new Date(status.next_daily).toLocaleTimeString()
                : 'Not scheduled'}
            </Text>
            <Clock color="#F59E0B" size={24} style={styles.statusIcon} />
          </View>
        </View>
      )}

      {/* Action Buttons */}
      <View style={styles.actionContainer}>
        <TouchableOpacity
          onPress={() => setShowCreateModal(true)}
          style={[styles.actionButton, styles.primaryButton]}
        >
          <Download color="#FFFFFF" size={20} />
          <Text style={styles.primaryButtonText}>Create Backup</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={cleanupBackups} style={styles.actionButton}>
          <Trash2 color="#666" size={20} />
          <Text style={styles.actionButtonText}>Cleanup Old</Text>
        </TouchableOpacity>
      </View>

      {/* Backup List */}
      <View style={styles.backupList}>
        <Text style={styles.sectionTitle}>Available Backups</Text>
        {backups.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateText}>
              No backups available. Create your first backup above.
            </Text>
          </View>
        ) : (
          backups.map((backup) => (
            <View key={backup.backup_id} style={styles.backupCard}>
              <View style={styles.backupHeader}>
                <Text style={styles.backupId}>{backup.backup_id}</Text>
                <View
                  style={[
                    styles.backupStatus,
                    { backgroundColor: getStatusColor(backup.status) },
                  ]}
                >
                  <Text style={styles.backupStatusText}>{backup.status}</Text>
                </View>
              </View>

              <View style={styles.backupDetails}>
                <Text style={styles.backupDetail}>
                  Created: {new Date(backup.created_at).toLocaleString()}
                </Text>
                <Text style={styles.backupDetail}>
                  Size: {backup.size ? formatFileSize(backup.size) : 'N/A'}
                </Text>
                {backup.duration && (
                  <Text style={styles.backupDetail}>
                    Duration: {formatDuration(backup.duration)}
                  </Text>
                )}
                <View style={styles.components}>
                  {backup.components.map((component) => (
                    <View key={component} style={styles.component}>
                      <Text style={styles.componentText}>{component}</Text>
                    </View>
                  ))}
                </View>
              </View>

              <View style={styles.backupActions}>
                <TouchableOpacity
                  onPress={() => {
                    setSelectedBackup(backup);
                    setShowRestoreModal(true);
                  }}
                  style={[
                    styles.backupAction,
                    backup.status !== 'completed' && styles.disabledAction,
                  ]}
                  disabled={backup.status !== 'completed'}
                >
                  <Upload color={backup.status === 'completed' ? '#2563EB' : '#9CA3AF'} size={16} />
                  <Text style={styles.backupActionText}>Restore</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.backupAction}>
                  <Eye color="#666" size={16} />
                  <Text style={styles.backupActionText}>Details</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
      </View>

      {/* Create Backup Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Create New Backup</Text>
            <TouchableOpacity
              onPress={() => setShowCreateModal(false)}
              style={styles.modalClose}
            >
              <Text style={styles.modalCloseText}>×</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <Text style={styles.formLabel}>Backup Type</Text>
            <View style={styles.radioGroup}>
              {['manual', 'full', 'incremental'].map((type) => (
                <TouchableOpacity
                  key={type}
                  onPress={() => setSelectedBackupType(type)}
                  style={styles.radioOption}
                >
                  <View
                    style={[
                      styles.radioCircle,
                      selectedBackupType === type && styles.radioSelected,
                    ]}
                  />
                  <Text style={styles.radioLabel}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.switchContainer}>
              <Text style={styles.switchLabel}>Include user files</Text>
              <Switch value={includeFiles} onValueChange={setIncludeFiles} />
            </View>

            <View style={styles.switchContainer}>
              <Text style={styles.switchLabel}>Compress archive</Text>
              <Switch value={compress} onValueChange={setCompress} />
            </View>

            <View style={styles.modalActions}>
              <TouchableOpacity
                onPress={createBackup}
                disabled={creating}
                style={[styles.modalButton, styles.primaryButton]}
              >
                {creating ? (
                  <RefreshCw color="#FFFFFF" size={20} />
                ) : (
                  <Download color="#FFFFFF" size={20} />
                )}
                <Text style={styles.primaryButtonText}>
                  {creating ? 'Creating...' : 'Create Backup'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                onPress={createComprehensiveBackup}
                disabled={creating}
                style={styles.modalButton}
              >
                <Database color="#666" size={20} />
                <Text style={styles.actionButtonText}>Comprehensive</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* Restore Backup Modal */}
      <Modal
        visible={showRestoreModal}
        animationType="slide"
        transparent={true}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.restoreModal}>
            <View style={styles.restoreHeader}>
              <AlertTriangle color="#EF4444" size={24} />
              <Text style={styles.restoreTitle}>Restore Backup</Text>
            </View>

            <Text style={styles.restoreWarning}>
              This is a destructive operation that will overwrite existing data.
            </Text>

            {selectedBackup && (
              <View style={styles.backupInfo}>
                <Text style={styles.backupInfoTitle}>Backup Details</Text>
                <Text style={styles.backupInfoText}>
                  ID: {selectedBackup.backup_id}
                </Text>
                <Text style={styles.backupInfoText}>
                  Created: {new Date(selectedBackup.created_at).toLocaleString()}
                </Text>
                <Text style={styles.backupInfoText}>
                  Components: {selectedBackup.components.join(', ')}
                </Text>
              </View>
            )}

            <View style={styles.confirmContainer}>
              <TouchableOpacity
                onPress={() => setRestoreConfirm(!restoreConfirm)}
                style={styles.checkboxContainer}
              >
                <View style={[styles.checkbox, restoreConfirm && styles.checkboxChecked]}>
                  {restoreConfirm && <Text style={styles.checkmark}>✓</Text>}
                </View>
                <Text style={styles.checkboxLabel}>
                  I understand this will overwrite existing data
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.restoreActions}>
              <TouchableOpacity
                onPress={() => {
                  setShowRestoreModal(false);
                  setSelectedBackup(null);
                  setRestoreConfirm(false);
                }}
                style={styles.restoreButton}
              >
                <Text style={styles.restoreButtonText}>Cancel</Text>
              </TouchableOpacity>

              <TouchableOpacity
                onPress={restoreBackup}
                disabled={!restoreConfirm}
                style={[
                  styles.restoreButton,
                  styles.destructiveButton,
                  !restoreConfirm && styles.disabledButton,
                ]}
              >
                <Upload color="#FFFFFF" size={16} />
                <Text style={styles.destructiveButtonText}>Restore Backup</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    marginTop: 8,
    fontSize: 16,
    color: '#666',
  },
  header: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  headerTitle: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    marginLeft: 8,
    color: '#111827',
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
  },
  shareButton: {
    padding: 8,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    margin: 16,
    padding: 12,
    borderRadius: 8,
  },
  errorText: {
    flex: 1,
    fontSize: 14,
    color: '#DC2626',
    marginLeft: 8,
  },
  errorClose: {
    padding: 4,
  },
  errorCloseText: {
    fontSize: 18,
    color: '#DC2626',
  },
  statusGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    gap: 12,
  },
  statusCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 16,
    width: '48%',
    minHeight: 120,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  statusLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  statusValue: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusValueText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: 8,
  },
  statusButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  statusButtonText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  statusIcon: {
    position: 'absolute',
    top: 12,
    right: 12,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#10B981',
  },
  actionContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
  },
  primaryButton: {
    backgroundColor: '#2563EB',
    borderColor: '#2563EB',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginLeft: 8,
  },
  primaryButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF',
    marginLeft: 8,
  },
  backupList: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  emptyState: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  emptyStateText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
  },
  backupCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  backupHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  backupId: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
    fontFamily: 'monospace',
  },
  backupStatus: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  backupStatusText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#FFFFFF',
  },
  backupDetails: {
    marginBottom: 12,
  },
  backupDetail: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 2,
  },
  components: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
    gap: 4,
  },
  component: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  componentText: {
    fontSize: 10,
    color: '#374151',
  },
  backupActions: {
    flexDirection: 'row',
    gap: 12,
  },
  backupAction: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#F9FAFB',
  },
  disabledAction: {
    opacity: 0.5,
  },
  backupActionText: {
    fontSize: 12,
    color: '#374151',
    marginLeft: 4,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  modalClose: {
    padding: 8,
  },
  modalCloseText: {
    fontSize: 24,
    color: '#6B7280',
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  formLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111827',
    marginBottom: 12,
  },
  radioGroup: {
    marginBottom: 24,
  },
  radioOption: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  radioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    marginRight: 12,
  },
  radioSelected: {
    borderColor: '#2563EB',
    backgroundColor: '#2563EB',
  },
  radioLabel: {
    fontSize: 16,
    color: '#374151',
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  switchLabel: {
    fontSize: 16,
    color: '#374151',
  },
  modalActions: {
    marginTop: 32,
    gap: 12,
  },
  modalButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  restoreModal: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 24,
    width: '100%',
    maxWidth: 400,
  },
  restoreHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  restoreTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 12,
  },
  restoreWarning: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 16,
  },
  backupInfo: {
    backgroundColor: '#F9FAFB',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  backupInfoTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
    marginBottom: 8,
  },
  backupInfoText: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 2,
  },
  confirmContainer: {
    marginBottom: 24,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    width: 20,
    height: 20,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    borderRadius: 4,
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#2563EB',
    borderColor: '#2563EB',
  },
  checkmark: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  checkboxLabel: {
    fontSize: 14,
    color: '#374151',
    flex: 1,
  },
  restoreActions: {
    flexDirection: 'row',
    gap: 12,
  },
  restoreButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
  },
  destructiveButton: {
    backgroundColor: '#EF4444',
    borderColor: '#EF4444',
  },
  disabledButton: {
    opacity: 0.5,
  },
  restoreButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  destructiveButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF',
    marginLeft: 8,
  },
});

export default BackupManager;