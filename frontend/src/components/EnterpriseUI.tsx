// Enterprise Design System for React Frontend
// Professional UI components with modern aesthetics

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styled, { createGlobalStyle, ThemeProvider } from 'styled-components';

// Enterprise Color System
export const lightTheme = {
  // Primary Palette
  primary: '#1E40AF',
  primaryHover: '#1E3A8A',
  primaryLight: '#DBEAFE',
  primaryDark: '#1E293B',
  
  // Secondary Palette
  secondary: '#7C3AED',
  secondaryHover: '#6D28D9',
  secondaryLight: '#EDE9FE',
  
  // Accent Colors
  accent: '#10B981',
  accentHover: '#059669',
  accentLight: '#D1FAE5',
  
  // Status Colors
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  
  // Neutral Colors
  background: '#FFFFFF',
  surface: '#F9FAFB',
  card: '#FFFFFF',
  border: '#E5E7EB',
  divider: '#E5E7EB',
  
  // Text Colors
  textPrimary: '#111827',
  textSecondary: '#6B7280',
  textMuted: '#9CA3AF',
  textInverse: '#FFFFFF',
  
  // Gradients
  gradientPrimary: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
  gradientSecondary: 'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)',
  gradientAccent: 'linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%)',
  gradientDark: 'linear-gradient(135deg, #1E3A8A 0%, #312E81 100%)',
  
  // Shadows
  shadowSm: '0 1px 2px rgba(0, 0, 0, 0.05)',
  shadowMd: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  shadowLg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  shadowXl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  shadow2xl: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  shadowInner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  shadowNone: 'none',
  
  // Spacing
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
    '4xl': '80px',
    '5xl': '96px',
    '6xl': '128px'
  },
  
  // Typography
  fontSize: {
    xs: '12px',
    sm: '14px',
    base: '16px',
    lg: '18px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '30px',
    '4xl': '36px',
    '5xl': '48px',
    '6xl': '64px'
  },
  
  // Border Radius
  borderRadius: {
    none: '0',
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    '2xl': '24px',
    '3xl': '32px',
    full: '9999px'
  },
  
  // Breakpoints
  breakpoints: {
    xs: '320px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px'
  },
  
  // Animation
  transition: {
    fast: '0.15s ease',
    base: '0.3s ease',
    slow: '0.5s ease',
    slower: '0.8s ease'
  },
  
  // Z-index
  zIndex: {
    hide: -1,
    auto: 0,
    base: 1,
    docked: 10,
    dropdown: 1000,
    sticky: 1100,
    banner: 1200,
    overlay: 1300,
    modal: 1400,
    popover: 1500,
    skipLink: 1600,
    toast: 1700,
    tooltip: 1800
  }
};

export const darkTheme = {
  // Primary Palette
  primary: '#3B82F6',
  primaryHover: '#2563EB',
  primaryLight: '#1E3A8A',
  primaryDark: '#1E40AF',
  
  // Secondary Palette
  secondary: '#8B5CF6',
  secondaryHover: '#7C3AED',
  secondaryLight: '#312E81',
  
  // Accent Colors
  accent: '#10B981',
  accentHover: '#059669',
  accentLight: '#064E3B',
  
  // Status Colors
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  
  // Neutral Colors
  background: '#0F172A',
  surface: '#1E293B',
  card: '#1E293B',
  border: '#334155',
  divider: '#334155',
  
  // Text Colors
  textPrimary: '#F9FAFB',
  textSecondary: '#CBD5E1',
  textMuted: '#94A3B8',
  textInverse: '#111827',
  
  // Gradients (same as light)
  gradientPrimary: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
  gradientSecondary: 'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)',
  gradientAccent: 'linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%)',
  gradientDark: 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)',
  
  // Shadows (adjusted for dark mode)
  shadowSm: '0 1px 2px rgba(0, 0, 0, 0.2)',
  shadowMd: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
  shadowLg: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
  shadowXl: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
  shadow2xl: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
  shadowInner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.2)',
  shadowNone: 'none',
  
  // Spacing
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
    '4xl': '80px',
    '5xl': '96px',
    '6xl': '128px'
  },
  
  // Typography
  fontSize: {
    xs: '12px',
    sm: '14px',
    base: '16px',
    lg: '18px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '30px',
    '4xl': '36px',
    '5xl': '48px',
    '6xl': '64px'
  },
  
  // Border Radius
  borderRadius: {
    none: '0',
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    '2xl': '24px',
    '3xl': '32px',
    full: '9999px'
  },
  
  // Breakpoints
  breakpoints: {
    xs: '320px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px'
  },
  
  // Animation
  transition: {
    fast: '0.15s ease',
    base: '0.3s ease',
    slow: '0.5s ease',
    slower: '0.8s ease'
  },
  
  // Z-index
  zIndex: {
    hide: -1,
    auto: 0,
    base: 1,
    docked: 10,
    dropdown: 1000,
    sticky: 1100,
    banner: 1200,
    overlay: 1300,
    modal: 1400,
    popover: 1500,
    skipLink: 1600,
    toast: 1700,
    tooltip: 1800
  }
};

