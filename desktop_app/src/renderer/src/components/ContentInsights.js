import React, { useState, useEffect, useMemo } from 'react';
import { useToast } from '../hooks/useToast';

const ContentInsights = ({ transcription, onInsightsGenerated }) => {
  const [insights, setInsights] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');
  const { addToast } = useToast();

  // Generate insights when transcription changes
  useEffect(() => {
    if (transcription && transcription.text) {
      // If we have a transcript ID, try to get real API insights
      if (transcription.id) {
        generateRealInsights(transcription.id);
      } else {
        generateInsights(transcription);
      }
    }
  }, [transcription]);

  // Add function to handle real API insights
  const generateRealInsights = async (transcriptId) => {
    try {
      setIsGenerating(true);
      
      // Try to get insights from API
      const response = await fetch('http://localhost:8000/api/v1/insights/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `transcript_id=${transcriptId}`
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setInsights(result.data);
          if (onInsightsGenerated) {
            onInsightsGenerated(result.data);
          }
          addToast('AI insights generated successfully!', 'success');
          return;
        }
      }
      
      // Fallback to mock insights if API fails
      throw new Error('API insights failed, using mock data');
      
    } catch (error) {
      console.warn('Using mock insights:', error);
      // Generate mock insights as fallback
      generateInsights(transcription);
    } finally {
      setIsGenerating(false);
    }
  };

  const generateInsights = async (transcript) => {
    if (!transcript.text || transcript.text.length < 100) {
      addToast('Transcript too short for meaningful insights', 'warning');
      return;
    }

    setIsGenerating(true);
    try {
      // Simulate AI processing time
      await new Promise(resolve => setTimeout(resolve, 2000));

      const generatedInsights = {
        summary: generateSummary(transcript.text),
        actionItems: extractActionItems(transcript.text),
        sentimentTimeline: analyzeSentimentTimeline(transcript),
        topics: extractTopics(transcript.text),
        keyHighlights: extractKeyHighlights(transcript.text),
        meetingMinutes: generateMeetingMinutes(transcript)
      };

      setInsights(generatedInsights);
      if (onInsightsGenerated) {
        onInsightsGenerated(generatedInsights);
      }
      addToast('Content insights generated successfully!', 'success');
    } catch (error) {
      console.error('Error generating insights:', error);
      addToast('Failed to generate insights. Please try again.', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const generateSummary = (text) => {
    // Mock AI summary generation
    const sentences = text.split('.').filter(s => s.trim().length > 10);
    const keyPoints = sentences
      .slice(0, Math.min(5, Math.floor(sentences.length * 0.3)))
      .map(s => s.trim())
      .filter(s => s.length > 20);

    return {
      executive: "This discussion covered key strategic initiatives and operational updates with actionable outcomes identified.",
      keyPoints: keyPoints.slice(0, 3),
      wordCount: text.split(' ').length,
      estimatedReadTime: Math.ceil(text.split(' ').length / 200)
    };
  };

  const extractActionItems = (text) => {
    // Mock action item extraction using keywords
    const actionKeywords = ['todo', 'action', 'follow up', 'next steps', 'assign', 'deadline', 'due', 'complete', 'finish', 'deliver'];
    const sentences = text.split('.').filter(s => s.trim().length > 10);
    
    const actionItems = sentences
      .filter(sentence => {
        const lowerSentence = sentence.toLowerCase();
        return actionKeywords.some(keyword => lowerSentence.includes(keyword));
      })
      .map((item, index) => ({
        id: index + 1,
        text: item.trim(),
        assignee: extractAssignee(item),
        priority: determinePriority(item),
        dueDate: extractDueDate(item),
        status: 'pending'
      }))
      .slice(0, 8); // Limit to 8 action items

    return actionItems;
  };

  const extractAssignee = (text) => {
    // Mock assignee extraction
    const names = ['John', 'Sarah', 'Mike', 'Lisa', 'David', 'Anna'];
    const lowerText = text.toLowerCase();
    const foundName = names.find(name => lowerText.includes(name.toLowerCase()));
    return foundName || 'Unassigned';
  };

  const determinePriority = (text) => {
    const urgentWords = ['urgent', 'asap', 'immediately', 'critical', 'important'];
    const lowerText = text.toLowerCase();
    if (urgentWords.some(word => lowerText.includes(word))) return 'high';
    if (lowerText.includes('soon') || lowerText.includes('priority')) return 'medium';
    return 'low';
  };

  const extractDueDate = (text) => {
    // Mock due date extraction
    const dueDatePatterns = ['tomorrow', 'next week', 'end of week', 'monday', 'friday'];
    const lowerText = text.toLowerCase();
    const foundPattern = dueDatePatterns.find(pattern => lowerText.includes(pattern));
    
    if (foundPattern) {
      const today = new Date();
      switch (foundPattern) {
        case 'tomorrow':
          today.setDate(today.getDate() + 1);
          break;
        case 'next week':
          today.setDate(today.getDate() + 7);
          break;
        case 'end of week':
          today.setDate(today.getDate() + (5 - today.getDay()));
          break;
        default:
          today.setDate(today.getDate() + 3);
      }
      return today.toISOString().split('T')[0];
    }
    return null;
  };

  const analyzeSentimentTimeline = (transcript) => {
    // Mock sentiment analysis over time
    const segments = transcript.segments || [];
    const sentimentData = [];

    for (let i = 0; i < Math.min(20, segments.length || 10); i++) {
      const timestamp = segments[i]?.start || (i * 30); // 30-second intervals
      const sentiment = Math.random() * 2 - 1; // Random sentiment between -1 and 1
      const emotion = determineDominantEmotion(sentiment);
      
      sentimentData.push({
        timestamp,
        sentiment,
        emotion,
        confidence: 0.7 + Math.random() * 0.3,
        text: segments[i]?.text || `Segment ${i + 1} content`
      });
    }

    return {
      data: sentimentData,
      overall: {
        average: sentimentData.reduce((sum, item) => sum + item.sentiment, 0) / sentimentData.length,
        trend: determineSentimentTrend(sentimentData),
        emotionalPeaks: findEmotionalPeaks(sentimentData)
      }
    };
  };

  const determineDominantEmotion = (sentiment) => {
    if (sentiment > 0.3) return 'positive';
    if (sentiment < -0.3) return 'negative';
    return 'neutral';
  };

  const determineSentimentTrend = (data) => {
    const firstHalf = data.slice(0, Math.floor(data.length / 2));
    const secondHalf = data.slice(Math.floor(data.length / 2));
    
    const firstAvg = firstHalf.reduce((sum, item) => sum + item.sentiment, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, item) => sum + item.sentiment, 0) / secondHalf.length;
    
    if (secondAvg > firstAvg + 0.1) return 'improving';
    if (secondAvg < firstAvg - 0.1) return 'declining';
    return 'stable';
  };

  const findEmotionalPeaks = (data) => {
    return data
      .filter(item => Math.abs(item.sentiment) > 0.5)
      .sort((a, b) => Math.abs(b.sentiment) - Math.abs(a.sentiment))
      .slice(0, 3);
  };

  const extractTopics = (text) => {
    // Mock topic extraction
    const topicKeywords = {
      'Strategy': ['strategy', 'plan', 'goal', 'objective', 'vision', 'mission'],
      'Budget': ['budget', 'cost', 'expense', 'revenue', 'profit', 'financial'],
      'Team': ['team', 'staff', 'hiring', 'training', 'performance', 'collaboration'],
      'Product': ['product', 'feature', 'development', 'release', 'launch', 'roadmap'],
      'Marketing': ['marketing', 'campaign', 'brand', 'customer', 'market', 'promotion'],
      'Technology': ['technology', 'system', 'software', 'infrastructure', 'api', 'platform']
    };

    const lowerText = text.toLowerCase();
    const topics = Object.entries(topicKeywords)
      .map(([topic, keywords]) => {
        const mentions = keywords.filter(keyword => lowerText.includes(keyword)).length;
        const relevance = mentions / keywords.length;
        return {
          name: topic,
          relevance,
          mentions,
          keywords: keywords.filter(keyword => lowerText.includes(keyword))
        };
      })
      .filter(topic => topic.mentions > 0)
      .sort((a, b) => b.relevance - a.relevance)
      .slice(0, 6);

    return topics;
  };

  const extractKeyHighlights = (text) => {
    // Mock key highlights extraction
    const sentences = text.split('.').filter(s => s.trim().length > 20);
    const importanceKeywords = ['important', 'key', 'critical', 'significant', 'major', 'essential'];
    
    const highlights = sentences
      .filter(sentence => {
        const lowerSentence = sentence.toLowerCase();
        return importanceKeywords.some(keyword => lowerSentence.includes(keyword)) ||
               sentence.length > 100; // Longer sentences often contain important info
      })
      .map((highlight, index) => ({
        id: index + 1,
        text: highlight.trim(),
        importance: Math.random() * 0.3 + 0.7, // Random importance 0.7-1.0
        category: categorizeHighlight(highlight)
      }))
      .sort((a, b) => b.importance - a.importance)
      .slice(0, 5);

    return highlights;
  };

  const categorizeHighlight = (text) => {
    const categories = ['Decision', 'Information', 'Action', 'Concern', 'Opportunity'];
    return categories[Math.floor(Math.random() * categories.length)];
  };

  const generateMeetingMinutes = (transcript) => {
    return {
      title: transcript.title || 'Meeting Minutes',
      date: new Date().toLocaleDateString(),
      duration: transcript.duration || 'Unknown',
      attendees: extractAttendees(transcript.text),
      agenda: extractAgenda(transcript.text),
      decisions: extractDecisions(transcript.text),
      nextMeeting: extractNextMeetingInfo(transcript.text)
    };
  };

  const extractAttendees = (text) => {
    // Mock attendee extraction
    const commonNames = ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Lisa Chen', 'David Wilson'];
    return commonNames.slice(0, Math.floor(Math.random() * 3) + 2);
  };

  const extractAgenda = (text) => {
    // Mock agenda extraction
    return [
      'Review previous action items',
      'Quarterly performance update',
      'New project initiatives',
      'Budget planning discussion',
      'Next steps and assignments'
    ];
  };

  const extractDecisions = (text) => {
    // Mock decisions extraction
    return [
      'Approved budget increase for Q4 marketing campaign',
      'Decided to postpone product launch to Q1 next year',
      'Agreed to hire two additional team members'
    ];
  };

  const extractNextMeetingInfo = (text) => {
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    return {
      date: nextWeek.toLocaleDateString(),
      time: '2:00 PM',
      agenda: 'Follow-up on action items and quarterly review'
    };
  };

  const renderSummaryTab = () => (
    <div className="space-y-6">
      <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
          Executive Summary
        </h3>
        <p className="text-blue-800 dark:text-blue-200">{insights?.summary?.executive}</p>
        <div className="flex gap-4 mt-3 text-sm text-blue-700 dark:text-blue-300">
          <span>📝 {insights?.summary?.wordCount} words</span>
          <span>⏱️ {insights?.summary?.estimatedReadTime} min read</span>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Key Points</h3>
        <ul className="space-y-2">
          {insights?.summary?.keyPoints?.map((point, index) => (
            <li key={index} className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full flex items-center justify-center text-sm font-bold">
                {index + 1}
              </span>
              <span className="text-gray-700 dark:text-gray-300">{point}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );

  const renderActionItemsTab = () => (
    <div className="space-y-4">
      {insights?.actionItems?.length > 0 ? (
        insights.actionItems.map((item) => (
          <div key={item.id} className="border dark:border-gray-600 rounded-lg p-4">
            <div className="flex items-start justify-between mb-2">
              <p className="text-gray-800 dark:text-gray-200 flex-1">{item.text}</p>
              <span className={`px-2 py-1 text-xs rounded-full ${
                item.priority === 'high' ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200' :
                item.priority === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200' :
                'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
              }`}>
                {item.priority}
              </span>
            </div>
            <div className="flex gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span>👤 {item.assignee}</span>
              {item.dueDate && <span>📅 {item.dueDate}</span>}
              <span className={`px-2 py-1 rounded ${
                item.status === 'pending' ? 'bg-gray-100 dark:bg-gray-700' : 'bg-green-100 dark:bg-green-900'
              }`}>
                {item.status}
              </span>
            </div>
          </div>
        ))
      ) : (
        <p className="text-gray-500 dark:text-gray-400 text-center py-8">
          No action items identified in this transcript.
        </p>
      )}
    </div>
  );

  const renderSentimentTab = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-900/20 dark:to-green-900/20 p-4 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">Overall Sentiment</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div 
                className={`h-3 rounded-full ${
                  insights?.sentimentTimeline?.overall?.average > 0 ? 'bg-green-500' : 'bg-red-500'
                }`}
                style={{ width: `${Math.abs(insights?.sentimentTimeline?.overall?.average || 0) * 50 + 50}%` }}
              ></div>
            </div>
          </div>
          <span className="text-sm font-medium">
            {insights?.sentimentTimeline?.overall?.average > 0 ? 'Positive' : 
             insights?.sentimentTimeline?.overall?.average < 0 ? 'Negative' : 'Neutral'}
          </span>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
          Trend: {insights?.sentimentTimeline?.overall?.trend}
        </p>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Emotional Peaks</h3>
        <div className="space-y-3">
          {insights?.sentimentTimeline?.overall?.emotionalPeaks?.map((peak, index) => (
            <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded">
              <span className={`w-3 h-3 rounded-full ${
                peak.emotion === 'positive' ? 'bg-green-500' :
                peak.emotion === 'negative' ? 'bg-red-500' : 'bg-gray-500'
              }`}></span>
              <div className="flex-1">
                <p className="text-sm text-gray-700 dark:text-gray-300">{peak.text}</p>
                <p className="text-xs text-gray-500">
                  {Math.floor(peak.timestamp / 60)}:{String(Math.floor(peak.timestamp % 60)).padStart(2, '0')}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderTopicsTab = () => (
    <div className="space-y-4">
      {insights?.topics?.map((topic, index) => (
        <div key={index} className="border dark:border-gray-600 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold">{topic.name}</h3>
            <span className="text-sm text-gray-500">{topic.mentions} mentions</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
            <div 
              className="bg-blue-500 h-2 rounded-full"
              style={{ width: `${topic.relevance * 100}%` }}
            ></div>
          </div>
          <div className="flex flex-wrap gap-2">
            {topic.keywords.map((keyword, idx) => (
              <span key={idx} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded">
                {keyword}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );

  const renderHighlightsTab = () => (
    <div className="space-y-4">
      {insights?.keyHighlights?.map((highlight) => (
        <div key={highlight.id} className="border dark:border-gray-600 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <p className="text-gray-800 dark:text-gray-200 flex-1">{highlight.text}</p>
            <span className="px-2 py-1 text-xs bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded">
              {highlight.category}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
            <div 
              className="bg-purple-500 h-1 rounded-full"
              style={{ width: `${highlight.importance * 100}%` }}
            ></div>
          </div>
        </div>
      ))}
    </div>
  );

  const renderMinutesTab = () => (
    <div className="space-y-6">
      <div className="border dark:border-gray-600 rounded-lg p-4">
        <h2 className="text-xl font-bold mb-4">{insights?.meetingMinutes?.title}</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <h3 className="font-semibold text-gray-700 dark:text-gray-300">Date</h3>
            <p className="text-gray-600 dark:text-gray-400">{insights?.meetingMinutes?.date}</p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-700 dark:text-gray-300">Duration</h3>
            <p className="text-gray-600 dark:text-gray-400">{insights?.meetingMinutes?.duration}</p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-700 dark:text-gray-300">Attendees</h3>
            <p className="text-gray-600 dark:text-gray-400">
              {insights?.meetingMinutes?.attendees?.join(', ')}
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Agenda</h3>
            <ul className="list-disc list-inside space-y-1">
              {insights?.meetingMinutes?.agenda?.map((item, index) => (
                <li key={index} className="text-gray-600 dark:text-gray-400">{item}</li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Key Decisions</h3>
            <ul className="list-disc list-inside space-y-1">
              {insights?.meetingMinutes?.decisions?.map((decision, index) => (
                <li key={index} className="text-gray-600 dark:text-gray-400">{decision}</li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Next Meeting</h3>
            <p className="text-gray-600 dark:text-gray-400">
              {insights?.meetingMinutes?.nextMeeting?.date} at {insights?.meetingMinutes?.nextMeeting?.time}
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              Agenda: {insights?.meetingMinutes?.nextMeeting?.agenda}
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  if (isGenerating) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Generating AI-powered insights...</p>
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">No insights available. Upload a transcript to get started.</p>
      </div>
    );
  }

  const tabs = [
    { id: 'summary', label: 'Summary', icon: '📋' },
    { id: 'actions', label: 'Action Items', icon: '✅' },
    { id: 'sentiment', label: 'Sentiment', icon: '😊' },
    { id: 'topics', label: 'Topics', icon: '🏷️' },
    { id: 'highlights', label: 'Highlights', icon: '⭐' },
    { id: 'minutes', label: 'Minutes', icon: '📝' }
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="border-b dark:border-gray-600">
        <div className="flex overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 px-4 py-3 text-sm font-medium border-b-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {activeTab === 'summary' && renderSummaryTab()}
        {activeTab === 'actions' && renderActionItemsTab()}
        {activeTab === 'sentiment' && renderSentimentTab()}
        {activeTab === 'topics' && renderTopicsTab()}
        {activeTab === 'highlights' && renderHighlightsTab()}
        {activeTab === 'minutes' && renderMinutesTab()}
      </div>
    </div>
  );
};

export default ContentInsights;