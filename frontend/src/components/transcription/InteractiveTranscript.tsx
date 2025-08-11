/**
 * Interactive Transcript Component for React Web
 * Provides clickable segments with audio synchronization
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { EnhancedAudioPlayer, useAudioPlayer, AudioPlayerRef } from '../audio/EnhancedAudioPlayer';
import { formatTime } from '../../utils/timeUtils';
import { webTheme } from '../../shared/theme';
import './InteractiveTranscript.css';

interface TranscriptSegment {
  id: string | number;
  text: string;
  start_time: number;
  end_time: number;
  speaker?: string;
  confidence?: number;
}

interface InteractiveTranscriptProps {
  segments: TranscriptSegment[];
  audioUrl: string;
  className?: string;
  showTimestamps?: boolean;
  showSpeakers?: boolean;
  showConfidence?: boolean;
  enableSearch?: boolean;
  enableEdit?: boolean;
}

export const InteractiveTranscript: React.FC<InteractiveTranscriptProps> = ({
  segments,
  audioUrl,
  className = '',
  showTimestamps = true,
  showSpeakers = true,
  showConfidence = false,
  enableSearch = true,
  enableEdit = false,
}) => {
  const { playerRef, jumpToTime } = useAudioPlayer();
  const [currentTime, setCurrentTime] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSegmentId, setSelectedSegmentId] = useState<string | number | null>(null);
  const [editingSegmentId, setEditingSegmentId] = useState<string | number | null>(null);
  const [editedSegments, setEditedSegments] = useState<Map<string | number, string>>(new Map());
  const [autoHighlight, setAutoHighlight] = useState(true);

  // Calculate current segment based on playback time
  const getCurrentSegmentId = useCallback(() => {
    const currentSegment = segments.find(
      segment => currentTime >= segment.start_time && currentTime <= segment.end_time
    );
    return currentSegment?.id || null;
  }, [currentTime, segments]);

  // Handle audio time updates
  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time);
    
    if (autoHighlight) {
      const currentSegmentId = getCurrentSegmentId();
      if (currentSegmentId !== selectedSegmentId) {
        setSelectedSegmentId(currentSegmentId);
      }
    }
  }, [autoHighlight, getCurrentSegmentId, selectedSegmentId]);

  // Handle segment click
  const handleSegmentClick = useCallback((segment: TranscriptSegment) => {
    setSelectedSegmentId(segment.id);
    jumpToTime(segment.start_time);
  }, [jumpToTime]);

  // Handle segment edit
  const handleSegmentEdit = useCallback((segmentId: string | number, newText: string) => {
    setEditedSegments(prev => new Map(prev).set(segmentId, newText));
  }, []);

  // Filter segments based on search
  const filteredSegments = segments.filter(segment => {
    if (!searchTerm) return true;
    const text = editedSegments.get(segment.id) || segment.text;
    return text.toLowerCase().includes(searchTerm.toLowerCase());
  });

  // Get segment display text
  const getSegmentText = (segment: TranscriptSegment) => {
    return editedSegments.get(segment.id) || segment.text;
  };

  // Highlight search term in text
  const highlightSearchTerm = (text: string) => {
    if (!searchTerm) return text;
    
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.split(regex).map((part, index) => 
      regex.test(part) ? (
        <mark 
          key={index} 
          style={{ backgroundColor: webTheme.colors.transcript.highlight }}
        >
          {part}
        </mark>
      ) : part
    );
  };

  return (
    <div className={`interactive-transcript ${className}`}>
      {/* Audio Player */}
      <div 
        className="audio-player-container"
        style={{ marginBottom: webTheme.spacing['6'] }}
      >
        <EnhancedAudioPlayer
          ref={playerRef}
          audioUrl={audioUrl}
          onTimeUpdate={handleTimeUpdate}
          className="w-full"
        />
      </div>

      {/* Controls */}
      <div 
        className="transcript-controls"
        style={{ marginBottom: webTheme.spacing['4'] }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center" style={{ gap: webTheme.spacing['4'] }}>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoHighlight}
                onChange={(e) => setAutoHighlight(e.target.checked)}
                style={{ marginRight: webTheme.spacing['2'] }}
              />
              <span style={{ fontSize: webTheme.typography.fontSize.sm }}>
                Auto-highlight current segment
              </span>
            </label>
            
            {enableSearch && (
              <input
                type="text"
                placeholder="Search transcript..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  padding: `${webTheme.spacing['2']} ${webTheme.spacing['3']}`,
                  border: `1px solid ${webTheme.colors.border.DEFAULT}`,
                  borderRadius: webTheme.borderRadius.md,
                  fontSize: webTheme.typography.fontSize.sm,
                }}
              />
            )}
          </div>

          <div 
            className="flex items-center"
            style={{ 
              gap: webTheme.spacing['2'],
              fontSize: webTheme.typography.fontSize.sm 
            }}
          >
            <label>
              <input
                type="checkbox"
                checked={showTimestamps}
                style={{ marginRight: webTheme.spacing['1'] }}
              />
              Timestamps
            </label>
            <label>
              <input
                type="checkbox"
                checked={showSpeakers}
                style={{ marginRight: webTheme.spacing['1'] }}
              />
              Speakers
            </label>
            <label>
              <input
                type="checkbox"
                checked={showConfidence}
                style={{ marginRight: webTheme.spacing['1'] }}
              />
              Confidence
            </label>
          </div>
        </div>
      </div>

      {/* Transcript Segments */}
      <div className="transcript-segments" style={{ gap: webTheme.spacing['2'] }}>
        {filteredSegments.map((segment) => {
          const isCurrentSegment = segment.id === getCurrentSegmentId();
          const isSelected = segment.id === selectedSegmentId;
          const isEditing = segment.id === editingSegmentId;
          const text = getSegmentText(segment);

          return (
            <div
              key={segment.id}
              className="transcript-segment"
              style={{
                padding: webTheme.spacing['4'],
                marginBottom: webTheme.spacing['2'],
                borderRadius: webTheme.borderRadius.lg,
                borderLeft: `4px solid ${
                  isCurrentSegment && autoHighlight 
                    ? webTheme.colors.transcript.current
                    : isSelected 
                    ? webTheme.colors.primary['400']
                    : webTheme.colors.border.light
                }`,
                backgroundColor: 
                  isCurrentSegment && autoHighlight 
                    ? webTheme.colors.warning['50']
                    : isSelected 
                    ? webTheme.colors.primary['50']
                    : webTheme.colors.background.primary,
                boxShadow: webTheme.boxShadow.xs,
                cursor: 'pointer',
                transition: 'all 200ms',
              }}
              onClick={() => !isEditing && handleSegmentClick(segment)}
              onMouseEnter={(e) => {
                if (!isCurrentSegment && !isSelected) {
                  e.currentTarget.style.backgroundColor = webTheme.colors.gray['50'];
                }
              }}
              onMouseLeave={(e) => {
                if (!isCurrentSegment && !isSelected) {
                  e.currentTarget.style.backgroundColor = webTheme.colors.background.primary;
                }
              }}
            >
              <div className="flex items-start">
                {/* Play Button */}
                <button
                  style={{
                    marginRight: webTheme.spacing['3'],
                    padding: webTheme.spacing['2'],
                    borderRadius: webTheme.borderRadius.DEFAULT,
                    transition: 'background-color 150ms',
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSegmentClick(segment);
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = webTheme.colors.gray['200'];
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  {isCurrentSegment && autoHighlight ? '🔊' : '▶️'} 
                  {showTimestamps && (
                    <span 
                      style={{ 
                        marginLeft: webTheme.spacing['1'], 
                        fontSize: webTheme.typography.fontSize.sm 
                      }}
                    >
                      {formatTime(segment.start_time)}
                    </span>
                  )}
                </button>

                {/* Content */}
                <div className="flex-1">
                  {/* Metadata */}
                  <div 
                    className="flex items-center"
                    style={{
                      fontSize: webTheme.typography.fontSize.sm,
                      color: webTheme.colors.text.secondary,
                      marginBottom: webTheme.spacing['1'],
                    }}
                  >
                    {showSpeakers && segment.speaker && (
                      <span 
                        style={{ 
                          fontWeight: webTheme.typography.fontWeight.medium,
                          marginRight: webTheme.spacing['4'],
                          color: webTheme.colors.transcript.speakerColors[
                            segment.id as number % webTheme.colors.transcript.speakerColors.length
                          ]
                        }}
                      >
                        {segment.speaker}
                      </span>
                    )}
                    {showTimestamps && (
                      <span style={{ marginRight: webTheme.spacing['4'] }}>
                        {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                      </span>
                    )}
                    {showConfidence && (
                      <span style={{
                        color: segment.confidence && segment.confidence > 0.9 
                          ? webTheme.colors.success['600']
                          : segment.confidence && segment.confidence < 0.7 
                          ? webTheme.colors.error['600']
                          : webTheme.colors.text.secondary
                      }}>
                        {(segment.confidence || 0).toFixed(2)}
                      </span>
                    )}
                  </div>

                  {/* Text */}
                  {isEditing ? (
                    <textarea
                      value={text}
                      onChange={(e) => handleSegmentEdit(segment.id, e.target.value)}
                      onBlur={() => setEditingSegmentId(null)}
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        width: '100%',
                        padding: webTheme.spacing['2'],
                        border: `1px solid ${webTheme.colors.border.DEFAULT}`,
                        borderRadius: webTheme.borderRadius.DEFAULT,
                      }}
                      autoFocus
                    />
                  ) : (
                    <div
                      className="segment-text"
                      onDoubleClick={() => enableEdit && setEditingSegmentId(segment.id)}
                      style={{
                        fontSize: webTheme.typography.fontSize.base,
                        lineHeight: webTheme.typography.lineHeight.relaxed,
                        color: webTheme.colors.text.primary,
                      }}
                    >
                      {highlightSearchTerm(text)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};