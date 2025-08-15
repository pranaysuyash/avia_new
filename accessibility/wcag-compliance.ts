/**
 * WCAG 2.1 AA Compliance Utilities
 * Accessibility testing and validation helpers
 * Follows WCAG 2.1 AA guidelines
 */

import { ThemeProvider } from '../shared/theme';

// WCAG Color contrast requirements
export const WCAG_CONTRAST_RATIOS = {
  AA_NORMAL: 4.5,      // Normal text AA
  AA_LARGE: 3,         // Large text AA (18pt+ or 14pt+ bold)
  AAA_NORMAL: 7,       // Normal text AAA
  AAA_LARGE: 4.5       // Large text AAA
} as const;

// Text size classifications for WCAG
export const TEXT_SIZES = {
  LARGE_PT: 18,        // 18pt or larger
  LARGE_BOLD_PT: 14    // 14pt or larger if bold
} as const;

/**
 * Convert hex color to RGB values
 */
export const hexToRgb = (hex: string): [number, number, number] | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result 
    ? [
        parseInt(result[1], 16),
        parseInt(result[2], 16),
        parseInt(result[3], 16)
      ]
    : null;
};

/**
 * Calculate relative luminance according to WCAG formula
 */
export const getRelativeLuminance = (r: number, g: number, b: number): number => {
  const [sR, sG, sB] = [r, g, b].map(component => {
    const c = component / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  
  return 0.2126 * sR + 0.7152 * sG + 0.0722 * sB;
};

/**
 * Calculate contrast ratio between two colors
 */
export const getContrastRatio = (color1: string, color2: string): number => {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);
  
  if (!rgb1 || !rgb2) return 1;
  
  const lum1 = getRelativeLuminance(...rgb1);
  const lum2 = getRelativeLuminance(...rgb2);
  
  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);
  
  return (lighter + 0.05) / (darker + 0.05);
};

/**
 * Check if color combination meets WCAG contrast requirements
 */
export const meetsContrastRequirement = (
  foreground: string, 
  background: string, 
  level: 'AA' | 'AAA' = 'AA',
  isLargeText: boolean = false
): boolean => {
  const ratio = getContrastRatio(foreground, background);
  
  if (level === 'AAA') {
    return ratio >= (isLargeText ? WCAG_CONTRAST_RATIOS.AAA_LARGE : WCAG_CONTRAST_RATIOS.AAA_NORMAL);
  }
  
  return ratio >= (isLargeText ? WCAG_CONTRAST_RATIOS.AA_LARGE : WCAG_CONTRAST_RATIOS.AA_NORMAL);
};

/**
 * Validate color combinations in design tokens
 */
export const validateDesignTokenContrast = (tokens: any): {
  valid: boolean;
  issues: Array<{
    path: string;
    foreground: string;
    background: string;
    ratio: number;
    required: number;
    level: string;
  }>;
} => {
  const issues: any[] = [];
  
  // Common color combinations to check
  const combinations = [
    {
      path: 'text.primary on background.primary',
      foreground: tokens.colors?.text?.primary || '#000000',
      background: tokens.colors?.background?.primary || '#ffffff',
      isLargeText: false
    },
    {
      path: 'text.secondary on background.primary',
      foreground: tokens.colors?.text?.secondary || '#666666',
      background: tokens.colors?.background?.primary || '#ffffff',
      isLargeText: false
    },
    {
      path: 'primary.contrast on primary.DEFAULT',
      foreground: tokens.colors?.primary?.contrast || '#ffffff',
      background: tokens.colors?.primary?.DEFAULT || '#3B82F6',
      isLargeText: false
    },
    {
      path: 'error.contrast on error.DEFAULT',
      foreground: tokens.colors?.error?.contrast || '#ffffff',
      background: tokens.colors?.error?.DEFAULT || '#EF4444',
      isLargeText: false
    },
    {
      path: 'success.contrast on success.DEFAULT',
      foreground: tokens.colors?.success?.contrast || '#ffffff',
      background: tokens.colors?.success?.DEFAULT || '#10B981',
      isLargeText: false
    }
  ];
  
  combinations.forEach(combo => {
    const ratio = getContrastRatio(combo.foreground, combo.background);
    const required = combo.isLargeText ? WCAG_CONTRAST_RATIOS.AA_LARGE : WCAG_CONTRAST_RATIOS.AA_NORMAL;
    
    if (ratio < required) {
      issues.push({
        path: combo.path,
        foreground: combo.foreground,
        background: combo.background,
        ratio: Math.round(ratio * 100) / 100,
        required,
        level: 'AA'
      });
    }
  });
  
  return {
    valid: issues.length === 0,
    issues
  };
};

/**
 * ARIA attribute validation
 */
