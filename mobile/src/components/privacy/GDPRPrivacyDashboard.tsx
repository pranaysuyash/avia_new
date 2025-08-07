import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
  Modal,
  TextInput,
  Switch,
  ActivityIndicator,
  Share,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import * as Notifications from 'expo-notifications';
import { format } from 'date-fns';

// Mobile-specific interfaces
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
  navigation?: any;
}

export const GDPRPrivacyDashboard: React.FC<GDPRPrivacyDashboardProps> = ({ navigation }) => {
  const { colors } = useTheme();
  
  // State
  const [dashboardData, setDashboardData] = useState<PrivacyDashboardData | null>(null);
  const [consents, setConsents] = useState<ConsentRecord[]>([]);
  const [exports, setExports] = useState<ExportRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('exports');

  // Modal states
  const [showExportModal, setShowExportModal] = useState(false);
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [showDeletionModal, setShowDeletionModal] = useState(false);
  const [showRightsModal, setShowRightsModal] = useState(false);

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

  // Mobile-specific functionality
  const showMobileNotification = async (title: string, body: string) => {
    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        sound: 'default',
        data: { type: 'privacy' },
      },
      trigger: null,
    });
  };

  const shareExportFile = async (exportRequest: ExportRequest) => {
    if (!exportRequest.download_url) return;

    try {
      // Download file to local storage
      const fileUri = `${FileSystem.documentDirectory}gdpr_export_${exportRequest.request_id}.${exportRequest.format_type || 'json'}`;
      
      const downloadResult = await FileSystem.downloadAsync(
        exportRequest.download_url,
        fileUri
      );

      if (downloadResult.status === 200) {
        // Share or open file
        if (await Sharing.isAvailableAsync()) {
          await Sharing.shareAsync(downloadResult.uri, {
            mimeType: exportRequest.format_type === 'json' ? 'application/json' : 'text/plain',
            dialogTitle: 'GDPR Data Export'
          });
        } else {
          Alert.alert(
            'Export Downloaded',
            `File saved to: ${downloadResult.uri}`,
            [{ text: 'OK' }]
          );
        }

        await showMobileNotification(
          'Export Downloaded',
          'Your GDPR data export has been downloaded successfully'
        );
      }
    } catch (err) {
      Alert.alert(
        'Download Error',
        'Failed to download export file. Please try again.',
        [{ text: 'OK' }]
      );
    }
  };

  const showConfirmAlert = (title: string, message: string, onConfirm: () => void) => {
    Alert.alert(
      title,
      message,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Confirm', onPress: onConfirm, style: 'destructive' }
      ]
    );
  };

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
      
      await showMobileNotification(
        'Export Requested',
        `Export request created: ${result.request_id}`
      );
      
      setShowExportModal(false);
      await fetchExports();
    } catch (err) {
      Alert.alert('Error', err instanceof Error ? err.message : 'Failed to request export');
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
      
      await showMobileNotification(
        'Consent Recorded',
        `Consent recorded: ${result.consent_id}`
      );
      
      setShowConsentModal(false);
      setConsentForm({ purpose: '', consent_text: '', consent_version: '1.0' });
      await fetchConsents();
    } catch (err) {
      Alert.alert('Error', err instanceof Error ? err.message : 'Failed to record consent');
    }
  };

  const withdrawConsent = async (consentId: string) => {
    showConfirmAlert(
      'Withdraw Consent',
      'Are you sure you want to withdraw this consent?',
      async () => {
        try {
          const response = await fetch(`/api/v1/gdpr/consent/withdraw/${consentId}`, {
            method: 'POST',
          });

          if (!response.ok) throw new Error('Failed to withdraw consent');

          await showMobileNotification('Consent Withdrawn', 'Consent withdrawn successfully');
          await fetchConsents();
        } catch (err) {
          Alert.alert('Error', err instanceof Error ? err.message : 'Failed to withdraw consent');
        }
      }
    );
  };

  const requestDataDeletion = async () => {
    if (!deletionConfirm.confirmation || !deletionConfirm.understanding) {
      Alert.alert(
        'Confirmation Required',
        'Please confirm both checkboxes to proceed with data deletion.'
      );
      return;
    }

    showConfirmAlert(
      'Delete All Data',
      'This will permanently delete ALL your data. This action cannot be undone. Are you sure?',
      async () => {
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
          
          await showMobileNotification(
            'Data Deletion Requested',
            `Data deletion ${result.status}. This action cannot be undone.`
          );
          
          if (result.status === 'completed') {
            // Navigate to login or close app
            if (navigation) {
              navigation.reset({
                index: 0,
                routes: [{ name: 'Login' }],
              });
            }
          }
          
          setShowDeletionModal(false);
        } catch (err) {
          Alert.alert('Error', err instanceof Error ? err.message : 'Failed to request deletion');
        }
      }
    );
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
        return colors.primary;
      case 'processing':
      case 'pending':
        return '#f59e0b';
      case 'failed':
        return '#ef4444';
      case 'withdrawn':
        return '#6b7280';
      default:
        return '#6b7280';
    }
  };

  const styles = {
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
    header: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      justifyContent: 'space-between' as const,
      paddingHorizontal: 16,
      paddingVertical: 12,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    headerTitle: {
      fontSize: 18,
      fontWeight: 'bold' as const,
      color: colors.text,
      flex: 1,
      marginLeft: 12,
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center' as const,
      alignItems: 'center' as const,
      padding: 20,
    },
    loadingText: {
      marginTop: 10,
      color: colors.text,
    },
    errorContainer: {
      backgroundColor: '#fee2e2',
      borderColor: '#fecaca',
      borderWidth: 1,
      borderRadius: 8,
      padding: 12,
      margin: 16,
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
    },
    errorText: {
      color: '#dc2626',
      marginLeft: 8,
      flex: 1,
    },
    statsGrid: {
      flexDirection: 'row' as const,
      flexWrap: 'wrap' as const,
      padding: 16,
      gap: 12,
    },
    statCard: {
      backgroundColor: colors.card,
      borderRadius: 8,
      padding: 16,
      flex: 1,
      minWidth: '45%',
      alignItems: 'center' as const,
    },
    statNumber: {
      fontSize: 24,
      fontWeight: 'bold' as const,
      color: colors.primary,
    },
    statLabel: {
      fontSize: 12,
      color: colors.text,
      textAlign: 'center' as const,
      marginTop: 4,
    },
    tabContainer: {
      flexDirection: 'row' as const,
      backgroundColor: colors.card,
      marginHorizontal: 16,
      borderRadius: 8,
      marginBottom: 16,
    },
    tab: {
      flex: 1,
      paddingVertical: 12,
      paddingHorizontal: 16,
      alignItems: 'center' as const,
    },
    activeTab: {
      backgroundColor: colors.primary,
      borderRadius: 8,
    },
    tabText: {
      fontSize: 14,
      color: colors.text,
    },
    activeTabText: {
      color: '#fff',
      fontWeight: 'bold' as const,
    },
    contentContainer: {
      flex: 1,
      paddingHorizontal: 16,
    },
    card: {
      backgroundColor: colors.card,
      borderRadius: 8,
      padding: 16,
      marginBottom: 16,
    },
    cardTitle: {
      fontSize: 16,
      fontWeight: 'bold' as const,
      color: colors.text,
      marginBottom: 8,
    },
    cardDescription: {
      fontSize: 14,
      color: colors.text,
      marginBottom: 16,
    },
    button: {
      backgroundColor: colors.primary,
      borderRadius: 8,
      paddingVertical: 12,
      paddingHorizontal: 16,
      alignItems: 'center' as const,
    },
    buttonText: {
      color: '#fff',
      fontWeight: 'bold' as const,
    },
    outlineButton: {
      borderWidth: 1,
      borderColor: colors.border,
      backgroundColor: 'transparent',
    },
    outlineButtonText: {
      color: colors.text,
    },
    exportItem: {
      flexDirection: 'row' as const,
      justifyContent: 'space-between' as const,
      alignItems: 'center' as const,
      paddingVertical: 12,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    exportInfo: {
      flex: 1,
    },
    exportId: {
      fontSize: 12,
      fontFamily: 'monospace',
      color: colors.text,
    },
    exportStatus: {
      fontSize: 12,
      fontWeight: 'bold' as const,
      marginTop: 2,
    },
    badge: {
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 12,
      alignSelf: 'flex-start' as const,
    },
    badgeText: {
      fontSize: 12,
      fontWeight: 'bold' as const,
      color: '#fff',
    },
    modal: {
      flex: 1,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      justifyContent: 'center' as const,
      alignItems: 'center' as const,
    },
    modalContent: {
      backgroundColor: colors.card,
      borderRadius: 12,
      padding: 24,
      margin: 20,
      maxHeight: '80%',
      width: '90%',
    },
    modalTitle: {
      fontSize: 18,
      fontWeight: 'bold' as const,
      color: colors.text,
      marginBottom: 8,
    },
    modalDescription: {
      fontSize: 14,
      color: colors.text,
      marginBottom: 20,
    },
    input: {
      borderWidth: 1,
      borderColor: colors.border,
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 10,
      fontSize: 16,
      color: colors.text,
      marginBottom: 16,
    },
    textArea: {
      height: 80,
      textAlignVertical: 'top' as const,
    },
    label: {
      fontSize: 14,
      fontWeight: 'bold' as const,
      color: colors.text,
      marginBottom: 4,
    },
    switchContainer: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      marginBottom: 16,
    },
    switchLabel: {
      flex: 1,
      fontSize: 14,
      color: colors.text,
      marginRight: 12,
    },
    modalButtons: {
      flexDirection: 'row' as const,
      justifyContent: 'space-between' as const,
      marginTop: 20,
    },
    modalButton: {
      flex: 1,
      paddingVertical: 12,
      borderRadius: 8,
      alignItems: 'center' as const,
      marginHorizontal: 5,
    },
    dangerZone: {
      borderWidth: 1,
      borderColor: '#fecaca',
      backgroundColor: '#fee2e2',
      borderRadius: 8,
      padding: 16,
      marginBottom: 16,
    },
    dangerTitle: {
      fontSize: 16,
      fontWeight: 'bold' as const,
      color: '#dc2626',
      marginBottom: 8,
    },
    dangerDescription: {
      fontSize: 14,
      color: '#dc2626',
      marginBottom: 12,
    },
    dangerButton: {
      backgroundColor: '#dc2626',
    },
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Icon name="shield" size={24} color={colors.primary} />
          <Text style={styles.headerTitle}>Privacy Dashboard</Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading privacy data...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Icon name="shield" size={24} color={colors.primary} />
        <Text style={styles.headerTitle}>GDPR Privacy Dashboard</Text>
        <TouchableOpacity onPress={() => setShowRightsModal(true)}>
          <Icon name="info" size={24} color={colors.text} />
        </TouchableOpacity>
        <TouchableOpacity onPress={refreshData} style={{ marginLeft: 12 }}>
          <Icon name="refresh" size={24} color={colors.text} />
        </TouchableOpacity>
      </View>

      {error && (
        <View style={styles.errorContainer}>
          <Icon name="warning" size={20} color="#dc2626" />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <ScrollView style={{ flex: 1 }}>
        {/* Dashboard Stats */}
        {dashboardData && (
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Icon name="description" size={32} color="#3b82f6" />
              <Text style={styles.statNumber}>{dashboardData.data_categories.length}</Text>
              <Text style={styles.statLabel}>Data Categories</Text>
            </View>
            <View style={styles.statCard}>
              <Icon name="check-circle" size={32} color="#10b981" />
              <Text style={styles.statNumber}>{dashboardData.active_consents}</Text>
              <Text style={styles.statLabel}>Active Consents</Text>
            </View>
            <View style={styles.statCard}>
              <Icon name="settings" size={32} color="#8b5cf6" />
              <Text style={styles.statNumber}>{dashboardData.processing_activities}</Text>
              <Text style={styles.statLabel}>Processing Activities</Text>
            </View>
            <View style={styles.statCard}>
              <Icon name="download" size={32} color="#f59e0b" />
              <Text style={styles.statNumber}>{dashboardData.export_requests}</Text>
              <Text style={styles.statLabel}>Export Requests</Text>
            </View>
          </View>
        )}

        {/* Tab Navigation */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'exports' && styles.activeTab]}
            onPress={() => setActiveTab('exports')}
          >
            <Text style={[styles.tabText, activeTab === 'exports' && styles.activeTabText]}>
              Exports
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'consents' && styles.activeTab]}
            onPress={() => setActiveTab('consents')}
          >
            <Text style={[styles.tabText, activeTab === 'consents' && styles.activeTabText]}>
              Consents
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'settings' && styles.activeTab]}
            onPress={() => setActiveTab('settings')}
          >
            <Text style={[styles.tabText, activeTab === 'settings' && styles.activeTabText]}>
              Settings
            </Text>
          </TouchableOpacity>
        </View>

        {/* Tab Content */}
        <View style={styles.contentContainer}>
          {activeTab === 'exports' && (
            <View style={styles.card}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardTitle}>Data Export Requests</Text>
                  <Text style={styles.cardDescription}>
                    Download your personal data (GDPR Article 20)
                  </Text>
                </View>
                <TouchableOpacity
                  style={styles.button}
                  onPress={() => setShowExportModal(true)}
                >
                  <Icon name="download" size={16} color="#fff" />
                  <Text style={styles.buttonText}>Request</Text>
                </TouchableOpacity>
              </View>

              {exports.length > 0 ? (
                exports.map((exportReq) => (
                  <View key={exportReq.request_id} style={styles.exportItem}>
                    <View style={styles.exportInfo}>
                      <Text style={styles.exportId}>
                        {exportReq.request_id.slice(0, 8)}...
                      </Text>
                      <Text style={styles.exportStatus}>
                        {exportReq.export_type}
                      </Text>
                      <View style={[styles.badge, { backgroundColor: getStatusColor(exportReq.status) }]}>
                        <Text style={styles.badgeText}>{exportReq.status}</Text>
                      </View>
                      <Text style={{ fontSize: 12, color: colors.text, marginTop: 4 }}>
                        {format(new Date(exportReq.requested_at), 'MMM dd, yyyy')}
                      </Text>
                    </View>
                    {exportReq.status === 'completed' && exportReq.download_url && (
                      <TouchableOpacity
                        style={[styles.button, styles.outlineButton]}
                        onPress={() => shareExportFile(exportReq)}
                      >
                        <Icon name="share" size={16} color={colors.text} />
                      </TouchableOpacity>
                    )}
                  </View>
                ))
              ) : (
                <Text style={{ textAlign: 'center', color: colors.text, padding: 20 }}>
                  No export requests yet. Request your data export to get started.
                </Text>
              )}
            </View>
          )}

          {activeTab === 'consents' && (
            <View style={styles.card}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardTitle}>Consent Management</Text>
                  <Text style={styles.cardDescription}>
                    Manage your consent preferences (GDPR Article 7)
                  </Text>
                </View>
                <TouchableOpacity
                  style={styles.button}
                  onPress={() => setShowConsentModal(true)}
                >
                  <Icon name="check-circle" size={16} color="#fff" />
                  <Text style={styles.buttonText}>Record</Text>
                </TouchableOpacity>
              </View>

              {consents.length > 0 ? (
                consents.map((consent) => (
                  <View key={consent.id} style={styles.exportItem}>
                    <View style={styles.exportInfo}>
                      <Text style={[styles.cardTitle, { fontSize: 14, marginBottom: 4 }]}>
                        {consent.purpose}
                      </Text>
                      <View style={[styles.badge, { backgroundColor: getStatusColor(consent.consent_status) }]}>
                        <Text style={styles.badgeText}>{consent.consent_status}</Text>
                      </View>
                      {consent.given_at && (
                        <Text style={{ fontSize: 12, color: colors.text, marginTop: 4 }}>
                          Given: {format(new Date(consent.given_at), 'MMM dd, yyyy')}
                        </Text>
                      )}
                    </View>
                    {consent.consent_status === 'given' && (
                      <TouchableOpacity
                        style={[styles.button, styles.outlineButton]}
                        onPress={() => withdrawConsent(consent.id)}
                      >
                        <Icon name="block" size={16} color={colors.text} />
                        <Text style={styles.outlineButtonText}>Withdraw</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                ))
              ) : (
                <Text style={{ textAlign: 'center', color: colors.text, padding: 20 }}>
                  No consent records found.
                </Text>
              )}
            </View>
          )}

          {activeTab === 'settings' && (
            <>
              {/* Data Categories */}
              {dashboardData && (
                <View style={styles.card}>
                  <Text style={styles.cardTitle}>Data Processing Overview</Text>
                  <Text style={styles.cardDescription}>
                    Categories of data we process and retention periods
                  </Text>

                  <Text style={[styles.label, { marginTop: 16 }]}>Data Categories:</Text>
                  <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 16 }}>
                    {dashboardData.data_categories.map((category) => (
                      <View key={category} style={[styles.badge, { backgroundColor: colors.primary, margin: 2 }]}>
                        <Text style={styles.badgeText}>
                          {category.replace('_', ' ')}
                        </Text>
                      </View>
                    ))}
                  </View>

                  <Text style={styles.label}>Retention Periods:</Text>
                  {Object.entries(dashboardData.data_retention_info).map(([category, days]) => (
                    <View key={category} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8 }}>
                      <Text style={{ color: colors.text, textTransform: 'capitalize' }}>
                        {category.replace('_', ' ')}
                      </Text>
                      <Text style={{ color: colors.text, fontSize: 12 }}>
                        {days} days
                      </Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Danger Zone */}
              <View style={styles.dangerZone}>
                <Text style={styles.dangerTitle}>Danger Zone</Text>
                <Text style={styles.dangerDescription}>
                  Permanently delete all your data. This action cannot be undone.
                </Text>
                <TouchableOpacity
                  style={[styles.button, styles.dangerButton]}
                  onPress={() => setShowDeletionModal(true)}
                >
                  <Icon name="delete" size={16} color="#fff" />
                  <Text style={styles.buttonText}>Delete All Data</Text>
                </TouchableOpacity>
              </View>
            </>
          )}
        </View>
      </ScrollView>

      {/* Export Request Modal */}
      <Modal visible={showExportModal} transparent animationType="slide">
        <View style={styles.modal}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Request Data Export</Text>
            <Text style={styles.modalDescription}>
              Export your personal data in compliance with GDPR Article 20
            </Text>

            <Text style={styles.label}>Export Type</Text>
            <TextInput
              style={styles.input}
              value={exportForm.export_type}
              onChangeText={(text) => setExportForm({ ...exportForm, export_type: text })}
              placeholder="full_export, transcripts_only, analytics_only"
            />

            <Text style={styles.label}>Format</Text>
            <TextInput
              style={styles.input}
              value={exportForm.format_type}
              onChangeText={(text) => setExportForm({ ...exportForm, format_type: text })}
              placeholder="json, csv, xml"
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.outlineButton]}
                onPress={() => setShowExportModal(false)}
              >
                <Text style={styles.outlineButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.button]}
                onPress={requestDataExport}
              >
                <Text style={styles.buttonText}>Request Export</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Consent Recording Modal */}
      <Modal visible={showConsentModal} transparent animationType="slide">
        <View style={styles.modal}>
          <ScrollView contentContainerStyle={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Record Consent</Text>
              <Text style={styles.modalDescription}>
                Record your consent for specific data processing purposes
              </Text>

              <Text style={styles.label}>Purpose</Text>
              <TextInput
                style={styles.input}
                value={consentForm.purpose}
                onChangeText={(text) => setConsentForm({ ...consentForm, purpose: text })}
                placeholder="e.g., Marketing communications"
              />

              <Text style={styles.label}>Consent Text</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={consentForm.consent_text}
                onChangeText={(text) => setConsentForm({ ...consentForm, consent_text: text })}
                placeholder="Full consent text that user agrees to..."
                multiline
              />

              <Text style={styles.label}>Version</Text>
              <TextInput
                style={styles.input}
                value={consentForm.consent_version}
                onChangeText={(text) => setConsentForm({ ...consentForm, consent_version: text })}
                placeholder="1.0"
              />

              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={[styles.modalButton, styles.outlineButton]}
                  onPress={() => setShowConsentModal(false)}
                >
                  <Text style={styles.outlineButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.modalButton, styles.button]}
                  onPress={recordConsent}
                >
                  <Text style={styles.buttonText}>Record Consent</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* Data Deletion Modal */}
      <Modal visible={showDeletionModal} transparent animationType="slide">
        <View style={styles.modal}>
          <ScrollView contentContainerStyle={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
            <View style={styles.modalContent}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                <Icon name="warning" size={24} color="#dc2626" />
                <Text style={[styles.modalTitle, { color: '#dc2626', marginLeft: 8, marginBottom: 0 }]}>
                  Delete All Data
                </Text>
              </View>
              <Text style={styles.modalDescription}>
                This will permanently delete ALL your data. This action cannot be undone.
              </Text>

              <View style={[styles.errorContainer, { margin: 0, marginBottom: 16 }]}>
                <Icon name="warning" size={20} color="#dc2626" />
                <Text style={styles.errorText}>
                  <Text style={{ fontWeight: 'bold' }}>WARNING:</Text> This will delete your account, 
                  transcripts, settings, and all associated data.
                </Text>
              </View>

              <Text style={styles.label}>Reason for deletion (optional)</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={deletionConfirm.reason}
                onChangeText={(text) => setDeletionConfirm({ ...deletionConfirm, reason: text })}
                placeholder="Please tell us why you're deleting your data..."
                multiline
              />

              <View style={styles.switchContainer}>
                <Text style={styles.switchLabel}>
                  I understand that this will permanently delete all my data
                </Text>
                <Switch
                  value={deletionConfirm.confirmation}
                  onValueChange={(value) => setDeletionConfirm({ ...deletionConfirm, confirmation: value })}
                />
              </View>

              <View style={styles.switchContainer}>
                <Text style={styles.switchLabel}>
                  I understand this action cannot be undone
                </Text>
                <Switch
                  value={deletionConfirm.understanding}
                  onValueChange={(value) => setDeletionConfirm({ ...deletionConfirm, understanding: value })}
                />
              </View>

              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={[styles.modalButton, styles.outlineButton]}
                  onPress={() => setShowDeletionModal(false)}
                >
                  <Text style={styles.outlineButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.modalButton, styles.dangerButton]}
                  onPress={requestDataDeletion}
                  disabled={!deletionConfirm.confirmation || !deletionConfirm.understanding}
                >
                  <Text style={styles.buttonText}>Delete All Data</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* Rights Information Modal */}
      <Modal visible={showRightsModal} transparent animationType="slide">
        <View style={styles.modal}>
          <ScrollView contentContainerStyle={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
            <View style={[styles.modalContent, { maxHeight: '90%' }]}>
              <Text style={styles.modalTitle}>Your Privacy Rights Under GDPR</Text>
              <Text style={styles.modalDescription}>
                Learn about your rights and how to exercise them
              </Text>

              <ScrollView style={{ maxHeight: 400 }}>
                <View style={{ marginBottom: 12, padding: 12, borderWidth: 1, borderColor: colors.border, borderRadius: 8 }}>
                  <Text style={[styles.label, { marginBottom: 4 }]}>Right to Access (Article 15)</Text>
                  <Text style={{ fontSize: 12, color: colors.text }}>
                    You can request information about your personal data we process
                  </Text>
                </View>

                <View style={{ marginBottom: 12, padding: 12, borderWidth: 1, borderColor: colors.border, borderRadius: 8 }}>
                  <Text style={[styles.label, { marginBottom: 4 }]}>Right to Rectification (Article 16)</Text>
                  <Text style={{ fontSize: 12, color: colors.text }}>
                    You can request correction of inaccurate personal data
                  </Text>
                </View>

                <View style={{ marginBottom: 12, padding: 12, borderWidth: 1, borderColor: colors.border, borderRadius: 8 }}>
                  <Text style={[styles.label, { marginBottom: 4 }]}>Right to Erasure (Article 17)</Text>
                  <Text style={{ fontSize: 12, color: colors.text }}>
                    You can request deletion of your personal data ("right to be forgotten")
                  </Text>
                </View>

                <View style={{ marginBottom: 12, padding: 12, borderWidth: 1, borderColor: colors.border, borderRadius: 8 }}>
                  <Text style={[styles.label, { marginBottom: 4 }]}>Right to Data Portability (Article 20)</Text>
                  <Text style={{ fontSize: 12, color: colors.text }}>
                    You can request your data in a structured, machine-readable format
                  </Text>
                </View>

                <View style={{ marginBottom: 12, padding: 12, borderWidth: 1, borderColor: colors.border, borderRadius: 8 }}>
                  <Text style={[styles.label, { marginBottom: 4 }]}>Right to Object (Article 21)</Text>
                  <Text style={{ fontSize: 12, color: colors.text }}>
                    You can object to certain types of data processing
                  </Text>
                </View>

                <View style={{ backgroundColor: colors.card, padding: 12, borderRadius: 8, marginTop: 16 }}>
                  <Text style={[styles.label, { marginBottom: 8 }]}>Contact Information</Text>
                  <Text style={{ fontSize: 12, color: colors.text }}>Privacy Officer: privacy@example.com</Text>
                  <Text style={{ fontSize: 12, color: colors.text }}>Data Protection Officer: dpo@example.com</Text>
                  <Text style={{ fontSize: 12, color: colors.text }}>Phone: +1-555-PRIVACY</Text>
                </View>
              </ScrollView>

              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={[styles.modalButton, styles.outlineButton]}
                  onPress={() => setShowRightsModal(false)}
                >
                  <Text style={styles.outlineButtonText}>Close</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.modalButton, styles.button]}
                  onPress={() => {
                    // Open external link
                    Share.share({
                      message: 'Learn more about GDPR: https://gdpr.eu/',
                      url: 'https://gdpr.eu/',
                      title: 'GDPR Information'
                    });
                  }}
                >
                  <Text style={styles.buttonText}>Learn More</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

export default GDPRPrivacyDashboard;