/**
 * Webpack Configuration for Sentry Source Map Upload
 * Handles source map generation and upload to Sentry
 */

const { sentryWebpackPlugin } = require('@sentry/webpack-plugin');
const { merge } = require('webpack-merge');
const baseConfig = require('./webpack.config.js');

const sentryConfig = {
  mode: 'production',
  devtool: 'source-map', // Generate full source maps
  
  plugins: [
    sentryWebpackPlugin({
      org: process.env.SENTRY_ORG || 'media-analysis-platform',
      project: process.env.SENTRY_PROJECT || 'web-app',
      authToken: process.env.SENTRY_AUTH_TOKEN,
      
      // Release configuration
      release: {
        name: process.env.SENTRY_RELEASE || `web-app@${process.env.npm_package_version}`,
        uploadLegacySourcemaps: {
          paths: ['./build'],
          ignore: ['node_modules'],
        },
        finalize: true,
        
        // Associate commits
        setCommits: {
          auto: true,
          ignoreMissing: true,
        },
        
        // Deploy tracking
        deploy: {
          env: process.env.NODE_ENV || 'production',
        },
      },
      
      // Source maps configuration
      sourcemaps: {
        assets: './build/**',
        ignore: ['./node_modules/**'],
        validate: true,
        
        // Delete source maps after upload
        deleteFilesAfterUpload: [
          './build/**/*.map',
        ],
      },
      
      // Bundle size tracking
      bundleSizeOptimizations: {
        excludeReplayIframe: true,
        excludeReplayShadowDom: true,
      },
      
      // Error handling
      errorHandler: (err, invokeErr, compilation) => {
        console.error('Sentry CLI Plugin Error:', err);
        if (invokeErr) {
          console.error('Invoke Error:', invokeErr);
        }
        // Don't fail the build on Sentry errors in CI
        if (process.env.CI) {
          console.warn('Sentry upload failed in CI, continuing build...');
        } else {
          compilation.errors.push('Sentry: ' + err);
        }
      },
      
      // Telemetry
      telemetry: false,
    }),
  ],
  
  optimization: {
    ...baseConfig.optimization,
    // Ensure consistent module IDs for better source map accuracy
    moduleIds: 'deterministic',
    chunkIds: 'deterministic',
  },
};

module.exports = merge(baseConfig, sentryConfig);