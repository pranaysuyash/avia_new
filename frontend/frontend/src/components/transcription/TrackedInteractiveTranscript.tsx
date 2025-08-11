/**
 * Tracked Interactive Transcript Component
 * Interactive transcript with PostHog event tracking
 */

import React, { useCallback, useRef } from 'react';
import { InteractiveTranscript } from './InteractiveTranscript';
import { trackFunnelEvent } from '../../utils/posthog';

interface TrackedInteractiveTranscriptProps {
  segments: any[];
  audioUrl: string;
  className?: string;
  showTimestamps?: boolean;
  showSpeakers?: boolean;
  showConfidence?: boolean;
  enableSearch?: boolean;
  enableEdit?: boolean;
  transcriptionId?: string;
}

export const TrackedInteractiveTranscript: React.FC<TrackedInteractiveTranscriptProps> = ({
  segments,
  transcriptionId,
  ...props
}) => {
  const segmentPlayCount = useRef<Map<string | number, number>>(new Map());
  const searchCount = useRef(0);
  const editCount = useRef(0);
  const lastSearchTime = useRef<number>(0);

  // Track segment interactions
  const trackSegmentPlay = useCallback((segmentId: string | number) => {
    const playCount = (segmentPlayCount.current.get(segmentId) || 0) + 1;
    segmentPlayCount.current.set(segmentId, playCount);
    
    trackFunnelEvent('SEGMENT_PLAYED', {
      segment_id: segmentId,
      play_count: playCount,
      transcription_id: transcriptionId,
    });
  }, [transcriptionId]);

  // Track search usage
  const trackSearch = useCallback((searchTerm: string) => {
    const now = Date.now();
    const timeSinceLastSearch = now - lastSearchTime.current;
    lastSearchTime.current = now;
    searchCount.current++;
    
    trackFunnelEvent('TRANSCRIPT_SEARCHED', {
      search_term_length: searchTerm.length,
      search_count: searchCount.current,
      time_since_last_search: timeSinceLastSearch,
      transcription_id: transcriptionId,
    });
  }, [transcriptionId]);

  // Track edit interactions
  const trackEdit = useCallback((segmentId: string | number, originalText: string, newText: string) => {
    editCount.current++;
    
    trackFunnelEvent('TRANSCRIPT_EDITED', {
      segment_id: segmentId,
      edit_count: editCount.current,
      text_length_change: newText.length - originalText.length,
      transcription_id: transcriptionId,
    });
  }, [transcriptionId]);

  // Track speaker rename
  const trackSpeakerRename = useCallback((oldName: string, newName: string) => {
    trackFunnelEvent('SPEAKER_RENAMED', {
      old_name: oldName,
      new_name: newName,
      transcription_id: transcriptionId,
    });
  }, [transcriptionId]);

  // Track export
  const trackExport = useCallback((format: string) => {
    trackFunnelEvent('TRANSCRIPT_EXPORTED', {
      format,
      segment_count: segments.length,
      transcription_id: transcriptionId,
    });
  }, [segments.length, transcriptionId]);

  // Create wrapped segments with tracking
  const trackedSegments = segments.map(segment => ({
    ...segment,
    onClick: () => {
      trackSegmentPlay(segment.id);
      segment.onClick?.();
    },
  }));

  return (
    <>
      <InteractiveTranscript
        segments={trackedSegments}
        {...props}
      />
      
      {/* Hidden tracking helpers */}
      <div style={{ display: 'none' }}>
        <input
          type="hidden"
          data-track-search
          onChange={(e) => trackSearch(e.target.value)}
        />
        <input
          type="hidden"
          data-track-edit
          onChange={(e) => {
            const [segmentId, originalText, newText] = e.target.value.split('|');
            trackEdit(segmentId, originalText, newText);
          }}
        />
        <input
          type="hidden"
          data-track-speaker-rename
          onChange={(e) => {
            const [oldName, newName] = e.target.value.split('|');
            trackSpeakerRename(oldName, newName);
          }}
        />
        <input
          type="hidden"
          data-track-export
          onChange={(e) => trackExport(e.target.value)}
        />
      </div>
    </>
  );
};

/**
 * Hook for tracking transcription events
 */
export function useTranscriptionTracking(transcriptionId?: string) {
  const trackTranscriptionStarted = useCallback(() => {
    trackFunnelEvent('TRANSCRIPTION_STARTED', {
      transcription_id: transcriptionId,
      timestamp: new Date().toISOString(),
    });
  }, [transcriptionId]);

  const trackTranscriptionProgress = useCallback((progress: number) => {
    trackFunnelEvent('TRANSCRIPTION_PROGRESS', {
      transcription_id: transcriptionId,
      progress,
    });
  }, [transcriptionId]);

  const trackTranscriptionCompleted = useCallback((duration: number, segmentCount: number) => {
    trackFunnelEvent('TRANSCRIPTION_COMPLETED', {
      transcription_id: transcriptionId,
      duration_ms: duration,
      segment_count: segmentCount,
    });
  }, [transcriptionId]);

  const trackTranscriptionFailed = useCallback((error: string) => {
    trackFunnelEvent('TRANSCRIPTION_FAILED', {
      transcription_id: transcriptionId,
      error,
    });
  }, [transcriptionId]);

  return {
    trackTranscriptionStarted,
    trackTranscriptionProgress,
    trackTranscriptionCompleted,
    trackTranscriptionFailed,
  };
}