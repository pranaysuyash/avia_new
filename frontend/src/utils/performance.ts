/**
 * Performance monitoring utilities
 * Tracks Web Vitals and custom metrics
 */

import { getCLS, getFCP, getFID, getLCP, getTTFB } from 'web-vitals';
import * as Sentry from '@sentry/react';

// Performance observer types
type MetricType = 'CLS' | 'FCP' | 'FID' | 'LCP' | 'TTFB';
type MetricValue = number;

interface PerformanceMetric {
  name: MetricType;
  value: MetricValue;
  rating: 'good' | 'needs-improvement' | 'poor';
  timestamp: number;
}

interface PerformanceReport {
  metrics: PerformanceMetric[];
  url: string;
  userAgent: string;
  connectionType?: string;
  timestamp: number;
}

// Thresholds for Web Vitals (in milliseconds)
const THRESHOLDS = {
  CLS: { good: 0.1, poor: 0.25 },
  FCP: { good: 1800, poor: 3000 },
  FID: { good: 100, poor: 300 },
  LCP: { good: 2500, poor: 4000 },
  TTFB: { good: 800, poor: 1800 },
};

// Calculate rating based on value and thresholds
function getRating(name: MetricType, value: number): 'good' | 'needs-improvement' | 'poor' {
  const threshold = THRESHOLDS[name];
  if (value <= threshold.good) return 'good';
  if (value <= threshold.poor) return 'needs-improvement';
  return 'poor';
}

// Collect and report Web Vitals
export function initWebVitals(onReport?: (metric: PerformanceMetric) => void) {
  const reportMetric = (name: MetricType, value: number) => {
    const metric: PerformanceMetric = {
      name,
      value,
      rating: getRating(name, value),
      timestamp: Date.now(),
    };

    // Report to callback
    if (onReport) {
      onReport(metric);
    }

    // Report to Sentry
    Sentry.addBreadcrumb({
      category: 'web-vitals',
      message: `${name}: ${value}`,
      level: metric.rating === 'poor' ? 'warning' : 'info',
      data: metric,
    });

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      const emoji = metric.rating === 'good' ? '✅' : metric.rating === 'poor' ? '❌' : '⚠️';
      console.log(`${emoji} ${name}: ${value.toFixed(2)}ms (${metric.rating})`);
    }
  };

  // Collect Web Vitals
  getCLS((metric) => reportMetric('CLS', metric.value * 1000)); // Convert to ms
  getFCP((metric) => reportMetric('FCP', metric.value));
  getFID((metric) => reportMetric('FID', metric.value));
  getLCP((metric) => reportMetric('LCP', metric.value));
  getTTFB((metric) => reportMetric('TTFB', metric.value));
}

// Custom performance marks and measures
class PerformanceTracker {
  private marks: Map<string, number> = new Map();
  private measures: Map<string, number[]> = new Map();

  // Mark a point in time
  mark(name: string) {
    const timestamp = performance.now();
    this.marks.set(name, timestamp);
    
    if (window.performance && window.performance.mark) {
      window.performance.mark(name);
    }
  }

  // Measure between two marks
  measure(name: string, startMark: string, endMark?: string) {
    const start = this.marks.get(startMark);
    const end = endMark ? this.marks.get(endMark) : performance.now();

    if (!start) {
      console.warn(`Start mark "${startMark}" not found`);
      return;
    }

    const duration = (end || performance.now()) - start;
    
    // Store measure
    if (!this.measures.has(name)) {
      this.measures.set(name, []);
    }
    this.measures.get(name)?.push(duration);

    // Native performance API
    if (window.performance && window.performance.measure) {
      try {
        window.performance.measure(name, startMark, endMark);
      } catch (e) {
        // Marks might not exist in native API
      }
    }

    // Report to Sentry
    Sentry.addBreadcrumb({
      category: 'performance',
      message: `${name}: ${duration.toFixed(2)}ms`,
      level: 'info',
      data: { name, duration, startMark, endMark },
    });

    return duration;
  }

  // Get average duration for a measure
  getAverage(name: string): number | null {
    const measures = this.measures.get(name);
    if (!measures || measures.length === 0) return null;
    
    const sum = measures.reduce((a, b) => a + b, 0);
    return sum / measures.length;
  }

  // Get all measures
  getMeasures(): Record<string, { count: number; average: number; total: number }> {
    const result: Record<string, { count: number; average: number; total: number }> = {};
    
    this.measures.forEach((values, name) => {
      const total = values.reduce((a, b) => a + b, 0);
      result[name] = {
        count: values.length,
        average: total / values.length,
        total,
      };
    });
    
    return result;
  }

