import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Stage, Layer, Rect, Circle, Line, Text, Arrow, Group } from 'react-konva';
import { Button, Select, ColorPicker, Slider, Input, Card, List, Space, Tooltip, message } from 'antd';
import {
  BorderOutlined,
  RadiusOutlined,
  EditOutlined,
  FontSizeOutlined,
  DrawOutlined,
  ArrowRightOutlined,
  HighlightOutlined,
  CloudUploadOutlined,
  UndoOutlined,
  RedoOutlined,
  DeleteOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  DownloadOutlined,
  UploadOutlined
} from '@ant-design/icons';
import Konva from 'konva';
import './ImageAnnotationCanvas.css';

const { Option } = Select;

export enum AnnotationType {
  BOUNDING_BOX = 'bounding_box',
  CIRCLE = 'circle',
  POLYGON = 'polygon',
  LINE = 'line',
  ARROW = 'arrow',
  TEXT = 'text',
  FREEHAND = 'freehand',
  BLUR = 'blur',
  HIGHLIGHT = 'highlight'
}

export enum DrawingMode {
  SELECT = 'select',
  DRAW = 'draw',
  EDIT = 'edit',
  DELETE = 'delete'
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
  points?: Point[];
  style: AnnotationStyle;
  visible: boolean;
  locked: boolean;
}

interface BoundingBoxAnnotation extends Annotation {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface CircleAnnotation extends Annotation {
  x: number;
  y: number;
  radius: number;
}

interface TextAnnotation extends Annotation {
  x: number;
  y: number;
  text: string;
}

const ImageAnnotationCanvas: React.FC = () => {
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(null);
  const [currentTool, setCurrentTool] = useState<AnnotationType>(AnnotationType.BOUNDING_BOX);
  const [drawingMode, setDrawingMode] = useState<DrawingMode>(DrawingMode.DRAW);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentPoints, setCurrentPoints] = useState<Point[]>([]);
  const [style, setStyle] = useState<AnnotationStyle>({
    strokeColor: '#ff0000',
    strokeWidth: 2,
    fontSize: 16,
    opacity: 1
  });
  
  const stageRef = useRef<Konva.Stage>(null);
  const layerRef = useRef<Konva.Layer>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [undoStack, setUndoStack] = useState<Annotation[][]>([]);
  const [redoStack, setRedoStack] = useState<Annotation[][]>([]);

