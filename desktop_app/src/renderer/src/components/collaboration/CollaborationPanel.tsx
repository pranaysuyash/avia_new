import React, { useState } from 'react';
import {
  Users,
  MessageSquare,
  Activity,
  UserPlus,
  Settings,
  Copy,
  Check,
  X,
  MoreVertical,
  Circle,
  Clock,
  Reply
} from 'lucide-react';
import { useCollaboration } from './CollaborationProvider';

interface CollaborationPanelProps {
  sessionId: string;
  onInvite?: () => void;
}

export const CollaborationPanel: React.FC<CollaborationPanelProps> = ({ sessionId, onInvite }) => {
  const {
    isConnected,
    activeUsers,
    currentUser,
    comments,
    addComment,
    resolveComment,
    replyToComment
  } = useCollaboration();

  const [activeTab, setActiveTab] = useState<'users' | 'comments' | 'activity'>('users');
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyText, setReplyText] = useState('');
  const [copiedSessionId, setCopiedSessionId] = useState(false);

  const handleCopySessionId = () => {
    navigator.clipboard.writeText(sessionId);
    setCopiedSessionId(true);
    setTimeout(() => setCopiedSessionId(false), 2000);
  };

  const handleAddComment = () => {
    if (newComment.trim()) {
      addComment({ text: newComment.trim(), resolved: false });
      setNewComment('');
    }
  };

  const handleReply = (commentId: string) => {
    if (replyText.trim()) {
      replyToComment(commentId, replyText.trim());
      setReplyText('');
      setReplyingTo(null);
    }
  };

  const getUserColor = (userId: string) => {
    // Generate consistent color for user
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-yellow-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500'
    ];
    const index = userId.charCodeAt(0) % colors.length;
    return colors[index];
  };

  return (
    <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold">Collaboration</h3>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-400">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Session ID */}
        <div className="bg-gray-900 rounded p-2">
          <div className="text-xs text-gray-400 mb-1">Session ID</div>
          <div className="flex items-center justify-between">
            <code className="text-xs text-gray-300">{sessionId}</code>
            <button
              onClick={handleCopySessionId}
              className="p-1 hover:bg-gray-700 rounded transition"
            >
              {copiedSessionId ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        <button
          onClick={onInvite}
          className="mt-3 w-full flex items-center justify-center gap-2 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        >
          <UserPlus className="w-4 h-4" />
          Invite Collaborators
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-700">
        <button
          onClick={() => setActiveTab('users')}
          className={`flex-1 py-2 text-sm font-medium transition ${
            activeTab === 'users'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Users className="w-4 h-4 mx-auto mb-1" />
          Users ({activeUsers.length})
        </button>
        <button
          onClick={() => setActiveTab('comments')}
          className={`flex-1 py-2 text-sm font-medium transition ${
            activeTab === 'comments'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <MessageSquare className="w-4 h-4 mx-auto mb-1" />
          Comments ({comments.filter(c => !c.resolved).length})
        </button>
        <button
          onClick={() => setActiveTab('activity')}
          className={`flex-1 py-2 text-sm font-medium transition ${
            activeTab === 'activity'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Activity className="w-4 h-4 mx-auto mb-1" />
          Activity
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'users' && (
          <div className="p-4 space-y-3">
            {activeUsers.map(user => (
              <div key={user.id} className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full ${getUserColor(user.id)} flex items-center justify-center text-white text-sm font-medium`}>
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-sm">
                    {user.name}
                    {user.id === currentUser?.id && <span className="text-gray-400 ml-1">(You)</span>}
                  </div>
                  <div className="text-xs text-gray-400">{user.email}</div>
                </div>
                <Circle className={`w-2 h-2 ${user.id === currentUser?.id ? 'text-green-500' : 'text-gray-500'} fill-current`} />
              </div>
            ))}
          </div>
        )}

        {activeTab === 'comments' && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {comments.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No comments yet</p>
                </div>
              ) : (
                comments.map(comment => (
                  <div key={comment.id} className={`space-y-2 ${comment.resolved ? 'opacity-50' : ''}`}>
                    <div className="bg-gray-900 rounded-lg p-3">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className={`w-6 h-6 rounded-full ${getUserColor(comment.userId)} flex items-center justify-center text-white text-xs font-medium`}>
                            {activeUsers.find(u => u.id === comment.userId)?.name.charAt(0) || '?'}
                          </div>
                          <span className="text-sm font-medium">
                            {activeUsers.find(u => u.id === comment.userId)?.name || 'Unknown'}
                          </span>
                          <span className="text-xs text-gray-400">
                            {new Date(comment.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <button className="p-1 hover:bg-gray-800 rounded">
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </div>
                      <p className="text-sm text-gray-300 mb-2">{comment.text}</p>
                      <div className="flex items-center gap-2">
                        {!comment.resolved && (
                          <>
                            <button
                              onClick={() => setReplyingTo(comment.id)}
                              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                            >
                              <Reply className="w-3 h-3" />
                              Reply
                            </button>
                            <button
                              onClick={() => resolveComment(comment.id)}
                              className="text-xs text-green-400 hover:text-green-300 flex items-center gap-1"
                            >
                              <Check className="w-3 h-3" />
                              Resolve
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Replies */}
                    {comment.replies && comment.replies.length > 0 && (
                      <div className="ml-8 space-y-2">
                        {comment.replies.map(reply => (
                          <div key={reply.id} className="bg-gray-900/50 rounded-lg p-2">
                            <div className="flex items-center gap-2 mb-1">
                              <div className={`w-5 h-5 rounded-full ${getUserColor(reply.userId)} flex items-center justify-center text-white text-xs font-medium`}>
                                {activeUsers.find(u => u.id === reply.userId)?.name.charAt(0) || '?'}
                              </div>
                              <span className="text-xs font-medium">
                                {activeUsers.find(u => u.id === reply.userId)?.name || 'Unknown'}
                              </span>
                              <span className="text-xs text-gray-400">
                                {new Date(reply.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="text-xs text-gray-300 ml-7">{reply.text}</p>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Reply input */}
                    {replyingTo === comment.id && (
                      <div className="ml-8 flex gap-2">
                        <input
                          type="text"
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && handleReply(comment.id)}
                          placeholder="Write a reply..."
                          className="flex-1 px-3 py-1 bg-gray-900 border border-gray-700 rounded text-sm focus:outline-none focus:border-blue-500"
                          autoFocus
                        />
                        <button
                          onClick={() => handleReply(comment.id)}
                          className="p-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setReplyingTo(null);
                            setReplyText('');
                          }}
                          className="p-1 bg-gray-700 text-white rounded hover:bg-gray-600"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* New comment input */}
            <div className="p-4 border-t border-gray-700">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddComment()}
                  placeholder="Add a comment..."
                  className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleAddComment}
                  disabled={!newComment.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="p-4 space-y-3">
            <div className="text-center text-gray-500 py-8">
              <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Activity feed coming soon</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CollaborationPanel;