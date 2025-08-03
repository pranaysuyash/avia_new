import React from 'react';
import { motion } from 'framer-motion';
import { TranscriptionResult } from '../../services/transcriptionApi';

interface TranscriptEditorProps {
  transcriptionResult: TranscriptionResult | null;
  isProcessing: boolean;
}

const TranscriptEditor: React.FC<TranscriptEditorProps> = ({ 
  transcriptionResult, 
  isProcessing 
}) => {
  if (isProcessing) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-500 dark:text-gray-400">Processing your audio file...</p>
          <p className="text-sm text-gray-400 mt-2">This may take a few moments</p>
        </div>
      </div>
    );
  }

  if (!transcriptionResult) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-gray-500 dark:text-gray-400">Upload an audio file to see the transcript</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="h-full flex flex-col"
    >
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Transcript
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Confidence: {(transcriptionResult.confidence * 100).toFixed(1)}% • 
          Language: {transcriptionResult.language} • 
          Duration: {Math.floor(transcriptionResult.duration / 60)}:{(transcriptionResult.duration % 60).toFixed(0).padStart(2, '0')}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {transcriptionResult.segments ? (
          // Show segmented transcript with timestamps
          <div className="space-y-4">
            {transcriptionResult.segments.map((segment, index) => (
              <div key={index} className="flex space-x-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-sm text-gray-500 dark:text-gray-400 font-mono min-w-[80px]">
                  {Math.floor(segment.start / 60)}:{(segment.start % 60).toFixed(1).padStart(4, '0')}
                </div>
                <div className="flex-1">
                  <p className="text-gray-900 dark:text-white">{segment.text}</p>
                  <div className="mt-1 text-xs text-gray-500">
                    Confidence: {(segment.confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          // Show full transcript
          <div className="prose prose-gray dark:prose-invert max-w-none">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
              <p className="text-gray-900 dark:text-white leading-relaxed whitespace-pre-wrap">
                {transcriptionResult.text}
              </p>
            </div>
          </div>
        )}

        {/* Export Options */}
        <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
            Export Options
          </h4>
          <div className="flex space-x-3">
            <button className="btn-secondary text-sm">
              Download TXT
            </button>
            <button className="btn-secondary text-sm">
              Download SRT
            </button>
            <button className="btn-secondary text-sm">
              Copy to Clipboard
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default TranscriptEditor;