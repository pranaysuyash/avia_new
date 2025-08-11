import React, { useState, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { Separator } from '../ui/separator';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';
import {
  Upload,
  FileText,
  Download,
  Scan,
  Eye,
  Table,
  Image as ImageIcon,
  Type,
  Grid,
  FileSearch,
  Languages,
  Brain,
  Sparkles,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  BarChart,
  PieChart,
  Hash,
  User,
  Calendar,
  MapPin,
  DollarSign,
  Mail,
  Phone,
  Link,
  ChevronRight
} from 'lucide-react';

interface DocumentMetadata {
  type: string;
  pages: number;
  language: string;
  confidence: number;
  processing_time: number;
}

interface ExtractedEntity {
  type: string;
  value: string;
  confidence: number;
  page?: number;
  bbox?: [number, number, number, number];
}

interface LayoutElement {
  type: string;
  content: string;
  confidence: number;
  bbox: [number, number, number, number];
  page: number;
}

interface TableData {
  headers: string[];
  rows: string[][];
  confidence: number;
  page: number;
}

interface AnalysisResult {
  document_id: string;
  metadata: DocumentMetadata;
  text_content: string;
  entities: ExtractedEntity[];
  layout_elements: LayoutElement[];
  tables: TableData[];
  summary?: string;
  key_phrases?: string[];
  sentiment?: {
    overall: string;
    score: number;
  };
}

interface AnalysisSettings {
  enable_ocr: boolean;
  enable_nlp: boolean;
  enable_entity_extraction: boolean;
  enable_summarization: boolean;
  enable_sentiment_analysis: boolean;
  enable_key_phrases: boolean;
  enable_language_detection: boolean;
  enable_table_extraction: boolean;
  enable_form_extraction: boolean;
  enable_layout_analysis: boolean;
  max_pages?: number;
  languages: string[];
}

const EnhancedDocumentAnalysis: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [settings, setSettings] = useState<AnalysisSettings>({
    enable_ocr: true,
    enable_nlp: true,
    enable_entity_extraction: true,
    enable_summarization: true,
    enable_sentiment_analysis: true,
    enable_key_phrases: true,
    enable_language_detection: true,
    enable_table_extraction: true,
    enable_form_extraction: true,
    enable_layout_analysis: true,
    languages: ['en'],
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
      setAnalysisResult(null);
      
      // Create preview for images/PDFs
      if (file.type.startsWith('image/') || file.type === 'application/pdf') {
        const reader = new FileReader();
        reader.onload = (e) => {
          setPreviewUrl(e.target?.result as string);
        };
        reader.readAsDataURL(file);
      }
    }
  };

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  }, []);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  }, []);

  const analyzeDocument = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('settings', JSON.stringify(settings));

      const response = await fetch('/api/v1/document-analysis/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Document analysis failed');
      }

      const result = await response.json();
      setAnalysisResult(result.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze document');
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadResults = () => {
    if (!analysisResult) return;

    const blob = new Blob([JSON.stringify(analysisResult, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis_${analysisResult.document_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportAsCSV = (data: TableData) => {
    const csv = [
      data.headers.join(','),
      ...data.rows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `table_export_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getEntityIcon = (type: string) => {
    const iconMap: { [key: string]: React.ReactNode } = {
      'PERSON': <User className="h-4 w-4" />,
      'DATE': <Calendar className="h-4 w-4" />,
      'LOCATION': <MapPin className="h-4 w-4" />,
      'MONEY': <DollarSign className="h-4 w-4" />,
      'EMAIL': <Mail className="h-4 w-4" />,
      'PHONE': <Phone className="h-4 w-4" />,
      'URL': <Link className="h-4 w-4" />,
      'NUMBER': <Hash className="h-4 w-4" />,
    };
    return iconMap[type] || <FileText className="h-4 w-4" />;
  };

  const getLayoutColor = (type: string) => {
    const colorMap: { [key: string]: string } = {
      'title': 'bg-purple-100 text-purple-800',
      'header': 'bg-blue-100 text-blue-800',
      'paragraph': 'bg-gray-100 text-gray-800',
      'table': 'bg-green-100 text-green-800',
      'figure': 'bg-yellow-100 text-yellow-800',
      'list': 'bg-indigo-100 text-indigo-800',
    };
    return colorMap[type.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center space-x-2">
        <FileSearch className="h-6 w-6 text-blue-600" />
        <h1 className="text-2xl font-bold">Document Analysis & Intelligence</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Brain className="h-5 w-5" />
              <span>Analysis Settings</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* File Upload */}
            <div
              className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary transition-colors"
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.doc,.docx"
                onChange={handleFileSelect}
                className="hidden"
              />
              <Upload className="h-8 w-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm text-gray-600">
                {selectedFile ? selectedFile.name : 'Drop document or click to browse'}
              </p>
              {selectedFile && (
                <div className="mt-2 space-y-1">
                  <Badge variant="secondary">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </Badge>
                  <Badge variant="secondary">
                    {selectedFile.type || 'Unknown type'}
                  </Badge>
                </div>
              )}
            </div>

            <Separator />

            {/* Analysis Options */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold">Analysis Features</h3>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="ocr" className="text-sm">OCR Text Extraction</Label>
                  <Switch
                    id="ocr"
                    checked={settings.enable_ocr}
                    onCheckedChange={(checked) =>
                      setSettings(prev => ({ ...prev, enable_ocr: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="entities" className="text-sm">Entity Recognition</Label>
                  <Switch
                    id="entities"
                    checked={settings.enable_entity_extraction}
                    onCheckedChange={(checked) =>
                      setSettings(prev => ({ ...prev, enable_entity_extraction: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="tables" className="text-sm">Table Extraction</Label>
                  <Switch
                    id="tables"
                    checked={settings.enable_table_extraction}
                    onCheckedChange={(checked) =>
                      setSettings(prev => ({ ...prev, enable_table_extraction: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="layout" className="text-sm">Layout Analysis</Label>
                  <Switch
                    id="layout"
                    checked={settings.enable_layout_analysis}
                    onCheckedChange={(checked) =>
                      setSettings(prev => ({ ...prev, enable_layout_analysis: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="summary" className="text-sm">Summarization</Label>
                  <Switch
                    id="summary"
                    checked={settings.enable_summarization}
                    onCheckedChange={(checked) =>
                      setSettings(prev => ({ ...prev, enable_summarization: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="sentiment" className="text-sm">Sentiment Analysis</Label>
                  <Switch
                    id="sentiment"
                    checked={settings.enable_sentiment_analysis}
                    onCheckedChange={(checked) =>
                      setSettings(prev => ({ ...prev, enable_sentiment_analysis: checked }))
                    }
                  />
                </div>
              </div>
            </div>

            <Separator />

            {/* Action Buttons */}
            <div className="space-y-2">
              <Button
                onClick={analyzeDocument}
                className="w-full"
                disabled={!selectedFile || isProcessing}
              >
                {isProcessing ? (
                  <>
                    <Clock className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Scan className="h-4 w-4 mr-2" />
                    Analyze Document
                  </>
                )}
              </Button>

              {analysisResult && (
                <Button onClick={downloadResults} variant="outline" className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Download Results
                </Button>
              )}
            </div>

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
                <Sparkles className="h-5 w-5" />
                <span>Analysis Results</span>
              </div>
              {analysisResult && (
                <Badge variant="success" className="flex items-center space-x-1">
                  <CheckCircle className="h-3 w-3" />
                  <span>Complete</span>
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!analysisResult ? (
              <div className="text-center py-12 text-gray-500">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Upload and analyze a document to see results</p>
              </div>
            ) : (
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="entities">Entities</TabsTrigger>
                  <TabsTrigger value="layout">Layout</TabsTrigger>
                  <TabsTrigger value="tables">Tables</TabsTrigger>
                  <TabsTrigger value="insights">Insights</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-gray-600">Document Type</p>
                      <p className="text-lg font-semibold capitalize">
                        {analysisResult.metadata.type}
                      </p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-gray-600">Pages</p>
                      <p className="text-lg font-semibold">
                        {analysisResult.metadata.pages}
                      </p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-gray-600">Language</p>
                      <p className="text-lg font-semibold uppercase">
                        {analysisResult.metadata.language}
                      </p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-gray-600">Confidence</p>
                      <p className="text-lg font-semibold">
                        {(analysisResult.metadata.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  {analysisResult.summary && (
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <h3 className="font-semibold mb-2">Summary</h3>
                      <p className="text-sm text-gray-700">{analysisResult.summary}</p>
                    </div>
                  )}

                  {analysisResult.key_phrases && analysisResult.key_phrases.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-2">Key Phrases</h3>
                      <div className="flex flex-wrap gap-2">
                        {analysisResult.key_phrases.map((phrase, idx) => (
                          <Badge key={idx} variant="secondary">
                            {phrase}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {analysisResult.sentiment && (
                    <div className="p-4 border rounded-lg">
                      <h3 className="font-semibold mb-2">Sentiment Analysis</h3>
                      <div className="flex items-center space-x-4">
                        <Badge
                          variant={
                            analysisResult.sentiment.overall === 'positive'
                              ? 'success'
                              : analysisResult.sentiment.overall === 'negative'
                              ? 'destructive'
                              : 'secondary'
                          }
                        >
                          {analysisResult.sentiment.overall}
                        </Badge>
                        <Progress
                          value={analysisResult.sentiment.score * 100}
                          className="flex-1"
                        />
                        <span className="text-sm font-medium">
                          {(analysisResult.sentiment.score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="entities" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(
                      analysisResult.entities.reduce((acc, entity) => {
                        if (!acc[entity.type]) acc[entity.type] = [];
                        acc[entity.type].push(entity);
                        return acc;
                      }, {} as Record<string, ExtractedEntity[]>)
                    ).map(([type, entities]) => (
                      <div key={type} className="border rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-3">
                          {getEntityIcon(type)}
                          <h3 className="font-semibold">{type}</h3>
                          <Badge variant="secondary" className="ml-auto">
                            {entities.length}
                          </Badge>
                        </div>
                        <div className="space-y-1">
                          {entities.slice(0, 5).map((entity, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between text-sm"
                            >
                              <span className="truncate">{entity.value}</span>
                              <span className="text-gray-500">
                                {(entity.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          ))}
                          {entities.length > 5 && (
                            <p className="text-xs text-gray-500 mt-2">
                              +{entities.length - 5} more
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="layout" className="space-y-4">
                  <div className="space-y-2">
                    {analysisResult.layout_elements.map((element, idx) => (
                      <div
                        key={idx}
                        className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-gray-50"
                      >
                        <Badge className={getLayoutColor(element.type)}>
                          {element.type}
                        </Badge>
                        <div className="flex-1">
                          <p className="text-sm text-gray-700 line-clamp-2">
                            {element.content}
                          </p>
                          <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                            <span>Page {element.page}</span>
                            <span>Confidence: {(element.confidence * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="tables" className="space-y-4">
                  {analysisResult.tables.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Table className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>No tables detected in document</p>
                    </div>
                  ) : (
                    analysisResult.tables.map((table, idx) => (
                      <div key={idx} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="font-semibold">Table {idx + 1}</h3>
                          <div className="flex items-center space-x-2">
                            <Badge variant="secondary">Page {table.page}</Badge>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => exportAsCSV(table)}
                            >
                              <Download className="h-3 w-3 mr-1" />
                              CSV
                            </Button>
                          </div>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                {table.headers.map((header, i) => (
                                  <th
                                    key={i}
                                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                                  >
                                    {header}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {table.rows.slice(0, 5).map((row, i) => (
                                <tr key={i}>
                                  {row.map((cell, j) => (
                                    <td key={j} className="px-3 py-2 text-sm text-gray-900">
                                      {cell}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        {table.rows.length > 5 && (
                          <p className="text-xs text-gray-500 mt-2">
                            Showing 5 of {table.rows.length} rows
                          </p>
                        )}
                      </div>
                    ))
                  )}
                </TabsContent>

                <TabsContent value="insights" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Entity Distribution</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {Object.entries(
                            analysisResult.entities.reduce((acc, e) => {
                              acc[e.type] = (acc[e.type] || 0) + 1;
                              return acc;
                            }, {} as Record<string, number>)
                          ).map(([type, count]) => (
                            <div key={type} className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                {getEntityIcon(type)}
                                <span className="text-sm">{type}</span>
                              </div>
                              <Badge>{count}</Badge>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Processing Metrics</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Processing Time</span>
                            <span className="font-medium">
                              {analysisResult.metadata.processing_time.toFixed(2)}s
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Extracted Text</span>
                            <span className="font-medium">
                              {analysisResult.text_content.length} chars
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Layout Elements</span>
                            <span className="font-medium">
                              {analysisResult.layout_elements.length}
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Tables Found</span>
                            <span className="font-medium">{analysisResult.tables.length}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {previewUrl && selectedFile?.type.startsWith('image/') && (
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Document Preview</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <img
                          src={previewUrl}
                          alt="Document preview"
                          className="max-w-full rounded-lg"
                        />
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>
              </Tabs>
            )}

            {isProcessing && (
              <div className="space-y-4">
                <Progress value={33} className="w-full" />
                <p className="text-center text-sm text-gray-600">
                  Analyzing document structure and content...
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EnhancedDocumentAnalysis;