  // Load image
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          setImage(img);
          // Reset annotations when new image is loaded
          setAnnotations([]);
          setUndoStack([]);
          setRedoStack([]);
        };
        img.src = e.target?.result as string;
      };
      reader.readAsDataURL(file);
    }
  };

  // Mouse event handlers
  const handleMouseDown = (e: Konva.KonvaEventObject<MouseEvent>) => {
    if (drawingMode !== DrawingMode.DRAW) return;

    const stage = e.target.getStage();
    if (!stage) return;

    const point = stage.getPointerPosition();
    if (!point) return;

    setIsDrawing(true);
    setCurrentPoints([point]);
  };

  const handleMouseMove = (e: Konva.KonvaEventObject<MouseEvent>) => {
    if (!isDrawing || drawingMode !== DrawingMode.DRAW) return;

    const stage = e.target.getStage();
    if (!stage) return;

    const point = stage.getPointerPosition();
    if (!point) return;

    setCurrentPoints(prev => [...prev, point]);
  };

  const handleMouseUp = () => {
    if (!isDrawing || currentPoints.length < 2) {
      setIsDrawing(false);
      setCurrentPoints([]);
      return;
    }

    // Create annotation based on current tool
    const newAnnotation = createAnnotation(currentPoints);
    if (newAnnotation) {
      addAnnotation(newAnnotation);
    }

    setIsDrawing(false);
    setCurrentPoints([]);
  };

  // Create annotation from points
  const createAnnotation = (points: Point[]): Annotation | null => {
    const id = `ann_${Date.now()}`;
    const baseAnnotation = {
      id,
      style: { ...style },
      visible: true,
      locked: false
    };

    switch (currentTool) {
      case AnnotationType.BOUNDING_BOX:
        if (points.length >= 2) {
          const x = Math.min(points[0].x, points[points.length - 1].x);
          const y = Math.min(points[0].y, points[points.length - 1].y);
          const width = Math.abs(points[points.length - 1].x - points[0].x);
          const height = Math.abs(points[points.length - 1].y - points[0].y);
          
          return {
            ...baseAnnotation,
            type: AnnotationType.BOUNDING_BOX,
            x,
            y,
            width,
            height
          } as BoundingBoxAnnotation;
        }
        break;

      case AnnotationType.CIRCLE:
        if (points.length >= 2) {
          const center = points[0];
          const radius = Math.sqrt(
            Math.pow(points[points.length - 1].x - center.x, 2) +
            Math.pow(points[points.length - 1].y - center.y, 2)
          );
          
          return {
            ...baseAnnotation,
            type: AnnotationType.CIRCLE,
            x: center.x,
            y: center.y,
            radius
          } as CircleAnnotation;
        }
        break;

      case AnnotationType.LINE:
      case AnnotationType.ARROW:
        if (points.length >= 2) {
          return {
            ...baseAnnotation,
            type: currentTool,
            points: [points[0], points[points.length - 1]]
          };
        }
        break;

      case AnnotationType.FREEHAND:
        return {
          ...baseAnnotation,
          type: AnnotationType.FREEHAND,
          points
        };

      default:
        return null;
    }

    return null;
  };

  // Add annotation with undo support
  const addAnnotation = (annotation: Annotation) => {
    setUndoStack(prev => [...prev, annotations]);
    setRedoStack([]);
    setAnnotations(prev => [...prev, annotation]);
    message.success('Annotation added');
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
    message.success('Annotation deleted');
  };

  // Toggle visibility
  const toggleVisibility = (id: string) => {
    setAnnotations(prev => prev.map(ann => 
      ann.id === id ? { ...ann, visible: !ann.visible } : ann
    ));
  };

  // Update annotation
  const updateAnnotation = (id: string, updates: Partial<Annotation>) => {
    setAnnotations(prev => prev.map(ann => 
      ann.id === id ? { ...ann, ...updates } : ann
    ));
  };

  // Export annotations
  const exportAnnotations = () => {
    const data = {
      image: {
        width: image?.width || 0,
        height: image?.height || 0
      },
      annotations
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `annotations_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    message.success('Annotations exported');
  };

  // Import annotations
  const importAnnotations = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target?.result as string);
          setAnnotations(data.annotations || []);
          message.success('Annotations imported');
        } catch (error) {
          message.error('Failed to import annotations');
        }
      };
      reader.readAsText(file);
    }
  };

  // Render annotation shapes
  const renderAnnotation = (annotation: Annotation) => {
    const commonProps = {
      key: annotation.id,
      id: annotation.id,
      visible: annotation.visible,
      draggable: drawingMode === DrawingMode.EDIT && !annotation.locked,
      onClick: () => {
        if (drawingMode === DrawingMode.SELECT) {
          setSelectedAnnotation(annotation.id);
        } else if (drawingMode === DrawingMode.DELETE) {
          deleteAnnotation(annotation.id);
        }
      },
      onDragEnd: (e: Konva.KonvaEventObject<DragEvent>) => {
        const node = e.target;
        updateAnnotation(annotation.id, {
          x: node.x(),
          y: node.y()
        });
      }
    };

    switch (annotation.type) {
      case AnnotationType.BOUNDING_BOX:
        const bbox = annotation as BoundingBoxAnnotation;
        return (
          <Group {...commonProps}>
            <Rect
              x={bbox.x}
              y={bbox.y}
              width={bbox.width}
              height={bbox.height}
              stroke={bbox.style.strokeColor}
              strokeWidth={bbox.style.strokeWidth}
              fill={bbox.style.fillColor}
              opacity={bbox.style.opacity}
            />
            {bbox.label && (
              <Text
                x={bbox.x}
                y={bbox.y - 20}
                text={bbox.label}
                fontSize={12}
                fill={bbox.style.strokeColor}
              />
            )}
          </Group>
        );

      case AnnotationType.CIRCLE:
        const circle = annotation as CircleAnnotation;
        return (
          <Circle
            {...commonProps}
            x={circle.x}
            y={circle.y}
            radius={circle.radius}
            stroke={circle.style.strokeColor}
            strokeWidth={circle.style.strokeWidth}
            fill={circle.style.fillColor}
            opacity={circle.style.opacity}
          />
        );

      case AnnotationType.LINE:
        return (
          <Line
            {...commonProps}
            points={annotation.points?.flatMap(p => [p.x, p.y]) || []}
            stroke={annotation.style.strokeColor}
            strokeWidth={annotation.style.strokeWidth}
            opacity={annotation.style.opacity}
          />
        );

      case AnnotationType.ARROW:
        return (
          <Arrow
            {...commonProps}
            points={annotation.points?.flatMap(p => [p.x, p.y]) || []}
            stroke={annotation.style.strokeColor}
            strokeWidth={annotation.style.strokeWidth}
            fill={annotation.style.strokeColor}
            opacity={annotation.style.opacity}
          />
        );

      case AnnotationType.TEXT:
        const text = annotation as TextAnnotation;
        return (
          <Text
            {...commonProps}
            x={text.x}
            y={text.y}
            text={text.text}
            fontSize={text.style.fontSize}
            fill={text.style.strokeColor}
            opacity={text.style.opacity}
          />
        );

      case AnnotationType.FREEHAND:
        return (
          <Line
            {...commonProps}
            points={annotation.points?.flatMap(p => [p.x, p.y]) || []}
            stroke={annotation.style.strokeColor}
            strokeWidth={annotation.style.strokeWidth}
            opacity={annotation.style.opacity}
            tension={0.5}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="image-annotation-container">
      <div className="annotation-toolbar">
        <Space>
          <Select value={drawingMode} onChange={setDrawingMode} style={{ width: 120 }}>
            <Option value={DrawingMode.DRAW}>Draw</Option>
            <Option value={DrawingMode.SELECT}>Select</Option>
            <Option value={DrawingMode.EDIT}>Edit</Option>
            <Option value={DrawingMode.DELETE}>Delete</Option>
          </Select>

          <Button.Group>
            <Tooltip title="Bounding Box">
              <Button
                icon={<BorderOutlined />}
                type={currentTool === AnnotationType.BOUNDING_BOX ? 'primary' : 'default'}
                onClick={() => setCurrentTool(AnnotationType.BOUNDING_BOX)}
              />
            </Tooltip>
            <Tooltip title="Circle">
              <Button
                icon={<RadiusOutlined />}
                type={currentTool === AnnotationType.CIRCLE ? 'primary' : 'default'}
                onClick={() => setCurrentTool(AnnotationType.CIRCLE)}
              />
            </Tooltip>
            <Tooltip title="Line">
              <Button
                icon={<EditOutlined />}
                type={currentTool === AnnotationType.LINE ? 'primary' : 'default'}
                onClick={() => setCurrentTool(AnnotationType.LINE)}
              />
            </Tooltip>
            <Tooltip title="Arrow">
              <Button
                icon={<ArrowRightOutlined />}
                type={currentTool === AnnotationType.ARROW ? 'primary' : 'default'}
                onClick={() => setCurrentTool(AnnotationType.ARROW)}
              />
            </Tooltip>
            <Tooltip title="Text">
              <Button
                icon={<FontSizeOutlined />}
                type={currentTool === AnnotationType.TEXT ? 'primary' : 'default'}
                onClick={() => setCurrentTool(AnnotationType.TEXT)}
              />
            </Tooltip>
            <Tooltip title="Freehand">
              <Button
                icon={<DrawOutlined />}
                type={currentTool === AnnotationType.FREEHAND ? 'primary' : 'default'}
                onClick={() => setCurrentTool(AnnotationType.FREEHAND)}
              />
            </Tooltip>
          </Button.Group>

          <Button icon={<UndoOutlined />} onClick={undo} disabled={undoStack.length === 0} />
          <Button icon={<RedoOutlined />} onClick={redo} disabled={redoStack.length === 0} />
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            style={{ display: 'none' }}
          />
          <Button
            icon={<CloudUploadOutlined />}
            onClick={() => fileInputRef.current?.click()}
          >
            Upload Image
          </Button>

          <Button icon={<DownloadOutlined />} onClick={exportAnnotations}>
            Export
          </Button>
        </Space>
      </div>

      <div className="annotation-main">
        <div className="canvas-container">
          {image ? (
            <Stage
              ref={stageRef}
              width={image.width}
              height={image.height}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
            >
              <Layer ref={layerRef}>
                <Rect
                  x={0}
                  y={0}
                  width={image.width}
                  height={image.height}
                  fillPatternImage={image}
                />
                {annotations.map(renderAnnotation)}
                {isDrawing && currentPoints.length > 1 && (
                  <Line
                    points={currentPoints.flatMap(p => [p.x, p.y])}
                    stroke={style.strokeColor}
                    strokeWidth={style.strokeWidth}
                    dash={[5, 5]}
                  />
                )}
              </Layer>
            </Stage>
          ) : (
            <div className="upload-placeholder">
              <CloudUploadOutlined style={{ fontSize: 48 }} />
              <p>Click to upload an image</p>
              <Button onClick={() => fileInputRef.current?.click()}>
                Select Image
              </Button>
            </div>
          )}
        </div>

        <div className="annotation-sidebar">
          <Card title="Style Settings" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <label>Stroke Color</label>
                <Input
                  type="color"
                  value={style.strokeColor}
                  onChange={(e) => setStyle(prev => ({ ...prev, strokeColor: e.target.value }))}
                />
              </div>
              <div>
                <label>Stroke Width</label>
                <Slider
                  min={1}
                  max={10}
                  value={style.strokeWidth}
                  onChange={(value) => setStyle(prev => ({ ...prev, strokeWidth: value }))}
                />
              </div>
              <div>
                <label>Opacity</label>
                <Slider
                  min={0}
                  max={1}
                  step={0.1}
                  value={style.opacity}
                  onChange={(value) => setStyle(prev => ({ ...prev, opacity: value }))}
                />
              </div>
            </Space>
          </Card>

          <Card title="Annotations" size="small" style={{ marginTop: 16 }}>
            <List
              dataSource={annotations}
              renderItem={(annotation) => (
                <List.Item
                  actions={[
                    <Button
                      icon={annotation.visible ? <EyeOutlined /> : <EyeInvisibleOutlined />}
                      size="small"
                      onClick={() => toggleVisibility(annotation.id)}
                    />,
                    <Button
                      icon={<DeleteOutlined />}
                      size="small"
                      danger
                      onClick={() => deleteAnnotation(annotation.id)}
                    />
                  ]}
                >
                  <span>{annotation.type} - {annotation.label || annotation.id}</span>
                </List.Item>
              )}
            />
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ImageAnnotationCanvas;