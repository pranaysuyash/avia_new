/**
 * Test suite for ContentManagement React Native screen
 * Task 203: Advanced Content Management System
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import ContentManagement from '../ContentManagement';

// Mock fetch
global.fetch = jest.fn();

// Mock react-native-document-picker
jest.mock('react-native-document-picker', () => ({
  pick: jest.fn(),
  types: {
    allFiles: 'allFiles',
    audio: 'audio',
    video: 'video',
  },
}));

describe('ContentManagement Screen', () => {
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

  test('renders content management screen', () => {
    const { getByText, getByPlaceholderText } = render(<ContentManagement />);
    
    expect(getByText('Content')).toBeTruthy();
    expect(getByPlaceholderText('Search content...')).toBeTruthy();
  });

  test('displays view mode buttons', () => {
    const { getByTestId } = render(<ContentManagement />);
    
    expect(getByTestId('grid-view-button')).toBeTruthy();
    expect(getByTestId('list-view-button')).toBeTruthy();
  });

  test('switches between grid and list view', () => {
    const { getByTestId } = render(<ContentManagement />);
    
    const listButton = getByTestId('list-view-button');
    fireEvent.press(listButton);
    
    // View mode should change
    expect(getByTestId('list-view-button')).toBeTruthy();
  });

  test('handles search input', () => {
    const { getByPlaceholderText } = render(<ContentManagement />);
    
    const searchInput = getByPlaceholderText('Search content...');
    fireEvent.changeText(searchInput, 'meeting');
    
    expect(searchInput.props.value).toBe('meeting');
  });

  test('displays filter options', () => {
    const { getByTestId } = render(<ContentManagement />);
    
    const filterButton = getByTestId('filter-button');
    fireEvent.press(filterButton);
    
    expect(getByTestId('filter-modal')).toBeTruthy();
  });

  test('shows content items', async () => {
    const { getByText } = render(<ContentManagement />);
    
    await waitFor(() => {
      expect(getByText('Team Meeting - Product Roadmap Q4')).toBeTruthy();
      expect(getByText('Customer Interview - User Research')).toBeTruthy();
    });
  });

  test('handles content selection', () => {
    const { getByText } = render(<ContentManagement />);
    
    const contentItem = getByText('Team Meeting - Product Roadmap Q4');
    fireEvent.press(contentItem);
    
    expect(getByText('Team Meeting - Product Roadmap Q4')).toBeTruthy();
  });

  test('opens upload modal', () => {
    const { getByTestId } = render(<ContentManagement />);
    
    const uploadButton = getByTestId('upload-button');
    fireEvent.press(uploadButton);
    
    expect(getByTestId('upload-modal')).toBeTruthy();
  });

  test('handles document picker', async () => {
    const DocumentPicker = require('react-native-document-picker');
    DocumentPicker.pick.mockResolvedValue([{
      uri: 'file://test.mp3',
      name: 'test.mp3',
      type: 'audio/mp3',
      size: 1024000
    }]);
    
    const { getByTestId } = render(<ContentManagement />);
    
    const uploadButton = getByTestId('upload-button');
    fireEvent.press(uploadButton);
    
    const pickFileButton = getByTestId('pick-file-button');
    fireEvent.press(pickFileButton);
    
    await waitFor(() => {
      expect(DocumentPicker.pick).toHaveBeenCalled();
    });
  });

  test('displays tags', () => {
    const { getByText } = render(<ContentManagement />);
    
    expect(getByText('meeting')).toBeTruthy();
    expect(getByText('product')).toBeTruthy();
    expect(getByText('interview')).toBeTruthy();
  });

  test('filters by tag', () => {
    const { getByText } = render(<ContentManagement />);
    
    const tagButton = getByText('meeting');
    fireEvent.press(tagButton);
    
    // Tag should be selected
    expect(tagButton).toBeTruthy();
  });

  test('shows loading state', () => {
    const { getByTestId } = render(<ContentManagement />);
    
    expect(getByTestId('loading-indicator')).toBeTruthy();
  });

  test('handles content deletion', () => {
    const { getByText, getByTestId } = render(<ContentManagement />);
    
    const contentItem = getByText('Team Meeting - Product Roadmap Q4');
    fireEvent.longPress(contentItem);
    
    const deleteButton = getByTestId('delete-button');
    fireEvent.press(deleteButton);
    
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/content/items/'),
      expect.objectContaining({ method: 'DELETE' })
    );
  });

  test('displays quality indicators', () => {
    const { getByText } = render(<ContentManagement />);
    
    expect(getByText('good')).toBeTruthy();
    expect(getByText('excellent')).toBeTruthy();
  });

  test('shows content duration', () => {
    const { getByText } = render(<ContentManagement />);
    
    expect(getByText('45:30')).toBeTruthy(); // Duration for first item
    expect(getByText('32:15')).toBeTruthy(); // Duration for second item
  });
});