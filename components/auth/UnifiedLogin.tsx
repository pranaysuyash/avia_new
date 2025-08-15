/**
 * Unified Login Component
 * Accessible, responsive login form with platform adaptations
 * Follows WCAG 2.1 AA guidelines and unified design system
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FiMail, 
  FiLock, 
  FiEye, 
  FiEyeOff, 
  FiAlertCircle, 
  FiCheck,
  FiLoader
} from 'react-icons/fi';
import { ThemeProvider } from '../../shared/theme';

// Platform detection
const isReactNative = typeof window === 'undefined' && typeof global !== 'undefined';
const isElectron = typeof window !== 'undefined' && window.electronAPI;

// Base interfaces
interface LoginProps {
  onSubmit: (credentials: LoginCredentials) => Promise<boolean>;
  onForgotPassword?: () => void;
  onRegister?: () => void;
  loading?: boolean;
  error?: string;
  socialLogin?: boolean;
  rememberMe?: boolean;
  autoFocus?: boolean;
  variant?: 'modal' | 'page' | 'inline';
  platform?: 'web' | 'mobile' | 'desktop';
}

interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

interface FormValidation {
  email: {
    isValid: boolean;
    message: string;
  };
  password: {
    isValid: boolean;
    message: string;
  };
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

const validateEmail = (email: string): { isValid: boolean; message: string } => {
  if (!email) {
    return { isValid: false, message: 'Email is required' };
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { isValid: false, message: 'Please enter a valid email address' };
  }
  
  return { isValid: true, message: '' };
};

const validatePassword = (password: string): { isValid: boolean; message: string } => {
  if (!password) {
    return { isValid: false, message: 'Password is required' };
  }
  
  if (password.length < 6) {
    return { isValid: false, message: 'Password must be at least 6 characters' };
  }
  
  return { isValid: true, message: '' };
};

// Main component
export const UnifiedLogin: React.FC<LoginProps> = ({
  onSubmit,
  onForgotPassword,
  onRegister,
  loading = false,
  error,
  socialLogin = true,
  rememberMe = true,
  autoFocus = true,
  variant = 'page',
  platform = 'web'
}) => {
  // State management
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
    rememberMe: false
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [validation, setValidation] = useState<FormValidation>({
    email: { isValid: true, message: '' },
    password: { isValid: true, message: '' }
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);
  
  // Refs for accessibility
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const submitRef = useRef<HTMLButtonElement>(null);
  const errorRef = useRef<HTMLDivElement>(null);
  
  // Theme
  const theme = ThemeProvider.web;
  const isHighContrast = ThemeProvider.isHighContrast();
  const prefersReducedMotion = ThemeProvider.prefersReducedMotion();
  
  // Auto-focus email field
  useEffect(() => {
    if (autoFocus && emailRef.current) {
      // Delay to ensure component is fully mounted
      const timer = setTimeout(() => {
        emailRef.current?.focus();
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [autoFocus]);
  
  // Announce errors to screen readers
  useEffect(() => {
    if (error) {
      announceToScreenReader(`Login error: ${error}`);
    }
  }, [error]);
  
  // Real-time validation
  const validateField = useCallback((field: 'email' | 'password', value: string) => {
    let validationResult;
    
    switch (field) {
      case 'email':
        validationResult = validateEmail(value);
        break;
      case 'password':
        validationResult = validatePassword(value);
        break;
      default:
        return;
    }
    
    setValidation(prev => ({
      ...prev,
      [field]: validationResult
    }));
  }, []);
  
  // Handle input changes
  const handleInputChange = useCallback((field: keyof LoginCredentials, value: string | boolean) => {
    setCredentials(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Validate on change for better UX
    if (typeof value === 'string' && (field === 'email' || field === 'password')) {
      validateField(field, value);
    }
  }, [validateField]);
  
  // Handle form submission
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Prevent double submission
    if (isSubmitting || loading) return;
    
    // Validate all fields
    const emailValidation = validateEmail(credentials.email);
    const passwordValidation = validatePassword(credentials.password);
    
    setValidation({
      email: emailValidation,
      password: passwordValidation
    });
    
    // Check if form is valid
    if (!emailValidation.isValid || !passwordValidation.isValid) {
      announceToScreenReader('Please correct the errors in the form');
      
      // Focus first invalid field
      if (!emailValidation.isValid) {
        emailRef.current?.focus();
      } else if (!passwordValidation.isValid) {
        passwordRef.current?.focus();
      }
      
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const success = await onSubmit(credentials);
      
      if (success) {
        announceToScreenReader('Login successful');
      } else {
        announceToScreenReader('Login failed. Please check your credentials.');
      }
    } catch (err) {
      console.error('Login error:', err);
      announceToScreenReader('An error occurred during login');
    } finally {
      setIsSubmitting(false);
    }
  }, [credentials, isSubmitting, loading, onSubmit]);
  
  // Handle OAuth login
  const handleOAuthLogin = useCallback(async (provider: 'google' | 'github') => {
    if (isElectron && window.electronAPI?.oauthLogin) {
      try {
        const result = await window.electronAPI.oauthLogin(provider);
        if (result.success) {
          await onSubmit({ email: result.token, password: '', rememberMe: false });
        }
      } catch (err) {
        console.error(`${provider} OAuth error:`, err);
      }
    } else {
      // Web OAuth redirect
      window.location.href = `${process.env.REACT_APP_API_URL || 'http://localhost:8001'}/api/auth/${provider}`;
    }
  }, [onSubmit]);
  
  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Enter':
        if (e.currentTarget === emailRef.current) {
          e.preventDefault();
          passwordRef.current?.focus();
        } else if (e.currentTarget === passwordRef.current) {
          e.preventDefault();
          submitRef.current?.click();
        }
        break;
      case 'Tab':
        // Let browser handle natural tab flow
        break;
      case 'Escape':
        if (variant === 'modal') {
          // Handle modal close
          (e.target as HTMLElement).blur();
        }
        break;
    }
  }, [variant]);
  
  // Dynamic styles based on platform and preferences
  const getContainerStyles = () => {
    const baseStyles = `
      ${variant === 'page' ? 'min-h-screen flex items-center justify-center' : ''}
      ${variant === 'modal' ? 'max-w-md mx-auto' : ''}
      ${variant === 'inline' ? 'w-full' : ''}
      bg-background-primary py-12 px-4 sm:px-6 lg:px-8
    `;
    
    return isHighContrast 
      ? `${baseStyles} border-2 border-accessibility-highContrast-border`
      : baseStyles;
  };
  
  const getInputStyles = (field: 'email' | 'password') => {
    const isInvalid = !validation[field].isValid && credentials[field];
    const isFocused = focusedField === field;
    
    return `
      appearance-none relative block w-full px-3 py-2 pl-10
      ${field === 'password' ? 'pr-10' : ''}
      border ${isInvalid 
        ? 'border-error-DEFAULT focus:border-error-DEFAULT focus:ring-error-DEFAULT' 
        : 'border-border-DEFAULT focus:border-primary-DEFAULT focus:ring-primary-DEFAULT'
      }
      placeholder-text-tertiary text-text-primary
      ${field === 'email' ? 'rounded-t-md' : 'rounded-b-md'}
      focus:outline-none focus:ring-2 focus:ring-offset-2 focus:z-10
      text-sm sm:text-base
      ${isHighContrast ? 'bg-accessibility-highContrast-background' : 'bg-background-primary'}
      transition-colors duration-200
      ${isFocused ? 'ring-2 ring-accessibility-focus-outline ring-offset-2' : ''}
    `;
  };
  
  const motionProps = prefersReducedMotion ? {} : {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3 }
  };
  
  return (
    <div className={getContainerStyles()}>
      <motion.div
        {...motionProps}
        className="max-w-md w-full space-y-8"
      >
        {/* Header */}
        <div className="text-center">
          <h1 
            className="text-3xl font-extrabold text-text-primary"
            id="login-title"
          >
            Sign in to your account
          </h1>
          {onRegister && (
            <p className="mt-2 text-sm text-text-secondary">
              Or{' '}
              <button
                type="button"
                onClick={onRegister}
                className="font-medium text-primary-DEFAULT hover:text-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded"
              >
                create a new account
              </button>
            </p>
          )}
        </div>
        
        {/* Main Form */}
        <form 
          className="mt-8 space-y-6" 
          onSubmit={handleSubmit}
          aria-labelledby="login-title"
          noValidate
        >
          {/* Form Fields */}
          <div className="rounded-md shadow-sm -space-y-px">
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FiMail 
                    className="h-5 w-5 text-text-tertiary" 
                    aria-hidden="true"
                  />
                </div>
                <input
                  ref={emailRef}
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={credentials.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  onFocus={() => setFocusedField('email')}
                  onBlur={() => setFocusedField(null)}
                  onKeyDown={handleKeyDown}
                  className={getInputStyles('email')}
                  placeholder="Email address"
                  aria-describedby={
                    validation.email.message ? "email-error" : "email-description"
                  }
                  aria-invalid={!validation.email.isValid}
                />
              </div>
              <div id="email-description" className="sr-only">
                Enter your email address to sign in
              </div>
              {validation.email.message && (
                <div 
                  id="email-error"
                  className="mt-1 text-sm text-error-DEFAULT flex items-center"
                  role="alert"
                  aria-live="polite"
                >
                  <FiAlertCircle className="h-4 w-4 mr-1" aria-hidden="true" />
                  {validation.email.message}
                </div>
              )}
            </div>
            
            {/* Password Field */}
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FiLock 
                    className="h-5 w-5 text-text-tertiary" 
                    aria-hidden="true"
                  />
                </div>
                <input
                  ref={passwordRef}
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={credentials.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  onKeyDown={handleKeyDown}
                  className={getInputStyles('password')}
                  placeholder="Password"
                  aria-describedby={
                    validation.password.message ? "password-error" : "password-description"
                  }
                  aria-invalid={!validation.password.isValid}
                />
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-text-tertiary hover:text-text-secondary focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded-full p-1"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    tabIndex={0}
                  >
                    {showPassword ? (
                      <FiEyeOff className="h-5 w-5" aria-hidden="true" />
                    ) : (
                      <FiEye className="h-5 w-5" aria-hidden="true" />
                    )}
                  </button>
                </div>
              </div>
              <div id="password-description" className="sr-only">
                Enter your password. Must be at least 6 characters.
              </div>
              {validation.password.message && (
                <div 
                  id="password-error"
                  className="mt-1 text-sm text-error-DEFAULT flex items-center"
                  role="alert"
                  aria-live="polite"
                >
                  <FiAlertCircle className="h-4 w-4 mr-1" aria-hidden="true" />
                  {validation.password.message}
                </div>
              )}
            </div>
          </div>
          
          {/* Global Error */}
          <AnimatePresence>
            {error && (
              <motion.div
                ref={errorRef}
                initial={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
                className="rounded-md bg-error-50 border border-error-200 p-4"
                role="alert"
                aria-live="assertive"
              >
                <div className="flex">
                  <div className="flex-shrink-0">
                    <FiAlertCircle className="h-5 w-5 text-error-DEFAULT" aria-hidden="true" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-error-800">
                      Login Error
                    </h3>
                    <div className="mt-1 text-sm text-error-700">
                      {error}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Remember Me & Forgot Password */}
          <div className="flex items-center justify-between">
            {rememberMe && (
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  checked={credentials.rememberMe}
                  onChange={(e) => handleInputChange('rememberMe', e.target.checked)}
                  className="h-4 w-4 text-primary-DEFAULT focus:ring-primary-DEFAULT border-border-DEFAULT rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-text-primary">
                  Remember me
                </label>
              </div>
            )}
            
            {onForgotPassword && (
              <div className="text-sm">
                <button
                  type="button"
                  onClick={onForgotPassword}
                  className="font-medium text-primary-DEFAULT hover:text-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded"
                >
                  Forgot your password?
                </button>
              </div>
            )}
          </div>
          
          {/* Submit Button */}
          <div>
            <button
              ref={submitRef}
              type="submit"
              disabled={loading || isSubmitting}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-primary-contrast bg-primary-DEFAULT hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-DEFAULT disabled:bg-interactive-disabled disabled:cursor-not-allowed transition-colors duration-200"
              aria-describedby="submit-description"
            >
              <span className="absolute left-0 inset-y-0 flex items-center pl-3">
                {(loading || isSubmitting) ? (
                  <FiLoader 
                    className="h-5 w-5 animate-spin" 
                    aria-hidden="true"
                  />
                ) : (
                  <FiCheck 
                    className="h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity" 
                    aria-hidden="true"
                  />
                )}
              </span>
              {(loading || isSubmitting) ? 'Signing in...' : 'Sign in'}
            </button>
            <div id="submit-description" className="sr-only">
              Click to sign in with your email and password
            </div>
          </div>
          
          {/* Social Login */}
          {socialLogin && (
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border-DEFAULT" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-background-primary text-text-secondary">
                    Or continue with
                  </span>
                </div>
              </div>
              
              <div className="mt-6 grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => handleOAuthLogin('google')}
                  className="w-full inline-flex justify-center py-2 px-4 border border-border-DEFAULT rounded-md shadow-sm bg-background-primary text-sm font-medium text-text-secondary hover:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-DEFAULT transition-colors duration-200"
                  aria-label="Sign in with Google"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24" aria-hidden="true">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  <span className="ml-2">Google</span>
                </button>
                
                <button
                  type="button"
                  onClick={() => handleOAuthLogin('github')}
                  className="w-full inline-flex justify-center py-2 px-4 border border-border-DEFAULT rounded-md shadow-sm bg-background-primary text-sm font-medium text-text-secondary hover:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-DEFAULT transition-colors duration-200"
                  aria-label="Sign in with GitHub"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path
                      fillRule="evenodd"
                      d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="ml-2">GitHub</span>
                </button>
              </div>
            </div>
          )}
        </form>
      </motion.div>
    </div>
  );
};

export default UnifiedLogin;