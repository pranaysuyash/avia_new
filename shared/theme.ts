/**
 * Shared Theme Configuration
 * Maps design tokens for use across React, Electron, and React Native
 */

import designTokens from '../design-tokens.json';

// React Web & Electron theme (CSS-in-JS compatible)
export const webTheme = {
  colors: designTokens.colors,
  typography: designTokens.typography,
  spacing: designTokens.spacing,
  sizing: designTokens.sizing,
  borderRadius: designTokens.borderRadius,
  boxShadow: designTokens.boxShadow,
  animation: designTokens.animation,
  breakpoints: designTokens.breakpoints,
  zIndex: designTokens.zIndex,
  opacity: designTokens.opacity,
};

// React Native theme (RN style compatible)
export const mobileTheme = {
  colors: {
    ...Object.entries(designTokens.colors).reduce((acc, [key, value]) => {
      if (typeof value === 'string') {
        acc[key] = value;
      } else if (typeof value === 'object') {
        // Flatten color scales for RN
        Object.entries(value).forEach(([shade, color]) => {
          acc[`${key}${shade}`] = color;
        });
      }
      return acc;
    }, {} as Record<string, string>),
  },
  typography: {
    fontSizes: Object.entries(designTokens.typography.fontSize).reduce((acc, [key, value]) => {
      acc[key] = parseInt(value) * 16; // Convert rem to pixels for RN
      return acc;
    }, {} as Record<string, number>),
    fontWeights: designTokens.typography.fontWeight,
    lineHeights: Object.entries(designTokens.typography.lineHeight).reduce((acc, [key, value]) => {
      acc[key] = parseFloat(value);
      return acc;
    }, {} as Record<string, number>),
  },
  spacing: Object.entries(designTokens.spacing).reduce((acc, [key, value]) => {
    acc[key] = value === '0' ? 0 : parseInt(value) * 4; // Convert rem to pixels
    return acc;
  }, {} as Record<string, number>),
  borderRadius: Object.entries(designTokens.borderRadius).reduce((acc, [key, value]) => {
    if (value === '9999px') {
      acc[key] = 9999;
    } else {
      acc[key] = parseInt(value) * 4;
    }
    return acc;
  }, {} as Record<string, number>),
  shadows: {
    xs: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.05,
      shadowRadius: 2,
      elevation: 1,
    },
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.1,
      shadowRadius: 3,
      elevation: 2,
    },
    DEFAULT: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.1,
      shadowRadius: 6,
      elevation: 3,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 10 },
      shadowOpacity: 0.1,
      shadowRadius: 15,
      elevation: 5,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 20 },
      shadowOpacity: 0.1,
      shadowRadius: 25,
      elevation: 8,
    },
  },
};

// Utility functions for theme usage
export const getColor = (path: string): string => {
  const keys = path.split('.');
  let value: any = designTokens.colors;
  
  for (const key of keys) {
    value = value[key];
    if (!value) return '#000000';
  }
  
  return value;
};

export const getSpacing = (size: string | number): string => {
  if (typeof size === 'number') {
    return `${size * 0.25}rem`;
  }
  return designTokens.spacing[size] || '0';
};

export const getFontSize = (size: string): string => {
  return designTokens.typography.fontSize[size] || '1rem';
};

export const getShadow = (size: string): string => {
  return designTokens.boxShadow[size] || 'none';
};

// Platform-specific theme providers
export const ThemeProvider = {
  web: webTheme,
  mobile: mobileTheme,
  getColor,
  getSpacing,
  getFontSize,
  getShadow,
};