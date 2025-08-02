# Mobile Video Processor Dependencies

The VideoProcessor component requires the following React Native packages to be installed:

## Required Dependencies

```json
{
  "dependencies": {
    "react-native-video": "^6.0.0",
    "react-native-document-picker": "^9.0.0",
    "react-native-fs": "^2.20.0",
    "@react-native-community/slider": "^4.4.0",
    "react-native-vector-icons": "^10.0.0"
  }
}
```

## Installation Commands

```bash
# Install the packages
npm install react-native-video react-native-document-picker react-native-fs @react-native-community/slider react-native-vector-icons

# For iOS, run pod install
cd ios && pod install

# For Android, make sure to follow the setup instructions for each package
```

## Setup Instructions

### react-native-video
Follow the installation guide at: https://github.com/react-native-video/react-native-video

### react-native-document-picker
Follow the installation guide at: https://github.com/rnmods/react-native-document-picker

### react-native-fs
Follow the installation guide at: https://github.com/itinance/react-native-fs

### @react-native-community/slider
Follow the installation guide at: https://github.com/callstack/react-native-slider

### react-native-vector-icons
Follow the installation guide at: https://github.com/oblador/react-native-vector-icons

## Platform-Specific Configuration

### iOS
- Add camera and photo library permissions to Info.plist
- Configure video playback capabilities

### Android
- Add file system permissions to AndroidManifest.xml
- Configure video playback and file access permissions

## Usage Notes

- The component handles video file selection, processing, and playback
- All external dependencies are properly imported and typed
- File operations use React Native File System for cross-platform compatibility
- Video playback uses react-native-video for optimal performance