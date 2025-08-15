/**
 * Enhanced Transcript Editor with AI Correction Integration
 * Connects React UI to the existing TranscriptionCorrectionSystem backend
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { InteractiveTranscript } from './InteractiveTranscript';
import { webTheme } from '../../shared/theme';

interface CorrectionSuggestion {
  type: string;
  original: string;
  suggestion: string;
  confidence: number;
  position: number;
}

interface CorrectionResponse {
  original_text: string;
  corrected_text: string;
  corrections: any[];
  confidence_score: number;
  processing_time_ms: number;
}

interface EnhancedTranscriptEditorProps {
  segments: any[];
  audioUrl: string;
  transcriptionId?: string;
  userId?: string;
  onSegmentUpdate?: (segmentId: string | number, newText: string) => void;
  className?: string;
}

export const EnhancedTranscriptEditor: React.FC<EnhancedTranscriptEditorProps> = ({
  segments,
  audioUrl,
  transcriptionId,
  userId,
  onSegmentUpdate,
  className = '',
}) => {
  const [editingSegmentId, setEditingSegmentId] = useState<string | number | null>(null);
  const [suggestions, setSuggestions] = useState<Map<string | number, CorrectionSuggestion[]>>(new Map());
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [correctionStats, setCorrectionStats] = useState<any>(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const debounceTimer = useRef<NodeJS.Timeout>();

  // Load correction stats on mount
  useEffect(() => {
    loadCorrectionStats();
  }, []);

  const loadCorrectionStats = async () => {
    try {
      const response = await fetch('/api/transcript-correction/stats');
      if (response.ok) {
        const stats = await response.json();
        setCorrectionStats(stats);
      }
    } catch (error) {
      console.error('Failed to load correction stats:', error);
    }
  };

  // Get AI correction suggestions for text
  const getSuggestions = useCallback(async (text: string, segmentId: string | number) => {
    if (!text.trim() || text.length < 3) return;

    try {
      setIsLoadingSuggestions(true);
      const response = await fetch(`/api/transcript-correction/suggestions/${encodeURIComponent(text)}`);
      
      if (response.ok) {
        const data = await response.json();
        setSuggestions(prev => new Map(prev).set(segmentId, data.suggestions));
      }
    } catch (error) {
      console.error('Failed to get suggestions:', error);
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, []);

  // Debounced suggestion loading
  const debouncedGetSuggestions = useCallback((text: string, segmentId: string | number) => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    
    debounceTimer.current = setTimeout(() => {
      getSuggestions(text, segmentId);
    }, 500);
  }, [getSuggestions]);

  // Apply AI correction to text
  const applyAICorrection = useCallback(async (text: string, segmentId: string | number) => {
    try {
      const response = await fetch('/api/transcript-correction/correct', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          correction_types: ['spelling', 'grammar', 'punctuation'],
          user_id: userId,
        }),
      });

      if (response.ok) {
        const result: CorrectionResponse = await response.json();
        return result.corrected_text;
      }
    } catch (error) {
      console.error('Failed to apply AI correction:', error);
    }
    
    return text;
  }, [userId]);

  // Submit correction feedback
  const submitFeedback = useCallback(async (
    originalText: string,
    suggestedCorrection: string,
    userCorrection: string,
    accepted: boolean
  ) => {
    try {
      await fetch('/api/transcript-correction/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          original_text: originalText,
          suggested_correction: suggestedCorrection,
          user_correction: userCorrection,
          accepted,
          correction_type: 'spelling',
          user_id: userId,
        }),
      });
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  }, [userId]);

  // Handle segment editing
  const handleSegmentEdit = useCallback((segmentId: string | number, newText: string) => {
    // Get suggestions for the new text
    if (showSuggestions) {
      debouncedGetSuggestions(newText, segmentId);
    }
    
    // Update parent component
    onSegmentUpdate?.(segmentId, newText);
  }, [debouncedGetSuggestions, onSegmentUpdate, showSuggestions]);

  // Apply suggestion to text
  const applySuggestion = useCallback((
    segmentId: string | number,
    suggestion: CorrectionSuggestion,
    currentText: string
  ) => {
    const newText = currentText.replace(suggestion.original, suggestion.suggestion);
    handleSegmentEdit(segmentId, newText);
    
    // Submit positive feedback
    submitFeedback(suggestion.original, suggestion.suggestion, suggestion.suggestion, true);
    
    // Remove applied suggestion
    setSuggestions(prev => {
      const newSuggestions = new Map(prev);
      const segmentSuggestions = newSuggestions.get(segmentId) || [];
      newSuggestions.set(
        segmentId,
        segmentSuggestions.filter(s => s.position !== suggestion.position)
      );
      return newSuggestions;
    });
  }, [handleSegmentEdit, submitFeedback]);

  // Auto-correct segment
  const autoCorrectSegment = useCallback(async (segmentId: string | number, text: string) => {
    const correctedText = await applyAICorrection(text, segmentId);
    if (correctedText !== text) {
      handleSegmentEdit(segmentId, correctedText);
      submitFeedback(text, correctedText, correctedText, true);
    }
  }, [applyAICorrection, handleSegmentEdit, submitFeedback]);

  // Render correction suggestions overlay
  const renderSuggestionsOverlay = (segmentId: string | number, text: string) => {
    const segmentSuggestions = suggestions.get(segmentId) || [];
    
    if (!showSuggestions || segmentSuggestions.length === 0) return null;

    return (
      <div
        style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          backgroundColor: webTheme.colors.background.primary,
          border: `1px solid ${webTheme.colors.border.DEFAULT}`,
          borderRadius: webTheme.borderRadius.md,
          boxShadow: webTheme.boxShadow.lg,
          zIndex: 1000,
          maxHeight: '200px',
          overflowY: 'auto',
        }}
      >
        <div
          style={{
            padding: webTheme.spacing['2'],
            borderBottom: `1px solid ${webTheme.colors.border.light}`,
            fontSize: webTheme.typography.fontSize.sm,
            fontWeight: webTheme.typography.fontWeight.medium,
            color: webTheme.colors.text.secondary,
          }}
        >
          AI Suggestions {isLoadingSuggestions && '(Loading...)'}
        </div>
        
        {segmentSuggestions.map((suggestion, index) => (
          <div
            key={index}
            style={{
              padding: webTheme.spacing['3'],
              borderBottom: index < segmentSuggestions.length - 1 
                ? `1px solid ${webTheme.colors.border.light}` 
                : 'none',
              cursor: 'pointer',
              transition: 'background-color 150ms',
            }}
            onClick={() => applySuggestion(segmentId, suggestion, text)}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = webTheme.colors.gray['50'];
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ textDecoration: 'line-through', color: webTheme.colors.error['600'] }}>
                  {suggestion.original}
                </span>
                <span style={{ margin: `0 ${webTheme.spacing['2']}` }}>→</span>
                <span style={{ color: webTheme.colors.success['600'], fontWeight: webTheme.typography.fontWeight.medium }}>
                  {suggestion.suggestion}
                </span>
              </div>
              <div style={{ fontSize: webTheme.typography.fontSize.xs, color: webTheme.colors.text.secondary }}>
                {suggestion.type} ({Math.round(suggestion.confidence * 100)}%)
              </div>
            </div>
          </div>
        ))}
        
        <div
          style={{
            padding: webTheme.spacing['2'],
            borderTop: `1px solid ${webTheme.colors.border.light}`,
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <button
            onClick={() => autoCorrectSegment(segmentId, text)}
            style={{
              padding: `${webTheme.spacing['1']} ${webTheme.spacing['3']}`,
              backgroundColor: webTheme.colors.primary['600'],
              color: 'white',
              border: 'none',
              borderRadius: webTheme.borderRadius.DEFAULT,
              fontSize: webTheme.typography.fontSize.sm,
              cursor: 'pointer',
            }}
          >
            Apply All
          </button>
          <button
            onClick={() => setSuggestions(prev => {
              const newSuggestions = new Map(prev);
              newSuggestions.delete(segmentId);
              return newSuggestions;
            })}
            style={{
              padding: `${webTheme.spacing['1']} ${webTheme.spacing['3']}`,
              backgroundColor: 'transparent',
              color: webTheme.colors.text.secondary,
              border: `1px solid ${webTheme.colors.border.DEFAULT}`,
              borderRadius: webTheme.borderRadius.DEFAULT,
              fontSize: webTheme.typography.fontSize.sm,
              cursor: 'pointer',
            }}
          >
            Dismiss
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className={`enhanced-transcript-editor ${className}`}>
      {/* Controls */}
      <div
        style={{
          marginBottom: webTheme.spacing['4'],
          padding: webTheme.spacing['4'],
          backgroundColor: webTheme.colors.background.secondary,
          borderRadius: webTheme.borderRadius.lg,
          border: `1px solid ${webTheme.colors.border.light}`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: webTheme.typography.fontSize.lg, fontWeight: webTheme.typography.fontWeight.semibold }}>
              AI-Powered Transcript Editor
            </h3>
            <p style={{ margin: `${webTheme.spacing['1']} 0 0 0`, fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
              Double-click any segment to edit. AI suggestions will appear automatically.
            </p>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: webTheme.spacing['4'] }}>
            <label style={{ display: 'flex', alignItems: 'center', fontSize: webTheme.typography.fontSize.sm }}>
              <input
                type="checkbox"
                checked={showSuggestions}
             
             onChange={(e) => setShowSuggestions(e.target.checked)}
                style={{ marginRight: webTheme.spacing['2'] }}
              />
              AI Suggestions
            </label>
            
            {correctionStats && (
              <div style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                {correctionStats.learned_patterns} patterns learned
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Enhanced Interactive Transcript */}
      <div style={{ position: 'relative' }}>
        <InteractiveTranscript
          segments={segments.map(segment => ({
            ...segment,
            // Add suggestion overlay for editing segments
            renderOverlay: editingSegmentId === segment.id 
              ? () => renderSuggestionsOverlay(segment.id, segment.text)
              : undefined,
          }))}
          audioUrl={audioUrl}
          enableEdit={true}
          showConfidence={true}
          onSegmentEdit={handleSegmentEdit}
          onEditStart={(segmentId) => {
            setEditingSegmentId(segmentId);
            // Load suggestions when editing starts
            const segment = segments.find(s => s.id === segmentId);
            if (segment && showSuggestions) {
              getSuggestions(segment.text, segmentId);
            }
          }}
          onEditEnd={() => {
            setEditingSegmentId(null);
            // Clear suggestions when editing ends
            setSuggestions(new Map());
          }}
        />
      </div>

      {/* Correction Statistics */}
      {correctionStats && (
        <div
          style={{
            marginTop: webTheme.spacing['6'],
            padding: webTheme.spacing['4'],
            backgroundColor: webTheme.colors.background.secondary,
            borderRadius: webTheme.borderRadius.lg,
            border: `1px solid ${webTheme.colors.border.light}`,
          }}
        >
          <h4 style={{ margin: `0 0 ${webTheme.spacing['3']} 0`, fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
            Correction Statistics
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: webTheme.spacing['4'] }}>
            <div>
              <div style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                Learned Patterns
              </div>
              <div style={{ fontSize: webTheme.typography.fontSize.xl, fontWeight: webTheme.typography.fontWeight.bold, color: webTheme.colors.primary['600'] }}>
                {correctionStats.learned_patterns}
              </div>
            </div>
            <div>
              <div style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                Total Corrections
              </div>
              <div style={{ fontSize: webTheme.typography.fontSize.xl, fontWeight: webTheme.typography.fontWeight.bold, color: webTheme.colors.success['600'] }}>
                {correctionStats.total_corrections}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Hook for transcript correction functionality
 */
export function useTranscriptCorrection(userId?: string) {
  const [isProcessing, setIsProcessing] = useState(false);

  const correctText = useCallback(async (text: string) => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/transcript-correction/correct', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          correction_types: ['spelling', 'grammar', 'punctuation'],
          user_id: userId,
        }),
      });

      if (response.ok) {
        const result: CorrectionResponse = await response.json();
        return result;
      }
    } catch (error) {
      console.error('Correction failed:', error);
    } finally {
      setIsProcessing(false);
    }
    
    return null;
  }, [userId]);

  const getSuggestions = useCallback(async (text: string) => {
    try {
      const response = await fetch(`/api/transcript-correction/suggestions/${encodeURIComponent(text)}`);
      if (response.ok) {
        const data = await response.json();
        return data.suggestions;
      }
    } catch (error) {
      console.error('Failed to get suggestions:', error);
    }
    
    return [];
  }, []);

  return {
    correctText,
    getSuggestions,
    isProcessing,
  };
}