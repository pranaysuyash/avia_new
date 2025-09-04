#!/usr/bin/env python3
"""
Image Annotation UI
Streamlit interface for interactive image annotation and markup
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import json
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import os
from streamlit_intent_utils import render_share_inline, render_share_block, log_ux_event, get_params, update_params

from image_annotation_system import (
    AnnotationManager, AnnotationRenderer, AnnotationType, DrawingMode,
    Point, Color, AnnotationStyle, Annotation, BoundingBoxAnnotation,
    CircleAnnotation, TextAnnotation, PolygonAnnotation, LineAnnotation,
    ArrowAnnotation, FreehandAnnotation, BlurAnnotation, HighlightAnnotation
)

# Page configuration
st.set_page_config(
    page_title="Image Annotation Tool",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #ff6b6b 0%, #4ecdc4 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .annotation-toolbar {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
    }
    
    .annotation-list {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #e9ecef;
    }
    
    .annotation-item {
        background: #f8f9fa;
        padding: 0.75rem;
        border-radius: 5px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #007bff;
    }
    
    .tool-button {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        border-radius: 5px;
        background: #007bff;
        color: white;
        text-decoration: none;
        transition: all 0.3s;
    }
    
    .tool-button:hover {
        background: #0056b3;
        transform: translateY(-2px);
    }
    
    .color-picker {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        border: 2px solid #ddd;
        cursor: pointer;
    }
    
    .export-button {
        background: #28a745;
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 5px;
        border: none;
        cursor: pointer;
    }
    
    .canvas-container {
        border: 2px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
        background: #f8f9fa;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'annotation_manager' not in st.session_state:
    st.session_state.annotation_manager = AnnotationManager()
if 'current_tool' not in st.session_state:
    st.session_state.current_tool = AnnotationType.BOUNDING_BOX
if 'drawing_mode' not in st.session_state:
    st.session_state.drawing_mode = DrawingMode.DRAW
if 'current_image_id' not in st.session_state:
    st.session_state.current_image_id = None
if 'annotation_style' not in st.session_state:
    st.session_state.annotation_style = AnnotationStyle()
if 'drawing_state' not in st.session_state:
    st.session_state.drawing_state = {}

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎨 Image Annotation Tool</h1>
        <p>Interactive image annotation with bounding boxes, text overlays, and markup tools</p>
    </div>
    """, unsafe_allow_html=True)
    # Inline share input
    try:
        render_share_inline("Shareable view link")
    except Exception:
        pass
    
    # Sidebar
    with st.sidebar:
        # Share + reset controls
        try:
            render_share_block("Share Image Annotation View")
        except Exception:
            pass
        if st.button("Reset View/Filters"):
            try:
                st.experimental_set_query_params()
            except Exception:
                pass
            try:
                log_ux_event("st_filters_cleared", {"scope": "image_annotation"})
            except Exception:
                pass
            st.rerun()
        render_sidebar()
    
    # Main content
    col1, col2 = st.columns([3, 1])
    
    with col1:
        render_canvas_area()
    
    with col2:
        render_annotation_panel()

