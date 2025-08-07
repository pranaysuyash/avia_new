/**
 * Webpack Bundle Analyzer Configuration
 * Helps monitor and optimize bundle sizes
 */

const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const SpeedMeasurePlugin = require('speed-measure-webpack-plugin');
const { merge } = require('webpack-merge');

// Import base webpack configs
const webConfig = require('./frontend/webpack.config.js');
const desktopConfig = require('./desktop_app/webpack.config.js');

const smp = new SpeedMeasurePlugin();

// Bundle size limits aligned with Lighthouse budgets
const BUNDLE_SIZE_LIMITS = {
  scripts: 300 * 1024, // 300KB
  styles: 100 * 1024, // 100KB
  images: 500 * 1024, // 500KB
  fonts: 150 * 1024, // 150KB
  total: 1500 * 1024, // 1.5MB
};

// Common analyzer configuration
const analyzerConfig = {
  plugins: [
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      reportFilename: 'bundle-report.html',
      openAnalyzer: false,
      generateStatsFile: true,
      statsFilename: 'bundle-stats.json',
      statsOptions: {
        source: false,
        reasons: true,
        optimizationBailout: true,
        chunkModules: true,
      },
    }),
  ],
  performance: {
    hints: 'error',
    maxEntrypointSize: BUNDLE_SIZE_LIMITS.total,
    maxAssetSize: BUNDLE_SIZE_LIMITS.scripts,
    assetFilter: (assetFilename) => {
      // Check different asset types
      if (assetFilename.endsWith('.js')) {
        return true; // Check JS files
      }
      if (assetFilename.endsWith('.css')) {
        return true; // Check CSS files
      }
      return false; // Ignore other assets for performance hints
    },
  },
};

// Web app analyzer config
const webAnalyzerConfig = smp.wrap(
  merge(webConfig, analyzerConfig, {
    output: {
      path: path.resolve(__dirname, 'dist/web-analyze'),
    },
  })
);

// Desktop app analyzer config
const desktopAnalyzerConfig = smp.wrap(
  merge(desktopConfig, analyzerConfig, {
    output: {
      path: path.resolve(__dirname, 'dist/desktop-analyze'),
    },
  })
);

// Export configurations
module.exports = {
  web: webAnalyzerConfig,
  desktop: desktopAnalyzerConfig,
};