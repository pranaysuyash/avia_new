import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal,
  FlatList,
  Animated,
  Dimensions,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import {
  Card,
  Button,
  Avatar,
  Badge,
  Slider,
  Switch,
  ProgressBar,
  Chip,
  FAB,
  Portal,
  Dialog,
  Paragraph,
  Title,
  Subheading,
  Caption,
  Surface,
  Divider,
  List,
  IconButton,
  Menu,
  Provider as PaperProvider,
  DefaultTheme,
  DarkTheme,
  useTheme,
} from 'react-native-paper';
import {
  GestureHandlerRootView,
  PanGestureHandler,
  TapGestureHandler,
  State,
} from 'react-native-gesture-handler';
import MaterialIcons from 'react-native-vector-icons/MaterialIcons';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import { Picker } from '@react-native-picker/picker';
import DocumentPicker from 'react-native-document-picker';
import RNFS from 'react-native-fs';
import Sound from 'react-native-sound';
import Video from 'react-native-video';

const { width, height } = Dimensions.get('window');

interface VoiceProfile {
  id: string;
  name: string;
  language: string;
  country: string;
  gender: string;
  age_range: string;
  style: string;
  accent?: string;
  sample_url?: string;
  description?: string;
  premium: boolean;
}

interface DubbingJob {
  id: string;
  type: string;
  status: string;
  progress: number;
  created_at: string;
  result_url?: string;
  metadata?: any;
}

interface Language {
  code: string;
  name: string;
  native_name: string;
  voice_count: number;
  premium_voices: number;
  popular: boolean;
}

