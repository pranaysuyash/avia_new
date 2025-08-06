import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Modal,
  TextInput,
  Alert,
  Dimensions,
  Image,
  PanResponder,
  GestureResponderEvent,
  PanResponderGestureState,
} from 'react-native';
import Svg, { Rect, Circle, Line, Polyline, Polygon, Text as SvgText, G, Defs, ClipPath } from 'react-native-svg';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system';
import Icon from 'react-native-vector-icons/MaterialIcons';

export enum AnnotationType {
  BOUNDING_BOX = 'bounding_box',
  CIRCLE = 'circle',
  POLYGON = 'polygon',
  LINE = 'line',
  ARROW = 'arrow',
  TEXT = 'text',
  FREEHAND = 'freehand',
}

interface Point {
  x: number;
  y: number;
}

interface AnnotationStyle {
  strokeColor: string;
  fillColor?: string;
  strokeWidth: number;
  fontSize?: number;
  opacity?: number;
}

interface Annotation {
  id: string;
  type: AnnotationType;
  label?: string;
  points: Point[];
  style: AnnotationStyle;
  visible: boolean;
}

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

const ImageAnnotationMobile: React.FC = () => {
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [currentTool, setCurrentTool] = useState<AnnotationType>(AnnotationType.BOUNDING_BOX);
  const [currentPoints, setCurrentPoints] = useState<Point[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(null);
  const [showToolbar, setShowToolbar] = useState(true);
  const [showAnnotationList, setShowAnnotationList] = useState(false);
  const [labelModalVisible, setLabelModalVisible] = useState(false);
  const [tempLabel, setTempLabel] = useState('');
  const [pendingAnnotation, setPendingAnnotation] = useState<Annotation | null>(null);
  
  const [style, setStyle] = useState<AnnotationStyle>({
    strokeColor: '#ff0000',
    strokeWidth: 2,
    fontSize: 16,
    opacity: 1,
  });
  
  const [undoStack, setUndoStack] = useState<Annotation[][]>([]);
  const [redoStack, setRedoStack] = useState<Annotation[][]>([]);

  // Pan responder for drawing
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      
      onPanResponderGrant: (evt: GestureResponderEvent) => {
        const { locationX, locationY } = evt.nativeEvent;
        handleTouchStart(locationX, locationY);
      },
      
      onPanResponderMove: (evt: GestureResponderEvent) => {
        const { locationX, locationY } = evt.nativeEvent;
        handleTouchMove(locationX, locationY);
      },
      
      onPanResponderRelease: () => {
        handleTouchEnd();
      },
    })
  ).current;

  // Pick image from gallery
  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Denied', 'We need camera roll permissions to select images.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: false,
      quality: 1,
    });

    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0];
      setImageUri(asset.uri);
      setImageSize({ width: asset.width, height: asset.height });
      setAnnotations([]);
      setUndoStack([]);
      setRedoStack([]);
    }
  };

  // Handle touch events
  const handleTouchStart = (x: number, y: number) => {
    if (!imageUri) return;

    if (currentTool === AnnotationType.TEXT) {
      // For text, show input modal
      setCurrentPoints([{ x, y }]);
      setLabelModalVisible(true);
    } else {
      setIsDrawing(true);
      setCurrentPoints([{ x, y }]);
    }
  };

  const handleTouchMove = (x: number, y: number) => {
    if (!isDrawing || !imageUri) return;

    if (currentTool === AnnotationType.FREEHAND) {
      setCurrentPoints(prev => [...prev, { x, y }]);
    } else if (currentTool === AnnotationType.POLYGON) {
      // For polygon, add points on tap
      setCurrentPoints(prev => [...prev, { x, y }]);
    } else {
      // For other tools, update last point
      setCurrentPoints(prev => {
        const newPoints = [...prev];
        if (newPoints.length === 1) {
          newPoints.push({ x, y });
        } else {
          newPoints[newPoints.length - 1] = { x, y };
        }
        return newPoints;
      });
    }
  };

  const handleTouchEnd = () => {
    if (!isDrawing || currentPoints.length < 2) {
      setIsDrawing(false);
      setCurrentPoints([]);
      return;
    }

    // Create annotation
    const newAnnotation: Annotation = {
      id: `ann_${Date.now()}`,
      type: currentTool,
      points: [...currentPoints],
      style: { ...style },
      visible: true,
    };

    // For certain types, ask for label
    if ([AnnotationType.BOUNDING_BOX, AnnotationType.CIRCLE].includes(currentTool)) {
      setPendingAnnotation(newAnnotation);
      setLabelModalVisible(true);
    } else {
      addAnnotation(newAnnotation);
    }

    setIsDrawing(false);
    setCurrentPoints([]);
  };

  // Add annotation with undo support
  const addAnnotation = (annotation: Annotation) => {
    setUndoStack(prev => [...prev, annotations]);
    setRedoStack([]);
    setAnnotations(prev => [...prev, annotation]);
  };

  // Handle label submission
  const handleLabelSubmit = () => {
    if (currentTool === AnnotationType.TEXT && currentPoints.length > 0) {
      // Create text annotation
      const textAnnotation: Annotation = {
        id: `ann_${Date.now()}`,
        type: AnnotationType.TEXT,
        points: currentPoints,
        label: tempLabel,
        style: { ...style },
        visible: true,
      };
      addAnnotation(textAnnotation);
    } else if (pendingAnnotation) {
      // Add label to pending annotation
      pendingAnnotation.label = tempLabel;
      addAnnotation(pendingAnnotation);
      setPendingAnnotation(null);
    }

    setLabelModalVisible(false);
    setTempLabel('');
    setCurrentPoints([]);
  };

  // Undo/Redo
  const undo = () => {
    if (undoStack.length === 0) return;

    const previousState = undoStack[undoStack.length - 1];
    setUndoStack(prev => prev.slice(0, -1));
    setRedoStack(prev => [...prev, annotations]);
    setAnnotations(previousState);
  };

  const redo = () => {
    if (redoStack.length === 0) return;

    const nextState = redoStack[redoStack.length - 1];
    setRedoStack(prev => prev.slice(0, -1));
    setUndoStack(prev => [...prev, annotations]);
    setAnnotations(nextState);
  };

  // Delete annotation
  const deleteAnnotation = (id: string) => {
    setUndoStack(prev => [...prev, annotations]);
    setRedoStack([]);
    setAnnotations(prev => prev.filter(ann => ann.id !== id));
  };

  // Toggle visibility
  const toggleVisibility = (id: string) => {
    setAnnotations(prev => prev.map(ann => 
      ann.id === id ? { ...ann, visible: !ann.visible } : ann
    ));
  };

  // Export annotations
  const exportAnnotations = async () => {
    const data = {
      image: {
        uri: imageUri,
        width: imageSize.width,
        height: imageSize.height,
      },
      annotations,
    };

    const fileName = `annotations_${Date.now()}.json`;
    const fileUri = `${FileSystem.documentDirectory}${fileName}`;

    try {
      await FileSystem.writeAsStringAsync(fileUri, JSON.stringify(data, null, 2));
      Alert.alert('Success', `Annotations saved to ${fileName}`);
    } catch (error) {
      Alert.alert('Error', 'Failed to save annotations');
    }
  };

  // Render annotation
  const renderAnnotation = (annotation: Annotation) => {
    if (!annotation.visible) return null;

    const { type, points, style: annStyle, label } = annotation;

    switch (type) {
      case AnnotationType.BOUNDING_BOX:
        if (points.length >= 2) {
          const x = Math.min(points[0].x, points[1].x);
          const y = Math.min(points[0].y, points[1].y);
          const width = Math.abs(points[1].x - points[0].x);
          const height = Math.abs(points[1].y - points[0].y);

          return (
            <G key={annotation.id}>
              <Rect
                x={x}
                y={y}
                width={width}
                height={height}
                stroke={annStyle.strokeColor}
                strokeWidth={annStyle.strokeWidth}
                fill={annStyle.fillColor || 'transparent'}
                opacity={annStyle.opacity}
              />
              {label && (
                <SvgText
                  x={x}
                  y={y - 5}
                  fill={annStyle.strokeColor}
                  fontSize={12}
                >
                  {label}
                </SvgText>
              )}
            </G>
          );
        }
        break;

      case AnnotationType.CIRCLE:
        if (points.length >= 2) {
          const center = points[0];
          const radius = Math.sqrt(
            Math.pow(points[1].x - center.x, 2) +
            Math.pow(points[1].y - center.y, 2)
          );

          return (
            <Circle
              key={annotation.id}
              cx={center.x}
              cy={center.y}
              r={radius}
              stroke={annStyle.strokeColor}
              strokeWidth={annStyle.strokeWidth}
              fill={annStyle.fillColor || 'transparent'}
              opacity={annStyle.opacity}
            />
          );
        }
        break;

      case AnnotationType.LINE:
        if (points.length >= 2) {
          return (
            <Line
              key={annotation.id}
              x1={points[0].x}
              y1={points[0].y}
              x2={points[1].x}
              y2={points[1].y}
              stroke={annStyle.strokeColor}
              strokeWidth={annStyle.strokeWidth}
              opacity={annStyle.opacity}
            />
          );
        }
        break;

      case AnnotationType.ARROW:
        if (points.length >= 2) {
          const angle = Math.atan2(
            points[1].y - points[0].y,
            points[1].x - points[0].x
          );
          const arrowLength = 10;

          return (
            <G key={annotation.id}>
              <Line
                x1={points[0].x}
                y1={points[0].y}
                x2={points[1].x}
                y2={points[1].y}
                stroke={annStyle.strokeColor}
                strokeWidth={annStyle.strokeWidth}
                opacity={annStyle.opacity}
              />
              <Line
                x1={points[1].x}
                y1={points[1].y}
                x2={points[1].x - arrowLength * Math.cos(angle - Math.PI / 6)}
                y2={points[1].y - arrowLength * Math.sin(angle - Math.PI / 6)}
                stroke={annStyle.strokeColor}
                strokeWidth={annStyle.strokeWidth}
              />
              <Line
                x1={points[1].x}
                y1={points[1].y}
                x2={points[1].x - arrowLength * Math.cos(angle + Math.PI / 6)}
                y2={points[1].y - arrowLength * Math.sin(angle + Math.PI / 6)}
                stroke={annStyle.strokeColor}
                strokeWidth={annStyle.strokeWidth}
              />
            </G>
          );
        }
        break;

      case AnnotationType.FREEHAND:
        if (points.length > 1) {
          const pathData = points
            .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
            .join(' ');

          return (
            <Polyline
              key={annotation.id}
              points={points.map(p => `${p.x},${p.y}`).join(' ')}
              stroke={annStyle.strokeColor}
              strokeWidth={annStyle.strokeWidth}
              fill="none"
              opacity={annStyle.opacity}
            />
          );
        }
        break;

      case AnnotationType.TEXT:
        if (points.length > 0 && label) {
          return (
            <SvgText
              key={annotation.id}
              x={points[0].x}
              y={points[0].y}
              fill={annStyle.strokeColor}
              fontSize={annStyle.fontSize}
              opacity={annStyle.opacity}
            >
              {label}
            </SvgText>
          );
        }
        break;
    }

    return null;
  };

  // Render current drawing
  const renderCurrentDrawing = () => {
    if (!isDrawing || currentPoints.length === 0) return null;

    switch (currentTool) {
      case AnnotationType.BOUNDING_BOX:
        if (currentPoints.length >= 2) {
          const x = Math.min(currentPoints[0].x, currentPoints[1].x);
          const y = Math.min(currentPoints[0].y, currentPoints[1].y);
          const width = Math.abs(currentPoints[1].x - currentPoints[0].x);
          const height = Math.abs(currentPoints[1].y - currentPoints[0].y);

          return (
            <Rect
              x={x}
              y={y}
              width={width}
              height={height}
              stroke={style.strokeColor}
              strokeWidth={style.strokeWidth}
              fill="transparent"
              strokeDasharray="5,5"
            />
          );
        }
        break;

      case AnnotationType.CIRCLE:
        if (currentPoints.length >= 2) {
          const center = currentPoints[0];
          const radius = Math.sqrt(
            Math.pow(currentPoints[1].x - center.x, 2) +
            Math.pow(currentPoints[1].y - center.y, 2)
          );

          return (
            <Circle
              cx={center.x}
              cy={center.y}
              r={radius}
              stroke={style.strokeColor}
              strokeWidth={style.strokeWidth}
              fill="transparent"
              strokeDasharray="5,5"
            />
          );
        }
        break;

      case AnnotationType.LINE:
        if (currentPoints.length >= 2) {
          return (
            <Line
              x1={currentPoints[0].x}
              y1={currentPoints[0].y}
              x2={currentPoints[1].x}
              y2={currentPoints[1].y}
              stroke={style.strokeColor}
              strokeWidth={style.strokeWidth}
              strokeDasharray="5,5"
            />
          );
        }
        break;

      case AnnotationType.FREEHAND:
        if (currentPoints.length > 1) {
          return (
            <Polyline
              points={currentPoints.map(p => `${p.x},${p.y}`).join(' ')}
              stroke={style.strokeColor}
              strokeWidth={style.strokeWidth}
              fill="none"
              strokeDasharray="5,5"
            />
          );
        }
        break;
    }

    return null;
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Image Annotation</Text>
        <View style={styles.headerButtons}>
          <TouchableOpacity onPress={() => setShowToolbar(!showToolbar)}>
            <Icon name="build" size={24} color="#fff" />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => setShowAnnotationList(true)}>
            <Icon name="list" size={24} color="#fff" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Canvas Area */}
      <View style={styles.canvasContainer}>
        {imageUri ? (
          <View style={styles.imageWrapper}>
            <Image
              source={{ uri: imageUri }}
              style={[styles.image, { width: screenWidth, height: screenWidth * (imageSize.height / imageSize.width) }]}
              resizeMode="contain"
            />
            <Svg
              style={StyleSheet.absoluteFillObject}
              width={screenWidth}
              height={screenWidth * (imageSize.height / imageSize.width)}
              {...panResponder.panHandlers}
            >
              {annotations.map(renderAnnotation)}
              {renderCurrentDrawing()}
            </Svg>
          </View>
        ) : (
          <TouchableOpacity style={styles.uploadButton} onPress={pickImage}>
            <Icon name="add-photo-alternate" size={48} color="#666" />
            <Text style={styles.uploadText}>Tap to select an image</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Toolbar */}
      {showToolbar && (
        <View style={styles.toolbar}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <TouchableOpacity
              style={[styles.toolButton, currentTool === AnnotationType.BOUNDING_BOX && styles.toolButtonActive]}
              onPress={() => setCurrentTool(AnnotationType.BOUNDING_BOX)}
            >
              <Icon name="crop-square" size={24} color={currentTool === AnnotationType.BOUNDING_BOX ? '#fff' : '#333'} />
              <Text style={[styles.toolText, currentTool === AnnotationType.BOUNDING_BOX && styles.toolTextActive]}>Box</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.toolButton, currentTool === AnnotationType.CIRCLE && styles.toolButtonActive]}
              onPress={() => setCurrentTool(AnnotationType.CIRCLE)}
            >
              <Icon name="panorama-fish-eye" size={24} color={currentTool === AnnotationType.CIRCLE ? '#fff' : '#333'} />
              <Text style={[styles.toolText, currentTool === AnnotationType.CIRCLE && styles.toolTextActive]}>Circle</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.toolButton, currentTool === AnnotationType.LINE && styles.toolButtonActive]}
              onPress={() => setCurrentTool(AnnotationType.LINE)}
            >
              <Icon name="remove" size={24} color={currentTool === AnnotationType.LINE ? '#fff' : '#333'} />
              <Text style={[styles.toolText, currentTool === AnnotationType.LINE && styles.toolTextActive]}>Line</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.toolButton, currentTool === AnnotationType.ARROW && styles.toolButtonActive]}
              onPress={() => setCurrentTool(AnnotationType.ARROW)}
            >
              <Icon name="trending-flat" size={24} color={currentTool === AnnotationType.ARROW ? '#fff' : '#333'} />
              <Text style={[styles.toolText, currentTool === AnnotationType.ARROW && styles.toolTextActive]}>Arrow</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.toolButton, currentTool === AnnotationType.TEXT && styles.toolButtonActive]}
              onPress={() => setCurrentTool(AnnotationType.TEXT)}
            >
              <Icon name="text-fields" size={24} color={currentTool === AnnotationType.TEXT ? '#fff' : '#333'} />
              <Text style={[styles.toolText, currentTool === AnnotationType.TEXT && styles.toolTextActive]}>Text</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.toolButton, currentTool === AnnotationType.FREEHAND && styles.toolButtonActive]}
              onPress={() => setCurrentTool(AnnotationType.FREEHAND)}
            >
              <Icon name="gesture" size={24} color={currentTool === AnnotationType.FREEHAND ? '#fff' : '#333'} />
              <Text style={[styles.toolText, currentTool === AnnotationType.FREEHAND && styles.toolTextActive]}>Draw</Text>
            </TouchableOpacity>
          </ScrollView>

          <View style={styles.actionButtons}>
            <TouchableOpacity style={styles.actionButton} onPress={undo} disabled={undoStack.length === 0}>
              <Icon name="undo" size={24} color={undoStack.length === 0 ? '#ccc' : '#333'} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionButton} onPress={redo} disabled={redoStack.length === 0}>
              <Icon name="redo" size={24} color={redoStack.length === 0 ? '#ccc' : '#333'} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionButton} onPress={exportAnnotations}>
              <Icon name="save" size={24} color="#333" />
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Label Input Modal */}
      <Modal
        visible={labelModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setLabelModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Enter Label</Text>
            <TextInput
              style={styles.modalInput}
              value={tempLabel}
              onChangeText={setTempLabel}
              placeholder="Enter label..."
              autoFocus
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.modalButton} onPress={() => setLabelModalVisible(false)}>
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.modalButton, styles.modalButtonPrimary]} onPress={handleLabelSubmit}>
                <Text style={[styles.modalButtonText, styles.modalButtonTextPrimary]}>OK</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Annotation List Modal */}
      <Modal
        visible={showAnnotationList}
        transparent
        animationType="slide"
        onRequestClose={() => setShowAnnotationList(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, styles.annotationListModal]}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Annotations</Text>
              <TouchableOpacity onPress={() => setShowAnnotationList(false)}>
                <Icon name="close" size={24} color="#333" />
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.annotationList}>
              {annotations.map((annotation, index) => (
                <View key={annotation.id} style={styles.annotationItem}>
                  <Text style={styles.annotationItemText}>
                    {annotation.type} - {annotation.label || `Annotation ${index + 1}`}
                  </Text>
                  <View style={styles.annotationItemActions}>
                    <TouchableOpacity onPress={() => toggleVisibility(annotation.id)}>
                      <Icon name={annotation.visible ? 'visibility' : 'visibility-off'} size={20} color="#666" />
                    </TouchableOpacity>
                    <TouchableOpacity onPress={() => deleteAnnotation(annotation.id)}>
                      <Icon name="delete" size={20} color="#f44336" />
                    </TouchableOpacity>
                  </View>
                </View>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#2196F3',
    padding: 16,
    paddingTop: 40,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerButtons: {
    flexDirection: 'row',
    gap: 16,
  },
  canvasContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#e0e0e0',
  },
  imageWrapper: {
    position: 'relative',
  },
  image: {
    backgroundColor: '#fff',
  },
  uploadButton: {
    backgroundColor: '#fff',
    padding: 40,
    borderRadius: 8,
    alignItems: 'center',
    elevation: 2,
  },
  uploadText: {
    marginTop: 8,
    fontSize: 16,
    color: '#666',
  },
  toolbar: {
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingVertical: 8,
  },
  toolButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginHorizontal: 4,
    borderRadius: 8,
    alignItems: 'center',
    minWidth: 60,
  },
  toolButtonActive: {
    backgroundColor: '#2196F3',
  },
  toolText: {
    fontSize: 12,
    marginTop: 4,
    color: '#333',
  },
  toolTextActive: {
    color: '#fff',
  },
  actionButtons: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: 8,
    gap: 16,
  },
  actionButton: {
    padding: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 20,
    width: '80%',
    maxWidth: 300,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 4,
    padding: 8,
    marginTop: 16,
    fontSize: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 20,
    gap: 12,
  },
  modalButton: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 4,
  },
  modalButtonPrimary: {
    backgroundColor: '#2196F3',
  },
  modalButtonText: {
    fontSize: 16,
    color: '#666',
  },
  modalButtonTextPrimary: {
    color: '#fff',
  },
  annotationListModal: {
    width: '90%',
    maxHeight: '80%',
  },
  annotationList: {
    maxHeight: 300,
  },
  annotationItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  annotationItemText: {
    flex: 1,
    fontSize: 14,
  },
  annotationItemActions: {
    flexDirection: 'row',
    gap: 12,
  },
});

export default ImageAnnotationMobile;