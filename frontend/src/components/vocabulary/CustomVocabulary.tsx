import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Separator } from '../ui/separator';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Plus,
  Search,
  Edit,
  Trash2,
  Upload,
  Download,
  BookOpen,
  Volume2,
  Check,
  X,
  Clock,
  BarChart3,
  Globe,
  Tag,
  FileText,
  Mic,
  RefreshCw,
  Settings,
  Database,
  Users
} from 'lucide-react';

interface VocabularyEntry {
  id: string;
  word: string;
  definition: string;
  domain: string;
  pronunciation?: string;
  phonetic_transcription?: string;
  example_usage?: string;
  synonyms: string[];
  related_terms: string[];
  difficulty_level: string;
  language: string;
  tags: string[];
  status: string;
  confidence_score: number;
  usage_count: number;
  created_at: string;
  updated_at: string;
  created_by: string;
}

interface VocabularyDomain {
  domain_name: string;
  description: string;
  keywords: string[];
  priority_level: string;
  auto_validation: boolean;
  min_confidence_threshold: number;
  language: string;
  entry_count: number;
}

interface VocabularyAnalytics {
  total_entries: number;
  entries_by_domain: Record<string, number>;
  entries_by_status: Record<string, number>;
  entries_by_language: Record<string, number>;
  most_used_words: Array<{ word: string; count: number }>;
  recent_additions: Array<{ word: string; domain: string; created_at: string }>;
  validation_statistics: Record<string, any>;
  domain_coverage: Record<string, number>;
}

