/**
 * Tailwind CSS Configuration with Design Tokens
 * This config uses the unified design tokens for consistency
 */

const designTokens = require('./design-tokens.json');

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app.py',
    './frontend/src/**/*.{js,jsx,ts,tsx}',
    './desktop_app/src/renderer/src/**/*.{js,jsx,ts,tsx}',
    './**/*.py', // For Streamlit components
  ],
  theme: {
    colors: {
      ...designTokens.colors,
      transparent: 'transparent',
      current: 'currentColor',
    },
    fontFamily: designTokens.typography.fontFamily,
    fontSize: designTokens.typography.fontSize,
    fontWeight: designTokens.typography.fontWeight,
    lineHeight: designTokens.typography.lineHeight,
    spacing: designTokens.spacing,
    borderRadius: designTokens.borderRadius,
    boxShadow: designTokens.boxShadow,
    screens: designTokens.breakpoints,
    zIndex: designTokens.zIndex,
    opacity: designTokens.opacity,
    extend: {
      animation: {
        'pulse-highlight': 'pulse-highlight 2s infinite',
        'fade-in': 'fade-in 300ms ease-out',
        'slide-up': 'slide-up 300ms ease-out',
      },
      keyframes: {
        'pulse-highlight': {
          '0%': { boxShadow: '0 0 0 0 rgba(255, 193, 7, 0.4)' },
          '50%': { boxShadow: '0 0 0 8px rgba(255, 193, 7, 0)' },
          '100%': { boxShadow: '0 0 0 0 rgba(255, 193, 7, 0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      transitionDuration: designTokens.animation.duration,
      transitionTimingFunction: designTokens.animation.easing,
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
};