import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiMic,
  FiUser,
  FiEdit2,
  FiSave,
  FiDownload,
  FiRefreshCw,
  FiClock,
  FiActivity,
  FiSettings,
  FiPlay,
  FiPause,
  FiSkipBack,
  FiSkipForward,
  FiVolume2,
  FiGitMerge,
  FiTrash2,
} from 'react-icons/fi';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

interface SpeakerSegment {
  start: number;
  end: number;
  speaker: string;
  confidence: number;
  text?: string;
  embedding?: number[];
}

interface SpeakerProfile {
  id: string;
  name: string;
  color: string;
  totalDuration: number;
  segmentCount: number;
  averageConfidence: number;
  voiceCharacteristics?: {
    pitch: number;
    energy: number;
    spectralCentroid: number;
  };
}

interface DiarizationResult {
  speakers: SpeakerProfile[];
  segments: SpeakerSegment[];
  totalDuration: number;
  confidence: number;
  method: string;
}

interface SpeakerDiarizationProps {
  audioUrl?: string;
  transcriptData?: any;
  onSpeakerUpdate?: (speakers: SpeakerProfile[]) => void;
  onSegmentClick?: (segment: SpeakerSegment) => void;
}

const SPEAKER_COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', 
  '#8b5cf6', '#06b6d4', '#f97316', '#84cc16',
  '#ec4899', '#14b8a6', '#f43f5e', '#6366f1'
];

