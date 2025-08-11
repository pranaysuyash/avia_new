/**
 * Performance Monitoring Utilities
 * Tracks and reports Core Web Vitals and custom metrics
 */

import React from 'react';
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
}

interface PerformanceBudget {
  metric: string;
  budget: number;
  unit?: string;
}

// Performance budgets aligned with Lighthouse CI
const PERFORMANCE_BUDGETS: PerformanceBudget[] = [
  { metric: 'FCP', budget: 1800, unit: 'ms' },
  { metric: 'LCP', budget: 2500, unit: 'ms' },
  { metric: 'CLS', budget: 0.1 },
  { metric: 'FID', budget: 100, unit: 'ms' },
  { metric: 'TTFB', budget: 800, unit: 'ms' },
];

class PerformanceMonitor {
  private metrics: Map<string, PerformanceMetric> = new Map();
  private observers: Map<string, PerformanceObserver> = new Map();
  private reportCallback?: (metrics: PerformanceMetric[]) => void;

  constructor() {
    this.initializeWebVitals();
    this.initializeCustomMetrics();
  }

  /**
   * Initialize Core Web Vitals tracking
   */
  private initializeWebVitals() {
    // Track Core Web Vitals
    getCLS(this.handleMetric.bind(this));
    getFID(this.handleMetric.bind(this));
    getFCP(this.handleMetric.bind(this));
    getLCP(this.handleMetric.bind(this));
    getTTFB(this.handleMetric.bind(this));
  }

  /**
   * Initialize custom performance metrics
   */
  private initializeCustomMetrics() {
    // Track JavaScript execution time
    this.measureJavaScriptExecution();
    
    // Track resource loading
    this.measureResourceLoading();
    
    // Track long tasks
    this.measureLongTasks();
    
    // Track memory usage
    this.measureMemoryUsage();
  }

  /**
   * Handle metric reporting
   */
  private handleMetric(metric: PerformanceMetric) {
    this.metrics.set(metric.name, metric);
    
    // Check against budget
    const budget = PERFORMANCE_BUDGETS.find(b => b.metric === metric.name);
    if (budget && metric.value > budget.budget) {
      console.warn(
        `Performance budget exceeded for ${metric.name}: ${metric.value}${budget.unit || ''} (budget: ${budget.budget}${budget.unit || ''})`
      );
    }
    
    // Report if callback is set
    if (this.reportCallback) {
      this.reportCallback(Array.from(this.metrics.values()));
    }
  }

  /**
   * Measure JavaScript execution time
   */
  private measureJavaScriptExecution() {
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'measure') {
            this.handleMetric({
              name: `JS:${entry.name}`,
              value: entry.duration,
              rating: entry.duration < 50 ? 'good' : entry.duration < 100 ? 'needs-improvement' : 'poor',
              delta: 0,
              id: `js-${Date.now()}`,
            });
          }
        }
      });
      
      observer.observe({ entryTypes: ['measure'] });
      this.observers.set('js-execution', observer);
    }
  }

  /**
   * Measure resource loading performance
   */
  private measureResourceLoading() {
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'resource') {
            const resourceEntry = entry as PerformanceResourceTiming;
            const loadTime = resourceEntry.responseEnd - resourceEntry.startTime;
            
            // Track slow resources
            if (loadTime > 1000) {
              this.handleMetric({
                name: `Resource:${resourceEntry.name.split('/').pop()}`,
                value: loadTime,
                rating: loadTime < 1000 ? 'good' : loadTime < 2000 ? 'needs-improvement' : 'poor',
                delta: 0,
                id: `resource-${Date.now()}`,
              });
            }
          }
        }
      });
      
      observer.observe({ entryTypes: ['resource'] });
      this.observers.set('resource-loading', observer);
    }
  }

  /**
   * Measure long tasks that block the main thread
   */
  private measureLongTasks() {
    if ('PerformanceObserver' in window && 'PerformanceLongTaskTiming' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.handleMetric({
            name: 'LongTask',
            value: entry.duration,
            rating: entry.duration < 50 ? 'good' : entry.duration < 100 ? 'needs-improvement' : 'poor',
            delta: 0,
            id: `longtask-${Date.now()}`,
          });
        }
      });
      
      try {
        observer.observe({ entryTypes: ['longtask'] });
        this.observers.set('long-tasks', observer);
      } catch (e) {
        // Long task timing not supported
      }
    }
  }

  /**
   * Measure memory usage
   */
  private measureMemoryUsage() {
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        const usedMemoryMB = memory.usedJSHeapSize / 1048576;
        
        this.handleMetric({
          name: 'MemoryUsage',
          value: usedMemoryMB,
          rating: usedMemoryMB < 50 ? 'good' : usedMemoryMB < 100 ? 'needs-improvement' : 'poor',
          delta: 0,
          id: `memory-${Date.now()}`,
        });
      }, 10000); // Check every 10 seconds
    }
  }

  /**
   * Mark the start of a custom performance measurement
   */
  public markStart(name: string) {
    performance.mark(`${name}-start`);
  }

  /**
   * Mark the end of a custom performance measurement
   */
  public markEnd(name: string) {
    performance.mark(`${name}-end`);
    performance.measure(name, `${name}-start`, `${name}-end`);
  }

  /**
   * Set callback for metric reporting
   */
  public onMetricReport(callback: (metrics: PerformanceMetric[]) => void) {
    this.reportCallback = callback;
  }

  /**
   * Get all collected metrics
   */
  public getMetrics(): PerformanceMetric[] {
    return Array.from(this.metrics.values());
  }

  /**
   * Get metrics that exceed budget
   */
  public getBudgetViolations(): Array<PerformanceMetric & { budget: number }> {
    const violations: Array<PerformanceMetric & { budget: number }> = [];
    
    for (const [name, metric] of this.metrics) {
      const budget = PERFORMANCE_BUDGETS.find(b => b.metric === name);
      if (budget && metric.value > budget.budget) {
        violations.push({ ...metric, budget: budget.budget });
      }
    }
    
    return violations;
  }

  /**
   * Clear all observers
   */
  public disconnect() {
    for (const observer of this.observers.values()) {
      observer.disconnect();
    }
    this.observers.clear();
  }
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Export utility functions
export function measurePerformance<T>(
  name: string,
  fn: () => T | Promise<T>
): T | Promise<T> {
  performanceMonitor.markStart(name);
  
  const result = fn();
  
  if (result instanceof Promise) {
    return result.finally(() => {
      performanceMonitor.markEnd(name);
    });
  } else {
    performanceMonitor.markEnd(name);
    return result;
  }
}

// React hook for performance monitoring
export function usePerformanceMonitor() {
  const [metrics, setMetrics] = React.useState<PerformanceMetric[]>([]);
  const [violations, setViolations] = React.useState<Array<PerformanceMetric & { budget: number }>>([]);
  
  React.useEffect(() => {
    performanceMonitor.onMetricReport((newMetrics) => {
      setMetrics(newMetrics);
      setViolations(performanceMonitor.getBudgetViolations());
    });
    
    return () => {
      performanceMonitor.disconnect();
    };
  }, []);
  
  return { metrics, violations };
}