import React, { useRef, useState, useEffect } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  Settings,
  Download,
  Scissors,
  Subtitles,
  Camera,
  ChevronRight
} from 'lucide-react';

interface VideoPlayerProps {
  src: string;
  poster?: string;
  transcriptionSegments?: TranscriptionSegment[];
  onTimeUpdate?: (currentTime: number) => void;
  onSegmentClick?: (segment: TranscriptionSegment) => void;
}

interface TranscriptionSegment {
  id: string;
  start: number;
  end: number;
  text: string;
  speaker?: string;
  confidence?: number;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  src,
  poster,
  transcriptionSegments = [],
  onTimeUpdate,
  onSegmentClick
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showTranscript, setShowTranscript] = useState(true);
  const [activeSegment, setActiveSegment] = useState<TranscriptionSegment | null>(null);
  const [showTrimDialog, setShowTrimDialog] = useState(false);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const updateTime = () => {
      setCurrentTime(video.currentTime);
      if (onTimeUpdate) {
        onTimeUpdate(video.currentTime);
      }
      
      // Find active segment
      const segment = transcriptionSegments.find(
        seg => video.currentTime >= seg.start && video.currentTime <= seg.end
      );
      setActiveSegment(segment || null);
    };

    const updateDuration = () => {
      setDuration(video.duration);
      setTrimEnd(video.duration);
    };

    video.addEventListener('timeupdate', updateTime);
    video.addEventListener('loadedmetadata', updateDuration);

    return () => {
      video.removeEventListener('timeupdate', updateTime);
      video.removeEventListener('loadedmetadata', updateDuration);
    };
  }, [transcriptionSegments, onTimeUpdate]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const skip = (seconds: number) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime += seconds;
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value);
    setCurrentTime(newTime);
    if (videoRef.current) {
      videoRef.current.currentTime = newTime;
    }
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;

    if (!isFullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    setIsFullscreen(!isFullscreen);
  };

  const changePlaybackRate = (rate: number) => {
    if (!videoRef.current) return;
    videoRef.current.playbackRate = rate;
    setPlaybackRate(rate);
    setShowSettings(false);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSegmentClick = (segment: TranscriptionSegment) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = segment.start;
    if (onSegmentClick) {
      onSegmentClick(segment);
    }
  };

  const downloadVideo = () => {
    const a = document.createElement('a');
    a.href = src;
    a.download = 'video.mp4';
    a.click();
  };

  const takeScreenshot = () => {
    if (!videoRef.current) return;
    
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.drawImage(videoRef.current, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `screenshot_${formatTime(currentTime)}.png`;
      a.click();
      URL.revokeObjectURL(url);
    });
  };

  const handleTrim = () => {
    // In a real implementation, this would send trim parameters to backend
    console.log('Trim video from', formatTime(trimStart), 'to', formatTime(trimEnd));
    setShowTrimDialog(false);
  };

  return (
    <div className="relative bg-black rounded-lg overflow-hidden" ref={containerRef}>
      <div className="relative">
        <video
          ref={videoRef}
          src={src}
          poster={poster}
          className="w-full h-full"
          onClick={togglePlay}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        />

        {/* Active Transcript Overlay */}
        {showTranscript && activeSegment && (
          <div className="absolute bottom-20 left-0 right-0 px-4">
            <div className="bg-black/80 backdrop-blur rounded-lg p-3 text-center">
              {activeSegment.speaker && (
                <div className="text-sm text-gray-400 mb-1">{activeSegment.speaker}</div>
              )}
              <div className="text-white">{activeSegment.text}</div>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-4 transition-opacity ${showControls ? 'opacity-100' : 'opacity-0'}`}>
          {/* Progress Bar */}
          <div className="mb-4">
            <input
              type="range"
              min="0"
              max={duration || 0}
              value={currentTime}
              onChange={handleSeek}
              className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(currentTime / duration) * 100}%, #4b5563 ${(currentTime / duration) * 100}%, #4b5563 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Control Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button onClick={togglePlay} className="text-white hover:text-blue-400 transition">
                {isPlaying ? <Pause className="w-8 h-8" /> : <Play className="w-8 h-8" />}
              </button>
              
              <button onClick={() => skip(-10)} className="text-white hover:text-blue-400 transition">
                <SkipBack className="w-6 h-6" />
              </button>
              
              <button onClick={() => skip(10)} className="text-white hover:text-blue-400 transition">
                <SkipForward className="w-6 h-6" />
              </button>

              <div className="flex items-center gap-2">
                <button onClick={toggleMute} className="text-white hover:text-blue-400 transition">
                  {isMuted ? <VolumeX className="w-6 h-6" /> : <Volume2 className="w-6 h-6" />}
                </button>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={isMuted ? 0 : volume}
                  onChange={handleVolumeChange}
                  className="w-20 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowTranscript(!showTranscript)}
                className={`text-white hover:text-blue-400 transition ${showTranscript ? 'text-blue-400' : ''}`}
              >
                <Subtitles className="w-6 h-6" />
              </button>

              <button onClick={takeScreenshot} className="text-white hover:text-blue-400 transition">
                <Camera className="w-6 h-6" />
              </button>

              <button onClick={() => setShowTrimDialog(true)} className="text-white hover:text-blue-400 transition">
                <Scissors className="w-6 h-6" />
              </button>

              <button onClick={downloadVideo} className="text-white hover:text-blue-400 transition">
                <Download className="w-6 h-6" />
              </button>

              <div className="relative">
                <button onClick={() => setShowSettings(!showSettings)} className="text-white hover:text-blue-400 transition">
                  <Settings className="w-6 h-6" />
                </button>
                
                {showSettings && (
                  <div className="absolute bottom-full right-0 mb-2 bg-gray-900 rounded-lg shadow-lg p-2 min-w-[120px]">
                    <div className="text-sm text-gray-400 mb-2">Playback Speed</div>
                    {[0.5, 0.75, 1, 1.25, 1.5, 2].map(rate => (
                      <button
                        key={rate}
                        onClick={() => changePlaybackRate(rate)}
                        className={`block w-full text-left px-2 py-1 rounded hover:bg-gray-800 ${playbackRate === rate ? 'text-blue-400' : 'text-white'}`}
                      >
                        {rate}x
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button onClick={toggleFullscreen} className="text-white hover:text-blue-400 transition">
                {isFullscreen ? <Minimize className="w-6 h-6" /> : <Maximize className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Transcript Sidebar */}
      {showTranscript && transcriptionSegments.length > 0 && (
        <div className="absolute top-0 right-0 w-80 h-full bg-gray-900/95 backdrop-blur overflow-y-auto">
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-4">Transcript</h3>
            <div className="space-y-2">
              {transcriptionSegments.map(segment => (
                <button
                  key={segment.id}
                  onClick={() => handleSegmentClick(segment)}
                  className={`w-full text-left p-3 rounded-lg transition ${
                    activeSegment?.id === segment.id 
                      ? 'bg-blue-600/20 border border-blue-600' 
                      : 'hover:bg-gray-800'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 mt-0.5 text-gray-400" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-400">{formatTime(segment.start)}</span>
                        {segment.speaker && (
                          <span className="text-xs text-blue-400">{segment.speaker}</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-300">{segment.text}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Trim Dialog */}
      {showTrimDialog && (
        <div className="absolute inset-0 bg-black/80 backdrop-blur flex items-center justify-center">
          <div className="bg-gray-900 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Trim Video</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Start Time</label>
                <input
                  type="range"
                  min="0"
                  max={duration}
                  value={trimStart}
                  onChange={(e) => setTrimStart(parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="text-sm text-gray-400 mt-1">{formatTime(trimStart)}</div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">End Time</label>
                <input
                  type="range"
                  min="0"
                  max={duration}
                  value={trimEnd}
                  onChange={(e) => setTrimEnd(parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="text-sm text-gray-400 mt-1">{formatTime(trimEnd)}</div>
              </div>

              <div className="text-sm text-gray-400">
                Duration: {formatTime(trimEnd - trimStart)}
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleTrim}
                className="flex-1 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Trim Video
              </button>
              <button
                onClick={() => setShowTrimDialog(false)}
                className="flex-1 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;