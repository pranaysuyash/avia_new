/**
 * Internationalization Provider Component
 * React context provider for i18n functionality
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import apiService from '../../services/api';

// Types
interface LanguageInfo {
  code: string;
  name: string;
  native_name: string;
  direction: 'ltr' | 'rtl';
  flag: string;
}

interface TranslationContext {
  namespace?: string;
  variables?: Record<string, any>;
}

interface I18nContextType {
  currentLanguage: string;
  languages: LanguageInfo[];
  isRTL: boolean;
  textDirection: 'ltr' | 'rtl';
  loading: boolean;
  error: string | null;
  t: (key: string, context?: TranslationContext) => string;
  setLanguage: (languageCode: string) => Promise<void>;
  formatDate: (date: Date | string, options?: Intl.DateTimeFormatOptions) => string;
  formatTime: (date: Date | string) => string;
  formatNumber: (number: number) => string;
  formatCurrency: (amount: number) => string;
  detectLanguage: (text: string) => Promise<string>;
  refreshTranslations: () => Promise<void>;
}

// Create context
const I18nContext = createContext<I18nContextType | undefined>(undefined);

// Translation cache
const translationCache: Record<string, Record<string, string>> = {};
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const cacheTimestamps: Record<string, number> = {};

interface I18nProviderProps {
  children: ReactNode;
  defaultLanguage?: string;
}

export const I18nProvider: React.FC<I18nProviderProps> = ({
  children,
  defaultLanguage = 'en'
}) => {
  const { user } = useAuth();
  const [currentLanguage, setCurrentLanguage] = useState(defaultLanguage);
  const [languages, setLanguages] = useState<LanguageInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize i18n
  useEffect(() => {
    initializeI18n();
  }, [user]);

  // Update document direction when language changes
  useEffect(() => {
    const currentLang = languages.find(lang => lang.code === currentLanguage);
    if (currentLang) {
      document.dir = currentLang.direction;
      document.documentElement.lang = currentLanguage;
      
      // Update CSS custom properties for RTL support
      document.documentElement.style.setProperty('--text-direction', currentLang.direction);
    }
  }, [currentLanguage, languages]);

  const initializeI18n = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load supported languages
      const languagesResponse = await apiService.get('/api/v1/i18n/languages');
      setLanguages(languagesResponse.data);

      // Get user's language preference if logged in
      if (user) {
        try {
          const preferenceResponse = await apiService.get('/api/v1/i18n/user/preference');
          setCurrentLanguage(preferenceResponse.data.language_code);
        } catch (err) {
          console.warn('Failed to load user language preference, using default');
        }
      } else {
        // Detect browser language
        const browserLang = navigator.language.split('-')[0];
        const supportedLang = languagesResponse.data.find(
          (lang: LanguageInfo) => lang.code === browserLang
        );
        if (supportedLang) {
          setCurrentLanguage(browserLang);
        }
      }
    } catch (err) {
      console.error('Failed to initialize i18n:', err);
      setError('Failed to load language settings');
    } finally {
      setLoading(false);
    }
  };

  const isCacheValid = (cacheKey: string): boolean => {
    const timestamp = cacheTimestamps[cacheKey];
    return Boolean(timestamp && (Date.now() - timestamp) < CACHE_DURATION);
  };

  const t = useCallback((key: string, context?: TranslationContext): string => {
    const namespace = context?.namespace || 'general';
    const cacheKey = `${currentLanguage}:${namespace}`;

    // Check cache first
    if (translationCache[cacheKey] && isCacheValid(cacheKey)) {
      const cachedTranslation = translationCache[cacheKey][key];
      if (cachedTranslation) {
        return substituteVariables(cachedTranslation, context?.variables);
      }
    }

    // If not in cache, queue for loading and return key as fallback
    loadTranslation(key, namespace);
    return key; // Fallback while loading
  }, [currentLanguage]);

  const loadTranslation = async (key: string, namespace: string = 'general') => {
    try {
      const response = await apiService.post('/api/v1/i18n/translate', {
        key,
        language_code: currentLanguage,
        namespace
      });

      const cacheKey = `${currentLanguage}:${namespace}`;
      if (!translationCache[cacheKey]) {
        translationCache[cacheKey] = {};
      }
      
      translationCache[cacheKey][key] = response.data.value;
      cacheTimestamps[cacheKey] = Date.now();

      // Trigger re-render by updating a state
      setError(null);
    } catch (err) {
      console.warn(`Failed to load translation for key: ${key}`, err);
    }
  };

  const loadBulkTranslations = async (keys: string[], namespace: string = 'general') => {
    try {
      const response = await apiService.post('/api/v1/i18n/translate/bulk', {
        keys,
        language_code: currentLanguage,
        namespace
      });

      const cacheKey = `${currentLanguage}:${namespace}`;
      if (!translationCache[cacheKey]) {
        translationCache[cacheKey] = {};
      }

      Object.assign(translationCache[cacheKey], response.data);
      cacheTimestamps[cacheKey] = Date.now();
    } catch (err) {
      console.warn('Failed to load bulk translations:', err);
    }
  };

  const substituteVariables = (text: string, variables?: Record<string, any>): string => {
    if (!variables) return text;

    let result = text;
    Object.entries(variables).forEach(([key, value]) => {
      // Support both {{key}} and {key} patterns
      result = result.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), String(value));
      result = result.replace(new RegExp(`\\{${key}\\}`, 'g'), String(value));
    });

    return result;
  };

  const setLanguage = async (languageCode: string): Promise<void> => {
    try {
      setCurrentLanguage(languageCode);

      // Save user preference if logged in
      if (user) {
        await apiService.post('/api/v1/i18n/user/preference', {
          language_code: languageCode
        });
      } else {
        // Store in localStorage for non-authenticated users
        localStorage.setItem('preferredLanguage', languageCode);
      }

      // Clear cache to force reload of translations
      Object.keys(translationCache).forEach(key => {
        if (key.startsWith(languageCode)) {
          delete translationCache[key];
          delete cacheTimestamps[key];
        }
      });
    } catch (err) {
      console.error('Failed to set language:', err);
      throw err;
    }
  };

  const formatDate = (date: Date | string, options?: Intl.DateTimeFormatOptions): string => {
    try {
      const dateObj = typeof date === 'string' ? new Date(date) : date;
      return new Intl.DateTimeFormat(currentLanguage, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        ...options
      }).format(dateObj);
    } catch (err) {
      return String(date);
    }
  };

  const formatTime = (date: Date | string): string => {
    try {
      const dateObj = typeof date === 'string' ? new Date(date) : date;
      return new Intl.DateTimeFormat(currentLanguage, {
        hour: '2-digit',
        minute: '2-digit'
      }).format(dateObj);
    } catch (err) {
      return String(date);
    }
  };

  const formatNumber = (number: number): string => {
    try {
      return new Intl.NumberFormat(currentLanguage).format(number);
    } catch (err) {
      return String(number);
    }
  };

  const formatCurrency = (amount: number, currency: string = 'USD'): string => {
    try {
      return new Intl.NumberFormat(currentLanguage, {
        style: 'currency',
        currency
      }).format(amount);
    } catch (err) {
      return String(amount);
    }
  };

  const detectLanguage = async (text: string): Promise<string> => {
    try {
      const response = await apiService.get('/api/v1/i18n/detect-language', {
        params: { text }
      });
      return response.data.detected_language;
    } catch (err) {
      console.error('Language detection failed:', err);
      return 'en';
    }
  };

  const refreshTranslations = async (): Promise<void> => {
    // Clear cache
    Object.keys(translationCache).forEach(key => {
      delete translationCache[key];
      delete cacheTimestamps[key];
    });

    // Reload current translations
    await initializeI18n();
  };

  // Get computed properties
  const currentLang = languages.find(lang => lang.code === currentLanguage);
  const isRTL = currentLang?.direction === 'rtl' || false;
  const textDirection = currentLang?.direction || 'ltr';

  const contextValue: I18nContextType = {
    currentLanguage,
    languages,
    isRTL,
    textDirection,
    loading,
    error,
    t,
    setLanguage,
    formatDate,
    formatTime,
    formatNumber,
    formatCurrency,
    detectLanguage,
    refreshTranslations
  };

  return (
    <I18nContext.Provider value={contextValue}>
      {children}
    </I18nContext.Provider>
  );
};

// Custom hook to use i18n context
export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};

// Higher-order component for class components
export const withI18n = <P extends object>(
  Component: React.ComponentType<P & { i18n: I18nContextType }>
) => {
  return (props: P) => {
    const i18n = useI18n();
    return <Component {...props} i18n={i18n} />;
  };
};

// Utility components
export const Trans: React.FC<{
  i18nKey: string;
  namespace?: string;
  variables?: Record<string, any>;
  children?: ReactNode;
}> = ({ i18nKey, namespace, variables, children }) => {
  const { t } = useI18n();
  const translation = t(i18nKey, { namespace, variables });
  
  return <>{children || translation}</>;
};

export const LanguageSwitch: React.FC<{
  className?: string;
  showFlags?: boolean;
  showNativeNames?: boolean;
}> = ({ className, showFlags = true, showNativeNames = true }) => {
  const { currentLanguage, languages, setLanguage, loading } = useI18n();

  const handleLanguageChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    try {
      await setLanguage(event.target.value);
    } catch (err) {
      console.error('Failed to change language:', err);
    }
  };

  if (loading || languages.length === 0) {
    return <select disabled className={className}><option>Loading...</option></select>;
  }

  return (
    <select 
      value={currentLanguage}
      onChange={handleLanguageChange}
      className={className}
      aria-label="Select language"
    >
      {languages.map(language => (
        <option key={language.code} value={language.code}>
          {showFlags && `${language.flag} `}
          {showNativeNames ? language.native_name : language.name}
        </option>
      ))}
    </select>
  );
};

export default I18nProvider;