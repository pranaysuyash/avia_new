/**
 * Advanced Export Interface - React Component
 * Comprehensive export management with templates, batch operations, and analytics
 * Connects to the Advanced Export System backend
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiDownload,
  FiFileText,
  FiSettings,
  FiClock,
  FiUsers,
  FiTrendingUp,
  FiEdit3,
  FiCopy,
  FiTrash2,
  FiPlay,
  FiPause,
  FiRefreshCw,
  FiFilter,
  FiSearch,
  FiPlus,
  FiChevronDown,
  FiChevronRight,
  FiAlertCircle,
  FiCheckCircle,
  FiXCircle,
  FiLoader
} from 'react-icons/fi';
import { useAccessibility } from '../../../accessibility';

// Interfaces
interface ExportJob {
  id: string;
  name: string;
  userId: string;
  exportType: 'single_transcript' | 'batch_transcripts' | 'custom_template';
  formatType: 'text' | 'json' | 'markdown' | 'docx' | 'pdf' | 'xlsx' | 'csv';
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  progress: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  errorMessage?: string;
  resultFileUrl?: string;
  templateId?: string;
}

interface ExportTemplate {
  id: string;
  name: string;
  description: string;
  templateType: 'meeting_minutes' | 'interview' | 'lecture' | 'legal_deposition' | 'medical_consultation' | 'custom';
  outputFormat: 'markdown' | 'text' | 'html';
  createdBy: string;
  createdAt: string;
  isPublic: boolean;
  tags: string[];
  content: string;
}

interface ExportOptions {
  includeMetadata: boolean;
  includeEntities: boolean;
  includeSummary: boolean;
  includeAnnotations: boolean;
  includeTimestamps: boolean;
  includeConfidence: boolean;
  anonymizeData: boolean;
  customFields?: Record<string, any>;
}

interface AdvancedExportProps {
  transcriptIds?: string[];
  batchJobId?: string;
  onExportComplete?: (job: ExportJob) => void;
  className?: string;
}

export const AdvancedExportInterface: React.FC<AdvancedExportProps> = ({
  transcriptIds = [],
  batchJobId,
  onExportComplete,
  className = ''
}) => {
  // State
  const [activeTab, setActiveTab] = useState<'quick' | 'templates' | 'jobs' | 'analytics' | 'settings'>('quick');
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([]);
  const [templates, setTemplates] = useState<ExportTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<ExportTemplate | null>(null);
  const [isCreatingJob, setIsCreatingJob] = useState(false);
  const [showTemplateEditor, setShowTemplateEditor] = useState(false);
  const [jobFilters, setJobFilters] = useState({
    status: [] as string[],
    priority: [] as string[],
    search: ''
  });

  // Quick export form state
  const [quickExportForm, setQuickExportForm] = useState({
    name: `Export_${new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', '')}`,
    exportType: 'single_transcript' as ExportJob['exportType'],
    formatType: 'markdown' as ExportJob['formatType'],
    priority: 'normal' as ExportJob['priority'],
    templateId: '',
    scheduleTime: '',
    options: {
      includeMetadata: true,
      includeEntities: true,
      includeSummary: true,
      includeAnnotations: true,
      includeTimestamps: false,
      includeConfidence: false,
      anonymizeData: false
    } as ExportOptions
  });

  // Template editor state
  const [templateEditor, setTemplateEditor] = useState({
    name: '',
    description: '',
    templateType: 'custom' as ExportTemplate['templateType'],
    outputFormat: 'markdown' as ExportTemplate['outputFormat'],
    content: '',
    isPublic: false,
    tags: [] as string[]
  });

  // Accessibility
  const { announceToScreenReader } = useAccessibility();

  // Load data on component mount
  useEffect(() => {
    loadExportJobs();
    loadTemplates();
  }, []);

  // Poll for job updates
  useEffect(() => {
    const interval = setInterval(() => {
      const activeJobs = exportJobs.filter(job => 
        job.status === 'pending' || job.status === 'in_progress'
      );
      
      if (activeJobs.length > 0) {
        updateJobStatuses(activeJobs.map(job => job.id));
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [exportJobs]);

  const loadExportJobs = async () => {
    try {
      const response = await fetch('/api/exports/jobs');
      const data = await response.json();
      setExportJobs(data.jobs || []);
    } catch (error) {
      console.error('Failed to load export jobs:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/exports/templates');
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const updateJobStatuses = async (jobIds: string[]) => {
    try {
      const response = await fetch('/api/exports/jobs/status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jobIds })
      });
      
      const data = await response.json();
      
      setExportJobs(prevJobs => 
        prevJobs.map(job => {
          const updated = data.jobs.find((j: ExportJob) => j.id === job.id);
          return updated || job;
        })
      );
    } catch (error) {
      console.error('Failed to update job statuses:', error);
    }
  };

  const createExportJob = async (jobData: any) => {
    setIsCreatingJob(true);
    
    try {
      const response = await fetch('/api/exports/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobData)
      });
      
      const data = await response.json();
      
      if (data.success) {
        announceToScreenReader(`Export job ${data.job.name} created successfully`);
        await loadExportJobs();
        
        if (onExportComplete) {
          onExportComplete(data.job);
        }
      } else {
        throw new Error(data.error || 'Failed to create export job');
      }
    } catch (error) {
      console.error('Failed to create export job:', error);
      announceToScreenReader(`Failed to create export job: ${error.message}`);
    } finally {
      setIsCreatingJob(false);
    }
  };

  const cancelJob = async (jobId: string) => {
    try {
      await fetch(`/api/exports/jobs/${jobId}/cancel`, { method: 'POST' });
      await loadExportJobs();
      announceToScreenReader('Export job cancelled');
    } catch (error) {
      console.error('Failed to cancel job:', error);
    }
  };

  const saveTemplate = async (templateData: any) => {
    try {
      const response = await fetch('/api/exports/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(templateData)
      });
      
      const data = await response.json();
      
      if (data.success) {
        await loadTemplates();
        setShowTemplateEditor(false);
        announceToScreenReader(`Template ${templateData.name} saved successfully`);
      } else {
        throw new Error(data.error || 'Failed to save template');
      }
    } catch (error) {
      console.error('Failed to save template:', error);
      announceToScreenReader(`Failed to save template: ${error.message}`);
    }
  };

  const getStatusIcon = (status: ExportJob['status']) => {
    switch (status) {
      case 'pending': return <FiClock className="text-yellow-500" />;
      case 'in_progress': return <FiLoader className="text-blue-500 animate-spin" />;
      case 'completed': return <FiCheckCircle className="text-green-500" />;
      case 'failed': return <FiXCircle className="text-red-500" />;
      case 'cancelled': return <FiXCircle className="text-gray-500" />;
      default: return <FiAlertCircle className="text-gray-400" />;
    }
  };

  const getPriorityColor = (priority: ExportJob['priority']) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'normal': return 'bg-blue-100 text-blue-800';
      case 'low': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredJobs = exportJobs.filter(job => {
    const statusMatch = jobFilters.status.length === 0 || jobFilters.status.includes(job.status);
    const priorityMatch = jobFilters.priority.length === 0 || jobFilters.priority.includes(job.priority);
    const searchMatch = jobFilters.search === '' || 
      job.name.toLowerCase().includes(jobFilters.search.toLowerCase()) ||
      job.id.toLowerCase().includes(jobFilters.search.toLowerCase());
    
    return statusMatch && priorityMatch && searchMatch;
  });

  const renderQuickExport = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-4">🚀 Quick Export</h3>
        
        {/* Export Name and Type */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Export Name</label>
            <input
              type="text"
              value={quickExportForm.name}
              onChange={(e) => setQuickExportForm({...quickExportForm, name: e.target.value})}
              className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
              placeholder="Enter export name..."
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Priority</label>
            <select
              value={quickExportForm.priority}
              onChange={(e) => setQuickExportForm({...quickExportForm, priority: e.target.value as ExportJob['priority']})}
              className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
        </div>

        {/* Export Type and Format */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Export Source</label>
            <select
              value={quickExportForm.exportType}
              onChange={(e) => setQuickExportForm({...quickExportForm, exportType: e.target.value as ExportJob['exportType']})}
              className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
            >
              <option value="single_transcript">Single Transcript</option>
              <option value="batch_transcripts">Multiple Transcripts</option>
              <option value="custom_template">Custom Template</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Format</label>
            <select
              value={quickExportForm.formatType}
              onChange={(e) => setQuickExportForm({...quickExportForm, formatType: e.target.value as ExportJob['formatType']})}
              className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
            >
              <option value="markdown">Markdown</option>
              <option value="text">Plain Text</option>
              <option value="json">JSON</option>
              <option value="docx">Word Document</option>
              <option value="pdf">PDF</option>
              <option value="xlsx">Excel</option>
              <option value="csv">CSV</option>
            </select>
          </div>
        </div>

        {/* Template Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-text-secondary mb-2">Template (Optional)</label>
          <select
            value={quickExportForm.templateId}
            onChange={(e) => setQuickExportForm({...quickExportForm, templateId: e.target.value})}
            className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
          >
            <option value="">None (Standard Format)</option>
            {templates.map(template => (
              <option key={template.id} value={template.id}>
                {template.name} ({template.templateType})
              </option>
            ))}
          </select>
        </div>

        {/* Export Options */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-text-secondary mb-3">Export Options</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries({
              includeMetadata: 'Include Metadata',
              includeEntities: 'Include Entities', 
              includeSummary: 'Include Summary',
              includeAnnotations: 'Include Annotations',
              includeTimestamps: 'Include Timestamps',
              includeConfidence: 'Include Confidence Scores',
              anonymizeData: 'Anonymize Personal Data'
            }).map(([key, label]) => (
              <label key={key} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={quickExportForm.options[key as keyof ExportOptions] as boolean}
                  onChange={(e) => setQuickExportForm({
                    ...quickExportForm,
                    options: {
                      ...quickExportForm.options,
                      [key]: e.target.checked
                    }
                  })}
                  className="rounded border-border-DEFAULT text-primary-DEFAULT focus:ring-primary-DEFAULT"
                />
                <span className="text-sm text-text-secondary">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Schedule Option */}
        <div className="mb-6">
          <label className="flex items-center space-x-2 mb-2">
            <input
              type="checkbox"
              checked={!!quickExportForm.scheduleTime}
              onChange={(e) => setQuickExportForm({
                ...quickExportForm,
                scheduleTime: e.target.checked ? new Date(Date.now() + 3600000).toISOString().slice(0, 16) : ''
              })}
              className="rounded border-border-DEFAULT text-primary-DEFAULT focus:ring-primary-DEFAULT"
            />
            <span className="text-sm font-medium text-text-secondary">Schedule Export</span>
          </label>
          
          {quickExportForm.scheduleTime && (
            <input
              type="datetime-local"
              value={quickExportForm.scheduleTime}
              onChange={(e) => setQuickExportForm({...quickExportForm, scheduleTime: e.target.value})}
              className="w-full md:w-auto px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
            />
          )}
        </div>

        {/* Create Export Button */}
        <button
          onClick={() => createExportJob({
            ...quickExportForm,
            sourceData: {
              transcriptIds: transcriptIds,
              batchJobId: batchJobId
            }
          })}
          disabled={isCreatingJob}
          className="w-full md:w-auto flex items-center justify-center px-6 py-3 bg-primary-DEFAULT text-primary-contrast rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isCreatingJob ? (
            <>
              <FiLoader className="h-4 w-4 mr-2 animate-spin" />
              Creating Export...
            </>
          ) : (
            <>
              <FiPlay className="h-4 w-4 mr-2" />
              Create Export
            </>
          )}
        </button>
      </div>
    </div>
  );

  const renderTemplateManager = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-text-primary">📋 Template Manager</h3>
        <button
          onClick={() => setShowTemplateEditor(true)}
          className="flex items-center px-4 py-2 bg-primary-DEFAULT text-primary-contrast rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2 transition-colors"
        >
          <FiPlus className="h-4 w-4 mr-2" />
          New Template
        </button>
      </div>

      {/* Template Editor Modal */}
      <AnimatePresence>
        {showTemplateEditor && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="bg-white rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="p-6 border-b border-border-DEFAULT">
                <h4 className="text-lg font-semibold text-text-primary">Create New Template</h4>
              </div>
              
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">Template Name</label>
                    <input
                      type="text"
                      value={templateEditor.name}
                      onChange={(e) => setTemplateEditor({...templateEditor, name: e.target.value})}
                      className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
                      placeholder="Enter template name..."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">Template Type</label>
                    <select
                      value={templateEditor.templateType}
                      onChange={(e) => setTemplateEditor({...templateEditor, templateType: e.target.value as ExportTemplate['templateType']})}
                      className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
                    >
                      <option value="custom">Custom</option>
                      <option value="meeting_minutes">Meeting Minutes</option>
                      <option value="interview">Interview</option>
                      <option value="lecture">Lecture</option>
                      <option value="legal_deposition">Legal Deposition</option>
                      <option value="medical_consultation">Medical Consultation</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Description</label>
                  <textarea
                    value={templateEditor.description}
                    onChange={(e) => setTemplateEditor({...templateEditor, description: e.target.value})}
                    className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
                    rows={3}
                    placeholder="Describe your template..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Template Content (Jinja2 syntax)</label>
                  <textarea
                    value={templateEditor.content}
                    onChange={(e) => setTemplateEditor({...templateEditor, content: e.target.value})}
                    className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT font-mono"
                    rows={12}
                    placeholder="# {{ title }}

{{ transcript }}

{% if entities %}
## Entities
{% for entity_type, entity_list in entities.items() %}
**{{ entity_type }}**: {{ entity_list | join(', ') }}
{% endfor %}
{% endif %}"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={templateEditor.isPublic}
                      onChange={(e) => setTemplateEditor({...templateEditor, isPublic: e.target.checked})}
                      className="rounded border-border-DEFAULT text-primary-DEFAULT focus:ring-primary-DEFAULT"
                    />
                    <span className="text-sm text-text-secondary">Make Public</span>
                  </label>
                </div>
              </div>
              
              <div className="p-6 border-t border-border-DEFAULT flex items-center justify-end space-x-3">
                <button
                  onClick={() => setShowTemplateEditor(false)}
                  className="px-4 py-2 text-text-secondary border border-border-DEFAULT rounded-md hover:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => saveTemplate(templateEditor)}
                  className="px-4 py-2 bg-primary-DEFAULT text-primary-contrast rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2 transition-colors"
                >
                  Save Template
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Templates List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map(template => (
          <div key={template.id} className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-medium text-text-primary">{template.name}</h4>
                <p className="text-sm text-text-secondary capitalize">{template.templateType.replace('_', ' ')}</p>
              </div>
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => setSelectedTemplate(template)}
                  className="p-2 text-text-secondary hover:text-primary-DEFAULT focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded"
                  title="Edit template"
                >
                  <FiEdit3 className="h-4 w-4" />
                </button>
                <button
                  className="p-2 text-text-secondary hover:text-primary-DEFAULT focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded"
                  title="Copy template"
                >
                  <FiCopy className="h-4 w-4" />
                </button>
              </div>
            </div>
            
            <p className="text-sm text-text-secondary mb-3">{template.description}</p>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {template.isPublic && (
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Public</span>
                )}
                <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">{template.outputFormat}</span>
              </div>
              
              {template.tags.length > 0 && (
                <div className="flex items-center space-x-1">
                  {template.tags.slice(0, 2).map(tag => (
                    <span key={tag} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {tag}
                    </span>
                  ))}
                  {template.tags.length > 2 && (
                    <span className="text-xs text-text-secondary">+{template.tags.length - 2}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {templates.length === 0 && (
        <div className="text-center py-12">
          <FiFileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-text-primary mb-2">No Templates Yet</h3>
          <p className="text-text-secondary mb-4">Create your first custom export template to get started.</p>
          <button
            onClick={() => setShowTemplateEditor(true)}
            className="px-4 py-2 bg-primary-DEFAULT text-primary-contrast rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2 transition-colors"
          >
            Create Template
          </button>
        </div>
      )}
    </div>
  );

  const renderJobMonitor = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-text-primary">📊 Job Monitor</h3>
        <button
          onClick={loadExportJobs}
          className="flex items-center px-3 py-2 text-text-secondary border border-border-DEFAULT rounded-md hover:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT transition-colors"
        >
          <FiRefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Search</label>
            <div className="relative">
              <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <input
                type="text"
                value={jobFilters.search}
                onChange={(e) => setJobFilters({...jobFilters, search: e.target.value})}
                className="w-full pl-10 pr-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
                placeholder="Search jobs..."
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Status</label>
            <select
              multiple
              value={jobFilters.status}
              onChange={(e) => setJobFilters({
                ...jobFilters, 
                status: Array.from(e.target.selectedOptions, option => option.value)
              })}
              className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
            >
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Priority</label>
            <select
              multiple
              value={jobFilters.priority}
              onChange={(e) => setJobFilters({
                ...jobFilters,
                priority: Array.from(e.target.selectedOptions, option => option.value)
              })}
              className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
            >
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="normal">Normal</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Jobs List */}
      <div className="space-y-4">
        <AnimatePresence>
          {filteredJobs.map(job => (
            <motion.div
              key={job.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(job.status)}
                  <div>
                    <h4 className="font-medium text-text-primary">{job.name}</h4>
                    <p className="text-sm text-text-secondary">
                      {job.exportType} • {job.formatType} • Created {new Date(job.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className={`text-xs px-2 py-1 rounded ${getPriorityColor(job.priority)}`}>
                    {job.priority}
                  </span>
                  
                  {job.status === 'in_progress' || job.status === 'pending' ? (
                    <button
                      onClick={() => cancelJob(job.id)}
                      className="text-red-600 hover:text-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 rounded p-1"
                      title="Cancel job"
                    >
                      <FiXCircle className="h-4 w-4" />
                    </button>
                  ) : job.resultFileUrl ? (
                    <a
                      href={job.resultFileUrl}
                      className="text-primary-DEFAULT hover:text-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded p-1"
                      title="Download result"
                    >
                      <FiDownload className="h-4 w-4" />
                    </a>
                  ) : null}
                </div>
              </div>
              
              {/* Progress Bar */}
              {job.status === 'in_progress' && (
                <div className="mb-3">
                  <div className="flex items-center justify-between text-sm text-text-secondary mb-1">
                    <span>Progress</span>
                    <span>{job.progress}%</span>
                  </div>
                  <div className="w-full bg-background-secondary rounded-full h-2">
                    <div
                      className="bg-primary-DEFAULT h-2 rounded-full transition-all duration-300"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                </div>
              )}
              
              {/* Error Message */}
              {job.errorMessage && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                  {job.errorMessage}
                </div>
              )}
              
              {/* Job Details */}
              <div className="text-xs text-text-secondary grid grid-cols-1 md:grid-cols-3 gap-2 mt-3">
                <span>ID: {job.id.slice(0, 8)}...</span>
                {job.startedAt && <span>Started: {new Date(job.startedAt).toLocaleString()}</span>}
                {job.completedAt && <span>Completed: {new Date(job.completedAt).toLocaleString()}</span>}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {filteredJobs.length === 0 && (
          <div className="text-center py-12">
            <FiTrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-text-primary mb-2">No Export Jobs</h3>
            <p className="text-text-secondary">No export jobs match your current filters.</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-text-primary">📈 Export Analytics</h3>
      
      {/* Analytics cards would go here */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Total Exports</p>
              <p className="text-2xl font-semibold text-text-primary">{exportJobs.length}</p>
            </div>
            <FiTrendingUp className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Success Rate</p>
              <p className="text-2xl font-semibold text-green-600">
                {exportJobs.length > 0 ? Math.round((exportJobs.filter(j => j.status === 'completed').length / exportJobs.length) * 100) : 0}%
              </p>
            </div>
            <FiCheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Active Jobs</p>
              <p className="text-2xl font-semibold text-blue-600">
                {exportJobs.filter(j => j.status === 'pending' || j.status === 'in_progress').length}
              </p>
            </div>
            <FiLoader className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Templates</p>
              <p className="text-2xl font-semibold text-purple-600">{templates.length}</p>
            </div>
            <FiFileText className="h-8 w-8 text-purple-500" />
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-6">
        <h4 className="text-lg font-medium text-text-primary mb-4">Export Analytics Coming Soon</h4>
        <p className="text-text-secondary">Detailed analytics including format popularity, processing times, and usage trends will be available here.</p>
      </div>
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-text-primary">⚙️ Export Settings</h3>
      
      <div className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-6">
        <h4 className="text-lg font-medium text-text-primary mb-4">Export Settings Coming Soon</h4>
        <p className="text-text-secondary">Configuration options for default formats, storage settings, and notification preferences will be available here.</p>
      </div>
    </div>
  );

  return (
    <div className={`advanced-export-interface bg-background-primary ${className}`}>
      {/* Header */}
      <div className="bg-white border-b border-border-DEFAULT p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">📤 Advanced Export System</h1>
            <p className="text-text-secondary">Professional export tools with templates and analytics</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-background-secondary rounded-lg p-1">
          {[
            { id: 'quick', label: '🚀 Quick Export', icon: FiPlay },
            { id: 'templates', label: '📋 Templates', icon: FiFileText },
            { id: 'jobs', label: '📊 Jobs', icon: FiTrendingUp },
            { id: 'analytics', label: '📈 Analytics', icon: FiTrendingUp },
            { id: 'settings', label: '⚙️ Settings', icon: FiSettings }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-white text-primary-DEFAULT shadow-sm'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'quick' && renderQuickExport()}
            {activeTab === 'templates' && renderTemplateManager()}
            {activeTab === 'jobs' && renderJobMonitor()}
            {activeTab === 'analytics' && renderAnalytics()}
            {activeTab === 'settings' && renderSettings()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default AdvancedExportInterface;