/**
 * Collaborative Transcript Component
 * Real-time collaborative editing with WebRTC
 */

import React, { useCallback, useRef, useEffect, useState } from 'react';
import { useCollaboration } from '../../hooks/useCollaboration';
import { InteractiveTranscript } from '../transcription/InteractiveTranscript';
import { webTheme } from '../../../shared/theme';

interface CollaboratorCursor {
  userId: string;
  userName: string;
  color: string;
  x: number;
  y: number;
}

interface CollaborativeTranscriptProps {
  roomId: string;
  userId: string;
  userName: string;
  segments: any[];
  audioUrl: string;
  onSegmentEdit?: (segmentId: string, newText: string) => void;
}

export const CollaborativeTranscript: React.FC<CollaborativeTranscriptProps> = ({
  roomId,
  userId,
  userName,
  segments,
  audioUrl,
  onSegmentEdit,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [localEdits, setLocalEdits] = useState<Map<string, string>>(new Map());
  const [collaboratorCursors, setCollaboratorCursors] = useState<CollaboratorCursor[]>([]);

  const {
    isConnected,
    collaborators,
    error,
    sendCursor,
    sendSelection,
    sendEdit,
    sendPresence,
  } = useCollaboration({
    roomId,
    userId,
    userName,
    onMessage: handleCollaborationMessage,
  });

  // Handle incoming collaboration messages
  function handleCollaborationMessage(message: any) {
    switch (message.type) {
      case 'edit':
        // Apply remote edit
        if (message.userId !== userId) {
          setLocalEdits(prev => {
            const edits = new Map(prev);
            edits.set(message.data.segmentId, message.data.text);
            return edits;
          });
        }
        break;
    }
  }

  // Track mouse movement for cursor sharing
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      sendCursor(x, y);
    };

    const handleMouseLeave = () => {
      sendCursor(-1, -1); // Hide cursor
    };

    container.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      container.removeEventListener('mousemove', handleMouseMove);
      container.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [sendCursor]);

  // Update collaborator cursors
  useEffect(() => {
    const cursors = collaborators
      .filter(c => c.cursor && c.cursor.x >= 0 && c.cursor.y >= 0)
      .map(c => ({
        userId: c.userId,
        userName: c.userName,
        color: c.cursorColor,
        x: c.cursor!.x,
        y: c.cursor!.y,
      }));
    
    setCollaboratorCursors(cursors);
  }, [collaborators]);

  // Send presence updates
  useEffect(() => {
    sendPresence(true);

    const handleVisibilityChange = () => {
      sendPresence(!document.hidden);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      sendPresence(false);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [sendPresence]);

  // Handle segment edit
  const handleSegmentEdit = useCallback((segmentId: string, newText: string) => {
    // Send edit to collaborators
    sendEdit({
      segmentId,
      text: newText,
    });

    // Update local state
    setLocalEdits(prev => {
      const edits = new Map(prev);
      edits.set(segmentId, newText);
      return edits;
    });

    // Call parent handler
    onSegmentEdit?.(segmentId, newText);
  }, [sendEdit, onSegmentEdit]);

  // Handle text selection
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      const start = range.startOffset;
      const end = range.endOffset;
      
      if (start !== end) {
        sendSelection(start, end);
      }
    }
  }, [sendSelection]);

  // Merge local edits with segments
  const mergedSegments = segments.map(segment => ({
    ...segment,
    text: localEdits.get(segment.id) || segment.text,
  }));

  return (
    <div 
      ref={containerRef}
      style={{ position: 'relative' }}
      onMouseUp={handleTextSelection}
    >
      {/* Connection Status */}
      <div
        style={{
          position: 'absolute',
          top: webTheme.spacing['2'],
          right: webTheme.spacing['2'],
          zIndex: webTheme.zIndex.dropdown,
          display: 'flex',
          alignItems: 'center',
          gap: webTheme.spacing['2'],
          padding: `${webTheme.spacing['2']} ${webTheme.spacing['3']}`,
          backgroundColor: isConnected 
            ? webTheme.colors.success['50']
            : error 
            ? webTheme.colors.error['50']
            : webTheme.colors.warning['50'],
          borderRadius: webTheme.borderRadius.full,
          fontSize: webTheme.typography.fontSize.sm,
        }}
      >
        <div
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isConnected
              ? webTheme.colors.success.DEFAULT
              : error
              ? webTheme.colors.error.DEFAULT
              : webTheme.colors.warning.DEFAULT,
          }}
        />
        <span style={{ 
          color: isConnected 
            ? webTheme.colors.success['700']
            : error
            ? webTheme.colors.error['700']
            : webTheme.colors.warning['700']
        }}>
          {isConnected 
            ? `${collaborators.length + 1} collaborators`
            : error
            ? 'Connection error'
            : 'Connecting...'}
        </span>
      </div>

      {/* Collaborator List */}
      {isConnected && collaborators.length > 0 && (
        <div
          style={{
            position: 'absolute',
            top: webTheme.spacing['12'],
            right: webTheme.spacing['2'],
            zIndex: webTheme.zIndex.dropdown,
            backgroundColor: webTheme.colors.background.primary,
            borderRadius: webTheme.borderRadius.lg,
            boxShadow: webTheme.boxShadow.md,
            padding: webTheme.spacing['3'],
            minWidth: '200px',
          }}
        >
          <h4
            style={{
              fontSize: webTheme.typography.fontSize.sm,
              fontWeight: webTheme.typography.fontWeight.semibold,
              marginBottom: webTheme.spacing['2'],
              color: webTheme.colors.text.primary,
            }}
          >
            Active Collaborators
          </h4>
          {collaborators.map(collaborator => (
            <div
              key={collaborator.userId}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: webTheme.spacing['2'],
                marginBottom: webTheme.spacing['1'],
              }}
            >
              <div
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  backgroundColor: collaborator.cursorColor,
                  opacity: collaborator.isActive ? 1 : 0.5,
                }}
              />
              <span
                style={{
                  fontSize: webTheme.typography.fontSize.sm,
                  color: collaborator.isActive 
                    ? webTheme.colors.text.primary
                    : webTheme.colors.text.secondary,
                }}
              >
                {collaborator.userName}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Collaborator Cursors */}
      {collaboratorCursors.map(cursor => (
        <div
          key={cursor.userId}
          style={{
            position: 'absolute',
            left: cursor.x,
            top: cursor.y,
            zIndex: webTheme.zIndex.tooltip,
            pointerEvents: 'none',
            transition: 'all 100ms ease-out',
          }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            style={{ transform: 'translate(-2px, -2px)' }}
          >
            <path
              d="M2 2 L2 14 L6 10 L10 16 L12 14 L8 8 L14 8 Z"
              fill={cursor.color}
              stroke="#000"
              strokeWidth="0.5"
            />
          </svg>
          <div
            style={{
              position: 'absolute',
              top: '20px',
              left: '0px',
              backgroundColor: cursor.color,
              color: webTheme.colors.text.inverse,
              padding: `${webTheme.spacing['1']} ${webTheme.spacing['2']}`,
              borderRadius: webTheme.borderRadius.DEFAULT,
              fontSize: webTheme.typography.fontSize.xs,
              whiteSpace: 'nowrap',
              fontWeight: webTheme.typography.fontWeight.medium,
            }}
          >
            {cursor.userName}
          </div>
        </div>
      ))}

      {/* Interactive Transcript */}
      <InteractiveTranscript
        segments={mergedSegments}
        audioUrl={audioUrl}
        enableEdit={true}
        onSegmentEdit={handleSegmentEdit}
      />
    </div>
  );
};