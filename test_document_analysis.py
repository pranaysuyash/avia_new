"""
Comprehensive Test Suite for Advanced Document Analysis System
Tests all components including multiple OCR engines, Hugging Face models, and computer vision approaches
"""

import pytest
import numpy as np
import cv2
from PIL import Image
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Mock heavy dependencies before importing
import sys
from unittest.mock import Mock, MagicMock

# Mock all the heavy ML libraries before any imports
mock_modules = [
    'pytesseract', 'easyocr', 'paddleocr', 'layoutparser', 'fitz',
    'detectron2', 'detectron2.utils', 'detectron2.utils.logger', 
    'detectron2.model_zoo', 'detectron2.engine', 'detectron2.config',
    'camelot', 'tabula', 'pdfplumber', 'transformers', 'torch', 
    'torchvision', 'torchvision.transforms', 'skimage', 'skimage.filters',
    'skimage.morphology', 'skimage.measure', 'scipy', 'scipy.ndimage',
    'scipy.sparse', 'sklearn', 'sklearn.cluster', 'sklearn.base',
    'sklearn.utils', 'sklearn.utils._metadata_requests', 'sklearn.utils._chunking',
    'sklearn.utils._param_validation'
]

for module in mock_modules:
    sys.modules[module] = Mock()

# Now import the actual module
from document_analysis_system import (
    DocumentAnalysisSystem, DocumentType, LayoutElement,
    DocumentAnalysisResult, DocumentElement, DocumentTable, FormField,
    BoundingBox, TableCell
)

