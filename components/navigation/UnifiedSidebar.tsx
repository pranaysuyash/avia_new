/**
 * Unified Sidebar Component
 * Accessible, collapsible sidebar navigation
 * Follows WCAG 2.1 AA guidelines and unified design system
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiHome,
  FiFileText,
  FiUpload,
  FiBarChart3,
  FiSettings,
  FiHelpCircle,
  FiUsers,
  FiFolder,
  FiStar,
  FiClock,
  FiChevronDown,
  FiChevronRight,
  FiChevronLeft,
  FiX,
  FiMenu,
  FiSearch
} from 'react-icons/fi';
import { ThemeProvider } from '../../shared/theme';

// Interfaces
interface SidebarItem {
  id: string;
  label: string;
  href?: string;
  icon?: React.ComponentType<{ className?: string }>;
  onClick?: () => void;
  children?: SidebarItem[];
  badge?: string | number;
  disabled?: boolean;
  active?: boolean;
  category?: string;
}

interface SidebarCategory {
  id: string;
  label: string;
  items: SidebarItem[];
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

interface SidebarProps {
  items?: SidebarItem[];
  categories?: SidebarCategory[];
  collapsed?: boolean;
  onCollapseToggle?: (collapsed: boolean) => void;
  position?: 'left' | 'right';
  variant?: 'fixed' | 'overlay' | 'push';
  resizable?: boolean;
  searchEnabled?: boolean;
  onSearch?: (query: string) => void;
  currentPath?: string;
  className?: string;
  width?: number;
  minWidth?: number;
  maxWidth?: number;
}

// Default navigation items
const defaultItems: SidebarItem[] = [
  {
    id: 'home',
    label: 'Home',
    href: '/',
    icon: FiHome,
    active: true
  },
  {
    id: 'transcriptions',
    label: 'Transcriptions',
    icon: FiFileText,
    children: [
      { id: 'recent', label: 'Recent', href: '/transcriptions/recent', icon: FiClock },
      { id: 'starred', label: 'Starred', href: '/transcriptions/starred', icon: FiStar },
      { id: 'archived', label: 'Archived', href: '/transcriptions/archived', icon: FiFolder }
    ]
  },
  {
    id: 'upload',
    label: 'Upload',
    href: '/upload',
    icon: FiUpload,
    badge: 'New'
  },
  {
    id: 'analytics',
    label: 'Analytics',
    href: '/analytics',
    icon: FiBarChart3
  },
  {
    id: 'team',
    label: 'Team',
    href: '/team',
    icon: FiUsers
  },
  {
    id: 'settings',
    label: 'Settings',
    href: '/settings',
    icon: FiSettings
  },
  {
    id: 'help',
    label: 'Help & Support',
    href: '/help',
    icon: FiHelpCircle
  }
];

// Accessibility helpers
const announceToScreenReader = (message: string) => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  document.body.appendChild(announcement);
  
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

export const UnifiedSidebar: React.FC<SidebarProps> = ({
  items = defaultItems,
  categories,
  collapsed = false,
  onCollapseToggle,
  position = 'left',
  variant = 'fixed',
  resizable = false,
  searchEnabled = true,
  onSearch,
  currentPath = '/',
  className = '',
  width = 256,
  minWidth = 200,
  maxWidth = 400
}) => {
  // State management
  const [isCollapsed, setIsCollapsed] = useState(collapsed);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredItems, setFilteredItems] = useState(items);
  const [currentWidth, setCurrentWidth] = useState(width);
  const [isResizing, setIsResizing] = useState(false);
  
  // Refs
  const sidebarRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const resizeHandleRef = useRef<HTMLDivElement>(null);
  
  // Theme
  const theme = ThemeProvider.web;
  const prefersReducedMotion = ThemeProvider.prefersReducedMotion();
  
  // Handle collapse toggle
  const handleCollapseToggle = useCallback(() => {
    const newCollapsed = !isCollapsed;
    setIsCollapsed(newCollapsed);
    onCollapseToggle?.(newCollapsed);
    announceToScreenReader(newCollapsed ? 'Sidebar collapsed' : 'Sidebar expanded');
  }, [isCollapsed, onCollapseToggle]);
  
  // Handle item expansion
  const toggleItemExpansion = useCallback((itemId: string) => {
    setExpandedItems(prev => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(itemId)) {
        newExpanded.delete(itemId);
      } else {
        newExpanded.add(itemId);
      }
      
      const item = items.find(i => i.id === itemId);
      announceToScreenReader(
        `${item?.label} ${newExpanded.has(itemId) ? 'expanded' : 'collapsed'}`
      );
      
      return newExpanded;
    });
  }, [items]);
  
  // Handle search
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    
    if (!query.trim()) {
      setFilteredItems(items);
      return;
    }
    
    const filterItems = (itemList: SidebarItem[]): SidebarItem[] => {
      return itemList.filter(item => {
        const matchesQuery = item.label.toLowerCase().includes(query.toLowerCase());
        const hasMatchingChildren = item.children && 
          filterItems(item.children).length > 0;
        
        return matchesQuery || hasMatchingChildren;
      }).map(item => ({
        ...item,
        children: item.children ? filterItems(item.children) : undefined
      }));
    };
    
    const filtered = filterItems(items);
    setFilteredItems(filtered);
    onSearch?.(query);
    
    // Auto-expand items with matching children
    filtered.forEach(item => {
      if (item.children && item.children.length > 0) {
        setExpandedItems(prev => new Set([...prev, item.id]));
      }
    });
  }, [items, onSearch]);
  
  // Handle resize
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    if (!resizable) return;
    
    setIsResizing(true);
    const startX = e.clientX;
    const startWidth = currentWidth;
    
    const handleMouseMove = (e: MouseEvent) => {
      const diff = position === 'left' ? e.clientX - startX : startX - e.clientX;
      const newWidth = Math.min(Math.max(startWidth + diff, minWidth), maxWidth);
      setCurrentWidth(newWidth);
    };
    
    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [resizable, currentWidth, minWidth, maxWidth, position]);
  
  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const focusableElements = sidebarRef.current?.querySelectorAll(
      'a, button, input, [tabindex]:not([tabindex="-1"])'
    );
    
    if (!focusableElements) return;
    
    const currentElement = document.activeElement;
    const currentIndex = Array.from(focusableElements).indexOf(currentElement as HTMLElement);
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        const nextIndex = (currentIndex + 1) % focusableElements.length;
        (focusableElements[nextIndex] as HTMLElement).focus();
        break;
      case 'ArrowUp':
        e.preventDefault();
        const prevIndex = currentIndex === 0 ? focusableElements.length - 1 : currentIndex - 1;
        (focusableElements[prevIndex] as HTMLElement).focus();
        break;
      case '/':
        if (searchEnabled && e.ctrlKey) {
          e.preventDefault();
          searchInputRef.current?.focus();
        }
        break;
      case 'Escape':
        if (variant === 'overlay') {
          handleCollapseToggle();
        }
        break;
    }
  }, [searchEnabled, variant, handleCollapseToggle]);
  
  // Auto-expand items based on current path
  useEffect(() => {
    items.forEach(item => {
      if (item.children) {
        const hasActiveChild = item.children.some(child => 
          child.href === currentPath || child.active
        );
        if (hasActiveChild) {
          setExpandedItems(prev => new Set([...prev, item.id]));
        }
      }
    });
  }, [currentPath, items]);
  
  // Initialize filtered items
  useEffect(() => {
    setFilteredItems(items);
  }, [items]);
  
  // Render sidebar item
  const renderSidebarItem = (item: SidebarItem, level = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.has(item.id);
    const isActive = item.active || item.href === currentPath;
    const indent = level * (isCollapsed ? 0 : 16);
    
    const itemContent = (
      <>
        {item.icon && (
          <item.icon 
            className={`
              ${isCollapsed ? 'h-5 w-5' : 'h-4 w-4 mr-3'}
              ${isActive ? 'text-primary-DEFAULT' : 'text-text-secondary group-hover:text-primary-DEFAULT'}
              transition-colors duration-200
            `}
            aria-hidden="true"
          />
        )}
        {!isCollapsed && (
          <>
            <span className={`
              flex-1 text-sm font-medium truncate
              ${isActive ? 'text-primary-DEFAULT' : 'text-text-primary group-hover:text-primary-DEFAULT'}
              transition-colors duration-200
            `}>
              {item.label}
            </span>
            {item.badge && (
              <span 
                className="ml-2 px-2 py-1 text-xs bg-primary-DEFAULT text-primary-contrast rounded-full"
                aria-label={`${item.badge} notifications`}
              >
                {item.badge}
              </span>
            )}
            {hasChildren && (
              <div className="ml-2">
                {isExpanded ? (
                  <FiChevronDown className="h-4 w-4 text-text-secondary" aria-hidden="true" />
                ) : (
                  <FiChevronRight className="h-4 w-4 text-text-secondary" aria-hidden="true" />
                )}
              </div>
            )}
          </>
        )}
      </>
    );
    
    const itemClass = `
      group flex items-center w-full px-3 py-2 text-left rounded-md transition-all duration-200
      ${isActive 
        ? 'bg-primary-DEFAULT/10 text-primary-DEFAULT border-r-2 border-primary-DEFAULT' 
        : 'hover:bg-interactive-hover'
      }
      ${item.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2
      ${isCollapsed ? 'justify-center' : ''}
    `;
    
    const handleItemClick = () => {
      if (item.disabled) return;
      
      if (hasChildren) {
        toggleItemExpansion(item.id);
      } else {
        item.onClick?.();
      }
    };
    
    return (
      <div key={item.id} style={{ marginLeft: indent }}>
        {item.href && !hasChildren ? (
          <a
            href={item.href}
            onClick={item.onClick}
            className={itemClass}
            aria-current={isActive ? 'page' : undefined}
            aria-disabled={item.disabled}
            title={isCollapsed ? item.label : undefined}
          >
            {itemContent}
          </a>
        ) : (
          <button
            onClick={handleItemClick}
            className={itemClass}
            aria-expanded={hasChildren ? isExpanded : undefined}
            aria-disabled={item.disabled}
            title={isCollapsed ? item.label : undefined}
          >
            {itemContent}
          </button>
        )}
        
        {/* Children */}
        {hasChildren && !isCollapsed && (
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={prefersReducedMotion ? {} : { opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={prefersReducedMotion ? {} : { opacity: 0, height: 0 }}
                className="ml-4 mt-1 space-y-1"
              >
                {item.children?.map(child => renderSidebarItem(child, level + 1))}
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>
    );
  };
  
  // Render category section
  const renderCategory = (category: SidebarCategory) => {
    const [isCategoryExpanded, setIsCategoryExpanded] = useState(
      category.defaultExpanded ?? true
    );
    
    return (
      <div key={category.id} className="mb-6">
        {!isCollapsed && (
          <div className="px-3 mb-2">
            {category.collapsible ? (
              <button
                onClick={() => setIsCategoryExpanded(!isCategoryExpanded)}
                className="w-full flex items-center justify-between text-xs font-semibold text-text-tertiary uppercase tracking-wider hover:text-text-secondary transition-colors duration-200"
                aria-expanded={isCategoryExpanded}
              >
                {category.label}
                {isCategoryExpanded ? (
                  <FiChevronDown className="h-3 w-3" />
                ) : (
                  <FiChevronRight className="h-3 w-3" />
                )}
              </button>
            ) : (
              <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                {category.label}
              </h3>
            )}
          </div>
        )}
        
        <AnimatePresence>
          {(isCategoryExpanded || isCollapsed) && (
            <motion.div
              initial={prefersReducedMotion ? {} : { opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={prefersReducedMotion ? {} : { opacity: 0, height: 0 }}
              className="space-y-1"
            >
              {category.items.map(item => renderSidebarItem(item))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };
  
  return (
    <>
      {/* Overlay backdrop for mobile */}
      {variant === 'overlay' && !isCollapsed && (
        <div
          className="fixed inset-0 bg-background-overlay z-20 md:hidden"
          onClick={handleCollapseToggle}
          aria-hidden="true"
        />
      )}
      
      {/* Sidebar */}
      <motion.aside
        ref={sidebarRef}
        initial={false}
        animate={{
          width: isCollapsed ? 64 : currentWidth,
          x: variant === 'overlay' && isCollapsed ? (position === 'left' ? -currentWidth : currentWidth) : 0
        }}
        transition={{ duration: prefersReducedMotion ? 0 : 0.3, ease: 'easeInOut' }}
        className={`
          ${variant === 'fixed' ? 'relative' : 'fixed'}
          ${variant === 'overlay' ? 'z-30' : 'z-10'}
          ${position === 'right' ? 'right-0' : 'left-0'}
          h-full bg-background-primary border-r border-border-DEFAULT
          flex flex-col overflow-hidden
          ${className}
        `}
        role="navigation"
        aria-label="Main navigation"
        onKeyDown={handleKeyDown}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-border-DEFAULT">
          {!isCollapsed && searchEnabled && (
            <div className="flex-1 mr-2">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
                  <FiSearch className="h-4 w-4 text-text-tertiary" aria-hidden="true" />
                </div>
                <input
                  ref={searchInputRef}
                  type="search"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="
                    w-full pl-8 pr-3 py-1.5 text-sm border border-border-DEFAULT rounded-md
                    bg-background-secondary text-text-primary placeholder-text-tertiary
                    focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT
                    transition-colors duration-200
                  "
                  aria-label="Search navigation"
                  aria-describedby="search-hint"
                />
                <div id="search-hint" className="sr-only">
                  Press Ctrl+/ to focus search
                </div>
              </div>
            </div>
          )}
          
          <button
            onClick={handleCollapseToggle}
            className="p-1.5 text-text-secondary hover:text-text-primary hover:bg-interactive-hover rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {variant === 'overlay' && !isCollapsed ? (
              <FiX className="h-4 w-4" />
            ) : isCollapsed ? (
              <FiChevronRight className="h-4 w-4" />
            ) : (
              <FiChevronLeft className="h-4 w-4" />
            )}
          </button>
        </div>
        
        {/* Navigation Content */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {categories ? (
            categories.map(renderCategory)
          ) : (
            filteredItems.map(item => renderSidebarItem(item))
          )}
          
          {searchQuery && filteredItems.length === 0 && (
            <div className="px-3 py-6 text-center">
              <FiSearch className="h-8 w-8 text-text-tertiary mx-auto mb-2" />
              <p className="text-sm text-text-secondary">
                No results found for "{searchQuery}"
              </p>
            </div>
          )}
        </div>
        
        {/* Resize Handle */}
        {resizable && !isCollapsed && (
          <div
            ref={resizeHandleRef}
            className={`
              absolute top-0 ${position === 'left' ? 'right-0' : 'left-0'} bottom-0 w-1
              cursor-col-resize hover:bg-primary-DEFAULT/20 transition-colors duration-200
              ${isResizing ? 'bg-primary-DEFAULT/40' : ''}
            `}
            onMouseDown={handleResizeStart}
            aria-label="Resize sidebar"
            role="separator"
            aria-orientation="vertical"
          />
        )}
      </motion.aside>
    </>
  );
};

export default UnifiedSidebar;