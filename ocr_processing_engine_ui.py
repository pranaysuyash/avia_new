"""
Streamlit UI for Enterprise OCR Processing Engine

This module provides a comprehensive web interface for configuring and testing
OCR processing with multiple providers and advanced settings.
"""

import streamlit as st
import cv2
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from PIL import Image
import io
import base64

from ocr_processing_engine import (
    OCRProcessingService, OCRConfig, OCRProvider, PreprocessingMode,
    RoutingPolicy, TextDetectionMethod, OCRResult, TextSegment,
    TextDetectionService, create_ocr_config
)


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Enterprise OCR Processing Engine",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Enterprise OCR Processing Engine")
    st.markdown("Advanced OCR processing with multiple providers and intelligent routing")
    
    # Initialize session state
    if 'ocr_results' not in st.session_state:
        st.session_state.ocr_results = None
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    if 'provider_metrics' not in st.session_state:
        st.session_state.provider_metrics = {}
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ OCR Configuration")
        config = configure_ocr_settings()
        
        st.header("📊 Provider Status")
        display_provider_status()
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["🖼️ Image Processing", "📈 Analytics", "🔧 Text Detection", "📋 History"])
    
    with tab1:
        image_processing_tab(config)
    
    with tab2:
        analytics_tab()
    
    with tab3:
        text_detection_tab()
    
    with tab4:
        history_tab()


def configure_ocr_settings() -> OCRConfig:
    """Configure OCR settings in sidebar"""
    
    # Provider selection
    st.subheader("🔌 OCR Providers")
    
    available_providers = []
    service = OCRProcessingService()
    try:
        all_providers = service.get_available_providers()
        
        for provider in OCRProvider:
            if provider.value in all_providers:
                if st.checkbox(f"{provider.value.title()}", value=True, key=f"provider_{provider.value}"):
                    available_providers.append(provider)
        
        if not available_providers:
            st.warning("No providers selected! Defaulting to available providers.")
            available_providers = [OCRProvider(p) for p in all_providers]
    
    finally:
        service.cleanup()
    
    # Routing policy
    st.subheader("🎯 Routing Policy")
    routing_policy = st.selectbox(
        "Provider Selection Strategy",
        options=[policy.value for policy in RoutingPolicy],
        index=3,  # Default to balanced
        help="How to select OCR provider for processing"
    )
    
    # Preprocessing settings
    st.subheader("🔧 Preprocessing")
    
    preprocessing_mode = st.selectbox(
        "Preprocessing Mode",
        options=[mode.value for mode in PreprocessingMode],
        index=1,  # Default to standard
        help="Level of image preprocessing to apply"
    )
    
    # Language settings
    st.subheader("🌐 Language Settings")
    
    languages = st.multiselect(
        "Languages",
        options=['en', 'es', 'fr', 'de', 'zh', 'ja', 'ko', 'ar', 'ru'],
        default=['en'],
        help="Languages to detect and process"
    )
    
    # Quality settings
    st.subheader("📊 Quality Settings")
    
    confidence_threshold = st.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Minimum confidence score for text segments"
    )
    
    # Advanced settings
    with st.expander("🔬 Advanced Settings"):
        enable_calibration = st.checkbox(
            "Enable Confidence Calibration",
            value=True,
            help="Calibrate confidence scores based on historical accuracy"
        )
        
        enable_normalization = st.checkbox(
            "Enable Text Normalization",
            value=True,
            help="Apply text cleaning and normalization"
        )
        
        enable_language_detection = st.checkbox(
            "Enable Language Detection",
            value=True,
            help="Automatically detect text language"
        )
        
        max_processing_time = st.slider(
            "Max Processing Time (seconds)",
            min_value=5.0,
            max_value=120.0,
            value=30.0,
            step=5.0,
            help="Maximum time allowed for processing"
        )
    
    return OCRConfig(
        providers=available_providers,
        routing_policy=RoutingPolicy(routing_policy),
        preprocessing_mode=PreprocessingMode(preprocessing_mode),
        languages=languages,
        confidence_threshold=confidence_threshold,
        enable_confidence_calibration=enable_calibration,
        enable_text_normalization=enable_normalization,
        enable_language_detection=enable_language_detection,
        max_processing_time=max_processing_time
    )


