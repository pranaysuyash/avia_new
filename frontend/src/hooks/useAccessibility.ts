import { useEffect, useState, useCallback } from 'react';

interface AccessibilitySettings {
  reducedMotion: boolean;
  highContrast: boolean;
  largeText: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
}

export const useAccessibility = () => {
  const [settings, setSettings] = useState<AccessibilitySettings>({
    reducedMotion: false,
    highContrast: false,
    largeText: false,
    screenReader: false,
    keyboardNavigation: true,
  });

  const [announcements, setAnnouncements] = useState<string[]>([]);

  // Initialize accessibility settings from localStorage and system preferences
  useEffect(() => {
    const savedSettings = localStorage.getItem('accessibility-settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }

    // Check system preferences
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');

    setSettings(prev => ({
      ...prev,
      reducedMotion: mediaQuery.matches,
      highContrast: contrastQuery.matches,
    }));

    const handleChange = (e: MediaQueryListEvent) => {
      if (e.media === '(prefers-reduced-motion: reduce)') {
        setSettings(prev => ({ ...prev, reducedMotion: e.matches }));
      } else if (e.media === '(prefers-contrast: high)') {
        setSettings(prev => ({ ...prev, highContrast: e.matches }));
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    contrastQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
      contrastQuery.removeEventListener('change', handleChange);
    };
  }, []);

  // Announce content to screen readers
  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    setAnnouncements(prev => [...prev, message]);

    // Create a temporary element for screen reader announcements
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.style.width = '1px';
    announcement.style.height = '1px';
    announcement.style.overflow = 'hidden';

    document.body.appendChild(announcement);
    announcement.textContent = message;

    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }, []);

  // Update accessibility settings
  const updateSetting = useCallback((key: keyof AccessibilitySettings, value: boolean) => {
    setSettings(prev => {
      const newSettings = { ...prev, [key]: value };
      localStorage.setItem('accessibility-settings', JSON.stringify(newSettings));
      return newSettings;
    });
  }, []);

  // Keyboard navigation utilities
  const handleKeyboardNavigation = useCallback((event: KeyboardEvent, actions: {
    onEnter?: () => void;
    onEscape?: () => void;
    onArrowUp?: () => void;
    onArrowDown?: () => void;
    onArrowLeft?: () => void;
    onArrowRight?: () => void;
    onTab?: () => void;
  }) => {
    switch (event.key) {
      case 'Enter':
        actions.onEnter?.();
        break;
      case 'Escape':
        actions.onEscape?.();
        break;
      case 'ArrowUp':
        event.preventDefault();
        actions.onArrowUp?.();
        break;
      case 'ArrowDown':
        event.preventDefault();
        actions.onArrowDown?.();
        break;
      case 'ArrowLeft':
        event.preventDefault();
        actions.onArrowLeft?.();
        break;
      case 'ArrowRight':
        event.preventDefault();
        actions.onArrowRight?.();
        break;
      case 'Tab':
        actions.onTab?.();
        break;
    }
  }, []);

  // Focus management
  const focusElement = useCallback((selector: string) => {
    const element = document.querySelector(selector) as HTMLElement;
    if (element) {
      element.focus();
      // Scroll into view if needed
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, []);

  // Skip link functionality
  const createSkipLink = useCallback((targetId: string, label: string = 'Skip to main content') => {
    const skipLink = document.createElement('a');
    skipLink.href = `#${targetId}`;
    skipLink.textContent = label;
    skipLink.className = 'skip-link';
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 6px;
      background: #000;
      color: #fff;
      padding: 8px;
      text-decoration: none;
      z-index: 1000;
      border-radius: 4px;
      font-size: 14px;
    `;

    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '6px';
    });

    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px';
    });

    document.body.insertBefore(skipLink, document.body.firstChild);
  }, []);

  return {
    settings,
    announcements,
    announce,
    updateSetting,
    handleKeyboardNavigation,
    focusElement,
    createSkipLink,
  };
};
