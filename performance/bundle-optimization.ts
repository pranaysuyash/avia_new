/**
 * Bundle Optimization Utilities
 * Code splitting, lazy loading, and bundle analysis tools
 * Optimize JavaScript and CSS bundles for better performance
 */

import React from 'react';

// Bundle analysis interfaces
interface BundleAnalysis {
  totalSize: number;
  chunks: Array<{
    name: string;
    size: number;
    modules: string[];
  }>;
  duplicates: Array<{
    module: string;
    chunks: string[];
    size: number;
  }>;
  recommendations: string[];
}

interface LazyComponentOptions {
  fallback?: React.ComponentType;
  retryCount?: number;
  retryDelay?: number;
}

/**
 * Code splitting utilities
 */
export const codeSplitting = {
  /**
   * Create a lazy-loaded component with error boundary
   */
  createLazyComponent: <T extends React.ComponentType<any>>(
    importFn: () => Promise<{ default: T }>,
    options: LazyComponentOptions = {}
  ): React.ComponentType<React.ComponentProps<T>> => {
    const {
      fallback: Fallback = () => <div>Loading...</div>,
      retryCount = 3,
      retryDelay = 1000
    } = options;

    let retries = 0;

    const LazyComponent = React.lazy(async () => {
      try {
        return await importFn();
      } catch (error) {
        if (retries < retryCount) {
          retries++;
          await new Promise(resolve => setTimeout(resolve, retryDelay));
          return importFn();
        }
        throw error;
      }
    });

    return (props: React.ComponentProps<T>) => (
      <React.Suspense fallback={<Fallback />}>
        <LazyComponent {...props} />
      </React.Suspense>
    );
  },

  /**
   * Route-based code splitting
   */
  createLazyRoute: (
    importFn: () => Promise<{ default: React.ComponentType<any> }>,
    fallback?: React.ComponentType
  ) => {
    const LazyRoute = React.lazy(importFn);
    
    return (props: any) => (
      <React.Suspense 
        fallback={
          fallback ? <fallback /> : 
          <div className="flex items-center justify-center min-h-[200px]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-DEFAULT"></div>
          </div>
        }
      >
        <LazyRoute {...props} />
      </React.Suspense>
    );
  },

  /**
   * Feature-based code splitting
   */
  createFeatureLoader: (features: Record<string, () => Promise<any>>) => {
    const loadedFeatures = new Map<string, any>();
    const loadingFeatures = new Map<string, Promise<any>>();

    return {
      load: async <T>(featureName: string): Promise<T> => {
        // Return if already loaded
        if (loadedFeatures.has(featureName)) {
          return loadedFeatures.get(featureName);
        }

        // Return existing loading promise
        if (loadingFeatures.has(featureName)) {
          return loadingFeatures.get(featureName);
        }

        // Start loading
        const loader = features[featureName];
        if (!loader) {
          throw new Error(`Feature "${featureName}" not found`);
        }

        const loadingPromise = loader().then(module => {
          const feature = module.default || module;
          loadedFeatures.set(featureName, feature);
          loadingFeatures.delete(featureName);
          return feature;
        });

        loadingFeatures.set(featureName, loadingPromise);
        return loadingPromise;
      },

      isLoaded: (featureName: string): boolean => {
        return loadedFeatures.has(featureName);
      },

      preload: async (featureNames: string[]): Promise<void> => {
        await Promise.all(
          featureNames.map(name => this.load(name).catch(() => {}))
        );
      }
    };
  }
};

/**
 * Resource optimization utilities
 */
