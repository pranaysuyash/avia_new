import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  Modal,
  Switch,
  ActivityIndicator,
  StyleSheet,
  Dimensions
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import Icon from 'react-native-vector-icons/MaterialIcons';

const { width } = Dimensions.get('window');

interface MedicalEntity {
  text: string;
  entity_type: string;
  confidence: number;
  start_pos: number;
  end_pos: number;
  normalized_form: string;
  medical_code?: string;
  context?: string;
}

interface PHIViolation {
  violation_type: string;
  text: string;
  position: [number, number];
  severity: string;
  recommendation: string;
}

interface MedicalCode {
  code: string;
  description: string;
  confidence: number;
  category: string;
}

interface TranscriptionResult {
  transcript_id: string;
  original_text: string;
  anonymized_text: string;
  medical_entities: MedicalEntity[];
  phi_violations: PHIViolation[];
  medical_codes: {
    icd10_codes: MedicalCode[];
    cpt_codes: MedicalCode[];
  };
  compliance_score: number;
  processing_time: number;
  timestamp: string;
  compliance_status: string;
}

interface HIPAAMedicalTranscriptionMobileProps {
  onTranscriptionComplete?: (result: TranscriptionResult) => void;
}

const HIPAAMedicalTranscriptionMobile: React.FC<HIPAAMedicalTranscriptionMobileProps> = ({
  onTranscriptionComplete
}) => {
  const [transcriptText, setTranscriptText] = useState('');
  const [result, setResult] = useState<TranscriptionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('input');
  const [showOriginalText, setShowOriginalText] = useState(false);
  const [complianceLevel, setComplianceLevel] = useState('standard');
  const [enablePHIDetection, setEnablePHIDetection] = useState(true);
  const [enableMedicalCoding, setEnableMedicalCoding] = useState(true);
  const [enableAuditLogging, setEnableAuditLogging] = useState(true);
  const [settingsModalVisible, setSettingsModalVisible] = useState(false);
  const [complianceModalVisible, setComplianceModalVisible] = useState(false);

  const sampleTranscripts = {
    'Cardiology': `Patient: John Smith, DOB: 03/15/1975

Chief Complaint: Chest pain and shortness of breath

History: 48-year-old male with acute chest pain, radiating to left arm. 
History of hypertension and diabetes.

Exam: BP 160/95, HR 110, irregular rhythm

Assessment: Acute myocardial infarction
Plan: Aspirin, metoprolol, cardiology follow-up`,

    'Emergency': `Patient: Mary Johnson, Phone: 555-123-4567

Chief Complaint: Severe abdominal pain

HPI: 41-year-old female with sudden RUQ pain after fatty meal.
Associated nausea and vomiting.

Exam: Tender RUQ, positive Murphy's sign
Labs: WBC 12,000, bilirubin 2.5

Assessment: Acute cholecystitis
Plan: NPO, IV fluids, surgery consult`,

    'Progress Note': `Patient: Robert Davis, Room 302

Subjective: Feeling better, pain 4/10
Objective: VS stable, abdomen soft
Assessment: Post-op day 2, recovering well
Plan: Advance diet, PT, discharge planning`
  };

  const processTranscription = async () => {
    if (!transcriptText.trim()) {
      Alert.alert('Error', 'Please enter medical transcript text');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/v1/medical/transcribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await getAuthToken()}`
        },
        body: JSON.stringify({
          text: transcriptText,
          compliance_level: complianceLevel,
          enable_phi_detection: enablePHIDetection,
          enable_medical_coding: enableMedicalCoding,
          enable_audit_logging: enableAuditLogging
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: TranscriptionResult = await response.json();
      setResult(data);
      setActiveTab('results');
      onTranscriptionComplete?.(data);
    } catch (error) {
      Alert.alert('Error', error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getAuthToken = async (): Promise<string> => {
    // In a real app, retrieve from secure storage
    return 'demo_token';
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity.toLowerCase()) {
      case 'high':
      case 'critical':
        return '#f44336';
      case 'medium':
        return '#ff9800';
      case 'low':
        return '#2196f3';
      default:
        return '#757575';
    }
  };

  const getComplianceColor = (score: number): string => {
    if (score >= 0.9) return '#4caf50';
    if (score >= 0.7) return '#ff9800';
    return '#f44336';
  };

  const renderInputTab = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.header}>
        <Icon name="local-hospital" size={32} color="#1976d2" />
        <Text style={styles.title}>HIPAA Medical Transcription</Text>
      </View>

      <Text style={styles.subtitle}>
        Enterprise-grade medical transcription with HIPAA compliance
      </Text>

      {/* Settings Button */}
      <TouchableOpacity
        style={styles.settingsButton}
        onPress={() => setSettingsModalVisible(true)}
      >
        <Icon name="settings" size={20} color="#1976d2" />
        <Text style={styles.settingsButtonText}>Configuration</Text>
      </TouchableOpacity>

      {/* Sample Transcripts */}
      <Text style={styles.sectionTitle}>Sample Transcripts:</Text>
      <View style={styles.sampleButtons}>
        {Object.keys(sampleTranscripts).map((sampleName) => (
          <TouchableOpacity
            key={sampleName}
            style={styles.sampleButton}
            onPress={() => setTranscriptText(sampleTranscripts[sampleName as keyof typeof sampleTranscripts])}
          >
            <Text style={styles.sampleButtonText}>{sampleName}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Input Area */}
      <Text style={styles.inputLabel}>Medical Transcript:</Text>
      <TextInput
        style={styles.textInput}
        multiline
        numberOfLines={10}
        placeholder="Enter medical transcript text here..."
        value={transcriptText}
        onChangeText={setTranscriptText}
        textAlignVertical="top"
      />

      {/* Action Buttons */}
      <View style={styles.actionButtons}>
        <TouchableOpacity
          style={[styles.processButton, (!transcriptText.trim() || loading) && styles.disabledButton]}
          onPress={processTranscription}
          disabled={!transcriptText.trim() || loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Icon name="security" size={20} color="#fff" />
          )}
          <Text style={styles.processButtonText}>
            {loading ? 'Processing...' : 'Process with HIPAA'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.infoButton}
          onPress={() => setComplianceModalVisible(true)}
        >
          <Icon name="info" size={20} color="#1976d2" />
          <Text style={styles.infoButtonText}>Compliance Info</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  const renderResultsTab = () => {
    if (!result) return null;

    return (
      <ScrollView style={styles.tabContent}>
        <View style={styles.resultsHeader}>
          <Text style={styles.resultsTitle}>Processing Results</Text>
          <View style={styles.complianceScore}>
            <Text style={[styles.scoreText, { color: getComplianceColor(result.compliance_score) }]}>
              {(result.compliance_score * 100).toFixed(1)}%
            </Text>
            <Text style={styles.scoreLabel}>Compliance</Text>
          </View>
        </View>

        {/* Transcript Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Transcript</Text>
            <TouchableOpacity
              onPress={() => setShowOriginalText(!showOriginalText)}
              style={styles.toggleButton}
            >
              <Icon
                name={showOriginalText ? 'visibility-off' : 'visibility'}
                size={20}
                color="#1976d2"
              />
            </TouchableOpacity>
          </View>

          {showOriginalText ? (
            <View style={styles.textContainer}>
              <Text style={styles.textLabel}>Original (PHI Visible):</Text>
              <Text style={styles.originalText}>{result.original_text}</Text>
            </View>
          ) : (
            <View style={styles.warningContainer}>
              <Icon name="warning" size={20} color="#ff9800" />
              <Text style={styles.warningText}>
                Original text hidden for PHI protection
              </Text>
            </View>
          )}

          <View style={styles.textContainer}>
            <Text style={styles.textLabel}>De-identified:</Text>
            <Text style={styles.anonymizedText}>{result.anonymized_text}</Text>
          </View>
        </View>

        {/* PHI Violations */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>PHI Analysis</Text>
          {result.phi_violations.length > 0 ? (
            result.phi_violations.map((violation, index) => (
              <View key={index} style={styles.violationItem}>
                <View style={styles.violationHeader}>
                  <Text style={[styles.violationType, { color: getSeverityColor(violation.severity) }]}>
                    {violation.violation_type.replace('potential_', '')}
                  </Text>
                  <Text style={[styles.violationSeverity, { color: getSeverityColor(violation.severity) }]}>
                    {violation.severity}
                  </Text>
                </View>
                <Text style={styles.violationText}>{violation.text}</Text>
                <Text style={styles.violationRecommendation}>{violation.recommendation}</Text>
              </View>
            ))
          ) : (
            <View style={styles.successContainer}>
              <Icon name="check-circle" size={20} color="#4caf50" />
              <Text style={styles.successText}>No PHI violations detected</Text>
            </View>
          )}
        </View>

        {/* Medical Entities */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Medical Entities</Text>
          {result.medical_entities.length > 0 ? (
            result.medical_entities.slice(0, 5).map((entity, index) => (
              <View key={index} style={styles.entityItem}>
                <Text style={styles.entityText}>{entity.text}</Text>
                <View style={styles.entityDetails}>
                  <Text style={styles.entityType}>{entity.entity_type}</Text>
                  <Text style={styles.entityConfidence}>
                    {(entity.confidence * 100).toFixed(1)}%
                  </Text>
                </View>
                {entity.medical_code && (
                  <Text style={styles.entityCode}>{entity.medical_code}</Text>
                )}
              </View>
            ))
          ) : (
            <Text style={styles.noDataText}>No medical entities detected</Text>
          )}
        </View>

        {/* Medical Codes */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Medical Codes</Text>
          
          {result.medical_codes.icd10_codes.length > 0 && (
            <View style={styles.codeSection}>
              <Text style={styles.codeTitle}>ICD-10 Codes:</Text>
              {result.medical_codes.icd10_codes.map((code, index) => (
                <View key={index} style={styles.codeItem}>
                  <Text style={styles.codeNumber}>{code.code}</Text>
                  <Text style={styles.codeDescription}>{code.description}</Text>
                  <Text style={styles.codeConfidence}>
                    {(code.confidence * 100).toFixed(1)}%
                  </Text>
                </View>
              ))}
            </View>
          )}

          {result.medical_codes.cpt_codes.length > 0 && (
            <View style={styles.codeSection}>
              <Text style={styles.codeTitle}>CPT Codes:</Text>
              {result.medical_codes.cpt_codes.map((code, index) => (
                <View key={index} style={styles.codeItem}>
                  <Text style={styles.codeNumber}>{code.code}</Text>
                  <Text style={styles.codeDescription}>{code.description}</Text>
                  <Text style={styles.codeConfidence}>
                    {(code.confidence * 100).toFixed(1)}%
                  </Text>
                </View>
              ))}
            </View>
          )}

          {result.medical_codes.icd10_codes.length === 0 && result.medical_codes.cpt_codes.length === 0 && (
            <Text style={styles.noDataText}>No medical codes suggested</Text>
          )}
        </View>
      </ScrollView>
    );
  };

  const renderSettingsModal = () => (
    <Modal
      visible={settingsModalVisible}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Configuration Settings</Text>
          <TouchableOpacity
            onPress={() => setSettingsModalVisible(false)}
            style={styles.closeButton}
          >
            <Icon name="close" size={24} color="#757575" />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.modalContent}>
          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Compliance Level:</Text>
            <Picker
              selectedValue={complianceLevel}
              onValueChange={setComplianceLevel}
              style={styles.picker}
            >
              <Picker.Item label="Strict" value="strict" />
              <Picker.Item label="Standard" value="standard" />
              <Picker.Item label="Research" value="research" />
            </Picker>
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>PHI Detection:</Text>
            <Switch
              value={enablePHIDetection}
              onValueChange={setEnablePHIDetection}
              trackColor={{ false: '#767577', true: '#81b0ff' }}
              thumbColor={enablePHIDetection ? '#1976d2' : '#f4f3f4'}
            />
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Medical Coding:</Text>
            <Switch
              value={enableMedicalCoding}
              onValueChange={setEnableMedicalCoding}
              trackColor={{ false: '#767577', true: '#81b0ff' }}
              thumbColor={enableMedicalCoding ? '#1976d2' : '#f4f3f4'}
            />
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Audit Logging:</Text>
            <Switch
              value={enableAuditLogging}
              onValueChange={setEnableAuditLogging}
              trackColor={{ false: '#767577', true: '#81b0ff' }}
              thumbColor={enableAuditLogging ? '#1976d2' : '#f4f3f4'}
            />
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  const renderComplianceModal = () => (
    <Modal
      visible={complianceModalVisible}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>HIPAA Compliance Information</Text>
          <TouchableOpacity
            onPress={() => setComplianceModalVisible(false)}
            style={styles.closeButton}
          >
            <Icon name="close" size={24} color="#757575" />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.modalContent}>
          <Text style={styles.infoSectionTitle}>Protected Health Information (PHI)</Text>
          <Text style={styles.infoText}>
            PHI includes any information that can identify a patient:
          </Text>
          <Text style={styles.infoList}>
            • Names and addresses{'\n'}
            • Dates of birth and death{'\n'}
            • Phone and fax numbers{'\n'}
            • Email addresses{'\n'}
            • Social Security numbers{'\n'}
            • Medical record numbers{'\n'}
            • Account numbers
          </Text>

          <Text style={styles.infoSectionTitle}>Compliance Levels</Text>
          <Text style={styles.infoText}>
            <Text style={styles.infoBold}>Strict:</Text> Maximum security with comprehensive PHI detection{'\n'}
            <Text style={styles.infoBold}>Standard:</Text> Balanced approach for typical healthcare use{'\n'}
            <Text style={styles.infoBold}>Research:</Text> Optimized for research and analytics
          </Text>

          <Text style={styles.infoSectionTitle}>Security Features</Text>
          <Text style={styles.infoList}>
            • End-to-end encryption{'\n'}
            • Comprehensive audit logging{'\n'}
            • Role-based access controls{'\n'}
            • Automated breach detection{'\n'}
            • Safe Harbor de-identification
          </Text>
        </ScrollView>
      </View>
    </Modal>
  );

  return (
    <View style={styles.container}>
      {/* Tab Navigation */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'input' && styles.activeTab]}
          onPress={() => setActiveTab('input')}
        >
          <Icon name="edit" size={20} color={activeTab === 'input' ? '#1976d2' : '#757575'} />
          <Text style={[styles.tabText, activeTab === 'input' && styles.activeTabText]}>
            Input
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'results' && styles.activeTab]}
          onPress={() => setActiveTab('results')}
          disabled={!result}
        >
          <Icon
            name="assessment"
            size={20}
            color={activeTab === 'results' && result ? '#1976d2' : '#757575'}
          />
          <Text style={[
            styles.tabText,
            activeTab === 'results' && result && styles.activeTabText,
            !result && styles.disabledTabText
          ]}>
            Results
          </Text>
        </TouchableOpacity>
      </View>

      {/* Tab Content */}
      {activeTab === 'input' ? renderInputTab() : renderResultsTab()}

      {/* Modals */}
      {renderSettingsModal()}
      {renderComplianceModal()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#1976d2',
  },
  tabText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#757575',
  },
  activeTabText: {
    color: '#1976d2',
    fontWeight: '600',
  },
  disabledTabText: {
    color: '#bdbdbd',
  },
  tabContent: {
    flex: 1,
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginLeft: 12,
    color: '#1976d2',
  },
  subtitle: {
    fontSize: 14,
    color: '#757575',
    marginBottom: 16,
    lineHeight: 20,
  },
  settingsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-end',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1976d2',
    marginBottom: 16,
  },
  settingsButtonText: {
    marginLeft: 8,
    color: '#1976d2',
    fontSize: 14,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    color: '#333',
  },
  sampleButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 16,
  },
  sampleButton: {
    backgroundColor: '#e3f2fd',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  sampleButtonText: {
    color: '#1976d2',
    fontSize: 12,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: '#333',
  },
  textInput: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    minHeight: 200,
    marginBottom: 16,
  },
  actionButtons: {
    gap: 12,
  },
  processButton: {
    backgroundColor: '#1976d2',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 8,
  },
  disabledButton: {
    backgroundColor: '#bdbdbd',
  },
  processButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  infoButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1976d2',
  },
  infoButtonText: {
    color: '#1976d2',
    fontSize: 14,
    marginLeft: 8,
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  resultsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  complianceScore: {
    alignItems: 'center',
  },
  scoreText: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  scoreLabel: {
    fontSize: 12,
    color: '#757575',
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  toggleButton: {
    padding: 4,
  },
  textContainer: {
    marginBottom: 16,
  },
  textLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: '#333',
  },
  originalText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#333',
    backgroundColor: '#fff3e0',
    padding: 12,
    borderRadius: 8,
  },
  anonymizedText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#333',
    backgroundColor: '#e8f5e8',
    padding: 12,
    borderRadius: 8,
  },
  warningContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff3e0',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  warningText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#f57c00',
  },
  violationItem: {
    backgroundColor: '#fafafa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  violationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  violationType: {
    fontSize: 14,
    fontWeight: '600',
  },
  violationSeverity: {
    fontSize: 12,
    fontWeight: '600',
  },
  violationText: {
    fontSize: 14,
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  violationRecommendation: {
    fontSize: 12,
    color: '#757575',
    fontStyle: 'italic',
  },
  successContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e8f5e8',
    padding: 12,
    borderRadius: 8,
  },
  successText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#2e7d32',
  },
  entityItem: {
    backgroundColor: '#fafafa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  entityText: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  entityDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  entityType: {
    fontSize: 12,
    color: '#1976d2',
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  entityConfidence: {
    fontSize: 12,
    color: '#757575',
  },
  entityCode: {
    fontSize: 12,
    color: '#4caf50',
    fontWeight: '600',
  },
  noDataText: {
    fontSize: 14,
    color: '#757575',
    fontStyle: 'italic',
    textAlign: 'center',
    paddingVertical: 16,
  },
  codeSection: {
    marginBottom: 16,
  },
  codeTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: '#333',
  },
  codeItem: {
    backgroundColor: '#fafafa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  codeNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1976d2',
    marginBottom: 4,
  },
  codeDescription: {
    fontSize: 14,
    marginBottom: 4,
  },
  codeConfidence: {
    fontSize: 12,
    color: '#757575',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  closeButton: {
    padding: 8,
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
  },
  picker: {
    width: 150,
  },
  infoSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 16,
    marginBottom: 8,
    color: '#333',
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#333',
    marginBottom: 12,
  },
  infoBold: {
    fontWeight: 'bold',
  },
  infoList: {
    fontSize: 14,
    lineHeight: 20,
    color: '#333',
    marginBottom: 12,
    paddingLeft: 8,
  },
});

export default HIPAAMedicalTranscriptionMobile;