const CustomVocabulary: React.FC = () => {
  const [entries, setEntries] = useState<VocabularyEntry[]>([]);
  const [domains, setDomains] = useState<VocabularyDomain[]>([]);
  const [analytics, setAnalytics] = useState<VocabularyAnalytics | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<VocabularyEntry | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Search and filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  
  // Form state for new/edit entry
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    word: '',
    definition: '',
    domain: '',
    pronunciation: '',
    phonetic_transcription: '',
    example_usage: '',
    synonyms: '',
    related_terms: '',
    difficulty_level: 'intermediate',
    language: 'en',
    tags: ''
  });
  
  // Domain creation
  const [showDomainForm, setShowDomainForm] = useState(false);
  const [domainForm, setDomainForm] = useState({
    domain_name: '',
    description: '',
    keywords: '',
    priority_level: 'medium',
    auto_validation: false,
    min_confidence_threshold: 0.7,
    language: 'en'
  });
  
  // Bulk import
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [bulkImportText, setBulkImportText] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadEntries();
    loadDomains();
    loadAnalytics();
  }, []);

  const loadEntries = async () => {
    try {
      setIsLoading(true);
      const searchParams = {
        query: searchQuery || 'all',
        domain: selectedDomain || undefined,
        language: selectedLanguage || undefined,
        status: selectedStatus || undefined,
        limit: 50
      };
      
      const response = await fetch('/api/v1/custom-vocabulary/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(searchParams)
      });
      
      if (response.ok) {
        const data = await response.json();
        setEntries(data.data);
      }
    } catch (error) {
      setError('Failed to load vocabulary entries');
    } finally {
      setIsLoading(false);
    }
  };

  const loadDomains = async () => {
    try {
      const response = await fetch('/api/v1/custom-vocabulary/domains');
      if (response.ok) {
        const data = await response.json();
        setDomains(data.data);
      }
    } catch (error) {
      console.error('Failed to load domains:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch('/api/v1/custom-vocabulary/analytics');
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data.data);
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };

  const handleSearch = () => {
    loadEntries();
  };

  const handleCreateEntry = async () => {
    try {
      setIsLoading(true);
      const entryData = {
        ...formData,
        synonyms: formData.synonyms.split(',').map(s => s.trim()).filter(s => s),
        related_terms: formData.related_terms.split(',').map(s => s.trim()).filter(s => s),
        tags: formData.tags.split(',').map(s => s.trim()).filter(s => s)
      };
      
      const response = await fetch('/api/v1/custom-vocabulary/entries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entryData)
      });
      
      if (response.ok) {
        resetForm();
        loadEntries();
        loadAnalytics();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create entry');
      }
    } catch (error) {
      setError('Failed to create vocabulary entry');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateEntry = async () => {
    if (!selectedEntry) return;
    
    try {
      setIsLoading(true);
      const entryData = {
        ...formData,
        synonyms: formData.synonyms.split(',').map(s => s.trim()).filter(s => s),
        related_terms: formData.related_terms.split(',').map(s => s.trim()).filter(s => s),
        tags: formData.tags.split(',').map(s => s.trim()).filter(s => s)
      };
      
      const response = await fetch(`/api/v1/custom-vocabulary/entries/${selectedEntry.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entryData)
      });
      
      if (response.ok) {
        resetForm();
        loadEntries();
        loadAnalytics();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to update entry');
      }
    } catch (error) {
      setError('Failed to update vocabulary entry');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteEntry = async (entryId: string) => {
    if (!confirm('Are you sure you want to delete this entry?')) return;
    
    try {
      const response = await fetch(`/api/v1/custom-vocabulary/entries/${entryId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        loadEntries();
        loadAnalytics();
      } else {
        setError('Failed to delete entry');
      }
    } catch (error) {
      setError('Failed to delete vocabulary entry');
    }
  };

  const handleValidateEntry = async (entryId: string, status: string) => {
    try {
      const formData = new FormData();
      formData.append('validation_status', status);
      
      const response = await fetch(`/api/v1/custom-vocabulary/validate/${entryId}`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        loadEntries();
        loadAnalytics();
      } else {
        setError('Failed to validate entry');
      }
    } catch (error) {
      setError('Failed to validate vocabulary entry');
    }
  };

  const handleCreateDomain = async () => {
    try {
      setIsLoading(true);
      const domainData = {
        ...domainForm,
        keywords: domainForm.keywords.split(',').map(s => s.trim()).filter(s => s)
      };
      
      const response = await fetch('/api/v1/custom-vocabulary/domains', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(domainData)
      });
      
      if (response.ok) {
        setShowDomainForm(false);
        setDomainForm({
          domain_name: '',
          description: '',
          keywords: '',
          priority_level: 'medium',
          auto_validation: false,
          min_confidence_threshold: 0.7,
          language: 'en'
        });
        loadDomains();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create domain');
      }
    } catch (error) {
      setError('Failed to create domain');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBulkImport = async () => {
    try {
      setIsLoading(true);
      const lines = bulkImportText.split('\n').filter(line => line.trim());
      const entries = lines.map(line => {
        const parts = line.split('\t'); // Tab-separated format
        return {
          word: parts[0] || '',
          definition: parts[1] || '',
          domain: selectedDomain || 'general',
          pronunciation: parts[2] || '',
          example_usage: parts[3] || '',
          synonyms: parts[4] ? parts[4].split(',').map(s => s.trim()) : [],
          related_terms: parts[5] ? parts[5].split(',').map(s => s.trim()) : [],
          difficulty_level: parts[6] || 'intermediate',
          language: selectedLanguage || 'en',
          tags: parts[7] ? parts[7].split(',').map(s => s.trim()) : []
        };
      });
      
      const importData = {
        entries,
        domain: selectedDomain || 'general',
        auto_validate: false,
        overwrite_existing: false
      };
      
      const response = await fetch('/api/v1/custom-vocabulary/bulk-import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(importData)
      });
      
      if (response.ok) {
        const result = await response.json();
        setShowBulkImport(false);
        setBulkImportText('');
        loadEntries();
        loadAnalytics();
        alert(`Import completed: ${result.data.summary.successful} successful, ${result.data.summary.failed} failed`);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to import entries');
      }
    } catch (error) {
      setError('Failed to perform bulk import');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async (format: string) => {
    try {
      const response = await fetch('/api/v1/custom-vocabulary/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: selectedDomain || undefined,
          language: selectedLanguage || undefined,
          format
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        const blob = new Blob([data.data.export_data], { 
          type: format === 'json' ? 'application/json' : 'text/csv' 
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vocabulary_export.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      setError('Failed to export vocabulary');
    }
  };

  const resetForm = () => {
    setFormData({
      word: '',
      definition: '',
      domain: '',
      pronunciation: '',
      phonetic_transcription: '',
      example_usage: '',
      synonyms: '',
      related_terms: '',
      difficulty_level: 'intermediate',
      language: 'en',
      tags: ''
    });
    setSelectedEntry(null);
    setIsEditing(false);
  };

  const editEntry = (entry: VocabularyEntry) => {
    setFormData({
      word: entry.word,
      definition: entry.definition,
      domain: entry.domain,
      pronunciation: entry.pronunciation || '',
      phonetic_transcription: entry.phonetic_transcription || '',
      example_usage: entry.example_usage || '',
      synonyms: entry.synonyms.join(', '),
      related_terms: entry.related_terms.join(', '),
      difficulty_level: entry.difficulty_level,
      language: entry.language,
      tags: entry.tags.join(', ')
    });
    setSelectedEntry(entry);
    setIsEditing(true);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getDifficultyColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'beginner':
        return 'bg-green-100 text-green-800';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'advanced':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Custom Vocabulary Management
        </h1>
        <p className="text-gray-600">
          Manage domain-specific terminology and custom vocabulary entries
        </p>
      </div>

      <Tabs defaultValue="entries" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="entries">
            <BookOpen className="w-4 h-4 mr-2" />
            Entries
          </TabsTrigger>
          <TabsTrigger value="domains">
            <Database className="w-4 h-4 mr-2" />
            Domains
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="w-4 h-4 mr-2" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="import-export">
            <Upload className="w-4 h-4 mr-2" />
            Import/Export
          </TabsTrigger>
        </TabsList>

        <TabsContent value="entries" className="space-y-6">
          {/* Search and Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="w-5 h-5" />
                Search & Filter
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <Label htmlFor="search">Search Terms</Label>
                  <Input
                    id="search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search vocabulary..."
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                </div>
                <div>
                  <Label htmlFor="domain-filter">Domain</Label>
                  <select
                    id="domain-filter"
                    value={selectedDomain}
                    onChange={(e) => setSelectedDomain(e.target.value)}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="">All domains</option>
                    {domains.map(domain => (
                      <option key={domain.domain_name} value={domain.domain_name}>
                        {domain.domain_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label htmlFor="language-filter">Language</Label>
                  <select
                    id="language-filter"
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="">All languages</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="status-filter">Status</Label>
                  <select
                    id="status-filter"
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="">All statuses</option>
                    <option value="approved">Approved</option>
                    <option value="pending">Pending</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
              </div>
              <Button onClick={handleSearch} disabled={isLoading}>
                <Search className="w-4 h-4 mr-2" />
                Search
              </Button>
            </CardContent>
          </Card>

          {/* Add/Edit Entry Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  {isEditing ? 'Edit Entry' : 'Add New Entry'}
                </span>
                {isEditing && (
                  <Button variant="outline" onClick={resetForm}>
                    Cancel
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="word">Word *</Label>
                  <Input
                    id="word"
                    value={formData.word}
                    onChange={(e) => setFormData({...formData, word: e.target.value})}
                    placeholder="Enter word"
                  />
                </div>
                <div>
                  <Label htmlFor="domain">Domain *</Label>
                  <select
                    id="domain"
                    value={formData.domain}
                    onChange={(e) => setFormData({...formData, domain: e.target.value})}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="">Select domain</option>
                    {domains.map(domain => (
                      <option key={domain.domain_name} value={domain.domain_name}>
                        {domain.domain_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <Label htmlFor="definition">Definition *</Label>
                <textarea
                  id="definition"
                  value={formData.definition}
                  onChange={(e) => setFormData({...formData, definition: e.target.value})}
                  placeholder="Enter definition"
                  className="w-full mt-1 p-3 border border-gray-300 rounded-md resize-none"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="pronunciation">Pronunciation</Label>
                  <Input
                    id="pronunciation"
                    value={formData.pronunciation}
                    onChange={(e) => setFormData({...formData, pronunciation: e.target.value})}
                    placeholder="e.g., /prəˌnʌnsiˈeɪʃən/"
                  />
                </div>
                <div>
                  <Label htmlFor="phonetic">Phonetic Transcription</Label>
                  <Input
                    id="phonetic"
                    value={formData.phonetic_transcription}
                    onChange={(e) => setFormData({...formData, phonetic_transcription: e.target.value})}
                    placeholder="IPA transcription"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="example">Example Usage</Label>
                <Input
                  id="example"
                  value={formData.example_usage}
                  onChange={(e) => setFormData({...formData, example_usage: e.target.value})}
                  placeholder="Example sentence using the word"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="synonyms">Synonyms (comma-separated)</Label>
                  <Input
                    id="synonyms"
                    value={formData.synonyms}
                    onChange={(e) => setFormData({...formData, synonyms: e.target.value})}
                    placeholder="synonym1, synonym2, synonym3"
                  />
                </div>
                <div>
                  <Label htmlFor="related">Related Terms (comma-separated)</Label>
                  <Input
                    id="related"
                    value={formData.related_terms}
                    onChange={(e) => setFormData({...formData, related_terms: e.target.value})}
                    placeholder="term1, term2, term3"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="difficulty">Difficulty Level</Label>
                  <select
                    value={formData.difficulty_level}
                    onChange={(e) => setFormData({...formData, difficulty_level: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="language">Language</Label>
                  <select
                    value={formData.language}
                    onChange={(e) => setFormData({...formData, language: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="tags">Tags (comma-separated)</Label>
                  <Input
                    id="tags"
                    value={formData.tags}
                    onChange={(e) => setFormData({...formData, tags: e.target.value})}
                    placeholder="tag1, tag2, tag3"
                  />
                </div>
              </div>

              <Button 
                onClick={isEditing ? handleUpdateEntry : handleCreateEntry}
                disabled={isLoading || !formData.word || !formData.definition || !formData.domain}
                className="w-full"
              >
                {isLoading ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4 mr-2" />
                )}
                {isEditing ? 'Update Entry' : 'Add Entry'}
              </Button>
            </CardContent>
          </Card>

          {/* Entries List */}
          <Card>
            <CardHeader>
              <CardTitle>Vocabulary Entries ({entries.length})</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
                  <p>Loading entries...</p>
                </div>
              ) : entries.length === 0 ? (
                <div className="text-center py-8">
                  <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No vocabulary entries found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {entries.map((entry) => (
                    <div key={entry.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold">{entry.word}</h3>
                            <Badge className={getStatusColor(entry.status)}>
                              {entry.status}
                            </Badge>
                            <Badge className={getDifficultyColor(entry.difficulty_level)}>
                              {entry.difficulty_level}
                            </Badge>
                            <Badge variant="outline">{entry.domain}</Badge>
                          </div>
                          <p className="text-gray-700 mb-2">{entry.definition}</p>
                          {entry.example_usage && (
                            <p className="text-sm text-gray-600 italic mb-2">
                              Example: {entry.example_usage}
                            </p>
                          )}
                          <div className="flex items-center gap-4 text-sm text-gray-500">
                            <span>Usage: {entry.usage_count}</span>
                            <span>Confidence: {(entry.confidence_score * 100).toFixed(0)}%</span>
                            <span>Language: {entry.language}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {entry.status === 'pending' && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleValidateEntry(entry.id, 'approved')}
                              >
                                <Check className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleValidateEntry(entry.id, 'rejected')}
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => editEntry(entry)}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteEntry(entry.id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      
                      {(entry.synonyms.length > 0 || entry.related_terms.length > 0 || entry.tags.length > 0) && (
                        <div className="space-y-2">
                          {entry.synonyms.length > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium">Synonyms:</span>
                              <div className="flex flex-wrap gap-1">
                                {entry.synonyms.map((synonym, idx) => (
                                  <Badge key={idx} variant="secondary" className="text-xs">
                                    {synonym}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                          {entry.related_terms.length > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium">Related:</span>
                              <div className="flex flex-wrap gap-1">
                                {entry.related_terms.map((term, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs">
                                    {term}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                          {entry.tags.length > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium">Tags:</span>
                              <div className="flex flex-wrap gap-1">
                                {entry.tags.map((tag, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs">
                                    <Tag className="w-3 h-3 mr-1" />
                                    {tag}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="domains" className="space-y-6">
          {/* Domain Creation Form */}
          {showDomainForm && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Create New Domain</span>
                  <Button variant="outline" onClick={() => setShowDomainForm(false)}>
                    Cancel
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="domain-name">Domain Name *</Label>
                    <Input
                      id="domain-name"
                      value={domainForm.domain_name}
                      onChange={(e) => setDomainForm({...domainForm, domain_name: e.target.value})}
                      placeholder="e.g., medical, legal, technical"
                    />
                  </div>
                  <div>
                    <Label htmlFor="priority">Priority Level</Label>
                    <select
                      value={domainForm.priority_level}
                      onChange={(e) => setDomainForm({...domainForm, priority_level: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="domain-description">Description *</Label>
                  <textarea
                    id="domain-description"
                    value={domainForm.description}
                    onChange={(e) => setDomainForm({...domainForm, description: e.target.value})}
                    placeholder="Describe this domain and its purpose"
                    className="w-full mt-1 p-3 border border-gray-300 rounded-md resize-none"
                    rows={3}
                  />
                </div>

                <div>
                  <Label htmlFor="keywords">Keywords (comma-separated)</Label>
                  <Input
                    id="keywords"
                    value={domainForm.keywords}
                    onChange={(e) => setDomainForm({...domainForm, keywords: e.target.value})}
                    placeholder="keyword1, keyword2, keyword3"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="domain-language">Language</Label>
                    <select
                      value={domainForm.language}
                      onChange={(e) => setDomainForm({...domainForm, language: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                      <option value="it">Italian</option>
                    </select>
                  </div>
                  <div>
                    <Label htmlFor="threshold">Min Confidence: {domainForm.min_confidence_threshold}</Label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={domainForm.min_confidence_threshold}
                      onChange={(e) => setDomainForm({...domainForm, min_confidence_threshold: parseFloat(e.target.value)})}
                      className="w-full mt-1"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="auto-validation">Auto Validation</Label>
                    <Switch
                      id="auto-validation"
                      checked={domainForm.auto_validation}
                      onCheckedChange={(checked) => setDomainForm({...domainForm, auto_validation: checked})}
                    />
                  </div>
                </div>

                <Button 
                  onClick={handleCreateDomain}
                  disabled={isLoading || !domainForm.domain_name || !domainForm.description}
                  className="w-full"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Domain
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Domains List */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Vocabulary Domains ({domains.length})</span>
                <Button onClick={() => setShowDomainForm(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Domain
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {domains.length === 0 ? (
                <div className="text-center py-8">
                  <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No domains created yet</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {domains.map((domain) => (
                    <div key={domain.domain_name} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="text-lg font-semibold">{domain.domain_name}</h3>
                          <p className="text-gray-600 text-sm">{domain.description}</p>
                        </div>
                        <Badge variant="outline">{domain.priority_level}</Badge>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span>Entries:</span>
                          <span className="font-medium">{domain.entry_count || 0}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Language:</span>
                          <span className="font-medium">{domain.language}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Auto Validation:</span>
                          <span className="font-medium">{domain.auto_validation ? 'Yes' : 'No'}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Min Confidence:</span>
                          <span className="font-medium">{(domain.min_confidence_threshold * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                      
                      {domain.keywords.length > 0 && (
                        <div className="mt-3">
                          <p className="text-sm font-medium mb-1">Keywords:</p>
                          <div className="flex flex-wrap gap-1">
                            {domain.keywords.map((keyword, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {keyword}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          {analytics && (
            <>
              {/* Overview Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-6 text-center">
                    <div className="text-2xl font-bold text-blue-600">{analytics.total_entries}</div>
                    <div className="text-sm text-gray-500">Total Entries</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6 text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {Object.keys(analytics.entries_by_domain).length}
                    </div>
                    <div className="text-sm text-gray-500">Active Domains</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6 text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {Object.keys(analytics.entries_by_language).length}
                    </div>
                    <div className="text-sm text-gray-500">Languages</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6 text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {analytics.entries_by_status.approved || 0}
                    </div>
                    <div className="text-sm text-gray-500">Approved Entries</div>
                  </CardContent>
                </Card>
              </div>

              {/* Detailed Analytics */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Entries by Domain</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(analytics.entries_by_domain).map(([domain, count]) => (
                        <div key={domain} className="flex items-center justify-between">
                          <span className="text-sm">{domain}</span>
                          <div className="flex items-center gap-2">
                            <div className="w-20 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${(count / analytics.total_entries) * 100}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium">{count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Entries by Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(analytics.entries_by_status).map(([status, count]) => (
                        <div key={status} className="flex items-center justify-between">
                          <span className="text-sm capitalize">{status}</span>
                          <div className="flex items-center gap-2">
                            <div className="w-20 bg-gray-200 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full ${
                                  status === 'approved' ? 'bg-green-600' :
                                  status === 'pending' ? 'bg-yellow-600' : 'bg-red-600'
                                }`}
                                style={{ width: `${(count / analytics.total_entries) * 100}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium">{count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Most Used Words</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analytics.most_used_words.slice(0, 10).map((item, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm font-medium">{item.word}</span>
                          <Badge variant="outline">{item.count} uses</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Recent Additions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analytics.recent_additions.slice(0, 10).map((item, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <div>
                            <span className="text-sm font-medium">{item.word}</span>
                            <span className="text-xs text-gray-500 ml-2">({item.domain})</span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {new Date(item.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}

          {!analytics && (
            <Card>
              <CardContent className="text-center py-12">
                <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Loading analytics...</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="import-export" className="space-y-6">
          {/* Bulk Import */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Bulk Import
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="import-domain">Target Domain</Label>
                  <select
                    id="import-domain"
                    value={selectedDomain}
                    onChange={(e) => setSelectedDomain(e.target.value)}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="">Select domain</option>
                    {domains.map(domain => (
                      <option key={domain.domain_name} value={domain.domain_name}>
                        {domain.domain_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label htmlFor="import-language">Language</Label>
                  <select
                    id="import-language"
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="">Select language</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                  </select>
                </div>
              </div>

              <div>
                <Label htmlFor="import-data">Import Data (Tab-separated format)</Label>
                <textarea
                  id="import-data"
                  value={bulkImportText}
                  onChange={(e) => setBulkImportText(e.target.value)}
                  placeholder="word	definition	pronunciation	example	synonyms	related_terms	difficulty	tags"
                  className="w-full mt-1 p-3 border border-gray-300 rounded-md resize-none font-mono text-sm"
                  rows={10}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Format: word, definition, pronunciation, example, synonyms, related_terms, difficulty, tags (tab-separated)
                </p>
              </div>

              <Button 
                onClick={handleBulkImport}
                disabled={isLoading || !bulkImportText.trim() || !selectedDomain}
                className="w-full"
              >
                <Upload className="w-4 h-4 mr-2" />
                Import Entries
              </Button>
            </CardContent>
          </Card>

          {/* Export */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="w-5 h-5" />
                Export Vocabulary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="export-domain">Filter by Domain</Label>
                  <select
                    id="export-domain"
                    value={selectedDomain}
                    onChange={(e) => setSelectedDomain(e.target.value)}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="">All domains</option>
                    {domains.map(domain => (
                      <option key={domain.domain_name} value={domain.domain_name}>
                        {domain.domain_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label htmlFor="export-language">Filter by Language</Label>
                  <select
                    id="export-language"
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="">All languages</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-2">
                <Button onClick={() => handleExport('json')} className="flex-1">
                  <Download className="w-4 h-4 mr-2" />
                  Export JSON
                </Button>
                <Button onClick={() => handleExport('csv')} className="flex-1">
                  <Download className="w-4 h-4 mr-2" />
                  Export CSV
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default CustomVocabulary;