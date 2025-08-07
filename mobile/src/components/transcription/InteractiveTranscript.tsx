/**
 * Interactive Transcript Component for React Native
 * Provides clickable segments with audio synchronization
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  Switch,
  FlatList,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { EnhancedAudioPlayer, AudioPlayerRef, setupPlayer } from '../audio/EnhancedAudioPlayer';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../providers/ThemeProvider';

interface TranscriptSegment {
  id: string | number;
  text: string;
  start_time: number;
  end_time: number;
  speaker?: string;
  confidence?: number;
}

interface InteractiveTranscriptProps {
  segments: TranscriptSegment[];
  audioUrl: string;
  audioTitle?: string;
}

export const InteractiveTranscript: React.FC<InteractiveTranscriptProps> = ({
  segments,
  audioUrl,
  audioTitle = 'Transcript Audio',
}) => {
  const { theme, styles: themeStyles } = useTheme();
  const audioPlayerRef = useRef<AudioPlayerRef>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSegmentId, setSelectedSegmentId] = useState<string | number | null>(null);
  const [autoHighlight, setAutoHighlight] = useState(true);
  const [showTimestamps, setShowTimestamps] = useState(true);
  const [showSpeakers, setShowSpeakers] = useState(true);
  const flatListRef = useRef<FlatList>(null);

  // Create styles with theme
  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.backgroundSecondary,
    },
    audioPlayerContainer: {
      backgroundColor: theme.colors.backgroundPrimary,
      marginBottom: theme.spacing[2],
    },
    controls: {
      backgroundColor: theme.colors.backgroundPrimary,
      paddingHorizontal: theme.spacing[4],
      paddingVertical: theme.spacing[2],
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.borderLight,
    },
    searchContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: theme.colors.backgroundTertiary,
      borderRadius: theme.borderRadius.md,
      paddingHorizontal: theme.spacing[3],
      paddingVertical: theme.spacing[2],
      marginBottom: theme.spacing[2],
    },
    searchIcon: {
      marginRight: theme.spacing[2],
    },
    searchInput: {
      flex: 1,
      fontSize: theme.typography.fontSizes.base,
      color: theme.colors.textPrimary,
    },
    toggles: {
      flexDirection: 'row',
      justifyContent: 'space-around',
    },
    toggle: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    toggleLabel: {
      fontSize: theme.typography.fontSizes.xs,
      color: theme.colors.textSecondary,
      marginRight: theme.spacing[1],
    },
    segmentsList: {
      paddingHorizontal: theme.spacing[4],
      paddingBottom: theme.spacing[5],
    },
    segment: {
      backgroundColor: theme.colors.backgroundPrimary,
      marginVertical: theme.spacing[1],
      padding: theme.spacing[4],
      borderRadius: theme.borderRadius.md,
      borderLeftWidth: 4,
      borderLeftColor: theme.colors.borderLight,
      ...theme.shadows.xs,
    },
    currentSegment: {
      borderLeftColor: theme.colors.transcriptCurrent,
      backgroundColor: theme.colors.warning50,
    },
    selectedSegment: {
      borderLeftColor: theme.colors.primary,
      backgroundColor: theme.colors.primary50,
    },
    segmentHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: theme.spacing[2],
    },
    playButton: {
      flexDirection: 'row',
      alignItems: 'center',
      marginRight: theme.spacing[2],
    },
    timestamp: {
      fontSize: theme.typography.fontSizes.xs,
      color: theme.colors.textSecondary,
      marginLeft: theme.spacing[1],
    },
    speaker: {
      fontSize: theme.typography.fontSizes.sm,
      fontWeight: theme.typography.fontWeights.semibold,
      color: theme.colors.textPrimary,
    },
    segmentText: {
      fontSize: theme.typography.fontSizes.base,
      lineHeight: theme.typography.fontSizes.base * theme.typography.lineHeights.relaxed,
      color: theme.colors.textPrimary,
    },
    highlight: {
      backgroundColor: theme.colors.transcriptHighlight,
      fontWeight: theme.typography.fontWeights.medium,
    },
    lowConfidence: {
      flexDirection: 'row',
      alignItems: 'center',
      marginTop: theme.spacing[1],
    },
    confidenceText: {
      fontSize: theme.typography.fontSizes.xs,
      color: theme.colors.warning,
      marginLeft: theme.spacing[1],
    },
  });

  // Setup audio player on mount
  useEffect(() => {
    setupPlayer();
  }, []);

  // Calculate current segment based on playback time
  const getCurrentSegmentIndex = useCallback(() => {
    const index = segments.findIndex(
      segment => currentTime >= segment.start_time && currentTime <= segment.end_time
    );
    return index;
  }, [currentTime, segments]);

  // Handle audio time updates
  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time);
    
    if (autoHighlight) {
      const currentIndex = segments.findIndex(
        segment => time >= segment.start_time && time <= segment.end_time
      );
      
      if (currentIndex !== -1) {
        const currentSegment = segments[currentIndex];
        if (currentSegment.id !== selectedSegmentId) {
          setSelectedSegmentId(currentSegment.id);
          
          // Auto-scroll to current segment
          flatListRef.current?.scrollToIndex({
            index: currentIndex,
            animated: true,
            viewPosition: 0.5,
          });
        }
      }
    }
  }, [autoHighlight, segments, selectedSegmentId]);

  // Handle segment press
  const handleSegmentPress = useCallback(async (segment: TranscriptSegment) => {
    setSelectedSegmentId(segment.id);
    await audioPlayerRef.current?.jumpToTime(segment.start_time, true);
  }, []);

  // Filter segments based on search
  const filteredSegments = segments.filter(segment => {
    if (!searchQuery) return true;
    return segment.text.toLowerCase().includes(searchQuery.toLowerCase());
  });

  // Format time for display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Render individual segment
  const renderSegment = ({ item: segment, index }: { item: TranscriptSegment; index: number }) => {
    const isCurrentSegment = autoHighlight && currentTime >= segment.start_time && currentTime <= segment.end_time;
    const isSelected = segment.id === selectedSegmentId;

    return (
      <TouchableOpacity
        style={[
          styles.segment,
          isCurrentSegment && styles.currentSegment,
          isSelected && styles.selectedSegment,
        ]}
        onPress={() => handleSegmentPress(segment)}
        activeOpacity={0.7}
      >
        <View style={styles.segmentHeader}>
          <TouchableOpacity
            style={styles.playButton}
            onPress={() => handleSegmentPress(segment)}
          >
            <Ionicons
              name={isCurrentSegment ? 'volume-high' : 'play-circle'}
              size={24}
              color={isCurrentSegment ? '#007AFF' : '#666'}
            />
            {showTimestamps && (
              <Text style={styles.timestamp}>{formatTime(segment.start_time)}</Text>
            )}
          </TouchableOpacity>

          {showSpeakers && segment.speaker && (
            <Text style={styles.speaker}>{segment.speaker}</Text>
          )}
        </View>

        <Text style={styles.segmentText}>
          {searchQuery ? highlightText(segment.text, searchQuery) : segment.text}
        </Text>

        {segment.confidence && segment.confidence < 0.8 && (
          <View style={styles.lowConfidence}>
            <Ionicons name="warning" size={12} color="#FF9500" />
            <Text style={styles.confidenceText}>Low confidence</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* Audio Player */}
      <View style={styles.audioPlayerContainer}>
        <EnhancedAudioPlayer
          ref={audioPlayerRef}
          audioUrl={audioUrl}
          title={audioTitle}
          onTimeUpdate={handleTimeUpdate}
        />
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        <View style={styles.searchContainer}>
          <Ionicons name="search" size={20} color="#666" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search transcript..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholderTextColor="#999"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color="#666" />
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.toggles}>
          <View style={styles.toggle}>
            <Text style={styles.toggleLabel}>Auto-highlight</Text>
            <Switch
              value={autoHighlight}
              onValueChange={setAutoHighlight}
              trackColor={{ false: '#767577', true: '#81b0ff' }}
              thumbColor={autoHighlight ? '#007AFF' : '#f4f3f4'}
            />
          </View>

          <View style={styles.toggle}>
            <Text style={styles.toggleLabel}>Timestamps</Text>
            <Switch
              value={showTimestamps}
              onValueChange={setShowTimestamps}
              trackColor={{ false: '#767577', true: '#81b0ff' }}
              thumbColor={showTimestamps ? '#007AFF' : '#f4f3f4'}
            />
          </View>

          <View style={styles.toggle}>
            <Text style={styles.toggleLabel}>Speakers</Text>
            <Switch
              value={showSpeakers}
              onValueChange={setShowSpeakers}
              trackColor={{ false: '#767577', true: '#81b0ff' }}
              thumbColor={showSpeakers ? '#007AFF' : '#f4f3f4'}
            />
          </View>
        </View>
      </View>

      {/* Transcript Segments */}
      <FlatList
        ref={flatListRef}
        data={filteredSegments}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderSegment}
        contentContainerStyle={styles.segmentsList}
        onScrollToIndexFailed={() => {
          // Handle scroll failure gracefully
        }}
      />
    </KeyboardAvoidingView>
  );
};

// Utility function to highlight search terms
const highlightText = (text: string, query: string): React.ReactNode => {
  if (!query) return text;

  const parts = text.split(new RegExp(`(${query})`, 'gi'));
  return (
    <Text>
      {parts.map((part, index) =>
        part.toLowerCase() === query.toLowerCase() ? (
          <Text key={index} style={styles.highlight}>
            {part}
          </Text>
        ) : (
          part
        )
      )}
    </Text>
  );
};

