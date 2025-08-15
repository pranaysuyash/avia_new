/**
 * Medical Transcription Desktop - Task 129 Electron Implementation
 * HIPAA-compliant medical transcription with desktop-specific features
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  Shield,
  FileText,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Heart,
  Pill,
  Microscope,
  Stethoscope,
  UserCheck,
  Lock,
  Eye,
  EyeOff,
  Download,
  Upload,
  Search,
  Filter,
  Calendar,
  Clock,
  TrendingUp,
  BarChart3,
  Users,
  Settings,
  FolderOpen,
  Save,
  FileX,
  Database,
  Key,
  AlertCircle,
  CheckSquare
} from 'lucide-react';

// Types (enhanced for comprehensive schema with desktop-specific additions)
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
  file_path?: string; // Desktop-specific: local file path
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

// Desktop-specific interfaces
interface EncryptionSettings {
  enabled: boolean;
  keyPath: string;
  algorithm: string;
}

interface AuditLog {
  timestamp: string;
  user_id: string;
  action: string;
  resource_id: string;
  success: boolean;
  details: string;
}

const MedicalTranscriptionDesktop: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState<'transcription' | 'reports' | 'compliance' | 'security' | 'audit'>('transcription');
  const [transcriptText, setTranscriptText] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentResult, setCurrentResult] = useState<ProcessingResult | null>(null);
  const [complianceLevel, setComplianceLevel] = useState<HIPAAComplianceLevel>('standard');
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [showPHI, setShowPHI] = useState(false);

  // Desktop-specific state
  const [encryptionSettings, setEncryptionSettings] = useState<EncryptionSettings>({
    enabled: true,
    keyPath: '',
    algorithm: 'AES-256-GCM'
  });
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [securityStatus, setSecurityStatus] = useState<'secure' | 'warning' | 'error'>('secure');
  const [dbStatus, setDbStatus] = useState<'connected' | 'disconnected' | 'error'>('connected');

  // Form state
  const [metadata, setMetadata] = useState({
    patient_id: `PATIENT_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`,
    provider_id: 'DR_ATTENDING',
    report_type: 'consultation' as 'consultation' | 'progress_note' | 'discharge_summary',
    transcript_id: `TRANS_${Math.random().toString(36).substring(2, 10)}`
  });

  // Desktop-specific: Communication with main process
  useEffect(() => {
    // Listen for medical processing results
    window.electronAPI?.onMedicalProcessingResult?.((result: ProcessingResult) => {
      setCurrentResult(result);
      setLoading(false);
      
      if (result.success && result.report_id) {
        // Add to reports list
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
    });

    // Listen for security status updates
    window.electronAPI?.onSecurityStatusUpdate?.((status: { 
      security: 'secure' | 'warning' | 'error',
      database: 'connected' | 'disconnected' | 'error',
      encryption: EncryptionSettings 
    }) => {
      setSecurityStatus(status.security);
      setDbStatus(status.database);
      setEncryptionSettings(status.encryption);
    });

    // Listen for audit log updates
    window.electronAPI?.onAuditLogUpdate?.((logs: AuditLog[]) => {
      setAuditLogs(logs);
    });

    return () => {
      window.electronAPI?.removeAllListeners?.('medical-processing-result');
      window.electronAPI?.removeAllListeners?.('security-status-update');
      window.electronAPI?.removeAllListeners?.('audit-log-update');
    };
  }, [metadata]);

  // Process medical transcription using Electron's main process
  const processTranscription = useCallback(async () => {
    if (!transcriptText.trim()) {
      alert('Please enter transcript text to process.');
      return;
    }

    setLoading(true);
    try {
      await window.electronAPI?.processMedicalTranscription?.({
        transcript_text: transcriptText,
        metadata: {
          ...metadata,
          user_id: 'desktop_user'
        },
        compliance_level: complianceLevel
      });
    } catch (error) {
      console.error('Error processing transcription:', error);
      setCurrentResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
      setLoading(false);
    }
  }, [transcriptText, metadata, complianceLevel]);

  // Desktop-specific: Load transcript from file
  const loadTranscriptFromFile = async () => {
    try {
      const filePath = await window.electronAPI?.openFileDialog?.({
        filters: [
          { name: 'Text Files', extensions: ['txt'] },
          { name: 'All Files', extensions: ['*'] }
        ]
      });
      
      if (filePath) {
        const content = await window.electronAPI?.readFile?.(filePath);
        if (content) {
          setTranscriptText(content);
        }
      }
    } catch (error) {
      console.error('Error loading file:', error);
    }
  };

  // Desktop-specific: Export report to file
  const exportReport = async (report: MedicalReport) => {
    try {
      const filePath = await window.electronAPI?.saveFileDialog?.({
        defaultPath: `medical_report_${report.patient_id}_${new Date().toISOString().slice(0, 10)}.json`,
        filters: [
          { name: 'JSON Files', extensions: ['json'] },
          { name: 'Text Files', extensions: ['txt'] }
        ]
      });
      
      if (filePath) {
        const exportData = {
          report_id: report.report_id,
          metadata: {
            patient_id: report.patient_id,
            provider_id: report.provider_id,
            transcript_id: report.transcript_id,
            report_type: report.report_type
          },
          sections: report.sections,
          entities: report.entities,
          medications: report.medications,
          procedures: report.procedures,
          diagnoses: report.diagnoses,
          processed_at: report.created_at,
          compliance_status: report.compliance_status
        };
        
        await window.electronAPI?.writeFile?.(filePath, JSON.stringify(exportData, null, 2));
        alert('Report exported successfully!');
      }
    } catch (error) {
      console.error('Error exporting report:', error);
      alert('Failed to export report.');
    }
  };

  // Desktop-specific: Secure database backup
  const performSecureBackup = async () => {
    try {
      const backupPath = await window.electronAPI?.createSecureBackup?.();
      if (backupPath) {
        alert(`Secure backup created at: ${backupPath}`);
      }
    } catch (error) {
      console.error('Error creating backup:', error);
      alert('Failed to create secure backup.');
    }
  };

  // Render transcription tab (similar to React but with desktop features)
  const renderTranscriptionTab = () => (
    <div className="flex-1 p-6 space-y-6 overflow-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white p-6 rounded-lg">
        <div className="flex items-center space-x-3">
          <Stethoscope className="w-8 h-8" />
          <div>
            <h1 className="text-2xl font-bold">Medical Transcription Processing</h1>
            <p className="opacity-90">HIPAA-compliant medical transcription with desktop security</p>
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Settings className="w-5 h-5 mr-2" />
          Configuration
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              HIPAA Compliance Level
            </label>
            <select
              value={complianceLevel}
              onChange={(e) => setComplianceLevel(e.target.value as HIPAAComplianceLevel)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            >
              <option value="strict">🔒 Strict (No PHI allowed)</option>
              <option value="standard">🛡️ Standard (PHI anonymized)</option>
              <option value="research">📊 Research (Limited PHI)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Patient ID
            </label>
            <input
              type="text"
              value={metadata.patient_id}
              onChange={(e) => setMetadata(prev => ({ ...prev, patient_id: e.target.value }))}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              placeholder="Anonymous patient identifier"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Provider ID
            </label>
            <input
              type="text"
              value={metadata.provider_id}
              onChange={(e) => setMetadata(prev => ({ ...prev, provider_id: e.target.value }))}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              placeholder="Provider identifier"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Type
            </label>
            <select
              value={metadata.report_type}
              onChange={(e) => setMetadata(prev => ({ ...prev, report_type: e.target.value as any }))}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            >
              <option value="consultation">👨‍⚕️ Consultation Note</option>
              <option value="progress_note">📝 Progress Note (SOAP)</option>
              <option value="discharge_summary">🏠 Discharge Summary</option>
            </select>
          </div>
        </div>
      </div>

      {/* Transcription Input */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <FileText className="w-5 h-5 mr-2" />
          Medical Transcript
        </h2>
        
        <textarea
          value={transcriptText}
          onChange={(e) => setTranscriptText(e.target.value)}
          placeholder="Enter or paste medical transcript here..."
          className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
        />
        
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">
              {transcriptText.length} characters
            </span>
            <button
              onClick={loadTranscriptFromFile}
              className="text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-1"
            >
              <FolderOpen className="w-4 h-4" />
              <span>Load from File</span>
            </button>
            <button
              onClick={() => setTranscriptText('')}
              className="text-sm text-red-600 hover:text-red-700 flex items-center space-x-1"
            >
              <FileX className="w-4 h-4" />
              <span>Clear</span>
            </button>
          </div>
          
          <button
            onClick={processTranscription}
            disabled={loading || !transcriptText.trim()}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Activity className="w-4 h-4" />
                <span>Process Transcript</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results (similar to React implementation but with export buttons) */}
      {currentResult && currentResult.success && (
        <div className="space-y-6">
          {/* Success Message with Export */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                <h3 className="text-green-800 font-medium">Transcript processed successfully!</h3>
              </div>
              <button
                onClick={() => exportReport(reports[0])}
                className="text-green-600 hover:text-green-700 flex items-center space-x-1"
              >
                <Download className="w-4 h-4" />
                <span>Export Report</span>
              </button>
            </div>
          </div>

          {/* PHI Violations Alert */}
          {currentResult.phi_violations && currentResult.phi_violations.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
                  <h3 className="text-yellow-800 font-medium">PHI Detection Alert</h3>
                </div>
                <button
                  onClick={() => setShowPHI(!showPHI)}
                  className="text-yellow-600 hover:text-yellow-700 flex items-center space-x-1"
                >
                  {showPHI ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  <span>{showPHI ? 'Hide' : 'Show'} Details</span>
                </button>
              </div>
              <p className="text-yellow-700 mt-2">
                Protected Health Information (PHI) was detected and handled according to your compliance settings.
              </p>
              
              {showPHI && (
                <div className="mt-4 space-y-3">
                  {currentResult.phi_violations.map((violation, index) => (
                    <div key={index} className="bg-white p-3 rounded border">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-900">{violation.violation_type}</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          violation.severity === 'high' ? 'bg-red-100 text-red-800' :
                          violation.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {violation.severity}
                        </span>
                      </div>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Text:</strong> {violation.text}
                      </p>
                      <p className="text-gray-600 text-sm">
                        <strong>Recommendation:</strong> {violation.recommendation}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Clinical Information Summary (similar to React) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Medications */}
            {currentResult.medications && currentResult.medications.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Pill className="w-5 h-5 mr-2 text-blue-600" />
                  Medications ({currentResult.medications.length})
                </h3>
                <div className="space-y-3">
                  {currentResult.medications.slice(0, 5).map((med, index) => (
                    <div key={index} className="border-l-4 border-blue-500 pl-3">
                      <div className="font-medium text-gray-900">{med.name}</div>
                      <div className="text-sm text-gray-600">
                        Confidence: {(med.confidence * 100).toFixed(1)}%
                      </div>
                      {med.context && (
                        <div className="text-xs text-gray-500 mt-1">{med.context}</div>
                      )}
                    </div>
                  ))}
                  {currentResult.medications.length > 5 && (
                    <div className="text-sm text-gray-500">
                      +{currentResult.medications.length - 5} more medications
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Procedures */}
            {currentResult.procedures && currentResult.procedures.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Microscope className="w-5 h-5 mr-2 text-green-600" />
                  Procedures ({currentResult.procedures.length})
                </h3>
                <div className="space-y-3">
                  {currentResult.procedures.slice(0, 5).map((proc, index) => (
                    <div key={index} className="border-l-4 border-green-500 pl-3">
                      <div className="font-medium text-gray-900">{proc.name}</div>
                      <div className="text-sm text-gray-600">
                        Confidence: {(proc.confidence * 100).toFixed(1)}%
                      </div>
                      {proc.context && (
                        <div className="text-xs text-gray-500 mt-1">{proc.context}</div>
                      )}
                    </div>
                  ))}
                  {currentResult.procedures.length > 5 && (
                    <div className="text-sm text-gray-500">
                      +{currentResult.procedures.length - 5} more procedures
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Diagnoses */}
            {currentResult.diagnoses && currentResult.diagnoses.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Heart className="w-5 h-5 mr-2 text-red-600" />
                  Diagnoses ({currentResult.diagnoses.length})
                </h3>
                <div className="space-y-3">
                  {currentResult.diagnoses.slice(0, 5).map((diag, index) => (
                    <div key={index} className="border-l-4 border-red-500 pl-3">
                      <div className="font-medium text-gray-900">{diag.name}</div>
                      <div className="text-sm text-gray-600">
                        Confidence: {(diag.confidence * 100).toFixed(1)}%
                      </div>
                      {diag.context && (
                        <div className="text-xs text-gray-500 mt-1">{diag.context}</div>
                      )}
                    </div>
                  ))}
                  {currentResult.diagnoses.length > 5 && (
                    <div className="text-sm text-gray-500">
                      +{currentResult.diagnoses.length - 5} more diagnoses
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Comprehensive Analysis Dashboard - Desktop */}
          {currentResult.comprehensive_analysis && (
            <div className="bg-white rounded-lg shadow-sm border p-6 mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-purple-600" />
                Comprehensive Clinical Analysis
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-3xl font-bold text-purple-600">
                    {currentResult.comprehensive_analysis.patient_engagement_score.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Patient Engagement Score</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-lg font-medium text-blue-600">
                    {currentResult.comprehensive_analysis.care_quality_indicators.filter(i => i.status === 'excellent').length}
                  </div>
                  <div className="text-sm text-gray-600">Excellent Indicators</div>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-lg font-medium text-orange-600">
                    {currentResult.comprehensive_analysis.clinical_decision_support.filter(r => r.priority === 'high').length}
                  </div>
                  <div className="text-sm text-gray-600">High Priority Actions</div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Care Quality Indicators */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Care Quality Indicators</h4>
                  <div className="space-y-2">
                    {currentResult.comprehensive_analysis.care_quality_indicators.map((indicator, index) => (
                      <div key={index} className={`p-3 rounded border-l-4 ${
                        indicator.status === 'excellent' ? 'border-green-500 bg-green-50' :
                        indicator.status === 'good' ? 'border-blue-500 bg-blue-50' :
                        indicator.status === 'needs_improvement' ? 'border-yellow-500 bg-yellow-50' :
                        'border-red-500 bg-red-50'
                      }`}>
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">{indicator.indicator}</span>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            indicator.status === 'excellent' ? 'bg-green-100 text-green-800' :
                            indicator.status === 'good' ? 'bg-blue-100 text-blue-800' :
                            indicator.status === 'needs_improvement' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {indicator.status.replace('_', ' ')}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">{indicator.details}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Clinical Decision Support */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Clinical Decision Support</h4>
                  <div className="space-y-2">
                    {currentResult.comprehensive_analysis.clinical_decision_support.map((recommendation, index) => (
                      <div key={index} className={`p-3 rounded border-l-4 ${
                        recommendation.priority === 'high' ? 'border-red-500 bg-red-50' :
                        recommendation.priority === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                        'border-green-500 bg-green-50'
                      }`}>
                        <div className="flex items-center justify-between mb-1">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            recommendation.priority === 'high' ? 'bg-red-100 text-red-800' :
                            recommendation.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {recommendation.priority.toUpperCase()}
                          </span>
                          <span className="text-xs text-gray-500">
                            Evidence: {recommendation.evidence_level}
                          </span>
                        </div>
                        <p className="text-xs text-gray-700">{recommendation.recommendation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Advanced Clinical Data - Desktop */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
            {/* Vital Signs */}
            {currentResult.vital_signs && currentResult.vital_signs.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-4">
                <h3 className="text-base font-semibold text-gray-900 mb-3 flex items-center">
                  <Activity className="w-4 h-4 mr-2 text-indigo-600" />
                  Vital Signs ({currentResult.vital_signs.length})
                </h3>
                <div className="space-y-2">
                  {currentResult.vital_signs.map((vital, index) => (
                    <div key={index} className="border-l-4 border-indigo-500 pl-2">
                      <div className="font-medium text-sm text-gray-900">{vital.type}</div>
                      <div className="text-xs text-gray-600">
                        {vital.value} {vital.unit}
                      </div>
                      {vital.interpretation && (
                        <div className="text-xs text-gray-500">{vital.interpretation}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Voice Biomarkers */}
            {currentResult.voice_biomarkers && currentResult.voice_biomarkers.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-4">
                <h3 className="text-base font-semibold text-gray-900 mb-3 flex items-center">
                  <Activity className="w-4 h-4 mr-2 text-purple-600" />
                  Voice Biomarkers
                </h3>
                <div className="space-y-2">
                  {currentResult.voice_biomarkers.map((biomarker, index) => (
                    <div key={index} className="border-l-4 border-purple-500 pl-2">
                      <div className="font-medium text-sm text-gray-900">{biomarker.biomarker_type}</div>
                      <div className="text-xs text-gray-600">Value: {biomarker.value}</div>
                      <div className="text-xs text-purple-600">{biomarker.interpretation}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Emotional State */}
            {currentResult.emotional_state && currentResult.emotional_state.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-4">
                <h3 className="text-base font-semibold text-gray-900 mb-3 flex items-center">
                  <Heart className="w-4 h-4 mr-2 text-pink-600" />
                  Emotional Analysis
                </h3>
                <div className="space-y-2">
                  {currentResult.emotional_state.map((emotion, index) => (
                    <div key={index} className="border-l-4 border-pink-500 pl-2">
                      <div className="font-medium text-sm text-gray-900">{emotion.emotion}</div>
                      <div className="text-xs text-gray-600">Intensity: {emotion.intensity}/10</div>
                      <div className="text-xs text-gray-500">{emotion.context}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Social Determinants */}
            {currentResult.social_determinants && currentResult.social_determinants.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-4">
                <h3 className="text-base font-semibold text-gray-900 mb-3 flex items-center">
                  <Users className="w-4 h-4 mr-2 text-emerald-600" />
                  Social Determinants
                </h3>
                <div className="space-y-2">
                  {currentResult.social_determinants.map((determinant, index) => (
                    <div key={index} className={`border-l-4 pl-2 ${
                      determinant.impact_level === 'high' ? 'border-red-500' :
                      determinant.impact_level === 'medium' ? 'border-yellow-500' :
                      'border-emerald-500'
                    }`}>
                      <div className="font-medium text-sm text-gray-900">{determinant.factor}</div>
                      <div className="text-xs text-gray-600">Category: {determinant.category}</div>
                      <div className={`text-xs font-medium ${
                        determinant.impact_level === 'high' ? 'text-red-600' :
                        determinant.impact_level === 'medium' ? 'text-yellow-600' :
                        'text-emerald-600'
                      }`}>
                        Impact: {determinant.impact_level}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Test Results and Ambient Sounds */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            {/* Test Results */}
            {currentResult.test_results && currentResult.test_results.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Microscope className="w-5 h-5 mr-2 text-teal-600" />
                  Laboratory Results
                </h3>
                <div className="space-y-3">
                  {currentResult.test_results.map((test, index) => (
                    <div key={index} className={`border-l-4 pl-3 ${
                      test.abnormal ? 'border-red-500' : 'border-teal-500'
                    }`}>
                      <div className="font-medium text-gray-900">{test.test_name}</div>
                      <div className="text-sm text-gray-600">{test.value}</div>
                      {test.reference_range && (
                        <div className="text-xs text-gray-500">Reference: {test.reference_range}</div>
                      )}
                      {test.interpretation && (
                        <div className={`text-xs mt-1 ${
                          test.abnormal ? 'text-red-600' : 'text-teal-600'
                        }`}>{test.interpretation}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Ambient Sounds */}
            {currentResult.ambient_sounds && currentResult.ambient_sounds.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Activity className="w-5 h-5 mr-2 text-orange-600" />
                  Environmental Context
                </h3>
                <div className="space-y-3">
                  {currentResult.ambient_sounds.map((sound, index) => (
                    <div key={index} className="border-l-4 border-orange-500 pl-3">
                      <div className="font-medium text-gray-900">{sound.sound_type}</div>
                      <div className="text-sm text-gray-600">Duration: {sound.duration}s</div>
                      <div className="text-xs text-gray-500">{sound.context}</div>
                      {sound.clinical_relevance && (
                        <div className="text-xs text-orange-600 mt-1 font-medium">
                          Clinical relevance: {sound.clinical_relevance}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  // Render security tab (desktop-specific)
  const renderSecurityTab = () => (
    <div className="flex-1 p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
          <Shield className="w-5 h-5 mr-2" />
          Security & Encryption Management
        </h2>

        {/* Security Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className={`p-4 rounded-lg ${
            securityStatus === 'secure' ? 'bg-green-50 border border-green-200' :
            securityStatus === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
            'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center mb-2">
              {securityStatus === 'secure' ? (
                <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              ) : securityStatus === 'warning' ? (
                <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600 mr-2" />
              )}
              <h3 className="font-medium">Security Status</h3>
            </div>
            <p className={`text-sm ${
              securityStatus === 'secure' ? 'text-green-700' :
              securityStatus === 'warning' ? 'text-yellow-700' :
              'text-red-700'
            }`}>
              {securityStatus === 'secure' ? 'All security checks passed' :
               securityStatus === 'warning' ? 'Some security concerns detected' :
               'Critical security issues detected'}
            </p>
          </div>

          <div className={`p-4 rounded-lg ${
            dbStatus === 'connected' ? 'bg-green-50 border border-green-200' :
            'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center mb-2">
              <Database className="w-5 h-5 mr-2" />
              <h3 className="font-medium">Database</h3>
            </div>
            <p className={`text-sm ${
              dbStatus === 'connected' ? 'text-green-700' : 'text-red-700'
            }`}>
              {dbStatus === 'connected' ? 'Securely connected' : 'Connection issues'}
            </p>
          </div>

          <div className={`p-4 rounded-lg ${
            encryptionSettings.enabled ? 'bg-green-50 border border-green-200' :
            'bg-yellow-50 border border-yellow-200'
          }`}>
            <div className="flex items-center mb-2">
              <Key className="w-5 h-5 mr-2" />
              <h3 className="font-medium">Encryption</h3>
            </div>
            <p className={`text-sm ${
              encryptionSettings.enabled ? 'text-green-700' : 'text-yellow-700'
            }`}>
              {encryptionSettings.enabled ? `${encryptionSettings.algorithm} enabled` : 'Encryption disabled'}
            </p>
          </div>
        </div>

        {/* Encryption Settings */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Encryption Configuration</h3>
          
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={encryptionSettings.enabled}
                onChange={(e) => setEncryptionSettings(prev => ({ ...prev, enabled: e.target.checked }))}
                className="rounded border-gray-300"
              />
              <label className="text-sm font-medium text-gray-700">
                Enable data encryption at rest
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Encryption Algorithm
              </label>
              <select
                value={encryptionSettings.algorithm}
                onChange={(e) => setEncryptionSettings(prev => ({ ...prev, algorithm: e.target.value }))}
                className="w-full p-2 border border-gray-300 rounded-lg"
              >
                <option value="AES-256-GCM">AES-256-GCM (Recommended)</option>
                <option value="AES-256-CBC">AES-256-CBC</option>
                <option value="ChaCha20-Poly1305">ChaCha20-Poly1305</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Key File Path
              </label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={encryptionSettings.keyPath}
                  onChange={(e) => setEncryptionSettings(prev => ({ ...prev, keyPath: e.target.value }))}
                  className="flex-1 p-2 border border-gray-300 rounded-lg"
                  placeholder="Path to encryption key file"
                />
                <button
                  onClick={() => window.electronAPI?.selectKeyFile?.()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Browse
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Backup Management */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Secure Backup</h3>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={performSecureBackup}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>Create Secure Backup</span>
            </button>
            
            <button
              onClick={() => window.electronAPI?.restoreFromBackup?.()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
            >
              <Upload className="w-4 h-4" />
              <span>Restore from Backup</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Render audit tab (desktop-specific)
  const renderAuditTab = () => (
    <div className="flex-1 p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <CheckSquare className="w-5 h-5 mr-2" />
          Audit Log ({auditLogs.length})
        </h2>
        
        {auditLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No audit events recorded yet.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {auditLogs.slice(0, 50).map((log, index) => (
              <div key={index} className={`p-3 rounded border-l-4 ${
                log.success ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'
              }`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-gray-900">{log.action}</span>
                  <span className="text-sm text-gray-500">
                    {new Date(log.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  User: {log.user_id} | Resource: {log.resource_id}
                </div>
                {log.details && (
                  <div className="text-xs text-gray-500 mt-1">{log.details}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b flex-shrink-0">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Stethoscope className="w-8 h-8 text-green-600" />
              <h1 className="text-xl font-semibold text-gray-900">
                Medical Transcription System
              </h1>
            </div>
            
            {/* Status indicators */}
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-1 ${
                securityStatus === 'secure' ? 'text-green-600' :
                securityStatus === 'warning' ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                <Shield className="w-4 h-4" />
                <span className="text-sm">{securityStatus}</span>
              </div>
              
              <div className={`flex items-center space-x-1 ${
                dbStatus === 'connected' ? 'text-green-600' : 'text-red-600'
              }`}>
                <Database className="w-4 h-4" />
                <span className="text-sm">{dbStatus}</span>
              </div>
            </div>
          </div>
          
          {/* Tab navigation */}
          <div className="flex space-x-1 mt-4">
            {[
              { id: 'transcription', label: 'Transcription', icon: Stethoscope },
              { id: 'reports', label: 'Reports', icon: FileText },
              { id: 'compliance', label: 'Compliance', icon: Shield },
              { id: 'security', label: 'Security', icon: Lock },
              { id: 'audit', label: 'Audit Log', icon: CheckSquare }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-green-100 text-green-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'transcription' && renderTranscriptionTab()}
        {activeTab === 'reports' && (
          <div className="flex-1 p-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Medical Reports</h2>
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Reports management interface</p>
              </div>
            </div>
          </div>
        )}
        {activeTab === 'compliance' && (
          <div className="flex-1 p-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">HIPAA Compliance</h2>
              <div className="text-center py-8 text-gray-500">
                <Shield className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Compliance dashboard interface</p>
              </div>
            </div>
          </div>
        )}
        {activeTab === 'security' && renderSecurityTab()}
        {activeTab === 'audit' && renderAuditTab()}
      </div>
    </div>
  );
};

export default MedicalTranscriptionDesktop;