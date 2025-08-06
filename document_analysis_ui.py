"""
Document Analysis and Structure Detection UI
Streamlit interface for comprehensive document analysis with multiple engines and models
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import base64
import io
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from document_analysis_system import (
    DocumentAnalysisSystem, DocumentType, LayoutElement,
    DocumentAnalysisResult, DocumentElement, DocumentTable, FormField
)

def render_document_analysis_dashboard():
    """Main document analysis dashboard"""
    st.title("📄 Advanced Document Analysis & Structure Detection")
    
    # Initialize system
    if 'doc_analysis_system' not in st.session_state:
        with st.spinner("Initializing document analysis system..."):
            st.session_state.doc_analysis_system = DocumentAnalysisSystem()
    
    system = st.session_state.doc_analysis_system
    
    # Sidebar configuration
    st.sidebar.title("Analysis Configuration")
    
    # Model selection
    st.sidebar.subheader("🤖 Model Selection")
    layout_model = st.sidebar.selectbox(
        "Layout Detection Model",
        ["publaynet", "newspaper", "prima"],
        help="Choose the layout detection model based on document type"
    )
    
    ocr_engines = st.sidebar.multiselect(
        "OCR Engines",
        ["Tesseract", "EasyOCR", "PaddleOCR"],
        default=["Tesseract", "EasyOCR"],
        help="Select OCR engines to use (multiple engines improve accuracy)"
    )
    
    enable_handwriting = st.sidebar.checkbox(
        "Enable Handwriting Recognition",
        value=True,
        help="Use TrOCR and specialized models for handwritten text"
    )
    
    enable_table_extraction = st.sidebar.checkbox(
        "Enable Advanced Table Extraction",
        value=True,
        help="Use multiple methods for table detection and extraction"
    )
    
    enable_form_detection = st.sidebar.checkbox(
        "Enable Form Field Detection",
        value=True,
        help="Detect checkboxes, text fields, and signatures"
    )
    
    # Processing options
    st.sidebar.subheader("⚙️ Processing Options")
    preprocessing_level = st.sidebar.select_slider(
        "Image Preprocessing Level",
        options=["Basic", "Standard", "Advanced"],
        value="Standard",
        help="Higher levels apply more preprocessing but may take longer"
    )
    
    confidence_threshold = st.sidebar.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="Minimum confidence for including detected elements"
    )
    
    # Main interface
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Upload & Analyze", 
        "🔍 Analysis Results", 
        "📊 Structure Visualization",
        "📋 Table Extraction",
        "📝 Form Analysis"
    ])
    
    with tab1:
        render_upload_interface(system, layout_model, ocr_engines, enable_handwriting, 
                              enable_table_extraction, enable_form_detection, 
                              preprocessing_level, confidence_threshold)
    
    with tab2:
        render_analysis_results()
    
    with tab3:
        render_structure_visualization()
    
    with tab4:
        render_table_extraction()
    
    with tab5:
        render_form_analysis()

def render_upload_interface(system, layout_model, ocr_engines, enable_handwriting,
                          enable_table_extraction, enable_form_detection,
                          preprocessing_level, confidence_threshold):
    """Render document upload and analysis interface"""
    
    st.header("📤 Document Upload & Analysis")
    
    # File upload options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a document file",
            type=['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'webp', 'pdf'],
            help="Supported formats: PNG, JPG, JPEG, TIFF, BMP, WEBP, PDF"
        )
    
    with col2:
        st.subheader("Sample Documents")
        sample_docs = {
            "Invoice Sample": "sample_invoice.png",
            "Form Sample": "sample_form.png",
            "Contract Sample": "sample_contract.png",
            "Receipt Sample": "sample_receipt.png"
        }
        
        selected_sample = st.selectbox(
            "Or try a sample document",
            ["None"] + list(sample_docs.keys())
        )
        
        if selected_sample != "None":
            st.info(f"Selected: {selected_sample}")
    
    # Analysis configuration
    st.subheader("🔧 Analysis Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        analyze_layout = st.checkbox("Layout Analysis", value=True)
        analyze_text = st.checkbox("Text Extraction", value=True)
    
    with col2:
        analyze_tables = st.checkbox("Table Detection", value=enable_table_extraction)
        analyze_forms = st.checkbox("Form Fields", value=enable_form_detection)
    
    with col3:
        analyze_handwriting = st.checkbox("Handwriting", value=enable_handwriting)
        classify_document = st.checkbox("Document Classification", value=True)
    
    # Process document
    if uploaded_file is not None or selected_sample != "None":
        
        # Load image
        if uploaded_file is not None:
            # Handle uploaded file
            if uploaded_file.type == "application/pdf":
                # Handle PDF
                st.info("PDF processing - converting to images...")
                # This would need PDF to image conversion
                image = None
                pdf_path = uploaded_file.name
            else:
                # Handle image file
                image = Image.open(uploaded_file)
                image_array = np.array(image)
                pdf_path = None
        else:
            # Handle sample document
            st.info("Loading sample document...")
            # This would load from sample files
            image_array = np.zeros((800, 600, 3), dtype=np.uint8)  # Placeholder
            pdf_path = None
        
        if image is not None:
            # Display original image
            st.subheader("📷 Original Document")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.image(image, caption="Original Document", use_column_width=True)
            
            with col2:
                st.write("**Document Info:**")
                st.write(f"Size: {image.size}")
                st.write(f"Mode: {image.mode}")
                st.write(f"Format: {image.format}")
        
        # Analysis button
        if st.button("🚀 Analyze Document", type="primary"):
            
            with st.spinner("Analyzing document... This may take a few minutes."):
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Convert PIL to numpy if needed
                    if isinstance(image, Image.Image):
                        image_array = np.array(image)
                    
                    # Update progress
                    progress_bar.progress(10)
                    status_text.text("Preprocessing image...")
                    
                    # Perform analysis
                    result = system.analyze_document(image_array, pdf_path)
                    
                    progress_bar.progress(100)
                    status_text.text("Analysis complete!")
                    
                    # Store results in session state
                    st.session_state.analysis_result = result
                    st.session_state.original_image = image_array
                    
                    # Display quick summary
                    st.success("✅ Document analysis completed!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Document Type", result.document_type.value.title())
                    
                    with col2:
                        st.metric("Layout Elements", len(result.elements))
                    
                    with col3:
                        st.metric("Tables Found", len(result.tables))
                    
                    with col4:
                        st.metric("Form Fields", len(result.form_fields))
                    
                    # Overall confidence
                    st.metric("Overall Confidence", f"{result.confidence:.2%}")
                    
                    # Quick preview of extracted text
                    if result.text_content:
                        st.subheader("📝 Extracted Text Preview")
                        preview_text = result.text_content[:500] + "..." if len(result.text_content) > 500 else result.text_content
                        st.text_area("Text Content", preview_text, height=150)
                    
                except Exception as e:
                    st.error(f"Error during analysis: {e}")
                    progress_bar.progress(0)
                    status_text.text("Analysis failed")

def render_analysis_results():
    """Render detailed analysis results"""
    
    st.header("🔍 Detailed Analysis Results")
    
    if 'analysis_result' not in st.session_state:
        st.info("👆 Please upload and analyze a document first.")
        return
    
    result = st.session_state.analysis_result
    
    # Document classification
    st.subheader("📋 Document Classification")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Document Type:** {result.document_type.value.title()}")
        st.write(f"**Overall Confidence:** {result.confidence:.2%}")
        st.write(f"**Text Length:** {len(result.text_content)} characters")
    
    with col2:
        # Confidence gauge
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = result.confidence * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Confidence Score"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Layout elements analysis
    st.subheader("🏗️ Layout Elements")
    
    if result.elements:
        # Element type distribution
        element_types = [elem.element_type.value for elem in result.elements]
        element_counts = pd.Series(element_types).value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                values=element_counts.values,
                names=element_counts.index,
                title="Element Type Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Element details table
            element_data = []
            for i, elem in enumerate(result.elements):
                element_data.append({
                    "ID": i + 1,
                    "Type": elem.element_type.value.title(),
                    "Confidence": f"{elem.confidence:.2%}",
                    "Text Preview": elem.text[:50] + "..." if len(elem.text) > 50 else elem.text,
                    "Bbox": f"({elem.bbox.x1}, {elem.bbox.y1}, {elem.bbox.x2}, {elem.bbox.y2})"
                })
            
            df = pd.DataFrame(element_data)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No layout elements detected.")
    
    # Full text content
    st.subheader("📄 Complete Text Content")
    
    if result.text_content:
        # Text statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Characters", len(result.text_content))
        
        with col2:
            word_count = len(result.text_content.split())
            st.metric("Words", word_count)
        
        with col3:
            line_count = len(result.text_content.split('\n'))
            st.metric("Lines", line_count)
        
        with col4:
            avg_word_length = np.mean([len(word) for word in result.text_content.split()]) if word_count > 0 else 0
            st.metric("Avg Word Length", f"{avg_word_length:.1f}")
        
        # Full text display
        st.text_area("Full Text Content", result.text_content, height=300)
        
        # Download options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="📄 Download Text",
                data=result.text_content,
                file_name="extracted_text.txt",
                mime="text/plain"
            )
        
        with col2:
            json_result = export_to_json(result)
            st.download_button(
                label="📊 Download JSON",
                data=json_result,
                file_name="analysis_result.json",
                mime="application/json"
            )
        
        with col3:
            csv_result = export_to_csv(result)
            st.download_button(
                label="📈 Download CSV",
                data=csv_result,
                file_name="analysis_result.csv",
                mime="text/csv"
            )
    else:
        st.warning("No text content extracted.")

def render_structure_visualization():
    """Render document structure visualization"""
    
    st.header("📊 Document Structure Visualization")
    
    if 'analysis_result' not in st.session_state or 'original_image' not in st.session_state:
        st.info("👆 Please upload and analyze a document first.")
        return
    
    result = st.session_state.analysis_result
    image = st.session_state.original_image
    
    # Visualization options
    st.subheader("🎨 Visualization Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_bboxes = st.checkbox("Show Bounding Boxes", value=True)
        show_text = st.checkbox("Show Text Labels", value=True)
    
    with col2:
        show_confidence = st.checkbox("Show Confidence Scores", value=False)
        color_by_type = st.checkbox("Color by Element Type", value=True)
    
    with col3:
        bbox_thickness = st.slider("Box Thickness", 1, 5, 2)
        font_size = st.slider("Font Size", 8, 20, 12)
    
    # Create visualization
    if result.elements:
        fig, ax = plt.subplots(1, 1, figsize=(12, 16))
        ax.imshow(image)
        ax.set_title("Document Structure Analysis", fontsize=16, fontweight='bold')
        
        # Color map for different element types
        colors = {
            'title': 'red',
            'header': 'blue',
            'paragraph': 'green',
            'list': 'orange',
            'table': 'purple',
            'figure': 'brown',
            'caption': 'pink',
            'footer': 'gray',
            'signature': 'cyan',
            'logo': 'magenta',
            'form_field': 'yellow',
            'handwriting': 'lime'
        }
        
        for i, elem in enumerate(result.elements):
            bbox = elem.bbox
            
            if show_bboxes:
                # Choose color
                if color_by_type:
                    color = colors.get(elem.element_type.value, 'black')
                else:
                    color = 'red'
                
                # Draw bounding box
                rect = patches.Rectangle(
                    (bbox.x1, bbox.y1),
                    bbox.x2 - bbox.x1,
                    bbox.y2 - bbox.y1,
                    linewidth=bbox_thickness,
                    edgecolor=color,
                    facecolor='none',
                    alpha=0.8
                )
                ax.add_patch(rect)
                
                # Add labels
                if show_text or show_confidence:
                    label_parts = []
                    if show_text:
                        label_parts.append(f"{elem.element_type.value}")
                    if show_confidence:
                        label_parts.append(f"{elem.confidence:.2f}")
                    
                    label = " | ".join(label_parts)
                    
                    ax.text(
                        bbox.x1, bbox.y1 - 5,
                        label,
                        fontsize=font_size,
                        color=color,
                        fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
                    )
        
        ax.axis('off')
        st.pyplot(fig, use_container_width=True)
        
        # Legend
        if color_by_type:
            st.subheader("🎨 Element Type Legend")
            legend_cols = st.columns(4)
            
            unique_types = list(set(elem.element_type.value for elem in result.elements))
            for i, elem_type in enumerate(unique_types):
                col_idx = i % 4
                color = colors.get(elem_type, 'black')
                legend_cols[col_idx].markdown(
                    f'<span style="color: {color};">●</span> {elem_type.title()}',
                    unsafe_allow_html=True
                )
    else:
        st.info("No layout elements to visualize.")
    
    # Element statistics
    if result.elements:
        st.subheader("📈 Element Statistics")
        
        # Create statistics dataframe
        stats_data = []
        for elem in result.elements:
            bbox = elem.bbox
            area = (bbox.x2 - bbox.x1) * (bbox.y2 - bbox.y1)
            
            stats_data.append({
                'Element Type': elem.element_type.value.title(),
                'Confidence': elem.confidence,
                'Area (pixels)': area,
                'Width': bbox.x2 - bbox.x1,
                'Height': bbox.y2 - bbox.y1,
                'Text Length': len(elem.text)
            })
        
        stats_df = pd.DataFrame(stats_data)
        
        # Display statistics
        col1, col2 = st.columns(2)
        
        with col1:
            # Confidence distribution
            fig = px.histogram(
                stats_df,
                x='Confidence',
                title='Confidence Score Distribution',
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Area distribution by type
            fig = px.box(
                stats_df,
                x='Element Type',
                y='Area (pixels)',
                title='Element Area Distribution by Type'
            )
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

def render_table_extraction():
    """Render table extraction results"""
    
    st.header("📋 Table Extraction Results")
    
    if 'analysis_result' not in st.session_state:
        st.info("👆 Please upload and analyze a document first.")
        return
    
    result = st.session_state.analysis_result
    
    if not result.tables:
        st.info("No tables detected in the document.")
        return
    
    st.write(f"**Found {len(result.tables)} table(s)**")
    
    for i, table in enumerate(result.tables):
        st.subheader(f"📊 Table {i + 1}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Rows", table.num_rows)
        
        with col2:
            st.metric("Columns", table.num_cols)
        
        with col3:
            st.metric("Confidence", f"{table.confidence:.2%}")
        
        # Create table dataframe
        if table.cells:
            # Initialize empty dataframe
            table_data = {}
            max_row = max(cell.row for cell in table.cells)
            max_col = max(cell.col for cell in table.cells)
            
            # Fill table data
            for row in range(max_row + 1):
                for col in range(max_col + 1):
                    # Find cell for this position
                    cell_text = ""
                    for cell in table.cells:
                        if cell.row == row and cell.col == col:
                            cell_text = cell.text
                            break
                    
                    col_name = f"Column {col + 1}"
                    if col_name not in table_data:
                        table_data[col_name] = []
                    table_data[col_name].append(cell_text)
            
            # Display table
            if table_data:
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True)
                
                # Download table
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download Table {i + 1} as CSV",
                    data=csv_data,
                    file_name=f"table_{i + 1}.csv",
                    mime="text/csv"
                )
        
        # Table visualization
        if 'original_image' in st.session_state:
            st.subheader(f"📍 Table {i + 1} Location")
            
            image = st.session_state.original_image
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            ax.imshow(image)
            
            # Draw table bounding box
            bbox = table.bbox
            rect = patches.Rectangle(
                (bbox.x1, bbox.y1),
                bbox.x2 - bbox.x1,
                bbox.y2 - bbox.y1,
                linewidth=3,
                edgecolor='red',
                facecolor='none',
                alpha=0.8
            )
            ax.add_patch(rect)
            
            # Draw cell boundaries
            for cell in table.cells:
                cell_bbox = cell.bbox
                cell_rect = patches.Rectangle(
                    (cell_bbox.x1, cell_bbox.y1),
                    cell_bbox.x2 - cell_bbox.x1,
                    cell_bbox.y2 - cell_bbox.y1,
                    linewidth=1,
                    edgecolor='blue',
                    facecolor='none',
                    alpha=0.5
                )
                ax.add_patch(cell_rect)
            
            ax.set_title(f"Table {i + 1} Structure")
            ax.axis('off')
            st.pyplot(fig, use_container_width=True)

def render_form_analysis():
    """Render form field analysis"""
    
    st.header("📝 Form Field Analysis")
    
    if 'analysis_result' not in st.session_state:
        st.info("👆 Please upload and analyze a document first.")
        return
    
    result = st.session_state.analysis_result
    
    if not result.form_fields:
        st.info("No form fields detected in the document.")
        return
    
    st.write(f"**Found {len(result.form_fields)} form field(s)**")
    
    # Form field statistics
    field_types = [field.field_type for field in result.form_fields]
    field_type_counts = pd.Series(field_types).value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Field type distribution
        fig = px.pie(
            values=field_type_counts.values,
            names=field_type_counts.index,
            title="Form Field Type Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Field details
        field_data = []
        for i, field in enumerate(result.form_fields):
            field_data.append({
                "ID": i + 1,
                "Name": field.field_name,
                "Type": field.field_type.title(),
                "Value": field.field_value[:30] + "..." if len(field.field_value) > 30 else field.field_value,
                "Confidence": f"{field.confidence:.2%}"
            })
        
        df = pd.DataFrame(field_data)
        st.dataframe(df, use_container_width=True)
    
    # Form field visualization
    if 'original_image' in st.session_state:
        st.subheader("📍 Form Field Locations")
        
        image = st.session_state.original_image
        fig, ax = plt.subplots(1, 1, figsize=(12, 16))
        ax.imshow(image)
        
        # Color map for field types
        field_colors = {
            'text': 'blue',
            'checkbox': 'green',
            'radio': 'orange',
            'signature': 'red',
            'dropdown': 'purple'
        }
        
        for i, field in enumerate(result.form_fields):
            bbox = field.bbox
            color = field_colors.get(field.field_type, 'black')
            
            # Draw bounding box
            rect = patches.Rectangle(
                (bbox.x1, bbox.y1),
                bbox.x2 - bbox.x1,
                bbox.y2 - bbox.y1,
                linewidth=2,
                edgecolor=color,
                facecolor='none',
                alpha=0.8
            )
            ax.add_patch(rect)
            
            # Add label
            label = f"{field.field_type}: {field.field_name}"
            ax.text(
                bbox.x1, bbox.y1 - 5,
                label,
                fontsize=10,
                color=color,
                fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
            )
        
        ax.set_title("Form Field Detection")
        ax.axis('off')
        st.pyplot(fig, use_container_width=True)
        
        # Legend
        st.subheader("🎨 Field Type Legend")
        legend_cols = st.columns(len(field_colors))
        
        for i, (field_type, color) in enumerate(field_colors.items()):
            if i < len(legend_cols):
                legend_cols[i].markdown(
                    f'<span style="color: {color};">●</span> {field_type.title()}',
                    unsafe_allow_html=True
                )

def export_to_json(result: DocumentAnalysisResult) -> str:
    """Export analysis result to JSON"""
    try:
        system = DocumentAnalysisSystem()
        return system.export_results(result, 'json')
    except Exception as e:
        return json.dumps({"error": str(e)})

def export_to_csv(result: DocumentAnalysisResult) -> str:
    """Export analysis result to CSV"""
    try:
        system = DocumentAnalysisSystem()
        return system.export_results(result, 'csv')
    except Exception as e:
        return f"Error exporting to CSV: {e}"

if __name__ == "__main__":
    render_document_analysis_dashboard()