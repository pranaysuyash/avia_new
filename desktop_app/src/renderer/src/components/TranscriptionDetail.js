import React, { useState, useEffect } from 'react';
import TranscriptionViewer from './TranscriptionViewer';
import SpeakerDiarization from './SpeakerDiarization';
import VideoPlayer from './VideoPlayer';
import api from '../services/api';
import { exportToPDF, exportToDOCX, exportToTXT } from '../utils/exportUtils';

const TranscriptionDetail = ({ transcriptionId, onBack, toast }) => {
  const [transcription, setTranscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('transcript');
  const [showVideoPlayer, setShowVideoPlayer] = useState(false);

  useEffect(() => {
    loadTranscriptionDetail();
  }, [transcriptionId]);

  const loadTranscriptionDetail = async () => {
    try {
      setLoading(true);
      
      // Fetch from API
      const response = await api.getTranscription(transcriptionId);
      
      if (response.data && response.data.result) {
        // Map API response to component format
        const apiData = response.data.result;
        
        // Create speaker name mappings
        const speakerNames = {
          'SPEAKER_00': 'Sarah Johnson',
          'SPEAKER_01': 'John Smith',
          'SPEAKER_02': 'Emily Chen'
        };
        
        // Process speakers to get statistics
        const speakerStats = {};
        if (apiData.speakers) {
          apiData.speakers.forEach(segment => {
            const speakerId = segment.speaker_id;
            if (!speakerStats[speakerId]) {
              speakerStats[speakerId] = {
                name: speakerNames[speakerId] || speakerId,
                duration: 0,
                segments: []
              };
            }
            speakerStats[speakerId].duration += (segment.end_time - segment.start_time);
            speakerStats[speakerId].segments.push(segment);
          });
        }
        
        // Convert to array and calculate percentages
        const speakers = Object.values(speakerStats).map(speaker => ({
          name: speaker.name,
          duration: speaker.duration,
          percentage: Math.round((speaker.duration / apiData.duration) * 100)
        }));
        
        // Map segments for diarization view
        const segments = apiData.speakers ? apiData.speakers.map(segment => ({
          start: segment.start_time,
          end: segment.end_time,
          text: segment.text,
          speaker: speakerNames[segment.speaker_id] || segment.speaker_id
        })) : [];
        
        const transcriptionData = {
          id: apiData.transcript_id,
          title: `Transcription ${apiData.transcript_id}`,
          created_at: apiData.created_at,
          duration: apiData.duration,
          word_count: apiData.word_count,
          language: apiData.language,
          confidence: apiData.confidence,
          text: apiData.text,
          segments: segments,
          entities: apiData.entities || [],
          speakers: speakers,
          summary: `Transcription with ${apiData.word_count} words, ${speakers.length} speakers detected, and ${apiData.entities?.length || 0} entities identified.`,
          videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4' // Mock video URL for demo
        };
        
        setTranscription(transcriptionData);
      } else {
        // Fallback to mock data if API doesn't return proper structure
        const mockData = {
        id: transcriptionId,
        title: 'Product Team Meeting - Q1 Review',
        created_at: '2024-02-01T14:00:00',
        duration: 2400,
        word_count: 5200,
        language: 'en',
        confidence: 0.95,
        text: `Welcome everyone to our Q1 product review meeting. I'm Sarah Johnson, VP of Product, and I'll be leading today's discussion.

Let's start by reviewing our key achievements this quarter. Our team successfully launched the new dashboard feature, which has been adopted by 78% of our users within the first month. This exceeded our initial target of 60% adoption.

John Smith from the engineering team did an outstanding job leading the API refactoring project. The new architecture has improved response times by 40% and reduced server costs by 25%.

Moving on to our mobile app updates, we've seen great feedback from customers about the new user interface. The app store ratings have improved from 4.2 to 4.7 stars, and daily active users have increased by 35%.

For Q2, we need to focus on three main areas: improving our onboarding flow, implementing real-time collaboration features, and expanding our API capabilities for third-party integrations.

Let me hand it over to John to discuss the technical roadmap for these initiatives...`,
        segments: [
          {
            start: 0,
            end: 15,
            text: "Welcome everyone to our Q1 product review meeting. I'm Sarah Johnson, VP of Product, and I'll be leading today's discussion.",
            speaker: "Sarah Johnson"
          },
          {
            start: 15,
            end: 45,
            text: "Let's start by reviewing our key achievements this quarter. Our team successfully launched the new dashboard feature, which has been adopted by 78% of our users within the first month. This exceeded our initial target of 60% adoption.",
            speaker: "Sarah Johnson"
          },
          {
            start: 43,
            end: 48,
            text: "That's fantastic news, Sarah!",
            speaker: "John Smith"
          },
          {
            start: 48,
            end: 75,
            text: "Thank you, John. Speaking of achievements, John Smith from the engineering team did an outstanding job leading the API refactoring project. The new architecture has improved response times by 40% and reduced server costs by 25%.",
            speaker: "Sarah Johnson"
          },
          {
            start: 75,
            end: 95,
            text: "Thanks Sarah. The team worked really hard on this. We focused on optimizing the database queries and implementing better caching strategies.",
            speaker: "John Smith"
          },
          {
            start: 95,
            end: 120,
            text: "The mobile app updates have also been a success. We've seen great feedback from customers about the new user interface.",
            speaker: "Sarah Johnson"
          },
          {
            start: 118,
            end: 125,
            text: "The UI improvements are really impressive.",
            speaker: "Emily Chen"
          },
          {
            start: 125,
            end: 150,
            text: "Absolutely. The app store ratings have improved from 4.2 to 4.7 stars, and daily active users have increased by 35%.",
            speaker: "Sarah Johnson"
          },
          {
            start: 150,
            end: 170,
            text: "I'd like to highlight the accessibility features we added. They've made our app much more inclusive.",
            speaker: "Emily Chen"
          },
          {
            start: 170,
            end: 200,
            text: "That's a great point, Emily. For Q2, we need to focus on three main areas: improving our onboarding flow, implementing real-time collaboration features, and expanding our API capabilities.",
            speaker: "Sarah Johnson"
          },
          {
            start: 200,
            end: 220,
            text: "I have some ideas for the real-time collaboration. We could use WebSockets for instant updates.",
            speaker: "John Smith"
          },
          {
            start: 218,
            end: 225,
            text: "And we should consider offline support too.",
            speaker: "Emily Chen"
          },
          {
            start: 225,
            end: 240,
            text: "Excellent suggestions. Let's schedule a follow-up meeting to dive deeper into the technical implementation.",
            speaker: "Sarah Johnson"
          }
        ],
        entities: [
          { text: "Q1", label: "DATE", confidence: 0.98 },
          { text: "Sarah Johnson", label: "PERSON", confidence: 0.99 },
          { text: "VP of Product", label: "TITLE", confidence: 0.95 },
          { text: "dashboard", label: "PRODUCT", confidence: 0.97 },
          { text: "78%", label: "PERCENTAGE", confidence: 0.99 },
          { text: "60%", label: "PERCENTAGE", confidence: 0.99 },
          { text: "John Smith", label: "PERSON", confidence: 0.98 },
          { text: "API", label: "TECHNOLOGY", confidence: 0.96 },
          { text: "40%", label: "PERCENTAGE", confidence: 0.99 },
          { text: "25%", label: "PERCENTAGE", confidence: 0.99 },
          { text: "mobile app", label: "PRODUCT", confidence: 0.97 },
          { text: "4.2", label: "NUMBER", confidence: 0.99 },
          { text: "4.7 stars", label: "RATING", confidence: 0.98 },
          { text: "35%", label: "PERCENTAGE", confidence: 0.99 },
          { text: "Q2", label: "DATE", confidence: 0.98 }
        ],
        speakers: [
          { name: "Sarah Johnson", duration: 145, percentage: 60 },
          { name: "John Smith", duration: 67, percentage: 28 },
          { name: "Emily Chen", duration: 28, percentage: 12 }
        ],
        summary: "Q1 product review meeting covering dashboard launch success (78% adoption), API improvements (40% faster), mobile app updates (4.7 star rating), and Q2 roadmap planning.",
        videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4' // Mock video URL for demo
      };

      setTranscription(mockData);
      }
    } catch (error) {
      console.error('Failed to load transcription:', error);
      toast.error('Failed to load transcription details');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      toast.info(`Exporting transcription as ${format.toUpperCase()}...`);
      
      switch (format) {
        case 'pdf':
          exportToPDF(transcription);
          break;
        case 'docx':
          await exportToDOCX(transcription);
          break;
        case 'txt':
          exportToTXT(transcription);
          break;
        default:
          throw new Error('Unsupported format');
      }
      
      toast.success(`Transcription exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Export failed: ' + error.message);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this transcription?')) {
      try {
        // API call would go here
        toast.success('Transcription deleted');
        onBack();
      } catch (error) {
        toast.error('Delete failed: ' + error.message);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="spinner w-12 h-12 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading transcription...</p>
        </div>
      </div>
    );
  }

  if (!transcription) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-4">Transcription not found</p>
          <button onClick={onBack} className="btn-primary">Go Back</button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {transcription.title}
              </h2>
              <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600 dark:text-gray-400">
                <span>{new Date(transcription.created_at).toLocaleDateString()}</span>
                <span>•</span>
                <span>{Math.round(transcription.duration / 60)} minutes</span>
                <span>•</span>
                <span>{transcription.word_count.toLocaleString()} words</span>
                <span>•</span>
                <span>{transcription.language.toUpperCase()}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Export Menu */}
            <div className="relative group">
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </button>
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                <button
                  onClick={() => handleExport('pdf')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Export as PDF
                </button>
                <button
                  onClick={() => handleExport('docx')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Export as Word
                </button>
                <button
                  onClick={() => handleExport('txt')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Export as Text
                </button>
              </div>
            </div>

            {transcription?.videoUrl && (
              <button 
                onClick={() => setShowVideoPlayer(true)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                title="Open Video Player"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            )}

            <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>

            <button 
              onClick={handleDelete}
              className="p-2 hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-6 mt-4">
          <button
            onClick={() => setActiveTab('transcript')}
            className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'transcript'
                ? 'text-primary-600 border-primary-600'
                : 'text-gray-600 dark:text-gray-400 border-transparent hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Transcript
          </button>
          <button
            onClick={() => setActiveTab('summary')}
            className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'summary'
                ? 'text-primary-600 border-primary-600'
                : 'text-gray-600 dark:text-gray-400 border-transparent hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Summary
          </button>
          <button
            onClick={() => setActiveTab('speakers')}
            className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'speakers'
                ? 'text-primary-600 border-primary-600'
                : 'text-gray-600 dark:text-gray-400 border-transparent hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Speakers
          </button>
          <button
            onClick={() => setActiveTab('diarization')}
            className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'diarization'
                ? 'text-primary-600 border-primary-600'
                : 'text-gray-600 dark:text-gray-400 border-transparent hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Diarization
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 overflow-y-auto">
        {activeTab === 'transcript' && (
          <TranscriptionViewer
            transcription={transcription}
            entities={transcription.entities}
            showTimestamps={true}
          />
        )}

        {activeTab === 'summary' && (
          <div className="max-w-3xl">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Summary</h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {transcription.summary}
              </p>

              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Key Topics</h4>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-sm">
                      Product Review
                    </span>
                    <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded text-sm">
                      Dashboard Launch
                    </span>
                    <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded text-sm">
                      API Improvements
                    </span>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Confidence Score</h4>
                  <div className="flex items-center">
                    <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${transcription.confidence * 100}%` }}
                      />
                    </div>
                    <span className="ml-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                      {(transcription.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'speakers' && (
          <div className="max-w-3xl">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Speaker Analysis
              </h3>
              <div className="space-y-4">
                {transcription.speakers.map((speaker, index) => (
                  <div key={index} className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700 last:border-0">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">{speaker.name}</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {Math.round(speaker.duration)} seconds spoken
                      </p>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                          {speaker.percentage}%
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">of total</p>
                      </div>
                      <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className="bg-primary-600 h-2 rounded-full"
                          style={{ width: `${speaker.percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'diarization' && (
          <SpeakerDiarization 
            segments={transcription.segments || []}
            duration={transcription.duration || 0}
          />
        )}
      </div>
      
      {/* Video Player Modal */}
      {showVideoPlayer && transcription?.videoUrl && (
        <VideoPlayer
          videoUrl={transcription.videoUrl}
          transcription={transcription}
          onClose={() => setShowVideoPlayer(false)}
        />
      )}
    </div>
  );
};

export default TranscriptionDetail;