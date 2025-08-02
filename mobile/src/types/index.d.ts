declare module 'react-native-document-picker' {
  export interface DocumentPickerResponse {
    uri: string;
    type: string;
    name: string;
    size: number;
  }

  export interface DocumentPickerOptions {
    type: string[];
  }

  export const types: {
    allFiles: string;
    images: string;
    plainText: string;
    audio: string;
    pdf: string;
    video: string;
  };

  export function pick(options: DocumentPickerOptions): Promise<DocumentPickerResponse[]>;
  export function isCancel(error: any): boolean;
}

declare module 'react-native-fs' {
  export const DocumentDirectoryPath: string;
  export const CachesDirectoryPath: string;
  export const ExternalDirectoryPath: string;
  export const ExternalStorageDirectoryPath: string;
  export const TemporaryDirectoryPath: string;
  export const LibraryDirectoryPath: string;
  export const PicturesDirectoryPath: string;

  export function writeFile(filepath: string, contents: string, encoding?: string): Promise<void>;
  export function readFile(filepath: string, encoding?: string): Promise<string>;
  export function exists(filepath: string): Promise<boolean>;
  export function unlink(filepath: string): Promise<void>;
  export function mkdir(filepath: string, options?: any): Promise<void>;
}

declare module '@react-native-community/slider' {
  import { Component } from 'react';
  import { ViewStyle } from 'react-native';

  export interface SliderProps {
    style?: ViewStyle;
    value?: number;
    onValueChange?: (value: number) => void;
    minimumValue?: number;
    maximumValue?: number;
    step?: number;
    minimumTrackTintColor?: string;
    maximumTrackTintColor?: string;
    thumbTintColor?: string;
    disabled?: boolean;
  }

  export class Slider extends Component<SliderProps> {}
}

declare module 'react-native-vector-icons/MaterialIcons' {
  import { Component } from 'react';
  import { TextStyle } from 'react-native';

  export interface IconProps {
    name: string;
    size?: number;
    color?: string;
    style?: TextStyle;
  }

  export default class Icon extends Component<IconProps> {}
}