/**
 * Unified Header Component
 * Accessible, responsive header with navigation
 * Follows WCAG 2.1 AA guidelines and unified design system
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiMenu,
  FiX,
  FiSearch,
  FiBell,
  FiUser,
  FiSettings,
  FiLogOut,
  FiHome,
  FiFileText,
  FiUpload,
  FiBarChart3,
  FiHelpCircle,
  FiChevronDown,
  FiMoon,
  FiSun,
  FiMonitor,
  FiActivity
} from 'react-icons/fi';
import { ThemeProvider } from '../../shared/theme';
import { logUxEvent } from '../shared/uxTelemetry';
import { ShareViewButton } from '../shared/ShareViewButton';

// Interfaces
interface NavigationItem {
  id: string;
  label: string;
  href?: string;
  icon?: React.ComponentType<{ className?: string }>;
  onClick?: () => void;
  children?: NavigationItem[];
  badge?: string | number;
  disabled?: boolean;
}

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role?: string;
}

interface HeaderProps {
  user?: User;
  navigation: NavigationItem[];
  logo?: {
    src?: string;
    alt?: string;
    text?: string;
    href?: string;
  };
  searchEnabled?: boolean;
  notificationsEnabled?: boolean;
  themeToggle?: boolean;
  onSearch?: (query: string) => void;
  onNotificationClick?: () => void;
  onProfileClick?: () => void;
  onLogout?: () => void;
  onThemeChange?: (theme: 'light' | 'dark' | 'system') => void;
  variant?: 'full' | 'minimal' | 'transparent';
  sticky?: boolean;
  className?: string;
  mainId?: string; // target for skip link (defaults to #main-content)
  showDevToolsToggle?: boolean; // adds a button to toggle dev telemetry overlay via ?dev_telemetry=1
  showShareButton?: boolean; // shows a Share button that copies the current URL
}

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

// Default navigation items
const defaultNavigation: NavigationItem[] = [
  {
    id: 'home',
    label: 'Home',
    href: '/',
    icon: FiHome
  },
  {
    id: 'transcriptions',
    label: 'Transcriptions',
    href: '/transcriptions',
    icon: FiFileText,
    children: [
      { id: 'recent', label: 'Recent', href: '/transcriptions/recent' },
      { id: 'archived', label: 'Archived', href: '/transcriptions/archived' },
      { id: 'shared', label: 'Shared', href: '/transcriptions/shared' }
    ]
  },
  {
    id: 'upload',
    label: 'Upload',
    href: '/upload',
    icon: FiUpload
  },
  {
    id: 'analytics',
    label: 'Analytics',
    href: '/analytics',
    icon: FiBarChart3
  },
  {
    id: 'help',
    label: 'Help',
    href: '/help',
    icon: FiHelpCircle
  }
];

export const UnifiedHeader: React.FC<HeaderProps> = ({
  user,
  navigation = defaultNavigation,
  logo = { text: 'NER Platform', href: '/' },
  searchEnabled = true,
  notificationsEnabled = true,
  themeToggle = true,
  onSearch,
  onNotificationClick,
  onProfileClick,
  onLogout,
  onThemeChange,
  variant = 'full',
  sticky = true,
  className = '',
  mainId = 'main-content',
  showDevToolsToggle = false,
  showShareButton = true
}) => {
  // State management
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [currentTheme, setCurrentTheme] = useState<'light' | 'dark' | 'system'>('system');
  
  // Refs
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const profileButtonRef = useRef<HTMLButtonElement>(null);
  const mobileMenuRef = useRef<HTMLDivElement>(null);
  
  // Theme
  const theme = ThemeProvider.web;
  const prefersReducedMotion = ThemeProvider.prefersReducedMotion();
  
  // Handle mobile menu toggle
  const toggleMobileMenu = useCallback(() => {
    setIsMenuOpen(prev => {
      const newState = !prev;
      announceToScreenReader(newState ? 'Menu opened' : 'Menu closed');
      
      if (newState) {
        // Focus first menu item when opening
        setTimeout(() => {
          const firstMenuItem = mobileMenuRef.current?.querySelector('a, button');
          (firstMenuItem as HTMLElement)?.focus();
        }, 100);
      } else {
        // Return focus to menu button when closing
        menuButtonRef.current?.focus();
      }
      
      return newState;
    });
  }, []);
  
  // Handle search
  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim() && onSearch) {
      onSearch(searchQuery.trim());
      announceToScreenReader(`Searching for ${searchQuery}`);
    }
  }, [searchQuery, onSearch]);
  
  // Handle dropdown toggle
  const toggleDropdown = useCallback((itemId: string) => {
    setActiveDropdown(prev => {
      const newState = prev === itemId ? null : itemId;
      if (newState) {
        announceToScreenReader(`${navigation.find(n => n.id === itemId)?.label} menu opened`);
      }
      return newState;
    });
  }, [navigation]);
  
  // Handle theme change
  const handleThemeChange = useCallback((newTheme: 'light' | 'dark' | 'system') => {
    setCurrentTheme(newTheme);
    onThemeChange?.(newTheme);
    announceToScreenReader(`Theme changed to ${newTheme}`);
  }, [onThemeChange]);
  
  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (activeDropdown && !(event.target as Element).closest('[data-dropdown]')) {
        setActiveDropdown(null);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [activeDropdown]);
  
  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Escape':
        if (isMenuOpen) {
          setIsMenuOpen(false);
          menuButtonRef.current?.focus();
        }
        if (activeDropdown) {
          setActiveDropdown(null);
        }
        break;
      case '/':
        if (searchEnabled && !isSearchFocused && e.ctrlKey) {
          e.preventDefault();
          searchInputRef.current?.focus();
          announceToScreenReader('Search focused');
        }
        break;
    }
  }, [isMenuOpen, activeDropdown, searchEnabled, isSearchFocused]);
  
  // Attach global keyboard listener
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown as any);
    return () => document.removeEventListener('keydown', handleKeyDown as any);
  }, [handleKeyDown]);
  
  // Navigation item renderer
  const renderNavigationItem = (item: NavigationItem, isMobile = false) => {
    const hasChildren = item.children && item.children.length > 0;
    const isDropdownOpen = activeDropdown === item.id;
    
    const itemContent = (
      <>
        {item.icon && (
          <item.icon 
            className={`h-5 w-5 ${isMobile ? 'mr-3' : 'mr-2'}`} 
            aria-hidden="true"
          />
        )}
        <span>{item.label}</span>
        {item.badge && (
          <span 
            className="ml-2 px-2 py-1 text-xs bg-primary-DEFAULT text-primary-contrast rounded-full"
            aria-label={`${item.badge} notifications`}
          >
            {item.badge}
          </span>
        )}
        {hasChildren && (
          <FiChevronDown 
            className={`ml-auto h-4 w-4 transition-transform duration-200 ${
              isDropdownOpen ? 'rotate-180' : ''
            }`}
            aria-hidden="true"
          />
        )}
      </>
    );
    
    if (hasChildren) {
      return (
        <div key={item.id} className="relative" data-dropdown>
          <button
            onClick={() => toggleDropdown(item.id)}
            disabled={item.disabled}
            className={`
              ${isMobile ? 'w-full text-left px-4 py-3' : 'px-3 py-2'}
              flex items-center text-sm font-medium rounded-md transition-colors duration-200
              ${item.disabled 
                ? 'text-text-tertiary cursor-not-allowed' 
                : 'text-text-primary hover:text-primary-DEFAULT hover:bg-interactive-hover'
              }
              focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2
            `}
            aria-expanded={isDropdownOpen}
            aria-haspopup="true"
            aria-label={`${item.label} menu`}
          >
            {itemContent}
          </button>
          
          <AnimatePresence>
            {isDropdownOpen && (
              <motion.div
                initial={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className={`
                  ${isMobile 
                    ? 'bg-background-secondary border-l-2 border-primary-DEFAULT ml-4' 
                    : 'absolute left-0 mt-2 w-48 bg-background-primary border border-border-DEFAULT rounded-md shadow-lg z-10'
                  }
                `}
                role="menu"
                aria-label={`${item.label} submenu`}
              >
                {item.children?.map((child) => (
                  <a
                    key={child.id}
                    href={child.href}
                    onClick={(e) => {
                      try { logUxEvent('nav_click', { id: child.id, label: child.label, href: child.href }); } catch {}
                      child.onClick?.();
                    }}
                    className={`
                      block px-4 py-2 text-sm text-text-primary hover:bg-interactive-hover hover:text-primary-DEFAULT
                      focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-inset
                      ${isMobile ? 'border-l-2 border-transparent hover:border-primary-DEFAULT' : 'first:rounded-t-md last:rounded-b-md'}
                    `}
                    role="menuitem"
                  >
                    <div className="flex items-center">
                      {child.icon && (
                        <child.icon className="h-4 w-4 mr-2" aria-hidden="true" />
                      )}
                      {child.label}
                      {child.badge && (
                        <span 
                          className="ml-auto px-2 py-1 text-xs bg-primary-DEFAULT text-primary-contrast rounded-full"
                          aria-label={`${child.badge} items`}
                        >
                          {child.badge}
                        </span>
                      )}
                    </div>
                  </a>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      );
    }
    
    return (
      <a
        key={item.id}
        href={item.href}
        onClick={(e) => {
          try { logUxEvent('nav_click', { id: item.id, label: item.label, href: item.href }); } catch {}
          item.onClick?.();
        }}
        className={`
          ${isMobile ? 'block px-4 py-3' : 'px-3 py-2'}
          flex items-center text-sm font-medium rounded-md transition-colors duration-200
          ${item.disabled 
            ? 'text-text-tertiary cursor-not-allowed' 
            : 'text-text-primary hover:text-primary-DEFAULT hover:bg-interactive-hover'
          }
          focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2
        `}
        aria-disabled={item.disabled}
      >
        {itemContent}
      </a>
    );
  };
  
  // Theme icon renderer
  const getThemeIcon = () => {
    switch (currentTheme) {
      case 'light':
        return FiSun;
      case 'dark':
        return FiMoon;
      default:
        return FiMonitor;
    }
  };
  
  const ThemeIcon = getThemeIcon();

  // Toggle dev telemetry overlay by updating query param
  const toggleDevTelemetry = useCallback(() => {
    try {
      const url = new URL(window.location.href);
      const isOn = url.searchParams.get('dev_telemetry') === '1';
      if (isOn) {
        url.searchParams.delete('dev_telemetry');
      } else {
        url.searchParams.set('dev_telemetry', '1');
      }
      window.history.replaceState({}, '', url.toString());
      // Emit an event so app shells that read this on mount can react immediately
      try { (window as any).dispatchEvent(new Event('dev_telemetry_toggle')); } catch {}
      try { logUxEvent('dev_telemetry_toggled', { enabled: !isOn }); } catch {}
    } catch {}
  }, []);
  
  return (
    <header 
      className={`
        ${sticky ? 'sticky top-0 z-40' : ''}
        ${variant === 'transparent' ? 'bg-background-overlay backdrop-blur-sm' : 'bg-background-primary'}
        border-b border-border-DEFAULT
        ${className}
      `}
      role="banner"
    >
      {/* Skip to content link for accessibility */}
      <a href={`#${mainId}`} className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 bg-primary-DEFAULT text-primary-contrast px-3 py-1 rounded">
        Skip to main content
      </a>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <a
              href={logo.href}
              className="flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2 rounded"
              aria-label={`${logo.text || logo.alt} - Go to homepage`}
            >
              {logo.src ? (
                <img
                  src={logo.src}
                  alt={logo.alt || ''}
                  className="h-8 w-auto"
                />
              ) : (
                <div className="h-8 w-8 bg-primary-DEFAULT rounded flex items-center justify-center">
                  <span className="text-primary-contrast font-bold text-lg">
                    {logo.text?.charAt(0) || 'N'}
                  </span>
                </div>
              )}
              {logo.text && (
                <span className="text-xl font-bold text-text-primary">
                  {logo.text}
                </span>
              )}
            </a>
          </div>
          
          {/* Desktop Navigation */}
          <nav 
            className="hidden md:flex space-x-1"
            role="navigation"
            aria-label="Primary navigation"
          >
            {navigation.map(renderNavigationItem)}
          </nav>
          
          {/* Right Side Actions */}
          <div className="flex items-center space-x-2">
            {/* Dev tools toggle (optional) */}
            {showDevToolsToggle && (
              <button
                onClick={toggleDevTelemetry}
                className="p-2 text-text-secondary hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded-full transition-colors duration-200"
                aria-label="Toggle developer telemetry overlay"
                title="Toggle developer telemetry overlay"
              >
                <FiActivity className="h-5 w-5" />
              </button>
            )}
            {/* Search */}
            {searchEnabled && variant !== 'minimal' && (
              <form onSubmit={handleSearch} className="hidden md:block">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <FiSearch className="h-4 w-4 text-text-tertiary" aria-hidden="true" />
                  </div>
                  <input
                    ref={searchInputRef}
                    type="search"
                    placeholder="Search... (Ctrl+/)"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onFocus={() => setIsSearchFocused(true)}
                    onBlur={() => setIsSearchFocused(false)}
                    className="
                      w-64 pl-10 pr-4 py-2 border border-border-DEFAULT rounded-md
                      bg-background-primary text-text-primary placeholder-text-tertiary
                      focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT
                      transition-colors duration-200
                    "
                    aria-label="Search"
                    aria-describedby="search-description"
                  />
                  <div id="search-description" className="sr-only">
                    Press Ctrl+/ to focus search from anywhere
                  </div>
                </div>
              </form>
            )}
            
            {/* Theme Toggle */}
            {themeToggle && (
              <div className="relative" data-dropdown>
                <button
                  onClick={() => toggleDropdown('theme')}
                  className="p-2 text-text-secondary hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded-full transition-colors duration-200"
                  aria-label="Change theme"
                  aria-expanded={activeDropdown === 'theme'}
                  aria-haspopup="true"
                >
                  <ThemeIcon className="h-5 w-5" />
                </button>
                
                <AnimatePresence>
                  {activeDropdown === 'theme' && (
                    <motion.div
                      initial={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
                      className="absolute right-0 mt-2 w-36 bg-background-primary border border-border-DEFAULT rounded-md shadow-lg z-10"
                      role="menu"
                      aria-label="Theme options"
                    >
                      {[
                        { value: 'light', label: 'Light', icon: FiSun },
                        { value: 'dark', label: 'Dark', icon: FiMoon },
                        { value: 'system', label: 'System', icon: FiMonitor }
                      ].map(({ value, label, icon: Icon }) => (
                        <button
                          key={value}
                          onClick={() => handleThemeChange(value as any)}
                          className={`
                            w-full flex items-center px-4 py-2 text-sm text-left
                            ${currentTheme === value 
                              ? 'bg-primary-DEFAULT text-primary-contrast' 
                              : 'text-text-primary hover:bg-interactive-hover'
                            }
                            first:rounded-t-md last:rounded-b-md
                            focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-inset
                          `}
                          role="menuitem"
                        >
                          <Icon className="h-4 w-4 mr-2" aria-hidden="true" />
                          {label}
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* Share current view */}
            {showShareButton && (
              <div className="ml-2">
                <ShareViewButton
                  label="Share"
                  className="px-3 py-2 text-sm font-medium rounded-md bg-interactive-muted text-text-primary hover:bg-interactive-hover focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2"
                />
              </div>
            )}
            
            {/* Notifications */}
            {notificationsEnabled && user && (
              <button
                onClick={onNotificationClick}
                className="p-2 text-text-secondary hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded-full transition-colors duration-200 relative"
                aria-label="Notifications"
              >
                <FiBell className="h-5 w-5" />
                {/* Notification badge example */}
                <span className="absolute -top-1 -right-1 h-3 w-3 bg-error-DEFAULT rounded-full" aria-hidden="true" />
              </button>
            )}
            
            {/* User Profile */}
            {user && (
              <div className="relative ml-3" data-dropdown>
                <button
                  ref={profileButtonRef}
                  onClick={() => toggleDropdown('profile')}
                  className="flex items-center max-w-xs bg-background-primary rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2 transition-colors duration-200"
                  aria-expanded={activeDropdown === 'profile'}
                  aria-haspopup="true"
                  aria-label="User menu"
                >
                  {user.avatar ? (
                    <img
                      className="h-8 w-8 rounded-full"
                      src={user.avatar}
                      alt={`${user.name} avatar`}
                    />
                  ) : (
                    <div className="h-8 w-8 bg-primary-DEFAULT rounded-full flex items-center justify-center">
                      <FiUser className="h-4 w-4 text-primary-contrast" />
                    </div>
                  )}
                  <span className="hidden md:block ml-2 text-text-primary">
                    {user.name}
                  </span>
                  <FiChevronDown className="hidden md:block ml-1 h-4 w-4 text-text-secondary" aria-hidden="true" />
                </button>
                
                <AnimatePresence>
                  {activeDropdown === 'profile' && (
                    <motion.div
                      initial={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
                      className="absolute right-0 mt-2 w-48 bg-background-primary border border-border-DEFAULT rounded-md shadow-lg z-10"
                      role="menu"
                      aria-label="User menu"
                    >
                      <div className="px-4 py-3 border-b border-border-DEFAULT">
                        <p className="text-sm font-medium text-text-primary">{user.name}</p>
                        <p className="text-sm text-text-secondary">{user.email}</p>
                        {user.role && (
                          <p className="text-xs text-text-tertiary mt-1">{user.role}</p>
                        )}
                      </div>
                      
                      <button
                        onClick={onProfileClick}
                        className="w-full flex items-center px-4 py-2 text-sm text-text-primary hover:bg-interactive-hover focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-inset"
                        role="menuitem"
                      >
                        <FiUser className="h-4 w-4 mr-2" aria-hidden="true" />
                        Your Profile
                      </button>
                      
                      <button
                        onClick={() => {/* Handle settings */}}
                        className="w-full flex items-center px-4 py-2 text-sm text-text-primary hover:bg-interactive-hover focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-inset"
                        role="menuitem"
                      >
                        <FiSettings className="h-4 w-4 mr-2" aria-hidden="true" />
                        Settings
                      </button>
                      
                      <button
                        onClick={onLogout}
                        className="w-full flex items-center px-4 py-2 text-sm text-error-DEFAULT hover:bg-error-50 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-inset rounded-b-md"
                        role="menuitem"
                      >
                        <FiLogOut className="h-4 w-4 mr-2" aria-hidden="true" />
                        Sign out
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
            
            {/* Mobile menu button */}
            <button
              ref={menuButtonRef}
              onClick={toggleMobileMenu}
              className="md:hidden p-2 text-text-secondary hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded-md transition-colors duration-200"
              aria-expanded={isMenuOpen}
              aria-label="Toggle navigation menu"
            >
              {isMenuOpen ? (
                <FiX className="h-6 w-6" aria-hidden="true" />
              ) : (
                <FiMenu className="h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
        
        {/* Mobile Menu */}
        <AnimatePresence>
          {isMenuOpen && (
            <motion.div
              ref={mobileMenuRef}
              initial={prefersReducedMotion ? {} : { opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={prefersReducedMotion ? {} : { opacity: 0, height: 0 }}
              className="md:hidden border-t border-border-DEFAULT"
              role="navigation"
              aria-label="Mobile navigation"
            >
              <div className="px-2 pt-2 pb-3 space-y-1 bg-background-primary">
                {/* Mobile Search */}
                {searchEnabled && (
                  <div className="px-2 pb-3">
                    <form onSubmit={handleSearch}>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <FiSearch className="h-4 w-4 text-text-tertiary" aria-hidden="true" />
                        </div>
                        <input
                          type="search"
                          placeholder="Search..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="
                            w-full pl-10 pr-4 py-2 border border-border-DEFAULT rounded-md
                            bg-background-primary text-text-primary placeholder-text-tertiary
                            focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT
                          "
                          aria-label="Search"
                        />
                      </div>
                    </form>
                  </div>
                )}
                
                {/* Mobile Navigation Items */}
                {navigation.map(item => renderNavigationItem(item, true))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
};

export default UnifiedHeader;
