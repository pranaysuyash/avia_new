import React from 'react';
import { useCollaboration } from './CollaborationProvider';
import { Users, Circle } from 'lucide-react';

interface PresenceIndicatorProps {
  maxDisplay?: number;
  showNames?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const PresenceIndicator: React.FC<PresenceIndicatorProps> = ({
  maxDisplay = 5,
  showNames = false,
  size = 'md'
}) => {
  const { activeUsers, currentUser, isConnected } = useCollaboration();

  const sizeClasses = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-10 h-10 text-base'
  };

  const getUserColor = (userId: string) => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-yellow-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-red-500',
      'bg-orange-500'
    ];
    const index = userId.charCodeAt(0) % colors.length;
    return colors[index];
  };

  const displayUsers = activeUsers.filter(u => u.id !== currentUser?.id).slice(0, maxDisplay);
  const remainingCount = Math.max(0, activeUsers.length - maxDisplay - 1);

  if (!isConnected) {
    return (
      <div className="flex items-center gap-2 text-gray-500">
        <Circle className="w-2 h-2 fill-current" />
        <span className="text-sm">Offline</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center">
        <Users className="w-4 h-4 text-gray-400 mr-2" />
        
        {/* Current user */}
        {currentUser && (
          <div className="relative group">
            <div className={`${sizeClasses[size]} ${getUserColor(currentUser.id)} rounded-full flex items-center justify-center text-white font-medium ring-2 ring-gray-900 -mr-2`}>
              {currentUser.name.charAt(0).toUpperCase()}
            </div>
            {showNames && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                {currentUser.name} (You)
              </div>
            )}
          </div>
        )}

        {/* Other users */}
        {displayUsers.map((user, index) => (
          <div key={user.id} className="relative group">
            <div 
              className={`${sizeClasses[size]} ${getUserColor(user.id)} rounded-full flex items-center justify-center text-white font-medium ring-2 ring-gray-900 -mr-2 hover:z-10 transition-transform hover:scale-110`}
              style={{ zIndex: maxDisplay - index }}
            >
              {user.name.charAt(0).toUpperCase()}
            </div>
            {showNames && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
                {user.name}
              </div>
            )}
          </div>
        ))}

        {/* Remaining count */}
        {remainingCount > 0 && (
          <div className={`${sizeClasses[size]} bg-gray-700 rounded-full flex items-center justify-center text-white font-medium ring-2 ring-gray-900`}>
            +{remainingCount}
          </div>
        )}
      </div>

      {/* Status text */}
      <span className="text-sm text-gray-400">
        {activeUsers.length === 1 ? '1 user online' : `${activeUsers.length} users online`}
      </span>
    </div>
  );
};

export default PresenceIndicator;