export const resourceOptimization = {
  /**
   * Preload critical chunks
   */
  preloadChunks: (chunkNames: string[]): void => {
    if (typeof document === 'undefined') return;

    chunkNames.forEach(chunkName => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'script';
      link.href = `/chunks/${chunkName}.js`;
      document.head.appendChild(link);
    });
  },

  /**
   * Prefetch non-critical chunks
   */
  prefetchChunks: (chunkNames: string[]): void => {
    if (typeof document === 'undefined') return;

    chunkNames.forEach(chunkName => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = `/chunks/${chunkName}.js`;
      document.head.appendChild(link);
    });
  },

  /**
   * Dynamic import with retry logic
   */
  dynamicImport: async <T>(
    importFn: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> => {
    let lastError: Error;

    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await importFn();
      } catch (error) {
        lastError = error as Error;
        
        if (i < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
        }
      }
    }

    throw lastError!;
  },

  /**
   * Module federation loader
   */
  loadRemoteModule: async (remoteName: string, moduleName: string): Promise<any> => {
    // @ts-ignore - Module federation specific
    const remote = window[remoteName];
    
    if (!remote) {
      throw new Error(`Remote "${remoteName}" not found`);
    }

    try {
      await remote.init();
      const factory = await remote.get(moduleName);
      return factory();
    } catch (error) {
      throw new Error(`Failed to load remote module "${moduleName}" from "${remoteName}"`);
    }
  }
};

/**
 * Bundle analysis utilities
 */
export const bundleAnalysis = {
  /**
   * Analyze bundle composition
   */
  analyzeBundles: async (): Promise<BundleAnalysis> => {
    // This would typically integrate with webpack-bundle-analyzer or similar
    const analysis: BundleAnalysis = {
      totalSize: 0,
      chunks: [],
      duplicates: [],
      recommendations: []
    };

    // Simulate analysis (in real implementation, this would parse actual bundle data)
    if (typeof window !== 'undefined' && 'performance' in window) {
      const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
      
      resources.forEach(resource => {
        if (resource.name.includes('.js') || resource.name.includes('.css')) {
          analysis.totalSize += resource.transferSize || 0;
        }
      });
    }

    // Add recommendations based on analysis
    if (analysis.totalSize > 1024 * 1024) { // > 1MB
      analysis.recommendations.push('Consider code splitting to reduce initial bundle size');
    }

    return analysis;
  },

  /**
   * Identify unused code
   */
  findUnusedCode: (): Promise<string[]> => {
    return new Promise((resolve) => {
      // This would integrate with tools like webpack-unused or coverage APIs
      const unused: string[] = [];
      
      // Simulate finding unused modules
      if (typeof window !== 'undefined') {
        // Check for unused CSS
        const styleSheets = Array.from(document.styleSheets);
        styleSheets.forEach(sheet => {
          try {
            const rules = Array.from(sheet.cssRules || []);
            rules.forEach(rule => {
              if (rule.type === CSSRule.STYLE_RULE) {
                const styleRule = rule as CSSStyleRule;
                const elements = document.querySelectorAll(styleRule.selectorText);
                if (elements.length === 0) {
                  unused.push(`Unused CSS rule: ${styleRule.selectorText}`);
                }
              }
            });
          } catch (e) {
            // Skip cross-origin stylesheets
          }
        });
      }

      resolve(unused);
    });
  },

  /**
   * Generate optimization report
   */
  generateOptimizationReport: async (): Promise<string> => {
    const analysis = await bundleAnalysis.analyzeBundles();
    const unused = await bundleAnalysis.findUnusedCode();

    let report = `# Bundle Optimization Report\n\n`;
    
    report += `## Bundle Size Analysis\n`;
    report += `- **Total Size**: ${(analysis.totalSize / 1024).toFixed(2)} KB\n`;
    report += `- **Chunks**: ${analysis.chunks.length}\n`;
    report += `- **Duplicates Found**: ${analysis.duplicates.length}\n\n`;

    if (analysis.recommendations.length > 0) {
      report += `## Recommendations\n`;
      analysis.recommendations.forEach(rec => {
        report += `- ${rec}\n`;
      });
      report += `\n`;
    }

    if (unused.length > 0) {
      report += `## Unused Code (${unused.length} items)\n`;
      unused.slice(0, 10).forEach(item => {
        report += `- ${item}\n`;
      });
      if (unused.length > 10) {
        report += `- ... and ${unused.length - 10} more\n`;
      }
    }

    return report;
  }
};

/**
 * Tree shaking utilities
 */
