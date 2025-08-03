import React, { useState, useEffect } from 'react';
import {
  Brain,
  TrendingUp,
  Users,
  Calendar,
  MapPin,
  Hash,
  BarChart3,
  PieChart,
  AlertCircle,
  ChevronRight,
  Download,
  RefreshCw
} from 'lucide-react';
import { api } from '../../services/api';

interface InsightMetric {
  label: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
}

interface ContentInsight {
  summary: string;
  sentiment: {
    overall: string;
    score: number;
    distribution: {
      positive: number;
      neutral: number;
      negative: number;
    };
  };
  topics: Array<{
    topic: string;
    relevance: number;
    keywords: string[];
  }>;
  entities: {
    people: string[];
    organizations: string[];
    locations: string[];
    dates: string[];
    products: string[];
  };
  keyPhrases: Array<{
    phrase: string;
    score: number;
  }>;
  statistics: {
    wordCount: number;
    uniqueWords: number;
    averageSentenceLength: number;
    readabilityScore: number;
  };
  recommendations: string[];
}

interface ContentInsightsProps {
  text: string;
  transcriptionId?: string;
  onInsightsGenerated?: (insights: ContentInsight) => void;
}

export const ContentInsights: React.FC<ContentInsightsProps> = ({ 
  text, 
  transcriptionId,
  onInsightsGenerated 
}) => {
  const [insights, setInsights] = useState<ContentInsight | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'overview' | 'entities' | 'topics' | 'sentiment'>('overview');

  useEffect(() => {
    if (text && text.trim()) {
      generateInsights();
    }
  }, [text]);

  const generateInsights = async () => {
    if (!text || !text.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await api.post('/content-insights/analyze', {
        text,
        transcription_id: transcriptionId
      });

      setInsights(response.data);
      if (onInsightsGenerated) {
        onInsightsGenerated(response.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate insights');
    } finally {
      setIsLoading(false);
    }
  };

  const exportInsights = async () => {
    if (!insights) return;

    try {
      const response = await api.post('/content-insights/export', {
        insights,
        transcription_id: transcriptionId
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `content_insights_${new Date().toISOString()}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to export insights');
    }
  };

  const getMetrics = (): InsightMetric[] => {
    if (!insights) return [];

    return [
      {
        label: 'Word Count',
        value: insights.statistics.wordCount.toLocaleString(),
        icon: <Hash className="w-4 h-4" />
      },
      {
        label: 'Unique Words',
        value: insights.statistics.uniqueWords.toLocaleString(),
        icon: <BarChart3 className="w-4 h-4" />
      },
      {
        label: 'Readability Score',
        value: `${insights.statistics.readabilityScore}/100`,
        icon: <TrendingUp className="w-4 h-4" />
      },
      {
        label: 'Avg Sentence Length',
        value: insights.statistics.averageSentenceLength.toFixed(1),
        icon: <PieChart className="w-4 h-4" />
      }
    ];
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-400">Generating insights...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700 rounded p-4">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="text-center py-12">
        <Brain className="w-12 h-12 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-400">No insights available yet</p>
        <button
          onClick={generateInsights}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Generate Insights
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-blue-500" />
          <h2 className="text-xl font-semibold">Content Insights</h2>
        </div>
        <div className="flex gap-2">
          <button
            onClick={generateInsights}
            className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-700 text-white rounded hover:bg-gray-600"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={exportInsights}
            className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <Download className="w-4 h-4" />
            Export PDF
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="font-semibold mb-2">Executive Summary</h3>
        <p className="text-gray-300 text-sm leading-relaxed">{insights.summary}</p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-4 gap-4">
        {getMetrics().map((metric, idx) => (
          <div key={idx} className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">{metric.label}</span>
              {metric.icon}
            </div>
            <div className="text-2xl font-bold">{metric.value}</div>
            {metric.change && (
              <div className={`text-sm mt-1 ${metric.change > 0 ? 'text-green-500' : 'text-red-500'}`}>
                {metric.change > 0 ? '+' : ''}{metric.change}%
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <div className="flex gap-6">
          {(['overview', 'entities', 'topics', 'sentiment'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? 'text-blue-500 border-blue-500'
                  : 'text-gray-400 border-transparent hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="min-h-[300px]">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            {/* Key Phrases */}
            <div>
              <h4 className="font-semibold mb-3">Key Phrases</h4>
              <div className="flex flex-wrap gap-2">
                {insights.keyPhrases.slice(0, 10).map((phrase, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-blue-900/30 border border-blue-700 rounded-full text-sm"
                    style={{ opacity: 0.5 + (phrase.score * 0.5) }}
                  >
                    {phrase.phrase}
                  </span>
                ))}
              </div>
            </div>

            {/* Recommendations */}
            <div>
              <h4 className="font-semibold mb-3">Recommendations</h4>
              <ul className="space-y-2">
                {insights.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 text-blue-500 mt-0.5" />
                    <span className="text-sm text-gray-300">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'entities' && (
          <div className="grid grid-cols-2 gap-6">
            {Object.entries(insights.entities).map(([type, entities]) => (
              <div key={type}>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  {type === 'people' && <Users className="w-4 h-4" />}
                  {type === 'locations' && <MapPin className="w-4 h-4" />}
                  {type === 'dates' && <Calendar className="w-4 h-4" />}
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </h4>
                {entities.length > 0 ? (
                  <ul className="space-y-1">
                    {entities.slice(0, 10).map((entity, idx) => (
                      <li key={idx} className="text-sm text-gray-300">• {entity}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">None found</p>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'topics' && (
          <div className="space-y-4">
            {insights.topics.map((topic, idx) => (
              <div key={idx} className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold">{topic.topic}</h4>
                  <span className="text-sm text-gray-400">
                    Relevance: {(topic.relevance * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2 mb-3">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${topic.relevance * 100}%` }}
                  />
                </div>
                <div className="flex flex-wrap gap-2">
                  {topic.keywords.map((keyword, kidx) => (
                    <span key={kidx} className="text-xs px-2 py-1 bg-gray-700 rounded">
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'sentiment' && (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-6">
              <h4 className="font-semibold mb-4">Overall Sentiment</h4>
              <div className="flex items-center justify-between mb-4">
                <span className="text-3xl font-bold capitalize">{insights.sentiment.overall}</span>
                <span className="text-2xl text-gray-400">{(insights.sentiment.score * 100).toFixed(0)}%</span>
              </div>
              <div className="space-y-3">
                {Object.entries(insights.sentiment.distribution).map(([sentiment, value]) => (
                  <div key={sentiment}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize">{sentiment}</span>
                      <span>{value}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          sentiment === 'positive' ? 'bg-green-500' :
                          sentiment === 'negative' ? 'bg-red-500' :
                          'bg-gray-500'
                        }`}
                        style={{ width: `${value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContentInsights;