/**
 * Unified Navigation Components
 * Cross-platform accessible navigation components
 * 
 * @fileoverview Exports unified navigation components for all platforms
 * @version 1.0.0
 */

// Core navigation components
export { UnifiedHeader } from './UnifiedHeader';
export { UnifiedSidebar } from './UnifiedSidebar';
export { UnifiedBreadcrumbs, AutoBreadcrumbs, StructuredBreadcrumbs } from './UnifiedBreadcrumbs';

// Export types and interfaces
export type {
  NavigationItem,
  User,
  HeaderProps
} from './UnifiedHeader';

export type {
  SidebarItem,
  SidebarCategory,
  SidebarProps
} from './UnifiedSidebar';

export type {
  BreadcrumbItem,
  BreadcrumbsProps
} from './UnifiedBreadcrumbs';

/**
 * Component Usage Examples:
 * 
 * Header:
 * ```tsx
 * import { UnifiedHeader } from './components/navigation';
 * 
 * <UnifiedHeader
 *   user={currentUser}
 *   navigation={navigationItems}
 *   logo={{ text: 'My App', href: '/' }}
 *   searchEnabled={true}
 *   onLogout={handleLogout}
 * />
 * ```
 * 
 * Sidebar:
 * ```tsx
 * import { UnifiedSidebar } from './components/navigation';
 * 
 * <UnifiedSidebar
 *   items={sidebarItems}
 *   collapsed={isCollapsed}
 *   onCollapseToggle={setIsCollapsed}
 *   resizable={true}
 *   currentPath={location.pathname}
 * />
 * ```
 * 
 * Breadcrumbs:
 * ```tsx
 * import { AutoBreadcrumbs } from './components/navigation';
 * 
 * <AutoBreadcrumbs
 *   pathname={location.pathname}
 *   pathLabels={{
 *     '/transcriptions': 'Transcriptions',
 *     '/transcriptions/recent': 'Recent Files'
 *   }}
 * />
 * ```
 */