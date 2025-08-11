/**
 * Content Management Component
 * Task 203: Advanced Content Management and Organization System
 * React component for managing transcribed content with tagging and collections
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, Filter, Plus, Upload, Download, Share2, Edit, Trash2,
  Folder, Tag, Star, Clock, FileText, Grid, List, 
  ChevronDown, ChevronRight, MoreVertical, X, Check,
  Calendar, Users, Lock, Globe, AlertCircle, TrendingUp
} from 'lucide-react';
// Note: Drag and drop functionality would require react-beautiful-dnd package
// import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

interface ContentItem {
  id: string;
  title: string;
  description?: string;
  contentType: string;
  status: 'processing' | 'ready' | 'archived' | 'deleted';
  quality: 'excellent' | 'good' | 'fair' | 'poor' | 'needs_review';
  duration?: number;
  fileSize?: number;
  transcriptionText?: string;
  summary?: string;
  tags: Tag[];
  categories: Category[];
  createdAt: string;
  updatedAt: string;
  lastAccessed?: string;
  sharedWith?: string[];
  accessLevel: 'private' | 'team' | 'organization' | 'public';
}

interface Tag {
  id: string;
  name: string;
  color: string;
  usageCount?: number;
}

interface Category {
  id: string;
  name: string;
  path: string;
  parentId?: string;
  children?: Category[];
}

interface Collection {
  id: string;
  name: string;
  description?: string;
  itemsCount: number;
  accessLevel: 'private' | 'team' | 'organization' | 'public';
  coverImage?: string;
  createdAt: string;
  updatedAt: string;
}

const ContentManagement: React.FC = () => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [contentItems, setContentItems] = useState<ContentItem[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'collections' | 'shared'>('all');

  // Mock data
  const mockContentItems: ContentItem[] = [
    {
      id: '1',
      title: 'Team Meeting - Product Roadmap Q4',
      description: 'Discussion about Q4 product roadmap priorities and resource allocation',
      contentType: 'meeting',
      status: 'ready',
      quality: 'good',
      duration: 2730,
      fileSize: 15728640,
      summary: 'Team discussed Q4 priorities including new feature launches...',
      tags: [
        { id: 't1', name: 'meeting', color: '#3b82f6' },
        { id: 't2', name: 'product', color: '#10b981' }
      ],
      categories: [{ id: 'c1', name: 'Business', path: '/Business' }],
      createdAt: '2025-08-07T14:30:00Z',
      updatedAt: '2025-08-07T14:35:00Z',
      accessLevel: 'team'
    },
    {
      id: '2',
      title: 'Customer Interview - User Research',
      description: 'In-depth user research interview covering pain points',
      contentType: 'interview',
      status: 'ready',
      quality: 'excellent',
      duration: 1935,
      fileSize: 10485760,
      summary: 'Customer shared insights about workflow challenges...',
      tags: [
        { id: 't3', name: 'interview', color: '#f59e0b' },
        { id: 't4', name: 'research', color: '#8b5cf6' }
      ],
      categories: [{ id: 'c2', name: 'Research', path: '/Research' }],
      createdAt: '2025-08-07T11:20:00Z',
      updatedAt: '2025-08-07T11:25:00Z',
      accessLevel: 'private'
    }
  ];

  const mockTags: Tag[] = [
    { id: 't1', name: 'meeting', color: '#3b82f6', usageCount: 45 },
    { id: 't2', name: 'product', color: '#10b981', usageCount: 32 },
    { id: 't3', name: 'interview', color: '#f59e0b', usageCount: 28 },
    { id: 't4', name: 'research', color: '#8b5cf6', usageCount: 24 },
    { id: 't5', name: 'sales', color: '#ef4444', usageCount: 19 },
  ];

  const mockCategories: Category[] = [
    {
      id: 'c1',
      name: 'Business',
      path: '/Business',
      children: [
        { id: 'c11', name: 'Meetings', path: '/Business/Meetings' },
        { id: 'c12', name: 'Presentations', path: '/Business/Presentations' }
      ]
    },
    {
      id: 'c2',
      name: 'Research',
      path: '/Research',
      children: [
        { id: 'c21', name: 'User Interviews', path: '/Research/User Interviews' },
        { id: 'c22', name: 'Market Analysis', path: '/Research/Market Analysis' }
      ]
    }
  ];

  const mockCollections: Collection[] = [
    {
      id: 'col1',
      name: 'Customer Interviews',
      description: 'All customer research interviews and feedback sessions',
      itemsCount: 23,
      accessLevel: 'team',
      createdAt: '2025-08-01T10:00:00Z',
      updatedAt: '2025-08-07T14:30:00Z'
    },
    {
      id: 'col2',
      name: 'Product Planning',
      description: 'Product roadmap discussions and planning sessions',
      itemsCount: 16,
      accessLevel: 'private',
      createdAt: '2025-07-15T09:00:00Z',
      updatedAt: '2025-08-06T16:45:00Z'
    }
  ];

  useEffect(() => {
    // Initialize with mock data
    setContentItems(mockContentItems);
    setTags(mockTags);
    setCategories(mockCategories);
    setCollections(mockCollections);
  }, []);

  const fetchContent = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/content/items');
      if (response.ok) {
        const data = await response.json();
        setContentItems(data.data.results);
      }
    } catch (error) {
      console.error('Failed to fetch content:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    // Implement search logic
  }, []);

  const handleTagFilter = (tagId: string) => {
    setSelectedTags(prev => 
      prev.includes(tagId) 
        ? prev.filter(t => t !== tagId)
        : [...prev, tagId]
    );
  };

  const handleDelete = async (contentId: string) => {
    if (confirm('Are you sure you want to delete this content?')) {
      try {
        const response = await fetch(`/api/v1/content/items/${contentId}`, {
          method: 'DELETE'
        });
        if (response.ok) {
          setContentItems(prev => prev.filter(item => item.id !== contentId));
        }
      } catch (error) {
        console.error('Failed to delete content:', error);
      }
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const getQualityColor = (quality: string): string => {
    switch (quality) {
      case 'excellent': return 'text-green-600 bg-green-100';
      case 'good': return 'text-blue-600 bg-blue-100';
      case 'fair': return 'text-yellow-600 bg-yellow-100';
      case 'poor': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const renderContentCard = (item: ContentItem) => (
    <div 
      key={item.id}
      className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-4 cursor-pointer"
      onClick={() => setSelectedContent(item)}
    >
      <div className="flex justify-between items-start mb-2">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 line-clamp-1">{item.title}</h3>
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">{item.description}</p>
        </div>
        <button 
          onClick={(e) => {
            e.stopPropagation();
            // Show more options menu
          }}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <MoreVertical className="h-4 w-4 text-gray-500" />
        </button>
      </div>
      
      {/* Tags */}
      <div className="flex flex-wrap gap-1 mb-3">
        {item.tags.slice(0, 3).map(tag => (
          <span 
            key={tag.id}
            className="px-2 py-1 text-xs rounded-full"
            style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
          >
            {tag.name}
          </span>
        ))}
        {item.tags.length > 3 && (
          <span className="px-2 py-1 text-xs text-gray-500">
            +{item.tags.length - 3}
          </span>
        )}
      </div>
      
      {/* Metadata */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-3">
          <span className="flex items-center">
            <Clock className="h-3 w-3 mr-1" />
            {item.duration ? formatDuration(item.duration) : 'N/A'}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-xs ${getQualityColor(item.quality)}`}>
            {item.quality}
          </span>
        </div>
        <span>{new Date(item.createdAt).toLocaleDateString()}</span>
      </div>
    </div>
  );

  const renderContentList = (item: ContentItem) => (
    <div 
      key={item.id}
      className="bg-white border-b hover:bg-gray-50 p-4 cursor-pointer"
      onClick={() => setSelectedContent(item)}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 flex-1">
          <FileText className="h-8 w-8 text-gray-400" />
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900">{item.title}</h3>
            <p className="text-sm text-gray-600">{item.description}</p>
          </div>
          <div className="flex items-center space-x-6">
            <div className="text-sm text-gray-500">
              <span className="font-medium">Type:</span> {item.contentType}
            </div>
            <div className="text-sm text-gray-500">
              <span className="font-medium">Duration:</span> {item.duration ? formatDuration(item.duration) : 'N/A'}
            </div>
            <span className={`px-2 py-1 rounded-full text-xs ${getQualityColor(item.quality)}`}>
              {item.quality}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2 ml-4">
          <button 
            onClick={(e) => {
              e.stopPropagation();
              // Handle share
            }}
            className="p-2 hover:bg-gray-200 rounded"
          >
            <Share2 className="h-4 w-4 text-gray-600" />
          </button>
          <button 
            onClick={(e) => {
              e.stopPropagation();
              // Handle edit
            }}
            className="p-2 hover:bg-gray-200 rounded"
          >
            <Edit className="h-4 w-4 text-gray-600" />
          </button>
          <button 
            onClick={(e) => {
              e.stopPropagation();
              handleDelete(item.id);
            }}
            className="p-2 hover:bg-gray-200 rounded"
          >
            <Trash2 className="h-4 w-4 text-gray-600" />
          </button>
        </div>
      </div>
    </div>
  );

  const renderUploadModal = () => {
    if (!showUploadModal) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Upload Content</h2>
            <button 
              onClick={() => setShowUploadModal(false)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Content Title
              </label>
              <input 
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter a descriptive title"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Content Type
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option>Audio Transcription</option>
                <option>Video Transcription</option>
                <option>Meeting</option>
                <option>Interview</option>
                <option>Lecture</option>
                <option>Podcast</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Method
              </label>
              <div className="grid grid-cols-3 gap-4">
                <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 transition-colors">
                  <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <span className="text-sm text-gray-600">File Upload</span>
                </button>
                <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 transition-colors">
                  <FileText className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <span className="text-sm text-gray-600">Text Input</span>
                </button>
                <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 transition-colors">
                  <Globe className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <span className="text-sm text-gray-600">URL Import</span>
                </button>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags
              </label>
              <div className="flex flex-wrap gap-2">
                {tags.map(tag => (
                  <label key={tag.id} className="flex items-center">
                    <input 
                      type="checkbox"
                      className="mr-2"
                    />
                    <span 
                      className="px-2 py-1 text-xs rounded-full cursor-pointer"
                      style={{ backgroundColor: `${tag.color}20`, color: tag.color }}
                    >
                      {tag.name}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>
          
          <div className="flex justify-end space-x-3 mt-6">
            <button 
              onClick={() => setShowUploadModal(false)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              Upload & Process
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderFilterPanel = () => {
    if (!showFilterPanel) return null;
    
    return (
      <div className="bg-white border rounded-lg p-4 mb-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">Filters</h3>
          <button 
            onClick={() => setShowFilterPanel(false)}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        
        <div className="space-y-4">
          {/* Content Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Content Type
            </label>
            <div className="space-y-2">
              {['Meeting', 'Interview', 'Webinar', 'Podcast', 'Lecture'].map(type => (
                <label key={type} className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  <span className="text-sm">{type}</span>
                </label>
              ))}
            </div>
          </div>
          
          {/* Quality Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quality Level
            </label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
              <option>All</option>
              <option>Excellent</option>
              <option>Good</option>
              <option>Fair</option>
              <option>Poor</option>
              <option>Needs Review</option>
            </select>
          </div>
          
          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Range
            </label>
            <div className="grid grid-cols-2 gap-2">
              <input 
                type="date"
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
              <input 
                type="date"
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>
          </div>
          
          <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm">
            Apply Filters
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Folder className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Content Management</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Search Bar */}
              <div className="relative">
                <input 
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  placeholder="Search content..."
                  className="w-64 pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
              </div>
              
              <button 
                onClick={() => setShowFilterPanel(!showFilterPanel)}
                className="p-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <Filter className="h-5 w-5 text-gray-600" />
              </button>
              
              <button 
                onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                className="p-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                {viewMode === 'grid' ? <List className="h-5 w-5" /> : <Grid className="h-5 w-5" />}
              </button>
              
              <button 
                onClick={() => setShowUploadModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-2"
              >
                <Plus className="h-5 w-5" />
                <span>Upload Content</span>
              </button>
            </div>
          </div>
          
          {/* Tabs */}
          <div className="flex space-x-8 border-b">
            {[
              { id: 'all', label: 'All Content', count: contentItems.length },
              { id: 'collections', label: 'Collections', count: collections.length },
              { id: 'shared', label: 'Shared with Me', count: 0 }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-3 px-1 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <span className="font-medium">{tab.label}</span>
                {tab.count > 0 && (
                  <span className="ml-2 px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex gap-6">
          {/* Sidebar */}
          <div className="w-64 flex-shrink-0">
            {/* Categories */}
            <div className="bg-white rounded-lg p-4 mb-4">
              <h3 className="font-semibold mb-3">Categories</h3>
              <div className="space-y-1">
                {categories.map(category => (
                  <div key={category.id}>
                    <button className="w-full flex items-center justify-between py-1.5 px-2 text-sm hover:bg-gray-100 rounded">
                      <span className="flex items-center">
                        <ChevronRight className="h-4 w-4 mr-1" />
                        {category.name}
                      </span>
                      <span className="text-xs text-gray-500">
                        {category.children?.length || 0}
                      </span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Tags */}
            <div className="bg-white rounded-lg p-4">
              <h3 className="font-semibold mb-3">Popular Tags</h3>
              <div className="flex flex-wrap gap-2">
                {tags.map(tag => (
                  <button
                    key={tag.id}
                    onClick={() => handleTagFilter(tag.id)}
                    className={`px-2 py-1 text-xs rounded-full transition-colors ${
                      selectedTags.includes(tag.id) 
                        ? 'ring-2 ring-offset-1' 
                        : ''
                    }`}
                    style={{ 
                      backgroundColor: `${tag.color}20`, 
                      color: tag.color,
                      outline: selectedTags.includes(tag.id) ? `2px solid ${tag.color}` : 'none'
                    }}
                  >
                    {tag.name} ({tag.usageCount})
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          {/* Main Content */}
          <div className="flex-1">
            {/* Filter Panel */}
            {renderFilterPanel()}
            
            {/* Content Grid/List */}
            {loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <>
                {activeTab === 'all' && (
                  <div className={viewMode === 'grid' 
                    ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' 
                    : 'space-y-0'
                  }>
                    {contentItems
                      .filter(item => {
                        if (searchQuery) {
                          return item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                 item.description?.toLowerCase().includes(searchQuery.toLowerCase());
                        }
                        return true;
                      })
                      .filter(item => {
                        if (selectedTags.length > 0) {
                          return item.tags.some(tag => selectedTags.includes(tag.id));
                        }
                        return true;
                      })
                      .map(item => 
                        viewMode === 'grid' 
                          ? renderContentCard(item)
                          : renderContentList(item)
                      )}
                  </div>
                )}
                
                {activeTab === 'collections' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {collections.map(collection => (
                      <div key={collection.id} className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow cursor-pointer">
                        <div className="flex items-start justify-between mb-2">
                          <Folder className="h-8 w-8 text-blue-500" />
                          <span className="text-xs text-gray-500">{collection.itemsCount} items</span>
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-1">{collection.name}</h3>
                        <p className="text-sm text-gray-600">{collection.description}</p>
                        <div className="mt-3 flex items-center justify-between">
                          <span className="text-xs text-gray-500">
                            Updated {new Date(collection.updatedAt).toLocaleDateString()}
                          </span>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            collection.accessLevel === 'private' 
                              ? 'bg-gray-100 text-gray-600'
                              : 'bg-green-100 text-green-600'
                          }`}>
                            {collection.accessLevel}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* Upload Modal */}
      {renderUploadModal()}
    </div>
  );
};

export default ContentManagement;