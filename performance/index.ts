/**
 * Performance Optimization Module
 * Complete performance toolkit for web applications
 * 
 * @fileoverview Performance monitoring, optimization, and bundle analysis
 * @version 1.0.0
 */

// Core Web Vitals monitoring
export {
  PerformanceMonitor,
  performanceOptimizations,
  resourceOptimizations,
  performanceReporting,
  usePerformanceMonitor,
  globalPerformanceMonitor,
  PERFORMANCE_THRESHOLDS
} from './core-web-vitals';

// Bundle optimization
export {
  codeSplitting,
  resourceOptimization,
  bundleAnalysis,
  treeShaking,
  progressiveLoading,
  useBundleOptimization
} from './bundle-optimization';

// Re-export defaults
export { default as coreWebVitals } from './core-web-vitals';
export { default as bundleOptimization } from './bundle-optimization';

/**
 * Quick Start Guide:
 * 
 * 1. Performance Monitoring:
 * ```typescript
 * import { usePerformanceMonitor } from './performance';
 * 
 * function App() {
 *   const { metrics, score, grade } = usePerformanceMonitor();
 *   
 *   return (
 *     <div>
 *       Performance Score: {score}% (Grade: {grade})
 *       LCP: {metrics.lcp}ms
 *     </div>
 *   );
 * }
 * ```
 * 
 * 2. Code Splitting:
 * ```typescript
 * import { codeSplitting } from './performance';
 * 
 * const LazyDashboard = codeSplitting.createLazyComponent(
 *   () => import('./Dashboard'),
 *   { fallback: LoadingSpinner }
 * );
 * ```
 * 
 * 3. Resource Optimization:
 * ```typescript
 * import { performanceOptimizations } from './performance';
 * 
 * // Lazy load images
 * performanceOptimizations.lazyLoadImages();
 * 
 * // Preload critical resources
 * performanceOptimizations.preloadCriticalResources([
 *   { href: '/api/critical-data', as: 'fetch' }
 * ]);
 * ```
 * 
 * 4. Bundle Analysis:
 * ```typescript
 * import { bundleAnalysis } from './performance';
 * 
 * const report = await bundleAnalysis.generateOptimizationReport();
 * console.log(report);
 * ```
 * 
 * 5. Progressive Loading:
 * ```typescript
 * import { progressiveLoading } from './performance';
 * 
 * await progressiveLoading.loadProgressively([
 *   { url: '/critical.js', priority: 'high', type: 'script' },
 *   { url: '/optional.js', priority: 'low', type: 'script' }
 * ]);
 * ```
 */

/**
 * Performance Best Practices Summary:
 * 
 * 🚀 **Core Web Vitals Targets**
 * - LCP (Largest Contentful Paint): < 2.5s
 * - FID (First Input Delay): < 100ms
 * - CLS (Cumulative Layout Shift): < 0.1
 * 
 * 📦 **Bundle Optimization**
 * - Keep initial bundle < 250KB gzipped
 * - Use code splitting for routes and features
 * - Tree shake unused code
 * - Implement progressive loading
 * 
 * 🖼️ **Resource Loading**
 * - Lazy load images and videos
 * - Preload critical resources
 * - Use WebP/AVIF image formats
 * - Compress assets with gzip/brotli
 * 
 * ⚡ **Runtime Performance**
 * - Debounce/throttle event handlers
 * - Use virtual scrolling for large lists
 * - Minimize DOM manipulations
 * - Cache expensive calculations
 * 
 * 🔧 **Development Tools**
 * - Chrome DevTools Performance tab
 * - Lighthouse audits
 * - webpack-bundle-analyzer
 * - Web Vitals extension
 */

/**
 * Common Performance Patterns:
 * 
 * ```typescript
 * // 1. Lazy Route Component
 * const LazyRoute = codeSplitting.createLazyRoute(
 *   () => import('./pages/Dashboard')
 * );
 * 
 * // 2. Performance Monitoring Component
 * function PerformanceWidget() {
 *   const { score, grade, metrics } = usePerformanceMonitor();
 *   
 *   return (
 *     <div className="performance-widget">
 *       <span className={`grade grade-${grade.toLowerCase()}`}>
 *         {grade}
 *       </span>
 *       <span>{score}%</span>
 *     </div>
 *   );
 * }
 * 
 * // 3. Optimized Image Component
 * function OptimizedImage({ src, alt, ...props }) {
 *   return (
 *     <img
 *       data-src={src}
 *       alt={alt}
 *       loading="lazy"
 *       {...props}
 *       onLoad={() => performanceOptimizations.lazyLoadImages()}
 *     />
 *   );
 * }
 * 
 * // 4. Virtual List Component
 * function VirtualList({ items, renderItem }) {
 *   const containerRef = useRef();
 *   
 *   useEffect(() => {
 *     if (containerRef.current) {
 *       const scroller = performanceOptimizations.createVirtualScroller({
 *         container: containerRef.current,
 *         itemHeight: 50,
 *         items,
 *         renderItem
 *       });
 *       
 *       return scroller.destroy;
 *     }
 *   }, [items, renderItem]);
 *   
 *   return <div ref={containerRef} className="virtual-list" />;
 * }
 * ```
 */