import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  ScrollView,
  Text,
  StyleSheet,
  Alert,
  Modal,
  TouchableOpacity,
  Dimensions,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
  FlatList,
  Platform,
  PermissionsAndroid,
  Image,
  PanResponder,
  Animated,
} from 'react-native';
import {
  Card,
  Button,
  IconButton,
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
  Switch,
  Slider,
  Provider as PaperProvider,
  DefaultTheme,
  DarkTheme,
  useTheme,
  Snackbar,
  Menu,
  Badge,
  SegmentedButtons,
} from 'react-native-paper';
import MaterialIcons from 'react-native-vector-icons/MaterialIcons';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import DocumentPicker from 'react-native-document-picker';
import ImagePicker from 'react-native-image-crop-picker';
import RNFS from 'react-native-fs';
import { GestureHandlerRootView, PinchGestureHandler, State } from 'react-native-gesture-handler';
import ViewShot from 'react-native-view-shot';
import ImageEditor from '@react-native-community/image-editor';
import { manipulateAsync, FlipType, SaveFormat } from 'expo-image-manipulator';
import { Share } from 'react-native';
import { buildLink } from '../../utils/deeplink';
import { logUxEvent } from '../../utils/uxTelemetry';
import { SkeletonList } from '../shared/Skeleton';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface ImageFile {
  id: string;
  name: string;
  path: string;
  size: number;
  width: number;
  height: number;
  format: string;
  processed: boolean;
  processing: boolean;
  thumbnailPath?: string;
  metadata?: ImageMetadata;
  adjustments?: ImageAdjustments;
}

interface ImageMetadata {
  colorSpace: string;
  bitDepth: number;
  dpi: number;
  hasAlpha: boolean;
  orientation: number;
}

interface ImageAdjustments {
  brightness: number;
  contrast: number;
  saturation: number;
  sharpness: number;
  rotation: number;
  flipHorizontal: boolean;
  flipVertical: boolean;
  cropArea?: CropArea;
}

