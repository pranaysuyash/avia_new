import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import {
  CloudArrowUpIcon,
  MicrophoneIcon,
  DocumentTextIcon,
  PlayIcon,
  ArrowDownTrayIcon,
  UserGroupIcon,
  TagIcon,
  ChartBarIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import WaveformPlayer from '../components/transcription/WaveformPlayer';
import TranscriptEditor from '../components/workspace/TranscriptEditor';
import { logUxEvent } from '../services/uxTelemetry';
import EntityPanel from '../components/workspace/EntityPanel';
import ProcessingModal from '../components/workspace/ProcessingModal';
import { StructuredAnalysis, ContentInsights } from '../components/analysis';
import { transcriptionAPI, TranscriptionResult } from '../services/transcriptionApi';

const TranscriptionWorkspace: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<'transcript' | 'entities' | 'insights' | 'analysis'>(() => {
    try { const url = new URL(window.location.href); const t = url.searchParams.get('tw_tab'); if (t && ['transcript','entities','insights','analysis'].includes(t)) return t as any; } catch {}
    return 'transcript';
  });
  const [isPlaying, setIsPlaying] = useState(false);
  const [transcriptionResult, setTranscriptionResult] = useState<TranscriptionResult | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('auto');
  const [detectCodeSwitching, setDetectCodeSwitching] = useState(false);
  const [processingError, setProcessingError] = useState<string | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<'basic' | 'advanced' | 'multilingual' | 'whisperx'>('basic');

  const methodInfo = {
    basic: {
      name: 'Basic NER',
      subtitle: 'Fast processing',
      description: 'Uses spaCy for quick entity recognition. Best for English content with standard entities (names, organizations, locations). Processes in real-time.',
      features: ['Fast processing (< 1 sec)', 'Standard entities', 'English optimized', 'Low resource usage'],
      bestFor: 'Quick transcriptions, live meetings, standard business content'
    },
    advanced: {
      name: 'Advanced NER',
      subtitle: 'High accuracy',
      description: 'Uses transformer models (BERT/RoBERTa) for superior accuracy. Detects complex entities and relationships. Slower but more accurate.',
      features: ['High accuracy (95%+)', 'Complex entity detection', 'Context understanding', 'Custom entity types'],
      bestFor: 'Legal documents, medical records, technical content, research'
    },
    multilingual: {
      name: 'Multilingual',
      subtitle: 'Multi-language support',
      description: 'Supports 100+ languages with automatic language detection. Uses multilingual models for consistent entity recognition across languages.',
      features: ['100+ languages', 'Auto language detection', 'Cross-lingual entities', 'Unicode support'],
      bestFor: 'International content, mixed-language documents, global teams'
    },
    whisperx: {
      name: 'WhisperX',
      subtitle: 'With diarization',
      description: 'OpenAI Whisper with speaker diarization. Identifies who said what. Best for meetings, interviews, and multi-speaker content.',
      features: ['Speaker identification', 'Timestamp alignment', 'High quality transcription', 'Speaker analytics'],
      bestFor: 'Meetings, interviews, podcasts, panel discussions'
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const uploadedFile = acceptedFiles[0];
      setFile(uploadedFile);
      setIsProcessing(true);
      setProcessingError(null);
      setTranscriptionResult(null);

      try {
        // Call real transcription API
        const result = await transcriptionAPI.transcribeFile({
          file: uploadedFile,
          language: selectedLanguage === 'auto' ? undefined : selectedLanguage,
          detectCodeSwitching,
          method: selectedMethod
        });

        setTranscriptionResult(result);
        setIsProcessing(false);
      } catch (error) {
        console.error('Transcription failed:', error);
        setProcessingError(error instanceof Error ? error.message : 'Transcription failed');
        setIsProcessing(false);
      }
    }
  }, [selectedLanguage, detectCodeSwitching, selectedMethod]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a'],
      'video/*': ['.mp4', '.mov', '.avi']
    },
    maxFiles: 1
  });

  const tabs = [
    { id: 'transcript', label: 'Transcript', icon: DocumentTextIcon },
    { id: 'entities', label: 'Entities', icon: TagIcon },
    { id: 'insights', label: 'Insights', icon: ChartBarIcon },
    { id: 'analysis', label: 'Analysis', icon: DocumentTextIcon }
  ];

  // Sync active tab to query param
  React.useEffect(() => {
    try { const url = new URL(window.location.href); url.searchParams.set('tw_tab', activeTab); window.history.replaceState({}, '', url.toString()); } catch {}
  }, [activeTab]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {file && (
              <button 
                onClick={() => {
                  setFile(null);
                  setTranscriptionResult(null);
                  setIsProcessing(false);
                  setProcessingError(null);
                }}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="Back to transcriptions"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            <div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Transcription Workspace
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {file ? file.name : 'Upload or record audio to begin'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button className="btn-secondary" onClick={async () => { try { const href = window.location.href; await navigator.clipboard.writeText(href); logUxEvent('share_workspace_view', { href }); } catch {} }}>
              <UserGroupIcon className="h-5 w-5 mr-2" />
              Share
            </button>
            <button className="btn-primary">
              <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {!file ? (
          /* Upload Area */
          <div className="flex-1 flex items-center justify-center p-6">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-full max-w-2xl"
            >
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
                  isDragActive
                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} />
                <CloudArrowUpIcon className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Drop your file here, or click to browse
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Support for MP3, WAV, M4A, MP4, MOV, AVI
                </p>
              </div>

              <div className="mt-6 flex items-center">
                <div className="flex-1 border-t border-gray-300 dark:border-gray-600"></div>
                <span className="px-4 text-sm text-gray-500 dark:text-gray-400">or</span>
                <div className="flex-1 border-t border-gray-300 dark:border-gray-600"></div>
              </div>

              <button className="mt-6 w-full btn-primary py-4">
                <MicrophoneIcon className="h-6 w-6 mr-3" />
                Start Recording
              </button>

              {/* Transcription Options */}
              <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
                  Transcription Settings
                </h3>
                
                <div className="space-y-4">
                  {/* Language Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Language
                    </label>
                    <select
                      value={selectedLanguage}
                      onChange={(e) => setSelectedLanguage(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    >
                      <option value="auto">Auto-detect</option>
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                      <option value="it">Italian</option>
                      <option value="pt">Portuguese</option>
                      <option value="nl">Dutch</option>
                      <option value="ja">Japanese</option>
                      <option value="ko">Korean</option>
                      <option value="zh">Chinese</option>
                    </select>
                  </div>

                  {/* Code Switching Option */}
                  <div className="flex items-center">
                    <input
                      id="code-switching"
                      type="checkbox"
                      checked={detectCodeSwitching}
                      onChange={(e) => setDetectCodeSwitching(e.target.checked)}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <label htmlFor="code-switching" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                      Detect code-switching (multiple languages in same audio)
                    </label>
                  </div>

                  {/* Transcription Method */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Transcription Method
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="relative group">
                        <button 
                          onClick={() => setSelectedMethod('basic')}
                          className={`w-full p-3 border rounded-lg text-center hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                            selectedMethod === 'basic' 
                              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' 
                              : 'border-gray-300 dark:border-gray-600'
                          }`}
                        >
                          <div className="text-sm font-medium text-gray-900 dark:text-white">Basic NER</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Fast processing</div>
                        </button>
                        {/* Hover tooltip */}
                        <div className="absolute z-10 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
                          <div className="font-medium mb-1">{methodInfo.basic.name}</div>
                          <div className="text-gray-300 mb-2">{methodInfo.basic.description}</div>
                          <div className="text-gray-400">Best for: {methodInfo.basic.bestFor}</div>
                          <div className="absolute bottom-0 left-8 transform translate-y-full w-0 h-0 border-l-8 border-l-transparent border-r-8 border-r-transparent border-t-8 border-t-gray-900"></div>
                        </div>
                      </div>
                      
                      <div className="relative group">
                        <button 
                          onClick={() => setSelectedMethod('advanced')}
                          className={`w-full p-3 border rounded-lg text-center hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                            selectedMethod === 'advanced' 
                              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' 
                              : 'border-gray-300 dark:border-gray-600'
                          }`}
                        >
                          <div className="text-sm font-medium text-gray-900 dark:text-white">Advanced NER</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">High accuracy</div>
                        </button>
                        {/* Hover tooltip */}
                        <div className="absolute z-10 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 bottom-full right-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
                          <div className="font-medium mb-1">{methodInfo.advanced.name}</div>
                          <div className="text-gray-300 mb-2">{methodInfo.advanced.description}</div>
                          <div className="text-gray-400">Best for: {methodInfo.advanced.bestFor}</div>
                          <div className="absolute bottom-0 right-8 transform translate-y-full w-0 h-0 border-l-8 border-l-transparent border-r-8 border-r-transparent border-t-8 border-t-gray-900"></div>
                        </div>
                      </div>
                      
                      <div className="relative group">
                        <button 
                          onClick={() => setSelectedMethod('multilingual')}
                          className={`w-full p-3 border rounded-lg text-center hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                            selectedMethod === 'multilingual' 
                              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' 
                              : 'border-gray-300 dark:border-gray-600'
                          }`}
                        >
                          <div className="text-sm font-medium text-gray-900 dark:text-white">Multilingual</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Multi-language support</div>
                        </button>
                        {/* Hover tooltip */}
                        <div className="absolute z-10 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
                          <div className="font-medium mb-1">{methodInfo.multilingual.name}</div>
                          <div className="text-gray-300 mb-2">{methodInfo.multilingual.description}</div>
                          <div className="text-gray-400">Best for: {methodInfo.multilingual.bestFor}</div>
                          <div className="absolute bottom-0 left-8 transform translate-y-full w-0 h-0 border-l-8 border-l-transparent border-r-8 border-r-transparent border-t-8 border-t-gray-900"></div>
                        </div>
                      </div>
                      
                      <div className="relative group">
                        <button 
                          onClick={() => setSelectedMethod('whisperx')}
                          className={`w-full p-3 border rounded-lg text-center hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                            selectedMethod === 'whisperx' 
                              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' 
                              : 'border-gray-300 dark:border-gray-600'
                          }`}
                        >
                          <div className="text-sm font-medium text-gray-900 dark:text-white">WhisperX</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">With diarization</div>
                        </button>
                        {/* Hover tooltip */}
                        <div className="absolute z-10 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 bottom-full right-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
                          <div className="font-medium mb-1">{methodInfo.whisperx.name}</div>
                          <div className="text-gray-300 mb-2">{methodInfo.whisperx.description}</div>
                          <div className="text-gray-400">Best for: {methodInfo.whisperx.bestFor}</div>
                          <div className="absolute bottom-0 right-8 transform translate-y-full w-0 h-0 border-l-8 border-l-transparent border-r-8 border-r-transparent border-t-8 border-t-gray-900"></div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Small info text below */}
                    <div className="mt-3 flex items-center text-xs text-gray-500 dark:text-gray-400">
                      <InformationCircleIcon className="h-4 w-4 mr-1" />
                      <span>Hover over options to see detailed information</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        ) : (
          /* Processing View */
          <div className="flex-1 flex">
            <div className="flex-1 flex flex-col">
              {/* Waveform */}
              <div className="h-48 bg-gray-900 p-4">
                <WaveformPlayer
                  audioUrl={URL.createObjectURL(file)}
                  isPlaying={isPlaying}
                  onPlayPause={() => setIsPlaying(!isPlaying)}
                />
              </div>

              {/* Tabs */}
              <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <div className="flex space-x-8 px-6">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`flex items-center py-4 px-1 border-b-2 text-sm font-medium transition-colors ${
                        activeTab === tab.id
                          ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                          : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
                      }`}
                    >
                      <tab.icon className="h-5 w-5 mr-2" />
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-auto">
                {activeTab === 'transcript' && (
                  <TranscriptEditor 
                    transcriptionResult={transcriptionResult}
                    isProcessing={isProcessing}
                  />
                )}
                {activeTab === 'entities' && (
                  <EntityPanel 
                    entities={transcriptionResult?.entities || {}}
                    isProcessing={isProcessing}
                  />
                )}
                {activeTab === 'insights' && (
                  <div className="p-6">
                    <ContentInsights 
                      text={transcriptionResult?.text || ''}
                      transcriptionId={transcriptionResult?.id}
                    />
                  </div>
                )}
                {activeTab === 'analysis' && (
                  <div className="p-6">
                    <StructuredAnalysis 
                      text={transcriptionResult?.text || ''}
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Right Sidebar - Quick Actions */}
            <div className="w-80 bg-gray-50 dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 p-6 overflow-auto">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
                Quick Actions
              </h3>
              <div className="space-y-3">
                <button className="w-full btn-secondary justify-center">
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Play from Start
                </button>
                <button className="w-full btn-secondary justify-center">
                  <TagIcon className="h-4 w-4 mr-2" />
                  Add Tags
                </button>
                <button className="w-full btn-secondary justify-center">
                  <UserGroupIcon className="h-4 w-4 mr-2" />
                  Assign Speaker
                </button>
              </div>

              {/* Language Selection */}
              <div className="mt-8">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
                  Settings
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Language</label>
                    <select 
                      value={selectedLanguage}
                      onChange={(e) => setSelectedLanguage(e.target.value)}
                      className="mt-1 block w-full text-sm border border-gray-300 rounded-md px-3 py-2"
                    >
                      <option value="auto">Auto-detect</option>
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                      <option value="it">Italian</option>
                      <option value="pt">Portuguese</option>
                      <option value="ja">Japanese</option>
                      <option value="ko">Korean</option>
                      <option value="zh">Chinese</option>
                    </select>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={detectCodeSwitching}
                      onChange={(e) => setDetectCodeSwitching(e.target.checked)}
                      className="mr-2"
                    />
                    <label className="text-xs text-gray-500 dark:text-gray-400">
                      Detect Code-Switching
                    </label>
                  </div>
                </div>
              </div>

              {/* Processing Info - Show real data */}
              {transcriptionResult && (
                <div className="mt-8">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
                    Processing Info
                  </h3>
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-xs text-gray-500 dark:text-gray-400">Duration</dt>
                      <dd className="text-sm font-medium text-gray-900 dark:text-white">
                        {Math.floor(transcriptionResult.duration / 60)}:{(transcriptionResult.duration % 60).toFixed(0).padStart(2, '0')}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-gray-500 dark:text-gray-400">Confidence</dt>
                      <dd className="text-sm font-medium text-gray-900 dark:text-white">
                        {(transcriptionResult.confidence * 100).toFixed(1)}%
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-gray-500 dark:text-gray-400">Language</dt>
                      <dd className="text-sm font-medium text-gray-900 dark:text-white">
                        {transcriptionResult.language}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-gray-500 dark:text-gray-400">Entities Found</dt>
                      <dd className="text-sm font-medium text-gray-900 dark:text-white">
                        {Object.values(transcriptionResult.entities).flat().length}
                      </dd>
                    </div>
                  </dl>
                </div>
              )}

              {/* Error Display */}
              {processingError && (
                <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <h3 className="text-sm font-medium text-red-800 mb-2">Processing Error</h3>
                  <p className="text-sm text-red-600">{processingError}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Processing Modal */}
      {isProcessing && <ProcessingModal />}
    </div>
  );
};

export default TranscriptionWorkspace;
