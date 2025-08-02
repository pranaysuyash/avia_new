import React, { useState, useRef, useEffect } from 'react';

const VideoPlayer = ({ videoUrl, transcription, onClose }) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [activeSegment, setActiveSegment] = useState(null);
  const [showTranscript, setShowTranscript] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const transcriptRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
      
      // Find active segment
      if (transcription && transcription.segments) {
        const active = transcription.segments.find(
          segment => video.currentTime >= segment.start && video.currentTime <= segment.end
        );
        setActiveSegment(active);
      }
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, [transcription]);

  useEffect(() => {
    // Auto-scroll to active segment
    if (autoScroll && activeSegment && transcriptRef.current) {
      const segmentElement = document.getElementById(`segment-${activeSegment.start}`);
      if (segmentElement) {
        segmentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [activeSegment, autoScroll]);

  const togglePlayPause = () => {
    const video = videoRef.current;
    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (time) => {
    const video = videoRef.current;
    video.currentTime = time;
    setCurrentTime(time);
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    videoRef.current.volume = newVolume;
  };

  const handlePlaybackRateChange = (rate) => {
    setPlaybackRate(rate);
    videoRef.current.playbackRate = rate;
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSegmentClick = (segment) => {
    handleSeek(segment.start);
    setActiveSegment(segment);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex">
      {/* Video Section */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 bg-gray-900">
          <h2 className="text-xl font-semibold text-white">
            Video Player with Synchronized Transcription
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Video Container */}
        <div className="flex-1 relative bg-black flex items-center justify-center">
          <video
            ref={videoRef}
            src={videoUrl}
            className="max-w-full max-h-full"
            onClick={togglePlayPause}
          />
          
          {/* Play/Pause Overlay */}
          <div 
            className="absolute inset-0 flex items-center justify-center pointer-events-none"
            style={{ display: isPlaying ? 'none' : 'flex' }}
          >
            <div className="bg-black bg-opacity-50 rounded-full p-4">
              <svg className="w-16 h-16 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Video Controls */}
        <div className="bg-gray-900 p-4">
          {/* Progress Bar */}
          <div className="mb-4">
            <div className="relative h-2 bg-gray-700 rounded cursor-pointer"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const clickedTime = (x / rect.width) * duration;
                handleSeek(clickedTime);
              }}
            >
              <div 
                className="absolute h-full bg-primary-600 rounded"
                style={{ width: `${(currentTime / duration) * 100}%` }}
              />
              
              {/* Segment Markers */}
              {transcription && transcription.segments && transcription.segments.map((segment, index) => (
                <div
                  key={index}
                  className="absolute top-0 h-full w-px bg-gray-500 opacity-50"
                  style={{ left: `${(segment.start / duration) * 100}%` }}
                />
              ))}
            </div>
          </div>

          {/* Control Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* Play/Pause */}
              <button
                onClick={togglePlayPause}
                className="p-2 hover:bg-gray-800 rounded-lg text-white"
              >
                {isPlaying ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </button>

              {/* Time Display */}
              <span className="text-white text-sm">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>

              {/* Volume Control */}
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={volume}
                  onChange={handleVolumeChange}
                  className="w-20"
                />
              </div>

              {/* Playback Speed */}
              <div className="relative group">
                <button className="px-3 py-1 bg-gray-800 rounded text-white text-sm hover:bg-gray-700">
                  {playbackRate}x
                </button>
                <div className="absolute bottom-full mb-2 hidden group-hover:block bg-gray-800 rounded shadow-lg">
                  {[0.5, 0.75, 1, 1.25, 1.5, 2].map(rate => (
                    <button
                      key={rate}
                      onClick={() => handlePlaybackRateChange(rate)}
                      className="block w-full px-4 py-2 text-white text-sm hover:bg-gray-700"
                    >
                      {rate}x
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Controls */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowTranscript(!showTranscript)}
                className={`px-3 py-1 rounded text-sm ${
                  showTranscript ? 'bg-primary-600 text-white' : 'bg-gray-800 text-gray-300'
                }`}
              >
                Transcript
              </button>
              
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={`px-3 py-1 rounded text-sm ${
                  autoScroll ? 'bg-primary-600 text-white' : 'bg-gray-800 text-gray-300'
                }`}
              >
                Auto-scroll
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Transcript Panel */}
      {showTranscript && (
        <div className="w-96 bg-gray-900 border-l border-gray-800 flex flex-col">
          <div className="p-4 border-b border-gray-800">
            <h3 className="text-lg font-semibold text-white">Transcript</h3>
          </div>
          
          <div ref={transcriptRef} className="flex-1 overflow-y-auto p-4">
            {transcription && transcription.segments ? (
              <div className="space-y-3">
                {transcription.segments.map((segment, index) => (
                  <div
                    key={index}
                    id={`segment-${segment.start}`}
                    onClick={() => handleSegmentClick(segment)}
                    className={`p-3 rounded cursor-pointer transition-all ${
                      activeSegment && activeSegment.start === segment.start
                        ? 'bg-primary-600 bg-opacity-20 border-l-4 border-primary-600'
                        : 'hover:bg-gray-800'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <span className="text-xs text-gray-500">
                        {formatTime(segment.start)} - {formatTime(segment.end)}
                      </span>
                      <span className="text-xs text-gray-500">
                        {segment.speaker}
                      </span>
                    </div>
                    <p className="text-sm text-gray-300">
                      {segment.text}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No transcript available</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;