// Component prop interfaces
interface CardProps {
  padding?: string;
  elevated?: boolean;
  hoverable?: boolean;
}

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'accent' | 'gradient' | 'ghost' | 'outline';
  size?: 'small' | 'medium' | 'large';
  rounded?: boolean;
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
}

interface InputProps {
  variant?: 'primary' | 'secondary' | 'error';
  size?: 'small' | 'medium' | 'large';
  rounded?: boolean;
}

interface BadgeProps {
  status?: 'success' | 'warning' | 'error' | 'info' | 'online' | 'offline' | 'busy' | 'away';
  size?: 'small' | 'medium' | 'large';
  rounded?: boolean;
}

interface ProgressProps {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'small' | 'medium' | 'large';
}

interface ModalProps {
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
}

interface TooltipProps {
  placement?: 'top' | 'bottom' | 'left' | 'right';
}

interface DividerProps {
  orientation?: 'horizontal' | 'vertical';
  variant?: 'solid' | 'dashed' | 'dotted';
}

// Global Styles
export const GlobalStyle = createGlobalStyle`
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
  
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: ${props => props.theme.background};
    color: ${props => props.theme.textPrimary};
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  
  h1, h2, h3, h4, h5, h6 {
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.2;
  }
  
  /* Custom Scrollbar */
  ::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }
  
  ::-webkit-scrollbar-track {
    background: ${props => props.theme.surface};
    border-radius: 10px;
  }
  
  ::-webkit-scrollbar-thumb {
    background: ${props => props.theme.border};
    border-radius: 10px;
    
    &:hover {
      background: ${props => props.theme.textMuted};
    }
  }
`;

// Professional Card Component
export const Card = styled(motion.div)<CardProps>`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 16px;
  padding: ${props => props.padding || '24px'};
  box-shadow: ${props => props.elevated ? props.theme.shadowLg : props.theme.shadowMd};
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    ${props => props.hoverable && `
      transform: translateY(-4px);
      box-shadow: ${props.theme.shadowXl};
    `}
  }
`;

// Glass Morphism Card
export const GlassCard = styled(Card)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

