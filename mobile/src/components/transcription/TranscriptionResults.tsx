import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Modal,
  Alert,
  Platform,
  Share,
  ActivityIndicator,
} from 'react-native';
import { Audio } from 'expo-av';
import Slider from '@react-native-community/slider';
import Icon from 'react-native-vector-icons/MaterialIcons';
import styles from './styles';

interface Entity {
  text: string;
  label: string;
  start: number;
  end: number;
}

interface Speaker {
  id: string;
  name: string;
  color: string;
}

interface TranscriptSegment {
  id: string;
  speaker?: string;
  text: string;
  start: number;
  end: number;
  entities?: Entity[];
}

interface TranscriptionResultsProps {
  transcriptId: string;
  audioUrl?: string;
  segments: TranscriptSegment[];
  speakers?: Speaker[];
  language?: string;
  onSave?: (updatedSegments: TranscriptSegment[]) => void;
  onExport?: (format: string) => void;
}

const TranscriptionResults: React.FC<TranscriptionResultsProps> = ({
  transcriptId,
  audioUrl,
  segments: initialSegments,
  speakers = [],
  language = 'en',
  onSave,
  onExport,
}) => {
  const [segments, setSegments] = useState<TranscriptSegment[]>(initialSegments);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [editingSegment, setEditingSegment] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showExportModal, setShowExportModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedEntities, setSelectedEntities] = useState<Set<string>>(new Set());
  
  const soundRef = useRef<Audio.Sound | null>(null);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    loadAudio();
    return () => {
      if (soundRef.current) {
        soundRef.current.unloadAsync();
      }
    };
  }, [audioUrl]);

  const loadAudio = async () => {
    if (!audioUrl) return;
    
    try {
      setIsLoading(true);
      const { sound } = await Audio.Sound.createAsync(
        { uri: audioUrl },
        { shouldPlay: false }
      );
      soundRef.current = sound;
      
      const status = await sound.getStatusAsync();
      if (status.isLoaded) {
        setDuration(status.durationMillis || 0);
      }
      
      sound.setOnPlaybackStatusUpdate(onPlaybackStatusUpdate);
    } catch (error) {
      Alert.alert('Error', 'Failed to load audio file');
      console.error('Audio loading error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const onPlaybackStatusUpdate = (status: any) => {
    if (status.isLoaded) {
      setCurrentTime(status.positionMillis || 0);
      setIsPlaying(status.isPlaying);
      
      if (status.didJustFinish) {
        setIsPlaying(false);
        setCurrentTime(0);
      }
    }
  };

  const togglePlayPause = async () => {
    if (!soundRef.current) return;
    
    if (isPlaying) {
      await soundRef.current.pauseAsync();
    } else {
      await soundRef.current.playAsync();
    }
  };

  const seekToTime = async (time: number) => {
    if (!soundRef.current) return;
    await soundRef.current.setPositionAsync(time);
    setCurrentTime(time);
  };

  const jumpToSegment = (segment: TranscriptSegment) => {
    seekToTime(segment.start * 1000);
    scrollToSegment(segment.id);
  };

  const scrollToSegment = (segmentId: string) => {
    // Implementation for scrolling to specific segment
    // This would require measuring segment positions
  };

  const handleSegmentEdit = (segmentId: string, newText: string) => {
    setSegments(prev =>
      prev.map(seg =>
        seg.id === segmentId ? { ...seg, text: newText } : seg
      )
    );
    setEditingSegment(null);
  };

  const toggleEntitySelection = (entityText: string) => {
    setSelectedEntities(prev => {
      const newSet = new Set(prev);
      if (newSet.has(entityText)) {
        newSet.delete(entityText);
      } else {
        newSet.add(entityText);
      }
      return newSet;
    });
  };

  const formatTime = (milliseconds: number) => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const handleExport = async (format: string) => {
    setShowExportModal(false);
    
    if (onExport) {
      onExport(format);
    } else {
      // Default export handling
      const content = segments.map(seg => seg.text).join('\n\n');
      
      try {
        await Share.share({
          message: content,
          title: `Transcript - ${transcriptId}`,
        });
      } catch (error) {
        Alert.alert('Error', 'Failed to share transcript');
      }
    }
  };

  const handleSave = () => {
    if (onSave) {
      onSave(segments);
      Alert.alert('Success', 'Transcript saved successfully');
    }
  };

  const filteredSegments = segments.filter(segment =>
    segment.text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const renderSegment = (segment: TranscriptSegment) => {
    const isEditing = editingSegment === segment.id;
    const speaker = speakers.find(s => s.id === segment.speaker);
    const isCurrentSegment = currentTime >= segment.start * 1000 && 
                            currentTime < segment.end * 1000;

    return (
      <TouchableOpacity
        key={segment.id}
        style={[
          styles.segment,
          isCurrentSegment && styles.currentSegment,
        ]}
        onPress={() => jumpToSegment(segment)}
        onLongPress={() => setEditingSegment(segment.id)}
      >
        <View style={styles.segmentHeader}>
          {speaker && (
            <View style={[styles.speakerBadge, { backgroundColor: speaker.color }]}>
              <Text style={styles.speakerName}>{speaker.name}</Text>
            </View>
          )}
          <Text style={styles.timestamp}>
            {formatTime(segment.start * 1000)}
          </Text>
        </View>
        
        {isEditing ? (
          <TextInput
            style={styles.editInput}
            value={segment.text}
            onChangeText={(text) => handleSegmentEdit(segment.id, text)}
            onBlur={() => setEditingSegment(null)}
            multiline
            autoFocus
          />
        ) : (
          <Text style={styles.segmentText}>
            {segment.entities && segment.entities.length > 0 ? (
              renderTextWithEntities(segment.text, segment.entities)
            ) : (
              segment.text
            )}
          </Text>
        )}
      </TouchableOpacity>
    );
  };

  const renderTextWithEntities = (text: string, entities: Entity[]) => {
    const elements: React.ReactNode[] = [];
    let lastEnd = 0;

    entities.forEach((entity, index) => {
      if (entity.start > lastEnd) {
        elements.push(
          <Text key={`text-${index}`}>{text.slice(lastEnd, entity.start)}</Text>
        );
      }
      
      elements.push(
        <TouchableOpacity
          key={`entity-${index}`}
          onPress={() => toggleEntitySelection(entity.text)}
          style={[
            styles.entity,
            styles[`entity${entity.label}`] || styles.entityDefault,
            selectedEntities.has(entity.text) && styles.entitySelected,
          ]}
        >
          <Text style={styles.entityText}>{entity.text}</Text>
        </TouchableOpacity>
      );
      
      lastEnd = entity.end;
    });

    if (lastEnd < text.length) {
      elements.push(
        <Text key="text-final">{text.slice(lastEnd)}</Text>
      );
    }

    return <Text>{elements}</Text>;
  };

  return (
    <View style={styles.container}>
      {/* Audio Player */}
      {audioUrl && (
        <View style={styles.audioPlayer}>
          <TouchableOpacity
            style={styles.playButton}
            onPress={togglePlayPause}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#007AFF" />
            ) : (
              <Icon
                name={isPlaying ? 'pause' : 'play-arrow'}
                size={32}
                color="#007AFF"
              />
            )}
          </TouchableOpacity>
          
          <View style={styles.sliderContainer}>
            <Text style={styles.timeText}>{formatTime(currentTime)}</Text>
            <Slider
              style={styles.slider}
              value={currentTime}
              minimumValue={0}
              maximumValue={duration}
              onSlidingComplete={seekToTime}
              minimumTrackTintColor="#007AFF"
              maximumTrackTintColor="#E0E0E0"
              thumbTintColor="#007AFF"
            />
            <Text style={styles.timeText}>{formatTime(duration)}</Text>
          </View>
        </View>
      )}

      {/* Search Bar */}
      <View style={styles.searchBar}>
        <Icon name="search" size={20} color="#666" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search transcript..."
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery !== '' && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Icon name="close" size={20} color="#666" />
          </TouchableOpacity>
        )}
      </View>

      {/* Action Buttons */}
      <View style={styles.actionBar}>
        <TouchableOpacity style={styles.actionButton} onPress={handleSave}>
          <Icon name="save" size={20} color="#007AFF" />
          <Text style={styles.actionButtonText}>Save</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => setShowExportModal(true)}
        >
          <Icon name="file-download" size={20} color="#007AFF" />
          <Text style={styles.actionButtonText}>Export</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionButton}>
          <Icon name="analytics" size={20} color="#007AFF" />
          <Text style={styles.actionButtonText}>Insights</Text>
        </TouchableOpacity>
      </View>

      {/* Transcript */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.transcriptContainer}
        showsVerticalScrollIndicator={true}
      >
        {filteredSegments.map(renderSegment)}
      </ScrollView>

      {/* Export Modal */}
      <Modal
        visible={showExportModal}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowExportModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Export Transcript</Text>
            
            <TouchableOpacity
              style={styles.exportOption}
              onPress={() => handleExport('txt')}
            >
              <Icon name="description" size={24} color="#007AFF" />
              <Text style={styles.exportOptionText}>Plain Text (.txt)</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.exportOption}
              onPress={() => handleExport('pdf')}
            >
              <Icon name="picture-as-pdf" size={24} color="#007AFF" />
              <Text style={styles.exportOptionText}>PDF Document</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.exportOption}
              onPress={() => handleExport('docx')}
            >
              <Icon name="article" size={24} color="#007AFF" />
              <Text style={styles.exportOptionText}>Word Document (.docx)</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.exportOption}
              onPress={() => handleExport('srt')}
            >
              <Icon name="subtitles" size={24} color="#007AFF" />
              <Text style={styles.exportOptionText}>Subtitles (.srt)</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.exportOption, styles.cancelButton]}
              onPress={() => setShowExportModal(false)}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

export default TranscriptionResults;