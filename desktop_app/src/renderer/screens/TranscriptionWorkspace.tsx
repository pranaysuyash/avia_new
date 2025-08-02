import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import {
  CloudArrowUpIcon,
  MicrophoneIcon,
  DocumentTextIcon,
  PlayIcon,
  PauseIcon,
  ArrowDownTrayIcon,
  UserGroupIcon,
  TagIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import WaveformPlayer from '../components/workspace/WaveformPlayer';
import TranscriptEditor from '../components/workspace/TranscriptEditor';
import EntityPanel from '../components/workspace/EntityPanel';
import ProcessingModal from '../components/workspace/ProcessingModal';

const TranscriptionWorkspace: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<'transcript' | 'entities' | 'insights'>('transcript');
  const [isPlaying, setIsPlaying] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      // Start processing
      setIsProcessing(true);
      // Simulate processing
      setTimeout(() => setIsProcessing(false), 3000);
    }
  }, []);

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
    { id: 'insights', label: 'Insights', icon: ChartBarIcon }
  ];

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Transcription Workspace
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {file ? file.name : 'Upload or record audio to begin'}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="btn-secondary">
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
            </motion.div>
          </div>
        ) : (
          /* Processing View */
          <>
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
              <div className="flex-1 overflow-hidden">
                {activeTab === 'transcript' && <TranscriptEditor />}
                {activeTab === 'entities' && <EntityPanel />}
                {activeTab === 'insights' && (
                  <div className="p-6">
                    <p className="text-gray-500">Insights panel coming soon...</p>
                  </div>
                )}
              </div>
            </div>

            {/* Right Sidebar - Quick Actions */}
            <div className="w-80 bg-gray-50 dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 p-6">
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

              <div className="mt-8">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
                  Processing Info
                </h3>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-xs text-gray-500 dark:text-gray-400">Duration</dt>
                    <dd className="text-sm font-medium text-gray-900 dark:text-white">23:45</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500 dark:text-gray-400">Confidence</dt>
                    <dd className="text-sm font-medium text-gray-900 dark:text-white">96.8%</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500 dark:text-gray-400">Language</dt>
                    <dd className="text-sm font-medium text-gray-900 dark:text-white">English</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500 dark:text-gray-400">Speakers</dt>
                    <dd className="text-sm font-medium text-gray-900 dark:text-white">3</dd>
                  </div>
                </dl>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Processing Modal */}
      {isProcessing && <ProcessingModal />}
    </div>
  );
};

export default TranscriptionWorkspace;