def display_provider_status():
    """Display status of available OCR providers"""
    service = OCRProcessingService()
    try:
        available_providers = service.get_available_providers()
        
        if available_providers:
            for provider in available_providers:
                st.success(f"✅ {provider.title()}")
        else:
            st.error("❌ No providers available")
        
        # Display metrics if available
        if st.session_state.provider_metrics:
            st.subheader("📈 Performance Metrics")
            for provider, metrics in st.session_state.provider_metrics.items():
                with st.expander(f"{provider.title()} Metrics"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Success Rate", f"{metrics.get('success_rate', 0):.1%}")
                        st.metric("Avg Latency", f"{metrics.get('average_latency', 0):.2f}s")
                    with col2:
                        st.metric("Avg Confidence", f"{metrics.get('average_confidence', 0):.3f}")
                        st.metric("Total Requests", f"{metrics.get('total_requests', 0):,}")
    
    finally:
        service.cleanup()


def image_processing_tab(config: OCRConfig):
    """Main image processing interface"""
    st.header("🖼️ Image OCR Processing")
    
    # Image upload options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📁 Upload Image")
        
        upload_method = st.radio(
            "Upload Method",
            options=["File Upload", "Camera Capture", "Sample Images"],
            horizontal=True
        )
        
        image = None
        
        if upload_method == "File Upload":
            uploaded_file = st.file_uploader(
                "Choose an image file",
                type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
                help="Upload an image containing text for OCR processing"
            )
            
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)
        
        elif upload_method == "Camera Capture":
            camera_image = st.camera_input("Take a picture")
            if camera_image is not None:
                image = Image.open(camera_image)
        
        elif upload_method == "Sample Images":
            sample_choice = st.selectbox(
                "Choose Sample",
                options=["Text Document", "Street Sign", "Receipt", "Business Card"]
            )
            
            if st.button("Generate Sample Image"):
                image = generate_sample_image(sample_choice)
                st.image(image, caption=f"Sample: {sample_choice}", use_column_width=True)
    
    with col2:
        st.subheader("⚡ Quick Actions")
        
        if image is not None:
            # Convert PIL to numpy array
            image_array = np.array(image)
            if len(image_array.shape) == 3 and image_array.shape[2] == 4:
                # Convert RGBA to RGB
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
            elif len(image_array.shape) == 3:
                # Convert RGB to BGR for OpenCV
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Cost estimation
            if st.button("💰 Estimate Cost"):
                estimate_processing_cost(image_array, config)
            
            # Process image
            if st.button("🚀 Process Image", type="primary"):
                process_image_with_ocr(image_array, config)
            
            # Batch processing
            st.subheader("📦 Batch Processing")
            if st.button("🔄 Process Multiple"):
                st.info("Batch processing feature - upload multiple images")
        
        else:
            st.info("Upload an image to see processing options")
    
    # Display results
    if st.session_state.ocr_results:
        display_ocr_results(st.session_state.ocr_results)


