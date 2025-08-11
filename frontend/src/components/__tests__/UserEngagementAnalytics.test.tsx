/**
 * Test suite for UserEngagementAnalytics component
 * Task 202: User Engagement Analytics
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import UserEngagementAnalytics from '../UserEngagementAnalytics';

// Mock fetch
global.fetch = jest.fn();

// Mock recharts to avoid rendering issues in tests
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => null,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => null,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => null,
  AreaChart: ({ children }: any) => <div data-testid="area-chart">{children}</div>,
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  Cell: () => null,
}));

describe('UserEngagementAnalytics Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          data: {
            metrics: {
              activeUsers: 1234,
              avgSessionDuration: 240,
              pageViews: 5678,
              bounceRate: 0.35,
              conversionRate: 0.12,
              retentionRate: 0.75
            },
            timeSeries: [],
            userSegments: [],
            behaviorFlows: []
          }
        })
      })
    );
  });

  test('renders analytics dashboard with header', () => {
    render(<UserEngagementAnalytics />);
    
    expect(screen.getByText('User Engagement Analytics')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /overview/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /behavior/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cohorts/i })).toBeInTheDocument();
  });

  test('displays key metrics cards', async () => {
    render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Active Users')).toBeInTheDocument();
      expect(screen.getByText('Avg Session')).toBeInTheDocument();
      expect(screen.getByText('Page Views')).toBeInTheDocument();
      expect(screen.getByText('Bounce Rate')).toBeInTheDocument();
    });
  });

  test('renders engagement trend chart', async () => {
    render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Engagement Trends')).toBeInTheDocument();
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  test('handles date range selection', () => {
    render(<UserEngagementAnalytics />);
    
    const dateSelect = screen.getByRole('combobox');
    fireEvent.change(dateSelect, { target: { value: '30d' } });
    
    expect(dateSelect).toHaveValue('30d');
  });

  test('switches between view tabs', () => {
    render(<UserEngagementAnalytics />);
    
    const behaviorTab = screen.getByRole('button', { name: /behavior/i });
    fireEvent.click(behaviorTab);
    
    expect(behaviorTab).toHaveClass('active');
    expect(screen.getByText(/User Behavior Flow/i)).toBeInTheDocument();
  });

  test('displays user segments correctly', async () => {
    render(<UserEngagementAnalytics />);
    
    const cohortsTab = screen.getByRole('button', { name: /cohorts/i });
    fireEvent.click(cohortsTab);
    
    await waitFor(() => {
      expect(screen.getByText(/User Segments/i)).toBeInTheDocument();
    });
  });

  test('shows loading state initially', () => {
    render(<UserEngagementAnalytics />);
    
    expect(screen.getByText('Loading analytics...')).toBeInTheDocument();
  });

  test('handles API error gracefully', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.reject(new Error('API Error'))
    );
    
    render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      // Component should still render with mock data
      expect(screen.getByText('Active Users')).toBeInTheDocument();
    });
  });

  test('refreshes data on button click', async () => {
    render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Active Users')).toBeInTheDocument();
    });
    
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);
    
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  test('exports analytics data', async () => {
    render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Active Users')).toBeInTheDocument();
    });
    
    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);
    
    // Check if export API was called
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/export'),
      expect.any(Object)
    );
  });

  test('displays retention analysis', () => {
    render(<UserEngagementAnalytics />);
    
    const retentionTab = screen.getByRole('button', { name: /retention/i });
    fireEvent.click(retentionTab);
    
    expect(screen.getByText(/Retention Analysis/i)).toBeInTheDocument();
  });

  test('shows churn prediction when available', async () => {
    render(<UserEngagementAnalytics />);
    
    const churnTab = screen.getByRole('button', { name: /churn/i });
    fireEvent.click(churnTab);
    
    await waitFor(() => {
      expect(screen.getByText(/Churn Prediction/i)).toBeInTheDocument();
    });
  });
});