def render_sidebar():
    """Render the sidebar with tools and settings"""
    st.header("🛠️ Annotation Tools")
    
    # Drawing mode
    st.subheader("Mode")
    params = get_params()
    mode_default = params.get('ia_mode', DrawingMode.DRAW.value)
    mode = st.radio(
        "Select mode:",
        [DrawingMode.DRAW.value, DrawingMode.SELECT.value, DrawingMode.EDIT.value, DrawingMode.DELETE.value],
        format_func=lambda x: x.title(),
        index=[DrawingMode.DRAW.value, DrawingMode.SELECT.value, DrawingMode.EDIT.value, DrawingMode.DELETE.value].index(mode_default) if mode_default in [d.value for d in DrawingMode] else 0
    )
    st.session_state.drawing_mode = DrawingMode(mode)
    try:
        update_params({'ia_mode': mode})
    except Exception:
        pass
    
    # Tool selection
    st.subheader("Tools")
    
    tool_cols = st.columns(3)
    tools = [
        (AnnotationType.BOUNDING_BOX, "📦", "Box"),
        (AnnotationType.CIRCLE, "⭕", "Circle"),
        (AnnotationType.POLYGON, "🔷", "Polygon"),
        (AnnotationType.LINE, "📏", "Line"),
        (AnnotationType.ARROW, "➡️", "Arrow"),
        (AnnotationType.TEXT, "📝", "Text"),
        (AnnotationType.FREEHAND, "✏️", "Draw"),
        (AnnotationType.BLUR, "🌫️", "Blur"),
        (AnnotationType.HIGHLIGHT, "🔆", "Highlight")
    ]
    
    # Initialize tool from deep link
    tool_default = params.get('ia_tool')
    if tool_default:
        try:
            st.session_state.current_tool = getattr(AnnotationType, tool_default)
        except Exception:
            pass
    for i, (tool_type, icon, name) in enumerate(tools):
        col = tool_cols[i % 3]
        with col:
            if st.button(f"{icon} {name}", key=f"tool_{tool_type.value}"):
                st.session_state.current_tool = tool_type
                try:
                    update_params({'ia_tool': tool_type.name})
                except Exception:
                    pass
    
    # Style settings
    st.subheader("Style Settings")
    
    # Stroke color
    col1, col2 = st.columns(2)
    with col1:
        st.write("Stroke Color")
        stroke_color = st.color_picker(
            "Stroke",
            value=st.session_state.annotation_style.stroke_color.to_hex(),
            key="stroke_color"
        )
    
    with col2:
        st.write("Fill Color")
        use_fill = st.checkbox("Use fill", key="use_fill")
        if use_fill:
            fill_color = st.color_picker(
                "Fill",
                value="#ffff00",
                key="fill_color"
            )
    
    # Update style
    r, g, b = int(stroke_color[1:3], 16), int(stroke_color[3:5], 16), int(stroke_color[5:7], 16)
    st.session_state.annotation_style.stroke_color = Color(r, g, b)
    
    if use_fill:
        r, g, b = int(fill_color[1:3], 16), int(fill_color[3:5], 16), int(fill_color[5:7], 16)
        st.session_state.annotation_style.fill_color = Color(r, g, b, 128)
    else:
        st.session_state.annotation_style.fill_color = None
    
    # Stroke width
    st.session_state.annotation_style.stroke_width = st.slider(
        "Stroke Width",
        min_value=1,
        max_value=10,
        value=2
    )
    
    # Font size for text
    if st.session_state.current_tool == AnnotationType.TEXT:
        st.session_state.annotation_style.font_size = st.slider(
            "Font Size",
            min_value=10,
            max_value=50,
            value=16
        )
    
    # Blur strength
    if st.session_state.current_tool == AnnotationType.BLUR:
        blur_strength = st.slider(
            "Blur Strength",
            min_value=5,
            max_value=51,
            value=25,
            step=2
        )
        st.session_state.blur_strength = blur_strength
    
    # Export/Import
    st.subheader("📤 Export/Import")
    
    export_format = st.selectbox(
        "Export format:",
        ["JSON", "COCO", "YOLO"]
    )
    
    if st.button("Export Annotations", type="primary"):
        export_annotations(export_format.lower())
    
    # Import
    uploaded_annotations = st.file_uploader(
        "Import annotations",
        type=['json', 'txt'],
        help="Import annotations from file"
    )
    
    if uploaded_annotations:
        import_annotations(uploaded_annotations, export_format.lower())

def render_canvas_area():
    """Render the main canvas area for annotation"""
    st.subheader("🖼️ Canvas")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an image",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        help="Upload an image to annotate"
    )
    
    if uploaded_file:
        # Load image
        image_bytes = uploaded_file.getvalue()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to OpenCV format
        image_array = np.array(image)
        if len(image_array.shape) == 2:  # Grayscale
            image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2BGR)
        elif image_array.shape[2] == 4:  # RGBA
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGR)
        else:  # RGB
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        # Save temporarily
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            cv2.imwrite(tmp.name, image_array)
            temp_path = tmp.name
        
        # Create or get annotated image
        if st.session_state.current_image_id is None or \
           st.session_state.current_image_id not in st.session_state.annotation_manager.annotated_images:
            annotated_image = st.session_state.annotation_manager.create_annotated_image(temp_path)
            st.session_state.current_image_id = annotated_image.image_id
        
        # Render toolbar
        render_toolbar()
        
        # Display image with annotations
        if st.session_state.current_image_id:
            rendered_image = st.session_state.annotation_manager.render_image(
                st.session_state.current_image_id
            )
            
            if rendered_image is not None:
                # Convert back to RGB for display
                display_image = cv2.cvtColor(rendered_image, cv2.COLOR_BGR2RGB)
                
                # Create interactive canvas
                st.markdown('<div class="canvas-container">', unsafe_allow_html=True)
                
                # Display image
                image_placeholder = st.empty()
                image_placeholder.image(display_image, use_column_width=True)
                
                # Add drawing interaction (simplified for demo)
                if st.session_state.drawing_mode == DrawingMode.DRAW:
                    render_drawing_controls()
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Clean up
        try:
            os.unlink(temp_path)
        except:
            pass
    else:
        st.info("👆 Upload an image to start annotating")

