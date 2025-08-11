/**
 * Test suite for UserEngagementAnalytics React Native screen
 * Task 202: User Engagement Analytics
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import UserEngagementAnalytics from '../UserEngagementAnalytics';

// Mock fetch
global.fetch = jest.fn();

// Mock react-native-chart-kit
jest.mock('react-native-chart-kit', () => ({
  LineChart: ({ children }: any) => children,
  BarChart: ({ children }: any) => children,
  PieChart: ({ children }: any) => children,
  ProgressChart: ({ children }: any) => children,
}));

describe('UserEngagementAnalytics Screen', () => {
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

  test('renders analytics screen with header', () => {
    const { getByText } = render(<UserEngagementAnalytics />);
    
    expect(getByText('User Analytics')).toBeTruthy();
    expect(getByText('Overview')).toBeTruthy();
    expect(getByText('Behavior')).toBeTruthy();
    expect(getByText('Cohorts')).toBeTruthy();
  });

  test('displays key metrics cards', async () => {
    const { getByText } = render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      expect(getByText('Active Users')).toBeTruthy();
      expect(getByText('1,234')).toBeTruthy();
      expect(getByText('Avg Session')).toBeTruthy();
      expect(getByText('Page Views')).toBeTruthy();
    });
  });

  test('handles tab switching', () => {
    const { getByText } = render(<UserEngagementAnalytics />);
    
    const behaviorTab = getByText('Behavior');
    fireEvent.press(behaviorTab);
    
    expect(getByText('User Behavior')).toBeTruthy();
  });

  test('shows loading state', () => {
    const { getByText } = render(<UserEngagementAnalytics />);
    
    expect(getByText('Loading analytics...')).toBeTruthy();
  });

  test('handles refresh action', async () => {
    const { getByTestId } = render(<UserEngagementAnalytics />);
    
    const refreshButton = getByTestId('refresh-button');
    fireEvent.press(refreshButton);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  test('displays engagement trends chart', async () => {
    const { getByText } = render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      expect(getByText('Engagement Trends')).toBeTruthy();
    });
  });

  test('switches to cohorts view', () => {
    const { getByText } = render(<UserEngagementAnalytics />);
    
    const cohortsTab = getByText('Cohorts');
    fireEvent.press(cohortsTab);
    
    expect(getByText('User Segments')).toBeTruthy();
  });

  test('handles API error gracefully', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.reject(new Error('API Error'))
    );
    
    const { getByText } = render(<UserEngagementAnalytics />);
    
    await waitFor(() => {
      // Should still show UI with mock data
      expect(getByText('Active Users')).toBeTruthy();
    });
  });

  test('displays conversion funnel', () => {
    const { getByText } = render(<UserEngagementAnalytics />);
    
    const behaviorTab = getByText('Behavior');
    fireEvent.press(behaviorTab);
    
    expect(getByText('Conversion Funnel')).toBeTruthy();
  });

  test('shows retention analysis', () => {
    const { getByText } = render(<UserEngagementAnalytics />);
    
    const retentionTab = getByText('Retention');
    fireEvent.press(retentionTab);
    
    expect(getByText('Retention Analysis')).toBeTruthy();
  });
});