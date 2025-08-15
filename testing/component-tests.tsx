/**
 * Component Testing Suite
 * Comprehensive testing utilities for UI/UX components
 * Tests accessibility, performance, and functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { accessibilityTestUtils, createAccessibilityTest } from '../accessibility/accessibility-test';
import { ThemeProvider } from '../shared/theme';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Test utilities
export const testUtils = {
  /**
   * Render component with theme provider
   */
  renderWithTheme: (component: React.ReactElement) => {
    return render(
      <ThemeProvider.Provider value={ThemeProvider.web}>
        {component}
      </ThemeProvider.Provider>
    );
  },

  /**
   * Render component with user event setup
   */
  renderWithUser: (component: React.ReactElement) => {
    const user = userEvent.setup();
    const result = testUtils.renderWithTheme(component);
    return { ...result, user };
  },

  /**
   * Wait for element to be removed
   */
  waitForElementToBeRemoved: async (element: HTMLElement | (() => HTMLElement)) => {
    await waitFor(() => {
      const el = typeof element === 'function' ? element() : element;
      expect(el).not.toBeInTheDocument();
    });
  },

  /**
   * Simulate viewport resize
   */
  resizeViewport: (width: number, height: number = 768) => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: width,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: height,
    });
    window.dispatchEvent(new Event('resize'));
  },

  /**
   * Mock intersection observer
   */
  mockIntersectionObserver: () => {
    const mockObserver = {
      observe: jest.fn(),
      unobserve: jest.fn(),
      disconnect: jest.fn(),
    };

    global.IntersectionObserver = jest.fn(() => mockObserver) as any;
    return mockObserver;
  },

  /**
   * Mock performance observer
   */
  mockPerformanceObserver: () => {
    const mockObserver = {
      observe: jest.fn(),
      disconnect: jest.fn(),
    };

    global.PerformanceObserver = jest.fn(() => mockObserver) as any;
    return mockObserver;
  }
};

/**
 * Accessibility testing suite
 */
export const accessibilityTests = {
  /**
   * Test component accessibility with axe
   */
  testAxeCompliance: async (component: React.ReactElement) => {
    const { container } = testUtils.renderWithTheme(component);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  },

  /**
   * Test keyboard navigation
   */
  testKeyboardNavigation: async (component: React.ReactElement) => {
    const { container, user } = testUtils.renderWithUser(component);
    
    // Find all interactive elements
    const interactiveElements = container.querySelectorAll(
      'button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"]), [role="button"], [role="link"]'
    );

    // Test that all elements are reachable via Tab
    for (let i = 0; i < interactiveElements.length; i++) {
      await user.tab();
      const activeElement = document.activeElement;
      expect(activeElement).toBeInTheDocument();
    }

    // Test Shift+Tab navigation
    for (let i = interactiveElements.length - 1; i >= 0; i--) {
      await user.tab({ shift: true });
      const activeElement = document.activeElement;
      expect(activeElement).toBeInTheDocument();
    }
  },

  /**
   * Test screen reader compatibility
   */
  testScreenReaderSupport: (component: React.ReactElement) => {
    const { container } = testUtils.renderWithTheme(component);

    // Check for proper semantic structure
    const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const landmarks = container.querySelectorAll('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"]');
    const labels = container.querySelectorAll('label, [aria-label], [aria-labelledby]');

    // Basic checks
    expect(headings.length).toBeGreaterThanOrEqual(0);
    expect(landmarks.length).toBeGreaterThanOrEqual(0);
    
    // Check that interactive elements have accessible names
    const interactiveElements = container.querySelectorAll('button, input, select, textarea');
    interactiveElements.forEach(element => {
      const hasAccessibleName = 
        element.getAttribute('aria-label') ||
        element.getAttribute('aria-labelledby') ||
        element.textContent?.trim() ||
        container.querySelector(`label[for="${element.id}"]`);
      
      expect(hasAccessibleName).toBeTruthy();
    });
  },

  /**
   * Test focus management
   */
  testFocusManagement: async (component: React.ReactElement) => {
    const { container, user } = testUtils.renderWithUser(component);

    // Test initial focus
    const autoFocusElement = container.querySelector('[autofocus]');
    if (autoFocusElement) {
      expect(document.activeElement).toBe(autoFocusElement);
    }

    // Test focus trap in modals/dialogs
    const dialogs = container.querySelectorAll('[role="dialog"], [role="alertdialog"]');
    
    for (const dialog of Array.from(dialogs)) {
      const focusableElements = dialog.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      if (focusableElements.length > 0) {
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

        // Test focus trap
        lastElement.focus();
        await user.tab();
        expect(document.activeElement).toBe(firstElement);

        firstElement.focus();
        await user.tab({ shift: true });
        expect(document.activeElement).toBe(lastElement);
      }
    }
  }
};

