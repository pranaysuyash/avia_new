/**
 * Unified Breadcrumbs Component
 * Accessible breadcrumb navigation
 * Follows WCAG 2.1 AA guidelines and unified design system
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  FiHome,
  FiChevronRight,
  FiMoreHorizontal,
  FiFolder,
  FiFile
} from 'react-icons/fi';
import { ThemeProvider } from '../../shared/theme';

// Interfaces
interface BreadcrumbItem {
  id: string;
  label: string;
  href?: string;
  icon?: React.ComponentType<{ className?: string }>;
  onClick?: () => void;
  disabled?: boolean;
  current?: boolean;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  separator?: React.ComponentType<{ className?: string }> | string;
  maxItems?: number;
  showHome?: boolean;
  homeHref?: string;
  onHomeClick?: () => void;
  variant?: 'standard' | 'compact' | 'dropdown';
  className?: string;
}

// Default breadcrumb items
const createHomeBreadcrumb = (href: string = '/', onClick?: () => void): BreadcrumbItem => ({
  id: 'home',
  label: 'Home',
  href,
  icon: FiHome,
  onClick
});

export const UnifiedBreadcrumbs: React.FC<BreadcrumbsProps> = ({
  items,
  separator = FiChevronRight,
  maxItems = 4,
  showHome = true,
  homeHref = '/',
  onHomeClick,
  variant = 'standard',
  className = ''
}) => {
  // Theme
  const theme = ThemeProvider.web;
  const prefersReducedMotion = ThemeProvider.prefersReducedMotion();
  
  // Process breadcrumb items
  const processedItems = useMemo(() => {
    let allItems = [...items];
    
    // Add home breadcrumb if requested and not already present
    if (showHome && !allItems.some(item => item.id === 'home')) {
      allItems.unshift(createHomeBreadcrumb(homeHref, onHomeClick));
    }
    
    // Mark the last item as current if not already marked
    if (allItems.length > 0 && !allItems.some(item => item.current)) {
      allItems[allItems.length - 1] = { ...allItems[allItems.length - 1], current: true };
    }
    
    return allItems;
  }, [items, showHome, homeHref, onHomeClick]);
  
  // Handle item truncation for long breadcrumb trails
  const displayItems = useMemo(() => {
    if (processedItems.length <= maxItems) {
      return processedItems;
    }
    
    // Always show first item (home), last item (current), and truncate middle items
    const firstItem = processedItems[0];
    const lastItem = processedItems[processedItems.length - 1];
    const middleItems = processedItems.slice(1, -1);
    
    if (middleItems.length <= maxItems - 2) {
      return processedItems;
    }
    
    // Create truncated version
    const truncatedItems = [firstItem];
    
    // Add ellipsis item
    const ellipsisItem: BreadcrumbItem = {
      id: 'ellipsis',
      label: '...',
      disabled: true
    };
    truncatedItems.push(ellipsisItem);
    
    // Add last few items before current
    const remainingSlots = maxItems - 3; // first, ellipsis, current
    if (remainingSlots > 0) {
      truncatedItems.push(...middleItems.slice(-remainingSlots));
    }
    
    truncatedItems.push(lastItem);
    
    return truncatedItems;
  }, [processedItems, maxItems]);
  
  // Render separator
  const renderSeparator = (index: number) => {
    if (typeof separator === 'string') {
      return (
        <span 
          className="mx-2 text-text-tertiary select-none" 
          aria-hidden="true"
          key={`separator-${index}`}
        >
          {separator}
        </span>
      );
    }
    
    const SeparatorIcon = separator;
    return (
      <SeparatorIcon 
        className="mx-2 h-4 w-4 text-text-tertiary" 
        aria-hidden="true"
        key={`separator-${index}`}
      />
    );
  };
  
  // Render breadcrumb item
  const renderBreadcrumbItem = (item: BreadcrumbItem, index: number, isLast: boolean) => {
    const itemContent = (
      <span className="flex items-center">
        {item.icon && (
          <item.icon 
            className="h-4 w-4 mr-1.5 flex-shrink-0" 
            aria-hidden="true"
          />
        )}
        <span className={`
          ${variant === 'compact' ? 'text-sm' : 'text-sm sm:text-base'}
          ${isLast ? 'font-medium' : 'font-normal'}
          truncate
        `}>
          {item.label}
        </span>
      </span>
    );
    
    const baseClasses = `
      inline-flex items-center transition-colors duration-200 rounded-md
      focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-1
      ${variant === 'compact' ? 'px-1 py-0.5' : 'px-2 py-1'}
    `;
    
    if (item.current || isLast) {
      return (
        <span
          key={item.id}
          className={`
            ${baseClasses}
            text-text-primary cursor-default
          `}
          aria-current="page"
          role="listitem"
        >
          {itemContent}
        </span>
      );
    }
    
    if (item.disabled) {
      return (
        <span
          key={item.id}
          className={`
            ${baseClasses}
            text-text-tertiary cursor-not-allowed
          `}
          aria-disabled="true"
          role="listitem"
        >
          {itemContent}
        </span>
      );
    }
    
    if (item.href) {
      return (
        <a
          key={item.id}
          href={item.href}
          onClick={item.onClick}
          className={`
            ${baseClasses}
            text-text-secondary hover:text-primary-DEFAULT hover:bg-interactive-hover
          `}
          role="listitem"
        >
          {itemContent}
        </a>
      );
    }
    
    return (
      <button
        key={item.id}
        onClick={item.onClick}
        className={`
          ${baseClasses}
          text-text-secondary hover:text-primary-DEFAULT hover:bg-interactive-hover
        `}
        role="listitem"
      >
        {itemContent}
      </button>
    );
  };
  
  // Render dropdown variant (for mobile/compact spaces)
  const renderDropdownVariant = () => {
    const currentItem = displayItems[displayItems.length - 1];
    
    return (
      <div className="relative inline-block">
        <button
          className="flex items-center space-x-1 px-3 py-2 text-sm bg-background-secondary border border-border-DEFAULT rounded-md hover:bg-interactive-hover focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT transition-colors duration-200"
          aria-label="Show breadcrumb navigation"
          aria-haspopup="true"
        >
          <FiMoreHorizontal className="h-4 w-4 text-text-secondary" />
          <span className="text-text-primary">{currentItem.label}</span>
        </button>
        
        {/* Dropdown menu would be implemented here */}
      </div>
    );
  };
  
  if (variant === 'dropdown') {
    return (
      <nav 
        aria-label="Breadcrumb" 
        className={`flex items-center ${className}`}
        role="navigation"
      >
        {renderDropdownVariant()}
      </nav>
    );
  }
  
  return (
    <nav 
      aria-label="Breadcrumb" 
      className={`flex items-center ${className}`}
      role="navigation"
    >
      <ol className="flex items-center space-x-0" role="list">
        {displayItems.map((item, index) => {
          const isLast = index === displayItems.length - 1;
          
          return (
            <li key={item.id} className="flex items-center">
              <motion.div
                initial={prefersReducedMotion ? {} : { opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1, duration: 0.2 }}
                className="flex items-center"
              >
                {renderBreadcrumbItem(item, index, isLast)}
                {!isLast && renderSeparator(index)}
              </motion.div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

// Enhanced breadcrumb with auto-generation from URL
interface AutoBreadcrumbsProps extends Omit<BreadcrumbsProps, 'items'> {
  pathname: string;
  pathLabels?: Record<string, string>;
  pathIcons?: Record<string, React.ComponentType<{ className?: string }>>;
  excludePaths?: string[];
}

export const AutoBreadcrumbs: React.FC<AutoBreadcrumbsProps> = ({
  pathname,
  pathLabels = {},
  pathIcons = {},
  excludePaths = [],
  ...breadcrumbProps
}) => {
  const items = useMemo(() => {
    const segments = pathname.split('/').filter(Boolean);
    const breadcrumbItems: BreadcrumbItem[] = [];
    
    segments.forEach((segment, index) => {
      const path = '/' + segments.slice(0, index + 1).join('/');
      
      // Skip excluded paths
      if (excludePaths.includes(path)) {
        return;
      }
      
      // Generate label
      const label = pathLabels[path] || pathLabels[segment] || 
                    segment.replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      
      // Get icon
      const icon = pathIcons[path] || pathIcons[segment] || 
                   (index === segments.length - 1 ? FiFile : FiFolder);
      
      breadcrumbItems.push({
        id: path,
        label,
        href: path,
        icon,
        current: index === segments.length - 1
      });
    });
    
    return breadcrumbItems;
  }, [pathname, pathLabels, pathIcons, excludePaths]);
  
  return <UnifiedBreadcrumbs items={items} {...breadcrumbProps} />;
};

// Structured data breadcrumbs for SEO
export const StructuredBreadcrumbs: React.FC<BreadcrumbsProps & { baseUrl?: string }> = ({
  items,
  baseUrl = '',
  ...props
}) => {
  const structuredData = useMemo(() => {
    const itemListElement = items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.label,
      item: item.href ? `${baseUrl}${item.href}` : undefined
    }));
    
    return {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement
    };
  }, [items, baseUrl]);
  
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <UnifiedBreadcrumbs items={items} {...props} />
    </>
  );
};

export default UnifiedBreadcrumbs;