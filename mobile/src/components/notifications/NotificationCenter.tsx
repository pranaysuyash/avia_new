import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Platform,
  Modal,
  FlatList,
  Switch,
  RefreshControl,
  Dimensions,
  Animated,
  PanResponder,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient } from '../../services/api';
import { theme } from '../../theme';
import AsyncStorage from '@react-native-async-storage/async-storage';
import PushNotification from 'react-native-push-notification';
import { formatDistanceToNow } from 'date-fns';

const { width: screenWidth } = Dimensions.get('window');

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'task_update' | 'system' | 'collaboration' | 'security';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  data?: Record<string, any>;
  action_url?: string;
  action_text?: string;
  read: boolean;
  read_at?: string;
  created_at: string;
  expires_at?: string;
}

interface NotificationPreferences {
  email_enabled: boolean;
  sms_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  notification_types: Record<string, boolean>;
  priority_threshold: string;
}

const NotificationCenter: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedTab, setSelectedTab] = useState<'all' | 'unread'>('all');
  const [showSettings, setShowSettings] = useState(false);
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    email_enabled: true,
    sms_enabled: false,
    push_enabled: true,
    in_app_enabled: true,
    quiet_hours_enabled: false,
    notification_types: {
      info: true,
      success: true,
      warning: true,
      error: true,
      task_update: true,
      system: true,
      collaboration: true,
      security: true,
    },
    priority_threshold: 'low',
  });

  const swipeAnimations = useRef<Record<string, Animated.Value>>({}).current;
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    configurePushNotifications();
    loadNotifications();
    loadPreferences();
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const configurePushNotifications = () => {
    PushNotification.configure({
      onNotification: function (notification) {
        console.log('NOTIFICATION:', notification);
        // Handle notification tap
        if (notification.userInteraction) {
          handleNotificationTap(notification.data);
        }
      },
      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },
      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });
  };

  const connectWebSocket = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const wsUrl = `ws://localhost:8000/api/v1/notifications/ws?token=${token}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Connected to notification service');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'notification') {
          handleNewNotification(data.data);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current.onclose = () => {
        console.log('Disconnected from notification service');
        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

  const handleNewNotification = (notification: any) => {
    // Add to notifications list
    setNotifications(prev => [notification, ...prev]);
    setUnreadCount(prev => prev + 1);
    
    // Show local notification if app is in background
    if (preferences.push_enabled) {
      PushNotification.localNotification({
        title: notification.title,
        message: notification.message,
        data: notification,
        priority: notification.priority === 'urgent' ? 'high' : 'default',
      });
    }
  };

  const handleNotificationTap = (data: any) => {
    if (data.action_url) {
      // Navigate to action URL
      // You'll need to implement navigation based on your app's routing
    }
    setModalVisible(true);
  };

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/notifications/', {
        params: { limit: 50 },
      });
      setNotifications(response.data);
      updateUnreadCount(response.data);
    } catch (err) {
      Alert.alert('Error', 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadNotifications();
    setRefreshing(false);
  };

  const updateUnreadCount = (notificationsList: Notification[]) => {
    const count = notificationsList.filter(n => !n.read).length;
    setUnreadCount(count);
    // Update badge count
    PushNotification.setApplicationIconBadgeNumber(count);
  };

  const loadPreferences = async () => {
    try {
      const response = await apiClient.get('/api/v1/notifications/preferences');
      setPreferences(response.data);
    } catch (err) {
      console.error('Failed to load preferences:', err);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await apiClient.put(`/api/v1/notifications/${notificationId}/read`);
      setNotifications(prev =>
        prev.map(n => (n.id === notificationId ? { ...n, read: true } : n))
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await apiClient.put('/api/v1/notifications/mark-all-read');
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
      PushNotification.setApplicationIconBadgeNumber(0);
    } catch (err) {
      Alert.alert('Error', 'Failed to mark all as read');
    }
  };

  const deleteNotification = async (notificationId: string) => {
    try {
      await apiClient.delete(`/api/v1/notifications/${notificationId}`);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      updateUnreadCount(notifications.filter(n => n.id !== notificationId));
    } catch (err) {
      Alert.alert('Error', 'Failed to delete notification');
    }
  };

  const clearAll = () => {
    Alert.alert(
      'Clear All Notifications',
      'Are you sure you want to clear all notifications?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiClient.delete('/api/v1/notifications/clear-all');
              setNotifications([]);
              setUnreadCount(0);
              PushNotification.setApplicationIconBadgeNumber(0);
            } catch (err) {
              Alert.alert('Error', 'Failed to clear notifications');
            }
          },
        },
      ]
    );
  };

  const updatePreferences = async () => {
    try {
      await apiClient.put('/api/v1/notifications/preferences', preferences);
      Alert.alert('Success', 'Preferences updated');
      setShowSettings(false);
    } catch (err) {
      Alert.alert('Error', 'Failed to update preferences');
    }
  };

  const getIcon = (type: string) => {
    const icons: Record<string, string> = {
      info: 'info',
      success: 'check-circle',
      warning: 'warning',
      error: 'error',
      task_update: 'assignment',
      system: 'settings',
      collaboration: 'group',
      security: 'security',
    };
    return icons[type] || 'notifications';
  };

  const getIconColor = (type: string) => {
    const colors: Record<string, string> = {
      info: theme.colors.info,
      success: theme.colors.success,
      warning: theme.colors.warning,
      error: theme.colors.error,
      task_update: theme.colors.primary,
      system: theme.colors.text,
      collaboration: theme.colors.primary,
      security: theme.colors.error,
    };
    return colors[type] || theme.colors.text;
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: theme.colors.textSecondary,
      medium: theme.colors.primary,
      high: theme.colors.secondary,
      urgent: theme.colors.error,
    };
    return colors[priority] || theme.colors.textSecondary;
  };

  const createPanResponder = (notificationId: string) => {
    if (!swipeAnimations[notificationId]) {
      swipeAnimations[notificationId] = new Animated.Value(0);
    }

    return PanResponder.create({
      onMoveShouldSetPanResponder: (_, gestureState) => {
        return Math.abs(gestureState.dx) > 20;
      },
      onPanResponderMove: (_, gestureState) => {
        swipeAnimations[notificationId].setValue(gestureState.dx);
      },
      onPanResponderRelease: (_, gestureState) => {
        if (gestureState.dx < -100) {
          // Swipe left - Delete
          Animated.timing(swipeAnimations[notificationId], {
            toValue: -screenWidth,
            duration: 200,
            useNativeDriver: true,
          }).start(() => {
            deleteNotification(notificationId);
          });
        } else if (gestureState.dx > 100) {
          // Swipe right - Mark as read/unread
          Animated.timing(swipeAnimations[notificationId], {
            toValue: 0,
            duration: 200,
            useNativeDriver: true,
          }).start(() => {
            const notification = notifications.find(n => n.id === notificationId);
            if (notification && !notification.read) {
              markAsRead(notificationId);
            }
          });
        } else {
          // Reset position
          Animated.spring(swipeAnimations[notificationId], {
            toValue: 0,
            useNativeDriver: true,
          }).start();
        }
      },
    });
  };

  const renderNotification = ({ item }: { item: Notification }) => {
    const panResponder = createPanResponder(item.id);

    return (
      <Animated.View
        style={[
          styles.notificationContainer,
          {
            transform: [{ translateX: swipeAnimations[item.id] || new Animated.Value(0) }],
          },
        ]}
        {...panResponder.panHandlers}
      >
        <TouchableOpacity
          style={[
            styles.notificationItem,
            !item.read && styles.unreadNotification,
          ]}
          onPress={() => {
            if (!item.read) {
              markAsRead(item.id);
            }
            if (item.action_url) {
              // Handle navigation
            }
          }}
          activeOpacity={0.8}
        >
          <View style={styles.notificationIcon}>
            <Icon
              name={getIcon(item.type)}
              size={24}
              color={getIconColor(item.type)}
            />
          </View>
          <View style={styles.notificationContent}>
            <View style={styles.notificationHeader}>
              <Text style={styles.notificationTitle} numberOfLines={1}>
                {item.title}
              </Text>
              {item.priority === 'urgent' && (
                <Icon name="priority-high" size={18} color={theme.colors.error} />
              )}
              <View
                style={[
                  styles.priorityBadge,
                  { backgroundColor: getPriorityColor(item.priority) },
                ]}
              >
                <Text style={styles.priorityText}>{item.priority}</Text>
              </View>
            </View>
            <Text style={styles.notificationMessage} numberOfLines={2}>
              {item.message}
            </Text>
            <Text style={styles.notificationTime}>
              {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
            </Text>
          </View>
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={() => deleteNotification(item.id)}
          >
            <Icon name="close" size={20} color={theme.colors.textSecondary} />
          </TouchableOpacity>
        </TouchableOpacity>
      </Animated.View>
    );
  };

  const filteredNotifications = notifications.filter(n => {
    if (selectedTab === 'unread') return !n.read;
    return true;
  });

  return (
    <>
      {/* Notification Icon Button */}
      <TouchableOpacity
        style={styles.iconButton}
        onPress={() => setModalVisible(true)}
      >
        <Icon name="notifications" size={24} color={theme.colors.text} />
        {unreadCount > 0 && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>
              {unreadCount > 99 ? '99+' : unreadCount}
            </Text>
          </View>
        )}
      </TouchableOpacity>

      {/* Notification Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            {/* Header */}
            <View style={styles.header}>
              <Text style={styles.title}>Notifications</Text>
              <View style={styles.headerActions}>
                <TouchableOpacity
                  style={styles.headerButton}
                  onPress={() => setShowSettings(true)}
                >
                  <Icon name="settings" size={24} color={theme.colors.text} />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.headerButton}
                  onPress={() => setModalVisible(false)}
                >
                  <Icon name="close" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>
            </View>

            {/* Tabs */}
            <View style={styles.tabs}>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'all' && styles.activeTab]}
                onPress={() => setSelectedTab('all')}
              >
                <Text style={[styles.tabText, selectedTab === 'all' && styles.activeTabText]}>
                  All
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'unread' && styles.activeTab]}
                onPress={() => setSelectedTab('unread')}
              >
                <Text style={[styles.tabText, selectedTab === 'unread' && styles.activeTabText]}>
                  Unread ({unreadCount})
                </Text>
              </TouchableOpacity>
            </View>

            {/* Actions */}
            {filteredNotifications.length > 0 && (
              <View style={styles.actions}>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={markAllAsRead}
                >
                  <Icon name="done-all" size={18} color={theme.colors.primary} />
                  <Text style={styles.actionText}>Mark all read</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={clearAll}
                >
                  <Icon name="delete" size={18} color={theme.colors.error} />
                  <Text style={[styles.actionText, { color: theme.colors.error }]}>
                    Clear all
                  </Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Notifications List */}
            {loading ? (
              <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color={theme.colors.primary} />
              </View>
            ) : filteredNotifications.length === 0 ? (
              <View style={styles.centerContainer}>
                <Icon name="notifications-none" size={64} color={theme.colors.textSecondary} />
                <Text style={styles.emptyText}>
                  {selectedTab === 'unread' ? 'No unread notifications' : 'No notifications'}
                </Text>
              </View>
            ) : (
              <FlatList
                data={filteredNotifications}
                renderItem={renderNotification}
                keyExtractor={item => item.id}
                refreshControl={
                  <RefreshControl
                    refreshing={refreshing}
                    onRefresh={onRefresh}
                    colors={[theme.colors.primary]}
                  />
                }
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.listContent}
              />
            )}
          </View>
        </View>
      </Modal>

      {/* Settings Modal */}
      <Modal
        visible={showSettings}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowSettings(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.header}>
              <Text style={styles.title}>Notification Settings</Text>
              <TouchableOpacity onPress={() => setShowSettings(false)}>
                <Icon name="close" size={24} color={theme.colors.text} />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
              {/* Delivery Channels */}
              <View style={styles.settingsSection}>
                <Text style={styles.sectionTitle}>Delivery Channels</Text>
                <View style={styles.settingItem}>
                  <Text style={styles.settingLabel}>Email Notifications</Text>
                  <Switch
                    value={preferences.email_enabled}
                    onValueChange={(value) =>
                      setPreferences({ ...preferences, email_enabled: value })
                    }
                    trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                  />
                </View>
                <View style={styles.settingItem}>
                  <Text style={styles.settingLabel}>Push Notifications</Text>
                  <Switch
                    value={preferences.push_enabled}
                    onValueChange={(value) =>
                      setPreferences({ ...preferences, push_enabled: value })
                    }
                    trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                  />
                </View>
                <View style={styles.settingItem}>
                  <Text style={styles.settingLabel}>In-App Notifications</Text>
                  <Switch
                    value={preferences.in_app_enabled}
                    onValueChange={(value) =>
                      setPreferences({ ...preferences, in_app_enabled: value })
                    }
                    trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                  />
                </View>
              </View>

              {/* Notification Types */}
              <View style={styles.settingsSection}>
                <Text style={styles.sectionTitle}>Notification Types</Text>
                {Object.entries(preferences.notification_types).map(([type, enabled]) => (
                  <View key={type} style={styles.settingItem}>
                    <View style={styles.settingLabelRow}>
                      <Icon
                        name={getIcon(type)}
                        size={20}
                        color={getIconColor(type)}
                        style={styles.settingIcon}
                      />
                      <Text style={styles.settingLabel}>
                        {type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
                      </Text>
                    </View>
                    <Switch
                      value={enabled}
                      onValueChange={(value) =>
                        setPreferences({
                          ...preferences,
                          notification_types: {
                            ...preferences.notification_types,
                            [type]: value,
                          },
                        })
                      }
                      trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                    />
                  </View>
                ))}
              </View>

              <TouchableOpacity style={styles.saveButton} onPress={updatePreferences}>
                <Text style={styles.saveButtonText}>Save Settings</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  iconButton: {
    position: 'relative',
    padding: 8,
  },
  badge: {
    position: 'absolute',
    top: 0,
    right: 0,
    backgroundColor: theme.colors.error,
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  badgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: theme.colors.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    height: '90%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 8,
  },
  headerButton: {
    padding: 8,
  },
  tabs: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: theme.colors.primary,
  },
  tabText: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  activeTabText: {
    color: theme.colors.primary,
    fontWeight: '500',
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  actionText: {
    fontSize: 14,
    color: theme.colors.primary,
  },
  listContent: {
    paddingBottom: 20,
  },
  notificationContainer: {
    backgroundColor: theme.colors.background,
  },
  notificationItem: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  unreadNotification: {
    backgroundColor: theme.colors.primary + '10',
  },
  notificationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: theme.colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  notificationContent: {
    flex: 1,
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: theme.colors.text,
    flex: 1,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginLeft: 8,
  },
  priorityText: {
    fontSize: 10,
    color: '#fff',
    fontWeight: '500',
    textTransform: 'uppercase',
  },
  notificationMessage: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginBottom: 4,
  },
  notificationTime: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  deleteButton: {
    padding: 8,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 16,
    color: theme.colors.textSecondary,
    marginTop: 16,
  },
  settingsSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  settingLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingIcon: {
    marginRight: 12,
  },
  settingLabel: {
    fontSize: 16,
    color: theme.colors.text,
  },
  saveButton: {
    backgroundColor: theme.colors.primary,
    marginHorizontal: 16,
    marginVertical: 24,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default NotificationCenter;