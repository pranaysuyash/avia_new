/**
 * Performance Dashboard Component
 * Shows real-time performance metrics and budget violations
 */

import React, { useState, useEffect } from 'react';
import { usePerformanceMonitor } from '../../utils/performanceMonitor';
import { webTheme } from '../../../shared/theme';

interface MetricCardProps {
  name: string;
  value: number;
  unit?: string;
  rating: 'good' | 'needs-improvement' | 'poor';
  budget?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({ name, value, unit = 'ms', rating, budget }) => {
  const getRatingColor = () => {
    switch (rating) {
      case 'good':
        return webTheme.colors.success.DEFAULT;
      case 'needs-improvement':
        return webTheme.colors.warning.DEFAULT;
      case 'poor':
        return webTheme.colors.error.DEFAULT;
    }
  };

  const formatValue = (val: number) => {
    if (unit === 'ms' && val > 1000) {
      return `${(val / 1000).toFixed(2)}s`;
    }
    return `${val.toFixed(2)}${unit}`;
  };

  return (
    <div
      style={{
        padding: webTheme.spacing['4'],
        backgroundColor: webTheme.colors.background.primary,
        borderRadius: webTheme.borderRadius.lg,
        boxShadow: webTheme.boxShadow.sm,
        border: `2px solid ${getRatingColor()}`,
      }}
    >
      <h3
        style={{
          fontSize: webTheme.typography.fontSize.sm,
          fontWeight: webTheme.typography.fontWeight.medium,
          color: webTheme.colors.text.secondary,
          marginBottom: webTheme.spacing['2'],
        }}
      >
        {name}
      </h3>
      <div
        style={{
          fontSize: webTheme.typography.fontSize['2xl'],
          fontWeight: webTheme.typography.fontWeight.bold,
          color: getRatingColor(),
        }}
      >
        {formatValue(value)}
      </div>
      {budget && (
        <div
          style={{
            fontSize: webTheme.typography.fontSize.xs,
            color: webTheme.colors.text.tertiary,
            marginTop: webTheme.spacing['1'],
          }}
        >
          Budget: {formatValue(budget)}
        </div>
      )}
    </div>
  );
};

interface PerformanceDashboardProps {
  showInProduction?: boolean;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  showInProduction = false,
  position = 'bottom-right',
}) => {
  const { metrics, violations } = usePerformanceMonitor();
  const [isMinimized, setIsMinimized] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  // Don't show in production unless explicitly enabled
  useEffect(() => {
    if (process.env.NODE_ENV === 'production' && !showInProduction) {
      setIsVisible(false);
    }
  }, [showInProduction]);

  if (!isVisible) return null;

  const getPositionStyles = () => {
    const base = {
      position: 'fixed' as const,
      zIndex: webTheme.zIndex.tooltip,
    };

    switch (position) {
      case 'top-left':
        return { ...base, top: webTheme.spacing['4'], left: webTheme.spacing['4'] };
      case 'top-right':
        return { ...base, top: webTheme.spacing['4'], right: webTheme.spacing['4'] };
      case 'bottom-left':
        return { ...base, bottom: webTheme.spacing['4'], left: webTheme.spacing['4'] };
      case 'bottom-right':
      default:
        return { ...base, bottom: webTheme.spacing['4'], right: webTheme.spacing['4'] };
    }
  };

  // Core Web Vitals
  const coreWebVitals = ['FCP', 'LCP', 'CLS', 'FID', 'TTFB'];
  const coreMetrics = metrics.filter(m => coreWebVitals.includes(m.name));

  return (
    <div
      style={{
        ...getPositionStyles(),
        backgroundColor: webTheme.colors.background.secondary,
        borderRadius: webTheme.borderRadius.xl,
        boxShadow: webTheme.boxShadow.lg,
        border: `1px solid ${webTheme.colors.border.DEFAULT}`,
        maxWidth: '400px',
        transition: 'all 300ms ease',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: webTheme.spacing['3'],
          borderBottom: `1px solid ${webTheme.colors.border.light}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
        }}
        onClick={() => setIsMinimized(!isMinimized)}
      >
        <h2
          style={{
            fontSize: webTheme.typography.fontSize.base,
            fontWeight: webTheme.typography.fontWeight.semibold,
            color: webTheme.colors.text.primary,
            margin: 0,
          }}
        >
          🚀 Performance Monitor
        </h2>
        <button
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: webTheme.typography.fontSize.lg,
          }}
        >
          {isMinimized ? '▲' : '▼'}
        </button>
      </div>

      {/* Content */}
      {!isMinimized && (
        <div style={{ padding: webTheme.spacing['4'] }}>
          {/* Core Web Vitals */}
          <div style={{ marginBottom: webTheme.spacing['4'] }}>
            <h3
              style={{
                fontSize: webTheme.typography.fontSize.sm,
                fontWeight: webTheme.typography.fontWeight.medium,
                color: webTheme.colors.text.secondary,
                marginBottom: webTheme.spacing['3'],
              }}
            >
              Core Web Vitals
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: webTheme.spacing['3'],
              }}
            >
              {coreMetrics.map(metric => (
                <MetricCard
                  key={metric.id}
                  name={metric.name}
                  value={metric.value}
                  unit={metric.name === 'CLS' ? '' : 'ms'}
                  rating={metric.rating}
                />
              ))}
            </div>
          </div>

          {/* Budget Violations */}
          {violations.length > 0 && (
            <div>
              <h3
                style={{
                  fontSize: webTheme.typography.fontSize.sm,
                  fontWeight: webTheme.typography.fontWeight.medium,
                  color: webTheme.colors.error.DEFAULT,
                  marginBottom: webTheme.spacing['2'],
                }}
              >
                ⚠️ Budget Violations
              </h3>
              <div
                style={{
                  fontSize: webTheme.typography.fontSize.xs,
                  color: webTheme.colors.text.secondary,
                }}
              >
                {violations.map(violation => (
                  <div
                    key={violation.id}
                    style={{
                      padding: webTheme.spacing['2'],
                      backgroundColor: webTheme.colors.error['50'],
                      borderRadius: webTheme.borderRadius.DEFAULT,
                      marginBottom: webTheme.spacing['2'],
                    }}
                  >
                    <strong>{violation.name}:</strong> {violation.value.toFixed(2)}
                    {violation.name !== 'CLS' ? 'ms' : ''} (budget: {violation.budget})
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Hide button */}
          <button
            onClick={() => setIsVisible(false)}
            style={{
              marginTop: webTheme.spacing['3'],
              padding: `${webTheme.spacing['1']} ${webTheme.spacing['3']}`,
              backgroundColor: webTheme.colors.gray['200'],
              border: 'none',
              borderRadius: webTheme.borderRadius.DEFAULT,
              fontSize: webTheme.typography.fontSize.xs,
              cursor: 'pointer',
              width: '100%',
            }}
          >
            Hide Dashboard
          </button>
        </div>
      )}
    </div>
  );
};