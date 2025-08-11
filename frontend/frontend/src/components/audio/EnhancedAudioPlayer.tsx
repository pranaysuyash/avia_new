/**
 * Enhanced Audio Player Component for React Web
 * Provides programmatic control and jump-to-time functionality
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { formatTime } from '../../utils/timeUtils';

interface EnhancedAudioPlayerProps {
  audioUrl: string;
  initialTime?: number;
  onTimeUpdate?: (currentTime: number, duration: number) => void;
  onPlay?: () => void;
  onPause?: () => void;
  className?: string;
}

export interface AudioPlayerRef {
  jumpToTime: (time: number, autoPlay?: boolean) => void;
  play: () => void;
  pause: () => void;
  getCurrentTime: () => number;
  getDuration: () => number;
  isPlaying: () => boolean;
}

export const EnhancedAudioPlayer = React.forwardRef<AudioPlayerRef, EnhancedAudioPlayerProps>(
  ({ audioUrl, initialTime = 0, onTimeUpdate, onPlay, onPause, className }, ref) => {
    const audioRef = useRef<HTMLAudioElement>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    // Expose methods via ref
    React.useImperativeHandle(ref, () => ({
      jumpToTime: (time: number, autoPlay = true) => {
        if (audioRef.current) {
          audioRef.current.currentTime = time;
          if (autoPlay) {
            audioRef.current.play();
          }
        }
      },
      play: () => audioRef.current?.play(),
      pause: () => audioRef.current?.pause(),
      getCurrentTime: () => audioRef.current?.currentTime || 0,
      getDuration: () => audioRef.current?.duration || 0,
      isPlaying: () => !audioRef.current?.paused || false,
    }));

    // Set initial time when metadata loads
    useEffect(() => {
      const audio = audioRef.current;
      if (!audio) return;

      const handleLoadedMetadata = () => {
        setDuration(audio.duration);
        if (initialTime > 0) {
          audio.currentTime = initialTime;
        }
        setIsLoading(false);
      };

      audio.addEventListener('loadedmetadata', handleLoadedMetadata);
      return () => audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
    }, [initialTime]);

    // Handle time updates
    const handleTimeUpdate = useCallback(() => {
      const audio = audioRef.current;
      if (!audio) return;

      setCurrentTime(audio.currentTime);
      onTimeUpdate?.(audio.currentTime, audio.duration);
    }, [onTimeUpdate]);

    // Handle play/pause events
    const handlePlay = useCallback(() => {
      setIsPlaying(true);
      onPlay?.();
    }, [onPlay]);

    const handlePause = useCallback(() => {
      setIsPlaying(false);
      onPause?.();
    }, [onPause]);

    return (
      <div className={`enhanced-audio-player ${className || ''}`}>
        <audio
          ref={audioRef}
          src={audioUrl}
          onTimeUpdate={handleTimeUpdate}
          onPlay={handlePlay}
          onPause={handlePause}
          controls
          className="w-full"
          preload="metadata"
        />
        
        <div className="audio-info flex justify-between text-sm text-gray-600 mt-2">
          <span className="current-time">{formatTime(currentTime)}</span>
          <span className="duration">{formatTime(duration)}</span>
        </div>

        {isLoading && (
          <div className="loading-indicator text-center text-gray-500 mt-2">
            Loading audio...
          </div>
        )}
      </div>
    );
  }
);

EnhancedAudioPlayer.displayName = 'EnhancedAudioPlayer';

// Utility hook for managing audio player
export const useAudioPlayer = () => {
  const playerRef = useRef<AudioPlayerRef>(null);

  const jumpToTime = useCallback((time: number, autoPlay = true) => {
    playerRef.current?.jumpToTime(time, autoPlay);
  }, []);

  const play = useCallback(() => {
    playerRef.current?.play();
  }, []);

  const pause = useCallback(() => {
    playerRef.current?.pause();
  }, []);

  return {
    playerRef,
    jumpToTime,
    play,
    pause,
  };
};