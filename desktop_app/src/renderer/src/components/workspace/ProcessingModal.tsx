import React from 'react';
import { motion } from 'framer-motion';

const ProcessingModal: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-8 max-w-md w-full mx-4"
      >
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-indigo-500 border-t-transparent rounded-full mx-auto mb-6"></div>
          
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Processing Your Audio
          </h3>
          
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            Please wait while we transcribe your audio file and extract entities. This may take a few moments.
          </p>
          
          <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-4">
            <motion.div
              className="bg-indigo-600 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: '100%' }}
              transition={{ duration: 3, ease: 'easeInOut' }}
            />
          </div>
          
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <div className="space-y-1">
              <div>✓ Audio file uploaded</div>
              <div>⏳ Transcribing speech...</div>
              <div>⏳ Extracting entities...</div>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default ProcessingModal;