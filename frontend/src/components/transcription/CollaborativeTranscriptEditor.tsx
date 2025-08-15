/**
 * Collaborative Transcript Editor Component
 * Integrates collaborative editing with transcript-specific features and AI corrections
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { CollaborativeEditor } from '../collaboration/CollaborativeEditor';
import { EnhancedTranscriptEditor, useTranscriptCorrection } from './EnhancedTranscriptEditor';
import { webTheme } from '../../shared/theme';

interface TranscriptSegment {
  id: string | number;
  text: string;
  start_time: number;
  end_time: number;
  speaker?: string;
  confidence?: number;
}

interface CollaborativeUser {
  user_id: number;
  username: string;
  avatar_url?: string;
  color: string;
  cursor_position?: number;
  selection_start?: number;
  selection_end?: number;
  is_editing?: boolean;
  last_seen?: string;
}

interface TranscriptEdit {
  segment_id: string | number;
  original_text: string;
  new_text: string;
  user_id: number;
  timestamp: string;
  edit_type: 'manual' | 'ai_suggestion' | 'collaborative';
}

interface CollaborativeTranscriptEditorProps {
  segments: TranscriptSegment[];
  audioUrl: string;
  transcriptionId: string;
  currentUser: CollaborativeUser;
  sessionId?: string;
  onSegmentUpdate?: (segmentId: string | number, newText: string, editType: string) => void;
  onCollaborativeEdit?: (edit: TranscriptEdit) => void;
  className?: string;
}

export const CollaborativeTranscriptEditor: React.FC<CollaborativeTranscriptEditorProps> = ({
  segments,
  audioUrl,
  transcriptionId,
  currentUser,
  sessionId = `transcript_${transcriptionId}`,
  onSegmentUpdate,
  onCollaborativeEdit,
  className = '',
}) => {
  const [activeUsers, setActiveUsers] = useState<CollaborativeUser[]>([currentUser]);
  const [editingSegments, setEditingSegments] = useState<Set<string | number>>(new Set());
  const [segmentLocks, setSegmentLocks] = useState<Map<string | number, number>>(new Map());
  const [collaborativeEdits, setCollaborativeEdits] = useState<TranscriptEdit[]>([]);
  const [showAISuggestions, setShowAISuggestions] = useState(true);
  const [showCollaborativeIndicators, setShowCollaborativeIndicators] = useState(true);
  const [versionHistory, setVersionHistory] = useState<any[]>([]);
  
  const wsRef = useRef<WebSocket | null>(null);
  const { correctText, getSuggestions, isProcessing } = useTranscriptCorrection(currentUser.user_id.toString());

  // WebSocket connection for real-time collaboration
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `ws://localhost:8000/ws/transcript/${transcriptionId}/${sessionId}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Connected to collaborative transcript editing');
        // Send user join event
        wsRef.current?.send(JSON.stringify({
          type: 'user_join',
          user: currentUser,
          timestamp: new Date().toISOString()
        }));
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      wsRef.current.onclose = () => {
        console.log('Disconnected from collaborative editing');
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [transcriptionId, sessionId, currentUser]);

  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'user_joined':
        setActiveUsers(prev => {
          const existing = prev.find(u => u.user_id === data.user.user_id);
          if (existing) return prev;
          return [...prev, data.user];
        });
        break;

      case 'user_left':
        setActiveUsers(prev => prev.filter(u => u.user_id !== data.user_id));
        setSegmentLocks(prev => {
          const newLocks = new Map(prev);
          for (const [segmentId, userId] of newLocks.entries()) {
            if (userId === data.user_id) {
              newLocks.delete(segmentId);
            }
          }
          return newLocks;
        });
        break;

      case 'segment_edit_start':
        setSegmentLocks(prev => new Map(prev).set(data.segment_id, data.user_id));
        setEditingSegments(prev => new Set(prev).add(data.segment_id));
        break;

      case 'segment_edit_end':
        setSegmentLocks(prev => {
          const newLocks = new Map(prev);
          newLocks.delete(data.segment_id);
          return newLocks;
        });
        setEditingSegments(prev => {
          const newSet = new Set(prev);
          newSet.delete(data.segment_id);
          return newSet;
        });
        break;

      case 'segment_updated':
        const edit: TranscriptEdit = {
          segment_id: data.segment_id,
          original_text: data.original_text,
          new_text: data.new_text,
          user_id: data.user_id,
          timestamp: data.timestamp,
          edit_type: data.edit_type || 'collaborative'
        };
        
        setCollaborativeEdits(prev => [edit, ...prev.slice(0, 49)]); // Keep last 50 edits
        onCollaborativeEdit?.(edit);
        onSegmentUpdate?.(data.segment_id, data.new_text, data.edit_type);
        break;

      case 'ai_suggestion':
        // Handle AI suggestions from other users
        break;

      case 'version_created':
        setVersionHistory(prev => [data.version, ...prev]);
        break;
    }
  }, [onSegmentUpdate, onCollaborativeEdit]);

  const handleSegmentEditStart = useCallback((segmentId: string | number) => {
    // Check if segment is locked by another user
    const lockingUserId = segmentLocks.get(segmentId);
    if (lockingUserId && lockingUserId !== currentUser.user_id) {
      const lockingUser = activeUsers.find(u => u.user_id === lockingUserId);
      alert(`This segment is currently being edited by ${lockingUser?.username || 'another user'}`);
      return false;
    }

    // Lock the segment for this user
    wsRef.current?.send(JSON.stringify({
      type: 'segment_edit_start',
      segment_id: segmentId,
      user_id: currentUser.user_id,
      timestamp: new Date().toISOString()
    }));

    return true;
  }, [segmentLocks, activeUsers, currentUser]);

  const handleSegmentEditEnd = useCallback((segmentId: string | number) => {
    wsRef.current?.send(JSON.stringify({
      type: 'segment_edit_end',
      segment_id: segmentId,
      user_id: currentUser.user_id,
      timestamp: new Date().toISOString()
    }));
  }, [currentUser]);

  const handleSegmentUpdate = useCallback(async (segmentId: string | number, newText: string, editType: string = 'manual') => {
    const segment = segments.find(s => s.id === segmentId);
    if (!segment) return;

    // Apply AI corrections if enabled and it's a manual edit
    let finalText = newText;
    if (showAISuggestions && editType === 'manual') {
      const correctionResult = await correctText(newText);
      if (correctionResult && correctionResult.corrected_text !== newText) {
        finalText = correctionResult.corrected_text;
        editType = 'ai_suggestion';
      }
    }

    // Send update to other users
    wsRef.current?.send(JSON.stringify({
      type: 'segment_updated',
      segment_id: segmentId,
      original_text: segment.text,
      new_text: finalText,
      user_id: currentUser.user_id,
      edit_type: editType,
      timestamp: new Date().toISOString()
    }));

    // Update local state
    onSegmentUpdate?.(segmentId, finalText, editType);
    handleSegmentEditEnd(segmentId);
  }, [segments, showAISuggestions, correctText, currentUser, onSegmentUpdate]);

  const createVersion = useCallback(async (description: string) => {
    try {
      const response = await fetch(`/api/transcripts/${transcriptionId}/versions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description,
          segments: segments,
          created_by: currentUser.user_id
        }),
      });

      if (response.ok) {
        const version = await response.json();
        wsRef.current?.send(JSON.stringify({
          type: 'version_created',
          version,
          user_id: currentUser.user_id,
          timestamp: new Date().toISOString()
        }));
      }
    } catch (error) {
      console.error('Failed to create version:', error);
    }
  }, [transcriptionId, segments, currentUser]);

  const renderCollaborativeIndicators = () => {
    if (!showCollaborativeIndicators) return null;

    return (
      <div style={{ 
        marginBottom: webTheme.spacing['4'],
        padding: webTheme.spacing['3'],
        backgroundColor: webTheme.colors.background.secondary,
        borderRadius: webTheme.borderRadius.lg,
        border: `1px solid ${webTheme.colors.border.light}`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h4 style={{ margin: 0, fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
              👥 Collaborative Session
            </h4>
            <p style={{ margin: `${webTheme.spacing['1']} 0 0 0`, fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
              {activeUsers.length} user{activeUsers.length !== 1 ? 's' : ''} active
            </p>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: webTheme.spacing['3'] }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: webTheme.spacing['2'] }}>
              {activeUsers.slice(0, 5).map((user) => (
                <div
                  key={user.user_id}
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: user.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: webTheme.typography.fontSize.sm,
                    fontWeight: webTheme.typography.fontWeight.medium,
                    border: user.user_id === currentUser.user_id ? `2px solid ${webTheme.colors.primary['500']}` : 'none',
                  }}
                  title={user.username}
                >
                  {user.username.charAt(0).toUpperCase()}
                </div>
              ))}
              {activeUsers.length > 5 && (
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: webTheme.colors.gray['400'],
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: webTheme.typography.fontSize.sm,
                }}>
                  +{activeUsers.length - 5}
                </div>
              )}
            </div>
            
            <button
              onClick={() => createVersion('Manual save')}
              style={{
                padding: `${webTheme.spacing['2']} ${webTheme.spacing['3']}`,
                backgroundColor: webTheme.colors.primary['600'],
                color: 'white',
                border: 'none',
                borderRadius: webTheme.borderRadius.DEFAULT,
                fontSize: webTheme.typography.fontSize.sm,
                cursor: 'pointer',
              }}
            >
              💾 Save Version
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderEditHistory = () => {
    if (collaborativeEdits.length === 0) return null;

    return (
      <div style={{ 
        marginTop: webTheme.spacing['6'],
        padding: webTheme.spacing['4'],
        backgroundColor: webTheme.colors.background.secondary,
        borderRadius: webTheme.borderRadius.lg,
        border: `1px solid ${webTheme.colors.border.light}`,
      }}>
        <h4 style={{ margin: `0 0 ${webTheme.spacing['3']} 0`, fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
          📝 Recent Edits
        </h4>
        
        <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
          {collaborativeEdits.slice(0, 10).map((edit, index) => {
            const user = activeUsers.find(u => u.user_id === edit.user_id);
            const editTypeIcon = edit.edit_type === 'ai_suggestion' ? '🤖' : 
                                edit.edit_type === 'collaborative' ? '👥' : '✏️';
            
            return (
              <div
                key={`${edit.segment_id}-${edit.timestamp}-${index}`}
                style={{
                  padding: webTheme.spacing['3'],
                  marginBottom: webTheme.spacing['2'],
                  backgroundColor: webTheme.colors.background.primary,
                  borderRadius: webTheme.borderRadius.md,
                  border: `1px solid ${webTheme.colors.border.light}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: webTheme.spacing['2'] }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: webTheme.spacing['2'] }}>
                    <span>{editTypeIcon}</span>
                    <span style={{ fontSize: webTheme.typography.fontSize.sm, fontWeight: webTheme.typography.fontWeight.medium }}>
                      {user?.username || 'Unknown User'}
                    </span>
                    <span style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                      edited segment {edit.segment_id}
                    </span>
                  </div>
                  <span style={{ fontSize: webTheme.typography.fontSize.xs, color: webTheme.colors.text.secondary }}>
                    {new Date(edit.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                
                <div style={{ fontSize: webTheme.typography.fontSize.sm }}>
                  <div style={{ color: webTheme.colors.error['600'], textDecoration: 'line-through', marginBottom: webTheme.spacing['1'] }}>
                    {edit.original_text}
                  </div>
                  <div style={{ color: webTheme.colors.success['600'] }}>
                    {edit.new_text}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const enhancedSegments = segments.map(segment => ({
    ...segment,
    isLocked: segmentLocks.has(segment.id) && segmentLocks.get(segment.id) !== currentUser.user_id,
    lockingUser: segmentLocks.has(segment.id) ? 
      activeUsers.find(u => u.user_id === segmentLocks.get(segment.id)) : undefined,
    isBeingEdited: editingSegments.has(segment.id),
  }));

  return (
    <div className={`collaborative-transcript-editor ${className}`}>
      {/* Header */}
      <div style={{ marginBottom: webTheme.spacing['6'] }}>
        <h2 style={{ margin: 0, fontSize: webTheme.typography.fontSize.xl, fontWeight: webTheme.typography.fontWeight.bold }}>
          👥 Collaborative Transcript Editor
        </h2>
        <p style={{ margin: `${webTheme.spacing['2']} 0 0 0`, fontSize: webTheme.typography.fontSize.base, color: webTheme.colors.text.secondary }}>
          Real-time collaborative editing with AI corrections and version control
        </p>
      </div>

      {/* Collaborative Indicators */}
      {renderCollaborativeIndicators()}

      {/* Controls */}
      <div style={{ 
        marginBottom: webTheme.spacing['4'],
        display: 'flex',
        gap: webTheme.spacing['4'],
        alignItems: 'center'
      }}>
        <label style={{ display: 'flex', alignItems: 'center', fontSize: webTheme.typography.fontSize.sm }}>
          <input
            type="checkbox"
            checked={showAISuggestions}
            onChange={(e) => setShowAISuggestions(e.target.checked)}
            style={{ marginRight: webTheme.spacing['2'] }}
          />
          🤖 AI Corrections
        </label>
        
        <label style={{ display: 'flex', alignItems: 'center', fontSize: webTheme.typography.fontSize.sm }}>
          <input
            type="checkbox"
            checked={showCollaborativeIndicators}
            onChange={(e) => setShowCollaborativeIndicators(e.target.checked)}
            style={{ marginRight: webTheme.spacing['2'] }}
          />
          👥 Show Collaboration
        </label>
      </div>

      {/* Enhanced Transcript Editor with Collaborative Features */}
      <EnhancedTranscriptEditor
        segments={enhancedSegments}
        audioUrl={audioUrl}
        transcriptionId={transcriptionId}
        userId={currentUser.user_id.toString()}
        onSegmentUpdate={(segmentId, newText) => handleSegmentUpdate(segmentId, newText, 'manual')}
        onEditStart={handleSegmentEditStart}
        onEditEnd={handleSegmentEditEnd}
        className="collaborative-enhanced"
      />

      {/* Edit History */}
      {renderEditHistory()}
    </div>
  );
};

