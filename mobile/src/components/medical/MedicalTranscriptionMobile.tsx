/**
 * Medical Transcription Mobile - Task 129 React Native Implementation
 * HIPAA-compliant medical transcription optimized for mobile devices
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  ActivityIndicator,
  Alert,
  Modal,
  FlatList,
  Switch,
  Dimensions,
  SafeAreaView,
  RefreshControl
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Picker } from '@react-native-picker/picker';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// Types (enhanced for comprehensive schema)
interface MedicalEntity {
  text: string;
  entity_type: 'symptom' | 'medication' | 'procedure' | 'diagnosis' | 'anatomy' | 'dosage' | 'measurement' | 'condition' | 'provider' | 'facility' | 'vital_sign' | 'test_result' | 'voice_biomarker' | 'ambient_sound' | 'emotion' | 'social_determinant';
  confidence: number;
  start_pos: number;
  end_pos: number;
  normalized_form: string;
  medical_code?: string;
  context?: string;
  severity?: string;
  category?: string;
  subcategory?: string;
  value?: string | number;
  unit?: string;
  timestamp?: string;
}

interface HIPAAViolation {
  violation_type: string;
  text: string;
  position: [number, number];
  severity: 'high' | 'medium' | 'low';
  recommendation: string;
}

interface MedicalReport {
  report_id: string;
  patient_id: string;
  provider_id: string;
  transcript_id: string;
  report_type: string;
  sections: Record<string, string>;
  entities: MedicalEntity[];
  medications: Array<{
    name: string;
    normalized_name: string;
    confidence: number;
    context?: string;
    medical_code?: string;
  }>;
  procedures: Array<{
    name: string;
    normalized_name: string;
    confidence: number;
    context?: string;
    medical_code?: string;
  }>;
  diagnoses: Array<{
    name: string;
    normalized_name: string;
    confidence: number;
    context?: string;
    medical_code?: string;
  }>;
  created_at: string;
  compliance_status: string;
}

interface ProcessingResult {
  success: boolean;
  processing_id?: string;
  report_id?: string;
  entities?: MedicalEntity[];
  sections?: Record<string, string>;
  phi_violations?: HIPAAViolation[];
  compliance_status?: string;
  medications?: MedicalReport['medications'];
  procedures?: MedicalReport['procedures'];
  diagnoses?: MedicalReport['diagnoses'];
  vital_signs?: Array<{
    type: string;
    value: number;
    unit: string;
    timestamp?: string;
    interpretation?: string;
  }>;
  test_results?: Array<{
    test_name: string;
    value: string;
    reference_range?: string;
    interpretation?: string;
    abnormal?: boolean;
  }>;
  voice_biomarkers?: Array<{
    biomarker_type: string;
    value: number;
    interpretation: string;
    confidence: number;
  }>;
  ambient_sounds?: Array<{
    sound_type: string;
    duration: number;
    context: string;
    clinical_relevance?: string;
  }>;
  emotional_state?: Array<{
    emotion: string;
    intensity: number;
    context: string;
    timestamp?: string;
  }>;
  social_determinants?: Array<{
    category: string;
    factor: string;
    impact_level: string;
    notes?: string;
  }>;
  comprehensive_analysis?: {
    patient_engagement_score: number;
    care_quality_indicators: Array<{
      indicator: string;
      status: 'excellent' | 'good' | 'needs_improvement' | 'concerning';
      details: string;
    }>;
    clinical_decision_support: Array<{
      recommendation: string;
      evidence_level: string;
      priority: 'high' | 'medium' | 'low';
    }>;
  };
  error?: string;
}

type HIPAAComplianceLevel = 'strict' | 'standard' | 'research';

export const MedicalTranscriptionMobile: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState<'transcription' | 'reports' | 'compliance' | 'settings'>('transcription');
  const [transcriptText, setTranscriptText] = useState('');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [currentResult, setCurrentResult] = useState<ProcessingResult | null>(null);
  const [complianceLevel, setComplianceLevel] = useState<HIPAAComplianceLevel>('standard');
  const [reports, setReports] = useState<MedicalReport[]>([]);
  
  // Modal states
  const [showPHIModal, setShowPHIModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [selectedReport, setSelectedReport] = useState<MedicalReport | null>(null);

  // Form state
  const [metadata, setMetadata] = useState({
    patient_id: `PATIENT_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`,
    provider_id: 'DR_ATTENDING',
    report_type: 'consultation' as 'consultation' | 'progress_note' | 'discharge_summary',
    transcript_id: `TRANS_${Math.random().toString(36).substring(2, 10)}`
  });

  // Sample medical transcript
  const sampleTranscript = `Patient presents with chief complaint of chest pain.

History of Present Illness:
Patient reports onset of sharp chest pain 2 hours ago, radiating to left arm. Associated with shortness of breath and nausea.

Physical Examination:
BP 140/90, HR 95, RR 18, Temp 98.6F
Heart: Regular rate and rhythm
Lungs: Clear bilaterally

Assessment and Plan:
1. Chest pain - rule out MI
   - EKG ordered
   - Cardiac enzymes
   - Aspirin 325mg
2. Hypertension
   - Consider lisinopril 5mg bid

Follow up in 24 hours.`;

  // Process medical transcription
  const processTranscription = useCallback(async () => {
    if (!transcriptText.trim()) {
      Alert.alert('Error', 'Please enter transcript text to process.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/medical/process-transcription-mobile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript_text: transcriptText,
          metadata: {
            ...metadata,
            user_id: 'mobile_user'
          },
          compliance_level: complianceLevel
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process transcription');
      }

      const result: ProcessingResult = await response.json();
      setCurrentResult(result);

      // Add to reports if successful
      if (result.success && result.report_id) {
        const newReport: MedicalReport = {
          report_id: result.report_id,
          patient_id: metadata.patient_id,
          provider_id: metadata.provider_id,
          transcript_id: metadata.transcript_id,
          report_type: metadata.report_type,
          sections: result.sections || {},
          entities: result.entities || [],
          medications: result.medications || [],
          procedures: result.procedures || [],
          diagnoses: result.diagnoses || [],
          created_at: new Date().toISOString(),
          compliance_status: result.compliance_status || 'pending_review'
        };
        setReports(prev => [newReport, ...prev]);
      }

      if (result.success) {
        Alert.alert('Success', 'Transcript processed successfully!');
      } else {
        Alert.alert('Error', result.error || 'Processing failed');
      }
    } catch (error) {
      console.error('Error processing transcription:', error);
      Alert.alert('Error', 'Failed to process transcription. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [transcriptText, metadata, complianceLevel]);

  // Refresh reports
  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    // Simulate refresh delay
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  }, []);

  // Render transcription tab
  const renderTranscriptionTab = () => (
    <ScrollView 
      style={styles.tabContent}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Header */}
      <View style={styles.headerCard}>
        <View style={styles.headerContent}>
          <Icon name="local-hospital" size={32} color="#fff" />
          <View style={styles.headerText}>
            <Text style={styles.headerTitle}>Medical Transcription</Text>
            <Text style={styles.headerSubtitle}>HIPAA-compliant processing</Text>
          </View>
        </View>
      </View>

      {/* Configuration */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Configuration</Text>
        
        <View style={styles.configGrid}>
          <View style={styles.configItem}>
            <Text style={styles.configLabel}>Compliance Level</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={complianceLevel}
                onValueChange={(value) => setComplianceLevel(value)}
                style={styles.picker}
              >
                <Picker.Item label="🔒 Strict" value="strict" />
                <Picker.Item label="🛡️ Standard" value="standard" />
                <Picker.Item label="📊 Research" value="research" />
              </Picker>
            </View>
          </View>

          <View style={styles.configItem}>
            <Text style={styles.configLabel}>Report Type</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={metadata.report_type}
                onValueChange={(value) => setMetadata(prev => ({ ...prev, report_type: value }))}
                style={styles.picker}
              >
                <Picker.Item label="👨‍⚕️ Consultation" value="consultation" />
                <Picker.Item label="📝 Progress Note" value="progress_note" />
                <Picker.Item label="🏠 Discharge Summary" value="discharge_summary" />
              </Picker>
            </View>
          </View>
        </View>

        <View style={styles.inputRow}>
          <View style={styles.inputHalf}>
            <Text style={styles.inputLabel}>Patient ID</Text>
            <TextInput
              style={styles.textInput}
              value={metadata.patient_id}
              onChangeText={(text) => setMetadata(prev => ({ ...prev, patient_id: text }))}
              placeholder="Patient identifier"
            />
          </View>
          
          <View style={styles.inputHalf}>
            <Text style={styles.inputLabel}>Provider ID</Text>
            <TextInput
              style={styles.textInput}
              value={metadata.provider_id}
              onChangeText={(text) => setMetadata(prev => ({ ...prev, provider_id: text }))}
              placeholder="Provider identifier"
            />
          </View>
        </View>
      </View>

      {/* Transcript Input */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Medical Transcript</Text>
        
        <TextInput
          style={styles.transcriptInput}
          value={transcriptText}
          onChangeText={setTranscriptText}
          placeholder="Enter or paste medical transcript here..."
          multiline
          textAlignVertical="top"
        />
        
        <View style={styles.transcriptActions}>
          <View style={styles.transcriptInfo}>
            <Text style={styles.characterCount}>{transcriptText.length} characters</Text>
          </View>
          
          <View style={styles.transcriptButtons}>
            <TouchableOpacity
              style={styles.sampleButton}
              onPress={() => setTranscriptText(sampleTranscript)}
            >
              <Icon name="description" size={16} color="#007AFF" />
              <Text style={styles.sampleButtonText}>Sample</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.clearButton}
              onPress={() => setTranscriptText('')}
            >
              <Icon name="clear" size={16} color="#FF3B30" />
              <Text style={styles.clearButtonText}>Clear</Text>
            </TouchableOpacity>
          </View>
        </View>
        
        <TouchableOpacity
          style={[styles.processButton, (!transcriptText.trim() || loading) && styles.processButtonDisabled]}
          onPress={processTranscription}
          disabled={!transcriptText.trim() || loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Icon name="play-arrow" size={20} color="#fff" />
          )}
          <Text style={styles.processButtonText}>
            {loading ? 'Processing...' : 'Process Transcript'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Results */}
      {currentResult && (
        <View style={styles.card}>
          {currentResult.success ? (
            <>
              {/* Success Header */}
              <View style={styles.successHeader}>
                <Icon name="check-circle" size={24} color="#34C759" />
                <Text style={styles.successText}>Processing Successful</Text>
              </View>

              {/* PHI Alert */}
              {currentResult.phi_violations && currentResult.phi_violations.length > 0 && (
                <TouchableOpacity
                  style={styles.phiAlert}
                  onPress={() => setShowPHIModal(true)}
                >
                  <View style={styles.phiAlertContent}>
                    <Icon name="warning" size={20} color="#FF9500" />
                    <Text style={styles.phiAlertText}>
                      PHI Detected ({currentResult.phi_violations.length})
                    </Text>
                  </View>
                  <Icon name="chevron-right" size={20} color="#FF9500" />
                </TouchableOpacity>
              )}

              {/* Clinical Summary */}
              <View style={styles.clinicalSummary}>
                <Text style={styles.clinicalTitle}>Clinical Summary</Text>
                
                <View style={styles.summaryGrid}>
                  {currentResult.medications && currentResult.medications.length > 0 && (
                    <View style={styles.summaryItem}>
                      <Icon name="local-pharmacy" size={20} color="#007AFF" />
                      <Text style={styles.summaryLabel}>Medications</Text>
                      <Text style={styles.summaryCount}>{currentResult.medications.length}</Text>
                    </View>
                  )}
                  
                  {currentResult.procedures && currentResult.procedures.length > 0 && (
                    <View style={styles.summaryItem}>
                      <Icon name="science" size={20} color="#34C759" />
                      <Text style={styles.summaryLabel}>Procedures</Text>
                      <Text style={styles.summaryCount}>{currentResult.procedures.length}</Text>
                    </View>
                  )}
                  
                  {currentResult.diagnoses && currentResult.diagnoses.length > 0 && (
                    <View style={styles.summaryItem}>
                      <Icon name="favorite" size={20} color="#FF3B30" />
                      <Text style={styles.summaryLabel}>Diagnoses</Text>
                      <Text style={styles.summaryCount}>{currentResult.diagnoses.length}</Text>
                    </View>
                  )}
                </View>

                {/* Comprehensive Analysis Summary - Mobile */}
                {currentResult.comprehensive_analysis && (
                  <View style={styles.analysisCard}>
                    <Text style={styles.analysisTitle}>Clinical Analysis</Text>
                    <View style={styles.analysisMetrics}>
                      <View style={styles.analysisMetric}>
                        <Text style={styles.analysisScore}>
                          {currentResult.comprehensive_analysis.patient_engagement_score.toFixed(1)}
                        </Text>
                        <Text style={styles.analysisLabel}>Engagement Score</Text>
                      </View>
                      <View style={styles.analysisMetric}>
                        <Text style={styles.analysisScore}>
                          {currentResult.comprehensive_analysis.care_quality_indicators.filter(i => i.status === 'excellent').length}
                        </Text>
                        <Text style={styles.analysisLabel}>Excellent Indicators</Text>
                      </View>
                      <View style={styles.analysisMetric}>
                        <Text style={styles.analysisScore}>
                          {currentResult.comprehensive_analysis.clinical_decision_support.filter(r => r.priority === 'high').length}
                        </Text>
                        <Text style={styles.analysisLabel}>High Priority</Text>
                      </View>
                    </View>
                  </View>
                )}

                {/* Advanced Clinical Data Grid - Mobile */}
                <View style={styles.advancedDataGrid}>
                  {/* Vital Signs */}
                  {currentResult.vital_signs && currentResult.vital_signs.length > 0 && (
                    <View style={styles.summaryItem}>
                      <Icon name="monitor" size={20} color="#5856D6" />
                      <Text style={styles.summaryLabel}>Vital Signs</Text>
                      <Text style={styles.summaryCount}>{currentResult.vital_signs.length}</Text>
                    </View>
                  )}

                  {/* Voice Biomarkers */}
                  {currentResult.voice_biomarkers && currentResult.voice_biomarkers.length > 0 && (
                    <View style={styles.summaryItem}>
                      <Icon name="graphic-eq" size={20} color="#AF52DE" />
                      <Text style={styles.summaryLabel}>Voice Biomarkers</Text>
                      <Text style={styles.summaryCount}>{currentResult.voice_biomarkers.length}</Text>
                    </View>
                  )}

                  {/* Emotional State */}
                  {currentResult.emotional_state && currentResult.emotional_state.length > 0 && (
                    <View style={styles.summaryItem}>
                      <Icon name="sentiment-satisfied" size={20} color="#FF2D92" />
                      <Text style={styles.summaryLabel}>Emotions</Text>
                      <Text style={styles.summaryCount}>{currentResult.emotional_state.length}</Text>
                    </View>
                  )}

                  {/* Test Results */}
                  {currentResult.test_results && currentResult.test_results.length > 0 && (
                    <View style={styles.summaryItem}>
                      <Icon name="biotech" size={20} color="#30D158" />
                      <Text style={styles.summaryLabel}>Lab Results</Text>
                      <Text style={styles.summaryCount}>{currentResult.test_results.length}</Text>
                    </View>
                  )}

                  {/* Social Determinants */}
                  {currentResult.social_determinants && currentResult.social_determinants.length > 0 && (
                    <View style={styles.summaryItem}>
                      <Icon name="people" size={20} color="#32D74B" />
                      <Text style={styles.summaryLabel}>Social Factors</Text>
                      <Text style={styles.summaryCount}>{currentResult.social_determinants.length}</Text>
                    </View>
                  )}

                  {/* Ambient Sounds */}
                  {currentResult.ambient_sounds && currentResult.ambient_sounds.length > 0 && (
                    <View style={styles.summaryItem}>
                      <Icon name="hearing" size={20} color="#FF9500" />
                      <Text style={styles.summaryLabel}>Ambient Context</Text>
                      <Text style={styles.summaryCount}>{currentResult.ambient_sounds.length}</Text>
                    </View>
                  )}
                </View>

                {/* High Priority Clinical Recommendations - Mobile */}
                {currentResult.comprehensive_analysis && currentResult.comprehensive_analysis.clinical_decision_support.filter(r => r.priority === 'high').length > 0 && (
                  <View style={styles.priorityRecommendations}>
                    <Text style={styles.priorityTitle}>High Priority Recommendations</Text>
                    {currentResult.comprehensive_analysis.clinical_decision_support.filter(r => r.priority === 'high').map((rec, index) => (
                      <View key={index} style={styles.priorityItem}>
                        <Icon name="priority-high" size={16} color="#FF3B30" />
                        <Text style={styles.priorityText}>{rec.recommendation}</Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>

              {/* Compliance Status */}
              <View style={[
                styles.complianceStatus,
                currentResult.compliance_status === 'compliant' ? styles.complianceGood :
                currentResult.compliance_status === 'pending_review' ? styles.complianceWarning :
                styles.complianceError
              ]}>
                <Icon
                  name={
                    currentResult.compliance_status === 'compliant' ? 'verified' :
                    currentResult.compliance_status === 'pending_review' ? 'schedule' :
                    'error'
                  }
                  size={20}
                  color={
                    currentResult.compliance_status === 'compliant' ? '#34C759' :
                    currentResult.compliance_status === 'pending_review' ? '#FF9500' :
                    '#FF3B30'
                  }
                />
                <Text style={[
                  styles.complianceText,
                  currentResult.compliance_status === 'compliant' ? styles.complianceTextGood :
                  currentResult.compliance_status === 'pending_review' ? styles.complianceTextWarning :
                  styles.complianceTextError
                ]}>
                  {currentResult.compliance_status === 'compliant' ? 'HIPAA Compliant' :
                   currentResult.compliance_status === 'pending_review' ? 'Pending Review' :
                   'Compliance Issue'}
                </Text>
              </View>
            </>
          ) : (
            /* Error Display */
            <View style={styles.errorContainer}>
              <Icon name="error" size={24} color="#FF3B30" />
              <Text style={styles.errorText}>Processing Failed</Text>
              <Text style={styles.errorDetail}>{currentResult.error}</Text>
            </View>
          )}
        </View>
      )}
    </ScrollView>
  );

  // Render reports tab
  const renderReportsTab = () => (
    <View style={styles.tabContent}>
      <View style={styles.reportsHeader}>
        <Text style={styles.reportsTitle}>Medical Reports ({reports.length})</Text>
        <TouchableOpacity onPress={onRefresh}>
          <Icon name="refresh" size={24} color="#007AFF" />
        </TouchableOpacity>
      </View>
      
      {reports.length === 0 ? (
        <View style={styles.emptyState}>
          <Icon name="description" size={64} color="#C7C7CC" />
          <Text style={styles.emptyStateText}>No reports generated yet</Text>
          <Text style={styles.emptyStateSubtext}>Process a transcript to create your first report</Text>
        </View>
      ) : (
        <FlatList
          data={reports}
          keyExtractor={(item) => item.report_id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.reportItem}
              onPress={() => {
                setSelectedReport(item);
                setShowReportModal(true);
              }}
            >
              <View style={styles.reportHeader}>
                <Text style={styles.reportTitle}>
                  {item.patient_id} - {item.report_type.replace('_', ' ').toUpperCase()}
                </Text>
                <View style={[
                  styles.complianceBadge,
                  item.compliance_status === 'compliant' ? styles.badgeGreen :
                  item.compliance_status === 'pending_review' ? styles.badgeYellow :
                  styles.badgeRed
                ]}>
                  <Text style={styles.badgeText}>{item.compliance_status}</Text>
                </View>
              </View>
              
              <Text style={styles.reportMeta}>
                Provider: {item.provider_id} • {new Date(item.created_at).toLocaleDateString()}
              </Text>
              
              <View style={styles.reportStats}>
                <Text style={styles.reportStat}>{item.entities.length} entities</Text>
                <Text style={styles.reportStat}>{item.medications.length} medications</Text>
                <Text style={styles.reportStat}>{item.procedures.length} procedures</Text>
                <Text style={styles.reportStat}>{item.diagnoses.length} diagnoses</Text>
              </View>
              
              <Icon name="chevron-right" size={20} color="#C7C7CC" style={styles.reportChevron} />
            </TouchableOpacity>
          )}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        />
      )}
    </View>
  );

  // Render compliance tab
  const renderComplianceTab = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>HIPAA Compliance Dashboard</Text>
        
        <View style={styles.complianceMetrics}>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>{reports.length}</Text>
            <Text style={styles.metricLabel}>Total Reports</Text>
          </View>
          
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>
              {reports.filter(r => r.compliance_status === 'compliant').length}
            </Text>
            <Text style={styles.metricLabel}>Compliant</Text>
          </View>
          
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>
              {reports.filter(r => r.compliance_status === 'pending_review').length}
            </Text>
            <Text style={styles.metricLabel}>Pending Review</Text>
          </View>
        </View>
        
        <View style={styles.complianceInfo}>
          <Text style={styles.complianceInfoTitle}>Current Compliance Level</Text>
          <Text style={styles.complianceInfoValue}>
            {complianceLevel === 'strict' ? '🔒 Strict' :
             complianceLevel === 'standard' ? '🛡️ Standard' :
             '📊 Research'}
          </Text>
          <Text style={styles.complianceInfoDesc}>
            {complianceLevel === 'strict' ? 'No PHI allowed in transcripts' :
             complianceLevel === 'standard' ? 'PHI automatically anonymized' :
             'Limited PHI allowed for research purposes'}
          </Text>
        </View>
      </View>
    </ScrollView>
  );

  // Render settings tab
  const renderSettingsTab = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Settings</Text>
        
        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>HIPAA Compliance Level</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={complianceLevel}
              onValueChange={(value) => setComplianceLevel(value)}
              style={styles.picker}
            >
              <Picker.Item label="🔒 Strict (No PHI)" value="strict" />
              <Picker.Item label="🛡️ Standard (PHI anonymized)" value="standard" />
              <Picker.Item label="📊 Research (Limited PHI)" value="research" />
            </Picker>
          </View>
        </View>
        
        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>Default Provider ID</Text>
          <TextInput
            style={styles.textInput}
            value={metadata.provider_id}
            onChangeText={(text) => setMetadata(prev => ({ ...prev, provider_id: text }))}
            placeholder="Enter default provider ID"
          />
        </View>
        
        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>Auto-generate Patient IDs</Text>
          <Switch
            value={true}
            onValueChange={() => {}}
            trackColor={{ false: '#767577', true: '#81b0ff' }}
            thumbColor="#f5dd4b"
          />
        </View>
      </View>
    </ScrollView>
  );

  // PHI Modal
  const renderPHIModal = () => (
    <Modal
      visible={showPHIModal}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <SafeAreaView style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>PHI Detection Details</Text>
          <TouchableOpacity onPress={() => setShowPHIModal(false)}>
            <Icon name="close" size={24} color="#007AFF" />
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.modalContent}>
          {currentResult?.phi_violations?.map((violation, index) => (
            <View key={index} style={styles.violationItem}>
              <View style={styles.violationHeader}>
                <Text style={styles.violationType}>{violation.violation_type}</Text>
                <View style={[
                  styles.severityBadge,
                  violation.severity === 'high' ? styles.severityHigh :
                  violation.severity === 'medium' ? styles.severityMedium :
                  styles.severityLow
                ]}>
                  <Text style={styles.severityText}>{violation.severity}</Text>
                </View>
              </View>
              
              <Text style={styles.violationText}>Text: {violation.text}</Text>
              <Text style={styles.violationRecommendation}>
                Recommendation: {violation.recommendation}
              </Text>
            </View>
          ))}
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );

  // Report Detail Modal
  const renderReportModal = () => (
    <Modal
      visible={showReportModal}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <SafeAreaView style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Medical Report</Text>
          <TouchableOpacity onPress={() => setShowReportModal(false)}>
            <Icon name="close" size={24} color="#007AFF" />
          </TouchableOpacity>
        </View>
        
        {selectedReport && (
          <ScrollView style={styles.modalContent}>
            <View style={styles.reportDetailHeader}>
              <Text style={styles.reportDetailTitle}>
                {selectedReport.patient_id} - {selectedReport.report_type.replace('_', ' ').toUpperCase()}
              </Text>
              <Text style={styles.reportDetailMeta}>
                Provider: {selectedReport.provider_id}
              </Text>
              <Text style={styles.reportDetailMeta}>
                Created: {new Date(selectedReport.created_at).toLocaleString()}
              </Text>
            </View>
            
            {/* Report Sections */}
            {Object.entries(selectedReport.sections).map(([sectionName, content]) => (
              content.trim() && (
                <View key={sectionName} style={styles.reportSection}>
                  <Text style={styles.reportSectionTitle}>
                    {sectionName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </Text>
                  <Text style={styles.reportSectionContent}>{content}</Text>
                </View>
              )
            ))}
          </ScrollView>
        )}
      </SafeAreaView>
    </Modal>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Tab Navigation */}
      <View style={styles.tabBar}>
        {[
          { id: 'transcription', label: 'Transcription', icon: 'local-hospital' },
          { id: 'reports', label: 'Reports', icon: 'description' },
          { id: 'compliance', label: 'Compliance', icon: 'verified-user' },
          { id: 'settings', label: 'Settings', icon: 'settings' }
        ].map((tab) => (
          <TouchableOpacity
            key={tab.id}
            style={[styles.tab, activeTab === tab.id && styles.activeTab]}
            onPress={() => setActiveTab(tab.id as any)}
          >
            <Icon
              name={tab.icon}
              size={20}
              color={activeTab === tab.id ? '#007AFF' : '#8E8E93'}
            />
            <Text style={[
              styles.tabLabel,
              activeTab === tab.id && styles.activeTabLabel
            ]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Tab Content */}
      {activeTab === 'transcription' && renderTranscriptionTab()}
      {activeTab === 'reports' && renderReportsTab()}
      {activeTab === 'compliance' && renderComplianceTab()}
      {activeTab === 'settings' && renderSettingsTab()}

      {/* Modals */}
      {renderPHIModal()}
      {renderReportModal()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    paddingVertical: 8,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
  },
  activeTab: {
    backgroundColor: '#E3F2FD',
    borderRadius: 8,
    marginHorizontal: 4,
  },
  tabLabel: {
    fontSize: 10,
    color: '#8E8E93',
    marginTop: 2,
  },
  activeTabLabel: {
    color: '#007AFF',
    fontWeight: '600',
  },
  tabContent: {
    flex: 1,
    padding: 16,
  },
  headerCard: {
    backgroundColor: 'linear-gradient(135deg, #2E8B57 0%, #228B22 100%)',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerText: {
    marginLeft: 16,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.9,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 16,
  },
  configGrid: {
    marginBottom: 16,
  },
  configItem: {
    marginBottom: 16,
  },
  configLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#3C3C43',
    marginBottom: 8,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#D1D1D6',
    borderRadius: 8,
    backgroundColor: '#F9F9F9',
  },
  picker: {
    height: 44,
  },
  inputRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  inputHalf: {
    flex: 0.48,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#3C3C43',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#D1D1D6',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#F9F9F9',
  },
  transcriptInput: {
    borderWidth: 1,
    borderColor: '#D1D1D6',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    height: 120,
    backgroundColor: '#F9F9F9',
    textAlignVertical: 'top',
  },
  transcriptActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    marginBottom: 16,
  },
  transcriptInfo: {
    flex: 1,
  },
  characterCount: {
    fontSize: 12,
    color: '#8E8E93',
  },
  transcriptButtons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sampleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 12,
  },
  sampleButtonText: {
    fontSize: 14,
    color: '#007AFF',
    marginLeft: 4,
  },
  clearButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  clearButtonText: {
    fontSize: 14,
    color: '#FF3B30',
    marginLeft: 4,
  },
  processButton: {
    backgroundColor: '#34C759',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 8,
  },
  processButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  processButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  successHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  successText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#34C759',
    marginLeft: 8,
  },
  phiAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFF3CD',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  phiAlertContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  phiAlertText: {
    fontSize: 14,
    color: '#B45309',
    marginLeft: 8,
  },
  clinicalSummary: {
    marginBottom: 16,
  },
  clinicalTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 12,
  },
  summaryGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  summaryItem: {
    alignItems: 'center',
    flex: 1,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 4,
  },
  summaryCount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1D1D1F',
    marginTop: 2,
  },
  complianceStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
  },
  complianceGood: {
    backgroundColor: '#D4EDDA',
  },
  complianceWarning: {
    backgroundColor: '#FFF3CD',
  },
  complianceError: {
    backgroundColor: '#F8D7DA',
  },
  complianceText: {
    fontSize: 14,
    fontWeight: '500',
    marginLeft: 8,
  },
  complianceTextGood: {
    color: '#155724',
  },
  complianceTextWarning: {
    color: '#856404',
  },
  complianceTextError: {
    color: '#721C24',
  },
  errorContainer: {
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF3B30',
    marginTop: 8,
  },
  errorDetail: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 4,
    textAlign: 'center',
  },
  reportsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  reportsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1D1D1F',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '500',
    color: '#8E8E93',
    marginTop: 16,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#C7C7CC',
    marginTop: 8,
    textAlign: 'center',
  },
  reportItem: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    position: 'relative',
  },
  reportHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  reportTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    flex: 1,
  },
  complianceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeGreen: {
    backgroundColor: '#D4EDDA',
  },
  badgeYellow: {
    backgroundColor: '#FFF3CD',
  },
  badgeRed: {
    backgroundColor: '#F8D7DA',
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  reportMeta: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 8,
  },
  reportStats: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  reportStat: {
    fontSize: 12,
    color: '#8E8E93',
    marginRight: 16,
  },
  reportChevron: {
    position: 'absolute',
    right: 16,
    top: '50%',
    marginTop: -10,
  },
  complianceMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 24,
  },
  metricCard: {
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  metricLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 4,
  },
  complianceInfo: {
    backgroundColor: '#F2F2F7',
    borderRadius: 8,
    padding: 16,
  },
  complianceInfoTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 8,
  },
  complianceInfoValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 4,
  },
  complianceInfoDesc: {
    fontSize: 12,
    color: '#8E8E93',
  },
  settingItem: {
    marginBottom: 24,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1D1D1F',
    marginBottom: 8,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  violationItem: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  violationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  violationType: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  severityHigh: {
    backgroundColor: '#F8D7DA',
  },
  severityMedium: {
    backgroundColor: '#FFF3CD',
  },
  severityLow: {
    backgroundColor: '#D1ECF1',
  },
  severityText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  violationText: {
    fontSize: 14,
    color: '#3C3C43',
    marginBottom: 8,
  },
  violationRecommendation: {
    fontSize: 12,
    color: '#8E8E93',
  },
  reportDetailHeader: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  reportDetailTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1D1D1F',
    marginBottom: 8,
  },
  reportDetailMeta: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  reportSection: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  reportSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 8,
  },
  reportSectionContent: {
    fontSize: 14,
    color: '#3C3C43',
    lineHeight: 20,
  },
  // Comprehensive Analysis Styles
  analysisCard: {
    backgroundColor: '#F8F5FF',
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  analysisTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#5856D6',
    marginBottom: 12,
  },
  analysisMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  analysisMetric: {
    alignItems: 'center',
    flex: 1,
  },
  analysisScore: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#5856D6',
  },
  analysisLabel: {
    fontSize: 11,
    color: '#8E8E93',
    marginTop: 4,
    textAlign: 'center',
  },
  // Advanced Data Grid Styles
  advancedDataGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    marginTop: 16,
    padding: 12,
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
  },
  // Priority Recommendations Styles
  priorityRecommendations: {
    backgroundColor: '#FFF5F5',
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#FF3B30',
  },
  priorityTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF3B30',
    marginBottom: 12,
  },
  priorityItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
    paddingHorizontal: 8,
  },
  priorityText: {
    fontSize: 14,
    color: '#1D1D1F',
    flex: 1,
    marginLeft: 8,
    lineHeight: 20,
  },
});

export default MedicalTranscriptionMobile;