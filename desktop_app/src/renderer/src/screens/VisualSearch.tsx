import React, { useState, useEffect, useRef } from 'react';
import { logUxEvent } from '../services/uxTelemetry';
import { motion } from 'framer-motion';
import { 
  MagnifyingGlassIcon, 
  ClockIcon, 
  MapIcon, 
  SparklesIcon,
  PhotoIcon,
  FunnelIcon,
  ArrowsPointingOutIcon
} from '@heroicons/react/24/outline';

interface TimelineData {
  hour: number;
  content_density: number;
  transcription_count: number;
  dominant_topics: string[];
  avg_confidence: number;
  languages: string[];
}

interface ContentCluster {
  id: string;
  topic: string;
  center_x: number;
  center_y: number;
  size: number;
  transcription_count: number;
  avg_similarity: number;
  keywords: string[];
  color: string;
  transcriptions: Array<{
    id: string;
    title: string;
    x: number;
    y: number;
    similarity: number;
  }>;
}

interface SimilarityResult {
  transcript_id: string;
  title: string;
  similarity_score: number;
  preview: string;
  duration: number;
  topics: string[];
  matching_segments: Array<{
    start_time: number;
    end_time: number;
    text: string;
    similarity: number;
  }>;
}

interface Recommendation {
  id: string;
  transcript_id: string;
  title: string;
  type: string;
  score: number;
  reason: string;
  duration: number;
  topics: string[];
  view_count: number;
  rating: number;
}

const VisualSearch: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'timeline' | 'map' | 'similarity' | 'image' | 'recommendations'>(() => {
    try { const url = new URL(window.location.href); const t = url.searchParams.get('vs_tab'); if (t && ['timeline','map','similarity','image','recommendations'].includes(t)) return t as any; } catch {}
    return 'timeline';
  });
  const [timelineData, setTimelineData] = useState<TimelineData[]>([]);
  const [contentMap, setContentMap] = useState<ContentCluster[]>([]);
  const [similarityResults, setSimilarityResults] = useState<SimilarityResult[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [imageDescription, setImageDescription] = useState('');
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);
  const mapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  // Sync tab into URL for shareable state
  useEffect(() => {
    try { const url = new URL(window.location.href); url.searchParams.set('vs_tab', activeTab); window.history.replaceState({}, '', url.toString()); } catch {}
  }, [activeTab]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      // Load timeline
      const timelineResponse = await fetch('http://localhost:8001/api/visual-search/timeline');
      if (timelineResponse.ok) {
        const timelineResult = await timelineResponse.json();
        setTimelineData(timelineResult.data.timeline);
      }

      // Load content map
      const mapResponse = await fetch('http://localhost:8001/api/visual-search/content-map');
      if (mapResponse.ok) {
        const mapResult = await mapResponse.json();
        setContentMap(mapResult.data.clusters);
      }

      // Load recommendations
      const recResponse = await fetch('http://localhost:8001/api/visual-search/recommendations');
      if (recResponse.ok) {
        const recResult = await recResponse.json();
        setRecommendations(recResult.data.recommendations);
      }
    } catch (error) {
      console.error('Failed to load visual search data:', error);
    } finally {
      setLoading(false);
    }
  };

  const performSimilaritySearch = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/visual-search/similarity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, limit: 10 })
      });
      
      if (response.ok) {
        const result = await response.json();
        setSimilarityResults(result.data.results);
        setActiveTab('similarity');
      }
    } catch (error) {
      console.error('Similarity search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const performImageSearch = async () => {
    if (!imageDescription.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/visual-search/image-to-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_description: imageDescription, limit: 5 })
      });
      
      if (response.ok) {
        const result = await response.json();
        setSimilarityResults(result.data.results.map((item: any) => ({
          transcript_id: item.transcript_id,
          title: item.title,
          similarity_score: item.relevance_score,
          preview: item.description,
          duration: item.duration,
          topics: item.visual_concepts,
          matching_segments: []
        })));
        setActiveTab('image');
      }
    } catch (error) {
      console.error('Image search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderTimeline = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Content Density Timeline
        </h3>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <ClockIcon className="h-4 w-4" />
          <span>24-hour view</span>
        </div>
      </div>
      
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <div className="grid grid-cols-24 gap-1 h-40">
          {timelineData.map((hour) => (
            <div
              key={hour.hour}
              className="relative group cursor-pointer"
              title={`Hour ${hour.hour}: ${hour.content_density}% density, ${hour.transcription_count} transcriptions`}
            >
              <div
                className="bg-indigo-500 rounded-sm transition-opacity hover:opacity-80"
                style={{
                  height: `${hour.content_density}%`,
                  marginTop: `${100 - hour.content_density}%`
                }}
              />
              <div className="absolute bottom-0 left-0 right-0 text-xs text-center text-gray-600 dark:text-gray-300">
                {hour.hour}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
          <div className="bg-white dark:bg-gray-800 rounded p-3">
            <div className="text-gray-500 dark:text-gray-400">Peak Hour</div>
            <div className="text-xl font-semibold">
              {timelineData.length > 0 ? Math.max(...timelineData.map(h => h.content_density)) : 0}%
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded p-3">
            <div className="text-gray-500 dark:text-gray-400">Total Transcriptions</div>
            <div className="text-xl font-semibold">
              {timelineData.reduce((sum, h) => sum + h.transcription_count, 0)}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded p-3">
            <div className="text-gray-500 dark:text-gray-400">Avg Confidence</div>
            <div className="text-xl font-semibold">
              {timelineData.length > 0 ? Math.round(timelineData.reduce((sum, h) => sum + h.avg_confidence, 0) / timelineData.length * 100) : 0}%
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderContentMap = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Interactive Content Map
        </h3>
        <div className="flex items-center space-x-2">
          <button className="btn-secondary text-sm">
            <ArrowsPointingOutIcon className="h-4 w-4 mr-1" />
            Zoom
          </button>
          <button className="btn-secondary text-sm">
            <FunnelIcon className="h-4 w-4 mr-1" />
            Filter
          </button>
        </div>
      </div>
      
      <div 
        ref={mapRef}
        className="relative bg-gray-50 dark:bg-gray-700 rounded-lg h-96 overflow-hidden"
      >
        <svg width="100%" height="100%" className="absolute inset-0">
          {contentMap.map((cluster) => (
            <g key={cluster.id}>
              {/* Cluster background */}
              <circle
                cx={`${cluster.center_x}%`}
                cy={`${cluster.center_y}%`}
                r={cluster.size}
                fill={cluster.color}
                fillOpacity={selectedCluster === cluster.id ? 0.3 : 0.2}
                stroke={cluster.color}
                strokeWidth={selectedCluster === cluster.id ? 3 : 1}
                className="cursor-pointer transition-all"
                onClick={() => setSelectedCluster(
                  selectedCluster === cluster.id ? null : cluster.id
                )}
              />
              
              {/* Cluster label */}
              <text
                x={`${cluster.center_x}%`}
                y={`${cluster.center_y}%`}
                textAnchor="middle"
                className="text-sm font-medium fill-current text-gray-800 dark:text-gray-200"
                style={{ pointerEvents: 'none' }}
              >
                {cluster.topic}
              </text>
              
              {/* Individual transcriptions */}
              {selectedCluster === cluster.id && cluster.transcriptions.map((transcript) => (
                <circle
                  key={transcript.id}
                  cx={`${cluster.center_x + transcript.x}%`}
                  cy={`${cluster.center_y + transcript.y}%`}
                  r="3"
                  fill={cluster.color}
                  className="cursor-pointer hover:r-4 transition-all"
                  onClick={() => console.log(transcript.title)}
                >
                  <title>{transcript.title}</title>
                </circle>
              ))}
            </g>
          ))}
        </svg>
      </div>
      
      {selectedCluster && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          {(() => {
            const cluster = contentMap.find(c => c.id === selectedCluster);
            return cluster ? (
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                  {cluster.topic} Cluster
                </h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Transcriptions:</span>
                    <span className="ml-2 font-medium">{cluster.transcription_count}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Avg Similarity:</span>
                    <span className="ml-2 font-medium">{(cluster.avg_similarity * 100).toFixed(1)}%</span>
                  </div>
                </div>
                <div className="mt-3">
                  <span className="text-gray-500 dark:text-gray-400 text-sm">Keywords:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {cluster.keywords.map((keyword, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : null;
          })()}
        </div>
      )}
    </div>
  );

  const renderSimilaritySearch = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Visual Similarity Search
        </h3>
      </div>
      
      <div className="flex space-x-3">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Enter search query for similarity matching..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm"
          onKeyPress={(e) => e.key === 'Enter' && performSimilaritySearch()}
        />
        <button
          onClick={performSimilaritySearch}
          disabled={loading || !searchQuery.trim()}
          className="btn-primary"
        >
          <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
          Search
        </button>
      </div>
      
      {similarityResults.length > 0 && (
        <div className="space-y-4">
          {similarityResults.map((result) => (
            <div
              key={result.transcript_id}
              className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {result.title}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {result.preview}
                  </p>
                  <div className="flex items-center space-x-4 mt-3 text-xs text-gray-500">
                    <span>Duration: {Math.round(result.duration / 60)}min</span>
                    <span>Topics: {result.topics.join(', ')}</span>
                  </div>
                </div>
                <div className="text-right ml-4">
                  <div className="text-lg font-semibold text-indigo-600">
                    {(result.similarity_score * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500">similarity</div>
                </div>
              </div>
              
              {result.matching_segments.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Matching Segments:
                  </div>
                  {result.matching_segments.map((segment, index) => (
                    <div key={index} className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      <span className="font-mono text-xs">
                        {Math.round(segment.start_time)}s-{Math.round(segment.end_time)}s
                      </span>
                      : {segment.text}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderImageSearch = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Image-to-Text Search
        </h3>
      </div>
      
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <PhotoIcon className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium">Upload an image to find related audio content</p>
            <p>Our AI will analyze the image and search for transcriptions discussing similar visual concepts.</p>
          </div>
        </div>
      </div>
      
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Describe the image or visual content:
        </label>
        <textarea
          value={imageDescription}
          onChange={(e) => setImageDescription(e.target.value)}
          placeholder="e.g., 'A chart showing sales data', 'Screenshot of a dashboard', 'Diagram explaining a process'..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm h-24 resize-none"
        />
        <button
          onClick={performImageSearch}
          disabled={loading || !imageDescription.trim()}
          className="btn-primary"
        >
          <PhotoIcon className="h-4 w-4 mr-2" />
          Search Related Content
        </button>
      </div>
      
      {similarityResults.length > 0 && activeTab === 'image' && (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900 dark:text-white">
            Related Audio Content:
          </h4>
          {similarityResults.map((result) => (
            <div
              key={result.transcript_id}
              className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h5 className="font-medium text-gray-900 dark:text-white">
                    {result.title}
                  </h5>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {result.preview}
                  </p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {result.topics.map((concept, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 rounded"
                      >
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="text-right ml-4">
                  <div className="text-lg font-semibold text-purple-600">
                    {(result.similarity_score * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500">relevance</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderRecommendations = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Smart Content Recommendations
        </h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {recommendations.map((rec) => (
          <div
            key={rec.id}
            className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className={`px-2 py-1 text-xs rounded ${{
                    'trending': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200',
                    'similar_to_recent': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200',
                    'topic_based': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200',
                    'collaborative': 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-200'
                  }[rec.type] || 'bg-gray-100 text-gray-800'}`}>
                    {rec.type.replace('_', ' ')}
                  </span>
                  <div className="flex items-center">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className={`h-3 w-3 ${
                          i < Math.floor(rec.rating) ? 'text-yellow-400' : 'text-gray-300'
                        }`}
                      >
                        ★
                      </div>
                    ))}
                  </div>
                </div>
                <h4 className="font-medium text-gray-900 dark:text-white text-sm">
                  {rec.title}
                </h4>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  {rec.reason}
                </p>
                <div className="flex items-center space-x-3 mt-2 text-xs text-gray-500">
                  <span>{Math.round(rec.duration / 60)}min</span>
                  <span>{rec.view_count} views</span>
                  <span>{rec.topics.join(', ')}</span>
                </div>
              </div>
              <div className="text-right ml-3">
                <div className="text-lg font-semibold text-emerald-600">
                  {(rec.score * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">match</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  if (loading && timelineData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Visual Search & Content Discovery
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Explore and discover content through advanced visual search capabilities
          </p>
        </div>
        <button
          onClick={async () => { try { const href = window.location.href; await navigator.clipboard.writeText(href); logUxEvent('share_visual_search_view', { href }); } catch {} }}
          className="px-3 py-2 text-sm rounded-md bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
          title="Copy shareable link"
        >
          Share
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'timeline', label: 'Timeline', icon: ClockIcon },
            { id: 'map', label: 'Content Map', icon: MapIcon },
            { id: 'similarity', label: 'Similarity Search', icon: MagnifyingGlassIcon },
            { id: 'image', label: 'Image Search', icon: PhotoIcon },
            { id: 'recommendations', label: 'Recommendations', icon: SparklesIcon }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {activeTab === 'timeline' && renderTimeline()}
        {activeTab === 'map' && renderContentMap()}
        {activeTab === 'similarity' && renderSimilaritySearch()}
        {activeTab === 'image' && renderImageSearch()}
        {activeTab === 'recommendations' && renderRecommendations()}
      </div>
    </motion.div>
  );
};

export default VisualSearch;
