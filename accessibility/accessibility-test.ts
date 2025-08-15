/**
 * Accessibility Testing Suite
 * Automated accessibility testing for React components
 * Follows WCAG 2.1 AA guidelines
 */

import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { accessibilityTest, validateAriaAttributes, validateKeyboardNavigation } from './wcag-compliance';

// Test utilities for accessibility
export const accessibilityTestUtils = {
  /**
   * Test color contrast compliance
   */
  testColorContrast: async (component: React.ReactElement) => {
    const { container } = render(component);
    const audit = accessibilityTest.audit(container);
    
    const contrastIssues = audit.issues.filter(issue => issue.type === 'color-contrast');
    
    return {
      passed: contrastIssues.length === 0,
      issues: contrastIssues,
      message: contrastIssues.length > 0 
        ? `Found ${contrastIssues.length} color contrast violations`
        : 'All color contrasts meet WCAG 2.1 AA requirements'
    };
  },

  /**
   * Test keyboard navigation
   */
  testKeyboardNavigation: async (component: React.ReactElement) => {
    const user = userEvent.setup();
    const { container } = render(component);
    
    // Find all interactive elements
    const interactiveElements = container.querySelectorAll(
      'button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"]), [role="button"], [role="link"]'
    );
    
    const issues: string[] = [];
    
    // Test Tab navigation
    for (let i = 0; i < interactiveElements.length; i++) {
      await user.tab();
      const focused = document.activeElement;
      
      if (!focused || !container.contains(focused)) {
        issues.push(`Element ${i + 1} not reachable via Tab navigation`);
      }
    }
    
    // Test Shift+Tab navigation
    for (let i = interactiveElements.length - 1; i >= 0; i--) {
      await user.tab({ shift: true });
      const focused = document.activeElement;
      
      if (!focused || !container.contains(focused)) {
        issues.push(`Element ${i + 1} not reachable via Shift+Tab navigation`);
      }
    }
    
    // Test Enter/Space activation on buttons
    const buttons = container.querySelectorAll('button, [role="button"]');
    for (const button of Array.from(buttons)) {
      (button as HTMLElement).focus();
      
      // Test Enter key
      const enterResult = fireEvent.keyDown(button, { key: 'Enter' });
      if (!enterResult) {
        issues.push(`Button not activatable with Enter key: ${button.textContent}`);
      }
      
      // Test Space key
      const spaceResult = fireEvent.keyDown(button, { key: ' ' });
      if (!spaceResult) {
        issues.push(`Button not activatable with Space key: ${button.textContent}`);
      }
    }
    
    return {
      passed: issues.length === 0,
      issues,
      message: issues.length > 0 
        ? `Found ${issues.length} keyboard navigation issues`
        : 'Keyboard navigation works correctly'
    };
  },

  /**
   * Test ARIA attributes
   */
  testAriaAttributes: async (component: React.ReactElement) => {
    const { container } = render(component);
    const elements = container.querySelectorAll('*');
    
    const allIssues: string[] = [];
    
    elements.forEach(element => {
      const validation = validateAriaAttributes(element);
      allIssues.push(...validation.issues);
    });
    
    return {
      passed: allIssues.length === 0,
      issues: allIssues,
      message: allIssues.length > 0 
        ? `Found ${allIssues.length} ARIA attribute issues`
        : 'All ARIA attributes are valid'
    };
  },

  /**
   * Test screen reader announcements
   */
  testScreenReaderAnnouncements: async (component: React.ReactElement) => {
    const { container } = render(component);
    
    // Check for aria-live regions
    const liveRegions = container.querySelectorAll('[aria-live]');
    const issues: string[] = [];
    
    if (liveRegions.length === 0) {
      // This might be okay for some components
      return {
        passed: true,
        issues: [],
        message: 'No live regions found - this may be intentional'
      };
    }
    
    liveRegions.forEach(region => {
      const liveValue = region.getAttribute('aria-live');
      if (!['polite', 'assertive', 'off'].includes(liveValue || '')) {
        issues.push(`Invalid aria-live value: ${liveValue}`);
      }
    });
    
    return {
      passed: issues.length === 0,
      issues,
      message: issues.length > 0 
        ? `Found ${issues.length} screen reader announcement issues`
        : 'Screen reader announcements configured correctly'
    };
  },

  /**
   * Test form accessibility
   */
  testFormAccessibility: async (component: React.ReactElement) => {
    const { container } = render(component);
    const formElements = container.querySelectorAll('input, select, textarea');
    
    const issues: string[] = [];
    
    formElements.forEach(element => {
      const id = element.getAttribute('id');
      const label = id ? container.querySelector(`label[for="${id}"]`) : null;
      const ariaLabel = element.getAttribute('aria-label');
      const ariaLabelledBy = element.getAttribute('aria-labelledby');
      
      if (!label && !ariaLabel && !ariaLabelledBy) {
        issues.push(`Form element missing accessible label: ${element.tagName}`);
      }
      
      // Check for required fields
      if (element.hasAttribute('required')) {
        const hasRequiredIndicator = ariaLabel?.includes('required') ||
          label?.textContent?.includes('*') ||
          element.getAttribute('aria-required') === 'true';
        
        if (!hasRequiredIndicator) {
          issues.push(`Required field not clearly indicated: ${element.tagName}`);
        }
      }
      
      // Check for error states
      if (element.getAttribute('aria-invalid') === 'true') {
        const hasErrorMessage = element.getAttribute('aria-describedby');
        if (!hasErrorMessage) {
          issues.push(`Invalid field missing error message: ${element.tagName}`);
        }
      }
    });
    
    return {
      passed: issues.length === 0,
      issues,
      message: issues.length > 0 
        ? `Found ${issues.length} form accessibility issues`
        : 'Form accessibility is correct'
    };
  },

  /**
   * Test focus management
   */
  testFocusManagement: async (component: React.ReactElement) => {
    const user = userEvent.setup();
    const { container } = render(component);
    
    const issues: string[] = [];
    
    // Test initial focus
    const autoFocusElement = container.querySelector('[autofocus]');
    if (autoFocusElement && document.activeElement !== autoFocusElement) {
      issues.push('Autofocus element not focused on mount');
    }
    
    // Test focus trap (if modal/dialog)
    const dialog = container.querySelector('[role="dialog"], [role="alertdialog"]');
    if (dialog) {
      const focusableElements = dialog.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      if (focusableElements.length === 0) {
        issues.push('Dialog has no focusable elements');
      } else {
        // Test focus trap by tabbing through all elements
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
        
        lastElement.focus();
        await user.tab();
        
        if (document.activeElement !== firstElement) {
          issues.push('Focus trap not working - Tab from last element should focus first');
        }
        
        firstElement.focus();
        await user.tab({ shift: true });
        
        if (document.activeElement !== lastElement) {
          issues.push('Focus trap not working - Shift+Tab from first element should focus last');
        }
      }
    }
    
    // Test focus indicators
    const focusableElements = container.querySelectorAll(
      'button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    for (const element of Array.from(focusableElements)) {
      (element as HTMLElement).focus();
      const computedStyle = getComputedStyle(element as HTMLElement);
      
      // Check for focus outline
      if (computedStyle.outline === 'none' && 
          computedStyle.boxShadow === 'none' &&
          !computedStyle.border.includes('focus')) {
        issues.push(`Element missing focus indicator: ${element.tagName}`);
      }
    }
    
    return {
      passed: issues.length === 0,
      issues,
      message: issues.length > 0 
        ? `Found ${issues.length} focus management issues`
        : 'Focus management works correctly'
    };
  },

  /**
   * Run comprehensive accessibility test suite
   */
  runFullSuite: async (component: React.ReactElement) => {
    const tests = [
      { name: 'Color Contrast', test: accessibilityTestUtils.testColorContrast },
      { name: 'Keyboard Navigation', test: accessibilityTestUtils.testKeyboardNavigation },
      { name: 'ARIA Attributes', test: accessibilityTestUtils.testAriaAttributes },
      { name: 'Screen Reader', test: accessibilityTestUtils.testScreenReaderAnnouncements },
      { name: 'Form Accessibility', test: accessibilityTestUtils.testFormAccessibility },
      { name: 'Focus Management', test: accessibilityTestUtils.testFocusManagement }
    ];
    
    const results = [];
    
    for (const { name, test } of tests) {
      try {
        const result = await test(component);
        results.push({
          name,
          ...result
        });
      } catch (error) {
        results.push({
          name,
          passed: false,
          issues: [`Test failed: ${error}`],
          message: `Test "${name}" failed with error`
        });
      }
    }
    
    const passedTests = results.filter(r => r.passed).length;
    const totalTests = results.length;
    
    return {
      summary: {
        passed: passedTests,
        total: totalTests,
        score: Math.round((passedTests / totalTests) * 100)
      },
      results
    };
  }
};

