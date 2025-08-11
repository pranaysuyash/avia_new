import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Separator } from '../ui/separator';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Upload, 
  Play, 
  Pause,
  Clock,
  Bookmark,
  Search,
  Download,
  RefreshCw,
  Target,
  Navigation,
  Timer,
  Zap
} from 'lucide-react';

interface WordTimestamp {
  word: string;
  start_time: number;
  end_time: number;
  confidence: number;
  speaker_id?: string;
  segment_id?: string;
  duration: number;
}

interface SegmentTimestamp {
  id: string;
  start_time: number;
  end_time: number;
  segment_type: string;
  content: string;
  speaker_id?: string;
  topic?: string;
  confidence: number;
  metadata: Record<string, any>;
  duration: number;
}

interface BookmarkData {
  id: string;
  timestamp: number;
  title: string;
  description?: string;
  category: string;
  importance: number;
  created_at: string;
  metadata: Record<string, any>;
}in
terface TimestampingResult {
  word_timestamps: WordTimestamp[];
  segment_timestamps: SegmentTimestamp[];
  bookmarks: BookmarkData[];
  total_duration: number;
  total_words: number;
  total_segments: number;
  average_confidence: number;
  processing_time: number;
  config_used: any;
  metadata: Record<string, any>;
}

interface TimestampingConfig {
  precision_level: string;
  timestamp_format: string;
  include_confidence: boolean;
  enable_speaker_timestamps: boolean;
  enable_word_timestamps: boolean;
  enable_segment_timestamps: boolean;
  min_word_confidence: number;
  alignment_method: string;
  audio_sample_rate: number;
  enable_silence_detection: boolean;
  silence_threshold: number;
}

