"""
Image Entity Extraction UI Component
Streamlit interface for image-based entity extraction and analysis
"""

import streamlit as st
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from typing import Dict, List, Any
import base64
import io

from image_entity_extraction_system import (
    ImageEntityExtractionSystem, ImageAnalysisResult, VisualEntity,
    EntityType, ImageQuality, BoundingBox
)

class ImageEntityExtractionUI:
    """Streamlit UI for image entity extraction"""
    
    def __init__(self):
        self.system = ImageEntityExtractionSystem()
        self.setup_page_config()
    
    def setup_page_config(self):
        """Configure Streamlit page"""
        st.set_page_config(
            page_title="Image Entity Extraction",
            page_icon="🖼️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render_main_interface(self):
        """Render the main interface"""
        st.title("🖼️ Image Entity Extraction & Analysis")
        st.markdown("Advanced image analysis with entity detection, OCR, and visual content understanding")
        
        # Sidebar controls
        self.render_sidebar()
        
        # Main content area
        col1, col2 = st.columns([1, 1])
        
        with col1:
            self.render_image_upload()
        
        with col2:
            if 'analysis_result' in st.session_state:
                self.render_analysis_results()
    
    def render_sidebar(self):
        """Render sidebar controls"""
        st.sidebar.header("⚙️ Analysis Settings")
        
        # Analysis options
        st.sidebar.subheader("Detection Options")
        
        enable_ocr = st.sidebar.checkbox("Enable OCR Text Extraction", value=True)
        enable_object_detection = st.sidebar.checkbox("Enable Object Detection", value=True)
        enable_face_detection = st.sidebar.checkbox("Enable Face Detection", value=True)
        enable_logo_detection = st.sidebar.checkbox("Enable Logo/Signature Detection", value=True)
        enable_code_detection = st.sidebar.checkbox("Enable QR/Barcode Detection", value=True)
        
        # Confidence thresholds
        st.sidebar.subheader("Confidence Thresholds")
        
        min_confidence = st.sidebar.slider(
            "Minimum Detection Confidence",
            min_value=0.1,
            max_value=1.0,
            value=0.5,
            step=0.1
        )
        
        # Store settings in session state
        st.session_state.analysis_settings = {
            'enable_ocr': enable_ocr,
            'enable_object_detection': enable_object_detection,
            'enable_face_detection': enable_face_detection,
            'enable_logo_detection': enable_logo_detection,
            'enable_code_detection': enable_code_detection,
            'min_confidence': min_confidence
        }
        
        # Model information
        st.sidebar.subheader("📊 Model Information")
        st.sidebar.info("""
        **AI Models Used:**
        - CLIP: Image-text understanding
        - BLIP: Image captioning
        - DETR: Object detection
        - ViT: Image classification
        - YOLO: Real-time object detection
        - spaCy: Named entity recognition
        """)
    
    def render_image_upload(self):
        """Render image upload interface"""
        st.header("📤 Upload Image")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'],
            help="Upload an image for entity extraction and analysis"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # Convert to numpy array
            image_array = np.array(image)
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Analysis button
            if st.button("🔍 Analyze Image", type="primary"):
                with st.spinner("Analyzing image... This may take a moment."):
                    try:
                        # Run analysis
                        result = self.system.analyze_image(image_data=image_array)
                        st.session_state.analysis_result = result
                        st.session_state.original_image = image_array
                        st.success("✅ Analysis completed successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")
        
        # Sample images for testing
        st.subheader("📋 Try Sample Images")
        
        sample_options = [
            "None",
            "Business Card",
            "Document with Text",
            "Product Image",
            "Chart/Graph",
            "Mixed Content"
        ]
        
        selected_sample = st.selectbox("Select a sample image:", sample_options)
        
        if selected_sample != "None":
            if st.button(f"Load {selected_sample}"):
                sample_image = self.create_sample_image(selected_sample)
                st.session_state.analysis_result = self.system.analyze_image(image_data=sample_image)
                st.session_state.original_image = sample_image
                st.success(f"✅ Loaded and analyzed {selected_sample}")
                st.rerun()
    
    def render_analysis_results(self):
        """Render analysis results"""
        if 'analysis_result' not in st.session_state:
            st.info("👆 Upload an image to see analysis results")
            return
        
        result: ImageAnalysisResult = st.session_state.analysis_result
        
        st.header("📊 Analysis Results")
        
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Overall Confidence",
                f"{result.confidence:.1%}",
                delta=None
            )
        
        with col2:
            st.metric(
                "Entities Found",
                len(result.visual_entities),
                delta=None
            )
        
        with col3:
            st.metric(
                "Image Quality",
                result.quality_assessment.overall_quality.value.title(),
                delta=None
            )
        
        with col4:
            st.metric(
                "Faces Detected",
                result.visual_content.faces_detected,
                delta=None
            )
        
        # Tabs for different result views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎯 Entities", "🖼️ Visual Content", "📋 Metadata", 
            "⭐ Quality", "📄 Raw Data"
        ])
        
        with tab1:
            self.render_entities_tab(result)
        
        with tab2:
            self.render_visual_content_tab(result)
        
        with tab3:
            self.render_metadata_tab(result)
        
        with tab4:
            self.render_quality_tab(result)
        
        with tab5:
            self.render_raw_data_tab(result)
    
    def render_entities_tab(self, result: ImageAnalysisResult):
        """Render entities analysis tab"""
        st.subheader("🎯 Detected Entities")
        
        if not result.visual_entities:
            st.info("No entities detected in the image")
            return
        
        # Filter entities by confidence
        min_conf = st.session_state.analysis_settings.get('min_confidence', 0.5)
        filtered_entities = [e for e in result.visual_entities if e.confidence >= min_conf]
        
        if not filtered_entities:
            st.warning(f"No entities found above confidence threshold of {min_conf}")
            return
        
        # Entity summary
        entity_types = {}
        for entity in filtered_entities:
            entity_type = entity.entity_type.value
            if entity_type not in entity_types:
                entity_types[entity_type] = 0
            entity_types[entity_type] += 1
        
        # Display entity type distribution
        if entity_types:
            fig = px.pie(
                values=list(entity_types.values()),
                names=list(entity_types.keys()),
                title="Entity Type Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Entity details table
        st.subheader("📋 Entity Details")
        
        entity_data = []
        for i, entity in enumerate(filtered_entities):
            entity_data.append({
                'ID': i + 1,
                'Type': entity.entity_type.value.title(),
                'Text': entity.text[:50] + "..." if len(entity.text) > 50 else entity.text,
                'Confidence': f"{entity.confidence:.1%}",
                'Source': entity.metadata.get('source', 'unknown'),
                'Bounding Box': f"({entity.bbox.x1}, {entity.bbox.y1}) - ({entity.bbox.x2}, {entity.bbox.y2})"
            })
        
        df = pd.DataFrame(entity_data)
        st.dataframe(df, use_container_width=True)
        
        # Visualize entities on image
        if 'original_image' in st.session_state:
            st.subheader("🖼️ Entity Visualization")
            annotated_image = self.draw_entity_boxes(
                st.session_state.original_image.copy(),
                filtered_entities
            )
            st.image(
                cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB),
                caption="Detected Entities",
                use_column_width=True
            )
    
    def render_visual_content_tab(self, result: ImageAnalysisResult):
        """Render visual content analysis tab"""
        st.subheader("🖼️ Visual Content Analysis")
        
        content = result.visual_content
        
        # Content description
        st.subheader("📝 Image Description")
        st.write(content.description)
        
        # Content classification
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏷️ Content Type")
            st.info(content.content_type.title())
        
        with col2:
            st.subheader("🎭 Scene Classification")
            st.info(content.scene_classification.title())
        
        # Dominant colors
        if content.dominant_colors:
            st.subheader("🎨 Dominant Colors")
            color_cols = st.columns(min(len(content.dominant_colors), 5))
            
            for i, color in enumerate(content.dominant_colors[:5]):
                with color_cols[i]:
                    # Create color swatch
                    color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                    st.markdown(
                        f'<div style="background-color: {color_hex}; '
                        f'height: 50px; border-radius: 5px; margin: 5px;"></div>',
                        unsafe_allow_html=True
                    )
                    st.caption(f"RGB: {color}")
        
        # Objects detected
        if content.objects_detected:
            st.subheader("🎯 Objects Detected")
            
            object_data = []
            for obj in content.objects_detected:
                object_data.append({
                    'Object': obj['name'].title(),
                    'Confidence': f"{obj['confidence']:.1%}",
                    'Source': obj.get('source', 'unknown'),
                    'Bounding Box': str(obj.get('bbox', 'N/A'))
                })
            
            df = pd.DataFrame(object_data)
            st.dataframe(df, use_container_width=True)
        
        # Text regions
        if content.text_regions:
            st.subheader("📝 Text Regions")
            st.info(f"Found {len(content.text_regions)} potential text regions")
        
        # Landmarks
        if content.landmarks:
            st.subheader("🗺️ Detected Landmarks")
            st.info(f"Found {len(content.landmarks)} landmark points")
        
        # Face Recognition Results
        if hasattr(content, 'face_identities') and content.face_identities:
            st.subheader("👤 Face Recognition Results")
            
            for i, face in enumerate(content.face_identities):
                with st.expander(f"Face {i+1} - Confidence: {face['confidence']:.1%}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Basic Information:**")
                        st.write(f"Face ID: {face['face_id']}")
                        st.write(f"Estimated Age: {face['features']['estimated_age'].title()}")
                        st.write(f"Estimated Gender: {face['features']['estimated_gender'].title()}")
                    
                    with col2:
                        st.write("**Quality Metrics:**")
                        quality = face['features']['face_quality']
                        st.write(f"Overall Quality: {quality['overall_quality']:.2f}")
                        st.write(f"Sharpness: {quality['sharpness']:.1f}")
                        st.write(f"Brightness: {quality['brightness']:.1f}")
        
        # Scene Analysis
        if hasattr(content, 'scene_analysis') and content.scene_analysis:
            st.subheader("🎬 Scene Understanding")
            scene = content.scene_analysis
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Scene Type:** {scene.get('scene_type', 'Unknown').title()}")
                st.write(f"**Setting:** {scene.get('indoor_outdoor', 'Unknown').title()}")
                st.write(f"**Confidence:** {scene.get('context_confidence', 0):.1%}")
            
            with col2:
                if scene.get('activity_detected'):
                    st.write("**Activities Detected:**")
                    for activity in scene['activity_detected'][:3]:
                        st.write(f"• {activity['activity'].title()} ({activity['confidence']:.1%})")
        
        # Logo and Brand Detection
        if hasattr(content, 'logos_brands') and content.logos_brands:
            st.subheader("🏷️ Logos & Brands Detected")
            
            for logo in content.logos_brands:
                risk_color = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(logo.get('compliance_risk', 'low'), '⚪')
                st.write(f"{risk_color} **{logo['brand_name'].title()}** - {logo['type'].replace('_', ' ').title()}")
                st.write(f"   Confidence: {logo['confidence']:.1%} | Risk: {logo.get('compliance_risk', 'unknown').title()}")
        
        # Content Safety Assessment
        if hasattr(content, 'safety_assessment') and content.safety_assessment:
            st.subheader("🛡️ Content Safety Assessment")
            safety = content.safety_assessment
            
            # Overall safety status
            safety_icon = "✅" if safety['safe'] else "⚠️"
            safety_status = "Safe" if safety['safe'] else "Flagged"
            st.markdown(f"**{safety_icon} Status: {safety_status}** (Confidence: {safety['confidence']:.1%})")
            
            # Safety flags
            if safety['flags']:
                st.write("**Safety Flags:**")
                for flag in safety['flags']:
                    severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(flag['severity'], '⚪')
                    st.write(f"{severity_icon} {flag['category'].replace('_', ' ').title()}: {flag['content']}")
            
            # Recommendations
            if safety.get('recommendations'):
                st.write("**Recommendations:**")
                for rec in safety['recommendations']:
                    st.write(f"• {rec}")
    
    def render_metadata_tab(self, result: ImageAnalysisResult):
        """Render metadata tab"""
        st.subheader("📋 Image Metadata")
        
        metadata = result.metadata
        
        # Basic information
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Basic Information")
            st.write(f"**Filename:** {metadata.filename}")
            st.write(f"**File Size:** {metadata.file_size:,} bytes")
            st.write(f"**Dimensions:** {metadata.dimensions[0]} × {metadata.dimensions[1]}")
            st.write(f"**Format:** {metadata.format}")
            st.write(f"**Color Mode:** {metadata.mode}")
        
        with col2:
            st.subheader("📷 Camera Information")
            st.write(f"**Make:** {metadata.camera_make or 'Unknown'}")
            st.write(f"**Model:** {metadata.camera_model or 'Unknown'}")
            st.write(f"**Software:** {metadata.software or 'Unknown'}")
            st.write(f"**Creation Date:** {metadata.creation_date or 'Unknown'}")
        
        # GPS information
        if metadata.gps_coordinates:
            st.subheader("🗺️ GPS Location")
            lat, lon = metadata.gps_coordinates
            st.write(f"**Latitude:** {lat:.6f}")
            st.write(f"**Longitude:** {lon:.6f}")
            
            # Show on map
            map_data = pd.DataFrame({
                'lat': [lat],
                'lon': [lon]
            })
            st.map(map_data)
        
        # Additional metadata
        if any([metadata.artist, metadata.copyright, metadata.description]):
            st.subheader("ℹ️ Additional Information")
            if metadata.artist:
                st.write(f"**Artist:** {metadata.artist}")
            if metadata.copyright:
                st.write(f"**Copyright:** {metadata.copyright}")
            if metadata.description:
                st.write(f"**Description:** {metadata.description}")
    
    def render_quality_tab(self, result: ImageAnalysisResult):
        """Render quality assessment tab"""
        st.subheader("⭐ Image Quality Assessment")
        
        quality = result.quality_assessment
        
        # Overall quality
        quality_color = {
            'excellent': 'green',
            'good': 'blue',
            'fair': 'orange',
            'poor': 'red',
            'very_poor': 'darkred'
        }.get(quality.overall_quality.value, 'gray')
        
        st.markdown(
            f'<h3 style="color: {quality_color};">Overall Quality: '
            f'{quality.overall_quality.value.title()}</h3>',
            unsafe_allow_html=True
        )
        
        # Quality metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Quality Metrics")
            
            metrics = [
                ("Sharpness", quality.sharpness_score, 1000),
                ("Brightness", quality.brightness_score, 255),
                ("Contrast", quality.contrast_score, 100),
                ("Noise Level", quality.noise_level, 1000),
                ("Blur Detection", quality.blur_detection, 100)
            ]
            
            for name, value, max_val in metrics:
                normalized_value = min(value / max_val, 1.0) if max_val > 0 else 0
                st.metric(
                    name,
                    f"{value:.1f}",
                    delta=f"{normalized_value:.1%} of max"
                )
        
        with col2:
            st.subheader("🎨 Color Analysis")
            
            if quality.color_balance:
                for channel, value in quality.color_balance.items():
                    st.metric(
                        channel.replace('_', ' ').title(),
                        f"{value:.1f}"
                    )
        
        # Recommendations
        if quality.recommendations:
            st.subheader("💡 Improvement Recommendations")
            for i, recommendation in enumerate(quality.recommendations, 1):
                st.write(f"{i}. {recommendation}")
        
        # Quality visualization
        if quality.histogram_analysis:
            st.subheader("📈 Histogram Analysis")
            
            # Create histogram plot
            fig = go.Figure()
            
            if 'red_histogram' in quality.histogram_analysis:
                # Color histograms
                x_values = list(range(256))
                
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=quality.histogram_analysis['red_histogram'],
                    mode='lines',
                    name='Red',
                    line=dict(color='red')
                ))
                
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=quality.histogram_analysis['green_histogram'],
                    mode='lines',
                    name='Green',
                    line=dict(color='green')
                ))
                
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=quality.histogram_analysis['blue_histogram'],
                    mode='lines',
                    name='Blue',
                    line=dict(color='blue')
                ))
            
            elif 'grayscale_histogram' in quality.histogram_analysis:
                # Grayscale histogram
                x_values = list(range(256))
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=quality.histogram_analysis['grayscale_histogram'],
                    mode='lines',
                    name='Grayscale',
                    line=dict(color='gray')
                ))
            
            fig.update_layout(
                title="Color Distribution",
                xaxis_title="Pixel Value",
                yaxis_title="Frequency",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def render_raw_data_tab(self, result: ImageAnalysisResult):
        """Render raw data tab"""
        st.subheader("📄 Raw Analysis Data")
        
        # Convert result to dictionary for display
        result_dict = {
            'confidence': result.confidence,
            'extracted_text': result.extracted_text,
            'visual_entities': [
                {
                    'type': entity.entity_type.value,
                    'text': entity.text,
                    'confidence': entity.confidence,
                    'bbox': {
                        'x1': entity.bbox.x1,
                        'y1': entity.bbox.y1,
                        'x2': entity.bbox.x2,
                        'y2': entity.bbox.y2
                    },
                    'metadata': entity.metadata
                }
                for entity in result.visual_entities
            ],
            'visual_content': {
                'content_type': result.visual_content.content_type,
                'description': result.visual_content.description,
                'scene_classification': result.visual_content.scene_classification,
                'dominant_colors': result.visual_content.dominant_colors,
                'faces_detected': result.visual_content.faces_detected,
                'objects_detected': result.visual_content.objects_detected,
                'landmarks': result.visual_content.landmarks
            }
        }
        
        # Display as JSON
        st.json(result_dict)
        
        # Download button
        json_str = json.dumps(result_dict, indent=2, default=str)
        st.download_button(
            label="📥 Download Analysis Results",
            data=json_str,
            file_name="image_analysis_results.json",
            mime="application/json"
        )
    
    def draw_entity_boxes(self, image: np.ndarray, entities: List[VisualEntity]) -> np.ndarray:
        """Draw bounding boxes for entities on image"""
        annotated_image = image.copy()
        
        # Color map for different entity types
        color_map = {
            EntityType.PERSON: (0, 255, 0),      # Green
            EntityType.ORGANIZATION: (255, 0, 0), # Red
            EntityType.LOCATION: (0, 0, 255),     # Blue
            EntityType.PRODUCT: (255, 255, 0),    # Yellow
            EntityType.LOGO: (255, 0, 255),       # Magenta
            EntityType.SIGNATURE: (0, 255, 255),  # Cyan
            EntityType.QR_CODE: (128, 0, 128),    # Purple
            EntityType.BARCODE: (255, 128, 0),    # Orange
            EntityType.CHART: (128, 255, 128),    # Light Green
        }
        
        for entity in entities:
            if entity.bbox.x2 > entity.bbox.x1 and entity.bbox.y2 > entity.bbox.y1:
                color = color_map.get(entity.entity_type, (128, 128, 128))
                
                # Draw bounding box
                cv2.rectangle(
                    annotated_image,
                    (entity.bbox.x1, entity.bbox.y1),
                    (entity.bbox.x2, entity.bbox.y2),
                    color,
                    2
                )
                
                # Draw label
                label = f"{entity.entity_type.value}: {entity.confidence:.1%}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                
                # Background for label
                cv2.rectangle(
                    annotated_image,
                    (entity.bbox.x1, entity.bbox.y1 - label_size[1] - 10),
                    (entity.bbox.x1 + label_size[0], entity.bbox.y1),
                    color,
                    -1
                )
                
                # Label text
                cv2.putText(
                    annotated_image,
                    label,
                    (entity.bbox.x1, entity.bbox.y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
        
        return annotated_image
    
    def create_sample_image(self, sample_type: str) -> np.ndarray:
        """Create sample images for testing"""
        # Create a simple sample image based on type
        if sample_type == "Business Card":
            # Create a business card-like image
            image = np.ones((300, 500, 3), dtype=np.uint8) * 255
            cv2.putText(image, "John Doe", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            cv2.putText(image, "Software Engineer", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
            cv2.putText(image, "john.doe@email.com", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            cv2.putText(image, "+1 (555) 123-4567", (50, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            
        elif sample_type == "Document with Text":
            # Create a document-like image
            image = np.ones((600, 800, 3), dtype=np.uint8) * 255
            cv2.putText(image, "IMPORTANT DOCUMENT", (200, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            cv2.putText(image, "Date: January 15, 2024", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
            cv2.putText(image, "This is a sample document with various", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            cv2.putText(image, "types of information including names,", (50, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            cv2.putText(image, "dates, and organizations like ACME Corp.", (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            
        else:
            # Default sample image
            image = np.random.randint(100, 200, (400, 600, 3), dtype=np.uint8)
            cv2.putText(image, "Sample Image", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return image

def main():
    """Main function to run the Streamlit app"""
    ui = ImageEntityExtractionUI()
    ui.render_main_interface()

if __name__ == "__main__":
    main()