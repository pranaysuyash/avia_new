import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ChartBarIcon,
  HeartIcon,
  MicrophoneIcon,
  AcademicCapIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  PresentationChartLineIcon,
  UserGroupIcon,
  BookOpenIcon,
  SpeakerWaveIcon
} from '@heroicons/react/24/outline';
import { Line, Bar, Radar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface ContentAnalysisData {
  transcript_id: string;
  emotion_analysis: {
    dominant_emotion: string;
    emotion_scores: { [key: string]: number };
    emotion_timeline: Array<{
      time: number;
      emotion: string;
      sentiment: number;
      confidence: number;
    }>;
    overall_sentiment: string;
    sentiment_score: number;
    mood_changes: Array<{
      time: number;
      from: string;
      to: string;
      intensity: number;
    }>;
  };
  speaking_patterns: {
    speaking_rate: number;
    pace_variation: number;
    pause_frequency: number;
    pause_duration_avg: number;
    filler_word_count: number;
    filler_word_ratio: number;
    emphasis_patterns: Array<{
      type: string;
      word: string;
      position: number;
      context: string;
    }>;
    fluency_score: number;
  };
  complexity_analysis: {
    readability_score: number;
    grade_level: number;
    vocabulary_diversity: number;
    sentence_complexity: number;
    technical_term_ratio: number;
    jargon_score: number;
    clarity_score: number;
  };
  bias_analysis: {
    bias_detected: boolean;
    bias_types: string[];
    bias_instances: Array<{
      type: string;
      term?: string;
      count?: number;
      category?: string;
      context?: string;
      suggestion?: string;
    }>;
    inclusivity_score: number;
    suggestions: string[];
    gender_balance: {
      male: number;
      female: number;
      neutral_ratio: number;
    };
  };
  key_insights: string[];
  recommendations: string[];
  metadata: {
    analyzed_at: string;
    text_length: number;
    word_count: number;
    has_audio: boolean;
    has_timestamps: boolean;
  };
}

const ContentAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'emotion' | 'speaking' | 'complexity' | 'bias'>('emotion');
  const [analysisData, setAnalysisData] = useState<ContentAnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTranscript, setSelectedTranscript] = useState<string>('test_transcript_001');

  useEffect(() => {
    analyzeContent();
  }, [selectedTranscript]);

  const analyzeContent = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/content-analysis/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript_id: selectedTranscript })
      });
      
      if (response.ok) {
        const result = await response.json();
        setAnalysisData(result.data);
      }
    } catch (error) {
      console.error('Failed to analyze content:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderEmotionAnalysis = () => {
    if (!analysisData) return null;
    
    const emotionData = {
      labels: Object.keys(analysisData.emotion_analysis.emotion_scores),
      datasets: [{
        label: 'Emotion Distribution',
        data: Object.values(analysisData.emotion_analysis.emotion_scores),
        backgroundColor: [
          'rgba(255, 206, 86, 0.5)',
          'rgba(54, 162, 235, 0.5)',
          'rgba(75, 192, 192, 0.5)',
          'rgba(255, 99, 132, 0.5)',
          'rgba(153, 102, 255, 0.5)',
          'rgba(255, 159, 64, 0.5)'
        ],
        borderColor: [
          'rgba(255, 206, 86, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)'
        ],
        borderWidth: 1
      }]
    };

    const timelineData = {
      labels: analysisData.emotion_analysis.emotion_timeline.map(e => `${e.time}s`),
      datasets: [{
        label: 'Sentiment Over Time',
        data: analysisData.emotion_analysis.emotion_timeline.map(e => e.sentiment),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.4,
        fill: true
      }]
    };

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Overall Emotion Summary */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Overall Emotional Tone
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Dominant Emotion:</span>
                <span className="text-xl font-semibold capitalize text-indigo-600">
                  {analysisData.emotion_analysis.dominant_emotion}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Overall Sentiment:</span>
                <div className="flex items-center space-x-2">
                  <span className={`text-lg font-medium capitalize ${
                    analysisData.emotion_analysis.overall_sentiment === 'positive' 
                      ? 'text-emerald-600' 
                      : analysisData.emotion_analysis.overall_sentiment === 'negative'
                      ? 'text-red-600'
                      : 'text-gray-600'
                  }`}>
                    {analysisData.emotion_analysis.overall_sentiment}
                  </span>
                  <span className="text-sm text-gray-500">
                    ({(analysisData.emotion_analysis.sentiment_score * 100).toFixed(0)}%)
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Mood Changes:</span>
                <span className="text-lg font-medium">
                  {analysisData.emotion_analysis.mood_changes.length}
                </span>
              </div>
            </div>
          </div>

          {/* Emotion Distribution Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Emotion Distribution
            </h3>
            <div className="h-64">
              <Doughnut 
                data={emotionData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'right'
                    }
                  }
                }}
              />
            </div>
          </div>
        </div>

        {/* Sentiment Timeline */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Sentiment Timeline
          </h3>
          <div className="h-64">
            <Line 
              data={timelineData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    min: -1,
                    max: 1
                  }
                }
              }}
            />
          </div>
        </div>

        {/* Mood Changes */}
        {analysisData.emotion_analysis.mood_changes.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Mood Transitions
            </h3>
            <div className="space-y-3">
              {analysisData.emotion_analysis.mood_changes.map((change, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-500">@{change.time}s</span>
                    <span className="text-sm font-medium capitalize">{change.from}</span>
                    <span className="text-gray-400">→</span>
                    <span className="text-sm font-medium capitalize">{change.to}</span>
                  </div>
                  <div className="text-sm text-gray-500">
                    Intensity: {(change.intensity * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderSpeakingPatterns = () => {
    if (!analysisData) return null;

    const paceData = {
      labels: ['Speaking Rate', 'Fluency', 'Clarity'],
      datasets: [{
        label: 'Speaking Metrics',
        data: [
          analysisData.speaking_patterns.speaking_rate / 200, // Normalize to 0-1
          analysisData.speaking_patterns.fluency_score,
          1 - analysisData.speaking_patterns.filler_word_ratio * 10 // Inverse of filler ratio
        ],
        backgroundColor: 'rgba(99, 102, 241, 0.2)',
        borderColor: 'rgba(99, 102, 241, 1)',
        pointBackgroundColor: 'rgba(99, 102, 241, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(99, 102, 241, 1)'
      }]
    };

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Speaking Metrics */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Speaking Metrics
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Speaking Rate:</span>
                <span className="text-lg font-medium">
                  {analysisData.speaking_patterns.speaking_rate.toFixed(0)} WPM
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Fluency Score:</span>
                <div className="flex items-center space-x-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-indigo-600 h-2 rounded-full"
                      style={{ width: `${analysisData.speaking_patterns.fluency_score * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-500">
                    {(analysisData.speaking_patterns.fluency_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Pause Frequency:</span>
                <span className="text-lg font-medium">
                  {analysisData.speaking_patterns.pause_frequency.toFixed(1)}/min
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Filler Words:</span>
                <span className="text-lg font-medium">
                  {analysisData.speaking_patterns.filler_word_count}
                  <span className="text-sm text-gray-500 ml-1">
                    ({(analysisData.speaking_patterns.filler_word_ratio * 100).toFixed(1)}%)
                  </span>
                </span>
              </div>
            </div>
          </div>

          {/* Speaking Pattern Radar */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Speaking Pattern Analysis
            </h3>
            <div className="h-64">
              <Radar 
                data={paceData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    r: {
                      beginAtZero: true,
                      max: 1
                    }
                  }
                }}
              />
            </div>
          </div>
        </div>

        {/* Emphasis Patterns */}
        {analysisData.speaking_patterns.emphasis_patterns.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Emphasis Patterns
            </h3>
            <div className="space-y-3">
              {analysisData.speaking_patterns.emphasis_patterns.map((pattern, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className={`px-2 py-1 text-xs rounded ${
                    pattern.type === 'capitalization' ? 'bg-blue-100 text-blue-800' :
                    pattern.type === 'repetition' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-purple-100 text-purple-800'
                  }`}>
                    {pattern.type}
                  </span>
                  <div className="flex-1">
                    <span className="font-medium text-gray-900 dark:text-white">
                      "{pattern.word}"
                    </span>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {pattern.context}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderComplexityAnalysis = () => {
    if (!analysisData) return null;

    const complexityData = {
      labels: ['Readability', 'Clarity', 'Vocabulary Diversity', 'Simplicity'],
      datasets: [{
        label: 'Content Complexity',
        data: [
          analysisData.complexity_analysis.readability_score / 100,
          analysisData.complexity_analysis.clarity_score,
          analysisData.complexity_analysis.vocabulary_diversity,
          1 - analysisData.complexity_analysis.jargon_score
        ],
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 2
      }]
    };

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Readability Scores */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Readability Metrics
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Reading Ease:</span>
                <div className="flex items-center space-x-2">
                  <span className="text-lg font-medium">
                    {analysisData.complexity_analysis.readability_score.toFixed(1)}
                  </span>
                  <span className="text-sm text-gray-500">
                    ({analysisData.complexity_analysis.readability_score >= 60 ? 'Easy' : 
                      analysisData.complexity_analysis.readability_score >= 30 ? 'Moderate' : 'Difficult'})
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Grade Level:</span>
                <span className="text-lg font-medium">
                  {analysisData.complexity_analysis.grade_level.toFixed(1)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Clarity Score:</span>
                <div className="flex items-center space-x-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-emerald-600 h-2 rounded-full"
                      style={{ width: `${analysisData.complexity_analysis.clarity_score * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-500">
                    {(analysisData.complexity_analysis.clarity_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Complexity Radar */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Complexity Overview
            </h3>
            <div className="h-64">
              <Radar 
                data={complexityData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    r: {
                      beginAtZero: true,
                      max: 1
                    }
                  }
                }}
              />
            </div>
          </div>
        </div>

        {/* Vocabulary Analysis */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Vocabulary Analysis
          </h3>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-indigo-600">
                {(analysisData.complexity_analysis.vocabulary_diversity * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-gray-500">Vocabulary Diversity</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-600">
                {(analysisData.complexity_analysis.technical_term_ratio * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-gray-500">Technical Terms</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">
                {(analysisData.complexity_analysis.jargon_score * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-gray-500">Jargon Density</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderBiasAnalysis = () => {
    if (!analysisData) return null;

    const genderData = {
      labels: ['Male', 'Female', 'Neutral'],
      datasets: [{
        label: 'Gender Representation',
        data: [
          analysisData.bias_analysis.gender_balance.male,
          analysisData.bias_analysis.gender_balance.female,
          analysisData.bias_analysis.gender_balance.neutral_ratio
        ],
        backgroundColor: [
          'rgba(59, 130, 246, 0.5)',
          'rgba(236, 72, 153, 0.5)',
          'rgba(156, 163, 175, 0.5)'
        ],
        borderColor: [
          'rgba(59, 130, 246, 1)',
          'rgba(236, 72, 153, 1)',
          'rgba(156, 163, 175, 1)'
        ],
        borderWidth: 1
      }]
    };

    return (
      <div className="space-y-6">
        {/* Bias Summary */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Bias Analysis Summary
            </h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Inclusivity Score:</span>
              <span className="text-xl font-bold text-emerald-600">
                {(analysisData.bias_analysis.inclusivity_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {analysisData.bias_analysis.bias_detected ? (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-yellow-600">
                <ExclamationTriangleIcon className="h-5 w-5" />
                <span className="font-medium">
                  {analysisData.bias_analysis.bias_types.length} types of bias detected
                </span>
              </div>
              
              <div className="flex flex-wrap gap-2">
                {analysisData.bias_analysis.bias_types.map((type) => (
                  <span key={type} className="px-3 py-1 text-sm bg-yellow-100 text-yellow-800 rounded-full">
                    {type}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-emerald-600">
              <LightBulbIcon className="h-5 w-5" />
              <span>No significant bias detected</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Gender Balance */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Gender Language Balance
            </h3>
            <div className="h-64">
              <Doughnut 
                data={genderData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom'
                    }
                  }
                }}
              />
            </div>
          </div>

          {/* Bias Instances */}
          {analysisData.bias_analysis.bias_instances.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Bias Instances Found
              </h3>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {analysisData.bias_analysis.bias_instances.map((instance, index) => (
                  <div key={index} className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {instance.type} bias
                        </span>
                        {instance.term && (
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Term: "{instance.term}"
                          </p>
                        )}
                        {instance.context && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                            "{instance.context}"
                          </p>
                        )}
                      </div>
                      {instance.count && (
                        <span className="text-sm font-medium text-gray-500">
                          ×{instance.count}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Suggestions */}
        {analysisData.bias_analysis.suggestions.length > 0 && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
            <h3 className="text-lg font-medium text-blue-900 dark:text-blue-100 mb-3">
              Inclusivity Recommendations
            </h3>
            <ul className="space-y-2">
              {analysisData.bias_analysis.suggestions.map((suggestion, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <span className="text-blue-600 dark:text-blue-400">•</span>
                  <span className="text-sm text-blue-800 dark:text-blue-200">{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
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
          Advanced Content Analysis
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          AI-powered insights into emotions, speaking patterns, complexity, and bias
        </p>
      </div>

      {/* Quick Summary */}
      {analysisData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <HeartIcon className="h-8 w-8 text-rose-500" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Sentiment</p>
                <p className="text-lg font-semibold capitalize">
                  {analysisData.emotion_analysis.overall_sentiment}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <MicrophoneIcon className="h-8 w-8 text-indigo-500" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Fluency</p>
                <p className="text-lg font-semibold">
                  {(analysisData.speaking_patterns.fluency_score * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <AcademicCapIcon className="h-8 w-8 text-emerald-500" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Grade Level</p>
                <p className="text-lg font-semibold">
                  {analysisData.complexity_analysis.grade_level.toFixed(0)}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <UserGroupIcon className="h-8 w-8 text-purple-500" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Inclusivity</p>
                <p className="text-lg font-semibold">
                  {(analysisData.bias_analysis.inclusivity_score * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'emotion', label: 'Emotions', icon: HeartIcon },
            { id: 'speaking', label: 'Speaking', icon: SpeakerWaveIcon },
            { id: 'complexity', label: 'Complexity', icon: BookOpenIcon },
            { id: 'bias', label: 'Bias Analysis', icon: UserGroupIcon }
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
        {activeTab === 'emotion' && renderEmotionAnalysis()}
        {activeTab === 'speaking' && renderSpeakingPatterns()}
        {activeTab === 'complexity' && renderComplexityAnalysis()}
        {activeTab === 'bias' && renderBiasAnalysis()}
      </div>

      {/* Key Insights and Recommendations */}
      {analysisData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
            <h3 className="text-lg font-medium text-green-900 dark:text-green-100 mb-3">
              Key Insights
            </h3>
            <ul className="space-y-2">
              {analysisData.key_insights.map((insight, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <LightBulbIcon className="h-4 w-4 text-green-600 dark:text-green-400 mt-0.5" />
                  <span className="text-sm text-green-800 dark:text-green-200">{insight}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-6">
            <h3 className="text-lg font-medium text-indigo-900 dark:text-indigo-100 mb-3">
              Recommendations
            </h3>
            <ul className="space-y-2">
              {analysisData.recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <PresentationChartLineIcon className="h-4 w-4 text-indigo-600 dark:text-indigo-400 mt-0.5" />
                  <span className="text-sm text-indigo-800 dark:text-indigo-200">{recommendation}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default ContentAnalysis;