const AdvancedTimestamping: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [transcriptText, setTranscriptText] = useState('');
  const [result, setResult] = useState<TimestampingResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Configuration state
  const [config, setConfig] = useState<TimestampingConfig>({
    precision_level: 'word',
    timestamp_format: 'seconds',
    include_confidence: true,
    enable_speaker_timestamps: true,
    enable_word_timestamps: true,
    enable_segment_timestamps: true,
    min_word_confidence: 0.5,
    alignment_method: 'forced',
    audio_sample_rate: 16000,
    enable_silence_detection: true,
    silence_threshold: 0.01
  });
  
  // Audio playback
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Bookmarks
  const [bookmarks, setBookmarks] = useState<BookmarkData[]>([]);
  const [newBookmark, setNewBookmark] = useState({
    title: '',
    description: '',
    category: 'general',
    importance: 1
  });
  
  // Search and navigation
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedWord, setSelectedWord] = useState<WordTimestamp | null>(null);

  // Audio playback time update
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration);

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', () => setIsPlaying(false));

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', () => setIsPlaying(false));
    };
  }, [selectedFile]); 
 const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setResult(null);
      setError(null);
      setSessionId(null);
      setBookmarks([]);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select an audio file');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('audio_file', selectedFile);

      const requestBody = {
        config: config,
        transcript_text: transcriptText || null,
        include_bookmarks: true
      };

      formData.append('request', JSON.stringify(requestBody));

      const response = await fetch('/api/v1/advanced-timestamping/analyze', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze timestamps');
      }

      const data = await response.json();
      setResult(data.data);
      setBookmarks(data.data.bookmarks || []);
      
      // Generate session ID for bookmark management
      setSessionId(`session_${Date.now()}`);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const togglePlayback = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const seekToTime = (time: number) => {
    const audio = audioRef.current;
    if (audio) {
      audio.currentTime = time;
      setCurrentTime(time);
    }
  };

  const createBookmark = async () => {
    if (!sessionId || !newBookmark.title.trim()) return;

    try {
      const response = await fetch('/api/v1/advanced-timestamping/bookmarks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...newBookmark,
          timestamp: currentTime
        }),
        params: { session_id: sessionId }
      });

      if (response.ok) {
        const data = await response.json();
        setBookmarks(prev => [...prev, data.data]);
        setNewBookmark({
          title: '',
          description: '',
          category: 'general',
          importance: 1
        });
      }
    } catch (error) {
      console.error('Failed to create bookmark:', error);
    }
  };

  const searchTimestamps = () => {
    if (!result || !searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    const results = result.word_timestamps.filter(word =>
      word.word.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setSearchResults(results);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
  };

  const exportTimestamps = async (format: string) => {
    if (!sessionId) return;

    try {
      const response = await fetch(
        `/api/v1/advanced-timestamping/export/${sessionId}?format=${format}&include_bookmarks=true`
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `timestamps_${sessionId}.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to export timestamps:', error);
    }
  };  const 
renderWordTimeline = () => {
    if (!result) return null;

    const totalWidth = 800;
    const wordsPerPixel = result.word_timestamps.length / totalWidth;

    return (
      <div className="relative">
        <div className="flex h-12 bg-gray-100 rounded-lg overflow-hidden">
          {result.word_timestamps.map((word, index) => {
            const width = Math.max(1, totalWidth / result.word_timestamps.length);
            const opacity = word.confidence;
            const isSelected = selectedWord?.word === word.word && selectedWord?.start_time === word.start_time;
            
            return (
              <div
                key={index}
                className={`flex-shrink-0 cursor-pointer hover:bg-blue-300 transition-colors ${
                  isSelected ? 'bg-blue-500' : 'bg-blue-200'
                }`}
                style={{
                  width: `${width}px`,
                  opacity: opacity,
                  height: '100%'
                }}
                onClick={() => {
                  seekToTime(word.start_time);
                  setSelectedWord(word);
                }}
                title={`${word.word} (${formatTime(word.start_time)} - ${formatTime(word.end_time)})`}
              />
            );
          })}
        </div>
        
        {/* Playback position indicator */}
        {duration > 0 && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-red-500 pointer-events-none"
            style={{
              left: `${(currentTime / duration) * totalWidth}px`
            }}
          />
        )}
      </div>
    );
  };

  const renderTranscriptWithTimestamps = () => {
    if (!result) return null;

    return (
      <div className="max-h-64 overflow-y-auto p-4 bg-gray-50 rounded-lg">
        <div className="space-y-2">
          {result.segment_timestamps.map((segment, index) => (
            <div key={index} className="border-l-4 border-blue-500 pl-4">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-2">
                  {segment.speaker_id && (
                    <Badge variant="secondary">{segment.speaker_id}</Badge>
                  )}
                  <span className="text-xs text-gray-500">
                    {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => seekToTime(segment.start_time)}
                >
                  <Play className="h-3 w-3" />
                </Button>
              </div>
              <p className="text-sm leading-relaxed">
                {segment.content.split(' ').map((word, wordIndex) => {
                  const wordTimestamp = result.word_timestamps.find(wt => 
                    wt.word.toLowerCase() === word.toLowerCase() &&
                    wt.start_time >= segment.start_time &&
                    wt.end_time <= segment.end_time
                  );
                  
                  return (
                    <span
                      key={wordIndex}
                      className={`cursor-pointer hover:bg-yellow-200 ${
                        selectedWord === wordTimestamp ? 'bg-yellow-300' : ''
                      }`}
                      onClick={() => {
                        if (wordTimestamp) {
                          seekToTime(wordTimestamp.start_time);
                          setSelectedWord(wordTimestamp);
                        }
                      }}
                      title={wordTimestamp ? `${formatTime(wordTimestamp.start_time)} - ${formatTime(wordTimestamp.end_time)}` : ''}
                    >
                      {word}{' '}
                    </span>
                  );
                })}
              </p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderBookmarks = () => {
    return (
      <div className="space-y-4">
        {/* Create Bookmark */}
        <div className="p-4 border rounded-lg">
          <h4 className="font-medium mb-3">Create Bookmark</h4>
          <div className="space-y-3">
            <div>
              <Label htmlFor="bookmark-title">Title</Label>
              <Input
                id="bookmark-title"
                value={newBookmark.title}
                onChange={(e) => setNewBookmark(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Bookmark title"
              />
            </div>
            <div>
              <Label htmlFor="bookmark-description">Description</Label>
              <Input
                id="bookmark-description"
                value={newBookmark.description}
                onChange={(e) => setNewBookmark(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Optional description"
              />
            </div>
            <div className="flex items-center space-x-4">
              <div>
                <Label htmlFor="bookmark-category">Category</Label>
                <Select 
                  value={newBookmark.category} 
                  onValueChange={(value) => setNewBookmark(prev => ({ ...prev, category: value }))}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General</SelectItem>
                    <SelectItem value="important">Important</SelectItem>
                    <SelectItem value="question">Question</SelectItem>
                    <SelectItem value="action">Action</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="bookmark-importance">Importance</Label>
                <Select 
                  value={newBookmark.importance.toString()} 
                  onValueChange={(value) => setNewBookmark(prev => ({ ...prev, importance: parseInt(value) }))}
                >
                  <SelectTrigger className="w-20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1</SelectItem>
                    <SelectItem value="2">2</SelectItem>
                    <SelectItem value="3">3</SelectItem>
                    <SelectItem value="4">4</SelectItem>
                    <SelectItem value="5">5</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button onClick={createBookmark} disabled={!newBookmark.title.trim()}>
              <Bookmark className="h-4 w-4 mr-2" />
              Create at {formatTime(currentTime)}
            </Button>
          </div>
        </div>

        {/* Bookmarks List */}
        <div className="space-y-2">
          <h4 className="font-medium">Bookmarks ({bookmarks.length})</h4>
          {bookmarks.map((bookmark) => (
            <div key={bookmark.id} className="p-3 border rounded-lg hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Bookmark className="h-4 w-4 text-blue-600" />
                  <span className="font-medium">{bookmark.title}</span>
                  <Badge variant="outline">{bookmark.category}</Badge>
                  <div className="flex">
                    {Array.from({ length: bookmark.importance }).map((_, i) => (
                      <span key={i} className="text-yellow-400">★</span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">{formatTime(bookmark.timestamp)}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => seekToTime(bookmark.timestamp)}
                  >
                    <Navigation className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              {bookmark.description && (
                <p className="text-sm text-gray-600 mt-1">{bookmark.description}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };  r
eturn (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center space-x-2">
        <Timer className="h-6 w-6 text-purple-600" />
        <h1 className="text-2xl font-bold">Advanced Timestamping</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="h-5 w-5" />
              <span>Configuration</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* File Upload */}
            <div className="space-y-2">
              <Label>Audio File</Label>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                  className="flex-1"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  {selectedFile ? selectedFile.name : 'Select File'}
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </div>

            {/* Audio Player */}
            {selectedFile && (
              <div className="space-y-2">
                <audio
                  ref={audioRef}
                  src={URL.createObjectURL(selectedFile)}
                  className="hidden"
                />
                <div className="flex items-center space-x-2">
                  <Button
                    onClick={togglePlayback}
                    variant="outline"
                    size="sm"
                  >
                    {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                  <div className="flex-1 text-sm text-gray-500">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </div>
                </div>
                {duration > 0 && (
                  <Progress value={(currentTime / duration) * 100} className="h-2" />
                )}
              </div>
            )}

            {/* Optional Transcript */}
            <div className="space-y-2">
              <Label htmlFor="transcript">Transcript (Optional)</Label>
              <textarea
                id="transcript"
                className="w-full h-24 p-2 border rounded-md text-sm"
                placeholder="Paste transcript text for better alignment..."
                value={transcriptText}
                onChange={(e) => setTranscriptText(e.target.value)}
              />
            </div>

            <Separator />

            {/* Configuration Options */}
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="basic">Basic</TabsTrigger>
                <TabsTrigger value="advanced">Advanced</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4">
                <div>
                  <Label htmlFor="precision">Precision Level</Label>
                  <Select 
                    value={config.precision_level} 
                    onValueChange={(value) => setConfig(prev => ({ ...prev, precision_level: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="word">Word Level</SelectItem>
                      <SelectItem value="phrase">Phrase Level</SelectItem>
                      <SelectItem value="sentence">Sentence Level</SelectItem>
                      <SelectItem value="segment">Segment Level</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="format">Timestamp Format</Label>
                  <Select 
                    value={config.timestamp_format} 
                    onValueChange={(value) => setConfig(prev => ({ ...prev, timestamp_format: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="seconds">Seconds</SelectItem>
                      <SelectItem value="milliseconds">Milliseconds</SelectItem>
                      <SelectItem value="timecode">Timecode</SelectItem>
                      <SelectItem value="frames">Frames</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="alignment">Alignment Method</Label>
                  <Select 
                    value={config.alignment_method} 
                    onValueChange={(value) => setConfig(prev => ({ ...prev, alignment_method: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="forced">Forced Alignment</SelectItem>
                      <SelectItem value="vad_based">VAD-based</SelectItem>
                      <SelectItem value="energy_based">Energy-based</SelectItem>
                      <SelectItem value="hybrid">Hybrid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>

              <TabsContent value="advanced" className="space-y-4">
                <div>
                  <Label htmlFor="confidence">Min Word Confidence</Label>
                  <Input
                    id="confidence"
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.min_word_confidence}
                    onChange={(e) => setConfig(prev => ({ ...prev, min_word_confidence: parseFloat(e.target.value) }))}
                  />
                </div>

                <div>
                  <Label htmlFor="sample-rate">Sample Rate (Hz)</Label>
                  <Select 
                    value={config.audio_sample_rate.toString()} 
                    onValueChange={(value) => setConfig(prev => ({ ...prev, audio_sample_rate: parseInt(value) }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="8000">8000 Hz</SelectItem>
                      <SelectItem value="16000">16000 Hz</SelectItem>
                      <SelectItem value="32000">32000 Hz</SelectItem>
                      <SelectItem value="48000">48000 Hz</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="word-timestamps"
                      checked={config.enable_word_timestamps}
                      onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enable_word_timestamps: checked }))}
                    />
                    <Label htmlFor="word-timestamps">Word Timestamps</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="speaker-timestamps"
                      checked={config.enable_speaker_timestamps}
                      onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enable_speaker_timestamps: checked }))}
                    />
                    <Label htmlFor="speaker-timestamps">Speaker Timestamps</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="silence-detection"
                      checked={config.enable_silence_detection}
                      onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enable_silence_detection: checked }))}
                    />
                    <Label htmlFor="silence-detection">Silence Detection</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="confidence-scores"
                      checked={config.include_confidence}
                      onCheckedChange={(checked) => setConfig(prev => ({ ...prev, include_confidence: checked }))}
                    />
                    <Label htmlFor="confidence-scores">Include Confidence</Label>
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <Separator />

            {/* Action Buttons */}
            <div className="space-y-2">
              <Button 
                onClick={handleAnalyze} 
                disabled={!selectedFile || isAnalyzing}
                className="w-full"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Generate Timestamps
                  </>
                )}
              </Button>

              {result && (
                <div className="flex space-x-2">
                  <Button onClick={() => exportTimestamps('json')} variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-1" />
                    JSON
                  </Button>
                  <Button onClick={() => exportTimestamps('srt')} variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-1" />
                    SRT
                  </Button>
                  <Button onClick={() => exportTimestamps('vtt')} variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-1" />
                    VTT
                  </Button>
                </div>
              )}
            </div>

            {error && (
              <Alert variant="destructive">
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
                <Target className="h-5 w-5" />
                <span>Timestamping Results</span>
              </div>
              {result && (
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>{result.total_words} words</span>
                  <span>{result.total_segments} segments</span>
                  <span>{(result.average_confidence * 100).toFixed(1)}% avg confidence</span>
                </div>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {result ? (
              <Tabs defaultValue="timeline" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="timeline">Timeline</TabsTrigger>
                  <TabsTrigger value="transcript">Transcript</TabsTrigger>
                  <TabsTrigger value="bookmarks">Bookmarks</TabsTrigger>
                  <TabsTrigger value="search">Search</TabsTrigger>
                </TabsList>

                <TabsContent value="timeline" className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-3">Word Timeline</h3>
                    {renderWordTimeline()}
                    <div className="flex items-center space-x-4 text-xs text-gray-500 mt-2">
                      <div className="flex items-center space-x-1">
                        <div className="w-3 h-3 bg-blue-200 rounded"></div>
                        <span>Words</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <div className="w-3 h-3 bg-blue-500 rounded"></div>
                        <span>Selected</span>
                      </div>
                      <span>Click words to navigate</span>
                    </div>
                  </div>

                  {selectedWord && (
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <h4 className="font-medium mb-2">Selected Word</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <strong>Word:</strong> {selectedWord.word}
                        </div>
                        <div>
                          <strong>Confidence:</strong> {(selectedWord.confidence * 100).toFixed(1)}%
                        </div>
                        <div>
                          <strong>Start:</strong> {formatTime(selectedWord.start_time)}
                        </div>
                        <div>
                          <strong>End:</strong> {formatTime(selectedWord.end_time)}
                        </div>
                        <div>
                          <strong>Duration:</strong> {(selectedWord.duration * 1000).toFixed(0)}ms
                        </div>
                        {selectedWord.speaker_id && (
                          <div>
                            <strong>Speaker:</strong> {selectedWord.speaker_id}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="transcript" className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-3">Interactive Transcript</h3>
                    {renderTranscriptWithTimestamps()}
                  </div>
                </TabsContent>

                <TabsContent value="bookmarks" className="space-y-4">
                  {renderBookmarks()}
                </TabsContent>

                <TabsContent value="search" className="space-y-4">
                  <div className="flex space-x-2">
                    <Input
                      placeholder="Search words in transcript..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && searchTimestamps()}
                    />
                    <Button onClick={searchTimestamps}>
                      <Search className="h-4 w-4" />
                    </Button>
                  </div>

                  {searchResults.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium">Search Results ({searchResults.length})</h4>
                      {searchResults.map((word, index) => (
                        <div
                          key={index}
                          className="p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                          onClick={() => {
                            seekToTime(word.start_time);
                            setSelectedWord(word);
                          }}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{word.word}</span>
                            <span className="text-sm text-gray-500">
                              {formatTime(word.start_time)} - {formatTime(word.end_time)}
                            </span>
                          </div>
                          <div className="text-xs text-gray-400">
                            Confidence: {(word.confidence * 100).toFixed(1)}%
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Timer className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Upload an audio file and click "Generate Timestamps" to see results</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdvancedTimestamping;