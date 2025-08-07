/**
 * Enhanced Audio Player Component for React Native Mobile App
 * Uses react-native-track-player for background playback support
 */

import React, { useEffect, useState, useCallback, useImperativeHandle, forwardRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Slider,
  ActivityIndicator,
  Platform,
} from 'react-native';
import TrackPlayer, {
  State,
  usePlaybackState,
  useProgress,
  Capability,
  Event,
  useTrackPlayerEvents,
} from 'react-native-track-player';
import { Ionicons } from '@expo/vector-icons';

interface EnhancedAudioPlayerProps {
  audioUrl: string;
  title?: string;
  artist?: string;
  initialTime?: number;
  onTimeUpdate?: (currentTime: number, duration: number) => void;
  onPlay?: () => void;
  onPause?: () => void;
}

export interface AudioPlayerRef {
  jumpToTime: (time: number, autoPlay?: boolean) => void;
  play: () => void;
  pause: () => void;
  getCurrentTime: () => number;
  getDuration: () => number;
  isPlaying: () => boolean;
}

// Setup TrackPlayer
export const setupPlayer = async () => {
  try {
    await TrackPlayer.setupPlayer({});
    await TrackPlayer.updateOptions({
      capabilities: [
        Capability.Play,
        Capability.Pause,
        Capability.SkipToNext,
        Capability.SkipToPrevious,
        Capability.Stop,
        Capability.SeekTo,
      ],
      compactCapabilities: [Capability.Play, Capability.Pause],
    });
  } catch (error) {
    console.error('Error setting up TrackPlayer:', error);
  }
};

export const EnhancedAudioPlayer = forwardRef<AudioPlayerRef, EnhancedAudioPlayerProps>(
  ({ audioUrl, title = 'Audio', artist = 'Unknown', initialTime = 0, onTimeUpdate, onPlay, onPause }, ref) => {
    const playbackState = usePlaybackState();
    const progress = useProgress();
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Initialize track
    useEffect(() => {
      const initializeTrack = async () => {
        try {
          setIsLoading(true);
          setError(null);

          // Clear any existing queue
          await TrackPlayer.reset();

          // Add track
          await TrackPlayer.add({
            id: '1',
            url: audioUrl,
            title: title,
            artist: artist,
          });

          // Seek to initial time if provided
          if (initialTime > 0) {
            await TrackPlayer.seekTo(initialTime);
          }

          setIsLoading(false);
        } catch (err) {
          console.error('Error initializing track:', err);
          setError('Failed to load audio');
          setIsLoading(false);
        }
      };

      initializeTrack();

      return () => {
        TrackPlayer.reset();
      };
    }, [audioUrl, title, artist, initialTime]);

    // Track time updates
    useEffect(() => {
      if (progress.position && progress.duration) {
        onTimeUpdate?.(progress.position, progress.duration);
      }
    }, [progress.position, progress.duration, onTimeUpdate]);

    // Track player events
    useTrackPlayerEvents([Event.PlaybackState], (event) => {
      if (event.state === State.Playing) {
        onPlay?.();
      } else if (event.state === State.Paused) {
        onPause?.();
      }
    });

    // Expose methods via ref
    useImperativeHandle(ref, () => ({
      jumpToTime: async (time: number, autoPlay = true) => {
        await TrackPlayer.seekTo(time);
        if (autoPlay) {
          await TrackPlayer.play();
        }
      },
      play: async () => await TrackPlayer.play(),
      pause: async () => await TrackPlayer.pause(),
      getCurrentTime: () => progress.position,
      getDuration: () => progress.duration,
      isPlaying: () => playbackState === State.Playing,
    }));

    const handlePlayPause = async () => {
      if (playbackState === State.Playing) {
        await TrackPlayer.pause();
      } else {
        await TrackPlayer.play();
      }
    };

    const handleSeek = async (value: number) => {
      await TrackPlayer.seekTo(value);
    };

    const formatTime = (seconds: number): string => {
      if (isNaN(seconds) || seconds < 0) return '00:00';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    if (isLoading) {
      return (
        <View style={styles.container}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading audio...</Text>
        </View>
      );
    }

    if (error) {
      return (
        <View style={styles.container}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      );
    }

    const isPlaying = playbackState === State.Playing;
    const isBuffering = playbackState === State.Buffering || playbackState === State.Loading;

    return (
      <View style={styles.container}>
        {/* Track Info */}
        <View style={styles.trackInfo}>
          <Text style={styles.title} numberOfLines={1}>{title}</Text>
          <Text style={styles.artist} numberOfLines={1}>{artist}</Text>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <Text style={styles.timeText}>{formatTime(progress.position)}</Text>
          <Slider
            style={styles.slider}
            minimumValue={0}
            maximumValue={progress.duration || 1}
            value={progress.position}
            onSlidingComplete={handleSeek}
            minimumTrackTintColor="#007AFF"
            maximumTrackTintColor="#CCCCCC"
            thumbTintColor="#007AFF"
          />
          <Text style={styles.timeText}>{formatTime(progress.duration)}</Text>
        </View>

        {/* Controls */}
        <View style={styles.controls}>
          <TouchableOpacity
            style={styles.controlButton}
            onPress={() => TrackPlayer.seekTo(Math.max(0, progress.position - 10))}
          >
            <Ionicons name="play-back" size={30} color="#007AFF" />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.playButton, isBuffering && styles.disabledButton]}
            onPress={handlePlayPause}
            disabled={isBuffering}
          >
            {isBuffering ? (
              <ActivityIndicator size="small" color="#007AFF" />
            ) : (
              <Ionicons
                name={isPlaying ? 'pause' : 'play'}
                size={40}
                color="#007AFF"
              />
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.controlButton}
            onPress={() => TrackPlayer.seekTo(Math.min(progress.duration, progress.position + 10))}
          >
            <Ionicons name="play-forward" size={30} color="#007AFF" />
          </TouchableOpacity>
        </View>

        {/* Additional Info */}
        <Text style={styles.hint}>Tap ← → to skip 10 seconds</Text>
      </View>
    );
  }
);

EnhancedAudioPlayer.displayName = 'EnhancedAudioPlayer';

// Utility hook for managing audio player
export const useAudioPlayer = () => {
  const [playerRef, setPlayerRef] = useState<AudioPlayerRef | null>(null);

  const jumpToTime = useCallback(async (time: number, autoPlay = true) => {
    if (playerRef) {
      await playerRef.jumpToTime(time, autoPlay);
    }
  }, [playerRef]);

  const play = useCallback(async () => {
    if (playerRef) {
      await playerRef.play();
    }
  }, [playerRef]);

  const pause = useCallback(async () => {
    if (playerRef) {
      await playerRef.pause();
    }
  }, [playerRef]);

  return {
    setPlayerRef,
    jumpToTime,
    play,
    pause,
  };
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  trackInfo: {
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  artist: {
    fontSize: 14,
    color: '#666',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  slider: {
    flex: 1,
    height: 40,
    marginHorizontal: 10,
  },
  timeText: {
    fontSize: 12,
    color: '#666',
    minWidth: 45,
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  controlButton: {
    padding: 10,
    marginHorizontal: 20,
  },
  playButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#F0F0F0',
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 20,
  },
  disabledButton: {
    opacity: 0.5,
  },
  hint: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  errorText: {
    fontSize: 14,
    color: '#FF3B30',
    textAlign: 'center',
  },
});