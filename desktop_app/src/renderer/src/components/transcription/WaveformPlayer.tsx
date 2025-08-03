import React, { useRef, useEffect, useState, useCallback } from 'react';
import { PlayIcon, PauseIcon, SpeakerWaveIcon, SpeakerXMarkIcon } from '@heroicons/react/24/solid';
import '../../styles/audio-player.css';

interface WaveformPlayerProps {
  audioUrl: string;
  isPlaying: boolean;
  onPlayPause: () => void;
}

const WaveformPlayer: React.FC<WaveformPlayerProps> = ({ audioUrl, isPlaying, onPlayPause }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.7);
  const [isMuted, setIsMuted] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, [audioUrl]);

  useEffect(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.play();
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  useEffect(() => {
    // Draw waveform visualization
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw waveform bars
    const barCount = 100;
    const barWidth = canvas.width / barCount;
    const barGap = 2;

    for (let i = 0; i < barCount; i++) {
      const barHeight = Math.random() * canvas.height * 0.8 + canvas.height * 0.1;
      const x = i * barWidth;
      const y = (canvas.height - barHeight) / 2;

      // Color based on playback position
      const isPlayed = currentTime > 0 && (i / barCount) < (currentTime / duration);
      ctx.fillStyle = isPlayed ? '#6366f1' : '#374151';

      ctx.fillRect(x + barGap / 2, y, barWidth - barGap, barHeight);
    }
  }, [currentTime, duration]);

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };


  const handleProgressBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const progressBar = progressBarRef.current;
    const audio = audioRef.current;
    if (!progressBar || !audio || !duration) return;

    const rect = progressBar.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    audio.currentTime = percentage * duration;
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsDragging(true);
    handleProgressBarClick(e);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return;
    const progressBar = progressBarRef.current;
    const audio = audioRef.current;
    if (!progressBar || !audio || !duration) return;

    const rect = progressBar.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    audio.currentTime = percentage * duration;
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging]);

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (newVolume > 0 && isMuted) {
      setIsMuted(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <audio ref={audioRef} src={audioUrl} />
      
      {/* Waveform */}
      <div className="flex-1 relative">
        <canvas
          ref={canvasRef}
          width={800}
          height={150}
          className="w-full h-full"
        />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mt-4">
        <button
          onClick={onPlayPause}
          className="p-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full transition-colors"
        >
          {isPlaying ? (
            <PauseIcon className="h-6 w-6" />
          ) : (
            <PlayIcon className="h-6 w-6" />
          )}
        </button>

        <div className="flex items-center space-x-4 text-sm text-gray-400 flex-1">
          <span className="w-12 text-right">{formatTime(currentTime)}</span>
          <div 
            ref={progressBarRef}
            className="flex-1 h-2 bg-gray-700 rounded-full relative cursor-pointer group"
            onMouseDown={handleMouseDown}
          >
            <div
              className="absolute top-0 left-0 h-full bg-indigo-600 rounded-full pointer-events-none"
              style={{ width: `${(currentTime / duration) * 100}%` }}
            />
            <div
              className="absolute h-4 w-4 bg-white rounded-full shadow-lg -top-1 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity"
              style={{ left: `${(currentTime / duration) * 100}%` }}
            />
          </div>
          <span className="w-12">{formatTime(duration)}</span>
        </div>

        <div className="flex items-center space-x-3">
          {/* Volume Control */}
          <button 
            onClick={toggleMute}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            {isMuted || volume === 0 ? (
              <SpeakerXMarkIcon className="h-5 w-5" />
            ) : (
              <SpeakerWaveIcon className="h-5 w-5" />
            )}
          </button>
          
          <div className="w-24 flex items-center">
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              style={{
                background: `linear-gradient(to right, #6366f1 ${(isMuted ? 0 : volume) * 100}%, #374151 ${(isMuted ? 0 : volume) * 100}%)`
              }}
            />
          </div>

          {/* More Options */}
          <button className="p-2 text-gray-400 hover:text-white transition-colors">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default WaveformPlayer;