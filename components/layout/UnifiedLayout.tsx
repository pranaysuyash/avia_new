/**
 * Unified Layout Component
 * Accessible, responsive layout container
 * Follows WCAG 2.1 AA guidelines and unified design system
 */

import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeProvider } from '../../shared/theme';
import { UnifiedHeader } from '../navigation/UnifiedHeader';
import { UnifiedSidebar } from '../navigation/UnifiedSidebar';
import { UnifiedBreadcrumbs, AutoBreadcrumbs } from '../navigation/UnifiedBreadcrumbs';

// Re-export navigation interfaces for convenience
export type { NavigationItem } from '../navigation/UnifiedHeader';
export type { SidebarItem, SidebarCategory } from '../navigation/UnifiedSidebar';
export type { BreadcrumbItem } from '../navigation/UnifiedBreadcrumbs';

// Layout interfaces
interface LayoutProps {
  children: React.ReactNode;
  
  // Header props
  user?: any;
  navigation?: any[];
  logo?: {
    src?: string;
    alt?: string;
    text?: string;
    href?: string;
  };
  
  // Sidebar props
  sidebarItems?: any[];
  sidebarCategories?: any[];
  sidebarCollapsed?: boolean;
  onSidebarCollapseToggle?: (collapsed: boolean) => void;
  
  // Breadcrumb props
  breadcrumbs?: any[];
  currentPath?: string;
  showBreadcrumbs?: boolean;
  autoBreadcrumbs?: boolean;
  pathLabels?: Record<string, string>;
  
  // Layout configuration
  layout?: 'default' | 'sidebar-only' | 'header-only' | 'minimal';
  variant?: 'app' | 'marketing' | 'documentation' | 'dashboard';
  stickyHeader?: boolean;
  resizableSidebar?: boolean;
  
  // Responsive behavior
  mobileBreakpoint?: number;
  hideSidebarOnMobile?: boolean;
  
  // Accessibility
  skipToMainId?: string;
  mainLandmarkLabel?: string;
  
  // Styling
  className?: string;
  headerClassName?: string;
  sidebarClassName?: string;
  mainClassName?: string;
  contentClassName?: string;
}

interface SkipLinkProps {
  targetId: string;
  className?: string;
}

// Skip to main content link for accessibility
const SkipLink: React.FC<SkipLinkProps> = ({ targetId, className = '' }) => {
  const handleSkip = (e: React.MouseEvent) => {
    e.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };
  
  return (
    <a
      href={`#${targetId}`}
      onClick={handleSkip}
      className={`
        sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50
        px-4 py-2 bg-primary-DEFAULT text-primary-contrast rounded-md
        font-medium text-sm shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-DEFAULT
        ${className}
      `}
    >
      Skip to main content
    </a>
  );
};

