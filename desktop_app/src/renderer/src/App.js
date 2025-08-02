import React, { useState, useEffect } from 'react';
import './styles/globals.css';
import api from './services/api';
import useToast from './hooks/useToast';
import ToastContainer from './components/ToastContainer';
import Settings from './components/Settings';
import SearchInterface from './components/SearchInterface';
import TranscriptionDetail from './components/TranscriptionDetail';
import TranscriptionStatus from './components/TranscriptionStatus';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import BatchUpload from './components/BatchUpload';
import ContentInsights from './components/ContentInsights';
import analytics from './utils/analytics';

function App() {
  const [stats, setStats] = useState({
    totalTranscriptions: 0,
    hoursProcessed: 0,
    entitiesFound: 0,
    accuracyRate: 0
  });
  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState('checking');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [recentTranscriptions, setRecentTranscriptions] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedTranscriptionId, setSelectedTranscriptionId] = useState(null);
  const [activeTranscriptions, setActiveTranscriptions] = useState([]);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [showBatchUpload, setShowBatchUpload] = useState(false);
  const [showContentInsights, setShowContentInsights] = useState(false);
  const [currentTranscription, setCurrentTranscription] = useState(null);
  const { toasts, toast, removeToast } = useToast();

  useEffect(() => {
    checkApiHealth();
    loadDashboardStats();
    loadRecentTranscriptions();
  }, []);

  const checkApiHealth = async () => {
    try {
      const health = await api.checkHealth();
      if (health.status === 'healthy') {
        setApiStatus('connected');
        toast.success('Connected to API server');
      } else {
        setApiStatus('error');
        toast.error('API server error');
      }
    } catch (error) {
      setApiStatus('disconnected');
      toast.error('Unable to connect to API server');
    }
  };

  const loadDashboardStats = async () => {
    try {
      setLoading(true);
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRecentTranscriptions = async () => {
    try {
      const data = await api.getTranscriptions({ limit: 5 });
      setRecentTranscriptions(data.items || []);
    } catch (error) {
      console.error('Failed to load transcriptions:', error);
    }
  };

  const handleFileUpload = async (file) => {
    try {
      analytics.trackFeatureUsage('file-upload', 'initiated');
      setSelectedFile(file);
      setUploadProgress(10);
      toast.info(`Starting upload of ${file.name}...`);
      
      // Upload file
      const uploadResult = await api.uploadFile(file, {
        language: 'auto',
        speakerCount: 2
      });
      
      if (!uploadResult.success) {
        throw new Error(uploadResult.message || 'Upload failed');
      }
      
      setUploadProgress(50);
      toast.info('File uploaded successfully, starting transcription...');
      
      // Start transcription processing
      const transcriptionResult = await api.processTranscription(uploadResult.data.file_id, {
        language: 'auto',
        enableDiarization: true,
        extractEntities: true
      });
      
      if (!transcriptionResult.success) {
        throw new Error(transcriptionResult.message || 'Transcription failed');
      }
      
      setUploadProgress(100);
      
      // Store the transcription for insights
      if (transcriptionResult.data?.result) {
        const transcription = transcriptionResult.data.result;
        setCurrentTranscription({
          id: transcription.transcript_id,
          title: transcription.title || file.name,
          text: transcription.text,
          duration: transcription.duration,
          segments: transcription.segments || [],
          entities: transcription.entities || [],
          uploadedAt: transcription.created_at,
          file_name: file.name
        });
        
        // Add to recent transcriptions
        setRecentTranscriptions(prev => [{
          id: transcription.transcript_id,
          title: transcription.title || file.name,
          created_at: transcription.created_at,
          duration: transcription.duration,
          word_count: transcription.word_count,
          language: transcription.language
        }, ...prev.slice(0, 4)]);
        
        toast.success(`Transcription completed! Generated ${transcription.word_count} words in ${transcription.processing_time}s`);
        
        // Generate insights automatically
        setTimeout(async () => {
          try {
            const insightsResult = await api.generateInsights(transcription.transcript_id);
            if (insightsResult.success) {
              toast.success('Content insights generated! Check the Insights tab.');
            }
          } catch (error) {
            console.warn('Insights generation failed:', error);
          }
        }, 1000);
      }
      
      // Reload stats
      await loadDashboardStats();
      
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Upload failed: ' + error.message);
    } finally {
      setUploadProgress(0);
      setSelectedFile(null);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const loadSampleTranscription = () => {
    // Sample transcription for testing ContentInsights
    const sampleTranscription = {
      id: "sample-transcript-1",
      title: "Team Strategy Meeting - Q3 Planning",
      text: `Welcome everyone to our Q3 strategy meeting. I'm Sarah Johnson, VP of Product, and today we'll be discussing our upcoming initiatives and addressing some critical issues that have come to our attention.

First, let's celebrate our achievements this quarter. Our engineering team, led by John Smith, has successfully delivered the new AI-powered search functionality, which has resulted in a 35% increase in user engagement. This is a fantastic achievement and demonstrates the value of our investment in AI technology.

However, we've also identified some areas that need immediate attention. Mike Davis from our customer support team has reported a 20% increase in user complaints regarding the new dashboard interface. The primary issues are related to navigation confusion and slower than expected load times. This is concerning and needs to be our top priority.

Lisa Chen from our UX team will be working closely with engineering to address these dashboard issues. We need to have fixes implemented by the end of this month to prevent further user frustration.

Moving on to our budget planning for Q4, I'm proposing a 15% increase in our engineering budget to hire two additional developers. This investment will accelerate our development timeline and ensure we can deliver our planned features on schedule.

Our roadmap for the next quarter includes three major initiatives: mobile app enhancement, third-party tool integration, and an advanced analytics dashboard. Each of these projects is critical for maintaining our competitive edge, especially given that TechCorp has recently launched a similar product.

The mobile app project is particularly important since our user research shows 60% of our users prefer mobile access. We're targeting a November 15th completion date for this initiative.

Before we conclude, I want to schedule a follow-up meeting next week to discuss our competitive strategy against TechCorp. We need to ensure we stay ahead of the competition.

To summarize our action items: fix the dashboard issues by month-end, finalize the Q4 budget proposal, begin execution on our three major initiatives, and schedule the competitive strategy meeting. Thank you all for your dedication and hard work.`,
      duration: "45 minutes",
      segments: [
        { start: 0, end: 30, speaker: "Sarah Johnson", text: "Welcome everyone to our Q3 strategy meeting..." },
        { start: 30, end: 60, speaker: "Sarah Johnson", text: "First, let's celebrate our achievements this quarter..." },
        { start: 60, end: 90, speaker: "Sarah Johnson", text: "However, we've also identified some areas..." },
        { start: 90, end: 120, speaker: "Mike Davis", text: "The primary issues are related to navigation..." },
        { start: 120, end: 150, speaker: "Sarah Johnson", text: "Moving on to our budget planning for Q4..." }
      ],
      uploadedAt: new Date().toISOString(),
      entities: [
        { type: 'PERSON', value: 'Sarah Johnson', confidence: 0.95 },
        { type: 'PERSON', value: 'John Smith', confidence: 0.92 },
        { type: 'PERSON', value: 'Mike Davis', confidence: 0.88 },
        { type: 'PERSON', value: 'Lisa Chen', confidence: 0.91 },
        { type: 'ORGANIZATION', value: 'TechCorp', confidence: 0.89 }
      ]
    };
    
    setCurrentTranscription(sampleTranscription);
    setActiveTab('insights');
    toast.success('Sample transcription loaded for Content Insights demo');
  };

  const handleVideoSelect = async (event) => {
    const file = event.target.files[0];
    if (file) {
      try {
        setSelectedFile(file);
        setUploadProgress(20);
        
        // Upload video
        const uploadResult = await api.uploadVideo(file);
        setUploadProgress(50);
        
        // Analyze video
        const analysisResult = await api.analyzeVideo(uploadResult.data.file_id, {
          extractFrames: true,
          detectScenes: true,
          generateThumbnails: true
        });
        
        setUploadProgress(100);
        
        // Show results
        toast.success(`Video processed! Duration: ${analysisResult.data.duration}s, ${analysisResult.data.scenes.length} scenes detected`);
        
        // Reload stats
        await loadDashboardStats();
        
      } catch (error) {
        console.error('Video processing failed:', error);
        toast.error('Video processing failed: ' + error.message);
      } finally {
        setUploadProgress(0);
        setSelectedFile(null);
      }
    }
  };

  const handleBatchStart = (batchId, files) => {
    // Add files to active transcriptions
    const batchTranscriptions = files.map(file => ({
      id: `${batchId}-${file.id}`,
      filename: file.name,
      startTime: new Date(),
      batchId: batchId
    }));
    
    setActiveTranscriptions(prev => [...prev, ...batchTranscriptions]);
    setShowBatchUpload(false);
    toast.info(`Started batch processing for ${files.length} files`);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
          <div className="p-4">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Transcription Platform
            </h1>
          </div>
          <nav className="mt-8">
            <button 
              onClick={() => {
                analytics.trackUserAction('tab-navigation', 'dashboard');
                setActiveTab('dashboard');
              }}
              className={`flex items-center px-4 py-2 text-sm font-medium ${activeTab === 'dashboard' ? 'text-white bg-primary-600 hover:bg-primary-700' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'} w-full text-left`}
            >
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              Dashboard
            </button>
            <button 
              onClick={() => setActiveTab('transcriptions')}
              className={`flex items-center px-4 py-2 mt-2 text-sm font-medium ${activeTab === 'transcriptions' ? 'text-white bg-primary-600 hover:bg-primary-700' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'} w-full text-left`}
            >
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
              Transcriptions
            </button>
            <button 
              onClick={() => setActiveTab('search')}
              className={`flex items-center px-4 py-2 mt-2 text-sm font-medium ${activeTab === 'search' ? 'text-white bg-primary-600 hover:bg-primary-700' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'} w-full text-left`}
            >
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Search
            </button>
            <button 
              onClick={() => setActiveTab('insights')}
              className={`flex items-center px-4 py-2 mt-2 text-sm font-medium ${activeTab === 'insights' ? 'text-white bg-primary-600 hover:bg-primary-700' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'} w-full text-left`}
            >
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Content Insights
            </button>
            <a href="#" className="flex items-center px-4 py-2 mt-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              History
            </a>
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="bg-white dark:bg-gray-800 shadow-sm">
            <div className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {activeTab === 'dashboard' ? 'Dashboard' : 
                   activeTab === 'search' ? 'Search' : 
                   activeTab === 'insights' ? 'Content Insights' : 
                   'Transcriptions'}
                </h2>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    apiStatus === 'connected' ? 'bg-green-500' : 
                    apiStatus === 'error' ? 'bg-red-500' : 
                    'bg-yellow-500 animate-pulse'
                  }`}></div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    API {apiStatus === 'connected' ? 'Connected' : apiStatus === 'error' ? 'Error' : 'Checking...'}
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button 
                  onClick={() => setShowAnalytics(true)}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <svg className="w-6 h-6 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </button>
                <button 
                  onClick={() => setShowSettings(true)}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <svg className="w-6 h-6 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
              </div>
            </div>
          </header>

          {/* Main Content Area */}
          <main className="flex-1 overflow-y-auto">
            {activeTab === 'transcription-detail' ? (
              <TranscriptionDetail
                transcriptionId={selectedTranscriptionId}
                onBack={() => {
                  setActiveTab('dashboard');
                  setSelectedTranscriptionId(null);
                }}
                toast={toast}
              />
            ) : (
              <div className="p-6">
                {activeTab === 'dashboard' && (
              <>
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Transcriptions</p>
                        <p className="text-2xl font-semibold text-gray-900 dark:text-white mt-1">{loading ? '...' : stats.totalTranscriptions.toLocaleString()}</p>
                      </div>
                      <div className="p-3 bg-primary-100 dark:bg-primary-900 rounded-lg">
                        <svg className="w-6 h-6 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Hours Processed</p>
                        <p className="text-2xl font-semibold text-gray-900 dark:text-white mt-1">{loading ? '...' : stats.hoursProcessed.toLocaleString()}</p>
                      </div>
                      <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                        <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Entities Found</p>
                        <p className="text-2xl font-semibold text-gray-900 dark:text-white mt-1">{loading ? '...' : stats.entitiesFound.toLocaleString()}</p>
                      </div>
                      <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                        <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                        </svg>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Accuracy Rate</p>
                        <p className="text-2xl font-semibold text-gray-900 dark:text-white mt-1">{loading ? '...' : `${stats.accuracyRate}%`}</p>
                      </div>
                      <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="mb-8">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <button 
                      onClick={() => setShowBatchUpload(true)}
                      className="p-4 bg-primary-600 hover:bg-primary-700 text-white rounded-lg flex items-center justify-center space-x-2 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      <span>New Transcription</span>
                    </button>
                    <button 
                      onClick={() => document.getElementById('fileInput').click()}
                      disabled={uploadProgress > 0}
                      className={`p-4 ${uploadProgress > 0 ? 'bg-gray-200 dark:bg-gray-700' : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'} text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-lg flex items-center justify-center space-x-2 transition-colors relative overflow-hidden`}
                    >
                      {uploadProgress > 0 && (
                        <div className="absolute inset-0 bg-primary-600 opacity-20" style={{ width: `${uploadProgress}%` }}></div>
                      )}
                      <svg className="w-5 h-5 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <span className="relative z-10">{uploadProgress > 0 ? `Uploading ${uploadProgress}%` : 'Upload Audio'}</span>
                    </button>
                    <input
                      id="fileInput"
                      type="file"
                      onChange={handleFileSelect}
                      accept="audio/*,video/*"
                      className="hidden"
                    />
                    <button 
                      onClick={() => document.getElementById('videoInput').click()}
                      className="p-4 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-lg flex items-center justify-center space-x-2 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span>Process Video</span>
                    </button>
                    <input
                      id="videoInput"
                      type="file"
                      onChange={handleVideoSelect}
                      accept="video/*"
                      className="hidden"
                    />
                    <button 
                      onClick={loadSampleTranscription}
                      className="p-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-lg flex items-center justify-center space-x-2 transition-all transform hover:scale-105"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      <span>Try Content Insights</span>
                    </button>
                  </div>
                  
                  {selectedFile && (
                    <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <p className="text-sm text-blue-800 dark:text-blue-200">
                        Selected file: <span className="font-medium">{selectedFile.name}</span> ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                      </p>
                    </div>
                  )}
                </div>

                {/* Active Transcriptions */}
                {activeTranscriptions.length > 0 && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Active Transcriptions</h3>
                    <div className="space-y-4">
                      {activeTranscriptions.map((transcription) => (
                        <TranscriptionStatus
                          key={transcription.id}
                          transcriptionId={transcription.id}
                          onComplete={(data) => {
                            // Remove from active list
                            setActiveTranscriptions(prev => prev.filter(t => t.id !== transcription.id));
                            // Reload recent transcriptions
                            loadRecentTranscriptions();
                            loadDashboardStats();
                          }}
                          toast={toast}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Recent Transcriptions */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Transcriptions</h3>
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                    {recentTranscriptions.length === 0 ? (
                      <div className="p-6">
                        <p className="text-gray-600 dark:text-gray-400">No recent transcriptions. Start by uploading an audio or video file.</p>
                      </div>
                    ) : (
                      <div className="divide-y divide-gray-200 dark:divide-gray-700">
                        {recentTranscriptions.map((transcription) => (
                          <div key={transcription.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                                  {transcription.title || `Transcription ${transcription.id}`}
                                </h4>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                  {transcription.duration ? `${Math.round(transcription.duration / 60)} minutes` : 'Processing...'} • 
                                  {' ' + (transcription.word_count || 0).toLocaleString()} words
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                  {new Date(transcription.created_at).toLocaleDateString()}
                                </p>
                              </div>
                              <div className="flex items-center space-x-2">
                                <button 
                                  onClick={() => {
                                    setSelectedTranscriptionId(transcription.id);
                                    setActiveTab('transcription-detail');
                                  }}
                                  className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                >
                                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                  </svg>
                                </button>
                                <button className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                  </svg>
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {activeTab === 'search' && (
              <SearchInterface toast={toast} />
            )}

            {activeTab === 'insights' && (
              <ContentInsights 
                transcription={currentTranscription}
                onInsightsGenerated={(insights) => {
                  console.log('Insights generated:', insights);
                  toast.success('Content insights generated successfully!');
                }}
              />
            )}

            {activeTab === 'transcriptions' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">All Transcriptions</h3>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                  <p className="text-gray-600 dark:text-gray-400">Transcriptions list view will be implemented here.</p>
                </div>
              </div>
            )}
              </div>
            )}
          </main>
        </div>
      </div>
      {showSettings && (
        <Settings onClose={() => setShowSettings(false)} toast={toast} />
      )}
      {showAnalytics && (
        <AnalyticsDashboard onClose={() => setShowAnalytics(false)} />
      )}
      {showBatchUpload && (
        <BatchUpload
          onClose={() => setShowBatchUpload(false)}
          toast={toast}
          onBatchStart={handleBatchStart}
        />
      )}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </div>
  );
}

export default App;