def generate_sample_image(sample_type: str) -> Image.Image:
    """Generate sample images for testing"""
    # Create a white background
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    
    if sample_type == "Text Document":
        # Add document-like text
        cv2.putText(img, "SAMPLE DOCUMENT", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(img, "This is a sample text document", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(img, "for OCR processing demonstration.", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(img, "It contains multiple lines of text", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(img, "with different font sizes and styles.", (50, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    elif sample_type == "Street Sign":
        # Create street sign-like image
        cv2.rectangle(img, (100, 100), (500, 300), (0, 100, 0), -1)
        cv2.putText(img, "MAIN STREET", (150, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        cv2.putText(img, "NEXT EXIT", (180, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    elif sample_type == "Receipt":
        # Create receipt-like image
        cv2.putText(img, "STORE RECEIPT", (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(img, "Item 1................$10.99", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(img, "Item 2................$15.50", (100, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(img, "Tax...................$2.12", (100, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(img, "Total................$28.61", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    elif sample_type == "Business Card":
        # Create business card-like image
        cv2.rectangle(img, (50, 100), (550, 300), (200, 200, 200), 2)
        cv2.putText(img, "John Smith", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(img, "Software Engineer", (100, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(img, "john.smith@company.com", (100, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(img, "(555) 123-4567", (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    # Convert BGR to RGB for PIL
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)


def estimate_processing_cost(image: np.ndarray, config: OCRConfig):
    """Estimate processing cost for image"""
    service = OCRProcessingService(config)
    
    try:
        with st.spinner("Estimating processing cost..."):
            cost_estimate = service.estimate_processing_cost([image], config)
        
        st.subheader("💰 Cost Estimation")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Estimated Cost",
                f"${cost_estimate['estimated_total_cost']:.4f}",
                help="Estimated cost for processing this image"
            )
        
        with col2:
            st.metric(
                "Processing Time",
                f"{cost_estimate['estimated_processing_time']:.2f}s",
                help="Estimated processing time"
            )
        
        with col3:
            st.metric(
                "Routing Policy",
                config.routing_policy.value.title(),
                help="Selected provider routing policy"
            )
    
    except Exception as e:
        st.error(f"Cost estimation failed: {str(e)}")
    
    finally:
        service.cleanup()


def process_image_with_ocr(image: np.ndarray, config: OCRConfig):
    """Process image with OCR and display results"""
    service = OCRProcessingService(config)
    
    try:
        with st.spinner("Processing image with OCR..."):
            start_time = time.time()
            result = service.process_image(image, config)
            end_time = time.time()
        
        # Store results
        st.session_state.ocr_results = result
        
        # Update processing history
        history_entry = {
            'timestamp': datetime.now(),
            'provider': result.provider,
            'segments_found': len(result.segments),
            'processing_time': end_time - start_time,
            'average_confidence': result.get_average_confidence(),
            'text_extracted': result.get_text()
        }
        st.session_state.processing_history.append(history_entry)
        
        # Update provider metrics
        provider_metrics = service.get_provider_metrics()
        st.session_state.provider_metrics.update(provider_metrics)
        
        st.success(f"✅ OCR processing completed in {end_time - start_time:.2f}s")
        
    except Exception as e:
        st.error(f"OCR processing failed: {str(e)}")
    
    finally:
        service.cleanup()


def display_ocr_results(result: OCRResult):
    """Display OCR processing results"""
    st.header("📋 OCR Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Provider Used", result.provider.title())
    
    with col2:
        st.metric("Segments Found", len(result.segments))
    
    with col3:
        st.metric("Processing Time", f"{result.processing_time:.3f}s")
    
    with col4:
        st.metric("Avg Confidence", f"{result.get_average_confidence():.3f}")
    
    # Extracted text
    st.subheader("📝 Extracted Text")
    extracted_text = result.get_text()
    
    if extracted_text:
        st.text_area(
            "Full Text",
            value=extracted_text,
            height=150,
            help="Complete extracted text from the image"
        )
        
        # Copy to clipboard button
        if st.button("📋 Copy to Clipboard"):
            st.write("Text copied to clipboard!")  # In real app, would use JS
    else:
        st.warning("No text was extracted from the image")
    
    # Detailed segments
    if result.segments:
        st.subheader("🔍 Text Segments")
        
        # Create DataFrame for segments
        segment_data = []
        for i, segment in enumerate(result.segments):
            segment_data.append({
                'Segment': i + 1,
                'Text': segment.text,
                'Confidence': f"{segment.confidence:.3f}",
                'Language': segment.language,
                'X': segment.bounding_box.x,
                'Y': segment.bounding_box.y,
                'Width': segment.bounding_box.width,
                'Height': segment.bounding_box.height
            })
        
        df = pd.DataFrame(segment_data)
        st.dataframe(df, use_container_width=True)
        
        # Confidence distribution
        confidences = [seg.confidence for seg in result.segments]
        
        fig_conf = px.histogram(
            x=confidences,
            nbins=20,
            title="Confidence Score Distribution",
            labels={'x': 'Confidence Score', 'y': 'Count'}
        )
        st.plotly_chart(fig_conf, use_container_width=True)
    
    # Processing details
    with st.expander("🔧 Processing Details"):
        st.json({
            'provider': result.provider,
            'detection_method': result.detection_method,
            'preprocessing_applied': result.preprocessing_applied,
            'confidence_calibrated': result.confidence_calibrated,
            'language_detected': result.language_detected,
            'image_hash': result.image_hash
        })


def analytics_tab():
    """Analytics and metrics dashboard"""
    st.header("📈 OCR Analytics Dashboard")
    
    if not st.session_state.processing_history:
        st.info("No processing history available. Process some images to see analytics.")
        return
    
    # Create DataFrame from history
    df = pd.DataFrame(st.session_state.processing_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Processed", len(df))
    
    with col2:
        avg_time = df['processing_time'].mean()
        st.metric("Avg Processing Time", f"{avg_time:.2f}s")
    
    with col3:
        avg_confidence = df['average_confidence'].mean()
        st.metric("Avg Confidence", f"{avg_confidence:.3f}")
    
    with col4:
        total_segments = df['segments_found'].sum()
        st.metric("Total Segments", f"{total_segments:,}")
    
    # Processing time over time
    fig_time = px.line(
        df, x='timestamp', y='processing_time',
        title='Processing Time Over Time',
        labels={'processing_time': 'Processing Time (s)', 'timestamp': 'Time'}
    )
    st.plotly_chart(fig_time, use_container_width=True)
    
    # Provider usage
    provider_counts = df['provider'].value_counts()
    fig_providers = px.pie(
        values=provider_counts.values,
        names=provider_counts.index,
        title='Provider Usage Distribution'
    )
    st.plotly_chart(fig_providers, use_container_width=True)
    
    # Confidence vs Processing Time
    fig_scatter = px.scatter(
        df, x='processing_time', y='average_confidence',
        color='provider', size='segments_found',
        title='Confidence vs Processing Time',
        labels={'processing_time': 'Processing Time (s)', 'average_confidence': 'Average Confidence'}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)


def text_detection_tab():
    """Text detection testing interface"""
    st.header("🔧 Text Detection Testing")
    
    st.markdown("Test different text detection methods separately from OCR recognition.")
    
    # Upload image for detection
    uploaded_file = st.file_uploader(
        "Upload image for text detection",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        key="detection_upload"
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        image_array = np.array(image)
        
        if len(image_array.shape) == 3:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(image, caption="Original Image", use_column_width=True)
        
        with col2:
            # Detection method selection
            detection_method = st.selectbox(
                "Detection Method",
                options=[method.value for method in TextDetectionMethod if method != TextDetectionMethod.PROVIDER_NATIVE],
                help="Choose text detection algorithm"
            )
            
            if st.button("🔍 Detect Text Regions"):
                detect_text_regions(image_array, TextDetectionMethod(detection_method))


def detect_text_regions(image: np.ndarray, method: TextDetectionMethod):
    """Detect and visualize text regions"""
    detector = TextDetectionService()
    
    with st.spinner(f"Detecting text regions using {method.value}..."):
        regions = detector.detect_text_regions(image, method)
    
    st.subheader(f"📍 Detected Regions ({len(regions)} found)")
    
    if regions:
        # Create visualization
        vis_image = image.copy()
        
        for i, region in enumerate(regions):
            # Draw bounding box
            cv2.rectangle(
                vis_image,
                (region.x, region.y),
                (region.x + region.width, region.y + region.height),
                (0, 255, 0), 2
            )
            
            # Add region number
            cv2.putText(
                vis_image, str(i + 1),
                (region.x, region.y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
            )
        
        # Convert BGR to RGB for display
        vis_image_rgb = cv2.cvtColor(vis_image, cv2.COLOR_BGR2RGB)
        st.image(vis_image_rgb, caption="Detected Text Regions", use_column_width=True)
        
        # Region details
        region_data = []
        for i, region in enumerate(regions):
            region_data.append({
                'Region': i + 1,
                'X': region.x,
                'Y': region.y,
                'Width': region.width,
                'Height': region.height,
                'Area': region.area(),
                'Confidence': f"{region.confidence:.3f}"
            })
        
        df = pd.DataFrame(region_data)
        st.dataframe(df, use_container_width=True)
    
    else:
        st.warning("No text regions detected")


def history_tab():
    """Processing history and logs"""
    st.header("📋 Processing History")
    
    if not st.session_state.processing_history:
        st.info("No processing history available.")
        return
    
    # Display history table
    df = pd.DataFrame(st.session_state.processing_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by timestamp (newest first)
    df = df.sort_values('timestamp', ascending=False)
    
    # Format for display
    display_df = df.copy()
    display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['processing_time'] = display_df['processing_time'].round(3)
    display_df['average_confidence'] = display_df['average_confidence'].round(3)
    
    st.dataframe(display_df, use_container_width=True)
    
    # Export options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export CSV"):
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"ocr_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("🗑️ Clear History"):
            st.session_state.processing_history = []
            st.session_state.provider_metrics = {}
            st.rerun()
    
    with col3:
        if st.button("📋 Generate Report"):
            generate_processing_report(df)


def generate_processing_report(df: pd.DataFrame):
    """Generate comprehensive processing report"""
    report = {
        'summary': {
            'total_processed': len(df),
            'date_range': {
                'start': df['timestamp'].min().isoformat(),
                'end': df['timestamp'].max().isoformat()
            },
            'average_processing_time': df['processing_time'].mean(),
            'average_confidence': df['average_confidence'].mean(),
            'total_segments': df['segments_found'].sum()
        },
        'provider_statistics': df.groupby('provider').agg({
            'processing_time': ['mean', 'std', 'min', 'max'],
            'average_confidence': ['mean', 'std'],
            'segments_found': ['sum', 'mean']
        }).to_dict(),
        'performance_trends': {
            'processing_times': df['processing_time'].tolist(),
            'confidence_scores': df['average_confidence'].tolist(),
            'timestamps': df['timestamp'].dt.isoformat().tolist()
        }
    }
    
    report_json = json.dumps(report, indent=2, default=str)
    
    st.download_button(
        label="📋 Download Report",
        data=report_json,
        file_name=f"ocr_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )


if __name__ == "__main__":
    main()