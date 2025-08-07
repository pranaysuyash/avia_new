/**
 * Mobile Internationalization Component
 * Touch-optimized i18n settings with native mobile features
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Switch,
  Modal,
  FlatList,
  Alert,
  Platform,
  Dimensions,
  ActivityIndicator,
  Share,
  Vibration,
  Animated,
  PanResponder
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Localization from 'expo-localization';
import * as Haptics from 'expo-haptics';
import * as FileSystem from 'expo-file-system';
import * as DocumentPicker from 'expo-document-picker';
import * as Sharing from 'expo-sharing';
import { MaterialIcons, Ionicons, FontAwesome5 } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface LanguageInfo {
  code: string;
  name: string;
  native_name: string;
  direction: 'ltr' | 'rtl';
  flag: string;
  region?: string;
  popularity?: number;
}

interface LocalePreferences {
  language: string;
  region: string;
  timezone: string;
  dateFormat: string;
  timeFormat: '12h' | '24h';
  numberFormat: string;
  currencyFormat: string;
  temperatureUnit: 'celsius' | 'fahrenheit';
  distanceUnit: 'metric' | 'imperial';
}

interface TranslationPack {
  id: string;
  name: string;
  language: string;
  size: number;
  version: string;
  downloaded: boolean;
  progress?: number;
}

const InternationalizationMobile: React.FC = () => {
  const insets = useSafeAreaInsets();
  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [languages, setLanguages] = useState<LanguageInfo[]>([]);
  const [localePreferences, setLocalePreferences] = useState<LocalePreferences>({
    language: 'en',
    region: 'US',
    timezone: 'America/New_York',
    dateFormat: 'MM/dd/yyyy',
    timeFormat: '12h',
    numberFormat: 'US',
    currencyFormat: 'USD',
    temperatureUnit: 'celsius',
    distanceUnit: 'metric'
  });
  
  const [translationPacks, setTranslationPacks] = useState<TranslationPack[]>([]);
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [autoDetectEnabled, setAutoDetectEnabled] = useState(true);
  const [offlineModeEnabled, setOfflineModeEnabled] = useState(false);
  const [downloadingPacks, setDownloadingPacks] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Animation values
  const slideAnimation = new Animated.Value(0);
  const scaleAnimation = new Animated.Value(1);

  useEffect(() => {
    initializeMobileI18n();
    detectDeviceLanguage();
  }, []);

  const initializeMobileI18n = async () => {
    try {
      setLoading(true);
      
      // Load stored preferences
      const storedPrefs = await AsyncStorage.getItem('locale_preferences');
      if (storedPrefs) {
        const prefs = JSON.parse(storedPrefs);
        setLocalePreferences(prefs);
        setCurrentLanguage(prefs.language);
      }
      
      // Load available languages
      const mockLanguages: LanguageInfo[] = [
        { code: 'en', name: 'English', native_name: 'English', direction: 'ltr', flag: '🇺🇸', popularity: 100 },
        { code: 'es', name: 'Spanish', native_name: 'Español', direction: 'ltr', flag: '🇪🇸', popularity: 85 },
        { code: 'fr', name: 'French', native_name: 'Français', direction: 'ltr', flag: '🇫🇷', popularity: 70 },
        { code: 'de', name: 'German', native_name: 'Deutsch', direction: 'ltr', flag: '🇩🇪', popularity: 65 },
        { code: 'it', name: 'Italian', native_name: 'Italiano', direction: 'ltr', flag: '🇮🇹', popularity: 55 },
        { code: 'pt', name: 'Portuguese', native_name: 'Português', direction: 'ltr', flag: '🇧🇷', popularity: 60 },
        { code: 'ru', name: 'Russian', native_name: 'Русский', direction: 'ltr', flag: '🇷🇺', popularity: 50 },
        { code: 'zh-CN', name: 'Chinese (Simplified)', native_name: '简体中文', direction: 'ltr', flag: '🇨🇳', popularity: 80 },
        { code: 'ja', name: 'Japanese', native_name: '日本語', direction: 'ltr', flag: '🇯🇵', popularity: 45 },
        { code: 'ko', name: 'Korean', native_name: '한국어', direction: 'ltr', flag: '🇰🇷', popularity: 40 },
        { code: 'ar', name: 'Arabic', native_name: 'العربية', direction: 'rtl', flag: '🇸🇦', popularity: 55 },
        { code: 'he', name: 'Hebrew', native_name: 'עברית', direction: 'rtl', flag: '🇮🇱', popularity: 25 },
        { code: 'hi', name: 'Hindi', native_name: 'हिन्दी', direction: 'ltr', flag: '🇮🇳', popularity: 50 },
        { code: 'th', name: 'Thai', native_name: 'ไทย', direction: 'ltr', flag: '🇹🇭', popularity: 30 },
        { code: 'vi', name: 'Vietnamese', native_name: 'Tiếng Việt', direction: 'ltr', flag: '🇻🇳', popularity: 35 }
      ];
      
      setLanguages(mockLanguages);
      
      // Load translation packs
      loadTranslationPacks();
    } catch (error) {
      console.error('Failed to initialize mobile i18n:', error);
      Alert.alert('Error', 'Failed to load language settings');
    } finally {
      setLoading(false);
    }
  };

  const detectDeviceLanguage = () => {
    const deviceLanguage = Localization.locale.split('-')[0];
    if (autoDetectEnabled) {
      setCurrentLanguage(deviceLanguage);
      setLocalePreferences(prev => ({
        ...prev,
        language: deviceLanguage,
        timezone: Localization.timezone || prev.timezone,
        region: Localization.region || prev.region
      }));
    }
  };

  const loadTranslationPacks = () => {
    const mockPacks: TranslationPack[] = [
      { id: '1', name: 'Core Translations', language: 'es', size: 2.1, version: '1.0', downloaded: true },
      { id: '2', name: 'UI Components', language: 'es', size: 1.5, version: '1.0', downloaded: false },
      { id: '3', name: 'Business Terms', language: 'es', size: 0.8, version: '1.0', downloaded: false },
      { id: '4', name: 'Core Translations', language: 'fr', size: 2.3, version: '1.0', downloaded: false },
      { id: '5', name: 'Legal Terms', language: 'de', size: 1.2, version: '1.0', downloaded: false },
    ];
    setTranslationPacks(mockPacks);
  };

  const handleLanguageChange = async (languageCode: string) => {
    try {
      // Haptic feedback
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      
      setCurrentLanguage(languageCode);
      const newPreferences = { ...localePreferences, language: languageCode };
      setLocalePreferences(newPreferences);
      
      // Save to storage
      await AsyncStorage.setItem('locale_preferences', JSON.stringify(newPreferences));
      
      // Update app language (would integrate with i18n system)
      // await I18n.changeLanguage(languageCode);
      
      // Animate change
      Animated.sequence([
        Animated.timing(scaleAnimation, {
          toValue: 1.1,
          duration: 100,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnimation, {
          toValue: 1,
          duration: 100,
          useNativeDriver: true,
        })
      ]).start();
      
      setShowLanguageModal(false);
      
      // Show success message
      Alert.alert(
        'Language Changed',
        `Application language changed to ${languageCode.toUpperCase()}`,
        [{ text: 'OK', onPress: () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success) }]
      );
    } catch (error) {
      console.error('Failed to change language:', error);
      Alert.alert('Error', 'Failed to change language');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }
  };

  const handleDownloadPack = async (packId: string) => {
    try {
      setDownloadingPacks(prev => new Set(prev).add(packId));
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      
      // Simulate download with progress
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 100));
        setTranslationPacks(prev => prev.map(pack => 
          pack.id === packId ? { ...pack, progress } : pack
        ));
      }
      
      // Mark as downloaded
      setTranslationPacks(prev => prev.map(pack => 
        pack.id === packId ? { ...pack, downloaded: true, progress: undefined } : pack
      ));
      
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Success', 'Translation pack downloaded successfully');
    } catch (error) {
      console.error('Download failed:', error);
      Alert.alert('Error', 'Failed to download translation pack');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setDownloadingPacks(prev => {
        const newSet = new Set(prev);
        newSet.delete(packId);
        return newSet;
      });
    }
  };

  const handleExportTranslations = async () => {
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      
      const translations = {
        language: currentLanguage,
        preferences: localePreferences,
        exportDate: new Date().toISOString(),
        translations: {}
      };
      
      const fileName = `translations_${currentLanguage}_${Date.now()}.json`;
      const fileUri = FileSystem.documentDirectory + fileName;
      
      await FileSystem.writeAsStringAsync(fileUri, JSON.stringify(translations, null, 2));
      
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(fileUri, {
          mimeType: 'application/json',
          dialogTitle: 'Export Translations'
        });
      } else {
        Alert.alert('Export Complete', `Translations exported to ${fileName}`);
      }
    } catch (error) {
      console.error('Export failed:', error);
      Alert.alert('Error', 'Failed to export translations');
    }
  };

  const handleImportTranslations = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/json', 'text/csv'],
        copyToCacheDirectory: true
      });
      
      if (result.type === 'success') {
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
        
        const content = await FileSystem.readAsStringAsync(result.uri);
        const data = JSON.parse(content);
        
        // Process imported data
        Alert.alert(
          'Import Complete',
          `Imported translations for ${data.language || 'unknown language'}`,
          [{ text: 'OK', onPress: () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success) }]
        );
      }
    } catch (error) {
      console.error('Import failed:', error);
      Alert.alert('Error', 'Failed to import translations');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }
  };

  const filteredLanguages = languages.filter(lang =>
    lang.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lang.native_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const renderLanguageItem = ({ item }: { item: LanguageInfo }) => (
    <TouchableOpacity
      style={[
        styles.languageItem,
        item.code === currentLanguage && styles.selectedLanguage
      ]}
      onPress={() => handleLanguageChange(item.code)}
      activeOpacity={0.7}
    >
      <View style={styles.languageInfo}>
        <Text style={styles.languageFlag}>{item.flag}</Text>
        <View style={styles.languageText}>
          <Text style={styles.languageName}>{item.native_name}</Text>
          <Text style={styles.languageSubtext}>{item.name}</Text>
        </View>
      </View>
      
      {item.direction === 'rtl' && (
        <MaterialIcons name="format-textdirection-r-to-l" size={20} color="#666" />
      )}
      
      {item.code === currentLanguage && (
        <MaterialIcons name="check-circle" size={24} color="#4CAF50" />
      )}
    </TouchableOpacity>
  );

  const renderTranslationPack = ({ item }: { item: TranslationPack }) => (
    <View style={styles.translationPack}>
      <View style={styles.packInfo}>
        <Text style={styles.packName}>{item.name}</Text>
        <Text style={styles.packDetails}>
          {item.language.toUpperCase()} • {item.size.toFixed(1)} MB • v{item.version}
        </Text>
        
        {item.progress !== undefined && (
          <View style={styles.progressContainer}>
            <View style={[styles.progressBar, { width: `${item.progress}%` }]} />
            <Text style={styles.progressText}>{item.progress}%</Text>
          </View>
        )}
      </View>
      
      <TouchableOpacity
        style={[
          styles.packButton,
          item.downloaded && styles.installedButton,
          downloadingPacks.has(item.id) && styles.downloadingButton
        ]}
        onPress={() => !item.downloaded && !downloadingPacks.has(item.id) && handleDownloadPack(item.id)}
        disabled={item.downloaded || downloadingPacks.has(item.id)}
      >
        {downloadingPacks.has(item.id) ? (
          <ActivityIndicator size="small" color="#fff" />
        ) : (
          <Text style={[styles.packButtonText, item.downloaded && styles.installedButtonText]}>
            {item.downloaded ? 'Installed' : 'Download'}
          </Text>
        )}
      </TouchableOpacity>
    </View>
  );

  const renderPreferenceItem = (title: string, subtitle: string, value: string, onPress: () => void) => (
    <TouchableOpacity style={styles.preferenceItem} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.preferenceInfo}>
        <Text style={styles.preferenceTitle}>{title}</Text>
        <Text style={styles.preferenceSubtitle}>{subtitle}</Text>
      </View>
      <View style={styles.preferenceValue}>
        <Text style={styles.preferenceValueText}>{value}</Text>
        <MaterialIcons name="chevron-right" size={20} color="#666" />
      </View>
    </TouchableOpacity>
  );

  const renderSwitchItem = (title: string, subtitle: string, value: boolean, onValueChange: (value: boolean) => void) => (
    <View style={styles.switchItem}>
      <View style={styles.switchInfo}>
        <Text style={styles.switchTitle}>{title}</Text>
        <Text style={styles.switchSubtitle}>{subtitle}</Text>
      </View>
      <Switch
        value={value}
        onValueChange={onValueChange}
        trackColor={{ false: '#E0E0E0', true: '#C8E6C9' }}
        thumbColor={value ? '#4CAF50' : '#fff'}
      />
    </View>
  );

  if (loading) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color="#6366f1" />
        <Text style={styles.loadingText}>Loading language settings...</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <LinearGradient
          colors={['#6366f1', '#8b5cf6']}
          style={styles.header}
        >
          <Text style={styles.headerTitle}>Language & Region</Text>
          <Text style={styles.headerSubtitle}>Customize your language preferences</Text>
        </LinearGradient>

        {/* Current Language */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Current Language</Text>
          <TouchableOpacity
            style={styles.currentLanguageCard}
            onPress={() => setShowLanguageModal(true)}
            activeOpacity={0.8}
          >
            <Animated.View style={[styles.currentLanguageContent, { transform: [{ scale: scaleAnimation }] }]}>
              <Text style={styles.currentLanguageFlag}>
                {languages.find(l => l.code === currentLanguage)?.flag || '🌐'}
              </Text>
              <View style={styles.currentLanguageText}>
                <Text style={styles.currentLanguageName}>
                  {languages.find(l => l.code === currentLanguage)?.native_name || 'English'}
                </Text>
                <Text style={styles.currentLanguageSubtext}>
                  {languages.find(l => l.code === currentLanguage)?.name || 'English'}
                </Text>
              </View>
              <MaterialIcons name="edit" size={24} color="#6366f1" />
            </Animated.View>
          </TouchableOpacity>
        </View>

        {/* Regional Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Regional Settings</Text>
          
          {renderPreferenceItem(
            'Date Format',
            'How dates are displayed',
            new Date().toLocaleDateString(currentLanguage),
            () => Alert.alert('Coming Soon', 'Date format customization')
          )}
          
          {renderPreferenceItem(
            'Time Format',
            'How time is displayed',
            new Date().toLocaleTimeString(currentLanguage, { 
              hour: '2-digit', 
              minute: '2-digit',
              hour12: localePreferences.timeFormat === '12h'
            }),
            () => Alert.alert('Coming Soon', 'Time format customization')
          )}
          
          {renderPreferenceItem(
            'Number Format',
            'How numbers are formatted',
            (12345.67).toLocaleString(currentLanguage),
            () => Alert.alert('Coming Soon', 'Number format customization')
          )}
          
          {renderPreferenceItem(
            'Currency',
            'Default currency format',
            (99.99).toLocaleString(currentLanguage, {
              style: 'currency',
              currency: localePreferences.currencyFormat
            }),
            () => Alert.alert('Coming Soon', 'Currency customization')
          )}
        </View>

        {/* Auto-Detection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Smart Features</Text>
          
          {renderSwitchItem(
            'Auto-detect Language',
            'Detect language from system settings',
            autoDetectEnabled,
            setAutoDetectEnabled
          )}
          
          {renderSwitchItem(
            'Offline Mode',
            'Use downloaded translations when offline',
            offlineModeEnabled,
            setOfflineModeEnabled
          )}
        </View>

        {/* Translation Packs */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Translation Packs</Text>
          <TouchableOpacity
            style={styles.downloadMoreButton}
            onPress={() => setShowDownloadModal(true)}
            activeOpacity={0.7}
          >
            <MaterialIcons name="cloud-download" size={24} color="#6366f1" />
            <Text style={styles.downloadMoreText}>Download More Languages</Text>
          </TouchableOpacity>
          
          <FlatList
            data={translationPacks.slice(0, 3)}
            renderItem={renderTranslationPack}
            keyExtractor={item => item.id}
            scrollEnabled={false}
          />
        </View>

        {/* Import/Export */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Backup & Restore</Text>
          
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={handleExportTranslations}
              activeOpacity={0.7}
            >
              <MaterialIcons name="file-download" size={24} color="#6366f1" />
              <Text style={styles.actionButtonText}>Export</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.actionButton}
              onPress={handleImportTranslations}
              activeOpacity={0.7}
            >
              <MaterialIcons name="file-upload" size={24} color="#6366f1" />
              <Text style={styles.actionButtonText}>Import</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={{ height: 50 }} />
      </ScrollView>

      {/* Language Selection Modal */}
      <Modal
        visible={showLanguageModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={[styles.modalContainer, { paddingTop: insets.top }]}>
          <View style={styles.modalHeader}>
            <TouchableOpacity
              onPress={() => setShowLanguageModal(false)}
              style={styles.modalCloseButton}
            >
              <MaterialIcons name="close" size={24} color="#333" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Select Language</Text>
            <View style={styles.modalCloseButton} />
          </View>
          
          <FlatList
            data={filteredLanguages}
            renderItem={renderLanguageItem}
            keyExtractor={item => item.code}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.languageList}
          />
        </View>
      </Modal>

      {/* Download Modal */}
      <Modal
        visible={showDownloadModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={[styles.modalContainer, { paddingTop: insets.top }]}>
          <View style={styles.modalHeader}>
            <TouchableOpacity
              onPress={() => setShowDownloadModal(false)}
              style={styles.modalCloseButton}
            >
              <MaterialIcons name="close" size={24} color="#333" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Download Translation Packs</Text>
            <View style={styles.modalCloseButton} />
          </View>
          
          <FlatList
            data={translationPacks}
            renderItem={renderTranslationPack}
            keyExtractor={item => item.id}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.translationPacksList}
          />
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6b7280',
  },
  header: {
    padding: 24,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#e0e7ff',
  },
  section: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 16,
  },
  currentLanguageCard: {
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  currentLanguageContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  currentLanguageFlag: {
    fontSize: 32,
    marginRight: 16,
  },
  currentLanguageText: {
    flex: 1,
  },
  currentLanguageName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  currentLanguageSubtext: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  preferenceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  preferenceInfo: {
    flex: 1,
  },
  preferenceTitle: {
    fontSize: 16,
    color: '#1f2937',
    fontWeight: '500',
  },
  preferenceSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  preferenceValue: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  preferenceValueText: {
    fontSize: 14,
    color: '#6366f1',
    marginRight: 8,
    fontWeight: '500',
  },
  switchItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  switchInfo: {
    flex: 1,
  },
  switchTitle: {
    fontSize: 16,
    color: '#1f2937',
    fontWeight: '500',
  },
  switchSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  downloadMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f0f4ff',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  downloadMoreText: {
    marginLeft: 8,
    fontSize: 16,
    color: '#6366f1',
    fontWeight: '500',
  },
  translationPack: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  packInfo: {
    flex: 1,
  },
  packName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1f2937',
  },
  packDetails: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  progressContainer: {
    marginTop: 8,
    height: 4,
    backgroundColor: '#e5e7eb',
    borderRadius: 2,
    position: 'relative',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#6366f1',
    borderRadius: 2,
  },
  progressText: {
    position: 'absolute',
    right: 0,
    top: -18,
    fontSize: 10,
    color: '#6366f1',
  },
  packButton: {
    backgroundColor: '#6366f1',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    minWidth: 80,
    alignItems: 'center',
  },
  installedButton: {
    backgroundColor: '#10b981',
  },
  downloadingButton: {
    backgroundColor: '#f59e0b',
  },
  packButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  installedButtonText: {
    color: '#fff',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  actionButton: {
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    minWidth: 100,
  },
  actionButtonText: {
    marginTop: 8,
    fontSize: 14,
    color: '#6366f1',
    fontWeight: '500',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  modalCloseButton: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  languageList: {
    paddingVertical: 8,
  },
  translationPacksList: {
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  languageItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  selectedLanguage: {
    backgroundColor: '#f0f4ff',
  },
  languageInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  languageFlag: {
    fontSize: 24,
    marginRight: 16,
  },
  languageText: {
    flex: 1,
  },
  languageName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1f2937',
  },
  languageSubtext: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
});

export default InternationalizationMobile;