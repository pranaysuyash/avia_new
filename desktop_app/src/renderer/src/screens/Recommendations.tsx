import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  SparklesIcon, 
  ArrowTrendingUpIcon, 
  ChartBarIcon,
  TagIcon,
  UserCircleIcon,
  LightBulbIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon
} from '@heroicons/react/24/outline';

interface Recommendation {
  transcript_id: string;
  title: string;
  score: number;
  recommendation_type: string;
  reason: string;
  duration: number;
  topics: string[];
  language: string;
  metadata: {
    view_count: number;
    completion_rate: number;
    created_days_ago: number;
  };
}

interface TrendingTopic {
  topic: string;
  score: number;
  transcript_count: number;
  view_count: number;
  trend: string;
  trend_percentage: number;
  top_transcripts: Array<{
    id: string;
    title: string;
    views: number;
  }>;
}

interface ContentGap {
  gap_id: string;
  topics: string[];
  description: string;
  gap_score: number;
  current_count: number;
  recommended_count: number;
  potential_audience: number;
  priority: string;
  suggested_formats: string[];
}

interface SmartTag {
  tag: string;
  confidence: number;
  source: string;
  relevance_reason: string;
}

const Recommendations: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'personal' | 'trending' | 'gaps' | 'tags'>('personal');
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [trendingTopics, setTrendingTopics] = useState<TrendingTopic[]>([]);
  const [contentGaps, setContentGaps] = useState<ContentGap[]>([]);
  const [smartTags, setSmartTags] = useState<SmartTag[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTranscript, setSelectedTranscript] = useState<string | null>(null);
  const [timeWindow, setTimeWindow] = useState<'daily' | 'weekly' | 'monthly'>('daily');

  useEffect(() => {
    loadPersonalizedRecommendations();
  }, []);

  const loadPersonalizedRecommendations = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/recommendations/personalized?limit=12');
      if (response.ok) {
        const result = await response.json();
        setRecommendations(result.data.recommendations);
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTrendingTopics = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/recommendations/trending-topics?time_window=${timeWindow}&limit=10`);
      if (response.ok) {
        const result = await response.json();
        setTrendingTopics(result.data.trending_topics);
      }
    } catch (error) {
      console.error('Failed to load trending topics:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadContentGaps = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/recommendations/content-gaps?limit=8');
      if (response.ok) {
        const result = await response.json();
        setContentGaps(result.data.content_gaps);
      }
    } catch (error) {
      console.error('Failed to load content gaps:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSmartTags = async () => {
    if (!selectedTranscript) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/recommendations/smart-tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript_id: selectedTranscript })
      });
      
      if (response.ok) {
        const result = await response.json();
        setSmartTags(result.data.suggested_tags);
      }
    } catch (error) {
      console.error('Failed to load smart tags:', error);
    } finally {
      setLoading(false);
    }
  };

  const trackInteraction = async (transcriptId: string, actionType: string) => {
    try {
      await fetch('http://localhost:8000/api/recommendations/track-interaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'test_user',
          transcript_id: transcriptId,
          action_type: actionType
        })
      });
    } catch (error) {
      console.error('Failed to track interaction:', error);
    }
  };

  useEffect(() => {
    if (activeTab === 'trending') {
      loadTrendingTopics();
    } else if (activeTab === 'gaps') {
      loadContentGaps();
    } else if (activeTab === 'tags' && selectedTranscript) {
      loadSmartTags();
    }
  }, [activeTab, timeWindow, selectedTranscript]);

  const renderPersonalizedRecommendations = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Personalized For You
        </h3>
        <button 
          onClick={loadPersonalizedRecommendations}
          className="btn-secondary text-sm"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {recommendations.map((rec) => (
          <motion.div
            key={rec.transcript_id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow"
          >
            {/* Thumbnail placeholder */}
            <div className="h-40 bg-gradient-to-br from-indigo-500 to-purple-600 relative">
              <div className="absolute inset-0 bg-black bg-opacity-20 flex items-center justify-center">
                <SparklesIcon className="h-12 w-12 text-white opacity-50" />
              </div>
              <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">
                {Math.floor(rec.duration / 60)}min
              </div>
            </div>
            
            <div className="p-4">
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-medium text-gray-900 dark:text-white text-sm flex-1">
                  {rec.title}
                </h4>
                <div className="text-right ml-2">
                  <div className="text-lg font-semibold text-indigo-600">
                    {Math.round(rec.score * 100)}%
                  </div>
                  <div className="text-xs text-gray-500">match</div>
                </div>
              </div>
              
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                {rec.reason}
              </p>
              
              <div className="flex flex-wrap gap-1 mb-3">
                {rec.topics.map((topic, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded"
                  >
                    {topic}
                  </span>
                ))}
              </div>
              
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{rec.metadata.view_count.toLocaleString()} views</span>
                <span>{(rec.metadata.completion_rate * 100).toFixed(0)}% completion</span>
              </div>
              
              <div className="mt-3 flex space-x-2">
                <button 
                  onClick={() => trackInteraction(rec.transcript_id, 'view')}
                  className="flex-1 btn-primary text-xs py-1"
                >
                  View
                </button>
                <button 
                  onClick={() => trackInteraction(rec.transcript_id, 'like')}
                  className="btn-secondary text-xs py-1 px-3"
                >
                  Like
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );

  const renderTrendingTopics = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Trending Topics
        </h3>
        <div className="flex items-center space-x-3">
          <select
            value={timeWindow}
            onChange={(e) => setTimeWindow(e.target.value as any)}
            className="text-sm border border-gray-300 rounded-md px-3 py-1"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {trendingTopics.map((topic) => (
          <div
            key={topic.topic}
            className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">
                  {topic.topic}
                </h4>
                <div className="flex items-center space-x-3 mt-1 text-sm text-gray-500">
                  <span>{topic.transcript_count} transcripts</span>
                  <span>{topic.view_count.toLocaleString()} views</span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {topic.score.toFixed(0)}
                  </div>
                  <div className="text-xs text-gray-500">score</div>
                </div>
                {topic.trend === 'up' && (
                  <div className="flex items-center text-emerald-600">
                    <ArrowUpIcon className="h-4 w-4" />
                    <span className="text-sm ml-1">+{topic.trend_percentage.toFixed(0)}%</span>
                  </div>
                )}
                {topic.trend === 'down' && (
                  <div className="flex items-center text-red-600">
                    <ArrowDownIcon className="h-4 w-4" />
                    <span className="text-sm ml-1">{topic.trend_percentage.toFixed(0)}%</span>
                  </div>
                )}
                {topic.trend === 'stable' && (
                  <div className="flex items-center text-gray-500">
                    <MinusIcon className="h-4 w-4" />
                    <span className="text-sm ml-1">0%</span>
                  </div>
                )}
                {topic.trend === 'new' && (
                  <span className="px-2 py-1 text-xs bg-indigo-100 text-indigo-800 rounded">
                    NEW
                  </span>
                )}
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Top Content:
              </div>
              {topic.top_transcripts.map((transcript) => (
                <div
                  key={transcript.id}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-gray-600 dark:text-gray-400 truncate flex-1">
                    {transcript.title}
                  </span>
                  <span className="text-xs text-gray-500 ml-2">
                    {transcript.views} views
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderContentGaps = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Content Gap Analysis
        </h3>
        <div className="text-sm text-gray-500">
          Opportunities for new content
        </div>
      </div>

      <div className="space-y-4">
        {contentGaps.map((gap) => (
          <div
            key={gap.gap_id}
            className="bg-white dark:bg-gray-800 rounded-lg p-5 border border-gray-200 dark:border-gray-700"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {gap.topics.join(' × ')}
                  </h4>
                  <span className={`px-2 py-1 text-xs rounded ${
                    gap.priority === 'high' 
                      ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200'
                      : gap.priority === 'medium'
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200'
                      : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200'
                  }`}>
                    {gap.priority} priority
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {gap.description}
                </p>
                
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Current content:</span>
                    <span className="ml-2 font-medium">{gap.current_count}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Recommended:</span>
                    <span className="ml-2 font-medium">{gap.recommended_count}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Potential audience:</span>
                    <span className="ml-2 font-medium">{gap.potential_audience.toLocaleString()}</span>
                  </div>
                </div>
                
                <div className="mt-3 flex items-center space-x-4">
                  <span className="text-sm text-gray-500">Suggested formats:</span>
                  <div className="flex space-x-2">
                    {gap.suggested_formats.map((format, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-200 rounded"
                      >
                        {format}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="text-right ml-4">
                <div className="text-3xl font-bold text-indigo-600">
                  {gap.gap_score.toFixed(0)}
                </div>
                <div className="text-xs text-gray-500">gap score</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderSmartTags = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Smart Tag Suggestions
        </h3>
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <TagIcon className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium">Select a transcript to get smart tag suggestions</p>
            <p>AI will analyze content and suggest relevant tags based on similar content and trends.</p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Select Transcript:
        </label>
        <select
          value={selectedTranscript || ''}
          onChange={(e) => setSelectedTranscript(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
        >
          <option value="">Choose a transcript...</option>
          {recommendations.map((rec) => (
            <option key={rec.transcript_id} value={rec.transcript_id}>
              {rec.title}
            </option>
          ))}
        </select>
      </div>

      {selectedTranscript && smartTags.length > 0 && (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900 dark:text-white">
            Suggested Tags:
          </h4>
          
          <div className="space-y-3">
            {smartTags.map((tag, index) => (
              <div
                key={index}
                className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-center space-x-3">
                  <div className="flex items-center justify-center h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30">
                    <TagIcon className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {tag.tag}
                    </div>
                    <div className="text-xs text-gray-500">
                      {tag.relevance_reason}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <div className="text-lg font-semibold text-indigo-600">
                      {(tag.confidence * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500">confidence</div>
                  </div>
                  <button className="btn-primary text-xs py-1 px-3">
                    Add Tag
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  if (loading && recommendations.length === 0) {
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
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Smart Content Recommendations
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Personalized content discovery powered by AI
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'personal', label: 'For You', icon: UserCircleIcon },
            { id: 'trending', label: 'Trending', icon: ArrowTrendingUpIcon },
            { id: 'gaps', label: 'Content Gaps', icon: ChartBarIcon },
            { id: 'tags', label: 'Smart Tags', icon: TagIcon }
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
        {activeTab === 'personal' && renderPersonalizedRecommendations()}
        {activeTab === 'trending' && renderTrendingTopics()}
        {activeTab === 'gaps' && renderContentGaps()}
        {activeTab === 'tags' && renderSmartTags()}
      </div>
    </motion.div>
  );
};

export default Recommendations;