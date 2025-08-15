/**
 * Comprehensive Accessibility System
 * WCAG 2.1 AA compliant accessibility utilities and hooks
 * Built upon existing design-system-accessibility.json configuration
 */

import { useEffect, useRef, useState, useCallback } from 'react';

// Load accessibility configuration
import accessibilityConfig from '../../design-system-accessibility.json';

// Types
interface AccessibilityPreferences {
  reducedMotion: boolean;
  highContrast: boolean;
  largeText: boolean;
  screenReader: boolean;
  keyboardOnly: boolean;
}

interface FocusManagement {
  trapFocus: (element: HTMLElement) => () => void;
  restoreFocus: (element?: HTMLElement) => void;
  moveFocus: (direction: 'next' | 'previous' | 'first' | 'last') => void;
}

interface ScreenReaderAnnouncements {
  announceToScreenReader: (message: string, priority?: 'polite' | 'assertive') => void;
  setLiveRegion: (message: string, level?: 'polite' | 'assertive' | 'off') => void;
}

interface KeyboardNavigation {
  handleKeyboardNavigation: (event: KeyboardEvent, handlers: KeyboardHandlers) => void;
  useKeyboardShortcuts: (shortcuts: KeyboardShortcuts) => void;
}

interface KeyboardHandlers {
  onEnter?: () => void;
  onSpace?: () => void;
  onEscape?: () => void;
  onArrowUp?: () => void;
  onArrowDown?: () => void;
  onArrowLeft?: () => void;
  onArrowRight?: () => void;
  onHome?: () => void;
  onEnd?: () => void;
  onPageUp?: () => void;
  onPageDown?: () => void;
}

interface KeyboardShortcuts {
  [key: string]: () => void;
}

interface ColorContrastUtils {
  checkContrast: (foreground: string, background: string) => { ratio: number; passes: boolean };
  getAccessibleColor: (baseColor: string, backgroundColor: string) => string;
}

// Accessibility Preferences Management
class AccessibilityPreferencesManager {
  private preferences: AccessibilityPreferences;
  private listeners: Set<(prefs: AccessibilityPreferences) => void> = new Set();

  constructor() {
    this.preferences = this.detectPreferences();
    this.setupMediaQueryListeners();
  }

  private detectPreferences(): AccessibilityPreferences {
    return {
      reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      highContrast: window.matchMedia('(prefers-contrast: high)').matches,
      largeText: window.matchMedia('(prefers-reduced-data: reduce)').matches,
      screenReader: this.detectScreenReader(),
      keyboardOnly: false // Will be detected on first keyboard interaction
    };
  }

  private detectScreenReader(): boolean {
    // Common screen reader detection methods
    return !!(
      navigator.userAgent.match(/NVDA|JAWS|VoiceOver|TalkBack|Dragon/i) ||
      window.speechSynthesis ||
      document.body.getAttribute('aria-hidden') ||
      (window as any).speechSynthesis
    );
  }

  private setupMediaQueryListeners(): void {
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)');

    reducedMotionQuery.addListener((e) => {
      this.updatePreference('reducedMotion', e.matches);
    });

    highContrastQuery.addListener((e) => {
      this.updatePreference('highContrast', e.matches);
    });

    // Detect keyboard-only navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        this.updatePreference('keyboardOnly', true);
      }
    });

    document.addEventListener('mousedown', () => {
      this.updatePreference('keyboardOnly', false);
    });
  }

  private updatePreference<K extends keyof AccessibilityPreferences>(
    key: K,
    value: AccessibilityPreferences[K]
  ): void {
    if (this.preferences[key] !== value) {
      this.preferences[key] = value;
      this.notifyListeners();
    }
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.preferences));
  }

  public getPreferences(): AccessibilityPreferences {
    return { ...this.preferences };
  }

  public subscribe(listener: (prefs: AccessibilityPreferences) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  public setPreference<K extends keyof AccessibilityPreferences>(
    key: K,
    value: AccessibilityPreferences[K]
  ): void {
    this.updatePreference(key, value);
  }
}

// Global accessibility manager instance
const accessibilityManager = new AccessibilityPreferencesManager();

// Screen Reader Utilities
class ScreenReaderManager {
  private liveRegion: HTMLElement | null = null;
  private announcements: string[] = [];

  constructor() {
    this.createLiveRegion();
  }

  private createLiveRegion(): void {
    if (this.liveRegion) return;

    this.liveRegion = document.createElement('div');
    this.liveRegion.setAttribute('aria-live', 'polite');
    this.liveRegion.setAttribute('aria-atomic', 'true');
    this.liveRegion.className = 'sr-only';
    this.liveRegion.style.cssText = `
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    `;

    document.body.appendChild(this.liveRegion);
  }

  public announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
    if (!this.liveRegion || !message.trim()) return;

    this.liveRegion.setAttribute('aria-live', priority);
    
    // Clear and set new message to ensure it's announced
    this.liveRegion.textContent = '';
    setTimeout(() => {
      if (this.liveRegion) {
        this.liveRegion.textContent = message;
      }
    }, 100);

    // Keep history for debugging
    this.announcements.push(`[${new Date().toISOString()}] ${priority}: ${message}`);
    if (this.announcements.length > 50) {
      this.announcements = this.announcements.slice(-25);
    }
  }

  public setLiveRegion(message: string, level: 'polite' | 'assertive' | 'off' = 'polite'): void {
    if (!this.liveRegion) return;

    this.liveRegion.setAttribute('aria-live', level);
    this.liveRegion.textContent = message;
  }

  public getAnnouncementHistory(): string[] {
    return [...this.announcements];
  }
}

const screenReaderManager = new ScreenReaderManager();

// Focus Management Utilities
class FocusManager {
  private focusStack: HTMLElement[] = [];
  private focusableSelectors = [
    'button:not([disabled])',
    '[href]',
    'input:not([disabled]):not([type="hidden"])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]'
  ].join(', ');

  public trapFocus(container: HTMLElement): () => void {
    const focusableElements = this.getFocusableElements(container);
    if (focusableElements.length === 0) return () => {};

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Store currently focused element
    const previouslyFocused = document.activeElement as HTMLElement;
    this.focusStack.push(previouslyFocused);

    // Focus first element
    firstElement.focus();

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);

    return () => {
      container.removeEventListener('keydown', handleTabKey);
      this.restoreFocus();
    };
  }

  public restoreFocus(element?: HTMLElement): void {
    const focusTarget = element || this.focusStack.pop();
    if (focusTarget && typeof focusTarget.focus === 'function') {
      focusTarget.focus();
    }
  }

  public moveFocus(direction: 'next' | 'previous' | 'first' | 'last'): void {
    const focusableElements = this.getFocusableElements(document.body);
    const currentIndex = focusableElements.findIndex(el => el === document.activeElement);

    let targetIndex: number;
    switch (direction) {
      case 'next':
        targetIndex = (currentIndex + 1) % focusableElements.length;
        break;
      case 'previous':
        targetIndex = currentIndex <= 0 ? focusableElements.length - 1 : currentIndex - 1;
        break;
      case 'first':
        targetIndex = 0;
        break;
      case 'last':
        targetIndex = focusableElements.length - 1;
        break;
    }

    focusableElements[targetIndex]?.focus();
  }

  private getFocusableElements(container: Element): HTMLElement[] {
    return Array.from(container.querySelectorAll(this.focusableSelectors))
      .filter((el): el is HTMLElement => {
        const element = el as HTMLElement;
        return !element.hidden && 
               element.offsetParent !== null && 
               !element.getAttribute('aria-hidden');
      });
  }
}

const focusManager = new FocusManager();

// Color Contrast Utilities
class ColorContrastChecker {
  private hexToRgb(hex: string): [number, number, number] | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
      parseInt(result[1], 16),
      parseInt(result[2], 16),
      parseInt(result[3], 16)
    ] : null;
  }

  private getLuminance(r: number, g: number, b: number): number {
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  }

  public checkContrast(foreground: string, background: string): { ratio: number; passes: boolean } {
    const fgRgb = this.hexToRgb(foreground);
    const bgRgb = this.hexToRgb(background);

    if (!fgRgb || !bgRgb) {
      return { ratio: 0, passes: false };
    }

    const fgLuminance = this.getLuminance(...fgRgb);
    const bgLuminance = this.getLuminance(...bgRgb);

    const ratio = (Math.max(fgLuminance, bgLuminance) + 0.05) / 
                  (Math.min(fgLuminance, bgLuminance) + 0.05);

    const passes = ratio >= accessibilityConfig.wcag.guidelines.colorContrast.normal;

    return { ratio, passes };
  }

  public getAccessibleColor(baseColor: string, backgroundColor: string): string {
    const contrast = this.checkContrast(baseColor, backgroundColor);
    if (contrast.passes) return baseColor;

    // Simple darkening/lightening algorithm
    const baseRgb = this.hexToRgb(baseColor);
    if (!baseRgb) return baseColor;

    const [r, g, b] = baseRgb;
    const isDark = (r + g + b) / 3 < 128;

    // Adjust color to meet contrast requirements
    const adjustment = isDark ? 50 : -50;
    const newR = Math.max(0, Math.min(255, r + adjustment));
    const newG = Math.max(0, Math.min(255, g + adjustment));
    const newB = Math.max(0, Math.min(255, b + adjustment));

    return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`;
  }
}

const colorContrastChecker = new ColorContrastChecker();

// React Hooks

export const useAccessibility = (): ScreenReaderAnnouncements => {
  return {
    announceToScreenReader: screenReaderManager.announce.bind(screenReaderManager),
    setLiveRegion: screenReaderManager.setLiveRegion.bind(screenReaderManager)
  };
};

export const useAccessibilityPreferences = (): AccessibilityPreferences => {
  const [preferences, setPreferences] = useState(accessibilityManager.getPreferences());

  useEffect(() => {
    return accessibilityManager.subscribe(setPreferences);
  }, []);

  return preferences;
};

export const useFocusManagement = (): FocusManagement => {
  return {
    trapFocus: focusManager.trapFocus.bind(focusManager),
    restoreFocus: focusManager.restoreFocus.bind(focusManager),
    moveFocus: focusManager.moveFocus.bind(focusManager)
  };
};

export const useKeyboardNavigation = (): KeyboardNavigation => {
  const handleKeyboardNavigation = useCallback((event: KeyboardEvent, handlers: KeyboardHandlers) => {
    const { key, shiftKey, ctrlKey, metaKey } = event;

    // Prevent handling if modifier keys are pressed (except Shift for Tab)
    if ((ctrlKey || metaKey) && key !== 'Tab') return;

    switch (key) {
      case 'Enter':
        handlers.onEnter?.();
        break;
      case ' ':
        handlers.onSpace?.();
        event.preventDefault(); // Prevent page scroll
        break;
      case 'Escape':
        handlers.onEscape?.();
        break;
      case 'ArrowUp':
        handlers.onArrowUp?.();
        event.preventDefault();
        break;
      case 'ArrowDown':
        handlers.onArrowDown?.();
        event.preventDefault();
        break;
      case 'ArrowLeft':
        handlers.onArrowLeft?.();
        event.preventDefault();
        break;
      case 'ArrowRight':
        handlers.onArrowRight?.();
        event.preventDefault();
        break;
      case 'Home':
        handlers.onHome?.();
        event.preventDefault();
        break;
      case 'End':
        handlers.onEnd?.();
        event.preventDefault();
        break;
      case 'PageUp':
        handlers.onPageUp?.();
        event.preventDefault();
        break;
      case 'PageDown':
        handlers.onPageDown?.();
        event.preventDefault();
        break;
    }
  }, []);

  const useKeyboardShortcuts = useCallback((shortcuts: KeyboardShortcuts) => {
    useEffect(() => {
      const handleKeyDown = (event: KeyboardEvent) => {
        const key = `${event.ctrlKey ? 'Ctrl+' : ''}${event.shiftKey ? 'Shift+' : ''}${event.altKey ? 'Alt+' : ''}${event.key}`;
        const handler = shortcuts[key];
        
        if (handler) {
          event.preventDefault();
          handler();
        }
      };

      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }, [shortcuts]);
  }, []);

  return { handleKeyboardNavigation, useKeyboardShortcuts };
};

export const useColorContrast = (): ColorContrastUtils => {
  return {
    checkContrast: colorContrastChecker.checkContrast.bind(colorContrastChecker),
    getAccessibleColor: colorContrastChecker.getAccessibleColor.bind(colorContrastChecker)
  };
};

// Skip Link Component Hook
export const useSkipLinks = () => {
  const addSkipLink = useCallback((targetId: string, label?: string) => {
    const existingSkipLink = document.getElementById(`skip-link-${targetId}`);
    if (existingSkipLink) return;

    const skipLink = document.createElement('a');
    skipLink.id = `skip-link-${targetId}`;
    skipLink.href = `#${targetId}`;
    skipLink.textContent = label || `Skip to ${targetId.replace('-', ' ')}`;
    skipLink.className = 'skip-link';
    
    // Style the skip link
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 6px;
      z-index: 1000;
      background: ${accessibilityConfig.keyboard.focusIndicator.color};
      color: white;
      padding: 8px;
      text-decoration: none;
      border-radius: 4px;
      transition: top 0.3s ease;
    `;

    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '6px';
    });

    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px';
    });

    document.body.insertBefore(skipLink, document.body.firstChild);
  }, []);

  return { addSkipLink };
};

// Accessible Form Validation Hook
export const useAccessibleForm = () => {
  const validateField = useCallback((
    element: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement,
    validationRules: {
      required?: boolean;
      minLength?: number;
      maxLength?: number;
      pattern?: RegExp;
      custom?: (value: string) => string | null;
    }
  ): string | null => {
    const { value } = element;
    const { required, minLength, maxLength, pattern, custom } = validationRules;

    if (required && !value.trim()) {
      return 'This field is required';
    }

    if (minLength && value.length < minLength) {
      return `Must be at least ${minLength} characters`;
    }

    if (maxLength && value.length > maxLength) {
      return `Must be no more than ${maxLength} characters`;
    }

    if (pattern && !pattern.test(value)) {
      return 'Please enter a valid value';
    }

    if (custom) {
      return custom(value);
    }

    return null;
  }, []);

  const setFieldError = useCallback((element: HTMLElement, error: string | null) => {
    const errorId = `${element.id}-error`;
    let errorElement = document.getElementById(errorId);

    if (error) {
      element.setAttribute('aria-invalid', 'true');
      element.setAttribute('aria-describedby', errorId);

      if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.id = errorId;
        errorElement.className = 'field-error';
        errorElement.style.cssText = `
          color: #dc2626;
          font-size: 0.875rem;
          margin-top: 0.25rem;
        `;
        element.parentNode?.insertBefore(errorElement, element.nextSibling);
      }

      errorElement.textContent = error;
      errorElement.setAttribute('role', 'alert');
    } else {
      element.removeAttribute('aria-invalid');
      element.removeAttribute('aria-describedby');
      errorElement?.remove();
    }
  }, []);

  return { validateField, setFieldError };
};

// Accessibility Testing Utilities
export const accessibilityTestUtils = {
  checkPageAccessibility: (): Promise<any[]> => {
    // In a real implementation, this would integrate with axe-core
    return Promise.resolve([]);
  },

  getAccessibilityReport: (): {
    violations: number;
    warnings: number;
    passes: number;
    recommendations: string[];
  } => {
    return {
      violations: 0,
      warnings: 0,
      passes: 0,
      recommendations: []
    };
  },

  logAccessibilityEvents: (enabled: boolean = false) => {
    if (!enabled) return;

    const events = ['focus', 'blur', 'keydown', 'click'];
    events.forEach(event => {
      document.addEventListener(event, (e) => {
        console.log(`[A11Y] ${event}:`, e.target);
      }, true);
    });
  }
};

// Export accessibility configuration
export { accessibilityConfig };

// Export global managers for advanced usage
export { 
  accessibilityManager, 
  screenReaderManager, 
  focusManager, 
  colorContrastChecker 
};