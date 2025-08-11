import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { Separator } from '../ui/separator';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import {
  Play,
  Pause,
  Download,
  Share2,
  Settings,
  Video,
  Image as ImageIcon,
  BarChart,
  Map,
  Users,
  Zap,
  Clock,
  DollarSign,
  Star,
  AlertCircle,
  CheckCircle,
  Search,
  Filter,
  ShoppingCart,
  Eye,
  TrendingUp,
  Target,
  Lightbulb,
  Palette,
  Calendar,
  FileVideo,
  Layers,
  Grid,
  Shuffle,
  ChevronRight,
  ChevronDown,
  ExternalLink,
  Copy,
  RefreshCw,
  BookOpen
} from 'lucide-react';

interface TranscriptSegment {
  text: string;
  timestamp_start: number;
  timestamp_end: number;
  speaker?: string;
  emotion?: string;
  topics?: string[];
}

interface BRollSuggestion {
  suggestion_id: string;
  timestamp_start: number;
  timestamp_end: number;
  content_type: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  keywords: string[];
  description: string;
  rationale: string;
  search_query: string;
  duration: number;
  transition_type?: string;
  mood?: string;
  color_scheme?: string[];
  alternatives?: string[];
  confidence: number;
}

interface AnalysisSettings {
  enable_context_analysis: boolean;
  enable_emotion_detection: boolean;
  enable_topic_modeling: boolean;
  enable_visual_metaphors: boolean;
  enable_pacing_analysis: boolean;
  min_suggestion_duration: number;
  max_suggestion_duration: number;
  suggestion_density: 'low' | 'medium' | 'high';
  target_audience?: string;
  content_style?: string;
  budget_tier?: 'free' | 'budget' | 'premium';
}

interface BRollAnalysisResponse {
  analysis_id: string;
  suggestions: BRollSuggestion[];
  summary: {
    total_suggestions: number;
    coverage_percentage: number;
    priority_breakdown: Record<string, number>;
    content_type_distribution: Record<string, number>;
    estimated_enhancement_score: number;
    key_moments: Array<{
      timestamp: number;
      duration: number;
      type: string;
      description: string;
    }>;
  };
  timeline: Array<{
    start: number;
    end: number;
    type: string;
    priority: string;
    label: string;
  }>;
  estimated_cost?: {
    per_clip: number;
    total: number;
    currency: string;
  };
  processing_time: number;
  created_at: string;
}

