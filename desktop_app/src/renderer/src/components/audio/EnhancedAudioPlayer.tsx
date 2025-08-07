/**
 * Enhanced Audio Player Component for Electron Desktop App
 * Provides programmatic control with native file system integration
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { formatTime } from '../../utils/timeUtils';

interface EnhancedAudioPlayerProps {
  audioPath: string; // Can be file:// URL or local path
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
  setVolume: (volume: number) => void;
  setPlaybackRate: (rate: number) => void;
}

export const EnhancedAudioPlayer = React.forwardRef<AudioPlayerRef, EnhancedAudioPlayerProps>(
  ({ audioPath, initialTime = 0, onTimeUpdate, onPlay, onPause, className }, ref) => {
    const audioRef = useRef<HTMLAudioElement>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [volume, setVolume] = useState(1);
    const [playbackRate, setPlaybackRate] = useState(1);
    const [audioUrl, setAudioUrl] = useState<string>('');

    // Convert local path to file URL if needed
    useEffect(() => {
      if (audioPath.startsWith('file://') || audioPath.startsWith('http')) {
        setAudioUrl(audioPath);
      } else {
        // For Electron, we can use file protocol
        setAudioUrl(`file://${audioPath}`);
      }
    }, [audioPath]);

    // Expose methods via ref
    React.useImperativeHandle(ref, () => ({
      jumpToTime: (time: number, autoPlay = true) => {
        if (audioRef.current) {
          audioRef.current.currentTime = time;
          if (autoPlay) {
            audioRef.current.play().catch(err => {
              console.error('Failed to play audio:', err);
            });
          }
        }
      },
      play: () => {
        audioRef.current?.play().catch(err => {
          console.error('Failed to play audio:', err);
        });
      },
      pause: () => audioRef.current?.pause(),
      getCurrentTime: () => audioRef.current?.currentTime || 0,
      getDuration: () => audioRef.current?.duration || 0,
      isPlaying: () => !audioRef.current?.paused || false,
      setVolume: (vol: number) => {
        if (audioRef.current) {
          audioRef.current.volume = Math.max(0, Math.min(1, vol));
          setVolume(vol);
        }
      },
      setPlaybackRate: (rate: number) => {
        if (audioRef.current) {
          audioRef.current.playbackRate = rate;
          setPlaybackRate(rate);
        }
      },
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

      const handleError = (e: Event) => {
        console.error('Audio loading error:', e);
        setIsLoading(false);
      };

      audio.addEventListener('loadedmetadata', handleLoadedMetadata);
      audio.addEventListener('error', handleError);
      
      return () => {
        audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
        audio.removeEventListener('error', handleError);
      };
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

    // Keyboard shortcuts
    useEffect(() => {
      const handleKeyPress = (e: KeyboardEvent) => {
        if (!audioRef.current) return;
        
        switch (e.key) {
          case ' ':
            e.preventDefault();
            if (audioRef.current.paused) {
              audioRef.current.play();
            } else {
              audioRef.current.pause();
            }
            break;
          case 'ArrowLeft':
            e.preventDefault();
            audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 5);
            break;
          case 'ArrowRight':
            e.preventDefault();
            audioRef.current.currentTime = Math.min(
              audioRef.current.duration,
              audioRef.current.currentTime + 5
            );
            break;
        }
      };

      window.addEventListener('keydown', handleKeyPress);
      return () => window.removeEventListener('keydown', handleKeyPress);
    }, []);

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
        
        <div className="audio-controls mt-2">
          <div className="flex items-center justify-between">
            <div className="audio-info text-sm text-gray-600">
              <span className="current-time">{formatTime(currentTime)}</span>
              <span className="mx-2">/</span>
              <span className="duration">{formatTime(duration)}</span>
            </div>

            <div className="flex items-center space-x-4">
              {/* Volume Control */}
              <div className="flex items-center">
                <span className="text-sm text-gray-600 mr-2">Volume:</span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={volume}
                  onChange={(e) => {
                    const vol = parseFloat(e.target.value);
                    if (audioRef.current) {
                      audioRef.current.volume = vol;
                      setVolume(vol);
                    }
                  }}
                  className="w-20"
                />
              </div>

              {/* Playback Speed */}
              <div className="flex items-center">
                <span className="text-sm text-gray-600 mr-2">Speed:</span>
                <select
                  value={playbackRate}
                  onChange={(e) => {
                    const rate = parseFloat(e.target.value);
                    if (audioRef.current) {
                      audioRef.current.playbackRate = rate;
                      setPlaybackRate(rate);
                    }
                  }}
                  className="text-sm border rounded px-2 py-1"
                >
                  <option value="0.5">0.5x</option>
                  <option value="0.75">0.75x</option>
                  <option value="1">1x</option>
                  <option value="1.25">1.25x</option>
                  <option value="1.5">1.5x</option>
                  <option value="2">2x</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {isLoading && (
          <div className="loading-indicator text-center text-gray-500 mt-2">
            Loading audio...
          </div>
        )}

        <div className="keyboard-shortcuts text-xs text-gray-500 mt-2">
          Keyboard shortcuts: Space (play/pause), ← → (skip 5s)
        </div>
      </div>
    );
  }
);

EnhancedAudioPlayer.displayName = 'EnhancedAudioPlayer';

// Utility hook for managing audio player in Electron
export const useElectronAudioPlayer = () => {
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

  const setVolume = useCallback((volume: number) => {
    playerRef.current?.setVolume(volume);
  }, []);

  const setPlaybackRate = useCallback((rate: number) => {
    playerRef.current?.setPlaybackRate(rate);
  }, []);

  return {
    playerRef,
    jumpToTime,
    play,
    pause,
    setVolume,
    setPlaybackRate,
  };
};