const AIDubbingMobile: React.FC = () => {
  const theme = useTheme();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [jobs, setJobs] = useState<DubbingJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  // Text synthesis state
  const [text, setText] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('en-US');
  const [selectedVoice, setSelectedVoice] = useState('');
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);
  const [volume, setVolume] = useState(1.0);
  const [audioFormat, setAudioFormat] = useState('mp3');
  const [quality, setQuality] = useState('high');
  
  // Video dubbing state
  const [videoFile, setVideoFile] = useState<any>(null);
  const [voiceMapping, setVoiceMapping] = useState<Record<string, string>>({});
  const [dubbingMode, setDubbingMode] = useState('full_replacement');
  const [preserveBackground, setPreserveBackground] = useState(true);
  const [syncLipMovement, setSyncLipMovement] = useState(false);
  const [backgroundMusicVolume, setBackgroundMusicVolume] = useState(0.3);
  
  // Voice cloning state
  const [cloneName, setCloneName] = useState('');
  const [cloneDescription, setCloneDescription] = useState('');
  const [cloneGender, setCloneGender] = useState('female');
  const [cloneAudioFiles, setCloneAudioFiles] = useState<any[]>([]);
  
  // UI state
  const [voiceSelectionVisible, setVoiceSelectionVisible] = useState(false);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [jobsVisible, setJobsVisible] = useState(false);
  const [voiceCloneVisible, setVoiceCloneVisible] = useState(false);
  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null);
  const [menuVisible, setMenuVisible] = useState(false);
  const [expandedAccordion, setExpandedAccordion] = useState<string | null>(null);

  const slideAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const soundRef = useRef<Sound | null>(null);

  useEffect(() => {
    loadInitialData();
    const interval = setInterval(loadJobs, 10000);
    return () => {
      clearInterval(interval);
      if (soundRef.current) {
        soundRef.current.release();
      }
    };
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      
      // Mock data - replace with actual API calls
      const mockVoices: VoiceProfile[] = [
        {
          id: 'voice_en_us_sarah',
          name: 'Sarah',
          language: 'en-US',
          country: 'United States',
          gender: 'female',
          age_range: '20-30',
          style: 'natural',
          description: 'Clear, professional female voice',
          premium: false
        },
        {
          id: 'voice_en_us_john',
          name: 'John',
          language: 'en-US',
          country: 'United States',
          gender: 'male',
          age_range: '30-40',
          style: 'professional',
          description: 'Deep, authoritative male voice',
          premium: true
        },
        {
          id: 'voice_es_es_maria',
          name: 'María',
          language: 'es-ES',
          country: 'Spain',
          gender: 'female',
          age_range: '25-35',
          style: 'conversational',
          description: 'Warm, friendly Spanish voice',
          premium: false
        },
      ];

      const mockLanguages: Language[] = [
        {
          code: 'en-US',
          name: 'English (US)',
          native_name: 'English',
          voice_count: 25,
          premium_voices: 10,
          popular: true
        },
        {
          code: 'es-ES',
          name: 'Spanish (Spain)',
          native_name: 'Español',
          voice_count: 20,
          premium_voices: 12,
          popular: true
        },
        {
          code: 'fr-FR',
          name: 'French (France)',
          native_name: 'Français',
          voice_count: 16,
          premium_voices: 9,
          popular: true
        },
      ];

      setVoices(mockVoices);
      setLanguages(mockLanguages);
    } catch (error) {
      console.error('Failed to load dubbing data:', error);
      Alert.alert('Error', 'Failed to load dubbing data');
    } finally {
      setLoading(false);
    }
  };

  const loadJobs = async () => {
    try {
      // Mock job updates
      const mockJobs: DubbingJob[] = [
        {
          id: 'job_1',
          type: 'text_synthesis',
          status: 'processing',
          progress: 75,
          created_at: new Date().toISOString(),
        },
        {
          id: 'job_2',
          type: 'video_dubbing',
          status: 'completed',
          progress: 100,
          created_at: new Date(Date.now() - 3600000).toISOString(),
          result_url: 'https://example.com/result.mp4'
        },
      ];
      setJobs(mockJobs);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([loadInitialData(), loadJobs()]);
    setRefreshing(false);
  };

  const handleTextSynthesis = async () => {
    if (!text.trim() || !selectedVoice) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      Alert.alert('Success', 'Speech synthesis started successfully');
      setText('');
      loadJobs();
    } catch (error) {
      Alert.alert('Error', 'Failed to start speech synthesis');
    } finally {
      setLoading(false);
    }
  };

  const handleVideoDubbing = async () => {
    if (!videoFile || Object.keys(voiceMapping).length === 0) {
      Alert.alert('Error', 'Please upload a video and configure voice mapping');
      return;
    }

    try {
      setLoading(true);
      
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      Alert.alert('Success', 'Video dubbing started successfully');
      setVideoFile(null);
      setVoiceMapping({});
      loadJobs();
    } catch (error) {
      Alert.alert('Error', 'Failed to start video dubbing');
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceCloning = async () => {
    if (!cloneName.trim() || cloneAudioFiles.length === 0) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      Alert.alert('Success', 'Voice cloning started successfully');
      setVoiceCloneVisible(false);
      setCloneName('');
      setCloneDescription('');
      setCloneAudioFiles([]);
      loadJobs();
    } catch (error) {
      Alert.alert('Error', 'Failed to start voice cloning');
    } finally {
      setLoading(false);
    }
  };

  const pickVideoFile = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.video],
        allowMultiSelection: false,
      });
      
      if (result && result.length > 0) {
        setVideoFile(result[0]);
      }
    } catch (error) {
      if (!DocumentPicker.isCancel(error)) {
        Alert.alert('Error', 'Failed to pick video file');
      }
    }
  };

  const pickAudioFiles = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.audio],
        allowMultiSelection: true,
      });
      
      if (result) {
        setCloneAudioFiles(result);
      }
    } catch (error) {
      if (!DocumentPicker.isCancel(error)) {
        Alert.alert('Error', 'Failed to pick audio files');
      }
    }
  };

  const playVoiceSample = async (voiceId: string, sampleUrl?: string) => {
    if (currentlyPlaying === voiceId) {
      if (soundRef.current) {
        soundRef.current.stop();
        soundRef.current.release();
        soundRef.current = null;
      }
      setCurrentlyPlaying(null);
      return;
    }

    if (sampleUrl) {
      if (soundRef.current) {
        soundRef.current.release();
      }
      
      soundRef.current = new Sound(sampleUrl, Sound.MAIN_BUNDLE, (error) => {
        if (!error) {
          setCurrentlyPlaying(voiceId);
          soundRef.current?.play((success) => {
            if (success) {
              setCurrentlyPlaying(null);
            }
          });
        }
      });
    }
  };

  const getJobStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#4CAF50';
      case 'processing': return '#FF9800';
      case 'failed': return '#F44336';
      case 'cancelled': return '#9E9E9E';
      default: return '#2196F3';
    }
  };

  const getJobStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return 'check-circle';
      case 'processing': return 'hourglass-empty';
      case 'failed': return 'error';
      case 'cancelled': return 'cancel';
      default: return 'info';
    }
  };

  const renderVoiceCard = ({ item }: { item: VoiceProfile }) => (
    <TouchableOpacity
      style={[
        styles.voiceCard,
        selectedVoice === item.id && styles.selectedVoiceCard
      ]}
      onPress={() => setSelectedVoice(item.id)}
    >
      <View style={styles.voiceCardHeader}>
        <Avatar.Icon 
          size={40} 
          icon="account-voice" 
          style={{ backgroundColor: theme.colors.primary }}
        />
        <View style={styles.voiceInfo}>
          <Text style={[styles.voiceName, { color: theme.colors.onSurface }]}>
            {item.name}
          </Text>
          <Caption>{item.country}</Caption>
        </View>
        {item.premium && (
          <Chip mode="outlined" compact textStyle={{ fontSize: 10 }}>
            Premium
          </Chip>
        )}
      </View>
      
      <Text style={[styles.voiceDescription, { color: theme.colors.onSurfaceVariant }]}>
        {item.description}
      </Text>
      
      <View style={styles.voiceCardFooter}>
        <View style={styles.voiceTags}>
          <Chip mode="outlined" compact textStyle={{ fontSize: 10 }}>
            {item.gender}
          </Chip>
          <Chip mode="outlined" compact textStyle={{ fontSize: 10 }}>
            {item.style}
          </Chip>
        </View>
        
        {item.sample_url && (
          <IconButton
            icon={currentlyPlaying === item.id ? 'pause' : 'play'}
            size={20}
            onPress={() => playVoiceSample(item.id, item.sample_url)}
          />
        )}
      </View>
    </TouchableOpacity>
  );

  const renderJobCard = ({ item }: { item: DubbingJob }) => (
    <Surface style={styles.jobCard} elevation={2}>
      <View style={styles.jobHeader}>
        <MaterialIcons 
          name={getJobStatusIcon(item.status)} 
          size={24} 
          color={getJobStatusColor(item.status)}
        />
        <View style={styles.jobInfo}>
          <Text style={[styles.jobTitle, { color: theme.colors.onSurface }]}>
            {item.type.replace('_', ' ').toUpperCase()} Job
          </Text>
          <Caption>
            Created: {new Date(item.created_at).toLocaleDateString()}
          </Caption>
        </View>
        <Badge 
          style={{ backgroundColor: getJobStatusColor(item.status) }}
          size={20}
        />
      </View>
      
      {item.status === 'processing' && (
        <View style={styles.jobProgress}>
          <ProgressBar 
            progress={item.progress / 100} 
            color={theme.colors.primary}
            style={{ marginVertical: 8 }}
          />
          <Caption>{item.progress}% complete</Caption>
        </View>
      )}
      
      {item.result_url && item.status === 'completed' && (
        <Button
          mode="outlined"
          icon="download"
          style={{ marginTop: 8 }}
          onPress={() => {
            // Handle download
            Alert.alert('Download', 'Download functionality would be implemented here');
          }}
        >
          Download
        </Button>
      )}
    </Surface>
  );

  const renderTabContent = () => {
    switch (selectedTab) {
      case 0: // Text to Speech
        return (
          <ScrollView style={styles.tabContent}>
            <Surface style={styles.section} elevation={1}>
              <Title>Text Content</Title>
              <TextInput
                style={[styles.textInput, { 
                  color: theme.colors.onSurface,
                  borderColor: theme.colors.outline 
                }]}
                multiline
                numberOfLines={6}
                value={text}
                onChangeText={setText}
                placeholder="Enter your text here..."
                placeholderTextColor={theme.colors.onSurfaceVariant}
              />
              
              <View style={styles.textStats}>
                <Chip mode="outlined" compact>{text.length} characters</Chip>
                <Chip mode="outlined" compact>~{Math.ceil(text.length / 5)} words</Chip>
                <Chip mode="outlined" compact>~{Math.ceil(text.length * 0.08)}s duration</Chip>
              </View>
            </Surface>

            <Surface style={styles.section} elevation={1}>
              <Title>Language & Voice</Title>
              
              <View style={styles.pickerContainer}>
                <Text style={[styles.label, { color: theme.colors.onSurface }]}>Language</Text>
                <Picker
                  selectedValue={selectedLanguage}
                  onValueChange={setSelectedLanguage}
                  style={[styles.picker, { color: theme.colors.onSurface }]}
                >
                  {languages.map((lang) => (
                    <Picker.Item 
                      key={lang.code} 
                      label={`${lang.name} (${lang.voice_count} voices)`} 
                      value={lang.code} 
                    />
                  ))}
                </Picker>
              </View>

              <Button
                mode="outlined"
                icon="account-voice"
                style={{ marginVertical: 8 }}
                onPress={() => setVoiceSelectionVisible(true)}
              >
                {selectedVoice ? 
                  voices.find(v => v.id === selectedVoice)?.name || 'Select Voice' :
                  'Select Voice'
                }
              </Button>
            </Surface>

            <Surface style={styles.section} elevation={1}>
              <TouchableOpacity
                style={styles.accordionHeader}
                onPress={() => setExpandedAccordion(
                  expandedAccordion === 'advanced' ? null : 'advanced'
                )}
              >
                <Title>Advanced Settings</Title>
                <MaterialIcons 
                  name={expandedAccordion === 'advanced' ? 'expand-less' : 'expand-more'} 
                  size={24} 
                  color={theme.colors.onSurface}
                />
              </TouchableOpacity>

              {expandedAccordion === 'advanced' && (
                <View style={styles.accordionContent}>
                  <View style={styles.sliderContainer}>
                    <Text style={[styles.sliderLabel, { color: theme.colors.onSurface }]}>
                      Speed: {speed.toFixed(1)}x
                    </Text>
                    <Slider
                      style={styles.slider}
                      minimumValue={0.5}
                      maximumValue={2.0}
                      step={0.1}
                      value={speed}
                      onValueChange={setSpeed}
                      thumbStyle={{ backgroundColor: theme.colors.primary }}
                      trackStyle={{ backgroundColor: theme.colors.outline }}
                      minimumTrackTintColor={theme.colors.primary}
                    />
                  </View>

                  <View style={styles.sliderContainer}>
                    <Text style={[styles.sliderLabel, { color: theme.colors.onSurface }]}>
                      Pitch: {pitch.toFixed(1)}x
                    </Text>
                    <Slider
                      style={styles.slider}
                      minimumValue={0.5}
                      maximumValue={2.0}
                      step={0.1}
                      value={pitch}
                      onValueChange={setPitch}
                      thumbStyle={{ backgroundColor: theme.colors.primary }}
                      trackStyle={{ backgroundColor: theme.colors.outline }}
                      minimumTrackTintColor={theme.colors.primary}
                    />
                  </View>

                  <View style={styles.sliderContainer}>
                    <Text style={[styles.sliderLabel, { color: theme.colors.onSurface }]}>
                      Volume: {volume.toFixed(1)}x
                    </Text>
                    <Slider
                      style={styles.slider}
                      minimumValue={0.1}
                      maximumValue={2.0}
                      step={0.1}
                      value={volume}
                      onValueChange={setVolume}
                      thumbStyle={{ backgroundColor: theme.colors.primary }}
                      trackStyle={{ backgroundColor: theme.colors.outline }}
                      minimumTrackTintColor={theme.colors.primary}
                    />
                  </View>

                  <View style={styles.pickerContainer}>
                    <Text style={[styles.label, { color: theme.colors.onSurface }]}>Quality</Text>
                    <Picker
                      selectedValue={quality}
                      onValueChange={setQuality}
                      style={[styles.picker, { color: theme.colors.onSurface }]}
                    >
                      <Picker.Item label="Standard" value="standard" />
                      <Picker.Item label="High" value="high" />
                      <Picker.Item label="Premium" value="premium" />
                      <Picker.Item label="Studio" value="studio" />
                    </Picker>
                  </View>

                  <View style={styles.pickerContainer}>
                    <Text style={[styles.label, { color: theme.colors.onSurface }]}>Format</Text>
                    <Picker
                      selectedValue={audioFormat}
                      onValueChange={setAudioFormat}
                      style={[styles.picker, { color: theme.colors.onSurface }]}
                    >
                      <Picker.Item label="MP3" value="mp3" />
                      <Picker.Item label="WAV" value="wav" />
                      <Picker.Item label="FLAC" value="flac" />
                      <Picker.Item label="OGG" value="ogg" />
                    </Picker>
                  </View>
                </View>
              )}
            </Surface>

            <View style={styles.actionContainer}>
              <Button
                mode="contained"
                icon="play-arrow"
                loading={loading}
                disabled={loading || !text.trim() || !selectedVoice}
                onPress={handleTextSynthesis}
                style={styles.actionButton}
              >
                Generate Speech
              </Button>
            </View>
          </ScrollView>
        );

      case 1: // Video Dubbing
        return (
          <ScrollView style={styles.tabContent}>
            <Surface style={styles.section} elevation={1}>
              <Title>Video Upload</Title>
              
              <TouchableOpacity
                style={[styles.uploadArea, { borderColor: theme.colors.outline }]}
                onPress={pickVideoFile}
              >
                {videoFile ? (
                  <View style={styles.uploadedFile}>
                    <MaterialIcons name="video-file" size={48} color={theme.colors.primary} />
                    <Text style={[styles.fileName, { color: theme.colors.onSurface }]}>
                      {videoFile.name}
                    </Text>
                    <Caption>{(videoFile.size / (1024 * 1024)).toFixed(2)} MB</Caption>
                  </View>
                ) : (
                  <View style={styles.uploadPrompt}>
                    <MaterialIcons name="cloud-upload" size={48} color={theme.colors.onSurfaceVariant} />
                    <Text style={[styles.uploadText, { color: theme.colors.onSurface }]}>
                      Upload Video File
                    </Text>
                    <Caption>Tap to select a video for dubbing</Caption>
                  </View>
                )}
              </TouchableOpacity>
            </Surface>

            {videoFile && (
              <Surface style={styles.section} elevation={1}>
                <Title>Voice Mapping</Title>
                <Paragraph>Map detected speakers to voice profiles</Paragraph>
                
                {/* Mock speaker detection */}
                {['Speaker 1 (Male)', 'Speaker 2 (Female)', 'Narrator'].map((speaker) => (
                  <View key={speaker} style={styles.speakerMapping}>
                    <View style={styles.speakerInfo}>
                      <MaterialIcons name="headset" size={24} color={theme.colors.primary} />
                      <Text style={[styles.speakerName, { color: theme.colors.onSurface }]}>
                        {speaker}
                      </Text>
                    </View>
                    
                    <Button
                      mode="outlined"
                      compact
                      onPress={() => setVoiceSelectionVisible(true)}
                    >
                      {voiceMapping[speaker] ? 
                        voices.find(v => v.id === voiceMapping[speaker])?.name || 'Select' :
                        'Select Voice'
                      }
                    </Button>
                  </View>
                ))}
              </Surface>
            )}

            <View style={styles.actionContainer}>
              <Button
                mode="contained"
                icon="movie"
                loading={loading}
                disabled={loading || !videoFile || Object.keys(voiceMapping).length === 0}
                onPress={handleVideoDubbing}
                style={styles.actionButton}
              >
                Start Dubbing
              </Button>
            </View>
          </ScrollView>
        );

      case 2: // Voice Cloning
        return (
          <ScrollView style={styles.tabContent}>
            <Surface style={styles.section} elevation={1}>
              <Title>Custom Voice Cloning</Title>
              <Paragraph>Create a personalized voice profile from your audio samples</Paragraph>
              
              <Button
                mode="contained"
                icon="plus"
                onPress={() => setVoiceCloneVisible(true)}
                style={{ marginTop: 16 }}
              >
                Start Voice Cloning
              </Button>
            </Surface>

            <Surface style={styles.section} elevation={1}>
              <Title>Your Custom Voices</Title>
              
              <View style={styles.customVoiceItem}>
                <Avatar.Icon size={40} icon="account-plus" />
                <View style={styles.customVoiceInfo}>
                  <Text style={[styles.customVoiceName, { color: theme.colors.onSurface }]}>
                    My Voice Clone
                  </Text>
                  <Caption>Created 2 days ago • English (US) • Female</Caption>
                </View>
                <Chip mode="outlined" compact>Training</Chip>
              </View>
            </Surface>
          </ScrollView>
        );

      case 3: // Job History
        return (
          <FlatList
            data={jobs}
            renderItem={renderJobCard}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.jobsList}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                colors={[theme.colors.primary]}
              />
            }
          />
        );

      default:
        return null;
    }
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PaperProvider theme={isDarkMode ? DarkTheme : DefaultTheme}>
        <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
          <StatusBar 
            backgroundColor={theme.colors.surface} 
            barStyle={isDarkMode ? 'light-content' : 'dark-content'} 
          />
          
          {/* Header */}
          <Surface style={styles.header} elevation={2}>
            <View style={styles.headerContent}>
              <Title style={{ color: theme.colors.onSurface }}>AI Dubbing Studio</Title>
              <View style={styles.headerActions}>
                <IconButton
                  icon="refresh"
                  onPress={onRefresh}
                  disabled={loading}
                />
                <Menu
                  visible={menuVisible}
                  onDismiss={() => setMenuVisible(false)}
                  anchor={
                    <IconButton
                      icon="dots-vertical"
                      onPress={() => setMenuVisible(true)}
                    />
                  }
                >
                  <Menu.Item
                    onPress={() => {
                      setMenuVisible(false);
                      setSettingsVisible(true);
                    }}
                    title="Settings"
                    icon="settings"
                  />
                  <Menu.Item
                    onPress={() => {
                      setMenuVisible(false);
                      setIsDarkMode(!isDarkMode);
                    }}
                    title={isDarkMode ? 'Light Mode' : 'Dark Mode'}
                    icon={isDarkMode ? 'white-balance-sunny' : 'moon-waning-crescent'}
                  />
                </Menu>
              </View>
            </View>
          </Surface>

          {/* Tab Navigation */}
          <Surface style={styles.tabBar} elevation={1}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.tabs}>
                {[
                  { label: 'Text to Speech', icon: 'record-voice-over' },
                  { label: 'Video Dubbing', icon: 'movie' },
                  { label: 'Voice Cloning', icon: 'person-add' },
                  { label: 'Jobs', icon: 'history' }
                ].map((tab, index) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.tab,
                      selectedTab === index && styles.activeTab,
                      { borderBottomColor: theme.colors.primary }
                    ]}
                    onPress={() => setSelectedTab(index)}
                  >
                    <MaterialIcons 
                      name={tab.icon as any} 
                      size={20} 
                      color={selectedTab === index ? theme.colors.primary : theme.colors.onSurfaceVariant}
                    />
                    <Text 
                      style={[
                        styles.tabText,
                        { 
                          color: selectedTab === index ? theme.colors.primary : theme.colors.onSurfaceVariant 
                        }
                      ]}
                    >
                      {tab.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
          </Surface>

          {/* Content */}
          <View style={styles.content}>
            {renderTabContent()}
          </View>

          {/* Voice Selection Modal */}
          <Modal
            visible={voiceSelectionVisible}
            onRequestClose={() => setVoiceSelectionVisible(false)}
            animationType="slide"
          >
            <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.colors.background }]}>
              <Surface style={styles.modalHeader} elevation={2}>
                <View style={styles.modalHeaderContent}>
                  <Title>Select Voice</Title>
                  <IconButton
                    icon="close"
                    onPress={() => setVoiceSelectionVisible(false)}
                  />
                </View>
              </Surface>
              
              <FlatList
                data={voices.filter(voice => !selectedLanguage || voice.language === selectedLanguage)}
                renderItem={renderVoiceCard}
                keyExtractor={(item) => item.id}
                contentContainerStyle={styles.voicesList}
              />
              
              <Surface style={styles.modalFooter} elevation={2}>
                <Button
                  mode="contained"
                  onPress={() => setVoiceSelectionVisible(false)}
                  disabled={!selectedVoice}
                  style={styles.modalButton}
                >
                  Select Voice
                </Button>
              </Surface>
            </SafeAreaView>
          </Modal>

          {/* Voice Cloning Modal */}
          <Portal>
            <Dialog
              visible={voiceCloneVisible}
              onDismiss={() => setVoiceCloneVisible(false)}
            >
              <Dialog.Title>Create Voice Clone</Dialog.Title>
              <Dialog.Content>
                <TextInput
                  style={[styles.input, { 
                    color: theme.colors.onSurface,
                    borderColor: theme.colors.outline 
                  }]}
                  placeholder="Voice Name"
                  value={cloneName}
                  onChangeText={setCloneName}
                  placeholderTextColor={theme.colors.onSurfaceVariant}
                />
                
                <TextInput
                  style={[styles.input, styles.multilineInput, { 
                    color: theme.colors.onSurface,
                    borderColor: theme.colors.outline 
                  }]}
                  placeholder="Description (Optional)"
                  value={cloneDescription}
                  onChangeText={setCloneDescription}
                  multiline
                  numberOfLines={3}
                  placeholderTextColor={theme.colors.onSurfaceVariant}
                />

                <TouchableOpacity
                  style={[styles.uploadArea, styles.smallUploadArea, { borderColor: theme.colors.outline }]}
                  onPress={pickAudioFiles}
                >
                  {cloneAudioFiles.length > 0 ? (
                    <View style={styles.uploadedFiles}>
                      <MaterialIcons name="audiotrack" size={32} color={theme.colors.primary} />
                      <Text style={[styles.filesCount, { color: theme.colors.onSurface }]}>
                        {cloneAudioFiles.length} files selected
                      </Text>
                    </View>
                  ) : (
                    <View style={styles.uploadPrompt}>
                      <MaterialIcons name="mic" size={32} color={theme.colors.onSurfaceVariant} />
                      <Text style={[styles.uploadText, { color: theme.colors.onSurface }]}>
                        Upload Training Audio
                      </Text>
                      <Caption>Minimum 5 minutes • Clear speech</Caption>
                    </View>
                  )}
                </TouchableOpacity>
              </Dialog.Content>
              <Dialog.Actions>
                <Button onPress={() => setVoiceCloneVisible(false)}>Cancel</Button>
                <Button
                  mode="contained"
                  onPress={handleVoiceCloning}
                  disabled={!cloneName.trim() || cloneAudioFiles.length === 0}
                  loading={loading}
                >
                  Start Cloning
                </Button>
              </Dialog.Actions>
            </Dialog>
          </Portal>

          {/* Floating Action Button */}
          <FAB
            style={[styles.fab, { backgroundColor: theme.colors.primary }]}
            icon="plus"
            onPress={() => setJobsVisible(true)}
          />
        </SafeAreaView>
      </PaperProvider>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerActions: {
    flexDirection: 'row',
  },
  tabBar: {
    paddingVertical: 8,
  },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: 8,
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
    marginHorizontal: 4,
  },
  activeTab: {
    borderBottomWidth: 2,
  },
  tabText: {
    marginLeft: 4,
    fontSize: 12,
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
    padding: 16,
  },
  section: {
    padding: 16,
    marginBottom: 16,
    borderRadius: 8,
  },
  textInput: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginVertical: 8,
    textAlignVertical: 'top',
    fontSize: 16,
    minHeight: 120,
  },
  textStats: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  label: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  pickerContainer: {
    marginVertical: 8,
  },
  picker: {
    borderWidth: 1,
    borderRadius: 8,
    marginTop: 4,
  },
  accordionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  accordionContent: {
    marginTop: 16,
  },
  sliderContainer: {
    marginVertical: 12,
  },
  sliderLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  slider: {
    height: 40,
  },
  actionContainer: {
    padding: 16,
  },
  actionButton: {
    paddingVertical: 4,
  },
  uploadArea: {
    borderWidth: 2,
    borderStyle: 'dashed',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    marginVertical: 8,
  },
  smallUploadArea: {
    padding: 16,
    marginVertical: 12,
  },
  uploadPrompt: {
    alignItems: 'center',
  },
  uploadText: {
    fontSize: 16,
    fontWeight: '500',
    marginTop: 8,
    marginBottom: 4,
  },
  uploadedFile: {
    alignItems: 'center',
  },
  uploadedFiles: {
    alignItems: 'center',
  },
  fileName: {
    fontSize: 16,
    fontWeight: '500',
    marginTop: 8,
  },
  filesCount: {
    fontSize: 16,
    fontWeight: '500',
    marginTop: 8,
  },
  speakerMapping: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  speakerInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  speakerName: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '500',
  },
  customVoiceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  customVoiceInfo: {
    flex: 1,
    marginLeft: 12,
  },
  customVoiceName: {
    fontSize: 16,
    fontWeight: '500',
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  modalHeaderContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalFooter: {
    padding: 16,
  },
  modalButton: {
    paddingVertical: 4,
  },
  voicesList: {
    padding: 16,
  },
  voiceCard: {
    backgroundColor: '#f5f5f5',
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  selectedVoiceCard: {
    borderColor: '#2196F3',
    backgroundColor: '#e3f2fd',
  },
  voiceCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  voiceInfo: {
    flex: 1,
    marginLeft: 12,
  },
  voiceName: {
    fontSize: 16,
    fontWeight: '500',
  },
  voiceDescription: {
    fontSize: 14,
    marginBottom: 12,
  },
  voiceCardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  voiceTags: {
    flexDirection: 'row',
    gap: 8,
  },
  jobsList: {
    padding: 16,
  },
  jobCard: {
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
  },
  jobHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  jobInfo: {
    flex: 1,
    marginLeft: 12,
  },
  jobTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  jobProgress: {
    marginVertical: 8,
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginVertical: 8,
    fontSize: 16,
  },
  multilineInput: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
});

export default AIDubbingMobile;