  // Clear all marks and measures
  clear() {
    this.marks.clear();
    this.measures.clear();
    
    if (window.performance && window.performance.clearMarks) {
      window.performance.clearMarks();
      window.performance.clearMeasures();
    }
  }
}

// Singleton instance
export const performanceTracker = new PerformanceTracker();

// React component render tracking
export function trackComponentRender(componentName: string) {
  const startMark = `${componentName}-render-start`;
  const endMark = `${componentName}-render-end`;
  const measureName = `${componentName}-render`;

  return {
    start: () => performanceTracker.mark(startMark),
    end: () => {
      performanceTracker.mark(endMark);
      return performanceTracker.measure(measureName, startMark, endMark);
    },
  };
}

// API call performance tracking
export function trackAPICall(endpoint: string) {
  const startMark = `api-${endpoint}-start`;
  const endMark = `api-${endpoint}-end`;
  const measureName = `api-${endpoint}`;

  return {
    start: () => performanceTracker.mark(startMark),
    end: () => {
      performanceTracker.mark(endMark);
      return performanceTracker.measure(measureName, startMark, endMark);
    },
  };
}

// Resource loading tracker
export function trackResourceLoading() {
  if (!window.performance || !window.performance.getEntriesByType) return;

  const resources = window.performance.getEntriesByType('resource');
  
  const summary = resources.reduce((acc, resource: any) => {
    const type = resource.initiatorType || 'other';
    if (!acc[type]) {
      acc[type] = {
        count: 0,
        totalDuration: 0,
        totalSize: 0,
      };
    }
    
    acc[type].count++;
    acc[type].totalDuration += resource.duration;
    acc[type].totalSize += resource.transferSize || 0;
    
    return acc;
  }, {} as Record<string, { count: number; totalDuration: number; totalSize: number }>);

  return summary;
}

// Long task observer
export function observeLongTasks(callback: (duration: number) => void) {
  if (!('PerformanceObserver' in window)) return;

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        // Report tasks longer than 50ms
        if (entry.duration > 50) {
          callback(entry.duration);
          
          // Report to Sentry
          Sentry.addBreadcrumb({
            category: 'performance',
            message: `Long task detected: ${entry.duration.toFixed(2)}ms`,
            level: 'warning',
            data: entry,
          });
        }
      }
    });

    observer.observe({ entryTypes: ['longtask'] });
    
    return () => observer.disconnect();
  } catch (e) {
    console.warn('Long task observer not supported');
  }
}

// Memory usage monitoring
export function getMemoryUsage() {
  if (!('memory' in performance)) return null;
  
  const memory = (performance as any).memory;
  return {
    usedJSHeapSize: memory.usedJSHeapSize,
    totalJSHeapSize: memory.totalJSHeapSize,
    jsHeapSizeLimit: memory.jsHeapSizeLimit,
    percentUsed: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100,
  };
}

// Connection quality monitoring
export function getConnectionInfo() {
  if (!('connection' in navigator)) return null;
  
  const connection = (navigator as any).connection;
  return {
    effectiveType: connection.effectiveType,
    downlink: connection.downlink,
    rtt: connection.rtt,
    saveData: connection.saveData,
  };
}

// Export performance report
export function generatePerformanceReport(): PerformanceReport {
  const metrics: PerformanceMetric[] = [];
  const measures = performanceTracker.getMeasures();
  
  // Add custom measures
  Object.entries(measures).forEach(([name, data]) => {
    metrics.push({
      name: name as MetricType,
      value: data.average,
      rating: 'good', // Custom metrics don't have thresholds
      timestamp: Date.now(),
    });
  });

  return {
    metrics,
    url: window.location.href,
    userAgent: navigator.userAgent,
    connectionType: getConnectionInfo()?.effectiveType,
    timestamp: Date.now(),
  };
}

// Send performance data to analytics
export function reportPerformance(endpoint?: string) {
  const report = generatePerformanceReport();
  
  // Send to your analytics endpoint
  if (endpoint) {
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(report),
    }).catch((error) => {
      console.error('Failed to report performance:', error);
    });
  }
  
  // Report to Sentry
  Sentry.addBreadcrumb({
    category: 'performance',
    message: 'Performance report generated',
    level: 'info',
    data: report,
  });
  
  return report;
}