export const validateAriaAttributes = (element: Element): {
  valid: boolean;
  issues: string[];
} => {
  const issues: string[] = [];
  const tagName = element.tagName.toLowerCase();
  
  // Check for required ARIA labels on interactive elements
  if (['button', 'a', 'input'].includes(tagName)) {
    const hasLabel = element.getAttribute('aria-label') || 
                    element.getAttribute('aria-labelledby') ||
                    element.textContent?.trim();
    
    if (!hasLabel) {
      issues.push(`Interactive element ${tagName} missing accessible label`);
    }
  }
  
  // Check for proper ARIA roles
  const role = element.getAttribute('role');
  if (role) {
    const validRoles = [
      'button', 'link', 'tab', 'tabpanel', 'navigation', 'main', 'banner',
      'contentinfo', 'complementary', 'article', 'section', 'dialog', 'menu',
      'menuitem', 'menubar', 'listbox', 'option', 'grid', 'gridcell'
    ];
    
    if (!validRoles.includes(role)) {
      issues.push(`Invalid ARIA role: ${role}`);
    }
  }
  
  // Check for proper ARIA relationships
  const labelledBy = element.getAttribute('aria-labelledby');
  if (labelledBy) {
    const labelElement = document.getElementById(labelledBy);
    if (!labelElement) {
      issues.push(`aria-labelledby references non-existent element: ${labelledBy}`);
    }
  }
  
  const describedBy = element.getAttribute('aria-describedby');
  if (describedBy) {
    const descElement = document.getElementById(describedBy);
    if (!descElement) {
      issues.push(`aria-describedby references non-existent element: ${describedBy}`);
    }
  }
  
  return {
    valid: issues.length === 0,
    issues
  };
};

/**
 * Keyboard navigation validation
 */
export const validateKeyboardNavigation = (container: Element): {
  valid: boolean;
  issues: string[];
} => {
  const issues: string[] = [];
  
  // Find all interactive elements
  const interactiveElements = container.querySelectorAll(
    'button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"]), [role="button"], [role="link"]'
  );
  
  let hasPositiveTabIndex = false;
  
  interactiveElements.forEach((element, index) => {
    const tabIndex = element.getAttribute('tabindex');
    
    // Check for positive tabindex (anti-pattern)
    if (tabIndex && parseInt(tabIndex) > 0) {
      hasPositiveTabIndex = true;
    }
    
    // Check if element is focusable
    const style = getComputedStyle(element as HTMLElement);
    if (style.display === 'none' || style.visibility === 'hidden') {
      const hasTabIndex = tabIndex && parseInt(tabIndex) >= 0;
      if (hasTabIndex) {
        issues.push(`Hidden element with positive tabindex: ${element.tagName}`);
      }
    }
  });
  
  if (hasPositiveTabIndex) {
    issues.push('Found positive tabindex values - use 0 or -1 instead');
  }
  
  if (interactiveElements.length === 0) {
    issues.push('No keyboard-focusable elements found');
  }
  
  return {
    valid: issues.length === 0,
    issues
  };
};

/**
 * Focus management utilities
 */
export const focusManagement = {
  /**
   * Set focus trap within container
   */
  trapFocus: (container: HTMLElement) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };
    
    container.addEventListener('keydown', handleTabKey);
    
    // Return cleanup function
    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  },
  
  /**
   * Save and restore focus
   */
  saveFocus: () => {
    const activeElement = document.activeElement as HTMLElement;
    return () => {
      if (activeElement && activeElement.focus) {
        activeElement.focus();
      }
    };
  },
  
  /**
   * Focus first element in container
   */
  focusFirst: (container: HTMLElement) => {
    const focusableElement = container.querySelector(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as HTMLElement;
    
    if (focusableElement) {
      focusableElement.focus();
    }
  }
};

/**
 * Screen reader utilities
 */
export const screenReader = {
  /**
   * Announce message to screen readers
   */
  announce: (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  },
  
  /**
   * Update accessible description
   */
  updateDescription: (elementId: string, description: string) => {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    let descriptionElement = document.getElementById(`${elementId}-description`);
    
    if (!descriptionElement) {
      descriptionElement = document.createElement('div');
      descriptionElement.id = `${elementId}-description`;
      descriptionElement.className = 'sr-only';
      document.body.appendChild(descriptionElement);
      element.setAttribute('aria-describedby', descriptionElement.id);
    }
    
    descriptionElement.textContent = description;
  }
};

/**
 * Accessibility testing suite
 */
