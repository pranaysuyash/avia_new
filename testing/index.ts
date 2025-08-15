/**
 * Testing Module
 * Comprehensive testing utilities for all platforms
 * 
 * @fileoverview Complete testing toolkit for React, React Native, Electron, and Streamlit
 * @version 1.0.0
 */

// Component testing utilities
export {
  testUtils,
  accessibilityTests,
  performanceTests,
  visualTests,
  interactionTests,
  errorTests,
  createComponentTestSuite
} from './component-tests';

// Cross-platform testing utilities
export {
  platformDetection,
  crossPlatformTests,
  platformMocks,
  crossPlatformPerformance,
  crossPlatformAccessibility,
  createCrossPlatformTestSuite
} from './cross-platform-tests';

// Re-export defaults
export { default as componentTesting } from './component-tests';
export { default as crossPlatformTesting } from './cross-platform-tests';

/**
 * Quick Start Guide:
 * 
 * 1. Basic Component Testing:
 * ```typescript
 * import { createComponentTestSuite } from './testing';
 * 
 * createComponentTestSuite('MyComponent', <MyComponent />, {
 *   customTests: [
 *     {
 *       name: 'handles user interaction',
 *       test: async () => {
 *         // Custom test implementation
 *       }
 *     }
 *   ]
 * });
 * ```
 * 
 * 2. Cross-Platform Testing:
 * ```typescript
 * import { createCrossPlatformTestSuite } from './testing';
 * 
 * createCrossPlatformTestSuite('UnifiedButton', {
 *   web: <UnifiedButton>Click me</UnifiedButton>,
 *   mobile: <UnifiedButton.Native>Click me</UnifiedButton.Native>,
 *   electron: <UnifiedButton.Electron>Click me</UnifiedButton.Electron>
 * });
 * ```
 * 
 * 3. Accessibility Testing:
 * ```typescript
 * import { accessibilityTests } from './testing';
 * 
 * describe('MyComponent Accessibility', () => {
 *   test('meets WCAG standards', async () => {
 *     await accessibilityTests.testAxeCompliance(<MyComponent />);
 *   });
 * 
 *   test('supports keyboard navigation', async () => {
 *     await accessibilityTests.testKeyboardNavigation(<MyComponent />);
 *   });
 * });
 * ```
 * 
 * 4. Performance Testing:
 * ```typescript
 * import { performanceTests } from './testing';
 * 
 * describe('MyComponent Performance', () => {
 *   test('renders quickly', async () => {
 *     const renderTime = await performanceTests.testRenderPerformance(<MyComponent />);
 *     expect(renderTime).toBeLessThan(16); // 60fps threshold
 *   });
 * });
 * ```
 * 
 * 5. Platform Detection:
 * ```typescript
 * import { platformDetection } from './testing';
 * 
 * const platform = platformDetection.getCurrentPlatform();
 * const capabilities = platformDetection.getPlatformCapabilities();
 * 
 * if (capabilities.hasCamera) {
 *   // Test camera functionality
 * }
 * ```
 */

/**
 * Testing Best Practices:
 * 
 * 🧪 **Test Strategy**
 * - Unit tests for individual components
 * - Integration tests for component interactions
 * - E2E tests for complete user workflows
 * - Visual regression tests for UI consistency
 * 
 * ♿ **Accessibility Testing**
 * - Use automated tools (axe-core) for baseline checks
 * - Manual testing with screen readers
 * - Keyboard navigation testing
 * - Color contrast validation
 * 
 * 📱 **Cross-Platform Testing**
 * - Test responsive design at multiple breakpoints
 * - Verify touch vs mouse interactions
 * - Platform-specific feature testing
 * - Performance across different devices
 * 
 * ⚡ **Performance Testing**
 * - Render performance (< 16ms for 60fps)
 * - Memory leak detection
 * - Bundle size monitoring
 * - Core Web Vitals compliance
 * 
 * 🎨 **Visual Testing**
 * - Snapshot testing for regression detection
 * - Theme variation testing
 * - Component state testing
 * - Error boundary testing
 */

/**
 * Test Configuration Examples:
 * 
 * ```typescript
 * // jest.config.js
 * module.exports = {
 *   setupFilesAfterEnv: ['<rootDir>/src/testing/setup.ts'],
 *   testEnvironment: 'jsdom',
 *   moduleNameMapping: {
 *     '^@/(.*)$': '<rootDir>/src/$1'
 *   },
 *   collectCoverageFrom: [
 *     'src/components/**/*.{ts,tsx}',
 *     '!src/components/**/*.stories.{ts,tsx}',
 *     '!src/components/**/*.test.{ts,tsx}'
 *   ],
 *   coverageThreshold: {
 *     global: {
 *       branches: 80,
 *       functions: 80,
 *       lines: 80,
 *       statements: 80
 *     }
 *   }
 * };
 * 
 * // setup.ts
 * import '@testing-library/jest-dom';
 * import { expect } from '@jest/globals';
 * import { accessibilityMatchers } from './accessibility/accessibility-test';
 * 
 * // Extend Jest matchers
 * expect.extend(accessibilityMatchers);
 * 
 * // Global test setup
 * beforeEach(() => {
 *   // Reset mocks
 *   jest.clearAllMocks();
 * });
 * ```
 * 
 * ```typescript
 * // Component test example
 * import { createComponentTestSuite, testUtils } from '@/testing';
 * 
 * describe('FileUpload Component', () => {
 *   createComponentTestSuite('FileUpload', <FileUpload />, {
 *     customTests: [
 *       {
 *         name: 'handles file selection',
 *         test: async () => {
 *           const { user } = testUtils.renderWithUser(<FileUpload />);
 *           const input = screen.getByLabelText(/upload/i);
 *           
 *           const file = new File(['content'], 'test.txt', { type: 'text/plain' });
 *           await user.upload(input, file);
 *           
 *           expect(screen.getByText('test.txt')).toBeInTheDocument();
 *         }
 *       },
 *       {
 *         name: 'validates file types',
 *         test: async () => {
 *           const { user } = testUtils.renderWithUser(
 *             <FileUpload accept="image/*" />
 *           );
 *           
 *           const input = screen.getByLabelText(/upload/i);
 *           const file = new File(['content'], 'test.txt', { type: 'text/plain' });
 *           
 *           await user.upload(input, file);
 *           
 *           expect(screen.getByText(/file type not accepted/i)).toBeInTheDocument();
 *         }
 *       }
 *     ]
 *   });
 * });
 * ```
 */

/**
 * CI/CD Integration:
 * 
 * ```yaml
 * # .github/workflows/test.yml
 * name: Tests
 * 
 * on: [push, pull_request]
 * 
 * jobs:
 *   test:
 *     runs-on: ubuntu-latest
 *     
 *     steps:
 *       - uses: actions/checkout@v3
 *       - uses: actions/setup-node@v3
 *         with:
 *           node-version: '18'
 *           cache: 'npm'
 *       
 *       - run: npm ci
 *       - run: npm run test:unit
 *       - run: npm run test:accessibility
 *       - run: npm run test:performance
 *       - run: npm run test:e2e
 *       
 *       - name: Upload coverage reports
 *         uses: codecov/codecov-action@v3
 * ```
 */