// Premium Button Component
export const Button = styled(motion.button)<ButtonProps>`
  background: ${props => {
    switch(props.variant) {
      case 'secondary': return props.theme.secondary;
      case 'accent': return props.theme.accent;
      case 'gradient': return props.theme.gradientPrimary;
      case 'ghost': return 'transparent';
      case 'outline': return 'transparent';
      default: return props.theme.primary;
    }
  }};
  
  color: ${props => props.variant === 'ghost' || props.variant === 'outline' 
    ? props.theme.primary 
    : props.theme.textInverse};
  
  border: ${props => props.variant === 'outline' 
    ? `2px solid ${props.theme.primary}` 
    : 'none'};
  
  border-radius: ${props => props.rounded ? '9999px' : '12px'};
  padding: ${props => props.size === 'large' ? '16px 32px' : props.size === 'small' ? '8px 16px' : '12px 24px'};
  font-weight: 600;
  font-size: ${props => props.size === 'large' ? '16px' : '14px'};
  letter-spacing: 0.025em;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: ${props => props.variant !== 'ghost' && props.variant !== 'outline' 
    ? props.theme.shadowMd 
    : 'none'};
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: ${props => props.fullWidth ? '100%' : 'auto'};
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s ease;
  }
  
  &:hover::before {
    left: 100%;
  }
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: ${props => props.variant !== 'ghost' && props.variant !== 'outline' 
      ? props.theme.shadowLg 
      : 'none'};
    
    ${props => props.variant === 'ghost' && `
      background: ${props.theme.surface};
    `}
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// Status Badge Component
export const Badge = styled.span<BadgeProps>`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  
  background: ${props => {
    switch(props.status) {
      case 'success': return props.theme.accentLight;
      case 'warning': return '#FEF3C7';
      case 'error': return '#FEE2E2';
      case 'info': return props.theme.primaryLight;
      default: return props.theme.surface;
    }
  }};
  
  color: ${props => {
    switch(props.status) {
      case 'success': return props.theme.accent;
      case 'warning': return props.theme.warning;
      case 'error': return props.theme.error;
      case 'info': return props.theme.primary;
      default: return props.theme.textSecondary;
    }
  }};
`;

// Input Field Component
export const Input = styled.input<InputProps>`
  background: ${props => props.theme.background};
  border: 2px solid ${props => props.theme.border};
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  font-family: inherit;
  color: ${props => props.theme.textPrimary};
  transition: all 0.2s ease;
  width: 100%;
  
  &::placeholder {
    color: ${props => props.theme.textMuted};
  }
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.primary};
    box-shadow: 0 0 0 3px ${props => props.theme.primaryLight};
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// Progress Ring Component
interface ProgressRingProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
}

export const ProgressRing: React.FC<ProgressRingProps> = ({ percentage, size = 120, strokeWidth = 8 }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke="#E5E7EB"
        strokeWidth={strokeWidth}
        fill="none"
      />
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke="url(#gradient)"
        strokeWidth={strokeWidth}
        fill="none"
        strokeDasharray={circumference}
        initial={{ strokeDashoffset: circumference }}
        animate={{ strokeDashoffset }}
        transition={{ duration: 1, ease: "easeOut" }}
        strokeLinecap="round"
      />
      <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#667EEA" />
          <stop offset="100%" stopColor="#764BA2" />
        </linearGradient>
      </defs>
    </svg>
  );
};