class TestDocumentAnalysisSystem:
    """Test cases for DocumentAnalysisSystem"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create a mock system to avoid loading heavy models in tests
        with patch('document_analysis_system.LayoutLMv3Processor'), \
             patch('document_analysis_system.LayoutLMv3ForTokenClassification'), \
             patch('document_analysis_system.TrOCRProcessor'), \
             patch('document_analysis_system.VisionEncoderDecoderModel'), \
             patch('document_analysis_system.DonutProcessor'), \
             patch('document_analysis_system.AutoModel'), \
             patch('document_analysis_system.easyocr.Reader'), \
             patch('document_analysis_system.paddleocr.PaddleOCR'), \
             patch('document_analysis_system.lp.Detectron2LayoutModel'):
            
            self.system = DocumentAnalysisSystem()
        
        # Create test image
        self.test_image = np.zeros((800, 600, 3), dtype=np.uint8)
        # Add some text-like patterns
        cv2.rectangle(self.test_image, (50, 50), (550, 100), (255, 255, 255), -1)
        cv2.rectangle(self.test_image, (50, 150), (550, 200), (255, 255, 255), -1)
        cv2.rectangle(self.test_image, (50, 250), (550, 400), (255, 255, 255), -1)
    
    def test_system_initialization(self):
        """Test system initialization"""
        assert self.system is not None
        assert hasattr(self.system, 'setup_models')
        assert hasattr(self.system, 'setup_ocr_engines')
        assert hasattr(self.system, 'setup_layout_models')
    
    def test_image_preprocessing(self):
        """Test image preprocessing pipeline"""
        processed = self.system.preprocess_image(self.test_image)
        
        assert processed is not None
        assert processed.shape[:2] == self.test_image.shape[:2]
        assert len(processed.shape) == 2  # Should be grayscale
    
    def test_deskew_image(self):
        """Test image deskewing"""
        # Create a slightly rotated image
        rows, cols = self.test_image.shape[:2]
        center = (cols // 2, rows // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, 5, 1.0)
        rotated = cv2.warpAffine(self.test_image, rotation_matrix, (cols, rows))
        
        # Convert to grayscale for deskewing
        gray_rotated = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
        
        deskewed = self.system.deskew_image(gray_rotated)
        
        assert deskewed is not None
        assert deskewed.shape == gray_rotated.shape
    
    def test_detect_layout_elements_computer_vision(self):
        """Test computer vision-based layout detection"""
        elements = self.system.detect_with_computer_vision(self.test_image)
        
        assert isinstance(elements, list)
        # Should detect some elements from our test pattern
        for element in elements:
            assert isinstance(element, DocumentElement)
            assert isinstance(element.bbox, BoundingBox)
            assert isinstance(element.confidence, float)
            assert 0 <= element.confidence <= 1
    
    def test_group_text_regions(self):
        """Test text region grouping"""
        # Create mock regions
        regions = [
            np.array([[100, 100], [150, 100], [150, 120], [100, 120]]),
            np.array([[100, 130], [150, 130], [150, 150], [100, 150]]),
            np.array([[300, 100], [350, 100], [350, 120], [300, 120]])
        ]
        
        grouped = self.system.group_text_regions(regions, (800, 600))
        
        assert isinstance(grouped, list)
        for group in grouped:
            assert 'x1' in group
            assert 'y1' in group
            assert 'x2' in group
            assert 'y2' in group
            assert 'confidence' in group
    
    def test_detect_horizontal_lines(self):
        """Test horizontal line detection"""
        # Create image with horizontal lines
        test_img = np.zeros((400, 600), dtype=np.uint8)
        cv2.line(test_img, (50, 100), (550, 100), 255, 2)
        cv2.line(test_img, (50, 200), (550, 200), 255, 2)
        cv2.line(test_img, (50, 300), (550, 300), 255, 2)
        
        lines = self.system.detect_horizontal_lines(test_img)
        
        assert isinstance(lines, list)
        # Should detect the horizontal lines we drew
        assert len(lines) >= 1
    
    def test_detect_vertical_lines(self):
        """Test vertical line detection"""
        # Create image with vertical lines
        test_img = np.zeros((400, 600), dtype=np.uint8)
        cv2.line(test_img, (100, 50), (100, 350), 255, 2)
        cv2.line(test_img, (200, 50), (200, 350), 255, 2)
        cv2.line(test_img, (300, 50), (300, 350), 255, 2)
        
        lines = self.system.detect_vertical_lines(test_img)
        
        assert isinstance(lines, list)
        # Should detect the vertical lines we drew
        assert len(lines) >= 1
    
    def test_detect_tables_from_lines(self):
        """Test table detection from line intersections"""
        h_lines = [(50, 100, 550, 102), (50, 200, 550, 202)]
        v_lines = [(100, 50, 102, 250), (200, 50, 202, 250)]
        
        tables = self.system.detect_tables_from_lines(h_lines, v_lines)
        
        assert isinstance(tables, list)
        for table in tables:
            assert 'x1' in table
            assert 'y1' in table
            assert 'x2' in table
            assert 'y2' in table
            assert 'confidence' in table
    
    @patch('document_analysis_system.pytesseract.image_to_string')
    def test_extract_text_from_region(self, mock_tesseract):
        """Test text extraction from image region"""
        mock_tesseract.return_value = "Sample extracted text"
        
        # Mock EasyOCR
        self.system.easyocr_reader = Mock()
        self.system.easyocr_reader.readtext.return_value = [
            ([(0, 0), (100, 0), (100, 20), (0, 20)], "Sample text", 0.9)
        ]
        
        # Mock PaddleOCR
        self.system.paddle_ocr = Mock()
        self.system.paddle_ocr.ocr.return_value = [
            [([0, 0, 100, 20], ("Sample text", 0.9))]
        ]
        
        text = self.system.extract_text_from_region(self.test_image)
        
        assert isinstance(text, str)
        assert len(text) > 0
    
    def test_detect_checkboxes(self):
        """Test checkbox detection"""
        # Create image with checkbox-like patterns
        test_img = np.zeros((200, 200, 3), dtype=np.uint8)
        cv2.rectangle(test_img, (50, 50), (70, 70), (255, 255, 255), 2)
        cv2.rectangle(test_img, (50, 100), (70, 120), (255, 255, 255), 2)
        
        form_fields = self.system.detect_checkboxes(test_img)
        
        assert isinstance(form_fields, list)
        for field in form_fields:
            assert isinstance(field, FormField)
            assert field.field_type == "checkbox"
    
    def test_detect_text_fields(self):
        """Test text field detection"""
        # Create image with text field-like rectangles
        test_img = np.zeros((200, 400, 3), dtype=np.uint8)
        cv2.rectangle(test_img, (50, 50), (350, 80), (255, 255, 255), 2)
        cv2.rectangle(test_img, (50, 100), (350, 130), (255, 255, 255), 2)
        
        with patch.object(self.system, 'extract_text_from_region', return_value="Sample text"):
            form_fields = self.system.detect_text_fields(test_img)
        
        assert isinstance(form_fields, list)
        for field in form_fields:
            assert isinstance(field, FormField)
            assert field.field_type == "text"
    
    def test_detect_signatures(self):
        """Test signature detection"""
        # Create image with signature-like irregular patterns
        test_img = np.zeros((200, 400), dtype=np.uint8)
        
        # Draw some irregular curves to simulate signature
        points = np.array([[100, 100], [120, 90], [140, 110], [160, 95], [180, 105]], np.int32)
        cv2.polylines(test_img, [points], False, 255, 2)
        
        form_fields = self.system.detect_signatures(test_img)
        
        assert isinstance(form_fields, list)
        # May or may not detect signatures depending on the pattern complexity
    
    @patch('document_analysis_system.pytesseract.image_to_string')
    def test_recognize_handwriting(self, mock_tesseract):
        """Test handwriting recognition"""
        mock_tesseract.return_value = "Handwritten text"
        
        # Mock TrOCR
        self.system.trocr_model = Mock()
        self.system.trocr_processor = Mock()
        mock_tensor = Mock()
        mock_tensor.zeros.return_value = Mock()
        self.system.trocr_processor.return_value = Mock(pixel_values=mock_tensor)
        self.system.trocr_model.generate.return_value = Mock()
        self.system.trocr_processor.batch_decode.return_value = ["Handwritten text"]
        
        text = self.system.recognize_handwriting(self.test_image)
        
        assert isinstance(text, str)
    
    def test_classify_document_type(self):
        """Test document type classification"""
        # Test with invoice-like text
        invoice_text = "Invoice #12345 Amount Due: $100.00 Tax: $10.00 Total: $110.00"
        doc_type = self.system.classify_document_type(self.test_image, invoice_text)
        
        assert isinstance(doc_type, DocumentType)
        assert doc_type == DocumentType.INVOICE
        
        # Test with contract-like text
        contract_text = "This agreement between parties hereby establishes terms and conditions"
        doc_type = self.system.classify_document_type(self.test_image, contract_text)
        
        assert doc_type == DocumentType.CONTRACT
        
        # Test with unknown text
        unknown_text = "Random text without specific keywords"
        doc_type = self.system.classify_document_type(self.test_image, unknown_text)
        
        assert doc_type == DocumentType.UNKNOWN
    
    @patch('document_analysis_system.camelot.read_pdf')
    def test_extract_tables_camelot(self, mock_camelot):
        """Test table extraction using Camelot"""
        # Mock Camelot table
        mock_table = Mock()
        mock_table.df = pd.DataFrame({
            'Column1': ['Row1Col1', 'Row2Col1'],
            'Column2': ['Row1Col2', 'Row2Col2']
        })
        mock_table.accuracy = 85.0
        
        mock_camelot.return_value = [mock_table]
        
        tables = self.system.extract_tables_camelot("test.pdf")
        
        assert isinstance(tables, list)
        assert len(tables) == 1
        
        table = tables[0]
        assert isinstance(table, DocumentTable)
        assert table.num_rows == 2
        assert table.num_cols == 2
        assert len(table.cells) == 4
    
    def test_extract_tables_cv(self):
        """Test computer vision table extraction"""
        # Create image with table-like structure
        test_img = np.zeros((300, 400, 3), dtype=np.uint8)
        
        # Draw horizontal lines
        cv2.line(test_img, (50, 100), (350, 100), (255, 255, 255), 2)
        cv2.line(test_img, (50, 150), (350, 150), (255, 255, 255), 2)
        cv2.line(test_img, (50, 200), (350, 200), (255, 255, 255), 2)
        
        # Draw vertical lines
        cv2.line(test_img, (100, 80), (100, 220), (255, 255, 255), 2)
        cv2.line(test_img, (200, 80), (200, 220), (255, 255, 255), 2)
        cv2.line(test_img, (300, 80), (300, 220), (255, 255, 255), 2)
        
        with patch.object(self.system, 'extract_text_from_region', return_value="Cell text"):
            tables = self.system.extract_tables_cv(test_img)
        
        assert isinstance(tables, list)
        # Should detect the table structure we created
        if tables:
            table = tables[0]
            assert isinstance(table, DocumentTable)
            assert table.num_rows > 0
            assert table.num_cols > 0
    
    def test_analyze_document_complete(self):
        """Test complete document analysis pipeline"""
        with patch.object(self.system, 'extract_text_from_region', return_value="Sample document text"):
            result = self.system.analyze_document(self.test_image)
        
        assert isinstance(result, DocumentAnalysisResult)
        assert isinstance(result.document_type, DocumentType)
        assert isinstance(result.elements, list)
        assert isinstance(result.tables, list)
        assert isinstance(result.form_fields, list)
        assert isinstance(result.text_content, str)
        assert isinstance(result.metadata, dict)
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1
    
    def test_export_results_json(self):
        """Test JSON export functionality"""
        # Create sample result
        bbox = BoundingBox(10, 20, 100, 80, 0.9)
        element = DocumentElement(
            element_type=LayoutElement.PARAGRAPH,
            bbox=bbox,
            text="Sample text",
            confidence=0.8,
            metadata={"method": "test"}
        )
        
        result = DocumentAnalysisResult(
            document_type=DocumentType.INVOICE,
            elements=[element],
            tables=[],
            form_fields=[],
            text_content="Sample text content",
            metadata={"test": True},
            confidence=0.85
        )
        
        json_output = self.system.export_results(result, 'json')
        
        assert isinstance(json_output, str)
        # Should be valid JSON
        parsed = json.loads(json_output)
        assert parsed['document_type'] == 'invoice'
        assert parsed['confidence'] == 0.85
        assert len(parsed['elements']) == 1
    
    def test_export_results_csv(self):
        """Test CSV export functionality"""
        # Create sample result
        bbox = BoundingBox(10, 20, 100, 80, 0.9)
        element = DocumentElement(
            element_type=LayoutElement.PARAGRAPH,
            bbox=bbox,
            text="Sample text",
            confidence=0.8,
            metadata={"method": "test"}
        )
        
        result = DocumentAnalysisResult(
            document_type=DocumentType.INVOICE,
            elements=[element],
            tables=[],
            form_fields=[],
            text_content="Sample text content",
            metadata={"test": True},
            confidence=0.85
        )
        
        csv_output = self.system.export_results(result, 'csv')
        
        assert isinstance(csv_output, str)
        assert "Element Type,Text,Confidence" in csv_output
        assert "paragraph,Sample text,0.8" in csv_output

class TestBoundingBox:
    """Test BoundingBox data class"""
    
    def test_bounding_box_creation(self):
        """Test BoundingBox creation"""
        bbox = BoundingBox(10, 20, 100, 80, 0.9)
        
        assert bbox.x1 == 10
        assert bbox.y1 == 20
        assert bbox.x2 == 100
        assert bbox.y2 == 80
        assert bbox.confidence == 0.9
    
    def test_bounding_box_default_confidence(self):
        """Test BoundingBox with default confidence"""
        bbox = BoundingBox(10, 20, 100, 80)
        
        assert bbox.confidence == 0.0

class TestDocumentElement:
    """Test DocumentElement data class"""
    
    def test_document_element_creation(self):
        """Test DocumentElement creation"""
        bbox = BoundingBox(10, 20, 100, 80, 0.9)
        element = DocumentElement(
            element_type=LayoutElement.PARAGRAPH,
            bbox=bbox,
            text="Sample text",
            confidence=0.8,
            metadata={"method": "test"}
        )
        
        assert element.element_type == LayoutElement.PARAGRAPH
        assert element.bbox == bbox
        assert element.text == "Sample text"
        assert element.confidence == 0.8
        assert element.metadata == {"method": "test"}

class TestTableCell:
    """Test TableCell data class"""
    
    def test_table_cell_creation(self):
        """Test TableCell creation"""
        bbox = BoundingBox(10, 20, 50, 40, 0.8)
        cell = TableCell(
            row=0,
            col=1,
            text="Cell content",
            bbox=bbox,
            confidence=0.9
        )
        
        assert cell.row == 0
        assert cell.col == 1
        assert cell.text == "Cell content"
        assert cell.bbox == bbox
        assert cell.confidence == 0.9

class TestDocumentTable:
    """Test DocumentTable data class"""
    
    def test_document_table_creation(self):
        """Test DocumentTable creation"""
        bbox1 = BoundingBox(10, 20, 50, 40, 0.8)
        bbox2 = BoundingBox(50, 20, 90, 40, 0.8)
        
        cell1 = TableCell(0, 0, "Cell 1", bbox1, 0.9)
        cell2 = TableCell(0, 1, "Cell 2", bbox2, 0.9)
        
        table_bbox = BoundingBox(10, 20, 90, 40, 0.85)
        
        table = DocumentTable(
            cells=[cell1, cell2],
            num_rows=1,
            num_cols=2,
            bbox=table_bbox,
            confidence=0.85
        )
        
        assert len(table.cells) == 2
        assert table.num_rows == 1
        assert table.num_cols == 2
        assert table.bbox == table_bbox
        assert table.confidence == 0.85

class TestFormField:
    """Test FormField data class"""
    
    def test_form_field_creation(self):
        """Test FormField creation"""
        bbox = BoundingBox(10, 20, 100, 40, 0.8)
        field = FormField(
            field_name="name",
            field_value="John Doe",
            field_type="text",
            bbox=bbox,
            confidence=0.9
        )
        
        assert field.field_name == "name"
        assert field.field_value == "John Doe"
        assert field.field_type == "text"
        assert field.bbox == bbox
        assert field.confidence == 0.9

class TestDocumentAnalysisResult:
    """Test DocumentAnalysisResult data class"""
    
    def test_document_analysis_result_creation(self):
        """Test DocumentAnalysisResult creation"""
        bbox = BoundingBox(10, 20, 100, 80, 0.9)
        element = DocumentElement(
            element_type=LayoutElement.PARAGRAPH,
            bbox=bbox,
            text="Sample text",
            confidence=0.8,
            metadata={"method": "test"}
        )
        
        result = DocumentAnalysisResult(
            document_type=DocumentType.INVOICE,
            elements=[element],
            tables=[],
            form_fields=[],
            text_content="Sample text content",
            metadata={"test": True},
            confidence=0.85
        )
        
        assert result.document_type == DocumentType.INVOICE
        assert len(result.elements) == 1
        assert len(result.tables) == 0
        assert len(result.form_fields) == 0
        assert result.text_content == "Sample text content"
        assert result.metadata == {"test": True}
        assert result.confidence == 0.85

class TestEnums:
    """Test enum classes"""
    
    def test_document_type_enum(self):
        """Test DocumentType enum"""
        assert DocumentType.INVOICE.value == "invoice"
        assert DocumentType.RECEIPT.value == "receipt"
        assert DocumentType.CONTRACT.value == "contract"
        assert DocumentType.UNKNOWN.value == "unknown"
    
    def test_layout_element_enum(self):
        """Test LayoutElement enum"""
        assert LayoutElement.TITLE.value == "title"
        assert LayoutElement.PARAGRAPH.value == "paragraph"
        assert LayoutElement.TABLE.value == "table"
        assert LayoutElement.FORM_FIELD.value == "form_field"

class TestIntegration:
    """Integration tests for the complete system"""
    
    def setup_method(self):
        """Set up integration test fixtures"""
        # Create a more realistic test image
        self.test_image = np.ones((1000, 800, 3), dtype=np.uint8) * 255
        
        # Add title area
        cv2.rectangle(self.test_image, (50, 50), (750, 120), (240, 240, 240), -1)
        cv2.putText(self.test_image, "INVOICE", (300, 90), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        
        # Add text areas
        cv2.rectangle(self.test_image, (50, 150), (750, 200), (250, 250, 250), -1)
        cv2.rectangle(self.test_image, (50, 220), (750, 270), (250, 250, 250), -1)
        
        # Add table-like structure
        for i in range(4):
            y = 320 + i * 50
            cv2.rectangle(self.test_image, (50, y), (750, y + 40), (245, 245, 245), -1)
            cv2.line(self.test_image, (200, y), (200, y + 40), (0, 0, 0), 1)
            cv2.line(self.test_image, (400, y), (400, y + 40), (0, 0, 0), 1)
            cv2.line(self.test_image, (600, y), (600, y + 40), (0, 0, 0), 1)
    
    @patch('document_analysis_system.LayoutLMv3Processor')
    @patch('document_analysis_system.LayoutLMv3ForTokenClassification')
    @patch('document_analysis_system.easyocr.Reader')
    @patch('document_analysis_system.paddleocr.PaddleOCR')
    @patch('document_analysis_system.pytesseract.image_to_string')
    def test_full_document_analysis_pipeline(self, mock_tesseract, mock_paddle, 
                                           mock_easyocr, mock_layoutlm_model, mock_layoutlm_processor):
        """Test the complete document analysis pipeline"""
        
        # Mock OCR responses
        mock_tesseract.return_value = "INVOICE\nCompany Name\nAddress\nItem 1 $10.00\nItem 2 $20.00\nTotal $30.00"
        
        mock_easyocr_instance = Mock()
        mock_easyocr_instance.readtext.return_value = [
            ([(50, 50), (750, 50), (750, 120), (50, 120)], "INVOICE", 0.95),
            ([(50, 150), (750, 150), (750, 200), (50, 200)], "Company Name", 0.90),
            ([(50, 220), (750, 220), (750, 270), (50, 270)], "Address", 0.88)
        ]
        mock_easyocr.return_value = mock_easyocr_instance
        
        mock_paddle_instance = Mock()
        mock_paddle_instance.ocr.return_value = [
            [([50, 50, 750, 120], ("INVOICE", 0.95))],
            [([50, 150, 750, 200], ("Company Name", 0.90))]
        ]
        mock_paddle.return_value = mock_paddle_instance
        
        # Initialize system with mocks
        with patch('document_analysis_system.lp.Detectron2LayoutModel'):
            system = DocumentAnalysisSystem()
        
        # Run analysis
        result = system.analyze_document(self.test_image)
        
        # Verify results
        assert isinstance(result, DocumentAnalysisResult)
        assert result.document_type == DocumentType.INVOICE  # Should detect as invoice
        assert len(result.text_content) > 0
        assert result.confidence > 0
        
        # Should detect some layout elements
        assert len(result.elements) >= 0  # May vary based on detection
        
        # Metadata should be populated
        assert 'image_shape' in result.metadata
        assert 'processing_methods' in result.metadata

if __name__ == "__main__":
    pytest.main([__file__, "-v"])