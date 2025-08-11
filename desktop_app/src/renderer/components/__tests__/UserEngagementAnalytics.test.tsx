/**
 * Test suite for UserEngagementAnalytics Electron component
 * Task 202: User Engagement Analytics
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import UserEngagementAnalytics from '../UserEngagementAnalytics';

// Mock electron
const mockIpcRenderer = {
  invoke: jest.fn(),
  on: jest.fn(),
  removeAllListeners: jest.fn(),
};

// Mock window.require
Object.defineProperty(window, 'require', {
  value: jest.fn(() => ({
    ipcRenderer: mockIpcRenderer
  }))
});

// Mock recharts
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => null,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => null,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => null,
  FunnelChart: ({ children }: any) => <div data-testid="funnel-chart">{children}</div>,
  Funnel: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  Cell: () => null,
  LabelList: () => null,
}));

describe('UserEngagementAnalytics Electron Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIpcRenderer.invoke.mockImplementation((channel: string) => {
      if (channel === 'fetch-analytics') {
        return Promise.resolve({
          metrics: {
            activeUsers: 1234,
            avgSessionDuration: 240,
            pageViews: 5678,
            bounceRate: 35,
            conversionRate: 12,
            retentionRate: 75
          },
          timeSeries: [],
          userSegments: [],
          behaviorFlows: []
        });
      }
      return Promise.resolve(null);
    });
  });

  test('renders analytics dashboard', () => {
    render(<UserEngagementAnalytics />);
    
    expect(screen.getByText('User Engagement Analytics')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /overview/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /behavior/i })).toBeInTheDocument();
  });

  test('displays metrics cards', async () => {
    render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Active Users')).toBeInTheDocument();
      expect(screen.getByText('1,234')).toBeInTheDocument();
      expect(screen.getByText('Avg Session')).toBeInTheDocument();
    });
  });

  test('handles date range selection', () => {
    render(<UserEngagementAnalytics />);
    
    const dateSelect = screen.getByRole('combobox');
    fireEvent.change(dateSelect, { target: { value: '30d' } });
    
    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('fetch-analytics', 
      expect.objectContaining({ dateRange: '30d' })
    );
  });

  test('switches between view tabs', () => {
    render(<UserEngagementAnalytics />);
    
    const behaviorTab = screen.getByRole('button', { name: /behavior/i });
    fireEvent.click(behaviorTab);
    
    expect(behaviorTab).toHaveClass('active');
  });

  test('handles refresh action', async () => {
    render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Active Users')).toBeInTheDocument();
    });
    
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);
    
    expect(mockIpcRenderer.invoke).toHaveBeenCalledTimes(2);
  });

  test('exports analytics data', async () => {
    render(<UserEngagementAnalytics />);
    
    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);
    
    await waitFor(() => {
      expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('export-analytics', 
        expect.any(Object)
      );
    });
  });

  test('displays churn analysis', () => {
    render(<UserEngagementAnalytics />);
    
    const churnTab = screen.getByRole('button', { name: /churn/i });
    fireEvent.click(churnTab);
    
    expect(screen.getByText('Churn Analysis')).toBeInTheDocument();
  });

  test('shows real-time analytics', () => {
    render(<UserEngagementAnalytics />);
    
    const realtimeTab = screen.getByRole('button', { name: /real-time/i });
    fireEvent.click(realtimeTab);
    
    expect(screen.getByText('Real-Time Analytics')).toBeInTheDocument();
  });

  test('handles IPC events', () => {
    render(<UserEngagementAnalytics />);
    
    expect(mockIpcRenderer.on).toHaveBeenCalledWith('analytics-updated', expect.any(Function));
    expect(mockIpcRenderer.on).toHaveBeenCalledWith('export-complete', expect.any(Function));
  });

  test('cleans up listeners on unmount', () => {
    const { unmount } = render(<UserEngagementAnalytics />);
    
    unmount();
    
    expect(mockIpcRenderer.removeAllListeners).toHaveBeenCalledWith('analytics-updated');
    expect(mockIpcRenderer.removeAllListeners).toHaveBeenCalledWith('export-complete');
  });

  test('displays loading state', () => {
    render(<UserEngagementAnalytics />);
    
    expect(screen.getByText('Loading analytics...')).toBeInTheDocument();
  });

  test('handles API error gracefully', async () => {
    mockIpcRenderer.invoke.mockRejectedValueOnce(new Error('IPC Error'));
    
    render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      // Should still render with mock data
      expect(screen.getByText('Active Users')).toBeInTheDocument();
    });
  });
});