/**
 * Onboarding Flow Component
 * Accessible, step-by-step onboarding experience
 * Follows WCAG 2.1 AA guidelines and unified design system
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiArrowRight,
  FiArrowLeft,
  FiCheck,
  FiPlay,
  FiUpload,
  FiSettings,
  FiUser,
  FiHelpCircle,
  FiX,
  FiSkipForward
} from 'react-icons/fi';
import { ThemeProvider } from '../../shared/theme';
import { logUxEvent } from '../../shared/uxTelemetry';
import { ShareViewButton } from '../shared/ShareViewButton';

// Interfaces
interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  content: React.ReactNode;
  icon?: React.ComponentType<{ className?: string }>;
  optional?: boolean;
  validation?: () => Promise<boolean> | boolean;
  action?: {
    label: string;
    onClick: () => Promise<void> | void;
  };
}

interface OnboardingFlowProps {
  steps: OnboardingStep[];
  currentStep?: number;
  onStepChange?: (step: number) => void;
  onComplete?: () => void;
  onSkip?: () => void;
  allowSkip?: boolean;
  showProgress?: boolean;
  variant?: 'modal' | 'fullscreen' | 'embedded';
  className?: string;
  enableDeepLinking?: boolean; // sync step to URL ?ob_step=
  onEvent?: (event: string, payload?: Record<string, unknown>) => void; // UX telemetry hook
}

// Default onboarding steps for the transcription app
const defaultSteps: OnboardingStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to NER Platform',
    description: 'Let\'s get you started with advanced video transcription and analytics',
    icon: FiPlay,
    content: (
      <div className="text-center space-y-4">
        <div className="mx-auto w-24 h-24 bg-primary-DEFAULT/10 rounded-full flex items-center justify-center">
          <FiPlay className="h-12 w-12 text-primary-DEFAULT" />
        </div>
        <p className="text-lg text-text-secondary">
          Transform your audio and video content into searchable, actionable insights
        </p>
        <ul className="space-y-2 text-left max-w-md mx-auto">
          <li className="flex items-center">
            <FiCheck className="h-4 w-4 text-success-DEFAULT mr-2" />
            <span>AI-powered transcription</span>
          </li>
          <li className="flex items-center">
            <FiCheck className="h-4 w-4 text-success-DEFAULT mr-2" />
            <span>Advanced analytics and insights</span>
          </li>
          <li className="flex items-center">
            <FiCheck className="h-4 w-4 text-success-DEFAULT mr-2" />
            <span>Real-time collaboration</span>
          </li>
        </ul>
      </div>
    )
  },
  {
    id: 'profile',
    title: 'Set Up Your Profile',
    description: 'Tell us about yourself to personalize your experience',
    icon: FiUser,
    content: (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="firstName" className="block text-sm font-medium text-text-primary mb-2">
              First Name <span className="text-error-DEFAULT">*</span>
            </label>
            <input
              id="firstName"
              type="text"
              required
              className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT"
              placeholder="Enter your first name"
            />
          </div>
          <div>
            <label htmlFor="lastName" className="block text-sm font-medium text-text-primary mb-2">
              Last Name <span className="text-error-DEFAULT">*</span>
            </label>
            <input
              id="lastName"
              type="text"
              required
              className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT"
              placeholder="Enter your last name"
            />
          </div>
        </div>
        
        <div>
          <label htmlFor="role" className="block text-sm font-medium text-text-primary mb-2">
            What's your primary role?
          </label>
          <select
            id="role"
            className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT"
          >
            <option value="">Select your role</option>
            <option value="content-creator">Content Creator</option>
            <option value="journalist">Journalist</option>
            <option value="researcher">Researcher</option>
            <option value="student">Student</option>
            <option value="business">Business Professional</option>
            <option value="other">Other</option>
          </select>
        </div>
        
        <div>
          <label htmlFor="useCase" className="block text-sm font-medium text-text-primary mb-2">
            What will you primarily use the platform for?
          </label>
          <textarea
            id="useCase"
            rows={3}
            className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:border-primary-DEFAULT"
            placeholder="Tell us about your primary use case (optional)"
          />
        </div>
      </div>
    ),
    validation: () => {
      const firstName = (document.getElementById('firstName') as HTMLInputElement)?.value;
      const lastName = (document.getElementById('lastName') as HTMLInputElement)?.value;
      return !!(firstName && lastName);
    }
  },
  {
    id: 'upload',
    title: 'Upload Your First File',
    description: 'Let\'s process your first audio or video file',
    icon: FiUpload,
    content: (
      <div className="space-y-6">
        <div className="border-2 border-dashed border-border-DEFAULT rounded-lg p-8 text-center">
          <FiUpload className="mx-auto h-12 w-12 text-text-tertiary mb-4" />
          <h3 className="text-lg font-medium text-text-primary mb-2">
            Drop your file here or click to browse
          </h3>
          <p className="text-text-secondary mb-4">
            Supports MP4, MP3, WAV, MOV files up to 500MB
          </p>
          <button className="px-4 py-2 bg-primary-DEFAULT text-primary-contrast rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2">
            Choose File
          </button>
        </div>
        
        <div className="bg-background-secondary rounded-lg p-4">
          <h4 className="font-medium text-text-primary mb-2">✨ Pro Tips:</h4>
          <ul className="space-y-1 text-sm text-text-secondary">
            <li>• Clear audio quality improves transcription accuracy</li>
            <li>• Files under 100MB process faster</li>
            <li>• You can upload multiple files at once</li>
          </ul>
        </div>
      </div>
    ),
    optional: true
  },
  {
    id: 'settings',
    title: 'Configure Your Preferences',
    description: 'Customize the platform to match your workflow',
    icon: FiSettings,
    content: (
      <div className="space-y-6">
        <div>
          <h4 className="font-medium text-text-primary mb-3">Language Settings</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input type="checkbox" defaultChecked className="rounded border-border-DEFAULT mr-2" />
              <span>Auto-detect language</span>
            </label>
            <div>
              <label htmlFor="defaultLanguage" className="block text-sm text-text-secondary mb-1">
                Default transcription language
              </label>
              <select
                id="defaultLanguage"
                className="w-full px-3 py-2 border border-border-DEFAULT rounded-md focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
              </select>
            </div>
          </div>
        </div>
        
        <div>
          <h4 className="font-medium text-text-primary mb-3">Notifications</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input type="checkbox" defaultChecked className="rounded border-border-DEFAULT mr-2" />
              <span>Email when transcription is complete</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="rounded border-border-DEFAULT mr-2" />
              <span>Weekly analytics summary</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="rounded border-border-DEFAULT mr-2" />
              <span>Product updates and tips</span>
            </label>
          </div>
        </div>
        
        <div>
          <h4 className="font-medium text-text-primary mb-3">Privacy</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input type="checkbox" defaultChecked className="rounded border-border-DEFAULT mr-2" />
              <span>Keep transcriptions private by default</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="rounded border-border-DEFAULT mr-2" />
              <span>Auto-delete files after 30 days</span>
            </label>
          </div>
        </div>
      </div>
    ),
    optional: true
  },
  {
    id: 'complete',
    title: 'You\'re All Set!',
    description: 'Welcome to the future of content transcription',
    icon: FiCheck,
    content: (
      <div className="text-center space-y-6">
        <div className="mx-auto w-24 h-24 bg-success-DEFAULT/10 rounded-full flex items-center justify-center">
          <FiCheck className="h-12 w-12 text-success-DEFAULT" />
        </div>
        
        <div>
          <h3 className="text-xl font-semibold text-text-primary mb-2">
            Welcome to NER Platform!
          </h3>
          <p className="text-text-secondary">
            Your account is ready. Start uploading files and discover powerful insights.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          <div className="p-4 bg-background-secondary rounded-lg">
            <FiUpload className="h-8 w-8 text-primary-DEFAULT mx-auto mb-2" />
            <h4 className="font-medium">Upload Files</h4>
            <p className="text-sm text-text-secondary">Start with your first transcription</p>
          </div>
          <div className="p-4 bg-background-secondary rounded-lg">
            <FiHelpCircle className="h-8 w-8 text-primary-DEFAULT mx-auto mb-2" />
            <h4 className="font-medium">Get Help</h4>
            <p className="text-sm text-text-secondary">Access tutorials and support</p>
          </div>
          <div className="p-4 bg-background-secondary rounded-lg">
            <FiSettings className="h-8 w-8 text-primary-DEFAULT mx-auto mb-2" />
            <h4 className="font-medium">Customize</h4>
            <p className="text-sm text-text-secondary">Adjust settings anytime</p>
          </div>
        </div>
      </div>
    ),
    action: {
      label: 'Start Using Platform',
      onClick: () => {
        console.log('Navigate to main dashboard');
      }
    }
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

export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({
  steps = defaultSteps,
  currentStep: externalCurrentStep,
  onStepChange,
  onComplete,
  onSkip,
  allowSkip = true,
  showProgress = true,
  variant = 'modal',
  className = '',
  enableDeepLinking = true,
  onEvent
}) => {
  // State
  const [internalCurrentStep, setInternalCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [isValidating, setIsValidating] = useState(false);
  
  // Use external step control if provided, otherwise use internal
  const currentStep = externalCurrentStep !== undefined ? externalCurrentStep : internalCurrentStep;
  const setCurrentStep = onStepChange || setInternalCurrentStep;
  
  // Refs
  const contentRef = useRef<HTMLDivElement>(null);
  
  // Theme
  const theme = ThemeProvider.web;
  const prefersReducedMotion = ThemeProvider.prefersReducedMotion();
  
  // Current step data
  const step = steps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;
  const progress = ((currentStep + 1) / steps.length) * 100;

  // Helpers for URL param sync
  const setQueryParam = (key: string, value: string) => {
    try {
      const url = new URL(window.location.href);
      url.searchParams.set(key, value);
      window.history.replaceState({}, '', url.toString());
    } catch (_) {}
  };
  const getQueryParam = (key: string) => {
    try {
      const url = new URL(window.location.href);
      return url.searchParams.get(key);
    } catch (_) { return null; }
  };
  
  // Handle step navigation
  const goToStep = useCallback(async (stepIndex: number) => {
    if (stepIndex < 0 || stepIndex >= steps.length) return;
    
    // Validate current step before moving forward
    if (stepIndex > currentStep && step.validation) {
      setIsValidating(true);
      try {
        const isValid = await step.validation();
        if (!isValid) {
          announceToScreenReader('Please complete the required fields before continuing');
          return;
        }
      } catch (error) {
        console.error('Validation error:', error);
        return;
      } finally {
        setIsValidating(false);
      }
    }
    
    // Mark current step as completed if moving forward
    if (stepIndex > currentStep) {
      setCompletedSteps(prev => new Set([...prev, currentStep]));
    }
    
    setCurrentStep(stepIndex);
    // Deep-link and telemetry
    if (enableDeepLinking) {
      setQueryParam('ob_step', String(stepIndex));
    }
    if (onEvent) onEvent('onboarding_step_change', { stepIndex, stepId: steps[stepIndex]?.id });
    else logUxEvent('onboarding_step_change', { stepIndex, stepId: steps[stepIndex]?.id });
    
    // Announce step change
    const newStep = steps[stepIndex];
    announceToScreenReader(`Step ${stepIndex + 1} of ${steps.length}: ${newStep.title}`);
    
    // Focus the content area
    setTimeout(() => {
      contentRef.current?.focus();
    }, 100);
  }, [currentStep, step, steps, setCurrentStep]);
  
  const handleNext = () => {
    if (isLastStep) {
      if (step.action) {
        step.action.onClick();
      }
      if (onEvent) onEvent('onboarding_complete'); else logUxEvent('onboarding_complete');
      onComplete?.();
    } else {
      goToStep(currentStep + 1);
    }
  };
  
  const handlePrevious = () => {
    goToStep(currentStep - 1);
  };
  
  const handleSkip = () => {
    if (step.optional && allowSkip) {
      if (isLastStep) {
      if (onEvent) onEvent('onboarding_skipped_last'); else logUxEvent('onboarding_skipped_last');
        onComplete?.();
      } else {
        if (onEvent) onEvent('onboarding_skip_step', { stepIndex: currentStep, stepId: step.id }); else logUxEvent('onboarding_skip_step', { stepIndex: currentStep, stepId: step.id });
        goToStep(currentStep + 1);
      }
    } else {
      if (onEvent) onEvent('onboarding_skip_disallowed', { stepIndex: currentStep }); else logUxEvent('onboarding_skip_disallowed', { stepIndex: currentStep });
      onSkip?.();
    }
  };
  
  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowRight':
      case 'Enter':
        if (!isLastStep && e.ctrlKey) {
          e.preventDefault();
          handleNext();
        }
        break;
      case 'ArrowLeft':
        if (!isFirstStep && e.ctrlKey) {
          e.preventDefault();
          handlePrevious();
        }
        break;
      case 'Escape':
        if (allowSkip) {
          handleSkip();
        }
        break;
    }
  }, [isFirstStep, isLastStep, allowSkip, handleNext, handlePrevious, handleSkip]);
  
  // Auto-focus content on step change
  useEffect(() => {
    contentRef.current?.focus();
  }, [currentStep]);

  // Initialize from deep link
  useEffect(() => {
    if (!enableDeepLinking) return;
    const qp = getQueryParam('ob_step');
    if (qp !== null) {
      const idx = Math.max(0, Math.min(steps.length - 1, parseInt(qp, 10)));
      if (!Number.isNaN(idx) && idx !== currentStep) {
        setCurrentStep(idx);
      }
    } else {
      // write initial
      setQueryParam('ob_step', String(currentStep));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  // Get container classes based on variant
  const getContainerClasses = () => {
    switch (variant) {
      case 'fullscreen':
        return 'fixed inset-0 bg-background-primary z-50';
      case 'modal':
        return 'fixed inset-0 bg-background-overlay/50 flex items-center justify-center z-50 p-4';
      case 'embedded':
        return 'w-full';
      default:
        return '';
    }
  };
  
  const getContentClasses = () => {
    switch (variant) {
      case 'fullscreen':
        return 'h-full flex flex-col';
      case 'modal':
        return 'bg-background-primary rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col';
      case 'embedded':
        return 'bg-background-primary border border-border-DEFAULT rounded-lg';
      default:
        return '';
    }
  };
  
  return (
    <div 
      className={`${getContainerClasses()} ${className}`}
      onKeyDown={handleKeyDown}
    >
      <div className={getContentClasses()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-DEFAULT">
          <div className="flex items-center space-x-3">
            {step.icon && (
              <div className="w-8 h-8 bg-primary-DEFAULT/10 rounded-full flex items-center justify-center">
                <step.icon className="h-4 w-4 text-primary-DEFAULT" />
              </div>
            )}
            <div>
              <h2 className="text-xl font-semibold text-text-primary">
                {step.title}
              </h2>
              <p className="text-sm text-text-secondary">
                Step {currentStep + 1} of {steps.length}
                {step.optional && ' (Optional)'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <ShareViewButton label="Share" className="px-3 py-1 text-sm rounded-md bg-interactive-muted hover:bg-interactive-hover" />
            {allowSkip && (
            <button
              onClick={handleSkip}
              className="p-2 text-text-tertiary hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded-full transition-colors duration-200"
              aria-label="Skip onboarding"
            >
              <FiX className="h-5 w-5" />
            </button>
            )}
          </div>
        </div>
        
        {/* Progress Bar */}
        {showProgress && (
          <div className="px-6 py-4 border-b border-border-DEFAULT">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-text-primary">Progress</span>
              <span className="text-sm text-text-secondary">{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-background-secondary rounded-full h-2">
              <motion.div
                className="bg-primary-DEFAULT h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: prefersReducedMotion ? 0 : 0.5 }}
              />
            </div>
            
            {/* Step indicators */}
            <div className="flex justify-between mt-3">
              {steps.map((_, index) => (
                <button
                  key={index}
                  onClick={() => goToStep(index)}
                  disabled={index > currentStep && !completedSteps.has(index)}
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-colors duration-200
                    ${index < currentStep || completedSteps.has(index)
                      ? 'bg-success-DEFAULT text-success-contrast'
                      : index === currentStep
                      ? 'bg-primary-DEFAULT text-primary-contrast'
                      : 'bg-background-secondary text-text-tertiary border border-border-DEFAULT'
                    }
                    ${index <= currentStep || completedSteps.has(index)
                      ? 'cursor-pointer hover:opacity-80'
                      : 'cursor-not-allowed'
                    }
                    focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2
                  `}
                  aria-label={`Go to step ${index + 1}: ${steps[index].title}`}
                  aria-current={index === currentStep ? 'step' : undefined}
                >
                  {index < currentStep || completedSteps.has(index) ? (
                    <FiCheck className="h-4 w-4" />
                  ) : (
                    index + 1
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Content */}
        <div className="flex-1 overflow-auto">
          <div 
            ref={contentRef}
            className="p-6 focus:outline-none"
            tabIndex={-1}
            role="main"
            aria-label={`${step.title}: ${step.description}`}
          >
            <div className="mb-6">
              <p className="text-text-secondary">{step.description}</p>
            </div>
            
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={prefersReducedMotion ? {} : { opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={prefersReducedMotion ? {} : { opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                {step.content}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-border-DEFAULT bg-background-secondary">
          <div className="flex items-center space-x-2">
            {!isFirstStep && (
              <button
                onClick={handlePrevious}
                className="flex items-center px-4 py-2 text-text-secondary hover:text-text-primary border border-border-DEFAULT rounded-md hover:bg-interactive-hover focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT transition-colors duration-200"
                aria-label="Go to previous step"
              >
                <FiArrowLeft className="h-4 w-4 mr-2" />
                Previous
              </button>
            )}
            
            {step.optional && (
              <button
                onClick={handleSkip}
                className="flex items-center px-4 py-2 text-text-tertiary hover:text-text-secondary transition-colors duration-200"
              >
                <FiSkipForward className="h-4 w-4 mr-2" />
                Skip
              </button>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            <span className="text-sm text-text-secondary">
              {currentStep + 1} of {steps.length}
            </span>
            
            <button
              onClick={handleNext}
              disabled={isValidating}
              className="flex items-center px-6 py-2 bg-primary-DEFAULT text-primary-contrast rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {isValidating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-contrast mr-2" />
                  Validating...
                </>
              ) : isLastStep ? (
                step.action ? step.action.label : 'Complete'
              ) : (
                <>
                  Next
                  <FiArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingFlow;
