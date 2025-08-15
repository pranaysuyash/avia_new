/**
 * Unified UI Components Integration
 * Bridges the new unified components with existing React frontend
 * 
 * @fileoverview Integration layer for cross-platform UI/UX components
 * @version 1.0.0
 */

// Import new unified components (TypeScript)
export * from '../../../../components/auth';
export * from '../../../../components/navigation';
export * from '../../../../components/layout';
export * from '../../../../components/flows';
export * from '../../../../components/ui';

// Import accessibility and performance utilities
export * from '../../../../accessibility';
export * from '../../../../performance';
export * from '../../../../testing';

/**
 * Integration Guide:
 * 
 * 1. Replace existing components gradually:
 * ```tsx
 * // Old way
 * import { FileUploader } from '../upload/FileUploader';
 * 
 * // New unified way
 * import { FileUpload } from './unified';
 * 
 * // Use with same props but enhanced accessibility
 * <FileUpload 
 *   accept="audio/*,video/*"
 *   onFileSelect={handleFiles}
 *   variant="gallery"
 * />
 * ```
 * 
 * 2. Use unified layout system:
 * ```tsx
 * import { AppLayout } from './unified';
 * 
 * <AppLayout
 *   user={currentUser}
 *   navigation={navigation}
 *   sidebarItems={sidebarItems}
 *   currentPath={location.pathname}
 * >
 *   <YourContent />
 * </AppLayout>
 * ```
 * 
 * 3. Add accessibility testing:
 * ```tsx
 * import { accessibilityTestUtils } from './unified';
 * 
 * // In tests
 * const result = await accessibilityTestUtils.runFullSuite(<MyComponent />);
 * expect(result.summary.score).toBeGreaterThan(80);
 * ```
 */