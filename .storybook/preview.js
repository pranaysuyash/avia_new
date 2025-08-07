import { webTheme } from '../shared/theme';
import '../tailwind.config.js';

export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
  backgrounds: {
    default: 'light',
    values: [
      {
        name: 'light',
        value: webTheme.colors.background.primary,
      },
      {
        name: 'secondary',
        value: webTheme.colors.background.secondary,
      },
      {
        name: 'dark',
        value: webTheme.colors.background.inverse,
      },
    ],
  },
  viewport: {
    viewports: {
      mobile: {
        name: 'Mobile',
        styles: {
          width: '375px',
          height: '667px',
        },
      },
      tablet: {
        name: 'Tablet',
        styles: {
          width: '768px',
          height: '1024px',
        },
      },
      desktop: {
        name: 'Desktop',
        styles: {
          width: '1440px',
          height: '900px',
        },
      },
    },
  },
};

// Global decorator to apply theme
export const decorators = [
  (Story) => (
    <div style={{ padding: '1rem' }}>
      <Story />
    </div>
  ),
];