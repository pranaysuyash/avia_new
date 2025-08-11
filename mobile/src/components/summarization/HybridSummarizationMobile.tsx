import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Share,
  Dimensions,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { Switch } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { styles } from './styles';

interface SummaryResult {
  summary: string;
  summary_type: string;
  length: string;
  style: string;
  word_count: number;
  sentence_count: number;
  compression_ratio: number;
  quality_score: number;
  key_points: string[];
  extracted_sentences: string[];
  confidence_score: number;
  processing_time: number;
  metadata: Record<string, any>;
  created_at: string;
}

interface SummaryOptions {
  summary_types: Array<{value: string, label: string, description: string}>;
  lengths: Array<{value: string, label: string, description: string}>;
  styles: Array<{value: string, label: string, description: string}>;
}

const { width } = Dimensions.get('window');

const HybridSummarizationMobile: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [summaryType, setSummaryType] = useState('hybrid');
  const [length, setLength] = useState('medium');
  const [style, setStyle] = useState('formal');
  const [query, setQuery] = useState('');
  const [maxSentences, setMaxSentences] = useState<string>('');
  const [maxWords, setMaxWords] = useState<string>('');
  const [focusKeywords, setFocusKeywords] = useState<string[]>([]);
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  const [preserveStructure, setPreserveStructure] = useState(false);
  const [includeQuotes, setIncludeQuotes] = useState(true);
  
  const [result, setResult] = useState<SummaryResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [options, setOptions] = useState<SummaryOptions | null>(null);
  
  const [keywordInput, setKeywordInput] = useState('');
  const [excludeInput, setExcludeInput] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    loadSummaryOptions();
  }, []);

  const loadSummaryOptions = async () => {
    try {
      const response = await fetch('/api/v1/hybrid-summarization/types');
      if (response.ok) {
        const data = await response.json();
        setOptions(data.data);
      }
    } catch (error) {
      console.error('Failed to load summary options:', error);
    }
  };

  const handleSummarize = async () => {
    if (!inputText.trim()) {
      Alert.alert('Error', 'Please enter text to summarize');
      return;
    }

    setIsLoading(true);

    try {
      const requestBody = {
        text: inputText,
        summary_type: summaryType,
        length,
        style,
        query: query || undefined,
        max_sentences: maxSentences ? parseInt(maxSentences) : undefined,
        max_words: maxWords ? parseInt(maxWords) : undefined,
        focus_keywords: focusKeywords.length > 0 ? focusKeywords : undefined,
        exclude_keywords: excludeKeywords.length > 0 ? excludeKeywords : undefined,
        preserve_structure: preserveStructure,
        include_quotes: includeQuotes,
        language: 'en'
      };

      const response = await fetch('/api/v1/hybrid-summarization/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create summary');
      }

      const data = await response.json();
      setResult(data.data);
    } catch (error) {
      Alert.alert('Error', error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const addKeyword = (keyword: string, type: 'focus' | 'exclude') => {
    if (!keyword.trim()) return;
    
    if (type === 'focus') {
      setFocusKeywords(prev => [...prev, keyword.trim()]);
      setKeywordInput('');
    } else {
      setExcludeKeywords(prev => [...prev, keyword.trim()]);
      setExcludeInput('');
    }
  };

  const removeKeyword = (keyword: string, type: 'focus' | 'exclude') => {
    if (type === 'focus') {
      setFocusKeywords(prev => prev.filter(k => k !== keyword));
    } else {
      setExcludeKeywords(prev => prev.filter(k => k !== keyword));
    }
  };

  const shareSummary = async () => {
    if (!result) return;
    
    try {
      await Share.share({
        message: `Summary:\n\n${result.summary}\n\nGenerated with Hybrid Summarization`,
        title: 'Summary'
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const renderKeywordTags = (keywords: string[], type: 'focus' | 'exclude') => {
    return (
      <View style={styles.keywordContainer}>
        {keywords.map((keyword, index) => (
          <TouchableOpacity
            key={index}
            style={[
              styles.keywordTag,
              type === 'focus' ? styles.focusTag : styles.excludeTag
            ]}
            onPress={() => removeKeyword(keyword, type)}
          >
            <Text style={styles.keywordText}>{keyword}</Text>
            <Icon name="close" size={16} color="#fff" />
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const renderProgressBar = (value: number, color: string) => {
    return (
      <View style={styles.progressContainer}>
        <View style={[styles.progressBar, { width: `${value * 100}%`, backgroundColor: color }]} />
      </View>
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Icon name="auto-awesome" size={24} color="#3B82F6" />
        <Text style={styles.title}>Hybrid Summarization</Text>
      </View>

      {/* Input Section */}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Input Text</Text>
        <TextInput
          style={styles.textArea}
          placeholder="Enter the text you want to summarize..."
          value={inputText}
          onChangeText={setInputText}
          multiline
          numberOfLines={6}
          textAlignVertical="top"
        />
        
        <View style={styles.textStats}>
          <Text style={styles.statText}>{inputText.length} characters</Text>
          <Text style={styles.statText}>
            {inputText.split(/\s+/).filter(w => w.length > 0).length} words
          </Text>
        </View>

        {/* Basic Options */}
        <View style={styles.optionsContainer}>
          <View style={styles.pickerContainer}>
            <Text style={styles.label}>Summary Type</Text>
            <Picker
              selectedValue={summaryType}
              onValueChange={setSummaryType}
              style={styles.picker}
            >
              {options?.summary_types.map(type => (
                <Picker.Item key={type.value} label={type.label} value={type.value} />
              ))}
            </Picker>
          </View>

          <View style={styles.row}>
            <View style={styles.halfWidth}>
              <Text style={styles.label}>Length</Text>
              <Picker
                selectedValue={length}
                onValueChange={setLength}
                style={styles.picker}
              >
                {options?.lengths.map(len => (
                  <Picker.Item key={len.value} label={len.label} value={len.value} />
                ))}
              </Picker>
            </View>

            <View style={styles.halfWidth}>
              <Text style={styles.label}>Style</Text>
              <Picker
                selectedValue={style}
                onValueChange={setStyle}
                style={styles.picker}
              >
                {options?.styles.map(st => (
                  <Picker.Item key={st.value} label={st.label} value={st.value} />
                ))}
              </Picker>
            </View>
          </View>

          {summaryType === 'query_focused' && (
            <View style={styles.inputContainer}>
              <Text style={styles.label}>Focus Query</Text>
              <TextInput
                style={styles.input}
                placeholder="What should the summary focus on?"
                value={query}
                onChangeText={setQuery}
              />
            </View>
          )}
        </View>

        {/* Advanced Options Toggle */}
        <TouchableOpacity
          style={styles.advancedToggle}
          onPress={() => setShowAdvanced(!showAdvanced)}
        >
          <Text style={styles.advancedToggleText}>Advanced Options</Text>
          <Icon 
            name={showAdvanced ? "expand-less" : "expand-more"} 
            size={24} 
            color="#3B82F6" 
          />
        </TouchableOpacity>

        {showAdvanced && (
          <View style={styles.advancedContainer}>
            <View style={styles.row}>
              <View style={styles.halfWidth}>
                <Text style={styles.label}>Max Sentences</Text>
                <TextInput
                  style={styles.input}
                  placeholder="1-50"
                  value={maxSentences}
                  onChangeText={setMaxSentences}
                  keyboardType="numeric"
                />
              </View>

              <View style={styles.halfWidth}>
                <Text style={styles.label}>Max Words</Text>
                <TextInput
                  style={styles.input}
                  placeholder="10-1000"
                  value={maxWords}
                  onChangeText={setMaxWords}
                  keyboardType="numeric"
                />
              </View>
            </View>

            {/* Focus Keywords */}
            <View style={styles.keywordSection}>
              <Text style={styles.label}>Focus Keywords</Text>
              <View style={styles.keywordInputRow}>
                <TextInput
                  style={[styles.input, styles.keywordInput]}
                  placeholder="Add keyword..."
                  value={keywordInput}
                  onChangeText={setKeywordInput}
                />
                <TouchableOpacity
                  style={styles.addButton}
                  onPress={() => addKeyword(keywordInput, 'focus')}
                >
                  <Icon name="add" size={20} color="#fff" />
                </TouchableOpacity>
              </View>
              {renderKeywordTags(focusKeywords, 'focus')}
            </View>

            {/* Exclude Keywords */}
            <View style={styles.keywordSection}>
              <Text style={styles.label}>Exclude Keywords</Text>
              <View style={styles.keywordInputRow}>
                <TextInput
                  style={[styles.input, styles.keywordInput]}
                  placeholder="Add keyword to exclude..."
                  value={excludeInput}
                  onChangeText={setExcludeInput}
                />
                <TouchableOpacity
                  style={[styles.addButton, styles.excludeButton]}
                  onPress={() => addKeyword(excludeInput, 'exclude')}
                >
                  <Icon name="add" size={20} color="#fff" />
                </TouchableOpacity>
              </View>
              {renderKeywordTags(excludeKeywords, 'exclude')}
            </View>

            {/* Switches */}
            <View style={styles.switchContainer}>
              <View style={styles.switchRow}>
                <Text style={styles.switchLabel}>Preserve Structure</Text>
                <Switch
                  value={preserveStructure}
                  onValueChange={setPreserveStructure}
                  trackColor={{ false: '#767577', true: '#3B82F6' }}
                  thumbColor={preserveStructure ? '#fff' : '#f4f3f4'}
                />
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.switchLabel}>Include Quotes</Text>
                <Switch
                  value={includeQuotes}
                  onValueChange={setIncludeQuotes}
                  trackColor={{ false: '#767577', true: '#3B82F6' }}
                  thumbColor={includeQuotes ? '#fff' : '#f4f3f4'}
                />
              </View>
            </View>
          </View>
        )}

        {/* Generate Button */}
        <TouchableOpacity
          style={[styles.generateButton, (!inputText.trim() || isLoading) && styles.disabledButton]}
          onPress={handleSummarize}
          disabled={!inputText.trim() || isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Icon name="bolt" size={20} color="#fff" />
          )}
          <Text style={styles.generateButtonText}>
            {isLoading ? 'Generating...' : 'Generate Summary'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Results Section */}
      {result && (
        <View style={styles.card}>
          <View style={styles.resultHeader}>
            <Text style={styles.sectionTitle}>Summary Result</Text>
            <TouchableOpacity onPress={shareSummary} style={styles.shareButton}>
              <Icon name="share" size={20} color="#3B82F6" />
            </TouchableOpacity>
          </View>

          {/* Summary Text */}
          <View style={styles.summaryContainer}>
            <Text style={styles.summaryText}>{result.summary}</Text>
          </View>

          {/* Metrics */}
          <View style={styles.metricsContainer}>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Quality Score</Text>
              <Text style={styles.metricValue}>{(result.quality_score * 100).toFixed(1)}%</Text>
            </View>
            {renderProgressBar(result.quality_score, '#10B981')}

            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Confidence</Text>
              <Text style={styles.metricValue}>{(result.confidence_score * 100).toFixed(1)}%</Text>
            </View>
            {renderProgressBar(result.confidence_score, '#3B82F6')}
          </View>

          {/* Stats Grid */}
          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{result.word_count}</Text>
              <Text style={styles.statLabel}>Words</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{result.sentence_count}</Text>
              <Text style={styles.statLabel}>Sentences</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{result.compression_ratio.toFixed(1)}x</Text>
              <Text style={styles.statLabel}>Compression</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{result.processing_time.toFixed(1)}s</Text>
              <Text style={styles.statLabel}>Time</Text>
            </View>
          </View>

          {/* Key Points */}
          {result.key_points.length > 0 && (
            <View style={styles.keyPointsContainer}>
              <Text style={styles.keyPointsTitle}>Key Points</Text>
              {result.key_points.map((point, index) => (
                <View key={index} style={styles.keyPointItem}>
                  <Text style={styles.bullet}>•</Text>
                  <Text style={styles.keyPointText}>{point}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Metadata */}
          <View style={styles.metadata}>
            <Text style={styles.metadataText}>
              Type: {result.summary_type} | Style: {result.style} | Length: {result.length}
            </Text>
            <Text style={styles.metadataText}>
              Created: {new Date(result.created_at).toLocaleString()}
            </Text>
          </View>
        </View>
      )}
    </ScrollView>
  );
};

export default HybridSummarizationMobile;