const SpeakerDiarization: React.FC<SpeakerDiarizationProps> = ({
  audioUrl,
  transcriptData,
  onSpeakerUpdate,
  onSegmentClick,
}) => {
  const [diarizationResult, setDiarizationResult] = useState<DiarizationResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedSpeaker, setSelectedSpeaker] = useState<SpeakerProfile | null>(null);
  const [newSpeakerName, setNewSpeakerName] = useState('');
  const [diarizationMethod, setDiarizationMethod] = useState('whisperx');
  const [minSpeakers, setMinSpeakers] = useState(2);
  const [maxSpeakers, setMaxSpeakers] = useState(10);
  const [selectedSegment, setSelectedSegment] = useState<SpeakerSegment | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  const processDiarization = async () => {
    if (!audioUrl) {
      setError('No audio URL provided');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/speaker-diarization/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          audio_url: audioUrl,
          method: diarizationMethod,
          min_speakers: minSpeakers,
          max_speakers: maxSpeakers,
          transcript_data: transcriptData,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process speaker diarization');
      }

      const result = await response.json();
      setDiarizationResult(result);
      onSpeakerUpdate?.(result.speakers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Diarization failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const updateSpeakerName = async (speakerId: string, newName: string) => {
    if (!diarizationResult) return;

    try {
      const response = await fetch('http://localhost:8000/api/speaker-diarization/update-speaker', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          speaker_id: speakerId,
          new_name: newName,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update speaker name');
      }

      // Update local state
      const updatedResult = {
        ...diarizationResult,
        speakers: diarizationResult.speakers.map(speaker =>
          speaker.id === speakerId ? { ...speaker, name: newName } : speaker
        ),
        segments: diarizationResult.segments.map(segment =>
          segment.speaker === speakerId ? { ...segment, speaker: newName } : segment
        ),
      };

      setDiarizationResult(updatedResult);
      onSpeakerUpdate?.(updatedResult.speakers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update speaker');
    }
  };

  const mergeSpeakers = async (speaker1Id: string, speaker2Id: string) => {
    if (!diarizationResult) return;

    try {
      const response = await fetch('http://localhost:8000/api/speaker-diarization/merge-speakers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          speaker1_id: speaker1Id,
          speaker2_id: speaker2Id,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to merge speakers');
      }

      const result = await response.json();
      setDiarizationResult(result);
      onSpeakerUpdate?.(result.speakers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to merge speakers');
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  const getSpeakerStats = () => {
    if (!diarizationResult) return [];

    return diarizationResult.speakers.map(speaker => ({
      name: speaker.name,
      duration: speaker.totalDuration,
      percentage: (speaker.totalDuration / diarizationResult.totalDuration) * 100,
      segments: speaker.segmentCount,
      color: speaker.color,
    }));
  };

  const handleEditSpeaker = (speaker: SpeakerProfile) => {
    setSelectedSpeaker(speaker);
    setNewSpeakerName(speaker.name);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = () => {
    if (selectedSpeaker && newSpeakerName.trim()) {
      updateSpeakerName(selectedSpeaker.id, newSpeakerName.trim());
      setEditDialogOpen(false);
      setSelectedSpeaker(null);
      setNewSpeakerName('');
    }
  };

  const exportDiarization = () => {
    if (!diarizationResult) return;

    const exportData = {
      speakers: diarizationResult.speakers,
      segments: diarizationResult.segments,
      metadata: {
        totalDuration: diarizationResult.totalDuration,
        confidence: diarizationResult.confidence,
        method: diarizationResult.method,
        exportedAt: new Date().toISOString(),
      },
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `speaker-diarization-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!timelineRef.current || !diarizationResult || !audioRef.current) return;

    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const time = percentage * diarizationResult.totalDuration;

    audioRef.current.currentTime = time;
    setCurrentTime(time);
  };

  const handleSegmentClick = (segment: SpeakerSegment) => {
    setSelectedSegment(segment);
    if (audioRef.current) {
      audioRef.current.currentTime = segment.start;
      setCurrentTime(segment.start);
    }
    onSegmentClick?.(segment);
  };

  const togglePlayPause = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const skipBackward = () => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 10);
  };

  const skipForward = () => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.min(
      audioRef.current.duration,
      audioRef.current.currentTime + 10
    );
  };

  useEffect(() => {
    if (audioUrl && !diarizationResult && !isProcessing) {
      processDiarization();
    }
  }, [audioUrl]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
    };
  }, []);

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 m-4"
      >
        <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
          Speaker Diarization Failed
        </h3>
        <p className="text-red-600 dark:text-red-300">{error}</p>
        <button
          onClick={processDiarization}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
        >
          Retry
        </button>
      </motion.div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <FiMic className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Speaker Diarization
          </h2>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={processDiarization}
            disabled={isProcessing}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
          >
            <FiRefreshCw className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />
            <span>Reprocess</span>
          </button>
          {diarizationResult && (
            <button
              onClick={exportDiarization}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <FiDownload className="w-4 h-4" />
              <span>Export</span>
            </button>
          )}
        </div>
      </div>

      {/* Audio Player */}
      {audioUrl && (
        <audio ref={audioRef} src={audioUrl} className="hidden" />
      )}

      {/* Processing Status */}
      <AnimatePresence>
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6"
          >
            <div className="flex items-center space-x-3 mb-3">
              <FiActivity className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-pulse" />
              <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200">
                Processing Speaker Diarization...
              </h3>
            </div>
            <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
              <div className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
            </div>
            <p className="text-sm text-blue-600 dark:text-blue-300 mt-2">
              Analyzing audio for speaker identification using {diarizationMethod}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Configuration */}
      {!diarizationResult && !isProcessing && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Diarization Settings
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Method
              </label>
              <select
                value={diarizationMethod}
                onChange={(e) => setDiarizationMethod(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="whisperx">WhisperX (Recommended)</option>
                <option value="pyannote">PyAnnote</option>
                <option value="resemblyzer">Resemblyzer</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Min Speakers
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={minSpeakers}
                onChange={(e) => setMinSpeakers(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Max Speakers
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={maxSpeakers}
                onChange={(e) => setMaxSpeakers(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <button
            onClick={processDiarization}
            disabled={!audioUrl}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Diarization
          </button>
        </motion.div>
      )}

      {/* Results */}
      {diarizationResult && (
        <>
          {/* Overview Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Speakers Detected</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {diarizationResult.speakers.length}
                  </p>
                </div>
                <FiUser className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Duration</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatDuration(diarizationResult.totalDuration)}
                  </p>
                </div>
                <FiClock className="w-8 h-8 text-green-600 dark:text-green-400" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Segments</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {diarizationResult.segments.length}
                  </p>
                </div>
                <FiActivity className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Confidence</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {(diarizationResult.confidence * 100).toFixed(1)}%
                  </p>
                </div>
                <FiSettings className="w-8 h-8 text-orange-600 dark:text-orange-400" />
              </div>
            </motion.div>
          </div>

          {/* Audio Controls */}
          {audioUrl && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-4"
            >
              <div className="flex items-center space-x-4">
                <button
                  onClick={togglePlayPause}
                  className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
                >
                  {isPlaying ? <FiPause className="w-5 h-5" /> : <FiPlay className="w-5 h-5" />}
                </button>
                <button
                  onClick={skipBackward}
                  className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  <FiSkipBack className="w-5 h-5" />
                </button>
                <button
                  onClick={skipForward}
                  className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  <FiSkipForward className="w-5 h-5" />
                </button>
                <div className="flex-1 flex items-center space-x-3">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {formatTime(currentTime)}
                  </span>
                  <div className="flex-1 h-1 bg-gray-200 dark:bg-gray-700 rounded-full">
                    <div
                      className="h-full bg-blue-600 rounded-full transition-all"
                      style={{
                        width: `${(currentTime / diarizationResult.totalDuration) * 100}%`,
                      }}
                    />
                  </div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {formatTime(diarizationResult.totalDuration)}
                  </span>
                </div>
                <FiVolume2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </div>
            </motion.div>
          )}

          {/* Speaker Timeline */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Speaker Timeline
            </h3>
            <div
              ref={timelineRef}
              onClick={handleTimelineClick}
              className="relative h-24 bg-gray-100 dark:bg-gray-700 rounded-lg cursor-pointer overflow-hidden"
            >
              {diarizationResult.segments.map((segment, index) => {
                const speaker = diarizationResult.speakers.find(s => s.name === segment.speaker);
                const left = (segment.start / diarizationResult.totalDuration) * 100;
                const width = ((segment.end - segment.start) / diarizationResult.totalDuration) * 100;

                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scaleX: 0 }}
                    animate={{ opacity: 1, scaleX: 1 }}
                    transition={{ delay: index * 0.01 }}
                    className="absolute h-full hover:opacity-80 transition-opacity"
                    style={{
                      left: `${left}%`,
                      width: `${width}%`,
                      backgroundColor: speaker?.color || '#gray',
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSegmentClick(segment);
                    }}
                    title={`${segment.speaker}: ${formatTime(segment.start)} - ${formatTime(segment.end)}`}
                  />
                );
              })}
              {/* Current time indicator */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
                style={{
                  left: `${(currentTime / diarizationResult.totalDuration) * 100}%`,
                }}
              />
            </div>
            <div className="flex justify-between mt-2">
              <span className="text-xs text-gray-600 dark:text-gray-400">0:00</span>
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {formatTime(diarizationResult.totalDuration)}
              </span>
            </div>
          </motion.div>

          {/* Speaker Statistics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Speaking Time Distribution
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={getSpeakerStats()}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="duration"
                    nameKey="name"
                  >
                    {getSpeakerStats().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip
                    formatter={(value: number) => [formatDuration(value), 'Duration']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Segment Count by Speaker
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={getSpeakerStats()}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="name" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <RechartsTooltip />
                  <Bar dataKey="segments" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </motion.div>
          </div>

          {/* Speaker Profiles */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Speaker Profiles
            </h3>
            <div className="space-y-4">
              {diarizationResult.speakers.map((speaker, index) => (
                <motion.div
                  key={speaker.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <div
                      className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold"
                      style={{ backgroundColor: speaker.color }}
                    >
                      {speaker.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">
                        {speaker.name}
                      </h4>
                      <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                        <span>Duration: {formatDuration(speaker.totalDuration)}</span>
                        <span>Segments: {speaker.segmentCount}</span>
                        <span>Confidence: {(speaker.averageConfidence * 100).toFixed(1)}%</span>
                      </div>
                      {speaker.voiceCharacteristics && (
                        <div className="flex items-center space-x-3 mt-1">
                          <span className="text-xs bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded">
                            Pitch: {speaker.voiceCharacteristics.pitch.toFixed(1)}Hz
                          </span>
                          <span className="text-xs bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded">
                            Energy: {speaker.voiceCharacteristics.energy.toFixed(2)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleEditSpeaker(speaker)}
                    className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    <FiEdit2 className="w-5 h-5" />
                  </button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </>
      )}

      {/* Edit Speaker Dialog */}
      <AnimatePresence>
        {editDialogOpen && selectedSpeaker && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={() => setEditDialogOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Edit Speaker
              </h3>
              <input
                type="text"
                value={newSpeakerName}
                onChange={(e) => setNewSpeakerName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                placeholder="Speaker name"
                autoFocus
              />
              <div className="flex justify-end space-x-3 mt-4">
                <button
                  onClick={() => setEditDialogOpen(false)}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Save
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SpeakerDiarization;