import React, { useState, useRef, useEffect } from 'react';
import { Card, Button, Select, Slider, Radio, Space, List, Modal, message, Upload, Tooltip } from 'antd';
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
  SaveOutlined,
  FolderOpenOutlined
} from '@ant-design/icons';
import './ImageAnnotation.css';

const { Option } = Select;
const { Dragger } = Upload;

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

interface Annotation {
  id: string;
  type: AnnotationType;
  label?: string;
  points: { x: number; y: number }[];
  style: {
    strokeColor: string;
    fillColor?: string;
    strokeWidth: number;
    fontSize?: number;
  };
  visible: boolean;
}

const ImageAnnotation: React.FC = () => {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [currentTool, setCurrentTool] = useState<AnnotationType>(AnnotationType.BOUNDING_BOX);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentAnnotation, setCurrentAnnotation] = useState<Annotation | null>(null);
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(null);
  const [undoStack, setUndoStack] = useState<Annotation[][]>([]);
  const [redoStack, setRedoStack] = useState<Annotation[][]>([]);
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  
  const [style, setStyle] = useState({
    strokeColor: '#ff0000',
    fillColor: '',
    strokeWidth: 2,
    fontSize: 16
  });

  // Initialize canvas
  useEffect(() => {
    if (imageSrc && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = () => {
        imageRef.current = img;
        canvas.width = img.width;
        canvas.height = img.height;
        redrawCanvas();
      };
      
      img.src = imageSrc;
    }
  }, [imageSrc]);

  // Redraw canvas
  const redrawCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    const img = imageRef.current;
    
    if (!canvas || !ctx || !img) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw image
    ctx.drawImage(img, 0, 0);
    
    // Draw annotations
    annotations.forEach(annotation => {
      if (!annotation.visible) return;
      
      ctx.strokeStyle = annotation.style.strokeColor;
      ctx.lineWidth = annotation.style.strokeWidth;
      
      switch (annotation.type) {
        case AnnotationType.BOUNDING_BOX:
          if (annotation.points.length >= 2) {
            const x = Math.min(annotation.points[0].x, annotation.points[1].x);
            const y = Math.min(annotation.points[0].y, annotation.points[1].y);
            const width = Math.abs(annotation.points[1].x - annotation.points[0].x);
            const height = Math.abs(annotation.points[1].y - annotation.points[0].y);
            
            ctx.strokeRect(x, y, width, height);
            
            if (annotation.style.fillColor) {
              ctx.fillStyle = annotation.style.fillColor;
              ctx.fillRect(x, y, width, height);
            }
            
            if (annotation.label) {
              ctx.fillStyle = annotation.style.strokeColor;
              ctx.font = '12px Arial';
              ctx.fillText(annotation.label, x, y - 5);
            }
          }
          break;
          
        case AnnotationType.CIRCLE:
          if (annotation.points.length >= 2) {
            const center = annotation.points[0];
            const radius = Math.sqrt(
              Math.pow(annotation.points[1].x - center.x, 2) +
              Math.pow(annotation.points[1].y - center.y, 2)
            );
            
            ctx.beginPath();
            ctx.arc(center.x, center.y, radius, 0, 2 * Math.PI);
            ctx.stroke();
            
            if (annotation.style.fillColor) {
              ctx.fillStyle = annotation.style.fillColor;
              ctx.fill();
            }
          }
          break;
          
        case AnnotationType.LINE:
        case AnnotationType.ARROW:
          if (annotation.points.length >= 2) {
            ctx.beginPath();
            ctx.moveTo(annotation.points[0].x, annotation.points[0].y);
            ctx.lineTo(annotation.points[1].x, annotation.points[1].y);
            ctx.stroke();
            
            if (annotation.type === AnnotationType.ARROW) {
              // Draw arrowhead
              const angle = Math.atan2(
                annotation.points[1].y - annotation.points[0].y,
                annotation.points[1].x - annotation.points[0].x
              );
              const arrowLength = 10;
              
              ctx.beginPath();
              ctx.moveTo(annotation.points[1].x, annotation.points[1].y);
              ctx.lineTo(
                annotation.points[1].x - arrowLength * Math.cos(angle - Math.PI / 6),
                annotation.points[1].y - arrowLength * Math.sin(angle - Math.PI / 6)
              );
              ctx.moveTo(annotation.points[1].x, annotation.points[1].y);
              ctx.lineTo(
                annotation.points[1].x - arrowLength * Math.cos(angle + Math.PI / 6),
                annotation.points[1].y - arrowLength * Math.sin(angle + Math.PI / 6)
              );
              ctx.stroke();
            }
          }
          break;
          
        case AnnotationType.FREEHAND:
          if (annotation.points.length > 1) {
            ctx.beginPath();
            ctx.moveTo(annotation.points[0].x, annotation.points[0].y);
            annotation.points.forEach(point => {
              ctx.lineTo(point.x, point.y);
            });
            ctx.stroke();
          }
          break;
          
        case AnnotationType.TEXT:
          if (annotation.points.length > 0 && annotation.label) {
            ctx.fillStyle = annotation.style.strokeColor;
            ctx.font = `${annotation.style.fontSize}px Arial`;
            ctx.fillText(annotation.label, annotation.points[0].x, annotation.points[0].y);
          }
          break;
      }
    });
    
    // Draw current annotation being drawn
    if (isDrawing && currentAnnotation) {
      ctx.strokeStyle = style.strokeColor;
      ctx.lineWidth = style.strokeWidth;
      ctx.setLineDash([5, 5]);
      
      switch (currentAnnotation.type) {
        case AnnotationType.BOUNDING_BOX:
          if (currentAnnotation.points.length >= 2) {
            const x = Math.min(currentAnnotation.points[0].x, currentAnnotation.points[1].x);
            const y = Math.min(currentAnnotation.points[0].y, currentAnnotation.points[1].y);
            const width = Math.abs(currentAnnotation.points[1].x - currentAnnotation.points[0].x);
            const height = Math.abs(currentAnnotation.points[1].y - currentAnnotation.points[0].y);
            ctx.strokeRect(x, y, width, height);
          }
          break;
      }
      
      ctx.setLineDash([]);
    }
  };

  // Redraw when annotations change
  useEffect(() => {
    redrawCanvas();
  }, [annotations, currentAnnotation]);

  // Handle file upload
  const handleFileUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      setImageSrc(e.target?.result as string);
    };
    reader.readAsDataURL(file);
    return false;
  };

  // Mouse event handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (currentTool === AnnotationType.TEXT) {
      // For text, show input dialog
      const text = prompt('Enter text:');
      if (text) {
        const newAnnotation: Annotation = {
          id: `ann_${Date.now()}`,
          type: AnnotationType.TEXT,
          label: text,
          points: [{ x, y }],
          style: { ...style },
          visible: true
        };
        addAnnotation(newAnnotation);
      }
    } else {
      setIsDrawing(true);
      setCurrentAnnotation({
        id: `ann_${Date.now()}`,
        type: currentTool,
        points: [{ x, y }],
        style: { ...style },
        visible: true
      });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !currentAnnotation) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (currentTool === AnnotationType.FREEHAND) {
      setCurrentAnnotation({
        ...currentAnnotation,
        points: [...currentAnnotation.points, { x, y }]
      });
    } else {
      setCurrentAnnotation({
        ...currentAnnotation,
        points: [currentAnnotation.points[0], { x, y }]
      });
    }
  };

  const handleMouseUp = () => {
    if (isDrawing && currentAnnotation) {
      if (currentAnnotation.type === AnnotationType.BOUNDING_BOX ||
          currentAnnotation.type === AnnotationType.CIRCLE ||
          currentAnnotation.type === AnnotationType.LINE ||
          currentAnnotation.type === AnnotationType.ARROW) {
        // Add label for certain types
        const label = prompt('Enter label (optional):');
        currentAnnotation.label = label || undefined;
      }
      
      addAnnotation(currentAnnotation);
      setIsDrawing(false);
      setCurrentAnnotation(null);
    }
  };

  // Add annotation with undo support
  const addAnnotation = (annotation: Annotation) => {
    setUndoStack([...undoStack, annotations]);
    setRedoStack([]);
    setAnnotations([...annotations, annotation]);
    message.success('Annotation added');
  };

  // Undo/Redo
  const undo = () => {
    if (undoStack.length === 0) return;
    
    const previousState = undoStack[undoStack.length - 1];
    setUndoStack(undoStack.slice(0, -1));
    setRedoStack([...redoStack, annotations]);
    setAnnotations(previousState);
  };

  const redo = () => {
    if (redoStack.length === 0) return;
    
    const nextState = redoStack[redoStack.length - 1];
    setRedoStack(redoStack.slice(0, -1));
    setUndoStack([...undoStack, annotations]);
    setAnnotations(nextState);
  };

  // Delete annotation
  const deleteAnnotation = (id: string) => {
    setUndoStack([...undoStack, annotations]);
    setRedoStack([]);
    setAnnotations(annotations.filter(ann => ann.id !== id));
    message.success('Annotation deleted');
  };

  // Toggle visibility
  const toggleVisibility = (id: string) => {
    setAnnotations(annotations.map(ann => 
      ann.id === id ? { ...ann, visible: !ann.visible } : ann
    ));
  };

  // Export annotations
  const exportAnnotations = () => {
    const data = {
      image: {
        src: imageSrc,
        width: imageRef.current?.width || 0,
        height: imageRef.current?.height || 0
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

  // Save to file system (Electron specific)
  const saveToFile = async () => {
    if (window.electron) {
      const data = {
        image: {
          src: imageSrc,
          width: imageRef.current?.width || 0,
          height: imageRef.current?.height || 0
        },
        annotations
      };
      
      try {
        await window.electron.saveAnnotations(data);
        message.success('Annotations saved');
      } catch (error) {
        message.error('Failed to save annotations');
      }
    }
  };

  // Load from file system (Electron specific)
  const loadFromFile = async () => {
    if (window.electron) {
      try {
        const data = await window.electron.loadAnnotations();
        if (data) {
          setImageSrc(data.image.src);
          setAnnotations(data.annotations);
          message.success('Annotations loaded');
        }
      } catch (error) {
        message.error('Failed to load annotations');
      }
    }
  };

  return (
    <div className="image-annotation-desktop">
      <Card className="annotation-header">
        <Space>
          <Radio.Group value={currentTool} onChange={(e) => setCurrentTool(e.target.value)}>
            <Radio.Button value={AnnotationType.BOUNDING_BOX}>
              <BorderOutlined /> Box
            </Radio.Button>
            <Radio.Button value={AnnotationType.CIRCLE}>
              <RadiusOutlined /> Circle
            </Radio.Button>
            <Radio.Button value={AnnotationType.LINE}>
              <EditOutlined /> Line
            </Radio.Button>
            <Radio.Button value={AnnotationType.ARROW}>
              <ArrowRightOutlined /> Arrow
            </Radio.Button>
            <Radio.Button value={AnnotationType.TEXT}>
              <FontSizeOutlined /> Text
            </Radio.Button>
            <Radio.Button value={AnnotationType.FREEHAND}>
              <DrawOutlined /> Draw
            </Radio.Button>
          </Radio.Group>

          <Button icon={<UndoOutlined />} onClick={undo} disabled={undoStack.length === 0}>
            Undo
          </Button>
          <Button icon={<RedoOutlined />} onClick={redo} disabled={redoStack.length === 0}>
            Redo
          </Button>
          <Button icon={<SaveOutlined />} onClick={saveToFile}>
            Save
          </Button>
          <Button icon={<FolderOpenOutlined />} onClick={loadFromFile}>
            Load
          </Button>
          <Button icon={<DownloadOutlined />} onClick={exportAnnotations}>
            Export
          </Button>
        </Space>
      </Card>

      <div className="annotation-workspace">
        <div className="canvas-area">
          {imageSrc ? (
            <canvas
              ref={canvasRef}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              className="annotation-canvas"
            />
          ) : (
            <Dragger
              accept="image/*"
              beforeUpload={handleFileUpload}
              showUploadList={false}
              className="upload-area"
            >
              <p className="ant-upload-drag-icon">
                <CloudUploadOutlined />
              </p>
              <p className="ant-upload-text">Click or drag image to this area</p>
              <p className="ant-upload-hint">Support for PNG, JPG, JPEG, BMP formats</p>
            </Dragger>
          )}
        </div>

        <Card className="annotation-panel" title="Annotations">
          <div className="style-controls">
            <h4>Style Settings</h4>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <label>Stroke Color</label>
                <input
                  type="color"
                  value={style.strokeColor}
                  onChange={(e) => setStyle({ ...style, strokeColor: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label>Fill Color</label>
                <input
                  type="color"
                  value={style.fillColor || '#ffffff'}
                  onChange={(e) => setStyle({ ...style, fillColor: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label>Stroke Width</label>
                <Slider
                  min={1}
                  max={10}
                  value={style.strokeWidth}
                  onChange={(value) => setStyle({ ...style, strokeWidth: value })}
                />
              </div>
            </Space>
          </div>

          <div className="annotation-list">
            <h4>Annotation List</h4>
            <List
              dataSource={annotations}
              renderItem={(annotation) => (
                <List.Item
                  actions={[
                    <Tooltip title={annotation.visible ? "Hide" : "Show"}>
                      <Button
                        icon={annotation.visible ? <EyeOutlined /> : <EyeInvisibleOutlined />}
                        size="small"
                        onClick={() => toggleVisibility(annotation.id)}
                      />
                    </Tooltip>,
                    <Tooltip title="Delete">
                      <Button
                        icon={<DeleteOutlined />}
                        size="small"
                        danger
                        onClick={() => deleteAnnotation(annotation.id)}
                      />
                    </Tooltip>
                  ]}
                >
                  <span>
                    {annotation.type} - {annotation.label || annotation.id}
                  </span>
                </List.Item>
              )}
            />
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ImageAnnotation;