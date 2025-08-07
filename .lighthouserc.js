/**
 * Lighthouse CI Configuration
 * Defines performance budgets and CI settings
 */

module.exports = {
  ci: {
    collect: {
      // Where to run Lighthouse CI
      url: [
        'http://localhost:8501/',
        'http://localhost:3000/',
        'http://localhost:3000/transcription',
        'http://localhost:3000/settings',
      ],
      numberOfRuns: 3,
      settings: {
        preset: 'desktop',
        throttling: {
          cpuSlowdownMultiplier: 1,
        },
      },
    },
    assert: {
      // Performance budgets
      assertions: {
        // Core Web Vitals
        'first-contentful-paint': ['error', { maxNumericValue: 1800 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['error', { maxNumericValue: 300 }],
        'interactive': ['error', { maxNumericValue: 3800 }],
        'speed-index': ['error', { maxNumericValue: 3400 }],
        
        // Performance Score
        'categories:performance': ['error', { minScore: 0.9 }],
        
        // Accessibility
        'categories:accessibility': ['error', { minScore: 0.95 }],
        
        // Best Practices
        'categories:best-practices': ['error', { minScore: 0.95 }],
        
        // SEO
        'categories:seo': ['error', { minScore: 0.9 }],
        
        // PWA (if applicable)
        'categories:pwa': ['warn', { minScore: 0.9 }],
        
        // Resource budgets
        'resource-summary:script:size': ['error', { maxNumericValue: 300000 }], // 300KB
        'resource-summary:stylesheet:size': ['error', { maxNumericValue: 100000 }], // 100KB
        'resource-summary:image:size': ['error', { maxNumericValue: 500000 }], // 500KB
        'resource-summary:font:size': ['error', { maxNumericValue: 150000 }], // 150KB
        'resource-summary:total:size': ['error', { maxNumericValue: 1500000 }], // 1.5MB
        
        // JavaScript execution
        'mainthread-work-breakdown': ['error', { maxNumericValue: 2000 }],
        'bootup-time': ['error', { maxNumericValue: 2000 }],
        
        // Network
        'network-requests': ['warn', { maxNumericValue: 50 }],
        'network-rtt': ['warn', { maxNumericValue: 100 }],
        
        // Images
        'uses-responsive-images': 'error',
        'uses-optimized-images': 'error',
        'uses-webp-images': 'warn',
        'image-aspect-ratio': 'warn',
        
        // Caching
        'uses-long-cache-ttl': 'warn',
        'efficient-animated-content': 'warn',
        
        // JavaScript
        'no-unload-listeners': 'error',
        'unused-javascript': ['warn', { maxLength: 2 }],
        'legacy-javascript': 'error',
        
        // Security
        'is-on-https': 'error',
        'geolocation-on-start': 'error',
        'notification-on-start': 'error',
        
        // Mobile specific
        'viewport': 'error',
        'content-width': 'error',
        
        // Third-party
        'third-party-summary': ['warn', { maxLength: 5 }],
      },
    },
    upload: {
      // Configure where to upload results (optional)
      target: 'temporary-public-storage',
    },
  },
};