// Animated Metric Card
interface MetricCardProps {
  title: string;
  value: string | number;
  change: string | number;
  icon: React.ReactNode;
  color?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon, color = 'primary' }) => {
  // Note: useTheme would need to be imported from styled-components
  // For now, using lightTheme as fallback
  const theme = lightTheme;
  
  return (
    <Card
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      hoverable
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div style={{
          width: '48px',
          height: '48px',
          background: color === 'primary' ? theme.primaryLight : 
                     color === 'secondary' ? theme.secondaryLight : 
                     color === 'accent' ? theme.accentLight : theme.primaryLight,
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '24px'
        }}>
          {icon}
        </div>
        {change && (
          <Badge status={typeof change === 'string' && change.startsWith('+') ? 'success' : 'error'}>
            {change}
          </Badge>
        )}
      </div>
      <div style={{ color: theme.textSecondary, fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
        {title}
      </div>
      <div style={{ color: theme.textPrimary, fontSize: '32px', fontWeight: '700', letterSpacing: '-0.02em' }}>
        {value}
      </div>
    </Card>
  );
};

// Loading Skeleton
interface SkeletonProps {
  rounded?: string;
  height?: string;
  width?: string;
}

export const Skeleton = styled.div<SkeletonProps>`
  background: linear-gradient(
    90deg,
    ${props => props.theme.surface} 25%,
    ${props => props.theme.border} 50%,
    ${props => props.theme.surface} 75%
  );
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: ${props => props.rounded ? props.rounded : '8px'};
  height: ${props => props.height || '20px'};
  width: ${props => props.width || '100%'};
  
  @keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
`;

// Tabs Component
export const TabContainer = styled.div`
  display: flex;
  gap: 8px;
  padding: 4px;
  background: ${props => props.theme.surface};
  border-radius: 12px;
  margin-bottom: 24px;
`;

export const Tab = styled.button<{ active?: boolean }>`
  flex: 1;
  padding: 12px 24px;
  background: ${props => props.active ? props.theme.background : 'transparent'};
  border: none;
  border-radius: 8px;
  font-weight: 600;
  color: ${props => props.active ? props.theme.primary : props.theme.textSecondary};
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: ${props => props.active ? props.theme.shadowSm : 'none'};
  
  &:hover:not(:disabled) {
    background: ${props => !props.active && props.theme.background};
    opacity: ${props => !props.active && '0.7'};
  }
`;

// Modern Table Component
export const Table = styled.table`
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
`;

export const TableHeader = styled.thead`
  background: ${props => props.theme.surface};
  
  th {
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: ${props => props.theme.textSecondary};
    border-bottom: 2px solid ${props => props.theme.border};
  }
`;

export const TableBody = styled.tbody`
  tr {
    transition: background 0.2s ease;
    
    &:hover {
      background: ${props => props.theme.surface};
    }
  }
  
  td {
    padding: 16px;
    border-bottom: 1px solid ${props => props.theme.border};
    color: ${props => props.theme.textPrimary};
  }
`;

// Floating Action Button
export const FAB = styled(motion.button)<ButtonProps>`
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 28px;
  background: ${props => props.theme.gradientPrimary};
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: ${props => props.theme.shadowLg};
  border: none;
  cursor: pointer;
  z-index: 1000;
  
  &:hover {
    transform: scale(1.1);
    box-shadow: ${props => props.theme.shadowXl};
  }
`;

// Timeline Component
interface TimelineItemProps {
  title: string;
  description: string;
  time: string;
  status: 'completed' | 'in_progress' | 'pending';
  icon: React.ReactNode;
  isLast: boolean;
}

export const TimelineItem: React.FC<TimelineItemProps> = ({ title, description, time, status, icon, isLast }) => {
  // Using lightTheme as fallback
  const theme = lightTheme;
  const statusColors = {
    completed: theme.success,
    in_progress: theme.warning,
    pending: theme.textMuted
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '32px' }}
    >
      <div style={{ position: 'relative' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: status === 'completed' ? theme.gradientPrimary : theme.surface,
          border: `3px solid ${statusColors[status]}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: status === 'completed' ? 'white' : statusColors[status],
          fontWeight: '700'
        }}>
          {icon || (status === 'completed' ? '✓' : '')}
        </div>
        {!isLast && (
          <div style={{
            position: 'absolute',
            top: '40px',
            left: '19px',
            width: '2px',
            height: '60px',
            background: theme.border
          }} />
        )}
      </div>
      <div style={{ marginLeft: '20px', flex: 1 }}>
        <div style={{ fontWeight: '600', color: theme.textPrimary, marginBottom: '4px' }}>
          {title}
        </div>
        <div style={{ fontSize: '14px', color: theme.textSecondary, marginBottom: '4px' }}>
          {description}
        </div>
        <div style={{ fontSize: '12px', color: theme.textMuted }}>
          {time}
        </div>
      </div>
    </motion.div>
  );
};

// Export hook for theme usage
import { useTheme } from 'styled-components';
export { useTheme };

// Export all components
export default {
  lightTheme,
  darkTheme,
  GlobalStyle,
  Card,
  GlassCard,
  Button,
  Badge,
  Input,
  ProgressRing,
  MetricCard,
  Skeleton,
  TabContainer,
  Tab,
  Table,
  TableHeader,
  TableBody,
  FAB,
  TimelineItem
};
