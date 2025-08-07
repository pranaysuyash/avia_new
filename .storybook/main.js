module.exports = {
  stories: [
    '../frontend/src/**/*.stories.@(js|jsx|ts|tsx)',
    '../desktop_app/src/renderer/src/**/*.stories.@(js|jsx|ts|tsx)',
    '../stories/**/*.stories.@(js|jsx|ts|tsx)'
  ],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-links',
    '@storybook/addon-a11y',
    '@storybook/addon-viewport',
  ],
  framework: {
    name: '@storybook/react-webpack5',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
  webpackFinal: async (config) => {
    // Add support for TypeScript path aliases
    config.resolve.alias = {
      ...config.resolve.alias,
      '@/design-tokens': path.resolve(__dirname, '../design-tokens.json'),
      '@/shared': path.resolve(__dirname, '../shared'),
    };
    return config;
  },
};