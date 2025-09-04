"""
Demo Application for Advanced Document Analysis System
Showcases comprehensive document structure detection with multiple engines and models
"""

import streamlit as st
from document_analysis_ui import render_document_analysis_dashboard

def main():
    """Main demo application"""
    st.set_page_config(
        page_title="Advanced Document Analysis Demo",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .tech-badge {
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📄 Advanced Document Analysis & Structure Detection</h1>
        <p>Comprehensive document processing with multiple AI models, OCR engines, and computer vision techniques</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo information
    with st.expander("ℹ️ About This Advanced Demo", expanded=False):
        st.markdown("""
        This demo showcases a **comprehensive document analysis system** with extensive open source options and cutting-edge AI models:
        
        ### 🤖 **AI Models & Engines**
        
        #### **Hugging Face Models:**
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="tech-badge">LayoutLMv3</div>
            <div class="tech-badge">TrOCR</div>
            <div class="tech-badge">Donut</div>
            <div class="tech-badge">Table Transformer</div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            - **LayoutLMv3**: Document understanding and layout analysis
            - **TrOCR**: Handwritten text recognition
            - **Donut**: End-to-end document parsing
            - **Table Transformer**: Advanced table structure detection
            """)
        
        st.markdown("""
        #### **OCR Engines:**
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="tech-badge">Tesseract</div>
            <div class="tech-badge">EasyOCR</div>
            <div class="tech-badge">PaddleOCR</div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            - **Tesseract**: Traditional OCR with 100+ languages
            - **EasyOCR**: Neural OCR with 80+ languages
            - **PaddleOCR**: High-performance Chinese/English OCR
            """)
        
        st.markdown("""
        #### **Computer Vision Libraries:**
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="tech-badge">OpenCV</div>
            <div class="tech-badge">LayoutParser</div>
            <div class="tech-badge">Detectron2</div>
            <div class="tech-badge">scikit-image</div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            - **OpenCV**: Image processing and computer vision
            - **LayoutParser**: Document layout analysis
            - **Detectron2**: Object detection for document elements
            - **scikit-image**: Advanced image processing algorithms
            """)
        
        st.markdown("""
        #### **Specialized Libraries:**
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="tech-badge">Camelot</div>
            <div class="tech-badge">Tabula</div>
            <div class="tech-badge">PDFplumber</div>
            <div class="tech-badge">PyMuPDF</div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            - **Camelot**: PDF table extraction
            - **Tabula**: Alternative table extraction
            - **PDFplumber**: PDF text and structure analysis
            - **PyMuPDF**: PDF processing and conversion
            """)
        
        st.markdown("""
        ### 🎯 **Key Features**
        
        <div class="feature-card">
        <h4>📋 Document Structure Detection</h4>
        <ul>
        <li><strong>Layout Analysis:</strong> Headers, paragraphs, lists, tables, figures</li>
        <li><strong>Multiple Models:</strong> PubLayNet, NewspaperNavigator, PrimaLayout</li>
        <li><strong>Computer Vision:</strong> MSER regions, line detection, clustering</li>
        </ul>
        </div>
        
        <div class="feature-card">
        <h4>📊 Advanced Table Extraction</h4>
        <ul>
        <li><strong>Multi-Method:</strong> Camelot, computer vision, Table Transformer</li>
        <li><strong>Structure Detection:</strong> Cell boundaries, row/column identification</li>
        <li><strong>Data Export:</strong> CSV, JSON, structured formats</li>
        </ul>
        </div>
        
        <div class="feature-card">
        <h4>📝 Form Field Detection</h4>
        <ul>
        <li><strong>Field Types:</strong> Text fields, checkboxes, radio buttons, signatures</li>
        <li><strong>Template Matching:</strong> Pattern recognition for form elements</li>
        <li><strong>Value Extraction:</strong> Automatic field value detection</li>
        </ul>
        </div>
        
        <div class="feature-card">
        <h4>✍️ Handwriting Recognition</h4>
        <ul>
        <li><strong>TrOCR Model:</strong> Microsoft's transformer-based handwriting OCR</li>
        <li><strong>Mixed Documents:</strong> Printed and handwritten text detection</li>
        <li><strong>Multiple Languages:</strong> Support for various scripts</li>
        </ul>
        </div>
        
        <div class="feature-card">
        <h4>🔍 Document Classification</h4>
        <ul>
        <li><strong>10+ Types:</strong> Invoice, receipt, contract, form, report, etc.</li>
        <li><strong>Keyword Analysis:</strong> Content-based classification</li>
        <li><strong>Layout Features:</strong> Structure-based type detection</li>
        </ul>
        </div>
        
        ### 🚀 **Advanced Processing Pipeline**
        
        1. **Image Preprocessing:** Deskewing, noise reduction, contrast enhancement
        2. **Multi-Engine OCR:** Parallel processing with multiple OCR engines
        3. **Layout Detection:** Multiple models for comprehensive structure analysis
        4. **Element Classification:** AI-powered categorization of document elements
        5. **Table Extraction:** Advanced table structure detection and data extraction
        6. **Form Analysis:** Automated form field detection and value extraction
        7. **Handwriting Recognition:** Specialized models for handwritten content
        8. **Document Classification:** Intelligent document type identification
        9. **Results Integration:** Comprehensive analysis with confidence scoring
        10. **Export Options:** Multiple output formats (JSON, CSV, structured data)
        
        ### 📈 **Performance Features**
        
        - **Parallel Processing:** Multiple OCR engines run simultaneously
        - **Confidence Scoring:** Each detection includes confidence metrics
        - **Fallback Systems:** Graceful degradation when models fail
        - **Batch Processing:** Support for multiple document analysis
        - **Memory Optimization:** Efficient processing of large documents
        - **GPU Acceleration:** CUDA support for compatible models
        
        ### 🔧 **Customization Options**
        
        - **Model Selection:** Choose specific models for different document types
        - **Processing Levels:** Basic, standard, or advanced preprocessing
        - **Confidence Thresholds:** Adjustable detection sensitivity
        - **Output Formats:** Flexible export options
        - **Visualization:** Interactive result visualization and annotation
        """, unsafe_allow_html=True)
    
    # Render the main dashboard
    render_document_analysis_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <h3>🔬 Advanced Document Analysis System</h3>
        <p><strong>Powered by:</strong> LayoutLMv3 • TrOCR • Donut • Table Transformer • EasyOCR • PaddleOCR • LayoutParser • Detectron2</p>
        <p><strong>Features:</strong> Multi-Engine OCR • Layout Analysis • Table Extraction • Form Detection • Handwriting Recognition • Document Classification</p>
        <p><strong>Open Source:</strong> Comprehensive integration of cutting-edge AI models and computer vision libraries</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()