export const treeShaking = {
  /**
   * Mark functions for tree shaking
   */
  markAsTreeShakeable: (module: any): void => {
    // Add sideEffects: false marker
    if (typeof module === 'object' && module !== null) {
      module.__esModule = true;
    }
  },

  /**
   * Create tree-shakeable utility exports
   */
  createTreeShakeableExport: <T extends Record<string, any>>(
    utilities: T
  ): T => {
    // Ensure each utility is individually exportable
    const treeShakeableUtilities = {} as T;
    
    Object.keys(utilities).forEach(key => {
      treeShakeableUtilities[key] = utilities[key];
    });

    return treeShakeableUtilities;
  }
};

/**
 * Progressive loading utilities
 */
export const progressiveLoading = {
  /**
   * Load resources progressively based on priority
   */
  loadProgressively: async (
    resources: Array<{
      url: string;
      priority: 'high' | 'medium' | 'low';
      type: 'script' | 'style' | 'image';
    }>
  ): Promise<void> => {
    const priorities = {
      high: resources.filter(r => r.priority === 'high'),
      medium: resources.filter(r => r.priority === 'medium'),
      low: resources.filter(r => r.priority === 'low')
    };

    // Load high priority first
    await Promise.all(priorities.high.map(resource => loadResource(resource)));
    
    // Then medium priority
    await Promise.all(priorities.medium.map(resource => loadResource(resource)));
    
    // Finally low priority (can be deferred)
    setTimeout(() => {
      Promise.all(priorities.low.map(resource => loadResource(resource)));
    }, 100);
  },

  /**
   * Adaptive loading based on connection
   */
  adaptiveLoad: (
    fastContent: () => Promise<any>,
    slowContent: () => Promise<any>
  ): Promise<any> => {
    // @ts-ignore - Not all browsers support this yet
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    
    const isSlowConnection = connection && (
      connection.effectiveType === '2g' ||
      connection.effectiveType === 'slow-2g' ||
      connection.saveData
    );

    return isSlowConnection ? slowContent() : fastContent();
  },

  /**
   * Intersection-based loading
   */
  createIntersectionLoader: (
    callback: () => Promise<void>,
    options: IntersectionObserverInit = {}
  ) => {
    return (element: Element) => {
      if (typeof IntersectionObserver === 'undefined') {
        // Fallback for unsupported browsers
        callback();
        return;
      }

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              callback();
              observer.unobserve(entry.target);
            }
          });
        },
        {
          rootMargin: '50px',
          ...options
        }
      );

      observer.observe(element);
      
      return () => observer.unobserve(element);
    };
  }
};

/**
 * Helper function to load individual resources
 */
function loadResource(resource: { url: string; type: string }): Promise<void> {
  return new Promise((resolve, reject) => {
    if (resource.type === 'script') {
      const script = document.createElement('script');
      script.src = resource.url;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error(`Failed to load script: ${resource.url}`));
      document.head.appendChild(script);
    } else if (resource.type === 'style') {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = resource.url;
      link.onload = () => resolve();
      link.onerror = () => reject(new Error(`Failed to load stylesheet: ${resource.url}`));
      document.head.appendChild(link);
    } else if (resource.type === 'image') {
      const img = new Image();
      img.onload = () => resolve();
      img.onerror = () => reject(new Error(`Failed to load image: ${resource.url}`));
      img.src = resource.url;
    } else {
      resolve();
    }
  });
}

/**
 * React hooks for bundle optimization
 */
export const useBundleOptimization = () => {
  const [isLoading, setIsLoading] = React.useState(false);
  const [loadedModules, setLoadedModules] = React.useState<Set<string>>(new Set());

  const loadModule = React.useCallback(async (
    moduleName: string,
    importFn: () => Promise<any>
  ) => {
    if (loadedModules.has(moduleName)) {
      return;
    }

    setIsLoading(true);
    try {
      await resourceOptimization.dynamicImport(importFn);
      setLoadedModules(prev => new Set([...prev, moduleName]));
    } finally {
      setIsLoading(false);
    }
  }, [loadedModules]);

  return {
    isLoading,
    loadedModules: Array.from(loadedModules),
    loadModule,
    isModuleLoaded: (moduleName: string) => loadedModules.has(moduleName)
  };
};

export default {
  codeSplitting,
  resourceOptimization,
  bundleAnalysis,
  treeShaking,
  progressiveLoading,
  useBundleOptimization
};