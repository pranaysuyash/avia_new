/**
 * Voice Profile Dashboard Component
 * Comprehensive interface for voice profiling and analysis
 */

import React, { useState, useEffect, useCallback } from 'react';
import { webTheme } from '../../shared/theme';

interface VoiceProfile {
  profile_id: string;
  name: string;
  voice_characteristics: Record<string, any>;
  enrollment_date: string;
  last_seen?: string;
  recognition_count: number;
}

interface EmotionAnalysis {
  primary_emotion: string;
  emotion_scores: Record<string, number>;
  valence: number;
  arousal: number;
  confidence: number;
  timestamp: string;
}

interface VoiceAnalysisResult {
  analysis_id: string;
  timestamp: string;
  audio_duration: number;
  results: {
    emotion?: EmotionAnalysis;
    identification?: {
      identified_speaker?: string;
      confidence: number;
      similarity_score: number;
      is_known_speaker: boolean;
    };
    stress?: {
      stress_level: number;
      fatigue_level: number;
      voice_quality: number;
      confidence: number;
    };
  };
  processing_time_ms: number;
}

interface VoiceProfileDashboardProps {
  className?: string;
}

export const VoiceProfileDashboard: React.FC<VoiceProfileDashboardProps> = ({
  className = '',
}) => {
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<VoiceProfile | null>(null);
  const [analysisResults, setAnalysisResults] = useState<VoiceAnalysisResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [showEnrollmentDialog, setShowEnrollmentDialog] = useState(false);
  const [enrollmentData, setEnrollmentData] = useState({
    name: '',
    description: '',
    audioFiles: [] as File[]
  });

  // Load profiles and stats on mount
  useEffect(() => {
    loadProfiles();
    loadStats();
  }, []);

  const loadProfiles = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/voice-profiling/profiles');
      if (response.ok) {
        const profilesData = await response.json();
        setProfiles(profilesData);
      }
    } catch (error) {
      console.error('Failed to load profiles:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/voice-profiling/stats');
      if (response.ok) {
        const statsData = await response.json();
        setStats(statsData);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const analyzeVoice = async (audioFile: File, analysisTypes: string[] = ['emotion', 'identification', 'stress']) => {
    try {
      setIsAnalyzing(true);
      const formData = new FormData();
      formData.append('audio_file', audioFile);
      formData.append('analysis_types', JSON.stringify(analysisTypes));

      const response = await fetch('/api/voice-profiling/analyze', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result: VoiceAnalysisResult = await response.json();
        setAnalysisResults(prev => [result, ...prev.slice(0, 9)]); // Keep last 10 results
        return result;
      }
    } catch (error) {
      console.error('Voice analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
    return null;
  };

  const enrollSpeaker = async () => {
    if (!enrollmentData.name || enrollmentData.audioFiles.length === 0) return;

    try {
      setIsLoading(true);
      const formData = new FormData();
      formData.append('name', enrollmentData.name);
      formData.append('description', enrollmentData.description);
      
      enrollmentData.audioFiles.forEach((file, index) => {
        formData.append('audio_files', file);
      });

      const response = await fetch('/api/voice-profiling/enroll', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const newProfile: VoiceProfile = await response.json();
        setProfiles(prev => [...prev, newProfile]);
        setShowEnrollmentDialog(false);
        setEnrollmentData({ name: '', description: '', audioFiles: [] });
      }
    } catch (error) {
      console.error('Speaker enrollment failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteProfile = async (profileId: string) => {
    try {
      const response = await fetch(`/api/voice-profiling/profiles/${profileId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setProfiles(prev => prev.filter(p => p.profile_id !== profileId));
        if (selectedProfile?.profile_id === profileId) {
          setSelectedProfile(null);
        }
      }
    } catch (error) {
      console.error('Failed to delete profile:', error);
    }
  };

  const renderEmotionVisualization = (emotion: EmotionAnalysis) => {
    const emotions = Object.entries(emotion.emotion_scores).sort(([,a], [,b]) => b - a);
    
    return (
      <div style={{ marginBottom: webTheme.spacing['4'] }}>
        <h4 style={{ margin: `0 0 ${webTheme.spacing['3']} 0`, fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
          Emotion Analysis
        </h4>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: webTheme.spacing['4'] }}>
          <div>
            <div style={{ marginBottom: webTheme.spacing['2'] }}>
              <span style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                Primary Emotion
              </span>
              <div style={{ fontSize: webTheme.typography.fontSize.lg, fontWeight: webTheme.typography.fontWeight.semibold, color: webTheme.colors.primary['600'] }}>
                {emotion.primary_emotion}
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: webTheme.spacing['2'] }}>
              <div>
                <span style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                  Valence
                </span>
                <div style={{ fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
                  {emotion.valence.toFixed(2)}
                </div>
              </div>
              <div>
                <span style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                  Arousal
                </span>
                <div style={{ fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
                  {emotion.arousal.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
          
          <div>
            <span style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary, marginBottom: webTheme.spacing['2'], display: 'block' }}>
              Emotion Scores
            </span>
            {emotions.slice(0, 5).map(([emotionName, score]) => (
              <div key={emotionName} style={{ marginBottom: webTheme.spacing['1'] }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: webTheme.spacing['1'] }}>
                  <span style={{ fontSize: webTheme.typography.fontSize.sm, textTransform: 'capitalize' }}>
                    {emotionName}
                  </span>
                  <span style={{ fontSize: webTheme.typography.fontSize.sm, fontWeight: webTheme.typography.fontWeight.medium }}>
                    {(score * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={{ 
                  width: '100%', 
                  height: '4px', 
                  backgroundColor: webTheme.colors.gray['200'], 
                  borderRadius: webTheme.borderRadius.DEFAULT 
                }}>
                  <div style={{ 
                    width: `${score * 100}%`, 
                    height: '100%', 
                    backgroundColor: webTheme.colors.primary['500'], 
                    borderRadius: webTheme.borderRadius.DEFAULT 
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderStressAnalysis = (stress: any) => {
    return (
      <div style={{ marginBottom: webTheme.spacing['4'] }}>
        <h4 style={{ margin: `0 0 ${webTheme.spacing['3']} 0`, fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
          Stress & Voice Quality Analysis
        </h4>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: webTheme.spacing['4'] }}>
          <div>
            <span style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
              Stress Level
            </span>
            <div style={{ 
              fontSize: webTheme.typography.fontSize.lg, 
              fontWeight: webTheme.typography.fontWeight.semibold,
              color: stress.stress_level > 0.7 ? webTheme.colors.error['600'] : 
                     stress.stress_level > 0.4 ? webTheme.colors.warning['600'] : 
                     webTheme.colors.success['600']
            }}>
              {(stress.stress_level * 100).toFixed(0)}%
            </div>
          </div>
          
          <div>
            <span style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
              Fatigue Level
            </span>
            <div style={{ 
              fontSize: webTheme.typography.fontSize.lg, 
              fontWeight: webTheme.typography.fontWeight.semibold,
              color: stress.fatigue_level > 0.7 ? webTheme.colors.error['600'] : 
                     stress.fatigue_level > 0.4 ? webTheme.colors.warning['600'] : 
                     webTheme.colors.success['600']
            }}>
              {(stress.fatigue_level * 100).toFixed(0)}%
            </div>
          </div>
          
          <div>
            <span style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
              Voice Quality
            </span>
            <div style={{ 
              fontSize: webTheme.typography.fontSize.lg, 
              fontWeight: webTheme.typography.fontWeight.semibold,
              color: stress.voice_quality > 0.7 ? webTheme.colors.success['600'] : 
                     stress.voice_quality > 0.4 ? webTheme.colors.warning['600'] : 
                     webTheme.colors.error['600']
            }}>
              {(stress.voice_quality * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`voice-profile-dashboard ${className}`}>
      {/* Header */}
      <div style={{ marginBottom: webTheme.spacing['6'], display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: webTheme.typography.fontSize.xl, fontWeight: webTheme.typography.fontWeight.bold }}>
            🎙️ Voice Profiling & Analysis Dashboard
          </h2>
          <p style={{ margin: `${webTheme.spacing['2']} 0 0 0`, fontSize: webTheme.typography.fontSize.base, color: webTheme.colors.text.secondary }}>
            Advanced voice analysis with emotion detection, speaker identification, and stress analysis
          </p>
        </div>
        <button
          onClick={async () => {
            try {
              const u = new URL(window.location.href);
              await navigator.clipboard.writeText(u.toString());
              // eslint-disable-next-line @typescript-eslint/no-var-requires
              const { logUxEvent } = require('../../components/shared/uxTelemetry');
              try { logUxEvent('share_view_copied', { page: 'voice_profile_dashboard' }); } catch {}
            } catch {}
          }}
          style={{ padding: '8px 12px', border: `1px solid ${webTheme.colors.border.light}`, borderRadius: 8, background: 'white', cursor: 'pointer' }}
          aria-label="Copy shareable link"
          title="Copy shareable link"
        >
          Share
        </button>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div style={{ 
          marginBottom: webTheme.spacing['6'],
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: webTheme.spacing['4']
        }}>
          <div style={{
            padding: webTheme.spacing['4'],
            backgroundColor: webTheme.colors.background.secondary,
            borderRadius: webTheme.borderRadius.lg,
            border: `1px solid ${webTheme.colors.border.light}`,
          }}>
            <div style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
              Enrolled Speakers
            </div>
            <div style={{ fontSize: webTheme.typography.fontSize.xl, fontWeight: webTheme.typography.fontWeight.bold, color: webTheme.colors.primary['600'] }}>
              {stats.enrolled_speakers}
            </div>
          </div>
          
          <div style={{
            padding: webTheme.spacing['4'],
            backgroundColor: webTheme.colors.background.secondary,
            borderRadius: webTheme.borderRadius.lg,
            border: `1px solid ${webTheme.colors.border.light}`,
          }}>
            <div style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
              Analysis Types
            </div>
            <div style={{ fontSize: webTheme.typography.fontSize.xl, fontWeight: webTheme.typography.fontWeight.bold, color: webTheme.colors.success['600'] }}>
              {stats.analysis_types?.length || 0}
            </div>
          </div>
          
          <div style={{
            padding: webTheme.spacing['4'],
            backgroundColor: webTheme.colors.background.secondary,
            borderRadius: webTheme.borderRadius.lg,
            border: `1px solid ${webTheme.colors.border.light}`,
          }}>
            <div style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
              System Status
            </div>
            <div style={{ fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium, color: webTheme.colors.success['600'] }}>
              {stats.system_status}
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: webTheme.spacing['6'] }}>
        {/* Voice Profiles Panel */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: webTheme.spacing['4'] }}>
            <h3 style={{ margin: 0, fontSize: webTheme.typography.fontSize.lg, fontWeight: webTheme.typography.fontWeight.semibold }}>
              Voice Profiles
            </h3>
            <button
              onClick={() => setShowEnrollmentDialog(true)}
              style={{
                padding: `${webTheme.spacing['2']} ${webTheme.spacing['4']}`,
                backgroundColor: webTheme.colors.primary['600'],
                color: 'white',
                border: 'none',
                borderRadius: webTheme.borderRadius.DEFAULT,
                fontSize: webTheme.typography.fontSize.sm,
                cursor: 'pointer',
              }}
            >
              + Enroll Speaker
            </button>
          </div>

          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {profiles.map((profile) => (
              <div
                key={profile.profile_id}
                onClick={() => setSelectedProfile(profile)}
                style={{
                  padding: webTheme.spacing['3'],
                  marginBottom: webTheme.spacing['2'],
                  backgroundColor: selectedProfile?.profile_id === profile.profile_id 
                    ? webTheme.colors.primary['50'] 
                    : webTheme.colors.background.primary,
                  border: `1px solid ${
                    selectedProfile?.profile_id === profile.profile_id 
                      ? webTheme.colors.primary['200'] 
                      : webTheme.colors.border.light
                  }`,
                  borderRadius: webTheme.borderRadius.md,
                  cursor: 'pointer',
                  transition: 'all 150ms',
                }}
                onMouseEnter={(e) => {
                  if (selectedProfile?.profile_id !== profile.profile_id) {
                    e.currentTarget.style.backgroundColor = webTheme.colors.gray['50'];
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedProfile?.profile_id !== profile.profile_id) {
                    e.currentTarget.style.backgroundColor = webTheme.colors.background.primary;
                  }
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
                      {profile.name}
                    </div>
                    <div style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                      {profile.recognition_count} recognitions
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteProfile(profile.profile_id);
                    }}
                    style={{
                      padding: webTheme.spacing['1'],
                      backgroundColor: 'transparent',
                      border: 'none',
                      color: webTheme.colors.error['600'],
                      cursor: 'pointer',
                      borderRadius: webTheme.borderRadius.DEFAULT,
                    }}
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Analysis Results Panel */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: webTheme.spacing['4'] }}>
            <h3 style={{ margin: 0, fontSize: webTheme.typography.fontSize.lg, fontWeight: webTheme.typography.fontWeight.semibold }}>
              Voice Analysis Results
            </h3>
            <input
              type="file"
              accept="audio/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  analyzeVoice(file);
                }
              }}
              style={{ display: 'none' }}
              id="voice-analysis-upload"
            />
            <label
              htmlFor="voice-analysis-upload"
              style={{
                padding: `${webTheme.spacing['2']} ${webTheme.spacing['4']}`,
                backgroundColor: webTheme.colors.success['600'],
                color: 'white',
                border: 'none',
                borderRadius: webTheme.borderRadius.DEFAULT,
                fontSize: webTheme.typography.fontSize.sm,
                cursor: 'pointer',
              }}
            >
              {isAnalyzing ? 'Analyzing...' : '🎤 Analyze Voice'}
            </label>
          </div>

          <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
            {analysisResults.map((result) => (
              <div
                key={result.analysis_id}
                style={{
                  padding: webTheme.spacing['4'],
                  marginBottom: webTheme.spacing['4'],
                  backgroundColor: webTheme.colors.background.secondary,
                  borderRadius: webTheme.borderRadius.lg,
                  border: `1px solid ${webTheme.colors.border.light}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: webTheme.spacing['3'] }}>
                  <div style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                    {new Date(result.timestamp).toLocaleString()}
                  </div>
                  <div style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                    {result.audio_duration.toFixed(1)}s • {result.processing_time_ms}ms
                  </div>
                </div>

                {result.results.emotion && renderEmotionVisualization(result.results.emotion)}
                {result.results.stress && renderStressAnalysis(result.results.stress)}
                
                {result.results.identification && (
                  <div>
                    <h4 style={{ margin: `0 0 ${webTheme.spacing['2']} 0`, fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
                      Speaker Identification
                    </h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: webTheme.spacing['4'] }}>
                      <div>
                        <span style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                          Identified Speaker
                        </span>
                        <div style={{ fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
                          {result.results.identification.identified_speaker || 'Unknown'}
                        </div>
                      </div>
                      <div>
                        <span style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary }}>
                          Confidence
                        </span>
                        <div style={{ fontSize: webTheme.typography.fontSize.base, fontWeight: webTheme.typography.fontWeight.medium }}>
                          {(result.results.identification.confidence * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Enrollment Dialog */}
      {showEnrollmentDialog && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: webTheme.colors.background.primary,
            padding: webTheme.spacing['6'],
            borderRadius: webTheme.borderRadius.lg,
            maxWidth: '500px',
            width: '90%',
          }}>
            <h3 style={{ margin: `0 0 ${webTheme.spacing['4']} 0`, fontSize: webTheme.typography.fontSize.lg, fontWeight: webTheme.typography.fontWeight.semibold }}>
              Enroll New Speaker
            </h3>
            
            <div style={{ marginBottom: webTheme.spacing['4'] }}>
              <label style={{ display: 'block', marginBottom: webTheme.spacing['2'], fontSize: webTheme.typography.fontSize.sm, fontWeight: webTheme.typography.fontWeight.medium }}>
                Speaker Name
              </label>
              <input
                type="text"
                value={enrollmentData.name}
                onChange={(e) => setEnrollmentData(prev => ({ ...prev, name: e.target.value }))}
                style={{
                  width: '100%',
                  padding: webTheme.spacing['3'],
                  border: `1px solid ${webTheme.colors.border.DEFAULT}`,
                  borderRadius: webTheme.borderRadius.DEFAULT,
                  fontSize: webTheme.typography.fontSize.base,
                }}
                placeholder="Enter speaker name"
              />
            </div>

            <div style={{ marginBottom: webTheme.spacing['4'] }}>
              <label style={{ display: 'block', marginBottom: webTheme.spacing['2'], fontSize: webTheme.typography.fontSize.sm, fontWeight: webTheme.typography.fontWeight.medium }}>
                Voice Samples (3-5 recommended)
              </label>
              <input
                type="file"
                accept="audio/*"
                multiple
                onChange={(e) => {
                  const files = Array.from(e.target.files || []);
                  setEnrollmentData(prev => ({ ...prev, audioFiles: files }));
                }}
                style={{
                  width: '100%',
                  padding: webTheme.spacing['3'],
                  border: `1px solid ${webTheme.colors.border.DEFAULT}`,
                  borderRadius: webTheme.borderRadius.DEFAULT,
                  fontSize: webTheme.typography.fontSize.base,
                }}
              />
              <div style={{ fontSize: webTheme.typography.fontSize.sm, color: webTheme.colors.text.secondary, marginTop: webTheme.spacing['1'] }}>
                {enrollmentData.audioFiles.length} files selected
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: webTheme.spacing['3'] }}>
              <button
                onClick={() => setShowEnrollmentDialog(false)}
                style={{
                  padding: `${webTheme.spacing['2']} ${webTheme.spacing['4']}`,
                  backgroundColor: 'transparent',
                  color: webTheme.colors.text.secondary,
                  border: `1px solid ${webTheme.colors.border.DEFAULT}`,
                  borderRadius: webTheme.borderRadius.DEFAULT,
                  fontSize: webTheme.typography.fontSize.sm,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={enrollSpeaker}
                disabled={!enrollmentData.name || enrollmentData.audioFiles.length === 0 || isLoading}
                style={{
                  padding: `${webTheme.spacing['2']} ${webTheme.spacing['4']}`,
                  backgroundColor: webTheme.colors.primary['600'],
                  color: 'white',
                  border: 'none',
                  borderRadius: webTheme.borderRadius.DEFAULT,
                  fontSize: webTheme.typography.fontSize.sm,
                  cursor: 'pointer',
                  opacity: (!enrollmentData.name || enrollmentData.audioFiles.length === 0 || isLoading) ? 0.5 : 1,
                }}
              >
                {isLoading ? 'Enrolling...' : 'Enroll Speaker'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Hook for voice profiling functionality
 */
export function useVoiceProfiling() {
  const [isProcessing, setIsProcessing] = useState(false);

  const analyzeVoice = useCallback(async (audioFile: File, analysisTypes: string[] = ['emotion', 'identification', 'stress']) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('audio_file', audioFile);
      formData.append('analysis_types', JSON.stringify(analysisTypes));

      const response = await fetch('/api/voice-profiling/analyze', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        return result;
      }
    } catch (error) {
      console.error('Voice analysis failed:', error);
    } finally {
      setIsProcessing(false);
    }
    
    return null;
  }, []);

  const enrollSpeaker = useCallback(async (name: string, audioFiles: File[]) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('name', name);
      
      audioFiles.forEach((file) => {
        formData.append('audio_files', file);
      });

      const response = await fetch('/api/voice-profiling/enroll', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        return result;
      }
    } catch (error) {
      console.error('Speaker enrollment failed:', error);
    } finally {
      setIsProcessing(false);
    }
    
    return null;
  }, []);

  return {
    analyzeVoice,
    enrollSpeaker,
    isProcessing,
  };
}
