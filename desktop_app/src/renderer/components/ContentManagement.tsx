/**
 * Content Management Component - Electron
 * Task 203: Advanced Content Management and Organization System
 * Desktop app component for managing transcribed content
 */

import React, { useState, useEffect, useRef } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import './ContentManagement.css';

const { ipcRenderer } = window.require('electron');

interface ContentItem {
  id: string;
  title: string;
  description?: string;
  contentType: string;
  status: string;
  quality: string;
  duration?: number;
  fileSize?: number;
  transcriptionText?: string;
  summary?: string;
  tags: Array<{ id: string; name: string; color: string }>;
  categories: Array<{ id: string; name: string; path: string }>;
  createdAt: string;
  updatedAt: string;
  accessLevel: string;
  thumbnailPath?: string;
}

interface Collection {
  id: string;
  name: string;
  description?: string;
  itemsCount: number;
  items?: string[];
  accessLevel: string;
  coverImage?: string;
}

interface Tag {
  id: string;
  name: string;
  color: string;
  usageCount: number;
}

interface Category {
  id: string;
  name: string;
  path: string;
  parentId?: string;
  children?: Category[];
  itemCount?: number;
}

const ContentManagement: React.FC = () => {
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'kanban'>('grid');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [contentItems, setContentItems] = useState<ContentItem[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showCreateCollectionModal, setShowCreateCollectionModal] = useState(false);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState<'date' | 'name' | 'size' | 'quality'>('date');
  const [filterQuality, setFilterQuality] = useState<string>('all');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize and load data
  useEffect(() => {
    loadContent();
    loadCollections();
    loadTags();
    loadCategories();

    // Set up IPC listeners
    ipcRenderer.on('content-updated', handleContentUpdate);
    ipcRenderer.on('upload-progress', handleUploadProgress);
    ipcRenderer.on('content-deleted', handleContentDeleted);

    return () => {
      ipcRenderer.removeAllListeners('content-updated');
      ipcRenderer.removeAllListeners('upload-progress');
      ipcRenderer.removeAllListeners('content-deleted');
    };
  }, []);

  const loadContent = async () => {
    setLoading(true);
    try {
      const content = await ipcRenderer.invoke('fetch-content', {
        filters: { quality: filterQuality },
        sortBy,
      });
      setContentItems(content || getMockContent());
    } catch (error) {
      console.error('Failed to load content:', error);
      setContentItems(getMockContent());
    } finally {
      setLoading(false);
    }
  };

  const loadCollections = async () => {
    try {
      const collections = await ipcRenderer.invoke('fetch-collections');
      setCollections(collections || getMockCollections());
    } catch (error) {
      console.error('Failed to load collections:', error);
      setCollections(getMockCollections());
    }
  };

  const loadTags = async () => {
    try {
      const tags = await ipcRenderer.invoke('fetch-tags');
      setTags(tags || getMockTags());
    } catch (error) {
      console.error('Failed to load tags:', error);
      setTags(getMockTags());
    }
  };

  const loadCategories = async () => {
    try {
      const categories = await ipcRenderer.invoke('fetch-categories');
      setCategories(categories || getMockCategories());
    } catch (error) {
      console.error('Failed to load categories:', error);
      setCategories(getMockCategories());
    }
  };

  const getMockContent = (): ContentItem[] => [
    {
      id: '1',
      title: 'Team Meeting - Product Roadmap Q4 2025',
      description: 'Discussion about Q4 product roadmap priorities and resource allocation',
      contentType: 'meeting',
      status: 'ready',
      quality: 'good',
      duration: 2730,
      fileSize: 15728640,
      summary: 'Team discussed Q4 priorities including new feature launches, technical debt reduction, and customer feedback implementation.',
      tags: [
        { id: 't1', name: 'meeting', color: '#3b82f6' },
        { id: 't2', name: 'product', color: '#10b981' },
        { id: 't3', name: 'roadmap', color: '#8b5cf6' }
      ],
      categories: [{ id: 'c1', name: 'Business', path: '/Business' }],
      createdAt: '2025-08-07T14:30:00Z',
      updatedAt: '2025-08-07T14:35:00Z',
      accessLevel: 'team'
    },
    {
      id: '2',
      title: 'Customer Interview - Enterprise User Research',
      description: 'In-depth user research interview covering pain points and feature requests',
      contentType: 'interview',
      status: 'ready',
      quality: 'excellent',
      duration: 1935,
      fileSize: 10485760,
      summary: 'Customer shared insights about workflow challenges and requested better integration capabilities.',
      tags: [
        { id: 't4', name: 'interview', color: '#f59e0b' },
        { id: 't5', name: 'research', color: '#ec4899' },
        { id: 't6', name: 'customer', color: '#06b6d4' }
      ],
      categories: [{ id: 'c2', name: 'Research', path: '/Research' }],
      createdAt: '2025-08-07T11:20:00Z',
      updatedAt: '2025-08-07T11:25:00Z',
      accessLevel: 'private'
    }
  ];

  const getMockCollections = (): Collection[] => [
    {
      id: 'col1',
      name: 'Customer Interviews',
      description: 'All customer research interviews and feedback sessions',
      itemsCount: 23,
      items: ['2'],
      accessLevel: 'team'
    },
    {
      id: 'col2',
      name: 'Product Planning',
      description: 'Product roadmap discussions and planning sessions',
      itemsCount: 16,
      items: ['1'],
      accessLevel: 'private'
    }
  ];

  const getMockTags = (): Tag[] => [
    { id: 't1', name: 'meeting', color: '#3b82f6', usageCount: 45 },
    { id: 't2', name: 'product', color: '#10b981', usageCount: 32 },
    { id: 't3', name: 'roadmap', color: '#8b5cf6', usageCount: 28 },
    { id: 't4', name: 'interview', color: '#f59e0b', usageCount: 24 },
    { id: 't5', name: 'research', color: '#ec4899', usageCount: 19 },
    { id: 't6', name: 'customer', color: '#06b6d4', usageCount: 15 }
  ];

  const getMockCategories = (): Category[] => [
    {
      id: 'c1',
      name: 'Business',
      path: '/Business',
      itemCount: 45,
      children: [
        { id: 'c11', name: 'Meetings', path: '/Business/Meetings', itemCount: 23 },
        { id: 'c12', name: 'Presentations', path: '/Business/Presentations', itemCount: 12 },
        { id: 'c13', name: 'Reports', path: '/Business/Reports', itemCount: 10 }
      ]
    },
    {
      id: 'c2',
      name: 'Research',
      path: '/Research',
      itemCount: 38,
      children: [
        { id: 'c21', name: 'User Interviews', path: '/Research/User Interviews', itemCount: 18 },
        { id: 'c22', name: 'Market Analysis', path: '/Research/Market Analysis', itemCount: 11 },
        { id: 'c23', name: 'Competitor Research', path: '/Research/Competitor Research', itemCount: 9 }
      ]
    }
  ];

  const handleContentUpdate = (_event: any, content: ContentItem) => {
    setContentItems(prev => {
      const index = prev.findIndex(item => item.id === content.id);
      if (index >= 0) {
        const updated = [...prev];
        updated[index] = content;
        return updated;
      }
      return [content, ...prev];
    });
  };

  const handleUploadProgress = (_event: any, data: { id: string; progress: number }) => {
    // Update upload progress UI
    console.log(`Upload progress for ${data.id}: ${data.progress}%`);
  };

  const handleContentDeleted = (_event: any, contentId: string) => {
    setContentItems(prev => prev.filter(item => item.id !== contentId));
  };

  const handleFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const result = await ipcRenderer.invoke('upload-content', {
        filePath: file.path,
        fileName: file.name,
        fileSize: file.size,
        contentType: determineContentType(file.name)
      });
      
      if (result.success) {
        console.log(`File ${file.name} uploaded successfully`);
      }
    }
  };

  const determineContentType = (fileName: string): string => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    const audioExts = ['mp3', 'wav', 'm4a', 'aac'];
    const videoExts = ['mp4', 'avi', 'mov', 'wmv'];
    
    if (audioExts.includes(ext || '')) return 'audio';
    if (videoExts.includes(ext || '')) return 'video';
    return 'document';
  };

  const handleDragEnd = (result: any) => {
    if (!result.destination) return;

    const items = Array.from(contentItems);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    setContentItems(items);
  };

  const handleDeleteContent = async (contentId: string) => {
    const confirmed = await ipcRenderer.invoke('show-confirmation', {
      title: 'Delete Content',
      message: 'Are you sure you want to delete this content? This action cannot be undone.',
      buttons: ['Cancel', 'Delete']
    });

    if (confirmed === 1) {
      await ipcRenderer.invoke('delete-content', contentId);
    }
  };

  const handleExportContent = async (contentId: string, format: 'pdf' | 'docx' | 'txt') => {
    await ipcRenderer.invoke('export-content', { contentId, format });
  };

  const handleCreateCollection = async (name: string, description: string) => {
    const result = await ipcRenderer.invoke('create-collection', { name, description });
    if (result.success) {
      loadCollections();
      setShowCreateCollectionModal(false);
    }
  };

  

  const filteredContent = contentItems.filter(item => {
    const matchesSearch = !searchQuery || 
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesTags = selectedTags.size === 0 ||
      item.tags.some(tag => selectedTags.has(tag.id));
    
    const matchesCategory = !selectedCategory ||
      item.categories.some(cat => cat.id === selectedCategory);
    
    const matchesQuality = filterQuality === 'all' || item.quality === filterQuality;

    return matchesSearch && matchesTags && matchesCategory && matchesQuality;
  });

  const renderContentGrid = () => (
    <div className="content-grid">
      {filteredContent.map(item => (
        <div 
          key={item.id}
          className={`content-card ${selectedItems.has(item.id) ? 'selected' : ''}`}
          onClick={() => setSelectedContent(item)}
        >
          <div className="content-card-header">
            <input
              type="checkbox"
              checked={selectedItems.has(item.id)}
              onChange={(e) => {
                e.stopPropagation();
                const newSelected = new Set(selectedItems);
                if (e.target.checked) {
                  newSelected.add(item.id);
                } else {
                  newSelected.delete(item.id);
                }
                setSelectedItems(newSelected);
              }}
              className="content-checkbox"
            />
            <div className={`content-type-badge ${item.contentType}`}>
              {item.contentType}
            </div>
            <div className="content-actions">
              <button className="action-btn" onClick={(e) => {
                e.stopPropagation();
                handleExportContent(item.id, 'pdf');
              }}>📥</button>
              <button className="action-btn" onClick={(e) => {
                e.stopPropagation();
                handleDeleteContent(item.id);
              }}>🗑️</button>
            </div>
          </div>
          <h3 className="content-title">{item.title}</h3>
          <p className="content-description">{item.description}</p>
          <div className="content-tags">
            {item.tags.map(tag => (
              <span 
                key={tag.id}
                className="tag"
                style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
              >
                {tag.name}
              </span>
            ))}
          </div>
          <div className="content-footer">
            <span className={`quality-badge ${item.quality}`}>
              {item.quality}
            </span>
            <span className="content-date">
              {new Date(item.createdAt).toLocaleDateString()}
            </span>
          </div>
        </div>
      ))}
    </div>
  );

  const renderContentList = () => (
    <div className="content-list">
      <table>
        <thead>
          <tr>
            <th>
              <input
                type="checkbox"
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedItems(new Set(filteredContent.map(item => item.id)));
                  } else {
                    setSelectedItems(new Set());
                  }
                }}
              />
            </th>
            <th>Title</th>
            <th>Type</th>
            <th>Quality</th>
            <th>Duration</th>
            <th>Tags</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredContent.map(item => (
            <tr 
              key={item.id}
              className={selectedItems.has(item.id) ? 'selected' : ''}
              onClick={() => setSelectedContent(item)}
            >
              <td>
                <input
                  type="checkbox"
                  checked={selectedItems.has(item.id)}
                  onChange={(e) => {
                    e.stopPropagation();
                    const newSelected = new Set(selectedItems);
                    if (e.target.checked) {
                      newSelected.add(item.id);
                    } else {
                      newSelected.delete(item.id);
                    }
                    setSelectedItems(newSelected);
                  }}
                />
              </td>
              <td className="title-cell">
                <div className="title-content">
                  <div className="title">{item.title}</div>
                  <div className="description">{item.description}</div>
                </div>
              </td>
              <td>{item.contentType}</td>
              <td>
                <span className={`quality-badge ${item.quality}`}>
                  {item.quality}
                </span>
              </td>
              <td>{item.duration ? `${Math.floor(item.duration / 60)}:${(item.duration % 60).toString().padStart(2, '0')}` : '-'}</td>
              <td>
                <div className="tags-cell">
                  {item.tags.slice(0, 2).map(tag => (
                    <span 
                      key={tag.id}
                      className="tag-small"
                      style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
                    >
                      {tag.name}
                    </span>
                  ))}
                  {item.tags.length > 2 && (
                    <span className="tag-more">+{item.tags.length - 2}</span>
                  )}
                </div>
              </td>
              <td>{new Date(item.createdAt).toLocaleDateString()}</td>
              <td>
                <div className="action-buttons">
                  <button 
                    className="action-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleExportContent(item.id, 'pdf');
                    }}
                  >📥</button>
                  <button 
                    className="action-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteContent(item.id);
                    }}
                  >🗑️</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderKanbanView = () => {
    const statusColumns = ['processing', 'ready', 'archived'];
    
    return (
      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="kanban-board">
          {statusColumns.map(status => (
            <div key={status} className="kanban-column">
              <h3 className="kanban-column-title">
                {status.charAt(0).toUpperCase() + status.slice(1)}
                <span className="kanban-count">
                  {filteredContent.filter(item => item.status === status).length}
                </span>
              </h3>
              <Droppable droppableId={status}>
                {(provided) => (
                  <div
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                    className="kanban-items"
                  >
                    {filteredContent
                      .filter(item => item.status === status)
                      .map((item, index) => (
                        <Draggable key={item.id} draggableId={item.id} index={index}>
                          {(provided, snapshot) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className={`kanban-card ${snapshot.isDragging ? 'dragging' : ''}`}
                            >
                              <div className="kanban-card-header">
                                <span className={`content-type-badge ${item.contentType}`}>
                                  {item.contentType}
                                </span>
                                <span className={`quality-badge ${item.quality}`}>
                                  {item.quality}
                                </span>
                              </div>
                              <h4>{item.title}</h4>
                              <p>{item.description}</p>
                              <div className="kanban-card-tags">
                                {item.tags.map(tag => (
                                  <span 
                                    key={tag.id}
                                    className="tag-small"
                                    style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
                                  >
                                    {tag.name}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          ))}
        </div>
      </DragDropContext>
    );
  };

  const renderUploadModal = () => {
    if (!showUploadModal) return null;
    
    return (
      <div 
        className="modal-overlay" 
        onClick={() => setShowUploadModal(false)}
        role="dialog"
        aria-labelledby="upload-modal-title"
        aria-modal="true"
      >
        <div 
          className="modal-content" 
          onClick={(e) => e.stopPropagation()}
          role="document"
        >
          <div className="modal-header">
            <h2 id="upload-modal-title">Upload Content</h2>
            <button 
              className="modal-close" 
              onClick={() => setShowUploadModal(false)}
              aria-label="Close upload modal"
            >
              ×
            </button>
          </div>
          <div className="modal-body">
            <div 
              className="upload-area"
              onDrop={(e) => {
                e.preventDefault();
                // Handle file drop if implemented
              }}
              onDragOver={(e) => {
                e.preventDefault();
              }}
            >
              <div className="upload-icon" aria-hidden="true">📁</div>
              <p>Drag and drop files here or click to browse</p>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={handleFileSelected}
                style={{ display: 'none' }}
                accept="audio/*,video/*,.txt,.pdf,.docx"
                tabIndex={-1}
              />
              <button 
                className="upload-btn" 
                onClick={handleFileUpload}
                aria-label="Select files to upload"
              >
                Select Files
              </button>
            </div>
            <div className="upload-options">
              <h3>Upload Options</h3>
              <div className="form-group">
                <label htmlFor="content-type">Content Type</label>
                <select 
                  id="content-type"
                  className="quality-select"
                  aria-label="Select content type"
                >
                  <option value="auto">Auto Detect</option>
                  <option value="meeting">Meeting</option>
                  <option value="interview">Interview</option>
                  <option value="lecture">Lecture</option>
                  <option value="presentation">Presentation</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="processing-priority">Processing Priority</label>
                <select 
                  id="processing-priority"
                  className="quality-select"
                  aria-label="Select processing priority"
                >
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button 
              className="modal-btn" 
              onClick={() => setShowUploadModal(false)}
              aria-label="Cancel upload"
            >
              Cancel
            </button>
            <button 
              className="modal-btn primary" 
              onClick={() => handleFileUpload()}
              aria-label="Upload selected files"
            >
              Upload
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderCreateCollectionModal = () => {
    if (!showCreateCollectionModal) return null;
    
    const [collectionName, setCollectionName] = useState('');
    const [collectionDescription, setCollectionDescription] = useState('');
    
    return (
      <div 
        className="modal-overlay" 
        onClick={() => setShowCreateCollectionModal(false)}
        role="dialog"
        aria-labelledby="create-collection-modal-title"
        aria-modal="true"
      >
        <div 
          className="modal-content" 
          onClick={(e) => e.stopPropagation()}
          role="document"
        >
          <div className="modal-header">
            <h2 id="create-collection-modal-title">Create New Collection</h2>
            <button 
              className="modal-close" 
              onClick={() => setShowCreateCollectionModal(false)}
              aria-label="Close create collection modal"
            >
              ×
            </button>
          </div>
          <div className="modal-body">
            <div className="form-group">
              <label htmlFor="collectionName">Collection Name</label>
              <input
                id="collectionName"
                type="text"
                className="search-input"
                value={collectionName}
                onChange={(e) => setCollectionName(e.target.value)}
                placeholder="Enter collection name"
                aria-required="true"
                aria-describedby="collection-name-help"
              />
              <div id="collection-name-help" className="sr-only">
                Enter a name for your new collection
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="collectionDescription">Description</label>
              <textarea
                id="collectionDescription"
                className="search-input"
                value={collectionDescription}
                onChange={(e) => setCollectionDescription(e.target.value)}
                placeholder="Enter collection description"
                rows={3}
                aria-describedby="collection-description-help"
              />
              <div id="collection-description-help" className="sr-only">
                Optionally describe what this collection is for
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="accessLevel">Access Level</label>
              <select 
                id="accessLevel"
                className="quality-select"
                aria-label="Select access level for collection"
              >
                <option value="private">Private</option>
                <option value="team">Team</option>
                <option value="organization">Organization</option>
                <option value="public">Public</option>
              </select>
            </div>
          </div>
          <div className="modal-footer">
            <button 
              className="modal-btn" 
              onClick={() => setShowCreateCollectionModal(false)}
              aria-label="Cancel creating collection"
            >
              Cancel
            </button>
            <button 
              className="modal-btn primary" 
              onClick={() => {
                handleCreateCollection(collectionName, collectionDescription);
                setCollectionName('');
                setCollectionDescription('');
              }}
              aria-label="Create collection"
            >
              Create Collection
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="content-management" role="main">
      <div className="content-header">
        <h1>Content Management</h1>
        <div className="header-actions">
          <div className="search-bar">
            <label htmlFor="content-search" className="sr-only">Search content</label>
            <input
              id="content-search"
              type="text"
              placeholder="Search content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
              aria-label="Search content"
            />
            <span className="search-icon" aria-hidden="true">🔍</span>
          </div>
          <div className="sort-selector">
            <label htmlFor="sort-by" className="sr-only">Sort by</label>
            <select 
              id="sort-by"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'date' | 'name' | 'size' | 'quality')}
              className="quality-select"
              aria-label="Sort content by"
            >
              <option value="date">Sort by Date</option>
              <option value="name">Sort by Name</option>
              <option value="size">Sort by Size</option>
              <option value="quality">Sort by Quality</option>
            </select>
          </div>
          <div className="view-switcher" role="tablist" aria-label="View modes">
            <button 
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
              aria-selected={viewMode === 'grid'}
              role="tab"
            >
              <span aria-hidden="true">⊞</span>
              <span className="sr-only">Grid view</span>
            </button>
            <button 
              className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
              aria-selected={viewMode === 'list'}
              role="tab"
            >
              <span aria-hidden="true">☰</span>
              <span className="sr-only">List view</span>
            </button>
            <button 
              className={`view-btn ${viewMode === 'kanban' ? 'active' : ''}`}
              onClick={() => setViewMode('kanban')}
              aria-selected={viewMode === 'kanban'}
              role="tab"
            >
              <span aria-hidden="true">⫿</span>
              <span className="sr-only">Kanban view</span>
            </button>
          </div>
          <button className="upload-btn" onClick={() => setShowUploadModal(true)} aria-label="Upload content">
            + Upload Content
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelected}
            style={{ display: 'none' }}
            accept="audio/*,video/*,.txt,.pdf,.docx"
            tabIndex={-1}
          />
        </div>
      </div>

      <div className="content-body">
        <aside className="content-sidebar">
          {/* Categories */}
          <div className="sidebar-section">
            <h3>Categories</h3>
            <div className="category-tree">
              {categories.map(category => (
                <div key={category.id} className="category-item">
                  <div 
                    className={`category-name ${selectedCategory === category.id ? 'selected' : ''}`}
                    onClick={() => setSelectedCategory(selectedCategory === category.id ? null : category.id)}
                  >
                    <span className="category-icon">📁</span>
                    {category.name}
                    <span className="category-count">{category.itemCount}</span>
                  </div>
                  {category.children && (
                    <div className="category-children">
                      {category.children.map(child => (
                        <div 
                          key={child.id}
                          className={`category-child ${selectedCategory === child.id ? 'selected' : ''}`}
                          onClick={() => setSelectedCategory(selectedCategory === child.id ? null : child.id)}
                        >
                          <span className="category-icon">📄</span>
                          {child.name}
                          <span className="category-count">{child.itemCount}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Tags */}
          <div className="sidebar-section">
            <h3>Tags</h3>
            <div className="tags-list">
              {tags.map(tag => (
                <label key={tag.id} className="tag-filter">
                  <input
                    type="checkbox"
                    checked={selectedTags.has(tag.id)}
                    onChange={(e) => {
                      const newTags = new Set(selectedTags);
                      if (e.target.checked) {
                        newTags.add(tag.id);
                      } else {
                        newTags.delete(tag.id);
                      }
                      setSelectedTags(newTags);
                    }}
                  />
                  <span 
                    className="tag-label"
                    style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
                  >
                    {tag.name} ({tag.usageCount})
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Collections */}
          <div className="sidebar-section">
            <div className="section-header">
              <h3>Collections</h3>
              <button 
                className="add-collection-btn"
                onClick={() => setShowCreateCollectionModal(true)}
              >+</button>
            </div>
            <div className="collections-list">
              {collections.map(collection => (
                <div key={collection.id} className="collection-item">
                  <span className="collection-icon">📚</span>
                  <div className="collection-info">
                    <div className="collection-name">{collection.name}</div>
                    <div className="collection-count">{collection.itemsCount} items</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quality Filter */}
          <div className="sidebar-section">
            <h3>Quality Filter</h3>
            <select 
              value={filterQuality}
              onChange={(e) => setFilterQuality(e.target.value)}
              className="quality-select"
            >
              <option value="all">All Quality Levels</option>
              <option value="excellent">Excellent</option>
              <option value="good">Good</option>
              <option value="fair">Fair</option>
              <option value="poor">Poor</option>
              <option value="needs_review">Needs Review</option>
            </select>
          </div>
        </aside>

        <main className="content-main">
          {selectedItems.size > 0 && (
            <div className="bulk-actions">
              <span className="selected-count">{selectedItems.size} items selected</span>
              <button className="bulk-btn">Add to Collection</button>
              <button className="bulk-btn">Add Tags</button>
              <button className="bulk-btn">Export</button>
              <button className="bulk-btn danger" onClick={() => {
                selectedItems.forEach(id => handleDeleteContent(id));
                setSelectedItems(new Set());
              }}>Delete</button>
              <button className="bulk-btn" onClick={() => setSelectedItems(new Set())}>
                Clear Selection
              </button>
            </div>
          )}

          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading content...</p>
            </div>
          ) : (
            <>
              {viewMode === 'grid' && renderContentGrid()}
              {viewMode === 'list' && renderContentList()}
              {viewMode === 'kanban' && renderKanbanView()}
            </>
          )}
        </main>
      </div>

      {/* Content Detail Modal */}
      {selectedContent && (
        <div className="modal-overlay" onClick={() => setSelectedContent(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedContent.title}</h2>
              <button className="modal-close" onClick={() => setSelectedContent(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-section">
                <h3>Description</h3>
                <p>{selectedContent.description}</p>
              </div>
              <div className="detail-section">
                <h3>Summary</h3>
                <p>{selectedContent.summary}</p>
              </div>
              <div className="detail-section">
                <h3>Details</h3>
                <div className="detail-grid">
                  <div>
                    <span className="detail-label">Type:</span>
                    <span>{selectedContent.contentType}</span>
                  </div>
                  <div>
                    <span className="detail-label">Quality:</span>
                    <span className={`quality-badge ${selectedContent.quality}`}>
                      {selectedContent.quality}
                    </span>
                  </div>
                  <div>
                    <span className="detail-label">Duration:</span>
                    <span>{selectedContent.duration ? `${Math.floor(selectedContent.duration / 60)}:${(selectedContent.duration % 60).toString().padStart(2, '0')}` : 'N/A'}</span>
                  </div>
                  <div>
                    <span className="detail-label">Size:</span>
                    <span>{selectedContent.fileSize ? `${(selectedContent.fileSize / 1024 / 1024).toFixed(2)} MB` : 'N/A'}</span>
                  </div>
                </div>
              </div>
              <div className="detail-section">
                <h3>Tags</h3>
                <div className="detail-tags">
                  {selectedContent.tags.map(tag => (
                    <span 
                      key={tag.id}
                      className="tag"
                      style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
                    >
                      {tag.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="modal-btn primary">Edit</button>
              <button className="modal-btn">Share</button>
              <button className="modal-btn">Export</button>
              <button className="modal-btn danger">Delete</button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {renderUploadModal()}

      {/* Create Collection Modal */}
      {renderCreateCollectionModal()}
    </div>
  );
};

export default ContentManagement;