/**
 * Jest custom matchers for accessibility testing
 */
export const accessibilityMatchers = {
  toBeAccessible: async function(component: React.ReactElement) {
    const result = await accessibilityTestUtils.runFullSuite(component);
    const passed = result.summary.score >= 80; // 80% pass rate threshold
    
    return {
      pass: passed,
      message: () => {
        if (passed) {
          return `Component passed accessibility tests (${result.summary.score}% success rate)`;
        } else {
          const failedTests = result.results.filter(r => !r.passed);
          const errorSummary = failedTests.map(test => 
            `${test.name}: ${test.issues.join(', ')}`
          ).join('\n');
          
          return `Component failed accessibility tests (${result.summary.score}% success rate):\n${errorSummary}`;
        }
      }
    };
  },
  
  toHaveGoodColorContrast: async function(component: React.ReactElement) {
    const result = await accessibilityTestUtils.testColorContrast(component);
    
    return {
      pass: result.passed,
      message: () => result.message
    };
  },
  
  toSupportKeyboardNavigation: async function(component: React.ReactElement) {
    const result = await accessibilityTestUtils.testKeyboardNavigation(component);
    
    return {
      pass: result.passed,
      message: () => result.message
    };
  },
  
  toHaveValidAriaAttributes: async function(component: React.ReactElement) {
    const result = await accessibilityTestUtils.testAriaAttributes(component);
    
    return {
      pass: result.passed,
      message: () => result.message
    };
  }
};

