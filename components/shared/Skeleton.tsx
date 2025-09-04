import React from 'react';

export const SkeletonLine: React.FC<{ width?: string; height?: number }>
  = ({ width = '100%', height = 12 }) => (
  <div
    style={{
      width,
      height,
      background: 'rgba(148,163,184,0.2)',
      borderRadius: 4,
      marginBottom: 6,
    }}
  />
);

export const SkeletonBlock: React.FC<{ rows?: number }>
  = ({ rows = 3 }) => (
  <div style={{ padding: 12, border: '1px solid rgba(148,163,184,0.3)', borderRadius: 8 }}>
    <SkeletonLine width="60%" height={16} />
    {Array.from({ length: rows }).map((_, i) => (
      <SkeletonLine key={i} width={`${90 - i * 10}%`} height={12} />
    ))}
  </div>
);

export default { SkeletonLine, SkeletonBlock };