/**
 * Hook for collaborative transcript editing
 */
export function useCollaborativeTranscriptEditing(transcriptionId: string, currentUser: CollaborativeUser) {
  const [isConnected, setIsConnected] = useState(false);
  const [activeUsers, setActiveUsers] = useState<CollaborativeUser[]>([]);
  const [editHistory, setEditHistory] = useState<TranscriptEdit[]>([]);

  const createVersion = useCallback(async (description: string, segments: TranscriptSegment[]) => {
    try {
      const response = await fetch(`/api/transcripts/${transcriptionId}/versions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description,
          segments,
          created_by: currentUser.user_id
        }),
      });

      if (response.ok) {
        const version = await response.json();
        return version;
      }
    } catch (error) {
      console.error('Failed to create version:', error);
    }
    
    return null;
  }, [transcriptionId, currentUser]);

  const getVersionHistory = useCallback(async () => {
    try {
      const response = await fetch(`/api/transcripts/${transcriptionId}/versions`);
      if (response.ok) {
        const versions = await response.json();
        return versions;
      }
    } catch (error) {
      console.error('Failed to get version history:', error);
    }
    
    return [];
  }, [transcriptionId]);

  return {
    isConnected,
    activeUsers,
    editHistory,
    createVersion,
    getVersionHistory,
  };
}