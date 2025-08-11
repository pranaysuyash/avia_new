import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Separator } from '../ui/separator';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  FileText, 
  Zap, 
  Settings, 
  Download, 
  Copy, 
  RefreshCw,
  Clock,
  BarChart3,
  Target,
  BookOpen,
  Users,
  Sparkles
} from 'lucide-react';

interface SummaryResult {
  summary: string;
  summary_type: string;
  length: string;
  style: string;
  word_count: number;
  sentence_count: number;
  compression_ratio: number;
  quality_score: number;
  key_points: string[];
  extracted_sentences: string[];
  confidence_score: number;
  processing_time: number;
  metadata: Record<string, any>;
  created_at: string;
}

interface SummaryOptions {
  summary_types: Array<{value: string, label: string, description: string}>;
  lengths: Array<{value: string, label: string, description: string}>;
  styles: Array<{value: string, label: string, description: string}>;
}

interface UserPreferences {
  preferred_length: string;
  preferred_style: string;
  focus_areas: string[];
  avoid_topics: string[];
  technical_level: string;
  include_examples: boolean;
  include_numbers: boolean;
  language: string;
}

const HybridSummarization: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [summaryType, setSummaryType] = useState('hybrid');
  const [length, setLength] = useState('medium');
  const [style, setStyle] = useState('formal');
  const [query, setQuery] = useState('');
  const [maxSentences, setMaxSentences] = useState<number | undefined>();
  const [maxWords, setMaxWords] = useState<number | undefined>();
  const [focusKeywords, setFocusKeywords] = useState<string[]>([]);
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  const [preserveStructure, setPreserveStructure] = useState(false);
  const [includeQuotes, setIncludeQuotes] = useState(true);
  const [language, setLanguage] = useState('en');
  
  const [result, setResult] = useState<SummaryResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<SummaryOptions | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  
  const [keywordInput, setKeywordInput] = useState('');
  const [excludeInput, setExcludeInput] = useState('');
  const [activeTab, setActiveTab] = useState('basic');

  // Load summary options and user preferences
  useEffect(() => {
    loadSummaryOptions();
    loadUserPreferences();
  }, []);

  const loadSummaryOptions = async () => {
    try {
      const response = await fetch('/api/v1/hybrid-summarization/types');
      if (response.ok) {
        const data = await response.json();
        setOptions(data.data);
      }
    } catch (error) {
      console.error('Failed to load summary options:', error);
    }
  };

  const loadUserPreferences = async () => {
    try {
      const userId = 'current-user'; // Replace with actual user ID
      const response = await fetch(`/api/v1/hybrid-summarization/preferences/${userId}`);
      if (response.ok) {
        const data = await response.json();
        const prefs = data.data.preferences;
        setPreferences(prefs);
        
        // Apply preferences to form
        setLength(prefs.preferred_length || 'medium');
        setStyle(prefs.preferred_style || 'formal');
        setLanguage(prefs.language || 'en');
      }
    } catch (error) {
      console.error('Failed to load user preferences:', error);
    }
  };

  const handleSummarize = async () => {
    if (!inputText.trim()) {
      setError('Please enter text to summarize');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const requestBody = {
        text: inputText,
        summary_type: summaryType,
        length,
        style,
        query: query || undefined,
        max_sentences: maxSentences,
        max_words: maxWords,
        focus_keywords: focusKeywords.length > 0 ? focusKeywords : undefined,
        exclude_keywords: excludeKeywords.length > 0 ? excludeKeywords : undefined,
        preserve_structure: preserveStructure,
        include_quotes: includeQuotes,
        language
      };

      const response = await fetch('/api/v1/hybrid-summarization/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create summary');
      }

      const data = await response.json();
      setResult(data.data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const addKeyword = (keyword: string, type: 'focus' | 'exclude') => {
    if (!keyword.trim()) return;
    
    if (type === 'focus') {
      setFocusKeywords(prev => [...prev, keyword.trim()]);
      setKeywordInput('');
    } else {
      setExcludeKeywords(prev => [...prev, keyword.trim()]);
      setExcludeInput('');
    }
  };

  const removeKeyword = (keyword: string, type: 'focus' | 'exclude') => {
    if (type === 'focus') {
      setFocusKeywords(prev => prev.filter(k => k !== keyword));
    } else {
      setExcludeKeywords(prev => prev.filter(k => k !== keyword));
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const exportSummary = () => {
    if (!result) return;
    
    const exportData = {
      summary: result.summary,
      metadata: {
        type: result.summary_type,
        length: result.length,
        style: result.style,
        word_count: result.word_count,
        quality_score: result.quality_score,
        created_at: result.created_at
      },
      key_points: result.key_points
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `summary-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center space-x-2">
        <Sparkles className="h-6 w-6 text-blue-600" />
        <h1 className="text-2xl font-bold">Hybrid Summarization</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Input Text</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="Enter the text you want to summarize..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="min-h-[200px]"
            />
            
            <div className="flex justify-between text-sm text-gray-500">
              <span>{inputText.length} characters</span>
              <span>{inputText.split(/\s+/).filter(w => w.length > 0).length} words</span>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="basic">Basic</TabsTrigger>
                <TabsTrigger value="advanced">Advanced</TabsTrigger>
                <TabsTrigger value="preferences">Preferences</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="summary-type">Summary Type</Label>
                    <Select value={summaryType} onValueChange={setSummaryType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {options?.summary_types.map(type => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="length">Length</Label>
                    <Select value={length} onValueChange={setLength}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {options?.lengths.map(len => (
                          <SelectItem key={len.value} value={len.value}>
                            {len.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="style">Style</Label>
                  <Select value={style} onValueChange={setStyle}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {options?.styles.map(st => (
                        <SelectItem key={st.value} value={st.value}>
                          {st.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {summaryType === 'query_focused' && (
                  <div>
                    <Label htmlFor="query">Focus Query</Label>
                    <Input
                      id="query"
                      placeholder="What should the summary focus on?"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </div>
                )}
              </TabsContent>

              <TabsContent value="advanced" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="max-sentences">Max Sentences</Label>
                    <Input
                      id="max-sentences"
                      type="number"
                      min="1"
                      max="50"
                      value={maxSentences || ''}
                      onChange={(e) => setMaxSentences(e.target.value ? parseInt(e.target.value) : undefined)}
                    />
                  </div>

                  <div>
                    <Label htmlFor="max-words">Max Words</Label>
                    <Input
                      id="max-words"
                      type="number"
                      min="10"
                      max="1000"
                      value={maxWords || ''}
                      onChange={(e) => setMaxWords(e.target.value ? parseInt(e.target.value) : undefined)}
                    />
                  </div>
                </div>

                <div>
                  <Label>Focus Keywords</Label>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="Add keyword to focus on..."
                      value={keywordInput}
                      onChange={(e) => setKeywordInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addKeyword(keywordInput, 'focus')}
                    />
                    <Button 
                      type="button" 
                      onClick={() => addKeyword(keywordInput, 'focus')}
                      size="sm"
                    >
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {focusKeywords.map(keyword => (
                      <Badge key={keyword} variant="secondary" className="cursor-pointer">
                        {keyword}
                        <button 
                          onClick={() => removeKeyword(keyword, 'focus')}
                          className="ml-1 text-xs"
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <Label>Exclude Keywords</Label>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="Add keyword to exclude..."
                      value={excludeInput}
                      onChange={(e) => setExcludeInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addKeyword(excludeInput, 'exclude')}
                    />
                    <Button 
                      type="button" 
                      onClick={() => addKeyword(excludeInput, 'exclude')}
                      size="sm"
                    >
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {excludeKeywords.map(keyword => (
                      <Badge key={keyword} variant="destructive" className="cursor-pointer">
                        {keyword}
                        <button 
                          onClick={() => removeKeyword(keyword, 'exclude')}
                          className="ml-1 text-xs"
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="preserve-structure"
                      checked={preserveStructure}
                      onCheckedChange={setPreserveStructure}
                    />
                    <Label htmlFor="preserve-structure">Preserve Structure</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="include-quotes"
                      checked={includeQuotes}
                      onCheckedChange={setIncludeQuotes}
                    />
                    <Label htmlFor="include-quotes">Include Quotes</Label>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="preferences" className="space-y-4">
                {preferences && (
                  <div className="space-y-4">
                    <div className="text-sm text-gray-600">
                      Your saved preferences are automatically applied
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <strong>Preferred Length:</strong> {preferences.preferred_length}
                      </div>
                      <div>
                        <strong>Preferred Style:</strong> {preferences.preferred_style}
                      </div>
                      <div>
                        <strong>Technical Level:</strong> {preferences.technical_level}
                      </div>
                      <div>
                        <strong>Language:</strong> {preferences.language}
                      </div>
                    </div>
                  </div>
                )}
              </TabsContent>
            </Tabs>

            <Button 
              onClick={handleSummarize} 
              disabled={isLoading || !inputText.trim()}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Generating Summary...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  Generate Summary
                </>
              )}
            </Button>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Results Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <BookOpen className="h-5 w-5" />
                <span>Summary Result</span>
              </div>
              {result && (
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(result.summary)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={exportSummary}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-6">
                {/* Summary Text */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-gray-800 leading-relaxed">{result.summary}</p>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Quality Score</span>
                      <span className="font-medium">{(result.quality_score * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={result.quality_score * 100} className="h-2" />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Confidence</span>
                      <span className="font-medium">{(result.confidence_score * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={result.confidence_score * 100} className="h-2" />
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-blue-600">{result.word_count}</div>
                    <div className="text-xs text-gray-500">Words</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">{result.sentence_count}</div>
                    <div className="text-xs text-gray-500">Sentences</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">{result.compression_ratio.toFixed(1)}x</div>
                    <div className="text-xs text-gray-500">Compression</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-orange-600">{result.processing_time.toFixed(1)}s</div>
                    <div className="text-xs text-gray-500">Time</div>
                  </div>
                </div>

                <Separator />

                {/* Key Points */}
                {result.key_points.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3 flex items-center">
                      <Target className="h-4 w-4 mr-2" />
                      Key Points
                    </h3>
                    <ul className="space-y-2">
                      {result.key_points.map((point, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <span className="text-blue-600 font-bold">•</span>
                          <span className="text-sm">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Extracted Sentences */}
                {result.extracted_sentences.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3 flex items-center">
                      <BarChart3 className="h-4 w-4 mr-2" />
                      Extracted Sentences
                    </h3>
                    <div className="space-y-2">
                      {result.extracted_sentences.map((sentence, index) => (
                        <div key={index} className="p-2 bg-blue-50 rounded text-sm">
                          {sentence}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Metadata */}
                <div className="text-xs text-gray-500 space-y-1">
                  <div>Type: {result.summary_type} | Style: {result.style} | Length: {result.length}</div>
                  <div>Created: {new Date(result.created_at).toLocaleString()}</div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Your summary will appear here</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default HybridSummarization;