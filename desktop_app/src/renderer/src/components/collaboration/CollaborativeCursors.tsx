import React, { useEffect, useRef } from 'react';
import { useCollaboration } from './CollaborationProvider';

interface CollaborativeCursorsProps {
  containerRef: React.RefObject<HTMLElement>;
}

export const CollaborativeCursors: React.FC<CollaborativeCursorsProps> = ({ containerRef }) => {
  const { cursors, activeUsers, updateCursor } = useCollaboration();
  const lastMousePosition = useRef({ x: 0, y: 0 });
  const throttleTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const handleMouseMove = (e: MouseEvent) => {
      const container = containerRef.current;
      if (!container) return;

      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;

      lastMousePosition.current = { x, y };

      // Throttle cursor updates to avoid overwhelming the server
      if (!throttleTimeout.current) {
        throttleTimeout.current = setTimeout(() => {
          updateCursor(lastMousePosition.current);
          throttleTimeout.current = null;
        }, 50); // Update every 50ms max
      }
    };

    const handleMouseLeave = () => {
      updateCursor({ x: -1, y: -1 }); // Hide cursor when leaving
    };

    containerRef.current.addEventListener('mousemove', handleMouseMove);
    containerRef.current.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      if (containerRef.current) {
        containerRef.current.removeEventListener('mousemove', handleMouseMove);
        containerRef.current.removeEventListener('mouseleave', handleMouseLeave);
      }
      if (throttleTimeout.current) {
        clearTimeout(throttleTimeout.current);
      }
    };
  }, [containerRef, updateCursor]);

  const getUserInfo = (userId: string) => {
    const user = activeUsers.find(u => u.id === userId);
    return {
      name: user?.name || 'Unknown',
      color: user?.color || '#3B82F6'
    };
  };

  return (
    <>
      {Array.from(cursors.entries()).map(([userId, cursor]) => {
        if (cursor.x < 0 || cursor.y < 0) return null; // Hidden cursor
        
        const userInfo = getUserInfo(userId);
        
        return (
          <div
            key={userId}
            className="absolute pointer-events-none z-50 transition-all duration-100"
            style={{
              left: `${cursor.x}%`,
              top: `${cursor.y}%`,
              transform: 'translate(-50%, -50%)'
            }}
          >
            {/* Cursor */}
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              className="drop-shadow-md"
            >
              <path
                d="M5.5 3.5L19.5 12L12 12L12 19.5L5.5 3.5Z"
                fill={userInfo.color}
                stroke="white"
                strokeWidth="1"
              />
            </svg>
            
            {/* User label */}
            <div
              className="absolute top-5 left-2 px-2 py-1 rounded text-xs text-white whitespace-nowrap"
              style={{ backgroundColor: userInfo.color }}
            >
              {userInfo.name}
            </div>
          </div>
        );
      })}
    </>
  );
};

export default CollaborativeCursors;