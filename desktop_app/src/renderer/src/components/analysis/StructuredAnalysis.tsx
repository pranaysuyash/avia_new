import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  AlertCircle, 
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Copy,
  FileJson,
  Table,
  Info
} from 'lucide-react';
import { api } from '../../services/api';

interface AnalysisTemplate {
  name: string;
  domain: string;
  description: string;
  schema?: any;
}

interface AnalysisResult {
  template_name: string;
  domain: string;
  confidence: number;
  processing_time: number;
  data: any;
  validation_errors: string[];
  analyzed_at: string;
}

interface StructuredAnalysisProps {
  text: string;
  onAnalysisComplete?: (result: AnalysisResult) => void;
}

export const StructuredAnalysis: React.FC<StructuredAnalysisProps> = ({ text, onAnalysisComplete }) => {
  const [templates, setTemplates] = useState<AnalysisTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [domainFilter, setDomainFilter] = useState<string>('All');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string>('');
  const [showSchemaPreview, setShowSchemaPreview] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/structured-analysis/templates');
      setTemplates(response.data.templates);
      if (response.data.templates.length > 0) {
        setSelectedTemplate(response.data.templates[0].name);
      }
    } catch (err) {
      setError('Failed to load analysis templates');
    }
  };

  const filteredTemplates = domainFilter === 'All' 
    ? templates 
    : templates.filter(t => t.domain === domainFilter);

  const domains = ['All', ...Array.from(new Set(templates.map(t => t.domain)))];

  const selectedTemplateInfo = templates.find(t => t.name === selectedTemplate);

  const performAnalysis = async () => {
    if (!text || !text.trim()) {
      setError('Please provide text for analysis');
      return;
    }

    setIsAnalyzing(true);
    setError('');
    setAnalysisResult(null);

    try {
      const response = await api.post('/structured-analysis/analyze', {
        text,
        template_name: selectedTemplate
      });

      setAnalysisResult(response.data);
      if (onAnalysisComplete) {
        onAnalysisComplete(response.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const exportAnalysis = async (format: 'json' | 'csv') => {
    if (!analysisResult) return;

    try {
      const response = await api.post('/structured-analysis/export', {
        result: analysisResult,
        format
      });

      const blob = new Blob([response.data], {
        type: format === 'json' ? 'application/json' : 'text/csv'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${analysisResult.template_name}_analysis_${new Date().toISOString()}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Failed to export as ${format}`);
    }
  };

  const copyToClipboard = () => {
    if (!analysisResult) return;
    navigator.clipboard.writeText(JSON.stringify(analysisResult.data, null, 2));
  };

  const renderAnalysisResults = () => {
    if (!analysisResult) return null;

    return (
      <div className="mt-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Analysis Results</h3>
          <div className="flex gap-2">
            <button
              onClick={() => exportAnalysis('json')}
              className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <FileJson className="w-4 h-4" />
              Export JSON
            </button>
            <button
              onClick={() => exportAnalysis('csv')}
              className="flex items-center gap-2 px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
            >
              <Table className="w-4 h-4" />
              Export CSV
            </button>
            <button
              onClick={copyToClipboard}
              className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              <Copy className="w-4 h-4" />
              Copy
            </button>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded p-3">
            <div className="text-sm text-gray-400">Template</div>
            <div className="text-lg font-semibold">{analysisResult.template_name}</div>
          </div>
          <div className="bg-gray-800 rounded p-3">
            <div className="text-sm text-gray-400">Domain</div>
            <div className="text-lg font-semibold capitalize">{analysisResult.domain}</div>
          </div>
          <div className="bg-gray-800 rounded p-3">
            <div className="text-sm text-gray-400">Confidence</div>
            <div className="text-lg font-semibold">{(analysisResult.confidence * 100).toFixed(1)}%</div>
          </div>
          <div className="bg-gray-800 rounded p-3">
            <div className="text-sm text-gray-400">Processing Time</div>
            <div className="text-lg font-semibold">{analysisResult.processing_time.toFixed(2)}s</div>
          </div>
        </div>

        {analysisResult.validation_errors.length > 0 ? (
          <div className="bg-yellow-900/20 border border-yellow-700 rounded p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-5 h-5 text-yellow-500" />
              <span className="font-semibold">Schema validation issues:</span>
            </div>
            <ul className="list-disc list-inside text-sm">
              {analysisResult.validation_errors.map((error, idx) => (
                <li key={idx}>{error}</li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="bg-green-900/20 border border-green-700 rounded p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span>Data validates against schema</span>
            </div>
          </div>
        )}

        <div className="bg-gray-800 rounded p-4">
          <h4 className="font-semibold mb-3">Extracted Data</h4>
          {renderDomainSpecificResults()}
        </div>
      </div>
    );
  };

  const renderDomainSpecificResults = () => {
    if (!analysisResult) return null;

    switch (analysisResult.domain) {
      case 'medical':
        return <MedicalResults data={analysisResult.data} />;
      case 'legal':
        return <LegalResults data={analysisResult.data} />;
      case 'business':
        return <BusinessResults data={analysisResult.data} />;
      case 'educational':
        return <EducationalResults data={analysisResult.data} />;
      default:
        return <GenericResults data={analysisResult.data} />;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-5 h-5" />
        <h2 className="text-xl font-semibold">Structured Analysis</h2>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Analysis Template</label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
          >
            {filteredTemplates.map(template => (
              <option key={template.name} value={template.name}>
                {template.name} ({template.domain})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Filter by Domain</label>
          <select
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
          >
            {domains.map(domain => (
              <option key={domain} value={domain}>{domain}</option>
            ))}
          </select>
        </div>
      </div>

      {selectedTemplateInfo && (
        <div className="bg-blue-900/20 border border-blue-700 rounded p-3">
          <div className="flex items-start gap-2">
            <Info className="w-5 h-5 text-blue-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm">{selectedTemplateInfo.description}</p>
              <button
                onClick={() => setShowSchemaPreview(!showSchemaPreview)}
                className="mt-2 text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                {showSchemaPreview ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                View Schema Structure
              </button>
            </div>
          </div>
          {showSchemaPreview && selectedTemplateInfo.schema && (
            <pre className="mt-3 p-3 bg-gray-900 rounded text-xs overflow-x-auto">
              {JSON.stringify(selectedTemplateInfo.schema, null, 2)}
            </pre>
          )}
        </div>
      )}

      <button
        onClick={performAnalysis}
        disabled={isAnalyzing || !text}
        className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isAnalyzing ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            Analyzing...
          </>
        ) : (
          <>
            <FileText className="w-4 h-4" />
            Perform Analysis
          </>
        )}
      </button>

      {error && (
        <div className="bg-red-900/20 border border-red-700 rounded p-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {renderAnalysisResults()}
    </div>
  );
};

// Domain-specific result components
const MedicalResults: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4">
    {data.summary && (
      <div>
        <h5 className="font-semibold mb-1">Clinical Summary</h5>
        <p className="text-sm text-gray-300">{data.summary}</p>
      </div>
    )}
    <div className="grid grid-cols-2 gap-4">
      <div>
        {data.patient_info && (
          <div className="mb-3">
            <h5 className="font-semibold mb-1">Patient Information</h5>
            <ul className="text-sm space-y-1">
              {data.patient_info.age && <li>Age: {data.patient_info.age}</li>}
              {data.patient_info.gender && <li>Gender: {data.patient_info.gender}</li>}
              {data.patient_info.medical_record_number && <li>MRN: {data.patient_info.medical_record_number}</li>}
            </ul>
          </div>
        )}
        {data.symptoms && data.symptoms.length > 0 && (
          <div className="mb-3">
            <h5 className="font-semibold mb-1">Symptoms</h5>
            <ul className="text-sm space-y-1">
              {data.symptoms.map((symptom: string, idx: number) => (
                <li key={idx}>• {symptom}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <div>
        {data.medications && data.medications.length > 0 && (
          <div className="mb-3">
            <h5 className="font-semibold mb-1">Medications</h5>
            <ul className="text-sm space-y-1">
              {data.medications.map((med: any, idx: number) => (
                <li key={idx}>
                  • {med.name}
                  {med.dosage && ` - ${med.dosage}`}
                  {med.frequency && ` (${med.frequency})`}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  </div>
);

const LegalResults: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4">
    {data.summary && (
      <div>
        <h5 className="font-semibold mb-1">Legal Summary</h5>
        <p className="text-sm text-gray-300">{data.summary}</p>
      </div>
    )}
    <div className="grid grid-cols-2 gap-4">
      <div>
        {data.case_info && (
          <div className="mb-3">
            <h5 className="font-semibold mb-1">Case Information</h5>
            <ul className="text-sm space-y-1">
              {data.case_info.case_number && <li>Case Number: {data.case_info.case_number}</li>}
              {data.case_info.case_type && <li>Type: {data.case_info.case_type}</li>}
              {data.case_info.jurisdiction && <li>Jurisdiction: {data.case_info.jurisdiction}</li>}
            </ul>
          </div>
        )}
      </div>
      <div>
        {data.statutes_cited && data.statutes_cited.length > 0 && (
          <div className="mb-3">
            <h5 className="font-semibold mb-1">Statutes Cited</h5>
            <ul className="text-sm space-y-1">
              {data.statutes_cited.map((statute: string, idx: number) => (
                <li key={idx}>• {statute}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  </div>
);

const BusinessResults: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4">
    {data.summary && (
      <div>
        <h5 className="font-semibold mb-1">Executive Summary</h5>
        <p className="text-sm text-gray-300">{data.summary}</p>
      </div>
    )}
    <div className="grid grid-cols-2 gap-4">
      <div>
        {data.meeting_info && (
          <div className="mb-3">
            <h5 className="font-semibold mb-1">Meeting Information</h5>
            <ul className="text-sm space-y-1">
              {data.meeting_info.title && <li>Title: {data.meeting_info.title}</li>}
              {data.meeting_info.date && <li>Date: {data.meeting_info.date}</li>}
              {data.meeting_info.meeting_type && <li>Type: {data.meeting_info.meeting_type}</li>}
            </ul>
          </div>
        )}
      </div>
      <div>
        {data.action_items && data.action_items.length > 0 && (
          <div className="mb-3">
            <h5 className="font-semibold mb-1">Action Items</h5>
            <ul className="text-sm space-y-1">
              {data.action_items.map((item: any, idx: number) => (
                <li key={idx}>
                  • {item.task}
                  {item.assignee && ` (${item.assignee})`}
                  {item.deadline && ` - Due: ${item.deadline}`}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  </div>
);

const EducationalResults: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4">
    {data.summary && (
      <div>
        <h5 className="font-semibold mb-1">Educational Summary</h5>
        <p className="text-sm text-gray-300">{data.summary}</p>
      </div>
    )}
    <div className="grid grid-cols-2 gap-4">
      <div>
        {data.course_info && (
          <div className="mb-3">
            <h5 className="font-semibold mb-1">Course Information</h5>
            <ul className="text-sm space-y-1">
              {data.course_info.subject && <li>Subject: {data.course_info.subject}</li>}
              {data.course_info.level && <li>Level: {data.course_info.level}</li>}
              {data.course_info.instructor && <li>Instructor: {data.course_info.instructor}</li>}
            </ul>
          </div>
        )}
      </div>
      <div>
        {data.key_concepts && data.key_concepts.length > 0 && (
          <div className="mb-3">
            <h5 className="font-semibold mb-1">Key Concepts</h5>
            <ul className="text-sm space-y-1">
              {data.key_concepts.map((concept: any, idx: number) => (
                <li key={idx}>
                  <strong>{concept.concept}:</strong> {concept.definition}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  </div>
);

const GenericResults: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-3">
    {Object.entries(data).map(([key, value]) => (
      <div key={key}>
        <h5 className="font-semibold mb-1">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h5>
        {Array.isArray(value) ? (
          <ul className="text-sm space-y-1">
            {value.map((item, idx) => (
              <li key={idx}>
                {typeof item === 'object' ? 
                  Object.entries(item).map(([k, v]) => `${k}: ${v}`).join(' - ') : 
                  `• ${item}`
                }
              </li>
            ))}
          </ul>
        ) : typeof value === 'object' && value !== null ? (
          <ul className="text-sm space-y-1">
            {Object.entries(value).map(([k, v]) => (
              <li key={k}>{k.replace(/_/g, ' ')}: {String(v)}</li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-gray-300">{String(value)}</p>
        )}
      </div>
    ))}
  </div>
);

export default StructuredAnalysis;