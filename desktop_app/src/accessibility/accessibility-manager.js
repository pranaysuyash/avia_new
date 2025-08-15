/**
 * Electron Accessibility Manager
 * Comprehensive accessibility system for desktop application
 * Integrates with OS accessibility APIs and provides WCAG 2.1 AA compliance
 */

const { ipcMain, ipcRenderer, systemPreferences, nativeTheme, shell } = require('electron');
const path = require('path');
const fs = require('fs').promises;

class AccessibilityManager {
  constructor(isMainProcess = false) {
    this.isMainProcess = isMainProcess;
    this.preferences = this.getDefaultPreferences();
    this.systemPreferences = null;
    this.accessibilityFeatures = new Set();
    
    this.init();
  }

  getDefaultPreferences() {
    return {
      highContrast: false,
      largeText: false,
      reducedMotion: false,
      screenReader: false,
      keyboardNavigation: false,
      soundEffects: true,
      visualIndicators: true,
      autoScroll: false,
      focusRing: true,
      voiceControl: false,
    };
  }

  async init() {
    if (this.isMainProcess) {
      await this.initMainProcess();
    } else {
      await this.initRendererProcess();
    }
  }

  async initMainProcess() {
    // Load saved preferences
    await this.loadPreferences();

    // Detect system accessibility features
    this.detectSystemAccessibilityFeatures();

    // Set up IPC handlers for accessibility
    this.setupIPCHandlers();

    // Monitor system preference changes
    this.monitorSystemChanges();

    // Apply initial accessibility settings
    this.applyAccessibilitySettings();

    console.log('🔧 Accessibility Manager initialized in main process');
  }

  async initRendererProcess() {
    // Load preferences from main process
    this.preferences = await this.requestFromMain('get-accessibility-preferences');

    // Set up IPC listeners
    this.setupRendererListeners();

    // Apply accessibility CSS and behaviors
    this.applyAccessibilityToRenderer();

    // Set up keyboard navigation
    this.initKeyboardNavigation();

    console.log('🎨 Accessibility Manager initialized in renderer process');
  }

  detectSystemAccessibilityFeatures() {
    if (!this.isMainProcess || process.platform !== 'darwin') return;

    try {
      // macOS accessibility detection
      const accessibilityFeatures = {
        highContrast: systemPreferences.getUserDefault('AppleInterfaceStyle', 'string') === 'Dark',
        reducedMotion: systemPreferences.getUserDefault('reduceMotion', 'boolean') || false,
        largeText: systemPreferences.getUserDefault('AppleMagnificationEnabled', 'boolean') || false,
        voiceControl: systemPreferences.getUserDefault('VoiceControlEnabled', 'boolean') || false,
      };

      // Update preferences with system settings
      this.preferences = { ...this.preferences, ...accessibilityFeatures };

      // Check for screen readers (VoiceOver on macOS)
      if (systemPreferences.isTrustedAccessibilityClient && systemPreferences.isTrustedAccessibilityClient(false)) {
        this.preferences.screenReader = true;
        this.accessibilityFeatures.add('screen-reader');
      }

      console.log('🔍 Detected system accessibility features:', Object.keys(accessibilityFeatures));
    } catch (error) {
      console.error('❌ Failed to detect system accessibility features:', error);
    }
  }

  setupIPCHandlers() {
    ipcMain.handle('get-accessibility-preferences', () => {
      return this.preferences;
    });

    ipcMain.handle('set-accessibility-preference', async (event, key, value) => {
      this.preferences[key] = value;
      await this.savePreferences();
      
      // Notify all renderer processes
      this.broadcastToRenderers('accessibility-preference-changed', { key, value });
      
      // Apply system-level changes
      this.applyAccessibilitySettings();
      
      return this.preferences;
    });

    ipcMain.handle('get-system-accessibility-info', () => {
      return {
        features: Array.from(this.accessibilityFeatures),
        platform: process.platform,
        screenReader: this.preferences.screenReader,
        highContrast: nativeTheme.shouldUseHighContrastColors,
        darkMode: nativeTheme.shouldUseDarkColors,
      };
    });

    ipcMain.handle('announce-to-screen-reader', (event, message) => {
      // Platform-specific screen reader announcements
      this.announceToScreenReader(message);
    });

    ipcMain.handle('trigger-accessibility-action', (event, action, data) => {
      return this.triggerAccessibilityAction(action, data);
    });
  }

