/**
 * React Native Theme Provider
 * Provides theme context using the unified design tokens
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { mobileTheme } from '../../shared/theme';
import { ViewStyle, TextStyle } from 'react-native';

// Define theme types for React Native
interface ThemeColors {
  primary: string;
  primary50: string;
  primary100: string;
  primary200: string;
  primary300: string;
  primary400: string;
  primary500: string;
  primary600: string;
  primary700: string;
  primary800: string;
  primary900: string;
  secondary: string;
  secondary50: string;
  secondary100: string;
  secondary200: string;
  secondary300: string;
  secondary400: string;
  secondary500: string;
  secondary600: string;
  secondary700: string;
  secondary800: string;
  secondary900: string;
  success: string;
  success50: string;
  success100: string;
  success200: string;
  success300: string;
  success400: string;
  success500: string;
  success600: string;
  success700: string;
  success800: string;
  success900: string;
  warning: string;
  warning50: string;
  warning100: string;
  warning200: string;
  warning300: string;
  warning400: string;
  warning500: string;
  warning600: string;
  warning700: string;
  warning800: string;
  warning900: string;
  error: string;
  error50: string;
  error100: string;
  error200: string;
  error300: string;
  error400: string;
  error500: string;
  error600: string;
  error700: string;
  error800: string;
  error900: string;
  gray: string;
  gray50: string;
  gray100: string;
  gray200: string;
  gray300: string;
  gray400: string;
  gray500: string;
  gray600: string;
  gray700: string;
  gray800: string;
  gray900: string;
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  textInverse: string;
  textError: string;
  textSuccess: string;
  backgroundPrimary: string;
  backgroundSecondary: string;
  backgroundTertiary: string;
  backgroundInverse: string;
  backgroundOverlay: string;
  borderLight: string;
  borderDEFAULT: string;
  borderDark: string;
  interactiveHover: string;
  interactiveActive: string;
  interactiveFocus: string;
  interactiveDisabled: string;
  audioWaveform: string;
  audioProgress: string;
  audioBuffered: string;
  audioCurrentTime: string;
  transcriptHighlight: string;
  transcriptSelected: string;
  transcriptCurrent: string;
  transcriptEdited: string;
  transcriptSpeakerColors: string[];
}

interface ThemeTypography {
  fontSizes: {
    xs: number;
    sm: number;
    base: number;
    lg: number;
    xl: number;
    '2xl': number;
    '3xl': number;
    '4xl': number;
    '5xl': number;
  };
  fontWeights: {
    thin: string;
    light: string;
    normal: string;
    medium: string;
    semibold: string;
    bold: string;
    extrabold: string;
    black: string;
  };
  lineHeights: {
    tight: number;
    snug: number;
    normal: number;
    relaxed: number;
    loose: number;
  };
}

interface ThemeSpacing {
  0: number;
  1: number;
  2: number;
  3: number;
  4: number;
  5: number;
  6: number;
  8: number;
  10: number;
  12: number;
  16: number;
  20: number;
  24: number;
  32: number;
  40: number;
  48: number;
  56: number;
  64: number;
}

interface ThemeBorderRadius {
  none: number;
  sm: number;
  DEFAULT: number;
  md: number;
  lg: number;
  xl: number;
  '2xl': number;
  '3xl': number;
  full: number;
}

interface ThemeShadow {
  shadowColor: string;
  shadowOffset: { width: number; height: number };
  shadowOpacity: number;
  shadowRadius: number;
  elevation: number;
}

interface ThemeShadows {
  xs: ThemeShadow;
  sm: ThemeShadow;
  DEFAULT: ThemeShadow;
  md: ThemeShadow;
  lg: ThemeShadow;
}

interface Theme {
  colors: ThemeColors;
  typography: ThemeTypography;
  spacing: ThemeSpacing;
  borderRadius: ThemeBorderRadius;
  shadows: ThemeShadows;
}

// Convert the imported theme to typed theme
const theme: Theme = {
  colors: mobileTheme.colors as ThemeColors,
  typography: mobileTheme.typography as ThemeTypography,
  spacing: mobileTheme.spacing as ThemeSpacing,
  borderRadius: mobileTheme.borderRadius as ThemeBorderRadius,
  shadows: mobileTheme.shadows as ThemeShadows,
};

// Create style helpers
export const createStyles = (theme: Theme) => ({
  // Text styles
  text: {
    h1: {
      fontSize: theme.typography.fontSizes['4xl'],
      fontWeight: theme.typography.fontWeights.bold,
      lineHeight: theme.typography.lineHeights.tight * theme.typography.fontSizes['4xl'],
      color: theme.colors.textPrimary,
    } as TextStyle,
    h2: {
      fontSize: theme.typography.fontSizes['3xl'],
      fontWeight: theme.typography.fontWeights.semibold,
      lineHeight: theme.typography.lineHeights.tight * theme.typography.fontSizes['3xl'],
      color: theme.colors.textPrimary,
    } as TextStyle,
    h3: {
      fontSize: theme.typography.fontSizes['2xl'],
      fontWeight: theme.typography.fontWeights.semibold,
      lineHeight: theme.typography.lineHeights.snug * theme.typography.fontSizes['2xl'],
      color: theme.colors.textPrimary,
    } as TextStyle,
    h4: {
      fontSize: theme.typography.fontSizes.xl,
      fontWeight: theme.typography.fontWeights.medium,
      lineHeight: theme.typography.lineHeights.snug * theme.typography.fontSizes.xl,
      color: theme.colors.textPrimary,
    } as TextStyle,
    body: {
      fontSize: theme.typography.fontSizes.base,
      fontWeight: theme.typography.fontWeights.normal,
      lineHeight: theme.typography.lineHeights.normal * theme.typography.fontSizes.base,
      color: theme.colors.textPrimary,
    } as TextStyle,
    small: {
      fontSize: theme.typography.fontSizes.sm,
      fontWeight: theme.typography.fontWeights.normal,
      lineHeight: theme.typography.lineHeights.normal * theme.typography.fontSizes.sm,
      color: theme.colors.textSecondary,
    } as TextStyle,
    caption: {
      fontSize: theme.typography.fontSizes.xs,
      fontWeight: theme.typography.fontWeights.normal,
      lineHeight: theme.typography.lineHeights.normal * theme.typography.fontSizes.xs,
      color: theme.colors.textTertiary,
    } as TextStyle,
  },
  
  // Button styles
  buttons: {
    primary: {
      container: {
        backgroundColor: theme.colors.primary,
        paddingHorizontal: theme.spacing[4],
        paddingVertical: theme.spacing[2],
        borderRadius: theme.borderRadius.md,
        ...theme.shadows.sm,
      } as ViewStyle,
      text: {
        color: theme.colors.textInverse,
        fontSize: theme.typography.fontSizes.base,
        fontWeight: theme.typography.fontWeights.medium,
      } as TextStyle,
    },
    secondary: {
      container: {
        backgroundColor: theme.colors.gray100,
        paddingHorizontal: theme.spacing[4],
        paddingVertical: theme.spacing[2],
        borderRadius: theme.borderRadius.md,
        borderWidth: 1,
        borderColor: theme.colors.borderDEFAULT,
      } as ViewStyle,
      text: {
        color: theme.colors.textPrimary,
        fontSize: theme.typography.fontSizes.base,
        fontWeight: theme.typography.fontWeights.medium,
      } as TextStyle,
    },
    ghost: {
      container: {
        paddingHorizontal: theme.spacing[3],
        paddingVertical: theme.spacing[2],
      } as ViewStyle,
      text: {
        color: theme.colors.primary,
        fontSize: theme.typography.fontSizes.base,
        fontWeight: theme.typography.fontWeights.medium,
      } as TextStyle,
    },
  },
  
  // Card styles
  card: {
    container: {
      backgroundColor: theme.colors.backgroundPrimary,
      borderRadius: theme.borderRadius.lg,
      padding: theme.spacing[4],
      ...theme.shadows.DEFAULT,
    } as ViewStyle,
    header: {
      marginBottom: theme.spacing[3],
    } as ViewStyle,
    content: {
      // Card content styles
    } as ViewStyle,
  },
  
  // Input styles
  input: {
    container: {
      marginBottom: theme.spacing[3],
    } as ViewStyle,
    field: {
      backgroundColor: theme.colors.backgroundPrimary,
      borderWidth: 1,
      borderColor: theme.colors.borderDEFAULT,
      borderRadius: theme.borderRadius.md,
      paddingHorizontal: theme.spacing[3],
      paddingVertical: theme.spacing[2],
      fontSize: theme.typography.fontSizes.base,
      color: theme.colors.textPrimary,
    } as TextStyle & ViewStyle,
    label: {
      fontSize: theme.typography.fontSizes.sm,
      fontWeight: theme.typography.fontWeights.medium,
      color: theme.colors.textPrimary,
      marginBottom: theme.spacing[1],
    } as TextStyle,
    error: {
      fontSize: theme.typography.fontSizes.sm,
      color: theme.colors.textError,
      marginTop: theme.spacing[1],
    } as TextStyle,
  },
  
  // Layout utilities
  layout: {
    container: {
      flex: 1,
      backgroundColor: theme.colors.backgroundSecondary,
    } as ViewStyle,
    section: {
      paddingHorizontal: theme.spacing[4],
      paddingVertical: theme.spacing[6],
    } as ViewStyle,
    row: {
      flexDirection: 'row',
      alignItems: 'center',
    } as ViewStyle,
    spaceBetween: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    } as ViewStyle,
  },
});

// Create context
const ThemeContext = createContext<{
  theme: Theme;
  styles: ReturnType<typeof createStyles>;
}>({
  theme,
  styles: createStyles(theme),
});

// Theme provider component
export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const styles = createStyles(theme);

  return (
    <ThemeContext.Provider value={{ theme, styles }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook to use theme
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

// Export theme for direct usage
export { theme };