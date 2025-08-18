import 'styled-components';

declare module 'styled-components' {
  export interface DefaultTheme {
    // Primary Palette
    primary: string;
    primaryHover: string;
    primaryLight: string;
    primaryDark: string;
    
    // Secondary Palette
    secondary: string;
    secondaryHover: string;
    secondaryLight: string;
    
    // Accent Colors
    accent: string;
    accentHover: string;
    accentLight: string;
    
    // Status Colors
    success: string;
    warning: string;
    error: string;
    info: string;
    
    // Neutral Colors
    background: string;
    surface: string;
    card: string;
    border: string;
    divider: string;
    
    // Text Colors
    textPrimary: string;
    textSecondary: string;
    textMuted: string;
    textInverse: string;
    
    // Gradients
    gradientPrimary: string;
    gradientSecondary: string;
    gradientAccent: string;
    gradientDark: string;
    
    // Shadows
    shadowSm: string;
    shadowMd: string;
    shadowLg: string;
    shadowXl: string;
    shadow2xl: string;
    shadowInner: string;
    shadowNone: string;
    
    // Spacing
    spacing: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
      '4xl': string;
      '5xl': string;
      '6xl': string;
    };
    
    // Typography
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
      '4xl': string;
      '5xl': string;
      '6xl': string;
    };
    
    // Border Radius
    borderRadius: {
      none: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
      full: string;
    };
    
    // Breakpoints
    breakpoints: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
      '2xl': string;
    };
    
    // Animation
    transition: {
      fast: string;
      base: string;
      slow: string;
      slower: string;
    };
    
    // Z-index
    zIndex: {
      hide: number;
      auto: number;
      base: number;
      docked: number;
      dropdown: number;
      sticky: number;
      banner: number;
      overlay: number;
      modal: number;
      popover: number;
      skipLink: number;
      toast: number;
      tooltip: number;
    };
  }
}