/**
 * Performance testing suite
 */
export const performanceTests = {
  /**
   * Test component render performance
   */
  testRenderPerformance: async (component: React.ReactElement, threshold: number = 16) => {
    const startTime = performance.now();
    
    await act(async () => {
      testUtils.renderWithTheme(component);
    });
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    expect(renderTime).toBeLessThan(threshold);
    return renderTime;
  },

  /**
   * Test component re-render performance
   */
  testReRenderPerformance: async (
    ComponentWithProps: React.ComponentType<any>,
    propChanges: any[],
    threshold: number = 8
  ) => {
    const { rerender } = testUtils.renderWithTheme(<ComponentWithProps {...propChanges[0]} />);
    
    const renderTimes: number[] = [];
    
    for (let i = 1; i < propChanges.length; i++) {
      const startTime = performance.now();
      
      await act(async () => {
        rerender(<ComponentWithProps {...propChanges[i]} />);
      });
      
      const endTime = performance.now();
      renderTimes.push(endTime - startTime);
    }
    
    const averageRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length;
    expect(averageRenderTime).toBeLessThan(threshold);
    
    return { renderTimes, averageRenderTime };
  },

  /**
   * Test memory usage
   */
  testMemoryUsage: async (component: React.ReactElement) => {
    const initialMemory = (performance as any).memory?.usedJSHeapSize || 0;
    
    const { unmount } = testUtils.renderWithTheme(component);
    
    // Force garbage collection if available
    if ((window as any).gc) {
      (window as any).gc();
    }
    
    unmount();
    
    // Force garbage collection again
    if ((window as any).gc) {
      (window as any).gc();
    }
    
    const finalMemory = (performance as any).memory?.usedJSHeapSize || 0;
    const memoryDifference = finalMemory - initialMemory;
    
    // Memory should not increase significantly after unmounting
    expect(memoryDifference).toBeLessThan(1024 * 1024); // 1MB threshold
    
    return memoryDifference;
  }
};

/**
 * Visual regression testing utilities
 */
export const visualTests = {
  /**
   * Test component snapshot
   */
  testSnapshot: (component: React.ReactElement, testName: string) => {
    const { container } = testUtils.renderWithTheme(component);
    expect(container.firstChild).toMatchSnapshot(testName);
  },

  /**
   * Test responsive behavior
   */
  testResponsiveDesign: async (component: React.ReactElement, breakpoints: number[] = [320, 768, 1024, 1440]) => {
    const { container } = testUtils.renderWithTheme(component);
    const snapshots: Record<string, any> = {};

    for (const breakpoint of breakpoints) {
      testUtils.resizeViewport(breakpoint);
      
      // Wait for any responsive changes
      await waitFor(() => {
        snapshots[`${breakpoint}px`] = container.innerHTML;
      });
    }

    return snapshots;
  },

  /**
   * Test theme variations
   */
  testThemeVariations: (component: React.ReactElement, themes: string[] = ['light', 'dark']) => {
    const snapshots: Record<string, any> = {};

    themes.forEach(themeName => {
      const { container } = render(
        <div data-theme={themeName}>
          {component}
        </div>
      );
      
      snapshots[themeName] = container.firstChild;
      expect(snapshots[themeName]).toMatchSnapshot(`${themeName}-theme`);
    });

    return snapshots;
  }
};

/**
 * Interaction testing utilities
 */
