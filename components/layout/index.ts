/**
 * Unified Layout Components
 * Cross-platform accessible layout components
 * 
 * @fileoverview Exports unified layout components for all platforms
 * @version 1.0.0
 */

// Core layout components
export {
  UnifiedLayout,
  AppLayout,
  MarketingLayout,
  DocumentationLayout,
  DashboardLayout,
  MinimalLayout
} from './UnifiedLayout';

// Re-export navigation types for convenience
export type {
  NavigationItem,
  SidebarItem,
  SidebarCategory,
  BreadcrumbItem
} from './UnifiedLayout';

/**
 * Layout Usage Examples:
 * 
 * App Layout (Full-featured):
 * ```tsx
 * import { AppLayout } from './components/layout';
 * 
 * <AppLayout
 *   user={currentUser}
 *   navigation={mainNavigation}
 *   sidebarItems={sidebarItems}
 *   currentPath={location.pathname}
 *   logo={{ text: 'My App' }}
 * >
 *   <YourPageContent />
 * </AppLayout>
 * ```
 * 
 * Marketing Layout (Header only):
 * ```tsx
 * import { MarketingLayout } from './components/layout';
 * 
 * <MarketingLayout
 *   navigation={publicNavigation}
 *   logo={{ text: 'My App' }}
 * >
 *   <LandingPageContent />
 * </MarketingLayout>
 * ```
 * 
 * Minimal Layout (Auth pages):
 * ```tsx
 * import { MinimalLayout } from './components/layout';
 * 
 * <MinimalLayout logo={{ text: 'My App' }}>
 *   <LoginForm />
 * </MinimalLayout>
 * ```
 */