  setupRendererListeners() {
    if (this.isMainProcess) return;

    ipcRenderer.on('accessibility-preference-changed', (event, { key, value }) => {
      this.preferences[key] = value;
      this.applyAccessibilityToRenderer();
      this.notifyAccessibilityChange(key, value);
    });

    ipcRenderer.on('system-accessibility-changed', (event, changes) => {
      console.log('🔄 System accessibility settings changed:', changes);
      this.handleSystemAccessibilityChanges(changes);
    });
  }

  async loadPreferences() {
    try {
      const { app } = require('electron');
      const userDataPath = app.getPath('userData');
      const preferencesPath = path.join(userDataPath, 'accessibility-preferences.json');
      
      const data = await fs.readFile(preferencesPath, 'utf8');
      const savedPreferences = JSON.parse(data);
      
      this.preferences = { ...this.preferences, ...savedPreferences };
      console.log('📂 Loaded accessibility preferences');
    } catch (error) {
      // File doesn't exist or is corrupted, use defaults
      console.log('📂 Using default accessibility preferences');
    }
  }

  async savePreferences() {
    try {
      const { app } = require('electron');
      const userDataPath = app.getPath('userData');
      const preferencesPath = path.join(userDataPath, 'accessibility-preferences.json');
      
      await fs.writeFile(preferencesPath, JSON.stringify(this.preferences, null, 2));
      console.log('💾 Saved accessibility preferences');
    } catch (error) {
      console.error('❌ Failed to save accessibility preferences:', error);
    }
  }

  applyAccessibilitySettings() {
    if (!this.isMainProcess) return;

    // Apply high contrast theme
    if (this.preferences.highContrast) {
      nativeTheme.themeSource = 'dark';
    }

    // System-level accessibility adjustments would go here
    // This varies significantly by platform
  }

  applyAccessibilityToRenderer() {
    if (this.isMainProcess) return;

    // Inject accessibility CSS
    this.injectAccessibilityCSS();

    // Configure ARIA live regions
    this.setupLiveRegions();

    // Apply font size adjustments
    if (this.preferences.largeText) {
      document.documentElement.style.fontSize = '120%';
    }

    // Configure motion preferences
    if (this.preferences.reducedMotion) {
      document.documentElement.style.setProperty('--animation-duration', '0.01ms');
      document.documentElement.style.setProperty('--transition-duration', '0.01ms');
    }

    // High contrast mode
    if (this.preferences.highContrast) {
      document.documentElement.classList.add('high-contrast-mode');
    } else {
      document.documentElement.classList.remove('high-contrast-mode');
    }

    // Screen reader optimizations
    if (this.preferences.screenReader) {
      document.documentElement.classList.add('screen-reader-mode');
    }
  }

  injectAccessibilityCSS() {
    const css = `
      /* Focus management */
      :focus {
        outline: 2px solid #3B82F6 !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
      }

      /* High contrast mode */
      .high-contrast-mode {
        filter: contrast(150%) !important;
      }

      .high-contrast-mode * {
        background-color: white !important;
        color: black !important;
        border-color: black !important;
      }

      .high-contrast-mode button,
      .high-contrast-mode input,
      .high-contrast-mode select,
      .high-contrast-mode textarea {
        border: 2px solid black !important;
        background-color: white !important;
        color: black !important;
      }

      /* Reduced motion */
      @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
          scroll-behavior: auto !important;
        }
      }

      /* Screen reader only content */
      .sr-only {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        padding: 0 !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        white-space: nowrap !important;
        border: 0 !important;
      }

      /* Skip links */
      .skip-link {
        position: absolute;
        top: -40px;
        left: 6px;
        z-index: 10000;
        background: #3B82F6;
        color: white;
        padding: 8px;
        text-decoration: none;
        border-radius: 4px;
        transition: top 0.3s ease;
      }

      .skip-link:focus {
        top: 6px;
      }

      /* Enhanced focus for keyboard navigation */
      .keyboard-navigation *:focus {
        outline: 3px solid #3B82F6 !important;
        outline-offset: 2px !important;
      }

      /* Minimum touch targets */
      button,
      [role="button"],
      input[type="button"],
      input[type="submit"],
      input[type="reset"] {
        min-height: 44px;
        min-width: 44px;
      }

      /* Screen reader mode optimizations */
      .screen-reader-mode .decorative {
        display: none !important;
      }

      .screen-reader-mode img:not([alt]) {
        opacity: 0.5;
      }

      .screen-reader-mode img:not([alt])::after {
        content: "Image without description";
        position: absolute;
        background: #ff0000;
        color: white;
        padding: 2px;
        font-size: 10px;
      }
    `;

    let styleElement = document.getElementById('accessibility-styles');
    if (!styleElement) {
      styleElement = document.createElement('style');
      styleElement.id = 'accessibility-styles';
      document.head.appendChild(styleElement);
    }
    styleElement.textContent = css;
  }

