/**
 * Design Tokens Type Definitions
 * Provides TypeScript types for design tokens
 */

export interface ColorScale {
  50: string;
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;
  600: string;
  700: string;
  800: string;
  900: string;
  DEFAULT: string;
}

export interface TextColors {
  primary: string;
  secondary: string;
  tertiary: string;
  inverse: string;
  error: string;
  success: string;
}

export interface BackgroundColors {
  primary: string;
  secondary: string;
  tertiary: string;
  inverse: string;
  overlay: string;
}

export interface BorderColors {
  light: string;
  DEFAULT: string;
  dark: string;
}

export interface InteractiveColors {
  hover: string;
  active: string;
  focus: string;
  disabled: string;
}

export interface AudioColors {
  waveform: string;
  progress: string;
  buffered: string;
  currentTime: string;
}

export interface TranscriptColors {
  highlight: string;
  selected: string;
  current: string;
  edited: string;
  speakerColors: string[];
}

export interface Colors {
  primary: ColorScale;
  secondary: ColorScale;
  success: ColorScale;
  warning: ColorScale;
  error: ColorScale;
  gray: ColorScale;
  text: TextColors;
  background: BackgroundColors;
  border: BorderColors;
  interactive: InteractiveColors;
  audio: AudioColors;
  transcript: TranscriptColors;
}

export interface Typography {
  fontFamily: {
    sans: string;
    serif: string;
    mono: string;
  };
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
  };
  fontWeight: {
    thin: string;
    light: string;
    normal: string;
    medium: string;
    semibold: string;
    bold: string;
    extrabold: string;
    black: string;
  };
  lineHeight: {
    tight: string;
    snug: string;
    normal: string;
    relaxed: string;
    loose: string;
  };
}

export interface ButtonSize {
  height: string;
  paddingX: string;
  fontSize: string;
}

export interface Sizing {
  icon: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  button: {
    sm: ButtonSize;
    md: ButtonSize;
    lg: ButtonSize;
  };
  input: {
    sm: ButtonSize;
    md: ButtonSize;
    lg: ButtonSize;
  };
}

export interface Animation {
  duration: {
    fast: string;
    normal: string;
    slow: string;
  };
  easing: {
    linear: string;
    in: string;
    out: string;
    inOut: string;
  };
}

export interface DesignTokens {
  colors: Colors;
  typography: Typography;
  spacing: Record<string, string>;
  sizing: Sizing;
  borderRadius: Record<string, string>;
  boxShadow: Record<string, string>;
  animation: Animation;
  breakpoints: Record<string, string>;
  zIndex: Record<string, string>;
  opacity: Record<string, string>;
}

declare const designTokens: DesignTokens;
export default designTokens;