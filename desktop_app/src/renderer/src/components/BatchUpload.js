import React, { useState, useRef } from 'react';
import api from '../services/api';
import analytics from '../utils/analytics';

const BatchUpload = ({ onClose, toast, onBatchStart }) => {
  const [files, setFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [settings, setSettings] = useState({
    language: 'auto',
    model: 'base',
    enableDiarization: true,
    extractEntities: true,
    parallelProcessing: true,
    maxConcurrent: 3
  });
  const fileInputRef = useRef(null);

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files);
    const audioVideoFiles = selectedFiles.filter(file => {
      const type = file.type.toLowerCase();
      return type.startsWith('audio/') || type.startsWith('video/');
    });

    if (audioVideoFiles.length < selectedFiles.length) {
      toast.warning(`${selectedFiles.length - audioVideoFiles.length} non-audio/video files were filtered out`);
    }

    const newFiles = audioVideoFiles.map(file => ({
      id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file: file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0,
      error: null
    }));

    setFiles([...files, ...newFiles]);
    analytics.trackFeatureUsage('batch-upload', 'files-selected', { count: newFiles.length });
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();

    const droppedFiles = Array.from(event.dataTransfer.files);
    const audioVideoFiles = droppedFiles.filter(file => {
      const type = file.type.toLowerCase();
      return type.startsWith('audio/') || type.startsWith('video/');
    });

    const newFiles = audioVideoFiles.map(file => ({
      id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file: file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0,
      error: null
    }));

    setFiles([...files, ...newFiles]);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const removeFile = (fileId) => {
    setFiles(files.filter(f => f.id !== fileId));
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return (
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'processing':
        return (
          <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
        );
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const processFiles = async () => {
    if (files.length === 0) {
      toast.error('No files selected');
      return;
    }

    setProcessing(true);
    analytics.trackFeatureUsage('batch-upload', 'processing-started', { 
      fileCount: files.length,
      settings: settings 
    });

    const batchId = `batch-${Date.now()}`;
    const processingQueue = [...files];
    let activeProcessing = 0;
    let completed = 0;
    let failed = 0;

    const processNextFile = async () => {
      if (processingQueue.length === 0 || activeProcessing >= settings.maxConcurrent) {
        return;
      }

      const fileToProcess = processingQueue.shift();
      activeProcessing++;

      // Update file status
      setFiles(prev => prev.map(f => 
        f.id === fileToProcess.id 
          ? { ...f, status: 'processing', progress: 10 }
          : f
      ));

      try {
        // Use real API for batch processing
        const response = await api.processBatch([fileToProcess], {
          language: settings.language,
          model: settings.model,
          enableDiarization: settings.enableDiarization,
          extractEntities: settings.extractEntities
        });

        if (response.data && response.data.results && response.data.results[0]) {
          const result = response.data.results[0];
          if (result.status === 'completed') {
            setFiles(prev => prev.map(f => 
              f.id === fileToProcess.id 
                ? { ...f, status: 'completed', progress: 100, transcriptId: result.transcript_id }
                : f
            ));
            completed++;
            toast.success(`Completed: ${fileToProcess.name}`);
          } else {
            throw new Error(result.error || 'Processing failed');
          }
        } else {
          throw new Error('Invalid API response');
        }
      } catch (error) {
        failed++;
        setFiles(prev => prev.map(f => 
          f.id === fileToProcess.id 
            ? { ...f, status: 'error', error: error.message }
            : f
        ));
        toast.error(`Failed: ${fileToProcess.name}`);
      } finally {
        activeProcessing--;
        
        // Process next file
        if (processingQueue.length > 0) {
          processNextFile();
        } else if (activeProcessing === 0) {
          // All files processed
          setProcessing(false);
          analytics.trackFeatureUsage('batch-upload', 'processing-completed', { 
            completed,
            failed,
            total: files.length 
          });
          
          toast.success(`Batch processing completed: ${completed} succeeded, ${failed} failed`);
          
          if (onBatchStart) {
            onBatchStart(batchId, files);
          }
        }
      }
    };

    // Start processing up to maxConcurrent files
    for (let i = 0; i < Math.min(settings.maxConcurrent, processingQueue.length); i++) {
      processNextFile();
    }
  };

  const totalSize = files.reduce((sum, file) => sum + file.size, 0);
  const completedCount = files.filter(f => f.status === 'completed').length;
  const errorCount = files.filter(f => f.status === 'error').length;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Batch File Processing
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Drop Zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center hover:border-primary-500 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Drop files here or click to browse
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Supports audio (MP3, WAV, M4A) and video (MP4, MOV, AVI) files
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="audio/*,video/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* Settings */}
          <div className="mt-6 grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Language
              </label>
              <select
                value={settings.language}
                onChange={(e) => setSettings({ ...settings, language: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="auto">Auto-detect</option>
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="zh">Chinese</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Model
              </label>
              <select
                value={settings.model}
                onChange={(e) => setSettings({ ...settings, model: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="tiny">Tiny (Fast)</option>
                <option value="base">Base (Balanced)</option>
                <option value="small">Small (Accurate)</option>
                <option value="medium">Medium (High Quality)</option>
                <option value="large">Large (Best Quality)</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="diarization"
                checked={settings.enableDiarization}
                onChange={(e) => setSettings({ ...settings, enableDiarization: e.target.checked })}
                className="mr-2"
              />
              <label htmlFor="diarization" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Enable Speaker Diarization
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="entities"
                checked={settings.extractEntities}
                onChange={(e) => setSettings({ ...settings, extractEntities: e.target.checked })}
                className="mr-2"
              />
              <label htmlFor="entities" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Extract Named Entities
              </label>
            </div>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Files ({files.length})
                </h3>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Total size: {formatFileSize(totalSize)}
                </div>
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
                  >
                    <div className="flex items-center space-x-3 flex-1">
                      {getStatusIcon(file.status)}
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>

                    {file.status === 'processing' && (
                      <div className="w-32">
                        <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full transition-all"
                            style={{ width: `${file.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {file.status === 'error' && (
                      <p className="text-xs text-red-600 dark:text-red-400 ml-2">
                        {file.error || 'Processing failed'}
                      </p>
                    )}

                    {!processing && file.status === 'pending' && (
                      <button
                        onClick={() => removeFile(file.id)}
                        className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Progress Summary */}
          {processing && (
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-blue-900 dark:text-blue-200">
                  Processing Files
                </p>
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  {completedCount} / {files.length} completed
                </p>
              </div>
              <div className="bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${(completedCount / files.length) * 100}%` }}
                />
              </div>
              {errorCount > 0 && (
                <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                  {errorCount} files failed to process
                </p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {settings.parallelProcessing 
                ? `Processing up to ${settings.maxConcurrent} files simultaneously`
                : 'Processing files sequentially'}
            </p>
            <div className="flex items-center space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={processFiles}
                disabled={files.length === 0 || processing}
                className={`px-4 py-2 rounded-lg font-medium ${
                  files.length === 0 || processing
                    ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                    : 'bg-primary-600 hover:bg-primary-700 text-white'
                }`}
              >
                {processing ? 'Processing...' : `Process ${files.length} Files`}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BatchUpload;