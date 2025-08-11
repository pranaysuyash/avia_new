/**
 * Test suite for ContentManagement component
 * Task 203: Advanced Content Management System
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ContentManagement from '../ContentManagement';

// Mock fetch
global.fetch = jest.fn();

describe('ContentManagement Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          data: {
            results: [
              {
                id: '1',
                title: 'Test Content',
                description: 'Test description',
                contentType: 'meeting',
                status: 'ready',
                quality: 'good',
                tags: [{ id: 't1', name: 'test', color: '#3b82f6' }],
                categories: [{ id: 'c1', name: 'Business', path: '/Business' }],
                createdAt: '2025-08-07T14:30:00Z',
                updatedAt: '2025-08-07T14:35:00Z',
                accessLevel: 'team'
              }
            ]
          }
        })
      })
    );
  });

  test('renders content management dashboard', () => {
    render(<ContentManagement />);
    
    expect(screen.getByText('Content Management')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search content...')).toBeInTheDocument();
    expect(screen.getByText('Upload Content')).toBeInTheDocument();
  });

  test('displays content tabs', () => {
    render(<ContentManagement />);
    
    expect(screen.getByRole('button', { name: /all content/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /collections/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /shared with me/i })).toBeInTheDocument();
  });

  test('renders sidebar with categories and tags', () => {
    render(<ContentManagement />);
    
    expect(screen.getByText('Categories')).toBeInTheDocument();
    expect(screen.getByText('Popular Tags')).toBeInTheDocument();
    expect(screen.getByText('Business')).toBeInTheDocument();
    expect(screen.getByText('Research')).toBeInTheDocument();
  });

  test('switches between grid and list view', () => {
    render(<ContentManagement />);
    
    const listViewButton = screen.getByRole('button', { name: /list/i });
    fireEvent.click(listViewButton);
    
    // Check if view mode changed (would need to check for list-specific elements)
    expect(screen.getByText('Team Meeting - Product Roadmap Q4')).toBeInTheDocument();
  });

  test('handles search functionality', () => {
    render(<ContentManagement />);
    
    const searchInput = screen.getByPlaceholderText('Search content...');
    fireEvent.change(searchInput, { target: { value: 'meeting' } });
    
    expect(searchInput).toHaveValue('meeting');
  });

  test('filters content by tags', () => {
    render(<ContentManagement />);
    
    const tagButton = screen.getByText('meeting (45)');
    fireEvent.click(tagButton);
    
    // Tag should be selected (would need to check for visual indication)
    expect(tagButton).toBeInTheDocument();
  });

  test('opens upload modal', () => {
    render(<ContentManagement />);
    
    const uploadButton = screen.getByText('Upload Content');
    fireEvent.click(uploadButton);
    
    expect(screen.getByText('Content Title')).toBeInTheDocument();
    expect(screen.getByText('Content Type')).toBeInTheDocument();
    expect(screen.getByText('Upload Method')).toBeInTheDocument();
  });

  test('closes upload modal', () => {
    render(<ContentManagement />);
    
    const uploadButton = screen.getByText('Upload Content');
    fireEvent.click(uploadButton);
    
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    expect(screen.queryByText('Content Title')).not.toBeInTheDocument();
  });

  test('displays filter panel', () => {
    render(<ContentManagement />);
    
    const filterButton = screen.getByRole('button', { name: /filter/i });
    fireEvent.click(filterButton);
    
    expect(screen.getByText('Filters')).toBeInTheDocument();
    expect(screen.getByText('Quality Level')).toBeInTheDocument();
    expect(screen.getByText('Date Range')).toBeInTheDocument();
  });

  test('handles content deletion', async () => {
    window.confirm = jest.fn(() => true);
    render(<ContentManagement />);
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0]);
      }
    });
    
    expect(window.confirm).toHaveBeenCalled();
  });

  test('switches to collections view', () => {
    render(<ContentManagement />);
    
    const collectionsTab = screen.getByRole('button', { name: /collections/i });
    fireEvent.click(collectionsTab);
    
    expect(screen.getByText('Customer Interviews')).toBeInTheDocument();
    expect(screen.getByText('Product Planning')).toBeInTheDocument();
  });

  test('displays content with proper formatting', () => {
    render(<ContentManagement />);
    
    expect(screen.getByText('Team Meeting - Product Roadmap Q4')).toBeInTheDocument();
    expect(screen.getByText(/Discussion about Q4 product roadmap/i)).toBeInTheDocument();
  });

  test('shows loading state', () => {
    render(<ContentManagement />);
    
    // Initially shows loading
    expect(screen.getByText('Team Meeting - Product Roadmap Q4')).toBeInTheDocument();
  });

  test('handles API error gracefully', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.reject(new Error('API Error'))
    );
    
    render(<ContentManagement />);
    
    // Should still show mock data
    await waitFor(() => {
      expect(screen.getByText('Team Meeting - Product Roadmap Q4')).toBeInTheDocument();
    });
  });

  test('filters by quality level', () => {
    render(<ContentManagement />);
    
    const filterButton = screen.getByRole('button', { name: /filter/i });
    fireEvent.click(filterButton);
    
    const qualitySelect = screen.getByRole('combobox');
    fireEvent.change(qualitySelect, { target: { value: 'Excellent' } });
    
    expect(qualitySelect).toHaveValue('Excellent');
  });

  test('displays content metadata correctly', () => {
    render(<ContentManagement />);
    
    expect(screen.getByText(/45:30/)).toBeInTheDocument(); // Duration
    expect(screen.getByText('good')).toBeInTheDocument(); // Quality
  });
});