/**
 * Medical Transcription Interface - Task 129 React Implementation
 * HIPAA-compliant medical transcription with specialized medical NLP capabilities
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
  Settings
} from 'lucide-react';

// Types for medical transcription (enhanced for comprehensive schema)
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
    dosage?: string;
    frequency?: string;
    route?: string;
  }>;
  procedures: Array<{
    name: string;
    normalized_name: string;
    confidence: number;
    context?: string;
    medical_code?: string;
    urgency?: string;
    status?: string;
  }>;
  diagnoses: Array<{
    name: string;
    normalized_name: string;
    confidence: number;
    context?: string;
    medical_code?: string;
    severity?: string;
    stage?: string;
  }>;
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
  vital_signs?: MedicalReport['vital_signs'];
  test_results?: MedicalReport['test_results'];
  voice_biomarkers?: MedicalReport['voice_biomarkers'];
  ambient_sounds?: MedicalReport['ambient_sounds'];
  emotional_state?: MedicalReport['emotional_state'];
  social_determinants?: MedicalReport['social_determinants'];
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

interface ComplianceReport {
  report_period: {
    start: string;
    end: string;
  };
  summary: {
    total_transcriptions: number;
    phi_incidents_detected: number;
    unresolved_phi_incidents: number;
    compliance_rate: number;
  };
  audit_activity: Record<string, number>;
  compliance_level: string;
  generated_at: string;
}

type HIPAAComplianceLevel = 'strict' | 'standard' | 'research';

const MedicalTranscriptionInterface: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState<'transcription' | 'reports' | 'entities' | 'compliance' | 'analytics'>('transcription');
  const [transcriptText, setTranscriptText] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentResult, setCurrentResult] = useState<ProcessingResult | null>(null);
  const [complianceLevel, setComplianceLevel] = useState<HIPAAComplianceLevel>('standard');
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [complianceReport, setComplianceReport] = useState<ComplianceReport | null>(null);
  const [showPHI, setShowPHI] = useState(false);

  // Form state
  const [metadata, setMetadata] = useState({
    patient_id: `PATIENT_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`,
    provider_id: 'DR_ATTENDING',
    report_type: 'consultation' as 'consultation' | 'progress_note' | 'discharge_summary',
    transcript_id: `TRANS_${Math.random().toString(36).substring(2, 10)}`
  });

  // Sample medical transcript for testing
  const sampleTranscript = `Patient John Doe, DOB 01/15/1980, MRN 123456789, presents with chief complaint of chest pain.

History of Present Illness:
The patient reports onset of chest pain approximately 2 hours ago. Pain is described as sharp, radiating to left arm. Associated with shortness of breath and nausea. No previous cardiac history.

Physical Examination:
BP 140/90, HR 95, RR 18, Temp 98.6F
Heart: Regular rate and rhythm, no murmurs
Lungs: Clear to auscultation bilaterally

Assessment and Plan:
1. Chest pain, rule out myocardial infarction
   - EKG ordered
   - Cardiac enzymes ordered
   - Start on aspirin 325mg po
2. Hypertension
   - Consider lisinopril 5mg bid
3. Anxiety related to chest pain
   - Reassurance provided

Follow up in 24 hours or sooner if symptoms worsen.`;

  // Load sample data
  useEffect(() => {
    setTranscriptText(sampleTranscript);
  }, []);

  // Process medical transcription
  const processTranscription = useCallback(async () => {
    if (!transcriptText.trim()) {
      alert('Please enter transcript text to process.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/medical/process-transcription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript_text: transcriptText,
          metadata: {
            ...metadata,
            user_id: 'react_user'
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
    } catch (error) {
      console.error('Error processing transcription:', error);
      setCurrentResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    } finally {
      setLoading(false);
    }
  }, [transcriptText, metadata, complianceLevel]);

  // Load compliance report
  const loadComplianceReport = useCallback(async () => {
    try {
      const response = await fetch('/api/medical/compliance-report');
      if (response.ok) {
        const report = await response.json();
        setComplianceReport(report);
      }
    } catch (error) {
      console.error('Error loading compliance report:', error);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'compliance') {
      loadComplianceReport();
    }
  }, [activeTab, loadComplianceReport]);

  // Render transcription tab
  const renderTranscriptionTab = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white p-6 rounded-lg">
        <div className="flex items-center space-x-3">
          <Stethoscope className="w-8 h-8" />
          <div>
            <h1 className="text-2xl font-bold">Medical Transcription Processing</h1>
            <p className="opacity-90">HIPAA-compliant medical transcription with specialized NLP</p>
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
              onClick={() => setTranscriptText(sampleTranscript)}
              className="text-sm text-green-600 hover:text-green-700"
            >
              Load Sample
            </button>
            <button
              onClick={() => setTranscriptText('')}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Clear
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

      {/* Results */}
      {currentResult && (
        <div className="space-y-6">
          {currentResult.success ? (
            <>
              {/* Success Message */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  <h3 className="text-green-800 font-medium">Transcript processed successfully!</h3>
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

              {/* Comprehensive Analysis Dashboard */}
              {currentResult.comprehensive_analysis && (
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-purple-600" />
                    Comprehensive Clinical Analysis
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    {/* Patient Engagement Score */}
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-3xl font-bold text-purple-600">
                        {currentResult.comprehensive_analysis.patient_engagement_score.toFixed(1)}
                      </div>
                      <div className="text-sm text-gray-600">Patient Engagement Score</div>
                    </div>
                    
                    {/* Care Quality Status */}
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-lg font-medium text-blue-600">
                        {currentResult.comprehensive_analysis.care_quality_indicators.filter(i => i.status === 'excellent').length}
                      </div>
                      <div className="text-sm text-gray-600">Excellent Indicators</div>
                    </div>
                    
                    {/* High Priority Recommendations */}
                    <div className="text-center p-4 bg-orange-50 rounded-lg">
                      <div className="text-lg font-medium text-orange-600">
                        {currentResult.comprehensive_analysis.clinical_decision_support.filter(r => r.priority === 'high').length}
                      </div>
                      <div className="text-sm text-gray-600">High Priority Actions</div>
                    </div>
                  </div>

                  {/* Care Quality Indicators */}
                  <div className="mb-6">
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
                            <span className="font-medium">{indicator.indicator}</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              indicator.status === 'excellent' ? 'bg-green-100 text-green-800' :
                              indicator.status === 'good' ? 'bg-blue-100 text-blue-800' :
                              indicator.status === 'needs_improvement' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {indicator.status.replace('_', ' ')}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{indicator.details}</p>
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
                          <p className="text-sm text-gray-700">{recommendation.recommendation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Clinical Information Summary */}
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

              {/* Advanced Clinical Data Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Vital Signs */}
                {currentResult.vital_signs && currentResult.vital_signs.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <Activity className="w-5 h-5 mr-2 text-indigo-600" />
                      Vital Signs ({currentResult.vital_signs.length})
                    </h3>
                    <div className="space-y-3">
                      {currentResult.vital_signs.map((vital, index) => (
                        <div key={index} className="border-l-4 border-indigo-500 pl-3">
                          <div className="font-medium text-gray-900">{vital.type}</div>
                          <div className="text-sm text-gray-600">
                            {vital.value} {vital.unit}
                          </div>
                          {vital.interpretation && (
                            <div className="text-xs text-gray-500 mt-1">{vital.interpretation}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Test Results */}
                {currentResult.test_results && currentResult.test_results.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <Microscope className="w-5 h-5 mr-2 text-teal-600" />
                      Test Results ({currentResult.test_results.length})
                    </h3>
                    <div className="space-y-3">
                      {currentResult.test_results.map((test, index) => (
                        <div key={index} className={`border-l-4 pl-3 ${
                          test.abnormal ? 'border-red-500' : 'border-teal-500'
                        }`}>
                          <div className="font-medium text-gray-900">{test.test_name}</div>
                          <div className="text-sm text-gray-600">{test.value}</div>
                          {test.reference_range && (
                            <div className="text-xs text-gray-500">Ref: {test.reference_range}</div>
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

                {/* Voice Biomarkers */}
                {currentResult.voice_biomarkers && currentResult.voice_biomarkers.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <Activity className="w-5 h-5 mr-2 text-purple-600" />
                      Voice Biomarkers ({currentResult.voice_biomarkers.length})
                    </h3>
                    <div className="space-y-3">
                      {currentResult.voice_biomarkers.map((biomarker, index) => (
                        <div key={index} className="border-l-4 border-purple-500 pl-3">
                          <div className="font-medium text-gray-900">{biomarker.biomarker_type}</div>
                          <div className="text-sm text-gray-600">Value: {biomarker.value}</div>
                          <div className="text-sm text-gray-600">
                            Confidence: {(biomarker.confidence * 100).toFixed(1)}%
                          </div>
                          <div className="text-xs text-purple-600 mt-1">{biomarker.interpretation}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Emotional State */}
                {currentResult.emotional_state && currentResult.emotional_state.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <Heart className="w-5 h-5 mr-2 text-pink-600" />
                      Emotional State ({currentResult.emotional_state.length})
                    </h3>
                    <div className="space-y-3">
                      {currentResult.emotional_state.map((emotion, index) => (
                        <div key={index} className="border-l-4 border-pink-500 pl-3">
                          <div className="font-medium text-gray-900">{emotion.emotion}</div>
                          <div className="text-sm text-gray-600">Intensity: {emotion.intensity}/10</div>
                          <div className="text-xs text-gray-500 mt-1">{emotion.context}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Environmental and Social Context */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Ambient Sounds */}
                {currentResult.ambient_sounds && currentResult.ambient_sounds.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <Activity className="w-5 h-5 mr-2 text-orange-600" />
                      Ambient Environmental Analysis
                    </h3>
                    <div className="space-y-3">
                      {currentResult.ambient_sounds.map((sound, index) => (
                        <div key={index} className="border-l-4 border-orange-500 pl-3">
                          <div className="font-medium text-gray-900">{sound.sound_type}</div>
                          <div className="text-sm text-gray-600">Duration: {sound.duration}s</div>
                          <div className="text-xs text-gray-500 mt-1">{sound.context}</div>
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

                {/* Social Determinants */}
                {currentResult.social_determinants && currentResult.social_determinants.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <Users className="w-5 h-5 mr-2 text-emerald-600" />
                      Social Determinants of Health
                    </h3>
                    <div className="space-y-3">
                      {currentResult.social_determinants.map((determinant, index) => (
                        <div key={index} className={`border-l-4 pl-3 ${
                          determinant.impact_level === 'high' ? 'border-red-500' :
                          determinant.impact_level === 'medium' ? 'border-yellow-500' :
                          'border-emerald-500'
                        }`}>
                          <div className="font-medium text-gray-900">{determinant.factor}</div>
                          <div className="text-sm text-gray-600">Category: {determinant.category}</div>
                          <div className={`text-xs mt-1 font-medium ${
                            determinant.impact_level === 'high' ? 'text-red-600' :
                            determinant.impact_level === 'medium' ? 'text-yellow-600' :
                            'text-emerald-600'
                          }`}>
                            Impact: {determinant.impact_level}
                          </div>
                          {determinant.notes && (
                            <div className="text-xs text-gray-500 mt-1">{determinant.notes}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Medical Report Sections */}
              {currentResult.sections && Object.keys(currentResult.sections).length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <FileText className="w-5 h-5 mr-2" />
                    Generated Medical Report
                  </h3>
                  <div className="space-y-4">
                    {Object.entries(currentResult.sections).map(([sectionName, content]) => (
                      content.trim() && (
                        <div key={sectionName} className="border-l-4 border-green-500 pl-4 py-2">
                          <h4 className="font-medium text-gray-900 mb-2">
                            {sectionName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </h4>
                          <p className="text-gray-700 leading-relaxed">{content}</p>
                        </div>
                      )
                    ))}
                  </div>
                </div>
              )}

              {/* Compliance Status */}
              {currentResult.compliance_status && (
                <div className={`rounded-lg p-4 ${
                  currentResult.compliance_status === 'compliant' ? 'bg-green-50 border border-green-200' :
                  currentResult.compliance_status === 'pending_review' ? 'bg-yellow-50 border border-yellow-200' :
                  'bg-red-50 border border-red-200'
                }`}>
                  <div className="flex items-center">
                    {currentResult.compliance_status === 'compliant' ? (
                      <>
                        <Shield className="w-5 h-5 text-green-600 mr-2" />
                        <h3 className="text-green-800 font-medium">HIPAA Compliant</h3>
                      </>
                    ) : currentResult.compliance_status === 'pending_review' ? (
                      <>
                        <Clock className="w-5 h-5 text-yellow-600 mr-2" />
                        <h3 className="text-yellow-800 font-medium">Pending Review</h3>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5 text-red-600 mr-2" />
                        <h3 className="text-red-800 font-medium">Compliance Issue</h3>
                      </>
                    )}
                  </div>
                  <p className={`mt-2 ${
                    currentResult.compliance_status === 'compliant' ? 'text-green-700' :
                    currentResult.compliance_status === 'pending_review' ? 'text-yellow-700' :
                    'text-red-700'
                  }`}>
                    {currentResult.compliance_status === 'compliant' 
                      ? 'This transcript meets HIPAA compliance requirements.'
                      : currentResult.compliance_status === 'pending_review'
                      ? 'This transcript requires manual review for final compliance approval.'
                      : 'This transcript has compliance issues that need to be addressed.'
                    }
                  </p>
                </div>
              )}
            </>
          ) : (
            /* Error Message */
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <XCircle className="w-5 h-5 text-red-600 mr-2" />
                <h3 className="text-red-800 font-medium">Processing Failed</h3>
              </div>
              <p className="text-red-700 mt-2">{currentResult.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );

  // Render other tabs with placeholder content
  const renderReportsTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <FileText className="w-5 h-5 mr-2" />
          Medical Reports ({reports.length})
        </h2>
        
        {reports.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No reports generated yet. Process a transcript first!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <div key={report.report_id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900">
                    {report.patient_id} - {report.report_type.replace('_', ' ').toUpperCase()}
                  </h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    report.compliance_status === 'compliant' ? 'bg-green-100 text-green-800' :
                    report.compliance_status === 'pending_review' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {report.compliance_status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">
                  Provider: {report.provider_id} | Created: {new Date(report.created_at).toLocaleString()}
                </p>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>{report.entities.length} entities</span>
                  <span>{report.medications.length} medications</span>
                  <span>{report.procedures.length} procedures</span>
                  <span>{report.diagnoses.length} diagnoses</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderEntitiesTab = () => (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <Search className="w-5 h-5 mr-2" />
        Medical Entity Analysis
      </h2>
      <div className="text-center py-8 text-gray-500">
        <Search className="w-16 h-16 mx-auto mb-4 opacity-50" />
        <p>Entity analysis will be displayed here after processing transcripts.</p>
      </div>
    </div>
  );

  const renderComplianceTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Shield className="w-5 h-5 mr-2" />
          HIPAA Compliance Dashboard
        </h2>
        
        {complianceReport ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-600">
                {complianceReport.summary.total_transcriptions}
              </div>
              <div className="text-sm text-gray-600">Total Transcriptions</div>
            </div>
            
            <div className="bg-yellow-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {complianceReport.summary.phi_incidents_detected}
              </div>
              <div className="text-sm text-gray-600">PHI Incidents</div>
            </div>
            
            <div className="bg-red-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-red-600">
                {complianceReport.summary.unresolved_phi_incidents}
              </div>
              <div className="text-sm text-gray-600">Unresolved PHI</div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-green-600">
                {complianceReport.summary.compliance_rate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Compliance Rate</div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Shield className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Loading compliance report...</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderAnalyticsTab = () => (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <BarChart3 className="w-5 h-5 mr-2" />
        Medical Transcription Analytics
      </h2>
      <div className="text-center py-8 text-gray-500">
        <TrendingUp className="w-16 h-16 mx-auto mb-4 opacity-50" />
        <p>Analytics and trends will be displayed here.</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'transcription', label: 'Transcription', icon: Stethoscope },
              { id: 'reports', label: 'Reports', icon: FileText },
              { id: 'entities', label: 'Entities', icon: Search },
              { id: 'compliance', label: 'Compliance', icon: Shield },
              { id: 'analytics', label: 'Analytics', icon: BarChart3 }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'transcription' && renderTranscriptionTab()}
        {activeTab === 'reports' && renderReportsTab()}
        {activeTab === 'entities' && renderEntitiesTab()}
        {activeTab === 'compliance' && renderComplianceTab()}
        {activeTab === 'analytics' && renderAnalyticsTab()}
      </div>
    </div>
  );
};

export default MedicalTranscriptionInterface;