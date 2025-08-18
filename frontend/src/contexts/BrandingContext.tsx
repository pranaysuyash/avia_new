import React, { createContext, useContext, useState } from 'react';

interface BrandingTheme {
  primaryColor: string;
  secondaryColor: string;
  logo: string;
  companyName: string;
  customCss?: string;
}

interface BrandingContextType {
  theme: BrandingTheme;
  updateTheme: (newTheme: Partial<BrandingTheme>) => void;
  resetTheme: () => void;
}

const defaultTheme: BrandingTheme = {
  primaryColor: '#3b82f6',
  secondaryColor: '#64748b',
  logo: '/logo.svg',
  companyName: 'Enterprise Platform',
};

const BrandingContext = createContext<BrandingContextType | undefined>(undefined);

export const useBranding = () => {
  const context = useContext(BrandingContext);
  if (context === undefined) {
    throw new Error('useBranding must be used within a BrandingProvider');
  }
  return context;
};

interface BrandingProviderProps {
  children: React.ReactNode;
  initialTheme?: Partial<BrandingTheme>;
}

export const BrandingProvider: React.FC<BrandingProviderProps> = ({ 
  children, 
  initialTheme = {} 
}) => {
  const [theme, setTheme] = useState<BrandingTheme>({
    ...defaultTheme,
    ...initialTheme,
  });

  const updateTheme = (newTheme: Partial<BrandingTheme>) => {
    setTheme(prev => ({ ...prev, ...newTheme }));
  };

  const resetTheme = () => {
    setTheme(defaultTheme);
  };

  const value = {
    theme,
    updateTheme,
    resetTheme,
  };

  return (
    <BrandingContext.Provider value={value}>
      {children}
    </BrandingContext.Provider>
  );
};