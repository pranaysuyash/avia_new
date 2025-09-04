import React from 'react';
import { View } from 'react-native';

type SkeletonProps = {
  width?: number | string;
  height?: number;
  radius?: number;
  style?: any;
};

export const SkeletonLine: React.FC<SkeletonProps> = ({ width = '100%', height = 12, radius = 6, style }) => (
  <View
    style={[
      {
        width,
        height,
        borderRadius: radius,
        backgroundColor: '#e6e8eb',
        marginVertical: 6,
      },
      style,
    ]}
    accessibilityRole="progressbar"
    accessibilityLabel="Loading"
  />
);

export const SkeletonBlock: React.FC<SkeletonProps> = ({ width = '100%', height = 80, radius = 8, style }) => (
  <View
    style={[
      {
        width,
        height,
        borderRadius: radius,
        backgroundColor: '#e6e8eb',
        marginVertical: 8,
      },
      style,
    ]}
    accessibilityRole="progressbar"
    accessibilityLabel="Loading content"
  />
);

export default { SkeletonLine, SkeletonBlock };

export const SkeletonList: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <>
    {Array.from({ length: rows }).map((_, idx) => (
      <View key={idx} style={{ marginBottom: 12 }}>
        <SkeletonLine width="70%" height={16} />
        <SkeletonLine width="90%" height={12} />
        <SkeletonLine width="50%" height={12} />
      </View>
    ))}
  </>
);
