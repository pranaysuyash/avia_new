import React, { useState, useEffect } from 'react';
import useWebSocket from '../hooks/useWebSocket';

const TranscriptionStatus = ({ transcriptionId, onComplete, toast }) => {
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [error, setError] = useState(null);
  
  const wsUrl = localStorage.getItem('apiEndpoint')?.replace('http', 'ws') || 'ws://localhost:8000';
  
  const { isConnected, sendMessage, subscribe } = useWebSocket(`${wsUrl}/ws`, {
    autoConnect: true,
    onConnect: () => {
      // Subscribe to this transcription's updates
      sendMessage('subscribe', { transcription_id: transcriptionId });
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      toast.error('Connection error: Unable to get real-time updates');
    }
  });

  useEffect(() => {
    // Subscribe to transcription status updates
    const unsubscribeStatus = subscribe('transcription:status', (data) => {
      if (data.transcription_id === transcriptionId) {
        setStatus(data.status);
        setCurrentStep(data.step || '');
        
        if (data.status === 'completed') {
          setProgress(100);
          toast.success('Transcription completed!');
          if (onComplete) onComplete(data);
        } else if (data.status === 'failed') {
          setError(data.error || 'Transcription failed');
          toast.error('Transcription failed: ' + (data.error || 'Unknown error'));
        }
      }
    });

    // Subscribe to progress updates
    const unsubscribeProgress = subscribe('transcription:progress', (data) => {
      if (data.transcription_id === transcriptionId) {
        setProgress(data.progress);
      }
    });

    // Subscribe to step updates
    const unsubscribeStep = subscribe('transcription:step', (data) => {
      if (data.transcription_id === transcriptionId) {
        setCurrentStep(data.step);
      }
    });

    return () => {
      unsubscribeStatus();
      unsubscribeProgress();
      unsubscribeStep();
    };
  }, [transcriptionId, subscribe, toast, onComplete]);

  const getStatusColor = () => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-400';
      case 'processing': return 'text-blue-600 bg-blue-100 dark:bg-blue-900 dark:text-blue-400';
      case 'completed': return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-400';
      case 'failed': return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-400';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-400';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'pending':
        return (
          <svg className="w-5 h-5 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'processing':
        return (
          <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case 'completed':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${getStatusColor()}`}>
            {getStatusIcon()}
          </div>
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white">
              Transcription Status
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {currentStep || 'Waiting to start...'}
            </p>
          </div>
        </div>
        
        {!isConnected && (
          <div className="flex items-center text-sm text-yellow-600 dark:text-yellow-400">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Not connected
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {status === 'processing' && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Processing Steps */}
      {status === 'processing' && (
        <div className="mt-4 space-y-2">
          <ProcessingStep 
            name="Audio Processing" 
            status={progress >= 25 ? 'completed' : progress > 0 ? 'active' : 'pending'} 
          />
          <ProcessingStep 
            name="Speech Recognition" 
            status={progress >= 50 ? 'completed' : progress > 25 ? 'active' : 'pending'} 
          />
          <ProcessingStep 
            name="Speaker Diarization" 
            status={progress >= 75 ? 'completed' : progress > 50 ? 'active' : 'pending'} 
          />
          <ProcessingStep 
            name="Entity Extraction" 
            status={progress >= 100 ? 'completed' : progress > 75 ? 'active' : 'pending'} 
          />
        </div>
      )}
    </div>
  );
};

const ProcessingStep = ({ name, status }) => {
  const getStepStyle = () => {
    switch (status) {
      case 'completed':
        return 'text-green-600 dark:text-green-400';
      case 'active':
        return 'text-blue-600 dark:text-blue-400';
      default:
        return 'text-gray-400 dark:text-gray-600';
    }
  };

  const getStepIcon = () => {
    switch (status) {
      case 'completed':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'active':
        return <div className="w-4 h-4 border-2 border-current rounded-full border-t-transparent animate-spin" />;
      default:
        return <div className="w-4 h-4 border-2 border-current rounded-full" />;
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${getStepStyle()}`}>
      {getStepIcon()}
      <span className="text-sm">{name}</span>
    </div>
  );
};

export default TranscriptionStatus;