/**
 * Interactive Learning Interface
 * UI for the sophisticated transcription correction and learning system
 * Connects to the advanced correction engine backend
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiPlay,
  FiPause,
  FiSkipBack,
  FiSkipForward,
  FiVolume2,
  FiEdit3,
  FiCheck,
  FiX,
  FiTrendingUp,
  FiTarget,
  FiAward,
  FiBrain,
  FiEye,
  FiRefreshCw,
  FiBookOpen,
  FiZap,
  FiUsers,
  FiClock,
  FiBarChart3
} from 'react-icons/fi';
import { useAccessibility } from '../../../accessibility';

// Interfaces
interface CorrectionSuggestion {
  id: string;
  type: 'spelling' | 'grammar' | 'punctuation' | 'capitalization' | 'word_boundary';
  original: string;
  suggested: string;
  confidence: number;
  position: {
    start: number;
    end: number;
  };
  context: string;
  explanation: string;
  learningPoints: string[];
}

interface LearningSession {
  id: string;
  userId: string;
  transcriptId: string;
  startTime: Date;
  endTime?: Date;
  corrections: CorrectionSuggestion[];
  accuracy: number;
  improvementAreas: string[];
  achievements: string[];
}

interface UserProgress {
  totalSessions: number;
  accuracyTrend: number[];
  strongAreas: string[];
  improvementAreas: string[];
  achievements: string[];
  streakDays: number;
  totalCorrections: number;
}

interface InteractiveLearningProps {
  transcriptId: string;
  initialTranscript: string;
  audioUrl?: string;
  onCorrectionApplied: (correction: CorrectionSuggestion) => void;
  onSessionComplete: (session: LearningSession) => void;
  className?: string;
}

export const InteractiveLearningInterface: React.FC<InteractiveLearningProps> = ({
  transcriptId,
  initialTranscript,
  audioUrl,
  onCorrectionApplied,
  onSessionComplete,
  className = ''
}) => {
  // State
  const [transcript, setTranscript] = useState(initialTranscript);
  const [suggestions, setSuggestions] = useState<CorrectionSuggestion[]>([]);
  const [currentSuggestion, setCurrentSuggestion] = useState<CorrectionSuggestion | null>(null);
  const [userProgress, setUserProgress] = useState<UserProgress | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [sessionStats, setSessionStats] = useState({
    correctionsApplied: 0,
    correctionsSkipped: 0,
    accuracy: 0,
    timeSpent: 0
  });
  const [learningMode, setLearningMode] = useState<'guided' | 'challenge' | 'review'>('guided');
  const [showExplanations, setShowExplanations] = useState(true);

  // Refs
  const audioRef = useRef<HTMLAudioElement>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const sessionStartTime = useRef(Date.now());

  // Accessibility
  const { announceToScreenReader } = useAccessibility();

  // Load suggestions from correction engine
  useEffect(() => {
    loadCorrectionSuggestions();
    loadUserProgress();
  }, [transcriptId]);

  const loadCorrectionSuggestions = async () => {
    setIsAnalyzing(true);
    try {
      const response = await fetch('/api/corrections/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          transcript: transcript,
          transcriptId,
          mode: learningMode 
        })
      });
      
      const data = await response.json();
      setSuggestions(data.suggestions || []);
      if (data.suggestions?.length > 0) {
        setCurrentSuggestion(data.suggestions[0]);
        announceToScreenReader(`Found ${data.suggestions.length} correction suggestions`);
      }
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const loadUserProgress = async () => {
    try {
      const response = await fetch('/api/learning/progress');
      const data = await response.json();
      setUserProgress(data);
    } catch (error) {
      console.error('Failed to load progress:', error);
    }
  };

  // Handle correction application
  const applySuggestion = useCallback(async (suggestion: CorrectionSuggestion, accepted: boolean) => {
    if (accepted) {
      // Apply the correction to transcript
      const newTranscript = transcript.slice(0, suggestion.position.start) +
                          suggestion.suggested +
                          transcript.slice(suggestion.position.end);
      
      setTranscript(newTranscript);
      onCorrectionApplied(suggestion);
      
      setSessionStats(prev => ({
        ...prev,
        correctionsApplied: prev.correctionsApplied + 1,
        accuracy: (prev.correctionsApplied + 1) / (prev.correctionsApplied + prev.correctionsSkipped + 1)
      }));
    } else {
      setSessionStats(prev => ({
        ...prev,
        correctionsSkipped: prev.correctionsSkipped + 1,
        accuracy: prev.correctionsApplied / (prev.correctionsApplied + prev.correctionsSkipped + 1)
      }));
    }

    // Record the learning interaction
    await recordLearningInteraction(suggestion, accepted);
    
    // Move to next suggestion
    const currentIndex = suggestions.indexOf(suggestion);
    if (currentIndex < suggestions.length - 1) {
      setCurrentSuggestion(suggestions[currentIndex + 1]);
      announceToScreenReader(`Moving to correction ${currentIndex + 2} of ${suggestions.length}`);
    } else {
      // Session complete
      completeSession();
    }
  }, [transcript, suggestions, onCorrectionApplied]);

  const recordLearningInteraction = async (suggestion: CorrectionSuggestion, accepted: boolean) => {
    try {
      await fetch('/api/learning/interaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcriptId,
          suggestion,
          accepted,
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      console.error('Failed to record interaction:', error);
    }
  };

  const completeSession = useCallback(() => {
    const endTime = Date.now();
    const session: LearningSession = {
      id: `session_${Date.now()}`,
      userId: 'current_user', // Would come from auth context
      transcriptId,
      startTime: new Date(sessionStartTime.current),
      endTime: new Date(endTime),
      corrections: suggestions,
      accuracy: sessionStats.accuracy,
      improvementAreas: ['spelling', 'grammar'], // Would be calculated
      achievements: sessionStats.accuracy > 0.8 ? ['high_accuracy'] : []
    };

    onSessionComplete(session);
    announceToScreenReader(`Session completed with ${Math.round(sessionStats.accuracy * 100)}% accuracy`);
  }, [transcriptId, suggestions, sessionStats, onSessionComplete]);

  // Audio control
  const togglePlayback = useCallback(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  }, [isPlaying]);

  const seekToSuggestion = useCallback((suggestion: CorrectionSuggestion) => {
    // Estimate time based on character position (rough approximation)
    const estimatedTime = (suggestion.position.start / transcript.length) * (audioRef.current?.duration || 0);
    if (audioRef.current && !isNaN(estimatedTime)) {
      audioRef.current.currentTime = estimatedTime;
      setCurrentTime(estimatedTime);
    }
    setCurrentSuggestion(suggestion);
  }, [transcript.length]);

  // Render suggestion highlight
  const renderHighlightedTranscript = () => {
    if (!currentSuggestion) return transcript;

    const { start, end } = currentSuggestion.position;
    return (
      <div className="whitespace-pre-wrap leading-relaxed">
        {transcript.slice(0, start)}
        <span className="bg-yellow-200 border-l-4 border-yellow-500 px-1 py-0.5 rounded">
          {transcript.slice(start, end)}
        </span>
        {transcript.slice(end)}
      </div>
    );
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCorrectionIcon = (type: string) => {
    switch (type) {
      case 'spelling': return '📝';
      case 'grammar': return '📚';
      case 'punctuation': return '🎯';
      case 'capitalization': return '🔤';
      default: return '✏️';
    }
  };

  return (
    <div className={`interactive-learning bg-background-primary rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-border-DEFAULT bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-full">
              <FiBrain className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-text-primary">Interactive Learning</h2>
              <p className="text-sm text-text-secondary">Improve your transcription accuracy</p>
            </div>
          </div>
          
          {/* Learning Mode Selector */}
          <div className="flex items-center space-x-2">
            <select
              value={learningMode}
              onChange={(e) => setLearningMode(e.target.value as any)}
              className="px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
            >
              <option value="guided">Guided Learning</option>
              <option value="challenge">Challenge Mode</option>
              <option value="review">Review Mode</option>
            </select>
          </div>
        </div>

        {/* Progress Stats */}
        {userProgress && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="text-center p-3 bg-white rounded-lg shadow-sm">
              <FiTrendingUp className="h-5 w-5 text-green-500 mx-auto mb-1" />
              <div className="text-lg font-semibold text-text-primary">{userProgress.streakDays}</div>
              <div className="text-xs text-text-secondary">Day Streak</div>
            </div>
            
            <div className="text-center p-3 bg-white rounded-lg shadow-sm">
              <FiTarget className="h-5 w-5 text-blue-500 mx-auto mb-1" />
              <div className="text-lg font-semibold text-text-primary">
                {Math.round((sessionStats.accuracy || 0) * 100)}%
              </div>
              <div className="text-xs text-text-secondary">Accuracy</div>
            </div>
            
            <div className="text-center p-3 bg-white rounded-lg shadow-sm">
              <FiAward className="h-5 w-5 text-yellow-500 mx-auto mb-1" />
              <div className="text-lg font-semibold text-text-primary">{userProgress.achievements.length}</div>
              <div className="text-xs text-text-secondary">Achievements</div>
            </div>
            
            <div className="text-center p-3 bg-white rounded-lg shadow-sm">
              <FiClock className="h-5 w-5 text-purple-500 mx-auto mb-1" />
              <div className="text-lg font-semibold text-text-primary">
                {Math.round(sessionStats.timeSpent / 60)}m
              </div>
              <div className="text-xs text-text-secondary">Session Time</div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
        {/* Transcript Panel */}
        <div className="lg:col-span-2">
          <div className="bg-background-secondary rounded-lg p-6 mb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Transcript</h3>
              
              {/* Audio Controls */}
              {audioUrl && (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setCurrentTime(Math.max(0, currentTime - 10))}
                    className="p-2 text-text-secondary hover:text-primary-DEFAULT focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded"
                    aria-label="Skip back 10 seconds"
                  >
                    <FiSkipBack className="h-4 w-4" />
                  </button>
                  
                  <button
                    onClick={togglePlayback}
                    className="p-3 bg-primary-DEFAULT text-primary-contrast rounded-full hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2"
                    aria-label={isPlaying ? 'Pause' : 'Play'}
                  >
                    {isPlaying ? <FiPause className="h-4 w-4" /> : <FiPlay className="h-4 w-4" />}
                  </button>
                  
                  <button
                    onClick={() => setCurrentTime(currentTime + 10)}
                    className="p-2 text-text-secondary hover:text-primary-DEFAULT focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded"
                    aria-label="Skip forward 10 seconds"
                  >
                    <FiSkipForward className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Transcript Content */}
            <div
              ref={transcriptRef}
              className="bg-white p-4 rounded border border-border-DEFAULT min-h-[300px] font-mono text-sm"
              tabIndex={0}
              role="textbox"
              aria-label="Transcript content"
            >
              {isAnalyzing ? (
                <div className="flex items-center justify-center py-12">
                  <FiRefreshCw className="h-6 w-6 animate-spin text-primary-DEFAULT mr-3" />
                  <span className="text-text-secondary">Analyzing transcript...</span>
                </div>
              ) : (
                renderHighlightedTranscript()
              )}
            </div>

            {/* Hidden audio element */}
            {audioUrl && (
              <audio
                ref={audioRef}
                src={audioUrl}
                onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                onEnded={() => setIsPlaying(false)}
                className="hidden"
              />
            )}
          </div>
        </div>

        {/* Learning Panel */}
        <div className="space-y-6">
          {/* Current Suggestion */}
          {currentSuggestion && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{getCorrectionIcon(currentSuggestion.type)}</span>
                  <div>
                    <h4 className="font-semibold text-text-primary capitalize">
                      {currentSuggestion.type.replace('_', ' ')} Correction
                    </h4>
                    <p className={`text-sm font-medium ${getConfidenceColor(currentSuggestion.confidence)}`}>
                      {Math.round(currentSuggestion.confidence * 100)}% confidence
                    </p>
                  </div>
                </div>
                
                <div className="text-sm text-text-secondary">
                  {suggestions.indexOf(currentSuggestion) + 1} of {suggestions.length}
                </div>
              </div>

              {/* Suggestion Details */}
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-text-secondary mb-1">Original:</div>
                  <div className="p-2 bg-red-50 border border-red-200 rounded text-sm">
                    "{currentSuggestion.original}"
                  </div>
                </div>
                
                <div>
                  <div className="text-sm text-text-secondary mb-1">Suggested:</div>
                  <div className="p-2 bg-green-50 border border-green-200 rounded text-sm">
                    "{currentSuggestion.suggested}"
                  </div>
                </div>

                {showExplanations && (
                  <div>
                    <div className="text-sm text-text-secondary mb-1">Explanation:</div>
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm">
                      {currentSuggestion.explanation}
                    </div>
                  </div>
                )}

                {/* Learning Points */}
                {currentSuggestion.learningPoints.length > 0 && (
                  <div>
                    <div className="text-sm text-text-secondary mb-2">💡 Learning Points:</div>
                    <ul className="space-y-1">
                      {currentSuggestion.learningPoints.map((point, index) => (
                        <li key={index} className="text-sm text-text-secondary flex items-start">
                          <span className="text-yellow-500 mr-2">•</span>
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-border-DEFAULT">
                <button
                  onClick={() => applySuggestion(currentSuggestion, false)}
                  className="flex items-center px-4 py-2 text-text-secondary border border-border-DEFAULT rounded-md hover:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT transition-colors"
                >
                  <FiX className="h-4 w-4 mr-2" />
                  Skip
                </button>
                
                <button
                  onClick={() => applySuggestion(currentSuggestion, true)}
                  className="flex items-center px-6 py-2 bg-primary-DEFAULT text-primary-contrast rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2 transition-colors"
                >
                  <FiCheck className="h-4 w-4 mr-2" />
                  Apply
                </button>
              </div>
            </motion.div>
          )}

          {/* Session Progress */}
          <div className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-4">
            <h4 className="font-semibold text-text-primary mb-3">Session Progress</h4>
            
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-text-secondary">Corrections Applied:</span>
                <span className="font-medium text-green-600">{sessionStats.correctionsApplied}</span>
              </div>
              
              <div className="flex justify-between text-sm">
                <span className="text-text-secondary">Corrections Skipped:</span>
                <span className="font-medium text-yellow-600">{sessionStats.correctionsSkipped}</span>
              </div>
              
              <div className="flex justify-between text-sm">
                <span className="text-text-secondary">Current Accuracy:</span>
                <span className="font-medium text-blue-600">
                  {Math.round(sessionStats.accuracy * 100)}%
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-4">
              <div className="flex justify-between text-xs text-text-secondary mb-1">
                <span>Progress</span>
                <span>
                  {currentSuggestion ? suggestions.indexOf(currentSuggestion) + 1 : suggestions.length} / {suggestions.length}
                </span>
              </div>
              <div className="w-full bg-background-secondary rounded-full h-2">
                <div
                  className="bg-primary-DEFAULT h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${currentSuggestion ? 
                      ((suggestions.indexOf(currentSuggestion) + 1) / suggestions.length) * 100 
                      : 100}%`
                  }}
                />
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border border-border-DEFAULT p-4">
            <h4 className="font-semibold text-text-primary mb-3">Quick Actions</h4>
            
            <div className="space-y-2">
              <button
                onClick={() => setShowExplanations(!showExplanations)}
                className="flex items-center w-full px-3 py-2 text-sm text-text-secondary hover:bg-background-secondary rounded transition-colors"
              >
                <FiEye className="h-4 w-4 mr-2" />
                {showExplanations ? 'Hide' : 'Show'} Explanations
              </button>
              
              <button
                onClick={loadCorrectionSuggestions}
                className="flex items-center w-full px-3 py-2 text-sm text-text-secondary hover:bg-background-secondary rounded transition-colors"
              >
                <FiRefreshCw className="h-4 w-4 mr-2" />
                Re-analyze Transcript
              </button>
              
              <button
                onClick={() => window.open('/learning/help', '_blank')}
                className="flex items-center w-full px-3 py-2 text-sm text-text-secondary hover:bg-background-secondary rounded transition-colors"
              >
                <FiBookOpen className="h-4 w-4 mr-2" />
                Learning Guide
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractiveLearningInterface;