/**
 * Push Notification Manager for React Native
 * Handles registration, receiving, and displaying push notifications
 */

import React, { useEffect, useState } from 'react';
import { Alert, Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Notification configuration
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

interface NotificationData {
  type: string;
  user_id?: string;
  file_name?: string;
  duration?: number;
  error?: string;
  timestamp: string;
  [key: string]: any;
}

interface PushNotificationManagerProps {
  userId?: string;
  onNotificationReceived?: (notification: any) => void;
  onNotificationTapped?: (data: NotificationData) => void;
}

export const PushNotificationManager: React.FC<PushNotificationManagerProps> = ({
  userId,
  onNotificationReceived,
  onNotificationTapped,
}) => {
  const [expoPushToken, setExpoPushToken] = useState<string>();
  const [notification, setNotification] = useState<any>();

  // Register for push notifications
  useEffect(() => {
    registerForPushNotificationsAsync().then(token => {
      if (token) {
        setExpoPushToken(token);
        // Save token to backend
        if (userId) {
          registerTokenWithServer(userId, token);
        }
      }
    });

    // Listen for notifications received while app is running
    const notificationListener = Notifications.addNotificationReceivedListener(notification => {
      setNotification(notification);
      onNotificationReceived?.(notification);
      handleNotificationReceived(notification);
    });

    // Listen for notification taps
    const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
      const data = response.notification.request.content.data as NotificationData;
      onNotificationTapped?.(data);
      handleNotificationTapped(data);
    });

    return () => {
      Notifications.removeNotificationSubscription(notificationListener);
      Notifications.removeNotificationSubscription(responseListener);
    };
  }, [userId]);

  const handleNotificationReceived = (notification: any) => {
    const data = notification.request.content.data as NotificationData;
    
    // Update badge count
    Notifications.setBadgeCountAsync(1);
    
    // Store notification for history
    storeNotification(notification);
    
    // Log notification for analytics
    console.log('📱 Notification received:', {
      type: data.type,
      title: notification.request.content.title,
      timestamp: new Date().toISOString()
    });
  };

  const handleNotificationTapped = (data: NotificationData) => {
    // Clear badge when notification is tapped
    Notifications.setBadgeCountAsync(0);
    
    // Handle different notification types
    switch (data.type) {
      case 'transcription_complete':
        // Navigate to transcript view
        console.log('🎉 Transcription complete for:', data.file_name);
        break;
        
      case 'transcription_failed':
        // Show error details
        Alert.alert(
          'Transcription Failed',
          `Failed to process ${data.file_name}. Please try again.`,
          [{ text: 'OK' }]
        );
        break;
        
      case 'quota_warning':
        // Navigate to usage/upgrade screen
        console.log('⚠️ Quota warning for user:', data.user_id);
        break;
        
      case 'sharing_notification':
        // Navigate to shared transcript
        console.log('📄 New shared transcript:', data.file_name);
        break;
        
      default:
        console.log('📱 Unknown notification type:', data.type);
    }
  };

  return null; // This is a utility component with no UI
};

// Helper function to register for push notifications
async function registerForPushNotificationsAsync() {
  let token;

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });
  }

  if (Device.isDevice) {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    
    if (finalStatus !== 'granted') {
      Alert.alert(
        'Push Notifications',
        'Enable push notifications to get notified when your transcriptions are ready!',
        [{ text: 'OK' }]
      );
      return;
    }
    
    // Get push token
    token = (await Notifications.getExpoPushTokenAsync()).data;
    console.log('📱 Expo push token:', token);
    
  } else {
    Alert.alert('Must use physical device for Push Notifications');
  }

  return token;
}

// Register token with backend server
async function registerTokenWithServer(userId: string, token: string) {
  try {
    const response = await fetch('/api/notifications/register-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        device_token: token,
        platform: Platform.OS,
      }),
    });

    if (response.ok) {
      console.log('✅ Push token registered with server');
      // Store locally for offline reference
      await AsyncStorage.setItem('push_token', token);
    } else {
      console.error('❌ Failed to register push token');
    }
  } catch (error) {
    console.error('❌ Error registering push token:', error);
  }
}

// Store notification in local storage for history
async function storeNotification(notification: any) {
  try {
    const stored = await AsyncStorage.getItem('notification_history');
    const history = stored ? JSON.parse(stored) : [];
    
    const notificationData = {
      id: notification.request.identifier,
      title: notification.request.content.title,
      body: notification.request.content.body,
      data: notification.request.content.data,
      timestamp: new Date().toISOString(),
      read: false
    };
    
    // Add to beginning of array (most recent first)
    history.unshift(notificationData);
    
    // Keep only last 100 notifications
    const trimmed = history.slice(0, 100);
    
    await AsyncStorage.setItem('notification_history', JSON.stringify(trimmed));
  } catch (error) {
    console.error('Error storing notification:', error);
  }
}

// Utility functions for managing notifications
export const NotificationUtils = {
  // Clear all notifications
  clearAllNotifications: async () => {
    await Notifications.dismissAllNotificationsAsync();
    await Notifications.setBadgeCountAsync(0);
  },

  // Schedule local notification
  scheduleLocalNotification: async (title: string, body: string, data: any, delaySeconds: number = 0) => {
    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        data,
        sound: true,
      },
      trigger: delaySeconds > 0 ? { seconds: delaySeconds } : null,
    });
  },

  // Get notification history
  getNotificationHistory: async () => {
    try {
      const stored = await AsyncStorage.getItem('notification_history');
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('Error getting notification history:', error);
      return [];
    }
  },

  // Mark notification as read
  markNotificationAsRead: async (notificationId: string) => {
    try {
      const stored = await AsyncStorage.getItem('notification_history');
      if (stored) {
        const history = JSON.parse(stored);
        const updated = history.map((notification: any) => 
          notification.id === notificationId 
            ? { ...notification, read: true }
            : notification
        );
        await AsyncStorage.setItem('notification_history', JSON.stringify(updated));
      }
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  },

  // Get unread notification count
  getUnreadCount: async () => {
    try {
      const stored = await AsyncStorage.getItem('notification_history');
      if (stored) {
        const history = JSON.parse(stored);
        return history.filter((notification: any) => !notification.read).length;
      }
      return 0;
    } catch (error) {
      console.error('Error getting unread count:', error);
      return 0;
    }
  }
};

export default PushNotificationManager;