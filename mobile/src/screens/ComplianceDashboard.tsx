import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  FlatList,
  Alert,
  Switch,
} from 'react-native';
import { Card, Button, Badge, ListItem, ProgressBar } from 'react-native-elements';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient } from '../services/apiClient';

interface ComplianceData {
  compliance_score: number;
  active_scans: number;
  vulnerabilities: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  certifications: Array<{
    name: string;
    status: string;
    expiry_date: string;
  }>;
  recent_audits: Array<{
    id: string;
    type: string;
    date: string;
    status: string;
    findings: number;
  }>;
}

const ComplianceDashboard: React.FC = () => {
  const [complianceData, setComplianceData] = useState<ComplianceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'certifications' | 'audits'>('overview');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getComplianceStatus();
      setComplianceData(data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load compliance data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return '#27ae60';
    if (score >= 70) return '#f39c12';
    return '#e74c3c';
  };

  const renderOverview = () => {
    if (!complianceData) return null;

    return (
      <ScrollView style={styles.overviewContainer}>
        <Card containerStyle={styles.scoreCard}>
          <Text style={styles.cardTitle}>Compliance Score</Text>
          <View style={styles.scoreContainer}>
            <View style={styles.scoreCircle}>
              <Text style={[styles.scoreValue, { color: getScoreColor(complianceData.compliance_score) }]}>
                {complianceData.compliance_score}%
              </Text>
            </View>
            <View style={styles.scoreDetails}>
              <Text style={styles.scoreLabel}>Overall Compliance</Text>
              <ProgressBar
                progress={complianceData.compliance_score / 100}
                color={getScoreColor(complianceData.compliance_score)}
                style={styles.progressBar}
              />
            </View>
          </View>
        </Card>

        <Card containerStyle={styles.vulnerabilitiesCard}>
          <Text style={styles.cardTitle}>Security Vulnerabilities</Text>
          <View style={styles.vulnerabilitiesGrid}>
            <View style={[styles.vulnItem, { backgroundColor: '#fee' }]}>
              <Text style={[styles.vulnCount, { color: '#e74c3c' }]}>
                {complianceData.vulnerabilities.critical}
              </Text>
              <Text style={styles.vulnLabel}>Critical</Text>
            </View>
            <View style={[styles.vulnItem, { backgroundColor: '#fef5e7' }]}>
              <Text style={[styles.vulnCount, { color: '#f39c12' }]}>
                {complianceData.vulnerabilities.high}
              </Text>
              <Text style={styles.vulnLabel}>High</Text>
            </View>
            <View style={[styles.vulnItem, { backgroundColor: '#fef9e7' }]}>
              <Text style={[styles.vulnCount, { color: '#f1c40f' }]}>
                {complianceData.vulnerabilities.medium}
              </Text>
              <Text style={styles.vulnLabel}>Medium</Text>
            </View>
            <View style={[styles.vulnItem, { backgroundColor: '#eafaf1' }]}>
              <Text style={[styles.vulnCount, { color: '#27ae60' }]}>
                {complianceData.vulnerabilities.low}
              </Text>
              <Text style={styles.vulnLabel}>Low</Text>
            </View>
          </View>
        </Card>

        <Card containerStyle={styles.scanCard}>
          <View style={styles.scanHeader}>
            <Text style={styles.cardTitle}>Active Security Scans</Text>
            <Badge
              value={complianceData.active_scans}
              badgeStyle={styles.scanBadge}
              textStyle={styles.scanBadgeText}
            />
          </View>
          <Button
            title="Run Security Scan"
            icon={<Icon name="security" size={20} color="white" style={{ marginRight: 10 }} />}
            buttonStyle={styles.scanButton}
            onPress={() => Alert.alert('Security Scan', 'Starting security scan...')}
          />
        </Card>
      </ScrollView>
    );
  };

  const renderCertifications = () => {
    if (!complianceData) return null;

    return (
      <FlatList
        data={complianceData.certifications}
        keyExtractor={(item, index) => `cert-${index}`}
        renderItem={({ item }) => {
          const isExpiringSoon = new Date(item.expiry_date) < new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
          
          return (
            <Card containerStyle={styles.certCard}>
              <View style={styles.certHeader}>
                <Icon 
                  name="verified-user" 
                  size={40} 
                  color={item.status === 'active' ? '#27ae60' : '#95a5a6'} 
                />
                <View style={styles.certInfo}>
                  <Text style={styles.certName}>{item.name}</Text>
                  <Badge
                    value={item.status}
                    badgeStyle={[
                      styles.certStatusBadge,
                      { backgroundColor: item.status === 'active' ? '#27ae60' : '#95a5a6' }
                    ]}
                    textStyle={styles.certStatusText}
                  />
                </View>
              </View>
              <View style={styles.certFooter}>
                <Text style={[styles.certExpiry, isExpiringSoon && styles.certExpiryWarning]}>
                  Expires: {new Date(item.expiry_date).toLocaleDateString()}
                </Text>
                {isExpiringSoon && (
                  <Icon name="warning" size={16} color="#f39c12" />
                )}
              </View>
            </Card>
          );
        }}
        contentContainerStyle={styles.certList}
      />
    );
  };

  const renderAudits = () => {
    if (!complianceData) return null;

    return (
      <FlatList
        data={complianceData.recent_audits}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Card containerStyle={styles.auditCard}>
            <View style={styles.auditHeader}>
              <View>
                <Text style={styles.auditType}>{item.type}</Text>
                <Text style={styles.auditDate}>
                  {new Date(item.date).toLocaleDateString()}
                </Text>
              </View>
              <View style={styles.auditStatus}>
                <Badge
                  value={item.status}
                  badgeStyle={[
                    styles.auditStatusBadge,
                    { backgroundColor: item.status === 'passed' ? '#27ae60' : '#e74c3c' }
                  ]}
                />
                {item.findings > 0 && (
                  <View style={styles.findingsBadge}>
                    <Text style={styles.findingsText}>{item.findings} findings</Text>
                  </View>
                )}
              </View>
            </View>
            <TouchableOpacity style={styles.auditAction}>
              <Text style={styles.auditActionText}>View Report</Text>
              <Icon name="chevron-right" size={20} color="#3498db" />
            </TouchableOpacity>
          </Card>
        )}
        contentContainerStyle={styles.auditList}
      />
    );
  };

  const renderTabs = () => (
    <View style={styles.tabContainer}>
      <TouchableOpacity
        style={[styles.tab, selectedTab === 'overview' && styles.activeTab]}
        onPress={() => setSelectedTab('overview')}
      >
        <Icon 
          name="dashboard" 
          size={20} 
          color={selectedTab === 'overview' ? '#3498db' : '#95a5a6'} 
        />
        <Text style={[styles.tabText, selectedTab === 'overview' && styles.activeTabText]}>
          Overview
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, selectedTab === 'certifications' && styles.activeTab]}
        onPress={() => setSelectedTab('certifications')}
      >
        <Icon 
          name="verified-user" 
          size={20} 
          color={selectedTab === 'certifications' ? '#3498db' : '#95a5a6'} 
        />
        <Text style={[styles.tabText, selectedTab === 'certifications' && styles.activeTabText]}>
          Certifications
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, selectedTab === 'audits' && styles.activeTab]}
        onPress={() => setSelectedTab('audits')}
      >
        <Icon 
          name="assignment" 
          size={20} 
          color={selectedTab === 'audits' ? '#3498db' : '#95a5a6'} 
        />
        <Text style={[styles.tabText, selectedTab === 'audits' && styles.activeTabText]}>
          Audits
        </Text>
      </TouchableOpacity>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#3498db" />
        <Text style={styles.loadingText}>Loading compliance data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
      >
        {renderTabs()}
        
        {selectedTab === 'overview' && renderOverview()}
        {selectedTab === 'certifications' && renderCertifications()}
        {selectedTab === 'audits' && renderAudits()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'white',
    elevation: 2,
    marginBottom: 15,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    gap: 5,
  },
  activeTab: {
    borderBottomWidth: 3,
    borderBottomColor: '#3498db',
  },
  tabText: {
    fontSize: 14,
    color: '#95a5a6',
  },
  activeTabText: {
    color: '#3498db',
    fontWeight: '600',
  },
  overviewContainer: {
    flex: 1,
  },
  scoreCard: {
    margin: 15,
    borderRadius: 10,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#2c3e50',
  },
  scoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  scoreCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 20,
  },
  scoreValue: {
    fontSize: 36,
    fontWeight: 'bold',
  },
  scoreDetails: {
    flex: 1,
  },
  scoreLabel: {
    fontSize: 16,
    color: '#7f8c8d',
    marginBottom: 10,
  },
  progressBar: {
    height: 10,
    borderRadius: 5,
  },
  vulnerabilitiesCard: {
    marginHorizontal: 15,
    marginBottom: 15,
    borderRadius: 10,
  },
  vulnerabilitiesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  vulnItem: {
    flex: 1,
    minWidth: '45%',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  vulnCount: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  vulnLabel: {
    fontSize: 14,
    color: '#7f8c8d',
    marginTop: 5,
  },
  scanCard: {
    marginHorizontal: 15,
    marginBottom: 15,
    borderRadius: 10,
  },
  scanHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  scanBadge: {
    backgroundColor: '#3498db',
    borderRadius: 15,
    paddingHorizontal: 12,
  },
  scanBadgeText: {
    fontSize: 14,
  },
  scanButton: {
    backgroundColor: '#3498db',
    borderRadius: 25,
    paddingVertical: 12,
  },
  certList: {
    padding: 15,
  },
  certCard: {
    marginBottom: 10,
    borderRadius: 10,
  },
  certHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  certInfo: {
    flex: 1,
    marginLeft: 15,
  },
  certName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 5,
  },
  certStatusBadge: {
    alignSelf: 'flex-start',
    borderRadius: 12,
    paddingHorizontal: 10,
  },
  certStatusText: {
    fontSize: 12,
    textTransform: 'uppercase',
  },
  certFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  certExpiry: {
    fontSize: 14,
    color: '#7f8c8d',
  },
  certExpiryWarning: {
    color: '#f39c12',
    fontWeight: '600',
  },
  auditList: {
    padding: 15,
  },
  auditCard: {
    marginBottom: 10,
    borderRadius: 10,
  },
  auditHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  auditType: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  auditDate: {
    fontSize: 14,
    color: '#7f8c8d',
    marginTop: 2,
  },
  auditStatus: {
    alignItems: 'flex-end',
  },
  auditStatusBadge: {
    borderRadius: 12,
    paddingHorizontal: 12,
  },
  findingsBadge: {
    marginTop: 5,
    backgroundColor: '#fef5e7',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  findingsText: {
    fontSize: 12,
    color: '#f39c12',
  },
  auditAction: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#ecf0f1',
  },
  auditActionText: {
    fontSize: 14,
    color: '#3498db',
  },
});

export default ComplianceDashboard;