export const UnifiedLayout: React.FC<LayoutProps> = ({
  children,
  
  // Header props
  user,
  navigation,
  logo = { text: 'NER Platform', href: '/' },
  
  // Sidebar props
  sidebarItems,
  sidebarCategories,
  sidebarCollapsed: initialSidebarCollapsed = false,
  onSidebarCollapseToggle,
  
  // Breadcrumb props
  breadcrumbs,
  currentPath = '/',
  showBreadcrumbs = true,
  autoBreadcrumbs = true,
  pathLabels,
  
  // Layout configuration
  layout = 'default',
  variant = 'app',
  stickyHeader = true,
  resizableSidebar = false,
  
  // Responsive behavior
  mobileBreakpoint = 768,
  hideSidebarOnMobile = true,
  
  // Accessibility
  skipToMainId = 'main-content',
  mainLandmarkLabel = 'Main content',
  
  // Styling
  className = '',
  headerClassName = '',
  sidebarClassName = '',
  mainClassName = '',
  contentClassName = ''
}) => {
  // State
  const [sidebarCollapsed, setSidebarCollapsed] = useState(initialSidebarCollapsed);
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(256);
  
  // Theme
  const theme = ThemeProvider.web;
  const prefersReducedMotion = ThemeProvider.prefersReducedMotion();
  
  // Handle sidebar collapse
  const handleSidebarToggle = useCallback((collapsed: boolean) => {
    setSidebarCollapsed(collapsed);
    onSidebarCollapseToggle?.(collapsed);
  }, [onSidebarCollapseToggle]);
  
  // Handle responsive behavior
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < mobileBreakpoint;
      setIsMobile(mobile);
      
      if (mobile && hideSidebarOnMobile && !sidebarCollapsed) {
        setSidebarCollapsed(true);
      }
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [mobileBreakpoint, hideSidebarOnMobile, sidebarCollapsed]);
  
  // Calculate layout classes
  const shouldShowSidebar = layout === 'default' || layout === 'sidebar-only';
  const shouldShowHeader = layout === 'default' || layout === 'header-only';
  const sidebarDisplayWidth = sidebarCollapsed ? 64 : sidebarWidth;
  
  // Variant-specific styling
  const getVariantClasses = () => {
    switch (variant) {
      case 'marketing':
        return {
          container: 'bg-gradient-to-br from-background-primary to-background-secondary',
          header: 'bg-background-primary/80 backdrop-blur-sm',
          main: 'bg-background-primary'
        };
      case 'documentation':
        return {
          container: 'bg-background-secondary',
          header: 'bg-background-primary border-b border-border-DEFAULT',
          main: 'bg-background-primary'
        };
      case 'dashboard':
        return {
          container: 'bg-background-secondary',
          header: 'bg-background-primary shadow-sm',
          main: 'bg-background-secondary'
        };
      default:
        return {
          container: 'bg-background-primary',
          header: 'bg-background-primary',
          main: 'bg-background-primary'
        };
    }
  };
  
  const variantClasses = getVariantClasses();
  
  return (
    <div className={`min-h-screen flex flex-col ${variantClasses.container} ${className}`}>
      {/* Skip Link */}
      <SkipLink targetId={skipToMainId} />
      
      {/* Header */}
      {shouldShowHeader && (
        <UnifiedHeader
          user={user}
          navigation={navigation}
          logo={logo}
          sticky={stickyHeader}
          variant={variant === 'marketing' ? 'transparent' : 'full'}
          className={`${variantClasses.header} ${headerClassName}`}
          onSearch={(query) => {
            // Handle global search
            console.log('Global search:', query);
          }}
          onNotificationClick={() => {
            // Handle notifications
            console.log('Notifications clicked');
          }}
          onProfileClick={() => {
            // Handle profile
            console.log('Profile clicked');
          }}
          onLogout={() => {
            // Handle logout
            console.log('Logout clicked');
          }}
          onThemeChange={(theme) => {
            // Handle theme change
            console.log('Theme changed to:', theme);
          }}
        />
      )}
      
      {/* Main Layout Container */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        {shouldShowSidebar && (
          <UnifiedSidebar
            items={sidebarItems}
            categories={sidebarCategories}
            collapsed={sidebarCollapsed}
            onCollapseToggle={handleSidebarToggle}
            variant={isMobile ? 'overlay' : 'fixed'}
            resizable={resizableSidebar && !isMobile}
            currentPath={currentPath}
            width={sidebarWidth}
            className={sidebarClassName}
            onSearch={(query) => {
              // Handle sidebar search
              console.log('Sidebar search:', query);
            }}
          />
        )}
        
        {/* Main Content Area */}
        <main
          id={skipToMainId}
          className={`
            flex-1 flex flex-col overflow-hidden
            ${shouldShowSidebar && !isMobile ? `ml-${sidebarCollapsed ? '16' : '64'}` : ''}
            ${variantClasses.main}
            ${mainClassName}
          `}
          style={{
            marginLeft: shouldShowSidebar && !isMobile ? sidebarDisplayWidth : 0
          }}
          role="main"
          aria-label={mainLandmarkLabel}
          tabIndex={-1}
        >
          {/* Breadcrumbs */}
          {showBreadcrumbs && (breadcrumbs || autoBreadcrumbs) && (
            <div className="border-b border-border-DEFAULT bg-background-primary px-4 py-3">
              {autoBreadcrumbs ? (
                <AutoBreadcrumbs
                  pathname={currentPath}
                  pathLabels={pathLabels}
                  maxItems={4}
                  variant="standard"
                />
              ) : breadcrumbs ? (
                <UnifiedBreadcrumbs
                  items={breadcrumbs}
                  maxItems={4}
                  variant="standard"
                />
              ) : null}
            </div>
          )}
          
          {/* Page Content */}
          <div className={`flex-1 overflow-auto ${contentClassName}`}>
            <AnimatePresence mode="wait">
              <motion.div
                key={currentPath}
                initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={prefersReducedMotion ? {} : { opacity: 0, y: -20 }}
                transition={{ duration: 0.2 }}
                className="h-full"
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
};

// Specialized layout components
export const AppLayout: React.FC<Omit<LayoutProps, 'variant'>> = (props) => (
  <UnifiedLayout {...props} variant="app" />
);

export const MarketingLayout: React.FC<Omit<LayoutProps, 'variant' | 'layout'>> = (props) => (
  <UnifiedLayout {...props} variant="marketing" layout="header-only" />
);

export const DocumentationLayout: React.FC<Omit<LayoutProps, 'variant'>> = (props) => (
  <UnifiedLayout {...props} variant="documentation" />
);

export const DashboardLayout: React.FC<Omit<LayoutProps, 'variant'>> = (props) => (
  <UnifiedLayout {...props} variant="dashboard" />
);

// Minimal layout for auth pages
export const MinimalLayout: React.FC<{
  children: React.ReactNode;
  logo?: LayoutProps['logo'];
  className?: string;
}> = ({ children, logo, className = '' }) => (
  <div className={`min-h-screen flex flex-col bg-background-primary ${className}`}>
    <SkipLink targetId="main-content" />
    
    {logo && (
      <header className="p-6">
        <a
          href={logo.href || '/'}
          className="flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2 rounded"
        >
          {logo.src ? (
            <img src={logo.src} alt={logo.alt || ''} className="h-8 w-auto" />
          ) : (
            <div className="h-8 w-8 bg-primary-DEFAULT rounded flex items-center justify-center">
              <span className="text-primary-contrast font-bold text-lg">
                {logo.text?.charAt(0) || 'N'}
              </span>
            </div>
          )}
          {logo.text && (
            <span className="text-xl font-bold text-text-primary">{logo.text}</span>
          )}
        </a>
      </header>
    )}
    
    <main id="main-content" className="flex-1 flex items-center justify-center px-4" role="main" tabIndex={-1}>
      {children}
    </main>
  </div>
);

export default UnifiedLayout;