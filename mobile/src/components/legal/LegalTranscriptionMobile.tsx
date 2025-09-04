import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Modal,
  FlatList
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import DocumentPicker from 'react-native-document-picker';
import RNFS from 'react-native-fs';
import { Share } from 'react-native';
import { buildLink } from '../../utils/deeplink';
import { logUxEvent } from '../../utils/uxTelemetry';
import { SkeletonList } from '../shared/Skeleton';

interface LegalEntity {
  type: string;
  text: string;
  confidence: number;
  start_pos: number;
  end_pos: number;
}

interface TranscriptionResult {
  status: string;
  transcript: string;
  legal_analysis: {
    entities: LegalEntity[];
    document_type: string;
    confidence_score: number;
  };
  compliance_check: {
    overall_score: number;
    checks: Array<{
      name: string;
      status: string;
      score: number;
    }>;
    recommendations: string[];
  };
  metadata: {
    case_number: string;
    proceeding_type: string;
    participants: string[];
    processing_time: number;
  };
}

const LegalTranscriptionMobile: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'upload' | 'results' | 'analysis' | 'export'>('upload');
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcriptionResult, setTranscriptionResult] = useState<TranscriptionResult | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Form state
  const [caseNumber, setCaseNumber] = useState('');
  const [proceedingType, setProceedingType] = useState('hearing');
  const [courtJurisdiction, setCourtJurisdiction] = useState('');
  const [confidentialityLevel, setConfidentialityLevel] = useState('standard');
  const [participants, setParticipants] = useState('');
  const [attorneyClientPrivilege, setAttorneyClientPrivilege] = useState(false);
  
  // Modal states
  const [showEntityModal, setShowEntityModal] = useState(false);
  const [showComplianceModal, setShowComplianceModal] = useState(false);

  const handleFilePicker = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.audio],
        copyTo: 'documentDirectory'
      });
      
      if (result && result.length > 0) {
        setSelectedFile(result[0]);
      }
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        Alert.alert('Error', 'Failed to select file');
      }
    }
  };

  const handleProcessTranscription = async () => {
    if (!selectedFile) {
      Alert.alert('Error', 'Please select an audio file first');
      return;
    }

    setIsProcessing(true);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', {
        uri: selectedFile.fileCopyUri || selectedFile.uri,
        type: selectedFile.type,
        name: selectedFile.name
      } as any);
      
      formData.append('case_number', caseNumber);
      formData.append('proceeding_type', proceedingType);
      formData.append('court_jurisdiction', courtJurisdiction);
      formData.append('confidentiality_level', confidentialityLevel);
      formData.append('participants', JSON.stringify(participants.split('\n').filter(p => p.trim())));
      formData.append('attorney_client_privilege', attorneyClientPrivilege.toString());

      const response = await fetch('/api/legal/transcribe', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setTranscriptionResult(result);
      setActiveTab('results');
      Alert.alert('Success', 'Legal transcription completed successfully!');
    } catch (err) {
      Alert.alert('Error', err instanceof Error ? err.message : 'An error occurred during transcription');
    } finally {
      setIsProcessing(false);
      setLoading(false);
    }
  };

  const renderTabButton = (tab: string, title: string, isActive: boolean) => (
    <TouchableOpacity
      key={tab}
      style={[styles.tabButton, isActive && styles.activeTabButton]}
      onPress={() => setActiveTab(tab as any)}
    >
      <Text style={[styles.tabButtonText, isActive && styles.activeTabButtonText]}>
        {title}
      </Text>
    </TouchableOpacity>
  );

  const shareLegalLink = async () => {
    const url = buildLink('legal');
    try {
      await Share.share({ message: url });
      await logUxEvent('share_legal_view', { url, tab: activeTab });
    } catch (_) {}
  };

  const renderUploadTab = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📁 Upload Legal Audio</Text>
        
        <TouchableOpacity style={styles.filePickerButton} onPress={handleFilePicker}>
          <Text style={styles.filePickerButtonText}>
            {selectedFile ? `Selected: ${selectedFile.name}` : 'Select Audio File'}
          </Text>
        </TouchableOpacity>
        
        {selectedFile && (
          <Text style={styles.fileInfo}>
            Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
          </Text>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📋 Case Information</Text>
        
        <TextInput
          style={styles.textInput}
          placeholder="Case Number (e.g., 2023-CV-1234)"
          value={caseNumber}
          onChangeText={setCaseNumber}
        />
        
        <View style={styles.pickerContainer}>
          <Text style={styles.pickerLabel}>Proceeding Type:</Text>
          <Picker
            selectedValue={proceedingType}
            onValueChange={setProceedingType}
            style={styles.picker}
          >
            <Picker.Item label="Hearing" value="hearing" />
            <Picker.Item label="Deposition" value="deposition" />
            <Picker.Item label="Trial" value="trial" />
            <Picker.Item label="Mediation" value="mediation" />
            <Picker.Item label="Arbitration" value="arbitration" />
            <Picker.Item label="Conference" value="conference" />
          </Picker>
        </View>
        
        <TextInput
          style={styles.textInput}
          placeholder="Court Jurisdiction"
          value={courtJurisdiction}
          onChangeText={setCourtJurisdiction}
        />
        
        <View style={styles.pickerContainer}>
          <Text style={styles.pickerLabel}>Confidentiality Level:</Text>
          <Picker
            selectedValue={confidentialityLevel}
            onValueChange={setConfidentialityLevel}
            style={styles.picker}
          >
            <Picker.Item label="Standard" value="standard" />
            <Picker.Item label="Confidential" value="confidential" />
            <Picker.Item label="Privileged" value="privileged" />
            <Picker.Item label="Sealed" value="sealed" />
          </Picker>
        </View>
        
        <TextInput
          style={[styles.textInput, styles.multilineInput]}
          placeholder="Participants (one per line)"
          value={participants}
          onChangeText={setParticipants}
          multiline
          numberOfLines={4}
        />
        
        <TouchableOpacity
          style={styles.checkboxContainer}
          onPress={() => setAttorneyClientPrivilege(!attorneyClientPrivilege)}
        >
          <View style={[styles.checkbox, attorneyClientPrivilege && styles.checkedCheckbox]}>
            {attorneyClientPrivilege && <Text style={styles.checkmark}>✓</Text>}
          </View>
          <Text style={styles.checkboxLabel}>
            Contains Attorney-Client Privileged Communications
          </Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[styles.processButton, (!selectedFile || isProcessing) && styles.disabledButton]}
        onPress={handleProcessTranscription}
        disabled={!selectedFile || isProcessing}
      >
        {isProcessing ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.processButtonText}>Process Legal Transcription</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );

  const renderResultsTab = () => {
    if (loading) {
      return (
        <View style={{ padding: 16 }}>
          <SkeletonList rows={6} />
        </View>
      );
    }
    if (!transcriptionResult) {
      return (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>
            No transcription results available. Please process an audio file first.
          </Text>
        </View>
      );
    }

    return (
      <ScrollView style={styles.tabContent}>
        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Document Type</Text>
            <Text style={styles.statValue}>
              {transcriptionResult.legal_analysis.document_type}
            </Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Confidence</Text>
            <Text style={styles.statValue}>
              {(transcriptionResult.legal_analysis.confidence_score * 100).toFixed(1)}%
            </Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Entities</Text>
            <Text style={styles.statValue}>
              {transcriptionResult.legal_analysis.entities.length}
            </Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Time</Text>
            <Text style={styles.statValue}>
              {transcriptionResult.metadata.processing_time.toFixed(1)}s
            </Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📝 Transcript</Text>
          <View style={styles.transcriptContainer}>
            <Text style={styles.transcriptText}>
              {transcriptionResult.transcript}
            </Text>
          </View>
        </View>

        <View style={styles.section}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => setShowEntityModal(true)}
          >
            <Text style={styles.actionButtonText}>
              View Legal Entities ({transcriptionResult.legal_analysis.entities.length})
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => setShowComplianceModal(true)}
          >
            <Text style={styles.actionButtonText}>
              View Compliance Check ({transcriptionResult.compliance_check.overall_score.toFixed(1)}/10)
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  };

  const renderAnalysisTab = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🔍 Legal Text Analysis</Text>
        <Text style={styles.sectionDescription}>
          Analyze legal text for entities, compliance, and structure.
        </Text>
        
        <TextInput
          style={[styles.textInput, styles.multilineInput]}
          placeholder="Paste legal document text here..."
          multiline
          numberOfLines={8}
        />
        
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>Analyze Legal Text</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  const renderExportTab = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📤 Export & Reports</Text>
        
        <View style={styles.pickerContainer}>
          <Text style={styles.pickerLabel}>Export Format:</Text>
          <Picker style={styles.picker}>
            <Picker.Item label="Court Reporter Format" value="court" />
            <Picker.Item label="Legal Brief Format" value="brief" />
            <Picker.Item label="Discovery Format" value="discovery" />
            <Picker.Item label="JSON Data" value="json" />
            <Picker.Item label="PDF Report" value="pdf" />
          </Picker>
        </View>
        
        <TouchableOpacity
          style={[styles.actionButton, !transcriptionResult && styles.disabledButton]}
          disabled={!transcriptionResult}
        >
          <Text style={styles.actionButtonText}>Generate Export</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  const renderEntityModal = () => (
    <Modal
      visible={showEntityModal}
      animationType="slide"
      onRequestClose={() => setShowEntityModal(false)}
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Legal Entities</Text>
          <TouchableOpacity onPress={() => setShowEntityModal(false)}>
            <Text style={styles.modalCloseButton}>✕</Text>
          </TouchableOpacity>
        </View>
        
        <FlatList
          data={transcriptionResult?.legal_analysis.entities || []}
          keyExtractor={(item, index) => index.toString()}
          renderItem={({ item }) => (
            <View style={styles.entityItem}>
              <View style={styles.entityHeader}>
                <Text style={styles.entityType}>{item.type}</Text>
                <Text style={styles.entityConfidence}>
                  {(item.confidence * 100).toFixed(1)}%
                </Text>
              </View>
              <Text style={styles.entityText}>{item.text}</Text>
              <Text style={styles.entityPosition}>
                Position: {item.start_pos}-{item.end_pos}
              </Text>
            </View>
          )}
        />
      </View>
    </Modal>
  );

  const renderComplianceModal = () => (
    <Modal
      visible={showComplianceModal}
      animationType="slide"
      onRequestClose={() => setShowComplianceModal(false)}
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Compliance Check</Text>
          <TouchableOpacity onPress={() => setShowComplianceModal(false)}>
            <Text style={styles.modalCloseButton}>✕</Text>
          </TouchableOpacity>
        </View>
        
        <ScrollView>
          <View style={styles.complianceScore}>
            <Text style={styles.complianceScoreLabel}>Overall Score</Text>
            <Text style={styles.complianceScoreValue}>
              {transcriptionResult?.compliance_check.overall_score.toFixed(1)}/10
            </Text>
          </View>
          
          {transcriptionResult?.compliance_check.recommendations.map((rec, index) => (
            <View key={index} style={styles.recommendationItem}>
              <Text style={styles.recommendationText}>• {rec}</Text>
            </View>
          ))}
        </ScrollView>
      </View>
    </Modal>
  );

  return (
    <View style={styles.container}>
      <View style={[styles.header, { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }] }>
        <View>
          <Text style={styles.headerTitle}>⚖️ Legal Transcription</Text>
          <Text style={styles.headerSubtitle}>
            Professional legal document processing
          </Text>
        </View>
        <TouchableOpacity onPress={shareLegalLink} accessibilityLabel="Share legal view" style={{ padding: 6 }}>
          <Text style={{ color: '#fff' }}>Share</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.tabContainer}>
        {renderTabButton('upload', 'Upload', activeTab === 'upload')}
        {renderTabButton('results', 'Results', activeTab === 'results')}
        {renderTabButton('analysis', 'Analysis', activeTab === 'analysis')}
        {renderTabButton('export', 'Export', activeTab === 'export')}
      </View>

      {activeTab === 'upload' && renderUploadTab()}
      {activeTab === 'results' && renderResultsTab()}
      {activeTab === 'analysis' && renderAnalysisTab()}
      {activeTab === 'export' && renderExportTab()}

      {renderEntityModal()}
      {renderComplianceModal()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5'
  },
  header: {
    backgroundColor: '#1976d2',
    padding: 20,
    paddingTop: 40
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#e3f2fd'
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0'
  },
  tabButton: {
    flex: 1,
    paddingVertical: 15,
    alignItems: 'center'
  },
  activeTabButton: {
    borderBottomWidth: 2,
    borderBottomColor: '#1976d2'
  },
  tabButtonText: {
    fontSize: 14,
    color: '#666'
  },
  activeTabButtonText: {
    color: '#1976d2',
    fontWeight: 'bold'
  },
  tabContent: {
    flex: 1,
    padding: 20
  },
  section: {
    marginBottom: 25
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333'
  },
  sectionDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15
  },
  filePickerButton: {
    backgroundColor: '#e3f2fd',
    padding: 20,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#1976d2',
    borderStyle: 'dashed',
    alignItems: 'center',
    marginBottom: 10
  },
  filePickerButtonText: {
    fontSize: 16,
    color: '#1976d2'
  },
  fileInfo: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center'
  },
  textInput: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    marginBottom: 15
  },
  multilineInput: {
    height: 100,
    textAlignVertical: 'top'
  },
  pickerContainer: {
    marginBottom: 15
  },
  pickerLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
    color: '#333'
  },
  picker: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15
  },
  checkbox: {
    width: 20,
    height: 20,
    borderWidth: 2,
    borderColor: '#1976d2',
    borderRadius: 3,
    marginRight: 10,
    alignItems: 'center',
    justifyContent: 'center'
  },
  checkedCheckbox: {
    backgroundColor: '#1976d2'
  },
  checkmark: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold'
  },
  checkboxLabel: {
    fontSize: 16,
    color: '#333',
    flex: 1
  },
  processButton: {
    backgroundColor: '#1976d2',
    padding: 18,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10
  },
  disabledButton: {
    backgroundColor: '#ccc'
  },
  processButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold'
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40
  },
  emptyStateText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center'
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 20
  },
  statCard: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    margin: 5,
    flex: 1,
    minWidth: '45%',
    alignItems: 'center'
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1976d2'
  },
  transcriptContainer: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    maxHeight: 200
  },
  transcriptText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#333'
  },
  actionButton: {
    backgroundColor: '#1976d2',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold'
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff'
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0'
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333'
  },
  modalCloseButton: {
    fontSize: 24,
    color: '#666'
  },
  entityItem: {
    backgroundColor: '#f9f9f9',
    padding: 15,
    marginHorizontal: 20,
    marginVertical: 5,
    borderRadius: 8
  },
  entityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 5
  },
  entityType: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1976d2'
  },
  entityConfidence: {
    fontSize: 14,
    color: '#666'
  },
  entityText: {
    fontSize: 16,
    color: '#333',
    marginBottom: 5
  },
  entityPosition: {
    fontSize: 12,
    color: '#999'
  },
  complianceScore: {
    backgroundColor: '#f9f9f9',
    padding: 20,
    margin: 20,
    borderRadius: 8,
    alignItems: 'center'
  },
  complianceScoreLabel: {
    fontSize: 16,
    color: '#666',
    marginBottom: 5
  },
  complianceScoreValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1976d2'
  },
  recommendationItem: {
    backgroundColor: '#fff3cd',
    padding: 15,
    marginHorizontal: 20,
    marginVertical: 5,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107'
  },
  recommendationText: {
    fontSize: 14,
    color: '#856404'
  }
});

export default LegalTranscriptionMobile;