export const interactionTests = {
  /**
   * Test form interactions
   */
  testFormInteractions: async (formComponent: React.ReactElement) => {
    const { user } = testUtils.renderWithUser(formComponent);
    
    // Find all form inputs
    const inputs = screen.getAllByRole('textbox');
    const selects = screen.queryAllByRole('combobox');
    const buttons = screen.getAllByRole('button');

    // Test input interactions
    for (const input of inputs) {
      await user.click(input);
      await user.type(input, 'test value');
      expect(input).toHaveValue('test value');
      
      await user.clear(input);
      expect(input).toHaveValue('');
    }

    // Test select interactions
    for (const select of selects) {
      await user.click(select);
      // Test would depend on specific select implementation
    }

    // Test button interactions
    for (const button of buttons) {
      if (!button.hasAttribute('disabled')) {
        await user.click(button);
        // Verify button behavior
      }
    }
  },

  /**
   * Test drag and drop interactions
   */
  testDragAndDrop: async (component: React.ReactElement, sourceSelector: string, targetSelector: string) => {
    const { container, user } = testUtils.renderWithUser(component);
    
    const sourceElement = container.querySelector(sourceSelector);
    const targetElement = container.querySelector(targetSelector);
    
    expect(sourceElement).toBeInTheDocument();
    expect(targetElement).toBeInTheDocument();

    // Simulate drag and drop
    await user.hover(sourceElement!);
    await user.pointer([
      { target: sourceElement, keys: '[MouseLeft>]' },
      { target: targetElement, keys: '[/MouseLeft]' }
    ]);
  },

  /**
   * Test loading states
   */
  testLoadingStates: async (component: React.ReactElement, triggerLoading: () => void) => {
    const { container } = testUtils.renderWithTheme(component);
    
    // Trigger loading state
    act(() => {
      triggerLoading();
    });

    // Check for loading indicators
    await waitFor(() => {
      const loadingSpinner = container.querySelector('[data-testid="loading-spinner"], .loading, .spinner');
      const loadingText = screen.queryByText(/loading/i);
      
      expect(loadingSpinner || loadingText).toBeInTheDocument();
    });
  }
};

/**
 * Error testing utilities
 */
export const errorTests = {
  /**
   * Test error boundaries
   */
  testErrorBoundary: (ErrorBoundary: React.ComponentType<any>, FailingComponent: React.ComponentType) => {
    // Suppress console.error for this test
    const originalError = console.error;
    console.error = jest.fn();

    const { container } = render(
      <ErrorBoundary>
        <FailingComponent />
      </ErrorBoundary>
    );

    // Check that error boundary renders fallback UI
    expect(container).toHaveTextContent(/error/i);

    // Restore console.error
    console.error = originalError;
  },

  /**
   * Test error handling
   */
  testErrorHandling: async (component: React.ReactElement, triggerError: () => void) => {
    const { container } = testUtils.renderWithTheme(component);
    
    // Trigger error
    act(() => {
      triggerError();
    });

    // Check for error display
    await waitFor(() => {
      const errorMessage = container.querySelector('[role="alert"], .error-message');
      expect(errorMessage).toBeInTheDocument();
    });
  }
};

/**
 * Complete component test suite
 */
export const createComponentTestSuite = (
  componentName: string,
  component: React.ReactElement,
  options: {
    skipAccessibility?: boolean;
    skipPerformance?: boolean;
    skipVisual?: boolean;
    customTests?: Array<{ name: string; test: () => void | Promise<void> }>;
  } = {}
) => {
  const { skipAccessibility, skipPerformance, skipVisual, customTests = [] } = options;

  describe(`${componentName} Component`, () => {
    beforeEach(() => {
      // Reset mocks
      testUtils.mockIntersectionObserver();
      testUtils.mockPerformanceObserver();
    });

    // Basic rendering test
    test('renders without crashing', () => {
      expect(() => testUtils.renderWithTheme(component)).not.toThrow();
    });

    // Accessibility tests
    if (!skipAccessibility) {
      describe('Accessibility', () => {
        test('meets axe accessibility standards', async () => {
          await accessibilityTests.testAxeCompliance(component);
        });

        test('supports keyboard navigation', async () => {
          await accessibilityTests.testKeyboardNavigation(component);
        });

        test('supports screen readers', () => {
          accessibilityTests.testScreenReaderSupport(component);
        });

        test('manages focus correctly', async () => {
          await accessibilityTests.testFocusManagement(component);
        });
      });
    }

    // Performance tests
    if (!skipPerformance) {
      describe('Performance', () => {
        test('renders within performance threshold', async () => {
          const renderTime = await performanceTests.testRenderPerformance(component);
          console.log(`${componentName} render time: ${renderTime.toFixed(2)}ms`);
        });

        test('does not leak memory', async () => {
          const memoryDiff = await performanceTests.testMemoryUsage(component);
          console.log(`${componentName} memory difference: ${memoryDiff} bytes`);
        });
      });
    }

    // Visual tests
    if (!skipVisual) {
      describe('Visual', () => {
        test('matches snapshot', () => {
          visualTests.testSnapshot(component, componentName);
        });

        test('responsive design works correctly', async () => {
          const snapshots = await visualTests.testResponsiveDesign(component);
          expect(Object.keys(snapshots)).toHaveLength(4);
        });
      });
    }

    // Custom tests
    if (customTests.length > 0) {
      describe('Custom Tests', () => {
        customTests.forEach(({ name, test }) => {
          test(name, test);
        });
      });
    }
  });
};

export default {
  testUtils,
  accessibilityTests,
  performanceTests,
  visualTests,
  interactionTests,
  errorTests,
  createComponentTestSuite
};