def render_toolbar():
    """Render annotation toolbar"""
    st.markdown('<div class="annotation-toolbar">', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("↩️ Undo"):
            if st.session_state.current_image_id:
                st.session_state.annotation_manager.undo(st.session_state.current_image_id)
                st.rerun()
    
    with col2:
        if st.button("↪️ Redo"):
            if st.session_state.current_image_id:
                st.session_state.annotation_manager.redo(st.session_state.current_image_id)
                st.rerun()
    
    with col3:
        if st.button("🗑️ Clear All"):
            if st.session_state.current_image_id:
                clear_all_annotations()
    
    with col4:
        if st.button("👁️ Toggle All"):
            toggle_all_visibility()
    
    with col5:
        st.write(f"Tool: {st.session_state.current_tool.value}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_drawing_controls():
    """Render drawing controls based on current tool"""
    tool = st.session_state.current_tool
    
    if tool == AnnotationType.BOUNDING_BOX:
        st.write("📦 Click and drag to draw a bounding box")
        
        # Simplified drawing interface
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            x1 = st.number_input("X1", value=50, step=10)
        with col2:
            y1 = st.number_input("Y1", value=50, step=10)
        with col3:
            x2 = st.number_input("X2", value=150, step=10)
        with col4:
            y2 = st.number_input("Y2", value=150, step=10)
        
        label = st.text_input("Label", value="Object")
        
        if st.button("Add Bounding Box", type="primary"):
            add_bounding_box(x1, y1, x2, y2, label)
    
    elif tool == AnnotationType.TEXT:
        st.write("📝 Click to place text")
        
        col1, col2 = st.columns(2)
        with col1:
            x = st.number_input("X", value=100, step=10)
            y = st.number_input("Y", value=100, step=10)
        with col2:
            text = st.text_input("Text", value="Annotation")
        
        if st.button("Add Text", type="primary"):
            add_text_annotation(x, y, text)
    
    elif tool == AnnotationType.CIRCLE:
        st.write("⭕ Click and drag to draw a circle")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            cx = st.number_input("Center X", value=100, step=10)
        with col2:
            cy = st.number_input("Center Y", value=100, step=10)
        with col3:
            radius = st.number_input("Radius", value=50, min_value=1, step=10)
        
        label = st.text_input("Label", value="")
        
        if st.button("Add Circle", type="primary"):
            add_circle_annotation(cx, cy, radius, label)

def render_annotation_panel():
    """Render the annotation list panel"""
    st.subheader("📋 Annotations")
    
    if st.session_state.current_image_id:
        annotated_image = st.session_state.annotation_manager.annotated_images.get(
            st.session_state.current_image_id
        )
        
        if annotated_image and annotated_image.annotations:
            st.markdown('<div class="annotation-list">', unsafe_allow_html=True)
            
            for i, annotation in enumerate(annotated_image.annotations):
                render_annotation_item(annotation, i)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Statistics
            st.subheader("📊 Statistics")
            stats = get_annotation_statistics(annotated_image.annotations)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Annotations", stats['total'])
                st.metric("Bounding Boxes", stats.get('bounding_box', 0))
            with col2:
                st.metric("Text Annotations", stats.get('text', 0))
                st.metric("Other", stats.get('other', 0))
        else:
            st.info("No annotations yet. Start drawing!")
    else:
        st.info("Upload an image to see annotations")

def render_annotation_item(annotation: Annotation, index: int):
    """Render a single annotation item"""
    icon_map = {
        AnnotationType.BOUNDING_BOX: "📦",
        AnnotationType.CIRCLE: "⭕",
        AnnotationType.TEXT: "📝",
        AnnotationType.POLYGON: "🔷",
        AnnotationType.LINE: "📏",
        AnnotationType.ARROW: "➡️",
        AnnotationType.FREEHAND: "✏️",
        AnnotationType.BLUR: "🌫️",
        AnnotationType.HIGHLIGHT: "🔆"
    }
    
    icon = icon_map.get(annotation.annotation_type, "🔹")
    
    with st.container():
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
        
        with col1:
            st.write(icon)
        
        with col2:
            label = annotation.label or f"{annotation.annotation_type.value} {index + 1}"
            st.write(f"**{label}**")
            
            # Edit label
            if st.session_state.drawing_mode == DrawingMode.EDIT:
                new_label = st.text_input(
                    "Label",
                    value=annotation.label,
                    key=f"label_{annotation.annotation_id}"
                )
                if new_label != annotation.label:
                    update_annotation_label(annotation.annotation_id, new_label)
        
        with col3:
            # Visibility toggle
            if st.checkbox("👁️", value=annotation.visible, key=f"vis_{annotation.annotation_id}"):
                update_annotation_visibility(annotation.annotation_id, True)
            else:
                update_annotation_visibility(annotation.annotation_id, False)
        
        with col4:
            # Delete button
            if st.button("🗑️", key=f"del_{annotation.annotation_id}"):
                delete_annotation(annotation.annotation_id)

# Helper functions
def add_bounding_box(x1: float, y1: float, x2: float, y2: float, label: str):
    """Add a bounding box annotation"""
    if st.session_state.current_image_id:
        bbox = BoundingBoxAnnotation(
            label=label,
            top_left=Point(min(x1, x2), min(y1, y2)),
            bottom_right=Point(max(x1, x2), max(y1, y2)),
            style=st.session_state.annotation_style
        )
        
        st.session_state.annotation_manager.add_annotation(
            st.session_state.current_image_id,
            bbox
        )
        st.success("Added bounding box!")
        st.rerun()

def add_text_annotation(x: float, y: float, text: str):
    """Add a text annotation"""
    if st.session_state.current_image_id:
        text_ann = TextAnnotation(
            position=Point(x, y),
            text=text,
            style=st.session_state.annotation_style
        )
        
        st.session_state.annotation_manager.add_annotation(
            st.session_state.current_image_id,
            text_ann
        )
        st.success("Added text!")
        st.rerun()

def add_circle_annotation(cx: float, cy: float, radius: float, label: str):
    """Add a circle annotation"""
    if st.session_state.current_image_id:
        circle = CircleAnnotation(
            label=label,
            center=Point(cx, cy),
            radius=radius,
            style=st.session_state.annotation_style
        )
        
        st.session_state.annotation_manager.add_annotation(
            st.session_state.current_image_id,
            circle
        )
        st.success("Added circle!")
        st.rerun()

def update_annotation_label(annotation_id: str, new_label: str):
    """Update annotation label"""
    if st.session_state.current_image_id:
        st.session_state.annotation_manager.update_annotation(
            st.session_state.current_image_id,
            annotation_id,
            {'label': new_label}
        )

def update_annotation_visibility(annotation_id: str, visible: bool):
    """Update annotation visibility"""
    if st.session_state.current_image_id:
        st.session_state.annotation_manager.update_annotation(
            st.session_state.current_image_id,
            annotation_id,
            {'visible': visible}
        )
        st.rerun()

def delete_annotation(annotation_id: str):
    """Delete an annotation"""
    if st.session_state.current_image_id:
        st.session_state.annotation_manager.remove_annotation(
            st.session_state.current_image_id,
            annotation_id
        )
        st.success("Deleted annotation!")
        st.rerun()

def clear_all_annotations():
    """Clear all annotations"""
    if st.session_state.current_image_id:
        annotated_image = st.session_state.annotation_manager.annotated_images.get(
            st.session_state.current_image_id
        )
        if annotated_image:
            # Save state for undo
            st.session_state.annotation_manager._save_state(st.session_state.current_image_id)
            
            # Clear annotations
            annotated_image.annotations = []
            annotated_image.updated_at = datetime.now()
            
            st.success("Cleared all annotations!")
            st.rerun()

def toggle_all_visibility():
    """Toggle visibility of all annotations"""
    if st.session_state.current_image_id:
        annotated_image = st.session_state.annotation_manager.annotated_images.get(
            st.session_state.current_image_id
        )
        if annotated_image:
            # Check if any are visible
            any_visible = any(a.visible for a in annotated_image.annotations)
            
            # Toggle all
            for annotation in annotated_image.annotations:
                annotation.visible = not any_visible
            
            st.rerun()

def export_annotations(format: str):
    """Export annotations"""
    if st.session_state.current_image_id:
        exported = st.session_state.annotation_manager.export_annotations(
            st.session_state.current_image_id,
            format
        )
        
        if exported:
            # Create download link
            b64 = base64.b64encode(exported.encode()).decode()
            filename = f"annotations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">Download {format.upper()} file</a>'
            st.markdown(href, unsafe_allow_html=True)

def import_annotations(file, format: str):
    """Import annotations from file"""
    if st.session_state.current_image_id and file:
        content = file.read().decode('utf-8')
        
        success = st.session_state.annotation_manager.import_annotations(
            st.session_state.current_image_id,
            content,
            format
        )
        
        if success:
            st.success("Imported annotations successfully!")
            st.rerun()
        else:
            st.error("Failed to import annotations")

def get_annotation_statistics(annotations: List[Annotation]) -> Dict[str, int]:
    """Get statistics about annotations"""
    stats = {'total': len(annotations)}
    
    for annotation in annotations:
        ann_type = annotation.annotation_type.value
        stats[ann_type] = stats.get(ann_type, 0) + 1
    
    # Group some types
    other_types = ['polygon', 'line', 'arrow', 'freehand', 'blur', 'highlight']
    stats['other'] = sum(stats.get(t, 0) for t in other_types)
    
    return stats

if __name__ == "__main__":
    main()
