/**
 * AI Assistant Component for React Native
 * Mobile-optimized AI writing assistant with touch gestures and native features
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  Platform,
  Alert,
  Share,
  Vibration,
  KeyboardAvoidingView,
  Modal,
  FlatList,
  Switch,
  Animated,
  PanResponder,
  LayoutAnimation,
  UIManager,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Voice from '@react-native-voice/voice';
import * as Haptics from 'expo-haptics';
import * as Clipboard from 'expo-clipboard';
import * as Speech from 'expo-speech';
import { MaterialIcons, Ionicons, FontAwesome5 } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// Types
interface AutoCompletion {
  text: string;
  confidence: number;
  source: 'ai' | 'history' | 'template';
}

interface Suggestion {
  id: string;
  type: string;
  text: string;
  confidence: number;
  metadata: any;
}

interface AIAssistantProps {
  value: string;
  onChangeText: (text: string) => void;
  context?: 'transcript' | 'email' | 'document' | 'chat' | 'note';
  placeholder?: string;
  multiline?: boolean;
  numberOfLines?: number;
  maxLength?: number;
  onFocus?: () => void;
  onBlur?: () => void;
  editable?: boolean;
  style?: any;
}

// Constants
const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const SUGGESTION_HEIGHT = 50;
const TOOLBAR_HEIGHT = 60;

const AIAssistant: React.FC<AIAssistantProps> = ({
  value,
  onChangeText,
  context = 'document',
  placeholder = 'Start typing or tap the mic...',
  multiline = true,
  numberOfLines = 4,
  maxLength,
  onFocus,
  onBlur,
  editable = true,
  style,
}) => {
  const insets = useSafeAreaInsets();
  const [completions, setCompletions] = useState<AutoCompletion[]>([]);
  const [showCompletions, setShowCompletions] = useState(false);
  const [selectedCompletionIndex, setSelectedCompletionIndex] = useState(0);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [loadingCompletions, setLoadingCompletions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [autoCompleteEnabled, setAutoCompleteEnabled] = useState(true);
  const [showToolbar, setShowToolbar] = useState(true);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [writingHistory, setWritingHistory] = useState<string[]>([]);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [selectedText, setSelectedText] = useState('');
  const [voiceResults, setVoiceResults] = useState<string[]>([]);
  const textInputRef = useRef<TextInput>(null);
  const completionTimeout = useRef<NodeJS.Timeout>();
  const wsRef = useRef<WebSocket | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const toolbarAnimation = useRef(new Animated.Value(1)).current;
  const completionSlideAnim = useRef(new Animated.Value(0)).current;

  // Voice recognition setup
  useEffect(() => {
    Voice.onSpeechStart = onSpeechStart;
    Voice.onSpeechEnd = onSpeechEnd;
    Voice.onSpeechResults = onSpeechResults;
    Voice.onSpeechPartialResults = onSpeechPartialResults;
    Voice.onSpeechError = onSpeechError;

    loadSettings();
    loadWritingHistory();

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // WebSocket connection for real-time completions
  useEffect(() => {
    if (autoCompleteEnabled) {
      connectWebSocket();
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [autoCompleteEnabled]);

  const connectWebSocket = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (!token) return;

      const ws = new WebSocket(
        `${process.env.API_URL?.replace('http', 'ws')}/api/v1/ai-suggestions/ws/autocomplete?token=${token}`
      );

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onclose = () => {
        setWsConnected(false);
        // Reconnect after delay
        setTimeout(connectWebSocket, 5000);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.completions) {
          setCompletions(
            data.completions.map((text: string, index: number) => ({
              text,
              confidence: data.confidence_scores[index],
              source: 'ai',
            }))
          );
          setShowCompletions(true);
          setLoadingCompletions(false);
          
          // Animate completion slide-in
          Animated.spring(completionSlideAnim, {
            toValue: 1,
            useNativeDriver: true,
          }).start();
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  };

  const loadSettings = async () => {
    try {
      const settings = await AsyncStorage.getItem('ai_assistant_settings');
      if (settings) {
        const parsed = JSON.parse(settings);
        setAutoCompleteEnabled(parsed.autoCompleteEnabled ?? true);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const loadWritingHistory = async () => {
    try {
      const history = await AsyncStorage.getItem('writing_history');
      if (history) {
        setWritingHistory(JSON.parse(history));
      }
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  // Voice recognition handlers
  const onSpeechStart = () => {
    setIsListening(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const onSpeechEnd = () => {
    setIsListening(false);
  };

  const onSpeechResults = (e: any) => {
    if (e.value && e.value[0]) {
      const spokenText = e.value[0];
      const newText = value ? `${value} ${spokenText}` : spokenText;
      onChangeText(newText);
      
      // Save to history
      addToHistory(spokenText);
    }
  };

  const onSpeechPartialResults = (e: any) => {
    if (e.value) {
      setVoiceResults(e.value);
    }
  };

  const onSpeechError = (e: any) => {
    console.error('Speech recognition error:', e);
    setIsListening(false);
    Alert.alert('Voice Recognition Error', 'Please try again');
  };

  const startListening = async () => {
    try {
      await Voice.start('en-US');
    } catch (error) {
      console.error('Failed to start voice recognition:', error);
    }
  };

  const stopListening = async () => {
    try {
      await Voice.stop();
    } catch (error) {
      console.error('Failed to stop voice recognition:', error);
    }
  };

  // Text change handler with debounced completions
  const handleTextChange = (text: string) => {
    onChangeText(text);
    
    // Clear previous timeout
    if (completionTimeout.current) {
      clearTimeout(completionTimeout.current);
    }
    
    // Get completions after delay
    if (autoCompleteEnabled && text.length > 2) {
      setLoadingCompletions(true);
      completionTimeout.current = setTimeout(() => {
        getCompletions(text);
      }, 300);
    } else {
      setShowCompletions(false);
      Animated.timing(completionSlideAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }).start();
    }
  };

  // Get auto-completions
  const getCompletions = async (text: string) => {
    // Get history-based completions first
    const historyCompletions = getHistoryCompletions(text);
    
    if (wsConnected && wsRef.current) {
      // Use WebSocket for real-time completions
      wsRef.current.send(
        JSON.stringify({
          text,
          context,
          max_completions: 5,
        })
      );
    } else {
      // Fallback to REST API
      try {
        const token = await AsyncStorage.getItem('authToken');
        const response = await fetch(`${process.env.API_URL}/api/v1/ai-suggestions/autocomplete`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            text,
            context,
            max_completions: 5,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          const aiCompletions = data.completions.map((text: string, index: number) => ({
            text,
            confidence: data.confidence_scores[index],
            source: 'ai',
          }));
          
          setCompletions([...historyCompletions, ...aiCompletions]);
          setShowCompletions(true);
          setLoadingCompletions(false);
        }
      } catch (error) {
        console.error('Failed to get completions:', error);
        setLoadingCompletions(false);
      }
    }
  };

  // Get completions from history
  const getHistoryCompletions = (text: string): AutoCompletion[] => {
    if (!text || text.length < 3) return [];
    
    const lastWord = text.split(' ').pop()?.toLowerCase() || '';
    
    return writingHistory
      .filter(h => h.toLowerCase().includes(lastWord))
      .slice(0, 2)
      .map(h => {
        const index = h.toLowerCase().indexOf(lastWord);
        const completion = h.substring(index + lastWord.length);
        return {
          text: completion.split(' ').slice(0, 5).join(' '),
          confidence: 0.8,
          source: 'history' as const,
        };
      });
  };

  // Apply completion
  const applyCompletion = (completion: AutoCompletion) => {
    const newText = value + completion.text;
    onChangeText(newText);
    setShowCompletions(false);
    
    // Haptic feedback
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    // Animate out
    Animated.timing(completionSlideAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: true,
    }).start();
    
    // Focus back to input
    textInputRef.current?.focus();
  };

  // Add to writing history
  const addToHistory = async (text: string) => {
    if (!text || text.length < 10) return;
    
    const newHistory = [text, ...writingHistory.filter(h => h !== text)].slice(0, 50);
    setWritingHistory(newHistory);
    
    try {
      await AsyncStorage.setItem('writing_history', JSON.stringify(newHistory));
    } catch (error) {
      console.error('Failed to save history:', error);
    }
  };

  // Grammar check
  const checkGrammar = async () => {
    if (!value) return;
    
    setLoadingSuggestions(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${process.env.API_URL}/api/v1/ai-suggestions/grammar-check?content=${encodeURIComponent(value)}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.corrections.length === 0) {
          Alert.alert('Grammar Check', 'No errors found! Your writing looks great.');
        } else {
          setSuggestions(data.corrections.map((c: any, i: number) => ({
            id: `grammar_${i}`,
            type: 'grammar_correction',
            text: c.corrected_text,
            confidence: 1.0,
            metadata: c,
          })));
          setShowSuggestions(true);
        }
      }
    } catch (error) {
      console.error('Grammar check failed:', error);
      Alert.alert('Error', 'Failed to check grammar');
    } finally {
      setLoadingSuggestions(false);
    }
  };

  // Summarize content
  const summarizeContent = async () => {
    if (!value || value.length < 50) {
      Alert.alert('Too Short', 'Content must be at least 50 characters to summarize');
      return;
    }
    
    setLoadingSuggestions(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${process.env.API_URL}/api/v1/ai-suggestions/summarize?content=${encodeURIComponent(value)}&length=short`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        Alert.alert('Summary', data.summary);
      }
    } catch (error) {
      console.error('Summarize failed:', error);
      Alert.alert('Error', 'Failed to generate summary');
    } finally {
      setLoadingSuggestions(false);
    }
  };

  // Text-to-speech
  const speakText = () => {
    if (!value) return;
    
    Speech.speak(value, {
      language: 'en',
      pitch: 1.0,
      rate: 0.9,
    });
    
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
  };

  // Share content
  const shareContent = async () => {
    if (!value) return;
    
    try {
      await Share.share({
        message: value,
        title: 'Shared from AI Assistant',
      });
    } catch (error) {
      console.error('Share failed:', error);
    }
  };

  // Toggle toolbar animation
  const toggleToolbar = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setShowToolbar(!showToolbar);
  };

  // Render completions
  const renderCompletions = () => {
    if (!showCompletions || completions.length === 0) return null;
    
    return (
      <Animated.View
        style={[
          styles.completionsContainer,
          {
            transform: [
              {
                translateY: completionSlideAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: [-50, 0],
                }),
              },
            ],
            opacity: completionSlideAnim,
          },
        ]}
      >
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {loadingCompletions ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#6366f1" />
              <Text style={styles.loadingText}>Getting suggestions...</Text>
            </View>
          ) : (
            completions.map((completion, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.completionChip,
                  index === selectedCompletionIndex && styles.completionChipSelected,
                ]}
                onPress={() => applyCompletion(completion)}
              >
                <View style={styles.completionContent}>
                  <Text style={styles.completionText} numberOfLines={1}>
                    {completion.text}
                  </Text>
                  <View style={styles.completionMeta}>
                    <MaterialIcons
                      name={completion.source === 'ai' ? 'auto-awesome' : 'history'}
                      size={12}
                      color="#6366f1"
                    />
                    <Text style={styles.completionConfidence}>
                      {Math.round(completion.confidence * 100)}%
                    </Text>
                  </View>
                </View>
              </TouchableOpacity>
            ))
          )}
        </ScrollView>
      </Animated.View>
    );
  };

  // Render AI toolbar
  const renderToolbar = () => {
    if (!showToolbar) return null;
    
    return (
      <Animated.View
        style={[
          styles.toolbar,
          {
            opacity: toolbarAnimation,
          },
        ]}
      >
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.toolbarContent}
        >
          <TouchableOpacity
            style={[styles.toolButton, isListening && styles.toolButtonActive]}
            onPress={isListening ? stopListening : startListening}
          >
            <MaterialIcons
              name={isListening ? 'mic-off' : 'mic'}
              size={20}
              color={isListening ? '#ef4444' : '#6366f1'}
            />
            <Text style={[styles.toolButtonText, isListening && styles.toolButtonTextActive]}>
              {isListening ? 'Stop' : 'Voice'}
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.toolButton}
            onPress={checkGrammar}
            disabled={!value}
          >
            <MaterialIcons name="spellcheck" size={20} color="#6366f1" />
            <Text style={styles.toolButtonText}>Grammar</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.toolButton}
            onPress={summarizeContent}
            disabled={!value || value.length < 50}
          >
            <MaterialIcons name="summarize" size={20} color="#6366f1" />
            <Text style={styles.toolButtonText}>Summary</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.toolButton}
            onPress={speakText}
            disabled={!value}
          >
            <MaterialIcons name="volume-up" size={20} color="#6366f1" />
            <Text style={styles.toolButtonText}>Speak</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.toolButton}
            onPress={async () => {
              await Clipboard.setStringAsync(value);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              Alert.alert('Copied', 'Text copied to clipboard');
            }}
            disabled={!value}
          >
            <MaterialIcons name="content-copy" size={20} color="#6366f1" />
            <Text style={styles.toolButtonText}>Copy</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.toolButton}
            onPress={shareContent}
            disabled={!value}
          >
            <MaterialIcons name="share" size={20} color="#6366f1" />
            <Text style={styles.toolButtonText}>Share</Text>
          </TouchableOpacity>
        </ScrollView>
        
        <TouchableOpacity
          style={styles.settingsButton}
          onPress={() => setShowQuickActions(true)}
        >
          <MaterialIcons name="more-vert" size={20} color="#6366f1" />
        </TouchableOpacity>
      </Animated.View>
    );
  };

  // Render suggestions modal
  const renderSuggestionsModal = () => (
    <Modal
      visible={showSuggestions}
      animationType="slide"
      transparent
      onRequestClose={() => setShowSuggestions(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={[styles.modalContent, { paddingBottom: insets.bottom }]}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>AI Suggestions</Text>
            <TouchableOpacity onPress={() => setShowSuggestions(false)}>
              <MaterialIcons name="close" size={24} color="#6b7280" />
            </TouchableOpacity>
          </View>
          
          {loadingSuggestions ? (
            <View style={styles.modalLoading}>
              <ActivityIndicator size="large" color="#6366f1" />
              <Text style={styles.modalLoadingText}>Analyzing your text...</Text>
            </View>
          ) : (
            <FlatList
              data={suggestions}
              keyExtractor={(item) => item.id}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.suggestionItem}
                  onPress={() => {
                    onChangeText(item.text);
                    setShowSuggestions(false);
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  }}
                >
                  <View style={styles.suggestionHeader}>
                    <View style={styles.suggestionTypeBadge}>
                      <Text style={styles.suggestionTypeText}>
                        {item.type.replace(/_/g, ' ')}
                      </Text>
                    </View>
                    <Text style={styles.suggestionConfidence}>
                      {Math.round(item.confidence * 100)}%
                    </Text>
                  </View>
                  
                  <Text style={styles.suggestionText}>{item.text}</Text>
                  
                  {item.metadata?.reason && (
                    <Text style={styles.suggestionReason}>{item.metadata.reason}</Text>
                  )}
                  
                  <View style={styles.suggestionActions}>
                    <TouchableOpacity
                      style={styles.suggestionActionButton}
                      onPress={() => {
                        onChangeText(item.text);
                        setShowSuggestions(false);
                      }}
                    >
                      <MaterialIcons name="check" size={20} color="#10b981" />
                      <Text style={styles.suggestionActionText}>Apply</Text>
                    </TouchableOpacity>
                    
                    <TouchableOpacity
                      style={styles.suggestionActionButton}
                      onPress={async () => {
                        await Clipboard.setStringAsync(item.text);
                        Alert.alert('Copied', 'Suggestion copied to clipboard');
                      }}
                    >
                      <MaterialIcons name="content-copy" size={20} color="#6366f1" />
                      <Text style={styles.suggestionActionText}>Copy</Text>
                    </TouchableOpacity>
                  </View>
                </TouchableOpacity>
              )}
              contentContainerStyle={styles.suggestionsList}
            />
          )}
        </View>
      </View>
    </Modal>
  );

  // Render quick actions modal
  const renderQuickActionsModal = () => (
    <Modal
      visible={showQuickActions}
      animationType="fade"
      transparent
      onRequestClose={() => setShowQuickActions(false)}
    >
      <TouchableOpacity
        style={styles.modalOverlay}
        activeOpacity={1}
        onPress={() => setShowQuickActions(false)}
      >
        <View style={styles.quickActionsMenu}>
          <TouchableOpacity
            style={styles.quickActionItem}
            onPress={() => {
              setAutoCompleteEnabled(!autoCompleteEnabled);
              setShowQuickActions(false);
              AsyncStorage.setItem(
                'ai_assistant_settings',
                JSON.stringify({ autoCompleteEnabled: !autoCompleteEnabled })
              );
            }}
          >
            <MaterialIcons name="auto-awesome" size={20} color="#6366f1" />
            <Text style={styles.quickActionText}>Auto-complete</Text>
            <Switch
              value={autoCompleteEnabled}
              onValueChange={setAutoCompleteEnabled}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor="#ffffff"
            />
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.quickActionItem}
            onPress={() => {
              addToHistory(value);
              setShowQuickActions(false);
              Alert.alert('Saved', 'Text saved to history');
            }}
          >
            <MaterialIcons name="history" size={20} color="#6366f1" />
            <Text style={styles.quickActionText}>Save to History</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.quickActionItem}
            onPress={() => {
              onChangeText('');
              setShowQuickActions(false);
            }}
          >
            <MaterialIcons name="clear" size={20} color="#ef4444" />
            <Text style={[styles.quickActionText, { color: '#ef4444' }]}>
              Clear Text
            </Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </Modal>
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.inputContainer}>
        <View style={styles.inputHeader}>
          <View style={styles.inputStatus}>
            {wsConnected && (
              <View style={styles.connectedIndicator}>
                <MaterialIcons name="cloud-done" size={16} color="#10b981" />
                <Text style={styles.connectedText}>AI Connected</Text>
              </View>
            )}
          </View>
          
          <TouchableOpacity onPress={toggleToolbar}>
            <MaterialIcons
              name={showToolbar ? 'keyboard-arrow-down' : 'keyboard-arrow-up'}
              size={24}
              color="#6b7280"
            />
          </TouchableOpacity>
        </View>
        
        <TextInput
          ref={textInputRef}
          value={value}
          onChangeText={handleTextChange}
          placeholder={placeholder}
          placeholderTextColor="#9ca3af"
          multiline={multiline}
          numberOfLines={numberOfLines}
          maxLength={maxLength}
          onFocus={onFocus}
          onBlur={() => {
            onBlur?.();
            // Save to history on blur if text is substantial
            if (value.length > 20) {
              addToHistory(value);
            }
          }}
          editable={editable}
          style={[styles.textInput, style]}
          textAlignVertical="top"
          onSelectionChange={(event) => {
            const { start, end } = event.nativeEvent.selection;
            setCursorPosition(end);
            if (start !== end) {
              setSelectedText(value.substring(start, end));
            } else {
              setSelectedText('');
            }
          }}
        />
        
        {isListening && voiceResults.length > 0 && (
          <View style={styles.voiceResults}>
            <Text style={styles.voiceResultsText}>{voiceResults[0]}</Text>
          </View>
        )}
      </View>
      
      {renderCompletions()}
      {renderToolbar()}
      {renderSuggestionsModal()}
      {renderQuickActionsModal()}
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  inputContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    marginHorizontal: 16,
    marginVertical: 8,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
  },
  inputHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
  },
  inputStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  connectedIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#d1fae5',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  connectedText: {
    marginLeft: 4,
    fontSize: 12,
    color: '#10b981',
    fontWeight: '500',
  },
  textInput: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    fontSize: 16,
    color: '#1f2937',
    minHeight: 100,
    maxHeight: 300,
  },
  voiceResults: {
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  voiceResultsText: {
    fontSize: 14,
    color: '#6b7280',
    fontStyle: 'italic',
  },
  completionsContainer: {
    backgroundColor: '#f9fafb',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#6b7280',
  },
  completionChip: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginHorizontal: 4,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    maxWidth: 200,
  },
  completionChipSelected: {
    borderColor: '#6366f1',
    backgroundColor: '#ede9fe',
  },
  completionContent: {
    flexDirection: 'column',
  },
  completionText: {
    fontSize: 14,
    color: '#1f2937',
    marginBottom: 2,
  },
  completionMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  completionConfidence: {
    marginLeft: 4,
    fontSize: 11,
    color: '#6b7280',
  },
  toolbar: {
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    flexDirection: 'row',
    paddingVertical: 8,
    paddingHorizontal: 16,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
  },
  toolbarContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  toolButton: {
    flexDirection: 'column',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 8,
  },
  toolButtonActive: {
    backgroundColor: '#fee2e2',
  },
  toolButtonText: {
    marginTop: 4,
    fontSize: 11,
    color: '#6b7280',
  },
  toolButtonTextActive: {
    color: '#ef4444',
  },
  settingsButton: {
    marginLeft: 'auto',
    padding: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: SCREEN_HEIGHT * 0.8,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1f2937',
  },
  modalLoading: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  modalLoadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6b7280',
  },
  suggestionsList: {
    paddingVertical: 16,
  },
  suggestionItem: {
    backgroundColor: '#f9fafb',
    marginHorizontal: 16,
    marginBottom: 12,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  suggestionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  suggestionTypeBadge: {
    backgroundColor: '#ede9fe',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  suggestionTypeText: {
    fontSize: 12,
    color: '#6366f1',
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  suggestionConfidence: {
    fontSize: 12,
    color: '#6b7280',
  },
  suggestionText: {
    fontSize: 14,
    color: '#1f2937',
    lineHeight: 20,
    marginBottom: 8,
  },
  suggestionReason: {
    fontSize: 12,
    color: '#6b7280',
    fontStyle: 'italic',
    marginBottom: 12,
  },
  suggestionActions: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
  },
  suggestionActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#ffffff',
    borderRadius: 8,
    marginRight: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  suggestionActionText: {
    marginLeft: 4,
    fontSize: 14,
    color: '#4b5563',
    fontWeight: '500',
  },
  quickActionsMenu: {
    position: 'absolute',
    bottom: TOOLBAR_HEIGHT + 20,
    right: 16,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 8,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    minWidth: 200,
  },
  quickActionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  quickActionText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#1f2937',
  },
});

export default AIAssistant;