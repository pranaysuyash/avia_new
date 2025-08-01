import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Provider as PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Import screens
import HomeScreen from './src/screens/HomeScreen';
import RecordScreen from './src/screens/RecordScreen';
import HistoryScreen from './src/screens/HistoryScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import TranscriptionScreen from './src/screens/TranscriptionScreen';
import CustomizationScreen from './src/screens/CustomizationScreen';

// Import services
import { AppStateManager } from './src/services/AppStateManager';
import { SyncService } from './src/services/SyncService';
import { OfflineManager } from './src/services/OfflineManager';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

const theme = {
  colors: {
    primary: '#6200EE',
    accent: '#03DAC6',
    background: '#FFFFFF',
    surface: '#FFFFFF',
    text: '#000000',
    onSurface: '#000000',
    disabled: '#9E9E9E',
    placeholder: '#757575',
    backdrop: '#000000',
    onBackground: '#000000',
    notification: '#F44336',
  },
};

function HomeStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.colors.primary,
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <Stack.Screen 
        name="HomeMain" 
        component={HomeScreen} 
        options={{ title: 'Transcription App' }}
      />
      <Stack.Screen 
        name="Transcription" 
        component={TranscriptionScreen}
        options={{ title: 'Transcription Results' }}
      />
      <Stack.Screen 
        name="Customization" 
        component={CustomizationScreen}
        options={{ title: 'AI Customization' }}
      />
    </Stack.Navigator>
  );
}

function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Home') {
            iconName = 'home';
          } else if (route.name === 'Record') {
            iconName = 'mic';
          } else if (route.name === 'History') {
            iconName = 'history';
          } else if (route.name === 'Settings') {
            iconName = 'settings';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: 'gray',
        headerShown: false,
      })}
    >
      <Tab.Screen name="Home" component={HomeStack} />
      <Tab.Screen name="Record" component={RecordScreen} />
      <Tab.Screen name="History" component={HistoryScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Initialize app state manager
        await AppStateManager.initialize();
        
        // Check network connectivity
        const connectionState = await SyncService.checkConnectivity();
        setIsOnline(connectionState.isConnected);
        
        // Initialize offline capabilities
        await OfflineManager.initialize();
        
        // Sync with server if online
        if (connectionState.isConnected) {
          await SyncService.syncWithServer();
        }
        
        setIsLoading(false);
      } catch (error) {
        console.error('App initialization failed:', error);
        setIsLoading(false);
      }
    };

    initializeApp();
  }, []);

  if (isLoading) {
    return (
      <PaperProvider theme={theme}>
        <SafeAreaProvider>
          {/* Loading screen would go here */}
        </SafeAreaProvider>
      </PaperProvider>
    );
  }

  return (
    <PaperProvider theme={theme}>
      <SafeAreaProvider>
        <NavigationContainer>
          <TabNavigator />
        </NavigationContainer>
      </SafeAreaProvider>
    </PaperProvider>
  );
}