interface CropArea {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface ProcessingSettings {
  autoEnhance: boolean;
  resize: boolean;
  resizeWidth: number;
  resizeHeight: number;
  maintainAspectRatio: boolean;
  compress: boolean;
  compressionQuality: number;
  removeBackground: boolean;
  denoise: boolean;
  outputFormat: string;
  batchMode: boolean;
}

const ImagePreprocessingMobile: React.FC = () => {
  const theme = useTheme();
  const [imageFiles, setImageFiles] = useState<ImageFile[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [currentImage, setCurrentImage] = useState<ImageFile | null>(null);
  const [loading, setLoading] = useState(true);
  const [processingQueue, setProcessingQueue] = useState<string[]>([]);
  
  const [settings, setSettings] = useState<ProcessingSettings>({
    autoEnhance: true,
    resize: false,
    resizeWidth: 1920,
    resizeHeight: 1080,
    maintainAspectRatio: true,
    compress: true,
    compressionQuality: 85,
    removeBackground: false,
    denoise: false,
    outputFormat: 'jpeg',
    batchMode: false,
  });

  const [adjustments, setAdjustments] = useState<ImageAdjustments>({
    brightness: 0,
    contrast: 0,
    saturation: 0,
    sharpness: 0,
    rotation: 0,
    flipHorizontal: false,
    flipVertical: false,
  });

  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'single'>('grid');
  const [editMode, setEditMode] = useState<'adjust' | 'crop' | 'filter'>('adjust');
  const [settingsModalVisible, setSettingsModalVisible] = useState(false);
  const [imageViewerVisible, setImageViewerVisible] = useState(false);
  const [snackbarVisible, setSnackbarVisible] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [menuVisible, setMenuVisible] = useState(false);
  const [filterMenuVisible, setFilterMenuVisible] = useState(false);
  const [filter, setFilter] = useState<'all' | 'processed' | 'unprocessed'>('all');
  const [cropMode, setCropMode] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        await new Promise(res => setTimeout(res, 500));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const sharePreprocessingLink = async () => {
    const url = buildLink('preprocessing');
    try {
      await Share.share({ message: url });
      await logUxEvent('share_preprocessing_view', { url });
    } catch (_) {}
  };

  // Animation values
  const imageScale = useRef(new Animated.Value(1)).current;
  const imageRotation = useRef(new Animated.Value(0)).current;
  const cropOverlayOpacity = useRef(new Animated.Value(0)).current;
  
  // Refs
  const viewShotRef = useRef<ViewShot>(null);
  const lastScale = useRef(1);
  const lastRotation = useRef(0);

  useEffect(() => {
    requestPermissions();
  }, []);

  const requestPermissions = async () => {
    if (Platform.OS === 'android') {
      try {
        const grants = await PermissionsAndroid.requestMultiple([
          PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.CAMERA,
        ]);
        
        const allGranted = Object.values(grants).every(
          result => result === PermissionsAndroid.RESULTS.GRANTED
        );
        
        if (!allGranted) {
          Alert.alert('Permissions required', 'Please grant all permissions to use image features');
        }
      } catch (err) {
        console.warn(err);
      }
    }
  };

  const pickImages = async () => {
    try {
      const results = await DocumentPicker.pick({
        type: [DocumentPicker.types.images],
        allowMultiSelection: true,
      });
      
      const newFiles: ImageFile[] = await Promise.all(
        results.map(async (file) => {
          const imageInfo = await getImageInfo(file.uri);
          return {
            id: `image_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            name: file.name || 'Unknown',
            path: file.uri,
            size: file.size || 0,
            width: imageInfo.width,
            height: imageInfo.height,
            format: file.name?.split('.').pop() || 'unknown',
            processed: false,
            processing: false,
          };
        })
      );
      
      setImageFiles([...imageFiles, ...newFiles]);
      showSnackbar(`Added ${results.length} image(s)`);
      
      // Generate thumbnails in background
      newFiles.forEach(file => generateThumbnail(file));
    } catch (error) {
      if (!DocumentPicker.isCancel(error)) {
        Alert.alert('Error', 'Failed to pick images');
      }
    }
  };

  const takePhoto = async () => {
    try {
      const image = await ImagePicker.openCamera({
        width: 1920,
        height: 1080,
        cropping: false,
        includeBase64: false,
      });
      
      const imageInfo = await getImageInfo(image.path);
      const newFile: ImageFile = {
        id: `photo_${Date.now()}`,
        name: `Photo_${new Date().toLocaleTimeString()}`,
        path: image.path,
        size: image.size || 0,
        width: imageInfo.width,
        height: imageInfo.height,
        format: 'jpeg',
        processed: false,
        processing: false,
      };
      
      setImageFiles([...imageFiles, newFile]);
      showSnackbar('Photo captured successfully');
      generateThumbnail(newFile);
    } catch (error) {
      console.error('Failed to take photo:', error);
    }
  };

  const getImageInfo = async (uri: string): Promise<{ width: number; height: number }> => {
    return new Promise((resolve, reject) => {
      Image.getSize(
        uri,
        (width, height) => resolve({ width, height }),
        reject
      );
    });
  };

  const generateThumbnail = async (file: ImageFile) => {
    try {
      // Mock thumbnail generation - in real app, use image manipulation library
      const thumbnailPath = `${RNFS.CachesDirectoryPath}/thumb_${file.id}.jpg`;
      
      // Update file with thumbnail
      setImageFiles(prev => prev.map(f => 
        f.id === file.id ? { ...f, thumbnailPath } : f
      ));
    } catch (error) {
      console.error('Failed to generate thumbnail:', error);
    }
  };

  const processSelectedImages = async () => {
    const filesToProcess = selectedFiles.length > 0 ? selectedFiles : imageFiles.map(f => f.id);
    
    if (filesToProcess.length === 0) {
      Alert.alert('No images', 'Please select images to process');
      return;
    }
    
    setProcessingQueue(filesToProcess);
    
    for (const fileId of filesToProcess) {
      await processImage(fileId);
    }
    
    setProcessingQueue([]);
    setSelectedFiles([]);
    showSnackbar('Image processing completed');
  };

  const processImage = async (fileId: string) => {
    try {
      setImageFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, processing: true } : f
      ));
      
      const file = imageFiles.find(f => f.id === fileId);
      if (!file) return;
      
      // Simulate processing stages
      const stages = [
        'Loading image...',
        'Analyzing content...',
        'Applying enhancements...',
        'Optimizing quality...',
        'Saving result...',
      ];
      
      for (const stage of stages) {
        await new Promise(resolve => setTimeout(resolve, 800));
      }
      
      // Update file as processed
      setImageFiles(prev => prev.map(f => 
        f.id === fileId ? { 
          ...f, 
          processing: false, 
          processed: true,
          metadata: {
            colorSpace: 'sRGB',
            bitDepth: 8,
            dpi: 72,
            hasAlpha: false,
            orientation: 1,
          }
        } : f
      ));
    } catch (error) {
      setImageFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, processing: false } : f
      ));
      Alert.alert('Error', 'Failed to process image');
    }
  };

  const applyAdjustments = async () => {
    if (!currentImage) return;
    
    try {
      setLoading(true);
      
      // Apply image adjustments using image manipulation library
      const manipulateOptions = [];
      
      if (adjustments.rotation !== 0) {
        manipulateOptions.push({ rotate: adjustments.rotation });
      }
      
      if (adjustments.flipHorizontal) {
        manipulateOptions.push({ flip: FlipType.Horizontal });
      }
      
      if (adjustments.flipVertical) {
        manipulateOptions.push({ flip: FlipType.Vertical });
      }
      
      if (adjustments.cropArea) {
        manipulateOptions.push({
          crop: {
            originX: adjustments.cropArea.x,
            originY: adjustments.cropArea.y,
            width: adjustments.cropArea.width,
            height: adjustments.cropArea.height,
          }
        });
      }
      
      // In real app, apply these adjustments to the image
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Update image with adjustments
      setImageFiles(prev => prev.map(f => 
        f.id === currentImage.id ? { ...f, adjustments, processed: true } : f
      ));
      
      showSnackbar('Adjustments applied successfully');
      setImageViewerVisible(false);
    } catch (error) {
      Alert.alert('Error', 'Failed to apply adjustments');
    } finally {
      setLoading(false);
    }
  };

  const deleteImage = (fileId: string) => {
    Alert.alert(
      'Delete Image',
      'Are you sure you want to delete this image?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            setImageFiles(prev => prev.filter(f => f.id !== fileId));
            setSelectedFiles(prev => prev.filter(id => id !== fileId));
            showSnackbar('Image deleted');
          },
        },
      ]
    );
  };

  const toggleFileSelection = (fileId: string) => {
    setSelectedFiles(prev => 
      prev.includes(fileId)
        ? prev.filter(id => id !== fileId)
        : [...prev, fileId]
    );
  };

  const showSnackbar = (message: string) => {
    setSnackbarMessage(message);
    setSnackbarVisible(true);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFilteredFiles = () => {
    switch (filter) {
      case 'processed':
        return imageFiles.filter(f => f.processed);
      case 'unprocessed':
        return imageFiles.filter(f => !f.processed);
      default:
        return imageFiles;
    }
  };

  const applyFilter = (filterName: string) => {
    setSelectedFilter(filterName);
    // In real app, apply the filter to the current image
  };

  const renderImageGrid = ({ item }: { item: ImageFile }) => {
    const isSelected = selectedFiles.includes(item.id);
    const isProcessing = item.processing || processingQueue.includes(item.id);
    
    return (
      <TouchableOpacity
        style={[styles.gridItem, isSelected && styles.selectedGridItem]}
        onPress={() => toggleFileSelection(item.id)}
        onLongPress={() => {
          setCurrentImage(item);
          setImageViewerVisible(true);
        }}
      >
        <Image
          source={{ uri: item.thumbnailPath || item.path }}
          style={styles.gridImage}
          resizeMode="cover"
        />
        
        {isProcessing && (
          <View style={styles.processingOverlay}>
            <ActivityIndicator color="#fff" size="large" />
          </View>
        )}
        
        {item.processed && (
          <View style={styles.processedIndicator}>
            <MaterialIcons name="check-circle" size={24} color="#4CAF50" />
          </View>
        )}
        
        <View style={styles.gridItemInfo}>
          <Text style={styles.gridItemName} numberOfLines={1}>
            {item.name}
          </Text>
          <Caption style={{ color: '#fff' }}>
            {item.width}x{item.height}
          </Caption>
        </View>
      </TouchableOpacity>
    );
  };

  const renderImageList = ({ item }: { item: ImageFile }) => {
    const isSelected = selectedFiles.includes(item.id);
    const isProcessing = item.processing || processingQueue.includes(item.id);
    
    return (
      <TouchableOpacity
        onPress={() => toggleFileSelection(item.id)}
        onLongPress={() => {
          setCurrentImage(item);
          setImageViewerVisible(true);
        }}
      >
        <Surface style={[styles.listItem, isSelected && styles.selectedListItem]} elevation={1}>
          <Image
            source={{ uri: item.thumbnailPath || item.path }}
            style={styles.listItemImage}
            resizeMode="cover"
          />
          
          <View style={styles.listItemInfo}>
            <Text style={[styles.listItemName, { color: theme.colors.onSurface }]} numberOfLines={1}>
              {item.name}
            </Text>
            <View style={styles.listItemMeta}>
              <Caption>{formatFileSize(item.size)}</Caption>
              <Caption> • </Caption>
              <Caption>{item.width}x{item.height}</Caption>
              <Caption> • </Caption>
              <Caption>{item.format.toUpperCase()}</Caption>
            </View>
            
            {isProcessing && (
              <ProgressBar 
                indeterminate 
                style={styles.processingProgress}
                color={theme.colors.primary}
              />
            )}
          </View>
          
          <View style={styles.listItemActions}>
            {item.processed && (
              <MaterialIcons name="check-circle" size={24} color="#4CAF50" />
            )}
            <IconButton
              icon="delete"
              onPress={() => deleteImage(item.id)}
            />
          </View>
        </Surface>
      </TouchableOpacity>
    );
  };

  const renderImageViewer = () => (
    <Modal
      visible={imageViewerVisible}
      onRequestClose={() => setImageViewerVisible(false)}
      animationType="slide"
      presentationStyle="fullScreen"
    >
      <SafeAreaView style={[styles.imageViewerContainer, { backgroundColor: '#000' }]}>
        {/* Header */}
        <Surface style={styles.imageViewerHeader} elevation={2}>
          <IconButton
            icon="arrow-back"
            onPress={() => setImageViewerVisible(false)}
            iconColor="#fff"
          />
          <Title style={{ color: '#fff', flex: 1 }}>{currentImage?.name}</Title>
          <IconButton
            icon="check"
            onPress={applyAdjustments}
            iconColor="#fff"
            disabled={loading}
          />
        </Surface>
        
        {/* Image Display */}
        <View style={styles.imageDisplay}>
          {currentImage && (
            <ViewShot ref={viewShotRef} style={styles.imageContainer}>
              <Animated.Image
                source={{ uri: currentImage.path }}
                style={[
                  styles.fullImage,
                  {
                    transform: [
                      { scale: imageScale },
                      { rotate: `${adjustments.rotation}deg` }
                    ],
                  }
                ]}
                resizeMode="contain"
              />
              
              {cropMode && (
                <Animated.View 
                  style={[
                    styles.cropOverlay,
                    { opacity: cropOverlayOpacity }
                  ]}
                >
                  <View style={styles.cropFrame} />
                </Animated.View>
              )}
            </ViewShot>
          )}
        </View>
        
        {/* Edit Mode Tabs */}
        <View style={styles.editModeTabs}>
          <SegmentedButtons
            value={editMode}
            onValueChange={setEditMode}
            buttons={[
              { value: 'adjust', label: 'Adjust', icon: 'tune' },
              { value: 'crop', label: 'Crop', icon: 'crop' },
              { value: 'filter', label: 'Filter', icon: 'filter' },
            ]}
            style={styles.segmentedButtons}
          />
        </View>
        
        {/* Edit Controls */}
        <Surface style={styles.editControls} elevation={2}>
          {editMode === 'adjust' && (
            <ScrollView style={styles.adjustmentControls}>
              <View style={styles.adjustmentRow}>
                <MaterialIcons name="brightness-6" size={24} color={theme.colors.onSurface} />
                <Slider
                  style={styles.adjustmentSlider}
                  minimumValue={-100}
                  maximumValue={100}
                  value={adjustments.brightness}
                  onValueChange={(value) => setAdjustments({ ...adjustments, brightness: value })}
                  thumbStyle={{ backgroundColor: theme.colors.primary }}
                  trackStyle={{ backgroundColor: theme.colors.outline }}
                  minimumTrackTintColor={theme.colors.primary}
                />
                <Text style={[styles.adjustmentValue, { color: theme.colors.onSurface }]}>
                  {Math.round(adjustments.brightness)}
                </Text>
              </View>
              
              <View style={styles.adjustmentRow}>
                <MaterialIcons name="contrast" size={24} color={theme.colors.onSurface} />
                <Slider
                  style={styles.adjustmentSlider}
                  minimumValue={-100}
                  maximumValue={100}
                  value={adjustments.contrast}
                  onValueChange={(value) => setAdjustments({ ...adjustments, contrast: value })}
                  thumbStyle={{ backgroundColor: theme.colors.primary }}
                  trackStyle={{ backgroundColor: theme.colors.outline }}
                  minimumTrackTintColor={theme.colors.primary}
                />
                <Text style={[styles.adjustmentValue, { color: theme.colors.onSurface }]}>
                  {Math.round(adjustments.contrast)}
                </Text>
              </View>
              
              <View style={styles.adjustmentRow}>
                <MaterialIcons name="invert-colors" size={24} color={theme.colors.onSurface} />
                <Slider
                  style={styles.adjustmentSlider}
                  minimumValue={-100}
                  maximumValue={100}
                  value={adjustments.saturation}
                  onValueChange={(value) => setAdjustments({ ...adjustments, saturation: value })}
                  thumbStyle={{ backgroundColor: theme.colors.primary }}
                  trackStyle={{ backgroundColor: theme.colors.outline }}
                  minimumTrackTintColor={theme.colors.primary}
                />
                <Text style={[styles.adjustmentValue, { color: theme.colors.onSurface }]}>
                  {Math.round(adjustments.saturation)}
                </Text>
              </View>
              
              <View style={styles.adjustmentActions}>
                <IconButton
                  icon="rotate-left"
                  onPress={() => setAdjustments({ ...adjustments, rotation: adjustments.rotation - 90 })}
                />
                <IconButton
                  icon="rotate-right"
                  onPress={() => setAdjustments({ ...adjustments, rotation: adjustments.rotation + 90 })}
                />
                <IconButton
                  icon="flip"
                  onPress={() => setAdjustments({ ...adjustments, flipHorizontal: !adjustments.flipHorizontal })}
                />
                <IconButton
                  icon="flip"
                  style={{ transform: [{ rotate: '90deg' }] }}
                  onPress={() => setAdjustments({ ...adjustments, flipVertical: !adjustments.flipVertical })}
                />
              </View>
            </ScrollView>
          )}
          
          {editMode === 'crop' && (
            <View style={styles.cropControls}>
              <View style={styles.cropPresets}>
                <Chip 
                  mode="outlined" 
                  onPress={() => setCropMode(true)}
                  selected={cropMode}
                >
                  Free
                </Chip>
                <Chip mode="outlined" onPress={() => {}}>1:1</Chip>
                <Chip mode="outlined" onPress={() => {}}>4:3</Chip>
                <Chip mode="outlined" onPress={() => {}}>16:9</Chip>
                <Chip mode="outlined" onPress={() => {}}>3:2</Chip>
              </View>
              
              {cropMode && (
                <Button
                  mode="contained"
                  onPress={() => {
                    setCropMode(false);
                    // Apply crop
                  }}
                  style={{ marginTop: 16 }}
                >
                  Apply Crop
                </Button>
              )}
            </View>
          )}
          
          {editMode === 'filter' && (
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.filterList}>
                {['Original', 'Vintage', 'Black & White', 'Sepia', 'Cool', 'Warm', 'Dramatic'].map((filter) => (
                  <TouchableOpacity
                    key={filter}
                    style={[
                      styles.filterItem,
                      selectedFilter === filter && styles.selectedFilterItem
                    ]}
                    onPress={() => applyFilter(filter)}
                  >
                    <View style={styles.filterPreview} />
                    <Text style={styles.filterName}>{filter}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
          )}
        </Surface>
      </SafeAreaView>
    </Modal>
  );

  const renderSettingsModal = () => (
    <Modal
      visible={settingsModalVisible}
      onRequestClose={() => setSettingsModalVisible(false)}
      animationType="slide"
    >
      <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.colors.background }]}>
        <Surface style={styles.modalHeader} elevation={2}>
          <Title>Processing Settings</Title>
          <IconButton
            icon="close"
            onPress={() => setSettingsModalVisible(false)}
          />
        </Surface>
        
        <ScrollView style={styles.modalContent}>
          <List.Section>
            <List.Subheader>Enhancement</List.Subheader>
            <List.Item
              title="Auto Enhance"
              description="Automatically adjust brightness, contrast, and colors"
              right={() => (
                <Switch
                  value={settings.autoEnhance}
                  onValueChange={(value) => setSettings({ ...settings, autoEnhance: value })}
                />
              )}
            />
            <List.Item
              title="Remove Background"
              description="Use AI to remove image background"
              right={() => (
                <Switch
                  value={settings.removeBackground}
                  onValueChange={(value) => setSettings({ ...settings, removeBackground: value })}
                />
              )}
            />
            <List.Item
              title="Denoise"
              description="Reduce image noise and grain"
              right={() => (
                <Switch
                  value={settings.denoise}
                  onValueChange={(value) => setSettings({ ...settings, denoise: value })}
                />
              )}
            />
          </List.Section>

          <Divider />

          <List.Section>
            <List.Subheader>Resize & Compress</List.Subheader>
            <List.Item
              title="Resize Images"
              right={() => (
                <Switch
                  value={settings.resize}
                  onValueChange={(value) => setSettings({ ...settings, resize: value })}
                />
              )}
            />
            {settings.resize && (
              <View style={styles.resizeSettings}>
                <View style={styles.resizeRow}>
                  <Text style={{ color: theme.colors.onSurface }}>Width:</Text>
                  <Chip mode="outlined">{settings.resizeWidth}px</Chip>
                </View>
                <View style={styles.resizeRow}>
                  <Text style={{ color: theme.colors.onSurface }}>Height:</Text>
                  <Chip mode="outlined">{settings.resizeHeight}px</Chip>
                </View>
                <List.Item
                  title="Maintain Aspect Ratio"
                  right={() => (
                    <Switch
                      value={settings.maintainAspectRatio}
                      onValueChange={(value) => setSettings({ ...settings, maintainAspectRatio: value })}
                    />
                  )}
                />
              </View>
            )}
            
            <List.Item
              title="Compress Images"
              right={() => (
                <Switch
                  value={settings.compress}
                  onValueChange={(value) => setSettings({ ...settings, compress: value })}
                />
              )}
            />
            {settings.compress && (
              <View style={styles.sliderContainer}>
                <Text style={[styles.sliderLabel, { color: theme.colors.onSurface }]}>
                  Quality: {settings.compressionQuality}%
                </Text>
                <Slider
                  style={styles.slider}
                  minimumValue={10}
                  maximumValue={100}
                  step={5}
                  value={settings.compressionQuality}
                  onValueChange={(value) => setSettings({ ...settings, compressionQuality: value })}
                  thumbStyle={{ backgroundColor: theme.colors.primary }}
                  trackStyle={{ backgroundColor: theme.colors.outline }}
                  minimumTrackTintColor={theme.colors.primary}
                />
              </View>
            )}
          </List.Section>

          <Divider />

          <List.Section>
            <List.Subheader>Output</List.Subheader>
            <List.Item
              title="Output Format"
              description={settings.outputFormat.toUpperCase()}
              onPress={() => {
                // Show format selection dialog
              }}
            />
            <List.Item
              title="Batch Processing"
              description="Apply same settings to all selected images"
              right={() => (
                <Switch
                  value={settings.batchMode}
                  onValueChange={(value) => setSettings({ ...settings, batchMode: value })}
                />
              )}
            />
          </List.Section>
        </ScrollView>
        
        <Surface style={styles.modalFooter} elevation={2}>
          <Button
            mode="contained"
            onPress={() => {
              setSettingsModalVisible(false);
              showSnackbar('Settings saved');
            }}
            style={styles.modalButton}
          >
            Save Settings
          </Button>
        </Surface>
      </SafeAreaView>
    </Modal>
  );

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PaperProvider>
        <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
          {/* Header */}
          <Surface style={styles.header} elevation={2}>
            <View style={styles.headerContent}>
              <Title>Image Preprocessing</Title>
              <View style={styles.headerActions}>
                <IconButton
                  icon="share-variant"
                  onPress={async () => {
                    const url = buildLink('preprocessing');
                    try { await Share.share({ message: url }); await logUxEvent('share_preprocessing_view', { url }); } catch {}
                  }}
                  accessibilityLabel="Share preprocessing view"
                />
                <Badge visible={selectedFiles.length > 0} style={styles.selectionBadge}>
                  {selectedFiles.length}
                </Badge>
                <Menu
                  visible={filterMenuVisible}
                  onDismiss={() => setFilterMenuVisible(false)}
                  anchor={
                    <IconButton
                      icon="filter-list"
                      onPress={() => setFilterMenuVisible(true)}
                    />
                  }
                >
                  <Menu.Item
                    onPress={() => {
                      setFilter('all');
                      setFilterMenuVisible(false);
                    }}
                    title="All Images"
                    icon={filter === 'all' ? 'check' : undefined}
                  />
                  <Menu.Item
                    onPress={() => {
                      setFilter('processed');
                      setFilterMenuVisible(false);
                    }}
                    title="Processed"
                    icon={filter === 'processed' ? 'check' : undefined}
                  />
                  <Menu.Item
                    onPress={() => {
                      setFilter('unprocessed');
                      setFilterMenuVisible(false);
                    }}
                    title="Unprocessed"
                    icon={filter === 'unprocessed' ? 'check' : undefined}
                  />
                </Menu>
                <Menu
                  visible={menuVisible}
                  onDismiss={() => setMenuVisible(false)}
                  anchor={
                    <IconButton
                      icon="view-module"
                      onPress={() => setMenuVisible(true)}
                    />
                  }
                >
                  <Menu.Item
                    onPress={() => {
                      setViewMode('grid');
                      setMenuVisible(false);
                    }}
                    title="Grid View"
                    icon="view-module"
                    disabled={viewMode === 'grid'}
                  />
                  <Menu.Item
                    onPress={() => {
                      setViewMode('list');
                      setMenuVisible(false);
                    }}
                    title="List View"
                    icon="view-list"
                    disabled={viewMode === 'list'}
                  />
                </Menu>
                <IconButton
                  icon="settings"
                  onPress={() => setSettingsModalVisible(true)}
                />
              </View>
            </View>
          </Surface>

          {/* Action Buttons */}
          <View style={styles.actionButtons}>
            <Button
              mode="contained"
              icon="camera"
              onPress={takePhoto}
              style={styles.actionButton}
            >
              Take Photo
            </Button>
            <Button
              mode="outlined"
              icon="folder-open"
              onPress={pickImages}
              style={styles.actionButton}
            >
              Import Images
            </Button>
          </View>

          {/* Image Grid/List */}
          <FlatList
            data={getFilteredFiles()}
            renderItem={viewMode === 'grid' ? renderImageGrid : renderImageList}
            keyExtractor={(item) => item.id}
            numColumns={viewMode === 'grid' ? 3 : 1}
            key={viewMode} // Force re-render when view mode changes
            contentContainerStyle={styles.imageList}
            ListEmptyComponent={
              <View style={styles.emptyState}>
                <MaterialIcons name="image" size={64} color={theme.colors.onSurfaceVariant} />
                <Subheading style={{ color: theme.colors.onSurfaceVariant, marginTop: 16 }}>
                  No images yet
                </Subheading>
                <Caption>Take a photo or import images to get started</Caption>
              </View>
            }
          />

          {/* Bottom Action Bar */}
          {imageFiles.length > 0 && (
            <Surface style={styles.bottomActionBar} elevation={3}>
              <Button
                mode="outlined"
                onPress={() => {
                  if (selectedFiles.length === imageFiles.length) {
                    setSelectedFiles([]);
                  } else {
                    setSelectedFiles(imageFiles.map(f => f.id));
                  }
                }}
                style={styles.bottomButton}
              >
                {selectedFiles.length === imageFiles.length ? 'Deselect All' : 'Select All'}
              </Button>
              <Button
                mode="contained"
                onPress={processSelectedImages}
                loading={processingQueue.length > 0}
                disabled={processingQueue.length > 0}
                style={styles.bottomButton}
                icon="auto-fix"
              >
                Process Images
              </Button>
            </Surface>
          )}

          {/* Image Viewer Modal */}
          {renderImageViewer()}

          {/* Settings Modal */}
          {renderSettingsModal()}

          {/* Snackbar */}
          <Snackbar
            visible={snackbarVisible}
            onDismiss={() => setSnackbarVisible(false)}
            duration={3000}
          >
            {snackbarMessage}
          </Snackbar>
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
    alignItems: 'center',
  },
  selectionBadge: {
    position: 'absolute',
    top: -8,
    right: -8,
    zIndex: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  actionButton: {
    flex: 1,
  },
  imageList: {
    padding: 8,
    paddingBottom: 80,
  },
  gridItem: {
    flex: 1,
    margin: 4,
    aspectRatio: 1,
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: '#f0f0f0',
  },
  selectedGridItem: {
    borderWidth: 3,
    borderColor: '#2196F3',
  },
  gridImage: {
    width: '100%',
    height: '100%',
  },
  processingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  processedIndicator: {
    position: 'absolute',
    top: 4,
    right: 4,
  },
  gridItemInfo: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0,0,0,0.7)',
    padding: 4,
  },
  gridItemName: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '500',
  },
  listItem: {
    flexDirection: 'row',
    padding: 12,
    marginBottom: 8,
    borderRadius: 8,
  },
  selectedListItem: {
    borderWidth: 2,
    borderColor: '#2196F3',
  },
  listItemImage: {
    width: 60,
    height: 60,
    borderRadius: 4,
    marginRight: 12,
  },
  listItemInfo: {
    flex: 1,
    justifyContent: 'center',
  },
  listItemName: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  listItemMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  processingProgress: {
    marginTop: 8,
    height: 2,
  },
  listItemActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 100,
  },
  bottomActionBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    padding: 16,
    justifyContent: 'space-around',
  },
  bottomButton: {
    flex: 1,
    marginHorizontal: 8,
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  modalContent: {
    flex: 1,
  },
  modalFooter: {
    padding: 16,
  },
  modalButton: {
    paddingVertical: 4,
  },
  sliderContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  sliderLabel: {
    fontSize: 14,
    marginBottom: 8,
  },
  slider: {
    height: 40,
  },
  resizeSettings: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  resizeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  imageViewerContainer: {
    flex: 1,
  },
  imageViewerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.8)',
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  imageDisplay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  imageContainer: {
    width: screenWidth,
    height: screenHeight * 0.6,
  },
  fullImage: {
    width: '100%',
    height: '100%',
  },
  cropOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  cropFrame: {
    position: 'absolute',
    top: '20%',
    left: '10%',
    right: '10%',
    bottom: '20%',
    borderWidth: 2,
    borderColor: '#fff',
    borderStyle: 'dashed',
  },
  editModeTabs: {
    backgroundColor: 'rgba(0,0,0,0.8)',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  segmentedButtons: {
    backgroundColor: 'transparent',
  },
  editControls: {
    backgroundColor: 'rgba(0,0,0,0.8)',
    maxHeight: 200,
  },
  adjustmentControls: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  adjustmentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  adjustmentSlider: {
    flex: 1,
    marginHorizontal: 16,
    height: 40,
  },
  adjustmentValue: {
    width: 40,
    textAlign: 'right',
    fontSize: 14,
  },
  adjustmentActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
  },
  cropControls: {
    padding: 16,
  },
  cropPresets: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterList: {
    flexDirection: 'row',
    paddingVertical: 16,
    paddingHorizontal: 8,
  },
  filterItem: {
    alignItems: 'center',
    marginHorizontal: 8,
  },
  selectedFilterItem: {
    transform: [{ scale: 1.1 }],
  },
  filterPreview: {
    width: 60,
    height: 60,
    borderRadius: 8,
    backgroundColor: '#ddd',
    marginBottom: 4,
  },
  filterName: {
    fontSize: 12,
    color: '#fff',
  },
});

export default ImagePreprocessingMobile;
