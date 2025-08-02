# Modern UI Implementation Guide

## Desktop App (Electron + React)

### 1. Project Setup

```bash
cd desktop_app/src/renderer
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          800: '#3730A3',
          900: '#312E81',
        },
        secondary: {
          500: '#8B5CF6',
          600: '#7C3AED',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.3s ease-in',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
```

### 3. Main Window Update

```javascript
// desktop_app/src/main.js - Update createWindow function
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: !isDev
    },
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    backgroundColor: '#f9fafb',
    show: false,
    frame: process.platform !== 'darwin', // Frameless on macOS
  });

  // Load React app instead of Streamlit
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/build/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });
}
```

### 4. Key Components Structure

```
desktop_app/src/renderer/
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── Layout.tsx
│   ├── dashboard/
│   │   ├── StatsCard.tsx
│   │   ├── RecentTranscriptions.tsx
│   │   ├── QuickActions.tsx
│   │   └── UsageChart.tsx
│   ├── workspace/
│   │   ├── WaveformPlayer.tsx
│   │   ├── TranscriptEditor.tsx
│   │   ├── EntityPanel.tsx
│   │   └── ProcessingModal.tsx
│   ├── common/
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   └── Toast.tsx
│   └── animations/
│       ├── FadeIn.tsx
│       ├── SlideIn.tsx
│       └── ScaleIn.tsx
├── screens/
│   ├── Dashboard.tsx
│   ├── TranscriptionWorkspace.tsx
│   ├── ProcessingQueue.tsx
│   ├── History.tsx
│   └── Settings.tsx
├── services/
│   ├── api.ts
│   ├── websocket.ts
│   ├── storage.ts
│   └── auth.ts
├── store/
│   ├── index.ts
│   ├── slices/
│   │   ├── transcriptionSlice.ts
│   │   ├── userSlice.ts
│   │   └── settingsSlice.ts
│   └── hooks.ts
├── styles/
│   ├── globals.css
│   └── animations.css
└── utils/
    ├── constants.ts
    ├── helpers.ts
    └── validators.ts
```

### 5. Example Component - Modern Card

```typescript
// components/common/Card.tsx
import React from 'react';
import { motion } from 'framer-motion';

interface CardProps {
  children: React.ReactNode;
  hover?: boolean;
  gradient?: boolean;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  hover = false, 
  gradient = false,
  className = '' 
}) => {
  const baseClasses = 'bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden';
  const hoverClasses = hover ? 'hover:shadow-md transition-shadow cursor-pointer' : '';
  const gradientClasses = gradient ? 'bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900' : '';

  return (
    <motion.div
      whileHover={hover ? { y: -2 } : {}}
      className={`${baseClasses} ${hoverClasses} ${gradientClasses} ${className}`}
    >
      {children}
    </motion.div>
  );
};
```

### 6. API Service Integration

```typescript
// services/api.ts
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const transcriptionAPI = {
  upload: (file: File, options?: any) => {
    const formData = new FormData();
    formData.append('file', file);
    if (options) {
      Object.keys(options).forEach(key => {
        formData.append(key, options[key]);
      });
    }
    return api.post('/transcriptions/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: options?.onProgress,
    });
  },
  
  get: (id: string) => api.get(`/transcriptions/${id}`),
  
  list: (params?: any) => api.get('/transcriptions', { params }),
  
  update: (id: string, data: any) => api.put(`/transcriptions/${id}`, data),
  
  delete: (id: string) => api.delete(`/transcriptions/${id}`),
};
```

## Mobile App (React Native)

### 1. Modern Components

```javascript
// components/Card.js
import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { Card as PaperCard } from 'react-native-paper';
import Animated, { 
  useAnimatedStyle, 
  useSharedValue, 
  withSpring 
} from 'react-native-reanimated';

export const ModernCard = ({ children, onPress, style, ...props }) => {
  const scale = useSharedValue(1);
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.98);
  };

  const handlePressOut = () => {
    scale.value = withSpring(1);
  };

  return (
    <TouchableOpacity
      onPress={onPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={1}
    >
      <Animated.View style={animatedStyle}>
        <PaperCard style={[styles.card, style]} {...props}>
          {children}
        </PaperCard>
      </Animated.View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
});
```

### 2. Recording Screen with Animation

```javascript
// screens/RecordScreen.js
import React, { useState, useRef } from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
  withSpring,
} from 'react-native-reanimated';
import { TouchableOpacity } from 'react-native-gesture-handler';

const { width } = Dimensions.get('window');
const RECORD_BUTTON_SIZE = 120;

export const RecordScreen = () => {
  const theme = useTheme();
  const [isRecording, setIsRecording] = useState(false);
  const pulseScale = useSharedValue(1);
  const buttonScale = useSharedValue(1);

  React.useEffect(() => {
    if (isRecording) {
      pulseScale.value = withRepeat(
        withTiming(1.3, { duration: 1000 }),
        -1,
        true
      );
    } else {
      pulseScale.value = withSpring(1);
    }
  }, [isRecording]);

  const pulseStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulseScale.value }],
    opacity: isRecording ? 0.3 : 0,
  }));

  const buttonStyle = useAnimatedStyle(() => ({
    transform: [{ scale: buttonScale.value }],
  }));

  const handlePress = () => {
    buttonScale.value = withSpring(0.9, {}, () => {
      buttonScale.value = withSpring(1);
    });
    setIsRecording(!isRecording);
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text variant="headlineMedium" style={styles.title}>
          {isRecording ? 'Recording...' : 'Tap to Record'}
        </Text>
        
        <View style={styles.recordContainer}>
          <Animated.View
            style={[
              styles.pulse,
              { backgroundColor: theme.colors.primary },
              pulseStyle,
            ]}
          />
          
          <TouchableOpacity onPress={handlePress}>
            <Animated.View
              style={[
                styles.recordButton,
                { backgroundColor: theme.colors.primary },
                buttonStyle,
              ]}
            >
              <View style={[
                styles.innerCircle,
                isRecording && styles.recordingInner,
              ]} />
            </Animated.View>
          </TouchableOpacity>
        </View>

        {isRecording && (
          <View style={styles.timer}>
            <Text variant="titleLarge">00:00</Text>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    marginBottom: 50,
  },
  recordContainer: {
    width: RECORD_BUTTON_SIZE,
    height: RECORD_BUTTON_SIZE,
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordButton: {
    width: RECORD_BUTTON_SIZE,
    height: RECORD_BUTTON_SIZE,
    borderRadius: RECORD_BUTTON_SIZE / 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  pulse: {
    position: 'absolute',
    width: RECORD_BUTTON_SIZE,
    height: RECORD_BUTTON_SIZE,
    borderRadius: RECORD_BUTTON_SIZE / 2,
  },
  innerCircle: {
    width: 40,
    height: 40,
    backgroundColor: 'white',
    borderRadius: 20,
  },
  recordingInner: {
    borderRadius: 8,
  },
  timer: {
    marginTop: 40,
  },
});
```

## Shared Design Tokens

```javascript
// shared/design-tokens.js
export const tokens = {
  colors: {
    primary: {
      50: '#EEF2FF',
      100: '#E0E7FF',
      200: '#C7D2FE',
      300: '#A5B4FC',
      400: '#818CF8',
      500: '#6366F1',
      600: '#4F46E5',
      700: '#4338CA',
      800: '#3730A3',
      900: '#312E81',
    },
    gray: {
      50: '#F9FAFB',
      100: '#F3F4F6',
      200: '#E5E7EB',
      300: '#D1D5DB',
      400: '#9CA3AF',
      500: '#6B7280',
      600: '#4B5563',
      700: '#374151',
      800: '#1F2937',
      900: '#111827',
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    full: 9999,
  },
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.05,
      shadowRadius: 2,
      elevation: 1,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 2,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 4,
    },
  },
};
```

## Implementation Steps

1. **Phase 1: Setup & Infrastructure**
   - Set up React app in desktop_app/src/renderer
   - Configure build process to work with Electron
   - Set up React Native with proper theming

2. **Phase 2: Core Components**
   - Build component library
   - Implement navigation
   - Create layout components

3. **Phase 3: Screen Implementation**
   - Dashboard with stats and quick actions
   - Transcription workspace with waveform
   - History with search and filters
   - Settings with theme toggle

4. **Phase 4: API Integration**
   - Connect to Python backend via REST API
   - Implement WebSocket for real-time updates
   - Add offline support

5. **Phase 5: Polish & Optimization**
   - Add animations and transitions
   - Optimize performance
   - Implement accessibility features
   - Add keyboard shortcuts

## Running the New UI

### Desktop
```bash
cd desktop_app/src/renderer
npm install
npm start  # Development
npm run build  # Production build
```

### Mobile
```bash
cd mobile_app
npm install
npx expo start
```

The new UI provides a modern, native experience that's far superior to the embedded Streamlit approach!