/**
 * Accessibility test helper for component testing
 */
export const createAccessibilityTest = (componentName: string) => {
  return {
    /**
     * Generate test cases for a component
     */
    generateTestCases: (component: React.ReactElement, customTests?: Array<{
      name: string;
      test: () => Promise<any>;
    }>) => {
      return [
        {
          name: `${componentName} - Color Contrast`,
          test: () => accessibilityTestUtils.testColorContrast(component)
        },
        {
          name: `${componentName} - Keyboard Navigation`,
          test: () => accessibilityTestUtils.testKeyboardNavigation(component)
        },
        {
          name: `${componentName} - ARIA Attributes`,
          test: () => accessibilityTestUtils.testAriaAttributes(component)
        },
        {
          name: `${componentName} - Focus Management`,
          test: () => accessibilityTestUtils.testFocusManagement(component)
        },
        ...(customTests || [])
      ];
    },
    
    /**
     * Run all tests and generate report
     */
    runTests: async (component: React.ReactElement) => {
      const suite = await accessibilityTestUtils.runFullSuite(component);
      
      console.log(`\n=== Accessibility Test Report: ${componentName} ===`);
      console.log(`Score: ${suite.summary.score}% (${suite.summary.passed}/${suite.summary.total} tests passed)\n`);
      
      suite.results.forEach(result => {
        const status = result.passed ? '✅' : '❌';
        console.log(`${status} ${result.name}: ${result.message}`);
        
        if (!result.passed && result.issues.length > 0) {
          result.issues.forEach(issue => {
            console.log(`   - ${issue}`);
          });
        }
      });
      
      console.log('\n');
      
      return suite;
    }
  };
};

export default accessibilityTestUtils;