const SmartBRollSuggestions: React.FC = () => {
  const [transcriptText, setTranscriptText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<BRollAnalysisResponse | null>(null);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('suggestions');
  const [showSettings, setShowSettings] = useState(false);
  const [previewSuggestion, setPreviewSuggestion] = useState<BRollSuggestion | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPriority, setFilterPriority] = useState<string>('all');
  const [filterContentType, setFilterContentType] = useState<string>('all');
  
  const [settings, setSettings] = useState<AnalysisSettings>({
    enable_context_analysis: true,
    enable_emotion_detection: true,
    enable_topic_modeling: true,
    enable_visual_metaphors: true,
    enable_pacing_analysis: true,
    min_suggestion_duration: 2.0,
    max_suggestion_duration: 10.0,
    suggestion_density: 'medium',
    target_audience: 'general',
    content_style: 'educational',
    budget_tier: 'budget'
  });

  const analyzeTranscript = async () => {
    if (!transcriptText.trim()) {
      setError('Please provide transcript text');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      // Parse transcript into segments (simplified)
      const segments: TranscriptSegment[] = transcriptText
        .split('\n')
        .filter(line => line.trim())
        .map((line, index) => ({
          text: line.trim(),
          timestamp_start: index * 10, // Simplified timing
          timestamp_end: (index + 1) * 10,
          speaker: `Speaker ${index % 2 + 1}`
        }));

      const requestBody = {
        transcript_segments: segments,
        video_duration: segments.length * 10,
        settings,
        metadata: {
          title: 'Video Analysis',
          created_at: new Date().toISOString()
        }
      };

      const response = await fetch('/api/v1/smart-broll/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const result = await response.json();
      setAnalysisResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze transcript');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const toggleSuggestion = (suggestionId: string) => {
    const newSelected = new Set(selectedSuggestions);
    if (newSelected.has(suggestionId)) {
      newSelected.delete(suggestionId);
    } else {
      newSelected.add(suggestionId);
    }
    setSelectedSuggestions(newSelected);
  };

  const generateShoppingList = async () => {
    if (!analysisResult) return;

    const selectedSuggestionObjs = analysisResult.suggestions.filter(s => 
      selectedSuggestions.has(s.suggestion_id)
    );

    try {
      const response = await fetch('/api/v1/smart-broll/generate-shopping-list', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          suggestions: selectedSuggestionObjs,
          budget: settings.budget_tier === 'free' ? 0 : 500,
          preferred_sources: ['pexels', 'unsplash']
        }),
      });

      const shoppingList = await response.json();
      console.log('Shopping list generated:', shoppingList);
    } catch (err) {
      setError('Failed to generate shopping list');
    }
  };

  const searchStockLibraries = async (suggestion: BRollSuggestion) => {
    try {
      const response = await fetch('/api/v1/smart-broll/search-stock', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: suggestion.search_query,
          content_type: suggestion.content_type,
          max_results: 10
        }),
      });

      const results = await response.json();
      console.log('Stock search results:', results);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[priority as keyof typeof colors] || colors.low;
  };

  const getContentTypeIcon = (contentType: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      stock_video: <Video className="h-4 w-4" />,
      stock_image: <ImageIcon className="h-4 w-4" />,
      animation: <Zap className="h-4 w-4" />,
      infographic: <BarChart className="h-4 w-4" />,
      map: <Map className="h-4 w-4" />,
      chart: <BarChart className="h-4 w-4" />,
      people: <Users className="h-4 w-4" />,
      technology: <Layers className="h-4 w-4" />,
      nature: <Palette className="h-4 w-4" />
    };
    return iconMap[contentType] || <FileVideo className="h-4 w-4" />;
  };

  const filteredSuggestions = analysisResult?.suggestions.filter(suggestion => {
    const matchesSearch = searchQuery === '' || 
      suggestion.keywords.some(k => k.toLowerCase().includes(searchQuery.toLowerCase())) ||
      suggestion.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesPriority = filterPriority === 'all' || suggestion.priority === filterPriority;
    const matchesContentType = filterContentType === 'all' || suggestion.content_type === filterContentType;
    
    return matchesSearch && matchesPriority && matchesContentType;
  }) || [];

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Lightbulb className="h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-bold">Smart B-Roll Suggestions</h1>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
          {analysisResult && (
            <Button onClick={generateShoppingList}>
              <ShoppingCart className="h-4 w-4 mr-2" />
              Shopping List
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BookOpen className="h-5 w-5" />
              <span>Transcript Input</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="transcript">Video Transcript</Label>
              <Textarea
                id="transcript"
                placeholder="Paste your video transcript here..."
                value={transcriptText}
                onChange={(e) => setTranscriptText(e.target.value)}
                rows={10}
                className="mt-2"
              />
            </div>

            {showSettings && (
              <div className="space-y-4 border-t pt-4">
                <h3 className="font-semibold">Analysis Settings</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Suggestion Density</Label>
                    <Select 
                      value={settings.suggestion_density} 
                      onValueChange={(value: 'low' | 'medium' | 'high') => 
                        setSettings({...settings, suggestion_density: value})
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label>Budget Tier</Label>
                    <Select 
                      value={settings.budget_tier || 'budget'} 
                      onValueChange={(value: 'free' | 'budget' | 'premium') => 
                        setSettings({...settings, budget_tier: value})
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="free">Free</SelectItem>
                        <SelectItem value="budget">Budget</SelectItem>
                        <SelectItem value="premium">Premium</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Context Analysis</Label>
                    <Switch
                      checked={settings.enable_context_analysis}
                      onCheckedChange={(checked) => 
                        setSettings({...settings, enable_context_analysis: checked})
                      }
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Emotion Detection</Label>
                    <Switch
                      checked={settings.enable_emotion_detection}
                      onCheckedChange={(checked) => 
                        setSettings({...settings, enable_emotion_detection: checked})
                      }
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Visual Metaphors</Label>
                    <Switch
                      checked={settings.enable_visual_metaphors}
                      onCheckedChange={(checked) => 
                        setSettings({...settings, enable_visual_metaphors: checked})
                      }
                    />
                  </div>
                </div>
              </div>
            )}

            <Button
              onClick={analyzeTranscript}
              className="w-full"
              disabled={!transcriptText.trim() || isAnalyzing}
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Target className="h-4 w-4 mr-2" />
                  Generate B-Roll Suggestions
                </>
              )}
            </Button>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Results Panel */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Grid className="h-5 w-5" />
                <span>B-Roll Suggestions</span>
              </div>
              {analysisResult && (
                <Badge variant="success" className="flex items-center space-x-1">
                  <CheckCircle className="h-3 w-3" />
                  <span>{analysisResult.suggestions.length} Suggestions</span>
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!analysisResult ? (
              <div className="text-center py-12 text-gray-500">
                <Video className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Analyze your transcript to see B-roll suggestions</p>
              </div>
            ) : (
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
                  <TabsTrigger value="timeline">Timeline</TabsTrigger>
                  <TabsTrigger value="summary">Summary</TabsTrigger>
                  <TabsTrigger value="shopping">Shopping</TabsTrigger>
                </TabsList>

                <TabsContent value="suggestions" className="space-y-4">
                  {/* Filters */}
                  <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          placeholder="Search suggestions..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="pl-10"
                        />
                      </div>
                    </div>
                    <Select value={filterPriority} onValueChange={setFilterPriority}>
                      <SelectTrigger className="w-[120px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Priority</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="low">Low</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={filterContentType} onValueChange={setFilterContentType}>
                      <SelectTrigger className="w-[140px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Types</SelectItem>
                        <SelectItem value="stock_video">Stock Video</SelectItem>
                        <SelectItem value="stock_image">Stock Image</SelectItem>
                        <SelectItem value="animation">Animation</SelectItem>
                        <SelectItem value="infographic">Infographic</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Suggestions List */}
                  <div className="space-y-3">
                    {filteredSuggestions.map((suggestion) => (
                      <div
                        key={suggestion.suggestion_id}
                        className={`border rounded-lg p-4 transition-all ${
                          selectedSuggestions.has(suggestion.suggestion_id)
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3 flex-1">
                            <div className="flex-shrink-0">
                              <input
                                type="checkbox"
                                checked={selectedSuggestions.has(suggestion.suggestion_id)}
                                onChange={() => toggleSuggestion(suggestion.suggestion_id)}
                                className="mt-1"
                              />
                            </div>
                            
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                {getContentTypeIcon(suggestion.content_type)}
                                <Badge className={getPriorityColor(suggestion.priority)}>
                                  {suggestion.priority}
                                </Badge>
                                <span className="text-sm text-gray-500">
                                  {formatTime(suggestion.timestamp_start)} - {formatTime(suggestion.timestamp_end)}
                                </span>
                                <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                                  {suggestion.duration.toFixed(1)}s
                                </span>
                              </div>
                              
                              <h4 className="font-medium mb-1">{suggestion.description}</h4>
                              <p className="text-sm text-gray-600 mb-2">{suggestion.rationale}</p>
                              
                              <div className="flex items-center space-x-2 mb-2">
                                <span className="text-xs font-medium">Keywords:</span>
                                {suggestion.keywords.map((keyword, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs">
                                    {keyword}
                                  </Badge>
                                ))}
                              </div>
                              
                              <div className="flex items-center space-x-4 text-xs text-gray-500">
                                <span>Confidence: {(suggestion.confidence * 100).toFixed(0)}%</span>
                                {suggestion.mood && <span>Mood: {suggestion.mood}</span>}
                                {suggestion.transition_type && <span>Transition: {suggestion.transition_type}</span>}
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => searchStockLibraries(suggestion)}
                            >
                              <Search className="h-3 w-3 mr-1" />
                              Search
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setPreviewSuggestion(suggestion)}
                            >
                              <Eye className="h-3 w-3 mr-1" />
                              Preview
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="timeline" className="space-y-4">
                  <div className="relative">
                    <div className="bg-gray-100 h-16 rounded-lg relative overflow-hidden">
                      {analysisResult.timeline.map((item, idx) => (
                        <div
                          key={idx}
                          className={`absolute top-2 h-12 rounded ${
                            item.priority === 'critical' ? 'bg-red-400' :
                            item.priority === 'high' ? 'bg-orange-400' :
                            item.priority === 'medium' ? 'bg-yellow-400' :
                            'bg-gray-400'
                          }`}
                          style={{
                            left: `${(item.start / (analysisResult.summary?.key_moments?.[0]?.timestamp || 100)) * 100}%`,
                            width: `${((item.end - item.start) / (analysisResult.summary?.key_moments?.[0]?.timestamp || 100)) * 100}%`,
                          }}
                          title={`${item.label} (${item.type})`}
                        />
                      ))}
                    </div>
                    <div className="flex justify-between text-xs text-gray-500 mt-2">
                      <span>0:00</span>
                      <span>Timeline</span>
                      <span>{formatTime(analysisResult.timeline[analysisResult.timeline.length - 1]?.end || 0)}</span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-red-600">
                        {analysisResult.summary.priority_breakdown.critical || 0}
                      </div>
                      <div className="text-sm text-gray-600">Critical</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">
                        {analysisResult.summary.priority_breakdown.high || 0}
                      </div>
                      <div className="text-sm text-gray-600">High</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-yellow-600">
                        {analysisResult.summary.priority_breakdown.medium || 0}
                      </div>
                      <div className="text-sm text-gray-600">Medium</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-gray-600">
                        {analysisResult.summary.priority_breakdown.low || 0}
                      </div>
                      <div className="text-sm text-gray-600">Low</div>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="summary" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <TrendingUp className="h-5 w-5 text-blue-600" />
                        <span className="font-medium">Enhancement Score</span>
                      </div>
                      <div className="text-3xl font-bold text-blue-600">
                        {analysisResult.summary.estimated_enhancement_score.toFixed(0)}%
                      </div>
                    </div>
                    
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <Clock className="h-5 w-5 text-green-600" />
                        <span className="font-medium">Coverage</span>
                      </div>
                      <div className="text-3xl font-bold text-green-600">
                        {analysisResult.summary.coverage_percentage.toFixed(0)}%
                      </div>
                    </div>
                    
                    {analysisResult.estimated_cost && (
                      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <div className="flex items-center space-x-2 mb-2">
                          <DollarSign className="h-5 w-5 text-yellow-600" />
                          <span className="font-medium">Estimated Cost</span>
                        </div>
                        <div className="text-3xl font-bold text-yellow-600">
                          ${analysisResult.estimated_cost.total}
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <h3 className="font-semibold mb-3">Key Moments</h3>
                    <div className="space-y-2">
                      {analysisResult.summary.key_moments.map((moment, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <div className="font-medium">{moment.description}</div>
                            <div className="text-sm text-gray-600">
                              {formatTime(moment.timestamp)} • {moment.duration}s • {moment.type}
                            </div>
                          </div>
                          <ChevronRight className="h-4 w-4 text-gray-400" />
                        </div>
                      ))}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="shopping" className="space-y-4">
                  <div className="text-center py-8">
                    <ShoppingCart className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <h3 className="text-lg font-medium mb-2">Generate Shopping List</h3>
                    <p className="text-gray-600 mb-4">
                      Select suggestions and generate a shopping list with cost estimates
                    </p>
                    <Button onClick={generateShoppingList} disabled={selectedSuggestions.size === 0}>
                      <ShoppingCart className="h-4 w-4 mr-2" />
                      Generate List ({selectedSuggestions.size} items)
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Preview Modal */}
      {previewSuggestion && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">B-Roll Preview</h3>
              <Button variant="outline" size="sm" onClick={() => setPreviewSuggestion(null)}>
                ×
              </Button>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium">{previewSuggestion.description}</h4>
                <p className="text-sm text-gray-600">{previewSuggestion.rationale}</p>
              </div>
              <div>
                <strong>Search Query:</strong> "{previewSuggestion.search_query}"
              </div>
              <div>
                <strong>Keywords:</strong> {previewSuggestion.keywords.join(', ')}
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setPreviewSuggestion(null)}>
                  Close
                </Button>
                <Button onClick={() => searchStockLibraries(previewSuggestion)}>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Search Stock
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartBRollSuggestions;