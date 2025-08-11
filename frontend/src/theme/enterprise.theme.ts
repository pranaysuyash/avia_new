import { createTheme, ThemeOptions, alpha } from '@mui/material/styles';

declare module '@mui/material/styles' {
  interface Palette {
    enterprise: {
      dashboard: string;
      sidebar: string;
      headerGradient: string;
    };
  }
  interface PaletteOptions {
    enterprise?: {
      dashboard?: string;
      sidebar?: string;
      headerGradient?: string;
    };
  }
  interface TypographyVariants {
    dashboard: {
      metric: React.CSSProperties;
      label: React.CSSProperties;
    };
  }
  interface TypographyVariantsOptions {
    dashboard?: {
      metric?: React.CSSProperties;
      label?: React.CSSProperties;
    };
  }
}

export interface BrandConfig {
  primaryColor?: string;
  secondaryColor?: string;
  logo?: string;
  companyName?: string;
}

export interface EnterpriseThemeOptions extends ThemeOptions {
  custom?: {
    audio?: {
      waveformPrimary: string;
      waveformProgress: string;
      speakerColors: string[];
    };
    analytics?: {
      chartColors: string[];
      heatmapGradient: string[];
    };
    status?: {
      processing: string;
      success: string;
      warning: string;
      error: string;
      info: string;
    };
  };
}

export const createEnterpriseTheme = (
  mode: 'light' | 'dark' = 'light',
  brandConfig?: BrandConfig
) => {
  const baseTheme = createTheme({
    palette: {
      mode,
      primary: {
        main: brandConfig?.primaryColor || '#1976d2',
        light: '#42a5f5',
        dark: '#1565c0',
        contrastText: '#ffffff',
      },
      secondary: {
        main: brandConfig?.secondaryColor || '#dc004e',
        light: '#f73378',
        dark: '#9a0036',
        contrastText: '#ffffff',
      },
      background: {
        default: mode === 'light' ? '#f5f5f5' : '#121212',
        paper: mode === 'light' ? '#ffffff' : '#1e1e1e',
      },
      enterprise: {
        dashboard: mode === 'light' ? '#fafafa' : '#1a1a1a',
        sidebar: mode === 'light' ? '#1e1e2e' : '#2d2d3d',
        headerGradient:
          mode === 'light'
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            : 'linear-gradient(135deg, #4a5568 0%, #2d3748 100%)',
      },
      success: {
        main: '#4caf50',
        light: '#81c784',
        dark: '#388e3c',
      },
      warning: {
        main: '#ff9800',
        light: '#ffb74d',
        dark: '#f57c00',
      },
      error: {
        main: '#f44336',
        light: '#e57373',
        dark: '#d32f2f',
      },
      info: {
        main: '#2196f3',
        light: '#64b5f6',
        dark: '#1976d2',
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: {
        fontSize: '2.5rem',
        fontWeight: 600,
        letterSpacing: '-0.02em',
        lineHeight: 1.2,
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 600,
        letterSpacing: '-0.01em',
        lineHeight: 1.3,
      },
      h3: {
        fontSize: '1.75rem',
        fontWeight: 600,
        lineHeight: 1.4,
      },
      h4: {
        fontSize: '1.5rem',
        fontWeight: 600,
        lineHeight: 1.4,
      },
      h5: {
        fontSize: '1.25rem',
        fontWeight: 600,
        lineHeight: 1.5,
      },
      h6: {
        fontSize: '1rem',
        fontWeight: 600,
        lineHeight: 1.6,
      },
      dashboard: {
        metric: {
          fontSize: '3rem',
          fontWeight: 700,
          lineHeight: 1.2,
        },
        label: {
          fontSize: '0.875rem',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        },
      },
    },
    shape: {
      borderRadius: 8,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
            borderRadius: 8,
            padding: '8px 16px',
          },
          contained: {
            boxShadow: 'none',
            '&:hover': {
              boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
          elevation1: {
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          },
          elevation2: {
            boxShadow: '0 4px 8px rgba(0,0,0,0.08)',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            boxShadow: '0 4px 8px rgba(0,0,0,0.08)',
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            fontWeight: 500,
          },
        },
      },
      MuiTextField: {
        defaultProps: {
          variant: 'outlined',
        },
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 8,
            },
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow: 'none',
            borderBottom: '1px solid',
            borderBottomColor: mode === 'light' ? '#e0e0e0' : '#2d2d2d',
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRight: 'none',
            boxShadow: '4px 0 8px rgba(0,0,0,0.08)',
          },
        },
      },
    },
  });

  // Add custom properties
  const customTheme = {
    ...baseTheme,
    custom: {
      audio: {
        waveformPrimary: '#4CAF50',
        waveformProgress: '#2196F3',
        speakerColors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
      },
      analytics: {
        chartColors: ['#6366F1', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#EF4444'],
        heatmapGradient: ['#EFF6FF', '#DBEAFE', '#93C5FD', '#3B82F6', '#1E40AF'],
      },
      status: {
        processing: '#F59E0B',
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        info: '#3B82F6',
      },
    },
  };

  return customTheme;
};

export default createEnterpriseTheme;
