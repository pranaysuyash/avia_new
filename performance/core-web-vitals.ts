/**
 * Core Web Vitals Performance Optimization
 * Monitoring and optimization utilities for web performance
 * Focuses on LCP, FID, CLS metrics
 */

// Performance measurement interfaces
interface PerformanceMetrics {
  lcp?: number;          // Largest Contentful Paint
  fid?: number;          // First Input Delay
  cls?: number;          // Cumulative Layout Shift
  fcp?: number;          // First Contentful Paint
  ttfb?: number;         // Time to First Byte
  inp?: number;          // Interaction to Next Paint
}

interface PerformanceThresholds {
  lcp: { good: number; poor: number };
  fid: { good: number; poor: number };
  cls: { good: number; poor: number };
  fcp: { good: number; poor: number };
  ttfb: { good: number; poor: number };
  inp: { good: number; poor: number };
}

// Core Web Vitals thresholds (in milliseconds, except CLS which is unitless)
export const PERFORMANCE_THRESHOLDS: PerformanceThresholds = {
  lcp: { good: 2500, poor: 4000 },      // Largest Contentful Paint
  fid: { good: 100, poor: 300 },        // First Input Delay
  cls: { good: 0.1, poor: 0.25 },       // Cumulative Layout Shift
  fcp: { good: 1800, poor: 3000 },      // First Contentful Paint
  ttfb: { good: 800, poor: 1800 },      // Time to First Byte
  inp: { good: 200, poor: 500 }         // Interaction to Next Paint
};

/**
 * Performance monitoring class
 */
export class PerformanceMonitor {
  private metrics: PerformanceMetrics = {};
  private observers: PerformanceObserver[] = [];
  private callbacks: Array<(metrics: PerformanceMetrics) => void> = [];

  constructor() {
    this.initializeObservers();
  }

  /**
   * Initialize performance observers
   */
  private initializeObservers(): void {
    if (typeof window === 'undefined') return;

    try {
      // Largest Contentful Paint (LCP)
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1] as any;
        this.metrics.lcp = lastEntry.startTime;
        this.notifyCallbacks();
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers.push(lcpObserver);

      // First Input Delay (FID)
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          this.metrics.fid = entry.processingStart - entry.startTime;
          this.notifyCallbacks();
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });
      this.observers.push(fidObserver);

      // Cumulative Layout Shift (CLS)
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
            this.metrics.cls = clsValue;
            this.notifyCallbacks();
          }
        });
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
      this.observers.push(clsObserver);

      // First Contentful Paint (FCP)
      const fcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (entry.name === 'first-contentful-paint') {
            this.metrics.fcp = entry.startTime;
            this.notifyCallbacks();
          }
        });
      });
      fcpObserver.observe({ entryTypes: ['paint'] });
      this.observers.push(fcpObserver);

      // Navigation timing for TTFB
      this.measureTTFB();

    } catch (error) {
      console.warn('Performance observers not supported:', error);
    }
  }

  /**
   * Measure Time to First Byte (TTFB)
   */
  private measureTTFB(): void {
    if (typeof window === 'undefined') return;

    const navigation = performance.getEntriesByType('navigation')[0] as any;
    if (navigation) {
      this.metrics.ttfb = navigation.responseStart - navigation.requestStart;
      this.notifyCallbacks();
    }
  }

  /**
   * Subscribe to performance metric updates
   */
  public subscribe(callback: (metrics: PerformanceMetrics) => void): () => void {
    this.callbacks.push(callback);
    
    // Return unsubscribe function
    return () => {
      const index = this.callbacks.indexOf(callback);
      if (index > -1) {
        this.callbacks.splice(index, 1);
      }
    };
  }

  /**
   * Notify all callbacks with current metrics
   */
  private notifyCallbacks(): void {
    this.callbacks.forEach(callback => callback({ ...this.metrics }));
  }

  /**
   * Get current metrics
   */
  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  /**
   * Get performance score (0-100)
   */
  public getScore(): number {
    const metrics = this.getMetrics();
    let score = 0;
    let count = 0;

    // Score each metric
    Object.entries(PERFORMANCE_THRESHOLDS).forEach(([key, thresholds]) => {
      const value = metrics[key as keyof PerformanceMetrics];
      if (value !== undefined) {
        if (value <= thresholds.good) {
          score += 100;
        } else if (value <= thresholds.poor) {
          score += 50;
        } else {
          score += 0;
        }
        count++;
      }
    });

    return count > 0 ? Math.round(score / count) : 0;
  }

  /**
   * Get performance grade (A-F)
   */
  public getGrade(): string {
    const score = this.getScore();
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  }

  /**
   * Cleanup observers
   */
  public destroy(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.callbacks = [];
  }
}

/**
 * Performance optimization utilities
 */
export const performanceOptimizations = {
  /**
   * Lazy load images with intersection observer
   */
  lazyLoadImages: (selector: string = 'img[data-src]'): void => {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) return;

    const images = document.querySelectorAll(selector);
    
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement;
          const src = img.getAttribute('data-src');
          if (src) {
            img.src = src;
            img.removeAttribute('data-src');
            imageObserver.unobserve(img);
          }
        }
      });
    }, {
      rootMargin: '50px 0px'
    });

    images.forEach(img => imageObserver.observe(img));
  },

  /**
   * Preload critical resources
   */
  preloadCriticalResources: (resources: Array<{ href: string; as: string; type?: string }>): void => {
    if (typeof document === 'undefined') return;

    resources.forEach(resource => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = resource.href;
      link.as = resource.as;
      if (resource.type) {
        link.type = resource.type;
      }
      document.head.appendChild(link);
    });
  },

  /**
   * Optimize font loading
   */
  optimizeFontLoading: (fontFaces: Array<{ family: string; url: string; weight?: string }>): void => {
    if (typeof document === 'undefined') return;

    fontFaces.forEach(font => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = font.url;
      link.as = 'font';
      link.type = 'font/woff2';
      link.crossOrigin = 'anonymous';
      document.head.appendChild(link);
    });
  },

  /**
   * Debounce function for performance
   */
  debounce: <T extends (...args: any[]) => void>(
    func: T,
    wait: number
  ): (...args: Parameters<T>) => void => {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(null, args), wait);
    };
  },

  /**
   * Throttle function for performance
   */
  throttle: <T extends (...args: any[]) => void>(
    func: T,
    limit: number
  ): (...args: Parameters<T>) => void => {
    let inThrottle: boolean;
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func.apply(null, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  /**
   * Virtual scrolling for large lists
   */
  createVirtualScroller: (options: {
    container: HTMLElement;
    itemHeight: number;
    items: any[];
    renderItem: (item: any, index: number) => HTMLElement;
    bufferSize?: number;
  }) => {
    const { container, itemHeight, items, renderItem, bufferSize = 5 } = options;
    
    let scrollTop = 0;
    let containerHeight = container.clientHeight;
    
    const totalHeight = items.length * itemHeight;
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    
    const update = () => {
      const startIndex = Math.floor(scrollTop / itemHeight);
      const endIndex = Math.min(startIndex + visibleCount + bufferSize, items.length);
      
      container.innerHTML = '';
      container.style.height = `${totalHeight}px`;
      container.style.position = 'relative';
      
      for (let i = Math.max(0, startIndex - bufferSize); i < endIndex; i++) {
        const item = renderItem(items[i], i);
        item.style.position = 'absolute';
        item.style.top = `${i * itemHeight}px`;
        item.style.height = `${itemHeight}px`;
        container.appendChild(item);
      }
    };
    
    const onScroll = performanceOptimizations.throttle(() => {
      scrollTop = container.scrollTop;
      update();
    }, 16);
    
    const onResize = performanceOptimizations.debounce(() => {
      containerHeight = container.clientHeight;
      update();
    }, 250);
    
    container.addEventListener('scroll', onScroll);
    window.addEventListener('resize', onResize);
    
    update();
    
    return {
      update,
      destroy: () => {
        container.removeEventListener('scroll', onScroll);
        window.removeEventListener('resize', onResize);
      }
    };
  }
};

/**
 * Resource loading optimizations
 */
export const resourceOptimizations = {
  /**
   * Load scripts asynchronously
   */
  loadScript: (src: string, async: boolean = true): Promise<void> => {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.async = async;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
      document.head.appendChild(script);
    });
  },

  /**
   * Load CSS asynchronously
   */
  loadCSS: (href: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.onload = () => resolve();
      link.onerror = () => reject(new Error(`Failed to load CSS: ${href}`));
      document.head.appendChild(link);
    });
  },

  /**
   * Preconnect to external domains
   */
  preconnect: (domains: string[]): void => {
    if (typeof document === 'undefined') return;

    domains.forEach(domain => {
      const link = document.createElement('link');
      link.rel = 'preconnect';
      link.href = domain;
      document.head.appendChild(link);
    });
  },

  /**
   * Service Worker registration for caching
   */
  registerServiceWorker: async (swPath: string = '/sw.js'): Promise<ServiceWorkerRegistration | null> => {
    if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
      return null;
    }

    try {
      const registration = await navigator.serviceWorker.register(swPath);
      console.log('Service Worker registered:', registration);
      return registration;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      return null;
    }
  }
};

/**
 * Performance monitoring hook for React
 */
export const usePerformanceMonitor = () => {
  const [metrics, setMetrics] = React.useState<PerformanceMetrics>({});
  const [monitor] = React.useState(() => new PerformanceMonitor());

  React.useEffect(() => {
    const unsubscribe = monitor.subscribe(setMetrics);
    return () => {
      unsubscribe();
      monitor.destroy();
    };
  }, [monitor]);

  return {
    metrics,
    score: monitor.getScore(),
    grade: monitor.getGrade(),
    isGood: (metric: keyof PerformanceMetrics) => {
      const value = metrics[metric];
      const threshold = PERFORMANCE_THRESHOLDS[metric];
      return value !== undefined && threshold && value <= threshold.good;
    },
    isPoor: (metric: keyof PerformanceMetrics) => {
      const value = metrics[metric];
      const threshold = PERFORMANCE_THRESHOLDS[metric];
      return value !== undefined && threshold && value > threshold.poor;
    }
  };
};

/**
 * Performance reporting utilities
 */
export const performanceReporting = {
  /**
   * Send performance metrics to analytics
   */
  reportMetrics: (metrics: PerformanceMetrics, endpoint?: string): void => {
    if (!endpoint) return;

    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...metrics,
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        url: window.location.href
      })
    }).catch(error => {
      console.warn('Failed to report performance metrics:', error);
    });
  },

  /**
   * Generate performance report
   */
  generateReport: (metrics: PerformanceMetrics): string => {
    const monitor = new PerformanceMonitor();
    const score = monitor.getScore();
    const grade = monitor.getGrade();

    let report = `# Performance Report\n\n`;
    report += `**Overall Score: ${score}/100 (Grade: ${grade})**\n\n`;

    report += `## Core Web Vitals\n\n`;

    Object.entries(PERFORMANCE_THRESHOLDS).forEach(([key, thresholds]) => {
      const value = metrics[key as keyof PerformanceMetrics];
      if (value !== undefined) {
        const status = value <= thresholds.good ? '🟢 Good' : 
                      value <= thresholds.poor ? '🟡 Needs Improvement' : '🔴 Poor';
        
        const unit = key === 'cls' ? '' : 'ms';
        report += `- **${key.toUpperCase()}**: ${value}${unit} (${status})\n`;
      }
    });

    report += `\n## Recommendations\n\n`;
    
    if (metrics.lcp && metrics.lcp > PERFORMANCE_THRESHOLDS.lcp.good) {
      report += `- **Improve LCP**: Optimize images, preload critical resources, reduce server response times\n`;
    }
    
    if (metrics.fid && metrics.fid > PERFORMANCE_THRESHOLDS.fid.good) {
      report += `- **Improve FID**: Reduce JavaScript execution time, defer non-critical scripts\n`;
    }
    
    if (metrics.cls && metrics.cls > PERFORMANCE_THRESHOLDS.cls.good) {
      report += `- **Improve CLS**: Set dimensions for images/videos, avoid inserting content above existing content\n`;
    }

    return report;
  }
};

// Global performance monitor instance
export const globalPerformanceMonitor = new PerformanceMonitor();

export default {
  PerformanceMonitor,
  performanceOptimizations,
  resourceOptimizations,
  performanceReporting,
  usePerformanceMonitor,
  PERFORMANCE_THRESHOLDS
};