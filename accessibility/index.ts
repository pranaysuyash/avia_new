/**
 * Accessibility Module
 * WCAG 2.1 AA compliance utilities and testing
 * 
 * @fileoverview Complete accessibility toolkit for the platform
 * @version 1.0.0
 */

// Core accessibility utilities
export {
  WCAG_CONTRAST_RATIOS,
  TEXT_SIZES,
  hexToRgb,
  getRelativeLuminance,
  getContrastRatio,
  meetsContrastRequirement,
  validateDesignTokenContrast,
  validateAriaAttributes,
  validateKeyboardNavigation,
  focusManagement,
  screenReader,
  accessibilityTest,
  useAccessibility
} from './wcag-compliance';

// Testing utilities
export {
  accessibilityTestUtils,
  accessibilityMatchers,
  createAccessibilityTest
} from './accessibility-test';

// Re-export default
export { default as wcagCompliance } from './wcag-compliance';
export { default as accessibilityTesting } from './accessibility-test';

/**
 * Quick Start Guide:
 * 
 * 1. Color Contrast Testing:
 * ```typescript
 * import { getContrastRatio, meetsContrastRequirement } from './accessibility';
 * 
 * const ratio = getContrastRatio('#000000', '#ffffff'); // 21
 * const isAccessible = meetsContrastRequirement('#000000', '#ffffff'); // true
 * ```
 * 
 * 2. Component Testing:
 * ```typescript
 * import { accessibilityTestUtils } from './accessibility';
 * 
 * const result = await accessibilityTestUtils.runFullSuite(<MyComponent />);
 * console.log(`Accessibility Score: ${result.summary.score}%`);
 * ```
 * 
 * 3. Focus Management:
 * ```typescript
 * import { focusManagement } from './accessibility';
 * 
 * const cleanup = focusManagement.trapFocus(modalElement);
 * // ... later
 * cleanup();
 * ```
 * 
 * 4. Screen Reader Announcements:
 * ```typescript
 * import { screenReader } from './accessibility';
 * 
 * screenReader.announce('Form submitted successfully');
 * ```
 * 
 * 5. Jest Testing:
 * ```typescript
 * import { accessibilityMatchers } from './accessibility';
 * 
 * expect.extend(accessibilityMatchers);
 * 
 * test('component is accessible', async () => {
 *   await expect(<MyComponent />).toBeAccessible();
 * });
 * ```
 */

/**
 * Accessibility Guidelines Summary:
 * 
 * 🎯 **Color & Contrast**
 * - Normal text: 4.5:1 contrast ratio minimum
 * - Large text (18pt+): 3:1 contrast ratio minimum
 * - Don't rely on color alone to convey information
 * 
 * ⌨️ **Keyboard Navigation**
 * - All interactive elements must be keyboard accessible
 * - Visible focus indicators required
 * - Logical tab order
 * - Escape key should close modals/dropdowns
 * 
 * 🏷️ **Labeling & ARIA**
 * - All form inputs need accessible labels
 * - Use semantic HTML when possible
 * - Provide alternative text for images
 * - Use ARIA attributes to enhance semantics
 * 
 * 📢 **Screen Readers**
 * - Use aria-live regions for dynamic content
 * - Provide context for complex interactions
 * - Announce state changes
 * 
 * 🎮 **Focus Management**
 * - Trap focus in modals/dialogs
 * - Return focus after closing overlays
 * - Skip links for main content
 * 
 * 📱 **Mobile Accessibility**
 * - Touch targets at least 44x44px
 * - Support screen reader gestures
 * - Consider one-handed usage
 */