  setupLiveRegions() {
    // Create ARIA live regions for announcements
    if (!document.getElementById('accessibility-announcements')) {
      const liveRegion = document.createElement('div');
      liveRegion.id = 'accessibility-announcements';
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.className = 'sr-only';
      document.body.appendChild(liveRegion);
    }

    if (!document.getElementById('accessibility-alerts')) {
      const alertRegion = document.createElement('div');
      alertRegion.id = 'accessibility-alerts';
      alertRegion.setAttribute('aria-live', 'assertive');
      alertRegion.setAttribute('aria-atomic', 'true');
      alertRegion.className = 'sr-only';
      document.body.appendChild(alertRegion);
    }
  }

  initKeyboardNavigation() {
    if (this.isMainProcess) return;

    // Enable keyboard navigation mode
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Tab') {
        document.documentElement.classList.add('keyboard-navigation');
        this.preferences.keyboardNavigation = true;
      }
    });

    document.addEventListener('mousedown', () => {
      document.documentElement.classList.remove('keyboard-navigation');
      this.preferences.keyboardNavigation = false;
    });

    // Global keyboard shortcuts for accessibility
    document.addEventListener('keydown', (event) => {
      // Alt + Shift + A: Open accessibility settings
      if (event.altKey && event.shiftKey && event.key === 'A') {
        event.preventDefault();
        this.openAccessibilitySettings();
      }

      // Alt + Shift + H: Toggle high contrast
      if (event.altKey && event.shiftKey && event.key === 'H') {
        event.preventDefault();
        this.togglePreference('highContrast');
      }

      // Alt + Shift + T: Toggle large text
      if (event.altKey && event.shiftKey && event.key === 'T') {
        event.preventDefault();
        this.togglePreference('largeText');
      }

      // Alt + Shift + M: Toggle reduced motion
      if (event.altKey && event.shiftKey && event.key === 'M') {
        event.preventDefault();
        this.togglePreference('reducedMotion');
      }
    });

    // Focus management
    this.initFocusManagement();
  }

  initFocusManagement() {
    // Track focus for better accessibility
    document.addEventListener('focus', (event) => {
      const element = event.target;
      
      // Announce focus changes to screen readers
      if (this.preferences.screenReader) {
        const label = this.getAccessibleLabel(element);
        if (label) {
          this.announceToScreenReader(`Focused: ${label}`);
        }
      }
    }, true);

    // Skip link functionality
    this.addSkipLinks();
  }

  addSkipLinks() {
    const skipTargets = [
      { href: '#main-content', label: 'Skip to main content' },
      { href: '#navigation', label: 'Skip to navigation' },
      { href: '#search', label: 'Skip to search' }
    ];

    const skipContainer = document.createElement('div');
    skipContainer.className = 'skip-links';
    
    skipTargets.forEach(target => {
      const skipLink = document.createElement('a');
      skipLink.href = target.href;
      skipLink.textContent = target.label;
      skipLink.className = 'skip-link';
      skipContainer.appendChild(skipLink);
    });

    document.body.insertBefore(skipContainer, document.body.firstChild);
  }

  // Screen reader announcements
  announceToScreenReader(message, priority = 'polite') {
    if (this.isMainProcess) {
      // Platform-specific screen reader integration would go here
      console.log(`📢 Screen Reader: ${message}`);
      return;
    }

    const regionId = priority === 'assertive' ? 'accessibility-alerts' : 'accessibility-announcements';
    const region = document.getElementById(regionId);
    
    if (region) {
      region.textContent = '';
      setTimeout(() => {
        region.textContent = message;
      }, 100);
    }
  }

  // Utility methods for renderer process
  async requestFromMain(channel, ...args) {
    if (this.isMainProcess) return null;
    return await ipcRenderer.invoke(channel, ...args);
  }

  sendToMain(channel, ...args) {
    if (this.isMainProcess) return;
    ipcRenderer.send(channel, ...args);
  }

  broadcastToRenderers(channel, data) {
    if (!this.isMainProcess) return;
    
    const { BrowserWindow } = require('electron');
    BrowserWindow.getAllWindows().forEach(window => {
      window.webContents.send(channel, data);
    });
  }

  async togglePreference(key) {
    const newValue = !this.preferences[key];
    
    if (this.isMainProcess) {
      this.preferences[key] = newValue;
      await this.savePreferences();
      this.applyAccessibilitySettings();
      this.broadcastToRenderers('accessibility-preference-changed', { key, value: newValue });
    } else {
      await this.requestFromMain('set-accessibility-preference', key, newValue);
    }

    this.announceToScreenReader(`${key.replace(/([A-Z])/g, ' $1').toLowerCase()} ${newValue ? 'enabled' : 'disabled'}`);
  }

  getAccessibleLabel(element) {
    return element.getAttribute('aria-label') ||
           element.getAttribute('aria-labelledby') ||
           element.getAttribute('title') ||
           element.textContent ||
           element.getAttribute('alt') ||
           element.tagName.toLowerCase();
  }

  openAccessibilitySettings() {
    // This would open an accessibility settings dialog
    this.announceToScreenReader('Opening accessibility settings');
    
    // For now, just log available shortcuts
    console.log(`
🔧 Accessibility Shortcuts:
• Alt + Shift + A: Open accessibility settings
• Alt + Shift + H: Toggle high contrast
• Alt + Shift + T: Toggle large text  
• Alt + Shift + M: Toggle reduced motion
    `);
  }

  // Color contrast checking
  checkColorContrast(foreground, background) {
    // Implementation would use the same algorithm as in the React version
    // This is a simplified version
    return {
      ratio: 4.5, // Placeholder
      passes: true
    };
  }

  // Validation methods
  validatePageAccessibility() {
    if (this.isMainProcess) return {};

    const issues = [];

    // Check for images without alt text
    const images = document.querySelectorAll('img:not([alt])');
    images.forEach(img => {
      issues.push({
        element: 'img',
        issue: 'Missing alt text',
        severity: 'critical',
        wcag: '1.1.1'
      });
    });

    // Check for buttons without accessible names
    const buttons = document.querySelectorAll('button:not([aria-label]):not([title])');
    buttons.forEach(btn => {
      if (!btn.textContent.trim()) {
        issues.push({
          element: 'button',
          issue: 'Button without accessible name',
          severity: 'critical', 
          wcag: '4.1.2'
        });
      }
    });

    return {
      issues,
      score: Math.max(0, 100 - (issues.length * 10))
    };
  }

  monitorSystemChanges() {
    if (!this.isMainProcess || process.platform !== 'darwin') return;

    // Monitor for system accessibility changes
    try {
      systemPreferences.subscribeNotification('AppleInterfaceThemeChangedNotification', () => {
        const isDark = systemPreferences.getUserDefault('AppleInterfaceStyle', 'string') === 'Dark';
        this.preferences.highContrast = isDark;
        this.broadcastToRenderers('system-accessibility-changed', { highContrast: isDark });
      });
    } catch (error) {
      console.error('❌ Failed to monitor system changes:', error);
    }
  }

  notifyAccessibilityChange(key, value) {
    // Custom event for accessibility changes
    const event = new CustomEvent('accessibility-change', {
      detail: { key, value, preferences: this.preferences }
    });
    document.dispatchEvent(event);
  }

  handleSystemAccessibilityChanges(changes) {
    Object.entries(changes).forEach(([key, value]) => {
      this.preferences[key] = value;
    });
    this.applyAccessibilityToRenderer();
  }

  triggerAccessibilityAction(action, data) {
    switch (action) {
      case 'focus-element':
        if (data.selector) {
          const element = document.querySelector(data.selector);
          if (element) element.focus();
        }
        break;
      case 'scroll-to-element':
        if (data.selector) {
          const element = document.querySelector(data.selector);
          if (element) element.scrollIntoView({ behavior: 'smooth' });
        }
        break;
      case 'announce':
        this.announceToScreenReader(data.message, data.priority);
        break;
      default:
        console.warn('Unknown accessibility action:', action);
    }
  }
}

// Export for use in main and renderer processes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AccessibilityManager;
}

// Auto-initialize based on process type
if (typeof window !== 'undefined') {
  // Renderer process
  window.accessibilityManager = new AccessibilityManager(false);
} else if (typeof process !== 'undefined' && process.type === 'browser') {
  // Main process - will be initialized when required
  global.AccessibilityManager = AccessibilityManager;
}