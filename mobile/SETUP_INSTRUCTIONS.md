# Mobile App Setup Instructions

## Prerequisites

Before running the mobile app, ensure you have the following installed:

- Node.js (version 16 or higher)
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development, macOS only)

## Installation Steps

### 1. Install Dependencies

Navigate to the mobile directory and install all required packages:

```bash
cd mobile
npm install
```

### 2. Install React Native Dependencies

Install the specific React Native video processing dependencies:

```bash
# Core video processing packages
npm install react-native-video@^6.0.0
npm install react-native-document-picker@^9.0.0
npm install react-native-fs@^2.20.0
npm install @react-native-community/slider@^4.4.0
npm install react-native-vector-icons@^10.0.0

# Navigation dependencies
npm install @react-navigation/native@^6.1.0
npm install @react-navigation/stack@^6.3.0
npm install react-native-screens@^3.25.0
npm install react-native-safe-area-context@^4.7.0
npm install react-native-gesture-handler@^2.13.0

# Development dependencies
npm install --save-dev @types/react@^18.0.24
npm install --save-dev @types/react-native@^0.72.0
npm install --save-dev typescript@4.8.4
```

### 3. Platform-Specific Setup

#### iOS Setup

```bash
cd ios
pod install
cd ..
```

#### Android Setup

Make sure Android Studio is installed and configured properly.

### 4. Configure Vector Icons

For `react-native-vector-icons`, follow the platform-specific setup:

#### iOS
1. Add the following to `ios/YourApp/Info.plist`:
```xml
<key>UIAppFonts</key>
<array>
  <string>MaterialIcons.ttf</string>
</array>
```

#### Android
1. Add the following to `android/app/build.gradle`:
```gradle
apply from: "../../node_modules/react-native-vector-icons/fonts.gradle"
```

### 5. Configure Permissions

#### iOS (ios/YourApp/Info.plist)
```xml
<key>NSCameraUsageDescription</key>
<string>This app needs access to camera to record videos</string>
<key>NSMicrophoneUsageDescription</key>
<string>This app needs access to microphone to record audio</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>This app needs access to photo library to select videos</string>
```

#### Android (android/app/src/main/AndroidManifest.xml)
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

## Troubleshooting

### "Cannot find module 'react'" Error

If you encounter the "Cannot find module 'react'" error, try the following:

1. **Clear npm cache:**
```bash
npm cache clean --force
```

2. **Delete node_modules and reinstall:**
```bash
rm -rf node_modules
rm package-lock.json
npm install
```

3. **Reset Metro bundler cache:**
```bash
npx react-native start --reset-cache
```

4. **Verify React installation:**
```bash
npm list react react-native
```

5. **Check TypeScript configuration:**
Make sure `tsconfig.json` is properly configured (should be fixed by our setup).

### Module Resolution Issues

If you're still having module resolution issues:

1. **Check your project structure:**
```
mobile/
├── src/
│   ├── components/
│   ├── types/
│   └── ...
├── package.json
├── tsconfig.json
└── node_modules/
```

2. **Verify type declarations:**
The `src/types/` directory contains custom type declarations for third-party packages.

3. **Restart your development server:**
```bash
npx react-native start --reset-cache
```

## Running the App

### Development Mode

```bash
# Start Metro bundler
npm start

# Run on iOS simulator
npm run ios

# Run on Android emulator
npm run android
```

### Production Build

```bash
# Android
cd android
./gradlew assembleRelease

# iOS
cd ios
xcodebuild -workspace YourApp.xcworkspace -scheme YourApp -configuration Release
```

## Project Structure

```
mobile/
├── src/
│   ├── components/
│   │   ├── video/
│   │   │   └── VideoProcessor.tsx
│   │   ├── media/
│   │   ├── dashboard/
│   │   └── ...
│   ├── api/
│   ├── types/
│   │   ├── index.d.ts
│   │   └── react-native-video.d.ts
│   └── utils/
├── android/
├── ios/
├── package.json
├── tsconfig.json
└── README.md
```

## Common Issues and Solutions

### 1. Metro bundler issues
```bash
npx react-native start --reset-cache
```

### 2. iOS build issues
```bash
cd ios
rm -rf Pods
pod install
```

### 3. Android build issues
```bash
cd android
./gradlew clean
```

### 4. TypeScript errors
Make sure all type declarations are properly installed and configured.

## Additional Resources

- [React Native Documentation](https://reactnative.dev/docs/getting-started)
- [React Native Video](https://github.com/react-native-video/react-native-video)
- [React Native Vector Icons](https://github.com/oblador/react-native-vector-icons)
- [React Navigation](https://reactnavigation.org/docs/getting-started)

## Support

If you continue to experience issues, please check:
1. Node.js version compatibility
2. React Native CLI version
3. Platform-specific setup requirements
4. Dependency version conflicts