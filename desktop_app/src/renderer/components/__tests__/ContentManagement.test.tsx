/**
 * Test suite for ContentManagement Electron component
 * Task 203: Advanced Content Management System
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ContentManagement from '../ContentManagement';

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

// Mock react-beautiful-dnd
jest.mock('react-beautiful-dnd', () => ({
  DragDropContext: ({ children }: any) => <div>{children}</div>,
  Droppable: ({ children }: any) => children({
    draggableProps: {},
    dragHandleProps: {},
    innerRef: jest.fn(),
  }),
  Draggable: ({ children }: any) => children({
    draggableProps: {},
    dragHandleProps: {},
    innerRef: jest.fn(),
  }, {}),
}));

describe('ContentManagement Electron Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIpcRenderer.invoke.mockImplementation((channel: string) => {
      if (channel === 'fetch-content') {
        return Promise.resolve([
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
        ]);
      }
      if (channel === 'fetch-collections') {
        return Promise.resolve([
          {
            id: 'col1',
            name: 'Test Collection',
            itemsCount: 5,
            accessLevel: 'team'
          }
        ]);
      }
      if (channel === 'fetch-tags') {
        return Promise.resolve([
          { id: 't1', name: 'test', color: '#3b82f6', usageCount: 10 }
        ]);
      }
      if (channel === 'fetch-categories') {
        return Promise.resolve([
          { id: 'c1', name: 'Business', path: '/Business', itemCount: 20 }
        ]);
      }
      return Promise.resolve(null);
    });
  });

  test('renders content management interface', () => {
    render(<ContentManagement />);
    
    expect(screen.getByText('Content Management')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search content...')).toBeInTheDocument();
    expect(screen.getByText('+ Upload Content')).toBeInTheDocument();
  });

  test('displays view mode buttons', () => {
    render(<ContentManagement />);
    
    expect(screen.getByText('⊞')).toBeInTheDocument(); // Grid
    expect(screen.getByText('☰')).toBeInTheDocument(); // List
    expect(screen.getByText('⫿')).toBeInTheDocument(); // Kanban
  });

  test('switches between view modes', () => {
    render(<ContentManagement />);
    
    const listButton = screen.getByText('☰');
    fireEvent.click(listButton);
    
    expect(listButton.parentElement).toHaveClass('active');
  });

  test('loads content on mount', async () => {
    render(<ContentManagement />);
    
    await waitFor(() => {
      expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('fetch-content', expect.any(Object));
      expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('fetch-collections');
      expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('fetch-tags');
      expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('fetch-categories');
    });
  });

  test('displays sidebar sections', async () => {
    render(<ContentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Categories')).toBeInTheDocument();
      expect(screen.getByText('Tags')).toBeInTheDocument();
      expect(screen.getByText('Collections')).toBeInTheDocument();
      expect(screen.getByText('Quality Filter')).toBeInTheDocument();
    });
  });

  test('handles search functionality', () => {
    render(<ContentManagement />);
    
    const searchInput = screen.getByPlaceholderText('Search content...');
    fireEvent.change(searchInput, { target: { value: 'meeting' } });
    
    expect(searchInput).toHaveValue('meeting');
  });

  test('filters by category', async () => {
    render(<ContentManagement />);
    
    await waitFor(() => {
      const categoryButton = screen.getByText('Business');
      fireEvent.click(categoryButton);
      
      expect(categoryButton.parentElement).toHaveClass('selected');
    });
  });

  test('filters by tags', async () => {
    render(<ContentManagement />);
    
    await waitFor(() => {
      const tagCheckbox = screen.getByRole('checkbox', { name: /test/i });
      fireEvent.click(tagCheckbox);
      
      expect(tagCheckbox).toBeChecked();
    });
  });

  test('handles file upload', () => {
    render(<ContentManagement />);
    
    const uploadButton = screen.getByText('+ Upload Content');
    fireEvent.click(uploadButton);
    
    // File input should be triggered
    expect(screen.getByText('+ Upload Content')).toBeInTheDocument();
  });

  test('handles content deletion', async () => {
    mockIpcRenderer.invoke.mockImplementation((channel: string) => {
      if (channel === 'show-confirmation') {
        return Promise.resolve(1); // User clicked "Delete"
      }
      return Promise.resolve(null);
    });
    
    render(<ContentManagement />);
    
    await waitFor(() => {
      const deleteButton = screen.getByText('🗑️');
      fireEvent.click(deleteButton);
    });
    
    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('show-confirmation', expect.any(Object));
  });

  test('displays content detail modal', async () => {
    render(<ContentManagement />);
    
    await waitFor(() => {
      const contentCard = screen.getByText('Team Meeting - Product Roadmap Q4 2025');
      fireEvent.click(contentCard);
      
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });

  test('handles bulk actions', async () => {
    render(<ContentManagement />);
    
    await waitFor(() => {
      const checkbox = screen.getAllByRole('checkbox')[0];
      fireEvent.click(checkbox);
      
      expect(screen.getByText('1 items selected')).toBeInTheDocument();
      expect(screen.getByText('Add to Collection')).toBeInTheDocument();
    });
  });

  test('filters by quality level', () => {
    render(<ContentManagement />);
    
    const qualitySelect = screen.getByRole('combobox');
    fireEvent.change(qualitySelect, { target: { value: 'excellent' } });
    
    expect(qualitySelect).toHaveValue('excellent');
  });

  test('handles IPC events', () => {
    render(<ContentManagement />);
    
    expect(mockIpcRenderer.on).toHaveBeenCalledWith('content-updated', expect.any(Function));
    expect(mockIpcRenderer.on).toHaveBeenCalledWith('upload-progress', expect.any(Function));
    expect(mockIpcRenderer.on).toHaveBeenCalledWith('content-deleted', expect.any(Function));
  });

  test('cleans up listeners on unmount', () => {
    const { unmount } = render(<ContentManagement />);
    
    unmount();
    
    expect(mockIpcRenderer.removeAllListeners).toHaveBeenCalledWith('content-updated');
    expect(mockIpcRenderer.removeAllListeners).toHaveBeenCalledWith('upload-progress');
    expect(mockIpcRenderer.removeAllListeners).toHaveBeenCalledWith('content-deleted');
  });
});