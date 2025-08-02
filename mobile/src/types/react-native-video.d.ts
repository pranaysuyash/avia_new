declare module 'react-native-video' {
  import { Component } from 'react';
  import { ViewStyle } from 'react-native';

  export interface VideoRef {
    seek(time: number): void;
    presentFullscreenPlayer(): void;
    dismissFullscreenPlayer(): void;
  }

  export interface VideoLoadData {
    duration: number;
    currentTime: number;
    canPlayReverse: boolean;
    canPlayFastForward: boolean;
    canPlaySlowForward: boolean;
    canPlaySlowReverse: boolean;
    canStepBackward: boolean;
    canStepForward: boolean;
    naturalSize: {
      width: number;
      height: number;
      orientation: 'portrait' | 'landscape';
    };
  }

  export interface VideoProgressData {
    currentTime: number;
    playableDuration: number;
    seekableDuration: number;
  }

  export interface VideoProps {
    source: { uri: string } | number;
    style?: ViewStyle;
    controls?: boolean;
    paused?: boolean;
    volume?: number;
    rate?: number;
    resizeMode?: 'contain' | 'cover' | 'stretch';
    onLoad?: (data: VideoLoadData) => void;
    onProgress?: (data: VideoProgressData) => void;
    onEnd?: () => void;
    onError?: (error: any) => void;
  }

  export default class Video extends Component<VideoProps> {}
}