/**
 * React Native Accessibility Provider
 * Comprehensive accessibility system for mobile app
 * WCAG 2.1 AA compliant with mobile-specific enhancements
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { AccessibilityInfo, Alert, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Haptics from 'expo-haptics';

// Types
interface AccessibilityPreferences {
  reduceMotion: boolean;
  highContrast: boolean;
  largeText: boolean;
  screenReader: boolean;
  voiceControl: boolean;
  hapticFeedback: boolean;
  audioDescriptions: boolean;
  boldText: boolean;
  reduceTransparency: boolean;
}

interface AccessibilityContextType {
  preferences: AccessibilityPreferences;
  updatePreference: (key: keyof AccessibilityPreferences, value: boolean) => void;
  announceToScreenReader: (message: string, priority?: 'low' | 'high') => void;
  triggerHaptic: (type: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error') => void;
  getAccessibleTextSize: (baseSize: number) => number;
  isScreenReaderEnabled: boolean;
  isVoiceControlEnabled: boolean;
  colorScheme: 'light' | 'dark' | 'high-contrast';
}

// Default preferences
const defaultPreferences: AccessibilityPreferences = {
  reduceMotion: false,
  highContrast: false,
  largeText: false,
  screenReader: false,
  voiceControl: false,
  hapticFeedback: true,
  audioDescriptions: false,
  boldText: false,
  reduceTransparency: false,
};

// Create context
const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

interface AccessibilityProviderProps {
  children: ReactNode;
}

export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({ children }) => {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(defaultPreferences);
  const [isScreenReaderEnabled, setIsScreenReaderEnabled] = useState(false);
  const [isVoiceControlEnabled, setIsVoiceControlEnabled] = useState(false);

  // Load preferences on mount
  useEffect(() => {
    loadPreferences();
    detectSystemAccessibilitySettings();
  }, []);

  // Listen to accessibility changes
  useEffect(() => {
    const screenReaderListener = AccessibilityInfo.addEventListener(
      'screenReaderChanged',
      setIsScreenReaderEnabled
    );

    // iOS specific listeners
    if (Platform.OS === 'ios') {
      const reduceMotionListener = AccessibilityInfo.addEventListener(
        'reduceMotionChanged',
        (enabled) => updatePreference('reduceMotion', enabled)
      );

      const reduceTransparencyListener = AccessibilityInfo.addEventListener(
        'reduceTransparencyChanged',
        (enabled) => updatePreference('reduceTransparency', enabled)
      );

      const boldTextListener = AccessibilityInfo.addEventListener(
        'boldTextChanged',
        (enabled) => updatePreference('boldText', enabled)
      );

      return () => {
        screenReaderListener.remove();
        reduceMotionListener.remove();
        reduceTransparencyListener.remove();
        boldTextListener.remove();
      };
    }

    return () => {
      screenReaderListener.remove();
    };
  }, []);

  const loadPreferences = async () => {
    try {
      const stored = await AsyncStorage.getItem('accessibility_preferences');
      if (stored) {
        const parsedPreferences = JSON.parse(stored);
        setPreferences({ ...defaultPreferences, ...parsedPreferences });
      }
    } catch (error) {
      console.error('Failed to load accessibility preferences:', error);
    }
  };

  const savePreferences = async (newPreferences: AccessibilityPreferences) => {
    try {
      await AsyncStorage.setItem('accessibility_preferences', JSON.stringify(newPreferences));
    } catch (error) {
      console.error('Failed to save accessibility preferences:', error);
    }
  };

  const detectSystemAccessibilitySettings = async () => {
    try {
      // Check system accessibility settings
      const screenReaderEnabled = await AccessibilityInfo.isScreenReaderEnabled();
      setIsScreenReaderEnabled(screenReaderEnabled);

      if (Platform.OS === 'ios') {
        const reduceMotion = await AccessibilityInfo.isReduceMotionEnabled();
        const reduceTransparency = await AccessibilityInfo.isReduceTransparencyEnabled();
        const boldText = await AccessibilityInfo.isBoldTextEnabled();

        setPreferences(prev => ({
          ...prev,
          reduceMotion,
          reduceTransparency,
          boldText,
          screenReader: screenReaderEnabled,
        }));
      }

      // Android specific checks
      if (Platform.OS === 'android') {
        // Android accessibility service detection would go here
        setPreferences(prev => ({
          ...prev,
          screenReader: screenReaderEnabled,
        }));
      }
    } catch (error) {
      console.error('Failed to detect system accessibility settings:', error);
    }
  };

  const updatePreference = useCallback(async (key: keyof AccessibilityPreferences, value: boolean) => {
    const newPreferences = { ...preferences, [key]: value };
    setPreferences(newPreferences);
    await savePreferences(newPreferences);

    // Announce change to screen reader
    announceToScreenReader(`${key.replace(/([A-Z])/g, ' $1').toLowerCase()} ${value ? 'enabled' : 'disabled'}`);
  }, [preferences]);

  const announceToScreenReader = useCallback((message: string, priority: 'low' | 'high' = 'low') => {
    if (isScreenReaderEnabled) {
      AccessibilityInfo.announceForAccessibility(message);
      
      // Add haptic feedback for important announcements
      if (priority === 'high' && preferences.hapticFeedback) {
        triggerHaptic('medium');
      }
    }
  }, [isScreenReaderEnabled, preferences.hapticFeedback]);

  const triggerHaptic = useCallback((type: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error') => {
    if (!preferences.hapticFeedback) return;

    try {
      switch (type) {
        case 'light':
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          break;
        case 'medium':
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          break;
        case 'heavy':
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
          break;
        case 'success':
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          break;
        case 'warning':
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
          break;
        case 'error':
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
          break;
      }
    } catch (error) {
      console.error('Failed to trigger haptic feedback:', error);
    }
  }, [preferences.hapticFeedback]);

  const getAccessibleTextSize = useCallback((baseSize: number): number => {
    let multiplier = 1;

    if (preferences.largeText) {
      multiplier *= 1.3;
    }

    if (preferences.boldText) {
      // Bold text doesn't increase size but improves readability
      multiplier *= 1.1;
    }

    // System font scaling (iOS and Android handle this automatically)
    return Math.round(baseSize * multiplier);
  }, [preferences.largeText, preferences.boldText]);

  const colorScheme = preferences.highContrast ? 'high-contrast' : 'light';

  const contextValue: AccessibilityContextType = {
    preferences,
    updatePreference,
    announceToScreenReader,
    triggerHaptic,
    getAccessibleTextSize,
    isScreenReaderEnabled,
    isVoiceControlEnabled,
    colorScheme,
  };

  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
    </AccessibilityContext.Provider>
  );
};

// Hook to use accessibility context
export const useAccessibility = (): AccessibilityContextType => {
  const context = useContext(AccessibilityContext);
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};

// Accessibility utilities for React Native components
export const AccessibilityUtils = {
  // Create accessible touchable props
  createAccessibleTouchableProps: (
    accessibilityLabel: string,
    accessibilityHint?: string,
    accessibilityRole: 'button' | 'link' | 'text' | 'image' | 'adjustable' = 'button',
    accessibilityStates?: string[]
  ) => ({
    accessible: true,
    accessibilityLabel,
    accessibilityHint,
    accessibilityRole,
    accessibilityStates: accessibilityStates || [],
  }),

  // Create accessible text props
  createAccessibleTextProps: (
    accessibilityLabel?: string,
    accessibilityRole: 'text' | 'header' | 'summary' = 'text'
  ) => ({
    accessible: true,
    accessibilityLabel,
    accessibilityRole,
  }),

  // Create accessible input props
  createAccessibleInputProps: (
    accessibilityLabel: string,
    accessibilityHint?: string,
    isRequired: boolean = false,
    hasError: boolean = false
  ) => ({
    accessible: true,
    accessibilityLabel: `${accessibilityLabel}${isRequired ? ', required' : ''}`,
    accessibilityHint,
    accessibilityStates: hasError ? ['disabled'] : undefined,
    accessibilityRole: 'search' as const,
  }),

  // Format accessibility announcements
  formatAnnouncement: (message: string, context?: string): string => {
    if (context) {
      return `${context}: ${message}`;
    }
    return message;
  },

  // Check if content should be animated
  shouldAnimate: (preferences: AccessibilityPreferences): boolean => {
    return !preferences.reduceMotion;
  },

  // Get accessible minimum touch target size
  getMinTouchTargetSize: (): number => {
    return 44; // 44pt minimum for both iOS and Android
  },
};

// High contrast color scheme
export const HighContrastColors = {
  background: '#FFFFFF',
  surface: '#F5F5F5',
  primary: '#000000',
  secondary: '#666666',
  text: '#000000',
  textSecondary: '#333333',
  border: '#000000',
  error: '#D32F2F',
  warning: '#F57C00',
  success: '#388E3C',
  info: '#1976D2',
};

// Accessible component wrappers
export const AccessibleText: React.FC<{
  children: ReactNode;
  style?: any;
  accessibilityLabel?: string;
  accessibilityRole?: 'text' | 'header' | 'summary';
  fontSize?: number;
}> = ({ children, style, accessibilityLabel, accessibilityRole = 'text', fontSize = 16 }) => {
  const { getAccessibleTextSize, preferences, colorScheme } = useAccessibility();
  
  const Text = require('react-native').Text;
  
  const accessibleStyle = {
    ...style,
    fontSize: getAccessibleTextSize(fontSize),
    fontWeight: preferences.boldText ? 'bold' : style?.fontWeight,
    color: colorScheme === 'high-contrast' ? HighContrastColors.text : style?.color,
  };

  return (
    <Text
      style={accessibleStyle}
      accessible={true}
      accessibilityLabel={accessibilityLabel}
      accessibilityRole={accessibilityRole}
    >
      {children}
    </Text>
  );
};

export const AccessibleTouchable: React.FC<{
  children: ReactNode;
  onPress: () => void;
  style?: any;
  accessibilityLabel: string;
  accessibilityHint?: string;
  accessibilityRole?: 'button' | 'link';
  disabled?: boolean;
}> = ({ 
  children, 
  onPress, 
  style, 
  accessibilityLabel, 
  accessibilityHint, 
  accessibilityRole = 'button',
  disabled = false
}) => {
  const { triggerHaptic, announceToScreenReader, colorScheme } = useAccessibility();
  
  const TouchableOpacity = require('react-native').TouchableOpacity;
  
  const handlePress = () => {
    if (disabled) return;
    
    triggerHaptic('light');
    announceToScreenReader(`${accessibilityLabel} activated`);
    onPress();
  };

  const accessibleStyle = {
    ...style,
    minHeight: AccessibilityUtils.getMinTouchTargetSize(),
    minWidth: AccessibilityUtils.getMinTouchTargetSize(),
    borderColor: colorScheme === 'high-contrast' ? HighContrastColors.border : style?.borderColor,
    backgroundColor: colorScheme === 'high-contrast' ? HighContrastColors.surface : style?.backgroundColor,
  };

  return (
    <TouchableOpacity
      style={accessibleStyle}
      onPress={handlePress}
      disabled={disabled}
      accessible={true}
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      accessibilityRole={accessibilityRole}
      accessibilityStates={disabled ? ['disabled'] : []}
    >
      {children}
    </TouchableOpacity>
  );
};

export default AccessibilityProvider;