export const accessibilityTest = {
  /**
   * Run comprehensive accessibility audit
   */
  audit: (container: Element = document.body): {
    score: number;
    issues: Array<{
      type: string;
      severity: 'error' | 'warning' | 'info';
      message: string;
      element?: Element;
    }>;
  } => {
    const issues: any[] = [];
    
    // Test 1: Color contrast
    const contrastTest = validateDesignTokenContrast(ThemeProvider.tokens);
    if (!contrastTest.valid) {
      contrastTest.issues.forEach(issue => {
        issues.push({
          type: 'color-contrast',
          severity: 'error' as const,
          message: `Low contrast ratio (${issue.ratio}) for ${issue.path}. Required: ${issue.required}`
        });
      });
    }
    
    // Test 2: ARIA attributes
    const allElements = container.querySelectorAll('*');
    allElements.forEach(element => {
      const ariaTest = validateAriaAttributes(element);
      if (!ariaTest.valid) {
        ariaTest.issues.forEach(issue => {
          issues.push({
            type: 'aria-attributes',
            severity: 'error' as const,
            message: issue,
            element
          });
        });
      }
    });
    
    // Test 3: Keyboard navigation
    const keyboardTest = validateKeyboardNavigation(container);
    if (!keyboardTest.valid) {
      keyboardTest.issues.forEach(issue => {
        issues.push({
          type: 'keyboard-navigation',
          severity: 'warning' as const,
          message: issue
        });
      });
    }
    
    // Test 4: Images without alt text
    const images = container.querySelectorAll('img');
    images.forEach(img => {
      if (!img.getAttribute('alt') && !img.getAttribute('aria-label')) {
        issues.push({
          type: 'missing-alt-text',
          severity: 'error' as const,
          message: 'Image missing alt text',
          element: img
        });
      }
    });
    
    // Test 5: Form labels
    const formInputs = container.querySelectorAll('input, select, textarea');
    formInputs.forEach(input => {
      const id = input.getAttribute('id');
      const hasLabel = id && container.querySelector(`label[for="${id}"]`);
      const hasAriaLabel = input.getAttribute('aria-label') || input.getAttribute('aria-labelledby');
      
      if (!hasLabel && !hasAriaLabel) {
        issues.push({
          type: 'missing-form-label',
          severity: 'error' as const,
          message: 'Form input missing label',
          element: input
        });
      }
    });
    
    // Calculate score (100 - percentage of issues)
    const totalTests = allElements.length * 2; // Rough estimate
    const errorCount = issues.filter(i => i.severity === 'error').length;
    const warningCount = issues.filter(i => i.severity === 'warning').length;
    
    const score = Math.max(0, 100 - ((errorCount * 5) + (warningCount * 2)));
    
    return {
      score: Math.round(score),
      issues
    };
  },
  
  /**
   * Generate accessibility report
   */
  generateReport: (container: Element = document.body): string => {
    const audit = accessibilityTest.audit(container);
    
    let report = `# Accessibility Audit Report\n\n`;
    report += `**Score: ${audit.score}/100**\n\n`;
    
    if (audit.issues.length === 0) {
      report += `✅ No accessibility issues found!\n\n`;
    } else {
      report += `## Issues Found (${audit.issues.length})\n\n`;
      
      const groupedIssues = audit.issues.reduce((groups, issue) => {
        if (!groups[issue.type]) {
          groups[issue.type] = [];
        }
        groups[issue.type].push(issue);
        return groups;
      }, {} as Record<string, typeof audit.issues>);
      
      Object.entries(groupedIssues).forEach(([type, typeIssues]) => {
        report += `### ${type.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}\n\n`;
        
        typeIssues.forEach(issue => {
          const severity = issue.severity === 'error' ? '🔴' : issue.severity === 'warning' ? '🟡' : '🔵';
          report += `${severity} ${issue.message}\n`;
        });
        
        report += `\n`;
      });
    }
    
    report += `## Recommendations\n\n`;
    report += `- Ensure all interactive elements have accessible labels\n`;
    report += `- Maintain proper color contrast ratios (4.5:1 for normal text)\n`;
    report += `- Provide keyboard navigation for all functionality\n`;
    report += `- Include alt text for all meaningful images\n`;
    report += `- Associate form inputs with labels\n`;
    report += `- Use semantic HTML elements where appropriate\n`;
    
    return report;
  }
};

/**
 * Accessibility hooks for React components
 */
export const useAccessibility = () => {
  return {
    announceToScreenReader: screenReader.announce,
    trapFocus: focusManagement.trapFocus,
    saveFocus: focusManagement.saveFocus,
    focusFirst: focusManagement.focusFirst,
    validateContrast: meetsContrastRequirement,
    audit: accessibilityTest.audit
  };
};

export default {
  validateDesignTokenContrast,
  validateAriaAttributes,
  validateKeyboardNavigation,
  meetsContrastRequirement,
  getContrastRatio,
  focusManagement,
  screenReader,
  accessibilityTest,
  useAccessibility
};